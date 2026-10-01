#!/usr/bin/env bash
# V69: score ONE deterministic motif shard, restartably and auditably.
#
# Shards are motif-wise: a subset of motifs against ALL regions. cisTarget ranks regions
# within each motif, so this axis keeps both scores and rankings shard-decomposable.
#
# DESIGN RULES, each one a response to a defect already recorded in this lane:
#
#   S16  An executing script is immutable. The caller copies this file to a
#        run-specific path and executes the COPY, so editing the worktree cannot reach
#        into a running shard. With many concurrent shards the exposure multiplies.
#
#   S12  No mutable shared filenames. Every artifact a shard writes -- its motif list,
#        its digest, its log, its receipt -- is named after the SHARD, so two shards
#        writing into one directory cannot overwrite each other's provenance.
#
#   Completion sentinel. The shard receipt is written only after the outputs are closed
#        and RE-READ FROM DISK. The presence of a valid receipt is the only thing that
#        marks a shard done, so an interrupted shard can never look complete.
#
#   Restartability. A crash at motif 10,000 must not require rebuilding the first 9,999.
#        Re-running this script for a shard whose receipt already validates is a no-op.
#
# Usage (inside container):
#   run_cistarget_motif_shard_v1.sh <shard_id> <frozen_motif_list> <start_1based> \
#                                   <count> <fasta> <out_dir> <threads>
set -euo pipefail

SHARD_ID="${1:?shard id}"
FROZEN_LIST="${2:?frozen motif list}"
START="${3:?1-based start index into the frozen list}"
COUNT="${4:?number of motifs in this shard}"
FASTA="${5:?region fasta}"
OUT_DIR="${6:?output dir}"
THREADS="${7:-4}"

MOTIF_DIR=/data/resources/v10nr_clust_public/singletons
CBUST=/usr/local/bin/cbust
PREFIX="$OUT_DIR/$SHARD_ID"
RECEIPT="$PREFIX.shard.json"

mkdir -p "$OUT_DIR"

# ---- restartability: a valid receipt means done ----
if [ -s "$RECEIPT" ]; then
  if micromamba run -n base python -c "
import json,sys,hashlib,os
r=json.load(open('$RECEIPT'))
if r.get('status')!='PASS__SHARD_COMPLETE': sys.exit(1)
for name,meta in r['outputs'].items():
    p=os.path.join('$OUT_DIR',name)
    if not os.path.exists(p): sys.exit(1)
    h=hashlib.sha256()
    with open(p,'rb') as fh:
        for b in iter(lambda: fh.read(8<<20), b''): h.update(b)
    if h.hexdigest()!=meta['sha256']: sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
    echo "SHARD $SHARD_ID ALREADY COMPLETE AND DIGEST-VERIFIED -- skipping"
    exit 0
  fi
  echo "SHARD $SHARD_ID has a receipt that does not validate; rebuilding"
fi

# ---- immutable per-shard motif list, sliced deterministically ----
SHARD_LIST="$PREFIX.motifs.lst"
END=$((START + COUNT - 1))
sed -n "${START},${END}p" "$FROZEN_LIST" > "$SHARD_LIST"
N_IN_SHARD=$(wc -l < "$SHARD_LIST")
if [ "$N_IN_SHARD" -ne "$COUNT" ]; then
  echo "FAIL__SHARD_SLICE_WRONG_SIZE expected=$COUNT got=$N_IN_SHARD" >&2
  exit 3
fi
sha256sum "$SHARD_LIST" > "$SHARD_LIST.sha256"

START_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)
START_EPOCH=$(date -u +%s)

micromamba run -n base python \
  /opt/create_cisTarget_databases/create_cistarget_motif_databases.py \
  -f "$FASTA" -M "$MOTIF_DIR" -m "$SHARD_LIST" -o "$PREFIX" \
  -c "$CBUST" -t "$THREADS" > "$PREFIX.score.log" 2>&1

END_EPOCH=$(date -u +%s)
END_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# ---- receipt written ONLY after re-reading the outputs from disk ----
micromamba run -n base python - \
  "$SHARD_ID" "$OUT_DIR" "$SHARD_LIST" "$FROZEN_LIST" "$START" "$COUNT" \
  "$FASTA" "$THREADS" "$START_ISO" "$END_ISO" "$((END_EPOCH-START_EPOCH))" "$RECEIPT" <<'PY'
import glob, hashlib, json, os, sys
import pandas as pd

(shard_id, out_dir, shard_list, frozen_list, start, count, fasta, threads,
 start_iso, end_iso, elapsed, receipt) = sys.argv[1:13]

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()

def ordered_digest(items):
    h = hashlib.sha256()
    for i, s in enumerate(items):
        h.update(str(i).encode()); h.update(b"\x1f")
        h.update(str(s).encode()); h.update(b"\x1e")
    return h.hexdigest()

expected = [l.strip() for l in open(shard_list) if l.strip()]
outputs, axis_ok, axis_detail = {}, True, {}

for p in sorted(glob.glob(os.path.join(out_dir, shard_id + "*.feather"))):
    outputs[os.path.basename(p)] = {"bytes": os.path.getsize(p), "sha256": sha(p)}

# Re-read the motifs_vs_regions scores from DISK and verify its motif axis is exactly
# this shard's frozen slice, in order. An incomplete or mis-sliced shard must not be
# able to present itself as complete.
target = os.path.join(out_dir, shard_id + ".motifs_vs_regions.scores.feather")
if os.path.exists(target):
    df = pd.read_feather(target)
    cols = [c for c in df.columns if c != "regions"]
    axis_ok = (cols == expected)
    axis_detail = {
        "n_motifs_in_output": len(cols),
        "n_motifs_expected": len(expected),
        "motif_axis_matches_shard_slice_in_order": axis_ok,
        "output_ordered_motif_digest": ordered_digest(cols),
        "shard_slice_ordered_motif_digest": ordered_digest(expected),
        "n_regions_in_output": int(df.shape[0]),
    }
else:
    axis_ok = False
    axis_detail = {"error": "motifs_vs_regions scores feather absent"}

rec = {
    "schema": "V69_CISTARGET_MOTIF_SHARD_V1",
    "shard_id": shard_id,
    "frozen_motif_list": frozen_list,
    "frozen_motif_list_sha256": sha(frozen_list),
    "slice_start_1based": int(start),
    "slice_count": int(count),
    "shard_motif_list": shard_list,
    "shard_motif_list_sha256": sha(shard_list),
    "region_fasta": fasta,
    "region_fasta_sha256": sha(fasta),
    "workers": int(threads),
    "started_utc": start_iso,
    "finished_utc": end_iso,
    "wall_clock_seconds": int(elapsed),
    "outputs": outputs,
    "motif_axis_verification": axis_detail,
    "verified_by_rereading_outputs_from_disk": True,
    "status": ("PASS__SHARD_COMPLETE" if (outputs and axis_ok)
               else "FAIL__SHARD_INCOMPLETE_OR_AXIS_MISMATCH"),
}
with open(receipt, "w") as fh:
    json.dump(rec, fh, indent=2)
    fh.write("\n")
print(json.dumps({k: v for k, v in rec.items() if k != "outputs"}, indent=2))
sys.exit(0 if rec["status"].startswith("PASS") else 4)
PY
echo "=== SHARD $SHARD_ID FINISHED ==="
