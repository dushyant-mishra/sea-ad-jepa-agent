#!/usr/bin/env bash
# REAL TD: G7 exactly once at ff4a21f9 against the externally accepted replacement G6, then STOP.
# Authority: TD_G7_OPERATIONAL_AUTHORIZATION_ff4a21f9.json (19a50126...) + the code-consumed owner decision (3d457d4d...)
# and runtime authorization (28b3a0c8...), byte-exact from their immutable commits; runbook MACHA_G7_RUNBOOK_ff4a21f9.
# Every pre-start check (runbook 1-9) runs BEFORE G7 can create its start marker. Because G7 loads the G1b authority and
# verifies the S174 cache only AFTER its marker, those exact G7 functions are executed here read-only first (step 8).
# Any precondition failure stops with the attempt unspent. Never retries. No TD56/57B/57C/59, TD60, selection or training.
set -u
REPO="D:/Jepa project"
EXEC=D:/jepa_wt_td_g7_exec_ff4a21f9
COMMIT=ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0
RUN=D:/jepa_td_real_g6_20261011
AUTH=$RUN/authority_g7_ff4a21f9; REC=$RUN/run_record_g7_ff4a21f9; P=$RUN/pr259_authority_g7_ff4a21f9
G6NS=$RUN/G6_OUT_ff4a21f9
OUTDIR=$RUN/G7_OUT_ff4a21f9; OUT=$OUTDIR/G7_RECEIPT.json; MARKER=$OUTDIR/G7_RECEIPT.json.STARTED_NOT_A_PASS.json
OLD_G6=$RUN/G6_OUT_fafd4309
CACHE="D:/Jepa project/data/cache/s174_rebuilt_real_train_v1"
PY=C:/Users/dushy/anaconda3/python.exe
for d in "$AUTH" "$REC" "$P" "$OUTDIR"; do [ -e "$d" ] && { echo "STOP: path already exists: $d"; exit 1; }; done
mkdir -p "$AUTH" "$REC" "$P"
stop() { echo "STOP before spending G7: $*" | tee -a "$REC/PRECONDITION_STOP.txt"; exit 1; }
pin() { [ -f "$1" ] && [ "$(sha256sum "$1" | cut -c1-64)" = "$2" ] || stop "pin mismatch or missing: $1"; echo "MATCH $2 $1" >> "$REC/PRECONDITION_PINS.txt"; }

# 0. both G6 namespaces are evidence: record before (the accepted one must hold exactly its five accepted files)
( cd "$G6NS" && ls -la && sha256sum * ) > "$REC/G6_ACCEPTED_NAMESPACE_BEFORE.txt" 2>&1
( cd "$OLD_G6" && ls -la && sha256sum * ) > "$REC/OLD_G6_OUT_fafd4309_BEFORE.txt" 2>&1
[ "$(ls -1 "$G6NS" | wc -l)" = "5" ] || stop "accepted G6 namespace does not hold exactly five files"
pin "$G6NS/G6_EXECUTION_START.json" 49bdff31a1a055b1bbf1ff539a49a93413c83bf0ab8838494485bc56492bd4f1
pin "$G6NS/G6_RECEIPT.json" 2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b
pin "$G6NS/MANIFEST.json" 4fbc14ceda829cca7446e67b9ad25d428608c5aaa5e87d08ae07c412279427bf
pin "$G6NS/TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz" fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9
pin "$G6NS/TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz" bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74
pin "$OLD_G6/G6_EXECUTION_START.json" ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894

# 1-2. fresh clean detached worktree at exactly ff4a21f9; qualified common/G6/G7 identity via the code's own code_identity
[ -e "$EXEC" ] && stop "execution worktree path already exists: $EXEC"
git -C "$REPO" worktree add --detach "$EXEC" "$COMMIT" || stop "worktree creation failed"
[ "$(git -C "$EXEC" rev-parse HEAD)" = "$COMMIT" ] || stop "HEAD is not $COMMIT"
[ -z "$(git -C "$EXEC" status --short)" ] || stop "execution worktree not clean"
"$PY" - "$EXEC" "$COMMIT" <<'PY' || stop "qualified implementation identity mismatch"
import importlib.util, sys
from pathlib import Path
root = Path(sys.argv[1]); v5 = root / "scripts" / "v5"
spec = importlib.util.spec_from_file_location("td_value_v2_common", v5 / "td_relational_value_read_v2_common.py")
common = importlib.util.module_from_spec(spec); spec.loader.exec_module(common)
identity = common.code_identity(v5 / "materialize_td_relational_corrected_sampleA_v2.py",
                                v5 / "audit_td_relational_g7_s174_overlap_v2.py")
