# Strict-Shuffled Graph Ablation Training Commands v1

## Approval and frozen inputs

- Approval: `APPROVED_STRICT_SHUFFLED_GRAPH_TRAINING`
- Seed: `7`
- H5AD: `data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad`
- Edge CSV: `results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv`
- Original-edge overlap: `0%`
- Degree sequence: exactly preserved
- External data: none

The historical partial log at
`results/logs/ablation_shuffled_graph_stage_a_v1.log` belongs to the obsolete,
non-strict shuffled attempt and is not reused.

## Stage A command

```powershell
conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_a_fast.py --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad --edge-csv results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv --out-dir results/models/ablation_strict_shuffled_graph_stage_a_v1 --epochs 50 --seed 7 --history-csv results/tables/ablation_strict_shuffled_graph_stage_a_v1_history.csv --log-file results/logs/ablation_strict_shuffled_graph_stage_a_v1.log
```

Stage B may proceed only after verifying:

- `results/tables/ablation_strict_shuffled_graph_stage_a_v1_history.csv`
- `results/logs/ablation_strict_shuffled_graph_stage_a_v1.log`
- `results/models/ablation_strict_shuffled_graph_stage_a_v1/fast_graph_jepa_epoch_030.pt`

## Stage B command

```powershell
conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_b_adversarial.py stage_a_checkpoint=results/models/ablation_strict_shuffled_graph_stage_a_v1/fast_graph_jepa_epoch_030.pt edge_csv=results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv out_dir=results/models/ablation_strict_shuffled_graph_stage_b_v1 history_csv=results/tables/ablation_strict_shuffled_graph_stage_b_v1_history.csv log_file=results/logs/ablation_strict_shuffled_graph_stage_b_v1.log seed=7
```

## Boundary

- These commands train only the strict-shuffled Graph-JEPA ablation.
- No downstream evaluation is included.
- No expression-only autoencoder or external validation is included.
- Evidence levels and the strict Level-2 gliosis criterion remain unchanged.
