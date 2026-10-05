# Learning

Storage, selection and reuse answer different questions. no-cache does not mean
"cannot store". private/no-store blocks this subset's shared storage; Vary selects
the representation; no-cache requires origin contact even when age is fresh.

A validator only helps with a matching stored representation. A Vary mismatch is
not permission to revalidate another user's variant. Declared sharing intention is
not authenticated metadata; headers can authorize protocol reuse while contradicting
that declared intention. This lab demonstrates the mismatch without leaking content.

The expiry boundary is strict: age equal to lifetime is stale. Independent fixture
labels and targeted mutations caught changing that comparison, ignoring private and
ignoring Vary. Passing examples alone cannot establish full cache conformance.

Practical mistakes/fixes: sandbox default temp paths denied writes, so tests now use
checked own-project temporary subtrees. The verifier initially needed parent directory
creation. Mutation detection initially accepted any exit 1, which could conceal a crash;
it now requires a fixture assertion failure and a failure-only unittest summary.
Failed attempts are retained in the earlier verification evidence.
