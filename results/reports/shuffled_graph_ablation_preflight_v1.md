# Shuffled-Graph Ablation Training Preflight v1

## Outcome

- Pass: 15
- Warning: 0
- Fail: 0
- Training run: no.

This preflight checks readiness only. Biological topology has not yet been compared with the degree-preserving shuffled topology.

## Checks

| check_name | status | observed | expected | notes |
| --- | --- | --- | --- | --- |
| shuffled_edge_file_exists | pass | True | True | results\tables\ablation_edge_sets\shuffled_graph_edges_v1.csv |
| shuffled_edge_count | pass | 114029 | 114029 | The source file stores each undirected edge once. |
| shuffled_zero_duplicate_edges | pass | 0 | 0 | Exact stored source-target pairs. |
| shuffled_zero_self_loops | pass | 0 | 0 | Self-loops are not part of the shuffled source edge set. |
| shuffled_node_coverage | pass | indexed_node_count=2957; incident_nodes=2676; degree_zero_nodes=281 | 2,957-node indexed feature space | The CSV spans indices 0-2956. Degree-zero nodes have no inter-gene rows but remain represented because the loader infers 2,957 nodes and adds self-loops. |
| manifest_degree_preserving | pass | True | True | results\tables\ablation_edge_sets\graph_ablation_edge_set_manifest_v1.csv |
| manifest_shuffle_seed | pass | 20260619 | 20260619 | results\tables\ablation_edge_sets\graph_ablation_edge_set_manifest_v1.csv |
| original_edge_overlap_recorded | pass | 0.243929 | approximately 0.2439 (24.39%) | NetworkX double-edge swap; 5 requested swaps per edge; original-edge overlap fraction=0.243929. |
| h5ad_exists | pass | True | True | data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad |
| stage_a_training_script_exists | pass | True | True | scripts\train_graph_jepa_stage_a_fast.py |
| stage_b_training_script_exists | pass | True | True | scripts\train_graph_jepa_stage_b_adversarial.py |
| required_stage_a_help_flags_present | pass | returncode=0; missing=[] | all required flags present | Help queried in the sea-ad-jepa Conda environment. |
| stage_a_output_directory_checked | pass | exists=False; finished_checkpoints=[] | no finished checkpoint | results\models\ablation_shuffled_graph_stage_a_v1 |
| stage_b_output_directory_checked | pass | exists=False; finished_checkpoints=[] | no finished checkpoint | results\models\ablation_shuffled_graph_stage_b_v1 |
| no_training_run | pass | stage_a_finished=[]; stage_b_finished=[] | no shuffled-graph finished checkpoints | Preflight only. The required approval string was not supplied. |

## Exact Stage A command for a separately approved future run

```powershell
conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_a_fast.py --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad --edge-csv results/tables/ablation_edge_sets/shuffled_graph_edges_v1.csv --out-dir results/models/ablation_shuffled_graph_stage_a_v1 --epochs 50 --seed 7 --history-csv results/tables/ablation_shuffled_graph_stage_a_v1_history.csv --log-file results/logs/ablation_shuffled_graph_stage_a_v1.log
```

## Exact Stage B command template

Run only after Stage A completes and its epoch 30 checkpoint, history, and log have been verified.

```powershell
conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_b_adversarial.py stage_a_checkpoint=results/models/ablation_shuffled_graph_stage_a_v1/fast_graph_jepa_epoch_030.pt edge_csv=results/tables/ablation_edge_sets/shuffled_graph_edges_v1.csv out_dir=results/models/ablation_shuffled_graph_stage_b_v1 history_csv=results/tables/ablation_shuffled_graph_stage_b_v1_history.csv log_file=results/logs/ablation_shuffled_graph_stage_b_v1.log seed=7
```

## Frozen run conditions

- Edge CSV: `results\tables\ablation_edge_sets\shuffled_graph_edges_v1.csv`
- Stage A output: `results\models\ablation_shuffled_graph_stage_a_v1`
- Stage B output: `results\models\ablation_shuffled_graph_stage_b_v1`
- Seed: `7`
- Stage A epochs: `50`
- Stage B initialization: Stage A epoch `30`
- No external validation data are part of these commands.

## Boundary

- `APPROVED_SHUFFLED_GRAPH_TRAINING` was not present in the request.
- No training command was executed.
- No expression-only autoencoder was trained.
- No external validation was run.
- Evidence levels and the strict Level-2 gliosis criterion are unchanged.
