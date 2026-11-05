# Macha repair of the V2 attempt journal (#570): fake bytes only, NO TRAINING

Stacked on #570 `0e2deffa`. It changes only `scripts/v5/jepa_synth2048_attempt_journal_v2.py`, the V2 test helpers, and the V2 workflow test list. The #568/#569 sources and all original Macha RED files (#557 `bfa53457`, #560 `3ab6c208`, #561 `be259ab4`, #566 `60a16378`, #567 `c513693f`) are byte-identical.

## Defects repaired (each has a RED test that fails at #570)

| # | Defect at #570 | Consequence | Repair |
|---|---|---|---|
| 1 | Forensic read stops at the first damaged file, including a damaged *payload* | One bit flip in an old checkpoint hides every later record: the last good state and the collapse record disappear | The hash-linked record is kept in two places, so payload, telemetry or quarantine damage marks only that record's evidence. The chain stops only where neither record copy is intact. |
| 2 | One lost or corrupt *local* record truncates the forensic chain, even though its outside copy is intact | Accidental `rm` of one record hides later collapse evidence | The forensic read uses whichever copy is intact, flags it `ONLY_ONE_INTACT_RECORD_COPY`, and stops on divergent valid copies |
| 3 | `commit_reported_update` writes `NOT_COLLAPSED_ONLY` itself; no measurement is required | Any commit is labelled probe-passed without a probe | A commit needs a caller-reported probe bound to the update, state SHA and run panel: three exact-collapse metrics, the CELL distinct-row witness and a nonfinite count. A probe showing exact collapse, nonfinite values or inexact CELL arithmetic is refused before any byte is written. |
| 4 | u0 is never probed, yet it is reported as the last probe pass | Wrong last healthy state when the first update collapses | RUN_OPEN requires the u0 probe. Its metrics become the run's u0 references. |
| 5 | Collapse evidence on any panel, with any `u0_reference > 0`, is accepted | A collapse claim is not comparable with the run | Collapse must cite the run panel and the run's own u0 value |
| 6 | Crash between link and unlink leaves `nlink=2`; reconcile and recovery refuse forever | A durable collapse record or state is stranded | Recovery removes only temp names that are hard-link twins, or byte prefixes, of retained bytes |
| 7 | A crash after the collapse files were durable becomes `ATTEMPT_ABORTED` | The typed collapse verdict is lost from the run status | Recovery completes a fully durable STATE_COLLAPSED, ATTEMPT_FAILED or RUNTIME_ABORT. A crashed COMMIT is never completed. The cause is written before the state. |
| 8 | A crash during the outside copy leaves a partial temp; the run can never be closed | The run cannot be closed or recovered | Covered by repair 6 |
| 9 | A crash during recovery collides with its own quarantine | Recovery is stranded and the collapse cause is hidden | Conflict-safe quarantine names. The abort records `uncommitted_typed_verdicts` derived from the quarantined bytes. |
| 10 | Any fresh process can continue a run after a crash | Silent resume without a verified restart (RT1–RT8 not run) | A process-lifetime writer capability. Only its SHA is stored in RUN_OPEN. Recovery and close need no capability. |
| 11 | No verified reader for the collapsed onset state | The onset state is kept but cannot be read back verified | `read_forensic_collapsed_state` (never resumable) |
| 12 (self-audit) | Erasing both copies of the collapse and close records also hides the durable cause file | The first evidence of collapse is invisible | The forensic report parses orphan typed causes into `uncommitted_collapse_evidence_updates` |
| 13 (self-audit) | One lost or corrupt copy of `run.lock.json` makes the forensic read refuse the whole run | Every checkpoint and the collapse become unreadable | The forensic read uses the intact run-lock copy. Every record re-checks its SHA. |

## Still not done

- No physical probe. Every value is caller-reported.
- No signed or independent external head (owner decision D1).
- No RT1–RT8 restart tests.
- The #569 collapse receipt does not yet carry the distinct-row witness.
- Every append re-hashes every stored state. That is O(n²) I/O, about 1 TB of hashing for 205 × 23 MiB.
- Pathological recoveries with thousands of stray files, or an empty non-temp orphan, still refuse.
- `fcntl` makes the module POSIX-only.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
