"""Strict bounded contract validation, inspired by the original CORS lab."""

import json
import re

INPUT_BYTES = 131_072
OUTPUT_BYTES = 524_288
MAX_INTEGER = 1_000_000_000
TOKEN = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", re.ASCII)
URI = re.compile(r"https?://([^/]+)/([A-Za-z0-9._~/-]*)(?:\?([A-Za-z0-9._~=&-]*))?", re.ASCII)
LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", re.ASCII)
AUTH = {"authorization", "cookie", "set-cookie"}
RAW_POLICY = {"cache-control", "vary", "date", "age", "expires"}


class Invalid(ValueError):
    """Fixed error code: document cannot be evaluated under this contract."""


def text(value, limit=256, nonempty=False):
    """Validate scalar text without coercion, truncation or replacement."""
    if type(value) is not str or len(value) > limit or (nonempty and not value):
        raise Invalid("TEXT_TYPE_OR_LIMIT")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise Invalid("TEXT_CONTROL")
    try:
        value.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise Invalid("INVALID_UNICODE") from exc
    return value


def keys(value, required):
    if type(value) is not dict or set(value) != set(required):
        raise Invalid("SCHEMA")


def number(value, lower=0, upper=MAX_INTEGER):
    if type(value) is not int or not lower <= value <= upper:
        raise Invalid("INTEGER_BOUND")
    return value


def boolean(value):
    if type(value) is not bool:
        raise Invalid("BOOLEAN_REQUIRED")
    return value


def _walk(value, depth, budget):
    # Reject custom containers before accessing their methods or iterating them.
    budget[0] += 1
    if budget[0] > 10_000:
        raise Invalid("NODE_LIMIT")
    kind = type(value)
    if kind in (dict, list):
        depth += 1
        if depth > 8 or len(value) > 200:
            raise Invalid("CONTAINER_LIMIT")
        if kind is dict:
            for key, item in value.items():
                text(key, 64, True)
                _walk(item, depth, budget)
        else:
            for item in value:
                _walk(item, depth, budget)
    elif kind is str:
        text(value, 512)
    elif kind is int:
        number(value)
    elif kind is not bool and value is not None:
        raise Invalid("BUILTIN_DATA_REQUIRED")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _integer(token):
    if len(token.lstrip("-")) > 10:
        raise Invalid("NUMERIC_TOKEN_LIMIT")
    return int(token)


def _noninteger(_):
    raise Invalid("INTEGER_ONLY")


def parse(raw):
    """Decode exact bytes with byte/depth/token bounds; evaluate() validates schema."""
    if type(raw) is not bytes or len(raw) > INPUT_BYTES:
        raise Invalid("INPUT_LIMIT")
    try:
        source = raw.decode("utf-8", "strict")
        quoted = escaped = False
        depth = 0
        for char in source:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > 8:
                    raise Invalid("JSON_DEPTH")
            elif char in "]}":
                depth -= 1
        return json.loads(source, object_pairs_hook=_pairs, parse_int=_integer,
                          parse_float=_noninteger, parse_constant=_noninteger)
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid("INVALID_JSON") from exc


def _uri_supported(value):
    text(value, 512, True)
    match = URI.fullmatch(value)
    if not match:
        return False
    host, path, _ = match.groups()
    labels = host.split(".")
    return (len(host) <= 253 and len(labels) >= 2
            and labels[-1] in {"test", "example"}
            and all(LABEL.fullmatch(label) for label in labels)
            and not any(segment in {".", ".."} for segment in path.split("/")))


