# Targeted Manifold Audit Raw-Distance Sanity Check

## Result

- Audited genes: 45
- Torch backend confirmed: `True`
- Genes with zero violation fraction: 45/45
- Baseline NN p95 threshold: 0.01746928
- Required distance fields: complete and non-null.
- Mean and p95 perturbed nearest-neighbor distances: nonzero.

| metric | minimum | median | maximum | n_non_null | all_zero |
| --- | --- | --- | --- | --- | --- |
| mean_nearest_real_cell_distance | 0.0026380573 | 0.0027720558 | 0.0036556618 | 45 | False |
| p95_nearest_real_cell_distance | 0.0095683197 | 0.0095683197 | 0.010334966 | 45 | False |
| baseline_nn_p95_threshold | 0.017469281 | 0.017469281 | 0.017469281 | 45 | False |
| manifold_violation_fraction | 0 | 0 | 0 | 45 | True |

## Interpretation

The zero manifold-violation fractions are a genuine threshold pass rather than a missing-value or all-zero-distance artifact: the underlying distances and positive baseline threshold are populated and nonzero.

This is technical perturbation QC only. It does not provide biological validation, causal evidence, druggability, spatial context, or therapeutic efficacy.
