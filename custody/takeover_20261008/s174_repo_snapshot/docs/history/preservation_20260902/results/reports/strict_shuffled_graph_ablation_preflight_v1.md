# Strict-Shuffled Graph Ablation Training Preflight v1

## Outcome

- Pass: 16
- Warning: 1
- Fail: 0
- Training run: no.

- Strict edge file: `results\tables\ablation_edge_sets\strict_shuffled_graph_edges_v1.csv`
- Original-edge overlap: `0`.
- Exact degree preservation: `True`.

## Checks

| check_name | status | observed | expected | notes |
| --- | --- | --- | --- | --- |
| strict_shuffled_edge_file_exists | pass | True | True | results\tables\ablation_edge_sets\strict_shuffled_graph_edges_v1.csv |
| strict_shuffled_edge_count | pass | 114029 | 114029 | Simple undirected edges stored once. |
| strict_shuffled_node_universe | pass | identity_nodes=2957; strict_max_index=2956 | authoritative identity map contains 0-2956; strict max index 2956 | The identity edge file supplies the full index-to-gene map, including degree-zero nodes. |
| degree_sequence_matches_original | pass | True | True | Exact node-wise degree sequence comparison. |
| original_edge_overlap_zero | pass | 0 | 0 | Canonical undirected intersection with the real graph. |
| strict_shuffled_zero_self_loops | pass | 0 | 0 | Required simple-graph invariant. |
| strict_shuffled_zero_duplicate_edges | pass | 0 | 0 | Canonical undirected duplicates. |
| h5ad_exists | pass | True | True | data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad |
| stage_a_training_script_exists | pass | True | True | scripts\train_graph_jepa_stage_a_fast.py |
| stage_b_training_script_exists | pass | True | True | scripts\train_graph_jepa_stage_b_adversarial.py |
| required_stage_a_help_flags_present | pass | returncode=0; missing=[] | all required flags present | Queried in the sea-ad-jepa Conda environment. |
| stage_a_output_directory_checked | pass | exists=False; checkpoints=[] | absent/empty with no checkpoints | results\models\ablation_strict_shuffled_graph_stage_a_v1 |
| stage_b_output_directory_checked | pass | exists=False; checkpoints=[] | absent/empty with no checkpoints | results\models\ablation_strict_shuffled_graph_stage_b_v1 |
| partial_interrupted_logs_checked | warning | old_non_strict_partial_log=True; strict_logs_exist=False | historical partial logs allowed only outside strict paths | `results\logs\ablation_shuffled_graph_stage_a_v1.log` is historical and will not be reused. |
| no_strict_shuffled_checkpoint_exists | pass | False | False | No strict-shuffled model checkpoint may predate approval. |
| no_strict_shuffled_history_exists | pass | [] | [] | No strict-shuffled training history may predate approval. |
| no_training_run | pass | True | True | Preflight only; APPROVED_STRICT_SHUFFLED_GRAPH_TRAINING was absent. |

## Future Stage A command after separate explicit approval

```powershell
conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_a_fast.py --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad --edge-csv results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv --out-dir results/models/ablation_strict_shuffled_graph_stage_a_v1 --epochs 50 --seed 7 --history-csv results/tables/ablation_strict_shuffled_graph_stage_a_v1_history.csv --log-file results/logs/ablation_strict_shuffled_graph_stage_a_v1.log
```

## Future Stage B command after verified Stage A completion

```powershell
conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_b_adversarial.py stage_a_checkpoint=results/models/ablation_strict_shuffled_graph_stage_a_v1/fast_graph_jepa_epoch_030.pt edge_csv=results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv out_dir=results/models/ablation_strict_shuffled_graph_stage_b_v1 history_csv=results/tables/ablation_strict_shuffled_graph_stage_b_v1_history.csv log_file=results/logs/ablation_strict_shuffled_graph_stage_b_v1.log seed=7
```

## Historical partial log

`results\logs\ablation_shuffled_graph_stage_a_v1.log` exists from the interrupted older, non-strict shuffled attempt. It is outside all strict-shuffled paths and must not be reused.

## Boundary

- `APPROVED_STRICT_SHUFFLED_GRAPH_TRAINING` was not present.
- No strict-shuffled training command was executed.
- No expression-only autoencoder was trained.
- No external validation was run.
- Evidence levels and the strict Level-2 gliosis criterion are unchanged.
