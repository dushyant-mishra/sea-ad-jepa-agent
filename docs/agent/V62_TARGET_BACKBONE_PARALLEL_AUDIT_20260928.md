# V62 — parallel target-backbone discovery audit

**Status:** `DISCOVERY_CANDIDATE_ONLY` — not biological specificity, not q-safety, not training authority.

This lane uses only the authenticated 50k discovery expression freeze and calibration/provenance metadata. No held-out/dev/sealed expression and no protected regulatory molecular outcome were opened.

## Authenticated inputs

- reconstructed discovery ZIP SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- inner discovery NPZ SHA-256 `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`
- sample freeze SHA-256 `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`
- address namespace SHA-256 `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- measurement support SHA-256 `ee5d12c144536efdacb983f6b9aa2acb46d47d395b2aa9c556ad10b191f3cdaa`

## Candidate construction

The candidate backbone is learned from protein-coding addresses measured in all 42 operators. Feature ranking is performed on discovery half A only, by equal-weight average within-source variance across HVS, NPH52 and SEA-AD. Within each source, genes are centered, a detected-address-count QC proxy is linearly removed, residual genes are scaled, and source covariances are averaged with equal source weight.

This is deliberately not a pooled PCA: the project already established that pooled source/operator geometry is non-identifying.

## Independent A/B result

At rank 4, independently fitted A and B source-balanced bases have:

- mean principal-angle cosine **0.9951**
- minimum principal-angle cosine **0.9907**

Rotation-invariant trace-variance fractions at rank 4:

| half | biology within source | source | donor after source+class | SEA-AD operator after class |
|---|---:|---:|---:|---:|
| A | 0.3815 | 0.0149 | 0.0830 | 0.1317 |
| B | 0.3515 | 0.0260 | 0.1530 | 0.1176 |

## Donor-disjoint stress test

Each source's donors were deterministically split into disjoint halves before fitting either basis:

- HVS 21 vs 20 donors
- NPH52 9 vs 8
- SEA-AD 23 vs 23
- 25,940 vs 24,060 cells
- donor overlap exactly zero

At rank 4, independent donor-half bases have mean cosine **0.9869** and minimum **0.9613**.

Projecting the half-1 basis onto entirely held-out half-2 donors gives:

- biology within source **0.3895**
- source **0.0363**
- donor residual after source+class **0.1168**
- SEA-AD operator residual after class **0.1361**

At rank 8, held-out values are biology **0.3610**, source **0.0268**, donor residual **0.0956**, SEA-AD operator residual **0.1030**.

The common subspace therefore does not look like simple donor memorization.

## Important limits

This does **not** defeat the V48 semantic-twin result. A same-cell latent technical variable could still mimic RNA-only state. The candidate remains a cell-state backbone requiring independently frozen external regulatory information for specificity.

It is also **not q-safe**. The discovery freeze is already normalized with the historical library denominator; token deletion alone cannot establish q-safety. Any production successor must use either `q_excluded_total__q_token_dropped` or `fixed_reference__q_token_dropped`, and teacher target determination must be independently Q-blind.

No rank is frozen here and no individual component is post-hoc selected.

## Reproducibility note

The parameterized donor-disjoint producer was rerun in this environment; its numeric payload reproduced exactly, with the only JSON difference being the added producer SHA-256 field. A second full source-balanced rerun exceeded this environment's memory ceiling and was killed; that execution failure is recorded and no scientific conclusion is inferred from it.

## Current interpretation

`DISCOVERY_CANDIDATE__SOURCE_BALANCED_COMMON_STATE_BACKBONE`

The intended architecture remains:

`common source-balanced RNA state backbone + independently frozen query-specific regulatory geometry`

`TRAINING=OFF`  
`TD60=BLOCKED`
