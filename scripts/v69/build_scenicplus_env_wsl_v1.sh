#!/usr/bin/env bash
# V69: build the SCENIC+ / pycisTopic / pycistarget execution environment in WSL.
#
# The JEPA repository is NOT cloned into the Linux home directory; this script is
# invoked against /mnt/d and installs only third-party software into a conda env.
# SCENIC+ source is cloned into the V69 large-output directory so its exact commit
# and file digests can be receipted.
set -euo pipefail

ENV_NAME="${ENV_NAME:-scenicplus_v69}"
OUT="${OUT:-/mnt/d/jepa_v5_outputs_20260925/v69_scenicplus}"
SRC="$OUT/env/scenicplus_src"

source "$HOME/miniconda3/etc/profile.d/conda.sh"

mkdir -p "$OUT/env" "$OUT/logs"

echo "=== [1/5] create env ==="
# cluster_buster is NOT a conda package; the Aerts lab publishes a precompiled
# Linux binary alongside the cisTarget resources, which is what we pin below.
# macs3 is installed from a wheel because this WSL image has no system compiler.
if ! conda env list | grep -qE "^${ENV_NAME}\s"; then
  mamba create -y -n "$ENV_NAME" -c conda-forge -c bioconda \
    python=3.11 bedtools htslib pybigwig \
    numpy pandas scipy pyarrow cython
fi

conda activate "$ENV_NAME"
python -V
pip install --no-input macs3 2>&1 | tail -5 || echo "MACS3_PIP_FAILED"

echo "--- pin Cluster-Buster binary (official Aerts lab build) ---"
CBUST="$OUT/env/cbust"
if [ ! -x "$CBUST" ]; then
  curl -L --fail --retry 5 -o "$CBUST" https://resources.aertslab.org/cistarget/programs/cbust
  chmod +x "$CBUST"
fi
sha256sum "$CBUST" | tee "$OUT/env/cbust.sha256"
"$CBUST" 2>&1 | head -3 || true
echo "cbust: $CBUST"
echo "macs3: $(command -v macs3 || echo ABSENT)"

echo "=== [2/5] clone SCENIC+ (pinned by commit, receipted) ==="
if [ ! -d "$SRC/.git" ]; then
  git clone --depth 50 https://github.com/aertslab/scenicplus "$SRC"
fi
cd "$SRC"
git log -1 --format='SCENICPLUS_COMMIT=%H%nSCENICPLUS_DATE=%cI' | tee "$OUT/env/scenicplus_commit.txt"

echo "=== [3/5] install SCENIC+ ==="
pip install --no-input . 2>&1 | tail -20

echo "=== [4/5] install create_cisTarget_databases ==="
CTDB="$OUT/env/create_cisTarget_databases"
if [ ! -d "$CTDB/.git" ]; then
  git clone --depth 50 https://github.com/aertslab/create_cisTarget_databases "$CTDB"
fi
cd "$CTDB"
git log -1 --format='CTDB_COMMIT=%H%nCTDB_DATE=%cI' | tee "$OUT/env/ctdb_commit.txt"
pip install --no-input -r requirements.txt 2>&1 | tail -10 || true

echo "=== [5/5] verify imports ==="
python - <<'PY'
import importlib, json, sys
mods = ["scenicplus", "pycisTopic", "pycistarget", "numpy", "pandas", "scipy", "pyarrow"]
out = {}
for m in mods:
    try:
        mod = importlib.import_module(m)
        out[m] = getattr(mod, "__version__", "NO_VERSION_ATTR")
    except Exception as e:
        out[m] = "IMPORT_FAILED: %s: %s" % (type(e).__name__, e)
print(json.dumps(out, indent=2))
PY
echo "=== ENV BUILD FINISHED ==="
