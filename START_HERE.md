# START HERE — JEPA T0 V2 Claude-Ready Repair Branch

Date: 2026-09-11
Status: `CLAUDE_READY_T0_V2_CONTINUATION__NO_TRAINING_AUTHORITY`

## Immediate instruction for Claude / next agent

This branch carries the repaired T0 V2 / V21-T1 continuation work order. Read these first:

1. `docs/agent/CLAUDE_T0_V2_WORK_ORDER_20260911.md`
2. `docs/agent/JEPA_T0_V2_CLAUDE_READY_POINTER.txt`
3. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
4. `docs/agent/CURRENT_AUTHORITY_INDEX.md`
5. `docs/agent/CURRENT_SUPERSESSION_MAP.md`

Re-fetch live heads before acting. Branch names do not confer authority.

Current intended continuation head when this START file was written:

`repair/t0-v21-authority-restoration-20260911`

This branch now includes the V21 authority restoration/API-surface guard and the fail-closed executor successor lineage. The previous ASAP handoff branch `handoff/jepa-new-chat-20260911-asap-repair-status` is useful historical context, but it was created from stale `93abcf50...`; the live restoration branch advanced afterward.

## Hard boundary

Training remains OFF. No S0-S4 production run, no real power-gate verdict, no AT8 opening, no protected partition opening, no `reader_validation`, no oracle, no V21 freeze claim, and no V5 training is authorized here.

Required work now: verify or finish the clean exact-head T0 V2 repaired candidate, preserving:

- `V21_AUTHORITY_API_RESTORED = TRUE` only after exact-head tests pass;
- `EFFECT_TRANSPORT_STATUS = OPEN`;
- `POWER_GATE_PRODUCTION_VERDICT_CAPABILITY = DISABLED`;
- `S0_S4_EXECUTION_AUTHORITY = FALSE`;
- `TRAINING_AUTHORITY = FALSE`.

---

# Start Here — JEPA v4

This repository preserves several generations of JEPA research history. Do **not** infer the current execution state from old v1-v3 dashboards, dated Stage81 documents, historical `scripts/`, or archived outputs.

## Current work

**Two lines are open. The T0/V21 line is the one being worked.**

### T0 V21-T1 — active

Current controlling gate:

`STOP_T0_V21_T1_CONTRACT_UNFROZEN`

The V21-T1 prospective design is **not frozen**. External review of `a89f4c3f`
returned **NO-GO** with six blockers; the design has since been amended
prospectively and the executor repaired, and both await owner approval and fresh
external review.

Implemented and adversarially qualified: the 28-fold outer leave-one-donor-out
construction, the single assembled HC3 regression, the empirical influence
minimum, the sealed cross-fit artifact, power calibrated by simulation against
the frozen Freedman-Lane test, the ridge procedure, and estimator selection.
**Not implemented**, and therefore blocking freeze: the measurement layer —
`S0`–`S4`, the thinning ladder, held-out-biology preservation, the three
ridge-stability displacements, QC power-calibration inputs, and the provenance
emitter.

Unauthorized until that is done and reviewed: running `S0`–`S4` selection,
running the power gate, opening AT8 values, opening any partition, opening
`reader_validation`, freezing V21-T1, and training.

Read: [`docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md`](docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md),
then `scripts/v4/t0_v21_selection_and_power_v1.py` and its test suite and
mutation audit.

### FULL104 Contextual Target V1 / F1 feasibility line — open, not advanced

Its gate is unchanged and its preflight has not been started:

`STOP_F1_REAL_READER_FORWARD_EXECUTOR_PREFLIGHT_UNFROZEN`

The F1 evidence-trend numerical repair at commit `249bc3b37cb6368ad97fde6bfb2a4560e83ff5a4` passed fresh external review. The stable paired-difference evidence slope and complete independent 11-gate reconstruction are accepted at synthetic-only scope.

The next authorized work is the **real F1 reader/forward/executor preflight**. The full real F1 biological sweep and training remain blocked until that preflight is prospectively frozen, executed and externally reviewed.

## Read in this order

1. [`docs/agent/memory-os/ACTIVE_STATE.md`](docs/agent/memory-os/ACTIVE_STATE.md) — compact current scientific state.
2. [`docs/agent/memory-os/NEXT_ALLOWED_ACTION.json`](docs/agent/memory-os/NEXT_ALLOWED_ACTION.json) — machine-readable live gate and prohibitions.
3. [`docs/agent/CURRENT_AUTHORITY_INDEX.md`](docs/agent/CURRENT_AUTHORITY_INDEX.md) — current accepted authority set.
4. [`docs/agent/reviews/F1_EVIDENCE_TREND_NUMERICAL_REPAIR_EXTERNAL_REVIEW_20260903.md`](docs/agent/reviews/F1_EVIDENCE_TREND_NUMERICAL_REPAIR_EXTERNAL_REVIEW_20260903.md) — controlling external review and transition to the real reader/forward/executor preflight.
5. [`docs/agent/CURRENT_SUPERSESSION_MAP.md`](docs/agent/CURRENT_SUPERSESSION_MAP.md) — current vs historical/superseded state.
6. [`docs/agent/EVIDENCE_INDEX.md`](docs/agent/EVIDENCE_INDEX.md) — selective map to deeper evidence.
7. [`docs/history/JEPA_PRESERVATION_LEDGER_20260902.md`](docs/history/JEPA_PRESERVATION_LEDGER_20260902.md) — preservation/backfill scope and chronology rules.

Use [`docs/agent/ACTIVE_STATE.md`](docs/agent/ACTIVE_STATE.md) as a dated historical scientific ledger, not as the sole live next-action pointer.

## Current boundary

The frozen current-104 nuisance design remains `(5,0,4)`, 104 x 16, rank 16, df 88, selected-design SHA-256 `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3`. The accepted effective centered design SHA-256 is `37653ed4a21f513a7389630bffa7447f9022323e8240bb80f53394138f1917eb`.

HC3 numerical independence is externally resolved: production uses reduced QR/triangular solves and independent validation uses thin SVD/pseudoinverse.

Evidence-trend numerical stability is also externally resolved. The conclusion-bearing current evidence slope is:

`(A100 - A20) + 0.5 * (A80 - A40)`

The accepted evidence-trend repair package root SHA-256 is `ce759e1397cba36d3d595603b14472ccbb756826144a4dbb3db31a964da0c607`.

The next preflight must:

- authenticate and hash-bind the real reader/forward path before any conclusion-capable real sweep;
- reuse the established WSL/CUDA lineage for heavy GPU/I/O work when authentication succeeds;
- detect current GPU/VRAM, RAM, CPU and storage/I/O resources at runtime rather than hard-code historical execution values;
- adapt only mechanical execution geometry such as batching, block size, worker count, prefetch, caching and concurrency;
- keep query design, evidence masks, nulls, donor order, protected programs, statistics, model architecture and scientific semantics invariant;
- validate query-safe teacher/student masking, block-major streaming, exact logical-order restoration, atomic shards, resume/restart and sufficient-statistic accumulation;
- benchmark only a prospectively fixed, non-conclusion-bearing technical fixture;
- receive fresh external review before the full real F1 biological sweep is authorized.

Until that preflight passes review:

- do not run or adjudicate the full real F1 biological sweep;
- do not train, finetune, run optimizer steps, write training checkpoints, or update EMA;
- do not access DEV/SEALED/pathology;
- do not change scientific/statistical identities as part of resource tuning;
- do not reselect `(5,0,4)`, reopen HC3 selection, or reopen the closed `D_shared` branch.

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
