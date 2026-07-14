param(
    [string]$ProjectDir = "D:\Jepa project",
    [string]$Config = "configs/stage75f_out_of_core_v1.yaml",
    [string]$CondaEnv = "sea-ad-jepa-v3"
)

$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $ProjectDir
New-Item -ItemType Directory -Force -Path "results/tables", "results/reports", "results/stage75e_container" | Out-Null

$checkPath = "results/stage75e_container/stage76_runtime_check.py"
$checkCode = @"
import importlib.util
import sys
mods = ["torch", "h5py", "numpy", "pandas", "yaml"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    raise SystemExit("missing required Python packages: " + ", ".join(missing))
import torch
print("python=" + sys.executable)
print("torch=" + torch.__version__)
print("cuda_available=" + str(torch.cuda.is_available()))
print("device=" + (torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"))
"@
Set-Content -LiteralPath $checkPath -Value $checkCode -Encoding UTF8

conda run -n $CondaEnv python $checkPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$log = "results/stage75e_container/stage76_perturbation_readiness.log"
conda run -n $CondaEnv python -u scripts/stage76_audit_perturbation_readiness.py --config $Config --project-dir $ProjectDir 2>&1 | Tee-Object -FilePath $log
exit $LASTEXITCODE
