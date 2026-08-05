# Graph-JEPA v4 Launchpad

This directory is the clean planning area for SEA-AD Graph-JEPA v4. It keeps v4 training design separate from the frozen v3/Stage75-79 evidence and visualization artifacts.

## Current v3 checkpoint

The v3 project established a self-supervised Graph-JEPA representation in which disease-relevant microglial state structure emerged without training the model as a disease classifier. Stage75-79 added enhancer-informed regulator context and bounded perturbation/control simulations, but the frozen v3 perturbation effects were very small relative to the JEPA latent geometry. Those later perturbation outputs are provenance and calibration material, not the central biological claim.

## v4 objective

Build a regulatory-aware Graph-JEPA v4 while preserving the strongest v3 idea: disease-state structure should be evaluated as emergent representation geometry, not as a directly supervised disease-label target.

## Organization rules

- Keep v3 frozen artifacts under their existing paths.
- Put v4 configs under `configs/v4/`.
- Put v4-only helper scripts under `scripts/v4/` unless they clearly belong in shared `scripts/`.
- Use local output namespaces such as `runs/v4/`, `logs/v4/`, `outputs/v4/`, and `results/v4/` for experimental training products.
- Do not commit raw data, model checkpoints, large matrices, temporary logs, or exploratory notebooks unless explicitly reviewed.
- Commit only small reproducibility artifacts, manifests, summaries, and methods notes after review.

## Initial v4 design questions

- Which gene universe preserves v3 disease-state discovery while forcing coverage of regulatory candidates?
- Should v4 use a full retrain, a staged warm start, or paired v3/v4 comparisons?
- Which regulators and target genes must be included in the feature space before training starts?
- Which v3 metrics define non-regression for disease-state geometry?
- Which perturbation claims should be deferred until v4 shows meaningful latent movement against controls?

## Cleanup Indexes For v4 Startup

Use these maps before adding or moving v4 files:

- `results/tables/project_file_inventory_v1.csv`
- `results/tables/project_git_provenance_index_v1.csv`
- `results/tables/project_doc_config_index_v1.csv`
- `results/tables/project_script_dependency_inventory_v1.csv`
- `results/tables/project_frozen_results_index_v1.csv`
- `results/reports/project_cleanup_phase3_5_summary_v1.json`

The intended workflow is: check the map, preserve frozen v3 paths, add new v4 work under v4 namespaces, then freeze only compact reviewed outputs.
