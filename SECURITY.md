# Security boundaries

This is an offline teaching subset, not a deployed cache or injection/privacy firewall.
Use synthetic metadata only; no secrets, real session fields or customer content.
Do not use its results as an authorization decision or confidentiality guarantee.

Reviewed boundaries: exact concrete API types; whole-document validation including
unsupported cases; duplicate-key/header detection; bounded bytes/depth/numbers/cases;
reserved URI subset; no raw/normalized conflicts; age distinct from reuse; inert reports;
exclusive local outputs; fixed verifier commands. Invalid cases reject the whole document.

CLI paths and the Python host process are trusted. File size reads are bounded, but
the application does not prevent a trusted caller from selecting special files, block
hostile filesystem races or provide OS process isolation. Fresh-output cleanup can fail
and is reported; stdout output is not transactional. Abruptly killing the mutation
verifier can prevent its finally block from restoring source; check saved source hashes
before using an interrupted run. All mutation evidence is provisional until restoration
and final tests pass.

Manual review is required before any deployment or merge. Those actions are currently
outside authorization. Source security issues should be recorded with a small synthetic
reproducer and affected contract/line; never include private HTTP content or credentials.
No remote disclosure or message is initiated automatically.
