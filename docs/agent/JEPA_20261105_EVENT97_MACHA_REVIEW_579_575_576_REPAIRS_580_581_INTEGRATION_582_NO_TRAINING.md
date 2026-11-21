# Event97 — Macha review of #579/#575/#576, repairs #580/#581, integration #582, Event96 source check (NO TRAINING)

**Date:** 2026-11-05 (US Eastern).

**Author:** Macha (independent reviewer and repair engineer).

**Scope:** synthetic only, using fake opaque bytes and tiny fake CPU tensors with manually set Adam slots. None of these occurred: forward or backward pass, optimizer step, EMA update, RT1–RT8, GPU, RNA, sealed controller or merge.

**Branches:** append-only on #322, mirrored byte-identically on #460. Events 1–96 are unchanged.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Scoped verdicts (Macha)

| Item | Exact head | Verdict | Basis |
|---|---|---|---|
| Sol #579 (reconcile guard, damaged new head) | `676c991f9ca2a4b6b2424d1da070b73b1fb46c01` | **REPAIR_REQUIRED → repaired in draft #580** | Sol's two fixes are confirmed correct. Two further gaps were inherited from Macha #577: (1) a sibling thread of the opening process could recover a live attempt; (2) reconcile mirrored a completed run's RUN_CLOSED over damaged history as "verified". |
| Sol #575 (structured CPU preflight) | `41e7c556e61e313253b7e839e948328b47ab88dc` | **REPAIR_REQUIRED → repaired in draft #581**; otherwise ACCEPT_SCOPED for its claims | Each bundle was checked only on its own, so a later checkpoint with a reshaped or missing module was accepted as the next probe-pass state of the same run. |
| Sol #576 (forensic own-evidence read) | `227a957c6997dc0e99233b1e4eedff3e9bb0f683` | **ACCEPT_SCOPED** | Under 12 seeded random accident patterns, the reader and the forensic report always agree, and readable states return their exact committed bytes. |
| Macha #578 (teacher mirrors online) | `9cfe01c4fea40100e0f837cf8ece88392efd93db` | Already ACCEPT_SCOPED by Sol (Event94); not re-tested | Its integration is tested in #582. |
| Sol Event96 (V5 runtime source locator) | PR224 `9d00684e` | **ACCEPT_SCOPED (static source identity only)** | All 5 source and test blobs (`59647eb0`, `ab266faa`, `41a6ebde`, `0fd06ae0`, `33d62e1a`) are identical at PR224, PR525 `b493efc3` and PR548 `cde03f73`. `canonical_runtime.py` is absent at all three. `main` has the older `inactive_update_reference.py` `3dc61b62` (with `optimizer.step()`) and lacks the guarded wrapper. The convergence test's `RUNTIME` is `inactive_update_reference.py`. Not executed. |

## Repairs (RED first in hosted CI, then GREEN)

**Draft #580** (base #579). RED `0ecc0d7858bd5e2a9cbb9a9d64c1d26b16c4ccdc`:
- run `42109490027`: 2 failed (`DID NOT RAISE`) and 7 controls passed, on both Python 3.11.9 and 3.12.7.

Repair `63bf1bdc8eea276d144e5f33a5828c137fe3217f`:
- run `42110388184`: 9 + 84 passed plus the read budget;
- Sol's #579 suite (`42110388397`): 57 passed;
- V2 suite (`42110388176`): 248 passed;
- 6/6 workflows, 12/12 jobs.

The repair, in the journal source:
- records the (pid, thread) that began an attempt;
- refuses recovery from another thread while that thread is alive (`ATTEMPT_THREAD_STILL_ALIVE__RECOVERY_REFUSED`);
- refuses `UNMIRRORED_COMPLETION_HAS_DAMAGED_HISTORY`.

The 7 controls, passing at #579 and after:
- real torch DataLoader workers, fork and spawn;
- multiprocessing pools with fork, spawn and forkserver;
- a dead attempt thread;
- a dead opener with a lingering forked loader (refused until the loader exits, then recovered).

**Draft #581** (base #575). RED `2af9f8d3a1311fc6da9ecd7551b122b89258e162`:
- run `42109496747`: 2 failed (reshaped, dropped) and 56 passed, on both Pythons.

Repair `86d96fc1450038c1482d4cfd8389682d0f085d62`:
- run `42110395980`: 58 passed;
- Sol's #575 workflow (`42110395951`): 55 + 57 passed;
- 4/4 jobs.

It binds u0's tensor names, shapes and dtypes plus the optimizer group layout, and refuses `MODEL_OR_OPTIMIZER_STRUCTURE_CHANGED_SINCE_U0` before any write.

## Integration (draft #582)

**Heads:** `e71d864b0496de0b86fe7442ba51d53b44e0b225` (merge commit `265c9e59d2b4a9ea438ef9af0dd467bf558f198f`).

**Merged:** #576 (contains #575) + #580 (contains #579 and #577) + #581 + #578.

**Conflict:** exactly one add/add, on `scripts/v5/jepa_v5_full_state_readonly_audit_v1.py`. #575 carries #571's `fea60030`; it was resolved to #578's `ae79cd1b`. No original test was modified.

**New cross-component tests** (`tests/test_jepa_v5_journal_integration_macha_v1.py`, 19):
- forensic reads of structured states;
- first collapse over damaged structured history;
- seeded reader-vs-report agreement;
- incomplete teacher refused through the bridge;
- a crash before the commit record never becomes a success;
- sibling-thread and forked-DataLoader ownership;
- the structured read budget.

**Hosted** run `42110895354`: 19 integration + 387 passed / 9 skipped, plus the read budget, on both Pythons; 10/10 workflows, 20/20 jobs.

**Local** WSL2 Python 3.11.15: 406 passed / 9 skipped.

**I/O on the combined tree** (local):

| Run | Checkpoint reads | Writer time | Other |
|---|---|---|---|
| 1 KiB × 40 updates | 73 = budget | — | — |
| 23 MiB × 33 updates | 66 = budget | 6.2 s | u32 scrub 0.62 s; RSS 134.5 MiB |

No regression from Event93.

## Not tested

- Real model measurements.
- Physical gradient origin, real Adam moments or EMA arithmetic.
- Frozen-panel CELL and gene-token probes.
- Complete Python/NumPy/CUDA/masking RNG, data cursor or AMP state.
- Restore and RT1–RT8.
- Windows-native execution and exFAT.
- A writer that hands its step to another thread while the beginning thread itself calls recovery.

Caller-reported probes, fabricated Adam moments and successful hashing are **not** evidence of healthy biological representations.

## Next slice (no execution without owner authority)

- Sol cross-reviews #580, #581 and #582.
- Then bind the source-pinned guarded one-update wrapper (PR224 `inactive_guarded_update_v1.py`) to the integrated journal as a non-executing contract. That means: BEGIN before the guarded update; structured bytes and probe after it; gradient, Adam and EMA telemetry from #571.
- Any actual optimizer step or RT1–RT8 needs separate owner authorization.
- The V80 backup is resolved (Event95) and is not an open task.
