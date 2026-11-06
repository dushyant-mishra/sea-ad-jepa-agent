# TD phase-2 controller adjudication authorization — 2026-10-13

Status: `AUTHORIZED_PHASE2_ONLY__ONE_EXECUTION__FREEZE_AND_STOP`

Phase 2 is authorized only to determine whether the frozen TD machinery correctly adjudicates the sealed known-truth synthetic cases. This qualifies the TD test, not a biological target.

Exact frozen bindings:
- TD execution commit: `1f474a44a6baabc667dbfda726e0755426c732e7`
- phase-1 evidence commit: `a1aed169be5f4552208128f9d71b2d601a657393`
- package SHA-256: `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- pre-fit archive SHA-256: `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`
- binding SHA-256: `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`
- blinded receipt SHA-256: `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`
- controller archive SHA-256: `f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328`
- controller archive size: `2028` bytes
- controller manifest raw SHA-256: `87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9`
- controller semantic commitment SHA-256: `a3d8ea34339aa06d995d498c2651d4dfd4e1058eec3640a7cd7ea1128efce293`

Before controller truth is opened, verify the exact TD checkout, blinded receipt hash, package identity, controller transport identities, and that the V4 runner authenticates the receipt and fit-engine identity before controller read. Any mismatch is a STOP.

Authorized action: exactly one V4 `adjudicate` invocation. Freeze the adjudication receipt, compute its SHA-256, record environment/stdout, then STOP for independent audit.

Only `controller_adjudication_authorized = true`. Real-data TD, target selection, representation selection, TD60, Stage 4, architecture/EMA selection, multimodal training, JEPA training, and continuation remain unauthorized.

Synthetic PASS qualifies the tested TD behavior only; it does not select a human biological target. FAIL/NOT_ESTIMABLE remain scoped to the exact test.

Phase-1 provenance caveats remain attached: Python 3.11.15 / NumPy 2.4.6, discarded Windows mtime-failed extraction followed by hash-verified extraction, and separate concurrent V79 work.

Terminal: `AUTHORIZED_PHASE2_ONLY__EXECUTE_ONCE__FREEZE_RECEIPT__STOP_FOR_INDEPENDENT_AUDIT`
