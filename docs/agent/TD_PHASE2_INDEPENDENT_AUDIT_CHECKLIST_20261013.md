# TD phase-2 independent audit checklist — 2026-10-13

Use only after the single authorized phase-2 adjudication returns.

## Mandatory identity checks

- TD execution commit = `1f474a44a6baabc667dbfda726e0755426c732e7`
- phase-1 evidence commit = `a1aed169be5f4552208128f9d71b2d601a657393`
- package SHA-256 = `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- binding SHA-256 = `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`
- blinded receipt SHA-256 = `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`
- controller archive SHA-256 = `f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328`
- controller manifest raw SHA-256 = `87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9`
- controller semantic commitment = `a3d8ea34339aa06d995d498c2651d4dfd4e1058eec3640a7cd7ea1128efce293`

Any mismatch = STOP.

## Execution checks

- exactly one `adjudicate` invocation;
- V4 runner authenticates blinded-receipt bytes and fit-engine identity before controller read;
- output path was new/write-once;
- adjudication receipt SHA-256 independently recomputed;
- stdout/stderr and environment recorded;
- no real-data TD, target selection, TD60, Stage 4, architecture selection, EMA selection, or training followed the run.

## Scientific interpretation checks

- synthetic adjudication qualifies the TD test only;
- `NOT_ESTIMABLE` is not biological failure;
- a scale-specific failure remains scale-specific;
- source-specific failure remains source-specific;
- aggregate performance cannot rescue a failed required constituent gate;
- no synthetic result directly selects a human biological target.

## Allowed audit outcomes

`PASS_PHASE2_EXECUTION_AND_CUSTODY`

or

`FAIL_PHASE2_EXECUTION_OR_CUSTODY__STOP`

A PASS permits only a separate scientific interpretation of which TD tests are qualified. It does not authorize real TD or training.
