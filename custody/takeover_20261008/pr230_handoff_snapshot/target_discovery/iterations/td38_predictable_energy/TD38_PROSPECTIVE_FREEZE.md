# TD38 — Multiscale Split-Ledger Predictable Energy prospective qualification

Status: FALSIFICATION_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

Predecessor: TD38S survived 24/24 rotation-invariant dependence-energy cases after TD37A showed source-specific canonical axes do not transfer.

## Materially new per-cell object

For a source/donor-training block and fixed disjoint gene views X,Y:
M = Wx Cxy Wy
where Wx=(Cxx+lambda_x I)^(-1/2), Wy=(Cyy+lambda_y I)^(-1/2).

For a held-out cell with whitened row vectors xw=x Wx and yw=y Wy define, for fixed m in {1,2,3,4}:

eX_m = xw (M M^T)^m xw^T
eY_m = yw (M^T M)^m yw^T

Equivalently in canonical coordinates:
eX_m = sum_j rho_j^(2m) zX_j^2
eY_m = sum_j rho_j^(2m) zY_j^2.

These energies do not require canonical-axis identity, sign, component matching, K selection, state correspondence, clustering, graph matching, or Procrustes alignment. They are invariant to orthogonal basis changes in either whitened view; in the unregularized population limit the scalar functional is invariant to invertible linear reparameterization of either view.

The candidate per-cell state is the matched multiscale predictable-energy profile, not the CCA axes.

## Input and firewall

Use A_NATURAL_MIXTURE only, global rows 0..24999.
Explicit global_row must be preserved before every merge and is the only CSR row address.
Sample B is not used.
native_class and broad_class are dropped before any discovery statistic.
Common-scalar addresses are the 17,186 addresses MEASURED_SCALAR in all 42 operators.

## Gene panels

Two independent 512-address panels, p in {0,1}, using the same deterministic TD38S rule:
SHA256("TD38S|panel|<p>|address|<g>").
First 256 genes = X; second 256 = Y.

No panel selection occurs from outcomes.

## Donor cross-fitting

Two deterministic donor splits k in {0,1}, using:
SHA256("TD38|split|<k>|source|<s>|donor|<d>").
Alternating ranked donors define H0/H1.
Run both directions H0->H1 and H1->H0.

## Nuisance preprocessing

Within each source/split/direction:
training nuisance model per selected gene:
intercept + log1p(source_library) + log1p(full-row detected_genes) + operator one-hot.
Use equal total donor weight.
Fit nuisance coefficients on training donors only and apply frozen coefficients to train and evaluation cells.
Center/standardize residual genes using weighted training mean/SD, variance floor 1e-8.

Regularization:
lambda = 1e-3 * mean diagonal covariance for each view; no tuning.
PSD inverse-square-root floor max(1e-10, 1e-10*max eigenvalue).

## Held-out same-cell concordance statistic

Fit M on training donors only.

For each held-out cell compute qX_m=log1p(max(eX_m,0)) and qY_m=log1p(max(eY_m,0)), m=1..4.

For each m compute equal-donor weighted Pearson correlation r_m between paired qX_m and qY_m on held-out cells.

Primary scalar:
R_energy = tanh(mean_m atanh(clip(r_m,-0.999999,0.999999))).

No moment is selected or dropped.

## Primary evaluation pairing null

On held-out cells only, permute the Y-view energy rows relative to X using exactly the TD37A v1.1 donor×operator depth/detection block construction and cyclic-shift hash rule, with preimage:
TD38|evalnull|<j>|source|<s>|split|<k>|direction|<dir>|donor|<d>|operator|<o>|block|<b>.

64 null replicates.
The trained M is fixed because the null concerns held-out same-cell correspondence and no evaluation information enters fitting.
Recompute all four r_m and R_energy after each pairing.
null_p95 = sorted null index 60.
PASS_EVAL iff observed R_energy > null_p95 and observed R_energy > 0.

## Training-pairing falsification

For every case, additionally create 16 training nulls by breaking X/Y pairing within the same donor×operator depth/detection blocks before estimating Cxy, using:
TD38|fitnull|<j>|source|<s>|split|<k>|direction|<dir>|donor|<d>|operator|<o>|block|<b>.

Marginal nuisance preprocessing and Cxx/Cyy remain the same; Cxy, M, held-out energies, and R_energy are recomputed.
FIT_NULL_MAX is the maximum R_energy over the 16 complete refits.

PASS_FIT iff observed R_energy > FIT_NULL_MAX.

## Shortcut audit

On held-out cells fit no biological model. Report correlations of each qX_m/qY_m and their mean profile with log_library and log_detected, and operator explained variance. These are descriptive attacks and cannot rescue a failed primary gate.

## Source gate

A source survives only if, for both panels, both splits, and both directions (8/8 cases):
- PASS_EVAL = true;
- PASS_FIT = true.

If any source fails:
NO_DONOR_RECURRENT_PER_CELL_PREDICTABLE_ENERGY__TD38_FAIL

If HVS, NPH52, and SEA_AD all survive:
TD38_LABEL_FREE_PER_CELL_ENERGY_SURVIVES__FREEZE_CROSS_SOURCE_VALIDATION_BEFORE_OPENING_ANNOTATIONS

No annotations may be opened before the label-free terminal is serialized.

No 50k result can authorize training, set production dimension, choose thresholds, or replace full reader_fit qualification.
