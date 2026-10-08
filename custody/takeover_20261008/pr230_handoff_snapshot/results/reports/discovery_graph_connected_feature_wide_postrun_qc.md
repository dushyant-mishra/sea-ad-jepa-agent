# Graph-Connected Feature-Wide Post-Run QC

## Completion Checks

- Rows: **2,676** (`PASS`; expected 2,676)
- Unique graph-connected genes: **2,676** (`PASS`)
- Scope is `graph_connected` for every row: **True**
- Manifest reports 27 completed/reused chunks: **True**
- Manifest reports 0 failed chunks: **True**

## Perturbation Success

| perturbation_success | count |
| --- | ---: |
| True | 2,676 |

## Missing Pathology Deltas

| delta column | missing values |
| --- | ---: |
| AT8_delta | 0 |
| A_beta_6e10_delta | 0 |
| GFAP_delta | 0 |
| Iba1_delta | 0 |
| NeuN_delta | 0 |

## Manifold-Safety Boundary

| manifold_safety_status | count |
| --- | ---: |
| not_computed | 2,676 |

The full run used `--skip-manifold-nearest-neighbor` because Windows scikit-learn/threadpoolctl crashed inside the nearest-neighbor manifold check. Therefore, the full graph-connected output is valid for pathology-delta ranking and null calibration, but it is **not manifold-verified**.

The successful pilot remains the manifold-verified feature-wide evidence. Any promoted top hit should receive a later targeted manifold audit.

## QC Verdict

**PASS for scorecard construction.** Row count, unique-gene count, chunk completion, perturbation success, and pathology-delta completeness are consistent with a complete run.
