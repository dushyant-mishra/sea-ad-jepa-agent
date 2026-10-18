# Macha focused re-check — Unified Task 4 T4-B1…B5 at `64535753` (PR #427)

Date: 2026-10-17.

Role: independent hostile reviewer of controller work. Non-controlling.

All probes are synthetic DEVELOPMENT fixtures. No probe mutates a module-private registry or monkeypatches a module global; every attack only passes ordinary Python values to the public functions. No protected, biological or real bytes were opened.

## Verdict

`REJECT_TASK4_CUSTODY_CANDIDATE` for `64535753acfab0993165b5666797808f20cd8743`.

**Closed:**
- T4-B2: FINAL with a harness subclass.
- T4-B3: identity re-creation; the lease also survives abandonment, and the two-thread double-spend has exactly one winner.
- T4-B4: all 8 CI workflows green on this SHA.
- T4-B5: Windows fsync, verified on real Windows.
- The five original subclass/reset attacks (A1–A5) and the duck-typed sealed set are refused.

**Still open: T4-B1.** The exact-type checks cover only the *outer* object. Forged values nested inside exact-type objects, or passed as ordinary arguments, get through. Exactly as before:
- custody completes on a fabricated record, this time with the frozen exam shrunk from 2 worlds to 1;
- an output is frozen for a world that was never exposed;
- uncommitted hidden material is revealed;
- an exposure is recorded under one world's name while carrying another world's content;
- the actor-independence check at creation is bypassed.

**Part of this is my fault.** My `36e3b46f` repair text offered exact types plus base-class method calls as the *smallest* repair, and holding the lawful state in the registry only as the *better* option. These probes show the smallest repair is insufficient. I should also have listed the nested-value side doors. They are listed in full below, so that one round can close them all.

## Head and evidence

