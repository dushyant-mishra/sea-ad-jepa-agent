# Discovery Feature-Wide Counterfactual Run Manifest

## Run Configuration

- Output: `results\tables\discovery_targeted_manifold_audit_smoke_v1.csv`
- Scope: `graph_connected`
- Pilot: `False`
- Resume: `False`
- Start chunk: `1`
- Limit genes: `3`
- Chunk size: `3`
- Batch size: `512`
- Max cells: `10000`
- Intervention: `global_mean`
- Manifold NN backend: `torch`
- Manifold query batch size: `512`
- Manifold reference batch size: `2048`
- Run signature: `fa9c6da8435f4470`
- Selected genes: 3

## Progress

- Chunks completed or reused: 1
- Chunks failed: 0
- Total elapsed seconds: 63.0
- Total elapsed minutes: 1.1

## Chunk Timing

| chunk | n_genes | status | elapsed_seconds | seconds_per_gene | normalized_path | log_path | failure_reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3 | completed | 63.0 | 21.01 | `results\tables\_feature_wide_counterfactual_chunks\discovery_targeted_manifold_audit_smoke_v1\feature_wide_chunk_0001_normalized.csv` | `results\tables\_feature_wide_counterfactual_chunks\discovery_targeted_manifold_audit_smoke_v1\feature_wide_chunk_0001.log` |  |

## Claim Boundary

Feature-wide counterfactuals are model-implied perturbation scores over the Graph-JEPA feature-gene universe, not biological intervention evidence and not genome-wide screening.