want = {"implementation_commit_sha": sys.argv[2],
        "common_script_sha256": "23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea",
        "g6_script_sha256": "8e6504e02e909a030a33b3fa2b4742fd78354486c1d2a0f40575c11108a6877d",
        "g7_script_sha256": "f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe",
        "common_entrypoint": "scripts/v5/td_relational_value_read_v2_common.py",
        "g6_entrypoint": "scripts/v5/materialize_td_relational_corrected_sampleA_v2.py",
        "g7_entrypoint": "scripts/v5/audit_td_relational_g7_s174_overlap_v2.py"}
if identity != want:
    raise SystemExit(f"IDENTITY MISMATCH\nactual={identity}\nexpected={want}")
print("qualified implementation identity: MATCH")
PY

# 3-4. fresh G7 operational authorization, G6 external acceptance, and the code-consumed owner decision and runtime
# authorization, byte-exact from their full immutable commits (never reserialized)
G7AUTH=$AUTH/TD_G7_OPERATIONAL_AUTHORIZATION_ff4a21f9.json; G6ACC=$AUTH/TD_G6_EXTERNAL_ACCEPTANCE_ff4a21f9_20261011.json
DEC=$AUTH/TD_G6G7_OWNER_DECISION_ff4a21f9.json; AUZ=$AUTH/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json
git -C "$REPO" cat-file blob eba777767928d27032fc23a23b185ebdeb1c881a:custody/owner_decisions/20261011/TD_G7_OPERATIONAL_AUTHORIZATION_ff4a21f9.json > "$G7AUTH" || stop "cannot materialize G7 operational authorization"
git -C "$REPO" cat-file blob 17a68667174ae8583305c546639dced7dded94d9:docs/agent/TD_G6_EXTERNAL_ACCEPTANCE_ff4a21f9_20261011.json > "$G6ACC" || stop "cannot materialize G6 external acceptance"
git -C "$REPO" cat-file blob 8283c726390c63b2dc68ed546a3116059aa70d67:custody/owner_decisions/20261011/TD_G6G7_OWNER_DECISION_ff4a21f9.json > "$DEC" || stop "cannot materialize owner decision"
git -C "$REPO" cat-file blob 8d5637f7eb26703bcd396135598c8da9e70e8ae8:custody/owner_decisions/20261011/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json > "$AUZ" || stop "cannot materialize runtime authorization"
pin "$G7AUTH" 19a50126219d25989ca466a83b813fcbabdeeb148804e1f616bbb7bbdfe3b4ee
pin "$G6ACC" 89932183a2c7b56d1e3ae42264ea3f3b3ae9001d865cfa93604b46f0db2129fb
pin "$DEC" 3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a
pin "$AUZ" 28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7
"$PY" - "$G7AUTH" "$G6ACC" <<'PY' || stop "G7 operational authorization or G6 acceptance content does not bind this run"
import json, sys
a = json.load(open(sys.argv[1], encoding="utf-8")); g = json.load(open(sys.argv[2], encoding="utf-8"))
want = {"implementation_commit_sha": "ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0",
        "g7_script_sha256": "f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe",
        "required_code_consumed_owner_decision_sha256": "3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a",
        "required_code_consumed_runtime_authorization_sha256": "28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7",
        "g6_external_acceptance_sha256": "89932183a2c7b56d1e3ae42264ea3f3b3ae9001d865cfa93604b46f0db2129fb",
        "g6_receipt_sha256": "2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b",
        "g6_values_sha256": "fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9",
        "g6_meta_sha256": "bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74",
        "fresh_output_required": True, "stop_after_g7": True, "corrected_biological_replay_authorized": False,
        "target_selection_authorized": False, "td60_authorized": False, "training_authorized": False,
        "stage4_authorized": False}
bad = {k: (a.get(k), v) for k, v in want.items() if a.get(k) != v}
if bad or not str(a.get("authorization", "")).startswith("EXECUTE_G7_ONCE_AT_ff4a21f9"):
    raise SystemExit(f"G7 operational authorization mismatch: {bad} {a.get('authorization')}")
if g.get("external_audit_disposition") != "ACCEPT_G6_PASS__VALUE_SUBSTRATE_AND_SOURCE_CUSTODY_CONFIRMED__NO_BIOLOGICAL_TARGET_AUTHORITY" \
        or g.get("g7_may_receive_fresh_operational_authority") is not True:
    raise SystemExit("G6 external acceptance does not release G7")
