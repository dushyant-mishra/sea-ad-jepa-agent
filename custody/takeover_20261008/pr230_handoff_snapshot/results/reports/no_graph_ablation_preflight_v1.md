# No-Graph Ablation Training Preflight v1

**Total Checks**: 13
**Pass**: 13
**Warning**: 0
**Fail**: 0

## ✅ PREFLIGHT PASSED

All critical checks passed. Training is approved to proceed once placeholders are resolved.

## Check Details

| Check Name | Status | Observed | Expected | Notes |
|---|---|---|---|---|
| no_graph_edge_file_exists | ✅ pass | exists | exists | Path: results\tables\ablation_edge_sets\no_graph_identity_edges_v1.csv |
| no_graph_edge_row_count | ✅ pass | 2957 | 2957 |  |
| no_graph_all_self_loops | ✅ pass | 2957 | 2957 |  |
| no_graph_zero_inter_gene_edges | ✅ pass | 0 | 0 |  |
| no_graph_zero_duplicate_edges | ✅ pass | 0 | 0 |  |
| h5ad_exists | ✅ pass | exists | exists | Path: data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad |
| training_script_exists | ✅ pass | exists | exists |  |
| required_help_flags_present | ✅ pass | all present | all present | Checked for: --edge-csv, --out-dir, --epochs, --h5ad, --seed |
| output_directory_checked | ✅ pass | checked | checked | Target dir: results\models\ablations\no_graph_jepa_v1 |
| no_existing_checkpoint_in_out_dir | ✅ pass | empty/no checkpoint | empty/no checkpoint | Warning if checkpoint already exists |
| protocol_exists | ✅ pass | exists | exists |  |
| frozen_command_template_extracted | ✅ pass | extracted | extracted | Command: python scripts/train_graph_jepa_stage_a_fast.py --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad --edge-csv results\tables\ablation_edge_sets\no_graph_identity_edges_v1.csv --out-dir results/models/ablation_no_graph_stage_a_v1 --epochs <MATCHED_EPOCHS> --seed <FROZEN_SEED> --history-csv results/tables/ablation_no_graph_stage_a_v1_history.csv --log-file results/logs/ablation_no_graph_stage_a_v1.log |
| no_training_run | ✅ pass | true | true | Preflight script only inspects files and metadata |

## Extracted Command Template

```bash
python scripts/train_graph_jepa_stage_a_fast.py --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad --edge-csv results\tables\ablation_edge_sets\no_graph_identity_edges_v1.csv --out-dir results/models/ablation_no_graph_stage_a_v1 --epochs <MATCHED_EPOCHS> --seed <FROZEN_SEED> --history-csv results/tables/ablation_no_graph_stage_a_v1_history.csv --log-file results/logs/ablation_no_graph_stage_a_v1.log
```

**Note**: Placeholders `<MATCHED_EPOCHS>` and `<FROZEN_SEED>` must be resolved before execution.

## Boundary

- No training was run.
