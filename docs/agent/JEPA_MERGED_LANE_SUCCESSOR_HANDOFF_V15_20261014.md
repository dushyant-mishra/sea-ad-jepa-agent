# JEPA merged lane successor handoff V15 — 2026-10-14

Status:
`TASK0_EXACT_HEAD_GREEN__INDEPENDENT_ACCEPTANCE_PENDING__DOWNSTREAM_REUSE_FIRST_A_T_PROGRAM_FROZEN_IN_ANALYSIS__EXACT_HISTORICAL_TEST_SCOPE_CUSTODIED__UNIFIED_TASK1_BLOCKED`

Binding authority:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Read first

Canonical audit/custody PR #322 exact audit head:
`5378f54bcf05c8a76ef7546d260528453d3bae0c`

Current downstream surfaces:
- `docs/agent/DOWNSTREAM_QUALIFICATION_DELTA_FROM_HISTORICAL_AUDITS_V1_20261014.md`
- `docs/agent/DOWNSTREAM_QUALIFICATION_EVIDENCE_REUSE_GUIDE_V1_20261014.md`
- `results/target_discovery/unified_qualification_v1/DOWNSTREAM_QUALIFICATION_EVIDENCE_REUSE_MATRIX_V1.json`
- `results/target_discovery/unified_qualification_v1/DOWNSTREAM_HISTORICAL_EXACT_ASSET_LEDGER_V1.json`
- `results/target_discovery/unified_qualification_v1/DOWNSTREAM_HISTORICAL_EXACT_ASSET_LEDGER_DELTA2_V1.json`
- `results/target_discovery/unified_qualification_v1/DOWNSTREAM_HISTORICAL_EXACT_ASSET_LEDGER_DELTA3_V1.json`
- `results/target_discovery/unified_qualification_v1/DOWNSTREAM_HISTORICAL_TEST_EVIDENCE_DELTA_V1.json`
- `results/target_discovery/unified_qualification_v1/DOWNSTREAM_QUALIFICATION_STATUS_MATRIX_V1.json`
- `results/target_discovery/unified_qualification_v1/DOWNSTREAM_UNRESOLVED_WORK_LEDGER_V1.json`
- `docs/agent/UNIFIED_DOWNSTREAM_QUALIFICATION_PROGRAM_AMENDMENT_CANDIDATE_V1_20261014.md`
- `docs/superpowers/plans/2026-10-14-downstream-qualification-program-v1.md`
- `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`

Task 0 / synthetic custody remains:
- Task 0 exact review candidate `c80d7398b41f10208ec1622bc52599383b940be6`;
- old synthetic Task1/2 exact head `ff597faf2182522a320ec5322f8db9b67c9c6094`;
- old Tasks 3–4 stopped/migrate-only;
- unified Task 1 blocked pending independent Macha acceptance.

## Downstream current truth

A teacher/student/predictor/EMA architecture exists and substantial mechanics are historically tested.

The current merged system is **not** fully qualified. Specifically:
- exact TQB-bound teacher: false;
- exact TQB-bound student: false;
- exact target-query shortcut authority: unresolved;
- final masking authority: unresolved;
- final model/protected registry: unresolved;
- current joined teacher/student/EMA runtime: false;
- current EMA timescale: unresolved;
- downstream certification: false;
- runtime eligibility: false;
- training eligibility: false;
- training authorization: false.

## Historical work already done — do not repeat

Classify every new claim first as:
`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`.

Already audited/scoped mechanics include:
- T1/C2 zero-gradient causal defect and corrected update order;
- EMA only after proved optimizer step;
- exact-copy/eval/no-grad teacher mechanics;
- F1-B optimizer/receipt guard pattern;
- checkpoint/RNG/schedule/EMA chronology;
- protected-population firewall;
- observation-state gradient firewall;
- data/target/proposal/packing authority separation;
- donor-primary target and relational V2 repair;
- p/q correction doctrine;
- FULL104 support/population geometry;
- context/visibility/within-donor audits;
- target-query shared identity path discovery;
- six-block/48-tensor/128×8 preexecution carryover defect discovery;
- common-core/biology semantic carryover audit;
- historical `.996` EMA not being current authority.

## Exact recovered downstream assets

Target-identity draft:
- `d9a678f261797f5dfc7a6e6b7a281e413ae7e0ae`
- `docs/agent/V5_TARGET_IDENTITY_SHORTCUT_AUDIT_SPEC_DRAFT_20260915.md`

