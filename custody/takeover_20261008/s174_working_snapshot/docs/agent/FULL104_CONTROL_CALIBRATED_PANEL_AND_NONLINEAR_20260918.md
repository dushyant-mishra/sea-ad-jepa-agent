# FULL104 control-calibrated panel size and nonlinear sampling — 2026-09-18

Status: prospective design repair; terminal masking-policy outcomes unopened; training off.

The prior successors made two outcome-blind but under-justified engineering choices:

- 128 targets because it is the next power of two above 104 donors;
- 256 sampled cells per donor for the nonlinear challenge.

Neither number is allowed to become final scientific authority merely because it
is convenient.

## Target-panel rule

The current nested target-count ladder is:

128 -> 256 -> 512 -> 1024

The first rung remains at least as large as the 104 independent donor units.
Targets are nested under the existing deterministic hash-ranked selector.

Only the planted-positive and within-donor shuffled-negative controls, replay,
donor coverage and bootstrap finiteness may be used to choose the rung. Real
masking-policy outcomes remain closed. Stop at the first control-qualified rung.
If none qualifies, fail closed.

The historical 32-target exploratory studies remain planning evidence only. They
show that target sampling contributes material uncertainty; they do not choose a
FULL104 target count.

## Nonlinear donor sampling rule

The new deterministic per-donor cap is calibrated over:

64 -> 128 -> 256 -> 512 -> 1024 cells per donor.

Again, only control evidence may choose the cap. The historical tree-model
capacity (32 screened features, 50 iterations, 15 leaves, L2=1) is retained as a
pre-FULL104 confirmation hypothesis. The new per-donor subsampling cap is not a
historical parameter and therefore must earn authority separately.

This preserves historical findings in the correct role while preventing new
runtime conveniences from becoming hidden FULL104 scientific assumptions.
