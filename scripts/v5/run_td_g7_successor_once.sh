#!/usr/bin/env bash
# One-shot, fail-closed launcher for the TD G7 successor at 8d41fb98 (external audit: PR #296, review 5486851355).
#
# usage: run_td_g7_successor_once.sh QUALIFY|EXECUTE <authority commit> <audited operational-authorization SHA-256>
#
# Must run from a clean checkout of <authority commit>, which holds this launcher, the launch checks and the three
# fresh authority records. Both modes run the identical path up to the attempt marker:
#   - fresh paths;
#   - G6 namespace pins;
#   - exact detached execution worktree at 8d41fb98 and its code identity;
#   - authority materialized from immutable commits;
#   - R1 scope lock;
#   - PR #259 and real-input pins;
#   - G7's own pre-marker path, including bind_execution with the fresh authority;
#   - the R2 replay: G1b, 35 shards, 34 matrices, join, sources.
# QUALIFY then stops before G7 and writes only under a timestamped launch-qualification directory. It never creates
# the EXECUTE paths, never creates a G7 marker and never invokes G7. EXECUTE invokes the G7 entrypoint exactly once.
# Nothing here invokes G6.
set -u
MODE=${1:-}
AUTH_COMMIT=${2:-}
EXPECTED_OP_SHA=${3:-}
TAG=8d41fb98
IMPL=8d41fb9838b425ddcb704ecbdf5cd51f3eeb9f27
REPO="D:/Jepa project"
RUN=D:/jepa_td_real_g6_20261011
G6NS=$RUN/G6_OUT_ff4a21f9
OLD_G6=$RUN/G6_OUT_fafd4309
OUTDIR=$RUN/G7_OUT_$TAG
OUT=$OUTDIR/G7_RECEIPT.json
MARKER=$OUTDIR/G7_RECEIPT.json.STARTED_NOT_A_PASS.json
CACHE="D:/Jepa project/data/cache/s174_rebuilt_real_train_v1"
FREEZE="D:/Jepa project/exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv"
PROVENANCE="D:/Jepa project/results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz"
COLLISION="D:/Jepa project-stage81a3r-20260814/results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz"
PY=C:/Users/dushy/anaconda3/python.exe
AUTH_DIR_REL=custody/owner_decisions/20261012
OWNER_REL=$AUTH_DIR_REL/TD_G6G7_OWNER_DECISION_$TAG.json
RUNTIME_REL=$AUTH_DIR_REL/TD_G6G7_RUNTIME_AUTHORIZATION_$TAG.json
OPERATIONAL_REL=$AUTH_DIR_REL/TD_G7_OPERATIONAL_AUTHORIZATION_$TAG.json
ACCEPTANCE_COMMIT=17a68667174ae8583305c546639dced7dded94d9
ACCEPTANCE_REL=docs/agent/TD_G6_EXTERNAL_ACCEPTANCE_ff4a21f9_20261011.json
PR259_COMMIT=80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947
PR259_BASE=results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split
export PYTHONDONTWRITEBYTECODE=1

case "$MODE" in
  QUALIFY) STAMP=$(date -u +%Y%m%dT%H%M%SZ); QROOT=$RUN/launch_qualification_g7_${TAG}_$STAMP
           AUTH=$QROOT/authority; REC=$QROOT/record; P=$QROOT/pr259; EXEC=D:/jepa_wt_td_g7_launchqual_${TAG}_$STAMP ;;
  EXECUTE) AUTH=$RUN/authority_g7_$TAG; REC=$RUN/run_record_g7_$TAG; P=$RUN/pr259_authority_g7_$TAG
           EXEC=D:/jepa_wt_td_g7_exec_$TAG ;;
  *) echo "STOP: mode must be QUALIFY or EXECUTE"; exit 1 ;;
esac
if ! [[ "$AUTH_COMMIT" =~ ^[0-9a-f]{40}$ && "$EXPECTED_OP_SHA" =~ ^[0-9a-f]{64}$ ]]; then
  echo "STOP: need a 40-hex authority commit and a 64-hex audited operational-authorization SHA-256"; exit 1
