# Macha focused re-review — Task 0 B1–B5 repair (PR #384)

Date: 2026-10-15.

Role: independent hostile reviewer of controller work. Scope: B1–B5 only. Non-controlling.

**Read-only.** No candidate outcome, `reader_validation`, `reader_oracle` or protected object was opened, and nothing was recomputed.

## Verdict

`REJECT_TASK0_B1_B5_REPAIR`

**B1–B4 are closed.** **B5 is not.** The repair merge that brings the controlling PR #380 amendment into the ancestry (`f1267d5e`) keeps the first parent's tree. The amendment file is therefore absent from the repaired tree. Because `5b6bf07e` is now the merge base, merging Task 0 into its destination plan branch deletes the controlling taxonomy amendment. That is a contradictory authority path introduced by the repair itself.

`TASK0_REMAINS_OPEN__UNIFIED_TASK1_REMAINS_BLOCKED`

## 1. Head reviewed

`db92f80d128c37b99aa7d2c169eaf44447fa2164` (PR #384, branch `repair/task0-b1-b5-20261015`).

Ancestors verified:
- `c80d7398` (rejected candidate);
- `5b6bf07e` (PR #380 taxonomy amendment);
- `9328f1c0` (base plan).

`db92f80d` differs from `f1267d5e` only by one line in `.github/workflows/td-unified-task0-b1-b5-repair.yml` (CI trigger).

## 2. B1 — CLOSED

The PR #356 decomposition now has exactly five children:

| child | class | state / destination | identity |
|---|---|---|---|
| `OLD_TASK1_IMPLEMENTATION` | REUSABLE | REDIRECT, ADAPT_AND_WRAP | `ff597faf`, `scripts/production_synthetic/canonical_v1.py`, blob `b8a34d8d…` |
| `OLD_TASK2_IMPLEMENTATION` | REUSABLE | REDIRECT, ADAPT_AND_WRAP | `ff597faf`, `custody_v1.py`, blob `8efb7622…` |
| `OLD_TASK3_REQUIREMENTS` | PRODUCTION_INTERFACE_DEPENDENCY | REDIRECT, requirements only | — |
| `OLD_TASK4_REQUIREMENTS` | KNOWN_TRUTH_SUBSTRATE | REDIRECT → `KNOWN_TRUTH_CASEBUNDLE_V1` / `TRUTH_BUNDLE_V1` | — |
| `OLD_TASKS5_12` | SUPERSEDED | STOP_AND_FREEZE | — |

`active_or_partial_work` now reads:
- `TASKS1_2_IMPLEMENTED_AND_CONTROLLER_VERIFIED__TASK3_STOPPED_REQUIREMENTS_MIGRATE_ONLY` @ `ff597faf`;
- `TASK4_STOPPED_REQUIREMENTS_MIGRATE_ONLY__TASKS5_12_SUPERSEDED`.

Both agree with `PREMERGER_MERGED_CUSTODY_COMPLETENESS_V1.json`. The validator (`_validate_b1_b5_repair_guards`) fails closed on wrong children, an unbound head, or dropped Task 4 requirements.

**Precedence.** Mixed parents (e.g. `PR356_SYNTH_PLAN` SUPERSEDED/STOP_AND_FREEZE with reusable children) are lawful under the controlling plan's precedence rule: Task 0 migration amendment, line 126, "Do not give one artifact conflicting classes without an explicit decomposition record." The explicit decomposition record is machine-required for every mixed parent, so there is no contradiction without a precedence rule.

## 3. B2 — CLOSED

Every identity was resolved independently against git. All match exactly:
- `ff597faf:…canonical_v1.py` → `b8a34d8d…`
- `ff597faf:…custody_v1.py` → `8efb7622…`
- `2c2723a1:…v3-1-1-implementation.md` → `ad81e3f2…`
- `ac1e73d7:scripts/v79/v79_v2_core_score_authority.py` → `fa1fb78f…`
- `c6899a29:…TD_CORRECTED_REPLAY_OUTCOME.md` → `91fe2cb4…`
- `f5a8ebed:…READER_FIT_SUPPORT_OVERLAP_PROFILE_V1.json` → `e816483b…` (SHA-256 `b78e65af…`)
- `f5a8ebed:…READER_FIT_DATA_GEOMETRY_PROFILE_V1.json` → `1b50ceb4…` (SHA-256 `1ddf3782…`)
- receipt index SHA-256 `2af2acc3…` (repo, `ccc3a089`)
- V79 terminal receipt SHA-256 `ef10852e…`, `byte_custody` LOCAL_ONLY with the full local path

The validator now:
- requires a 40-hex commit and either a 64-hex digest or a 40-hex blob + path, plus `byte_custody`, when identity is available;
- requires `identity_unavailable_reason` otherwise;
- refuses `AUTHENTICATED_CALIBRATION*` authority with unavailable identity;
- has a test proving a truncated commit is refused.

The old Tasks 1–2 children are identified by commit + exact path + blob, not by branch.

## 4. B3 — CLOSED

`MACHA_REAL_DATA_AUDIT` has the same `current_authority` (`AUDIT_CUSTODY_AUTHORITY_ONLY`) in the matrix and the dual-stream registry; the validator now refuses cross-surface authority conflicts. Its components are split:
- **Reusable:** partition-independent operator/support facts (289 zero-operator addresses; 17,186 core; source-only 730/4,894/4,710; reader-fit Level-4 census).
- **Protected-partition facts:** stress-only (`PROSPECTIVE_CONVENTION_STRESS_ONLY`, `calibration_authorized: false`), validator-enforced.

The four repair scripts read and write only Task 0 JSON/validator/test files; there is no data, SQLite, NPZ, reader-partition or network access. Both `audit_boundaries` remain all-false.

## 5. B4 — CLOSED

`PR356_TASK1` and `PR356_TASK2` bind my checkpoint (`f53c13e6`, `docs/agent/PRODUCTION_SYNTHETIC_TASKS_1_2_CHECKPOINT_MACHA_20261014.md`, SHA-256 `412473ac…`, matching the file) as `AUTHOR_PROVENANCE_ONLY__PR382_IS_INDEPENDENT_VERIFICATION`.

The unresolved ledger carries every reuse condition, each with `blocks_same_code_path: true`:
- `U_TASK2_REUSE_O1`–`O8`;
- `U_TASK2_REUSE_D1_EXCEPTION_WRAPPING`;
- `U_TASK2_E2_PRECOMMITMENT_ERRATUM`;
- `U_TASK2_POST_REVEAL_FRESH_FAMILY`;
- `U_TASK3_READER_FIT_CALIBRATION_STATUS`.

Nothing represents unified Task 1 as done:
- `task1_blocked: true`;
- Task 1's destination is "feeding unified Task1; unified receipt recursion/authority model remains new work";
- Task 2 "does not satisfy unified Task2 manifest/access law";
- `U_TASK1_3_FOUNDATION` stays open and blocks same-code-path, known-truth and human execution.

## 6. B5 — NOT CLOSED (blocking)

What was repaired correctly:
- The taxonomy JSON records `historical_biological_evidence_authority: RETROSPECTIVELY_RATIFIED_20261014`, with the exact chronology (`f98f0041` 14:44:53 → `5b6bf07e` 15:43:21 → `4417949b` 15:45:03).
- It binds the amendment by head and by blob `7f20050c…`, an immutable content identity whose 10-class list I verified previously.
- `5b6bf07e` is now in the ancestry.

**The new defect:**

| | |
|---|---|
| file | `docs/superpowers/plans/2026-10-14-unified-td-qualification-downstream-custody-v1-task0-taxonomy-amendment.md` (blob `7f20050c2a8d0f80f0c6418c007bc12f7fc1083f` at `5b6bf07e`) |
| record | merge commit `f1267d5e` (parents `8cb43355`, `5b6bf07e`) has a tree identical to `8cb43355`, so the amendment file **does not exist at `db92f80d`** |
| consequence | PR #381's base is the plan branch at `5b6bf07e`, now the merge base. `git diff --name-status origin/plan/…-20261014 db92f80d` shows exactly one deletion: this amendment. `git merge-tree --write-tree origin/plan/… db92f80d` yields a tree without it. Merging Task 0, by any strategy, deletes the controlling amendment that Task 0 claims to be bound to. |
| why the invariant is insufficient | the validator and `test_b5_…` assert the head and blob strings in the taxonomy JSON only; nothing checks that the bound file is present in the tree, or that the Task 0 lineage deletes no controlling-plan file |
| smallest lawful repair | (1) restore the file byte-identically: `git checkout 5b6bf07e -- <path>`, then commit; the blob must equal `7f20050c…`. (2) Add a regression test asserting that the path exists, that its git blob hash equals `7f20050c…`, and that its parsed class list equals `MIGRATION_CLASSES`. (3) Add a CI/test assertion that `git diff --diff-filter=D <plan-base> HEAD -- docs/superpowers/plans` is empty. |
| scope | B5 only; B1–B4 need no change |

## 7. Hostile tests

Local run at `db92f80d` (Windows, `sea-ad-jepa-v3`, Python 3.11.15; local evidence, not CI):

```
pytest tests/v5/td_unified/test_task0_b1_b5_regressions.py tests/v5/td_unified/test_premerger_migration_task0.py tests/v5/td_unified/test_premerger_custody_completeness_v1.py -q
35 passed
```

The tests pass because none covers the B5 tree-presence defect.

## 8. Non-blocking observations

- **N1.** Seven records keep `exact_identity_available: false` with `authority_basis: EXACT_COMMIT_AND_AUTHENTICATED_AUDIT_OR_RECEIPT` (JEPA_AUDIT_PR322, PR318_321, PR328 ×3, PR339, PR332_351). Each has a reason that narrows authority, and most require requalification. Suggest relabelling the basis, and having unified Task 1's registry refuse consumption of any identity-unavailable record until bound.
- **N2.** The old Tasks 1–2 children bind module blobs only. Their tests are exactly resolvable through commit `ff597faf`, but binding the test-file blobs (including `custody_fixtures_v1.py`) too would make the known-answer contract explicit.
- **N3.** Mixed parents could carry an explicit `effective_classification: DECOMPOSITION_RECORD` field for readers who see only the parent row.
- **N4.** The four `apply_task0_b1_b5_repairs*.py` scripts are one-shot mutators committed into `scripts/v5/td_unified/`. Mark them as historical repair tools so later tasks do not re-run them.

## 9. Freeze decision

Task 0 may **not** be frozen at `db92f80d`. Once the B5 file restoration and its regression land at a new head, a re-check of B5 alone suffices.

`TASK0_REMAINS_OPEN__UNIFIED_TASK1_REMAINS_BLOCKED`

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
