# START HERE — JEPA PROJECT

Date: 2026-09-18

Status: `TAKEOVER_FOR_F16_F17_AND_HANDOFF_GOVERNANCE_REPAIR__TERMINAL_OUTCOMES_UNOPENED__TRAINING_OFF`

## Current scientific base

Implementation branch:

`impl/v5-full104-masking-redteam2-20260918`

Scientific handoff base:

`3084c1f497a3db6056fd100fb896ccdf67318c8a`

Exact-head focused CI:

`35392547631` — SUCCESS

- regression step: `268 passed`
- explicit no-skip rerun: `268 passed`
- terminal FULL104 outcomes: UNOPENED
- training: OFF
- protected outcomes: CLOSED
- D_shared outcomes: CLOSED

The first task of the new chat is **not** to restart the project. It is to repair only the unresolved issues listed in the current takeover handoff, requalify the changed scientific head, then resume the already-defined GPU calibration/freeze sequence.

## Read first

1. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260918_F16_F17_GOVERNANCE_TAKEOVER.md`
2. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
3. `docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json`
4. `docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md`
5. `docs/agent/JEPA_NEW_CHAT_COMMANDS_20260918_V5_FULL104_MASKING_CURRENT.md`
6. `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`

Before acting, re-fetch the live implementation branch and PR #20. If the live source/test/workflow head differs from the scientific base above, classify the delta before editing.

## Do not duplicate Project files

The next chat is in the same Project and can access the already-uploaded Project artifacts. Do not create or re-upload duplicate copies merely for handoff convenience. The takeover handoff names the relevant Project files and their roles.

## Permanent methodology

For every component classify it as:

- `ALREADY_AUDITED`
- `SUPERSEDED`
- `OPEN`
- `CHANGED_INPUT_REQUIRES_REQUALIFICATION`

For every scientific repair:

1. reproduce the defect;
2. make the smallest prospective repair;
3. add a discriminating adversarial regression;
4. self-review the diff;
5. run historical/spillover checks;
6. run exact-head CI;
7. require the no-skip gate;
8. independently re-review before promotion.

Do not weaken tests to restore green status.

## Hard boundaries

`TRAINING_OFF`

`NO_TERMINAL_MASKING_OUTCOME_ACCESS_UNTIL_PRETERMINAL_REPAIRS_AND_FREEZE_CLOSE`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

`NO_PATHOLOGY_DEV_SEALED_OUTCOME_ACCESS_WHILE_DESIGN_OPEN`

Historical/smaller-run material may motivate hypotheses or model shape only; it may not silently become current FULL104 data, targets, folds, burden, seed, row cap, policy, PASS, or training authority.
