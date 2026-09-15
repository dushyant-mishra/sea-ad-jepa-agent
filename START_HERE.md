# START HERE — JEPA PROJECT

Date: 2026-09-15
Status: `CURRENT_V5_LAYER2_SHORTCUT_MASKING_AND_TEACHER_AUTHORITY_REVIEW__NO_TRAINING_AUTHORITY`

## Read first

Use `main` for project-current governance/startup context. Read in this order:

1. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
2. `docs/agent/JEPA_WORK_LEDGER_AND_FINDINGS_20260915_CURRENT.md`
3. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260915_CURRENT.json`
4. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260911_TARGET_DISCOVERY_V5_INTEGRATED_CURRENT.md` for upstream target-discovery / prior governance context
5. `docs/agent/JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json`
6. `docs/agent/JEPA_FORMULAS_AND_AUTHORITY_LEDGER_20260909_FINAL_R4.md`
7. `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`
8. `docs/agent/CURRENT_AUTHORITY_INDEX.md`
9. `docs/agent/CURRENT_SUPERSESSION_MAP.md`

Before writing or executing, re-fetch live heads. Branch names do not confer scientific authority.

## Permanent governing boundaries

Design order:

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> PRODUCTION GEOMETRY -> MODEL`

Protected-data rule:

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

Training remains OFF.

Do not inspect or execute real D_shared outcomes, protected/pathology outcomes, D_private, D_obs outcomes, TD60, or other confirmation data while design choices remain open.

## Current production population

- 4,553,407 cells
- 104 donors
- 42 operators / matrices
- 41,238 molecular addresses
- 17,186 common measured-core addresses
- 8,915 Level-4 expression blocks
- sources: SEA-AD, HVS, NPH52

## V5 representation status

Current candidate representation is the 256-D VALUE_ONLY half of each rebuilt view.

The 256 visibility channels were shown to be dominated by observation-state/QC encoding and are not current primary molecular-representation authority.

Current V0/V1 common-core split:

- V0: 8,568 addresses
- V1: 8,618 addresses
- disjoint; union = 17,186 common-core addresses

Primary representation authority remains NOT FROZEN.

## Layer-2 anti-shortcut findings — current

The project now separates:

1. representation substrate;
2. training shortcut / anti-cheat problem;
3. downstream donor-level nuisance/inference.

### Same-cell measurement/thinning shortcut

On the simple donor-held-out probe, matched measurement state did not improve V0->V1 prediction. Excess matched-state synergy was very small, reaching only ~0.005 R2 at the most extreme p=.25 condition.

Current terminal:

`MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS`

This is not proof that a deep encoder cannot exploit measurement state.

### Pooled context shortcut

On the BASE mechanics sample, donor-held-out raw-projection proxy results were approximately:

- Q_DEPTH + Q_DETECT -> V1: R2 ~0.031
- source + operator + QC -> V1: R2 ~0.4671
- V0 -> V1: R2 ~0.4666
- both -> V1: R2 ~0.4982

This shows large predictive collinearity with pooled context. It does NOT show that 85% of signal is technical.

Use:

`PREDICTIVE_INFORMATION_LARGELY_COLLINEAR_WITH_CONTEXT_ON_POOLED_MECHANICS_SAMPLE`

### Important estimator correction

An early within-operator estimator (`x4_within.py`) was proven by synthetic null fixture to create false residual signal. Its numbers were discarded and are not authority.

A replacement estimator was validated on null/positive fixtures before real-data use.

### Source-specific / within-donor correction

The corrected analysis showed that the pooled ~0.47 result conflated between-source, donor/operator and within-donor structure.

Donor-centred, cell-held-out cross-view R2 was approximately:

- ALL: 0.185
- HVS: 0.191
- NPH52: 0.265
- SEA_AD: 0.249

Measured QC explained little additional variance once V0 was present (~+0.003 R2).

Current interpretation:

`WITHIN_DONOR_MOLECULAR_VIEW_SIGNAL_BEYOND_MEASURED_QC_RECURS_ACROSS_ALL_THREE_SOURCES`

Do not translate this into `BIOLOGY_PROVEN` or `NONTECHNICAL_PROVEN`.

At the current linear model class, donor-generalizable cross-view signal is demonstrated in SEA_AD but not demonstrated in HVS/NPH52.

## New masking-shortcut blocker

A 2026 ICLR genomics workshop paper, "Taking the Easy Way Out: When Single-Cell Foundation Models Learn Shortcuts Instead of Biology" (OpenReview `KlDSNIvt9A`), shows that random single-gene masking can let models reconstruct hidden genes from visible correlated partners rather than learn global cell state.

This is directly relevant to JEPA hidden-target design.

Historical JEPA code already had graph-aware Pearson/correlation-expanded target masking. Current V5 fail-closed runtime uses graph-free uniform target blocks. Historical graph masking must not simply be restored without prospective review.

New blocker:

`MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

