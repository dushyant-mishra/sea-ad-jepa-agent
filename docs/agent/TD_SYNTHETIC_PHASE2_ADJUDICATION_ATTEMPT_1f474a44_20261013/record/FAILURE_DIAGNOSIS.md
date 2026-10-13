# Phase-2 adjudicate: technical failure before any receipt (read-only diagnosis; no repair, no rerun)

Invocation (exactly one): exit 1 at 19:49:10Z. stdout empty. stderr: `DiskRunnerV4Error: frozen profile scale grid mismatch`.

Call path: `adjudicate_frozen_blinded_phase` -> `authenticate_blinded_phase_inputs` -> `_fit_receipt_from_v4_document`
-> `V3._fit_receipt_from_document` -> `V3._profile` (disk_runner_v3.py line 199):
`if not isinstance(scales, Mapping) or tuple(scales) != G.SCALE_LABELS: raise DiskRunnerV3Error("frozen profile scale grid mismatch")`.
This is before `V3._read_controller_json(...)`. The controller manifest was never read by the runner.

Cause (deterministic round-trip defect):
- `G.SCALE_LABELS` = ('1/8', '1/6', '1/4', '1/3', '1/2') (frozen order).
- The blinded-receipt writer `V3._write_json_durable` uses `json.dumps(..., sort_keys=True)`, so every `scale_results`
  mapping is written in lexical key order ('1/2', '1/3', '1/4', '1/6', '1/8').
- The frozen V4 receipt e67aace8 (byte-identical copy from evidence a1aed169) has exactly that sorted order in all
  9 profiles and 45 control profiles; the key SET equals `G.SCALE_LABELS`.
- `_profile` compares key ORDER, so any blinded receipt written to disk by this code fails to re-authenticate.
  The receipt bytes and package are intact; the reader's order check is incompatible with the writer's sort_keys.

Relevant for the controller (not acted on):
- `V3._profile` is in `scripts/v5/td_relational_successor_disk_runner_v3.py`, which is NOT in the V4
  `FIT_ENGINE_FILES` list. A reader-side repair (e.g. require set equality and exactly five labels; the function
  already rebuilds `scale_results` in frozen `G.SCALE_LABELS` order) would not change the fit-engine identity bound
  in receipt e67aace8, so the frozen phase-1 receipt could remain the adjudication input. Any repair, new TD head,
  and new phase-2 authority are controller decisions.
- CI evidently never re-read a disk-written V4 receipt through `_profile`.
