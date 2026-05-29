param(
    [string]$OutDir = "data/raw/metadata"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$files = @(
    @{
        Url = "https://cdn.prod.website-files.com/689cfbd308fa7373b604d290/68debdfdd1b8e9f8fd64dab0_sea-ad_cohort_donor_metadata_072524.xlsx"
        Out = "sea-ad_cohort_donor_metadata_072524.xlsx"
    },
    @{
        Url = "https://cdn.prod.website-files.com/689cfbd308fa7373b604d290/68debdfd24606956df13f2dd_sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv"
        Out = "sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv"
    }
)

foreach ($file in $files) {
    $target = Join-Path $OutDir $file.Out
    Write-Host "Downloading $($file.Out)"
    Invoke-WebRequest -Uri $file.Url -OutFile $target
}

Write-Host "Done. Files are in $OutDir"

