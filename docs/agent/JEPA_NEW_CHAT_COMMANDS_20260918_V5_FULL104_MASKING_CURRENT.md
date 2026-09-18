# JEPA V5 — CURRENT FULL104 masking-calibration and final-freeze commands

Date: 2026-09-18

Status: CURRENT IMPLEMENTATION COMMAND AUTHORITY FOR PR #20. TERMINAL MASKING OUTCOMES UNOPENED. TRAINING OFF.

This file supersedes `docs/agent/JEPA_NEW_CHAT_COMMANDS_20260917_V5_FULL104_MASKING.md` for current execution.

Historical/smaller-run artifacts may motivate a current hypothesis or model shape only. They may not occupy a FULL104 runtime role, data root, target list, fold, burden, seed, row cap, selected policy, authority digest, or PASS state unless a current authority explicitly re-authorizes that exact role and binds current FULL104 roots.

Current scientific source/test/workflow anchor:

`3084c1f497a3db6056fd100fb896ccdf67318c8a`

Verified GitHub Actions run:

`35392547631` — PASS, including fail-on-skips.

## 1. Re-fetch and preserve the worktree

PowerShell:

```powershell
$Repo = "D:\Jepa project"
$Branch = "impl/v5-full104-masking-redteam2-20260918"
$ExpectedAnchor = "3084c1f497a3db6056fd100fb896ccdf67318c8a"

git -C $Repo fetch origin
git -C $Repo status --porcelain
git -C $Repo rev-parse "origin/$Branch"
git -C $Repo log -1 --oneline "origin/$Branch"
```

If the worktree is dirty, preserve it and STOP. Do not reset, clean, stash, rebase, or overwrite user changes automatically.

If source/test/workflow/data bytes have changed after `$ExpectedAnchor`, classify the delta as `CHANGED_INPUT_REQUIRES_REQUALIFICATION` and rerun the focused CI before proceeding.

## 2. Required current machine inputs

Use a new runtime directory that contains no Stage81, T1, discovery, RIDGE8-spike, or historical-cache material.

```powershell
$Worktree = "D:\Jepa project"
$L4 = "D:\Jepa project\outputs\full104_v014_20260826\03_phase2_state_derivation_v1\expression_level4"
$RUN = "<REQUIRED_NEW_EMPTY_FULL104_RUNTIME_OUTPUT_DIRECTORY>"
$PASS1 = "<REQUIRED_REAL_FULL104_PASS1_NPZ>"
$OBS = "<REQUIRED_CURRENT_OPERATOR_ADDRESS_OBSERVATION_STATE_FILE>"
$REGISTRY = "<REQUIRED_AUTHENTICATED_41238_ROW_CANONICAL_REGISTRY_CSV>"
$WORKERS = <REQUIRED_POSITIVE_INTEGER>

$SUPPORT = "$Worktree\docs\agent\V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json"
$REGISTRY_AUTH = "$Worktree\docs\agent\V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_20260916.json"
$REPRESENTATION = "$Worktree\docs\agent\V5_PRIMARY_REPRESENTATION_AUTHORITY_20260915.json"
$TEACHER_TARGET = "$Worktree\docs\agent\TEACHER_STUDENT_V5_SCIENTIFIC_TARGET_AUTHORITY_V2.json"
```

The angle-bracket values are mandatory unresolved machine paths, not authority placeholders. Do not run until each is replaced by a real path.

Verify physical roots before use:

```powershell
$ExpectedL4 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
$ExpectedObs = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
$ExpectedRegistry = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"

if ((Get-FileHash -Algorithm SHA256 "$L4\PHASE2_EXPRESSION_BLOCK_MANIFEST.csv").Hash.ToLowerInvariant() -ne $ExpectedL4) { throw "STOP: FULL104 manifest mismatch" }
if ((Get-FileHash -Algorithm SHA256 $OBS).Hash.ToLowerInvariant() -ne $ExpectedObs) { throw "STOP: observation-state mismatch" }
if ((Get-FileHash -Algorithm SHA256 $REGISTRY).Hash.ToLowerInvariant() -ne $ExpectedRegistry) { throw "STOP: canonical registry mismatch" }
```

## 3. Build the explicit pre-FULL104 confirmation parameters

