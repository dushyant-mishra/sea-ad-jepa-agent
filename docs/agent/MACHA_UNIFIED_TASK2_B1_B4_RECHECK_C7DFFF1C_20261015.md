# Macha focused re-check — Unified Task 2 T2-B1…B4 (draft PR #390)

Date: 2026-10-15.

Role: independent hostile reviewer of controller work. Scope: T2-B1…B4 only. Non-controlling.

The only real-data read was the reader-split raw bytes, metadata/partition identity only. No biological, candidate, validation or oracle values were opened.

## Verdict

`ACCEPT_UNIFIED_TASK2`, for exact head `c7dfff1cee608e4a101855d42cf0af08491c2aaf`.

`TASK2_MAY_BE_FROZEN__UNIFIED_TASK3_MAY_BEGIN_PROSPECTIVELY`

This grants no target, representation, Stage 4, protected-value or training authority.

## Head

| item | value |
|---|---|
| head | `c7dfff1c…` (draft PR #390 → `freeze/unified-task1-accepted-799d2e23-20261015`) |
| ancestors | rejected `2c391137`, frozen `799d2e23`, frozen `e37a22b8` |
| delta from `2c391137` | `manifest_v1.py`, `td_execution_manifest_v1.json`, one new test file; no frozen Task 0/1 file modified |
| local tests | full `tests/v5/td_unified`: 103 passed (local, not CI) |

## Hostile re-attack

The probe is `docs/agent/macha_task2_review_evidence_2c391137/task2_recheck_probe.py`, with its `.log`. All 27 attacks and positive controls behaved as expected; BAD = 0.

### T2-B1 — CLOSED

`_enforce_authoritative_population_payload` re-resolves the raw reader-split bytes, recomputes SHA-256, re-parses 149 = 104/22/23, and requires the policy's `fit_donors` and `crossfit_folds` to equal the recomputed donor set and the `DONOR_SHA256_ORDER_ROUND_ROBIN_V1` folds. A missing resolver fails closed.

This applies at every authority-consuming point: payload validation, `require_current_td_population_authority`, manifest population binding, sub-policy consistency, `issue_session` and `validate_producer_access`.

| attack | result |
|---|---|
| forged 104 `FAKE_*` donors, with or without a resolver | refused |
| lawful donors with non-law folds | refused |
| altered split bytes | refused (SHA mismatch) |
| real policy (positive control) | accepted |

The population registry `50b29d7e…` is now a custody annotation only, checked for consistency but not used as authority.

### T2-B2 — CLOSED

Authoritative access requires a `HarnessAccessRegistry` that issues the session id, stores the HMAC-attested `OBSERVED_ACCESS_LEDGER_V2_HARNESS_ATTESTED`, and resolves only ledgers it stored and whose HMAC verifies.

| attack | result |
|---|---|
| hand-made V1 ledger through `ledger_resolver` | refused ("requires harness-issued session registry") |
| hand-made V1 ledger with a registry | refused |
| hand-made V2 ledger with a forged HMAC | refused |
| genuine ledger presented to a different registry | refused |
| genuine harness receipt (positive control) | validates |

### T2-B3 — CLOSED

The cross-fit, protected-partition and three reader-partition sub-policies must equal canonical derivations from the access policy. "Biological values allowed", "folds chosen later" and "rescue estimability" are each refused with "sub-policy inconsistent".

### T2-B4 — CLOSED

The manifest now requires `normalization_library_contract_sha`, `target_portfolio_code_identity_sha`, `target_portfolio_policy_sha` and `unit_execution_identity_table_sha`. The schema's 21 required fields equal the code's, and the schema is closed.

The per-unit table is closed and non-empty with unique `unit_id`. Code identities are git-blob-verified against bytes; semantic identities are digest-checked with role checks.

Refused:
- an omitted field;
- a role-spoofed top-level object;
- nested spoofs: a library object in the normalization slot, a falsifier object in the metric slot;
- a unit code SHA with no bytes;
- an extra row key;
- an empty table.

## Residual, non-blocking — binding carry-forward

- **R1 (disclosed limitation, made precise).** The session object holds a reference to the registry and to all 104 fit values. Producer code in the same Python process can call `session._harness_registry._finalize_session(...)` with fabricated clean events and obtain an HMAC-attested ledger that validates; the key itself is reachable through name mangling. This is exactly the disclosed "application-level, not OS sandbox" limit. **Before any `HUMAN_EXECUTABLE` / human execution:** the registry, the HMAC key and the reader-fit values must live outside the producer process; finalization must be harness-driven; protected partitions must stay physically absent from producer processes. Record this in the unresolved ledger, blocking human execution.
- **R2.** Nested contract objects are verified for identity (digest + role) only. A vacuous `{"object_role":"METRIC_DEFINITION"}` is accepted. Content schemas for metric, falsifier, reference-producer, normalization/library and TargetPortfolio policy belong to their owning tasks and must be enforced there.
- **R3.** Fixture-authority (`FIXTURE_UNBOUND`) receipts validate with caller-supplied V1 ledgers by design. Every downstream consumer must require `AUTHENTICATED_READER_SPLIT` explicitly.
- **R4.** Attested ledgers live only in the in-memory registry, and the HMAC key is supplied by the caller. Ledger persistence and key custody need a design before receipts are consumed across processes (Task 3/11).
- **R5.** The source-balance caveat is preserved. Fold 4 holds out 1 NPH52 donor, so the five-fold law supports pooled donor-level cross-fit only, not per-fold source-stratified claims.
- **R6.** Carried forward: memoize recursive receipt verification (Task 1 M1) before Task 3.

## Freeze decision

Task 2 may be frozen at exactly `c7dfff1cee608e4a101855d42cf0af08491c2aaf`. Unified Task 3 may begin prospectively, RED-first, carrying R1–R6.

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
