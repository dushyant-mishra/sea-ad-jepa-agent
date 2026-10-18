# JEPA current custody V7 — Macha Task4 rejection and recheck

Current state: **Task4 remains unaccepted**. Macha's review head `d4d9ef94` rejected `36e3b46f1ca44465864a11872b459b5d108d6a67` for T4-B1–B5. PR #425 successor-6 `211375de...` repaired duplicate identity/race, but inherited Macha B1/B2/B4/B5 remained open. Do not use older V6 current-state wording as active authority.

**Active immutable candidate:** PR #427 at `64535753acfab0993165b5666797808f20cd8743`. Repair PR #426 is separate. Machine snapshot: `results/target_discovery/unified_qualification_v1/JEPA_LANE_AUDIT_SNAPSHOT_V7_20261017.json`.

- RED-first PR #426 Macha B1/B2 subclass tests: `39091118650`, job `117567897946`, four expected failures.
- Windows read-only fsync simulation RED: `39091241599`, job `117568264331`, one expected failure.
- Repair: module-class-bound digest and exposure identity checks, exact campaign/sealed/authority harness types, fixed FINAL verifier dispatch; inherited B3 locks/leases retained.
- CI-only B4: add pinned NumPy in three inherited failing workflows (no frozen Task0–3 production changes).
- B5: writable file fsync and POSIX parent directory fsync on renamed head; real Windows verification **still absent**.
- Pinned head CI: Task4 `39091466138`; Task0 migration `39091466284`; Task0 B1-B5 `39091466186`; Task3 B6 `39091466136`; Task1 `39091466221`; Task2 `39091466143`; Task3 registry `39091466195`; synthetic integration `39091466139` — all PASS. Prior exact code/test head `fba24066...` had 135 focused / 326 unified passes and projected 100k replay PASS.

**Next lawful step:** Macha repeats A1–A5 and sibling attacks on the exact PR #427 SHA, plus actual Windows custody tests, and issues a new exact-SHA ACCEPT or REJECT. No fallback to CI-only acceptance. Cross-process external trust remains unwired and FINAL fail-closed.

History: PR #322 V4–V6 and PR #323 V4–V6 remain preserved; Task0–3 frozen; local binaries remain hash-custodied, not Git-duplicated.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