Historical target-query code path:
- `src/sea_ad_jepa/v4/ipb_jepa.py`
- historical tree `c2bd13e8389dd25dc61612ef2aea88dc53099029`
- `BlockPredictor.block_queries()` uses target gene-identity embeddings.

V5 objective draft:
- `docs/agent/V5_TEACHER_STUDENT_OBJECTIVE_AUTHORITY_DRAFT_20260915.md`
- blob `d1dc4f6041ada842cb585ef14004530221f4866e`

Inactive V5 one-update reference:
- `src/sea_ad_jepa/v5/inactive_update_reference.py`
- blob `3dc61b629c1d4723e7df058f72c1497c4b4c6c20`
- proves packing/weight preservation, no teacher gradients, one optimizer step, EMA after step, deterministic replay and reference checkpoint/resume mechanics;
- explicitly not production/runtime/training authority.

Keyed-dropout reference:
- `src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py`
- blob `0fd06ae0891625924761ef097b20ba6e11495cb3`
- identity-addressed reference randomness; not production GPU kernel authority.

Preexecution carryover finding:
- commit `0f5e5ad21c7895444d2804897f87a2cd2bb04e16`
- `docs/agent/V5_PREEXECUTION_CARRYOVER_REDTEAM_20260915.md`

Hard-coded negative-control implementation:
- `src/sea_ad_jepa/v5/trainer_preexecution_contract_v2.py`
- blob `8a861f13bc0e020d323803d7949613737078d984`
- mechanics ordering reusable; literal 6/48/128×8 authority forbidden.

Depth-derived registry pattern:
- `src/sea_ad_jepa/v5/production_protected_registry_authority_v1.py`
- blob `d6b46738a9cd99b5e42f577c934954336c8e7145`

Current-registry checkpoint pattern:
- `src/sea_ad_jepa/v5/atomic_checkpoint_guard_v3.py`
- blob `f1f3ed3b46faa202a9f2131150fae5b1ed14530d`
- useful pattern but still needs current neutral authority rebinding.

Semantic/scope carryover audit:
- commit `88c45b97b3e9a4ad3c0fd178c992f844fd58dbab`
- `docs/agent/V5_SEMANTIC_AND_SCOPE_CARRYOVER_AUDIT_20260915.md`

## Exact historical test scope recovered

`tests/test_teacher_student_v5_inactive_update_reference.py`
blob `68b6d265e2a5be61d352ca967fc4e21fa94f3a8f`

Demonstrates historically:
- one optimizer step;
- no teacher gradients;
- exact EMA equation at caller-supplied momentum;
- deterministic replay;
- packing budget cannot change selected cells or scientific weight mass;
- checkpoint/resume matches uninterrupted two-update path;
- cursor/step mismatch fails closed.

It does **not** qualify the current production GPU runtime, current protected registry, current TQB-bound runtime, or EMA half-life.

`tests/test_teacher_student_v5_scientific_target_v2.py`
blob `b0df4f9b26583fbf8f59172f14193ae52334273e`

Demonstrates historically:
- donor-uniform base target;
- operator not base scientific mass;
- relational operator as admissibility boundary;
- no O(n^3) triplet-capacity weighting;
- historical TD57B/59/60 boundary not rewritten;
- old equal-operator V1 target superseded;
- common-core data support with numeric student schedule still unfrozen.

It does **not** establish exact current TQB target semantics, current q/horizon/masking, or execution/training authority.

## Prospective downstream governance

Amendment candidate:
`docs/agent/UNIFIED_DOWNSTREAM_QUALIFICATION_PROGRAM_AMENDMENT_CANDIDATE_V1_20261014.md`

Prospective plan:
`docs/superpowers/plans/2026-10-14-downstream-qualification-program-v1.md`

The current Task 8 must eventually become A–Q qualification packages, followed by:
- R `RUNTIME_ELIGIBILITY_RECEIPT_V1`;
- S independent project-scope `TRAINING_ELIGIBLE` review;
- T explicit owner `TRAINING_AUTHORIZED`.

This is not controlling until Task 0 acceptance and formal prospective amendment of PR #380.

## Next legal event

Macha independent review of exact:
- Task 0 `c80d7398b41f10208ec1622bc52599383b940be6`;
- old Task1/2 `ff597faf2182522a320ec5322f8db9b67c9c6094`.

Until then, allowed work is historical custody, exact-asset recovery, no-repeat classification, prospective schemas/tests and handoff synchronization only.

No candidate outcomes, protected validation/oracle values, unified Task 1 implementation, downstream authority implementation or training.
