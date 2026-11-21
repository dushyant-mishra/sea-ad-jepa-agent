# Event121 — independent source-only two-branch assimilation and V5 workflow-guard compatibility audit (2026-11-21)

**Scope:** inspect existing Event120 custody on historical draft #322 and active draft #460; compare with prospective layout draft #599 and unmerged CI guard draft #596. This is a source-only cross-branch review, NOT independent C3 approval, new synthetic realization, or training.

## Verified inherited Event120

- #322 exact head before this review: `0386aa99809f1ddca43749f91f4657ecb8bc4de2`; #460: `eaa389b8031b60df6baec30292da3fe49baa76ee`.
- Event120 human note is Git blob `787c734fcf6ca665a7818655e3daac974438dc1b` on both; machine receipt is blob `d86e30e8ee96a2073dfefdca33422381cd932085` on both.
- #599 `1f669d3b1d4a3dfddab48797b269af2a618c85df` uses three rare-program genes in each of three 512-gene views, four original 15-gene programmes, a shared rare0/perturbation mechanism, six positive queries plus two null queries and eight distinct non-q panel members per query. It intentionally reuses selected non-q programme genes **across different q panels**. No q address appears in any panel. This is a *new V2 rule*, not an inherited global-disjoint-panel approval.
- #599 hosted run `44929694541` passed all eight inert metadata tests; prior source contradiction run `44929694542` passed six. Inherited runs `44929694559` and `44929694537` failed during Python setup, before generator execution.
- #322 returned exact-head Actions runs include a failing V80 public-original-archive workflow `44930168974`: downloading historical fit/receipt artifacts from run `38504094639` returned HTTP 404. This is **not** a fresh failure of the DEV2048 role geometry, and is distinct from Event95's owner-resolved private V80 backup. #460 exact-head four handoff workflows succeeded (runs `44930172362`, `44930172411`, `44930172380`, `44930172361`).

## New cross-branch integration finding: CI ENTRYPOINT REPAIR REQUIRED

At #599 exact source, **both** source-only workflows invoke `python -m unittest discover -s tests/v79 -p test_...py -v`:

1. `.github/workflows/dev2048-v2-prospective-role-allocation.yml` (Git blob `37f9904fe0cf6006fa8b6ee9cca01942dd1021e1`).
2. `.github/workflows/dev2048-v2-pregeneration-feasibility.yml` (Git blob `10cc5403722acb7d71c98ff9b56343f8547e1c3f`).

Unmerged review #596 at `bc9da0547f4e187969f5dc21bc7a188e9a519d8d`, source `scripts/v5/jepa_v5_ci_explicit_nonstepping_allowlist_v1.py` (blob `b6c9b7289f3013b4755c7b41ad701f3251c71759`), explicitly rejects `unittest discover` in automatically triggered workflows (`DISCOVERY_TEST_ROUTE`). Therefore **combining #599's two workflow files with the #596 guard, unchanged, is incompatible**. This is a prospective integration finding; the workflows are presently on different unmerged branches. It does not imply that #599 executed step-capable tests or that the current isolated metadata tests failed.

**Narrow corrective direction:** replace both discovery invocations with a literal, independently reviewed test-module or exact-file invocation, and add static cross-branch regression proving the final combined tree passes the guard. Do not broaden test collection, disable the guard, or run optimizer/backward/EMA to obtain GREEN. Fresh exact-head CI and peer review still required.

## Scientific and authority boundary

The eight metadata tests demonstrate address/role arithmetic, not physical gene-effect remapping. Independent C3 review must determine whether cross-query reuse supports valid right-q/wrong-q/null tests without panel/source shortcuts; a versioned causal generator must preserve original PR328 perturb overlap and q-locus ATAC exclusion. Controller-only donor×source×split estimability, authenticated TRAIN-only real reference/Task3 operator binding and prospectively frozen *joint* finite realism PASS/NOT_ESTIMABLE gates remain absent. No real or synthetic dataset was generated in this review; no biological outcome, controller truth, optimizer, backward, EMA, M1/M2, Stage4 or production promotion.

**Disposition:** `EVENT120_TWO_BRANCH_CUSTODY_VERIFIED__V2_C3_PENDING__WORKFLOW_COMPOSITION_REPAIR_REQUIRED__NO_TRAINING`.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
