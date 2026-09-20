# Reproduction sequence for the FULL104 pass1 rebuild.
#
# EXECUTION ANCHOR CORRECTION
# ---------------------------
# An earlier version of this script stated that the pass1 builder and its test
# suite ran from a clean worktree at PR #29 head 1fef4452. That was false:
#   src/sea_ad_jepa/v5/full104_pass1_builder_v1.py
#   tests/test_v5_full104_pass1_builder_v1.py
# do not exist at 1fef4452. They first appear in the PR #31 successor commit.
# The original run had those two files copied into a PR29 worktree as untracked
# files, so that worktree was not clean and the stated anchor was wrong.
#
# This script therefore does NOT hard-code an anchor it cannot verify. It reads
# HEAD from the worktree it runs in, refuses to proceed unless that worktree is
# clean AND actually contains the builder and its test at that commit, and
# records the SHA-256 of the code that executes.
#
# Run from a clean worktree at the PR #31 successor head, which descends from
# PR #29 and therefore already carries the exact-decimal source_library parser.
#
# Nothing here opens a terminal masking outcome, target-panel ladder,
# null-equivalence margin, D_shared, protected/pathology/DEV/SEALED outcome,
# or training.

param(
  [Parameter(Mandatory=$true)][string]$Worktree,
  [string]$Python  = "C:\Users\dushy\anaconda3\envs\sea-ad-jepa\python.exe",
  [string]$Level4  = "C:\jepa_full104_ssd\expression_level4",
  [string]$OutRoot = "D:\jepa_full104_preterminal_20260919_a51cdbe8_outputs"
)

$ErrorActionPreference = "Stop"

$REGISTRY  = "D:\Jepa project\exports\foundation_calibration_bundle_20260824\contracts\address_namespace.csv"
$OBS       = "D:\Jepa project\exports\foundation_calibration_bundle_20260824\support\FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
$L4_SOURCE = "D:\Jepa project\outputs\full104_v014_20260826\03_phase2_state_derivation_v1\expression_level4"

$SHA_MANIFEST = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
$SHA_REGISTRY = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
$SHA_OBS      = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"

$BUILDER = "src/sea_ad_jepa/v5/full104_pass1_builder_v1.py"
$BTEST   = "tests/test_v5_full104_pass1_builder_v1.py"

# --------------------------------------- 0. VERIFY the anchor; never assert it
if (git -C $Worktree status --porcelain) { throw "worktree is dirty; refusing to run" }
$HEAD = (git -C $Worktree rev-parse HEAD).Trim()

foreach ($f in @($BUILDER, $BTEST)) {
  git -C $Worktree cat-file -e "${HEAD}:$f" 2>$null
  if ($LASTEXITCODE -ne 0) {
    throw "$f does not exist at $HEAD -- not a valid execution anchor for the builder"
  }
}

Write-Output "execution_anchor_git_oid : $HEAD"
Write-Output "builder_sha256           : $((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Worktree $BUILDER)).Hash.ToLower())"
Write-Output "builder_test_sha256      : $((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Worktree $BTEST)).Hash.ToLower())"
& $Python -c "import sys,numpy,scipy,torch;print('python',sys.version.split()[0],'numpy',numpy.__version__,'scipy',scipy.__version__,'torch',torch.__version__)"

# ------------------------------- 1. stage Level-4 to SSD (COPY, never move)
# D: remains the source-of-record. Names/structure preserved. No CSV is rewritten.
if (-not (Test-Path -LiteralPath $Level4)) {
  robocopy $L4_SOURCE $Level4 /E /COPY:DAT /R:2 /W:2 /NFL /NDL /NJH /NP /MT:8
  if ($LASTEXITCODE -ge 8) { throw "robocopy failed" }   # 0-7 are success codes
}
foreach ($pair in @(
    @{p="$Level4\PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"; s=$SHA_MANIFEST},
    @{p=$REGISTRY; s=$SHA_REGISTRY},
    @{p=$OBS;      s=$SHA_OBS})) {
  $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $pair.p).Hash.ToLower()
  if ($h -ne $pair.s) { throw "root mismatch: $($pair.p)" }
}