def _headers(value, allowed, scope):
    if type(value) is not list or len(value) > 32:
        raise Invalid("HEADER_LIMIT")
    result = {}
    for pair in value:
        if type(pair) is not list or len(pair) != 2:
            raise Invalid("HEADER_PAIR")
        name = text(pair[0], 64, True)
        field = text(pair[1])
        if not TOKEN.fullmatch(name):
            raise Invalid("HEADER_NAME")
        name = name.lower()
        if name in result:
            raise Invalid("DUPLICATE_HEADER")
        if name in RAW_POLICY:
            raise Invalid("CONFLICTING_RAW_METADATA")
        if name == "x-variant" and (not field.isascii() or "," in field or field != field.strip()):
            raise Invalid("AMBIGUOUS_VARIANT")
        if name in AUTH:
            scope.add("UNSUPPORTED_AUTH_CONTEXT")
        elif name not in allowed:
            scope.add("UNSUPPORTED_HEADER")
        result[name] = field
    return result


def _request(value, scope):
    keys(value, {"method", "uri", "headers"})
    method = text(value["method"], 32, True)
    if not TOKEN.fullmatch(method):
        raise Invalid("METHOD_TOKEN")
    if method != "GET":
        scope.add("UNSUPPORTED_METHOD")
    if not _uri_supported(value["uri"]):
        scope.add("UNSUPPORTED_URI")
    return {"method": method, "uri": value["uri"],
            "headers": _headers(value["headers"], {"x-variant"}, scope)}


def _response(value, scope):
    keys(value, {"status", "complete", "headers", "directives", "vary", "strong_validator"})
    number(value["status"], 100, 599)
    boolean(value["complete"])
    boolean(value["strong_validator"])
    if value["status"] != 200 or not value["complete"]:
        scope.add("UNSUPPORTED_RESPONSE")
    _headers(value["headers"], {"x-note"}, scope)
    directives = value["directives"]
    keys(directives, {"no_store", "no_cache", "private", "max_age", "s_maxage"})
    for name in ("no_store", "no_cache", "private"):
        boolean(directives[name])
    for name in ("max_age", "s_maxage"):
        if directives[name] is not None:
            number(directives[name])
    if directives["max_age"] is None and directives["s_maxage"] is None:
        scope.add("MISSING_EXPLICIT_LIFETIME")
    vary = value["vary"]
    if type(vary) is not list or len(vary) > 32:
        raise Invalid("VARY_LIMIT")
    names = []
    for field in vary:
        text(field, 64, True)
        if not TOKEN.fullmatch(field):
            raise Invalid("VARY_TOKEN")
        names.append(field.lower())
    if len(set(names)) != len(names) or ("*" in names and len(names) != 1):
        raise Invalid("AMBIGUOUS_VARY")
    if any(name not in {"x-variant", "*"} for name in names):
        scope.add("UNSUPPORTED_VARY")
    return {"directives": dict(directives), "vary": names,
            "strong_validator": value["strong_validator"]}


def validate(document):
    """Validate the complete document and return internal normalized cases.

    Unsupported scope accumulates only after common shape/type/bounds checks;
    a malformed unsupported case rejects the entire document.
    """
    _walk(document, 0, [0])
    if len(json.dumps(document, ensure_ascii=False).encode("utf-8")) > INPUT_BYTES:
        raise Invalid("INPUT_LIMIT")
    keys(document, {"version", "cases"})
    if type(document["version"]) is not int or document["version"] != 1:
        raise Invalid("VERSION")
    cases = document["cases"]
    if type(cases) is not list or not 1 <= len(cases) <= 100:
        raise Invalid("CASE_LIMIT")
    result, seen = [], set()
    for case in cases:
        keys(case, {"id", "original", "subsequent", "response", "corrected_initial_age",
                    "received_at", "now", "sharing_intended"})
        identity = text(case["id"], 64, True)
        if identity in seen:
            raise Invalid("DUPLICATE_ID")
        seen.add(identity)
        for name in ("corrected_initial_age", "received_at", "now"):
            number(case[name])
        if case["now"] < case["received_at"]:
            raise Invalid("TIME_ORDER")
        boolean(case["sharing_intended"])
        scope = set()
        original = _request(case["original"], scope)
        subsequent = _request(case["subsequent"], scope)
        response = _response(case["response"], scope)
        result.append({**case, "original": original, "subsequent": subsequent,
                       "response": response, "scope": sorted(scope)})
    return result
