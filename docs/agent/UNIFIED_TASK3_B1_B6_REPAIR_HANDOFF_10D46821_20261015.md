# Unified Task 3 B1-B6 focused repair handoff

Date: 2026-10-15

## Current gate

Task 3 rejected head: `851544e8dc2a3881193a4d5bbcf07933e1d61149`.
Macha rejection review head: `869ca777`.

Current focused repair candidate on PR #397:
`10d468214aa057be023e38cd7a89d64f208d92e3`.

Status:
`TASK3_B1_B6_REPAIRED__MACHA_FOCUSED_RECHECK_PENDING__TASK4_BLOCKED`

Do not use the rejected Task 3 head as authority. Do not start Task 4 implementation.

## Read first

On PR #322 audit branch:
1. `docs/agent/UNIFIED_TASK3_B1_B6_REPAIR_CHECKPOINT_10D46821_20261015.md`
2. `docs/agent/UNIFIED_TASK3_MACHA_B1_B6_RECHECK_PACKET_10D46821_20261015.md`
3. `docs/superpowers/specs/2026-10-15-unified-task4-sealed-challenge-custody-design.md`

## Six repair findings

- B1: enforce Task 1 authority scope/stage on every promotion.
- B2: fixed per-stage evidence table; future unavailable evidence fails closed.
- B3: strict registered actor IDs/roles; refuse lookalike/invented authority actors.
- B4: caller cache is not authority; cache is internal to a verification operation.
- B5: promotion/revocation replay anchored to fixed-start history; deleted revocations/hand-built advanced history refused.
- B6: self-mutating Task 3 write-capable workflows removed before repair.

R1/R4 remain unresolved for human execution and must not be presented as satisfied by process-local synthetic mechanics.

## Exact controller verification

At `10d46821...`:
- Task 3 run `38764885273`, job `116525386712`: 57 focused + 160 unified tests passed.
- frozen Task 2 run `38764885283`: success.
- inherited synthetic integration `38764885312`: success.

Controller GREEN is not acceptance.

## Next action

Obtain a Macha focused recheck of B1-B6 only on exact `10d468214aa057be023e38cd7a89d64f208d92e3`.

If Macha accepts, freeze exact Task 3 head first, update PR #322/#323, then derive the Task 4 implementation plan from the controlling Task 4 spec before creating any Task 4 RED execution branch.

## Permanent operating rule

Continue iterative self-audit/repair and keep PR #322/#323 updated with all historical audits, exact identities, scripts, tests, results, failures and no-repeat classifications so successors do not redo settled work.

Global authority remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
