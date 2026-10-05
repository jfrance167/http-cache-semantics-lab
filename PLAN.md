# HTTP cache semantics lab — proposed plan

Date: October 5, 2026. Status: stages 2–4 approved by coordinator under Jake's
direct mandate; October 5 01:41 decision in SUCCESSORS.md.
Tier 3 portfolio security learning tool, with a deliberately small offline scope.
Research and source limitations: [RESEARCH.md](RESEARCH.md).

## Problem and success criteria

Explain when a hypothetical shared cache could store and reuse one synthetic HTTP
response. Separate storage, request matching, freshness and proposed origin contact.
Demonstrate why a cacheable response is not necessarily intended for every requester.
Success means independently labelled fixtures, explicit unsupported cases, bounded
input/output, reproducible checks, and documentation that accurately limits the model.
No live cache, server, browser, proxy or HTTP request is part of this project.

## Proposed supported contract

A reusable Python library and CLI accept versioned normalized JSON, rather than wire
HTTP. Each case describes an anonymous GET, complete 200 response, original request,
subsequent request, explicit freshness lifetime directives, declared corrected initial
age, received time and evaluation time. Times are synthetic integer seconds; the CLI
never sleeps or reads wall-clock time to determine a decision.

The response has exact booleans for unqualified no-store, no-cache and private;
optional nonnegative max_age and s_maxage integers; a supported Vary selector; and
a boolean indicating whether a strong validator is available. The model proposes
validation or a fetch but never performs either or claims a successful 304 response.
Require an explicit lifetime on every supported response; no heuristic fallback.

The key is GET plus an already canonical target URI, including the query. Freeze a
narrow visible-ASCII URI contract before code, and reject fragments, userinfo and
noncanonical forms. Do not silently normalize unfamiliar URI syntax. Header names
are case insensitive, but the only supported varied field is synthetic x-variant.
Its already normalized value is compared exactly; absence differs from empty.
Vary: * cannot match. Other varied fields are unsupported, including negotiation
syntax whose semantic equivalence would need more parsing.

Proposed decision order: validate the entire case and supported scope; decide storage;
check key and Vary matching; require validation for no-cache; then assess freshness.
Freshness lifetime uses s_maxage when present, otherwise max_age. Current age is
declared corrected_initial_age plus now minus received_at. Equality with the lifetime
is stale. Stale entries are never released by this subset. A matching entry requiring
origin contact proposes CONDITIONAL_VALIDATION when a strong validator is available,
otherwise FETCH_REQUIRED. A mismatched entry is a miss, not a validator for another key.

Return separate storage_allowed, request_matches, current_age, freshness_lifetime,
fresh, proposed_action and reason codes. Unsupported inputs return UNSUPPORTED with
an explanation, distinct from invalid JSON and from a supported negative decision.
Retain case IDs, contract version and all declared modeling assumptions in reports.

An independent synthetic sharing_intended boolean describes fixture intent. It does
not alter the protocol decision or authenticate content. Show protocol reuse alongside
declared intent, including an intentionally mislabelled response. An unsafe teaching
comparator may ignore private/Vary/freshness, but cannot serve content or grant access.
No bodies, secrets or real session material are accepted or stored.

## Explicit exclusions

Authentication, Authorization/Cookie/Set-Cookie presence, qualified directives, request
cache-control directives, public/must-understand combinations, other status codes and
methods, partial responses, redirects, raw header parsing, Expires/Date/Age parsing,
heuristic freshness, weak validators, 304 merging, persistence, concurrency, eviction,
stale allowances, content negotiation and a private-cache implementation are unsupported.
HTTP permits some authenticated shared caching under specified conditions; this lab
does not substitute a blanket prohibition for those unimplemented rules.

No claim of RFC conformance, browser behavior, actual confidentiality or deployment
readiness. No API, dashboard, cloud/model dependency, cache modification, traffic
generation, system configuration, publication or merge.

## Architecture, dependencies and reuse

Build original standard-library code: contract loader/validator, pure decision model,
bounded JSON/escaped Markdown reporter, CLI and frozen fixture evaluator. Keep parser
validation separate from protocol reasoning. Reuse reviewed bounded-loader/reporting
ideas from the original CORS lab after inspecting their suitability; do not modify that
lab. No third-party runtime installation is needed. Existing verification tooling can
be reused without recreating shared helpers. Original implementation can use MIT;
borrowed code, if any, requires its source and license obligations recorded first.

