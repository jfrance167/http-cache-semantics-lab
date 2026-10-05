"""Independent frozen outcomes and adversarial contract/output checks."""

import ast
import copy
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
# Fixed local interpreter/CLI tests only; no input-derived commands or shell.
import subprocess  # nosec B404
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from cachelab import Invalid, evaluate, parse
from cachelab.contracts import INPUT_BYTES, OUTPUT_BYTES
from cachelab.report import encode, write_fresh

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = json.loads((ROOT / "fixtures/cases.json").read_text(encoding="utf-8"))
EXPECTED = json.loads((ROOT / "fixtures/expected.json").read_text(encoding="utf-8"))


def one():
    return {"version": 1, "cases": [copy.deepcopy(DOCUMENT["cases"][0])]}


@contextmanager
def scratch():
    # Sandbox default temp is not writable here; own temporary subtree only.
    temporary = tempfile.TemporaryDirectory(dir=ROOT, prefix="test-scratch-")
    if not Path(temporary.name).resolve().is_relative_to(ROOT):
        raise RuntimeError("temporary path outside project")
    try:
        yield temporary.name
    finally:
        temporary.cleanup()


class LabTests(unittest.TestCase):
    def test_frozen_labels(self):
        report = evaluate(DOCUMENT)
        self.assertEqual(len(report["results"]), 34)
        for actual, expected in zip(report["results"], EXPECTED):
            with self.subTest(case=expected["id"]):
                self.assertEqual({key: actual[key] for key in expected}, expected)
                if actual["status"] == "SUPPORTED":
                    reuse = expected["proposed_action"] == "REUSE"
                    self.assertEqual(actual["protocol_reusable"], reuse)
                    self.assertEqual(actual["origin_contact"], not reuse)
                    self.assertIs(actual["naive_reusable"], True)
                else:
                    for key in ("protocol_reusable", "origin_contact", "naive_reusable"):
                        self.assertIsNone(actual[key])

    def test_frozen_bytes(self):
        receipt = json.loads((ROOT / "research/fixture-freeze.json").read_text(encoding="utf-8-sig"))
        for entry in receipt:
            path = ROOT / ("CONTRACT.md" if entry["Path"].endswith("CONTRACT.md") else
                           "fixtures/" + entry["Path"].replace("\\", "/").split("/")[-1])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest().upper(), entry["Hash"])

    def test_no_input_mutation(self):
        doc = one()
        saved = copy.deepcopy(doc)
        evaluate(doc)
        self.assertEqual(doc, saved)

    def test_age_upper_bound(self):
        doc = one()
        case = doc["cases"][0]
        case.update(corrected_initial_age=10**9, received_at=0, now=10**9)
        self.assertEqual(evaluate(doc)["results"][0]["current_age"], 2*10**9)

    def test_types_bounds_time(self):
        for field, value in [("now", True), ("now", -1), ("now", 10**9+1),
                             ("now", 99), ("sharing_intended", 1), ("id", ""),
                             ("id", "a"*65), ("id", "\ud800"), ("id", "\x1b")]:
            with self.subTest(field=field, value=repr(value)):
                doc = one()
                doc["cases"][0][field] = value
                with self.assertRaises(Invalid):
                    evaluate(doc)

    def test_unknown_duplicate_ids_and_cases(self):
        for edit in [lambda d: d.update(extra=1), lambda d: d.update(version=True),
                     lambda d: d.update(cases=[]), lambda d: d["cases"].append(copy.deepcopy(d["cases"][0])),
                     lambda d: d.update(cases=[copy.deepcopy(d["cases"][0]) for _ in range(101)])]:
            doc = one()
            edit(doc)
            with self.assertRaises(Invalid):
                evaluate(doc)

    def test_json_boundaries(self):
        bad = [b'{"a":1,"a":2}', b'{"x":1.2}', b'{"x":NaN}', b'{"x":12345678901}',
               b'['*9+b'0'+b']'*9, b'\xff', b'{} '+b' ' * INPUT_BYTES, b'not-json']
        for raw in bad:
            with self.subTest(raw=raw[:30]), self.assertRaises(Invalid):
                parse(raw)
        self.assertEqual(parse(b'"[[]]"'), "[[]]")
        self.assertEqual(parse(b'{"x":1000000000}'), {"x":10**9})
        with self.assertRaises(Invalid):
            parse(bytearray(b'{}'))

    def test_custom_objects_not_executed(self):
        class Evil(dict):
            def items(self):
                raise RuntimeError("must not execute")
        for value in (Evil(), iter([]), object(), {"version":1,"cases":(one()["cases"][0],)}):
            with self.assertRaises(Invalid):
                evaluate(value)

    def test_api_depth_nodes_encoded_size(self):
        nested = []
        for _ in range(9):
            nested = [nested]
        with self.assertRaises(Invalid):
            evaluate(nested)
        doc = {str(i): [None]*200 for i in range(100)}
        with self.assertRaisesRegex(Invalid, "NODE_LIMIT"):
            evaluate(doc)
        doc = one()
        doc["cases"] = []
        for index in range(100):
            case = copy.deepcopy(one()["cases"][0])
            case["id"] = str(index)
            case["response"]["headers"] = [["x-note", "a"*256]]
            case["original"]["headers"] = [["x-variant", "b"*256]]
            case["subsequent"]["headers"] = [["x-variant", "c"*256]]
            doc["cases"].append(case)
        # API byte bound applies independently of a JSON input file's byte bound.
        for case in doc["cases"]:
            case["original"]["uri"] += "a"*400
            case["subsequent"]["uri"] += "b"*400
        with self.assertRaisesRegex(Invalid, "INPUT_LIMIT"):
            evaluate(doc)

    def test_unsupported_still_validates_every_field(self):
        doc = one()
        case = doc["cases"][0]
        case["original"]["headers"] = [["Authorization", ""]]
        case["response"]["directives"]["max_age"] = True
        with self.assertRaises(Invalid):
            evaluate(doc)
        case["response"]["directives"]["max_age"] = 60
        case["subsequent"]["headers"] = [["x-variant", "a"*257]]
        with self.assertRaises(Invalid):
            evaluate(doc)

    def test_auth_presence_all_messages_and_names(self):
        for where in ("original", "subsequent", "response"):
            for name in ("Authorization", "Cookie", "Set-Cookie"):
                doc = one()
                doc["cases"][0][where]["headers"] = [[name, ""]]
                result = evaluate(doc)["results"][0]
                self.assertEqual(result["reasons"], ["UNSUPPORTED_AUTH_CONTEXT"])
                self.assertIsNone(result["fresh"])

    def test_headers_and_vary_ambiguity(self):
        for pairs in ([["x-variant","a"],["X-Variant","b"]], [["cache-control",""]],
                      [["x-variant", "a,b"]], [["x-variant", " a"]], [["bad name", "a"]]):
            doc = one()
            doc["cases"][0]["original"]["headers"] = pairs
            with self.assertRaises(Invalid):
                evaluate(doc)
        for fields in (["*","x-variant"], ["x-variant","X-Variant"], ["x-variant,other"]):
            doc = one()
            doc["cases"][0]["response"]["vary"] = fields
            with self.assertRaises(Invalid):
                evaluate(doc)

    def test_scope_reasons_and_no_early_output(self):
        doc = one()
        case = doc["cases"][0]
        case["response"]["headers"] = [["x-other", "a"]]
        case["original"]["method"] = "HEAD"
        result = evaluate(doc)["results"][0]
        self.assertEqual(result["reasons"], ["UNSUPPORTED_HEADER","UNSUPPORTED_METHOD"])
        doc["cases"].append(copy.deepcopy(one()["cases"][0]))
        with self.assertRaises(Invalid):
            evaluate(doc)  # Duplicate ID invalid even after unsupported first case.

    def test_uri_scope_no_normalization(self):
        for uri in ("https://cache.test/a/../b", "https://cache.test:443/a",
                    "https://CACHE.test/a", "https://cache.test/%61", "https://cache.test/a#x",
                    "https://user@cache.test/a", "https://cache.test/é", "https://real.invalid/a"):
            doc = one()
            doc["cases"][0]["subsequent"]["uri"] = uri
            self.assertEqual(evaluate(doc)["results"][0]["status"], "UNSUPPORTED")

    def test_report_inert_ids(self):
        doc = one()
        doc["cases"][0]["id"] = '<img src=x>|[click](https://evil.test)'
        report = evaluate(doc)
        markdown = encode(report,"markdown")
        self.assertNotIn(b'<img', markdown)
        self.assertNotIn(b'[click]', markdown)
        self.assertIn(b'&#60;', markdown)
        self.assertEqual(json.loads(encode(report))["results"][0]["id"], doc["cases"][0]["id"])

    def test_output_bound(self):
        report = {"results":[], "assumptions":["a"*OUTPUT_BYTES]}
        for fmt in ("json","markdown"):
            with self.assertRaisesRegex(Invalid,"OUTPUT_LIMIT"):
                encode(report,fmt)

    def test_exclusive_output(self):
        with scratch() as tmp:
            path = Path(tmp)/"report.json"
            write_fresh(path,b'original')
            with self.assertRaises(FileExistsError):
                write_fresh(path,b'replacement')
            self.assertEqual(path.read_bytes(),b'original')

    def test_short_write_cleanup(self):
        stream = MagicMock()
        stream.__enter__.return_value = stream
        stream.write.return_value = 0
        with patch("cachelab.report.open", return_value=stream), patch("cachelab.report.os.unlink") as unlink:
            with self.assertRaises(OSError):
                write_fresh("owned-new",b'hello')
            unlink.assert_called_once_with("owned-new")
        with patch("cachelab.report.open", return_value=stream), patch("cachelab.report.os.unlink",side_effect=OSError):
            with self.assertRaisesRegex(Invalid,"CLEANUP_FAILED"):
                write_fresh("owned-new",b'hello')

    def test_close_failure_cleanup(self):
        stream = MagicMock()
        stream.__enter__.return_value = stream
        stream.write.return_value = 1
        stream.__exit__.side_effect = OSError("close failure")
        with patch("cachelab.report.open",return_value=stream), patch("cachelab.report.os.unlink") as unlink:
            with self.assertRaises(OSError):
                write_fresh("owned-new",b'x')
            unlink.assert_called_once()

    def test_cli_status_alias_and_existing(self):
        with scratch() as tmp:
            source,output = Path(tmp)/"in.json",Path(tmp)/"out.json"
            prefix = [sys.executable] + (["-O"] if sys.flags.optimize else []) + ["-m","cachelab"]
            def run(*arguments):
                # Fixed interpreter/module, test-owned file arguments, shell disabled.
                return subprocess.run(prefix+list(arguments),cwd=ROOT,capture_output=True,timeout=15,check=False)  # nosec B603
            source.write_text(json.dumps(one()),encoding="utf-8")
            self.assertEqual(run(str(source)).returncode,0)
            self.assertEqual(run(str(source),"--output",str(output)).returncode,0)
            self.assertEqual(run(str(source),"--output",str(output)).returncode,1)
            self.assertEqual(run(str(source),"--output",str(source)).returncode,1)
            source.write_text(json.dumps(DOCUMENT),encoding="utf-8")
            self.assertEqual(run(str(source)).returncode,2)
            source.write_text('{"bad":true}',encoding="utf-8")
            invalid = run(str(source))
            self.assertEqual(invalid.returncode,1)
            self.assertEqual(invalid.stdout,b'')
            self.assertNotIn(str(source).encode(),invalid.stderr)
            missing = Path(tmp)/"invalid-output.json"
            self.assertEqual(run(str(source),"--output",str(missing)).returncode,1)
            self.assertFalse(missing.exists())

    def test_forbidden_capabilities(self):
        allowed = {"json","re","os","sys","argparse","contracts","model","report"}
        for path in (ROOT/"cachelab").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertTrue(all(item.name in allowed for item in node.names))
                if isinstance(node, ast.ImportFrom):
                    self.assertIn(node.module,allowed)
                if isinstance(node, ast.Call) and isinstance(node.func,ast.Name):
                    self.assertNotIn(node.func.id,{"eval","exec","__import__","compile"})
                self.assertNotIsInstance(node,ast.Assert)


if __name__ == "__main__":
    unittest.main()
