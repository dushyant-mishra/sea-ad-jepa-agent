# JEPA merged-lane successor handoff V16 — 2026-10-14

Status: `TAKEOVER_READY__GPU_EXECUTION_HISTORY_RECOVERED__TASK0_INDEPENDENT_REVIEW_PENDING__UNIFIED_TASK1_BLOCKED`

Binding authority remains exactly:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Read first

1. PR #322 canonical audit/custody surface.
2. `docs/agent/JEPA_COMPLETE_TAKEOVER_AUDIT_MANIFEST_V1_20261014.md` on PR #322.
3. `docs/agent/JEPA_MERGED_LANE_MASTER_AUDIT_INDEX_V1_20261014.md`.
4. `results/target_discovery/JEPA_MERGED_LANE_AUDIT_STATE_V2_20261014.json`.
5. `results/target_discovery/JEPA_MERGED_LANE_EXTERNAL_ARTIFACT_CUSTODY_V1_20261014.csv`.
6. `docs/agent/MACHA_GPU_EXECUTION_ENVIRONMENT_AND_RUNTIME_CUSTODY_V1_20261014.md`.
7. `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`.
8. downstream reuse-first package in section 7 below.
9. `docs/agent/MACHA_TASK0_FINAL_INDEPENDENT_REVIEW_PACKET_V1_20261014.md`.

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

### GPU execution agent
Project history records a real GPU lane, not a hypothetical future environment. Historical evidence includes RTX 3080 Laptop GPU / 16 GB VRAM class execution, prior full 41,238-address GPU mechanics, frozen-cache/predictor GPU runs, GPU utilization/memory checks, true-gradient-accumulation doctrine, checkpoint/recovery requirements and remote FULL104 execution contracts.

Future GPU runs must re-detect and receipt the current hardware, driver, CUDA, PyTorch, kernels, environment, source roots and configuration. Historical software/settings are evidence only.

### Independent reviewer
Macha reviews frozen exact heads and adjudicates scientific/custody claims.

Do not conflate roles. A Macha-executed GPU run does not self-promote because Macha can also review. Execution evidence and independent adjudication must remain logically separate.

## Old synthetic merger state

Old Task 1 provides strong tested canonicalization primitives but does not complete unified Task 1. Reuse/adapt it under the unified JSON-native authority law. Ordered coordinate-registry identity is order-sensitive; keyed semantic row-set identity may be reorder-invariant. Do not import NumPy convenience semantics into the global identity root without explicit authority.

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

Registry payload SHA:
`50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`

Known population:
- 6,351,753 rows
- 149 donors
- 42 operators
- 3 sources
- 2,028 donor×operator strata
- 104 reader_fit / 22 reader_validation / 23 reader_oracle
- 4,553,407 reader-fit nuclei
- 1,400 reader-fit donor×operator groups

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

Historical evidence includes:
- teacher/student runtime PR #2 merge head `76bf7912cc621756fdbbd82218025d8e4c00a057`;
- rich-teacher/partial-RNA PR #312 `2ca8a91a960c823cc327d3885d008d3695837e83`;
- TargetPortfolio PR #332 `902054ad62eede84086fc2e0a90ceb27e2191da7`;
- post-TD harness source `97dd73f49e1554053bbfab6c5369377a23a72ceb`, historical GREEN `38448458550` / `115472916925`.

Already-audited mechanics/findings include:
- T1/C2 protected-gradient failure and repair;
- optimizer step proof, Adam moment gates and EMA-after-step chronology;
- no EMA after rejected/skipped update;
- teacher exact-copy/eval/no-grad mechanics;
- checkpoint/RNG/resume chronology;
- scientific-weight-preserving packing;
- donor-primary target doctrine and p/q separation;
- visibility/context/within-donor and same-cell measurement-shortcut audits;
- target-address identity shortcut discovery;
- semantic carryover rules;
- 6/48/128×8 preexecution carryover defect;
- depth-derived protected-registry/current-registry checkpoint successor pattern.

Historical V5 inactive update reference already tested one optimizer step, exact EMA equation at the supplied momentum, no teacher gradients, deterministic replay, weight-preserving packing, checkpoint/resume matching and cursor/step fail-close behavior. It is mechanics/reference evidence, not current production authority.

Target-address shortcut remains scientifically open: historical `BlockPredictor` queried the online trainable gene-identity embedding. The Sept. 15 audit already defined identity-only/shared/fixed/stopgrad/shuffle comparators. Reuse that spec.