CacheControl and requests-cache are useful references but introduce Requests sessions,
transport/persistence behavior and dependencies beyond this normalized teaching model.
HTTP retry/response-loss ambiguity is a credible alternate project, but its method and
retry reasoning is a different gap. Cache policy is the selected successor.

## Threat model and bounds

Assets: report integrity, accurate teaching claims, host files and bounded resource use.
An attacker may control the complete input file and all case text. Trusted components:
reviewed code, fixed contract, fixed fixture oracle and caller-selected fresh output path.
Neither caller labels nor a detector authenticate intended sharing or origin behavior.

Proposed limits: 128 KiB UTF-8 input, depth 8, 100 cases, 32 headers per request,
256 characters per header value, 512 per target URI, 64 per case ID, numeric tokens
at most 10 digits and values at most 1,000,000,000. Reject duplicate keys, unknown
fields, booleans used as integers, invalid Unicode, duplicate case IDs and impossible
time ordering. Library entry points also require bounded concrete built-in containers;
do not accept custom objects or generators. Bound final output to 512 KiB before writing.
Escape all report content, including IDs. Never inspect only a truncated prefix.

Use exclusive fresh output creation, protect against input/output aliases, and report
short writes honestly. Specify failure cleanup for newly created files before code;
do not promise atomic stdout. No commands, imports, paths or network actions come from
case content. A local process/JSON bound is not an OS sandbox or hard memory guarantee.

## Stages and definitions of done

1. **Research gate (completed):** finish candidate/source review and this plan; retain
   worker/source evidence. Obtain concrete implementation approval before project code.
2. **Contract and frozen oracle:** define exact fields, URI/Unicode grammar, status and
   output rules; freeze at least 24 distinct expected cases before implementation.
   Cover storage-versus-reuse, private/no-store/no-cache, mismatch/Vary/absence,
   zero lifetime, equality, s_maxage precedence, age accumulation and unsupported rules.
3. **Library and CLI:** implement pure decisions, bounded loader/reporters and demo.
   Verify malformed/deep/oversized inputs and no partial-success claims. All case text
   remains inert. Document exact CLI exit statuses before depending on them.
4. **Verification and portfolio:** normal and optimized Python tests, syntax check,
   available Bandit, forbidden-capability review, ECC actual-code self-review, focused
   mutations, source-restoration hashes, README/SECURITY/license/AI disclosure and
   concise STATE/DECISIONS/LEARNING records. Save verified evidence and a vault milestone.

Tests must use independently fixed expectations, not merely call the same algorithm to
construct an oracle. Focused mutations remove Vary matching, treat equality as fresh,
and permit private storage; each must fail an appropriate test, restore source, then
pass affected checks. Existing Bandit availability must be checked; no automatic
dependency installation. Record Windows/runtime scope and any missing checks.

Local security-sensitive completion remains subject to Jake's manual boundary review.
Repository/GitHub baseline, hosted checks, publication and deployment need their own
authorization. Preserve unrelated parent repository changes and older lab evidence.

## Worker use

Installed loopback Ollama qwen3.5:2b completed a three-definition extraction from supplied
facts in 558 ms. Raw brief/output/metadata remain in research/. Accepted only that
bounded extraction after review. Codex performed source verification, security judgments
and this plan. No remote drafting, paid inference or new model/service was used.

## Approved implementation addendum

Freeze exact contract/exits/grammar and at least 24 independent labels before code.
Age-freshness is separate from reuse. Private/no-store yield no available shared entry.
Vary mismatch/* means a miss, never validation of another variant. Validate unsupported
payloads completely. Auth/cookie/set-cookie presence in all three messages, including
empty values, is unsupported. Reject duplicate headers and raw/normalized conflicts.
Preserve supported query spelling; use reserved hosts without resolution. Define null
fields and derived bounds. Exact time, intent separation, escaped/exclusive output,
normal/optimized tests, mutations, ECC/SAST apply. No simulated 304, live services,
real data, publication, merge, new chat/scheduler. Decision: SUCCESSORS.md 01:41.
