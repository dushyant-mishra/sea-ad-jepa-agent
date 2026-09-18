# JEPA V5 NEW CHAT HANDOFF — AUDITED FULL104 masking calibration and terminal-freeze boundary

Date: 2026-09-18

Status: FULL104_MASKING_HANDOFF_AUTHORITY_REPAIRED__GPU_RUNTIME_RECEIPTS_PENDING__TERMINAL_OUTCOMES_UNOPENED__TRAINING_OFF

Implementation branch: impl/v5-full104-masking-redteam2-20260918

Current implementation/governance head: 038a162f03f29f5f0e00337dde3cbbcf3cf7870c

Verified scientific source/test anchor: f62dc42582c8b8933955505f5127bebfaa687304

Underlying source/data lineage anchor: 86692cde7e61fe4beae7fff4070bd376a8090af2

Draft implementation PR #20; current base impl/v5-full104-masking-redteam-freeze-20260918. At the final authority-package audit PR #20 was OPEN + DRAFT with GitHub mergeable_state=dirty. This is not a scientific-state defect, but it is a governance warning: do not merge/rebase/resolve the PR as housekeeping; re-fetch and audit any conflict separately.

Current docs-only handoff branch: handoff/jepa-v5-full104-calibration-takeover-ready-v2-20260918

This package supersedes all earlier 20260918 FULL104 masking-calibration handoff branches, including the prior final-audited package.

## 1. Why this successor handoff exists

Authority-package audits found four repaired defects in the original handoff plus one final governance warning:

1. CURRENT_WORK_CHECKPOINT_STATE.json named the new working branch but still carried PR #18, the old analysis PR base, and old verified-anchor metadata.
2. docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md was still the September-17 V2 plan and directed the GPU lane toward MaskingQualificationExecutionAuthorityV2 rather than the current cache-calibrated V3/V4 chain.
3. CURRENT_WORK_CHECKPOINT_STATE.json hard-pinned START_HERE.md to the implementation-head hash, while the docs-only handoff changed START_HERE, making the handoff branch internally hash-inconsistent.
4. Several takeover commands named scripts without their required arguments; the target-selection receipt step was omitted; and three final authority builders were implied although they do not yet exist.
5. PR #20 is currently conflict-dirty against its base. The implementation branch remains authoritative; the PR must not be merged/rebased/resolved automatically during takeover.

Implementation governance commit 038a162f03f29f5f0e00337dde3cbbcf3cf7870c repairs defects 1-3 and replaces the active plan. This handoff repairs the command/package layer.

The implementation governance repair changes only docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json and docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md. Scientific source/test/data bytes remain anchored at 86692cde7e61fe4beae7fff4070bd376a8090af2.

## 2. Biological task

Infer cellular/biological state from partial RNA, including query-local state relevant to a supplied canonical molecular address.

This is not hidden-gene scalar imputation. Ridge/correlation/nonlinear expression predictors are anti-shortcut diagnostics, not the JEPA biological target.

Permanent order:

DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL

IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK

## 3. FULL104 substrate and changed-input census

Current substrate:

- 4,553,407 cells
- 104 donors
- 42 operators
- 41,238 addresses
- 17,186 strict common-core addresses
- 8,915 authenticated Level-4 blocks
- block-manifest SHA-256 66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
- observation-state SHA-256 852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537
- canonical registry SHA-256 7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd
- GPU root D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/

Corrected census:

- strict-core measured-zero frequency 0.832983
- strict-core nonzeros 13,069,917,135
- strict-core measured zeros 65,184,935,567
- 17,053 / 17,186 core addresses estimable in all four donor-held-out folds
- donor Kish ESS about 42 donor-equivalents from 104 donors

Consequences:

- strict MEASURED_SCALAR support is required
- measured zero remains measured evidence
- masking eligibility stays value-independent over strictly measured addresses
- discovery-era 15% burden from the 800-address universe is not terminal authority

The GPU machine still must regenerate actual V2 census receipts from the real pass1 NPZ.

## 4. Historical findings: preserve context without spillover

September-17 discovery supports this exact pre-FULL104 candidate for independent confirmation:

- targeted partner cap 8
- ridge candidate pool 64
- ridge score features 32
- ridge alpha 1/100
- PREFIX inner folds 3
- PREFIX candidates 20
- PREFIX floor 1/20
- PREFIX reduction 1/2

That historical work may define what is worth confirming and the nonlinear model shape. It may not supply current FULL104 data, target lists, folds, burden, seeds, row caps, teacher health, or terminal PASS.

Historical Stage81A3, T1 checkpoints, discovery expression archives and exploratory RIDGE8 results remain support/provenance only.

## 5. Current implemented calibration chain

Git at 86692cde7e61fe4beae7fff4070bd376a8090af2 contains all current paths claimed in the manifest, including:

- authenticated FULL104 streaming executor and canonical reference
- parameter authority V2 and current burden ladder
- census V2 receipt/builder chain
- calibration-only cache contract/builder/evaluator
- target-panel capacity ladder and selector
- TargetPanelAuthorityV3 builder
- current OuterSplitAuthorityV1 builder
- PrecisionAuthorityV4 builder
- nonlinear model-capacity authority and row-cap calibration V2
- nonlinear cache evaluator
- masking decision V2
- masking execution authority V4
- RunContract V4 schema
- anti-spillover V2