EMA mechanics are historically strong, but historical `.996` is not current merged authority. Exact presentation unit/half-life remains prospective.

## Downstream reuse-first package

Read before any downstream implementation:
- `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`
- `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260915_V5_TARGET_AUTHORITY_CURRENT.md`
- `docs/agent/DOWNSTREAM_QUALIFICATION_DELTA_FROM_HISTORICAL_AUDITS_V1_20261014.md`
- `docs/agent/DOWNSTREAM_QUALIFICATION_EVIDENCE_REUSE_GUIDE_V1_20261014.md`
- `results/target_discovery/unified_qualification_v1/DOWNSTREAM_QUALIFICATION_EVIDENCE_REUSE_MATRIX_V1.json`
- exact historical asset ledgers V1 + delta2 + delta3
- `DOWNSTREAM_HISTORICAL_TEST_EVIDENCE_DELTA_V1.json`
- `DOWNSTREAM_QUALIFICATION_STATUS_MATRIX_V1.json`
- `DOWNSTREAM_UNRESOLVED_WORK_LEDGER_V1.json`
- `docs/superpowers/plans/2026-10-14-downstream-qualification-program-v1.md`
- `docs/agent/UNIFIED_DOWNSTREAM_QUALIFICATION_PROGRAM_AMENDMENT_CANDIDATE_V1_20261014.md`

Prospective packages A–T:
A TQB exact consumption; B teacher target/evidence; C student restriction/recoverability; D target-identity shortcut; E masking/evidence acquisition; F scientific weighting/proposal; G representation/subspace/transfer; H normalization/library/support channels; I multimodal provenance; J optimizer/gradient/moment/EMA joined runtime; K EMA timescale; L checkpoint/resume/source/runtime provenance; M model/protected-registry geometry; N packing/RNG/GPU equivalence; O collapse/movement/stability; P leakage/falsifier regression; Q downstream certification; R runtime eligibility; S independent training-eligibility review; T explicit owner authorization.

This is a prospective amendment candidate, not current authority.

## GPU qualification consequence

The project does not need to obtain a production GPU executor; Macha already provides it.

Package N must instead qualify the exact merged runtime on the current GPU environment:
- re-detect hardware/software/runtime;
- bind exact source/config/TQB/runtime roots;
- reference-vs-GPU semantics and gradient equivalence where required;
- true accumulation/microbatch qualification without changing scientific mass or optimizer definition;
- GPU RNG/packing qualification;
- current model/protected registry;
- current hardware/kernel provenance.

Package J runs inherited optimizer/gradient/moment/EMA attacks on the exact joined GPU configuration. Package L binds checkpoint/resume/source/environment provenance. Package R consumes those receipts.

## Heavy/private assets

Large calibration/expression/checkpoint/NPZ assets are not to be recopied into public Git for convenience. Their absence from Git does not mean historical work was absent.

Use:
`results/target_discovery/JEPA_MERGED_LANE_EXTERNAL_ARTIFACT_CUSTODY_V1_20261014.csv`

and later append-only custody manifests for exact path/size/SHA bindings.

## Permanent negative controls / closed work

Do not revive by default:
- V79 terminal NOT_QUALIFIED;
- discarded defective `x4_within` estimator real outputs;
- old QID matched-null estimand error;
- pooled context result as population authority;
- zero-margin G6 authority;
- G8 599 technical thinnings as biological calibration;
- caller-supplied geometry human authority;
- old wrong-cell R1 null;
- PR #328 disjoint-block geometry as production biology;
- duplicate repairs #375–#378;
- old synthetic Tasks 3–12 as an independent authority path.

## Next agent action

Immediate next action is **not** to implement unified Task 1.

1. Re-fetch PR #381 and exact old Task1/2 head.
2. Inspect Macha fresh independent verdict for `c80d7398...` and `ff597faf...`.
3. If accepted:
   - freeze Task 0 acceptance/custody pointers on #322/#323;
   - formally/prospectively reconcile the downstream A–T amendment into PR #380;
   - begin unified Task 1 RED-first using the existing canonical compatibility oracles;
   - do not treat old Task 1 as completing unified receipt/parent/authority logic.
4. Continue sequentially through manifest/access → registry/prerequisites → sealed custody → CaseBundle/TruthBundle → repaired-unit registration → TQB → downstream A–Q → GPU/runtime eligibility → independent training eligibility → explicit owner authorization.

Every task uses exact-head RED→GREEN, focused + inherited regression, hostile self-audit, independent review where required, and append-only audit/handoff updates.
