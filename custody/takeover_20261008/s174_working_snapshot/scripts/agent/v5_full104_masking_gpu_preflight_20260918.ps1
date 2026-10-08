param(
    [ValidateSet("Calibration","Terminal")]
    [string]$Mode = "Calibration",
    [Parameter(Mandatory=$true)][string]$ExpectedScientificAnchor,
    [string]$CanonicalRepo = "D:\Jepa project",
    [string]$Worktree = "D:\Jepa project",
    [string]$Level4Root = "D:\Jepa project\outputs\full104_v014_20260826\03_phase2_state_derivation_v1\expression_level4",
    [Parameter(Mandatory=$true)][string]$ObservationState,
    [Parameter(Mandatory=$true)][string]$Registry,
    [string]$RegistryAuthority = "docs\agent\V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_20260916.json",
    [string]$SupportAuthority = "docs\agent\V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json",
    [Parameter(Mandatory=$true)][string]$ParametersAuthority,
    [Parameter(Mandatory=$true)][string]$CensusAuthority,
    [Parameter(Mandatory=$true)][string]$SplitReceipt,
    [Parameter(Mandatory=$true)][string]$TargetEligibility,
    [Parameter(Mandatory=$true)][string]$CacheDir,
    [string]$TargetPanelAuthority,
    [string]$PrecisionAuthority,
    [string]$OuterSplitAuthority,
    [string]$NonlinearAuthority,
    [string]$RngAuthority,
    [string]$RunContract,
    [string]$MachineCheckpoint = "docs\agent\CURRENT_WORK_CHECKPOINT.json"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedBranch = "impl/v5-full104-masking-redteam2-20260918"
$ExpectedBlockManifestSha256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"

function Stop-Preflight([string]$Message) { throw "STOP_V5_FULL104_PREFLIGHT: $Message" }
function Resolve-RepoPath([string]$Value) {
    if ([System.IO.Path]::IsPathRooted($Value)) { return $Value }
    return (Join-Path $Worktree $Value)
}

foreach ($path in @($CanonicalRepo,$Worktree,$Level4Root)) {
    if (-not (Test-Path -LiteralPath $path)) { Stop-Preflight "required path does not exist: $path" }
}

Write-Host "== Git/worktree provenance =="
git -C $CanonicalRepo fetch origin
if ($LASTEXITCODE -ne 0) { Stop-Preflight "git fetch failed" }
$head = (git -C $Worktree rev-parse HEAD).Trim()
$branchNow = (git -C $Worktree branch --show-current).Trim()
if ($branchNow -ne $ExpectedBranch) { Stop-Preflight "wrong branch: $branchNow" }
$dirty = git -C $Worktree status --porcelain
if ($dirty) { Stop-Preflight "worktree is dirty; preserve user changes and use a clean isolated worktree" }

$statePath = Join-Path $Worktree "docs\agent\CURRENT_WORK_CHECKPOINT_STATE.json"
$planPath = Join-Path $Worktree "docs\exec-plans\active\JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md"
foreach ($path in @($statePath,$planPath)) {
    if (-not (Test-Path -LiteralPath $path)) { Stop-Preflight "missing governance file: $path" }
}
$state = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
$stateAnchor = [string]$state.assets.repository.scientific_implementation_head
if ($stateAnchor -ne $ExpectedScientificAnchor) {
    Stop-Preflight "supplied scientific anchor $ExpectedScientificAnchor disagrees with checkpoint-state anchor $stateAnchor"
}
git -C $Worktree merge-base --is-ancestor $ExpectedScientificAnchor HEAD
if ($LASTEXITCODE -ne 0) { Stop-Preflight "scientific anchor is not an ancestor of current HEAD" }

foreach ($authority in $state.authorities) {
    $authorityPath = Join-Path $Worktree ([string]$authority.path)
    if (-not (Test-Path -LiteralPath $authorityPath)) { Stop-Preflight "missing pinned authority $($authority.path)" }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $authorityPath).Hash.ToLowerInvariant()
    if ($actual -ne [string]$authority.sha256) {
        Stop-Preflight "pinned authority hash mismatch for $($authority.path)"
    }
}

$blockManifest = Join-Path $Level4Root "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
if (-not (Test-Path -LiteralPath $blockManifest)) { Stop-Preflight "FULL104 block manifest missing" }
$blockSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $blockManifest).Hash.ToLowerInvariant()
if ($blockSha -ne $ExpectedBlockManifestSha256) { Stop-Preflight "FULL104 block manifest SHA mismatch" }

