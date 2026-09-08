# START HERE — JEPA PROJECT

Date: 2026-09-08

## One current branch

**Use `main`.**

The project was consolidated on 2026-09-08. T0, Teacher/Student V5, Target
Discovery, F1/F1-B/C3, D1, sealed-holdout governance, and external-review
histories are all now reachable from `main`.

Do not infer current authority from an old branch name or old PASS/STOP file.

## Read in this order

1. [`docs/agent/CURRENT_AUTHORITY_INDEX.md`](docs/agent/CURRENT_AUTHORITY_INDEX.md)
2. [`docs/agent/CURRENT_SUPERSESSION_MAP.md`](docs/agent/CURRENT_SUPERSESSION_MAP.md)
3. [`docs/agent/JEPA_GLOBAL_BLOCKER_REVIEW_20260908.md`](docs/agent/JEPA_GLOBAL_BLOCKER_REVIEW_20260908.md)
4. [`docs/agent/JEPA_GLOBAL_BLOCKER_LEDGER_20260908.json`](docs/agent/JEPA_GLOBAL_BLOCKER_LEDGER_20260908.json)
5. [`docs/agent/JEPA_BRANCH_CONSOLIDATION_20260908.json`](docs/agent/JEPA_BRANCH_CONSOLIDATION_20260908.json)

## Immediate critical path

```text
close remaining T0 execution-substrate STOPs
        +
freeze V5 scientific/exposure authorities
        +
finish final trainer mechanics binding
        ↓
mechanics qualification
        ↓
full-reader exposure-defined teacher training
        ↓
TD60 learned-teacher continuity
        ↓
D1 / partial-evidence student downstream work
```

## Current execution boundary

Real T0, real F1, full-reader training, TD60 decision-bearing execution, real
D1, reader_validation/oracle, foundation development/sealed, and unauthorized
pathology access remain closed unless a newer explicit frozen authority opens
them.

## Branch hygiene

All old branch histories have been preserved in `main`.

The safe branch-ref deletion list is:
[`docs/agent/JEPA_SAFE_BRANCH_DELETE_LIST_20260908.md`](docs/agent/JEPA_SAFE_BRANCH_DELETE_LIST_20260908.md)

Deleting those old branch refs is repository hygiene only; it does not remove
their commits because those commits are now ancestors of `main`.
