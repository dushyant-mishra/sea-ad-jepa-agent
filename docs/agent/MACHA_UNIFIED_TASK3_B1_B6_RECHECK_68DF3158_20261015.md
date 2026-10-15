# Macha focused re-check — Unified Task 3 T3-B1…B6 (candidate `68df3158`)

Date: 2026-10-15.

Role: independent hostile reviewer of controller work. Non-controlling.

No protected, biological, candidate, validation or oracle values were opened. Every probe used the PR's own synthetic fixtures and lawful setup helpers.

## Verdict

`REJECT_UNIFIED_TASK3`

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

**Closed:** B1, B4 and B6, plus the narrow H5/H6 forms of B5 and the alias and self-mint forms of B3.

**Still open:**
1. The KNOWN_TRUTH gate that B2 closed for promotion can still be satisfied by declaring the stage.
2. The B3 repair is incomplete for content validators and evidence issuers, and the actor registry is unanchored.
3. A revocation does not survive the creation of a fresh custody object.
4. A defect I missed in the first review: Task 3 never applies frozen Task 2's population/manifest validators.

## Head

| item | value |
|---|---|
| reviewed | `68df31584d17f91da2635cdf8e03bbe93695f9d1` (pinned `candidate/unified-task3-green-68df3158-20261015`) |
| PR #392 head | `0a25f72c`; descends from `68df3158` through 10 commits that touch only the docs ledger |
| delta from `851544e8` | 39 commits, all human-authored, no `github-actions[bot]` |
| frozen Task 0–2 code | unmodified; Task 2's `manifest_v1.py` is identical to `c7dfff1c` |
| structure | the old module is preserved as `registry_v1_legacy.py`; `registry_v1.py` is now a facade (B5 custody) over it; new `actor_registry_v1.py` and `workflow_policy_v1.py` |
| local tests | 177 passed (local, not CI; Python 3.9, pytest 6.2.4). The bare run fails at collection on this machine because an unrelated `tests` package from PyMC in site-packages shadows the repo's; it was run through a wrapper that pins the repo's `tests` package and changes no repo file. For comparison, `851544e8` gives 154 passed under the same wrapper. |

## Probe

The probe is `docs/agent/macha_task3_review_evidence_851544e8/task3_recheck_probe.py`, with its `.log`.

Results: 38 checks, **31 expected, 7 BAD**, plus 4 NOTE rows.

The positive control P0 is the PR's own lawful flow: genesis → `REAL_REFERENCE_READY` (RRR) → `HUMAN_EXECUTABLE`, run with history custody. It succeeds.

## Per-blocker status

### T3-B1 — CLOSED

- Facade and legacy paths refuse `HUMAN_EXECUTED → DOWNSTREAM_CERTIFIED`, citing the frozen Task 1 law ("outside the allowed UNIT scope stage range").
- `DOWNSTREAM_CERTIFIED → TRAINING_ELIGIBLE` and `TRAINING_ELIGIBLE → TRAINING_AUTHORIZED` are refused (`NO_TRAINING_AUTHORITY`).
- `HUMAN_EXECUTABLE → HUMAN_EXECUTED` is refused (B2).
- Custody genesis refuses a declared UNIT record at `TRAINING_AUTHORIZED`.

Non-blocking: `RegistryUnit` construction still accepts a UNIT-scoped record at `TRAINING_AUTHORIZED`. It should call `validate_authority_record` itself.

### T3-B2 — CLOSED for promotion; OPEN by declaration (blocking, CRITICAL)

Promotion is closed. `SAME_CODE_PATH → KNOWN_TRUTH_QUALIFIED` is refused with and without a reviewer, on both the facade and legacy paths ("SEALED_CHALLENGE_REVIEW … not implemented … closed").

**N2 (blocking).** Because promotion to `KNOWN_TRUTH_QUALIFIED` is now impossible, every unit at that stage got there by being declared in a caller-constructed genesis. Such units are then accepted:
- custody genesis permits stages up to `KNOWN_TRUTH_QUALIFIED`;
- RRR requires the unit, and each prerequisite target, to be at `KNOWN_TRUTH_QUALIFIED`;
- P0 reaches `HUMAN_EXECUTABLE` from a declared, unevidenced `KNOWN_TRUTH_QUALIFIED`.

The registry thus states that `KNOWN_TRUTH_QUALIFIED` requires sealed-challenge evidence, and then consumes it without that evidence. That skips the plan's central rule: qualification requires a separately sealed challenge with independent adjudication, which is Task 4/5.

