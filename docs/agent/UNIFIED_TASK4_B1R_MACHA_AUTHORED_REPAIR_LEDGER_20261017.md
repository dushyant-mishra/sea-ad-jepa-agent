# Unified Task 4 T4-B1R repair — Macha-authored, independent audit required

Status: `CANDIDATE_ONLY__AUTHORED_BY_MACHA__INDEPENDENT_AUDIT_REQUIRED`

**Role change.** Macha (Claude) wrote this repair at the owner's request. Macha is therefore its author and **cannot** independently review or accept it (`SAME_AGENT_SEPARATE_PASS != INDEPENDENT_REVIEW`). Acceptance requires an independent auditor.

## Lineage

| item | value |
|---|---|
| base | `64535753acfab0993165b5666797808f20cd8743`, rejected by Macha (`REJECT_TASK4_CUSTODY_CANDIDATE`); review on `review/macha-task0-independent-review-20261014` @ `fd201f6c` |
| RED | `d180d508`: `tests/v5/td_unified/test_task4_macha_b1r_nested_red.py`. Against `64535753`: **7 failed**, 1 passed (the lawful control). Run locally. |
| GREEN | `d8a3171c`: `challenge_custody_v1.py`, `task4_authority_barrier_v1.py`, `task4_custody_store_v1.py` |
| frozen Task 0–3 | no Task 0–3 file is touched by these commits |

## What changed

1. **Handle identity.**
   - Per lifecycle token, the module records the exact campaign (`_LIFECYCLE_OBJECTS`), definition (`_ISSUED_DEFINITIONS`), sealed set (`_ISSUED_REALIZATION_SETS`) and exposure records (`_ISSUED_EXPOSURES`) that it issued.
   - Every entry point accepts only those objects (`is`). Value-equal copies, subclasses, and exact-type objects that carry forged nested values are refused.
   - The payload digest check is kept. It still detects in-place mutation of the issued campaign's dependency dict.
2. **Exact built-in arguments.** `realization_id`, `terminal_status`, `namespace`, `budget`, `hidden_spec` and each realization row (`dict`) must be exact built-in types.
3. **Dependencies.** Campaign dependencies must be an exact `dict`. One `dict.items()` snapshot is validated and stored, so validation and storage cannot see different values.
4. **Minor fixes.**
   - `require_task4_preauthority_barrier_green` now checks the exact type of `Task4BarrierStatus`.
   - On POSIX, the custody store fsyncs the parent directory when it first creates `events.jsonl`.

## Attacks now refused

| attack | expected and observed |
|---|---|
| N3: exact `ExposureRecord` with an eq-anything `realization_id` freezes an unexposed world | refused (not the issued exposure handle) |
| N4: exact `SealedChallengeDefinition` with a ne-nothing commitment reveals an uncommitted spec | refused (not the issued definition handle) |
| N6: `dict`-subclass dependencies shrink the finite exam from 2 to 1 | refused (not the current issued campaign handle) |
| N7: an eq-anything `realization_id` argument misbinds exposure content | refused (`realization_id` must be exact `str`) |
| N8: dependency validation and storage see different values | refused (dependencies must be an exact `dict`) |
| N9: an eq-anything `terminal_status` rewrites terminal accounting | refused |
| value-equal copy of an issued sealed set | refused |
| lawful chain → `CUSTODY_COMPLETE` | passes |

## Evidence (local, Windows, Python 3.9.7 — not CI)

| check | result |
|---|---|
| full `tests/v5/td_unified` | 332 passed, 3 skipped (two POSIX-only fsync harness tests; the 100k test is run separately) |
| projected 100k replay | 1 passed |
| Macha re-check probe (`docs/agent/macha_task4_review_evidence_36e3b46f/task4_recheck_probe.py`) | 17/17 expected |
| Macha original probe (`task4_probe1.py`) | 14/14 expected (A1–A5, FINAL, lease, concurrency) |

CI evidence is produced by the PR checks on the pushed head.

## What the independent auditor should attack

- Any remaining entry point that reads a caller-supplied object or value without handle identity or an exact built-in type.
- Thread interleavings around the post-advance registration of the definition, sealed set and exposure. These are designed to fail closed if another thread uses the advanced campaign before registration.
- In-place mutation of issued objects: `object.__setattr__` on frozen dataclasses is in-process tampering (C9), while the dict digest is a defence-in-depth check.
- Regression of A1–A5, the lease, concurrency, FINAL fail-closed and B4/B5.

## Unchanged

- DEVELOPMENT-only and non-authorizing.
- FINAL is still fail-closed; C5–C9 are hard `FAIL`.
- Process-local only. R4 and C1(b) remain open before any FINAL or `KNOWN_TRUTH_QUALIFIED` stage.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
