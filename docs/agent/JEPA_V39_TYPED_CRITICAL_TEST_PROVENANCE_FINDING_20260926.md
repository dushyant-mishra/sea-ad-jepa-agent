# V39 typed critical-test evidence provenance red-team (non-authorizing)

Date: 2026-09-26. Stacked on draft PR #165 V36 guard repair at `25447126e3cf269b8416b52b1bbb98deebaa5d64`. Main V25 unchanged. No real experiments, model updates, external execution, protected outcomes or scientific authority roots are opened.

## Independent distinction from V30/V34/V36

V30 showed the real issuer could accept an entirely invented digest graph. V34 now requires the actual typed closure validator, and V36 requires guard-side reissuance. Those repairs are not the same as evidence that the *parents* were physically authenticated. This targeted V39 review inspects **the real typed** `CriticalTestExecutionAuthorityV1`, not V30's toy `SyntheticCritical`.

The current V1 critical-test class accepts any caller-declared, unique nonempty `required_test_ids` list, any syntactically valid lower-case SHA-256 value for `test_suite_source_sha256`, and `EXECUTED_PASS` status per caller-declared test ID. It validates self-consistency of those fields, but it does NOT fetch source bytes, require an independently frozen complete critical-test manifest, read actual test-run logs/JUnit outcomes, bind to a runner/commit/environment, or authenticate a CI event. A separately checked source root is required for stronger provenance. The existing V2 closure's `_auth` helper also permits duck-typed `critical_test` objects with a `validate()` method and `canonical_digest()` rather than demanding this type.

Seven explicitly scoped tests physically exercise those behaviors and positive safety controls: fake type-valid `EXECUTED_PASS`, caller-selected subset, unread synthetic source SHA, duck-typed `_auth` acceptance, and correct rejection of failed status/missing status/malformed SHA. The *full* current V2 closure is not tested with a valid scientific graph; no current training authorization is demonstrated or possible from these tests. A green V39 diagnostic is an OPEN finding, not closure.

## Proposed versioned correction — not implicitly authorized

Define a successor **independent critical-test evidence contract** before allowing B2: a scientist/reviewer-frozen exact required suite/test-ID manifest; exact source and runner commit SHA, original test byte hashes, environment and job identity; materialized original machine results (JUnit IDs, executed count, skips/errors/failures, required pass assertions) tied to an authenticated immutable CI run or separately trusted executor; and fail-closed evidence review that compares real externally obtained data to the purported receipt. Merely adding JSON fields or having a caller compute a new digest is not physical attestation. Make the closure graph require that specific successor **only after** a separate reviewed type/semantic migration with all dependent code/tests and actual evidence bytes; preserve V1 and V2 historical semantics and original prior results.

The current V36 issuer/guard repair remains valuable but insufficient for full B2. Critical source/event evidence is an upstream OPEN root. Training OFF; full `0/33` authority closure; no hidden source root or status silently promoted.
