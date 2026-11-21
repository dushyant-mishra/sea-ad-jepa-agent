# Event111 (part 1 of 2) — Macha independent verdict on Sol #595; RED→GREEN repair #596 (NO TRAINING)

**Date:** 2026-11-13.

**Author:** Macha.

**Branches:** append-only on #322, mirrored byte-identically on #460. Events 1–110 are unchanged. Part 2, the DEV2048 pilot plan, is a separate document under the same event.

**Execution boundary:** inert temporary fixtures (trivial `def test_x(): pass` files and synthetic workflow text) and mocked subprocesses only. No broad test discovery, D1 dispatch, torch, model, optimizer, backward or EMA.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Verdict

**#595 exact head `37dc2469f05d83a6dcfc38cedc54e4f9325bd10c`** (unchanged since assignment): **REPAIR_REQUIRED (scoped).** Repaired in Macha draft **#596**, which Sol must review independently.

## Sol's changes: verified

| Check | Result |
|---|---|
| push-to-`main` / PR-to-`main` glob routes | refused (branch filters no longer exempt) |
| byte-identical D1 `a0e3fb26` | the only exemption |
| D1 plus one byte | refused |
| D1 bytes renamed | refused |
| inherited `PYTEST_ADDOPTS` / `PYTEST_PLUGINS` | reach the guarded subprocess as `''`; autoload off; argv is the explicit files only (mocked) |

## Remaining gaps

All three are in **Macha's own #594 code**, which #595 kept.

1. **Broad collection without a wildcard.** An automatic push-to-`main` route running `python -m pytest -q`, `pytest .`, `pytest tests/v5`, `--pyargs scripts` or `py.test -q tests` passed the scan, although each collects whole directories.
2. **Hidden config.** `.pytest.ini` and config files in `tests/` were not refused. pytest then ran an unreviewed inert test (2 passed).
3. **Unpinned runner config.** The runner did not pin its config or rootdir. A `pytest.ini` in the checkout's parent became `configfile` and added an unreviewed inert test. This is runner-controlled in hosted CI but real on a local clone.

## Repair in #596

- **Scan:** every pytest invocation in an automatic workflow must name explicit `tests/…py` files. Run steps are parsed per shell command, including YAML folded blocks and continuations; `pip install pytest` is not a test route.
- **Config refusal:** refuse `pytest.ini` / `.pytest.ini` and pytest config sections in the root and `tests/`.
- **Runner:** add `-c <empty reviewed ini> --rootdir <repo>`.

**Hosted evidence (Python 3.11.9 and 3.12.7):**

| Head | Result |
|---|---|
| RED `8c9d38b0` (run 43503537769) | exactly 9 subtests failed per Python |
| GREEN `bc9da054` | 5/5 workflows, 10/10 jobs: runs 43503950237 (static: 6 + 5 + earlier suites OK; inventories 41/33/10; quarantine), 43503950323 (480 passed, 37 skipped), 43503950409 (401 + 19), 43503950184 (84 + 9) |

All 33 real workflows pass the stricter scan.

**Limit:** a pass does not certify that every indirectly called helper is safe, and the scan does not parse scripts invoked from `run:`.
