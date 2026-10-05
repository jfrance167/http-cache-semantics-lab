# HTTP cache successor research

Research date: October 5, 2026. Recommendation: build the original bounded offline
model in [PLAN.md](PLAN.md), rather than adopt a live caching library. No code has
been implemented or upstream package executed in this research stage.

## Reuse and alternate

Reviewed prior CORS state/README: its scope excludes caching. Relevant access-control,
network-forensics and SIEM documentation and narrow workspace/vault searches did not
identify an existing matching shared-cache model; this is not an exhaustive audit of
every source file. No existing Graphify graph was available for the proposed lab.
Preserve all earlier lab evidence and limitations.

Read vault HTTP Idempotency and Retry Decisions.md and CSharp HttpClient Pools DNS and
Cookie Boundaries.md. The retry alternative concerns ambiguity after a response is
lost: repeated intended effects, response delivery and proof of non-application are
different questions. That supports a distinct later lab, rather than expanding this one.
Primary reference: [RFC 9110 §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2).

## Primary protocol evidence

[RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html) supports distinguishing storage
from reuse. Unqualified no-cache requires successful validation before reuse; unqualified
private prevents shared-cache storage; no-store constrains storage but is not a privacy
guarantee. Vary matching distinguishes absent fields, and Vary: * never matches. Freshness
uses a strict lifetime-greater-than-age comparison; shared caches give s-maxage precedence.
Authenticated reuse can be permitted under specified directives, so this plan excludes
that complexity rather than asserting it is universally prohibited.

Relevant sections: [storage](https://www.rfc-editor.org/rfc/rfc9111.html#section-3),
[authentication](https://www.rfc-editor.org/rfc/rfc9111.html#section-3.5),
[Vary](https://www.rfc-editor.org/rfc/rfc9111.html#section-4.1),
[freshness](https://www.rfc-editor.org/rfc/rfc9111.html#section-4.2.1),
[age](https://www.rfc-editor.org/rfc/rfc9111.html#section-4.2.3), and
[directives](https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2.2).
The normalized contract and conservative unsupported rules are proposed design choices,
not a claim to implement every rule in these sections.

## Strongest candidate: PSF CacheControl

Inspected actual connected-GitHub contents for
[controller](https://github.com/psf/cachecontrol/blob/master/cachecontrol/controller.py),
[tests](https://github.com/psf/cachecontrol/blob/master/tests/test_cache_control.py),
[manifest](https://github.com/psf/cachecontrol/blob/master/pyproject.toml),
[license](https://github.com/psf/cachecontrol/blob/master/LICENSE.txt) and
[CI](https://github.com/psf/cachecontrol/blob/master/.github/workflows/tests.yml).
Per-file blob identities are retained in research/source-identities.json. Branch links
are mutable; the recorded blobs identify inspected contents, not a pinned whole release.

Architecture: a Requests-session caching controller with serialization/backend support,
conditional handling and directive parsing. Tests include malformed Date, missing Date,
no-store with ETag, expired/fresh responses, Vary: *, and conditional responses. CI defines
Python 3.10–3.14 on Windows/Linux/macOS, pinned actions and minimal permissions. Its
results were not executed or verified here. The inspected manifest names version 0.14.4,
Python >=3.10, Requests and msgpack; filelock and Redis are optional. These dependencies
serve a transport/backend application and are unnecessary for this synthetic model.

Apache-2.0 requires applicable notices/attribution if code is adopted. No upstream code
is copied in the plan. Review of [issue 424](https://github.com/psf/cachecontrol/issues/424)
found a user report about concurrent Vary changes around conditional revalidation.
It was not reproduced, and no release-fix conclusion is drawn. It motivates excluding
concurrency and 304 updates. Another search result about no-cache is not treated as a
validated flaw: no-cache may permit storage. Activity, issue handling and declared CI
are maintenance evidence, not proof of package safety or current green checks.

## Alternate candidate: requests-cache

Inspected [policy actions](https://github.com/requests-cache/requests-cache/blob/main/requests_cache/policy/actions.py),
[manifest](https://github.com/requests-cache/requests-cache/blob/main/pyproject.toml),
[license](https://github.com/requests-cache/requests-cache/blob/main/LICENSE),
[history](https://github.com/requests-cache/requests-cache/blob/main/HISTORY.md) and
[header documentation](https://requests-cache.readthedocs.io/en/stable/user_guide/headers.html).
It implements persistent client caching, configurable expiration, conditional updates
and stale handling. The inspected manifest names 1.3.4 and Python >=3.8; dependencies
include Requests, urllib3, attrs, cattrs, platformdirs and url-normalize. BSD-2-Clause
requires preserving applicable copyright/conditions/disclaimer if adopting code.
Recent dated history entries provide maintenance evidence; not every chronology entry
was reconciled. No dependency/advisory scan or package installation occurred.

Test/CI retrieval was incomplete: a raw test URL failed, and guessed connected test/CI
paths returned 404. Do not infer absent tests or claim verified CI. CacheControl's actual
tests/CI supplied the stronger source comparison. Neither candidate's client-cache
behavior is assessed as a shared-proxy vulnerability in this research.

## Access and assurance limits

Connected GitHub was used successfully for CacheControl files and requests-cache history;
some searches/reads failed. Public primary-source web access supplemented it. Firecrawl
account access had failed, so the available web tool was used; no paid Firecrawl work.
No Scorecard, full advisory/supply-chain audit, upstream test run, live HTTP/browser
behavior or whole-repository security audit was performed. Missing evidence is a limit,
not evidence of insecurity. The standard-library recommendation rests on scope/fit,
not the assertion that fewer dependencies necessarily mean greater security.

## Local drafting evidence

research/local-brief.txt supplied three short protocol facts. The existing loopback
Ollama helper returned research/local-raw.txt and metadata using qwen3.5:2b, 558 ms,
30 output tokens, stop completion. Reviewed and accepted only the three definitions.
This is extraction of supplied facts, not an independent research/security review.
No remote provider, retry loop, paid fallback, model download or service change.
