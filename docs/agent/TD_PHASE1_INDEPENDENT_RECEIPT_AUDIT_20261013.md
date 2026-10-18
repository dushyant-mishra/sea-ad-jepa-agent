# TD phase-1 independent receipt audit — 2026-10-13

Status: `STRUCTURAL_AUDIT_PASS__CONTROLLER_REMAINS_CLOSED__PHASE2_NOT_AUTHORIZED_BY_THIS_DOCUMENT`

This audit checks the frozen phase-1 V4 blinded-fit receipt from Macha without using controller truth and without interpreting biological output values.

## Frozen evidence

- evidence commit: `a1aed169be5f4552208128f9d71b2d601a657393`
- TD execution commit: `1f474a44a6baabc667dbfda726e0755426c732e7`
- package SHA-256: `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- pre-fit archive SHA-256: `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`
- binding SHA-256: `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`
- blinded receipt SHA-256: `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`

## Independent checks

1. The evidence commit exists and records a single phase-1 execution with terminal `PHASE1_BLINDED_FIT_COMPLETE__V4_RECEIPT_FROZEN__CONTROLLER_UNOPENED__STOP_FOR_INDEPENDENT_RECEIPT_AUDIT`.
2. Pre-run and post-run records bind the checkout to exact TD commit `1f474a44...` and record an empty tracked/ignored worktree.
3. The phase-1 inventory contains exactly the authenticated pre-fit transport, binding, package-root record, nine SHA-named NPZ fit views, preflight/blinded receipts and execution records. It records zero files matching the controller archive SHA, zero matching its byte size, zero controller-like names, and no `adjudicate` invocation.
4. Runner stdout records blinded receipt SHA `e67aace8...`; the evidence byte manifest records the same SHA for the committed receipt.
5. The frozen structural audit records V4 schema, package binding, nine opaque profile/control containers, all authority flags false and `controller_truth_opened=false`.
6. The receipt fit-engine identity contains exactly the eight `FIT_ENGINE_FILES` hard-coded by `td_relational_successor_disk_runner_v4.py`.
7. Every receipt engine digest equals the exact predeclared engine digest in PR #320 external-review closure comment `6151299345`.
8. V4 phase-2 code authenticates the expected blinded-receipt SHA and recomputes/validates the exact fit-engine identity before `_read_controller_json(...)`; controller reading occurs only after those checks.

## Environment disclosure

Execution used Python 3.11.15 and NumPy 2.4.6 in the `sea-ad-jepa-v3` environment rather than a newly locked phase-1 environment. The phase-1 authority/certification did not specify a locked NumPy version; CI itself used Python 3.11 with NumPy unpinned. Therefore this is not a contract violation. It is retained as a reproducibility caveat and must remain attached to the receipt. No rerun is authorized or recommended from this audit alone.

The first extraction failed only to restore archive mtimes on Windows. The directory was discarded, re-extracted with mtime restoration disabled, and file bytes were subsequently hash-verified. This is not a content-integrity failure.

The concurrent V79 campaign is disclosed. Phase 1 is a deterministic CPU NumPy computation on authenticated bytes; no shared files or controller material were used. The concurrency disclosure remains part of provenance but is not by itself evidence of receipt corruption.

## Decision

`PASS_PHASE1_RECEIPT_STRUCTURE_AND_CUSTODY__SAFE_TO_CONSIDER_SEPARATE_PHASE2_AUTHORIZATION`

This decision does **not** open controller truth and does **not** authorize `adjudicate`, real TD, target selection, TD60, Stage4 or training. A separate explicit phase-2 authority must bind the exact frozen receipt SHA above, exact TD commit and controller identities before the controller archive may enter custody.
