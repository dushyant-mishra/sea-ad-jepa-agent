# v4 Start Checklist

Use this checklist before starting SEA-AD Graph-JEPA v4 training. It is intentionally conservative: v4 work should start cleanly without moving or rewriting frozen v3 provenance.

## Work Location

- Windows project path: `D:\Jepa project`
- WSL project path: `/mnt/d/Jepa project`
- GitHub remote: `https://github.com/dushyant-mishra/sea-ad-jepa-agent.git`
- Branch: `main`

Before any v4 work:

```powershell
cd "D:\Jepa project"
git pull --ff-only
git status --short
git rev-parse HEAD
```

Expected protected local state may still include:

- `docs/stage_c_finetuning_analysis.md`
- `results/tables/v2_1_gse174367_cell_trajectory_scores.csv`
- `results/tables/v2_2_abeta_responsive_microglia_cell_scores_summary.csv`

Do not stage those unless they become part of a separately reviewed task.

## Cleanup Maps To Read First

Use these maps before adding, moving, or deleting project files:

- `docs/project_file_map.md`
- `docs/v3_frozen_artifact_index.md`
- `docs/v4_migration_plan.md`
- `results/tables/project_file_inventory_v1.csv`
- `results/tables/project_git_provenance_index_v1.csv`
- `results/tables/project_doc_config_index_v1.csv`
- `results/tables/project_script_dependency_inventory_v1.csv`
- `results/tables/project_frozen_results_index_v1.csv`
- `results/reports/project_cleanup_phase3_5_summary_v1.json`

Regenerate cleanup indexes only from the project root:

```powershell
cd "D:\Jepa project"
conda run -n sea-ad-jepa-v3 python scripts\v4\build_project_file_inventory.py
conda run -n sea-ad-jepa-v3 python scripts\v4\build_git_provenance_index.py
conda run -n sea-ad-jepa-v3 python scripts\v4\build_cleanup_phase_indexes.py
```

## Frozen v3 Baseline

The central v3 result to preserve is:

Self-supervised Graph-JEPA recovered disease-relevant microglial state geometry without being trained as a disease-label classifier.

Preserve these v3 areas path-stably unless a specific reference audit approves a move:

- `configs/stage75e_scenicplus_preflight_v1.yaml`
- `configs/stage75f_out_of_core_v1.yaml`
- `scripts/stage75*` through `scripts/stage79*`
- `results/tables/stage75*` through `results/tables/stage79*`
- `results/reports/stage75*` through `results/reports/stage79*`
- `results/visualization/stage77*` through `results/visualization/stage79*`

The Stage75-79 perturbation/control results are frozen provenance and calibration. They are not evidence of validated regulation, causal control, therapeutic effect, or meaningful biological state rescue.

## v4 Namespaces

Put new v4 work here:

- configs: `configs/v4/`
- docs: `docs/v4/`
- v4-only scripts: `scripts/v4/`
- local runs: `runs/v4/`
- local logs: `logs/v4/`
- local outputs: `outputs/v4/`
- local results: `results/v4/`

Local run products are ignored by default. Freeze only compact reviewed summaries, manifests, figures, or visualization payloads.

## Do Not Commit

Do not commit:

- raw data under `data/`
- cisTarget or other large external resources
- model checkpoints or weight files
- full training run folders
- temporary logs
- exploratory notebooks or scratch bundles
- generated artifacts that have not been reviewed

## First v4 Technical Decisions

Resolve these before training:

- feature universe: which genes are required to preserve v3 disease geometry and cover regulatory candidates;
- training route: full retrain, warm start, or paired v3/v4 comparison;
- graph inputs: which frozen v3 regulatory context is allowed as model input versus audit-only annotation;
- non-regression metrics: which v3 geometry metrics v4 must preserve or improve;
- perturbation criteria: what would count as a meaningful simulated latent movement against controls.

## Minimum v4 Training Manifest

Before launching training, create a manifest that records:

- exact input matrices and feature ordering;
- graph source and graph transform;
- donor split strategy;
- model architecture and random seeds;
- training command and environment;
- output directories;
- planned non-regression checks;
- claim boundaries.

## Claim Boundaries

Allowed wording:

Model-based representation and perturbation hypotheses requiring experimental validation.

Disallowed without new evidence:

- validated GRN;
- proven TF activation or repression;
- causal rescue;
- therapeutic target claim;
- disease modification claim;
- biological effect-size claim from input-space perturbations alone.