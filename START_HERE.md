# Start Here — JEPA v4

This repository preserves several generations of JEPA research history. Do **not** infer the current execution state from old v1-v3 dashboards, dated Stage81 documents, historical `scripts/`, or archived outputs.

## Current work

The active project is the **FULL104 Contextual Target V1 / F1 feasibility line**.

Current controlling terminal:

`STOP_F1_EVIDENCE_TREND_NUMERICAL_DEFECT_UNRESOLVED`

The 15C HC3 numerical-robustness repair at commit `5e8127d360d1effd0867a73c2bb007ddffb2c901` passed external review. The remaining pre-result blocker is a separate evidence-trend arithmetic defect inherited from historical decision-v1. Real F1 execution and training remain blocked until that narrow repair passes fresh external review.

## Read in this order

1. [`docs/agent/memory-os/ACTIVE_STATE.md`](docs/agent/memory-os/ACTIVE_STATE.md) — compact current scientific state.
2. [`docs/agent/memory-os/NEXT_ALLOWED_ACTION.json`](docs/agent/memory-os/NEXT_ALLOWED_ACTION.json) — machine-readable live gate and prohibitions.
3. [`docs/agent/CURRENT_AUTHORITY_INDEX.md`](docs/agent/CURRENT_AUTHORITY_INDEX.md) — current accepted authority set.
4. [`docs/agent/reviews/F1_HC3_15C_NUMERICAL_ROBUSTNESS_REPAIR_EXTERNAL_REVIEW_20260902.md`](docs/agent/reviews/F1_HC3_15C_NUMERICAL_ROBUSTNESS_REPAIR_EXTERNAL_REVIEW_20260902.md) — controlling external review and transition to the evidence-trend gate.
5. [`docs/agent/CURRENT_SUPERSESSION_MAP.md`](docs/agent/CURRENT_SUPERSESSION_MAP.md) — current vs historical/superseded state.
6. [`docs/agent/EVIDENCE_INDEX.md`](docs/agent/EVIDENCE_INDEX.md) — selective map to deeper evidence.
7. [`docs/history/JEPA_PRESERVATION_LEDGER_20260902.md`](docs/history/JEPA_PRESERVATION_LEDGER_20260902.md) — preservation/backfill scope and chronology rules.

Use [`docs/agent/ACTIVE_STATE.md`](docs/agent/ACTIVE_STATE.md) as a dated historical scientific ledger, not as the sole live next-action pointer.

## Current boundary

The frozen current-104 nuisance design remains `(5,0,4)`, 104 x 16, rank 16, df 88, selected-design SHA-256 `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3`. The accepted effective centered design SHA-256 is `37653ed4a21f513a7389630bffa7447f9022323e8240bb80f53394138f1917eb`.

HC3 numerical independence is now externally resolved: production uses reduced QR/triangular solves and independent validation uses thin SVD/pseudoinverse.

Current decision-v4 still delegates evidence trend to historical v1 `evidence_slopes()`. For the frozen evidence grid `(0.2,0.4,0.6,0.8,1.0)`, the next prospective repair must change only the slope arithmetic to the algebraically identical stable form:

`(A100 - A20) + 0.5 * (A80 - A40)`.

Until that repair passes fresh external review:

- do not run the real F1 model-forward sweep;
- do not set real reader/forward authority;
- do not train, finetune, run optimizer steps, write training checkpoints, or update EMA;
- do not access DEV/SEALED/pathology for this repair;
- do not reselect `(5,0,4)` or reopen HC3 selection;
- do not reopen the closed `D_shared` branch.

## Repository roles

| Area | Meaning | Read first? |
|---|---|---|
| `docs/agent/memory-os/` | Compact live state and next action | **Yes** |
| `docs/agent/CURRENT_AUTHORITY_INDEX.md` | Current accepted authority set | **Yes** |
| `docs/agent/CURRENT_SUPERSESSION_MAP.md` | Current-vs-historical map | **Yes** |
| `docs/agent/reviews/` | External-review decisions | **Yes when named by live gate** |
| `docs/agent/provenance-anchors/` | Durable hash-bound roots for review packets | As needed |
| `docs/history/` | Preserved historical bytes, manifests and chronology ledgers | Selectively |
| `docs/v4/` | Earlier v4 contracts/status documents | Historical/selective |
| `scripts/v4/` | Current and historical reproducibility/conclusion-bearing code | When reviewing/implementing |
| `tests/v4/` | Contract and regression checks | When reviewing/implementing |
| `data/` | Local authoritative source data; never browse casually or commit | **No** |
| `outputs/`, `logs/`, `runs/`, `checkpoints/` | Primarily local/reproducible intermediates; selected review-safe evidence may be committed | **No** |
| `archive/` | Preserved older project generations | Provenance only |

## Chronology rule

The 2026-09-02 preservation commits contain recovered historical artifacts. Their Git commit dates are **backfill/preservation dates**, not proof that those artifacts were committed at their original historical times. Preserve the classification `RECOVERED_HISTORICAL_BYTES__BACKFILLED_20260902` and never fabricate historical Git chronology.

## Scientific objective

The current objective is to predict **biologically meaningful programs/state from partial RNA evidence while preserving the full address-resolved Molecular Ledger**. It is not exact hidden-gene reconstruction.
