param(
    [ValidateSet("single-cell", "neuropathology", "spatial")]
    [string]$Bucket = "single-cell",

    [string]$Prefix = "",

    [string]$Pattern = "",

    [int]$First = 200
)

$ErrorActionPreference = "Stop"

$bucketName = switch ($Bucket) {
    "single-cell" { "sea-ad-single-cell-profiling" }
    "neuropathology" { "sea-ad-quantitative-neuropathology" }
    "spatial" { "sea-ad-spatial-transcriptomics" }
}

$s3Uri = "s3://$bucketName/"
if ($Prefix -ne "") {
    $s3Uri = "s3://$bucketName/$Prefix"
}

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "AWS CLI is not installed in this environment. Install with: pip install awscli"
}

$lines = aws s3 ls --no-sign-request $s3Uri --recursive

if ($Pattern -ne "") {
    $lines = $lines | Where-Object { $_ -match $Pattern }
}

$lines | Select-Object -First $First
