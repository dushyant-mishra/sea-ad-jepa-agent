# JEPA V5 new-chat commands — audited FULL104 masking-calibration takeover

Date: 2026-09-18

These are execution templates, not scientific authority by themselves. Replace every <REQUIRED_...> placeholder with a real current-machine path before running anything. Never replace a missing current artifact with a historical or smaller-run file.

## A. Re-fetch live GitHub state first

PowerShell:

    cd "D:/Jepa project"
    git fetch origin
    git rev-parse origin/impl/v5-full104-masking-redteam2-20260918
    git log -1 --oneline origin/impl/v5-full104-masking-redteam2-20260918
    git status --porcelain

Expected implementation/governance head at this handoff:

    d6ef93e274e42e17d78f3fc652b0dfec202036ac

Scientific source/test/data anchor underneath the governance-only repair:

    86692cde7e61fe4beae7fff4070bd376a8090af2

PR #20 must still have head impl/v5-full104-masking-redteam2-20260918 and base impl/v5-full104-masking-redteam-freeze-20260918.

At the final authority-package audit, PR #20 was OPEN + DRAFT with GitHub mergeable_state=dirty. Re-fetch that state. Do not merge, rebase, retarget, or resolve PR conflicts as housekeeping; the implementation branch is the takeover authority.

If source/test/data bytes changed, classify the delta as CHANGED_INPUT_REQUIRES_REQUALIFICATION. Do not reset, clean, stash, rewrite history, or overwrite user changes.

## B. Read authority in order

    START_HERE.md
    docs/agent/JEPA_LATEST_HANDOFF_POINTER.json
    docs/agent/JEPA_NEW_CHAT_HANDOFF_20260918_V5_FULL104_MASKING_CALIBRATION_CURRENT.md
    docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260918_V5_FULL104_MASKING_CALIBRATION_CURRENT.json
    docs/agent/JEPA_NEW_CHAT_COMMANDS_20260918_V5_FULL104_MASKING_CALIBRATION.md
    docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json
    docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md
    docs/agent/handoff_artifacts/20260918/V5_FULL104_MASKING_DATA_RESULTS_SCRIPTS_MANIFEST.json
    docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md
    docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md

Do not use the superseded handoff branches handoff/jepa-v5-full104-calibration-20260918 or handoff/jepa-v5-full104-calibration-audited-20260918 as current authority.

## C. First task: exact-head CI

The exact current head has no workflow runs recorded at handoff.

Re-fetch .github/workflows/v5-full104-masking-runner.yml from the exact live head and run exactly its focused test list, including its fail-on-skips step. Do not silently shorten the suite. Also re-run the Stage-A spillover and runtime-closure focused suites if their workflow paths changed in the current delta.

Any skip or new failure is a STOP.

Do not cite historical 8ee5d0a5 green runs as verification of the current head.

## D. Refresh the GPU preflight before heavy execution

Do not use this as final authority:

    scripts/agent/v5_full104_masking_gpu_preflight_20260917.ps1

It is stale for the current cache-calibrated V4 chain.

Create or supersede it with a 20260918/current successor that checks at minimum:

- live branch/head and clean isolated worktree
- current checkpoint state and active execution plan
- FULL104 manifest SHA
- canonical registry SHA
- current census/support/split/eligibility roots
- calibration-cache role is calibration-only
- terminal executor role is authenticated FULL104 Level-4 stream
- current parameter/target-panel/precision/nonlinear/RNG/run-contract source hashes
- anti-spillover V2
- fail-on-skips focused tests
- no Stage81/T1/discovery matrix/placeholder root as current FULL104 input

Behavior-test the preflight before using it.

## E. Define real GPU-machine paths

PowerShell template:

    $REPO = "D:/Jepa project"
    $L4 = "D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4"
    $RUN = "<REQUIRED_NEW_EMPTY_RUNTIME_OUTPUT_DIRECTORY>"
    $PASS1 = "<REQUIRED_REAL_FULL104_PASS1_NPZ>"
    $OBS = "<REQUIRED_CURRENT_OBSERVATION_STATE_AUTHORITY_FILE>"
    $REGISTRY = "<REQUIRED_AUTHENTICATED_41238_ROW_CANONICAL_REGISTRY_CSV>"
    $SUPPORT = "$REPO/docs/agent/V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json"
    $REGISTRY_AUTH = "$REPO/docs/agent/V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_20260916.json"
    $WORKERS = <REQUIRED_POSITIVE_INTEGER>

Do not choose a RUN directory containing Stage81, T1, discovery, ridge8 spike, or any historical-cache path.

Expected Level-4 manifest SHA-256:

    66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29

Expected canonical registry SHA-256:

    7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd

## F. Build the explicit pre-FULL104 confirmation-parameter authority

    python scripts/agent/build_full104_masking_parameters_authority_v2_20260918.py --repo "$REPO" --out "$RUN/masking_parameters_authority_v2.json"

