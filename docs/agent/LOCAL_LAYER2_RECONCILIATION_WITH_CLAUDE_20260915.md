# LOCAL LAYER-2 RECONCILIATION WITH CLAUDE — 2026-09-15

Authority: `LOCAL_INDEPENDENT_REVIEW_PLUS_CLAUDE_RESULT_RECONCILIATION__NOT_NEW_FULL104_EXECUTION`.

This note folds Claude's completed cross-view audit into the independent local red-team lane without reclassifying confounded source/operator structure as causal technical effect.

## Claude validated findings

The earlier `x4_within.py` estimator was discarded after the local red-team showed it can manufacture within-operator signal from a pure operator-only fixture. Claude then validated a replacement estimator prospectively on null/positive fixtures before applying it to the real frozen arrays.

Validated fixture behavior reported by Claude:

- operator structure only, zero cell-level truth: raw R2 0.8299; operator-centred R2 -0.0068 — PASS;
- planted cell latent strength 0.5 / 1.0: raw R2 0.876 / 0.904; operator-centred R2 0.233 / 0.595 — PASS;
- no shared structure: raw and centred R2 approximately -0.002 — PASS.

Therefore the replacement estimator is materially stronger evidence than the discarded first implementation.

## Measurement-realization shortcut result

On the frozen BASE mechanics sample:

- matched-state predictor `V0^p -> V1^p` is worse than the clean predictor `V0^1 -> V1^p` at every p, symmetrically;
- matched-state advantage ranges roughly -0.002 at p=.90 to -0.016 at p=.25;
- attenuation-null excess synergy is 0.0000, 0.0002, 0.0013, 0.0051 for p=.90,.75,.50,.25;
- the largest excess is about 1.09% of full-depth cross-view R2;
- realized library/detection scalars add only about +0.0017 to +0.0026 R2 over clean V0.

Current interpretation:

`MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS`

This is not `SHORTCUT_ABSENT`. A deep encoder remains more capable than the ridge probe.

The evidence does not presently justify a view-local denominator rebuild or a measurement-decorrelated teacher/student objective solely to address the frozen thinning channel.

## Batch/context collinearity result

Full-depth donor-held-out results reported by Claude:

- `Q_DEPTH + Q_DETECT -> V1`: R2 ~0.031;
- `source + operator + QC -> V1`: R2 0.4671;
- `V0 -> V1`: R2 0.4666;
- combined nuisance/context + V0: R2 0.4982.

The overlap identity is:

`overlap = R2(V0) + R2(context) - R2(combined) = 0.4355`.

Thus overlap is:

- 87.4% of the combined explained variance;
- 93.3% of the V0-only explained variance;
- 93.2% of the context-only explained variance.

Use the phrase `largely redundant predictive information` only with the denominator stated. Do not translate this into `% technical`.

With Claude's validated fold-local centring estimator:

- raw V0->V1 R2: 0.4666;
- source-centred R2: 0.1987 (42.6% of raw retained);
- operator-centred R2: 0.0685 (14.7% of raw retained).

Current interpretation:

`CROSS_VIEW_SIGNAL_LARGELY_COLLINEAR_WITH_OPERATOR_SOURCE_STRUCTURE`

NOT:

`85_PERCENT_OF_SIGNAL_IS_TECHNICAL`.

Operator/source are confounded with region, platform, cohort, donor composition, disease composition and real biology. The centring analysis locates where predictive covariance sits; it does not identify its causal origin.

## Important metric caution

The actual historical JEPA training loss is MSE on layer-normalized hidden block states, not raw input-space total-variance R2. The current ridge R2 audit is therefore a proxy screen for accessible cross-view structure, not an exact simulation of the learner's future objective.

Before converting the 0.467 context result into a production anti-cheat gate, the same qualitative dominance should be checked under an objective-aligned diagnostic or explicitly remain classified as a linear-proxy finding.

## Mechanics-sample estimand caution

BASE is an operator-stratified whole-block mechanics sample, not empirical FULL104. Operator block inclusion probabilities vary by ~119x.

The existence of a strong coarse-context predictor is important on this sample. Its magnitude is distribution-dependent.

Before using 0.4671 as a training-population effect size, repeat or reweight the decomposition under explicit target views when mathematically valid:

- empirical/FULL104 structure;
- source-uniform target;
- donor-primary target.

Do not merge those estimands.

## Independent 50K local diagnostic

On the local 50K discovery expression substrate, using the same 17,186 common-core addresses and exact 8,568/8,618 V0/V1 partition but a neutral local CountSketch projection:

- V0->V1 R2 ~0.4725;
- source-only R2 ~0;
- operator-only R2 ~0;
- correctly computed within-operator V0->V1 R2 ~0.4724.

Source-specific within-operator R2 on this local diagnostic is:

- HVS: 0.4632 (10,958 cells; 41 donors; 24 operators);
- NPH52: 0.4508 (5,221 cells; 17 donors; 7 operators);
- SEA_AD: 0.4718 (33,821 cells; 46 donors; 11 operators).

All held-out cells had an operator represented in the corresponding training fold.

This does not contradict Claude because the projection/substrate differ. It does show that operator dominance is not a mathematical inevitability of disjoint common-core views, and that the source-specific recurrence diagnostic is mechanically capable of returning positive signal in all three sources on an independent real-data substrate. The V5 result is specific and must be understood, not assumed.

## Strongest next question

The immediate scientific question is no longer the thinning denominator channel.

It is:

`WHERE_DOES_THE_WITHIN_OPERATOR_CROSS_VIEW_SIGNAL_EXIST_AND_IS_IT_RECURRENT_ACROSS_SOURCES?`

Recommended next diagnostics, still outcome-blind:

1. source-specific operator-centred V0->V1 R2, with identical donor-held-out semantics;
2. source-only, operator-only, Q-only, operator+Q, V0-only, operator+V0 and operator+Q+V0 using a direct cross-fitted group-mean implementation as an independent code path;
3. effective sample size / support per source and operator for every reported result;
4. sensitivity of headline decomposition to the explicit weighting/estimand view;
5. an objective-aligned shortcut diagnostic before any production anti-cheat threshold is frozen.

The source-specific within-operator analysis is valuable because it asks whether the residual cross-view relation is reproducible inside multiple studies rather than being carried by one source. It still does not prove biology, but failure to recur would be a serious warning for a cross-source biological representation.

## Architecture implication — not yet a design decision

The current evidence does not support aggressive operator/source residualization as a production representation; prior stress work showed that can erase real geometry.

Instead, any future training design should distinguish:

- `context/batch predictable component`;
- `within-context cross-view component`.

A principled future objective may need to reward only the part of cross-view predictability that cannot be won by a frozen coarse-context shortcut family. Existing V5 shortcut-superiority guards already encode the governance principle: a learned representation must beat the strongest frozen shortcut baseline by a prospectively frozen increment in every held-out case.

No new threshold is frozen here.

## Current terminals

`MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS`

`CROSS_VIEW_SIGNAL_LARGELY_COLLINEAR_WITH_BATCH_STRUCTURE`

`BATCH_TECHNICAL_VS_BIOLOGICAL_DECOMPOSITION_NOT_IDENTIFIABLE_IN_FULL104`

`WITHIN_OPERATOR_CROSS_VIEW_SIGNAL_PRESENT_BUT_NOT_YET_SOURCE_REPLICATED`

`OBJECTIVE_ALIGNED_SHORTCUT_GATE_NOT_YET_FROZEN`

`PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN`

`MEASUREMENT_ROBUSTNESS_DECISION_RULE_NOT_YET_FROZEN`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

`TRAINING_OFF`
