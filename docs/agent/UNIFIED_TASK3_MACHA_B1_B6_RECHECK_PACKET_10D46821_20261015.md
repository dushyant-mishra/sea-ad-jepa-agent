# Macha focused recheck packet — Unified Task 3 B1-B6

Date: 2026-10-15
Review target: `10d468214aa057be023e38cd7a89d64f208d92e3`
PR: #397
Review scope: T3-B1 through T3-B6 only

Do not redo the complete Task 3 audit. The prior review at `851544e8...` remains historical authority for findings that held. Re-attack only the six blockers and verify that the repair did not weaken the previously passing prerequisite/Task2 bindings.

## Required verdict language

If all six are closed:
`ACCEPT_UNIFIED_TASK3_T3_B1_B6_REPAIR`
`TASK3_MAY_BE_FROZEN__UNIFIED_TASK4_MAY_BEGIN_PROSPECTIVELY`

If any remains open:
`REJECT_UNIFIED_TASK3_T3_B1_B6_REPAIR`
`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

## Exact target

- rejected parent: `851544e8dc2a3881193a4d5bbcf07933e1d61149`
- repair head: `10d468214aa057be023e38cd7a89d64f208d92e3`
- frozen Task 2 base ancestry: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`

Confirm the reviewed SHA before probing.

## B1 — authority scope/stage enforcement

Reproduce the original attack: a `UNIT:G8` record carrying `NO_TRAINING_AUTHORITY` must not be promotable to TRAINING_ELIGIBLE or TRAINING_AUTHORIZED by stepping through stages.

Also probe near-boundaries:
- UNIT record should not exceed the Task 1 maximum for that scope;
- a restriction cannot be dropped during promotion;
- a hand-built advanced record cannot bypass promotion validation.

## B2 — fixed stage evidence requirements

Reproduce:
- KNOWN_TRUTH_QUALIFIED cannot be granted with controller signoff alone;
- HUMAN_EXECUTED cannot be granted without the authoritative execution evidence required by the stage law.

Verify that stages depending on Task 4/5 evidence fail closed while those evidence types do not yet exist. Do not accept placeholder role labels, booleans or controller assertions as evidence.

## B3 — registered actors and no-self-qualification

Re-run all original producer lookalikes:
- `producer:G8 `
- ` producer:G8`
- `PRODUCER:G8`
- `producer：G8`

All must be refused as authority identities. An invented actor not present in the frozen actor registry must also be refused.

Verify exact registered controller/reviewer actors can be used only in their allowed roles, and actor-level producer/executor independence remains enforced using authenticated actor objects rather than digest inequality alone.

## B4 — cache authority

Re-run:
- prefilled caller cache with unverifiable dependencies;
- cache generated under one resolver then supplied with a resolver that holds none of the objects.

Neither may grant readiness. Cache state must be internal to the current verification operation and dependent identities must still be resolved/verified.

## B5 — fixed-start replay and revocation provenance

Re-run:
- revoke a unit, delete the revocation from a reconstructed history, then attempt re-promotion;
- build an advanced history manually without lawful readiness transitions;
- forge a promotion receipt that is internally consistent but not reachable from anchored history.

All must fail. Verify the current history is anchored to a fixed genesis/current session rather than trusting a caller-supplied latest state.

## B6 — workflow custody

Verify the two write-capable workflows are absent on the repair head:
- `.github/workflows/task3-red6-actor-repair.yml`
- `.github/workflows/apply-task3-cycle4-hardening.yml`

Confirm the normal Task 3 verification path is read-only and cannot commit/push production code or rewrite tests.

Historical workflow evidence is retained in the audit checkpoint. Do not require historical bot mutations themselves to disappear from Git history; require that they cannot mutate the repair/review head prospectively.

## R1-R6 checks relevant to the focused repair

- R1/R4: do NOT treat process-local synthetic evidence as a human-execution trust anchor. HUMAN_EXECUTABLE must stay blocked until real out-of-process registry/key/value custody exists.
- R2: content validators/authority actors must be registered/authenticated; invented validators cannot qualify content.
- R3/R5: previously passing behavior should remain intact.
- R6: caller cache must not become authority.

## Regression evidence from controller

On exact `10d46821...` controller CI records:
- Task 3 run `38764885273`, job `116525386712`: 57 focused + 160 full unified tests passed;
- frozen Task 2 `38764885283`: success;
- inherited unified synthetic integration `38764885312`: success.

These are controller evidence only. Base the independent verdict on your own hostile probes.

## Authority boundary

No protected values should be opened for this review. No target, representation, human-execution, Stage 4 or training authority changes merely because mechanics pass.
