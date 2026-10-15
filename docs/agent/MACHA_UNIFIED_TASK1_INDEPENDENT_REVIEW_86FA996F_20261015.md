# Macha independent hostile review — Unified Task 1 (A1 + A9), PR #385

Date: 2026-10-15.

Role: independent hostile reviewer of controller work. The Task 1 code is a controller re-implementation, not Macha's bytes. Non-controlling.

**Read-only.** No protected object or candidate outcome was opened, and nothing was recomputed.

## Verdict

`REJECT_UNIFIED_TASK1__BLOCKING_FINDINGS_T1_B1_TO_T1_B5`

`TASK1_REMAINS_OPEN__UNIFIED_TASK2_REMAINS_BLOCKED`

The structure is right:
- one ordered stage enum and four lineage statuses;
- recursive receipt verification that recomputes payload, receipt, inputs and role objects;
- cycle detection;
- closed receipt fields;
- byte compatibility with old Task 1 for plain JSON values.

But the canonical encoder can be made to emit forged or non-canonical bytes. That is the root identity primitive the whole unified lane will trust. Three more A1/A9 guarantees also hold only by string convention.

## 1. Head

| item | value |
|---|---|
| head | `86fa996f609bec3f39d0f6a12d7f040b2544af39` |
| branch | `implementation/unified-task1-live-20261015` → base `freeze/task0-accepted-e37a22b8-20261015` (= `e37a22b8`) |
| delta from frozen Task 0 | 10 added files; no Task 0 file modified or deleted (verified with `git diff --name-status`) |
| local tests | `pytest tests/v5/td_unified/test_canonical_v1.py tests/v5/td_unified/test_authority_v1.py` → 18 passed (local, not CI) |

## 2. Blocking findings

All probes are in `docs/agent/macha_task1_review_evidence_86fa996f/probe1.py` and `probe2.py`, with logs.

### T1-B1 — CRITICAL: the canonical encoder trusts subclass methods, so it can emit non-JSON or forged bytes

- **Locus.** `scripts/v5/td_unified/canonical_v1.py` `_encode` (lines ~74–115) and `_encode_string`. Values are dispatched with `isinstance` and then call `repr(value)`, `str(value)` and `value.replace`.
- **Failing inputs:**

  | input | canonical bytes produced |
  |---|---|
  | `{"x": np.float64(1.5)}` (numpy 2.4.6) | `{"x":np.float64(1.5)}` — invalid JSON; its digest differs from `{"x": 1.5}` |
  | float subclass with `__repr__ → "999"` | `{"x":999}` |
  | int subclass with `__str__ → "777"` | `{"x":777}` |
  | str subclass with `replace → "FORGED"` | `{"x":"FORGED"}` |

- **Why it matters.**
  - Every unified identity is `sha256(domain ‖ canonical_bytes)`.
  - Scientific payloads routinely carry `np.float64`, so identities silently depend on the Python type that carried a value, and on the numpy version: in numpy 1.x, `repr(np.float64(1.5))` is `1.5`.
  - Hostile subclasses can choose the bytes of any scalar.
  - The module and the reuse record claim the reviewed old-Task-1 behaviour is preserved, but old Task 1 converted numpy scalars explicitly. This is a regression from that substrate.
- **Why the tests missed it.** No test uses numpy scalars or subclasses.
- **Smallest repair.**
  - Dispatch on exact type: `type(v) is bool/int/float/str/list/tuple/dict`.
  - Encode with the base methods: `int.__repr__`, `float.__repr__`, `str.replace` called on `str(v)` only after `type(v) is str`.
  - Prospectively choose one numpy policy, either reject all numpy scalars or convert ≤64-bit ones as old Task 1 did, and test both `np.float64` and the subclass cases.
  - Note: `bool` must still be checked before `int`.

### T1-B2 — IMPORTANT: `producer_code_sha` is trusted as a string

- **Locus.** `verify_scientific_receipt` checks only that `producer_code_sha` is 40-hex. It is never resolved or recomputed.
- **Failing input.** `producer_code_sha = "0"*40` verifies.
- **Why it matters.** The plan's global constraints say scientific identity binds code identities, and that a digest string is never authority. Producer code is authority-bearing: it asserts which executable produced the output. This is the same class as the three defects already repaired (trusted input, output, manifest, registry and access hashes), and the last one left.
- **Smallest repair.** Resolve the producer code identity and verify it by recomputation, failing closed if unavailable. Two ways:
  - (a) through the resolver, as a canonical code-manifest object (paths + git blob SHAs) whose `canonical_sha256` is bound;
  - (b) through a code resolver that recomputes the git blob/commit.

  Either way, test that a well-formed but nonexistent SHA is refused.

### T1-B3 — IMPORTANT: receipt roles are untyped, and one identity may fill several roles

- **Locus.** `_verify_dependency` checks only digest equality, for output, manifest, registry and access policy.
- **Failing inputs.**
  - `{}` verifies simultaneously as output, manifest, registry and access policy.
  - An input object verifies as output, manifest, registry and access policy at once.
