# G7 #476 E3-to-V3 composed fixture path (2026-10-29)

**Scope:** synthetic mechanics only, incremental interface repair. No biological qualification and no source attestation.

Upstream exact source: ChatGPT #497 `a8ad4111906a6de8b3faa7292b432ba934df3499`; source review #476 `26031df25b51087f2f3ec35a88eef2919d794c68`; immutable Macha independent review #482 `58baa4f912c791866c1aae31eab797da9dca588a`. This work **adds** a new integration path without modifying the historical independent tests or V3 decision implementation.

## Contract

`adjudicate_fixture_g7_e3_v3_composed` in `scripts/v5/td_real_g7_e3_v3_composed_fixture.py`:
1. Captures all ten caller-controlled inputs as one exact built-in, immutable-in-transaction snapshot, rejecting subclasses before Python payload comparison. External in-memory inputs can mutate later, but are not reread.
2. Calls the already-reviewed E3 content binder on the snapshot. The binder checks full measured observations against level-rights content, frozen pins and claimed support counts.
3. Recomputes the canonical deciding-row digest over the same snapshot to ensure the V3 reducer sees exactly the binder's validated rows. Requires reference input identity to match.
4. Invokes the unchanged V3 decision algorithm. Reports a **mechanics-only** V3 status, with no donor contrasts and explicit false source/issuer/target/training flags.

The old `adjudicate_g7_terminal_v3` remains directly callable to preserve historical fixtures. Its direct invocation **does not** satisfy the new bound-content integration path. A future production orchestrator must be audited to call only the composed entry before any qualified G7 decision.

## Required REDs not repaired

- **R1:** opaque `atom_id` does not independently prove unique physical molecules/measurements. Aliases/read-depth splits remain hostile. Original R1 tests still RED.
- **R1D:** specimen/pseudodonor IDs can be manufactured as apparently independent donors. The new entry deliberately cannot authenticate them.
- **R2:** physical `library_size`, offset/scaled pooled depth and source-feature completeness are still unqualified. D1/D2 requires a separate prospective versioned decision.
- **Other source/issuer:** the fixture `decision_qualification` and `reference_artifact` may be self-pinned; a mechanical PASS is not an independently validated truth target or real biology.
- **Old direct V3:** remains a potential unsafe bypass if a caller wrongly treats that method as authority; it is historical interface only and not endorsed as the qualified integration.

Never change the V1 `library_size` meaning to D1. Do not override known RED review tests for a green number. Exact CI job receipts and independent reviews must be recorded before incremental acceptance.

**Standing authority:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
