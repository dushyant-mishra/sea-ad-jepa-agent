#!/usr/bin/env bash
set -euo pipefail
conda env remove -y -n sea-ad-scenicplus || true
conda create -y -n sea-ad-scenicplus python=3.11.8
conda run -n sea-ad-scenicplus python -m pip install --upgrade pip wheel setuptools
cd /tmp
rm -rf scenicplus
git clone https://github.com/aertslab/scenicplus
cd scenicplus
git checkout development
conda run -n sea-ad-scenicplus python -m pip install .
conda run -n sea-ad-scenicplus python -m pip install celloracle pyranges pybiomart mudata scanpy anndata
conda run -n sea-ad-scenicplus python - <<'PY'
import importlib.util
mods=['scenicplus','pycisTopic','pycistarget','ctxcore','arboreto','celloracle','pyranges','mudata','scanpy']
print({m: bool(importlib.util.find_spec(m)) for m in mods})
PY
