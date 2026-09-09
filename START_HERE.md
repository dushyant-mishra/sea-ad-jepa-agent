# START HERE — JEPA PROJECT

Date: 2026-09-09

## One current branch

**Use `main` for project-current governance and startup context.**

The project was consolidated on 2026-09-08. T0, Teacher/Student V5, Target Discovery, F1/F1-B/C3, D1, holdout governance, and external-review histories are reachable from main.

Do not infer current authority from an old branch name or historical PASS/STOP file. Active lane branches can carry staged execution evidence, but branch names themselves do not confer authority.

## Read in this order

1. [`docs/agent/CURRENT_AUTHORITY_INDEX.md`](docs/agent/CURRENT_AUTHORITY_INDEX.md)
2. [`docs/agent/memory-os/NEXT_ALLOWED_ACTION.json`](docs/agent/memory-os/NEXT_ALLOWED_ACTION.json)
3. [`docs/agent/memory-os/ACTIVE_STATE.md`](docs/agent/memory-os/ACTIVE_STATE.md)
4. [`docs/agent/CURRENT_SUPERSESSION_MAP.md`](docs/agent/CURRENT_SUPERSESSION_MAP.md)
5. [`docs/agent/T0_STAGE2_DISCOVERY_STATUS_20260909.md`](docs/agent/T0_STAGE2_DISCOVERY_STATUS_20260909.md)
6. [`docs/agent/T0_R8_ADJUDICATOR_READINESS_REPAIR_AUTHORIZATION_20260909.md`](docs/agent/T0_R8_ADJUDICATOR_READINESS_REPAIR_AUTHORIZATION_20260909.md)
7. [`docs/agent/TEACHER_STUDENT_V5_ANTI_CHEAT_AND_T1_MECHANICS_FINDINGS_20260909.md`](docs/agent/TEACHER_STUDENT_V5_ANTI_CHEAT_AND_T1_MECHANICS_FINDINGS_20260909.md)
8. [`docs/agent/memory-os/TEACHER_STUDENT_V5_ANTI_CHEAT_STATUS_20260909.json`](docs/agent/memory-os/TEACHER_STUDENT_V5_ANTI_CHEAT_STATUS_20260909.json)
9. [`docs/agent/FUTURE_FULL_RUN_FLEXIBILITY_POLICY_REVIEW_20260909.md`](docs/agent/FUTURE_FULL_RUN_FLEXIBILITY_POLICY_REVIEW_20260909.md)
10. [`docs/agent/memory-os/FUTURE_FULL_RUN_FLEXIBILITY_POLICY_20260909.json`](docs/agent/memory-os/FUTURE_FULL_RUN_FLEXIBILITY_POLICY_20260909.json)
11. [`docs/agent/JEPA_GLOBAL_BLOCKER_LEDGER_20260908.json`](docs/agent/JEPA_GLOBAL_BLOCKER_LEDGER_20260908.json)
12. [`docs/agent/JEPA_BRANCH_CONSOLIDATION_20260908.json`](docs/agent/JEPA_BRANCH_CONSOLIDATION_20260908.json)

## Current T0 boundary

Active T0 branch:
` t0/v20-pathology-blind-materialization-20260908 `

Verified Stage 2 discovery head:
`237427c734bfdf7d00f286ceeae63692b3075d49`

Current T0 terminal:

```text
DISCOVERY_STAGE_DONE_AND_REPLAYED__CONFIRMATION_NUMERIC_AT8_READY_TO_OPEN
```

Discovery AT8 was opened only for 28 discovery donors, the discovery object was fitted through the R7-gated frozen conclusion path, and the target was replayed from disk. Confirmation numeric AT8 remains closed.

Current T0 next step:

```text
AUTHORIZE_R8_ADJUDICATOR_READINESS_REPAIR__CONFIRMATION_NUMERIC_AT8_STILL_CLOSED
```

R8 may repair only the adjudicator readiness contradiction and must stop before confirmation numeric AT8 unless it reaches its required terminal and is reviewed.

