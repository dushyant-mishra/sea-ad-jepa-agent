# Event98 — Macha independent verdict on Event96: V5 runtime path, entrypoint and what is actually missing (NO EXECUTION)

**Date:** 2026-11-05 (US Eastern).

**Author:** Macha.

**Method:** static Git source and blob checks only. Nothing was imported, executed or trained.

**Branches:** append-only on #322, mirrored byte-identically on #460. Events 1–97 are unchanged, including Event68, Event90 and Event96.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Verdict on Event96

**ACCEPT_SCOPED, with two corrections.** This extends Event97, whose verdict covered static identity of five files only.

| Question | Finding |
|---|---|
| Historical path `src/sea_ad_jepa/v5/canonical_runtime.py` | **Absent** at PR224 `9d00684e`, PR525 `b493efc3`, PR548 `cde03f73`, #570 `0e2deffa`, #579 `676c991f`, integration #582 `e71d864b` and `main`. The path in Event68 is `LEGACY_PATH_INVALID`, as Sol stated. |
| Runtime entrypoint | `run_guarded_inactive_reference_update` in `src/sea_ad_jepa/v5/inactive_guarded_update_v1.py`. It requires `PrefreezeMechanicalAuthorityV1` and returns `training_authorized=False` and `execution_authorized=False`. Its in-repository callers are `_ema_bound_runtime_proof_impl_v1.py` and `tests/test_teacher_student_v5_inactive_update_reference.py`. |
| Is any **code** missing? | **No**, but **the canonical runtime is 12 files, not 5** (correction 1). |
| Is any **capability** missing? | **Yes: there is no multi-update V5 execution loop.** The "40-step" claim in Event68 belongs to V4 (correction 2). |

## Correction 1: PR224 defines its own canonical runtime file set

`src/sea_ad_jepa/v5/_inactive_checkpoint_binding_impl_v1.py` at PR224 defines `CANONICAL_RUNTIME_SOURCE_FILES`. The checkpoint binding hashes this set, so it is the authoritative definition.

| File | Blob (PR224 = PR525 = PR548 = #582) | `main` |
|---|---|---|
| v5/inactive_update_reference.py | `ab266faa` | **`3dc61b62` (older; contains `optimizer.step()`)** |
| v5/inactive_guarded_update_v1.py | `59647eb0` | absent |
| v5/prefreeze_runtime_authority.py | `41a6ebde` | absent |
| v5/inactive_checkpoint_binding_v1.py | `8d7ad56a` | absent |
| v5/ema_presentation_v1.py | `6f4442e2` | absent |
| v5/ema_bound_runtime_proof_v1.py | `b6bf21cc` | absent |
| v5/ema_persisted_continuation_v2.py | `865f6991` | absent |
| v5/data_first_geometry.py | `93b08f49` | same |
| v5/keyed_dropout_prototype_v2.py | `0fd06ae0` | same |
| v5/keyed_rng_contract_v2.py | `dcd4abf9` | same |
| v4/ipb_jepa.py | `3bd9d601` | same |
| v4/gene_tokenizer.py | `0fd28313` | same |
| v5/_inactive_checkpoint_binding_impl_v1.py (private) | `5be5177a` | absent |
| v5/_ema_bound_runtime_proof_impl_v1.py (private) | `fac5f7c7` | absent |
| v5/\_\_init\_\_.py | `5b80f3e9` | `255e6599` |

All 15 are **byte-identical across PR224, PR525, PR548 and the current integration #582**, so the guarded runtime survives intact in the active lineage.

Sol's Event96 table lists 5 of them. Any future binding, checkpoint or integration must use the full 12-file set plus the two private implementations, never the 5-file subset.

`main` lacks six of the canonical files and carries the older, unguarded reference module. **Never take the runtime from `main`.**

## Correction 2: the "40-step" claim is V4, not V5

Event68 row 101 attributes "Original **40-step bounded synthetic** V5 optimizer/EMA/checkpoint already executed" to the `canonical_runtime.py` row. At PR224:
- **The V5 runtime is a one-update guarded rehearsal.** Its tests run update 0 and check continuation to `next_update_index=1`. No V5 test or script loops over updates.
- **The 40 steps belong to V4.** They come from `scripts/v4/healthy_teacher_qualification_runner_v1.py` (`valid_steps=40`, "Mechanics-only u0->u40 healthy-teacher qualification runner"), `tests/test_teacher_student_unified_runtime_v1.py` and `docs/agent/HEALTHY_TEACHER_TRAINING_CONTRACT_V1_20260907.json`. That runner requires a separate explicit u0→u40 execution authority. PR224 and #226 documents say the package contains no such authority and is not permission to execute.
- **No execution record found.** My keyword searches of `docs/agent` and `results` at PR224 and #226 found no u40 execution receipt or result. That was a keyword-filtered search, so this is **not** a claim that no 40-step run ever happened anywhere. It means only that the cited refs do not show a V5 one.

**Consequence.** Nothing needs rebuilding: the guarded one-update V5 runtime exists and is preserved. But a multi-update V5 driver does not exist. The future driver must:
- call `begin_attempt` before each guarded update;
- use the integrated journal for structured bytes and probes;
- carry #571 gradient, Adam and EMA telemetry.

That driver is genuinely new engineering. Running it, even synthetically for RT1–RT8, needs **separate owner authorization**. No agent should assume a ready, already-executed 40-step V5 trainer.

## Not done

- No module was imported.
- No forward or backward pass, optimizer step or EMA update.
- No test was run for this event.
- Event68, Event90 and Event96 text is unchanged; this is an additive correction.
