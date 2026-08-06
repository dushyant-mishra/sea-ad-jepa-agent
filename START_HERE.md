# Start Here

This repository preserves several years of research history. Do not begin by
browsing `scripts/`, `results/`, or the full historical README.

## Current Work

The active project is **Graph-JEPA v4, pre-Stage81A2 data harmonization**.

Read these in order:

1. [V4_START_HERE.md](docs/v4/V4_START_HERE.md) - current status, blockers and
   the small set of authoritative files.
2. [STAGE81A0_V4_FAILURE_REGISTRY_AND_DESIGN_CONTRACT.md](docs/v4/STAGE81A0_V4_FAILURE_REGISTRY_AND_DESIGN_CONTRACT.md)
   - governing scientific design and claim boundaries.
3. [PRE_STAGE81A2_HARMONIZATION.md](docs/v4/PRE_STAGE81A2_HARMONIZATION.md)
   - current data-integration rules.

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

No v4 model has been trained. The data portfolio is acquired and virtually
registered. Foundation review is currently blocked by GSE97930 donor grouping;
the later spatial and perturbation stages retain their own independent blockers.