My first review used a declared `KNOWN_TRUTH_QUALIFIED` as its positive control without flagging this. That was an omission on my part. The B2 repair makes the contradiction explicit.

**Smallest repair:**
- Cap custody genesis at the highest stage reachable without unavailable evidence (`SAME_CODE_PATH`).
- In RRR, require for the unit and every prerequisite target an authenticated `SEALED_CHALLENGE_REVIEW` receipt for the `KNOWN_TRUTH_QUALIFIED` stage. That receipt does not exist yet, so RRR and `HUMAN_EXECUTABLE` fail closed until Task 4/5.
- Tests can still exercise every RRR/`HUMAN_EXECUTABLE` predicate by asserting that, with everything else satisfied, the only remaining blocker is that missing receipt.

### T3-B3 — PARTIAL (blocking)

Closed:
- The five original aliases (whitespace, case, fullwidth colon, `minted-by-producer-1`) are refused when absent from a curated registry.
- Independence is checked on the logical actor id. Four dual-role probes with curated registries are all refused:
  - C1 registered as both controller and reviewer;
  - `producer:G8` registered as reviewer;
  - `executor:G8` registered as controller;
  - `producer:G8` as revocation controller.
- The actor-id grammar is strict ASCII.

Open:
- **B3-V (IMPORTANT).** `_validate_content_validation_receipt` (`registry_v1_legacy.py` ~203–235) still resolves `validator_identity_sha` with `_resolve_object(…, "CONTENT_VALIDATOR")` rather than `_registered_actor`, and checks no independence. A receipt whose validator is an unregistered object with `actor_id = producer:G8` satisfies a content-required prerequisite. Both `derive_real_reference_ready` and `promote_unit` reach RRR. This was step 4 of Task 2 in the B3 plan, and it was not implemented. R2 therefore remains open.
- **B3-E (IMPORTANT).** The role `PREREQUISITE_EVIDENCE_ISSUER` is declared but never enforced. `PROCESS_ISOLATION` and `CROSS_PROCESS_LEDGER_CUSTODY` evidence objects carry no issuer field, and `_human_execution_blockers` (~754–787) checks only the boolean predicates. Task 2 R1 required process isolation to block `HUMAN_EXECUTABLE`; at present a dict that anyone can write satisfies that block. Planned in B3 but not implemented.
- **B3-R (IMPORTANT).** Nothing anchors `actor_registry_sha`. The B3 plan deferred this to B5, and B5 binds the digest only at genesis, which any caller constructs. A producer that writes its own actor registry, mints `minted-by-producer-1` as controller and `minted-by-producer-2` as reviewer, and creates its own custody reaches RRR. Self-minting is closed only when the caller is honest.

**Smallest repair:**
- Validators and evidence issuers resolve through `_registered_actor`, with roles `CONTENT_VALIDATOR` / `PREREQUISITE_EVIDENCE_ISSUER`, and must be logically distinct from the producer and executor. Add an `issuer_identity_sha` field to the evidence objects.
- Commit a frozen `TD_ACTOR_REGISTRY_V1` artifact and pin its canonical SHA in Task 3 code. Custody, promotion and revocation refuse any other `actor_registry_sha`. Tests either use the pinned registry's public actor objects, or use a separate fixture mode that cannot reach RRR.

### T3-B4 — CLOSED

The caller's `verification_cache` is ignored on the facade and legacy paths, and both use internal per-call caches.
- H4: a warmed cache with an empty resolver gives not ready.
- H3: a poisoned cache with an empty resolver gives not ready.
- Legacy `promote_unit` to RRR with a poisoned cache is refused.

### T3-B5 — PARTIAL (blocking)

Closed:
- H6 (deleted revocation with the same custody) is refused ("revocation event/head mismatch").
- H6 without custody is refused.
- H5 (fabricated RRR receipt) is refused (PR test).
- A fresh custody object cannot be created from an RRR genesis.

Open:
- **B5-F (IMPORTANT).** A revocation lives only inside one custody object, and any caller can construct another one with any key. After G8 was revoked in custody A, a fresh genesis plus custody B re-qualified **the same G8 canonical identity** to `HUMAN_EXECUTABLE`. Nothing compares `head_attestation` with any anchor. My first review asked for "anchor the registry head externally"; that was not done.

