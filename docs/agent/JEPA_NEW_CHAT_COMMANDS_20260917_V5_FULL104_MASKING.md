# JEPA V5 — New Chat and GPU Handoff Commands

Date: 2026-09-17

Status: `STREAMING_MASKING_EXECUTOR_PARITY_CLOSED__CANONICAL_GPU_FULL104_QUALIFICATION_NEXT__TRAINING_OFF`

Verified code anchor:

`8ee5d0a5be483e18819a6f6975efa183327b2158`

Working branch:

`impl/v5-remaining-rna-target-semantics-20260917`

## 1. Exact prompt for a new ChatGPT window

Paste the following into the new chat **as the first message**:

> Continue the JEPA project from the current GitHub state. Do not restart the project or repeat settled audits.
>
> Repository: `dushyant-mishra/sea-ad-jepa-agent`
>
> First, connect to GitHub and re-fetch the live head of `impl/v5-remaining-rna-target-semantics-20260917`. The verified implementation code anchor is `8ee5d0a5be483e18819a6f6975efa183327b2158`; later commits may be governance/handoff artifacts, so verify the live ancestry rather than assuming the branch has not moved.
>
> Read these files completely and in this order:
>
> 1. `START_HERE.md`
> 2. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
> 3. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260917_V5_CANONICAL_MASKING_RUNTIME_CURRENT.md`
> 4. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260917_V5_CANONICAL_MASKING_RUNTIME_CURRENT.json`
> 5. `docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json`
> 6. `docs/agent/handoff_artifacts/20260917/V5_FULL104_MASKING_DATA_RESULTS_SCRIPTS_MANIFEST.json`
> 7. `docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md`
> 8. `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`
> 9. `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`
>
> Then verify the relevant source/tests:
>
> - `src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py`
> - `src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py`
> - `src/sea_ad_jepa/v5/masking_qualification_parameters_authority_v1.py`
> - `src/sea_ad_jepa/v5/masking_qualification_design_authority_v1.py`
> - `src/sea_ad_jepa/v5/masking_qualification_run_contract_v1.py`
> - `src/sea_ad_jepa/v5/masking_qualification_execution_authority_v2.py`
> - `tests/test_v5_full104_masking_qualification_runner_v1.py`
> - `tests/test_v5_full104_masking_streaming_executor_v1.py`
> - `tests/test_v5_masking_qualification_run_contract_v1.py`
>
> The streaming FULL104 masking adapter is already implemented and CI parity-verified. Do **not** redesign or redo it unless its inputs changed. At the verified code anchor all four current workflows passed: runtime closure `35278901437`, masking runner + streaming parity `35278901430`, remaining-RNA/target semantics `35278901433`, and Stage-A spillover `35278901569`. No skipped critical tests were accepted.
>
> Scientific semantics are fixed: the objective is biological/cellular state inference from partial RNA, including query-local state associated with a supplied canonical molecular address. It is not hidden-gene scalar imputation. Expression attackers are anti-shortcut diagnostics only.
>
> FULL104 is 4,553,407 cells, 104 donors, 42 operators, 41,238 addresses, 17,186 common-core addresses, 8,915 Level-4 blocks. Block-manifest SHA-256 is `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`.
>
> Heavy Level-4 data are on the GPU/external-drive machine at `D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`. Do not ask me to upload or duplicate the >30 GB substrate. Do not substitute a smaller cache.
>
> The next authorized boundary is:
>
> `canonical worktree checkpoint -> authenticated FULL104 Level-4 binding -> prospectively freeze masking design + numeric parameters + exact source hashes/run contract -> only then execute the ladder through FULL_COMMON_CORE_17186_V1`.
>
> Before expensive execution, run `scripts/agent/v5_full104_masking_gpu_preflight_20260917.ps1` on the GPU worktree and validate `CURRENT_WORK_CHECKPOINT.json`. If the worktree is dirty, preserve it and STOP rather than reset/stash/clean automatically.
>
> Do not inspect terminal masking outcomes before the prospective run contract is frozen. Keep training OFF. Do not open D_shared, pathology, DEV or SEALED outcomes. Do not promote RIDGE8, cap 8, 15% mask burden, alpha 0.01, PREFIX3 thresholds, or any other exploratory choice merely because it performed well in discovery.
>
> Supporting exploratory science is on `analysis/v5-ridge8-expanded-validation-20260917` at `99dc3a6ff5f540fac17e86b135f2c6710bb41405`; it is supporting evidence, not production masking authority.
>
> Before repeating any historical work, classify it as `ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`. Do not reopen FULL104 lineage, VALUE_ONLY_256, support/estimability, base estimand, T0/T1/C2, QID/F1, Stage81A3, Layer-2, Stage-A structural qualification, or streaming/reference parity unless an input actually changed.
>
> Work iteratively with independent self-check/red-team passes. Use GitHub actively. Do the work rather than just planning it. Never claim terminal FULL104 execution or training authority until real artifacts support it.

## 2. GPU machine — safe repository inspection

Open **PowerShell** on the GPU laptop.

Do not reset, clean, stash or switch away from a dirty user worktree.

```powershell
$Repo = "D:\Jepa project"
$Branch = "impl/v5-remaining-rna-target-semantics-20260917"

git -C $Repo fetch origin
git -C $Repo status --short
git -C $Repo worktree list
git -C $Repo rev-parse HEAD
git -C $Repo branch --show-current
git -C $Repo log -1 --oneline "origin/$Branch"
```

If `git status --short` prints anything, **STOP and preserve those changes**. Use an already-existing clean isolated worktree if one is available. Do not automatically stash or clean.

If you need a fresh inspection-only worktree and no suitable worktree exists:

