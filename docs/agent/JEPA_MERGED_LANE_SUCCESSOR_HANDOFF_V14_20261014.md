# JEPA merged lane successor handoff V14 — 2026-10-14

Status:
`TASK0_EXACT_HEAD_GREEN__INDEPENDENT_ACCEPTANCE_PENDING__DOWNSTREAM_REUSE_FIRST_PROGRAM_AND_EXACT_ASSET_LEDGER_FROZEN__UNIFIED_TASK1_BLOCKED`

Binding authority:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Current read-first audit state

PR #322 audit/custody branch:
`science/jepa-robust-pipeline-post-jepa-anything-audit-20261013`

Current exact audit head:
`41aa7aed8714467c855794b9a24c1265edbd936a`

Read in this order:
1. `docs/agent/JEPA_MERGED_LANE_MASTER_AUDIT_INDEX_V1_20261014.md`
2. `results/target_discovery/JEPA_MERGED_LANE_AUDIT_STATE_V2_20261014.json`
3. `docs/agent/DOWNSTREAM_QUALIFICATION_DELTA_FROM_HISTORICAL_AUDITS_V1_20261014.md`
4. `docs/agent/DOWNSTREAM_QUALIFICATION_EVIDENCE_REUSE_GUIDE_V1_20261014.md`
5. `results/target_discovery/unified_qualification_v1/DOWNSTREAM_QUALIFICATION_EVIDENCE_REUSE_MATRIX_V1.json`
6. `results/target_discovery/unified_qualification_v1/DOWNSTREAM_HISTORICAL_EXACT_ASSET_LEDGER_V1.json`
7. `results/target_discovery/unified_qualification_v1/DOWNSTREAM_HISTORICAL_EXACT_ASSET_LEDGER_DELTA2_V1.json`
8. `results/target_discovery/unified_qualification_v1/DOWNSTREAM_QUALIFICATION_STATUS_MATRIX_V1.json`
9. `results/target_discovery/unified_qualification_v1/DOWNSTREAM_UNRESOLVED_WORK_LEDGER_V1.json`
10. `docs/agent/UNIFIED_DOWNSTREAM_QUALIFICATION_PROGRAM_AMENDMENT_CANDIDATE_V1_20261014.md`
11. `docs/superpowers/plans/2026-10-14-downstream-qualification-program-v1.md`
12. `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`
13. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260915_V5_TARGET_AUTHORITY_CURRENT.md`
14. `docs/agent/MACHA_TASK0_FINAL_INDEPENDENT_REVIEW_PACKET_V1_20261014.md`

## Task 0 / old synthetic state

PR #381 exact independent-review candidate:
`c80d7398b41f10208ec1622bc52599383b940be6`

Exact-head CI:
- focused `38645994312`, job `116132861396`: SUCCESS, `29 passed in 0.07s`;
- inherited `38645994388`: SUCCESS.

Old synthetic Task1/2 exact head:
`ff597faf2182522a320ec5322f8db9b67c9c6094`

Controller review PR #382:
- focused `38644641042`, job `116128364543`: `332 passed in 8.94s`;
- inherited `38644640881`: SUCCESS.

Old Tasks 3–4 remain `STOPPED_AFTER_MERGER__REQUIREMENTS_MIGRATE_ONLY`; old Tasks 5–12 have no independent continuation.

Unified Task 1 remains blocked until fresh Macha review accepts exact Task 0 + old Task1/2 custody.

## Downstream qualification — current doctrine

Do not restart historical downstream audits. Every proposed claim is first classified as:
`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`.

Teacher/student/EMA architecture exists. Strong historical mechanics exist. But no current merged receipt qualifies the whole exact TQB-bound teacher/student/EMA system.

Current conservative status:
- exact TQB-bound teacher qualified: **false**;
- exact TQB-bound student qualified: **false**;
- joined current teacher/student/EMA runtime qualified: **false**;
- current EMA timescale qualified: **false**;
- downstream certified: **false**;
- runtime eligible: **false**;
- training eligible: **false**;
- training authorized: **false**.

## Exact historical assets recovered during reuse-first audit

### Target identity/query shortcut

Draft threat model:
- commit `d9a678f261797f5dfc7a6e6b7a281e413ae7e0ae`
- `docs/agent/V5_TARGET_IDENTITY_SHORTCUT_AUDIT_SPEC_DRAFT_20260915.md`

It already defines comparator/control families for shared/fixed target-address codes, identity-only/full memory, stop-grad identity, target-ID shuffle and cell-memory shuffle. Do not reinvent the shortcut audit.

Historical target-query code path:
- `src/sea_ad_jepa/v4/ipb_jepa.py` at historical tree `c2bd13e8389dd25dc61612ef2aea88dc53099029`
- `BlockPredictor.block_queries()` consumes the supplied gene-identity embedding for hidden target addresses.
- historical tests include `tests/v4/test_stage81a3_ipb_jepa.py`.

This is a shortcut authority problem, not evidence of hidden-expression leakage.

### Preexecution carryover defect

Exact red-team finding:
- commit `0f5e5ad21c7895444d2804897f87a2cd2bb04e16`
- `docs/agent/V5_PREEXECUTION_CARRYOVER_REDTEAM_20260915.md`

Negative-control implementation:
- `src/sea_ad_jepa/v5/trainer_preexecution_contract_v2.py`
- blob `8a861f13bc0e020d323803d7949613737078d984`
- branch `planning/v5-teacher-student-ema-canonical-20260915`

It contains historical six-block/48-tensor/128×8 authority vocabulary. Preserve its mechanics-chain order and fail-closed patterns but do not use those geometry-specific constants as current authority.

### Protected registry / checkpoint successful patterns

Depth-derived registry:
- `src/sea_ad_jepa/v5/production_protected_registry_authority_v1.py`
- blob `d6b46738a9cd99b5e42f577c934954336c8e7145`

Checkpoint guard:
- `src/sea_ad_jepa/v5/atomic_checkpoint_guard_v3.py`
- blob `f1f3ed3b46faa202a9f2131150fae5b1ed14530d`

Use the depth-derived current-registry pattern. Checkpoint V3 is a useful pattern but still imports part of the old preexecution V2 authority vocabulary and therefore requires current rebinding.

### Semantic/scope carryover

Exact audit:
- commit `88c45b97b3e9a4ad3c0fd178c992f844fd58dbab`
- `docs/agent/V5_SEMANTIC_AND_SCOPE_CARRYOVER_AUDIT_20260915.md`

Permanent laws:
- `NAMES_DO_NOT_CREATE_CAUSAL_OR_BIOLOGICAL_AUTHORITY`;
- common-core support is comparability, not biological truth;
- native support is not automatically private biology;
- dimension-estimand authority != base-training-estimand authority;
- D_shared qualification-rank ceiling != production model width;
- observation gradient firewall != proof of measurement-free primary state.

## Prospective downstream plan amendment

Candidate:
`docs/agent/UNIFIED_DOWNSTREAM_QUALIFICATION_PROGRAM_AMENDMENT_CANDIDATE_V1_20261014.md`

This is **not yet controlling**. After Task 0 acceptance it should prospectively amend PR #380 before downstream implementation reaches the affected work.

It expands compressed Task 8 into packages A–Q plus later R–T lifecycle gates:
- A–P: scientific/mechanical qualification packages;
- Q: downstream certification finalizer;
- R: runtime eligibility receipt;
- S: independent project-scope training eligibility review;
- T: explicit owner training authorization.

The exact prospective implementation plan is:
`docs/superpowers/plans/2026-10-14-downstream-qualification-program-v1.md`

## Current dependency ledger

Machine ledger:
`results/target_discovery/unified_qualification_v1/DOWNSTREAM_UNRESOLVED_WORK_LEDGER_V1.json`

None of A–T is currently lawful to implement as authority-bearing code before Task 0 acceptance. Work allowed now is limited to custody, exact historical-asset recovery, no-repeat classification, prospective schema/test design and handoff synchronization.

## No-repeat rule

Before any new downstream analysis:
1. read `JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`;
2. search V4/V5 active-test manifests;
3. check exact-asset ledgers;
4. port/rebind an existing attack if equivalent;
5. write new audit logic only for a genuinely new current-input/authority claim.

Do not repeat zero-gradient archaeology, EMA chronology discovery, architecture recovery, FULL104 census, visibility/context audits, QID semantic defect discovery, target-identity path discovery, preexecution 48-tensor carryover discovery, or common-core/biology semantic audits.

## Next legal event

Macha must independently review exact:
- Task 0 `c80d7398b41f10208ec1622bc52599383b940be6`;
- old Task1/2 `ff597faf2182522a320ec5322f8db9b67c9c6094`.

Until accepted:
- no unified Task 1 implementation;
- no old synthetic Task 3/4 restart;
- no authority-bearing A–T implementation;
- no candidate outcomes;
- no reader_validation/oracle value access;
- no training.
