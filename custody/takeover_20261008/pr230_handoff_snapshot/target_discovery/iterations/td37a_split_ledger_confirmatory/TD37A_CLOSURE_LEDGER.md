# TD37A — Split-Ledger Canonical Concordance closure ledger

Status: `FALSIFICATION_ONLY__NO_TARGET_AUTHORITY`

Terminal:

`DONOR_RECURRENT_BUT_NOT_CROSS_SOURCE_SPLIT_LEDGER_STATE__TARGET_UNQUALIFIED`

## Binding prospective authority

Parent freeze:
`target_discovery/iterations/td37a_split_ledger_confirmatory/TD37A_PROSPECTIVE_FREEZE.md`

Technical addendum:
`target_discovery/iterations/td37a_split_ledger_confirmatory/TD37A_TECHNICAL_ADDENDUM_V1_1.md`

The clean confirmatory A-sample freeze was committed before any A-sample scientific statistic was inspected. The earlier B-sample TD37 observed run is `QUARANTINED_DIAGNOSTIC_ONLY` because TD37 v1 under-specified the donor-split hash preimage and executable primary-null bin construction.

## Historical predecessor / materially new attack

TD37A was opened only after reconciling:
- TD19/21/22 same-gene dependency failure;
- TD28/29A/30 label-free cluster/graph/diffusion failure;
- TD35/36 corrected variance-defined source/global and class-conditioned subspace failure;
- historical rejection of hidden-gene reconstruction as a biological target.

Materially new object: two disjoint hash-fixed gene views of the same cell provide intrinsic correspondence. Regularized CCA learns only within training donor blocks. Qualification requires donor-block recurrence and then application of the source canonical coefficients unchanged to another source. No state labels, state matching, graph matching, clustering, PCA variance ranking, same-gene edge replication, or hidden-gene reconstruction objective is used.

## Input / firewall audit

Primary confirmatory sample: `A_NATURAL_MIXTURE`, global rows 0–24,999.

Audit:
- rows: 25,000
- A/B stable-key overlap: 0
- annotations dropped before discovery: true
- common-scalar addresses: 17,186
- HVS: 1,129 rows / 41 donors / 23 operators
- NPH52: 1,310 / 17 / 7
- SEA_AD: 22,561 / 46 / 11
- inverse-log1p first-nonzero integer recovery fraction <1e-8: 1.0
- maximum residual: 3.55e-15

TD33 row-binding discipline was preserved. A uses global rows 0–24,999; Sample B was not used for TD37A statistics.

## Numerical preflight

The exact top-16 symmetric-eigendecomposition CCA implementation was compared against full dense SVD on three deterministic 256×256 synthetic matrices before scientific fitting.

- max singular-value difference: `3.91e-14`
- max leading-16 projector spectral-norm difference: `4.20e-14`

Both are far inside the frozen tolerances.

## Within-source donor recurrence

96 complete cases = 4 independent hash panels × 3 sources × 4 donor splits × 2 directions. Every case used 64 complete matched pairing-null refits.

### HVS

No fixed prefix passes the all-8-directions rule in any panel.

Median observed / median null-p95:
- r1: 0.0299 / 0.0864
- r2: 0.0161 / 0.0685
- r4: 0.0322 / 0.0499
- r8: 0.0298 / 0.0361
- r16: 0.0229 / 0.0279

### NPH52

No fixed prefix passes the all-8-directions rule in any panel. Some individual splits show very large observed concordance, but the matched null is also large and the direction-to-direction result is unstable.

Median observed / median null-p95:
- r1: 0.0987 / 0.4888
- r2: 0.2003 / 0.3195
- r4: 0.1455 / 0.1922
- r8: 0.0916 / 0.1184
- r16: 0.0626 / 0.0754

### SEA_AD

SEA_AD passes every fixed prefix in all 4 panels and all 8 split directions.

Median observed / minimum observed / median null-p95:
- r1: 0.8127 / 0.7749 / 0.1189
- r2: 0.7576 / 0.7349 / 0.0804
- r4: 0.7075 / 0.6679 / 0.0580
- r8: 0.5492 / 0.4715 / 0.0397
- r16: 0.3497 / 0.3030 / 0.0271

