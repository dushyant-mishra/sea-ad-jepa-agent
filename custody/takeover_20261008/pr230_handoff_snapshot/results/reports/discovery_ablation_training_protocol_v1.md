# Discovery Ablation Training Protocol v1

## Scope

This protocol freezes future ablation inputs, fairness requirements, outputs, and evaluation metrics. No training was run.

## Ablations and order

0. `real_graph_reference` — existing frozen comparator.
1. `no_graph_jepa` — first recommended future training; cleanest test of informative graph message passing.
2. `shuffled_graph_jepa` — tests biological topology specificity with preserved degree sequence.
3. `expression_only_autoencoder` — later learned expression comparator after architecture and CLI are frozen.

## Training fairness contract

- Same H5AD: `data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad`
- Exact same 2,957-feature order.
- Same frozen random seed set for matched runs.
- Same latent dimension and encoder capacity where applicable.
- Same Stage A and Stage B epoch schedules, masks, optimization settings, and checkpoint selection.
- Same pathology-head evaluation pipeline.
- Same donor-level cross-validation folds.
- Same downstream scorecard and ranking scripts.
- Same targeted manifold audit settings.
- Same donor-bootstrap robustness and strict gliosis diagnostic.

## Required outputs per trained ablation

- `model_checkpoint`
- `training_history_csv`
- `run_manifest`
- `predictive_representation_comparison`
- `discovery_ranking_calibration`
- `tier1_manifold_audit`
- `internal_robustness_table`
- `gliosis_diagnostic_table`

## Exact comparison metrics

- `mean_oof_spearman`
- `target_specific_oof_spearman`
- `oof_pearson`
- `mae`
- `rmse`
- `cleaner_vs_broad_separation`
- `tier1_overlap`
- `graph_neighborhood_artifact_behavior`
- `manifold_safety`
- `level2_gliosis_robustness`

## Frozen command templates

### real_graph_reference

- Status: `existing_reference`
- Edge set: `results/tables/v2_graph_consensus_edge_index.csv`
- Compute risk: none_for_existing_reference; evaluation only

```text
not_run_existing_checkpoint=results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt
```

### no_graph_jepa

- Status: `not_run_ready_for_approval`
- Edge set: `results\tables\ablation_edge_sets\no_graph_identity_edges_v1.csv`
- Compute risk: high; matched Stage A and Stage B GPU training plus downstream audits

```text
python scripts/train_graph_jepa_stage_a_fast.py --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad --edge-csv results\tables\ablation_edge_sets\no_graph_identity_edges_v1.csv --out-dir results/models/ablation_no_graph_stage_a_v1 --epochs <MATCHED_EPOCHS> --seed <FROZEN_SEED> --history-csv results/tables/ablation_no_graph_stage_a_v1_history.csv --log-file results/logs/ablation_no_graph_stage_a_v1.log
```

### shuffled_graph_jepa

- Status: `not_run_ready_for_approval`
- Edge set: `results\tables\ablation_edge_sets\shuffled_graph_edges_v1.csv`
- Compute risk: high; matched multi-seed training recommended to assess topology specificity

```text
python scripts/train_graph_jepa_stage_a_fast.py --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad --edge-csv results\tables\ablation_edge_sets\shuffled_graph_edges_v1.csv --out-dir results/models/ablation_shuffled_graph_stage_a_v1 --epochs <MATCHED_EPOCHS> --seed <FROZEN_SEED> --history-csv results/tables/ablation_shuffled_graph_stage_a_v1_history.csv --log-file results/logs/ablation_shuffled_graph_stage_a_v1.log
```

### expression_only_autoencoder

- Status: `not_run_requires_design_and_script_readiness`
- Edge set: `not_applicable`
- Compute risk: high_and_architecturally_divergent; requires new objective and fairness review

```text
not_available_until_expression_only_architecture_and_cli_are_frozen
```


## Approval gate

Before any training, require:

- explicit user approval;
- a command with no unresolved placeholders;
- a unique output directory and history path;
- frozen seed or seed set;
- matched epoch and optimization settings;
- expected runtime and storage estimate;
- confirmation that no existing artifact will be overwritten.

## First recommended future command

The first recommended future training is `no_graph_jepa`. Its command template is recorded in the protocol table and above, but it must not be executed until placeholders are resolved and approval is given.

## Boundary

- No training was run.
- This protocol does not claim ablation outcomes.
- This protocol does not change evidence levels.
