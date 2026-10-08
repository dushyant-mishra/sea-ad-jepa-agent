# Strict-Shuffled Graph Ablation Training Run Manifest v1

## Run status

| stage | status | checkpoint_path | checkpoint_exists | checkpoint_size_mb | history_exists | log_exists |
| --- | --- | --- | --- | --- | --- | --- |
| stage_a | completed_cleanly | results\models\ablation_strict_shuffled_graph_stage_a_v1\fast_graph_jepa_epoch_030.pt | True | 1.587 | True | True |
| stage_b_adversarial | completed_cleanly | results\models\ablation_strict_shuffled_graph_stage_b_v1\stage_b_adversarial.pt | True | 1.72 | True | True |

Stage A completed. Stage B completed.

## Graph invariant checks

- Edge CSV: `results\tables\ablation_edge_sets\strict_shuffled_graph_edges_v1.csv`
- Edge count: 114,029
- Original-edge overlap: 0 (0.0%)
- Degree preserving: `True`
- Self-loops: 0
- Duplicate undirected edges: 0

## Commands used

### Stage A

`conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_a_fast.py --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad --edge-csv results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv --out-dir results/models/ablation_strict_shuffled_graph_stage_a_v1 --epochs 50 --seed 7 --history-csv results/tables/ablation_strict_shuffled_graph_stage_a_v1_history.csv --log-file results/logs/ablation_strict_shuffled_graph_stage_a_v1.log`

### Stage B

`conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_b_adversarial.py stage_a_checkpoint=results/models/ablation_strict_shuffled_graph_stage_a_v1/fast_graph_jepa_epoch_030.pt edge_csv=results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv out_dir=results/models/ablation_strict_shuffled_graph_stage_b_v1 history_csv=results/tables/ablation_strict_shuffled_graph_stage_b_v1_history.csv log_file=results/logs/ablation_strict_shuffled_graph_stage_b_v1.log seed=7`

## Checkpoint tracking policy

Checkpoint files remain untracked. Repository policy ignores `results/` by default and selectively tracks lightweight tables, reports, histories, and logs; no `.pt` checkpoint files were staged.

## Boundary

- The old partial non-strict log `results\logs\ablation_shuffled_graph_stage_a_v1.log` was not reused.
- No external validation was run.
- No downstream strict-shuffled evaluation was run yet.
- Evidence levels and the strict Level-2 gliosis criterion are unchanged.
