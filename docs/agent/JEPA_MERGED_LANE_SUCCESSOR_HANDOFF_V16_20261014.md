# JEPA merged-lane successor handoff V16 — 2026-10-14

Status: `TAKEOVER_READY__GPU_EXECUTION_HISTORY_RECOVERED__TASK0_INDEPENDENT_REVIEW_PENDING__UNIFIED_TASK1_BLOCKED`

Binding authority remains exactly:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Read first

1. PR #322 canonical audit/custody surface.
2. `docs/agent/JEPA_NEW_AGENT_TAKEOVER_MANIFEST_V1_20261014.md` on PR #322.
3. `docs/agent/JEPA_COMPLETE_TAKEOVER_AUDIT_MANIFEST_V1_20261014.md` on PR #322.
4. `docs/agent/JEPA_SUCCESSOR_FIRST_24_HOURS_CHECKLIST_V1_20261014.md` on this branch.
5. `docs/agent/JEPA_MERGED_LANE_MASTER_AUDIT_INDEX_V1_20261014.md`.
6. `results/target_discovery/JEPA_MERGED_LANE_AUDIT_STATE_V2_20261014.json`.
7. `results/target_discovery/JEPA_MERGED_LANE_EXTERNAL_ARTIFACT_CUSTODY_V1_20261014.csv`.
8. `docs/agent/MACHA_GPU_EXECUTION_ENVIRONMENT_AND_RUNTIME_CUSTODY_V1_20261014.md`.
9. `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`.
10. downstream reuse-first package and `JEPA_NO_REPEAT_DECISION_TABLE_V1.json` on PR #322.
11. `docs/agent/MACHA_TASK0_FINAL_INDEPENDENT_REVIEW_PACKET_V1_20261014.md`.

Do not reconstruct history from chat or restart an audit simply because the conversation changed. First classify new work as:

`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`

## Current architecture

Accepted merged architecture PR #379 exact head:
`3064ca545f0c94859ea989cd49a04fcbd5b9a303`

One authority chain:

`known-truth substrate → unified TD qualification/controller → TARGET_QUALIFICATION_BUNDLE_V1 → downstream certification → runtime eligibility → independent training-eligibility review → explicit training authorization`

Known-truth and human-sealed modes share one production path. Hidden TruthBundle stays external to producers/executors/controller until normal output is frozen and external adjudication begins.

PR #380 is the controlling implementation-plan surface. A prospective downstream A–T expansion is already drafted but does not control until Task 0 acceptance and deliberate formal adoption.

## Current stop gate

Task 0 PR #381 exact independent-review candidate:

`c80d7398b41f10208ec1622bc52599383b940be6`

Exact-head evidence:
- focused run `38645994312`, job `116132861396`: SUCCESS, 29 passed;
- inherited run `38645994388`: SUCCESS.

Old synthetic Tasks 1–2 implementation:

`ff597faf2182522a320ec5322f8db9b67c9c6094`

Controller review PR #382:
- focused run `38644641042`, job `116128364543`: SUCCESS, 332 passed in 8.94s;
- inherited run `38644640881`: SUCCESS.

Only remaining Task 0 gate: fresh independent Macha review/adjudication of those exact heads.

Until accepted:
- unified Task 1 must not start;
- candidate outcomes stay closed;
- `reader_validation` stays closed;
- `reader_oracle` stays closed;
- old synthetic Tasks 3–4 stay `STOPPED_AFTER_MERGER__REQUIREMENTS_MIGRATE_ONLY`;
- old synthetic Tasks 5–12 have no independent continuation.

## Macha execution/review model

Macha is a Claude coding/execution agent operating on the project GPU laptop and also a historical scientific custodian/hostile reviewer.

Project history records real GPU execution, not a hypothetical future environment. Future GPU runs must re-detect and receipt the current hardware, driver, CUDA, PyTorch, kernels, environment, source roots and configuration. Historical software/settings are evidence only.

Do not conflate roles. A Macha-executed GPU run does not self-promote because Macha can also review. Execution evidence and independent adjudication must remain logically separate.

## Old synthetic merger state

Old Task 1 provides strong tested canonicalization primitives but does not complete unified Task 1. Reuse/adapt it under the unified JSON-native authority law.

Old Task 2 provides strong commit/reveal, identity-keyed RNG and custody infrastructure. It maps mainly into unified sealed-challenge/finalizer custody and does not complete unified Task 2.

Unified Task 2 is the real TD execution manifest/access law: deterministic reader-fit cross-fitting, validation/oracle firewall and actual producer-access receipts.

Old Tasks 3–4 are stopped in the old lane; their requirements migrate only. Old Tasks 5–12 remain stopped as a separate authority program.

## Real-TD controlling lineage

