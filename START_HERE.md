# START HERE — JEPA PROJECT

Date: 2026-09-18

Status: FULL104_MASKING_CONTROL_CALIBRATION_IMPLEMENTED__GPU_RECEIPT_EXECUTION_PENDING__TERMINAL_OUTCOMES_UNOPENED__TRAINING_OFF

## Current implementation and handoff

Production implementation branch:

impl/v5-full104-masking-redteam2-20260918

Implementation head captured by this handoff:

86692cde7e61fe4beae7fff4070bd376a8090af2

Draft implementation PR: #20

Docs-only handoff branch:

handoff/jepa-v5-full104-calibration-20260918

The handoff branch must remain one documentation commit above the implementation head. Do not mistake the handoff commit for a new scientific implementation.

## Read in this order

1. docs/agent/JEPA_LATEST_HANDOFF_POINTER.json
2. docs/agent/JEPA_NEW_CHAT_HANDOFF_20260918_V5_FULL104_MASKING_CALIBRATION_CURRENT.md
3. docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260918_V5_FULL104_MASKING_CALIBRATION_CURRENT.json
4. docs/agent/JEPA_NEW_CHAT_COMMANDS_20260918_V5_FULL104_MASKING_CALIBRATION.md
5. docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json
6. docs/agent/handoff_artifacts/20260918/V5_FULL104_MASKING_DATA_RESULTS_SCRIPTS_MANIFEST.json
7. docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md
8. docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md
9. docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md

Re-fetch live GitHub heads before any change. Classify repeated work as ALREADY_AUDITED, SUPERSEDED, OPEN, or CHANGED_INPUT_REQUIRES_REQUALIFICATION.

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

The calibration cache is not the FULL104 substrate. Its role is fixed as:

CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1

Terminal masking must consume:

AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1

## Changed-input census that drives current calibration

The corrected read-only census found:

- strict-core measured-zero fraction: 0.832983
- strict-core nonzeros: 13,069,917,135
- strict-core measured zeros: 65,184,935,567
- 17,053 / 17,186 addresses estimable in all four donor-held-out folds
- donor Kish ESS about 42 donor-equivalents from 104 donors

Scientific consequence: strict MEASURED_SCALAR support is required; measured zero remains real measured evidence; the old 15% burden from the 800-address discovery universe cannot be inherited.

The runtime V2 census receipts still have to be regenerated and hash-bound on the GPU machine before they create current authority.

## What is implemented now

The current branch includes:

- authenticated FULL104 streaming masking executor plus canonical reference
- explicit discovery-candidate parameter authority V2
- census V2 receipt/builder chain
- calibration-only cache builder with exact FULL104 source binding
- cache loader/evaluator with all-104-donor closure and full-donor sufficient-stat checks
- target-panel nested capacity ladder 128 -> 256 -> 512 -> 1024
- target-panel authority V3 builder
- current outer-split authority and precision V4 builders
- nonlinear model-capacity authority separated from row-cap calibration
- nonlinear row-cap ladder 64 -> 128 -> 256 -> 512 -> 1024
- nonlinear cache evaluator plus calibration authority V2
- masking decision V2, execution authority V4 and final run-contract V4
- anti-spillover V2 enforcing no placeholder/historical/smaller-run promotion

These are implementation capabilities, not evidence that the real GPU calibration or terminal masking has run.

## What remains open

No target-panel rung is selected yet. No nonlinear row cap is selected. No final run-contract V4 instance is frozen. No terminal 5% masking outcome has been opened. No masking policy is selected. Training remains OFF.

The first new-chat task is focused CI on the exact current implementation head. At handoff time GitHub reports no combined status checks on 86692cde7e61fe4beae7fff4070bd376a8090af2; do not inherit the old code-anchor green status as if it verified the latest 31-commit successor delta.

Also: scripts/agent/v5_full104_masking_gpu_preflight_20260917.ps1 is stale for the current V4/cache-calibrated chain. Refresh it before using it as a final GPU preflight.

## Immediate order

CI exact head -> refresh current GPU preflight -> regenerate census V2 runtime receipts -> build/authenticate calibration-only cache -> target-panel capacity ladder -> target-panel/split/precision authorities -> nonlinear capacity ladder -> nonlinear challenge authority -> bind RNG/current source hashes -> freeze final V4 run contract -> rebuild machine checkpoint -> independent review -> only then terminal FULL104 5% masking

Stop burden escalation at the first fully qualifying rung.

## Hard boundaries

TRAINING_OFF

NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION

NO_PATHOLOGY_DEV_SEALED_OUTCOME_ACCESS_WHILE_DESIGN_OPEN

NO_SMALLER_OR_HISTORICAL_FULL104_SUBSTITUTE

NO_CALIBRATION_CACHE_AS_TERMINAL_INPUT

NO_PLACEHOLDER_HASH_AUTHORITY

NO_POST_OUTCOME_RETUNING

## Do not redo without changed inputs

Do not reopen FULL104 lineage, K2, VALUE_ONLY_256, base estimand, T0/T1/C2 chronology, QID/F1, Stage81A3 scope, Layer-2, target-identity shortcut discovery, Stage-A structural qualification, visibility ablation, same-cell thinning, or streaming/reference parity merely because this is a new chat.