| item | value |
|---|---|
| reviewed | `64535753…` (PR #427 head = PR #426 head), base: frozen Task 3 `117dd51d` |
| delta from `36e3b46f` | 20 human-authored commits. Changes: `challenge_custody_v1.py`, `task4_custody_store_v1.py`, Task 3 test `conftest.py` (now also resets the Task 4 lease between tests), and the three inherited workflows (pinned `numpy==1.26.4`). No Task 0–3 *production* file changed. |
| CI (confirmed on `64535753`) | Task 0 migration `39091542287`, Task 0 B1–B5 `39091542283`, Task 1 `39091542281`, Task 2 `39091542253`, Task 3 registry `39091542280`, **Task 3 B6 `39091542274`**, Task 4 `39091542252`, synthetic `39091542289`: all success |
| Windows (local, not CI; Python 3.9) | full `tests/v5/td_unified`: 324 passed, 3 skipped; store/replay/external-root/fsync suites: 17 passed, 2 skipped; 100k replay benchmark: 1 passed. Skips: two POSIX-only fsync-harness tests and the 100k test, which was run separately. The 16 earlier Windows failures now pass. |
| probe | `docs/agent/macha_task4_review_evidence_36e3b46f/task4_recheck_probe.py` and its `.log`: 17 checks, **12 expected, 5 BAD** |

## Closed

| item | evidence |
|---|---|
| A1 subclass campaign | refused: "campaign must be a QualificationCampaign" |
| A2 / T4-B2 | `ShadowHarness` refused; the genuine harness still refuses FINAL |
| A3 subclass exposure | refused |
| A4 subclass definition | refused: "exact sealed challenge definition required" |
| duck-typed sealed set | refused: "exact sealed realization set required" |
| A5 / T4-B3 | identity re-creation refused ("already claimed in this process"), including after the first object is abandoned. Two threads exposing from the same campaign version: exactly one wins. |
| T4-B4 | all 8 workflows green, B6 included |
| T4-B5 | fsync through writable handles; directory fsync after `os.replace` on POSIX; Windows suite green locally |

## T4-B1R — CRITICAL: forged values nested inside exact-type objects

The outer `type(x) is …` checks pass in every case below. The forgery sits in a value the code never type-checks.

**N6. Finite exam shrunk, custody complete.**
- An exact `QualificationCampaign` carries the lawful token, but its `dependencies` is a `dict` subclass that overrides only `__getitem__` to return budget 1. Because the subclass leaves `__iter__` alone, `dict()` uses CPython's fast path and copies the stored values, so `to_payload` and the digest are unchanged.
- The module's `campaign.dependencies["qualification_budget"]` reads, however, return 1.
- The DEVELOPMENT chain then generates one row, seals budget 1, exposes one world, reveals, regenerates and finalizes, ending at **`CUSTODY_COMPLETE`**.
- The campaign identity froze budget 2; only 1 world was ever sealed or exposed.

**N3. Output frozen for an unexposed world, then revealed.**
- An exact `ExposureRecord` carries r0's issued fields, but its `realization_id` is `EqAnyStr("r1")`: a `str` subclass whose `__eq__` always returns `True`, keeping `str.__hash__`.
- Tuple membership, dict keys and set equality all accept it.
- An output is frozen for r1, which was never exposed, and the hidden material is then revealed (`exposed=['r0']`, frozen r0 and r1).

**N4. Uncommitted hidden material revealed.**
- An exact `SealedChallengeDefinition` carries `hidden_spec_commitment=EqAnyStr(committed)`. Its JSON identity is unchanged.
- The check `digest != definition.hidden_spec_commitment` goes to the subclass's reflected `__ne__`, which returns `False`.
- A different hidden spec is accepted at reveal.

**N7. Exposure named for one world, carrying another world's content.**
- `issue_exposure(realization_id=EqAnyStr("r1"))` passes the membership checks.
- `sealed.realization_ids.index(...)` matches r0 first, so the record says r1 but carries r0's content.

**N8. Actor independence bypassed at creation.**
- `validate_campaign_dependencies` validates values read through `dependencies[...]`, which a subclass can override, then stores `dict(dependencies)`, which copies the stored values.
- A `dict` subclass shows a distinct controller during validation while storing `controller == producer`.
- The campaign is created. Control: a plain dict with `controller == producer` is refused.

**Why this matters.** These are the same failures as A1, A3 and A4, reached one level deeper. They break the custody claims that the exam is a frozen finite budget, that a world is exposed before its output is frozen, that reveal must match the commitment, and that actors are independent.

**Repair that closes the class.** Every route above must be closed.

1. **Handle identity, not value inspection.** For each lifecycle token, the module keeps the exact objects it issued: the latest campaign, the definition, the sealed set, and each issued `ExposureRecord`. Every entry point requires `obj is registered_obj`, for example `_LIFECYCLE_OBJECTS[token] is campaign`. The caller cannot substitute a value at any depth, because every value used is one the module produced.
2. **Exact built-in arguments.** Caller-supplied arguments must be exact built-ins:
   - `realization_id`: `type is str`, checked against the sealed ids with `str.__eq__`, or better by exact-string set membership after normalisation;
   - `terminal_status` and `family`: `type is str`;
   - `budget`: `type is int`;
   - `hidden_spec`: `type is bytes` (already checked).
3. **Normalise, then validate.** `validate_campaign_dependencies` must normalise first, then validate, then store that same normalised copy:
   - require `type(dependencies) is dict`, or build `{str_key: value}` using `dict.items` on a copy;
   - recursively require exact `str`, `int`, `tuple` and `list` types for every value, including the unit-identity pairs;
   - run the independence checks on the normalised copy.
4. **RED tests.** Add N3, N4, N6, N7 and N8 as failing tests, then a regression of A1–A5.

## Non-blocking

- `require_task4_preauthority_barrier_green` still uses `isinstance(status, Task4BarrierStatus)`. FINAL now builds its status internally, so this is not exploitable through `_guard_final`. Make it exact anyway.
- When `events.jsonl` is first created, the parent directory is not fsynced on POSIX.
- The claim "frozen Tasks 0–3 unchanged" holds for production code. A Task 3 test file (`conftest.py`) and three Task 0/3 workflows changed, which is acceptable infrastructure, but the claim should say *production*.
- Carried forward: C1(b) and R4 must be in place before FINAL or `KNOWN_TRUTH_QUALIFIED` can be reached; requirement-policy roles come from a caller mapping (C5/R7); the store is never authoritative.

## Freeze decision

Task 4 may not be frozen at `64535753`. Next focused re-check: T4-B1R (N3, N4, N6, N7, N8), plus a regression of A1–A5, the lease and concurrency. B2–B5 stay accepted.

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
