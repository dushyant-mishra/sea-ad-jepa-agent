# GSE174367 Morabito External Validation

This analysis projects Morabito et al. GSE174367 microglia through the frozen SEA-AD Graph-JEPA v2.1 encoder (`upgrade_fine_08`). It treats the missing Braak/tangle stages 3-4 as a state-transition boundary, so the primary interpretation is early-stage versus late-stage tau pathology rather than a smooth continuous trajectory.

## Projection Setup

- projected microglia: `4126`
- donors/samples: `18`
- matched genes: `2924 / 2957`
- missing genes imputed from SEA-AD low-pathology anchor: `33`
- barcode match strategy: `Barcode`
- control-centroid shift applied: `True`
- control-centroid shift L2: `1.0515`

## Cell-Level Distribution

![AT8 trajectory by tangle stage](../figures/v2_1_gse174367_at8_trajectory_by_tangle.svg)

## Donor-Level Ordinal Correlations

| score | outcome | n_donors | spearman_rho | spearman_p |
| --- | --- | --- | --- | --- |
| trajectory_AT8/pTau_score | plaque_stage_numeric | 16 | 0.0761 | 0.7794 |
| trajectory_A beta/6e10_score | plaque_stage_numeric | 16 | 0.0761 | 0.7794 |
| trajectory_NeuN_score | plaque_stage_numeric | 16 | 0.06183 | 0.82 |
| trajectory_Iba1_score | plaque_stage_numeric | 16 | 0.04122 | 0.8795 |
| trajectory_GFAP_score | plaque_stage_numeric | 16 | -0.09037 | 0.7392 |
| trajectory_AT8/pTau_score | tangle_stage_numeric | 18 | 0.2237 | 0.3723 |
| trajectory_A beta/6e10_score | tangle_stage_numeric | 18 | 0.2237 | 0.3723 |
| trajectory_NeuN_score | tangle_stage_numeric | 18 | 0.1844 | 0.4639 |
| trajectory_Iba1_score | tangle_stage_numeric | 18 | 0.1767 | 0.4829 |
| trajectory_GFAP_score | tangle_stage_numeric | 18 | -0.1997 | 0.427 |

## Leave-One-Donor-Out Stability

- mean rho: `0.2231`
- min rho: `0.1311`
- max rho: `0.3203`

| held_out_donor | n_donors | spearman_rho | spearman_p |
| --- | --- | --- | --- |
| Sample-17 | 17 | 0.1311 | 0.616 |
| Sample-19 | 17 | 0.1311 | 0.616 |
| Sample-22 | 17 | 0.1311 | 0.616 |
| Sample-27 | 17 | 0.1311 | 0.616 |
| Sample-45 | 17 | 0.1619 | 0.5347 |
| Sample-52 | 17 | 0.1853 | 0.4766 |
| Sample-58 | 17 | 0.2074 | 0.4244 |
| Sample-47 | 17 | 0.2209 | 0.3941 |
| Sample-33 | 17 | 0.2288 | 0.3771 |
| Sample-46 | 17 | 0.2288 | 0.3771 |
| Sample-66 | 17 | 0.2296 | 0.3753 |
| Sample-100 | 17 | 0.2518 | 0.3296 |
| Sample-50 | 17 | 0.2712 | 0.2924 |
| Sample-90 | 17 | 0.2889 | 0.2607 |
| Sample-82 | 17 | 0.2889 | 0.2607 |
| Sample-43 | 17 | 0.293 | 0.2537 |
| Sample-37 | 17 | 0.3149 | 0.2183 |
| Sample-96 | 17 | 0.3203 | 0.2101 |

## Early-Versus-Late Transition Boundary

Because stages 3-4 are absent, this table treats Morabito as an early-versus-late tangle-state boundary test.

| score | comparison | n_early_donors | n_late_donors | auc_late_vs_early | rank_biserial_late_minus_early | late_mean | early_mean | mean_difference_late_minus_early |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| trajectory_AT8/pTau_score | tangle_stage_1_2_vs_5_6 | 7 | 11 | 0.6234 | 0.2468 | 0.4641 | 0.3531 | 0.1109 |
| trajectory_A beta/6e10_score | tangle_stage_1_2_vs_5_6 | 7 | 11 | 0.6234 | 0.2468 | 0.3913 | 0.2862 | 0.1051 |
| trajectory_NeuN_score | tangle_stage_1_2_vs_5_6 | 7 | 11 | 0.6104 | 0.2208 | 0.7973 | 0.6661 | 0.1312 |
| trajectory_Iba1_score | tangle_stage_1_2_vs_5_6 | 7 | 11 | 0.5974 | 0.1948 | 1.046 | 0.8967 | 0.1489 |
| trajectory_GFAP_score | tangle_stage_1_2_vs_5_6 | 7 | 11 | 0.3896 | -0.2208 | -1.545 | -1.389 | -0.1561 |

## Covariate Audit

| level | score | covariate | n | spearman_rho | spearman_p |
| --- | --- | --- | --- | --- | --- |
| cell | trajectory_AT8/pTau_score | Age | 4126 | -0.1378 | 6.191e-19 |
| cell | trajectory_AT8/pTau_score | PMI | 3985 | 0.02053 | 0.195 |
| cell | trajectory_AT8/pTau_score | RIN | 4126 | 0.02592 | 0.09595 |
| cell | trajectory_AT8/pTau_score | Batch | 4126 | -0.1398 | 1.806e-19 |
| donor | trajectory_AT8/pTau_score | Age | 18 | -0.2075 | 0.4087 |
| donor | trajectory_AT8/pTau_score | PMI | 17 | 0.1793 | 0.4912 |
| donor | trajectory_AT8/pTau_score | RIN | 18 | -0.04646 | 0.8547 |
| donor | trajectory_AT8/pTau_score | Batch | 18 | -0.2239 | 0.3718 |

## Interpretation Boundary

This is external observational validation, not perturbational causal proof. Because GSE174367 contains tangle stages 1, 2, 5, and 6 but not 3 or 4, positive trajectory separation supports cross-cohort early-versus-late tau-state transfer. It should not be over-described as continuous Braak-stage tracking unless intermediate-stage cohorts reproduce the same monotonic relationship.
