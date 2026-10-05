# JEPA REPOSITORY AUTHORITY / CLEANUP AUDIT — 2026-10-05

Scope: GitHub authority surface, target lineage, current-looking governance files, selected high-risk PR claims, custody lineage, and cleanup policy.

## Executive verdict

The repository's largest present risk is authority ambiguity, not loss of scientific evidence. Historical branches/PRs often correctly describe their own scope, but many old handoff/governance artifacts remained active-looking long after newer authority existed.

The cleanup policy is therefore conservative:

1. keep `main` as the canonical startup/navigation surface;
2. preserve historical result, audit, custody and evidence branches;
3. close superseded handoff/navigation PRs with explicit preservation notices;
4. add corrective notices to live PRs containing retracted or superseded claims;
5. never treat closure as scientific refutation unless the record explicitly says so;
6. do not delete branches without separate ancestry + unique-evidence review.

## Current scientific boundary

- V75 100K measurement architecture remains qualified within its declared scope.
- 500K promotion is not authorized.
- No production target winner is qualified.
- The synthetic learned-state scaling ladder is stopped.
- Training and multimodal training remain OFF.
- Stage 4 remains not authorized.
- `width=160` is architecture capacity, not biological dimensional authority.
- `cell_state` is implemented but is not qualified as the designated global biological state.

## Main cleanup completed

PR #212 merged the current authority/navigation surface to `main` at `ab6685019783810db3b1f129f1d72ac2881b223d`.

That update replaced stale V25/V21/V20-era startup files, corrected the README, added the Oct-5 target-authority reset handoff/state/audit, and added a fail-closed authority-surface CI guard.

The PR touched only governance/navigation/guard files; no model/runtime/scientific-result paths were changed.

## Important target-lineage result

The current terminal unresolved question is not the old August donor-centering proposal. V6R5B later executed strict donor-cross-fitted residual targeting and returned `RESIDUAL_TARGET_DOES_NOT_RESCUE`.

Later work still did not produce a qualified target winner. PR #163 defined competing value-blind constructions but selected none; PR #178's corrected synthetic comparison was `NOT_INFORMATIVE` and required real RNA.

The unresolved scientific question remains: which lawful real-TRAIN target construction retains biological information while adding material conditional information beyond gene/address identity, with zero encoder/EMA updates during qualification?

## High-risk stale claims already corrected

- PR #147 received a corrective notice: its NumPy/BLAS S9 diagnosis was retracted later by PR #178.
- PR #207 received a supersession notice: V75 100K measurement authority stands, but its learned-160D next-action sentence does not.
- PR #31 / PR #148 were also flagged for stale environment wording during cleanup.

## PR closure policy

PRs are classified before closure as one of:

- `CURRENT`
- `SUPERSEDED__NAVIGATION`
- `HISTORICAL_EVIDENCE`
- `CUSTODY_ONLY`
- `INCOMPLETE_STOPPED`
- `DEFERRED`

Closing a `SUPERSEDED__NAVIGATION` or `CUSTODY_ONLY` PR does not delete the branch or invalidate the evidence it preserves.

Substantive science, ETL, audit, review, or experiment PRs remain open until individually adjudicated.

## Cleanup actions completed so far

Superseded handoff/navigation/custody PRs closed with preservation notices include:

`#16, #34, #37, #40, #53, #68, #123, #148, #150, #159, #167, #174, #183, #184, #186, #190, #197, #208, #210, #211`.

This list is a repository-hygiene record, not a scientific verdict list.

## What remains

1. continue open-PR classification, prioritizing docs-only handoff/governance lanes;
2. preserve substantive experiment/data/audit PRs unless a successor clearly closes their active role;
3. identify branches that are exact duplicates before any branch deletion is considered;
4. keep retraction/supersession notices on historical PRs whose bodies can still mislead readers;
5. keep the authority-surface guard green on future main changes.
