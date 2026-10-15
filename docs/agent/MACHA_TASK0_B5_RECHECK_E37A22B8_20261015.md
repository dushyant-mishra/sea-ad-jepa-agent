# Macha narrow B5 re-check — Task 0 repair (PR #384)

Date: 2026-10-15.

Role: independent hostile reviewer of controller work. Scope: B5 only. B1–B4 were closed at `db92f80d`, and the delta to this head does not touch them. Non-controlling.

**Read-only.** No protected object was opened and nothing was recomputed.

## Verdict

`ACCEPT_TASK0_B1_B5_REPAIR`

`TASK0_MAY_BE_FROZEN__UNIFIED_TASK1_MAY_BEGIN_PROSPECTIVELY`

This does not authorize training or any later scientific authority.

## 1. Head reviewed

`e37a22b8059c0a4a93a789a8ca916fb7acde9fe3` (PR #384). Ancestors: `db92f80d`, `5b6bf07e`, `c80d7398`.

The delta from `db92f80d` is three commits (`08df3720`, `f1b5fc72`, `e37a22b8`) touching only:
- the restored amendment file;
- `tests/v5/td_unified/test_task0_b1_b5_regressions.py`;
- the B1–B5 workflow (`docs/superpowers/plans/**` trigger, `fetch-depth: 0`).

No B1–B4 record, validator or completeness artifact changed, so the B1–B4 closures at `db92f80d` carry over.

## 2. B5 — CLOSED

Each check below was run independently.

- **Restored byte-identically.** `git rev-parse e37a22b8:docs/superpowers/plans/2026-10-14-unified-td-qualification-downstream-custody-v1-task0-taxonomy-amendment.md` = `7f20050c2a8d0f80f0c6418c007bc12f7fc1083f`, the same as at `5b6bf07e`.
- **No deletion path.** `git diff --name-status --diff-filter=D origin/plan/unified-td-qualification-downstream-custody-v1-20261014 e37a22b8` is empty. The plan branch is at `5b6bf07e`.
- **Merge preserves the controlling amendment.** `git merge-tree --write-tree origin/plan/… e37a22b8` gives tree `11d2879e…`, which contains the amendment at blob `7f20050c…`.
- **Content binding.** `test_b5_controlling_plan_amendment_is_present_exact_and_matches_validator_enum`:
  - asserts the file exists;
  - asserts `git hash-object` equals `7f20050c…`;
  - parses the class bullets from the amendment and compares them with `MIGRATION_CLASSES` imported from the validator.

  The two sources are independent, so the check is not circular.
- **Lineage guard.** `test_b5_task0_does_not_delete_any_plan_file_from_controlling_plan_head` asserts that `git diff --diff-filter=D 5b6bf07e..HEAD -- docs/superpowers/plans` is empty. CI now fetches full history.
- **Chronology.** `RETROSPECTIVELY_RATIFIED_20261014`, with the exact `f98f0041` → `5b6bf07e` → `4417949b` chronology, is retained. No contradictory authority path remains: the controlling amendment is both in the ancestry and in the tree at the bound blob.

## 3. Hostile tests (local, Windows, `sea-ad-jepa-v3`; local evidence, not CI)

| run | result |
|---|---|
| clean: `test_task0_b1_b5_regressions.py` + `test_premerger_migration_task0.py` + `test_premerger_custody_completeness_v1.py` | 37 passed |
| mutation 1, one byte appended to the amendment (uncommitted) | `test_b5_controlling_plan_amendment_is_present…` FAILED |
| mutation 2, amendment deleted from the working tree | same test FAILED |
| mutation 3, committed deletion on a throwaway local commit, never pushed | both B5 tests FAILED |

After the probes the worktree was restored to `e37a22b8` with blob `7f20050c…` and a clean status.

Controller CI at this head, recorded but not used as my verdict:
- `task0-migration-audit` pass (run `38667792825`);
- `test` pass (run `38667792777`);
- `verify` pass (run `38667792863`).

## 4. Residual non-blocking observations

N1–N4 from the `db92f80d` review stand as non-blocking recommendations for unified Task 1:
- **N1.** Relabel identity-unavailable records that carry an exact-commit basis, and refuse to consume them until bound.
- **N2.** Bind the old Tasks 1–2 test blobs.
- **N3.** Add an `effective_classification` marker on mixed parents.
- **N4.** Mark the one-shot repair scripts historical.

## 5. Freeze decision

Task 0 may be frozen at exactly `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`.

Unified Task 1 may begin prospectively, RED-first, under PR #380. It must:
- carry `U_TASK1_3_FOUNDATION` and the O1–O8 / D1 / E2 / post-reveal / reader-fit-calibration items as blocking obligations;
- consume old Tasks 1–2 only as ADAPT_AND_WRAP substrate, never as completed unified tasks.

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