Use exact controlling repairs; do not redo archaeology:
- G8 #364 `95dd474a02ce571722df9e8f08b42e81af2e8736`
- G6 #365 `4110d4478c3353d86740dd135d62460ff7a7611f`
- geometry #366 `8d6b23a18051f64463ee9b2649f4fe5fc7123f0d`
- R1 #367 `949d76ff03cb57c5a88fef9efdb79fced9154024`
- G2 #368 `42df903d6190b7aa1b8eb65d810ab813cd327445`
- G7 #362 `5a711f9a4ea0328445a05dadc1e011efb16a3c13`
- R4/C6/C4 #358 `b7c317c640aa231a7d5ec1fa12271a39bfee86e6`
- C4→C6 firewall #351 `2abcb9fe156eac340ff12adff9426ed38d929e3e`
- G12 #360 `01ebdb9384b42d5cfae3de03c2adf5b6b327ee81`
- system battery #369 `651d7a5a1d4f4047d5ac875cc603f9151c2fed36`

Superseded duplicates: #375→#365, #376→#366, #377→#367, #378→#368.

Initial unified stage ceiling for current full repaired units is no higher than `FIXTURE_SAME_INTERFACE` pending exact prerequisites and executable mode-path equivalence.

## Population/support and protected-data law

Canonical population/support PR #349:
`1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7`

Known population:
- 6,351,753 rows
- 149 donors
- 42 operators
- 3 sources
- 2,028 donor×operator strata
- 104 reader_fit / 22 reader_validation / 23 reader_oracle
- 4,553,407 reader-fit nuclei

Current law:
- deterministic cross-fitting only within `reader_fit`;
- validation/oracle cannot rescue fit-side estimability;
- record actual observed access, not just intended access;
- a numerically correct output after forbidden access is invalid;
- measured zero != unsupported;
- unsupported != unresolved;
- unresolved/numerical failure != biological FAIL;
- source failure cannot average away;
- generic RNA presence does not manufacture candidate support;
- FULL104 denominator/off-address mass remains an information channel;
- address parity != evidence parity;
- no favorable zero-fill.

## Downstream teacher/student/EMA — reuse first

The architecture and much of the mechanics are already historically audited. Do not restart from zero.

Historical evidence includes teacher/student runtime, rich-teacher/partial-RNA work, TargetPortfolio, post-TD harness, T1/C2 update mechanics, EMA ordering, checkpoint/RNG/resume, V5 donor-primary target/proposal work, V5 inactive weighted update, keyed dropout, target-address shortcut audit, semantic carryover audits, preexecution carryover red-team, depth-derived protected registry and current-registry checkpoint patterns.

EMA mechanics are historically strong, but historical `.996` is not current merged authority. Exact presentation unit/half-life remains prospective.

Use PR #322 evidence-reuse, exact-asset, historical-test, status and unresolved-work ledgers before adding new downstream audits.

## Prospective downstream program

A TQB exact consumption; B teacher target/evidence; C student restriction/recoverability; D target-identity shortcut; E masking/evidence acquisition; F scientific weighting/proposal; G representation/subspace/transfer; H normalization/library/support channels; I multimodal provenance; J optimizer/gradient/moment/EMA joined runtime; K EMA timescale; L checkpoint/resume/source/runtime provenance; M model/protected-registry geometry; N packing/RNG/GPU equivalence; O collapse/movement/stability; P leakage/falsifier regression; Q downstream certification; R runtime eligibility; S independent training-eligibility review; T explicit owner authorization.

This is a prospective amendment candidate, not current authority.

## GPU qualification consequence

The project does not need to obtain a production GPU executor; Macha already provides it.

Package N must qualify the exact merged runtime on the current GPU environment: re-detect hardware/software, bind source/config/TQB/model/protected-registry roots, qualify reference-vs-GPU semantics/gradients where required, qualify true accumulation without changing scientific mass, test GPU RNG/packing, and freeze hardware/kernel/environment provenance.

## Heavy/private assets

Large calibration/expression/checkpoint/NPZ assets are not to be recopied into public Git for convenience. Use the audit branch external-artifact custody manifests and SHA bindings. FULL104 physical assets historically live on the execution laptop/attached drive.

## Next agent action

1. Re-fetch PR #381 and exact old Task1/2 head.
2. Inspect Macha fresh independent verdict for `c80d7398...` and `ff597faf...`.
3. If accepted: freeze Task 0 acceptance/custody pointers on #322/#323, prospectively reconcile the downstream A–T amendment into PR #380, then begin unified Task 1 only, RED-first.
4. If not accepted: do not start unified Task 1; continue only non-authorizing audit/design/reuse/custody work.

For every real defect: discriminating RED → intended failure → minimal repair → focused GREEN → inherited regression → hostile review → exact-head/workflow verification → freeze receipt → update #322/#323.