print("G7 operational authorization and G6 acceptance: MATCH")
PY

# 5-7. PR #259 evidence as exact immutable blobs, then every remaining metadata pin
PR259=80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947
BASE=results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split
for f in PREFLIGHT_RESULT.json TD_RELATIONAL_MAPPING_PREFLIGHT.json JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv S174_REBUILD_FREEZE_V1.json; do
  git -C "$REPO" cat-file blob "$PR259:$BASE/$f" > "$P/$f" || stop "cannot materialize PR259 $f"
done
pin "$P/PREFLIGHT_RESULT.json" 62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae
pin "$P/TD_RELATIONAL_MAPPING_PREFLIGHT.json" 6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0
pin "$P/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv" 4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660
pin "$P/S174_REBUILD_FREEZE_V1.json" 240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c
pin "D:/Jepa project/exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv" 79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6
pin "D:/Jepa project/results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz" df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51
pin "D:/Jepa project-stage81a3r-20260814/results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz" f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722

# 8. G1b authority + S174 cache, using G7's OWN functions read-only before the marker can exist; every Sample-A
#    HVS/SEA matrix must have its shard in the G1b authority; every authority meta shard loads through G7's own
#    metadata-only load_s174_cell_index (cell_id present, no duplicates); G7's lazy imports (h5py, scipy.sparse)
#    resolve; physical H5AD sources present at their frozen sizes.
#    Accepted residual risk (independent pre-run audit, finding 1): the 34 physical H5AD SHA-256 values are not
#    re-hashed here (~324 GB). The accepted G6 PASS authenticated all 34 at 2026-10-11T22:49-23:28Z, and its committed
#    receipt binds them. Sizes are re-checked, and G7 re-authenticates each overlapping source itself. A same-size
#    byte change since then would surface after the marker as a G7 failure.
"$PY" - "$EXEC" "$CACHE" "$P/S174_REBUILD_FREEZE_V1.json" > "$REC/PRESTART_G1B_CACHE_CHECK.txt" 2>&1 <<'PY' || stop "G1b authority / S174 cache / source presence pre-check failed (see PRESTART_G1B_CACHE_CHECK.txt)"
import importlib.util, json, os, sys
from pathlib import Path
import pandas as pd
exec_root, cache, freeze_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
g7_path = exec_root / "scripts" / "v5" / "audit_td_relational_g7_s174_overlap_v2.py"
sys.path.insert(0, str(g7_path.parent))
spec = importlib.util.spec_from_file_location("g7_prestart", g7_path)
g7 = importlib.util.module_from_spec(spec); spec.loader.exec_module(g7)
import h5py  # noqa: F401  (G7 imports it lazily after its marker)
from scipy import sparse  # noqa: F401  (likewise)
result, g1b_freeze, result_sha, freeze_sha = g7.load_g1b_authority_from_pass_commit(g7_path)
n, hashes = g7.verify_cache_hashes(cache, g1b_freeze)
print("g1b_result_sha256", result_sha); print("g1b_freeze_sha256", freeze_sha); print("verified_shards", n)
shards = g1b_freeze["rebuilt_cache"]["shards"]
for stem, rec in shards.items():
    cells, where, meta_sha = g7.load_s174_cell_index(cache / f"{stem}.meta.npz", rec["meta"])
    if len(where) != len(cells):
        raise SystemExit(f"STOP: duplicate S174 cell_id in shard {stem}")
print("s174_meta_cell_index_loaded_shards", len(shards))
macha = json.loads(freeze_path.read_text(encoding="utf-8"))
mats = {str(m["matrix_id"]): m for m in macha["matrices"]}
s = pd.read_csv("D:/Jepa project/exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv", dtype=str,
                usecols=["sample", "source", "matrix_id"])
a = s[(s["sample"] == "A_NATURAL_MIXTURE") & (s["source"] != "NPH52")]
missing_stems, missing_src = [], []
for mid in sorted(set(a.matrix_id)):
    m = mats[mid]
    if str(m["stem"]) not in shards:
        missing_stems.append(mid)
    src = Path("D:/Jepa project") / m["source"]["path"]
    if not src.is_file() or os.path.getsize(src) != int(m["source"]["bytes"]):
        missing_src.append(mid)
