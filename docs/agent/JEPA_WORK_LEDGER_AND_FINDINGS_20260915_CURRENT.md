# JEPA WORK LEDGER AND FINDINGS — 2026-09-15 CURRENT

Status: `CURRENT_PROJECT_LEDGER__NO_TRAINING_AUTHORITY`

This document is the compact project-current ledger for other agents and future chats. It records what was learned, what was corrected, what remains unresolved, and which ideas are only candidates rather than authority.

## Governing boundaries

Design order remains:

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> PRODUCTION GEOMETRY -> MODEL`

Standing protected-data rule:

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

Hard OFF unless prospectively frozen authority changes them:

- production training;
- protected/pathology/DEV/SEALED outcome access;
- real D_shared outcome inspection/execution;
- D_private;
- D_obs outcome execution;
- TD60;
- relational activation;
- external confirmation outcomes influencing design.

Training remains OFF.

## FULL104 production facts

Authenticated population facts used by current V5 work:

- 4,553,407 cells;
- 104 donors;
- 42 operators / 42 matrices;
- 41,238 molecular addresses;
- 17,186 common measured-core addresses;
- 8,915 Level-4 expression blocks;
- sources: SEA-AD, HVS, NPH52.

Important immutable substrate references remain documented in prior heavy-asset/handoff files. The Full104 Level-4 block manifest SHA-256 is:

`66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`

## T0 / target-discovery state

T0 terminal remains:

`T0_MEASUREMENT_PROCEDURE_NOT_QUALIFIED_AT_N28__BIOLOGY_UNRESOLVED`

Historical QID/F1 warning remains active. At historical commit `dd078625c3537f5ff2c3f8c0b382ba2803b24ee2`, intended QID used `own_similarity - paired_wrong_similarity`, but production supplied a matched-null state against the true teacher. Matched-null preserved query identity. Therefore:

`matched-null state intervention != demonstrated paired-wrong-query intervention`

Do not reintroduce this estimand error.

## V5 representation rebuild — current facts

A deterministic K=2 common-core split was built over the 17,186 common-core addresses:

- V0: 8,568 addresses;
- V1: 8,618 addresses;
- intersection: 0;
- union: 17,186.

FULL104 rebuilt substrate:

- `V0_full.npy`: `(4553407, 512)` float32, SHA-256 `3b3f102c6767727ca4ab56832f8e70baf203676d6b65973c42903b22b6d56ada`;
- `V1_full.npy`: `(4553407, 512)` float32, SHA-256 `c41df46d842d643f04566b8523a8aa711fa54bec1c836e0b394c0146017f231c`.

Each 512-D view is 256 VALUE channels + 256 VISIBILITY channels.

### Visibility ablation

Donor-held-out nuisance prediction showed the visibility channels are primarily observation-state/QC encoding:

- V0 VALUE_ONLY: Q_DETECT R2 ~0.702, Q_DEPTH R2 ~0.444;
- V0 VISIBILITY_ONLY: Q_DETECT R2 ~0.977, Q_DEPTH R2 ~0.834;
- V0 FULL: Q_DETECT R2 ~0.979, Q_DEPTH R2 ~0.859;
- V1 behaves similarly.

Current recommendation, NOT frozen authority:

`PRIMARY_MOLECULAR_REPRESENTATION_CANDIDATE = VALUE_ONLY_256`

`VISIBILITY_CHANNELS = OBSERVATION_STATE / NUISANCE CONTROL ONLY`

Do not reintroduce the historical 60% visible-mask geometry as current V5 biological authority.

## Same-cell measurement intervention — completed

The completed VALUE_ONLY same-cell thinning screen used p in:

`{1.00, 0.90, 0.75, 0.50, 0.25}`

with frozen BASE mechanics and source-conditional stress cells. The production screen package is held on the heavy-machine lane; its key frozen hashes are documented in the measurement closeout package.

Core findings:

- thinning mechanics replayed exactly when using declared `source_library`;
- the full source library extends beyond the 41K ledger and the outside-ledger fraction is source-dependent;
- VALUE_ONLY changes systematically under degradation;
- QC predictability from VALUE_ONLY rises as measurement worsens;
- V0 and V1 independently reproduce the degradation pattern;
- numerical rank does not collapse; the spectrum flattens under degradation;
- no biological validity was established by this experiment.

Important permanent substrate fact:

`FULL_SOURCE_LIBRARY_EXTENDS_BEYOND_41K_LEDGER__SOURCE_DEPENDENT_OUTSIDE_LEDGER_FRACTION`

## Layer-2 anti-shortcut audit — corrected current interpretation

A long discussion and subsequent execution separated three layers:

1. representation substrate;
2. training anti-cheat / shortcut exploitability;
3. downstream donor-level nuisance/inference.

The previous donor-first sequence was withdrawn because it jumped from Layer 1 to Layer 3 before resolving the training objective.

### Measurement-realization shortcut

Using frozen thinning arrays, matched measurement state did not improve the simple V0->V1 prediction task.

Reported results:

- `V0^p -> V1^p` was worse than `V0^1 -> V1^p` at every p in both directions;
- matched-state advantage ranged roughly from -0.002 at p=.90 to -0.016 at p=.25;
- excess interaction above a marginal attenuation null was approximately `0.0000, 0.0002, 0.0013, 0.0051` for p=.90,.75,.50,.25;
- the largest excess was about 1% of full-depth cross-view R2;
- realized post-intervention library/detection scalars added only ~0.0017 to ~0.0026 R2 over the clean-view predictor.

Current terminal:

`MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS`

This does NOT mean `SHORTCUT_ABSENT`. A deep encoder could exploit structure not accessible to a simple linear/ridge probe.

The current evidence does not justify a view-local denominator rebuild or a measurement-decorrelated teacher/student objective solely for this thinning channel.

### Initial pooled context/batch result

On the BASE mechanics sample at full depth, donor-held-out linear proxy results were:

- Q_DEPTH + Q_DETECT -> V1: R2 ~0.031;
- source + operator + QC -> V1: R2 ~0.4671;
- V0 -> V1: R2 ~0.4666;
- both combined -> V1: R2 ~0.4982.

Predictive overlap:

`0.4666 + 0.4671 - 0.4982 = 0.4355`

This is ~87.4% of combined explained variance, or ~93% of either standalone predictor's explained variance.

Use:

`LARGELY_REDUNDANT_PREDICTIVE_INFORMATION_WITH_CONTEXT`

Do NOT translate this into `% technical`.

Source/operator are confounded with cohort, region, platform, donor composition, disease composition and real biology.

### Estimator defect caught and repaired

An initial within-operator estimator (`x4_within.py`) was shown by an independent synthetic fixture to manufacture residual signal when truth contained only operator-level shared structure. Those numbers were discarded before entering the evidence record.

A replacement estimator was validated before real-data use:

- operator-only truth, zero cell-level signal -> operator-centred R2 ~ -0.0068;
- planted cell latent -> positive recovered residual;
- no shared structure -> ~ -0.002.

This is an important project lesson:

`NO_REAL_RESULT_FROM_THE_DISCARDED_X4_WITHIN_ESTIMATOR_IS_AUTHORITY`

## Source-specific recurrence — major correction to the previous batch-dominance framing

Follow-up analysis showed the pooled ~0.47 cross-view R2 conflated between-source, donor/operator and within-donor structure.

### Operator-centred, donor-held-out cross-view R2

- ALL: ~0.0687;
- HVS: ~0.0437;
- NPH52: ~0.0530;
- SEA_AD: ~0.2402.

### Donor-centred, cell-held-out cross-view R2

A separate estimator was first validated on fixtures:

- donor-structure-only truth -> ~ -0.0019;
- planted cell latent -> ~0.708.

Real results:

- ALL: ~0.1850;
- HVS: ~0.1906;
- NPH52: ~0.2646;
- SEA_AD: ~0.2487.

Interpretation:

`WITHIN_DONOR_MOLECULAR_VIEW_SIGNAL_BEYOND_MEASURED_QC_RECURS_ACROSS_ALL_THREE_SOURCES`

This is NOT proof of biology and NOT proof that the residual is nontechnical. It shows a recurrent molecular-view relation not explained by the measured Q_DEPTH/Q_DETECT family.

Donor-generalizable linear cross-view signal at this model class is demonstrated strongly in SEA_AD, but is not demonstrated in HVS/NPH52.

Use:

`DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_DEMONSTRATED_IN_SEA_AD_AT_THIS_MODEL_CLASS`

`DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_NOT_DEMONSTRATED_IN_HVS_OR_NPH52_AT_THIS_MODEL_CLASS`

Negative evidence is model-class-specific; do not convert it into absence.

### Within-donor QC control

After donor means were removed, Q_DEPTH/Q_DETECT-like realized QC contributed little once V0 was present:

- ALL: QC-only ~0.0208; V0-only ~0.1850; V0 increment over QC ~+0.1668; QC increment over V0 ~+0.0026;
- HVS: 0.0535 / 0.1906 / +0.1401 / +0.0029;
- NPH52: 0.0690 / 0.2646 / +0.1982 / +0.0026;
- SEA_AD: 0.0575 / 0.2487 / +0.1941 / +0.0029.

Current interpretation:

`MEASURED_QC_IS_NOT_THE_PRIMARY_EXPLANATION_FOR_WITHIN_DONOR_CROSS_VIEW_SIGNAL`

Do not say `THE_SIGNAL_IS_BIOLOGICAL` or `THE_SIGNAL_IS_NOT_TECHNICAL`.

### Variance decomposition explaining source differences

Reported fraction of V1 variance by source:

- HVS: between-operator ~0.213; donor-within-operator ~0.193; within-donor ~0.595;
- NPH52: ~0.253 / ~0.228 / ~0.519;
- SEA_AD: ~0.028 / ~0.040 / ~0.932.

SEA_AD retains far more signal after operator centring because its representation on this mechanics sample has much less between-operator/donor structure to remove.

### Layer-normalized loss-geometry proxy

A mechanics-aligned proxy repeated the analysis after per-row layer normalization:

- context-only donor-held-out: raw ~0.4671, layer-normalized ~0.4683;
- molecular V0-only donor-held-out: raw ~0.4666, layer-normalized ~0.4826;
- combined: raw ~0.4982, layer-normalized ~0.5115;
- molecular increment over context: raw +0.0311, layer-normalized +0.0432;
- within-donor molecular: raw ~0.1850, layer-normalized ~0.1960.

Classification:

`MECHANICS_ALIGNED_PROXY_ONLY`

The actual V5 objective operates on trained encoder hidden block states, which do not exist while training is OFF, and current V5 teacher-target authority is not frozen.

## Independent local red-team lane

Independent methodological review was preserved on:

`analysis/layer2-method-redteam-20260915`

Observed head after the latest local source-specific sanity check:

`b2b93f3f559df268069b74b4ae7fe4e1fbd523d4`

That lane includes:

- the synthetic proof that the discarded first within-operator estimator could manufacture signal;
- a local 50K discovery-expression sanity check using the same 17,186 common-core split but a neutral projection;
- caution that the mechanics sample is operator-stratified and its exact R2 magnitudes are distribution-dependent;
- caution that raw projection R2 is only a proxy for the future JEPA loss.

The local 50K diagnostic is SUPPORTING METHOD EVIDENCE ONLY, not V5 production authority.

## Architecture ideas — current ranking, NOT frozen

### 1. Residual-over-context objective

Leading candidate:

`full_prediction = stop_gradient(frozen_context_baseline) + molecular_increment`

Loss remains against the FULL target.

Purpose: do not give the molecular learner credit for rediscovering what a simple context shortcut already predicts.

Never equate the residual with biology. Call it:

`PREDICTIVE_INFORMATION_BEYOND_FROZEN_CONTEXT_BASELINE`

Do not subtract operator/source means from the raw representation as a production correction.

### 2. Environment-aware/source-aware training

Candidate principle: do not allow pooled cohort differences to dominate average loss. Future training should report source-specific losses at minimum and may later evaluate source-stratified/REx-like or worst-environment objectives prospectively.

No such objective is frozen.

### 3. Dependency-aware / adversarial masking

A 2026 ICLR genomics workshop paper, "Taking the Easy Way Out: When Single-Cell Foundation Models Learn Shortcuts Instead of Biology" (OpenReview id `KlDSNIvt9A`), identifies a second shortcut class: random masking can leave highly correlated gene partners visible, permitting local interpolation instead of global-state learning.

The paper's CorrMask construction:

- builds a gene-dependency graph from expression covariance;
- jointly masks correlated partners;
- mixes structural masking with random top-up;
- reports hybrid structural/random masking outperforming both random masking and 100% structural masking;
- emphasizes coverage and long-tail benefits.

Project-relevant conclusion:

`CONTEXT_SHORTCUT` and `LOCAL_CORRELATED_GENE_SHORTCUT` are distinct and may require complementary defenses.

Historical JEPA code already contained conceptually related graph-aware masking (`build_train_pearson_graph`, graph-expanded `sample_target_blocks`). Current V5 fail-closed runtime contains graph-free uniform target-block sampling. Historical graph masking must NOT simply be restored without review.

Major new blocker:

`MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

