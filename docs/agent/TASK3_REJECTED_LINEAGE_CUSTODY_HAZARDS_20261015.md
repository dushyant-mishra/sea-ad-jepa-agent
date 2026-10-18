# Unified Task 3 rejected-lineage custody hazards — 2026-10-15

Status: `NON_AUTHORIZING_AUDIT__B6_CLOSED__BOT_LINEAGE_ENUMERATED__READ_ONLY_POLICY_GREEN`

This file exists so a successor does not accidentally destroy RED evidence or mistake bot-mutated history for independently authored repair evidence.

## Controlling rejected state

- rejected Task 3 candidate: `851544e8dc2a3881193a4d5bbcf07933e1d61149`
- PR: #392
- independent Macha review head: `869ca777a498181c519ccfc04b8bf5db0f2888c7`
- verdict: `REJECT_UNIFIED_TASK3`
- gate: `TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

Macha's six blockers T3-B1 through T3-B6 remain the controlling review findings. This record closes **T3-B6 only** at the successor/controller level. It does not accept Task 3 and does not alter the independent-review gate.

## T3-B6: self-mutating workflow hazard

The rejected Task 3 lineage historically used GitHub Actions workflows with `contents: write` that ran repository patch scripts and committed/pushed changes back to `work/unified-task3-registry-impl-20261015`. That pattern is unacceptable for RED evidence because a deliberately failing hostile test can be rewritten by automation before an independent evaluator assesses the failure.

### Temporal workflow audit

The important distinction is historical versus still-armed state at rejected head `851544e8...`.

1. `.github/workflows/apply-task3-cycle1-hardening.yml`
   - historical write-capable revision at `10372a6a...`: `contents: write`, runs `scripts/v5/td_unified/apply_task3_cycle1_hardening.py`, commits/pushes GREEN1;
   - by rejected head `851544e8...` it had already been converted to `contents: read` verification-only and no longer committed/pushed.

2. `.github/workflows/apply-task3-cycle2-hardening.yml`
   - write-capable revision introduced at `40e3a274...`: runs `scripts/v5/td_unified/apply_task3_cycle2_hardening.py`, commits/pushes GREEN2;
   - by rejected head `851544e8...` it was `contents: read` verification-only.

3. `.github/workflows/apply-task3-cycle3-hardening.yml`
   - write-capable revision present at `15ffbac4...`: runs `scripts/v5/td_unified/apply_task3_cycle3_hardening.py`, commits/pushes GREEN3;
   - by rejected head `851544e8...` it was `contents: read` verification-only.

4. `.github/workflows/apply-task3-cycle4-hardening.yml`
   - still armed at rejected head `851544e8...` with `contents: write`;
   - runs `scripts/v5/td_unified/apply_task3_cycle4_hardening.py`;
   - commits/pushes GREEN4 source/test mutations.

5. `.github/workflows/task3-red6-actor-repair.yml`
   - still armed at rejected head `851544e8...` with `contents: write` and broad push trigger;
   - historical first form ran `scripts/agent/task3_red6_actor_identity_repair.py` and committed GREEN6 actor-identity changes;
   - later form ran `task3_red6_actor_identity_repair.py`, `task3_green6_actor_resolver_patch.py`, and `task3_green6_fixture_migration.py`, then committed/pushed GREEN6 fixture migration.

The ordinary `.github/workflows/unified-task3-registry.yml` is verification-only/read-only and is not part of the self-mutating class.

## Complete Task 3 bot-authored commit enumeration

Enumeration method: query the exact live Task 3 branch ancestry for commits authored by `41898282+github-actions[bot]@users.noreply.github.com`, then exclude the older September bot commit that predates frozen Task 2 and is not part of PR #392's Task 3 delta.

Exactly six Task 3 bot-authored commits occur after frozen Task 2 `c7dfff1c...`:

| bot commit | message | producing workflow revision/family | patch script(s) | immediate parent |
|---|---|---|---|---|
| `8196f0c4a8c4ac855dc9a23a9d1ff902ba78019c` | `task3 GREEN1: harden dependency, independence, and R1/R4 authority` | `apply-task3-cycle1-hardening.yml` write-capable cycle1 | `scripts/v5/td_unified/apply_task3_cycle1_hardening.py` | `7fd89b5eaff135175e0694cd2cf949ba5c050df8` |
| `ecab91c0669f6e6798ba280f2c739ed05a346564` | `task3 GREEN2: bind dependencies and promotion provenance to resolved objects` | `apply-task3-cycle2-hardening.yml`, introduced write-capable at `40e3a274...` | `scripts/v5/td_unified/apply_task3_cycle2_hardening.py` | `40e3a274e9065b7f10741dc7a3ad74ee6f366b3b` |
| `27c244b896d853ca41ad8e375b32a09ce056b2ad` | `task3 GREEN3: bind registry units to Task 2 execution table` | `apply-task3-cycle3-hardening.yml` write-capable cycle3 | `scripts/v5/td_unified/apply_task3_cycle3_hardening.py` | `15ffbac49c9a149d3f87089c94c2a7a5fe6e1044` |
| `e81ebbfe1ba828a4ea39f7f4d3ed737eb4fffac0` | `task3 GREEN4: bind semantic evidence and content validation receipts` | `apply-task3-cycle4-hardening.yml` write-capable cycle4 | `scripts/v5/td_unified/apply_task3_cycle4_hardening.py` | `ec450492d5cd1da49a198d91b8744e6ff3ecfe2d` |
| `a5397a8b81f4f8857ca00fcf38374c045094be2e` | `task3 GREEN6: bind producer executor actor identities` | `task3-red6-actor-repair.yml` at `c5970d9d...` | `scripts/agent/task3_red6_actor_identity_repair.py` | `c5970d9dadd05448bf2bf0be4bd7fe687be20c61` |
| `9052e3ce39e8e8acdc53ae19588f01a1ef4501be` | `task3 GREEN6: migrate actor-bound registry fixtures` | later `task3-red6-actor-repair.yml` form | `task3_red6_actor_identity_repair.py`; `task3_green6_actor_resolver_patch.py`; `task3_green6_fixture_migration.py` | `f1a742b4b8f769c244fcc3fbb8682ec4429c6ae9` |

### Correction of prior custody typo

The previously recorded SHA `9052e3ce32f7f8b84d7445e3ec81826c79b6960d` does **not** resolve to a repository commit. The actual Task 3 bot commit is:

`9052e3ce39e8e8acdc53ae19588f01a1ef4501be`.

The previously recorded parent `3bf1a2a60d92912f648c1d6c8df4bb48431778cf` was likewise not the parent of the live lineage commit; the immediate parent is `f1a742b4b8f769c244fcc3fbb8682ec4429c6ae9`.

## Successor containment and policy closure

The successor repaired infrastructure custody before adding new Task 3 hostile evidence:

1. deleted `.github/workflows/task3-red6-actor-repair.yml` first at successor commit `229317559f69929a72678ceebc1bdd43a0b62f65`;
2. deleted `.github/workflows/apply-task3-cycle4-hardening.yml` next at successor commit `6d6a0a315575ba61320b3fb7cac767d467219a49`;
3. verified both paths absent at the successor branch head;
4. preserved Macha H1-H6 plus alias/self-mint attacks as `tests/v5/td_unified/test_registry_v1_macha_rejection.py` at `51cdd4bea030be17242de7f81e9880dec802c6a7`;
5. forced read-only CI proof: `Unified Task 3 registry` run `38792404844`, job `116620027363`, with `GITHUB_TOKEN Contents: read`, produced `11 failed, 53 passed` exactly on B1, B2, five B3 actor attacks, H3/H4 cache attacks and H5/H6 history attacks;
6. added `tests/v5/td_unified/test_registry_v1_workflow_policy.py` and a dedicated read-only CI workflow; the first attempted policy run was invalid because pytest was absent and is not counted as RED evidence;
7. valid B6 RED: run `38798612344`, job `116641472764`, `Contents: read`, `5 failed`, each because `scripts/v5/td_unified/workflow_policy_v1.py` did not yet exist;
8. minimal policy implementation: `scripts/v5/td_unified/workflow_policy_v1.py` at repair commit `0fada97d6524d32a928c55a91da97c4e97d25f26`; it classifies Task 3 qualification workflows and rejects `contents: write`, `permissions: write-all`, Task 3 patch/migration scripts, `git commit`, and `git push`;
9. B6 GREEN: run `38798830296`, job `116642223925`, exact head `0fada97d...`, `Contents: read`, `5 passed in 0.06s`.

The policy suite also asserts that the two deleted write hazards remain absent and audits the current cycle1-cycle3/unified Task 3 workflows as read-only/non-mutating.

### Ordering deviation recorded

Parallel successor work landed B1/B2/B4 production repairs and a partial B3 actor-registry repair before the final B6 policy regression was green. This violated the preferred checklist ordering. It did **not** re-expose RED evidence to the original mutation mechanism because both still-armed write workflows had already been deleted and verified absent before those repair commits. The deviation is recorded rather than silently normalized; the B1-B4/B3 work must be evaluated on its own exact-head evidence.

## B6 closure decision

`T3-B6_CONTROLLER_CLOSED__INDEPENDENT_RECHECK_STILL_REQUIRED_FOR_TASK3_ACCEPTANCE`

Closure basis:

- rejected candidate and Macha evidence preserved;
- both live self-mutating workflows removed before successor RED work;
- all six bot-authored Task 3 commits enumerated and bound to workflow/script provenance;
- exact Macha attack suite preserved;
- dedicated future-regression guard proven RED→GREEN under `Contents: read`;
- guard fails on write permissions, mutator scripts and commit/push behavior, including renamed Task 3 qualification workflows.

This is controller-level closure only. Macha's final focused B1-B6 recheck remains mandatory before Task 3 can be accepted or frozen.

## RED evidence rule

Future RED tests are immutable evidence. A workflow may run them and report failure; it may not rewrite them, rewrite production code, or auto-commit a fix in response to that failure.

One-shot historical repair scripts may remain in Git as provenance, but must be clearly historical/non-runnable-by-default and must not be wired to push-triggered write workflows.

## Authority effect

None. B6 closure does not accept Task 3 and grants no target, representation, protected-value, Stage 4 or training authority.

Global stop state remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
