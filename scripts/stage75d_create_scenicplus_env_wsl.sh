#!/usr/bin/env bash
set -euo pipefail
conda env remove -y -n sea-ad-scenicplus || true
conda create -y -n sea-ad-scenicplus python=3.10.13
conda run -n sea-ad-scenicplus python -m pip install --upgrade pip wheel setuptools
conda install -y -n sea-ad-scenicplus -c conda-forge -c bioconda pybedtools=0.9.1 bedtools cython numpy pandas scipy
conda run -n sea-ad-scenicplus python -m pip install 'poetry<1.2' poetry-core
conda run -n sea-ad-scenicplus python - <<'PY'
import setuptools, pybedtools
print("setuptools", setuptools.__version__)
print("pybedtools", pybedtools.__version__)
PY
cd /tmp
rm -rf scenicplus
git clone https://github.com/aertslab/scenicplus
cd scenicplus
git checkout development
conda run -n sea-ad-scenicplus python -m pip install --no-build-isolation .
conda run -n sea-ad-scenicplus python -m pip install celloracle pyranges pybiomart mudata scanpy anndata
conda run -n sea-ad-scenicplus python - <<'PY'
import importlib.util
mods=['scenicplus','pycisTopic','pycistarget','ctxcore','arboreto','celloracle','pyranges','mudata','scanpy']
print({m: bool(importlib.util.find_spec(m)) for m in mods})
PY
