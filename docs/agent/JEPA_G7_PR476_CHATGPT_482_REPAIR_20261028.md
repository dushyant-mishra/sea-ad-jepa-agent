# ChatGPT repair of PR #476 against immutable Macha #482 — October 28, 2026

**Repair base:** Macha #482 exact head `58baa4f912c791866c1aae31eab797da9dca588a`, reviewing #476 exact head `26031df25b51087f2f3ec35a88eef2919d794c68`.

**Scope:** fixture mechanics only. This does not authenticate physical atoms, donor/specimen identity, normalization provenance, source issuers, known truth, or human G7 execution.

## Repairs

### Exact-type snapshot dispatch

The G7 strict JSON snapshot now uses type identity for bool/int/str instead of tuple-membership comparison. The same defensive identity rule is applied to required-source containers and terminal displacement numeric dispatch. Caller payload metaclasses can no longer choose an exception through these routes.

### Reviewed bind -> snapshot -> decide composition

A new fixture-only entry point, `adjudicate_fixture_g7_terminal_v3_bound`, snapshots every caller-controlled binder and V3 decision input before use, runs `bind_g7_terminal_inputs_e3`, recomputes and verifies the exact deciding-row digest, then calls the unchanged historical V3 reducer on those same snapshotted rows.

The historical `adjudicate_g7_terminal_v3` decision law is not modified. Direct V3 remains a lower-level primitive; only the new composed entry point claims that binder validation was consumed.

## Preserved blockers

- R1 physical atom/unit identity remains unauthenticated.
- R1D donor/specimen identity remains unauthenticated.
- R2 q-excluded normalization provenance remains unauthenticated.
- Existing external hostile RED cases for those source facts are not relaxed.
- A content hash is still data binding, not source authentication.
- No same-code-path, human G7, target-selection, representation-selection, Stage4 or training authority is added.

**Forward authorization:** NONE.

Standing stop: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
