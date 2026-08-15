param(
    [string]$SourceProject = $env:JEPA_SOURCE_PROJECT,
    [string]$Environment = "sea-ad-jepa-v3",
    [string]$WslRscript = "/home/dushyant_mishra/miniconda3/envs/stage81a2r-r-feature-audit/bin/Rscript"
)
$ErrorActionPreference = "Stop"
$Project = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$SourceProject = if ($SourceProject) { $SourceProject } else { $Project }
$SourceProject = (Resolve-Path $SourceProject).Path
$env:PYTHONPATH = Join-Path $Project "src"

$Registry = Join-Path $SourceProject "results\v4\stage81a2r_foundation_molecular_address_registry_candidate.csv"
if (-not (Test-Path $Registry)) {
    throw "SourceProject must contain the frozen A2R data/evidence assets: $SourceProject"
}

conda run -n $Environment python -m pytest -q `
    tests/v4/test_stage81a3r_real_train_global_state.py `
    --basetemp results/v4/.pytest-stage81a3r-real-train
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

conda run -n $Environment python scripts/v4/stage81a3r_verify_scalar_mapping_injectivity.py `
    --project-dir $Project --source-project $SourceProject --accept-known-supplemental
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

function Convert-ToWslPath([string]$Path) {
    $Value = (& wsl.exe wslpath -a -u $Path).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $Value) { throw "Unable to convert path for WSL: $Path" }
    return $Value
}

$ProjectWsl = Convert-ToWslPath $Project
$SourceWsl = Convert-ToWslPath $SourceProject
$NphCache = Join-Path $SourceProject "data\cache\stage81a3r_corrected_real_train"
New-Item -ItemType Directory -Force -Path $NphCache | Out-Null
$NphCacheWsl = Convert-ToWslPath $NphCache
$NphSources = @(
    "Astro_data_arranged_updatedId_final_batches.qs",
    "Endo_data_arranged_updatedId_final_batches.qs",
    "ExN_data_arranged_updatedId_final_batches.qs",
    "InN_data_arranged_updatedId_final_batches.qs",
    "MG_data_arranged_updatedId_final_batches.qs",
    "OPC_data_arranged_updatedId_final_batches.qs",
    "Oligo_data_arranged_updatedId_final_batches.qs"
)
foreach ($SourceObject in $NphSources) {
    $Command = "test -x '$WslRscript' && cd '$ProjectWsl' && '$WslRscript' scripts/v4/stage81a3r_materialize_corrected_nph_train_sample.R '$ProjectWsl' '$SourceWsl' '$NphCacheWsl' '$SourceObject'"
    & wsl.exe bash -lc $Command
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

conda run -n $Environment python scripts/v4/stage81a3r_corrected_real_train_global_state.py `
    --project-dir $Project --source-project $SourceProject
exit $LASTEXITCODE
