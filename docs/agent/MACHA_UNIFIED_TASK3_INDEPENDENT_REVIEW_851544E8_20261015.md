# Macha independent hostile review — Unified Task 3 (A2 + A5 + A6), PR #392

Date: 2026-10-15.

Role: independent hostile reviewer of controller work. Non-controlling.

No protected, biological, candidate, validation or oracle values were opened. Probes used the PR's own synthetic fixtures only.

## Verdict

`REJECT_UNIFIED_TASK3`

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

Much of the readiness derivation works:
- a missing or boolean resolver blocks;
- `asserted_ready` is ignored;
- revoked, requalification and stale identities block;
- cycles fail;
- `FIXTURE_UNBOUND` and per-fold claims are blocked at `REAL_REFERENCE_READY`.

But the registry does not enforce its own authority model:
- a unit-scoped record reaches `TRAINING_AUTHORIZED`;
- `KNOWN_TRUTH_QUALIFIED` needs no evidence;
- the owner-found actor self-qualification defect is still open through aliasing;
- the cache is caller-poisonable;
- revocation and history can be rewritten.

The delta also ships armed CI workflows that rewrite code and tests.

## 1. Head

| item | value |
|---|---|
| head | `851544e8dc2a3881193a4d5bbcf07933e1d61149` (PR #392 → `freeze/unified-task2-code-c7dfff1c-20261015`) |
| ancestors | frozen `c7dfff1c`, `799d2e23`, `e37a22b8` |
| delta | Task 3 code, schema, tests, workflows and patch scripts only; no frozen file modified |
| local tests | full `tests/v5/td_unified`: 154 passed (local, not CI) |

## Blocking findings

All probes are in `docs/agent/macha_task3_review_evidence_851544e8/task3_probe1.py` and its `.log`, run against the PR's own `registry_v1_dependency_fixtures`. There are 18 checks: 8 behaved as expected and **10 were BAD**. The 8 expected results include one NOTE row recording that a self-minted controller is accepted. The `HUMAN_EXECUTABLE` step in H1 was satisfied using self-asserted boolean `PROCESS_ISOLATION` and `CROSS_PROCESS_LEDGER_CUSTODY` dicts (see R1/R4).

### T3-B1 — CRITICAL: a unit-scoped registry record climbs to `TRAINING_AUTHORIZED`

- **Locus.** `promote_unit` (`registry_v1.py` ~776–865). Evidence gates exist only for `REAL_REFERENCE_READY` and `HUMAN_EXECUTABLE`, and frozen Task 1's `validate_authority_record` is never applied.
- **Attack.** H1. After a lawful `REAL_REFERENCE_READY`, the unit is promoted one stage at a time: `HUMAN_EXECUTABLE` → `HUMAN_EXECUTED` → `DOWNSTREAM_CERTIFIED` → `TRAINING_ELIGIBLE` → **`TRAINING_AUTHORIZED`**. The resulting record has `authority_scope=UNIT:G8` and `authority_restrictions=('NO_TRAINING_AUTHORITY',)`.
- **Why it is insufficient.** Frozen Task 1 (`799d2e23`) limits `UNIT:` scope to `SEMANTICS_ONLY…HUMAN_EXECUTED`, and the plan reserves training stages for project/owner authority. The registry is the authority system, yet it records a state that the frozen authority law forbids, while also carrying a restriction that says the opposite.
- **Smallest repair.**
  - `promote_unit` must validate the promoted record through Task 1 `validate_authority_record`. With UNIT scope, the maximum is `HUMAN_EXECUTED`.
  - `NO_TRAINING_AUTHORITY` must refuse any `TRAINING_*` stage.
  - Stages beyond `HUMAN_EXECUTED` are not unit-registry transitions.

### T3-B2 — CRITICAL: `KNOWN_TRUTH_QUALIFIED` (and `HUMAN_EXECUTED`) need no evidence

- **Locus.** `promote_unit`. No stage-specific evidence gate exists outside `REAL_REFERENCE_READY` and `HUMAN_EXECUTABLE`.
- **Attack.** H2. `SAME_CODE_PATH → KNOWN_TRUTH_QUALIFIED` succeeds with a controller object alone: no reviewer, no sealed-challenge or adjudication receipt. `HUMAN_EXECUTED` likewise needs no execution receipt (H1).
- **Why it is insufficient.** The plan's global constraint requires that "final qualification requires a separately sealed challenge realization/holdout and independent adjudication".
- **Smallest repair.**
  - Add a closed per-stage evidence-gate table.
  - Stages whose evidence types do not exist yet must fail closed: `KNOWN_TRUTH_QUALIFIED` until the Task 4/5 sealed-challenge adjudication receipts exist, and `HUMAN_EXECUTED` until execution receipts exist.
  - Require an independent reviewer for `KNOWN_TRUTH_QUALIFIED`.

### T3-B3 — CRITICAL: A5 actor self-qualification remains possible (aliasing, and no actor registry)

- **Loci.** `_actor_id` (~83–87) and the actor comparisons in `promote_unit` and `revoke_or_supersede`.
- **Attack.** With producer `actor_id = "producer:G8"`, these controller `actor_id`s are all accepted as distinct and the promotion succeeds:
  - `"producer:G8 "` (trailing space);
  - `" producer:G8"` (leading space);
  - `"PRODUCER:G8"`;
  - `"producer：G8"` (fullwidth colon).

  Separately, any newly minted string (`"minted-by-producer-1"`) is accepted as an independent controller.

  The exact-equal cases (controller = producer, reviewer = controller, reviewer = producer) are correctly refused.
- **Why it is insufficient.** Independence is checked by exact, un-normalized equality of free strings in self-declared objects. This is the owner-found RED6 defect class (the same actor presenting a separate role object), and it is still exploitable. With no closed actor set, a producer can always present a "distinct" controller.
- **Smallest repair.**
  - Bind a frozen, identity-bound `ACTOR_REGISTRY` (closed set, controller-curated, bound through the manifest/registry digest).
  - Each actor has a canonical id under a strict grammar (for example `^[a-z0-9][a-z0-9:_.-]*$`, ASCII only, no surrounding whitespace) and its permitted roles.
  - Refuse actors not in the registry. Compare independence on registry identity.
  - Require that prerequisite evidence, content-validation receipts and controller/reviewer objects are issued by registry actors distinct from the unit's producer and executor.

### T3-B4 — IMPORTANT: the verification cache is caller-poisonable and survives a resolver change (R6 not met)

- **Locus.** `_verify_unit_dependencies` (~448–553). It takes a caller-supplied `MutableMapping`, keyed by `(unit identity, field, sha)`, and trusts a cached `(True, None)` before verifying anything.
- **Attacks.**
  - **H3.** A cache pre-filled with `(True, None)` for the unit's keys makes `derive_real_reference_ready` return **ready** with `dependency_verifier = lambda s: None`, so nothing is resolvable.
  - **H4.** A cache warmed with the full resolver keeps reporting ready after switching to a resolver that lacks every object.
- **Why it is insufficient.** "Digest strings are not authority" is bypassed by a cache entry. Cached positives are not bound to the verifying resolver or context.
- **Smallest repair.** Make the cache internal and per-call (memoize inside one validation), or key it by an opaque resolver/context token held by the registry. Never accept caller-written entries. Store the verified object or bytes digest and re-check on hit. Add H3/H4 as RED tests.

### T3-B5 — IMPORTANT: active revocation and immutable history are not enforced

- **Locus.** `TDQualificationRegistry` is a caller-constructed tuple container with no append-only chain validation. `_validate_current_stage_promotion_provenance` (~714–773) checks one receipt for internal consistency only.
- **Attacks.**
  - **H6.** Revoke G8 (`REVOKED_BY_DEFECT`), then rebuild the registry with G8 set back to `ACTIVE` and the revocation receipt deleted. The unit is then re-promoted to `HUMAN_EXECUTABLE`.
  - **H5.** Hand-construct G8 directly at `REAL_REFERENCE_READY`, with a fabricated pre-registry snapshot (no prerequisites) and a fabricated `PromotionReceipt` that is internally consistent. Promotion to `HUMAN_EXECUTABLE` **succeeds**, although no lawful readiness derivation ever occurred.
- **Why it is insufficient.** "Revoked … must remain auditable but become unusable" (plan review focus) and "immutable promotion history" both hold only if the caller passes an honest registry object. Provenance checks a receipt's consistency, not its lawfulness.
- **Smallest repair.**
  - Add `validate_registry_history(registry, resolver, genesis_sha)`, which replays every promotion and revocation receipt from a genesis anchor. Each receipt's `pre_registry_sha` must equal the replayed state's canonical SHA. Current stage and lineage must equal the replay result. For gated promotions, readiness must be re-derived on the replayed pre-state.
  - Require it in `promote_unit` and `derive_real_reference_ready`.
  - Anchor the registry head externally, as Task 2's ledger-head obligation does.

### T3-B6 — IMPORTANT (custody): armed CI workflows rewrite code and tests on push

- **Loci.** `.github/workflows/task3-red6-actor-repair.yml` and `.github/workflows/apply-task3-cycle4-hardening.yml`, both `contents: write`.
- **Defect.**
  - `task3-red6-actor-repair` fires on **any** human push to `work/unified-task3-registry-impl-20261015`, with no path filter. It runs `scripts/agent/task3_green6_fixture_migration.py`, which rewrites every `tests/v5/td_unified/test_registry_v1*.py` (except cycle6) that constructs `RegistryUnit(` without `producer_actor_identity=`, then commits and pushes as `github-actions[bot]`.
  - A future hostile RED test that deliberately omits actor identity would therefore be silently "migrated" into a passing fixture. CI-authored commits (GREEN2/3/4/6) also became part of the reviewed code.
  - The reviewed bytes at `851544e8` are fixed and the patchers are idempotent, so this does not invalidate the head's content. It does compromise every future repair head on this branch, and the RED-first evidence.
- **Smallest repair.** Before any further push and before freeze, delete these write workflows, or reduce them to `contents: read` and `workflow_dispatch` with no commit step. Keep the patch scripts as historical evidence only.

## Packet sections

| section | result |
|---|---|
| A2 lineage/history | partial. One-stage steps; non-`ACTIVE` units cannot promote; `reidentify_unit` resets to `SEMANTICS_ONLY` + `REQUIRES_REQUALIFICATION`; supersession requires the successor identity and scope. **Fails** on T3-B1, T3-B2 and T3-B5. |
| A5 actor independence | **FAIL** (T3-B3). Exact-equal aliases are refused. |
| A6 prerequisite graph | **PASS** on the packet's checks: missing or boolean resolver, `asserted_ready`, revoked/requalification/insufficient-stage/stale identities, cycles, visibility of unsatisfied prerequisites. **Fails** on R6 (T3-B4). |
| frozen Task 2 binding | per-unit identities are matched against the exact Task 2 execution-identity row through the manifest; access-policy population authority is consistent with the unit; `FIXTURE_UNBOUND` is blocked at `REAL_REFERENCE_READY`. **PASS.** |
| R1, R4 | content predicates are enforced, but the evidence objects are self-asserted booleans by unregistered authors. Repaired by T3-B3's actor registry; currently insufficient. |
| R2 | a content-validation receipt plus a `CONTENT_VALIDATOR` object are required, but the validator is self-mintable (T3-B3). |
| R3 | **PASS** at `REAL_REFERENCE_READY`. |
| R5 | `PER_FOLD_SOURCE_STRATIFIED` blocked. **PASS.** |
| R6 | **FAIL** (T3-B4). |
| promotion/revocation provenance | **FAIL** (T3-B5). |

## Non-blocking

- Commits authored by CI bots should be listed in the Task 3 custody record together with the patch script and input that produced each, for reproducibility.
- `prerequisite_evidence_verifier` and `asserted_ready` are dead parameters kept for compatibility; remove them, to avoid suggesting they carry authority.

## Freeze decision

Task 3 may not be frozen at `851544e8`. Repair T3-B1 to T3-B6 RED-first, with the H1–H6 and aliasing probes as RED tests, disarm the write workflows first, and then a focused re-check of those items suffices.

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
