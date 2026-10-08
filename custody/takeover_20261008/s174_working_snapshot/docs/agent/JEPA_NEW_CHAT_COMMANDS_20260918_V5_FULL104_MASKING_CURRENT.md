# JEPA V5 — CURRENT FULL104 preterminal execution commands

Date: 2026-09-19

Status: `PRETERMINAL_FULL104_SAFE_LANE_ONLY__H3_G5_TERMINAL_LOCKED__TRAINING_OFF`

Scientific source/test/workflow anchor for this command revision:

`1323da9dd34b5437098749c8fc40d1033090784f`

This file supersedes the earlier September 18 command sequence wherever the
earlier sequence attempted target-panel sizing, a caller-entered equivalence
margin, terminal run-contract construction, or terminal masking execution.

## Permanent scope

Historical/smaller-run artifacts may motivate a current hypothesis, guard, or
explicitly re-authorized parameter-origin statement only. They may not occupy a
FULL104 runtime role, data root, target list, fold, burden, seed, row cap,
selected policy, PASS state, representation parent, geometry, teacher authority,
or training authority unless a current authority binds the exact current
FULL104 roots.

In particular:

- no Stage81/T1/discovery/50k artifact is FULL104;
- no placeholder is an authority;
- no historical pass1 is accepted from geometry/count coincidence;
- no caller-entered role SHA is accepted when it can be recomputed;
- `AddressUniverseLadderAuthorityV1` discovery universes are not current terminal universes;
- the calibration cache role remains
  `CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1`;
- terminal execution input, when eventually authorized, is
  `AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1`;
- do not use `scripts/agent/v5_full104_masking_gpu_preflight_20260917.ps1`;
- `TRAINING_OFF`.

## 1. Re-fetch and preserve the exact worktree

```powershell
$Repo = "D:\Jepa project"
$Worktree = $Repo
$Branch = "impl/v5-full104-provenance-spillover-repair-20260919"
$ExpectedScientificAnchor = "1323da9dd34b5437098749c8fc40d1033090784f"

git -C $Repo fetch origin
git -C $Repo status --porcelain
git -C $Repo rev-parse "origin/$Branch"
git -C $Repo log -1 --oneline "origin/$Branch"
```

If the worktree is dirty, preserve it and STOP. Do not reset, clean, stash,
rebase, or overwrite user changes automatically. If source/test/workflow bytes
moved after the expected scientific anchor, classify the changed dependency cone
before running the GPU lane.

## 2. Required physical FULL104 inputs

```powershell
$L4 = "D:\Jepa project\outputs\full104_v014_20260826\03_phase2_state_derivation_v1\expression_level4"
$RUN = "<REQUIRED_NEW_EMPTY_FULL104_RUNTIME_OUTPUT_DIRECTORY>"
$PASS1 = "<REQUIRED_REAL_FULL104_PASS1_NPZ>"
$OBS = "<REQUIRED_CURRENT_OPERATOR_ADDRESS_OBSERVATION_STATE_NPZ>"
$REGISTRY = "<REQUIRED_AUTHENTICATED_41238_ROW_CANONICAL_REGISTRY_CSV>"
$V0_FULL = "<REQUIRED_AUTHENTICATED_V0_FULL_PARENT_FILE>"
$V1_FULL = "<REQUIRED_AUTHENTICATED_V1_FULL_PARENT_FILE>"
$WORKERS = <REQUIRED_POSITIVE_INTEGER>

$SUPPORT = "$Worktree\docs\agent\V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json"

$ExpectedL4 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
$ExpectedObs = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
$ExpectedRegistry = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"

if ((Get-FileHash -Algorithm SHA256 "$L4\PHASE2_EXPRESSION_BLOCK_MANIFEST.csv").Hash.ToLowerInvariant() -ne $ExpectedL4) { throw "STOP: FULL104 manifest mismatch" }
if ((Get-FileHash -Algorithm SHA256 $OBS).Hash.ToLowerInvariant() -ne $ExpectedObs) { throw "STOP: observation-state mismatch" }
if ((Get-FileHash -Algorithm SHA256 $REGISTRY).Hash.ToLowerInvariant() -ne $ExpectedRegistry) { throw "STOP: canonical registry mismatch" }
```

Angle-bracket values are unresolved machine paths, not placeholders that may be
written into an authority.

## 3. Build the current FULL104-bound confirmation-parameter authority

