"""Local file CLI; no transport or server entry point."""

import argparse
import os
import sys

from .contracts import INPUT_BYTES, Invalid, parse
from .model import evaluate
from .report import encode, write_fresh


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline normalized cache teaching model")
    parser.add_argument("input")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", help="New file only; existing files are rejected")
    args = parser.parse_args(argv)
    try:
        if args.output and os.path.normcase(os.path.realpath(args.input)) == os.path.normcase(os.path.realpath(args.output)):
            raise Invalid("INPUT_OUTPUT_ALIAS")
        with open(args.input, "rb") as source:
            raw = source.read(INPUT_BYTES + 1)
        report = evaluate(parse(raw))
        payload = encode(report, args.format)
        if args.output:
            write_fresh(args.output, payload)
        else:
            if sys.stdout.buffer.write(payload) != len(payload):
                raise OSError("SHORT_STDOUT_WRITE")
            sys.stdout.buffer.flush()
        return 2 if any(item["status"] == "UNSUPPORTED" for item in report["results"]) else 0
    except Invalid as exc:
        sys.stderr.write("cachelab: " + str(exc) + "\n")
    except OSError:
        sys.stderr.write("cachelab: IO_ERROR\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
