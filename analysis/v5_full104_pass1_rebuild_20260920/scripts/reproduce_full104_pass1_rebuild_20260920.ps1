# Exact command sequence used for the 2026-09-20 FULL104 pass1 rebuild.
#
# Every path, hash and anchor below is the one actually used. Nothing here opens
# a terminal masking outcome, target-panel ladder, null-equivalence margin,
# D_shared, protected/pathology/DEV/SEALED outcome, or training.
#
# Canonical environment: conda env `sea-ad-jepa` (NOT `base`).
# Scientific anchor:     1fef4452e7d9b178adc532eef9786996e412943f  (PR #29)

$ErrorActionPreference = "Stop"

$PY        = "C:\Users\dushy\anaconda3\envs\sea-ad-jepa\python.exe"
$WORKTREE  = "D:\jepa_pr29_20260920"
$ANCHOR    = "1fef4452e7d9b178adc532eef9786996e412943f"
$OUT       = "D:\jepa_full104_preterminal_20260919_a51cdbe8_outputs"

# Source-of-record stays on D:. The SSD copy is what we read from.
$L4_SOURCE = "D:\Jepa project\outputs\full104_v014_20260826\03_phase2_state_derivation_v1\expression_level4"
$L4        = "C:\jepa_full104_ssd\expression_level4"
$REGISTRY  = "D:\Jepa project\exports\foundation_calibration_bundle_20260824\contracts\address_namespace.csv"
$OBS       = "D:\Jepa project\exports\foundation_calibration_bundle_20260824\support\FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"

# Expected immutable roots.
$SHA_MANIFEST = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
$SHA_REGISTRY = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
$SHA_OBS      = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"

# ---------------------------------------------------------------- 0. worktree
# The scientific worktree must be clean; run outputs live OUTSIDE it, otherwise
# the runtime envelope correctly refuses to run.
if (git -C $WORKTREE status --porcelain) { throw "scientific worktree is dirty" }
if ((git -C $WORKTREE rev-parse HEAD) -ne $ANCHOR) { throw "worktree HEAD is not the anchor" }

# ------------------------------------------------------- 1. stage Level-4 to SSD
# COPY, never move. Preserve names/structure. Do not rewrite any CSV.
robocopy $L4_SOURCE $L4 /E /COPY:DAT /R:2 /W:2 /NFL /NDL /NJH /NP /MT:8
if ($LASTEXITCODE -ge 8) { throw "robocopy failed" }   # 0-7 are success codes

foreach ($pair in @(
    @{p="$L4\PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"; s=$SHA_MANIFEST},
    @{p=$REGISTRY; s=$SHA_REGISTRY},
    @{p=$OBS;      s=$SHA_OBS})) {
  $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $pair.p).Hash.ToLower()
  if ($h -ne $pair.s) { throw "root mismatch: $($pair.p)" }
}

# --------------------------------------------------- 2. fresh runtime envelope
$RT = "$OUT\_shakedown_runtime_pr29_ssd"
Push-Location $WORKTREE
$env:PYTHONPATH = "src;."

& $PY scripts\agent\prepare_full104_runtime_envelope_v1.py `
    --mode prepare --runtime-root $RT --worktree $WORKTREE `
    --expected-scientific-anchor $ANCHOR `
    --level4-root $L4 --registry $REGISTRY --observation-state $OBS

# ------------------------------------------------------- 3. physical shakedown
# Receipt must be written INSIDE the envelope. ~131 min.
& $PY scripts\agent\run_full104_physical_shakedown_v1.py `
    --runtime-root $RT --worktree $WORKTREE `
    --expected-scientific-anchor $ANCHOR `
    --level4-root $L4 --registry $REGISTRY --observation-state $OBS `
    --out "$RT\full104_physical_shakedown_receipt_v1.json"
# -> FULL104_PHYSICAL_SHAKEDOWN_PASS
#    receipt 56ffb8687275eb81f9e8119c6279d9ef4eb6d536f3bc055bc32e5945064a8722

# ------------------------------------ 4. build selection_row-keyed pass1 (~29 min)
& $PY -c @"
import sys; sys.path.insert(0,'src')
from pathlib import Path
from sea_ad_jepa.v5.full104_pass1_builder_v1 import build_pass1_from_physical_full104
s = build_pass1_from_physical_full104(
    level4_root=Path(r'$L4'),
    registry_path=Path(r'$REGISTRY'),
    observation_state_path=Path(r'$OBS'),
    out_path=Path(r'$OUT\full104_pass1_v2_selection_row_keyed.npz'),
    expect_reference_geometry=True)
print(s.as_dict())
"@
# -> 8915 blocks / 4553407 rows / 104 donors / 17186 strict core
#    pass1 37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1

# ------------------------- 5. independent verifier + census receipts (~20 min)
# full104_pass1_physical_binding_v1.py is UNMODIFIED and is the sole verifier.
$C = "$OUT\census_v2"
New-Item -ItemType Directory -Force -Path $C | Out-Null
& $PY analysis\v5_full104_census_20260918\full104_readonly_census_receipts_v2.py `
    --pass1 "$OUT\full104_pass1_v2_selection_row_keyed.npz" `
    --level4-root $L4 --registry $REGISTRY --observation-state $OBS `
    --out-pass1-physical-binding "$C\full104_pass1_physical_binding_v1.json" `
    --out-summary               "$C\full104_census_summary_v2.json" `
    --out-split                 "$C\full104_split_receipt_v1.json" `
    --out-target-eligibility    "$C\full104_target_eligibility_v1.json"
# -> binding 4c44b89e91e85b762224a6c2cf7e5cd88956a1726f57a52c03ddcab4ad0c3602
#    17,053 all-fold eligible targets; per-fold 17070/17071/17072/17060

# ------------------------------------------------------------------ 6. tests
& $PY -m pytest -q -p no:randomly --strict-markers -rs `
    tests\test_v5_full104_pass1_builder_v1.py `
    tests\test_v5_full104_pass1_physical_binding_v1.py `
    tests\test_v5_full104_physical_shakedown_v1.py `
    tests\test_v5_full104_runtime_envelope_v1.py `
    tests\test_v5_full104_census_receipt_v2.py
# -> 52 passed, 0 skipped

Pop-Location

# NOT RUN, deliberately: census authority V2 (needs --support-authority),
# control-calibration cache, preterminal authorities, target-panel ladder,
# margin selection, terminal run contract, any masking rung.
