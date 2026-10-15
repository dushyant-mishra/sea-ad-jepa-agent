# Macha focused re-check — Unified Task 1 T1-B1…B5 (PR #386)

Date: 2026-10-15.

Role: independent hostile reviewer of controller work. Scope: T1-B1…B5 only. Non-controlling.

**Read-only.** Nothing protected was opened.

## Verdict

`ACCEPT_UNIFIED_TASK1_T1_B1_B5_REPAIR`

`TASK1_MAY_BE_FROZEN__UNIFIED_TASK2_MAY_BEGIN_PROSPECTIVELY`

This creates no training, target, representation or Stage 4 authority.

## Head

`799d2e235901dfad9ce3b305c767a1c989e362f6` (PR #386 → `implementation/unified-task1-live-20261015`).

Ancestors: `86fa996f`, `e37a22b8`.

The delta from `86fa996f` is 7 files: the `canonical_v1` and `authority_v1` modules, the authority schema, three test files and the workflow. No frozen Task 0 file is modified or deleted.

## Item verdicts

Probes are `probe3_recheck.py` and `probe4_recheck.py`, with logs, in `docs/agent/macha_task1_review_evidence_86fa996f/`. All 42 hostile probes behaved correctly: zero BAD results.

### T1-B1 — CLOSED

Exact-type dispatch is implemented: `type(v) is bool/int/float/str/dict/list/tuple`, encoded with `float.__repr__`, `int.__str__` and unbound `str.replace`. There is an explicit numpy policy:
- `np.bool_` → bool;
- numpy integers → `int`;
- numpy floats ≤ 8 bytes → widened to float64;
- wider floats, datetime/timedelta, `str_`, complex, arrays and numpy subclasses → rejected.

Probe results:
- **Subclasses rejected:** float, int, str, dict, list, IntEnum and `np.float64` subclasses all raise `CanonicalError`.
- **`np.float64(1.5)`** now produces `{"x":1.5}`, identical to the plain float.
- **Old Task 1 compatibility, including numpy scalars:** 0 mismatches over 4,000 seeded random objects, compared with `ff597faf` `canonical_json_bytes`.

### T1-B2 — CLOSED

`producer_code_sha` is now the git blob SHA-1 of the exact producer bytes. Those bytes are resolved and the blob identity is recomputed. Refused:
- `"0"*40` (unavailable);
- wrong bytes (identity mismatch);
- `str` instead of `bytes`.

A valid receipt verifies.

### T1-B3 — CLOSED

Each non-receipt dependency must be an exact `dict` with `object_role` equal to its slot (INPUT, OUTPUT, MANIFEST, REGISTRY or ACCESS_POLICY). Refused:
- `{}` alone in the access slot (role mismatch);
- an untagged input;
- `{}` in all four roles, an input reused as output, or a manifest object in the registry slot (cross-role reuse);
- a receipt in the access slot.

Full schema typing of the role objects remains a Task 2/3 obligation.

### T1-B4 — CLOSED

There is a closed grammar, `UNIT:<id>` | `PIPELINE:<id>` | `PROJECT`, applied by `fullmatch` and mirrored exactly by the JSON-schema `pattern`. In addition:
- the scope id must equal `unit_id`;
- `PROJECT` requires `unit_id == "PROJECT"`;
- the scope → stage table is UNIT SEMANTICS_ONLY…HUMAN_EXECUTED, PIPELINE SAME_CODE_PATH…TRAINING_ELIGIBLE, PROJECT TRAINING_AUTHORIZED only;
- restrictions are a separate tuple of uppercase tokens that cannot widen scope.

All the earlier failing scopes are now refused, along with `UNIT:G9` for unit G8, trailing spaces, a trailing newline, lowercase forms, and UNIT at DOWNSTREAM_CERTIFIED or TRAINING_AUTHORIZED. A non-string `unit_id` now raises `AuthorityError`.

### T1-B5 — CLOSED

The module docstring is now a byte-level fingerprint spec: domain, format, receipt identity and producer blob rule. The tests freeze two 64-hex known answers:
- `canonical_sha256({"a":1,"b":[true,null,1.0]}) = 8b441603…30e9`. I reproduced this independently with `hashlib` alone.
- a fixed receipt `receipt_sha256 = 7fd72094…7578`.

Mutating the domain to `…-V2` makes 2 tests fail. The source was restored afterwards and the worktree is clean.

## Tests (local, Windows, `sea-ad-jepa-v3`; local evidence, not CI)

- The three Task 1 files: 27 passed.
- Full `tests/v5/td_unified`: 64 passed. This needed `docs/superpowers/plans` in my sparse checkout; without it, Task 0's B5 presence test correctly reports the file missing, which is an artifact of my checkout and not a code defect.
- Controller CI, recorded but not relied upon: `task1-a1-a9` pass (run `38672796995`), `test` pass (run `38672796999`).

## Non-blocking carry-forward

- **M1.** Recursive verification is still unmemoized (exponential on diamond lineages). It must be fixed before Task 3 registry chains.
- **M3.** There is no raw-byte artifact identity path. Task 2's manifest must not trust raw SHA strings carried inside canonical mappings.
- **M4.** Revoked records are usability-gated in Task 3.
- **New N5.** The scope → stage table is frozen only in module code and docstring. Record it in the controlling plan as a prospective amendment, so the quantity has one authority.
- **New N6.** `canonical_v1` now imports numpy, which departs from the plan's "stdlib only". The departure is justified by the explicit numpy policy; record it.

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