- **Why it matters.** "Receipt binds manifest/registry/access" becomes vacuous. A receipt can bind an empty "access policy", undermining the plan's protected-partition review focus, which is enforced in Task 2 only if Task 2 can rely on the role binding.
- **Why the tests missed it.** `test_duplicate_or_conflicting_parent_identity_is_rejected` covers duplicates within one list only.
- **Smallest repair (Task 1 scope).**
  - Refuse the same SHA in more than one role across inputs, parents, output, manifest, registry and access.
  - Require each resolved role object to carry a declared role tag (`object_role ∈ {OUTPUT, MANIFEST, REGISTRY, ACCESS_POLICY}`) that equals its slot.

  Full schema typing of manifest, registry and access objects is a Task 2/3 obligation and should be recorded as such.

### T1-B4 — IMPORTANT: `authority_scope` is parsed by a short denylist, so unit records can claim pipeline or project scope

- **Locus.** `authority_v1.py` `_POSITIVE_TRAINING_SCOPES` / `_POSITIVE_PROJECT_SCOPES`, plus the schema's `"authority_scope": {"type": "string", "minLength": 1}`.
- **Failing inputs.** All of these are accepted at `FIXTURE_SAME_INTERFACE`, and at every other stage: `PIPELINE`, `PROJECT_WIDE`, `TD_PIPELINE`, `ALL`, `GLOBAL_PROJECT`, `project-training`, `TRAINING_PROJECT`, `Project Training`.
- **Why it matters.** The plan requires that "unit-level qualification can never imply pipeline/project authority." With a free-text denylist, any unlisted spelling of a broader scope passes. The repaired "negative scope" case (`UNIT:G8__NO_TRAINING_AUTHORITY`) shows that restrictions and scope are being mixed in one string.
- **Smallest repair.**
  - Use a closed scope grammar in code and schema: `UNIT:<unit_id>`, where the id must equal `record.unit_id`; `PIPELINE:<pipeline_id>`; or `PROJECT`.
  - Add a prospectively frozen scope → permitted-stage table. Its values are the deciding lane's to set; the mechanism is required now.
  - Move negative restrictions into a separate field.
  - Refuse anything else.

### T1-B5 — IMPORTANT: the unified identity format is not pinned by any known-answer digest

- **Locus.** `tests/v5/td_unified/test_canonical_v1.py` contains 0 hard-coded 64-hex values.
- **Why it matters.** Changing `_CANONICAL_DOMAIN`, the encoding, or the receipt body layout would change every unified identity while all 18 tests stay green. This is the same defect I required fixed in old Task 1 (known-answer tests plus a byte-level spec).
- **Smallest repair.**
  - Add frozen known-answer digests for `canonical_sha256` on fixed objects, including the control-character/DEL/non-ASCII/float object, and for one fixed receipt's `receipt_sha256` and `payload_sha256`.
  - Document the exact domain, receipt-body construction and field order in the module docstring.

## 3. Verified working (local probes)

- **Old Task 1 byte compatibility for plain JSON values.** `canonical_bytes` equals the old `canonical_json_bytes` at `ff597faf` on the frozen known-answer object and on 3,000 seeded random objects (0 mismatches). The ADAPT_AND_WRAP claim holds for plain JSON types; it fails for numpy and subclass values (T1-B1).
- **Recomputation and recursion.**
  - payload and receipt digests are recomputed;
  - inputs, output, manifest, registry and access are resolved and recomputed;
  - receipts used as inputs or parents are verified recursively;
  - cycles are refused;
  - closed receipt fields;
  - unknown schema refused.
- **A9.**
  - exactly 10 ordered stages and 4 lineage statuses;
  - schema enums equal code enums;
  - bare PASS/GREEN/mechanics labels are not stages;
  - one authority enum only.

## 4. Non-blocking (carry forward)

- **M1.** Recursive verification has no memoization. On a diamond-shaped lineage, verification time grows roughly ×4 every two levels: depth 16 takes 11.9 s. Memoize verified receipt SHAs within a call before Task 3's registry chains.
- **M2.** A non-string `unit_id` raises `AttributeError` instead of `AuthorityError`. Type-check all fields.
- **M3.** No unified raw-byte artifact identity exists. Raw SHA-256 strings carried inside a canonical mapping, such as SQLite or Level-4 hashes, are not verified against bytes. Task 2's manifest needs a raw-byte verification path, or it reintroduces a digest string as authority.
- **M4.** `validate_authority_record` accepts `TRAINING_AUTHORIZED` with `REVOKED_BY_DEFECT`. Usability gating belongs to Task 3; record it as a Task 3 obligation.
- **N1–N4** from the Task 0 review are correctly carried in `UNIFIED_TASK1_REUSE_SUBSTRATE_V1.json`.

## 5. Freeze decision

Unified Task 1 may not be frozen at `86fa996f`. After T1-B1 to T1-B5 are repaired RED-first, a focused re-check of those five items suffices.

`TASK1_REMAINS_OPEN__UNIFIED_TASK2_REMAINS_BLOCKED`

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
