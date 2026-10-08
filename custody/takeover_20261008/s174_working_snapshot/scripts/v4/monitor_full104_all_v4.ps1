$ErrorActionPreference = 'Stop'

$projectRoot = 'D:\Jepa project'
$relativeOutput = 'outputs\full104_v014_20260826\03_phase2_state_derivation_v1\shared_refit_null_sensitivity_results_v4_block_major_wsl'
$output = Join-Path $projectRoot $relativeOutput
$monitor = Join-Path $output 'monitoring'
$latest = Join-Path $monitor 'FULL104_ALL_HEALTH_LATEST.json'
$history = Join-Path $monitor 'FULL104_ALL_HEALTH_HISTORY.ndjson'

New-Item -ItemType Directory -Force -Path $monitor | Out-Null

$statePath = Join-Path $output 'RUN_STATE.json'
$state = if (Test-Path -LiteralPath $statePath) {
    Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
} else {
    $null
}
$aPath = Join-Path $output 'null_replicates_A'
$bPath = Join-Path $output 'null_replicates_B'
$a = @(Get-ChildItem -LiteralPath $aPath -Filter 'replicate_*.npz' -ErrorAction SilentlyContinue).Count
$b = @(Get-ChildItem -LiteralPath $bPath -Filter 'replicate_*.npz' -ErrorAction SilentlyContinue).Count

$savedPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$processListing = (& wsl.exe ps -eo cmd 2>$null) -join "`n"
$ErrorActionPreference = $savedPreference
$active = $processListing.Contains('run_full104_refit_null_block_major_v1.py') -and
          $processListing.Contains('shared_refit_null_sensitivity_results_v4_block_major_wsl')
$terminal = $state -and $state.status -eq 'ALL_COMPLETE_AWAITING_INDEPENDENT_REAL_RESULT_VALIDATION'
$health = if ($terminal) {
    'COMPLETE_AWAITING_INDEPENDENT_REAL_RESULT_VALIDATION'
} elseif ($active -and $state -and $state.status -eq 'RUNNING') {
    'RUNNING'
} elseif ($state -and $state.status -eq 'RUNNING') {
    'ATTENTION_REQUIRED_PROCESS_NOT_ACTIVE'
} else {
    'ATTENTION_REQUIRED_STATE_MISSING_OR_UNEXPECTED'
}

$record = [ordered]@{
    schema = 'full104-all-v4-health-v1'
    checked_at_utc = [DateTime]::UtcNow.ToString('o')
    health = $health
    run_status = if ($state) { $state.status } else { $null }
    implementation_fingerprint = if ($state) { $state.implementation_fingerprint } else { $null }
    process_active = [bool]$active
    A_completed = $a
    B_completed = $b
    total_completed = $a + $b
    total_required = 512
    D_or_selection_inspected = $false
}
$json = $record | ConvertTo-Json
$temp = "$latest.tmp"
Set-Content -LiteralPath $temp -Value $json -Encoding UTF8
Move-Item -LiteralPath $temp -Destination $latest -Force
Add-Content -LiteralPath $history -Value (($record | ConvertTo-Json -Compress)) -Encoding UTF8

if ($health.StartsWith('ATTENTION_REQUIRED')) {
    exit 2
}
