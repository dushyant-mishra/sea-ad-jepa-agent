# JEPA V5 — audited FULL104 safe-lane commands/status — 2026-09-19

Scientific branch: `impl/v5-full104-provenance-spillover-repair-20260919`

Scientific head: `a51cdbe8bbfac1c77980711cca13df8bc58caa1d`

This file intentionally contains **no executable terminal masking command**.

## 1. Start by verifying the exact scientific worktree

```powershell
$Repo = "D:\Jepa project"
$Branch = "impl/v5-full104-provenance-spillover-repair-20260919"
$ExpectedScientificHead = "a51cdbe8bbfac1c77980711cca13df8bc58caa1d"

git -C $Repo fetch origin
if ((git -C $Repo rev-parse "origin/$Branch").Trim() -ne $ExpectedScientificHead) { throw "STOP: branch moved; audit delta first" }
```

Use a clean dedicated execution worktree at the scientific head. Do not run from the docs/handoff branch.

## 2. Canonical local environment

Use conda env:

`sea-ad-jepa`

Do not use `base` for authority-bearing local execution.

Record Python, executable path, torch/CUDA/device, numpy/scipy/sklearn/pandas and complete package list in the evidence package.

## 3. Canonical physical inputs

```powershell
$L4 = "D:\Jepa project\outputs\full104_v014_20260826\03_phase2_state_derivation_v1\expression_level4"
$REGISTRY = "D:\Jepa project\exports\foundation_calibration_bundle_20260824\contracts\address_namespace.csv"
$OBS = "<current FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz path>"
```

Expected roots:

- manifest `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
- registry `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- observation state `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`

## 4. Old pass1 is forbidden

Do not use the September-17 pass1 as current input.

Classification:

`INVALID_FOR_CURRENT_ROLE__ROW_IDENTITY_KEYED_TO_BLOCK_ITERATION_ORDER`

Do not repair it by permutation.

The next lawful census run requires a newly produced physical pass1 keyed by `selection_row` and independently verified by the unchanged current physical-binding verifier.

## 5. Physical shakedown may run independently

The shakedown is non-terminal and may run in a prepared fresh runtime envelope:

```powershell
python "$Repo\scripts\agent\prepare_full104_runtime_envelope_v1.py" --mode prepare --runtime-root "<fresh sibling runtime dir>" --worktree "<clean scientific worktree>" --expected-scientific-anchor "$ExpectedScientificHead" --level4-root "$L4" --registry "$REGISTRY" --observation-state "$OBS"

python "$Repo\scripts\agent\run_full104_physical_shakedown_v1.py" --runtime-root "<same runtime dir>" --worktree "<clean scientific worktree>" --expected-scientific-anchor "$ExpectedScientificHead" --level4-root "$L4" --registry "$REGISTRY" --observation-state "$OBS" --out "<runtime dir>\full104_physical_shakedown_receipt_v1.json"
```

Do not claim PASS until receipt/log is returned and independently checked.

## 6. After a new pass1 exists

Run current physical binding/census receipt code only against the newly built pass1:

`analysis/v5_full104_census_20260918/full104_readonly_census_receipts_v2.py`

Then build:

`scripts/agent/build_full104_census_authority_v2_20260918.py`

Only if that physical chain passes may you build:

`scripts/agent/build_full104_control_calibration_cache_v1.py`

and safe outcome-blind authorities:

- `build_full104_outer_split_authority_v1_20260918.py`
- `build_full104_target_evidence_budget_template_authority_v1_20260918.py`
- `build_full104_burden_ladder_authority_v2_20260918.py`
- `build_full104_masking_parameters_authority_v3_20260919.py`

The calibration cache remains:

`CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1`

## 7. Representation parent authentication

Only when exact V0/V1 parent bytes are located by SHA:

`scripts/agent/build_full104_primary_representation_routing_v1_20260919.py`

This authenticates parent bytes but does not close F13 until the production consumer is bound.

## 8. Hard STOP list

Do not execute target-panel capacity ladder while H3 is open.

Do not type a null-equivalence margin while G5 is open.

Do not build terminal PrecisionAuthority V4 from a convenient number.

Do not build terminal RunContract.

Do not execute 5% or any higher terminal burden.

Do not select a masking policy.

Do not inspect D_shared/protected/pathology outcomes.

Do not train.

`TRAINING_OFF`
