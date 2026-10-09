param(
    [string]$CanonicalRepo = "D:\\Jepa project",
    [string]$Worktree = "D:\\Jepa project",
    [string]$Level4Root = "D:\\Jepa project\\outputs\\full104_v014_20260826\\03_phase2_state_derivation_v1\\expression_level4"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$VerifiedCodeAnchor = "8ee5d0a5be483e18819a6f6975efa183327b2158"
$ExpectedBlockManifestSha256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"

function Stop-Handoff([string]$Message) { throw "STOP_V5_FULL104_HANDOFF: $Message" }

if (-not (Test-Path -LiteralPath $CanonicalRepo)) { Stop-Handoff "Canonical repository path does not exist: $CanonicalRepo" }
if (-not (Test-Path -LiteralPath $Worktree)) { Stop-Handoff "Worktree path does not exist: $Worktree" }

Write-Host "== Git provenance =="
git -C $CanonicalRepo fetch origin
if ($LASTEXITCODE -ne 0) { Stop-Handoff "git fetch failed" }
$head = (git -C $Worktree rev-parse HEAD).Trim()
$branchNow = (git -C $Worktree branch --show-current).Trim()
$dirty = git -C $Worktree status --porcelain
if ($dirty) { Stop-Handoff "Worktree is not clean. Preserve user changes; do not reset/stash/clean automatically." }
git -C $Worktree merge-base --is-ancestor $VerifiedCodeAnchor HEAD
if ($LASTEXITCODE -ne 0) { Stop-Handoff "Verified code anchor $VerifiedCodeAnchor is not an ancestor of current HEAD $head" }
Write-Host "branch=$branchNow"
Write-Host "head=$head"
Write-Host "verified_code_anchor=$VerifiedCodeAnchor"

Write-Host "== Current handoff files =="
$requiredRepoFiles = @(
    "START_HERE.md",
    "docs/agent/JEPA_LATEST_HANDOFF_POINTER.json",
    "docs/agent/JEPA_NEW_CHAT_HANDOFF_20260917_V5_CANONICAL_MASKING_RUNTIME_CURRENT.md",
    "docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260917_V5_CANONICAL_MASKING_RUNTIME_CURRENT.json",
    "docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json",
    "docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md",
    "src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py",
    "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py",
    "src/sea_ad_jepa/v5/masking_qualification_parameters_authority_v1.py",
    "src/sea_ad_jepa/v5/masking_qualification_run_contract_v1.py",
    "src/sea_ad_jepa/v5/masking_qualification_execution_authority_v2.py"
)
foreach ($rel in $requiredRepoFiles) {
    $path = Join-Path $Worktree $rel
    if (-not (Test-Path -LiteralPath $path)) { Stop-Handoff "Missing required repository file: $rel" }
}

Write-Host "== Focused current-V5 verification =="
Push-Location $Worktree
try {
    $env:PYTHONPATH = "src;."
    python -m pytest -q -p no:randomly --strict-markers tests/test_v5_masking_qualification_run_contract_v1.py tests/test_v5_full104_masking_qualification_runner_v1.py tests/test_v5_full104_masking_streaming_executor_v1.py
    if ($LASTEXITCODE -ne 0) { Stop-Handoff "masking runner/streaming parity tests failed" }
    python -m pytest -q -p no:randomly --strict-markers tests/test_v5_current_stage_a_spillover_firewall_v1.py tests/test_v5_current_stage_a_spillover_firewall_v3.py
    if ($LASTEXITCODE -ne 0) { Stop-Handoff "Stage-A spillover tests failed" }
} finally { Pop-Location }

Write-Host "== Build and validate machine/worktree checkpoint =="
$statePath = Join-Path $Worktree "docs\\agent\\CURRENT_WORK_CHECKPOINT_STATE.json"
$checkpointPath = Join-Path $Worktree "docs\\agent\\CURRENT_WORK_CHECKPOINT.json"
$takeoverPath = Join-Path $Worktree "docs\\agent\\CLAUDE_TAKEOVER.md"
python (Join-Path $Worktree "scripts\\agent\\update_work_checkpoint.py") --worktree $Worktree --state $statePath --checkpoint $checkpointPath --takeover $takeoverPath
if ($LASTEXITCODE -ne 0) { Stop-Handoff "checkpoint build/update failed" }
python (Join-Path $Worktree "scripts\\agent\\work_checkpoint.py") validate --worktree $Worktree --checkpoint $checkpointPath
if ($LASTEXITCODE -ne 0) { Stop-Handoff "checkpoint validation failed" }

Write-Host "== Authenticate FULL104 Level-4 physical root =="
if (-not (Test-Path -LiteralPath $Level4Root)) { Stop-Handoff "Level-4 root not found: $Level4Root" }
$blockManifest = Join-Path $Level4Root "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
$materializationContract = Join-Path $Level4Root "MATERIALIZATION_CONTRACT.json"
$materializationAudit = Join-Path $Level4Root "PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json"
foreach ($path in @($blockManifest, $materializationContract, $materializationAudit)) { if (-not (Test-Path -LiteralPath $path)) { Stop-Handoff "Missing Level-4 authority file: $path" } }
$manifestSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $blockManifest).Hash.ToLowerInvariant()
if ($manifestSha -ne $ExpectedBlockManifestSha256) { Stop-Handoff "FULL104 block manifest SHA mismatch: $manifestSha != $ExpectedBlockManifestSha256" }
Write-Host "FULL104 block manifest SHA256 PASS: $manifestSha"

Write-Host "== Exact execution-source SHA-256 values =="
$runner = Join-Path $Worktree "src\\sea_ad_jepa\\v5\\full104_masking_qualification_runner_v1.py"
$streamer = Join-Path $Worktree "src\\sea_ad_jepa\\v5\\full104_masking_streaming_executor_v1.py"
$runnerSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $runner).Hash.ToLowerInvariant()
$streamerSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $streamer).Hash.ToLowerInvariant()
Write-Host "canonical_runner_sha256=$runnerSha"
Write-Host "streaming_executor_sha256=$streamerSha"

Write-Host ""
Write-Host "PREFLIGHT PASS."
Write-Host "Do NOT inspect terminal masking outcomes yet."
Write-Host "Next: bind donor/source + outer split + target panel + universe/support artifacts; instantiate/freeze design and numeric parameter authorities; bind these exact source SHA-256 values; freeze the run contract; only then execute FULL_COMMON_CORE_17186_V1."
Write-Host "Training remains OFF. D_shared/pathology/DEV/SEALED outcomes remain closed."
