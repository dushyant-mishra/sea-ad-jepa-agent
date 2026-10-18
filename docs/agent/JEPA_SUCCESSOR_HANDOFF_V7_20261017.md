# JEPA successor handoff V7 — independent Macha Task4 recheck

**Current working gate:** Task4 remains **NOT ACCEPTED**, despite eight exact-head CI checks passing.

Read PR #322 V7 machine/human custody before any changes. Frozen Tasks 0–3 remain unchanged. Macha rejected prior Task4 `36e3b46f...` (review `d4d9ef94`) for B1–B5; PR #425 successor6 `211375de...` only repaired duplicate campaign remint and concurrent double-spend.

Current exact candidate: **PR #427, `64535753acfab0993165b5666797808f20cd8743`**. Repair code and RED tests are on **PR #426**. Read `docs/agent/UNIFIED_TASK4_MACHA_B1_B5_REPAIR_RECHECK_V1_20261017.md` and matching JSON on PR #427.

Prospective repairs on PR #426:
- B1/B2: hostile RED `39091118650` found four subclass/overridable-method authority bypasses; repaired by exact types, module-controlled fingerprints and class-bound real FINAL checks.
- B3: retained successor6 in-process lease and atomic transition; never assert cross-process authority.
- B4: all three prior red safety workflows now green after pinned NumPy dependency addition.
- B5: hostile simulated Windows EBADF RED `39091241599`; writable fsync + POSIX directory rename sync repaired. **Actual Windows recheck not yet performed.**

Exact PR427 head `64535753...` has eight CI PASS, including Task4 `39091466138` and Task0 migration/B1-B5/Task3 B6. Earlier code/test `fba24066...` verified 135 focused and 326 unified tests passing plus 100k replay.

**Next action:** Macha re-runs A1–A5 and 14-check probe, PR417 and PR419 controls, exact-type/authority/no-world-exposed attacks, the three CI workflows and the 16 local Windows custody tests. Only explicit `ACCEPT_TASK4_CUSTODY_CANDIDATE` or `REJECT_TASK4_CUSTODY_CANDIDATE` pinned to `64535753...` can resolve the gate.

Do not redesign biology, reopen frozen Task0–3 or authorize real training. Keep the full Task4 hostile rejection lineage. Older V4–V6 handoffs are historical records.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
