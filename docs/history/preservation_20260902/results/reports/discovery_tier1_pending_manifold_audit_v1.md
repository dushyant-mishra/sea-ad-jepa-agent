# Pending Tier-1 Targeted Manifold Audit v1

## Result

- Genes audited: 19
- Torch-backend perturbations successful: 19/19
- `manifold_safe`: 19

| gene | therapeutic_like_score_percentile | mean_nearest_real_cell_distance | p95_nearest_real_cell_distance | baseline_nn_p95_threshold | manifold_violation_fraction | manifold_qc_status |
| --- | --- | --- | --- | --- | --- | --- |
| TMEM165 | 98.1315 | 0.00276252 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| ATRX | 98.0194 | 0.00281482 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| ZRANB2 | 97.9821 | 0.00271535 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| VPS39 | 97.87 | 0.00278013 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| CSMD3 | 97.7205 | 0.00277309 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| SLC38A2 | 97.6084 | 0.00269384 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| MTX2 | 97.5336 | 0.00277719 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| MAP3K7 | 97.4589 | 0.00276142 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| NSF | 97.1973 | 0.0027371 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| RPLP1 | 97.0105 | 0.00271532 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| CAMK2G | 96.4499 | 0.00276032 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| UBE2E3 | 96.4126 | 0.00272916 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| ZKSCAN1 | 96.3752 | 0.00273707 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| SYT1 | 96.3378 | 0.0027852 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| EIF2AK4 | 96.1883 | 0.00281253 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| LPIN2 | 95.6652 | 0.00276757 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| TCERG1 | 95.3662 | 0.00278894 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| WIPF2 | 95.3288 | 0.00273919 | 0.00956832 | 0.0174693 | 0 | manifold_safe |
| UBA3 | 95.142 | 0.00278122 | 0.00956832 | 0.0174693 | 0 | manifold_safe |

## Interpretation boundary

This completes targeted manifold QC for all previously pending Tier-1 candidates if every row is classified as `manifold_safe`, `borderline_manifold_shift`, or `manifold_violation_warning` rather than `not_computed`.

Manifold QC is technical latent-support QC. It does not prove biological relevance, causal mechanism, druggability, spatial plaque proximity, or therapeutic efficacy.