```powershell
$Repo = "D:\Jepa project"
$Worktree = "D:\jepa_v5_full104_masking_20260917"
$Branch = "impl/v5-remaining-rna-target-semantics-20260917"

git -C $Repo fetch origin
git -C $Repo worktree add --detach $Worktree "origin/$Branch"
git -C $Worktree status --short
git -C $Worktree rev-parse HEAD
```

The detached worktree is appropriate for verification/preflight. Do not create another remote branch unless implementation changes are actually required.

## 3. Run the committed GPU preflight

Against a clean worktree:

```powershell
$Repo = "D:\Jepa project"
$Worktree = "D:\jepa_v5_full104_masking_20260917"
$Level4 = "D:\Jepa project\outputs\full104_v014_20260826\03_phase2_state_derivation_v1\expression_level4"

powershell -ExecutionPolicy Bypass -File "$Worktree\scripts\agent\v5_full104_masking_gpu_preflight_20260917.ps1" -CanonicalRepo $Repo -Worktree $Worktree -Level4Root $Level4
```

The script must:

- verify that `8ee5d0a5be483e18819a6f6975efa183327b2158` is an ancestor of the worktree HEAD;
- refuse a dirty worktree;
- rerun the focused canonical-runner/streaming-parity and Stage-A tests;
- build and validate `docs/agent/CURRENT_WORK_CHECKPOINT.json`;
- verify the FULL104 Level-4 block-manifest SHA-256;
- compute the exact SHA-256 of the canonical masking reference and streaming executor sources;
- stop before any terminal scientific outcome is inspected.

A successful preflight is **not** masking authority and is **not** training authority.

## 4. Manual checkpoint commands, if needed

The committed preflight already performs this. These are the explicit equivalents:

```powershell
$Worktree = "D:\jepa_v5_full104_masking_20260917"

python "$Worktree\scripts\agent\update_work_checkpoint.py" --worktree $Worktree --state "$Worktree\docs\agent\CURRENT_WORK_CHECKPOINT_STATE.json" --checkpoint "$Worktree\docs\agent\CURRENT_WORK_CHECKPOINT.json" --takeover "$Worktree\docs\agent\CLAUDE_TAKEOVER.md"

python "$Worktree\scripts\agent\work_checkpoint.py" validate --worktree $Worktree --checkpoint "$Worktree\docs\agent\CURRENT_WORK_CHECKPOINT.json"
```

Expected validator result: `PASS`. Any mismatch is a STOP.

## 5. Exact source hashes for the prospective run contract

Compute these **on the execution worktree after preflight**:

```powershell
$Worktree = "D:\jepa_v5_full104_masking_20260917"

Get-FileHash -Algorithm SHA256 "$Worktree\src\sea_ad_jepa\v5\full104_masking_qualification_runner_v1.py"
Get-FileHash -Algorithm SHA256 "$Worktree\src\sea_ad_jepa\v5\full104_masking_streaming_executor_v1.py"
```

Do not copy a hash from this document. Compute the exact live execution-source digests and bind those values into the prospective authorities/run contract.

## 6. FULL104 Level-4 physical authentication

```powershell
$Level4 = "D:\Jepa project\outputs\full104_v014_20260826\03_phase2_state_derivation_v1\expression_level4"
$Expected = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"

$Actual = (Get-FileHash -Algorithm SHA256 "$Level4\PHASE2_EXPRESSION_BLOCK_MANIFEST.csv").Hash.ToLowerInvariant()
$Actual
if ($Actual -ne $Expected) { throw "STOP: FULL104 block manifest SHA mismatch" }

Test-Path "$Level4\MATERIALIZATION_CONTRACT.json"
Test-Path "$Level4\PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json"
```

All checks must pass before the substrate is used.

## 7. What the new chat must freeze before any terminal outcome

The next chat should instantiate and review the already-defined authority schemas rather than inventing replacements:

1. current physical FULL104 binding;
2. support eligibility binding;
3. outer split;
4. target panel;
5. address-universe ladder with terminal `FULL_COMMON_CORE_17186_V1`;
6. target evidence budget;
7. precision rule;
8. masking qualification design;
9. numeric masking parameter authority;
10. exact canonical-reference source SHA-256;
11. exact streaming-executor source SHA-256;
12. deterministic RNG/replay authority;
13. final prospective run contract.

Only after that contract is frozen may terminal masking outcomes be inspected.

## 8. Terminal execution boundary

The actual terminal runner invocation is intentionally **not hardcoded here**, because the current authority objects must first be instantiated from the authenticated live bindings and numeric choices. A command that silently invents those arguments would violate the prospective-freeze rule.

The next chat should create/review the concrete execution entrypoint **after** items 1–13 above are frozen, then independently verify it before launching expensive FULL104 compute.

Required terminal endpoint:

`FULL_COMMON_CORE_17186_V1`

Required reporting includes:

- primary paired target x outer-fold estimands;
- source-balanced donor-centered correlation-squared attack score;
- target-clustered precision/uncertainty;
- positive control;
- shuffled negative control;
- untreated mask identity;
- deterministic replay;
- no-privileged-metadata control;
- nonlinear challenge without retuning;
- explicit PASS with a fixed selected policy or FAIL with `NO_POLICY_QUALIFIED`.

## 9. What remains after masking qualification

Even a masking PASS does **not** authorize training.

Still required:

- selected masking policy authority from real execution;
- healthy-current-teacher remaining-RNA necessity evidence;
- current measurement robustness evidence;
- production geometry selection;
- geometry-specific memorization qualification;
- current runtime source/environment provenance;
- real current authority-graph closure;
- explicit final training authority.

Training stays OFF until all applicable gates close.