Before production training, determine what molecular dependencies must be hidden together so the JEPA cannot solve targets by local interpolation.

Preferred future audit, still outcome-blind:

- recover historical graph-masking lineage and why it was superseded;
- measure shortcut-partner exposure under uniform masking;
- compare pooled, within-source, donor-recurrent and cross-source-consensus dependency graphs;
- simulate uniform, historical graph-expanded and hybrid CorrMask-like masks;
- measure correlated-partner exposure, address coverage, mask-budget concentration, source/operator dependence, rare-address coverage and deterministic replay;
- do not choose structural ratio from protected outcomes.

A global FULL104 correlation graph is potentially unsafe because pooled covariance can encode source/operator/cohort composition. Recurrent/consensus dependency edges are preferred candidates for study.

### 4. Information bottleneck

Lower priority. Source/operator identity is low-dimensional, so a narrow bottleneck can preserve the shortcut while discarding subtle biology. If used later, apply it only after explicit context separation and prospectively test that within-context signal is preserved.

### 5. Source/operator adversarial removal

Not recommended as the first fix. FULL104 source/operator are biologically confounded; forcing invariance can erase real biology. Reserve adversarial removal for causally stronger nuisance variables if ever used.

## Current major blockers, ordered

1. `CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED`
   - The current fail-closed V5 runtime requires a current dataset-derived teacher target. Historical V4/V21 authority cannot be widened silently.