**Smallest repair:**
- Keep a revocation ledger keyed by unit canonical identity, anchored outside the custody object (a committed or published artifact, or the pinned genesis anchor).
- Custody genesis refuses revoked identities, so re-entry requires `reidentify_unit` → `REQUIRES_REQUALIFICATION`.
- Pin or publish the genesis anchor so that a second custody for the same manifest and actor registry is refused.

### T3-B6 — CLOSED

- `task3-red6-actor-repair.yml` and `apply-task3-cycle4-hardening.yml` are deleted.
- No committed workflow contains `contents: write`, `write-all`, `git commit` or `git push` (all 55 scanned).
- Cycles 1–3 are now verify-only (`contents: read`).
- A policy gate (`workflow_policy_v1.py`) exists.

Non-blocking:
- `unified-task3-registry.yml` has no `permissions:` block, so it inherits the repository default. Add `contents: read`.
- The policy's path markers do not include `registry_v1_legacy.py` or `actor_registry_v1.py`.

## New blocker — N1 (CRITICAL): frozen Task 2 population/manifest authority is not applied

Task 3 never imports `manifest_v1`. At the RRR consumption point, population authority is the string equality `unit.population_authority == access_policy["population_authority"]` (legacy ~606–611), where the access policy is any object with `object_role = ACCESS_POLICY`. The "Task 2 manifest" is any dict with `schema = TD_EXECUTION_MANIFEST_V1` plus two digest fields (~559–601).

The probe built an access policy with 104 `FAKE_*` donors and `crossfit_folds = "CHOSEN_LATER"`, and a 3-field manifest:
- frozen Task 2 refuses both (`validate_population_access_policy_payload`: fields mismatch; `validate_manifest`: fields/schema mismatch);
- Task 3 promotes the unit to **RRR** as `AUTHENTICATED_READER_SPLIT`.

This re-opens T2-B1 (string-based population authority) at the Task 3 consumption point. It also defeats R3 and the plan's "Task 3 consumes … Task 2 manifest/access objects" with `TD_EXECUTION_MANIFEST_V1` as root identity.

My first review recorded "frozen Task 2 binding: PASS". **That was wrong.** I checked row matching against a table without checking that the manifest holding the table was a valid Task 2 manifest.

**Smallest repair:** in the RRR and `HUMAN_EXECUTABLE` gates, resolve the unit's manifest and run frozen Task 2 `validate_manifest(payload, resolver, raw_resolver=…)`. That call re-derives the population and folds from the raw reader-split bytes. Then require `manifest.access_policy_sha == unit.access_policy_sha`. Fail closed without a raw resolver. Fixtures then use a Task-2-valid manifest, as the Task 2 suites already do.

## Required-format answers

1. **Head:** `68df31584d17f91da2635cdf8e03bbe93695f9d1`.
2. **A2 (lineage/history):** B1 closed. B2 is closed for promotion but open by declaration (N2). B5 is partial (B5-F).
3. **A5 (actor independence):** partial. The controller/reviewer/producer/executor checks are closed; validator and issuer are unbound; the registry is unanchored (B3-V, B3-E, B3-R).
4. **A6 (prerequisite graph):** the graph checks remain as accepted earlier; B4/R6 closed.
5. **Task 2 binding:** **FAIL** (N1). My earlier PASS is withdrawn.
6. **R1–R6:**
   - R1 open (B3-E);
   - R2 open (B3-V);
   - R3 open (N1);
   - R4 open (self-asserted custody evidence, no issuer);
   - R5 pass (`PER_FOLD_SOURCE_STRATIFIED` still blocked);
   - R6 closed.
7. **Provenance:** H5/H6 closed for a single custody; B5-F open across custodies.
8. **Probes:** 38 checks, 31 as expected, 7 BAD, 4 NOTE.
9. **Carry forward (not blocking once the items above are repaired):**
   - **R7.** Actor identities are public content digests, not credentials: a producer can present the registered C1 digest (NOTE row). Real human execution needs harness-attested or signed controller/reviewer actions.
   - **R1.** Custody private state is writable in-process (NOTE row).
   - `registry_v1_legacy.promote_unit` is a public, custody-free path to `HUMAN_EXECUTABLE` (NOTE row). Make it private, or have every downstream consumer require `validate_current`.
   - Construction-time Task 1 validation in `RegistryUnit`.
   - Explicit `permissions` on `unified-task3-registry.yml`.
10. **Freeze decision:** Task 3 may not be frozen at `68df3158`. A focused re-check of N1, N2, B3-V, B3-E, B3-R and B5-F suffices after a RED-first repair that adds these probes as tests. B1, B4 and B6 stay accepted.

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