## Current V5 reference

Current prospective V5 continuation head:
`028989a5f1504e4d6403a44e7c90d37172c54150`

The current V5 tree has been reconciled onto main.

Already frozen:
- scientific target V2;
- relational proposal V2;
- base proposal V3 with exact p/q correction;
- exactly one reader-fit-population-equivalent presentation horizon (4,553,407), no automatic extension.

Still open:
- evidence/view/block schedule;
- finite relational triplet budget;
- update/token execution geometry;
- EMA half-life and learned-teacher checkpoint milestone;
- GPU RNG kernel parity;
- hardware calibration;
- integrated trainer;
- anti-cheat qualification authority;
- mechanics qualification;
- external V5 review.

V5 training is not authorized.

## Future full-run flexibility rule

Future full-reader runs should be flexible during outcome-blind design/calibration, but immutable after decision-bearing evidence is opened or after production training starts.

```text
FLEXIBLE_BEFORE_FREEZE = true
FLEXIBLE_AFTER_OUTCOME_OR_DECISION_EVIDENCE = false
FLEXIBLE_AFTER_PRODUCTION_TRAINING_START = false
```

If an outcome-bearing discovery result is used to redesign a grid, schedule, target, or threshold, that run must be demoted to design evidence and a new frozen version must be created before confirmation/protected evidence.

## Target Discovery state

The current target is not fixed-coordinate prediction or absolute distance matching. The supported object is scale-free anchored triplet ordering from direct 160-D `cell_state` cosine geometry.

- TD57B: global donor-recurrent scale-free relational order passed.
- TD59: nearest-half mesoscale relational recurrence passed under frozen pilot criteria.
- TD57C: aggressive nearest-third fine-locality failed and remains closed.
- TD60: still prospective and must wait for a lawful full-reader exposure-defined learned teacher checkpoint.

Do not convert TD59's pilot nearest-half setting into an unfrozen production locality fraction.

## Historical T1 mechanics quarantine

Historical u10--u205 checkpoints are classified as:

```text
TRAINING_MECHANICS_DEFECT_INHERITED
```

They are not lawful resume points, biological teacher authority, or TD60 input. The clean u0 checkpoint is unaffected by the fp16-backward defect because it predates optimizer updates, but u0 alone does not authorize training.

Future healthy teacher/student training must bind:

```text
fp16 forward
  -> backward with autocast disabled
  -> unscale
  -> 48-tensor mandatory protected-gradient gate
  -> optimizer step proved
  -> both Adam moments checked
  -> EMA update
```

A teacher/student checkpoint is not biologically qualified because loss decreases.

## Protected-data boundary

Real T0 confirmation, real F1 biological sweep, production training, TD60, real D1, reader_validation/oracle, foundation development/sealed, external holdout and pathology remain closed unless a newer explicit frozen authority opens them.

## Branch hygiene

Branch consolidation and pruning are complete. The guarded cleanup deleted all 57 verified non-main refs and GitHub verified that only `main` remains. Commit history, tags, hashes, and immutable package artifacts were preserved.

Audit records:
- [`docs/agent/JEPA_BRANCH_CONSOLIDATION_20260908.json`](docs/agent/JEPA_BRANCH_CONSOLIDATION_20260908.json)
- [`docs/agent/JEPA_BRANCH_PRUNE_RESULT_20260908.json`](docs/agent/JEPA_BRANCH_PRUNE_RESULT_20260908.json)
- [`docs/agent/JEPA_SAFE_BRANCH_DELETE_LIST_20260908.json`](docs/agent/JEPA_SAFE_BRANCH_DELETE_LIST_20260908.json)

## Permanent implementation-verifier rule

All conclusion-bearing implementation is subject to [`MANDATORY_IMPLEMENTATION_VERIFIER_V1`](docs/agent/governance/MANDATORY_IMPLEMENTATION_VERIFIER_V1.md) before expensive execution or scientific promotion.
