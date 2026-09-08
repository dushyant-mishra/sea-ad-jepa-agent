# TD51S closure — aggregate alignment pass does not survive donor recurrence

Status: `TD51S_AGGREGATE_ALIGNMENT_PASS__DONOR_RECURRENCE_FAILS__TARGET_UNQUALIFIED`

Prospective freeze: `4032eefb6968f168a4fa1a19ab0ce18429172167`

## Frozen aggregate screen

TRAIN = pooled A_NATURAL_MIXTURE HVS + SEA_AD.
TEST = A_NATURAL_MIXTURE NPH52.
Target = TRAIN-prior-balanced query ordinal innovation:
`z_iq = sum_r (1-mu_qr^2) * (s_iqr-mu_qr) / sum_r (1-mu_qr^2)`.

All 64 target coordinates were measurable.
Selected ridge multipliers:
- shortcut: 0.001
- molecular: 1

Equal-donor NPH52 TEST:
- shortcut MSE: **3.8057814260**
- correct-cell molecular MSE: **3.3984090851**
- observed Delta: **0.1070403934**

64 donor/operator/depth/detection matched wrong-cell evaluation-context nulls:
- median Delta: **0.1064352760**
- maximum Delta: **0.1069955031**
- observed-minus-null-max: **+0.0000448903**

Thus the literal aggregate TD51S rule is narrowly satisfied.

## Mandatory donor-primary adversarial audit

Because donor is the primary biological unit and the aggregate margin is only 4.49e-05, a second implementation reconstructed the model, target standardization, null permutations and per-donor MSEs independently.

Independent aggregate reconstruction exactly reproduces the producing result:
- shortcut MSE: 3.8057814260
- molecular MSE: 3.3984090851
- Delta: 0.10704039335
- null median: 0.10643527603
- null max: 0.10699550310

Shortcut and molecular target centering/scaling are exactly identical (max mean/SD difference 0).

Per-donor matched-context support across 17 NPH52 donors:
- correct-cell Delta > donor-specific null median: **10/17**
- correct-cell Delta > donor-specific null maximum: **0/17**
- median donor margin over donor null median: approximately **+0.000676** in Delta units
- donor margins over null median range approximately **-0.003899 to +0.003761**

One donor (`human_NPH_906`) has one A-sample cell and therefore no movable matched context; it contributes zero within-donor discrimination rather than a positive result.

Leave-one-donor-out aggregate robustness:
- only **5/17** donor omissions retain observed Delta > all 64 matched wrong-cell nulls;
- **12/17** leave-one-donor-out reconstructions fail;
- LOO margin range approximately **-0.0004204 to +0.0002443**.

Thus the aggregate PASS is not a broad donor-recurrent same-cell effect. It depends on pooling small heterogeneous donor effects and is fragile to donor composition.

## Decision

Do not advance TD51S to train-null/source replication despite its literal pooled aggregate screen PASS.

Binding interpretation:
`PRIOR_BALANCED_ORDINAL_INNOVATION_HAS_TINY_POOLED_SAME_CELL_ADVANTAGE__DONOR_GENERALIZABILITY_NOT_ESTABLISHED`

This result reinforces the TD50 lesson: population-level ordinal structure is strong and transferable, but the current broad rank-sketch predictor does not yet demonstrate sufficiently donor-recurrent same-cell conditional information.

No target authority, production query/reference set, production weighting, threshold, or JEPA training authorization.

Any successor must make donor-level paired correct-cell advantage qualification-bearing from the outset and must be materially different from the already-failed joint inversion field (TD44–TD47) and broad global rank-sketch mapping (TD48–TD51).