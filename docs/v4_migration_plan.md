# v4 Migration Plan

This is the phased organization plan for moving from the crowded v1/v2/v3 repository state into clean v4 development without breaking paths.

## Phase 1: Map Before Moving

Status: started.

- Add `archive/v1/`, `archive/v2/`, and `archive/v3/` placeholders with README files.
- Add `docs/project_file_map.md`.
- Add `docs/v3_frozen_artifact_index.md`.
- Add tracked inventory `results/tables/project_file_inventory_v1.csv`.
- Add `scripts/v4/build_project_file_inventory.py` to regenerate the inventory.

## Phase 2: Tighten Ignore Rules And Provenance

Status: in progress.

- Ignore local raw/resource data.
- Ignore v4 run, log, output, results, and checkpoint namespaces.
- Keep tracked lightweight summaries and frozen visualization artifacts path-stable.
- Generate `results/tables/project_git_provenance_index_v1.csv` before any physical move.

## Phase 3: Organize Docs And Configs

Status: pending.

Low-risk candidates can be moved with `git mv` after link/reference checks:

- stage-specific docs into `docs/v3/stage75_79/` or another documented location;
- old train/agent configs into versioned subfolders only when scripts are updated or wrappers preserve compatibility.

## Phase 4: Script Inventory And Wrappers

Status: pending.

Before moving scripts, build a dependency/reference table with:

- script path;
- version/stage bucket;
- imported local modules;
- config paths used;
- output paths written;
- whether the script is active, frozen, legacy, or unknown.

If a script is moved, add a compatibility wrapper or update every caller in the same commit.

## Phase 5: Results Last

Status: pending.

Frozen results should usually stay where they are. Prefer indexes over moves because many artifacts contain path and hash provenance.

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
