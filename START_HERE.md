# Start Here

This repository preserves several years of research history. Do not begin by
browsing `scripts/`, `results/`, or the full historical README.

## Current Work

The active project is **SEA-AD MRA-JEPA v4, Stage81A3 development checkpoint**.
Stage81A2 is frozen; Stage81A3 and Freeze 1 are not frozen or declared.

Read these in order:

1. [CURRENT_STATE_HANDOFF.md](docs/v4/CURRENT_STATE_HANDOFF.md) - canonical
   stage authority, evidence chronology, blockers, and reproduction commands.
2. [V4_START_HERE.md](docs/v4/V4_START_HERE.md) - compact v4 navigation.
3. [STAGE81A0_V4_FAILURE_REGISTRY_AND_DESIGN_CONTRACT.md](docs/v4/STAGE81A0_V4_FAILURE_REGISTRY_AND_DESIGN_CONTRACT.md)
   - governing scientific design and claim boundaries.
4. [STAGE81A2_CANONICAL_DATA_VOCABULARY_SPLIT_FREEZE.md](docs/v4/STAGE81A2_CANONICAL_DATA_VOCABULARY_SPLIT_FREEZE.md)
   - immutable historical A2 data contract.

## Directory Meaning

| Directory | Meaning | Read first? |
|---|---|---|
| `docs/v4/` | Current v4 decisions and status | Yes |
| `configs/v4/` | Machine-readable v4 contracts | When implementing |
| `results/v4/` | Frozen registries and provenance, including many supporting files | Only through the v4 guide |
| `scripts/v4/` | Reproducibility builders and acquisition tools | Only when rerunning a stage |
| `tests/v4/` | Contract checks | For development |
| `data/` | Authoritative/local source data; never browse casually or commit | No |
| `outputs/`, `logs/`, `runs/`, `checkpoints/` | Reproducible local intermediates | No |
| `archive/` and non-v4 stage files | Preserved v1-v3 history | Only for provenance |

The machine-readable classification is
[`configs/v4/v4_artifact_map.yaml`](configs/v4/v4_artifact_map.yaml).

## Current Boundary

Stage81A3 contains substantial verified mechanics and bounded diagnostic work,
but no production foundation trajectory has begun. DEV and SEALED RNA remain
closed, pathology remains excluded from foundation development, and Stage81B/C
are not started. The next blockers are a versioned reconsideration of the 4,096-
gene address-space cap and independent qualification of per-gene contextual
capacity versus global-state resolution before Freeze 1; do not rewrite frozen
A2 or historical 160-D evidence in place.
