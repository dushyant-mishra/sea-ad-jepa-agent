# TD phase-2 scale-order repair — frozen-receipt reader preflight (read-only)

**Terminal:** `GREEN_REPAIR_HEAD_7659030c__FROZEN_RECEIPT_e67aace8_ACCEPTED_LOSSLESS__NEGATIVE_CONTROL_1f474a44_REPRODUCES_FAILURE__CONTROLLER_NOT_ACCESSED__PHASE2_NOT_RUN__STOP`

Packaging note: this report and `SOURCE_SHA256.txt` were assembled after the two preflight runs. The JSON outputs and run records under `record/` are the bytes the runs wrote. `tool/` holds a byte-identical copy of the script that ran from the session scratch directory (SHA-256 below).

## 1. Repaired head

PR #330, branch `fix/td-phase2-scale-grid-order-20261013`, head `7659030cd2fc9a2662c67a9bf4d23e0e8f3f1606`.

| commit | content |
|---|---|
| `19b527a9` | RED regression (controller-authored, unchanged) |
| `1c383b92` | `_profile`: accept the exact `G.SCALE_LABELS` key set with exact cardinality; reconstruction stays in `G.SCALE_LABELS` order |
| `f09dfe74` | fail-closed regressions (missing / extra / substituted / empty / non-mapping) and a full disk round-trip through `_write_json_durable` → `_read_json` |
| `7659030c` | CI: add the regression file to the V4 custody step (test-only; can be dropped if not wanted) |

Diff vs frozen TD head `1f474a44`: 3 files (`record/HEAD_DIFF_1f474a44_7659030c.txt`). All 8 V4 `FIT_ENGINE_FILES` and all `readiness_v2` gate-bound executor/decision files are blob-identical, so the fit-engine identity bound in `e67aace8` and the gate binding are unchanged.

## 2. Tests

| scope | evidence | result |
|---|---|---|
| RED test at `19b527a9` | local | FAIL `frozen profile scale grid mismatch` (as expected) |
| regression file, original reader | local | 2 RED tests fail; 6 fail-closed/accept tests pass |
| regression file, repaired reader | local | 8 passed |
| mutants: length-only check / no check | local | killed by `substituted` / by `missing, extra, substituted, empty` |
| workflow-equivalent suite, Python 3.11.15 (`sea-ad-jepa-v3`) | local | compile OK; custody 14 + 8; frozen V2 57; replay spillover 16 + 1 skip |
| `td-relational-blind-custody-v4-ci.yml`, run `38461198641` @ `7659030c` | **CI** | success: custody 22, frozen V2 57, spillover 16 + 1 skip |

The skip is `test_build_td_relational_replay_manifest.py:45`, which needs external replay authorities. It does not depend on this repair.

Why the defect escaped: `test_td_relational_successor_v3_custody.py::test_frozen_blinded_json_roundtrips_back_to_exact_receipt_shape` built the document with in-memory `_jsonable(fit)` and never passed through `sort_keys=True` serialization.

## 3. Frozen-receipt reader preflight

The tool calls only the phase-2 pre-controller path `D4.authenticate_blinded_phase_inputs`, which never receives a controller path. A `sys.addaudithook` logs every `open` / `listdir` / `scandir`, and `V3._read_controller_json` is replaced with a sentinel that aborts if called. Both runs used clean detached worktrees (0 status lines, including ignored files, before and after), interpreter `sea-ad-jepa-v3` Python 3.11.15 run as `-I -B`, and identical inputs:

| input | SHA-256 | pre = post |
|---|---|---|
| binding `TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json` | `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44` | ✓ |
| authenticated package root | `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115` | — |
| frozen V4 blinded receipt | `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684` | ✓ |

| | repaired `7659030c` | negative control `1f474a44` |
|---|---|---|
| status | `READER_ACCEPTED` (exit 0) | `READER_REFUSED` (exit 1): `DiskRunnerV4Error: frozen profile scale grid mismatch` (cause `DiskRunnerV3Error`) |
| challenges / primary / control profiles | 9 / 9 / 45 (5 per challenge) | — |
| on-disk `scale_results` key order (all 54) | `1/2,1/3,1/4,1/6,1/8` | same bytes |
| reconstructed order (all 54) | `1/8,1/6,1/4,1/3,1/2` = `G.SCALE_LABELS` | — |
| fit-engine identity (8 files) | matches the receipt binding | — |
| lossless check: re-serialized parsed receipt | byte-identical, SHA `e67aace8…` | — |
| fit-receipt authority | all 5 keys `false` | — |
| controller dir accessed / sentinel fired | no / no | no / no |
| inputs unchanged | yes | yes |

Non-stdlib paths the process touched (audit hook): the binding, the receipt, and that head's own `scripts/v5` sources. The `.pyc` lookups were failed reads; the tree was still clean afterwards. Forbidden directory: `D:/jepa_td_synthetic_phase2_20261013/phase2_controller`.

## 4. Boundary

Phase 1 was not rerun. Phase 2 (`adjudicate`) was not run. The controller manifest and realization receipt were not opened, listed or hashed by this work. No receipt, package, binding or controller bytes were modified. No authority was exercised: qualification, target selection, TD60, stage 4 and training all remain off. A fresh one-shot phase-2 authorization bound to `7659030c` (or to a head the controller selects) is required before any adjudication.

STOP.