```powershell
python "$Worktree\scripts\agent\build_full104_masking_parameters_authority_v2_20260918.py" --repo "$Worktree" --out "$RUN\masking_parameters_authority_v2.json"
$PARAMS = "$RUN\masking_parameters_authority_v2.json"
```

This explicitly re-authorizes the pre-FULL104 discovery candidate only. It does not authorize burden, target panel size, fold map, nonlinear row cap, terminal policy, or training.

## 4. Regenerate census V2 receipts and authority from real FULL104 pass1

```powershell
python "$Worktree\analysis\v5_full104_census_20260918\full104_readonly_census_receipts_v2.py" --pass1 "$PASS1" --out-summary "$RUN\full104_census_summary_v2.json" --out-split "$RUN\full104_split_receipt_v1.json" --out-target-eligibility "$RUN\full104_target_eligibility_v1.json"

python "$Worktree\scripts\agent\build_full104_census_authority_v2_20260918.py" --repo "$Worktree" --level4-root "$L4" --observation-state "$OBS" --pass1 "$PASS1" --summary "$RUN\full104_census_summary_v2.json" --split "$RUN\full104_split_receipt_v1.json" --target-eligibility "$RUN\full104_target_eligibility_v1.json" --support-authority "$SUPPORT" --out "$RUN\full104_census_authority_v2.json"

$CENSUS = "$RUN\full104_census_authority_v2.json"
$SPLIT = "$RUN\full104_split_receipt_v1.json"
$ELIG = "$RUN\full104_target_eligibility_v1.json"
```

STOP on any failure to reproduce current FULL104 support geometry, including 17,053 all-fold eligible targets and the 17,186 strict common core.

## 5. Build the authenticated calibration-only cache

```powershell
$CACHE = "$RUN\control_calibration_cache_v1"
python "$Worktree\scripts\agent\build_full104_control_calibration_cache_v1.py" --level4-root "$L4" --registry "$REGISTRY" --census-authority "$CENSUS" --split-receipt "$SPLIT" --target-eligibility "$ELIG" --support-authority "$SUPPORT" --out-dir "$CACHE"
```

Required cache role:

`CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1`

Never use `$CACHE` as terminal masking input or training input.

## 6. Run current calibration-mode GPU preflight

```powershell
powershell -ExecutionPolicy Bypass -File "$Worktree\scripts\agent\v5_full104_masking_gpu_preflight_20260918.ps1" -Mode Calibration -ExpectedScientificAnchor $ExpectedAnchor -CanonicalRepo $Repo -Worktree $Worktree -Level4Root $L4 -ObservationState $OBS -Registry $REGISTRY -ParametersAuthority $PARAMS -CensusAuthority $CENSUS -SplitReceipt $SPLIT -TargetEligibility $ELIG -CacheDir $CACHE
```

Do not use `scripts/agent/v5_full104_masking_gpu_preflight_20260917.ps1`.

## 7. Target-panel capacity ladder

Lawful order: `128 -> 256 -> 512 -> 1024`. Stop at the first qualifying rung.

Run A intentionally exits with code 3 after writing replay matrices. Accept code 3 only when the status is `REPLAY_REQUIRED_*`; any other nonzero code is a STOP. Run B must write to a different directory and consume unchanged Run-A matrices.

First rung:

```powershell
$TP_A = "$RUN\target_panel_128_runA"
$TP_B = "$RUN\target_panel_128_runB"

python "$Worktree\scripts\agent\evaluate_full104_target_panel_capacity_from_cache_v1.py" --cache-dir "$CACHE" --parameters-authority "$PARAMS" --out-dir "$TP_A" --workers $WORKERS
if ($LASTEXITCODE -ne 3) { throw "STOP: target-panel Run A did not request lawful replay" }
$TP_A_STATUS = Get-Content -Raw "$TP_A\target_panel_128.status.json" | ConvertFrom-Json
if ($TP_A_STATUS.status -ne "REPLAY_REQUIRED_BEFORE_CAPACITY_VERDICT") { throw "STOP: target-panel Run A status is not the exact replay-required state" }

python "$Worktree\scripts\agent\evaluate_full104_target_panel_capacity_from_cache_v1.py" --cache-dir "$CACHE" --parameters-authority "$PARAMS" --out-dir "$TP_B" --workers $WORKERS --replay-planted "$TP_A\target_panel_128.planted_f64.npy" --replay-shuffled "$TP_A\target_panel_128.shuffled_f64.npy"
if ($LASTEXITCODE -ne 0) { throw "STOP: target-panel Run B failed" }
```