This re-authorizes the frozen discovery-defined confirmation candidate. It does not inherit a masking burden and does not authorize training.

Set:

    $PARAMS = "$RUN/masking_parameters_authority_v2.json"

## G. Regenerate real census V2 receipts

First create summary/split/eligibility receipts from the actual pass1 NPZ:

    python analysis/v5_full104_census_20260918/full104_readonly_census_receipts_v2.py --pass1 "$PASS1" --out-summary "$RUN/full104_census_summary_v2.json" --out-split "$RUN/full104_split_receipt_v1.json" --out-target-eligibility "$RUN/full104_target_eligibility_v1.json"

Then build the census authority:

    python scripts/agent/build_full104_census_authority_v2_20260918.py --repo "$REPO" --level4-root "$L4" --observation-state "$OBS" --pass1 "$PASS1" --summary "$RUN/full104_census_summary_v2.json" --split "$RUN/full104_split_receipt_v1.json" --target-eligibility "$RUN/full104_target_eligibility_v1.json" --support-authority "$SUPPORT" --out "$RUN/full104_census_authority_v2.json"

STOP if the int64 cross-check, 17,053 all-fold eligibility, strict-core size, support binding, manifest hash, or observation-state hash does not reproduce.

## H. Build the calibration-only cache once

Use a new, nonexistent output directory:

    $CACHE = "$RUN/control_calibration_cache_v1"

    python scripts/agent/build_full104_control_calibration_cache_v1.py --level4-root "$L4" --registry "$REGISTRY" --census-authority "$RUN/full104_census_authority_v2.json" --split-receipt "$RUN/full104_split_receipt_v1.json" --target-eligibility "$RUN/full104_target_eligibility_v1.json" --support-authority "$SUPPORT" --out-dir "$CACHE"

Required role:

    CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1

Verify hashes, all 104 donors, retained-row accounting, and cache-evaluator closure before using the cache.

Never point terminal masking execution at $CACHE.

## I. Target-panel capacity ladder with non-tautological exact replay

Lawful ladder:

    128 -> 256 -> 512 -> 1024

The evaluator chooses only the next lawful rung from prior verdicts.

For each rung, use separate first-run and replay output directories. Example for the first rung:

    $TP_A = "$RUN/target_panel_128_runA"
    $TP_B = "$RUN/target_panel_128_runB"

First execution:

    python scripts/agent/evaluate_full104_target_panel_capacity_from_cache_v1.py --cache-dir "$CACHE" --parameters-authority "$PARAMS" --out-dir "$TP_A" --workers $WORKERS

A replay-required exit/status is expected. Preserve the run-A matrices unchanged.

Second execution, writing elsewhere:

    python scripts/agent/evaluate_full104_target_panel_capacity_from_cache_v1.py --cache-dir "$CACHE" --parameters-authority "$PARAMS" --out-dir "$TP_B" --workers $WORKERS --replay-planted "$TP_A/target_panel_128.planted_f64.npy" --replay-shuffled "$TP_A/target_panel_128.shuffled_f64.npy"

If 128 qualifies, STOP and do not inspect 256.

If it fails, evaluate 256 in two new directories and pass every prior verdict with repeated --prior-verdict arguments. Repeat only the next lawful rung. Never skip or reorder rungs.

The qualifying replay directory writes:

    target_panel_sizing_receipt_v2.json

## J. Build target selection and TargetPanelAuthorityV3

After a target count is selected:

    $SELECTED_TARGET_COUNT = <REQUIRED_SELECTED_COUNT_FROM_SIZING_RECEIPT>

    python scripts/agent/build_full104_target_panel_selection_v2_20260918.py --eligibility "$RUN/full104_target_eligibility_v1.json" --target-count $SELECTED_TARGET_COUNT --out "$RUN/target_panel_selection_v2.json"

Build TargetPanelAuthorityV3. Supply every evaluated capacity verdict with repeated --capacity-verdict:

    python scripts/agent/build_full104_target_panel_authority_v3_20260918.py --cache-dir "$CACHE" --canonical-registry-authority "$REGISTRY_AUTH" --support-authority "$SUPPORT" --census-authority "$RUN/full104_census_authority_v2.json" --target-eligibility "$RUN/full104_target_eligibility_v1.json" --sizing-receipt "<REQUIRED_QUALIFYING_REPLAY_DIR>/target_panel_sizing_receipt_v2.json" --capacity-verdict "<REQUIRED_VERDICT_1>" [--capacity-verdict "<REQUIRED_VERDICT_2>" ...] --selection-receipt "$RUN/target_panel_selection_v2.json" --out "$RUN/target_panel_authority_v3.json"

Do not omit failed lower-rung verdicts from the provenance chain.

