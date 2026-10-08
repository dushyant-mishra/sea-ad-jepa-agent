# Discovery Feature-Wide Counterfactual Feasibility

## Candidate Counterfactual Script Found

- `scripts/pathology_head_counterfactual_knockout.py`
- Uses frozen `FastGraphGeneJEPA` encoder plus frozen pathology head.
- Supports `--genes`, `--mode gene`, batching, `--max-cells`, and no retraining.

## Required Artifacts

- Encoder checkpoint: `results\models\v2_2_stage_b_adversarial\stage_b_adversarial.pt` (`available`)
- Pathology head: `results\models\pathology_heads_stage_b_lp\best_pathology_head.pt` (`available`)
- H5AD / feature source: `data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad` (`available`)
- Edge index: `results\tables\v2_graph_consensus_edge_index.csv` (`available`)
- Graph edge names: `results\tables\v2_graph_consensus_edges.csv` (`available`)

## Feature Universe

- Feature genes: 2,957
- Graph-connected feature genes: 2,676
- Selected scope: `graph_connected`
- Selected genes for this run: 45
- Chunk size: 45
- Estimated chunks / script calls: 1
- Max cells per perturbation run: 10,000

## Feasibility

- Feasible now: `True`
- Blockers: none detected for dry-run / pilot orchestration.

## Estimated Output Paths

- Full feature-wide output: `results\tables\discovery_targeted_manifold_audit_v1.csv`
- Pilot output: `results\tables\discovery_pilot_feature_wide_pathology_axis_counterfactuals.csv`

## Claim Boundary

Feature-wide counterfactuals are still model-implied perturbation scores, not biological intervention results. They improve null testing and ranking robustness, but they do not prove causality.