print("sample_a_hvs_sea_matrices", len(set(a.matrix_id)), "missing_shard_authority", missing_stems, "missing_or_resized_sources", missing_src)
if missing_stems or missing_src or n != len(shards):
    raise SystemExit("STOP: G1b/S174/source pre-check failed")
print("PRESTART_G1B_CACHE_SOURCE_CHECK: PASS")
PY

# 9. fresh never-used receipt path and adjacent marker path
[ -e "$OUT" ] || [ -e "$MARKER" ] || [ -e "$OUTDIR" ] && stop "G7 output path already exists"

# run G7 exactly once
CMD=("$PY" "$EXEC/scripts/v5/audit_td_relational_g7_s174_overlap_v2.py"
  --preflight-result "$P/PREFLIGHT_RESULT.json" --mapping-receipt "$P/TD_RELATIONAL_MAPPING_PREFLIGHT.json"
  --value-authorization "$AUZ" --owner-decision "$DEC" --g6-receipt "$G6NS/G6_RECEIPT.json"
  --replay-manifest "$P/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv"
  --sample-freeze "D:/Jepa project/exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv"
  --provenance "D:/Jepa project/results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz"
  --collision-ledger "D:/Jepa project-stage81a3r-20260814/results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz"
  --macha-freeze "$P/S174_REBUILD_FREEZE_V1.json" --s174-cache-root "$CACHE"
  --source-root "D:/Jepa project" --out "$OUT")
{ echo "utc_start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "exec_head=$(git -C "$EXEC" rev-parse HEAD) status=[$(git -C "$EXEC" status --short)]"
  "$PY" -c "import sys,numpy,pandas,scipy,h5py;print('python',sys.version.split()[0],'numpy',numpy.__version__,'pandas',pandas.__version__,'scipy',scipy.__version__,'h5py',h5py.__version__)"
  printf 'command:'; printf ' %q' "${CMD[@]}"; echo; } > "$REC/RUN_RECORD.txt" 2>&1
PYTHONDONTWRITEBYTECODE=1 "${CMD[@]}" > "$REC/g7.stdout.txt" 2> "$REC/g7.stderr.txt"
RC=$?
echo "exit_code=$RC utc_end=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$REC/RUN_RECORD.txt"

# preserve and hash the G7 namespace whatever the outcome; re-record both G6 namespaces
( cd "$OUTDIR" 2>/dev/null && ls -la && sha256sum * ) > "$REC/G7_NAMESPACE_SHA256.txt" 2>&1
echo "exec_status_after=[$(git -C "$EXEC" status --short)] exec_head_after=$(git -C "$EXEC" rev-parse HEAD)" >> "$REC/RUN_RECORD.txt"
( cd "$G6NS" && ls -la && sha256sum * ) > "$REC/G6_ACCEPTED_NAMESPACE_AFTER.txt" 2>&1
( cd "$OLD_G6" && ls -la && sha256sum * ) > "$REC/OLD_G6_OUT_fafd4309_AFTER.txt" 2>&1
cmp -s "$REC/G6_ACCEPTED_NAMESPACE_BEFORE.txt" "$REC/G6_ACCEPTED_NAMESPACE_AFTER.txt" \
  && echo "accepted_G6_OUT_ff4a21f9_unchanged=true" >> "$REC/RUN_RECORD.txt" || echo "accepted_G6_OUT_ff4a21f9_unchanged=FALSE" >> "$REC/RUN_RECORD.txt"
cmp -s "$REC/OLD_G6_OUT_fafd4309_BEFORE.txt" "$REC/OLD_G6_OUT_fafd4309_AFTER.txt" \
  && echo "old_G6_OUT_fafd4309_unchanged=true" >> "$REC/RUN_RECORD.txt" || echo "old_G6_OUT_fafd4309_unchanged=FALSE" >> "$REC/RUN_RECORD.txt"

# read-only post-run record (never mutates the namespace); G7 exit codes: 0 PASS, 3 NOT_ESTIMABLE, 2 mismatch/stop,
# 1 uncaught exception (before or after the marker: POSTRUN marker_exists tells which). Do not interrupt the run.
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
print("verified_physical_h5ad_count", len(r.get("verified_physical_h5ad_sha256", {})))
print("per_matrix_with_overlap", sum(1 for m in r.get("per_matrix", []) if m.get("overlap_cells")))
PY

echo "G7 exit code $RC. STOP: no TD56/57B/57C/59, TD60, selection, Stage4 or training. Evidence in $REC/"
exit $RC