Within-source terminal:
`WITHIN_SOURCE_RECURRENCE_EXISTS__TRANSFER_REQUIRED`.

This is a real source-internal predictable multigene object under the pilot but is not target authority.

## Frozen-coefficient cross-source transfer

Because SEA_AD passed recurrence, its CCA coefficients were applied unchanged to HVS and NPH52. Target sources received only their own prospectively allowed nuisance residualization/standardization. No target CCA refit, rotation, component matching, sign search, state matching, or graph optimization was allowed.

64 transfer cases = 4 panels × 2 targets × 4 splits × 2 directions, with 64 target matched-pairing nulls per case.

### SEA_AD -> HVS

No prefix has even one panel satisfying all eight transfer directions.

Median transferred correlations are approximately zero:
- r1: 0.00089
- r2: -0.00096
- r4: 0.00039
- r8: -0.00044
- r16: 0.00016

### SEA_AD -> NPH52

Again, no prefix has any panel satisfying all eight directions.

Median transferred correlations are approximately zero:
- r1: 0.000012
- r2: -0.00021
- r4: 0.00072
- r8: -0.00060
- r16: -0.00028

Transfer terminal:
`DONOR_RECURRENT_BUT_NOT_CROSS_SOURCE_SPLIT_LEDGER_STATE__TARGET_UNQUALIFIED`.

## Independent adjudication

A separate adjudicator reconstructed all p95 values and gates directly from the 160 raw case JSONs without importing the producing implementation.

Findings:
- 96/96 within-source cases reconstructed;
- 64/64 transfer cases reconstructed;
- within-source gate reproduced exactly;
- SEA_AD recurrence reproduced for r={1,2,4,8,16};
- HVS/NPH52 recurrence failure reproduced;
- transfer fails with zero passing panels for every target/prefix;
- transfer still fails under the contract-literal `observed > p95` rule even if the producing implementation's additional positivity condition is removed.

Panel overlaps from independent hash-panel reconstruction are small (14–22 genes out of 512 between panel pairs) and do not affect the terminal because transfer has zero all-direction passing panels.

## Interpretation

TD37A establishes an important distinction:

1. A strong, donor-recurrent **source-internal** common-information structure exists in SEA_AD across disjoint gene views.
2. The corresponding linear canonical coordinates are not a cross-source biological coordinate system: applying them unchanged to HVS or NPH52 collapses the signal to approximately zero.
3. Therefore the remaining TD34 annotated cross-source relational scaffold cannot be explained by a simple universal split-view linear latent with transferable coefficients.

This result is consistent with the broader Target Discovery pattern: source-specific coordinate systems can contain real biology without their axes/loadings being universal.

No annotations were opened to rescue or reinterpret TD37A after the label-free terminal. No JEPA training, optimizer, EMA, pathology, reader_validation, reader_oracle, development, or sealed data were used.

## Durability

Key artifact SHA manifest:
`TD37A_ARTIFACT_HASHES.csv` SHA-256 `8433e79cf99d2f35472bb09068a29ecfe811bd0d9170845a0930aa68febb74b3`.

Raw case hash manifest:
`TD37A_CASE_HASHES.csv` SHA-256 `1f4b49b16e89b0ef57e3ccab87089f228a4079b9056c78598e0dbdbac0c0738d` (160 case JSONs).

Local full-results ZIP:
SHA-256 `358fcd921b909f88d819746e48841e3a568a9e16a8bee76cef46011aa26cb592`.

## Next scientific implication

Do not rescue TD37A by source-specific coefficient alignment, rotation, Procrustes, or component matching; those would reopen the correspondence/search degree of freedom that the experiment deliberately removed.

A next candidate must be invariant to source-specific rotations/loadings by construction while remaining a per-cell trainable molecular target and while retaining intrinsic address-based correspondence. A promising direction for prospective review is a **multiscale split-ledger predictable-energy / common-information invariant** rather than transferable canonical axes. Any such iteration must be frozen separately and must again survive donor-block recurrence, depth/support/operator controls, and a structure-preserving null before TD34 labels are opened.
