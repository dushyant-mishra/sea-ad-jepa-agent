# JEPA V5 NEW CHAT HANDOFF — FULL104 masking control calibration and terminal-freeze boundary

Date: 2026-09-18

Status: FULL104_MASKING_CONTROL_CALIBRATION_IMPLEMENTED__GPU_RECEIPT_EXECUTION_PENDING__TERMINAL_OUTCOMES_UNOPENED__TRAINING_OFF

Implementation anchor: 86692cde7e61fe4beae7fff4070bd376a8090af2 on impl/v5-full104-masking-redteam2-20260918, draft PR #20.

This handoff is documentation-only. The next chat must re-fetch the live branch head and compare it with this anchor before acting.

## 1. Biological task

The model is supposed to infer cellular/biological state from partial RNA, including local state relevant to a supplied molecular address. We are not training it to guess one hidden gene value.

Current masking work is an anti-cheating qualification. Expression-based attackers are diagnostics, not the JEPA training objective.

## 2. Permanent work order

DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL

IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK

Protected outcomes and training remain closed while upstream choices are open.

## 3. FULL104 and changed-input census

Current heavy substrate:

- 4,553,407 cells
- 104 donors
- 42 operators
- 41,238 addresses
- strict common core 17,186
- 8,915 authenticated Level-4 sparse blocks
- block-manifest SHA-256 66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
- observation-state SHA-256 852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537
- canonical address registry SHA-256 7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd

Known GPU root:

D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/

The corrected FULL104 census changed the burden-calibration question:

- measured-zero fraction inside strict core = 0.832983
- core nonzero count = 13,069,917,135
- core measured-zero count = 65,184,935,567
- 17,053/17,186 core addresses estimable in every outer fold
- donor Kish ESS about 42 despite 104 donor inclusion units

Therefore measured zero is not structural missingness. Mask eligibility remains value-independent over strictly measured addresses. The old 15% discovery burden over 800 addresses cannot be inherited.

Important authority boundary: these census findings must be regenerated into the actual V2 execution receipts from the real GPU pass1 NPZ. Repository constants alone do not replace runtime receipts.

## 4. Current masking semantics

Primary arms:

1. UNIFORM_RANDOM
2. TOP8_CORRELATION
3. RIDGE8_CONDITIONAL
4. PREFIX3_SELECTIVE

Explicit pre-FULL104 confirmation candidate:

- targeted partner cap 8
- ridge candidate pool 64
- ridge score features 32
- ridge alpha 1/100
- PREFIX inner folds 3
- PREFIX candidates 20
- PREFIX floor 1/20
- PREFIX reduction 1/2

These are not hidden defaults. They are the exact discovery-defined candidate worth independently confirming. Do not retune them after seeing FULL104 outcomes.

Burden is separate: 5/10/15/20/30/50%, ascending. Stop at the first fully qualifying rung and never open a higher burden after a lower burden passes.

## 5. Calibration-only cache

A direct 128+ target calibration against the full stream would repeatedly scan all 8,915 blocks and was rejected as unnecessary execution burden.

Current solution:

- src/sea_ad_jepa/v5/full104_control_calibration_cache_v1.py
- scripts/agent/build_full104_control_calibration_cache_v1.py
- src/sea_ad_jepa/v5/full104_control_calibration_cache_evaluator_v1.py

The cache is bound to current FULL104 manifest, canonical registry, census/support/split/eligibility roots and exact normalization. It retains deterministic rows from all 104 donors and full-donor sufficient statistics for closure checks.

Permanent role:

CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1

RunContract V4 explicitly rejects that role as terminal input. Terminal masking must use the authenticated Level-4 block stream.

The direct-stream target-panel calibration script is superseded by the cache route.

## 6. Target-panel capacity

Panel-size calibration is separated from masking success. It asks only whether diagnostic capacity can distinguish a deliberately planted shortcut from a within-donor shuffled null without opening real masking-policy outcomes.

Nested ladder:

128 -> 256 -> 512 -> 1024

Current files:

- src/sea_ad_jepa/v5/target_panel_sizing_authority_v2.py
- src/sea_ad_jepa/v5/target_panel_selector_v2.py
- src/sea_ad_jepa/v5/full104_control_calibration_cache_evaluator_v1.py
- scripts/agent/evaluate_full104_target_panel_capacity_from_cache_v1.py
- scripts/agent/build_full104_target_panel_authority_v3_20260918.py

Exact replay is required. Stop at first qualifying target count. 128 is not automatically final because it is convenient.

## 7. Outer split and precision

Current builders:

- scripts/agent/build_full104_outer_split_authority_v1_20260918.py
- scripts/agent/build_full104_precision_authority_v4_20260918.py

The outer split must descend from the current source-stratified four-fold donor receipt. Precision is paired target-and-donor uncertainty with donors resampled within source.

The millions of cells improve per-donor measurement; they are not millions of independent biological units.

The 4096 bootstrap replicates are Monte-Carlo computation precision, not biological sample size.

## 8. Nonlinear capacity

Historical nonlinear work is retained only for model-shape provenance, not historical data, targets, folds, burden, seed, or row cap.

Current chain:

- src/sea_ad_jepa/v5/nonlinear_capacity_model_authority_v1.py
- scripts/agent/build_full104_nonlinear_capacity_model_authority_v1_20260918.py
- src/sea_ad_jepa/v5/nonlinear_sampling_calibration_authority_v2.py
- src/sea_ad_jepa/v5/full104_nonlinear_capacity_cache_evaluator_v1.py
- scripts/agent/evaluate_full104_nonlinear_capacity_from_cache_v1.py
- src/sea_ad_jepa/v5/masking_nonlinear_challenge_authority_v3.py
- src/sea_ad_jepa/v5/masking_nonlinear_challenge_executor_v1.py

