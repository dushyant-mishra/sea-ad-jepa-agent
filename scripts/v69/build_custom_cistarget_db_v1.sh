#!/usr/bin/env bash
# V69: build a CUSTOM cisTarget motif database over one route's own region universe.
#
# Runs inside the validated SCENIC+ container. Both routes use the identical motif
# collection, identical cbust binary, identical hg38 analysis-set FASTA and identical
# parameters, so the REGION UNIVERSE is the only thing that differs between them.
# That isolation is the whole point of the Route-A/Route-B comparison and is required
# by amendment 1 of the V69 prospective freeze.
#
# Usage (inside container):
#   build_custom_cistarget_db_v1.sh <route_id> <regions_bed> <out_dir> <n_threads> [n_motifs_limit]
#
# A positive <n_motifs_limit> runs a BENCHMARK over that many motifs so the full-run
# cost is MEASURED rather than estimated. A benchmark database is written to a
# separate prefix and must never be used as a real database.
set -euo pipefail

ROUTE_ID="${1:?route id}"
REGIONS_BED="${2:?regions bed}"
OUT_DIR="${3:?output dir}"
NTHREADS="${4:-16}"
NMOTIF_LIMIT="${5:-0}"

RES=/data/resources
FASTA="$RES/hg38.analysisSet.fa"
MOTIF_DIR="$RES/v10nr_clust_public/singletons"
BG_PADDING=1000   # create_cisTarget_databases default; adopted unchanged, not tuned

mkdir -p "$OUT_DIR"

echo "=== [1/4] chromosome sizes ==="
if [ ! -s "$RES/hg38.analysisSet.chrom.sizes" ]; then
  micromamba run -n base samtools faidx "$FASTA"
  cut -f1,2 "$FASTA.fai" > "$RES/hg38.analysisSet.chrom.sizes"
fi
wc -l < "$RES/hg38.analysisSet.chrom.sizes"

echo "=== [2/4] motif list ==="
MOTIF_LIST="$OUT_DIR/motifs.lst"
ls "$MOTIF_DIR" | sed 's/\.cb$//' | sort > "$MOTIF_LIST.full"
N_FULL=$(wc -l < "$MOTIF_LIST.full")
if [ "$NMOTIF_LIMIT" -gt 0 ]; then
  head -n "$NMOTIF_LIMIT" "$MOTIF_LIST.full" > "$MOTIF_LIST"
  DB_PREFIX="$OUT_DIR/BENCHMARK_${ROUTE_ID}_${NMOTIF_LIMIT}motifs"
  echo "BENCHMARK MODE: $NMOTIF_LIMIT of $N_FULL motifs"
else
  cp "$MOTIF_LIST.full" "$MOTIF_LIST"
  DB_PREFIX="$OUT_DIR/V69_${ROUTE_ID}_CUSTOM_CISTARGET"
  echo "FULL MODE: $N_FULL motifs"
fi
N_MOTIFS=$(wc -l < "$MOTIF_LIST")
sha256sum "$MOTIF_LIST" | tee "$OUT_DIR/motifs.lst.sha256"

echo "=== [3/4] region FASTA with padded background (padding=${BG_PADDING}) ==="
REGION_FA="$OUT_DIR/${ROUTE_ID}_regions_padded_bg.fa"
if [ ! -s "$REGION_FA" ]; then
  # Invoke as a SUBPROCESS, never `source`. That helper ends with
  #     create_fasta_with_padded_bg_from_bed "${@}"
  # so sourcing it immediately re-invokes the function with THIS script's positional
  # arguments, silently building the wrong FASTA from the wrong paths.
  micromamba run -n base bash \
    /opt/create_cisTarget_databases/create_fasta_with_padded_bg_from_bed.sh \
    "$FASTA" \
    "$RES/hg38.analysisSet.chrom.sizes" \
    "$REGIONS_BED" \
    "$REGION_FA" \
    "$BG_PADDING" \
    1
fi
N_FA=$(grep -c '^>' "$REGION_FA")
N_BED=$(wc -l < "$REGIONS_BED")
echo "regions in BED: $N_BED   sequences in FASTA: $N_FA"
if [ "$N_FA" -ne "$N_BED" ]; then
  echo "FAIL__REGION_FASTA_SEQUENCE_COUNT_NE_BED_REGION_COUNT bed=$N_BED fasta=$N_FA" >&2
  exit 3
fi
sha256sum "$REGION_FA" | tee "$OUT_DIR/$(basename "$REGION_FA").sha256"

echo "=== [4/4] cisTarget motif database ==="
START=$(date -u +%s)
micromamba run -n base python \
  /opt/create_cisTarget_databases/create_cistarget_motif_databases.py \
  -f "$REGION_FA" \
  -M "$MOTIF_DIR" \
  -m "$MOTIF_LIST" \
  -o "$DB_PREFIX" \
  -c /usr/local/bin/cbust \
  -t "$NTHREADS"
END=$(date -u +%s)
ELAPSED=$((END - START))

echo "MEASURED_ELAPSED_SECONDS=$ELAPSED"
echo "N_MOTIFS=$N_MOTIFS"
echo "N_REGIONS=$N_BED"
echo "SECONDS_PER_MOTIF=$(awk -v e="$ELAPSED" -v n="$N_MOTIFS" 'BEGIN{printf "%.4f", e/n}')"
ls -l "$DB_PREFIX"* || true
for f in "$DB_PREFIX"*.feather; do
  [ -e "$f" ] && sha256sum "$f" | tee "$f.sha256"
done
echo "=== DB BUILD FINISHED ==="
