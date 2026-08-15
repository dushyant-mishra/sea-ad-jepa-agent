# Graph-JEPA v4: Start Here

## One-Sentence Status

Stage81A2R is frozen with 41,238 universal molecular addresses, and Stage81A3
Freeze1 is declared with `d_gene=160` and the final range-closed
`d_global=224`; Stage81B and Stage81C have not started.

## What Matters Now

Read these artifacts for the current decision state:

| Priority | Artifact | Why it matters |
|---|---|---|
| 1 | `docs/v4/CURRENT_STATE_HANDOFF.md` | Canonical stage authority, chronology, blockers, and reproduction |
| 2 | `results/v4/stage81a3r_freeze1_contract.json` | Machine-readable frozen representation contract |
| 3 | `docs/v4/STAGE81A3R_FREEZE1_REPRESENTATION_CONTRACT.md` | Concise Freeze1 evidence and boundaries |
| 4 | `results/v4/stage81a2r_foundation_molecular_address_injectivity_audit.json` | Frozen A2R address counts and semantic hash |
| 5 | `docs/v4/STAGE81A3R_REAL_TRAIN_GLOBAL_STATE_READOUT.md` | Historical 208 audit and final 224 range closure |
| 6 | `docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md` | Full historical A3 experiment chronology |

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

## Carried-Forward Boundaries

1. `d_gene=160` is frozen from bounded synthetic qualification, not claimed to
   be a biologically complete contextual state.
2. `d_global=224` is a derived ordered summary and is not claimed to contain all
   molecular biology; the Molecular Ledger remains the high-resolution route.
3. Preferential U_BIO/U_MEAS separation was not demonstrated, so calibrated
   uncertainty outputs are excluded from Freeze1.
4. HVS retains 78 exact source donor IDs while the publication describes 75.
5. Fang MTG surgical provenance remains quarantined.
6. Local data/caches remain required for full regeneration and are inventoried
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

Begin Stage81B only under a separate authorization. Its first global-basis
action is a one-time complete-authorized-TRAIN refit using the frozen molecular
address, scalar-support, preprocessing, reproducibility-weighting,
ordered-linear, and `d_global=224` contract. Dimension reselection and access to
DEV, SEALED, pathology, or Phase-B Immune data are forbidden. Stage81C remains
not started.