Row-cap ladder:

64 -> 128 -> 256 -> 512 -> 1024

Stop at first qualifying cap with exact replay. Do not inherit 256 from the provisional successor.

## 9. Final run contract

Current contract:

src/sea_ad_jepa/v5/masking_qualification_run_contract_v4.py

It binds design/parameter/census/support/cache calibration provenance, target-panel sizing, outer split/precision, nonlinear calibration, RNG, machine checkpoint and exact source roles.

Critical separation:

- calibration provenance may be bound
- calibration cache may not be terminal execution input
- terminal execution role must be AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1

No final V4 run-contract instance exists yet.

## 10. Live implementation delta

The branch advanced by 31 commits from the earlier direct-driver snapshot 0ec5cccc... to 86692cde7e61fe4beae7fff4070bd376a8090af2. That delta added/finalized:

- calibration cache builder and evaluator
- target-panel cache evaluator
- target-panel V3 authority builder
- current outer-split and precision V4 builders
- nonlinear model-capacity authority separated from row-cap calibration
- nonlinear cache evaluator and calibration V2
- stronger RunContract V4 bindings
- anti-spillover and CI coverage
- governance state pointing to current successors

No terminal masking outcome artifact was added in that delta.

## 11. Exact open blockers

1. Current implementation head has no recorded combined CI status at handoff. Run focused CI first and fail on skips.
2. Refresh GPU preflight. The 20260917 PowerShell preflight still checks stale V1/V2 chain.
3. On GPU regenerate/hash-bind census V2 summary, split and target-eligibility receipts from the real pass1 NPZ.
4. Build authenticated FULL104 calibration cache.
5. Run target-panel capacity ladder with exact replay; issue sizing receipt and TargetPanelAuthorityV3.
6. Build current OuterSplitAuthorityV1 and PrecisionAuthorityV4.
7. Build nonlinear model-capacity authority; run nonlinear cap ladder with exact replay; issue calibration V2 receipt.
8. Freeze NonlinearChallengeAuthorityV3 and RNG authority.
9. Bind exact current source hashes and freeze final RunContract V4.
10. Rebuild/validate machine-bound CURRENT_WORK_CHECKPOINT.json on final committed source head.
11. Independent verification.
12. Only then open terminal 5% FULL104 masking. Escalate only after failure and stop at first full qualification.
13. Masking PASS still does not authorize training. Remaining-RNA, measurement robustness, final geometry/memorization, runtime provenance and explicit training authority remain afterward.

## 12. Historical findings in perspective

Supporting RIDGE8 branch:

analysis/v5-ridge8-expanded-validation-20260917 at 99dc3a6ff5f540fac17e86b135f2c6710bb41405

Historical findings support what is worth confirming: RIDGE8 strongest broad candidate in tested discovery threats, TOP8 comparator, PREFIX3 sparse/selective, nonlinear directionally supportive, STABLE variants ineffective or vacuous in tested threat models.

They do not create FULL104 policy authority.

Historical T1/C2, Stage81, QID/F1, Layer-2, visibility and same-cell-thinning findings remain adversarial context. Do not re-run them unless changed input requires requalification.

## 13. Local files attached to this chat

The data/results/scripts manifest records exact sizes and SHA-256 for every file physically available here.

It includes:

- FOUNDATION_CALIBRATION_BUNDLE_20260824.zip
- two-part FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K archive plus checksum CSV
- checkpoints.zip
- t1_checkpoint_u0200.zip
- expression.zip
- 66e64913-959f-4a7c-bbfe-6ff906fb281d.npz
- Status and Repair Plan.txt
- WSL execution issue.txt

These are not copied into Git because several are hundreds of MB and duplication would create a competing lineage.

The two discovery parts match the checksum CSV. Expected assembled archive: 607,959,761 bytes, SHA-256 63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7.

All local attachments remain supporting/local references unless explicitly requalified. None may substitute for FULL104.

## 14. Stale and superseded traps

- scripts/agent/v5_full104_masking_gpu_preflight_20260917.ps1: stale for current V4 chain
- scripts/agent/run_full104_target_panel_capacity_calibration_v1.py: direct-stream route superseded by cache route
- Stage81A3 corrected TRAIN cache: historical limited scope, never FULL104
- T1 checkpoint archives: historical failure evidence, not healthy current teacher
- provisional TargetPanelAuthorityV2, PrecisionV3, nonlinear sampling V1: forbidden in final V4 chain
- placeholder SHA roots: never production authority

## 15. CI truth

Old code anchor 8ee5d0a5... has previously recorded green workflows and no-skip gates. That does not independently verify the 31-commit current successor delta.

At handoff, GitHub returns no combined status entries for 86692cde7e61fe4beae7fff4070bd376a8090af2.

Therefore the next chat must not claim the current head is CI-verified until it actually checks the focused suite on that head.

## 16. Do not redo

Do not reopen FULL104 lineage, K2, VALUE_ONLY_256, base estimand, T0/T1/C2 chronology, QID/F1, Stage81A3 scope, Layer-2, target-identity shortcut discovery, Stage-A structural qualification, visibility ablation, same-cell thinning, or streaming/reference parity without changed inputs.

## 17. Exact takeover sequence

Exact-head CI -> refresh current GPU preflight -> runtime census receipts -> authenticated calibration cache -> control-only capacity selections -> final V4 freeze -> machine checkpoint -> independent review -> terminal FULL104 5% rung

Training remains OFF.