fi
for d in "$AUTH" "$REC" "$P" "$EXEC"; do [ -e "$d" ] && { echo "STOP: path already exists: $d"; exit 1; }; done
[ -e "$OUTDIR" ] || [ -e "$OUT" ] || [ -e "$MARKER" ] && { echo "STOP: G7 output namespace already exists: $OUTDIR"; exit 1; }
mkdir -p "$AUTH" "$REC" "$P"
stop() { echo "STOP before any G7 marker: $*" | tee -a "$REC/PRECONDITION_STOP.txt"; exit 1; }
pin() { [ -f "$1" ] && [ "$(sha256sum "$1" | cut -c1-64)" = "$2" ] || stop "pin mismatch or missing: $1"; echo "MATCH $2 $1" >> "$REC/PRECONDITION_PINS.txt"; }
{ echo "mode=$MODE utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "authority_commit=$AUTH_COMMIT"; echo "expected_operational_sha256=$EXPECTED_OP_SHA"
  echo "auth=$AUTH rec=$REC pr259=$P exec=$EXEC g7_out=$OUTDIR"; } > "$REC/LAUNCH_CONTEXT.txt"

# 1. this launcher and its checks run from a clean checkout of the authority commit
LAUNCH_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -W 2>/dev/null || pwd)
[ "$(git -C "$LAUNCH_ROOT" rev-parse HEAD)" = "$AUTH_COMMIT" ] || stop "launcher checkout HEAD is not the authority commit"
[ -z "$(git -C "$LAUNCH_ROOT" status --porcelain)" ] || stop "launcher checkout is not clean"
LAUNCHER=$LAUNCH_ROOT/scripts/v5/run_td_g7_successor_once.sh
CHECKS=$LAUNCH_ROOT/scripts/v5/td_g7_successor_launch_checks.py
echo "launcher_sha256=$(sha256sum "$LAUNCHER" | cut -c1-64) checks_sha256=$(sha256sum "$CHECKS" | cut -c1-64)" >> "$REC/LAUNCH_CONTEXT.txt"

# 2. accepted G6 namespace exactly five pinned files; the old fafd4309 namespace unchanged
( cd "$G6NS" && ls -la && sha256sum * ) > "$REC/G6_ACCEPTED_NAMESPACE_BEFORE.txt" 2>&1
( cd "$OLD_G6" && ls -la && sha256sum * ) > "$REC/OLD_G6_OUT_fafd4309_BEFORE.txt" 2>&1
[ "$(ls -1 "$G6NS" | wc -l)" = "5" ] || stop "accepted G6 namespace does not hold exactly five files"
pin "$G6NS/G6_EXECUTION_START.json" 49bdff31a1a055b1bbf1ff539a49a93413c83bf0ab8838494485bc56492bd4f1
pin "$G6NS/G6_RECEIPT.json" 2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b
pin "$G6NS/MANIFEST.json" 4fbc14ceda829cca7446e67b9ad25d428608c5aaa5e87d08ae07c412279427bf
pin "$G6NS/TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz" fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9
pin "$G6NS/TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz" bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74
pin "$OLD_G6/G6_EXECUTION_START.json" ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894

# 3. exact clean detached execution worktree at the qualified implementation commit, and its code identity
git -C "$REPO" worktree add --detach "$EXEC" "$IMPL" > "$REC/EXEC_WORKTREE.txt" 2>&1 || stop "worktree creation failed"
[ "$(git -C "$EXEC" rev-parse HEAD)" = "$IMPL" ] || stop "execution HEAD is not $IMPL"
[ -z "$(git -C "$EXEC" status --porcelain)" ] || stop "execution worktree not clean"

