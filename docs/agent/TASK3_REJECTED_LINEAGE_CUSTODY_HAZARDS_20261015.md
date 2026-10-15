# Unified Task 3 rejected-lineage custody hazards — 2026-10-15

Status: `NON_AUTHORIZING_AUDIT__READ_BEFORE_ANY_TASK3_REPAIR_PUSH`

This file exists so a successor does not accidentally destroy RED evidence or mistake bot-mutated history for independently authored repair evidence.

## Controlling rejected state

- rejected Task 3 candidate: `851544e8dc2a3881193a4d5bbcf07933e1d61149`
- PR: #392
- independent Macha review head: `869ca777a498181c519ccfc04b8bf5db0f2888c7`
- verdict: `REJECT_UNIFIED_TASK3`
- gate: `TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

Macha's six blockers T3-B1 through T3-B6 are controlling. In particular, T3-B6 is an infrastructure/custody blocker and must be addressed before any substantive Task 3 repair push.

## T3-B6: self-mutating workflow hazard

The rejected Task 3 lineage contains GitHub Actions workflows with `contents: write` that run repository patch scripts and commit/push changes back to the Task 3 branch. This is unacceptable for future RED evidence because a deliberately failing test can be rewritten by automation before a human/agent evaluates the failure.

Known write-capable workflows on the rejected lineage include:

1. `.github/workflows/task3-red6-actor-repair.yml`
   - triggers on pushes to `work/unified-task3-registry-impl-20261015` touching Task 3 registry/test/workflow surfaces;
   - runs `scripts/agent/task3_red6_actor_identity_repair.py`;
   - commits/pushes a GREEN migration when it changes files.

2. `.github/workflows/apply-task3-cycle1-hardening.yml`
   - has `contents: write`;
   - runs `scripts/v5/td_unified/apply_task3_cycle1_hardening.py`;
   - commits/pushes Task 3 hardening changes.

3. `.github/workflows/apply-task3-cycle4-hardening.yml`
   - has `contents: write`;
   - runs `scripts/v5/td_unified/apply_task3_cycle4_hardening.py`;
   - commits/pushes when the patch script changes files.

Other historical apply/repair workflows under the Task 3 lineage must be audited for the same pattern before any repair branch is pushed. Do not assume this list is exhaustive merely because these workflows are named here.

## Known bot-authored commit

Confirmed bot-authored Task 3 commit:

- `9052e3ce32f7f8b84d7445e3ec81826c79b6960d`
- commit message: `task3 GREEN6: migrate actor-bound registry fixtures`
- parent: `3bf1a2a60d92912f648c1d6c8df4bb48431778cf`
- author/committer: `github-actions[bot]`
- associated repair path: RED6 actor-identity migration machinery, including `.github/workflows/task3-red6-actor-repair.yml` and `scripts/agent/task3_red6_actor_identity_repair.py`.

This is a known mapping, not a claim that it is the only bot-authored commit. The successor must enumerate the full PR #392 commit history and record every `github-actions[bot]` authored/committed Task 3 change together with the workflow/script that produced it before declaring B6 closed.

## Required B6 repair order

Before adding B1-B5 production fixes:

1. preserve exact rejected head `851544e8...` and Macha review evidence unchanged;
2. cut a focused repair lineage without mutating the rejected candidate;
3. disable/delete self-mutating Task 3 workflows or convert them to explicit manual/read-only verification workflows with no repository commit/push step;
4. add a regression that fails if a Task 3 workflow used for qualification has repository write permission or a commit/push repair step;
5. enumerate bot-authored commits and bind each to its producing workflow/script in this custody record or a successor machine-readable mirror;
6. only then add Macha B1-B6 RED tests;
7. verify RED before changing production registry logic.

## RED evidence rule

Future RED tests must be immutable evidence. A workflow may run them and report failure; it may not rewrite them, rewrite production code, or auto-commit a fix in response to that failure.

One-shot historical repair scripts may remain in Git as provenance, but must be clearly labelled historical/non-runnable-by-default and must not be wired to push-triggered write workflows.

## Authority effect

None. Recording this lineage/custody hazard does not repair Task 3 and grants no authority.

Global stop state remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
