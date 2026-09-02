# Discovery Pilot Feature-Wide Counterfactual Validation

## Executive Summary

- Pilot rows: 221
- Successful perturbations: 221
- Failed perturbations: 0
- Missing required columns: none
- Approximate observed runtime: 54.6 minutes
- Approximate runtime per gene: 14.8 seconds/gene

## Manifold Safety

| manifold_safety_status | count |
| --- | --- |
| within_manifold_threshold | 221 |

## Reference Reproduction Check

The pilot is compared against `pathology_head_gene_counterfactual_summary.csv`, the closest existing frozen pathology-head gene counterfactual output. Differences can still arise from sampled cells, target set, or wrapper settings.

| target | n_overlap | sign_agreement | median_abs_diff | spearman |
| --- | --- | --- | --- | --- |
| AT8_delta | 10 | 1 | 8.538e-05 | 1 |
| A_beta_6e10_delta | 10 | 1 | 0.0001025 | 1 |
| GFAP_delta | 10 | 1 | 0.0002143 | 1 |
| Iba1_delta | 10 | 1 | 0.0002056 | 1 |
| NeuN_delta | 10 | 1 | 7.679e-05 | 1 |

## Output Schema

| column | present |
| --- | --- |
| gene | True |
| scope | True |
| AT8_delta | True |
| A_beta_6e10_delta | True |
| GFAP_delta | True |
| Iba1_delta | True |
| NeuN_delta | True |
| manifold_safety_status | True |
| prediction_safety_status | True |
| perturbation_success | True |
| failure_reason | True |

## Claim Boundary

This pilot validates the feature-wide scoring workflow and output schema. It does not validate biological causality. Feature-wide means the Graph-JEPA feature-gene universe, not the whole genome.
