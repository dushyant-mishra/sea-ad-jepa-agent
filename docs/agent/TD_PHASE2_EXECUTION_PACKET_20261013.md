# TD phase-2 execution packet — controller-issued 2026-10-13

Authority source: PR #329 `TD_PHASE2_CONTROLLER_ADJUDICATION_AUTHORIZATION_20261013.md`.

Executor role: independent execution only. Do not reinterpret authority. Do not modify TD code, synthetic worlds, controller truth, fit outputs, thresholds, target-selection rules, or downstream training state.

## Exact frozen inputs

- TD checkout: `1f474a44a6baabc667dbfda726e0755426c732e7`
- phase-1 evidence commit: `a1aed169be5f4552208128f9d71b2d601a657393`
- package SHA-256: `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- pre-fit archive SHA-256: `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`
- binding SHA-256: `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`
- frozen V4 receipt SHA-256: `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`
- controller archive SHA-256: `f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328`
- controller archive size: `2028`
- controller manifest raw SHA-256: `87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9`
- controller semantic commitment: `a3d8ea34339aa06d995d498c2651d4dfd4e1058eec3640a7cd7ea1128efce293`
- PR #321 workflow run: `38438433970`
- pre-fit artifact: `11834580081`
- controller artifact: `11833833421`

## Required pre-open checks

1. Fresh detached checkout at the exact TD commit; tracked and ignored worktree clean.
2. Download only the exact certified pre-fit and controller artifacts above.
3. Verify the inner pre-fit/controller archive hashes and sizes before extraction.
4. Extract into a new phase-2-only workspace.
5. Verify the binding and raw controller-manifest hashes above.
6. Copy the frozen phase-1 V4 receipt byte-for-byte from the evidence commit and recompute `e67aace8...`.
7. Confirm `td_relational_successor_disk_runner_v4.py` authenticates the frozen receipt SHA and all eight fit-engine hashes before `_read_controller_json(...)`. Any mismatch is STOP.

## Authorized execution

Run exactly one invocation of:

`python scripts/v5/td_relational_successor_disk_runner_v4.py adjudicate`

with:

- `--repo-root` = exact TD checkout
- `--binding` = authenticated extracted binding
- `--fit-dir` = authenticated extracted `pre_fit/fit_views`
- `--authenticated-package-sha256` = `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- `--blinded-receipt` = frozen V4 receipt
- `--blinded-receipt-sha256` = `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`
- `--controller-manifest` = authenticated extracted controller manifest
- `--output` = a new write-once `TD_RELATIONAL_SUCCESSOR_DISK_ADJUDICATION_V4.json`

Do not rerun on FAIL, NOT_ESTIMABLE, surprising biology, or an inconvenient result. A technical execution failure before a receipt exists is returned to the controller for adjudication; do not improvise a repair.

## Mandatory return package

Return and durably freeze:

1. exact checkout SHA and clean-status records before/after;
2. all input hashes/sizes and artifact IDs;
3. Python and NumPy versions;
4. exact command and start/end timestamps;
5. stdout and stderr;
6. exact adjudication receipt bytes;
7. independently recomputed receipt SHA-256;
8. qualification status and readiness status exactly as emitted;
9. confirmation that output authority flags remain false for real TD, target selection, representation selection, TD60, Stage 4, architecture/EMA selection, multimodal training, JEPA training, and continuation;
10. no downstream execution.

Terminal after successful execution:

`PHASE2_ADJUDICATION_COMPLETE__RECEIPT_FROZEN__STOP_FOR_INDEPENDENT_AUDIT`

## Scientific interpretation firewall

This experiment qualifies the TD test against sealed known truth. It does not select a human biological target. `NOT_ESTIMABLE` is not biological failure; a scale/source-specific FAIL remains scoped to that exact claim; aggregate performance cannot rescue a failed required gate.
