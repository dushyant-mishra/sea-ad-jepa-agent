# Macha — next target-discovery instruction: comprehensive G6/G7 custody repair

Status: `TEST_FIRST_REPAIR_REQUIRED__NO_VALUE_AUTHORITY__NO_G6_G7_EXECUTION`

Controlling audit:
`docs/agent/TD_MACHA_TARGET_DISCOVERY_FULL_SCRIPT_OUTPUT_AUDIT_20261011.md`

Accepted upstream evidence remains PR #259 only in its narrow value-blind G4/G5 sense:
- execution head `80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`
- executed code `bf253a4dd62d943398f9ff59ed8b1e74777140a5`
- exact driver SHA `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`
- exact mapping SHA `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`
- replay manifest SHA `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`

PR #267 remains blocked. PR #268 head `d8fa3024e06e265b77353c8382453e7ccbf2350f` preserves a valid RED regression for the G7 concurrency race, but is now scope-incomplete.

## Assignment

Create a fresh successor branch from exact PR #268 RED head:
`d8fa3024e06e265b77353c8382453e7ccbf2350f`

Suggested branch:
`fix/td-g6g7-full-custody-successor-20261011`

Do not modify PR #267 or erase PR #268 RED history.

Use strict test-first development. Before each production repair, add focused regression coverage and demonstrate the intended RED against the inherited implementation. Preserve the RED logs. Then implement the smallest repair and demonstrate GREEN.

## Required repairs

1. Runtime authorization must require and cryptographically verify an immutable owner-decision record contract. The code must verify dedicated decision schema, exact decision `AUTHORIZE_G6_G7_INTEGRITY_ONLY`, record physical SHA, exact PR #259 driver/mapping physical SHAs, exact implementation identity, and downstream false gates. Tests may use synthetic decision fixtures. Do **not** create a real owner decision or real runtime authorization.

2. Runtime authorization must reject any preflight/mapping receipt pair whose physical SHA is not exactly the accepted PR #259 driver/mapping SHA above, even if the JSON is semantically equivalent or the runtime authorization was constructed to match the altered bytes.

3. G6 execution-start spending must be atomic/exclusive. Add deterministic concurrent-start coverage proving exactly one successful starter and one rejection, including the pre-existing-empty-directory case.

4. G7 attempt-start spending must be atomic/exclusive. Retain and satisfy the PR #268 concurrent single-winner regression.

5. G7 must require a genuine complete same-authority G6 PASS execution. Strengthen `load_g6_pass_receipt()` or an equivalent gate to validate a minimum complete G6 receipt/materialization contract: exact authority trace, exact input authority hashes, required row/coverage semantics, values/meta artifact hashes and existence, manifest linkage, spent G6 execution-start marker, and false downstream gates. Add negative tests for fabricated/minimal PASS receipts and changed materialized artifacts.

6. `nph_historical_row()` must reject duplicate CSR address indices before dictionary materialization. Preserve the already-audited historical pass-through bytes; do not change historical values.

7. G6 receipt semantics must distinguish:
- 23,690 HVS/SEA rows physically reread and library-total verified;
- 1,310 NPH52 authenticated historical pass-through rows;
- 25,000 total covered Sample-A rows.
Do not describe all 25,000 as independently physical-reread source-library rows.

8. Preserve strict raw-count semantics. Do not introduce `round()` into V2 G6/G7. Fractional, negative, NaN and infinite physical/S174 counts must remain rejection conditions.

9. Preserve every existing PR #267 protection: exact G1b authority, immediate S174 meta/count reauthentication, duplicate S174 cell rejection, duplicate S174 CSR rejection, physical H5 counterpart authentication before S174 count loading, exact 9,216 replay-address comparison, zero mismatch tolerance, natural overlap only, and non-success semantics for mismatch/NOT_ESTIMABLE.

## Upstream S174 numerical assumption

The older S174 builder/probe/G1b lane rounded physical values before comparison. Do not rewrite historical S174 evidence or relabel its G1b result. The target-discovery V2 path must instead retain its own strict raw-integrality validation before using S174/physical overlap values. If strict validation fails on real bytes later, preserve that failure and STOP.

## Qualification after GREEN

Only after all required repairs have GREEN focused tests, qualify the new exact successor head from a fresh clean worktree.

Qualification must include at least:
- all current V2 common/G6/G7 tests;
- PR #268 concurrent G7 regression;
- new G6 concurrent single-winner regression;
- owner-decision binding negative/positive synthetic tests;
- exact-PR259-physical-SHA rejection/acceptance tests;
- complete-G6-receipt/materialization negative/positive tests;
- NPH duplicate-index rejection;
- exact PR #259 real-receipt compatibility test with exactly `1 passed / 0 skipped / 0 failed` using the original physical CRLF-containing bytes;
- static base-to-head changed-file inventory;
- full environment/version record.

Open an evidence-only draft qualification PR/head and preserve RED/GREEN logs plus exact hashes.

## Explicitly forbidden

Do not:
- create a real owner-decision record;
- create a real `JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2`;
- execute G6 or G7 against corrected real values;
- open corrected expression/count arrays as part of qualification;
- run corrected TD56/TD57B/TD57C/TD59/TD60;
- select a target;
- train anything;
- modify historical failure evidence or historical TD57C FAIL semantics.

Routine engineering and qualification do not require an owner checkpoint. After a genuine qualified successor exists, STOP at the value-read authority boundary and return all evidence to the coordinator.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
