# Graph-JEPA v4: Start Here

## One-Sentence Status

The v4 data portfolio is acquired and registered without fixed storage caps,
but Stage81A2 has not started and no v4 model has been trained.

## What Matters Now

Read only these five artifacts for the current decision state:

| Priority | Artifact | Why it matters |
|---|---|---|
| 1 | `results/v4/pre_stage81a2_harmonization_report.json` | Current pass/fail status and blockers |
| 2 | `results/v4/pre_stage81a2_modality_integration_registry.csv` | Which datasets can enter RNA, spatial, regulatory, holdout or validation paths |
| 3 | `results/v4/pre_stage81a2_perturbation_readiness_registry.csv` | Exact unresolved work before perturbation training |
| 4 | `results/v4/pre_stage81a2_dataset_role_candidates.csv` | Candidate role and leakage restrictions for every dataset |
| 5 | `results/v4/pre_stage81a2_dataset_manifest.csv` | Source path, hash, size and shape inventory |

Everything else in `results/v4/` is supporting provenance for one of those
files or a frozen output from an earlier Stage81 substage.

## Current Scientific Layout

| Branch | Current inputs | Rule |
|---|---|---|
| Foundation RNA | MTG primary; Immune Microglia/PVM specialization; PFC/DFC replication; other regions pending Stage81A2 | Preserve exact IDs and prevent donor/study leakage |
| Spatial | MTG MERFISH, HIP/MEC MERSCOPE, Caudate Xenium | Dedicated branch, shared-feature projection or missing-modality mechanism; never zero-fill as full RNA |
| Regulatory | MTG ATAC plus preserved Stage75-79 motif/chromatin evidence | Prior/adapter evidence only; not RNA vocabulary or a validated GRN |
| Clean holdout | Siletti all non-neuronal | Cannot influence training, vocabulary, architecture, thresholds, checkpoints or hyperparameters |
| Pathology context | GSE243292 | Validation only; pathology fields cannot supervise the pathology-blind foundation stage |
| Perturbation | 16 acquired processed assets | Blocked from training until content-level identity and matrix gates pass |

## Current Blockers

1. Exact spatial section identity is unresolved for three spatial datasets.
2. Fourteen perturbation assets still have unresolved source archive/table
   shapes and require content-level harmonization.
3. GSE301119 CRISPRa and CRISPRi require exact stable-feature alignment and
   explicit measurement masks for their unequal 19,162/36,601 feature spaces.

## Artifact Classes

**Canonical:** the five files above. Use these for current decisions.

**Supporting frozen provenance:** other tracked `results/v4/stage81*.csv/json`
files. Consult them only to audit how a canonical conclusion was derived.

**Builders:** `scripts/v4/`. Run only the script named by the relevant stage
documentation. They are not scientific results.

**Local generated intermediates:** `data/processed/v4/`, `outputs/v4/`,
`logs/v4/`, `runs/v4/`, and checkpoints. These can be large and are not an
entry point.

**Historical:** v1-v3 scripts/results and Stage75-79 evidence. They remain
important provenance and v4 regulatory inputs, but they are not the current
workflow dashboard.

## Next Work

Resolve the two blocker groups above, refresh the pre-Stage81A2 registries, and
review readiness. Do not begin model training merely because acquisition and
hash verification passed.