2. `CONTEXT_SHORTCUT_HANDLING_NOT_YET_FROZEN`
   - Decide whether context shortcuts remain qualification-only competitors or become an explicit frozen residual baseline inside training.

3. `MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`
   - Uniform random/graph-free masking may permit correlated-gene interpolation; historical graph masking may be over-structural.

4. `HVS_NPH52_DONOR_TRANSPORT_NOT_YET_EXPLAINED`
   - Within-donor cross-view signal exists, but simple donor-held-out transport is weak at this model class outside SEA_AD.

5. `SCIENTIFIC_TRAINING_ESTIMAND_NOT_YET_FROZEN`
   - Empirical/FULL104, source-uniform and donor-primary/operator-balanced targets are distinct scientific estimands and must not be silently merged.

6. `OBJECTIVE_ALIGNED_SHORTCUT_GATE_NOT_YET_FROZEN`
   - Before production training, freeze the shortcut family and prospective superiority rule under the actual V5 objective geometry.

7. `PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN`

8. `RANK_SUPPORT_AUTHORITY_NOT_YET_FROZEN`

9. `V3_NULL_NOT_YET_FROZEN`

10. `MEASUREMENT_ROBUSTNESS_DECISION_RULE_NOT_YET_FROZEN`

## Claude heavy-machine work that remained outstanding at this ledger update

