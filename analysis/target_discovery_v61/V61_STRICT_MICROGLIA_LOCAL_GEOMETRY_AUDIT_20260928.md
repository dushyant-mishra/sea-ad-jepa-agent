# V61 strict-microglia local-geometry stress test — 2026-09-28

Status: **SUPPORTING DISCOVERY EVIDENCE ONLY**

Question: does the source-balanced common-state backbone contain reproducible structure *within* the strict microglial compartment, or is its apparent biology mainly broad neuron/glia identity?

## Strict mapping

No disease/state label is available in the discovery freeze, so this test is unsupervised. The primary mapping was fixed before scoring:

- HVS: `native_class == Microglia-PVM` — 128 cells, 23 donors
- NPH52: `native_class == MG` — 304 cells, 16 donors
- SEA-AD: `native_class == Microglia-PVMSubclass` — 233 cells, 27 donors

SEA-AD `Immune` was **not** included in the primary mapping. A broader immune-inclusive mapping was sensitivity-only because it can improve power by mixing cell states.

## A/B diagnostic

Using the existing V61 source-balanced backbone scores:

- strict mapping: A=251 cells, B=414 cells
- leading local covariance direction cosine: **0.9395**
- top-2 mean cosine: **0.7429**, minimum **0.5011**

The A/B split is badly imbalanced for HVS microglia (9 vs 119), so this is not the decision-relevant result.

## Donor-disjoint primary stress

Donors were deterministically SHA-256 split within each source:

- HVS: 12 vs 11 donors
- NPH52: 8 vs 8 donors
- SEA-AD: 14 vs 13 donors
- strict-microglia cells: 379 vs 286
- donor overlap: exactly zero

Within each donor half, covariance was computed in the first 12 dimensions of the already-frozen V61 common backbone, centered within source, and the three source covariances were equal-weight averaged. No labels were used.

Principal-angle recurrence:

| local rank | mean cosine | minimum cosine |
|---:|---:|---:|
| 1 | 0.7682 | 0.7682 |
| 2 | 0.8790 | 0.7749 |
| 3 | 0.8563 | 0.6302 |
| 4 | 0.8039 | 0.2709 |
| 5 | 0.7967 | 0.1792 |
| 6 | 0.8771 | 0.3948 |

## Interpretation

There is reproducible low-dimensional within-microglia structure, especially at local rank 2, so the backbone is not explained solely by broad neuron-versus-glia identity.

However, the deeper local geometry is unstable. This result does **not** justify defining a multi-dimensional microglial target from RNA alone, does not supply disease-state semantics, and does not defeat same-RNA latent technical non-identifiability.

The intended use remains: a common RNA state backbone that may be **conditioned/constrained by independently frozen external regulatory object E**, followed by prospective synthetic specificity qualification.

No Corces target overlap was inspected here. No protected molecular outcome was opened.

`TRAINING=OFF`  
`TD60=BLOCKED`
