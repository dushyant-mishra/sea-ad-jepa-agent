# No-Graph Ablation Training Run Manifest v1

## Run status

| stage | status | checkpoint_path | checkpoint_exists | checkpoint_size_mb | history_exists | log_exists |
| --- | --- | --- | --- | --- | --- | --- |
| stage_a | completed_cleanly | results\models\ablation_no_graph_stage_a_v1\fast_graph_jepa_epoch_030.pt | True | 1.587 | True | True |
| stage_b_adversarial | completed_cleanly | results\models\ablation_no_graph_stage_b_v1\stage_b_adversarial.pt | True | 1.72 | True | True |

Both training stages completed cleanly according to their full epoch histories and terminal checkpoint-write messages.

## Commands used

### Stage A

`conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_a_fast.py --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad --edge-csv results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv --out-dir results/models/ablation_no_graph_stage_a_v1 --epochs 50 --seed 7 --history-csv results/tables/ablation_no_graph_stage_a_v1_history.csv --log-file results/logs/ablation_no_graph_stage_a_v1.log`

### Stage B adversarial calibration

`conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_b_adversarial.py stage_a_checkpoint=results/models/ablation_no_graph_stage_a_v1/fast_graph_jepa_epoch_030.pt edge_csv=results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv out_dir=results/models/ablation_no_graph_stage_b_v1 history_csv=results/tables/ablation_no_graph_stage_b_v1_history.csv log_file=results/logs/ablation_no_graph_stage_b_v1.log seed=7`

## Stage A outputs

- Output directory: `results\models\ablation_no_graph_stage_a_v1`
- Frozen Stage B initialization: `results\models\ablation_no_graph_stage_a_v1\fast_graph_jepa_epoch_030.pt`
- History: `results\tables\ablation_no_graph_stage_a_v1_history.csv` (50 epochs)
- Log: `results\logs\ablation_no_graph_stage_a_v1.log`

## Stage B outputs

- Output directory: `results\models\ablation_no_graph_stage_b_v1`
- Final checkpoint: `results\models\ablation_no_graph_stage_b_v1\stage_b_adversarial.pt`
- History: `results\tables\ablation_no_graph_stage_b_v1_history.csv` (20 epochs)
- Log: `results\logs\ablation_no_graph_stage_b_v1.log`

## Edge-set definition

`results\tables\ablation_edge_sets\no_graph_identity_edges_v1.csv` contains exactly 2,957 explicit self-loop rows and zero inter-gene edges. Under the current loader this preserves all feature nodes while making normalized graph propagation the identity.

## Checkpoint tracking policy

Model checkpoint files are intentionally left untracked. Repository policy ignores `results/` by default and selectively tracks lightweight tables and reports; no files under `results/models/` are currently tracked.

## Input and training boundaries

- The commands used only the frozen local training inputs; no external validation data were used.
- No shuffled-graph training output directory or checkpoint was created by this run.
- No expression-only autoencoder training output was created by this run.
- This artifact freezes training metadata only; downstream predictive evaluation is not included.
- Evidence levels are unchanged.