# 4. authority materialized from immutable commits; the audited operational-authorization SHA releases it
DEC=$AUTH/TD_G6G7_OWNER_DECISION_$TAG.json; AUZ=$AUTH/TD_G6G7_RUNTIME_AUTHORIZATION_$TAG.json
G7AUTH=$AUTH/TD_G7_OPERATIONAL_AUTHORIZATION_$TAG.json; G6ACC=$AUTH/TD_G6_EXTERNAL_ACCEPTANCE_ff4a21f9_20261011.json
git -C "$REPO" cat-file blob "$AUTH_COMMIT:$OWNER_REL" > "$DEC" || stop "cannot materialize owner decision"
git -C "$REPO" cat-file blob "$AUTH_COMMIT:$RUNTIME_REL" > "$AUZ" || stop "cannot materialize runtime authorization"
git -C "$REPO" cat-file blob "$AUTH_COMMIT:$OPERATIONAL_REL" > "$G7AUTH" || stop "cannot materialize operational authorization"
git -C "$REPO" cat-file blob "$ACCEPTANCE_COMMIT:$ACCEPTANCE_REL" > "$G6ACC" || stop "cannot materialize G6 external acceptance"
pin "$G7AUTH" "$EXPECTED_OP_SHA"
pin "$G6ACC" 89932183a2c7b56d1e3ae42264ea3f3b3ae9001d865cfa93604b46f0db2129fb

# 5. R1 scope lock and every authority binding (owner, runtime, operational; no spent ff4a21f9 authority)
"$PY" "$CHECKS" authority --owner-decision "$DEC" --runtime-authorization "$AUZ" --operational-authorization "$G7AUTH" \
  --expected-operational-sha256 "$EXPECTED_OP_SHA" --launcher "$LAUNCHER" > "$REC/AUTHORITY_CHECK.json" 2>&1 \
  || stop "authority / R1 scope-lock check failed (see AUTHORITY_CHECK.json)"

# 6. immutable PR #259 receipts and real metadata inputs
for f in PREFLIGHT_RESULT.json TD_RELATIONAL_MAPPING_PREFLIGHT.json JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv S174_REBUILD_FREEZE_V1.json; do
  git -C "$REPO" cat-file blob "$PR259_COMMIT:$PR259_BASE/$f" > "$P/$f" || stop "cannot materialize PR259 $f"
done
pin "$P/PREFLIGHT_RESULT.json" 62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae
pin "$P/TD_RELATIONAL_MAPPING_PREFLIGHT.json" 6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0
pin "$P/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv" 4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660
pin "$P/S174_REBUILD_FREEZE_V1.json" 240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c
pin "$FREEZE" 79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6
pin "$PROVENANCE" df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51
pin "$COLLISION" f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722

G7_ARGS=(--preflight-result "$P/PREFLIGHT_RESULT.json" --mapping-receipt "$P/TD_RELATIONAL_MAPPING_PREFLIGHT.json"
  --value-authorization "$AUZ" --owner-decision "$DEC" --g6-receipt "$G6NS/G6_RECEIPT.json" --g6-acceptance "$G6ACC"
  --replay-manifest "$P/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv" --sample-freeze "$FREEZE" --provenance "$PROVENANCE"
  --collision-ledger "$COLLISION" --macha-freeze "$P/S174_REBUILD_FREEZE_V1.json" --s174-cache-root "$CACHE"
  --source-root "D:/Jepa project")

# 7. G7's own pre-marker path (bind_execution with the fresh authority, continuity, inputs, accepted-G6 bridge) and
#    the R2 replay of the post-marker metadata prerequisites; read-only, from the exact execution worktree
"$PY" "$CHECKS" prestart --exec-root "$EXEC" "${G7_ARGS[@]}" > "$REC/PRESTART_CHECK.json" 2>&1 \
  || stop "G7 pre-marker path / R2 replay failed (see PRESTART_CHECK.json)"
[ -z "$(git -C "$EXEC" status --porcelain)" ] || stop "execution worktree changed during the pre-start checks"
[ -e "$OUTDIR" ] && stop "G7 output namespace appeared during the pre-start checks"

if [ "$MODE" = "QUALIFY" ]; then
  echo "QUALIFY_PASS__STOPPED_BEFORE_G7__NO_MARKER__NO_G7_INVOCATION utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee "$REC/QUALIFY_RESULT.txt"
  ( cd "$G6NS" && ls -la && sha256sum * ) > "$REC/G6_ACCEPTED_NAMESPACE_AFTER.txt" 2>&1
  cmp -s "$REC/G6_ACCEPTED_NAMESPACE_BEFORE.txt" "$REC/G6_ACCEPTED_NAMESPACE_AFTER.txt" || stop "accepted G6 namespace changed"
  exit 0
