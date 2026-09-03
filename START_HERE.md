# Start Here — JEPA v4

This repository preserves several generations of JEPA research history. Do **not** infer the current execution state from old v1-v3 dashboards, dated Stage81 documents, `scripts/`, or archived outputs.

## Current work

The active project is the **FULL104 Contextual Target V1 / F1 feasibility line**.

Current controlling terminal:

`STOP_F1_HC3_15C_NUMERICAL_INDEPENDENCE_UNRESOLVED`

15C has a completed **local synthetic-only PASS-awaiting-external-review packet**, but it is **not externally promoted**. Real F1 execution and training remain blocked pending one narrow HC3 numerical-robustness repair.

## Read in this order

1. [`docs/agent/memory-os/ACTIVE_STATE.md`](docs/agent/memory-os/ACTIVE_STATE.md) — compact current scientific state.
2. [`docs/agent/memory-os/NEXT_ALLOWED_ACTION.json`](docs/agent/memory-os/NEXT_ALLOWED_ACTION.json) — machine-readable live gate and prohibitions.
3. [`docs/agent/reviews/F1_HC3_15C_EXTERNAL_REVIEW_20260902.md`](docs/agent/reviews/F1_HC3_15C_EXTERNAL_REVIEW_20260902.md) — controlling external review and exact 15C blocker.
4. [`docs/agent/EVIDENCE_INDEX.md`](docs/agent/EVIDENCE_INDEX.md) — selective map to deeper evidence.
5. [`docs/history/JEPA_PRESERVATION_LEDGER_20260902.md`](docs/history/JEPA_PRESERVATION_LEDGER_20260902.md) — preservation/backfill scope and chronology rules.

Use [`docs/agent/ACTIVE_STATE.md`](docs/agent/ACTIVE_STATE.md) as a dated historical scientific ledger, not as the sole live next-action pointer.

## Current boundary

The frozen current-104 nuisance design remains `(5,0,4)`, 104 x 16, rank 16, df 88, selected-design SHA-256 `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3`.

The 15C external review found a narrow numerical-independence problem: both the inherited production HC3 arithmetic and the 15C independent validator use the same normal-equations inverse on a design with condition number about `5.87e6`. Before promotion, a prospectively frozen synthetic-only repair must demonstrate stable QR/SVD HC3 agreement with a genuinely independent numerical route.

Until that repair passes fresh external review:

- do not run the real F1 model-forward sweep;
- do not set real reader/forward authority;
- do not train, finetune, run optimizer steps, write training checkpoints, or update EMA;
- do not access DEV/SEALED/pathology for this repair;
- do not reselect `(5,0,4)` or reopen 15A4;
- do not reopen the closed `D_shared` branch.

## Repository roles

| Area | Meaning | Read first? |
|---|---|---|
| `docs/agent/memory-os/` | Compact live state, next action, decision/experiment memory | **Yes** |
| `docs/agent/reviews/` | Current external-review decisions | **Yes when named by live gate** |
| `docs/agent/provenance-anchors/` | Durable hash-bound roots for review packets | As needed |
| `docs/history/` | Preserved historical bytes, manifests, chronology/preservation ledgers | Selectively |
| `docs/v4/` | Earlier v4 contracts/status documents | Historical/selective |
| `scripts/v4/` | Current and historical reproducibility/conclusion-bearing code | When reviewing/implementing |
| `tests/v4/` | Contract and regression checks | When reviewing/implementing |
| `data/` | Local authoritative source data; never browse casually or commit | **No** |
| `outputs/`, `logs/`, `runs/`, `checkpoints/` | Primarily local/reproducible intermediates; selected review-safe evidence may be preserved elsewhere | **No** |
| `archive/` | Preserved older project generations | Provenance only |

## Chronology rule

The 2026-09-02 preservation commits contain recovered historical artifacts. Their Git commit dates are **backfill/preservation dates**, not proof that those artifacts were committed at their original historical times. Preserve the classification `RECOVERED_HISTORICAL_BYTES__BACKFILLED_20260902` and never fabricate historical Git chronology.

## Scientific objective

The current objective is to predict **biologically meaningful programs/state from partial RNA evidence while preserving the full address-resolved Molecular Ledger**. It is not exact hidden-gene reconstruction.