The latest work request asked Claude to close the current Layer-2 evidence package before architecture change:

- independently reproduce the context-shortcut decomposition with a second implementation;
- characterize estimand sensitivity under empirical/source-uniform/donor-primary views where lawful;
- characterize donor-level recurrence rather than only source-level averages;
- strengthen donor-generalization uncertainty with full refitting if feasible;
- preserve the layer-normalized result as mechanics-aligned proxy only;
- produce a mathematical residual-over-context specification, but do not production-train.

Future agents should re-fetch Claude's latest pushed head before assuming these are still outstanding.

## Current terminal summary

`MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS`

`WITHIN_DONOR_MOLECULAR_VIEW_SIGNAL_BEYOND_MEASURED_QC_RECURS_ACROSS_ALL_THREE_SOURCES`

`DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_DEMONSTRATED_IN_SEA_AD_AT_THIS_MODEL_CLASS`

`DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_NOT_DEMONSTRATED_IN_HVS_OR_NPH52_AT_THIS_MODEL_CLASS`

`PREDICTIVE_INFORMATION_LARGELY_COLLINEAR_WITH_CONTEXT_ON_POOLED_MECHANICS_SAMPLE`

`BATCH_TECHNICAL_VS_BIOLOGICAL_DECOMPOSITION_NOT_IDENTIFIABLE_IN_FULL104`

`MECHANICS_ALIGNED_LOSS_PROXY_CHARACTERIZED`

`MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

`CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED`

`PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

`TRAINING_OFF`

## Required startup behavior for future agents

1. Open `START_HERE.md`.
2. Open `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`.
3. Open this ledger.
4. Re-fetch live heads before acting; branch names do not confer authority.
5. Do not trust discarded estimator outputs.
6. Do not call context/source/operator variance "technical" unless causally demonstrated.
7. Do not call the within-donor molecular-view signal "biology" merely because measured QC does not explain it.
8. Do not modify the production trainer until the V5 teacher target, context-shortcut handling and masking authority have prospective contracts.
9. Keep D_shared sealed and training OFF.
