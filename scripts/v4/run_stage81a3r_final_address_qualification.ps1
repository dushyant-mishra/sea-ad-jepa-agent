param(
    [switch]$SkipMechanics
)

$ErrorActionPreference = "Stop"
$project = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$env:PYTHONPATH = if ($env:PYTHONPATH) {
    "$project\src;$env:PYTHONPATH"
} else {
    "$project\src"
}

$arguments = @(
    "run", "-n", "sea-ad-jepa-v3", "python",
    "scripts/v4/stage81a3r_final_address_qualification.py",
    "--project-dir", ".",
    "--config", "configs/v4/stage81a3r_final_address_qualification.yaml"
)
if ($SkipMechanics) {
    $arguments += "--skip-mechanics"
}

Push-Location $project
try {
    & conda @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Stage81A3R qualification failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}
