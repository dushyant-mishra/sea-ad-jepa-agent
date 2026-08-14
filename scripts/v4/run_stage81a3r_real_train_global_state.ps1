param(
    [string]$SourceProject = $env:JEPA_SOURCE_PROJECT,
    [string]$Environment = "sea-ad-jepa-v3"
)
$ErrorActionPreference = "Stop"
$Project = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$SourceProject = if ($SourceProject) { $SourceProject } else { $Project }
$env:PYTHONPATH = Join-Path $Project "src"

conda run -n $Environment python -m pytest -q `
    tests/v4/test_stage81a3r_real_train_global_state.py `
    --basetemp results/v4/.pytest-stage81a3r-real-train
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

conda run -n $Environment python scripts/v4/stage81a3r_real_train_global_state.py `
    --project-dir $Project --source-project $SourceProject
exit $LASTEXITCODE
