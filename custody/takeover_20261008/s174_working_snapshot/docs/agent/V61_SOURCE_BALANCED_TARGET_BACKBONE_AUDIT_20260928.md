# V61 source-balanced target-backbone audit — 2026-09-28

Status: **DISCOVERY_CANDIDATE_ONLY — NOT BIOLOGICALLY QUALIFIED — NOT TRAINING AUTHORITY**

## Inputs

- Reconstructed discovery archive SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- Inner NPZ SHA-256: `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`
- Discovery sample freeze SHA-256: `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`
- Address namespace SHA-256: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- Address measurement support SHA-256: `ee5d12c144536efdacb983f6b9aa2acb46d47d395b2aa9c556ad10b191f3cdaa`

The discovery matrix is 50,000 cells × 41,238 molecular addresses. No held-out/dev/sealed expression was opened.

## Construction audited

1. Restrict to protein-coding addresses measured in all 42 operators (`n=15,758`).
2. Select 400 features using **Sample A only**, ranked by equal-weight average within-source variance across HVS, NPH52 and SEA-AD.
3. Within each source, center genes, regress a cell-level detected-address-count proxy, standardize residual gene variance, and form a source covariance.
4. Average the three source covariances with equal source weight.
5. Eigendecompose the common covariance. Fit Sample A and Sample B independently for stability checks.

The 400-feature width is a computationally constrained audit width, not a scientific optimum. Earlier 1,500-feature execution exceeded this environment's memory ceiling; no result was inferred from that failed execution.

## Structural confounding correction

A prior all-source "operator after class" diagnostic was invalid. In HVS each of 24 operators contains one biological class, and in NPH52 each of 7 operators contains one class. Operator and biology are structurally aliased there. Operator contamination is therefore evaluated only in SEA-AD, where operators contain multiple broad classes. No operator-centering repair is used because it would erase biological structure in HVS/NPH52.

## Rotation-invariant subspace result

Per-PC interpretation is unstable under rotations/eigenvalue swaps, so the decision-relevant audit uses trace-variance fractions for the entire top-k subspace.

For k=3 to 8, Sample A and independent Sample B show reproducible biological structure:

- within-source broad-class trace eta-squared: roughly 0.34–0.38 on both halves;
- source trace eta-squared: roughly 0.01–0.03;
- SEA-AD operator trace eta-squared after class removal: roughly 0.085–0.132;
- donor trace eta-squared after source+class removal decreases with rank but is higher in B than A.

The top-4 subspace is especially stable geometrically: A/B mean principal-angle cosine `0.9951`, minimum `0.9907`. Rank choice is **not frozen** here.

This supports a candidate common biological-state backbone. It does not establish biological specificity against latent technical semantic twins.

## Important q-safety limitation

The discovery freeze contains already-normalized `log1p(raw * 10000 / library)` values. Historical q-intervention evidence showed that dropping q's token does **not** make this normalization q-safe when the denominator or derived QC summaries still include q.

Therefore this candidate cannot receive q-safety authority from this freeze. A future target evaluation must use either:

- `q_excluded_total + q_token_dropped`, or
- `fixed_reference + q_token_dropped`,

and must keep teacher-side target determination q-blind as a separate condition.

## Interpretation

The current result is:

`DISCOVERY_CANDIDATE__SOURCE_BALANCED_COMMON_STATE_BACKBONE`

It is a candidate cell-state backbone to be combined later with an independently frozen external regulatory neighborhood. It is not a final target and does not defeat the V48 same-RNA semantic-twin identifiability result.

## Governance

- `TRAINING=OFF`
- `TD60=BLOCKED`
- protected regulatory molecular outcomes unopened
- no claim of final biological specificity
