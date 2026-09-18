# START HERE — JEPA PROJECT

Date: 2026-09-18

Status: FULL104_MASKING_HANDOFF_AUTHORITY_REPAIRED__GPU_RUNTIME_RECEIPTS_PENDING__TERMINAL_OUTCOMES_UNOPENED__TRAINING_OFF

## Current implementation and handoff

Implementation branch:

impl/v5-full104-masking-redteam2-20260918

Current implementation/governance head:

d6ef93e274e42e17d78f3fc652b0dfec202036ac

Scientific source/test/data anchor underneath the docs-only governance repair:

86692cde7e61fe4beae7fff4070bd376a8090af2

Draft implementation PR: #20
PR base: impl/v5-full104-masking-redteam-freeze-20260918

Current audited docs-only handoff branch:

handoff/jepa-v5-full104-calibration-audited-20260918

The handoff branch must remain exactly one documentation commit above the implementation/governance head. Do not treat the handoff commit as a scientific implementation change.

The older handoff branch handoff/jepa-v5-full104-calibration-20260918 is superseded because its linked checkpoint state and execution plan were internally stale.

## Read in this order

1. docs/agent/JEPA_LATEST_HANDOFF_POINTER.json
2. docs/agent/JEPA_NEW_CHAT_HANDOFF_20260918_V5_FULL104_MASKING_CALIBRATION_CURRENT.md
3. docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260918_V5_FULL104_MASKING_CALIBRATION_CURRENT.json
4. docs/agent/JEPA_NEW_CHAT_COMMANDS_20260918_V5_FULL104_MASKING_CALIBRATION.md
5. docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json
6. docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md
7. docs/agent/handoff_artifacts/20260918/V5_FULL104_MASKING_DATA_RESULTS_SCRIPTS_MANIFEST.json
8. docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md
9. docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md

Re-fetch live GitHub heads before acting. Classify repeated work as ALREADY_AUDITED, SUPERSEDED, OPEN, or CHANGED_INPUT_REQUIRES_REQUALIFICATION.

## Governance repair completed before this handoff

Implementation-head governance commit d6ef93e274e42e17d78f3fc652b0dfec202036ac fixed:

- CURRENT_WORK_CHECKPOINT_STATE.json: PR #20/base are current; the historical green anchor is explicitly not current-head CI; START_HERE.md is no longer hard-pinned.
- docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md: the September-17 V2 execution plan was replaced by the current V4/cache-calibrated sequence.
- The active plan now explicitly records missing final builders instead of pretending the final freeze is already executable.

Pinned checkpoint authorities are stable implementation-governance files only: AGENTS.md and the active execution plan. A docs-only handoff can therefore update START_HERE without invalidating CURRENT_WORK_CHECKPOINT_STATE.json.

## Scientific objective

Infer biological/cellular state from partial RNA, including query-local state associated with a supplied canonical molecular address.

Do not turn this into hidden-gene scalar reconstruction. Ridge/correlation/nonlinear expression predictors are shortcut diagnostics only.

## Current FULL104 substrate

- 4,553,407 cells
- 104 donors
- 42 operators
- 41,238 addresses
- 17,186 strict common-core addresses
- 8,915 Level-4 blocks
- block-manifest SHA-256: 66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
- GPU Level-4 root: D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/

Calibration-cache role:

CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1

Terminal masking input role:

AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1

## Changed-input census

Corrected strict-core measured-zero frequency: 0.832983.
Core nonzeros: 13,069,917,135.
Core measured zeros: 65,184,935,567.
17,053 / 17,186 strict-core addresses are estimable in all four donor-held-out folds.
Kish ESS is about 42 donor-equivalents from 104 donors.

Runtime census V2 receipts still must be regenerated and hash-bound on the GPU machine. Repository constants are not runtime authority.

## Current immediate boundary

No target-panel rung is selected.
No nonlinear row cap is selected.
No final V4 run-contract instance exists.
No terminal masking outcome has been opened.
No masking policy is selected.
Training remains OFF.

The exact current implementation/governance head d6ef93e274e42e17d78f3fc652b0dfec202036ac has no workflow runs recorded at handoff. Run focused CI first and fail closed on skips. Do not inherit older green status as verification of this head.

scripts/agent/v5_full104_masking_gpu_preflight_20260917.ps1 is stale for the current chain. Refresh/supersede it before final GPU authority or execution.

## Builder gaps that remain real blockers

Before terminal masking, implement/test/review current builders for:

- NonlinearChallengeAuthorityV3. The existing build_full104_nonlinear_challenge_authority_v2_20260918.py is V2 only and is not final authority.
- MaskingRngReplayAuthorityV2.
- MaskingQualificationRunContractV4.

Do not replace these gaps with manual placeholder JSON.

## Hard boundaries

TRAINING_OFF

NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION

NO_PATHOLOGY_DEV_SEALED_OUTCOME_ACCESS_WHILE_DESIGN_OPEN

NO_SMALLER_OR_HISTORICAL_FULL104_SUBSTITUTE

NO_CALIBRATION_CACHE_AS_TERMINAL_INPUT

NO_PLACEHOLDER_HASH_AUTHORITY

NO_POST_OUTCOME_RETUNING

NO_BURDEN_ESCALATION_AFTER_FIRST_FULL_QUALIFICATION
