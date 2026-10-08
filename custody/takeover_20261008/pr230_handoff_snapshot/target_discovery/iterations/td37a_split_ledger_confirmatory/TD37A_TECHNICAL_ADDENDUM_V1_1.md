# TD37A technical execution addendum v1.1

Status: PROSPECTIVE_TECHNICAL_BINDING__NO_OUTCOME_INSPECTED
Parent freeze: TD37A_PROSPECTIVE_FREEZE.md
Date: 2026-09-08

This addendum resolves execution details that were not numerically explicit in the parent freeze. It does not change the scientific estimand, panels, donor splits, null family, or gates.

## Hash integer convention
`SHA256_U64(text)` means:
- UTF-8 encode the exact text;
- SHA-256 digest;
- take digest bytes 0..7;
- interpret as unsigned big-endian 64-bit integer.

## Ordinal rank fractions for null matching
Within each donor×operator stratum of size n:
- rank detected by lexicographic (detected_genes, global_row);
- rank library by lexicographic (source_library, global_row);
- ordinal ranks are 0..n-1 with no averaging;
- rank fraction = ordinal_rank / n, therefore lies in [0,1);
- detected octile = floor(8 * detected_rank_fraction), exactly one of 0..7.
Rows are then sorted by:
`(detected_octile, library_rank_fraction, detected_rank_fraction, global_row)`.

## Block construction
Inside each donor×operator stratum, after the above sort:
- if n=1, make one singleton block;
- otherwise take consecutive blocks of 8;
- if the last remainder has size 1, append it to the immediately preceding block, giving size 9;
- other remainders 2..7 remain their own final block.
Block index b is the zero-based block order within that donor×operator stratum.

## Cyclic null shift
For block size m>=2:
`shift = 1 + SHA256_U64("TD37A|null|<j>|source|<s>|donor|<d>|operator|<o>|block|<b>") mod (m-1)`.
Y is cyclically shifted forward by `shift` positions relative to the sorted X row order.
Singleton blocks self-pair and their row fraction is reported.

## Empirical p95 convention
With N=64 null replicates, sort the 64 null statistics ascending.
`null_p95 = sorted_null[ceil(0.95*N)-1]`.
For N=64 this is zero-based index 60.
PASS uses strict `observed > null_p95`.
No interpolated quantile is used.

## Exact top-16 CCA numerical implementation
The scientific model remains regularized linear CCA.

For speed, the implementation may compute the leading 16 singular triplets of whitened cross-covariance M exactly through the symmetric eigendecomposition of `M M^T`:
- obtain the largest 16 eigenpairs;
- singular values are square roots of nonnegative eigenvalues;
- right singular vectors are `v_j = M^T u_j / s_j` for s_j > numerical floor;
- canonical coefficients are constructed exactly as in the SVD formulation.

Before the first scientific fit, compare this route against full dense SVD on deterministic synthetic 256x256 matrices and require:
- max absolute singular-value difference <= 1e-10;
- absolute canonical subspace projector difference (spectral norm) <= 1e-8 for the leading 16-dimensional subspace.
If the check fails, use full SVD; do not relax tolerances post hoc.

## Numerical floors
- gene variance floor remains 1e-8 as parent freeze;
- PSD inverse-square-root eigenvalue floor = max(1e-10, 1e-10 * max_eigenvalue);
- singular values <=1e-12 are treated as non-estimable components; any requested prefix containing one is NOT_MEASURABLE for that fit and cannot PASS.

No A-sample label-free scientific statistic had been inspected before this addendum was committed.
