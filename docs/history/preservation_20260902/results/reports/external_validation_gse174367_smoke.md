# GSE174367 Morabito External Validation

This analysis projects Morabito et al. GSE174367 microglia through the frozen SEA-AD Graph-JEPA v2.1 encoder (`upgrade_fine_08`). It treats the missing Braak/tangle stages 3-4 as a state-transition boundary, so the primary interpretation is early-stage versus late-stage tau pathology rather than a smooth continuous trajectory.

## Projection Setup

- projected microglia: `100`
- donors/samples: `18`
- matched genes: `2924 / 2957`
- missing genes imputed from SEA-AD low-pathology anchor: `33`
- barcode match strategy: `Barcode`
- control-centroid shift applied: `True`
- control-centroid shift L2: `0.5299`

## Cell-Level Distribution

![AT8 trajectory by tangle stage](results/figures/v2_1_gse174367_smoke_at8_trajectory.png)

## Donor-Level Ordinal Correlations

| score | outcome | n_donors | spearman_rho | spearman_p |
| --- | --- | --- | --- | --- |
| trajectory_GFAP_score | plaque_stage_numeric | 16 | 0.1807 | 0.5029 |
| trajectory_Iba1_score | plaque_stage_numeric | 16 | -0.333 | 0.2076 |
| trajectory_NeuN_score | plaque_stage_numeric | 16 | -0.3821 | 0.1441 |
| trajectory_AT8/pTau_score | plaque_stage_numeric | 16 | -0.4709 | 0.06562 |
| trajectory_A beta/6e10_score | plaque_stage_numeric | 16 | -0.4709 | 0.06562 |
| trajectory_GFAP_score | tangle_stage_numeric | 18 | 0.2357 | 0.3465 |
| trajectory_AT8/pTau_score | tangle_stage_numeric | 18 | -0.1244 | 0.6229 |
| trajectory_A beta/6e10_score | tangle_stage_numeric | 18 | -0.1244 | 0.6229 |
| trajectory_Iba1_score | tangle_stage_numeric | 18 | -0.1484 | 0.5568 |
| trajectory_NeuN_score | tangle_stage_numeric | 18 | -0.1713 | 0.4968 |

## Leave-One-Donor-Out Stability

- mean rho: `-0.1235`
- min rho: `-0.2288`
- max rho: `0.0392`

| held_out_donor | n_donors | spearman_rho | spearman_p |
| --- | --- | --- | --- |
| Sample-22 | 17 | -0.2288 | 0.3772 |
| Sample-27 | 17 | -0.2069 | 0.4256 |
| Sample-58 | 17 | -0.1879 | 0.4703 |
| Sample-52 | 17 | -0.1879 | 0.4703 |
| Sample-66 | 17 | -0.18 | 0.4893 |
| Sample-47 | 17 | -0.1608 | 0.5375 |
| Sample-45 | 17 | -0.1452 | 0.5781 |
| Sample-17 | 17 | -0.1452 | 0.5781 |
| Sample-43 | 17 | -0.1452 | 0.5781 |
| Sample-33 | 17 | -0.1425 | 0.5853 |
| Sample-46 | 17 | -0.1425 | 0.5853 |
| Sample-37 | 17 | -0.1195 | 0.6477 |
| Sample-50 | 17 | -0.1195 | 0.6477 |
| Sample-100 | 17 | -0.04697 | 0.8579 |
| Sample-19 | 17 | -0.04112 | 0.8755 |
| Sample-90 | 17 | -0.03138 | 0.9048 |
| Sample-96 | 17 | -0.03138 | 0.9048 |
| Sample-82 | 17 | 0.03922 | 0.8812 |

## Covariate Audit

| level | score | covariate | n | spearman_rho | spearman_p |
| --- | --- | --- | --- | --- | --- |
| cell | trajectory_AT8/pTau_score | Age | 100 | -0.2995 | 0.002466 |
| cell | trajectory_AT8/pTau_score | PMI | 97 | 0.115 | 0.2618 |
| cell | trajectory_AT8/pTau_score | RIN | 100 | 0.1307 | 0.1948 |
| cell | trajectory_AT8/pTau_score | Batch | 100 | -0.2149 | 0.03179 |
| donor | trajectory_AT8/pTau_score | Age | 18 | -0.6215 | 0.005904 |
| donor | trajectory_AT8/pTau_score | PMI | 17 | 0.2824 | 0.2721 |
| donor | trajectory_AT8/pTau_score | RIN | 18 | 0.2788 | 0.2626 |
| donor | trajectory_AT8/pTau_score | Batch | 18 | -0.6008 | 0.008376 |

## Interpretation Boundary

This is external observational validation, not perturbational causal proof. Because GSE174367 contains tangle stages 1, 2, 5, and 6 but not 3 or 4, positive trajectory separation supports cross-cohort early-versus-late tau-state transfer. It should not be over-described as continuous Braak-stage tracking unless intermediate-stage cohorts reproduce the same monotonic relationship.
