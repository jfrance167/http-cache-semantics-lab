# Decisions

- Original stdlib normalized model, not a Requests caching wrapper: research candidates
  solve client transport/persistence, while this lab teaches hypothetical shared-cache
  decisions. Fewer dependencies are not asserted to prove security.
- Complete validation precedes scope decisions: unsupported authentication cannot hide
  malformed types, duplicates or oversized content in another represented message.
- Age-fresh is independent of storage/reuse. Null request_matches means no available
  shared entry; unsupported decision fields are all unknown rather than fabricated false.
- Declared corrected initial age avoids pretending to implement wire Date/Age arithmetic.
  Strict expiry equality and s_maxage precedence are independently labelled examples.
- Exact supported URI spelling/query order; unfamiliar canonicalization unsupported.
  No network resolution. Vary:* and mismatched variants propose a fetch, not validation
  of the wrong representation. No 304 merge or successful origin validation simulated.
- Synthetic sharing intent is independent from protocol labels; unsafe comparator is
  a teaching counterexample that never executes or grants permission.
- All user report characters become entities in Markdown; JSON is ASCII-escaped.
  Fresh-file creation refuses overwrite. Failure cleanup handles close errors as well
  as write/flush errors, but cannot guarantee durability or hostile-race protection.
- No separate Git/repository action under local-only approval. Parent changes preserved.
  MIT original code/AI disclosure; no upstream source adoption requiring license imports.
