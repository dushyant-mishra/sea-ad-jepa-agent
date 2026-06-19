# Graph Ablation Edge-Set Manifest v1

## Original graph summary

- Source: `results\tables\v2_graph_consensus_edges.csv`
- Model nodes: 2957
- Undirected edges stored once: 114029
- Original self-loops: 0
- Original duplicate undirected edges: 0

## No-graph / identity definition

- Path: `results\tables\ablation_edge_sets\no_graph_identity_edges_v1.csv`
- Rows: 2957 explicit self-loops, one for each model feature.
- Rationale: an empty edge file causes the current loader to infer only one node. Explicit self-loops retain all features while removing informative inter-gene message passing.
- The loader symmetrizes and adds self-loops again, but sparse coalescing and degree normalization still produce identity propagation.
- Readiness: `ready_for_future_approval_gated_training`.

## Shuffled graph definition

- Path: `results\tables\ablation_edge_sets\shuffled_graph_edges_v1.csv`
- Seed: 20260619
- Method: deterministic NetworkX double-edge swap on a simple undirected graph.
- Degree preserving: yes, exactly for every node.
- Edge count preserved: 114029
- Self-loops: none.
- Duplicate undirected edges: none.
- Original-edge overlap fraction after shuffle: 0.243929
- Readiness: `ready_for_future_approval_gated_training`.

## Future training command templates

No-graph Stage A:

```text
python scripts/train_graph_jepa_stage_a_fast.py --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad --edge-csv results\tables\ablation_edge_sets\no_graph_identity_edges_v1.csv --out-dir results/models/ablation_no_graph_stage_a_v1 --epochs <epochs> --seed <seed> --history-csv results/tables/ablation_no_graph_stage_a_v1_history.csv --log-file results/logs/ablation_no_graph_stage_a_v1.log
```

Shuffled-graph Stage A:

```text
python scripts/train_graph_jepa_stage_a_fast.py --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad --edge-csv results\tables\ablation_edge_sets\shuffled_graph_edges_v1.csv --out-dir results/models/ablation_shuffled_graph_stage_a_v1 --epochs <epochs> --seed <seed> --history-csv results/tables/ablation_shuffled_graph_stage_a_v1_history.csv --log-file results/logs/ablation_shuffled_graph_stage_a_v1.log
```

## Boundary

- No training was run.
- These files are frozen inputs for future approval-gated ablations.
- Preparing edge sets does not change evidence levels or scientific claims.
