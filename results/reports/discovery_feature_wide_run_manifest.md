# Discovery Feature-Wide Counterfactual Run Manifest

## Run Configuration

- Output: `results\tables\test_resume_feature_wide_tiny.csv`
- Scope: `graph_connected`
- Pilot: `True`
- Resume: `True`
- Start chunk: `1`
- Limit genes: `4`
- Chunk size: `2`
- Batch size: `32`
- Max cells: `200`
- Intervention: `global_mean`
- Run signature: `fcea710d09c9901d`
- Selected genes: 4

## Progress

- Chunks completed or reused: 2
- Chunks failed: 0
- Total elapsed seconds: 0.0
- Total elapsed minutes: 0.0

## Chunk Timing

| chunk | n_genes | status | elapsed_seconds | seconds_per_gene | normalized_path | failure_reason |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | skipped_resume | 0.0 | 0.00 | `results\tables\_feature_wide_counterfactual_chunks\feature_wide_chunk_0001_normalized.csv` |  |
| 2 | 2 | skipped_resume | 0.0 | 0.00 | `results\tables\_feature_wide_counterfactual_chunks\feature_wide_chunk_0002_normalized.csv` |  |

## Claim Boundary

Feature-wide counterfactuals are model-implied perturbation scores over the Graph-JEPA feature-gene universe, not biological intervention evidence and not genome-wide screening.