The old discovery work is parameter-origin provenance only. This command hashes
the current FULL104 manifest and current support authority before issuing the
conditional 32-feature confirmation authority. It does not close G3.

```powershell
python "$Worktree\scripts\agent\build_full104_masking_parameters_authority_v3_20260919.py" --repo "$Worktree" --level4-root "$L4" --support-authority "$SUPPORT" --out "$RUN\masking_parameters_authority_v3.json"
$PARAMS = "$RUN\masking_parameters_authority_v3.json"
```

## 4. Physically bind the real pass1 and regenerate census receipts

The pass1 NPZ is a derived acceleration artifact, not authority from its shape or
summary counts. The census command independently authenticates all physical
Level-4 block hashes, the registry, and the observation-state matrix; recomputes
the strict common core; checks selection-row→donor/source identity; recomputes
per-cell strict-core nonzero counts; and recomputes donor×core nonzero support.

```powershell
$PASS1_BINDING = "$RUN\full104_pass1_physical_binding_v1.json"

python "$Worktree\analysis\v5_full104_census_20260918\full104_readonly_census_receipts_v2.py" --pass1 "$PASS1" --level4-root "$L4" --registry "$REGISTRY" --observation-state "$OBS" --out-pass1-physical-binding "$PASS1_BINDING" --out-summary "$RUN\full104_census_summary_v2.json" --out-split "$RUN\full104_split_receipt_v1.json" --out-target-eligibility "$RUN\full104_target_eligibility_v1.json"

python "$Worktree\scripts\agent\build_full104_census_authority_v2_20260918.py" --repo "$Worktree" --level4-root "$L4" --observation-state "$OBS" --registry "$REGISTRY" --pass1 "$PASS1" --pass1-physical-binding "$PASS1_BINDING" --summary "$RUN\full104_census_summary_v2.json" --split "$RUN\full104_split_receipt_v1.json" --target-eligibility "$RUN\full104_target_eligibility_v1.json" --support-authority "$SUPPORT" --out "$RUN\full104_census_authority_v2.json"

$CENSUS = "$RUN\full104_census_authority_v2.json"
$SPLIT = "$RUN\full104_split_receipt_v1.json"
$ELIG = "$RUN\full104_target_eligibility_v1.json"
```

STOP on any failure to reproduce exactly 4,553,407 rows, 104 donors, 42
operators, the current source identities, the 17,186 strict common core, or the
17,053 all-fold eligible target geometry.

## 5. Build the authenticated calibration-only cache

```powershell
$CACHE = "$RUN\control_calibration_cache_v1"

python "$Worktree\scripts\agent\build_full104_control_calibration_cache_v1.py" --level4-root "$L4" --registry "$REGISTRY" --census-authority "$CENSUS" --pass1-physical-binding "$PASS1_BINDING" --split-receipt "$SPLIT" --target-eligibility "$ELIG" --support-authority "$SUPPORT" --out-dir "$CACHE"
```

The cache manifest must carry the exact physical pass1 binding root. Never use
this cache as terminal masking input or training input.

## 6. Safe outcome-blind authorities

Outer donor split:

```powershell
python "$Worktree\scripts\agent\build_full104_outer_split_authority_v1_20260918.py" --split-receipt "$SPLIT" --out "$RUN\outer_split_authority_v1.json"
```

Burden-free evidence-budget template and census-derived burden ladder:

```powershell
python "$Worktree\scripts\agent\build_full104_target_evidence_budget_template_authority_v1_20260918.py" --level4-root "$L4" --observation-state "$OBS" --support-authority "$SUPPORT" --census-authority "$CENSUS" --out "$RUN\target_evidence_budget_template_v1.json"

python "$Worktree\scripts\agent\build_full104_burden_ladder_authority_v2_20260918.py" --census-authority "$CENSUS" --out "$RUN\masking_burden_ladder_authority_v2.json"
```

These do not select a masking burden or inspect terminal outcomes.

## 7. Fresh runtime envelope and physical shakedown

Prepare a genuinely fresh runtime directory. The envelope is bound to the live
clean Git HEAD and current FULL104 roots; runtime contents are allowlisted rather
than accepted merely because their filenames look harmless.

