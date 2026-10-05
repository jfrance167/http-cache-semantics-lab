# Frozen normalized teaching contract v1

Frozen before application code, October 5, 2026. No raw HTTP parsing or network.
JSON has exactly version (integer 1) and cases (1–100). Every case has id, original,
subsequent, response, corrected_initial_age, received_at, now, sharing_intended.
IDs: unique 1–64 Unicode scalar characters, no controls. Requests: exactly method,
uri, headers. Response: exactly status, complete, headers, directives, vary,
strong_validator. Directives: exactly no_store, no_cache, private, max_age, s_maxage.
Booleans exact bool; numbers exact int, 0–1e9; status 100–599. Lifetime nullable,
at least one required for support. now >= received_at. Residence <=1e9 and derived
current age <=2e9; no wrap. Validate every field before returning unsupported.

Headers: 0–32 two-string lists, names 1–64 ASCII token chars, values <=256 Unicode
scalar chars, no controls. Case-insensitive duplicates invalid. x-variant values
visible ASCII (empty valid), no comma/leading/trailing space. All represented
Authorization/Cookie/Set-Cookie names unsupported even empty. Raw cache-control,
vary,date,age,expires invalid as conflicting normalized metadata. Other names
unsupported except request x-variant and response x-note. Unknown object fields
invalid. Methods ASCII tokens; only uppercase GET supported. Response 200 and
complete true supported. vary: <=32 unique case-insensitive tokens or sole *;
combined star/field invalid. Only x-variant or * supported. No raw directive grammar.

URI <=512 chars: supported http:// or https://, lowercase DNS labels (1–63 chars,
alphanumeric/internal hyphens), ending .test or .example, required slash path.
Path uses ASCII letters/digits/._~/-; dot-only . and .. segments excluded. Optional
query uses letters/digits/._~=&- and may be empty. Other spellings unsupported:
no normalization/lookup, ports, percent encoding, fragments, userinfo, Unicode,
backslashes. Exact comparison preserves path case, query order and empty query.

Limits: 131072 input bytes/524288 output bytes, depth 8 (root 1), integer numeric
tokens <=10 digits, no duplicate JSON keys/malformed Unicode/C0/DEL controls.
API: concrete dict/list/str/int/bool/null only, depth 8, 10000 nodes, strings <=512,
same schema/encoded byte limit. No object coercion/generator iteration/assert guards.

Results: exactly id,status,reasons,storage_allowed,request_matches,current_age,
freshness_lifetime,fresh,protocol_reusable,origin_contact,proposed_action,
sharing_intended,intent_conflict,naive_reusable. UNSUPPORTED action/status => all
decision/age/comparator fields null; declared sharing_intended retained; sorted
scope reasons. Supported => age/fresh independent of storage/matching. Storage
false for private/no_store; request_matches null for unavailable entries, otherwise
exact key+Vary. Reuse needs storage, match, fresh and not no_cache. origin_contact
inverse of protocol_reusable. intent_conflict = reusable and not sharing_intended.
Naive teaching comparator always true for supported complete GET/200, enforces nothing.

Reason/action precedence: no_store => NO_STORE/FETCH_REQUIRED; private =>
PRIVATE/FETCH_REQUIRED; URI mismatch => KEY_MISMATCH/FETCH_REQUIRED; Vary:* =>
VARY_STAR/FETCH_REQUIRED; Vary mismatch => VARY_MISMATCH/FETCH_REQUIRED; no_cache =>
NO_CACHE; stale => STALE. Matching no_cache/stale uses CONDITIONAL_VALIDATION if
strong_validator, else FETCH_REQUIRED. Reusable => FRESH/REUSE. Scope reasons:
UNSUPPORTED_METHOD/URI/HEADER/VARY/RESPONSE/AUTH_CONTEXT or MISSING_EXPLICIT_LIFETIME.
No 304 success or response-content release. s_maxage takes precedence over max_age;
current age = corrected_initial_age + now - received_at; fresh iff age < lifetime.

CLI: python -m cachelab INPUT [--format json|markdown] [--output FRESH_FILE].
Exit 0 all supported (including negative decisions); 2 any unsupported; 1 invalid
data/read/write error. argparse syntax error separately uses 2. Whole-document
validation/evaluation/encoding before output; fresh exclusive binary file, no overwrite
or input alias. On failed fresh write remove only own newly created file, report cleanup
failure. No atomic stdout promise. Fixed error codes, no paths/input echoed. JSON ASCII
escaping; Markdown encodes every user character as an HTML numeric entity.

Independent hand-selected fixture expectations frozen before application code;
separate hash receipt identifies bytes. This is a subset contract, not full HTTP.