If 128 fails, repeat only the next rung using new A/B directories and repeated `--prior-verdict` arguments for every lower rung. Never skip/reorder rungs or inspect higher rungs after a lower one qualifies.

Set the qualifying replay directory:

```powershell
$TPQ = "<REQUIRED_QUALIFYING_TARGET_PANEL_REPLAY_DIRECTORY>"
$TARGET_COUNT = <REQUIRED_SELECTED_COUNT_FROM_$TPQ\target_panel_sizing_receipt_v2.json>
```

Build target selection and TargetPanelAuthorityV3, supplying every evaluated capacity verdict:

```powershell
python "$Worktree\scripts\agent\build_full104_target_panel_selection_v2_20260918.py" --eligibility "$ELIG" --target-count $TARGET_COUNT --out "$RUN\target_panel_selection_v2.json"

$TP_CAPACITY_ARGS = @()
foreach ($r in @(<REQUIRED_ALL_TARGET_PANEL_CAPACITY_RECEIPT_PATHS_IN_LAWFUL_ORDER>)) { $TP_CAPACITY_ARGS += @("--capacity-receipt", $r) }
$TP_VERDICT_ARGS = @()
foreach ($v in @(<REQUIRED_ALL_TARGET_PANEL_VERDICT_PATHS_IN_LAWFUL_ORDER>)) { $TP_VERDICT_ARGS += @("--capacity-verdict", $v) }

python "$Worktree\scripts\agent\build_full104_target_panel_authority_v3_20260918.py" --cache-dir "$CACHE" --canonical-registry-authority "$REGISTRY_AUTH" --support-authority "$SUPPORT" --census-authority "$CENSUS" --target-eligibility "$ELIG" --sizing-plan "$TPQ\target_panel_sizing_plan_v2.json" --control-calibration-precision-plan "$TPQ\control_calibration_precision_plan_v2.json" --sizing-receipt "$TPQ\target_panel_sizing_receipt_v2.json" @TP_CAPACITY_ARGS @TP_VERDICT_ARGS --selection-receipt "$RUN\target_panel_selection_v2.json" --out "$RUN\target_panel_authority_v3.json"
```

## 8. Build outer split and PrecisionAuthorityV4

```powershell
python "$Worktree\scripts\agent\build_full104_outer_split_authority_v1_20260918.py" --split-receipt "$SPLIT" --out "$RUN\outer_split_authority_v1.json"

$NULL_MARGIN_NUMERATOR = <PROSPECTIVE_NULL_EQUIVALENCE_MARGIN_NUMERATOR__MUST_BE_FROZEN_BEFORE_TERMINAL_OUTCOMES>\n$NULL_MARGIN_DENOMINATOR = <PROSPECTIVE_NULL_EQUIVALENCE_MARGIN_DENOMINATOR__MUST_BE_FROZEN_BEFORE_TERMINAL_OUTCOMES>\n\npython "$Worktree\scripts\agent\build_full104_precision_authority_v4_20260918.py" --support-authority "$SUPPORT" --target-panel-authority "$RUN\target_panel_authority_v3.json" --target-panel-sizing-receipt "$TPQ\target_panel_sizing_receipt_v2.json" --outer-split-authority "$RUN\outer_split_authority_v1.json" --null-equivalence-margin-numerator $NULL_MARGIN_NUMERATOR --null-equivalence-margin-denominator $NULL_MARGIN_DENOMINATOR --out "$RUN\precision_authority_v4.json"
```

## 9. Nonlinear row-cap calibration

Build current model-shape authority:

```powershell
python "$Worktree\scripts\agent\build_full104_nonlinear_capacity_model_authority_v1_20260918.py" --repo "$Worktree" --parameters-authority "$PARAMS" --out "$RUN\nonlinear_capacity_model_authority_v1.json"
```

Lawful order: `64 -> 128 -> 256 -> 512 -> 1024`. Use the same separate Run-A/Run-B exact replay discipline and stop at first qualifying cap.

First rung:

```powershell
$NL_A = "$RUN\nonlinear_64_runA"
$NL_B = "$RUN\nonlinear_64_runB"

python "$Worktree\scripts\agent\evaluate_full104_nonlinear_capacity_from_cache_v1.py" --cache-dir "$CACHE" --parameters-authority "$PARAMS" --model-capacity-authority "$RUN\nonlinear_capacity_model_authority_v1.json" --target-panel-authority "$RUN\target_panel_authority_v3.json" --target-selection-receipt "$RUN\target_panel_selection_v2.json" --precision-authority "$RUN\precision_authority_v4.json" --outer-split-authority "$RUN\outer_split_authority_v1.json" --out-dir "$NL_A" --workers $WORKERS
if ($LASTEXITCODE -ne 3) { throw "STOP: nonlinear Run A did not request lawful replay" }
$NL_A_STATUS = Get-Content -Raw "$NL_A\nonlinear_cap_64.status.json" | ConvertFrom-Json
if ($NL_A_STATUS.status -ne "REPLAY_REQUIRED_BEFORE_NONLINEAR_CAPACITY_VERDICT") { throw "STOP: nonlinear Run A status is not the exact replay-required state" }

python "$Worktree\scripts\agent\evaluate_full104_nonlinear_capacity_from_cache_v1.py" --cache-dir "$CACHE" --parameters-authority "$PARAMS" --model-capacity-authority "$RUN\nonlinear_capacity_model_authority_v1.json" --target-panel-authority "$RUN\target_panel_authority_v3.json" --target-selection-receipt "$RUN\target_panel_selection_v2.json" --precision-authority "$RUN\precision_authority_v4.json" --outer-split-authority "$RUN\outer_split_authority_v1.json" --out-dir "$NL_B" --workers $WORKERS --replay-planted "$NL_A\nonlinear_cap_64.planted_f64.npy" --replay-shuffled "$NL_A\nonlinear_cap_64.shuffled_f64.npy"
if ($LASTEXITCODE -ne 0) { throw "STOP: nonlinear Run B failed" }
```

If 64 fails, continue only to the next lawful cap with repeated `--prior-verdict` arguments. Historical nonlinear work supplies model-shape provenance only; never import historical data, target list, folds, burden, seed, or row cap.

Set:

```powershell
$NLQ = "<REQUIRED_QUALIFYING_NONLINEAR_REPLAY_DIRECTORY>"
```

## 10. Build the remaining prospective current authorities

Evidence-budget template and burden ladder:

```powershell
python "$Worktree\scripts\agent\build_full104_target_evidence_budget_template_authority_v1_20260918.py" --level4-root "$L4" --observation-state "$OBS" --support-authority "$SUPPORT" --census-authority "$CENSUS" --out "$RUN\target_evidence_budget_template_v1.json"

python "$Worktree\scripts\agent\build_full104_burden_ladder_authority_v2_20260918.py" --census-authority "$CENSUS" --out "$RUN\masking_burden_ladder_authority_v2.json"
```

The template canonically binds `NO_ADDITIONAL_RETAINED_COUNT_FLOOR__FROZEN_BURDEN_LADDER_OWNS_MASK_FRACTION_V1`. It does not freeze one concrete burden.

RNG replay authority:

```powershell
python "$Worktree\scripts\agent\build_full104_rng_replay_authority_v2_20260918.py" --canonical-registry-authority "$REGISTRY_AUTH" --outer-split-authority "$RUN\outer_split_authority_v1.json" --target-panel-authority "$RUN\target_panel_authority_v3.json" --burden-ladder-authority "$RUN\masking_burden_ladder_authority_v2.json" --out "$RUN\masking_rng_replay_authority_v2.json"
```

NonlinearChallengeAuthorityV3 must receive every evaluated nonlinear capacity receipt and verdict:

```powershell
$NL_CAPACITY_ARGS = @()
foreach ($r in @(<REQUIRED_ALL_NONLINEAR_CAPACITY_RECEIPT_PATHS_IN_LAWFUL_ORDER>)) { $NL_CAPACITY_ARGS += @("--capacity-receipt", $r) }
$NL_VERDICT_ARGS = @()
foreach ($v in @(<REQUIRED_ALL_NONLINEAR_VERDICT_PATHS_IN_LAWFUL_ORDER>)) { $NL_VERDICT_ARGS += @("--cap-verdict", $v) }

python "$Worktree\scripts\agent\build_full104_nonlinear_challenge_authority_v3_20260918.py" --cache-dir "$CACHE" --parameters-authority "$PARAMS" --model-capacity-authority "$RUN\nonlinear_capacity_model_authority_v1.json" --target-panel-authority "$RUN\target_panel_authority_v3.json" --precision-authority "$RUN\precision_authority_v4.json" --outer-split-authority "$RUN\outer_split_authority_v1.json" --sampling-plan "$NLQ\nonlinear_sampling_calibration_plan_v2.json" --sampling-receipt "$NLQ\nonlinear_sampling_calibration_receipt_v2.json" @NL_CAPACITY_ARGS @NL_VERDICT_ARGS --out "$RUN\nonlinear_challenge_authority_v3.json"
```

Build DesignAuthorityV2. It deliberately has no discovery address-universe-ladder root:

```powershell
python "$Worktree\scripts\agent\build_full104_masking_design_authority_v2_20260918.py" --repo "$Worktree" --representation-authority "$REPRESENTATION" --teacher-target-semantics-authority "$TEACHER_TARGET" --canonical-registry-authority "$REGISTRY_AUTH" --support-authority "$SUPPORT" --target-evidence-budget-template "$RUN\target_evidence_budget_template_v1.json" --burden-ladder-authority "$RUN\masking_burden_ladder_authority_v2.json" --precision-authority "$RUN\precision_authority_v4.json" --outer-split-authority "$RUN\outer_split_authority_v1.json" --target-panel-authority "$RUN\target_panel_authority_v3.json" --rng-authority "$RUN\masking_rng_replay_authority_v2.json" --out "$RUN\masking_qualification_design_authority_v2.json"
```

Do not recreate `AddressUniverseLadderAuthorityV1` from discovery 800/2,000/6,000 universes. Those remain historical scale-stress evidence only.

## 11. Final source freeze and machine checkpoint

After all source changes are committed and exact-head CI passes, rebuild the machine/worktree checkpoint on that exact clean GPU worktree:

```powershell
python "$Worktree\scripts\agent\update_work_checkpoint.py" --worktree "$Worktree" --state "$Worktree\docs\agent\CURRENT_WORK_CHECKPOINT_STATE.json" --checkpoint "$Worktree\docs\agent\CURRENT_WORK_CHECKPOINT.json" --takeover "$Worktree\docs\agent\CLAUDE_TAKEOVER.md"

python "$Worktree\scripts\agent\work_checkpoint.py" validate --worktree "$Worktree" --checkpoint "$Worktree\docs\agent\CURRENT_WORK_CHECKPOINT.json"
if ($LASTEXITCODE -ne 0) { throw "STOP: machine checkpoint validation failed" }
```

## 12. Build the final RunContract V4 from artifact paths only

The builder intentionally exposes no caller-entered `--*-sha256` role arguments.

```powershell
python "$Worktree\scripts\agent\build_full104_masking_run_contract_v4_20260918.py" --repo "$Worktree" --support-authority "$SUPPORT" --parameters-authority "$PARAMS" --census-authority "$CENSUS" --cache-dir "$CACHE" --target-evidence-budget-template "$RUN\target_evidence_budget_template_v1.json" --burden-ladder-authority "$RUN\masking_burden_ladder_authority_v2.json" --outer-split-authority "$RUN\outer_split_authority_v1.json" --target-panel-sizing-plan "$TPQ\target_panel_sizing_plan_v2.json" --control-calibration-precision-plan "$TPQ\control_calibration_precision_plan_v2.json" --target-panel-sizing-receipt "$TPQ\target_panel_sizing_receipt_v2.json" --target-panel-authority "$RUN\target_panel_authority_v3.json" --target-selection-receipt "$RUN\target_panel_selection_v2.json" --precision-authority "$RUN\precision_authority_v4.json" --model-capacity-authority "$RUN\nonlinear_capacity_model_authority_v1.json" --nonlinear-sampling-plan "$NLQ\nonlinear_sampling_calibration_plan_v2.json" --nonlinear-sampling-receipt "$NLQ\nonlinear_sampling_calibration_receipt_v2.json" --nonlinear-authority "$RUN\nonlinear_challenge_authority_v3.json" --rng-authority "$RUN\masking_rng_replay_authority_v2.json" --design-authority "$RUN\masking_qualification_design_authority_v2.json" --machine-checkpoint "$Worktree\docs\agent\CURRENT_WORK_CHECKPOINT.json" --out "$RUN\masking_qualification_run_contract_v4.json"
```

