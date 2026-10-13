# TD synthetic phase-2 adjudication: single invocation failed technically before any receipt

**Date:** 2026-10-13.

**Authority:** PR #329 @ `cde596530d126795ab9421416af58f144b2ab41e`. The governing documents are
`TD_PHASE2_CONTROLLER_AUTHORIZATION_20261013.md` and `TD_PHASE2_EXECUTION_PACKET_20261013.md`, plus controller
comment `6153767837`.

**Terminal:** `PHASE2_ADJUDICATE_TECHNICAL_FAILURE_BEFORE_RECEIPT__FROZEN_PROFILE_SCALE_GRID_KEY_ORDER_DEFECT__CONTROLLER_MANIFEST_NOT_READ__NO_RECEIPT__NO_RERUN__RETURNED_TO_CONTROLLER`

Per the packet, a technical execution failure before a receipt exists goes back to the controller. I did not repair
anything, did not rerun, and did not improvise. The authorized invocation has been used.

## Mandatory return package

**1. Checkout.** `1f474a44a6baabc667dbfda726e0755426c732e7`, a fresh detached worktree at
`D:/jepa_wt_td_synth_phase2_1f474a44`. Tracked, untracked and ignored status was clean before and after (0 lines
each). Records: `record/CHECKOUT_PRE.txt`, `record/POST_RUN_STATE.txt`.

**2. Inputs.** Both pre-open verifications passed before extraction. Records: `record/ARCHIVE_VERIFICATION.txt`,
`record/INPUT_VERIFICATION.txt`.

| item | value |
|---|---|
| run | `38438433970` |
| pre-fit artifact | `11834580081`, zip `97c89d0e…` (identical to phase 1) |
| pre-fit archive | `ba0fa56a…`, **7,018,400 bytes**: MATCH |
| controller artifact | `11833833421`, zip `8e796017…` |
| controller archive | `f554e2a9…`, **2,028 bytes**: MATCH |
| binding | `ab29bacd…`: MATCH |
| package root | `0977c30f…` |
| fit views | 9 NPZ, each named by its own content SHA |
| controller manifest (raw) | `87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9`: MATCH |
| frozen V4 receipt | byte copy from evidence `a1aed169`, `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684` (328,351 bytes): MATCH |

The extracted controller tree holds `controller_manifest.json`, `controller_realization_receipt.json` and
`metadata/td_interface_identity.json`. I hashed them but did not read them, and they are not committed here.

**3. Versions.** Python 3.11.15, NumPy 2.4.6 (`sea-ad-jepa-v3`, the same environment as phase 1). Full freeze:
`record/PHASE2_ENVIRONMENT.txt`.

**4. Command.** Run once, with `PYTHONDONTWRITEBYTECODE=1 -B`; full text in `record/ADJUDICATE_RUN_RECORD.txt`.
Start 19:49 UTC; end 2026-10-13T19:49:10.874Z; exit 1.

```
python scripts/v5/td_relational_successor_disk_runner_v4.py adjudicate --repo-root D:/jepa_wt_td_synth_phase2_1f474a44 \
  --binding <ws>/phase2_package/pre_fit/TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json --fit-dir <ws>/phase2_package/pre_fit/fit_views \
  --authenticated-package-sha256 0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115 \
  --blinded-receipt <ws>/frozen_receipt/TD_RELATIONAL_SUCCESSOR_BLINDED_FIT_RECEIPT_V4.json \
  --blinded-receipt-sha256 e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684 \
  --controller-manifest <ws>/phase2_controller/controller/controller_manifest.json \
  --output <ws>/output/TD_RELATIONAL_SUCCESSOR_DISK_ADJUDICATION_V4.json      (<ws> = D:/jepa_td_synthetic_phase2_20261013)
```

**5. Output streams.** stdout was empty. stderr ends in
`DiskRunnerV4Error: frozen profile scale grid mismatch`; the full traceback is in `record/ADJUDICATE_STDERR.txt`.

**6–7. Adjudication receipt.** **None exists.** The output directory is empty, with no partial `.tmp`. There is
nothing to hash.

**8. Statuses.** **Not emitted.** There is no qualification status and no readiness status.

**9. Authority flags.** No output exists. Every downstream authority (real TD, target selection, representation
selection, TD60, Stage 4, architecture/EMA selection, multimodal training, JEPA training, continuation) remains
unauthorized and unexercised.

**10. Downstream execution.** None.

## Pre-open check 7 and the controller boundary

I confirmed by reading the code at `1f474a44` that `adjudicate_frozen_blinded_phase` checks the inputs before
reading any controller file. It:
1. validates the binding and package;
2. checks the blinded receipt's SHA-256 against the expected value;
3. recomputes all eight fit-engine hashes and requires the receipt to match;
4. only then calls `V3._read_controller_json`.

The failure was raised inside step 3's receipt reconstruction (`authenticate_blinded_phase_inputs`), **before the
controller read**. So the runner never read controller truth. I did not read it either; the controller files were
only hashed.

## Diagnosis (read-only; `record/FAILURE_DIAGNOSIS.md`)

**The defect is deterministic.** `V3._profile` (`td_relational_successor_disk_runner_v3.py`, line 199) requires
`tuple(scale_results) == G.SCALE_LABELS`.

| | key order |
|---|---|
| `G.SCALE_LABELS` (frozen) | `('1/8', '1/6', '1/4', '1/3', '1/2')` |
| receipt on disk | `('1/2', '1/3', '1/4', '1/6', '1/8')` |

The blinded-receipt writer `V3._write_json_durable` uses `json.dumps(..., sort_keys=True)`. Every `scale_results`
mapping therefore lands on disk in lexical order. The key **set** is identical, and all 9 profiles and 45 control
profiles share the sorted order. So any disk-written V4 blinded receipt fails this order check. The phase-1 receipt
bytes and the package are intact.

**For the controller to decide (not acted on):**
- `td_relational_successor_disk_runner_v3.py` is **not** among the V4 `FIT_ENGINE_FILES`.
- So a reader-side repair would not change the fit-engine identity recorded in receipt `e67aace8`. For example, the
  check could require set equality with exactly five labels; the function already rebuilds `scale_results` in frozen
  order.
- The frozen phase-1 receipt could therefore stay the adjudication input.
- A repair would still mean a new TD head and a new phase-2 authority.

## Evidence in this directory

All copies are byte-exact; see `SOURCE_SHA256.txt`.

**`record/`:**
- `CHECKOUT_PRE.txt`, `ARCHIVE_VERIFICATION.txt`, `INPUT_VERIFICATION.txt`, `PHASE2_ENVIRONMENT.txt`;
- `ADJUDICATE_RUN_RECORD.txt`, `ADJUDICATE_STDOUT.txt` (empty), `ADJUDICATE_STDERR.txt`;
- `POST_RUN_STATE.txt`, `FAILURE_DIAGNOSIS.md`.

**`input/`:** the frozen V4 receipt as used.

**Not committed:** the controller files and transports. They remain in the phase-2 workspace
`D:/jepa_td_synthetic_phase2_20261013/`, identified by the hashes above.

STOP. Returned to the controller.