```powershell
$SHAKEDOWN = "<REQUIRED_NEW_EMPTY_FULL104_SHAKEDOWN_DIRECTORY>"

python "$Worktree\scripts\agent\prepare_full104_runtime_envelope_v1.py" --mode prepare --runtime-root "$SHAKEDOWN" --worktree "$Worktree" --expected-scientific-anchor "$ExpectedScientificAnchor" --level4-root "$L4" --registry "$REGISTRY" --observation-state "$OBS"

python "$Worktree\scripts\agent\run_full104_physical_shakedown_v1.py" --runtime-root "$SHAKEDOWN" --worktree "$Worktree" --expected-scientific-anchor "$ExpectedScientificAnchor" --level4-root "$L4" --registry "$REGISTRY" --observation-state "$OBS" --out "$SHAKEDOWN\full104_physical_shakedown_receipt_v1.json"
```

The shakedown authenticates all blocks and metadata and applies the exact
production sparse `log1p(count * 10000 / source_library)` transform to every
nonzero while recording throughput and memory. It remains read-only and
non-terminal.

Validation-only mode remains available:

```powershell
python "$Worktree\scripts\agent\prepare_full104_runtime_envelope_v1.py" --mode validate --runtime-root "$SHAKEDOWN" --worktree "$Worktree" --expected-scientific-anchor "$ExpectedScientificAnchor"
```

## 8. Authenticate the current representation parents without claiming F13 closure

```powershell
python "$Worktree\scripts\agent\build_full104_primary_representation_routing_v1_20260919.py" --repo "$Worktree" --level4-root "$L4" --registry "$REGISTRY" --observation-state "$OBS" --v0-full-parent "$V0_FULL" --v1-full-parent "$V1_FULL" --out "$RUN\primary_representation_routing_v1.json"
```

This authenticates the current physical V0/V1 parents and enforces value channels
`[0:256)` versus visibility/QC `[256:512)`. It intentionally records
`production_model_consumer_bound = false`; therefore F13 remains open until the
actual production consumer is bound.

## 9. Calibration preflight

After the safe artifacts above exist and exact-head CI is green, calibration-mode
preflight may validate their closure. It must not open target-panel or terminal
outcomes.

Use the current September-18 preflight only. The September-17 preflight is
superseded and forbidden:

`v5_full104_masking_gpu_preflight_20260917.ps1`

## 10. H3/G5 hard STOP — do not execute the target-panel ladder

`STOP_H3_EQUIVALENCE_POWER_OPEN`

The current V2 target-panel ladder measures planted-shortcut superiority/capacity,
not equivalence precision for the terminal residual-within-margin claim.
Accordingly, do not execute the target-panel ladder.

The planted-shortcut capacity evidence remains supporting positive-control evidence only.
It may demonstrate that an attacker can detect an easy planted shortcut; it may
not select/freeze the production target-panel size.

## 11. G5 hard STOP — do not type a convenient margin

`STOP_G5_NULL_EQUIVALENCE_MARGIN_BASIS_OPEN`

Do not build terminal PrecisionAuthorityV4 from caller-entered numerator or
denominator values. A prospective scientific margin basis must be independently
justified/frozen first, then H3 equivalence-power/precision sizing must be defined
against that basis.

## 12. Terminal run-contract and one-rung execution remain shut

`STOP_H3_G5_TERMINAL_RUN_CONTRACT_UNAUTHORIZED`

`STOP_H3_G5_TERMINAL_MASKING_UNAUTHORIZED`

Do not construct the terminal run contract. Do not execute 5%. Do not inspect
10–50%. Do not select a masking policy.

No executable command for the blocked target-panel evaluator, terminal precision
builder, or terminal run-contract builder appears in this current command
authority by design.

## 13. Still-open scientific/mechanics blockers

Before terminal masking can reopen:

- H3: equivalence-power/precision panel sizing;
- G5: prospective scientific equivalence-margin basis;
- H4: preregister all-rung FAIL_CLOSED interpretations;
- G2: scientifically justify targeting-complexity materiality across panel sizes;
- G3: capacity-matched/deep shortcut gate beyond the 32-feature confirmation attacker;
- G4: prospective biological/state-signal preservation criterion;
- F13: prove the actual production model consumes the authenticated representation route;
- F14: prove current production dimension/rank/subspace authority;
- F15: prove actual production teacher/student mechanics.

Historical findings remain in perspective: they determine which regressions and
failure modes deserve protection, not current FULL104 outcomes or authorities.

A future masking PASS still does not authorize training.

`TRAINING_OFF`
