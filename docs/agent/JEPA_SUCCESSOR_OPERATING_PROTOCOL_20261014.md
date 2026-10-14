# JEPA successor operating protocol — 2026-10-14

Status: `CURRENT_OPERATING_PROTOCOL__NO_NEW_SCIENTIFIC_AUTHORITY`

Purpose: make the takeover operationally safe after the historical/scientific handoff. This file does not change any scientific conclusion, threshold, gate, target, representation, or authority. It defines how a successor should work without creating stale-state errors, duplicate audits, branch drift, or accidental authority expansion.

Global authority remains exactly:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Branch ownership

- PR #322 / `science/jepa-robust-pipeline-post-jepa-anything-audit-20261013` is the executable audit/custody surface. Keep current audited scripts, tests, workflows, receipts, machine state, historical cross-checks, and successor indexes there.
- PR #323 / `handoff/jepa-lane-takeover-20261013` is navigation/takeover only. Do not turn it into a second executable fork.
- New scientific designs or implementations use separate prospective branches rooted at an explicitly named exact head.
- Frozen evidence branches are append-only evidence. Do not rebase, force-update, or rewrite them merely to simplify history.

## 2. Start-of-task stale-state check

Before changing code or science:
1. read `JEPA_LANE_SUCCESSOR_HANDOFF_V4_20261014.md` and the PR #322 next-action checklist;
2. verify current PR #322/#323 heads and the takeover checkpoint;
3. check whether another agent advanced the exact dependency branch;
4. confirm the authority terminal and protected-data state;
5. if bytes, scientific question and authority are unchanged, do not repeat historical audits.

If a dependency head moved, distinguish code/science changes from append-only docs/receipt changes. Never invalidate a legitimate historical result merely because a governance branch tip advanced.

## 3. Concurrent-agent protocol

- Parallel work only on separable lanes.
- Each agent returns exact branch/head/base, tests/runs, hashes, authority state and protected/controller-data access.
- Do not merge another agent's branch merely to obtain documentation; reconcile immutable commit/blob/receipt identities first.
- If two agents modify the same scientific contract, STOP and reconcile prospectively.
- Independently audit another agent's result before using it downstream.
- V80/synthetic statistics, real-TD gate engineering and post-TD architecture remain separate authority lanes.

## 4. Scientific change protocol

For every new gate/repair/experiment:
1. classify history: `ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`;
2. state the unresolved question and why historical work did not already answer it;
3. freeze the prospective contract before values;
4. RED test before new code behavior;
5. implement the smallest lawful change;
6. run exact-head verification;
7. hostile-review against frozen contract and no-repeat matrix;
8. correct overreach and rerun;
9. freeze hashes/receipt/environment;
10. update the canonical audit/handoff only when the critical path changes.

Do not use current candidate outcomes to choose thresholds, comparators, support envelopes, source subsets, locality, evidence ladders, or model families.

## 5. Evidence/authority vocabulary

Use explicit labels:
- `HISTORICAL_PRIOR` — scoped, informative, not current PASS;
- `MECHANICALLY_QUALIFIED` — code/test mechanics, not biology;
- `SYNTHETIC_TEST_QUALIFIED` — known-truth test qualification, not human biology;
- `BIOLOGICAL_PASS/FAIL/NOT_ESTIMABLE` — only after authorized real execution;
- `FORENSIC_ONLY` — never resumable authority;
- `CLOSED/SPENT` — do not repeat absent explicit reopen trigger.

Never convert `NOT_ESTIMABLE` to FAIL, mechanics to biology, or synthetic amplitudes to human calibration.

## 6. Custody update rule

After a critical-path milestone, durably record exact source/base head, workflow run/job/test count, hashes/receipts, environment when decision-bearing, protected/controller access, authority flags, result scope, and remaining prerequisite. Update PR #322 machine/custody indexes first; update PR #323 only for navigation/current-next-action changes.

Large/private binaries remain external custody. Preserve exact SHA-256, size, class, location and allowed role rather than copying them into public Git.

## 7. Controller return package

Every major controller return should include:
- exact branch/head/base;
- question resolved;
- exact verification evidence;
- hashes/receipts;
- protected/controller access status;
- any authority change (normally none);
- remaining dependency/stop condition;
- what was NOT run.

Never report green engineering as a target result.

## 8. Current work order

Primary real-TD lane:
1. G11/G12 real population/evidence/support registry;
2. R1 recurrence/null/substantive rule;
3. G7 terminal stability;
4. G9/S1/S2 geometry-specific stability;
5. G2 same-metric substantive magnitude;
6. R4/C6/C4 matched increments;
7. G8 human technical calibration;
8. G6 human teacher target/evidence-right contract;
9. full 198-row readiness audit;
10. only then request fresh real-TD authority.

Separate synthetic lane: V79 remains frozen `NOT_QUALIFIED`; V80 benchmark is qualified; only a prospectively frozen successor estimator may be qualified next with immutable V79 Q00-Q11 non-regression and no tuning after controller scoring.

Post-TD work remains dormant until a legitimate target portfolio is frozen.

## 9. Stop conditions

STOP if a rule requires current outcomes to define it; provenance cannot be authenticated; repaired address binding is absent; support must be manufactured; source failure is averaged away; a composite rescues a failed constituent; a closed lane is reopened without trigger; concurrent agents changed the same contract; or any real TD/selection/TD60/Stage4/EMA/training action lacks fresh authority.

Terminal:
`SUCCESSOR_PROTOCOL_FROZEN__HISTORY_DO_NOT_REPEAT_BY_DEFAULT__OUTCOMES_UNREAD__REAL_TD_OFF__TARGET_NONE__REPRESENTATION_NONE__TRAINING_OFF`