Push-Location $Worktree
$env:PYTHONPATH = "src;."

# --------------------------------------------------- 2. fresh runtime envelope
$RT = "$OutRoot\_shakedown_runtime_$($HEAD.Substring(0,8))"
& $Python scripts\agent\prepare_full104_runtime_envelope_v1.py `
    --mode prepare --runtime-root $RT --worktree $Worktree `
    --expected-scientific-anchor $HEAD `
    --level4-root $Level4 --registry $REGISTRY --observation-state $OBS

# ------------------------------------------------------- 3. physical shakedown
# The receipt must be written INSIDE the envelope. ~131 min on this hardware.
& $Python scripts\agent\run_full104_physical_shakedown_v1.py `
    --runtime-root $RT --worktree $Worktree `
    --expected-scientific-anchor $HEAD `
    --level4-root $Level4 --registry $REGISTRY --observation-state $OBS `
    --out "$RT\full104_physical_shakedown_receipt_v1.json"
# expected: FULL104_PHYSICAL_SHAKEDOWN_PASS
#           8,915 blocks / 4,553,407 rows / 104 donors / 23,690,278,596 nnz

# ---------------------------- 4. build selection_row-keyed pass1 (~29 min)
$PASS1 = "$OutRoot\full104_pass1_v2_selection_row_keyed.npz"
& $Python -c @"
import sys; sys.path.insert(0,'src')
from pathlib import Path
from sea_ad_jepa.v5.full104_pass1_builder_v1 import build_pass1_from_physical_full104
print(build_pass1_from_physical_full104(
    level4_root=Path(r'$Level4'),
    registry_path=Path(r'$REGISTRY'),
    observation_state_path=Path(r'$OBS'),
    out_path=Path(r'$PASS1'),
    expect_reference_geometry=True).as_dict())
"@
Write-Output "pass1_sha256 : $((Get-FileHash -Algorithm SHA256 -LiteralPath $PASS1).Hash.ToLower())"
# expected: 37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1

# ------------------------- 5. independent verifier + census receipts (~20 min)
# full104_pass1_physical_binding_v1.py is UNMODIFIED and is the sole verifier.
$C = "$OutRoot\census_$($HEAD.Substring(0,8))"
New-Item -ItemType Directory -Force -Path $C | Out-Null
& $Python analysis\v5_full104_census_20260918\full104_readonly_census_receipts_v2.py `
    --pass1 $PASS1 `
    --level4-root $Level4 --registry $REGISTRY --observation-state $OBS `
    --out-pass1-physical-binding "$C\full104_pass1_physical_binding_v1.json" `
    --out-summary               "$C\full104_census_summary_v2.json" `
    --out-split                 "$C\full104_split_receipt_v1.json" `
    --out-target-eligibility    "$C\full104_target_eligibility_v1.json"
# expected: 17,053 all-fold eligible; per-fold 17,070/17,071/17,072/17,060

# ------------------------------------------------------------------ 6. tests
& $Python -m pytest -q -p no:randomly --strict-markers -rs `
    tests\test_v5_full104_pass1_builder_v1.py `
    tests\test_v5_full104_pass1_physical_binding_v1.py `
    tests\test_v5_full104_physical_shakedown_v1.py `
    tests\test_v5_full104_runtime_envelope_v1.py `
    tests\test_v5_full104_census_receipt_v2.py

# --------------------------------------------------------------- 7. audit checks
# Required checks; a NOT_MEASURABLE result makes the overall audit non-PASS.
& $Python analysis\v5_full104_pass1_rebuild_20260920\scripts\audit_checks_20260920.py --check all

Pop-Location

# NOT RUN, deliberately: control-calibration cache, preterminal authorities,
# target-panel ladder, margin selection, terminal run contract, any masking rung.
