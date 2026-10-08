# TD50S adversarial evaluation-alignment audit

Status: `TD50_PRIMARY_CONTRACT_PASS__CELL_ALIGNMENT_NOT_ESTABLISHED__DO_NOT_PROMOTE`

Parent prospective freeze:
`target_discovery/iterations/td50s_cross_source_ordinal_mapping/TD50S_PROSPECTIVE_FREEZE.md`

## Primary contract result

Independent reconstruction of the frozen TD50 pooled HVS+SEA_AD -> NPH52 screen:

- pooled TRAIN donors: 87
- NPH52 TEST donors: 17
- measurable query coordinates: 64/64
- shortcut selected lambda multiplier: 0.001
- molecular selected multiplier: 1
- shortcut MSE: **3.7642617849**
- molecular MSE: **3.3227714658**
- observed `Delta_cross`: **+0.1172847013**

16 complete TRAIN broken-context null refits:
- null min: **0.0757945**
- null median: **0.0819967**
- null max: **0.0901335**

Thus the original frozen TD50 primary rule is satisfied:
- observed > 0
- observed > max TRAIN null

Contract-literal terminal:
`TD50S_CROSS_SOURCE_QUERY_ORDINAL_MAPPING_SURVIVES__PRIMARY_CONTRACT_ONLY`

## Implementation / leakage audit

Confirmed:
- NPH52 tau is not used in model fitting, predictor standardization, target centering/scaling, or lambda selection.
- NPH52 tau enters only final TEST scoring.
- explicit global_row is retained and used for CSR addressing.
- source ID, dataset ID, donor ID and operator identity are not model predictors.
- source is used only to define pooled TRAIN inner donor folds.
- NPH52 sparse 17,122-gene rank CountSketch independently matches dense average-rank computation on 32 deterministic cells with maximum absolute difference **6.66e-16**.

No target-value leakage was found.

## Leave-one-training-source diagnostic

Using the same portable shortcut and target definition:

- HVS-only -> NPH52: `Delta_cross = +0.1812551`
- SEA_AD-only -> NPH52: `Delta_cross = +0.0612697`
- pooled HVS+SEA_AD -> NPH52: `+0.1172847`

The pooled positive is therefore not carried solely by one training source.

## Adversarial TEST-cell alignment audit

The primary TD50 contract permutes context only in TRAIN.

To determine whether the large NPH52 gain actually depends on the **correct NPH52 cell's** molecular context, the frozen pooled model was held fixed and the 256-dimensional NPH52 context sketch was cyclically reassigned within the same NPH52 donor×operator depth/detection matched blocks. Shortcut features and target tau remained on the true cell.

64 deterministic evaluation-alignment nulls were run.

### Raw TEST MSE gain

Observed:
`Delta_cross = 0.1172847013`

Evaluation-alignment null:
- median: **0.1168030388**
- max: **0.1175615742**

Observed does **not** exceed the null maximum.

### Within-donor-centered TEST variation

To remove donor-level offsets, true tau and each model prediction were independently centered within each NPH52 donor for each query coordinate before MSE scoring.

Observed within-donor delta:
**+0.03669835**

Evaluation-alignment null:
- median: **+0.03590484**
- max: **+0.03715447**

Observed again does **not** exceed the null maximum.

Between-donor-mean diagnostic:
- shortcut mean-level MSE: 1.47933
- molecular mean-level MSE: 1.12170
- delta: **+0.24176**

Thus a large fraction of TD50's primary cross-source gain is explained by donor/source-distribution calibration rather than correct-cell molecular alignment.

## Interpretation

TD50 demonstrates that the broad ordinal context carries transferable source/donor calibration information about query tau.

It does **not** establish that the correct held-out NPH52 cell's molecular context carries qualification-bearing complementary information, because matched within-donor/operator/depth reassignment reproduces the gain.

The post-freeze adversarial audit does not rewrite the prospective TD50 primary terminal. It blocks scientific promotion beyond that terminal.

Binding promotion status:
`TD50_PRIMARY_PASS_BUT_TEST_CELL_ALIGNMENT_FAILS__QUERY_ORDINAL_TARGET_UNQUALIFIED`

## Next target requirement

Any successor must make the held-out-cell alignment null qualification-bearing from the start and reduce the population-order floor before target formation.

No target authority or JEPA training authorization.
