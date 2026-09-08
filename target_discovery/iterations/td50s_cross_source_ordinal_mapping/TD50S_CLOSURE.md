# TD50S closure — training-null pass, same-cell evaluation-alignment failure

Status: `TD50S_PREDECLARED_TRAIN_NULL_PASSES__MATCHED_EVAL_ALIGNMENT_FAILS__TARGET_UNQUALIFIED`

Prospective freeze: `780f2dfd16094e3b748dbb0e533de21f94bb93c2`

## Predeclared cross-source result

TRAIN = all A_NATURAL_MIXTURE HVS + SEA_AD donors.
TEST = all A_NATURAL_MIXTURE NPH52 donors.
No NPH52 target tau was used for fitting, model selection, predictor standardization, or target centering.

64/64 target coordinates measurable.
Selected ridge multipliers:
- shortcut: 0.001
- molecular context: 1

NPH52 equal-donor test:
- shortcut MSE: 3.7642617849
- molecular MSE: 3.3227714658
- observed Delta_cross: **+0.1172847013**

All 16 complete HVS+SEA_AD broken-context TRAIN null refits were completed.
Null Delta range:
- max: **+0.0901335438**
- median: approximately +0.0819
- min: approximately +0.0758

Thus the originally frozen TRAIN-null criterion is satisfied: observed Delta_cross > 0 and observed > all 16 TRAIN nulls.

## Mandatory adversarial self-check after the frozen gate

A same-cell evaluation-alignment attack was then run on NPH52, preserving donor, operator, source_library and detected-gene structure while cyclically replacing each NPH52 molecular-context row with a matched wrong-cell row inside the same TD37A-style block.

Primary observed:
- Delta_cross = **0.1172847013**

64 matched NPH52 evaluation-context nulls:
- median Delta = **0.1168030388**
- max Delta = **0.1175615742**

The null maximum exceeds the observed value.

Within-donor-centered decomposition:
- observed within-donor Delta = **0.0366983458**
- eval-null median = **0.0359048405**
- eval-null max = **0.0371544745**

Again the null maximum exceeds observed.

Between-donor mean component:
- shortcut MSE: 1.4793322439
- molecular MSE: 1.1216950592
- Delta_between = **0.2417558234**

Therefore much of the apparent cross-source gain is transferable donor/population structure, and even the smaller within-donor gain is not demonstrably same-cell-specific under the matched evaluation attack.

Additional source diagnostic:
- HVS-only -> NPH52 Delta: +0.1813
- SEA_AD-only -> NPH52 Delta: +0.0613

This shows the broad mapping is not a single-source accident, but does not rescue same-cell identifiability.

## Decision

Do not promote TD50S despite satisfying its original TRAIN-null terminal. The post-gate adversarial check exposes a missing qualification condition: correct-cell evaluation context must beat matched wrong-cell evaluation context.

Binding classification:
`CROSS_SOURCE_ORDINAL_POPULATION_MAPPING_EXISTS__SAME_CELL_CONDITIONAL_INFORMATION_NOT_ESTABLISHED`

No target authority, production dimension, threshold, or JEPA training authorization.

Next iteration must prospectively make matched wrong-cell evaluation context qualification-bearing and should remove donor-level target means so that only within-donor/cell-specific residual information can pass.
