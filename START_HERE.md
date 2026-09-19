# START HERE — JEPA PROJECT

Date: 2026-09-19

Status: `FULL104_PRETERMINAL_PROVENANCE_REPAIR_ACTIVE__OLD_PASS1_INVALID__H3_G5_TERMINAL_LOCKED__TRAINING_OFF`

## Current scientific execution anchor

Branch:

`impl/v5-full104-provenance-spillover-repair-20260919`

Exact scientific head:

`a51cdbe8bbfac1c77980711cca13df8bc58caa1d`

Do **not** run GPU/scientific work from the documentation handoff branch.

## Read in this order

1. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
2. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260919_FULL104_AUDITED_CURRENT.md`
3. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260919_FULL104_AUDITED_CURRENT.json`
4. `docs/agent/JEPA_CURRENT_SCIENTIFIC_AUDIT_20260919.md`
5. `docs/agent/JEPA_NEW_CHAT_COMMANDS_20260919_FULL104_AUDITED_SAFE_LANE.md`
6. `docs/agent/handoff_artifacts/20260919/JEPA_LOCAL_ENVIRONMENT_ASSET_MANIFEST_20260919.json`
7. `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md` only for historical context.

Before any action, re-fetch the live scientific branch and compare it with the exact head above. If it moved, audit the changed dependency cone first.

## Critical current finding

The September-17 `pass1.npz` is **invalid for current role** because its per-cell arrays were indexed by block traversal position rather than the immutable global cell identity `selection_row`.

Do not permute or patch it. Build a new physical pass1 keyed by `selection_row`, then pass it through the unchanged independent physical verifier before regenerating census/split/eligibility/cache.

## Permanent scientific boundaries

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL`

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

`TRAINING_OFF`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

`NO_TERMINAL_MASKING_OUTCOME_ACCESS`

The JEPA objective is query-local/cellular state from partial RNA, not hidden-gene scalar reconstruction.

## Hard terminal locks

- H3 equivalence-power panel sizing open;
- G5 scientific null-equivalence margin basis open;
- terminal run-contract construction blocked;
- terminal 5%+ masking execution blocked.

## Additional audit blockers before final training

- G3 capacity-matched shortcut attacker;
- G4 state-signal preservation;
- G2 targeting-complexity materiality;
- H4 all-rung failure interpretation;
- query-scalar/global-context leakage proof;
- F13 representation consumer binding;
- F14 production dimension/geometry;
- F15 current teacher/student/runtime;
- final authority closure must be updated from older masking schemas;
- execution PASS/hash fields must be derived from physical evidence rather than caller declarations.

Historical/smaller-run files may motivate tests but cannot occupy current FULL104 data/target/fold/burden/seed/PASS/runtime/training roles.
