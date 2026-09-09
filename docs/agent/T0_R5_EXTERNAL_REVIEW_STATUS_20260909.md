# T0 R5 external review status — 2026-09-09

## Reviewed candidate

`t0/v20-pathology-blind-materialization-20260908`

Head reviewed: `0f0076235b96691a04f56bc213f0280c68200e0c`

## Review result

`STOP_T0_R5_REAL_POPULATION_AUTHORITY_NOT_MATERIALIZED`

R5 repaired important structural defects, but the real dataset authority is not complete.

## Accepted as improved

- R4 withdrawal was correct.
- The old public caller-vector `prove_source_library` path is no longer a proof path.
- A population raw-source authority mechanism exists.
- Technical completeness is no longer allowed to take Q_DEPTH from an unproven stored value.
- The full 35,076 B1 projection is the production default.
- Closure `rows` and `nnz` are required on the production path.
- A physical read plan is required and recorded.
- Estimability preflight roots bind more decision-bearing records.

## Not accepted as complete

- The real 20,804-row raw-source population authority has not been produced.
- The real technical-completeness authority has not been produced.
- No replay report exists for either production artifact.
- No CI is attached.
- The attempted production run was denied by Claude Code permissions.

## Ruling on synthetic fixtures

Synthetic fixtures remain useful only for adversarial software testing.

They cannot establish population closure. A three-row real-asset spot check also cannot establish population closure.

From this point, progress must be measured by real-dataset authority artifacts and replay, not by additional synthetic test counts.

## Current gates

```
PRODUCTION_B2_NOT_RUN remains effectively true until a real 20,804-row artifact exists.
DONOR_ROLE_GATE_SHUT
real_execution_ready=False
NUMERIC_CONFIRMATION_AT8_NOT_ACCESSED
NO_ELIGIBLE_DONOR_CONSTRUCTION
```

If a real production B2 run is authorized, the terminal wording can change only after the package exists and replays, for example:

`PRODUCTION_B2_RAW_SOURCE_POPULATION_AUTHORITY_MATERIALIZED_AND_REPLAYED`

Do not use a bare flag flip as evidence.

## Immediate next action

Commit and run the real-B2 production harness through an allowed permission path, then replay the emitted package from disk.
