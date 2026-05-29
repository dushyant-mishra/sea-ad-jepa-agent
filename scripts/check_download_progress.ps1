param(
    [string]$PathPattern = "data\raw\snrna\SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad*",
    [Int64]$ExpectedBytes = 36319410584
)

$file = Get-ChildItem -Force $PathPattern -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($null -eq $file) {
    Write-Host "No matching download file found: $PathPattern"
    exit 1
}

$size = $file.Length
$pct = [math]::Min(100, ($size / $ExpectedBytes) * 100)
$filled = [math]::Floor($pct / 2)
$bar = ("#" * $filled) + ("-" * (50 - $filled))
$gb = [math]::Round($size / 1GB, 3)
$expectedGb = [math]::Round($ExpectedBytes / 1GB, 3)

"[$bar] {0:N2}%  $gb / $expectedGb GiB" -f $pct
"File: $($file.Name)"
"LastWriteTime: $($file.LastWriteTime)"