fi

# 8. EXECUTE: the G7 entrypoint exactly once (never G6)
CMD=("$PY" "$EXEC/scripts/v5/audit_td_relational_g7_s174_overlap_v2.py" "${G7_ARGS[@]}" --out "$OUT")
{ echo "utc_start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "exec_head=$(git -C "$EXEC" rev-parse HEAD) status=[$(git -C "$EXEC" status --short)]"
  "$PY" -c "import sys,numpy,pandas,scipy,h5py;print('python',sys.version.split()[0],'numpy',numpy.__version__,'pandas',pandas.__version__,'scipy',scipy.__version__,'h5py',h5py.__version__)"
  printf 'command:'; printf ' %q' "${CMD[@]}"; echo; } > "$REC/RUN_RECORD.txt" 2>&1
"${CMD[@]}" > "$REC/g7.stdout.txt" 2> "$REC/g7.stderr.txt"
RC=$?
echo "exit_code=$RC utc_end=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$REC/RUN_RECORD.txt"

# 9. preserve and hash the G7 namespace whatever the outcome; re-record both G6 namespaces; never repair or rerun
( cd "$OUTDIR" 2>/dev/null && ls -la && sha256sum * ) > "$REC/G7_NAMESPACE_SHA256.txt" 2>&1
echo "exec_status_after=[$(git -C "$EXEC" status --short)] exec_head_after=$(git -C "$EXEC" rev-parse HEAD)" >> "$REC/RUN_RECORD.txt"
( cd "$G6NS" && ls -la && sha256sum * ) > "$REC/G6_ACCEPTED_NAMESPACE_AFTER.txt" 2>&1
( cd "$OLD_G6" && ls -la && sha256sum * ) > "$REC/OLD_G6_OUT_fafd4309_AFTER.txt" 2>&1
cmp -s "$REC/G6_ACCEPTED_NAMESPACE_BEFORE.txt" "$REC/G6_ACCEPTED_NAMESPACE_AFTER.txt" \
  && echo "accepted_G6_OUT_ff4a21f9_unchanged=true" >> "$REC/RUN_RECORD.txt" || echo "accepted_G6_OUT_ff4a21f9_unchanged=FALSE" >> "$REC/RUN_RECORD.txt"
cmp -s "$REC/OLD_G6_OUT_fafd4309_BEFORE.txt" "$REC/OLD_G6_OUT_fafd4309_AFTER.txt" \
  && echo "old_G6_OUT_fafd4309_unchanged=true" >> "$REC/RUN_RECORD.txt" || echo "old_G6_OUT_fafd4309_unchanged=FALSE" >> "$REC/RUN_RECORD.txt"
"$PY" - "$OUT" "$MARKER" >> "$REC/POSTRUN_SUMMARY.txt" 2>&1 <<'PY'
import hashlib, json, sys
from pathlib import Path
out, marker = Path(sys.argv[1]), Path(sys.argv[2])
print("marker_exists", marker.is_file(), "marker_sha256", hashlib.sha256(marker.read_bytes()).hexdigest() if marker.is_file() else None)
if not out.is_file():
    print("receipt_written False"); raise SystemExit(0)
r = json.loads(out.read_text(encoding="utf-8"))
print("receipt_sha256", hashlib.sha256(out.read_bytes()).hexdigest())
for k in ("schema", "status", "natural_overlap_cells", "checked_cell_address_entries", "mismatches", "s174_verified_shards",
          "no_overlap_is_not_pass", "biological_replay_authorized", "target_selection_authorized", "td60_authorized",
          "training_authorized"):
    print(k, r.get(k))
print("g6_predecessor_acceptance", (r.get("g6_predecessor") or {}).get("external_acceptance_sha256"))
PY
echo "G7_EXIT_CODE=$RC (0 PASS, 3 NOT_ESTIMABLE, 2 mismatch/stop, 1 exception). STOP for external audit."
exit $RC
