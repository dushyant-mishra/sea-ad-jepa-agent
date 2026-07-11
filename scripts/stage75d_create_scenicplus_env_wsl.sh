#!/usr/bin/env bash
set -euo pipefail
conda env remove -y -n sea-ad-scenicplus || true
conda create -y -n sea-ad-scenicplus python=3.10.13
conda run -n sea-ad-scenicplus python -m pip install --upgrade pip wheel setuptools
conda install -y -n sea-ad-scenicplus -c conda-forge -c bioconda pybedtools=0.9.1 bedtools macs2=2.2.9.1 cython=0.29.37 numpy pandas scipy
conda run -n sea-ad-scenicplus python - <<'PY'
import setuptools, pybedtools
print("setuptools", setuptools.__version__)
print("pybedtools", pybedtools.__version__)
try:
    import MACS2
    print("MACS2", getattr(MACS2, "__version__", "installed"))
except Exception as exc:
    print("MACS2 import check failed", type(exc).__name__, exc)
PY
cd /tmp
rm -rf scenicplus
git clone https://github.com/aertslab/scenicplus
cd scenicplus
git checkout development
if ! conda run -n sea-ad-scenicplus python -m pip install .; then
  echo "Primary SCENIC+ install failed; trying no-build-isolation fallback with Poetry backend and modern packaging..."
  conda run -n sea-ad-scenicplus python -m pip install 'poetry<1.2' poetry-core 'packaging>=24.2'
  conda run -n sea-ad-scenicplus python -m pip install --no-build-isolation .
fi
conda run -n sea-ad-scenicplus python -m pip install celloracle pyranges pybiomart mudata scanpy anndata
conda run -n sea-ad-scenicplus python - <<'PY'
import importlib.util
mods=['scenicplus','pycisTopic','pycistarget','ctxcore','arboreto','celloracle','pyranges','mudata','scanpy']
print({m: bool(importlib.util.find_spec(m)) for m in mods})
PY
