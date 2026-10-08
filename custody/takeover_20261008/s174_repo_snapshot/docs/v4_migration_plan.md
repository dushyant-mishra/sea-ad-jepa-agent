# v4 Migration Plan

This is the phased organization plan for moving from the crowded v1/v2/v3 repository state into clean v4 development without breaking paths.

## Phase 1: Map Before Moving

Status: complete as non-destructive map layer.

- Add `archive/v1/`, `archive/v2/`, and `archive/v3/` placeholders with README files.
- Add `docs/project_file_map.md`.
- Add `docs/v3_frozen_artifact_index.md`.
- Add tracked inventory `results/tables/project_file_inventory_v1.csv`.
- Add `scripts/v4/build_project_file_inventory.py` to regenerate the inventory.

## Phase 2: Tighten Ignore Rules And Provenance

Status: complete as provenance/index layer.

- Ignore local raw/resource data.
- Ignore v4 run, log, output, results, and checkpoint namespaces.
- Keep tracked lightweight summaries and frozen visualization artifacts path-stable.
- Generate `results/tables/project_git_provenance_index_v1.csv` before any physical move.

## Phase 3: Organize Docs And Configs

Status: complete as index-first cleanup; physical moves deferred.

Docs and configs are now mapped in `results/tables/project_doc_config_index_v1.csv`. Low-risk candidates can be moved with `git mv` only after link/reference checks:

- stage-specific docs into `docs/v3/stage75_79/` or another documented location;
- old train/agent configs into versioned subfolders only when scripts are updated or wrappers preserve compatibility.

## Phase 4: Script Inventory And Wrappers

Status: complete as dependency inventory; wrappers deferred until a specific move is approved.

Before moving scripts, use `results/tables/project_script_dependency_inventory_v1.csv`, which records:

- script path;
- version/stage bucket;
- imported local modules;
- config paths used;
- output paths written;
- whether the script is active, frozen, legacy, or unknown.

If a script is moved, add a compatibility wrapper or update every caller in the same commit.

## Phase 5: Results Last

Status: complete as frozen-result hash index; physical result moves deferred.

Frozen results should usually stay where they are. `results/tables/project_frozen_results_index_v1.csv` records tracked result paths, sizes, stages, roles, and SHA-256 hashes. Prefer indexes over moves because many artifacts contain path and hash provenance.

For v4, use clean namespaces from the beginning:

- `results/v4/tables/`
- `results/v4/reports/`
- `results/v4/figures/`
- `results/v4/visualization/`

## Stop Conditions

Stop and review before any physical move that touches:

- `results/visualization/` frozen HTML/JSON;
- Stage75-79 configs or scripts;
- training scripts with hard-coded output paths;
- any file under `data/`;
- large files, checkpoints, or model artifacts.

## Phase 3-5 Index Regeneration

Regenerate the docs/configs, script dependency, and frozen-results indexes with:

```powershell
cd "D:\Jepa project"
conda run -n sea-ad-jepa-v3 python scripts\v4\build_cleanup_phase_indexes.py
```

The script writes:

- `results/tables/project_doc_config_index_v1.csv`
- `results/tables/project_script_dependency_inventory_v1.csv`
- `results/tables/project_frozen_results_index_v1.csv`
- `results/reports/project_cleanup_phase3_5_summary_v1.json`
