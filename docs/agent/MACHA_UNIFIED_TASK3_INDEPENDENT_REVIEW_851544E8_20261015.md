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
| head | `851544e8dc2a3881193a4d5bbcf07933e1d61149` (PR #392 → frozen Task 2 base) |
| ancestors | frozen `c7dfff1c`, `799d2e23`, `e37a22b8` |
| delta | Task 3 code, schema, tests, workflows and patch scripts only; no frozen file modified |
| local tests | full `tests/v5/td_unified`: 154 passed (local, not CI) |

The exact source review is preserved at `review/macha-task0-independent-review-20261014` head `869ca777a498181c519ccfc04b8bf5db0f2888c7`.

## Blocking findings

All probes are in `docs/agent/macha_task3_review_evidence_851544e8/task3_probe1.py`, run against the PR's own dependency fixtures. There are 18 checks: 8 behaved as expected and 10 were BAD.

### T3-B1 — CRITICAL: unit scope reaches `TRAINING_AUTHORIZED`

`promote_unit` does not apply frozen Task 1 `validate_authority_record`. A unit with `authority_scope=UNIT:G8` and `NO_TRAINING_AUTHORITY` can step from `HUMAN_EXECUTED` through `DOWNSTREAM_CERTIFIED`, `TRAINING_ELIGIBLE` and `TRAINING_AUTHORIZED`.

Required repair: validate every promoted result against frozen Task 1 authority law. UNIT scope maximum is `HUMAN_EXECUTED`; `NO_TRAINING_AUTHORITY` refuses all `TRAINING_*`; later pipeline/project stages are not unit-registry transitions.

### T3-B2 — CRITICAL: stage evidence gates are missing

`SAME_CODE_PATH → KNOWN_TRUTH_QUALIFIED` succeeds with a controller alone: no independent reviewer and no sealed-challenge/adjudication evidence. `HUMAN_EXECUTED` likewise has no execution-receipt gate.

Required repair: closed per-stage evidence-gate table. Stages whose evidence types do not yet exist must fail closed. `KNOWN_TRUTH_QUALIFIED` waits for Task 4/5 sealed challenge/adjudication evidence; `HUMAN_EXECUTED` waits for execution evidence.

### T3-B3 — CRITICAL: actor aliasing and self-minted actors defeat A5

With producer `actor_id="producer:G8"`, controller aliases with trailing whitespace, leading whitespace, changed case, or a fullwidth colon are accepted as distinct. Any newly invented actor string is also accepted because there is no closed actor registry. Exact-equal aliases are correctly refused, but that is insufficient.

Required repair: frozen identity-bound `ACTOR_REGISTRY`; strict ASCII canonical actor IDs; explicit permitted roles; refuse unknown actors; compare independence on authenticated registry identities. Prerequisite evidence/content validators must also be issued by authorized registered actors distinct from producer/executor where required.

### T3-B4 — IMPORTANT: caller-poisonable verification cache

`_verify_unit_dependencies` accepts a caller-supplied writable cache and trusts positive entries before verifying dependencies. Pre-filled positives can make unresolvable dependencies ready; a warmed cache can survive a resolver change.

Required repair: internal per-call or context-bound cache only. Never accept caller-written positives. Re-check verified object/bytes identity on cache use and invalidate on context/dependency mutation.

### T3-B5 — IMPORTANT: revocation/history can be rewritten

`TDQualificationRegistry` is a caller-constructed tuple container with no append-only chain replay. A revoked unit can be rebuilt as ACTIVE after deleting the revocation receipt and then re-promoted. A fabricated `REAL_REFERENCE_READY` history with an internally consistent receipt can enable promotion although no lawful readiness derivation occurred.

Required repair: replay every promotion/revocation from a genesis anchor. Every receipt `pre_registry_sha` must equal replayed state. Current stage/lineage must equal replay. Gated promotions must rederive readiness on replayed pre-state. Anchor latest registry head outside the registry object.

### T3-B6 — IMPORTANT: armed CI workflows rewrite code/tests

`.github/workflows/task3-red6-actor-repair.yml` and `.github/workflows/apply-task3-cycle4-hardening.yml` have `contents: write` behavior and can commit code/test rewrites after human pushes. A future hostile RED test deliberately omitting actor identity could be silently migrated into a passing fixture.

Required repair: before any further Task 3 push, delete/disarm these write workflows or make them read-only/manual-only with no commit step. Preserve patch scripts and CI-bot commit provenance as historical evidence only.

## Packet results

- A2 lineage/history: partial; one-stage steps, non-ACTIVE blocking, reidentification reset and successor identity checks work; fails B1/B2/B5.
- A5 actor independence: FAIL (B3).
- A6 prerequisite graph: PASS on missing/boolean resolver, ignored asserted_ready, revoked/requalification/insufficient-stage/stale dependencies, cycles and visible unsatisfied prerequisites; fails R6 via B4.
- frozen Task 2 binding: PASS; exact per-unit execution identity and population authority binding work; `FIXTURE_UNBOUND` blocked at `REAL_REFERENCE_READY`.
- R1/R4: predicates exist but evidence can be self-asserted by unregistered authors; insufficient until actor/trust anchor repair.
- R2: content receipt/validator objects exist but validators are self-mintable; insufficient until B3 repair.
- R3: PASS.
- R5: PASS; per-fold source-stratified claims blocked.
- R6: FAIL via B4.
- promotion/revocation provenance: FAIL via B5.

## Non-blocking carry-forward

- List CI-bot-authored Task 3 commits in custody records with the patch script/workflow that generated each.
- Remove dead `prerequisite_evidence_verifier` and `asserted_ready` compatibility parameters so they do not appear authoritative.
- R1/R4 require a real trust anchor before `HUMAN_EXECUTABLE`.

## Freeze decision

Task 3 may not be frozen at `851544e8`. Repair T3-B1 through T3-B6 RED-first, disarming the write workflows before any repair push. After exact-head GREEN verification, a focused independent recheck of these six findings is sufficient.

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
