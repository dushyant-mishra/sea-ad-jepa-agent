# JEPA successor operating protocol — 2026-10-14

Status: `CURRENT_OPERATING_PROTOCOL__NO_NEW_SCIENTIFIC_AUTHORITY`

Purpose: make the takeover operationally safe after the historical/scientific handoff. This file does not change any scientific conclusion, threshold, gate, target, representation, or authority. It defines how a successor should work without creating stale-state errors, duplicate audits, branch drift, or accidental authority expansion.

Global authority remains exactly:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Branch ownership

- PR #322 / `science/jepa-robust-pipeline-post-jepa-anything-audit-20261013` is the executable audit/custody surface. Keep current audited scripts, tests, workflows, receipts, machine state, historical cross-checks, and successor indexes here.
- PR #323 / `handoff/jepa-lane-takeover-20261013` is navigation/takeover only. Do not turn it into a second executable fork.
- New scientific designs or implementations should use separate prospective branches rooted at an explicitly named exact head.
- Frozen evidence branches are append-only evidence. Do not rebase, force-update, or rewrite them merely to simplify history.
- A new branch must name its parent head in its first durable design/authorization document.

## 2. Start-of-task stale-state check

Before changing code or science:
1. read `JEPA_LANE_SUCCESSOR_HANDOFF_V4_20261014.md` and `JEPA_LANE_NEXT_ACTIONS_AND_TAKEOVER_CHECKLIST_20261014.md`;
2. verify the current PR #322/#323 heads;
3. read `JEPA_LANE_TAKEOVER_CHECKPOINT_20261014.json`;
4. check whether another agent has advanced the exact dependency branch;
5. confirm the authority terminal has not changed;
6. confirm whether biological outcomes/controller truth relevant to the task remain unopened;
7. if the underlying bytes, scientific question and authority are unchanged, do not repeat the historical audit.

If any dependency head moved, first determine whether the new commits are code/science changes or docs/receipts only. Never invalidate a legitimate historical result solely because an append-only governance branch tip moved.

## 3. Concurrent-agent protocol

Parallel work is allowed only on separable lanes.

- Each agent owns a distinct branch/worktree and must return exact head, base head, test/run identities, hashes, authority state, and whether any protected/controller data were read.
- Do not merge another agent's branch into a scientific execution branch simply to obtain documentation. Reconcile by immutable commit/blob/receipt identities first.
- If two agents modify the same scientific contract, STOP and reconcile the contract prospectively before either result becomes authority.
- If another agent returns a result while you are working, independently audit its custody/result before consuming it downstream.
- V80/synthetic statistical qualification, real-TD gate engineering, and post-TD architecture work remain separate authority lanes.

## 4. Scientific change protocol

For every gate/repair/experiment:
1. classify history: `ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`;
2. state the unresolved question and why historical work did not already answer it;
3. freeze the prospective scientific contract before values;
4. write a RED regression/hostile test before new behavior where code is involved;
5. implement the smallest lawful change;
6. run exact-head verification;
7. hostile-review the diff against the frozen contract and historical no-repeat matrix;
8. fix any overreach and rerun;
9. freeze hashes/receipt/environment;
10. update PR #322 custody/index and PR #323 navigation only if the critical path changed.

Do not use current candidate outcomes to choose a threshold, comparator, support envelope, source subset, locality, evidence ladder, or model family.

## 5. Evidence/authority vocabulary

Use these labels explicitly:
- `HISTORICAL_PRIOR` — informative, scoped, not current PASS;
- `MECHANICALLY_QUALIFIED` — code/test behavior qualified, not biology;
- `SYNTHETIC_TEST_QUALIFIED` — test-of-test passed known truth, not human biology;
- `BIOLOGICAL_PASS/FAIL/NOT_ESTIMABLE` — only after authorized real execution under frozen rules;
- `FORENSIC_ONLY` — never resumable authority;
- `CLOSED/SPENT` — no repeat absent explicit reopen trigger.

Never convert `NOT_ESTIMABLE` to FAIL, mechanical validity to biological validity, or synthetic effect sizes to human calibration.

## 6. Custody update rule

After any milestone that changes the critical path, update all relevant durable surfaces:
- exact source branch/head;
- exact workflow run/job and test count;
- source/blob/receipt hashes;
- environment/dependency identity where decision-bearing;
- protected/controller data-access statement;
- authority flags;
- result scope;
- new prerequisite or stop condition;
- `JEPA_LANE_CUSTODY_FILE_INDEX_20261014.csv` when new executable custody is added;
- `JEPA_LANE_TAKEOVER_CHECKPOINT_20261014.json` when current machine state changes;
- `JEPA_LANE_CURRENT_DELTA_V2_20261014.md` (or successor append-only delta) for changed operational facts;
- PR #323 handoff only for navigation/current-next-action changes.

Do not copy large/private binaries to public Git. Preserve exact SHA-256, size, scientific class, custody location, and allowed role instead.

## 7. Controller return package

Every major return to the controller should contain only decision-bearing information:
- exact branch and head;
- base head;
- what scientific/mechanical question was resolved;
- exact tests/runs and PASS/FAIL/NE;
- hashes/receipts needed for independent verification;
- protected/controller data access status;
- what authority changed, if any (normally none);
- remaining dependency/stop condition;
- explicit statement of what was NOT run.

Do not report a green implementation as a target result.

## 8. Current lane assignment for successor

Primary real-TD lane:
- finish G11/G12 frozen real registry;
- finish R1 recurrence/null/substantive rule;
- finish G7 terminal stability;
- finish G9/S1/S2 geometry-specific stability;
- finish G2 same-metric substantive magnitude;
- finish R4/C6/C4 matched increments;
- prepare G8 human technical calibration;
- freeze G6 human teacher target/evidence rights;
- then rerun the complete readiness audit before requesting real-TD authority.

Separate synthetic lane:
- V79 remains frozen `NOT_QUALIFIED`;
- V80 benchmark package is qualified;
- only a prospectively frozen successor estimator may be qualified next, with immutable V79 Q00-Q11 non-regression and no tuning after controller scoring.

Post-TD lane remains dormant until a legitimate target portfolio is frozen.

## 9. Stop conditions

STOP and return to controller if:
- a scientific rule can only be completed after looking at current candidate outcomes;
- an exact prerequisite/data/provenance identity cannot be authenticated;
- repaired molecular-address binding is absent where required;
- support must be imputed/manufactured to make a claim estimable;
- source-specific failure is being averaged away;
- a composite is being used to rescue a failed constituent;
- a historical closed lane is being reopened without an explicit trigger;
- another agent changed the same scientific contract concurrently;
- any real TD, target selection, TD60, Stage4, production EMA selection, or training action would occur without fresh explicit authority.

Terminal remains:
`SUCCESSOR_PROTOCOL_FROZEN__HISTORY_DO_NOT_REPEAT_BY_DEFAULT__OUTCOMES_UNREAD__REAL_TD_OFF__TARGET_NONE__REPRESENTATION_NONE__TRAINING_OFF`
