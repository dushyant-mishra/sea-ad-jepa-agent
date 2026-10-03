#!/usr/bin/env bash
# V74 LANE E: prove, behaviourally, that a killed shard restarts INDEPENDENTLY and that
# completed shards are NOT rebuilt -- and that the skip is driven by output DIGESTS, not
# by the mere presence of a receipt.
#
# Why this is run at 4 motifs per shard and not at 512: the property under test is the
# receipt-validation and skip logic, which is scale-independent. A 512-motif version
# would cost ~5 hours and would test exactly the same branch. The scale-dependent
# questions -- wall time, overhead, peak scratch, peak memory -- are measured separately
# by the 512-motif pilot. That split is a deliberate scope limit, stated rather than
# implied.
#
# The script executed by each shard is the IMMUTABLE snapshot outside the worktree.
#
# Usage: laneE_restart_and_merge_behaviour_v1.sh
set -uo pipefail

SCRATCH=C:/jepa_scratch/v74_laneE
RUN="$SCRATCH/restart/run1"
EV="$SCRATCH/restart/EVIDENCE.txt"
IMG=scenicplus:1.0a2-container.1
FROZEN=/data/routeA/cistarget_benchmark/motifs.lst.full
FASTA=/data/routeA/cistarget_benchmark/ROUTE_A_SUBMITTED_PEAKS_regions_padded_bg.fa
DRIVER=/scratch/shared/immutable_scripts/run_cistarget_motif_shard_v1.sh

rm -rf "$RUN"; mkdir -p "$RUN"
: > "$EV"
log() { echo "$*" | tee -a "$EV"; }

shard() {   # shard(id, start, count, container_name)
  MSYS_NO_PATHCONV=1 docker run --rm --name "$4" \
    -v "D:/jepa_v5_outputs_20260925/v69_scenicplus:/data:ro" \
    -v "$SCRATCH:/scratch" \
    "$IMG" bash "$DRIVER" "$1" "$FROZEN" "$2" "$3" "$FASTA" /scratch/restart/run1 4
}

log "=== V74 LANE E restart/merge behaviour, $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
log "--- driver digest actually executed ---"
sha256sum "$SCRATCH/shared/immutable_scripts/run_cistarget_motif_shard_v1.sh" | tee -a "$EV"

# ---- STEP 1: two shards to completion -----------------------------------------
log ""
log "### STEP 1: build SHARD_A (motifs 1-4) and SHARD_B (motifs 5-8) to completion"
shard SHARD_A 1 4 v74E_A >>"$EV" 2>&1; log "SHARD_A rc=$?"
shard SHARD_B 5 4 v74E_B >>"$EV" 2>&1; log "SHARD_B rc=$?"
for S in SHARD_A SHARD_B; do
  log "$S receipt status: $(python -c "import json;print(json.load(open(r'$RUN/$S.shard.json'))['status'])")"
done

log ""
log "--- fingerprint of the completed shards BEFORE the interruption ---"
BEFORE="$SCRATCH/restart/before.txt"
( cd "$RUN" && sha256sum SHARD_A.*.feather SHARD_B.*.feather && \
  stat -c '%n %Y %s' SHARD_A.*.feather SHARD_B.*.feather ) | tee "$BEFORE" | tee -a "$EV"

# ---- STEP 2: kill SHARD_C mid-run ---------------------------------------------
log ""
log "### STEP 2: start SHARD_C (motifs 9-12) and KILL it mid-run"
shard SHARD_C 9 4 v74E_C >>"$EV" 2>&1 &
BGPID=$!
sleep 75
docker kill v74E_C >>"$EV" 2>&1 && log "docker kill v74E_C issued at $(date -u +%H:%M:%SZ)"
wait $BGPID; log "SHARD_C interrupted run rc=$?"
if [ -s "$RUN/SHARD_C.shard.json" ]; then
  log "DEFECT: SHARD_C wrote a receipt despite being killed"
else
  log "OK: SHARD_C has NO receipt -- an interrupted shard cannot look complete"
fi
log "SHARD_C leftovers: $(ls "$RUN" | grep -c '^SHARD_C') file(s): $(ls "$RUN" | grep '^SHARD_C' | tr '\n' ' ')"

# ---- STEP 3: restart the whole plan -------------------------------------------
log ""
log "### STEP 3: re-run ALL THREE shards. A and B must be SKIPPED, C must rebuild."
R="$SCRATCH/restart/restart_output.txt"
: > "$R"
for spec in "SHARD_A 1 4 v74E_A2" "SHARD_B 5 4 v74E_B2" "SHARD_C 9 4 v74E_C2"; do
  set -- $spec
  echo "--- $1 ---" >> "$R"
  shard "$1" "$2" "$3" "$4" >> "$R" 2>&1
  echo "rc=$?" >> "$R"
done
cat "$R" >> "$EV"
log "SHARD_A skipped: $(grep -c 'SHARD_A ALREADY COMPLETE AND DIGEST-VERIFIED' "$R")"
log "SHARD_B skipped: $(grep -c 'SHARD_B ALREADY COMPLETE AND DIGEST-VERIFIED' "$R")"
log "SHARD_C rebuilt: $(grep -c 'SHARD SHARD_C FINISHED' "$R")"

log ""
log "--- fingerprint AFTER the restart: completed shards must be byte- and mtime-identical ---"
AFTER="$SCRATCH/restart/after.txt"
( cd "$RUN" && sha256sum SHARD_A.*.feather SHARD_B.*.feather && \
  stat -c '%n %Y %s' SHARD_A.*.feather SHARD_B.*.feather ) | tee "$AFTER" | tee -a "$EV"
if diff -q "$BEFORE" "$AFTER" >/dev/null; then
  log "PASS: completed shards were NOT touched by the restart (digests AND mtimes identical)"
else
  log "FAIL: the restart modified completed shards"
  diff "$BEFORE" "$AFTER" | tee -a "$EV"
fi

# ---- STEP 4: NEGATIVE CONTROL -- corrupt one byte of a completed output --------
# If the skip were driven by the presence of a receipt rather than by the digests it
# records, this shard would be skipped and the corruption would survive into the merge.
log ""
log "### STEP 4: NEGATIVE CONTROL -- corrupt 1 byte of SHARD_A output, re-run"
TARGET="$RUN/SHARD_A.motifs_vs_regions.scores.feather"
python - "$TARGET" <<'PY'
import sys
p = sys.argv[1]
with open(p, "r+b") as fh:
    fh.seek(1024)
    b = fh.read(1)
    fh.seek(1024)
    fh.write(bytes([b[0] ^ 0xFF]))
print("flipped one byte at offset 1024 of", p)
PY
log "corrupted digest now: $(sha256sum "$TARGET" | awk '{print $1}')"
C="$SCRATCH/restart/corrupt_rerun.txt"
shard SHARD_A 1 4 v74E_A3 > "$C" 2>&1; log "SHARD_A corrupt re-run rc=$?"
cat "$C" >> "$EV"
if grep -q 'ALREADY COMPLETE AND DIGEST-VERIFIED' "$C"; then
  log "FAIL: a corrupted output was SKIPPED -- the gate is presence-based, not digest-based"
else
  log "PASS: the corrupted shard was NOT skipped; it was rebuilt"
fi
log "SHARD_A digest after rebuild: $(sha256sum "$TARGET" | awk '{print $1}')"
log "(must equal the pre-corruption digest in before.txt, which proves the rebuild is deterministic)"

log ""
log "=== finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
cp "$EV" "D:/jepa_v5_outputs_20260925/v74_laneE/logs/RESTART_BEHAVIOUR_EVIDENCE.txt"
