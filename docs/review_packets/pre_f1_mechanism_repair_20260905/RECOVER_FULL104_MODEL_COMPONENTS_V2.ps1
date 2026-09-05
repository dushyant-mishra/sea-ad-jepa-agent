$ErrorActionPreference = 'SilentlyContinue'
$roots = @('D:\Jepa project') + (Get-ChildItem 'D:\' -Directory -Filter 'Jepa project*' | ForEach-Object { $_.FullName })
$hits = foreach ($r in ($roots | Select-Object -Unique)) {
    Get-ChildItem $r -Recurse -File -Filter 'full104_model_components_v2.py' | Select-Object FullName,Length,LastWriteTime
}
$hits | Sort-Object FullName | Format-Table -AutoSize
