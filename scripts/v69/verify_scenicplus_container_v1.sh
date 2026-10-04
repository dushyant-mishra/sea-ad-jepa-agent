#!/usr/bin/env bash
# V69: verify the SCENIC+ execution container and emit an environment manifest.
#
# Every tool this lane uses is smoke-tested INSIDE the running image and its own
# version string is captured. The container README's tool list is NOT treated as
# evidence.
#
# PATH CAVEAT, learned the hard way: `command -v bedtools` under `bash -lc` reports
# ABSENT, because the micromamba base environment is not on a login shell's PATH.
# Every conda-provided tool must be invoked through `micromamba run -n base`. A
# naive PATH probe produces a FALSE ABSENT for bedtools, macs2, samtools and meme.
set -euo pipefail

IMAGE="${IMAGE:-scenicplus:1.0a2}"
OUT="${OUT:-D:/jepa_v5_outputs_20260925/v69_scenicplus}"
ENVDIR="$OUT/env/container"

mkdir -p "$ENVDIR"

echo "=== image identity ==="
docker image inspect "$IMAGE" --format '{{.Id}}' | tee "$ENVDIR/image_id.txt"
docker image inspect "$IMAGE" --format '{{.Created}}' | tee "$ENVDIR/image_created.txt"
docker image inspect "$IMAGE" --format '{{json .RepoTags}}' | tee "$ENVDIR/image_repotags.json"

echo "=== python stack ==="
docker run --rm "$IMAGE" micromamba run -n base python - <<'PY' > "$ENVDIR/python_imports.json"
import json, importlib
mods = ["scenicplus", "pycisTopic", "pycistarget", "pyscenic", "pybedtools",
        "pysam", "scanpy", "anndata", "numpy", "pandas", "scipy", "pyarrow",
        "sklearn", "loomxpy"]
out = {}
for m in mods:
    try:
        mod = importlib.import_module(m)
        out[m] = getattr(mod, "__version__", "NO_VERSION_ATTR")
    except Exception as e:
        out[m] = "IMPORT_FAILED: %s: %s" % (type(e).__name__, e)
print(json.dumps(out, indent=2))
PY
cat "$ENVDIR/python_imports.json"

echo "=== tool smoke tests ==="
docker run --rm "$IMAGE" bash -c '
set -u
echo "## bedtools";  micromamba run -n base bedtools --version 2>&1 | head -1
echo "## macs2";     micromamba run -n base macs2 --version 2>&1 | head -1
echo "## samtools";  micromamba run -n base samtools --version 2>&1 | head -1
echo "## meme";      micromamba run -n base meme -version 2>&1 | head -1
echo "## cbust";     /usr/local/bin/cbust 2>&1 | head -1
echo "## mallet";    /opt/mallet/bin/mallet train-topics --help TRUE 2>&1 | grep -m1 -- "--num-topics"
echo "## liftOver";  /usr/local/bin/liftOver 2>&1 | head -1
echo "## bigWigAverageOverBed"; /usr/local/bin/bigWigAverageOverBed 2>&1 | head -1
echo "## create_cistarget_motif_databases.py"; micromamba run -n base python \
  /opt/create_cisTarget_databases/create_cistarget_motif_databases.py --help 2>&1 | head -1
echo "## convert_..._to_rankings"; micromamba run -n base python \
  /opt/create_cisTarget_databases/convert_motifs_or_tracks_vs_regions_or_genes_scores_to_rankings_cistarget_dbs.py --help 2>&1 | head -1
echo "## resolved paths"; micromamba run -n base bash -c \
  "command -v cbust bedtools macs2 samtools meme create_cistarget_motif_databases.py mallet"
' 2>&1 | tee "$ENVDIR/tool_smoke_tests.txt"

echo "=== environment manifest regenerated from the RUNNING container ==="
docker run --rm "$IMAGE" micromamba run -n base python -m pip freeze \
  > "$ENVDIR/pip_freeze_regenerated_from_running_container.txt"
wc -l "$ENVDIR/pip_freeze_regenerated_from_running_container.txt"

docker run --rm "$IMAGE" micromamba list -n base \
  > "$ENVDIR/micromamba_list_regenerated_from_running_container.txt" 2>/dev/null || true

echo "=== pip check ==="
docker run --rm "$IMAGE" micromamba run -n base python -m pip check \
  > "$ENVDIR/pip_check_regenerated.txt" 2>&1 || true
cat "$ENVDIR/pip_check_regenerated.txt"

echo "=== VERIFICATION COMPLETE ==="
