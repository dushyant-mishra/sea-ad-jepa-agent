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
4. **Minor fix.** `require_task4_preauthority_barrier_green` now checks the exact type of `Task4BarrierStatus`.

**Reverted.** A POSIX parent-directory fsync at `events.jsonl` creation was reverted in `399c4a6a` (see below). The B5 harness `test_new_store_fsync_does_not_use_readonly_fd` simulates Windows by rejecting *every* read-only descriptor, and POSIX directories can only be opened read-only. That failed CI run `39093821991`. The test is skipped on Windows, so the local run missed it. Creation-time directory durability stays a non-blocking open item. It needs a harness that exempts directory descriptors, decided by the owning lane.

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

## Round 2: after the independent rejection of `11ef009c` (PR #429)

**My first round was wrong on one point.** In that round's audit list I filed in-place mutation of issued objects as C9 in-process tampering. The independent auditor showed it is an ordinary caller action against an object the module hands out. In PR #429 (`c8e3aa07`, run `39094331098`), mutating an authentic `ExposureRecord` with `object.__setattr__` was enough to freeze an output for a world that was never exposed. The finding is correct and has been repaired.

| commit | content |
|---|---|
| `c8e3aa07` | independent PR #429 RED, fast-forwarded in unchanged |
| `b2eb9406` | sibling-route RED: definition, sealed set, campaign terminal accounting, an eq-anything value swapped into the campaign (JSON-identical), and an in-place edit of dependencies. Against `11ef009c`: PR #429, the definition route and the eq-anything campaign route are accepted; the other three are already refused and are kept as regression guards. |
| `efd77956` | **private snapshots** |

**What `efd77956` does.**
- For each issued campaign, definition, sealed set and exposure, the module keeps the public handle it returned and a separate private copy that it never returns.
- Every transition reads private state only. Terminal accounting lives in that private state.
- A handle is accepted only if it is the exact object issued **and** every field still equals the private copy under exact built-in types at every depth. `_exact_equal` never calls an overridable `__eq__`.
- So the following are all refused:
  - value-equal copies;
  - subclasses;
  - forged nested values;
  - `object.__setattr__` mutation;
  - in-place edits of a mutable dict;
  - look-alike `str`/`int` subclasses.

**Round 2 evidence (local, Windows, Python 3.9.7 — not CI).**

| check | result |
|---|---|
| PR #429 RED + sibling REDs + T4-B1R REDs | 15 passed |
| full `tests/v5/td_unified` | 339 passed, 3 skipped |
| projected 100k replay | 1 passed |
| re-check probe / original probe | 17/17 and 14/14 expected |
| author self-check (`task4_mutation_probe.py`) | 5/5. Refuses plain-value mutation, a lifecycle-token swap, a namespace flip and a stale handle; confirms no private object or private dependency dict is ever returned. |

CI on the pushed head is the confirming evidence. This is an author's self-check, **not** an independent review.

## What the independent auditor should attack

- Any entry point that still reads caller-held state instead of the private copy.
- Any route by which a private copy, or a mutable value inside one, reaches a caller. Private objects share immutable `str`, `int` and `tuple` values with their public handles; each public campaign gets its own dependency dict.
- The window between an advance and the registration of a definition, sealed set or exposure (designed to fail closed).
- Regression of A1–A5, N3–N9, the lease, concurrency, FINAL fail-closed and B4/B5.

## Unchanged

- DEVELOPMENT-only and non-authorizing.
- FINAL is still fail-closed; C5–C9 are hard `FAIL`.
- Process-local only. R4 and C1(b) remain open before any FINAL or `KNOWN_TRUTH_QUALIFIED` stage.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
