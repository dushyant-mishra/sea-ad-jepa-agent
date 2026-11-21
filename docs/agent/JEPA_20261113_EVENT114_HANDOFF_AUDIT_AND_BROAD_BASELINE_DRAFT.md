# Event114 — Two-branch audit and broad baseline draft (2026-11-13)

## Required handoff and maintenance

- Start at [active handoff #460](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/460)'s first-read pointer. Use [canonical audit #322](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/322) for append-only chronology and the no-repeat source index. Both PRs and their distinct roles must be included in every handoff.
- Read Event113 and its machine map, follow Events112–108 as needed, and use Event90 for the original science/script/data/result crosswalk. For any lane, read the exact source pins, distinguish prior and superseding verdicts, and do not reopen completed work without a named delta.
- During implementation, use separate scoped drafts. For each material result, record exact source and implementation heads, changed code/data and hashes, scoped test evidence (including failures), independent review state, residual blockers and authority. Append only on #322; mirror the same review blobs and refresh the first-read on #460. Verify prior entries unchanged, mirror blobs identical and live heads/status after publication. If only one side updates, report the partial state and reconcile before handoff. Keep implementation progress separate from scientific promotion.

## Exact-head verification

- Checked #322 `1e32533aca54264a10f095b49b73f11c2c7b6b1f` and #460 `7d8f97c6cc4e8da5b50338eb7bc543749cd3f0c0` before publication. Removed only the Event113 record and key in memory, then compared to prior #322 `2998f4d401daba73acad93c6483e4a81365543db`: all 112 previous events and 77 keys matched. Event113 handoff, source map and archived OOF/Stage33B patch matched by Git blob on both heads.
- Hosted runs at the **pre-Event114 heads**: #322 26/27; the only failure was V80 original-archive preservation (run 43513334112). #460 4/4, including first-read/source custody (run 43513529099). Those results are not Event114 CI results and do not authorize execution.
- The conversation copy of the Event113 ZIP matched SHA256 `5773e17d6d87f603da2943d0f48e1c0a60e9f89ef0b13b9e6fe609caee771b34`; three script Git blobs and the archived OOF patch matched its source map. The conversation attachment ID can change on re-upload; use content identity.

## New findings and implementation delta

- **Preservation helper:** Event113's broad score was a student-vs-target correlation across type means; it lacked the named cell-type-only comparator. Event114 archives a byte-pinned draft against the Event113 ZIP: `docs/agent/archive/event114_dev2048_review/jepa-event114-broad-type-baseline-draft.patch`. It requires a caller-supplied frozen type-to-prediction mapping, scores it against the same required type means, and exposes student-minus-baseline correlation. It retains a measured zero, and missing baseline coverage yields NOT_ESTIMABLE for the comparison without erasing the student score. Five named inert Preservation tests passed locally: a type-only student can score broad 1.0 with increment 0 and undefined fine score; a missing baseline type blocks comparison. This is a detached draft and does not verify baseline fitting provenance, freeze the evaluation panel, or establish preservation in a trained model.
- **#596 additional source-only bypass:** At `bc9da0547f4e187969f5dc21bc7a188e9a519d8d`, `verify_no_wildcard_pytest_routes` partitions text on literal LF + `jobs:` and `_logical_run_lines` recognizes only line-start `run:` entries. A YAML flow-map step such as `steps: [{run: "python -m pytest -q"}]` never produces a scanner line, even when its job is under a normal `jobs:` key. No workflow or broad collection was executed to demonstrate this. This is distinct from the shell quoting, traversal and direct config-override cases already recorded in Event113. Repair should enforce the guarded entrypoint for scoped workflows, with inert parsed-YAML cases; not another claim of arbitrary shell safety.
- **M1 helper source-only gap:** `m1_evidence.py` signs code/contract/FIT/U0/batch/premise/run pins but no environment digest. Environment verification must be bound by a trusted launcher before this helper can support an execution gate. The 22,136 half-life is encoded in the review helper; that is not owner approval. Reopen tests in the ZIP mock the subprocess; no real U1 reload is established.

## Next implementation gates

1. Fix and independently review the scoped #596 CI boundary without running broad collection. Keep non-CI #594 review open.
2. On a separate #597 successor draft, enforce trusted disk-derived launcher pins and isolated U0-to-U1 persistence, then exercise actual upstream noninterference with inert fixtures. Freeze and verify evaluation panel and baseline provenance separately. Keep the archived Stage33B patch independent; migrate its consumers before changing the shared API.
3. No M1 or M2 without separate authorization. No real training, model update, merge, restricted data, V80 substitute, target or representation winner, or Stage4 authorization.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
