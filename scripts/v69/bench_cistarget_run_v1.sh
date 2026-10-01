#!/usr/bin/env bash
# V69: one measured cisTarget scoring run, for the storage and worker-scaling tables.
#
# A single run of a FIXED workload against a FIXED motif list, parameterised only by
# where it reads/writes and how many workers it uses. Everything scientific is held
# constant so that the only varying factors are the ones under test.
#
# Usage (inside container):
#   bench_cistarget_run_v1.sh <run_id> <fasta> <motif_list> <out_dir> <threads>
#
# Emits <out_dir>/<run_id>.bench.json containing wall time, worker count, input digests,
# output digests and the exact command. The OUTPUT DIGESTS are the point: runs that
# differ only in storage or worker count MUST produce digest-identical outputs, and a
# difference is a more important finding than any timing result.
set -euo pipefail

RUN_ID="${1:?run id}"
FASTA="${2:?region fasta}"
MOTIF_LIST="${3:?motif list}"
OUT_DIR="${4:?output dir}"
THREADS="${5:?threads}"

MOTIF_DIR=/data/resources/v10nr_clust_public/singletons
CBUST=/usr/local/bin/cbust
DB_PREFIX="$OUT_DIR/${RUN_ID}"

# ---- thread pinning: the ONLY parallelism is the tool's own -t ----
# The image sets no thread environment variables and OpenBLAS defaults to 16 threads,
# so without this each of N workers could spawn up to 16 BLAS threads -- N x 16 in
# total. That silently oversubscribes the machine and makes any worker-scaling
# measurement an artifact of the oversubscription rather than of the worker count.
# Pinned to 1 so that -t means what it says. Recorded in the receipt.
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

mkdir -p "$OUT_DIR"

N_MOTIFS=$(wc -l < "$MOTIF_LIST")
N_SEQS=$(grep -c '^>' "$FASTA")
MOTIF_SHA=$(sha256sum "$MOTIF_LIST" | awk '{print $1}')
FASTA_SHA=$(sha256sum "$FASTA" | awk '{print $1}')

CMD="python /opt/create_cisTarget_databases/create_cistarget_motif_databases.py -f $FASTA -M $MOTIF_DIR -m $MOTIF_LIST -o $DB_PREFIX -c $CBUST -t $THREADS"

START_EPOCH=$(date -u +%s)
START_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)
# shellcheck disable=SC2086
micromamba run -n base $CMD > "$OUT_DIR/${RUN_ID}.score.log" 2>&1
END_EPOCH=$(date -u +%s)
END_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ELAPSED=$((END_EPOCH - START_EPOCH))

# The tool's own scoring-phase timing isolates cbust from feather I/O.
CBUST_SECONDS=$(grep -oE 'Scoring [0-9]+ motifs with Cluster-Buster took: [0-9.]+' \
  "$OUT_DIR/${RUN_ID}.score.log" | grep -oE '[0-9.]+$' || echo "UNMEASURED")

# Digest every produced feather. Written only after the files are closed, and computed
# by re-reading from disk rather than from anything held in memory.
python - "$OUT_DIR" "$RUN_ID" "$ELAPSED" "$CBUST_SECONDS" "$N_MOTIFS" "$N_SEQS" \
         "$MOTIF_SHA" "$FASTA_SHA" "$THREADS" "$START_ISO" "$END_ISO" "$CMD" <<'PY'
import hashlib, json, os, sys, glob
out_dir, run_id, elapsed, cbust_s, n_motifs, n_seqs, motif_sha, fasta_sha, \
    threads, start_iso, end_iso, cmd = sys.argv[1:13]

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()

outputs = {}
for p in sorted(glob.glob(os.path.join(out_dir, run_id + "*.feather"))):
    outputs[os.path.basename(p)] = {"bytes": os.path.getsize(p), "sha256": sha(p)}

rec = {
    "schema": "V69_CISTARGET_BENCH_RUN_V1",
    "run_id": run_id,
    "workers": int(threads),
    "wall_clock_seconds": int(elapsed),
    "cbust_scoring_seconds": (float(cbust_s) if cbust_s != "UNMEASURED" else "UNMEASURED"),
    "n_motifs": int(n_motifs),
    "n_region_sequences": int(n_seqs),
    "motif_list_sha256": motif_sha,
    "region_fasta_sha256": fasta_sha,
    "started_utc": start_iso,
    "finished_utc": end_iso,
    "command": cmd,
    "thread_pinning": {
        "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
        "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
        "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS"),
        "NUMEXPR_NUM_THREADS": os.environ.get("NUMEXPR_NUM_THREADS"),
        "why": ("The image sets no thread env vars and OpenBLAS defaults to 16, so "
                "without pinning N workers could spawn N x 16 threads and the measured "
                "scaling would be an artifact of oversubscription."),
    },
    "outputs": outputs,
    "n_outputs": len(outputs),
    "status": "PASS__RUN_COMPLETE" if outputs else "FAIL__NO_OUTPUT_PRODUCED",
}
with open(os.path.join(out_dir, run_id + ".bench.json"), "w") as fh:
    json.dump(rec, fh, indent=2)
    fh.write("\n")
print(json.dumps(rec, indent=2))
PY
echo "=== BENCH RUN $RUN_ID FINISHED ==="