## K. Build current outer split and precision

    python scripts/agent/build_full104_outer_split_authority_v1_20260918.py --split-receipt "$RUN/full104_split_receipt_v1.json" --out "$RUN/outer_split_authority_v1.json"

    python scripts/agent/build_full104_precision_authority_v4_20260918.py --support-authority "$SUPPORT" --target-panel-authority "$RUN/target_panel_authority_v3.json" --target-panel-sizing-receipt "<REQUIRED_QUALIFYING_REPLAY_DIR>/target_panel_sizing_receipt_v2.json" --outer-split-authority "$RUN/outer_split_authority_v1.json" --out "$RUN/precision_authority_v4.json"

The 4096 bootstrap replicates are Monte-Carlo precision, not 4096 biological samples.

## L. Nonlinear capacity ladder

First build model-shape authority:

    python scripts/agent/build_full104_nonlinear_capacity_model_authority_v1_20260918.py --repo "$REPO" --parameters-authority "$PARAMS" --out "$RUN/nonlinear_capacity_model_authority_v1.json"

Lawful row-cap ladder:

    64 -> 128 -> 256 -> 512 -> 1024

Use the same separate run-A/run-B replay discipline as the target-panel ladder.

First 64-cap run:

    $NL_A = "$RUN/nonlinear_64_runA"
    $NL_B = "$RUN/nonlinear_64_runB"

    python scripts/agent/evaluate_full104_nonlinear_capacity_from_cache_v1.py --cache-dir "$CACHE" --parameters-authority "$PARAMS" --model-capacity-authority "$RUN/nonlinear_capacity_model_authority_v1.json" --target-panel-authority "$RUN/target_panel_authority_v3.json" --target-selection-receipt "$RUN/target_panel_selection_v2.json" --precision-authority "$RUN/precision_authority_v4.json" --outer-split-authority "$RUN/outer_split_authority_v1.json" --out-dir "$NL_A" --workers $WORKERS

Replay into a different directory:

    python scripts/agent/evaluate_full104_nonlinear_capacity_from_cache_v1.py --cache-dir "$CACHE" --parameters-authority "$PARAMS" --model-capacity-authority "$RUN/nonlinear_capacity_model_authority_v1.json" --target-panel-authority "$RUN/target_panel_authority_v3.json" --target-selection-receipt "$RUN/target_panel_selection_v2.json" --precision-authority "$RUN/precision_authority_v4.json" --outer-split-authority "$RUN/outer_split_authority_v1.json" --out-dir "$NL_B" --workers $WORKERS --replay-planted "$NL_A/nonlinear_cap_64.planted_f64.npy" --replay-shuffled "$NL_A/nonlinear_cap_64.shuffled_f64.npy"

If 64 qualifies, STOP. If it fails, use the next lawful cap, new A/B directories, and pass all prior verdicts using repeated --prior-verdict arguments.

The qualifying replay directory writes:

    nonlinear_sampling_calibration_receipt_v2.json

Historical nonlinear work may justify model shape only. Do not import historical data, target lists, folds, burden, seeds, or row caps.

## M. Close three implementation gaps before terminal masking

At this head there is no current executable builder for each of the following final authorities:

1. NonlinearChallengeAuthorityV3
2. MaskingRngReplayAuthorityV2
3. MaskingQualificationRunContractV4

Implement behavior-tested builders on the implementation branch, with independent verifier review before promotion.

Do not use:

    scripts/agent/build_full104_nonlinear_challenge_authority_v2_20260918.py

as final nonlinear authority. It creates V2 only.

Do not hand-write placeholder JSON for any of the three gaps.

After these builders exist, update the current active plan/checkpoint state and refresh the GPU preflight again if its source inventory changed.

## N. Final V4 freeze and machine checkpoint

Only after all current runtime receipts and authorities exist:

- bind exact current source hashes
- freeze MaskingQualificationRunContractV4 before inspecting terminal policy outcomes
- terminal input role must be AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1
- calibration cache may be provenance/calibration input only
- rebuild docs/agent/CURRENT_WORK_CHECKPOINT.json on the final committed GPU-worktree head
- validate it using scripts/agent/work_checkpoint.py
- independently review the final package

## O. Only then open terminal masking

Start at 5%.

Do not inspect 10% if 5% fully qualifies. Escalate only after explicit failure and stop at the first full qualification.

A masking PASS does not authorize training. Remaining-RNA necessity, measurement robustness, final production geometry/memorization, runtime provenance and explicit final training authority still follow.

## Permanent anti-spillover rules

- no Stage81 cache as FULL104
- no historical T1 checkpoint as healthy teacher
- no discovery matrices as FULL104
- no historical target list, fold map, burden, seed or row cap in current calibration
- no placeholder SHA roots
- no free PASS strings
- no cache as terminal input
- no post-outcome retuning
- no reopening settled audits without changed input