This builder reconstructs current typed objects, validates exact-current support semantics, binds the calibration cache only as provenance, derives live source hashes itself, binds the checkpoint semantic digest, and requires terminal input role `AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1`.

## 13. Terminal-mode preflight

Only after RunContract V4 exists:

```powershell
powershell -ExecutionPolicy Bypass -File "$Worktree\scripts\agent\v5_full104_masking_gpu_preflight_20260918.ps1" -Mode Terminal -ExpectedScientificAnchor $ExpectedAnchor -CanonicalRepo $Repo -Worktree $Worktree -Level4Root $L4 -ObservationState $OBS -Registry $REGISTRY -ParametersAuthority $PARAMS -CensusAuthority $CENSUS -SplitReceipt $SPLIT -TargetEligibility $ELIG -CacheDir $CACHE -TargetPanelAuthority "$RUN\target_panel_authority_v3.json" -PrecisionAuthority "$RUN\precision_authority_v4.json" -OuterSplitAuthority "$RUN\outer_split_authority_v1.json" -NonlinearAuthority "$RUN\nonlinear_challenge_authority_v3.json" -RngAuthority "$RUN\masking_rng_replay_authority_v2.json" -RunContract "$RUN\masking_qualification_run_contract_v4.json" -MachineCheckpoint "$Worktree\docs\agent\CURRENT_WORK_CHECKPOINT.json"
```

Any failure is a STOP.

## 14. Terminal masking boundary

The current one-rung terminal evidence assembler, mechanical controls, and one-rung executor are implemented and exact-head CI tested. Terminal execution is still STOPPED until GPU control/calibration authority instances, final RunContract V4, final machine checkpoint, terminal preflight, and an independent exact-head audit are complete. Do not substitute the older 2026-09-16 runner, a historical results file, a calibration-cache evaluator, or hand-assembled decision JSON.

Only after that current terminal executor exists and terminal preflight passes may the 5% FULL104 terminal rung be opened.

- start at 5%;
- do not inspect 10% if 5% fully qualifies;
- escalate only after explicit failure;
- stop at the first fully qualifying rung;
- calibration cache remains forbidden as terminal execution input;
- no post-outcome parameter retuning.

A masking PASS still does not authorize training. Healthy-current-teacher remaining-RNA necessity, measurement robustness, production geometry + geometry-specific memorization, current runtime provenance, and an explicit final training authority remain open.

## Permanent anti-spillover rules

- no Stage81/T1/discovery matrix as FULL104;
- no historical target list, fold map, burden, seed, row cap, or selected policy as current authority;
- no historical/non-current same-schema authority document at FULL104 ingress;
- no provisional September 17 support placeholder root;
- no discovery address-universe ladder in final Design V2;
- no caller-entered role SHA in the final RunContract builder;
- no placeholder SHA roots or free PASS strings;
- no calibration cache as terminal/training input;
- no historical T1 checkpoint as healthy-current-teacher authority;
- no post-outcome retuning;
- no reopening settled audits without changed inputs.


## September 18 audit-driven safeguards

At scientific head `3084c1f497a3db6056fd100fb896ccdf67318c8a`:
- terminal raw arrays/axes/masks are internally hash-bound;
- terminal assembly requires QualificationPrecisionAuthorityV4;
- source framing is fixed to the observed HVS/NPH52/SEA_AD populations;
- targeted policy improvement requires a per-source lower-bound guardrail;
- null tolerance is a prospectively frozen equivalence margin, never the observed negative-control width;
- the negative-control 95% CI must contain zero and fit wholly inside the frozen margin;
- replay/untreated identity/no-privileged-metadata come from a mechanical-control receipt;
- one-rung execution cannot auto-escalate and cannot continue after a lower rung qualifies;
- calibration cache remains forbidden as terminal input.

Exact-head CI: run `35392547631`, 268 passed in the regression step and 268 passed in the no-skip rerun.
