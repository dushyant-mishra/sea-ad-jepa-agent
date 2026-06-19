# Discovery Ablation Artifact Readiness v1

## Existing usable artifacts

- `real_graph_stage_b_jepa`: `results\models\v2_2_stage_b_adversarial\stage_b_adversarial.pt`
- `pathology_head`: `results\models\pathology_heads_stage_b_lp\best_pathology_head.pt`

## Missing ablation artifacts

- `shuffled_graph_jepa`: `not_available_existing_artifact`
- `no_graph_jepa`: `not_available_existing_artifact`
- `expression_only_autoencoder`: `not_available_existing_artifact`

## Confirmed script flags and safe command templates

| artifact | script | help status / notes | smoke command | full template |
| --- | --- | --- | --- | --- |
| real_graph_stage_b_jepa | scripts\train_graph_jepa_stage_b_adversarial.py | help_inspected | python scripts/train_graph_jepa_stage_b_adversarial.py epochs=1 max_steps_per_epoch=2 per_domain_batch_size=8 out_dir=results/models/smoke_tests/stage_b_adversarial history_csv=results/tables/smoke_stage_b_adversarial_history.csv log_file=results/logs/smoke_stage_b_adversarial.log | python scripts/train_graph_jepa_stage_b_adversarial.py stage_a_checkpoint=<checkpoint> out_dir=<output> epochs=<epochs> |
| pathology_head |  | Existing frozen pathology head used by current counterfactual pipeline. | not_applicable | not_assessed_in_ablation_stage |
| shuffled_graph_jepa | scripts\train_graph_jepa_stage_a_fast.py | help_inspected; requires a precomputed deterministic shuffled edge CSV. | smoke_training_not_supported_without_script_patch; a reproducible shuffled-edge generator/input is not exposed by confirmed flags | python scripts/train_graph_jepa_stage_a_fast.py --edge-csv <precomputed_shuffled_edge_csv> --out-dir <output> --epochs <epochs> --h5ad <h5ad> |
| no_graph_jepa | scripts\train_graph_jepa_stage_a_fast.py | help_inspected; no explicit no-graph/identity-graph mode was confirmed. | smoke_training_not_supported_without_script_patch; identity/no-graph topology is not exposed by confirmed flags | requires_script_patch_or_precomputed_identity_edge_csv; then use confirmed --edge-csv --out-dir --epochs --h5ad flags |
| expression_only_autoencoder | scripts\train_jepa_snrna.py | help_failed_returncode_1 | smoke_training_not_supported_without_script_patch | not_generated_help_failed_or_no_confirmed_flags |

## What is needed to test graph contribution rigorously

- Train matched shuffled-graph and identity/no-graph models with the same feature space, architecture, masks, optimization budget, seeds, and evaluation folds.
- Define the shuffled topology generator and identity/no-graph semantics before training.
- Add an expression-only learned baseline only after its training script and objective are explicitly specified.

## Boundary

- Missing ablations are not negative evidence.
- No new ablation model was trained in this stage.
- Future ablation training requires explicit approval.