Calibration-cache role:

CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1

Terminal input role:

AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1

## 6. Current exact-head CI boundary

PR #20 now points to 038a162f03f29f5f0e00337dde3cbbcf3cf7870c and base impl/v5-full104-masking-redteam-freeze-20260918.

Scientific source/test anchor f62dc42582c8b8933955505f5127bebfaa687304 is verified by GitHub Actions run 35373584821: SUCCESS with the explicit fail-closed-on-skips step also SUCCESS. The prior run 35373486676 failed only because anti-spillover still referenced nonlinear sampling V1; f62dc425... repaired those two stale test references. Live head 038a162f... is docs-only governance above f62dc425.... Re-run CI after any source/test/workflow change.

## 7. Current execution order

Follow docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md and the audited command templates.

Sequence:

1. re-fetch live head/PR and confirm f62dc425... scientific-anchor CI still applies; rerun only after source/test/workflow changes
2. refresh/supersede stale 20260917 GPU preflight
3. regenerate real census V2 receipts from pass1 NPZ
4. build explicit masking-parameter authority V2
5. build authenticated calibration-only cache
6. target-panel ladder 128 -> 256 -> 512 -> 1024 with separate run-A/run-B exact replay; stop at first pass
7. build target-selection receipt and TargetPanelAuthorityV3
8. build OuterSplitAuthorityV1 and PrecisionAuthorityV4
9. build nonlinear model-capacity V1 and run row-cap ladder 64 -> 128 -> 256 -> 512 -> 1024 with separate exact replay; stop at first pass
10. close the three missing final-builder gaps
11. bind RNG/current source hashes and freeze final RunContract V4
12. rebuild/validate machine checkpoint and independently review
13. only then open terminal FULL104 5% rung
14. stop burden escalation at first full qualification
15. masking closure still does not authorize training

## 8. Three explicit implementation gaps before final freeze

The repository does not yet contain a current executable builder for:

- NonlinearChallengeAuthorityV3
- MaskingRngReplayAuthorityV2
- MaskingQualificationRunContractV4

The existing scripts/agent/build_full104_nonlinear_challenge_authority_v2_20260918.py builds V2 only and must not be promoted as V3.

Implement these builders prospectively with behavior tests, exact role/root binding, anti-placeholder checks and independent verifier review before terminal outcome access.

## 9. Replay rule that must not be weakened

Target-panel and nonlinear cache evaluators write matrices to their output directories before comparing replay inputs.

Therefore the first and second executions must use different output directories. Preserve run-A matrices unchanged and use them as replay inputs for run-B.

Do not replay against matrices in the same directory being overwritten.

## 10. Governance state after repair

CURRENT_WORK_CHECKPOINT_STATE.json now pins only:

- AGENTS.md
- docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md

It intentionally does not hard-pin START_HERE.md, because docs-only handoff commits update START_HERE.

The active execution-plan SHA pinned in checkpoint state is f1c8db99ebb6eb35c39583590e5a50b7a7c6146c5eae40e5d31751a8a2e2468a.

The machine-bound docs/agent/CURRENT_WORK_CHECKPOINT.json still must be built and validated on the canonical GPU worktree after final source/authority freeze and again immediately before terminal execution.

## 11. Local assets physically verified in this chat

All ten files listed under local_chat_assets in the manifest are physically present here with the recorded sizes and SHA-256 values.

The two FOUNDATION_DISCOVERY_EXPRESSION parts concatenate to 607,959,761 bytes with SHA-256 63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7.

These assets remain historical/support-only and are not FULL104 substitutes.

## 12. Do not redo without changed inputs

Do not reopen merely because this is a new chat:

- FULL104 lineage/substrate
- K2 partition
- VALUE_ONLY_256 representation
- base estimand
- T0/T1/C2 chronology
- QID/F1
- Stage81A3 scope
- Layer-2
- target-identity shortcut discovery
- Stage-A structural qualification
- visibility ablation
- same-cell thinning
- streaming/reference parity

Classify proposed repetition as ALREADY_AUDITED, SUPERSEDED, OPEN, or CHANGED_INPUT_REQUIRES_REQUALIFICATION.

## 13. Hard boundaries

TRAINING_OFF

NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION

NO_PATHOLOGY_DEV_SEALED_OUTCOME_ACCESS_WHILE_DESIGN_OPEN

NO_SMALLER_OR_HISTORICAL_FULL104_SUBSTITUTE

NO_CALIBRATION_CACHE_AS_TERMINAL_INPUT

NO_PLACEHOLDER_HASH_AUTHORITY

NO_FREE_PASS_STATUS_WITHOUT_BOUND_EVIDENCE

NO_POST_OUTCOME_RETUNING

NO_BURDEN_ESCALATION_AFTER_FIRST_FULL_QUALIFICATION

No target-panel count is selected.
No nonlinear row cap is selected.
No terminal masking policy is selected.
No final V4 run-contract instance exists.
Training remains OFF.