Current candidate direction, NOT frozen:

- hybrid dependency-aware + random masking;
- preserve full address coverage;
- audit correlated-partner exposure;
- avoid a pooled FULL104 graph that merely encodes source/operator composition;
- prefer donor-recurrent / cross-source-consensus dependency evidence where support permits.

## Current architecture candidates — not authority

Leading candidate:

`full_prediction = stop_gradient(frozen_context_baseline) + molecular_increment`

Loss remains against the complete target. The residual is NOT to be called biology; call it:

`PREDICTIVE_INFORMATION_BEYOND_FROZEN_CONTEXT_BASELINE`

Candidate combination:

`RESIDUAL_OVER_CONTEXT + DEPENDENCY_AWARE_HYBRID_MASKING`

Lower-priority candidates:

- generic information bottleneck;
- source/operator adversarial invariance.

Reason: source/operator are low-dimensional but biologically confounded, so both compression and adversarial removal can preserve shortcuts or erase biology.

## Major blockers now

1. `CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED`
2. `CONTEXT_SHORTCUT_HANDLING_NOT_YET_FROZEN`
3. `MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`
4. `HVS_NPH52_DONOR_TRANSPORT_NOT_YET_EXPLAINED`
5. `SCIENTIFIC_TRAINING_ESTIMAND_NOT_YET_FROZEN`
6. `OBJECTIVE_ALIGNED_SHORTCUT_GATE_NOT_YET_FROZEN`
7. `PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN`
8. `RANK_SUPPORT_AUTHORITY_NOT_YET_FROZEN`
9. `V3_NULL_NOT_YET_FROZEN`
10. `MEASUREMENT_ROBUSTNESS_DECISION_RULE_NOT_YET_FROZEN`

## Current heavy-machine closeout work

The latest requested Claude closeout includes:

- independent second implementation of the context decomposition;
- estimand-weighting sensitivity;
- donor-level recurrence characterization;
- stronger full-refit donor-generalization uncertainty if feasible;
- Layer-2 closeout package;
- no production training.

Re-fetch Claude's latest pushed head before assuming these remain outstanding.

## Independent review lane

Methodological red-team/supporting checks are preserved separately on:

`analysis/layer2-method-redteam-20260915`

Observed head at the time of this governance update:

`b2b93f3f559df268069b74b4ae7fe4e1fbd523d4`

This lane is not production authority.

## Upstream target-discovery / T0 boundary

The prior 20260911 integrated target-discovery->V5 handoff remains required historical/upstream context.

T0 remains unresolved for biology and does not authorize training.

Historical QID warning remains active: matched-null state intervention was not demonstrated equivalent to paired-wrong-query intervention.

## Permanent rules

- A decreasing loss, passing CI, branch name, design draft or healthy checkpoint is not biological/training authority.
- Do not call source/operator structure `technical` without causal support.
- Do not call within-donor molecular-view signal `biology` merely because measured QC does not explain it.
- Do not trust outputs from discarded estimators.
- Do not silently inherit historical V4/V21 teacher semantics into current V5.
- Do not restore historical graph masking without prospective review.
- Do not merge empirical, source-uniform and donor-primary estimands.
- D_shared remains sealed.
- Training remains OFF.