Write-Host "== Current authority/root closure =="
$validator = Join-Path $Worktree "scripts\agent\validate_full104_masking_gpu_preflight_v1.py"
if (-not (Test-Path -LiteralPath $validator)) { Stop-Preflight "current preflight validator missing" }

$validatorArgs = @(
    $validator,
    "--mode", $Mode.ToLowerInvariant(),
    "--repo", $Worktree,
    "--level4-root", $Level4Root,
    "--observation-state", (Resolve-RepoPath $ObservationState),
    "--registry", (Resolve-RepoPath $Registry),
    "--registry-authority", (Resolve-RepoPath $RegistryAuthority),
    "--support-authority", (Resolve-RepoPath $SupportAuthority),
    "--parameters-authority", (Resolve-RepoPath $ParametersAuthority),
    "--census-authority", (Resolve-RepoPath $CensusAuthority),
    "--split-receipt", (Resolve-RepoPath $SplitReceipt),
    "--target-eligibility", (Resolve-RepoPath $TargetEligibility),
    "--cache-dir", (Resolve-RepoPath $CacheDir)
)
if ($Mode -eq "Terminal") {
    $terminalValues = @{
        "--target-panel-authority" = $TargetPanelAuthority
        "--precision-authority" = $PrecisionAuthority
        "--outer-split-authority" = $OuterSplitAuthority
        "--nonlinear-authority" = $NonlinearAuthority
        "--rng-authority" = $RngAuthority
        "--run-contract" = $RunContract
        "--machine-checkpoint" = $MachineCheckpoint
    }
    foreach ($entry in $terminalValues.GetEnumerator()) {
        if ([string]::IsNullOrWhiteSpace([string]$entry.Value)) {
            Stop-Preflight "$($entry.Key) is required in Terminal mode"
        }
        $validatorArgs += @($entry.Key, (Resolve-RepoPath ([string]$entry.Value)))
    }
}
Push-Location $Worktree
try {
    $env:PYTHONPATH = "src;."
    python @validatorArgs
    if ($LASTEXITCODE -ne 0) { Stop-Preflight "authority/root validator failed" }
} finally { Pop-Location }

Write-Host "== Current focused regression suite, fail closed on skips =="
$workflowPath = Join-Path $Worktree ".github\workflows\v5-full104-masking-runner.yml"
$workflow = Get-Content -Raw -LiteralPath $workflowPath
$begin = $workflow.IndexOf("- name: Run FULL104 masking authority regressions")
$finish = $workflow.IndexOf("- name: Fail closed on skips", $begin)
if ($begin -lt 0 -or $finish -le $begin) { Stop-Preflight "cannot recover focused-test block from current workflow" }
$block = $workflow.Substring($begin, $finish - $begin)
$matches = [regex]::Matches($block, "tests/[A-Za-z0-9_./-]+\.py")
$focusedTests = @($matches | ForEach-Object { $_.Value } | Select-Object -Unique)
if ($focusedTests.Count -lt 1) { Stop-Preflight "current workflow exposes no focused tests" }

$stageATests = @(
    "tests/test_v5_current_stage_a_spillover_firewall_v1.py",
    "tests/test_v5_current_stage_a_spillover_firewall_v3.py"
)
Push-Location $Worktree
try {
    $env:PYTHONPATH = "src;."
    $output = & python -m pytest -q -p no:randomly --strict-markers -rs @focusedTests @stageATests 2>&1
    $code = $LASTEXITCODE
    $output | ForEach-Object { Write-Host $_ }
    if ($code -ne 0) { Stop-Preflight "focused masking/Stage-A tests failed" }
    $joined = ($output -join [Environment]::NewLine)
    if ($joined -match "(?im)\bskipped\b|\bSKIPPED\b") { Stop-Preflight "critical focused suite reported a skip" }
} finally { Pop-Location }

if ($Mode -eq "Terminal") {
    Write-Host "== Machine checkpoint =="
    $checkpoint = Resolve-RepoPath $MachineCheckpoint
    if (-not (Test-Path -LiteralPath $checkpoint)) { Stop-Preflight "terminal machine checkpoint missing" }
    python (Join-Path $Worktree "scripts\agent\work_checkpoint.py") validate --worktree $Worktree --checkpoint $checkpoint
    if ($LASTEXITCODE -ne 0) { Stop-Preflight "machine checkpoint validation failed" }
}

Write-Host ""
Write-Host "PREFLIGHT PASS mode=$Mode head=$head scientific_anchor=$ExpectedScientificAnchor"
Write-Host "Terminal masking outcomes remain closed unless Mode=Terminal and the separately frozen terminal run contract authorizes execution."
Write-Host "Training remains OFF. D_shared/pathology/DEV/SEALED outcomes remain closed."
