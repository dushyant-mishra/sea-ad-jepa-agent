# JEPA successor handoff V6 — exact Task 4 review gate

**Start at PR #425**, candidate `211375de57cc1f70d46c6eb3a4860d61a1aba0a6`, rather than restarting the history. Candidate mechanically GREEN; **not accepted**. For full history, use PR #322 V6 then earlier V5/V4 indexes, not an unbounded repository audit.

Frozen Tasks 0–3: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`, `799d2e235901dfad9ce3b305c767a1c989e362f6`, `c7dfff1cee608e4a101855d42cf0af08491c2aaf`, `117dd51dea827e734b299982da93991b934bdc8f` (Macha accepted Task 3). Production frozen code has not changed.

**New hostile findings since V5:**
1. PR #422 RED `39084356745`: using the same campaign ID, dependencies and genesis ledger twice could remint zero-spend exam state. This rejected successor-5 (PR #421, `36e3b46f...`).
2. PR #424 RED `39084723524`: two threads could both issue ordinal-1 exposure for the same realization. Both GREEN predecessor claims remain negative evidence, not acceptance.

Repair PR #423 ported both REDs before production changes, added an atomic campaign identity lease and serialized lifecycle check/update for DEVELOPMENT mechanics, plus hostile sibling tests and synthetic test-process isolation. PR #425 exact candidate `211375de57cc1f70d46c6eb3a4860d61a1aba0a6`: Task4 run `39084913154`, job `117549328489`: **129 passed, 1 skipped** focused; **1 passed** projected100k replay; **320 passed, 1 skipped** full unified. Task2 `39084913157`, Task3 `39084913175`, synthetic integration `39084913173` PASS. Older inherited environment failures are separate.

**Next action:** independent hostile review on another branch, exact SHA only. Test process restart/multi-process duplication, concurrent calls, state/receipt replay, generator substitutions, sealing/reveal ordering, C1–C9, and legacy registry routes. Return an explicit exact-head `ACCEPT_TASK4_CUSTODY_CANDIDATE` or `REJECT_TASK4_CUSTODY_CANDIDATE`. If RED, preserve it before a new narrow successor repair. If accepted, freeze only stated non-authorizing mechanics.

**Boundary:** Process-local DEVELOPMENT identity leases and locks do **not** prove durable cross-process or independently authenticated execution. FINAL remains fail-closed. No target, representation, Stage4 or real training authority.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
