# Controller audit of Macha old synthetic Tasks 1–2 — V1 — 2026-10-14

Reviewed implementation branch:
`implementation/production-synthetic-v3-1-1-20261014`

Observed exact head:
`ff597faf2182522a320ec5322f8db9b67c9c6094`

Status:
`SUBSTRATE_REUSE_CANDIDATE__NOT_YET_ACCEPTED_AS_COMPLETED_TASK1_OR_TASK2__NO_UNIFIED_PROMOTION`

Global authority remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Branch/custody state

Compared with accepted old #356 plan head `2c2723a1a731e7a848196aef3f7c4ab965e9ff6a`, the implementation branch is diverged: 13 commits ahead, 2 commits behind, merge base `befd95c20d1946f1026ac49462669f34b97f9607`.

The two missing plan commits add execution-support documentation only:
- `2026-10-14-production-synthetic-post-macha-real-lane-dependency-delta.md`
- `2026-10-14-production-synthetic-tasks-1-3-execution-handoff.md`

The implementation branch does inherit `befd95c...`, which already binds the accepted F1/N3–N6 addendum. Therefore the divergence is a custody/review-state issue, not evidence that the core controlling specs were omitted. Before final acceptance, however, the exact reviewed head must explicitly reconcile the later handoff obligations and current controller instruction to STOP after old Task 2.

No PR was found for this implementation branch, and no PR-triggered GitHub Actions workflow run was found at exact head `ff597faf...`. Therefore exact-head CI/fresh-review completion evidence is currently absent from the GitHub surface inspected here.

A local checkout/test attempt from this environment failed before checkout because outbound DNS access to github.com is unavailable. This is an environment limitation, not test evidence. No local PASS is claimed.

## 2. Files present

Relative to the old plan lineage, the branch adds only Task 1/2 implementation and tests:
- `scripts/production_synthetic/canonical_v1.py`
- `scripts/production_synthetic/custody_v1.py`
- `tests/production_synthetic/custody_fixtures_v1.py`
- `tests/production_synthetic/test_canonical_v1.py`
- `tests/production_synthetic/test_custody_v1.py`
- `tests/production_synthetic/test_custody_v1_hostile.py`

No old Task 3 or Task 4 implementation file is present in this compare, consistent with the current controller instruction to stop after Task 2.

## 3. Task 1 review

### Positive findings

The canonical module is unusually explicit and suitable as a reuse candidate:
- byte-level canonical JSON format is specified in the module;
- NaN/Inf rejected;
- `None` is distinct from measured zero;
- bool/int and int/float distinctions are explicit;
- negative zero normalization is explicit;
- raw transport SHA and semantic SHA are separate/domain-separated;
- strict JSON loader rejects duplicate keys, nonfinite constants, overflow and nonzero-underflow-to-zero;
- text and JSON-file semantic identities are explicit rather than type-guessed;
- identity-key duplicates/missing identity are fail-closed;
- the 41,238 registry has an explicitly order-sensitive digest;
- a separate semantic row-set digest is explicitly order-invariant to row/shard reorder;
- known-answer and permutation tests distinguish these two concepts.

The apparent plan tension between “registry ordered content” and “storage/shard reorder invariance” is resolved by separate objects:
- `ordered_registry_digest` for coordinate/order-bearing registries;
- `semantic_row_set_sha256` for scientifically keyed unordered row sets.

That is coherent, provided downstream schemas explicitly choose the correct identity type rather than using either interchangeably.

### Migration classification

Current classification: `ADAPT_AND_WRAP`, potentially `DIRECT_REUSE` after exact-head test/review verification.

Reasons it should not simply become the unified global canonical module unchanged:
- semantic domain prefixes are named `JEPA-PRODUCTION-SYNTHETIC-*`, while unified authority spans TD/known-truth/downstream;
- unified Task 1 additionally requires recursive receipt verification, parent/dependency-chain verification and authority-state types that this module correctly does not implement;
- final migration must guarantee one canonical serializer/digest law, not two nearly identical implementations.

