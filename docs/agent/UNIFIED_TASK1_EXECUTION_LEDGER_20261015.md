# Unified Task 1 execution ledger — 2026-10-15

Base/freeze: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`.
Controlling plan: PR #380 head `5b6bf07e7d8b69b286ea430b09765a5ee4743325` plus frozen Task 0 custody.
Authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## Carry-forward blockers

Unified Task 1 begins prospectively only after Task 0 acceptance. Old Tasks 1–2 are ADAPT_AND_WRAP substrate only, never completed unified work. Carry forward `U_TASK1_3_FOUNDATION`, O1–O8, D1 exception-wrapping, E2 precommitment erratum, post-reveal fresh-family design, and reader-fit calibration-status questions as blocking dependencies for any same-code-path or later qualification use.

Macha non-blocking carry-forward remains:
- N1: refuse identity-unavailable records until exact bytes are bound;
- N2: bind old Tasks 1–2 test-file blobs;
- N3: mixed-parent effective classification comes from the decomposition record;
- N4: one-shot Task 0 repair scripts must be labelled historical before later reuse.

## Reuse evidence

Old Task 1 implementation: `ff597faf2182522a320ec5322f8db9b67c9c6094:scripts/production_synthetic/canonical_v1.py`, blob `b8a34d8d47f618e7dcde1b3e5c53584701294561`.
Old Task 1 tests: `ff597faf2182522a320ec5322f8db9b67c9c6094:tests/production_synthetic/test_canonical_v1.py`, blob `0bce5cbdde37112f316ffc1386342b34c0ed4d41`.
These establish tested canonical byte behavior and known-answer compatibility; they do not establish the new recursive scientific-receipt or unified-authority semantics.

Machine custody: `results/target_discovery/unified_qualification_v1/UNIFIED_TASK1_REUSE_SUBSTRATE_V1.json`.

## Rulings

Ruling: preserve the old Task 1 canonical byte rules rather than invent a second serializer — this preserves semantic distinctions such as measured zero vs missing and avoids needless byte-semantic churn. Unified receipt identities use a new explicit V1 hash domain/schema; old synthetic identity prefixes are not silently reinterpreted as new authority.

Ruling: a digest string is never scientific authority. A1 verification therefore reserializes/re-hashes the receipt payload, every declared input, every parent receipt, and the output/manifest/registry/access-policy dependency roots. `producer_code_sha` remains an exact 40-hex Git identity rather than a canonical scientific-object digest.

Ruling: Task 1 does not consume any candidate outcomes or protected partitions. All tests use synthetic dictionaries and dummy/exact local identities only.

## Iterative RED/GREEN/self-audit record

### Cycle 0 — initial prospective RED

PR #385 began with tests and no unified implementation modules.
RED head: `3ecad1c12f20d9e564698cc553c7240742896f97`.
Run `38668789110`, job `116206724828`: RED during collection because `canonical_v1` and `authority_v1` did not yet exist. This established that the new tests were not accidentally satisfied by historical code.

Initial implementation introduced canonical bytes, scientific receipts, recursive parent verification, the authority enums/record, and closed schemas. First A1/A9 GREEN was observed at head `8949e0653c02286cefd2d7e8bf8c6d9c5713a7c4`, run `38668916891`, job `116207135721`.

### Cycle 1 — hostile authority-scope audit

Finding: A9 initially searched for the substring `TRAINING` in authority scope. That incorrectly rejected an explicit negative scope such as `UNIT:G8__NO_TRAINING_AUTHORITY`.

RED head: `a49cc6f35050f49877eaf4509765d9221c344c93`.
Run `38669103645`, job `116207724967`: `1 failed, 14 passed`; the negative-scope hostile test failed for the intended reason.

Repair: only explicit reserved positive training/project scopes can imply training/project authority. Negative labels no longer self-promote or falsely fail.
Repair commit: `e3b85626dae975706e81003eef0b6e05eb406d35`.

### Cycle 2 — hostile declared-input audit

Finding: A1 recomputed the receipt/payload and recursively verified parent receipts, but `input_shas` were still trusted as strings.

RED head: `089f11497406fea80428d7a8f459c034eae6bbf7`.
Run `38669293382`, job `116208336215`: `1 failed, 15 passed`; a missing input object was incorrectly accepted.

Repair: every input identity is resolved through the supplied resolver and independently recomputed. Receipt-shaped inputs are recursively verified and must resolve to the exact requested receipt identity.
Repair code commit: `6368342a60f4044f59677a63e2d50d23a3831421`; hostile fixture follow-up: `18bafd2376c64b63e0d1f31a37cd5aebb914adf6`.
A1/A9 run `38669511152`, job `116209044025`: GREEN on that candidate.

### Cycle 3 — hostile authority-dependency audit

Finding: output, manifest, registry, and access-policy SHA fields were receipt-bound but their underlying objects were not independently resolved/re-hashed. This violated the accepted no-trusted-digest rule for authority-bearing dependencies.

RED head: `9eca781de0c65c0cf848456cb4fb738cae3ca395`.
Run `38669613609`, job `116209370034`: `1 failed, 17 passed`; removing one authority dependency did not invalidate verification.

Repair: output, manifest, registry, and access-policy roots are now resolved and independently re-hashed; receipt-shaped dependencies recurse through the same verifier. Valid test fixtures now bind to actual synthetic dependency objects rather than dummy hash strings.
Repair code commit: `739ac3b5eca7c5b19a243dfaa291ead1317dbfe4`; fixture/hostile-test follow-up: `791ba5cf80142820f3bd6163eba1da6bff2cf785`.
A1/A9 run `38669744861`, job `116209802273`: focused test step GREEN on the repair candidate.

## Current review posture

Task 1 A1+A9 is **not frozen and has no independent acceptance yet**. Before any freeze claim:
1. verify focused A1/A9 CI on the exact review head;
2. verify inherited unified synthetic integration on the same exact head;
3. verify inherited Task 0 custody/audit checks remain green;
4. run a final whole-branch hostile diff review;
5. send the exact head to Macha for independent Task 1 adjudication.

## Iterative protocol

Each Task 1 change follows RED -> intended failure confirmation -> minimal GREEN -> inherited compatibility/regression -> hostile self-audit -> fix/repeat -> exact-head CI -> independent review before freeze.
