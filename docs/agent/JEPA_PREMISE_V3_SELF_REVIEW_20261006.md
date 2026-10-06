# JEPA premise V3 self-review — 2026-10-06

Role: `SELF_REVIEW__NOT_INDEPENDENT_REVIEW`
Branch reviewed: `design/premise-qualification-contract-v3-20261006`
Reviewed through: `8ec1a20c3b14da1d96223821aae3f62d59c2d940`

## Review questions

- Does any artifact authorize training or Stage-A execution?
- Is any target, representation, dimension, estimand or numeric deciding margin selected?
- Is `cell_state` implicitly privileged?
- Can technology/dataset/donor identity become an unrestricted model shortcut?
- Are biological-evidence and measurement-depth uncertainty collapsed?
- Are biological-support OOD and measurement-regime OOD collapsed?
- Can stable subspace be misreported as stable coordinate semantics?
- Can target-object recoverability be promoted to biological truth?
- Are donor/operator/study/technology transfer collapsed into one pass?
- Can external assets be assumed independent merely because they are external?
- Can exposure/access or same-nucleus/separate-nucleus evidence classes be conflated?
- Can cell count substitute for donor count?
- Can observational multimodal support be promoted to causality?
- Can Stage A exceed the RNA-representation claim level?
- Can fitted diagnostic readouts use deciding held-out units?
- Are the machine-readable source-document pointers real files?
- Does the CLI actually fail closed when validating a supplied corrupted state?

## Findings discovered and repaired during self-review

### SR-1 — machine-readable source-document paths were stale

Four machine-state paths did not match the actual V3 filenames.

Repair: add source-document existence test, observe RED (16 passed / 1 failed naming exactly four paths), then correct only those four paths. Subsequent guard GREEN.

### SR-2 — CLI ignored a supplied state path

The Python validation function was fail-closed, but the command-line entrypoint always read the canonical file and ignored an argument. A caller could therefore believe a supplied state was validated when it was not.

Repair: add CLI mutation test, observe RED (26 passed / 1 failed), then make the CLI accept at most one state path and fail closed on unreadable/invalid JSON. Subsequent guard GREEN.

## Current review result

No additional Critical or Important self-review finding remains after SR-1 and SR-2 repairs.

This is explicitly **not** an independent review and is not merge authority.

PR #220 must remain draft until a separate reviewer attacks the whole branch for hidden scientific flexibility, representation favoritism, observation-channel shortcuts, external-asset overclaim, estimand leakage, and machine/prose mismatch.

## Authority state

`TRAINING=OFF`; Stage A execution not authorized; TEST sealed; Morabito protected; no target winner; no representation winner; no estimand selected; no deciding numeric margin selected.