Preferred migration: preserve/freeze these byte semantics and known-answer vectors; either import this exact primitive from a shared neutral module or move it byte-for-byte into the unified shared layer with an explicitly governed domain-version decision. Do not reimplement from prose.

### Open acceptance evidence

Before Task 1 is accepted as old-task complete:
- exact pytest output at the frozen head;
- exact RED lineage and GREEN head;
- fresh reviewer verdict/no open Critical or Important finding;
- reconcile branch with the old execution-handoff obligations without changing accepted scientific bytes merely for history shape.

## 4. Task 2 review

### Positive findings

The custody implementation covers substantially more hostile surface than the minimal brief:
- generator freeze binds source/dependencies/registries/distributions/mechanism mixture/calibration/applicability/serialization/difficulty/challenges/budgets;
- withheld commitment is nonce-salted and hash-cycle handling is explicit;
- nonce floor >=256 bits;
- scientific RNG streams are identity-keyed and reject integer seed/offset namespaces;
- storage traversal order is not the RNG identity;
- append-only hash-chained ledger with replayed state-machine validation;
- exact exposure/fit-output/reveal chronology;
- reveal refused before all required fit outputs are frozen;
- strict linear successor lineage;
- post-exposure successor/requalification semantics;
- no-change rerolls/public-family reuse protections added through later repair commits;
- method identity is digest-bound and qualification draws are counted both per method and over the whole lineage;
- secret scanning covers multiple raw/base64/hex/decimal/list/wrapped representations without echoing matching secrets/paths;
- no-unique-withheld-public-code-path attestation;
- caller-secret/error no-echo policy.

### Critical migration obligations explicitly deferred by Task 2

The module itself correctly states that several properties require later packaging/qualification/finalizer authority. These must be preserved as explicit unified prerequisites:
1. one externally anchored genesis ledger per testbed;
2. externally published ledger head after every entry and expected-head verification on load;
3. both per-method and lineage-wide qualification draw reporting/multiplicity accounting;
4. `withheld_check_eligible` is final only after reveal;
5. regenerate each realization after reveal and verify content SHA;
6. secret scans must operate on full exact committed-tree exports for every published commit, not sparse/dirty working copies;
7. defect-record truth requires independent reviewer audit.

These obligations map mainly to unified Tasks 4, 9, 11 and 12. They must not disappear because the Task 2 unit tests are green.

### Migration classification

Current classification: `ADAPT_AND_WRAP`, with several primitives likely `DIRECT_REUSE` after exact test/review evidence.

It does **not** satisfy unified Task 2. Unified Task 2 is the TD execution manifest/population-access law. This Task 2 is challenge custody/RNG and maps primarily to unified Task 4 plus later challenge/finalizer audit obligations.

### Open acceptance evidence

Before old Task 2 is accepted as complete:
- exact pytest output at a frozen head;
- fresh reviewer verdict/no open Critical or Important finding;
- exact branch/head freeze;
- explicit statement that no real withheld spec/nonce was committed;
- full-tree secret-scan evidence or a clear statement that only fixture scan tests were run and production scan remains future controller work;
- no Task 3/4 continuation.

## 5. Controller verdict

`TASK1_CODE_HIGH_QUALITY_REUSE_CANDIDATE__TASK2_CUSTODY_HIGH_VALUE_REUSE_CANDIDATE__EXACT_REVIEW_AND_CI_EVIDENCE_MISSING__BRANCH_DOC_DIVERGENCE_MUST_BE_RECONCILED__DO_NOT_PROMOTE_OR_START_TASK3`

This audit is sufficient to eliminate rediscovery work when Macha returns. The next return package does not need a narrative reconstruction; it only needs exact frozen head, RED/GREEN evidence, review verdict and any changes after `ff597faf...`.
