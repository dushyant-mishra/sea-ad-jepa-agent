param(
  [string]$Config = "configs/stage75f_out_of_core_v1.yaml",
  [string]$ProjectDir = "."
)
$ErrorActionPreference = "Stop"
$repo = Resolve-Path $ProjectDir
Push-Location $repo
try {
  conda run -n sea-ad-jepa-v3 python scripts/stage78_compute_jepa_latent_shift.py --config $Config --project-dir .
  exit $LASTEXITCODE
} finally {
  Pop-Location
}