"""Pure decisions for the frozen subset; does not store or release responses."""

from .contracts import validate

ASSUMPTIONS = ["synthetic shared cache; anonymous complete GET/200 subset",
               "declared corrected initial age and synthetic integer times",
               "origin contact is proposed, never performed; no simulated 304",
               "intent is caller-declared, not authenticated",
               "not an HTTP conformance implementation or confidentiality guarantee"]


def _decide(case):
    result = {"id": case["id"], "status": "SUPPORTED", "reasons": [],
              "storage_allowed": None, "request_matches": None, "current_age": None,
              "freshness_lifetime": None, "fresh": None, "protocol_reusable": None,
              "origin_contact": None, "proposed_action": "UNSUPPORTED",
              "sharing_intended": case["sharing_intended"], "intent_conflict": None,
              "naive_reusable": None}
    if case["scope"]:
        result.update(status="UNSUPPORTED", reasons=case["scope"])
        return result
    response = case["response"]
    directives = response["directives"]
    lifetime = (directives["s_maxage"] if directives["s_maxage"] is not None
                else directives["max_age"])
    age = case["corrected_initial_age"] + case["now"] - case["received_at"]
    fresh = age < lifetime
    storage = not (directives["no_store"] or directives["private"])
    matches = None
    action = "FETCH_REQUIRED"
    original, subsequent = case["original"], case["subsequent"]
    if not storage:
        reason = "NO_STORE" if directives["no_store"] else "PRIVATE"
    elif original["uri"] != subsequent["uri"]:
        matches, reason = False, "KEY_MISMATCH"
    elif "*" in response["vary"]:
        matches, reason = False, "VARY_STAR"
    elif any(original["headers"].get(name) != subsequent["headers"].get(name)
             for name in response["vary"]):
        matches, reason = False, "VARY_MISMATCH"
    else:
        matches = True
        if directives["no_cache"] or not fresh:
            reason = "NO_CACHE" if directives["no_cache"] else "STALE"
            if response["strong_validator"]:
                action = "CONDITIONAL_VALIDATION"
        else:
            reason, action = "FRESH", "REUSE"
    reusable = action == "REUSE"
    result.update(storage_allowed=storage, request_matches=matches, current_age=age,
                  freshness_lifetime=lifetime, fresh=fresh, proposed_action=action,
                  reasons=[reason], protocol_reusable=reusable, origin_contact=not reusable,
                  intent_conflict=reusable and not case["sharing_intended"], naive_reusable=True)
    return result


def evaluate(document):
    """Evaluate concrete JSON-like data after complete bounded validation.

    Returns inert reasoning records, never an access-control or transport decision.
    One invalid case rejects the document, even if another case is unsupported.
    """
    cases = validate(document)
    return {"version": 1, "assumptions": list(ASSUMPTIONS),
            "results": [_decide(case) for case in cases]}
