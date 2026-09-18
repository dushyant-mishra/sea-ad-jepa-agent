# JEPA V5 new-chat commands — 2026-09-18 FULL104 masking calibration

These commands are startup guidance. They do not create scientific authority by themselves.

## A. Re-fetch the live implementation

PowerShell:

cd "D:/Jepa project"
git fetch origin
git rev-parse origin/impl/v5-full104-masking-redteam2-20260918
git log -1 --oneline origin/impl/v5-full104-masking-redteam2-20260918
git status --porcelain

Expected handoff implementation anchor:

86692cde7e61fe4beae7fff4070bd376a8090af2

If the live head differs, classify the delta as CHANGED_INPUT_REQUIRES_REQUALIFICATION before using this handoff as current.

Do not reset, clean, stash or overwrite a dirty worktree.

## B. Read authority before acting

Read in order:

START_HERE.md
docs/agent/JEPA_LATEST_HANDOFF_POINTER.json
docs/agent/JEPA_NEW_CHAT_HANDOFF_20260918_V5_FULL104_MASKING_CALIBRATION_CURRENT.md
docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260918_V5_FULL104_MASKING_CALIBRATION_CURRENT.json
docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json
docs/agent/handoff_artifacts/20260918/V5_FULL104_MASKING_DATA_RESULTS_SCRIPTS_MANIFEST.json
docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md
docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md

## C. First task: focused CI on exact current head

At handoff the current head has no combined status entry. Run the current focused suite from .github/workflows/v5-full104-masking-runner.yml locally and/or trigger the workflow on the exact head. Fail closed on skips.

Do not inherit 8ee5d0a5 green status as verification of this successor delta.

## D. Refresh GPU preflight

scripts/agent/v5_full104_masking_gpu_preflight_20260917.ps1 is stale because it checks the older chain.

Update or supersede it so it validates current V4/cache-calibrated sources, tests, roots and terminal input role.

Do not use the stale script as final execution authority.

## E. GPU Level-4 root

Known root:

D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/

Expected manifest SHA-256:

66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29

## F. Regenerate census V2 runtime receipts

Use the current census receipt machinery, then build census authority V2 with:

python scripts/agent/build_full104_census_authority_v2_20260918.py

Required real-machine inputs include:
- Level-4 root
- current observation-state authority
- real pass1 NPZ
- V2 summary receipt
- V2 split receipt
- V2 target-eligibility receipt
- docs/agent/V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json

Never substitute test fixtures or historical caches.

## G. Build calibration-only cache

Use:

python scripts/agent/build_full104_control_calibration_cache_v1.py

Required inputs:
- authenticated FULL104 Level-4 root
- authenticated 41,238-row canonical registry CSV
- census authority V2
- split receipt
- target-eligibility receipt
- support authority
- new empty output directory

Required cache role:

CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1

Never point terminal masking execution at this cache.

## H. Target-panel capacity ladder

Use:

scripts/agent/evaluate_full104_target_panel_capacity_from_cache_v1.py

Evaluate only the next lawful nested rung:

128 -> 256 -> 512 -> 1024

Exact replay is required. Stop at first qualification.

Then build:

scripts/agent/build_full104_target_panel_authority_v3_20260918.py

## I. Outer split and precision

Use:

scripts/agent/build_full104_outer_split_authority_v1_20260918.py
scripts/agent/build_full104_precision_authority_v4_20260918.py

Both must descend from current runtime receipts and selected target panel.

## J. Nonlinear capacity

Build model-shape-only authority with:

scripts/agent/build_full104_nonlinear_capacity_model_authority_v1_20260918.py

Then run:

scripts/agent/evaluate_full104_nonlinear_capacity_from_cache_v1.py

Ladder:

64 -> 128 -> 256 -> 512 -> 1024

Exact replay, stop at first pass. Do not import historical data, targets, folds, burden, seed or row cap.

## K. Final V4 freeze

Only after target panel, outer split, precision, nonlinear calibration, RNG and exact current source roots exist:

- instantiate and freeze MaskingQualificationRunContractV4
- terminal execution input role must be AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1
- calibration cache may be provenance input but is forbidden as terminal execution input
- rebuild and validate CURRENT_WORK_CHECKPOINT.json on final committed HEAD
- independently verify the package

## L. Only then open terminal masking

Start at 5%.

Do not inspect 10% if 5% fully qualifies. Escalate only after explicit failure.

Masking PASS does not authorize training. Remaining-RNA, measurement robustness, geometry/memorization, runtime provenance and explicit final training authority still follow.

## Never do

- no training
- no D_shared/pathology/DEV/SEALED opening
- no Stage81/T1/discovery-data substitution for FULL104
- no placeholder hashes
- no post-outcome retuning
- no calibration cache as terminal input
- no stale 20260917 GPU preflight as final authority
