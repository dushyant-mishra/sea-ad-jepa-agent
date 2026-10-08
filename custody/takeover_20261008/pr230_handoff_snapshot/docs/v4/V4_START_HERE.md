# Graph-JEPA v4: Start Here

## One-Sentence Status

Stage81A2 is frozen at `808ce4f`; Stage81A3 has verified development evidence
but is not frozen. The 4,096-gene address-space cap and the independent 160-D
gene-token/global-state assumptions must be reopened in a versioned revision
before Freeze 1.

## What Matters Now

Read these artifacts for the current decision state:

| Priority | Artifact | Why it matters |
|---|---|---|
| 1 | `docs/v4/CURRENT_STATE_HANDOFF.md` | Canonical stage authority, chronology, blockers, and reproduction |
| 2 | `results/v4/stage81_current_state_manifest.json` | Machine-readable checkpoint state |
| 3 | `results/v4/stage81a2_freeze_report.json` | Frozen A2 contract and hashes |
| 4 | `docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md` | Full A3 experiment chronology |
| 5 | `results/v4/stage81a3_foundation_biological_state_domain_qualification.json` | Intrinsic state/domain qualification summary |
| 6 | `results/v4/stage81a3_rare_biology_completeness.json` | Final rare-state chronology boundary |
| 7 | `results/v4/stage81a3_context_identifiability_after_human_adjudication.json` | Context identifiability, not context benefit |

Everything else in `results/v4/` is supporting evidence, frozen provenance, or
a tracked negative result. Start from the handoff rather than browsing by name.

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

1. The 4,096 vocabulary was a configured top-K capacity, not a biological
   saturation point. A versioned maximal-exact-gene revision is required before
   Freeze 1; implementation has not started.
2. `d_gene=160` and PCA160/`d_cell=160` are distinct capacity and resolution
   assumptions. Historical tests remain valid, but neither value is frozen or
   biologically privileged for the future revision.
3. HVS retains 78 exact source donor IDs while the publication describes 75.
4. Fang MTG surgical provenance remains quarantined.
5. Local data/caches remain required for full regeneration and are inventoried
   separately rather than committed as raw data.

## Artifact Classes

**Canonical:** the handoff and machine-readable current-state manifest above.

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

Re-establish the intrinsic representation under a versioned maximal-exact-
transcriptome contract while independently qualifying `d_gene` contextual
capacity and `d_cell` global-state resolution. Preserve Stage81A2 and historical
160-D evidence unchanged; do not begin Stage81B, Stage81C, or production
training in that design step.
