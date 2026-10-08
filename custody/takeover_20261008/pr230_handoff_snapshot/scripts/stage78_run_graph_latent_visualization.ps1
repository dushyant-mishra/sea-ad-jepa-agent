param(
  [string]$Config = "configs/stage75f_out_of_core_v1.yaml",
  [string]$ProjectDir = "."
)
$ErrorActionPreference = "Stop"
$repo = Resolve-Path $ProjectDir
Push-Location $repo
try {
  Push-Location "web/stage78_graph_explorer"
  $env:STAGE78_NODE_VERSION = (node --version)
  $env:STAGE78_NPM_VERSION = (npm --version)
  npm ci
  npm run build
  Pop-Location
  conda run -n sea-ad-jepa-v3 python scripts/stage78_build_graph_latent_visualization.py --config $Config --project-dir .
  exit $LASTEXITCODE
} finally {
  if ((Get-Location).Path -like "*web*stage78_graph_explorer*") { Pop-Location }
  Pop-Location
}
