param(
    [string]$OutDir = "data/external/grubman_gse138852"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$files = @(
    @{
        Url = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE138nnn/GSE138852/suppl/GSE138852_counts.csv.gz"
        Out = "GSE138852_counts.csv.gz"
    },
    @{
        Url = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE138nnn/GSE138852/suppl/GSE138852_covariates.csv.gz"
        Out = "GSE138852_covariates.csv.gz"
    }
)

foreach ($file in $files) {
    $target = Join-Path $OutDir $file.Out
    Write-Host "Downloading $($file.Out)"
    Invoke-WebRequest -Uri $file.Url -OutFile $target
}

Write-Host "Done. Files are in $OutDir"
