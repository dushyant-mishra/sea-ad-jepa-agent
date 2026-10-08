# TD39S — Pointwise Split-Ledger Excess Concordance fast screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Historical failure attacked
TD38S established source-recurrent rotation-invariant population dependence.
TD38 failed because per-cell quadratic predictable energies remained reproducible under a training broken-pair null, indicating that marginal cell structure could mimic the target.

TD39S therefore uses the paired bilinear cross-term and explicitly subtracts the matched technical-pairing baseline per cell.

## Fixed disjoint molecular panels
From the 17,186 all-operator common-scalar addresses, rank each address g by:
SHA256("TD39S|address|<g>").
Take the first 1,024 unique addresses.
Panel A = positions 0..511.
Panel B = positions 512..1023.
Within each panel, first 256 = X and second 256 = Y.
Panel A and B have zero gene overlap by construction.

## Input / row binding
A_NATURAL_MIXTURE only; global rows 0..24999.
Preserve explicit global_row before merges; only global_row addresses CSR.
Sample B and biological labels are not used.

## Preprocessing and operator fit
Use the TD38 nuisance residualization, equal-donor weighting, standardization, ridge and whitening unchanged.

For a fitted panel:
M = Wx Cxy Wy.
For held-out cell i:
c_i = xw_i M yw_i^T.
This scalar is invariant to orthogonal reparameterization of either whitened view and uses the paired cross-term rather than separate marginal energies.

## Per-cell matched baseline
For the held-out evaluation block, construct 64 TD37A-style donor×operator depth/detection matched cyclic Y permutations with hash:
TD39S|baseline|<panel>|<j>|source|<s>|split|<k>|direction|<dir>|donor|<d>|operator|<o>|block|<b>.

For each cell i, average its 64 permuted bilinear scores to obtain b_i.
Define the per-cell excess concordance target estimate:
t_i = c_i - b_i.

## Fast screen case
Only one prospective necessary-condition case is run:
source HVS, donor split 0, direction H0->H1.

Fit Panel A and Panel B independently on the same training donors.
Compute held-out tA_i and tB_i.

Primary statistic:
R_panel = equal-donor weighted Pearson correlation(tA,tB).

Evaluation null:
permute tB across held-out cells within the same donor×operator depth/detection blocks using 64 deterministic shifts:
TD39S|panelnull|<j>|...
PASS_EVAL iff observed R_panel > null p95 (index 60) and R_panel>0.

Training-pair falsification:
16 complete refits. In each replicate, independently break training X/Y pairing inside Panel A and Panel B using:
TD39S|fitnull|<panel>|<j>|...
Recompute each panel's M, each panel's 64-permutation per-cell baseline, tA/tB, and R_panel.
PASS_FIT iff observed R_panel > maximum of the 16 fit-null R_panel values.

## Kill / survive
If PASS_EVAL or PASS_FIT is false:
NO_PER_CELL_EXCESS_CONCORDANCE_RECURRENCE__TD39S_KILL

If both pass:
TD39S_SURVIVES_FAST_SCREEN__FREEZE_FULL_TD39_BEFORE_MORE_CASES

No labels may be opened. No target/training authority is granted.
