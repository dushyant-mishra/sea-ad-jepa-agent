# TD real G9/S1/S2 geometry recurrence engine V1

Status: prospective, outcome-blind, test-of-test only.

## Unresolved question
Can a common recurrence/stability engine correctly distinguish stable geometry from adverse-null recurrence, instability, alignment leakage, and insufficient donor/source resolution before any human candidate values are opened?

## Historical constraint
Reuse only valid mechanics: donor-primary resampling, principal-angle/canonical subspace comparison, and train-only orthogonal alignment. Do not inherit Stage81A3 thresholds, D=160, 50-PC constants, or old source-specific outcomes.

## Prospective mechanics
1. RED known-truth tests first.
2. Orthogonal-invariant subspace displacement from principal-angle/projector geometry.
3. Procrustes fit only on explicitly disjoint inner-train units; held-out units cannot influence alignment.
4. Per-donor adverse-null advantage = median(null displacement) - observed displacement.
5. Null defeat must exceed independent U_refit in the same metric.
6. Observed displacement must also be noninferior to the independently qualified same-metric stability margin.
7. Required source strata are noncompensating.
8. Underpowered required strata -> NOT_ESTIMABLE.
9. Exact deciding-input binding must match the reference artifact.
10. Known-truth decision qualification required before human FAIL semantics.

No human outcomes are read. No target, representation, TD60, Stage4, EMA, or training authority is granted.