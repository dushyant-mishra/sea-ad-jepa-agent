#!/usr/bin/env bash
# REAL TD: replacement G6 exactly once at ff4a21f9 under the fresh owner decision + runtime authorization, then STOP.
# NO G7. Any precondition failure stops BEFORE G6_EXECUTION_START.json exists (attempt unspent). Never retries.
# Adapted from the auditor-approved RUN_REAL_G6_ONCE.sh: new commit, new G6 identity, new authority commits, new
# never-used paths. The old G6_OUT_fafd4309 namespace and both qualification records are never touched.
# Run from Git Bash. All paths given to Python are Windows form (D:/...).
set -u
REPO="D:/Jepa project"
EXEC=D:/jepa_wt_td_g6_exec_ff4a21f9
COMMIT=ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0
RUN=D:/jepa_td_real_g6_20261011
AUTH=$RUN/authority_ff4a21f9; REC=$RUN/run_record_ff4a21f9; P=$RUN/pr259_authority_ff4a21f9
OUT=$RUN/G6_OUT_ff4a21f9
OLD_OUT=$RUN/G6_OUT_fafd4309
PY=C:/Users/dushy/anaconda3/python.exe
for d in "$AUTH" "$REC" "$P"; do [ -e "$d" ] && { echo "STOP: path already exists: $d"; exit 1; }; done
mkdir -p "$AUTH" "$REC" "$P"
stop() { echo "STOP before spending G6: $*" | tee -a "$REC/PRECONDITION_STOP.txt"; exit 1; }
pin() { [ -f "$1" ] && [ "$(sha256sum "$1" | cut -c1-64)" = "$2" ] || stop "pin mismatch or missing: $1"; echo "MATCH $2 $1" >> "$REC/PRECONDITION_PINS.txt"; }

# 0. the historical spent namespace is evidence: record it before and after, never touch it
( cd "$OLD_OUT" && ls -la && sha256sum * ) > "$REC/OLD_G6_OUT_fafd4309_BEFORE.txt" 2>&1
pin "$OLD_OUT/G6_EXECUTION_START.json" ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894

# 1-2. fresh clean detached worktree at exactly ff4a21f9; qualified identity via the implementation's own code_identity
[ -e "$EXEC" ] && stop "execution worktree path already exists: $EXEC"
git -C "$REPO" worktree add --detach "$EXEC" "$COMMIT" || stop "worktree creation failed"
[ "$(git -C "$EXEC" rev-parse HEAD)" = "$COMMIT" ] || stop "HEAD is not $COMMIT"
[ -z "$(git -C "$EXEC" status --short)" ] || stop "execution worktree not clean"
"$PY" - "$EXEC" "$COMMIT" <<'PY' || stop "qualified implementation identity mismatch"
import importlib.util, sys
from pathlib import Path

root = Path(sys.argv[1])
want_commit = sys.argv[2]
v5 = root / "scripts" / "v5"

common_path = v5 / "td_relational_value_read_v2_common.py"
spec = importlib.util.spec_from_file_location("td_value_v2_common", common_path)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)

identity = common.code_identity(
    v5 / "materialize_td_relational_corrected_sampleA_v2.py",
    v5 / "audit_td_relational_g7_s174_overlap_v2.py",
)

want = {
    "implementation_commit_sha": want_commit,
    "common_script_sha256": "23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea",
    "g6_script_sha256": "8e6504e02e909a030a33b3fa2b4742fd78354486c1d2a0f40575c11108a6877d",
    "g7_script_sha256": "f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe",
    "common_entrypoint": "scripts/v5/td_relational_value_read_v2_common.py",
    "g6_entrypoint": "scripts/v5/materialize_td_relational_corrected_sampleA_v2.py",
    "g7_entrypoint": "scripts/v5/audit_td_relational_g7_s174_overlap_v2.py",
}
if identity != want:
    raise SystemExit(f"IDENTITY MISMATCH\nactual={identity}\nexpected={want}")
print("qualified implementation identity: MATCH")
PY

# 3-4. fresh owner decision + runtime authorization, byte-exact from their full immutable authority commits
DEC=$AUTH/TD_G6G7_OWNER_DECISION_ff4a21f9.json; AUZ=$AUTH/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json
git -C "$REPO" cat-file blob \
  8283c726390c63b2dc68ed546a3116059aa70d67:custody/owner_decisions/20261011/TD_G6G7_OWNER_DECISION_ff4a21f9.json \
  > "$DEC" || stop "cannot materialize owner decision"
git -C "$REPO" cat-file blob \
  8d5637f7eb26703bcd396135598c8da9e70e8ae8:custody/owner_decisions/20261011/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json \
  > "$AUZ" || stop "cannot materialize runtime authorization"
pin "$DEC" 3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a
pin "$AUZ" 28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7

# 5. PR #259 evidence as exact immutable blobs from its execution head; then every remaining small pin
PR259=80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947
BASE=results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split
git -C "$REPO" cat-file blob "$PR259:$BASE/PREFLIGHT_RESULT.json" \
  > "$P/PREFLIGHT_RESULT.json" || stop "cannot materialize PR259 preflight receipt"
git -C "$REPO" cat-file blob "$PR259:$BASE/TD_RELATIONAL_MAPPING_PREFLIGHT.json" \
  > "$P/TD_RELATIONAL_MAPPING_PREFLIGHT.json" || stop "cannot materialize PR259 mapping receipt"
git -C "$REPO" cat-file blob "$PR259:$BASE/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv" \
  > "$P/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv" || stop "cannot materialize PR259 replay manifest"
git -C "$REPO" cat-file blob "$PR259:$BASE/S174_REBUILD_FREEZE_V1.json" \
  > "$P/S174_REBUILD_FREEZE_V1.json" || stop "cannot materialize PR259 Macha freeze"
pin "$P/PREFLIGHT_RESULT.json" 62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae
pin "$P/TD_RELATIONAL_MAPPING_PREFLIGHT.json" 6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0
pin "$P/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv" 4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660
pin "$P/S174_REBUILD_FREEZE_V1.json" 240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c
pin "D:/Jepa project/exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv" 79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6
pin "D:/Jepa project/results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz" df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51
pin "D:/Jepa project-stage81a3r-20260814/results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz" f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722
pin "D:/Jepa project/JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip" c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417
C=$RUN/historical_csr_50k
pin "$C/data.npy" 0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e
pin "$C/indices.npy" f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771
pin "$C/indptr.npy" 58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1
pin "$C/shape.npy" 5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb

# 6. a new, never-used output namespace (G6 creates it and spends it with its start marker)
[ -e "$OUT" ] && stop "output namespace already exists: $OUT"

# 7-8. run replacement G6 exactly once
CMD=("$PY" "$EXEC/scripts/v5/materialize_td_relational_corrected_sampleA_v2.py"
  --preflight-result "$P/PREFLIGHT_RESULT.json" --mapping-receipt "$P/TD_RELATIONAL_MAPPING_PREFLIGHT.json"
  --value-authorization "$AUZ" --owner-decision "$DEC"
  --replay-manifest "$P/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv"
  --sample-freeze "D:/Jepa project/exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv"
  --provenance "D:/Jepa project/results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz"
  --collision-ledger "D:/Jepa project-stage81a3r-20260814/results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz"
  --macha-freeze "$P/S174_REBUILD_FREEZE_V1.json"
  --td-artifacts-zip "D:/Jepa project/JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip"
  --historical-csr-root "$C"
  --source-root "D:/Jepa project" --output-dir "$OUT")
{ echo "utc_start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "exec_head=$(git -C "$EXEC" rev-parse HEAD) status=[$(git -C "$EXEC" status --short)]"
  "$PY" -c "import sys,numpy,pandas,scipy,h5py;print('python',sys.version.split()[0],'numpy',numpy.__version__,'pandas',pandas.__version__,'scipy',scipy.__version__,'h5py',h5py.__version__)"
  printf 'command:'; printf ' %q' "${CMD[@]}"; echo; } > "$REC/RUN_RECORD.txt" 2>&1
PYTHONDONTWRITEBYTECODE=1 "${CMD[@]}" > "$REC/g6.stdout.txt" 2> "$REC/g6.stderr.txt"
RC=$?
echo "exit_code=$RC utc_end=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$REC/RUN_RECORD.txt"

# 9. preserve and hash the complete namespace, whatever the outcome; re-record the old namespace
( cd "$OUT" 2>/dev/null && sha256sum * ) > "$REC/G6_NAMESPACE_SHA256.txt" 2>&1
ls -la "$OUT" >> "$REC/G6_NAMESPACE_SHA256.txt" 2>&1
echo "exec_status_after=[$(git -C "$EXEC" status --short)] exec_head_after=$(git -C "$EXEC" rev-parse HEAD)" >> "$REC/RUN_RECORD.txt"
( cd "$OLD_OUT" && ls -la && sha256sum * ) > "$REC/OLD_G6_OUT_fafd4309_AFTER.txt" 2>&1
cmp -s "$REC/OLD_G6_OUT_fafd4309_BEFORE.txt" "$REC/OLD_G6_OUT_fafd4309_AFTER.txt" \
  && echo "old_G6_OUT_fafd4309_unchanged=true" >> "$REC/RUN_RECORD.txt" \
  || echo "old_G6_OUT_fafd4309_unchanged=FALSE" >> "$REC/RUN_RECORD.txt"

# 10-13. read-only post-run PASS contract (never mutates the namespace)
if [ "$RC" -eq 0 ]; then
"$PY" - "$OUT" <<'PY'
import hashlib, json, sys
from pathlib import Path

out = Path(sys.argv[1])

expected_files = {
    "G6_EXECUTION_START.json",
    "G6_RECEIPT.json",
    "MANIFEST.json",
    "TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz",
    "TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz",
}

actual_files = {p.name for p in out.iterdir() if p.is_file()}
if actual_files != expected_files:
    raise SystemExit(
        f"G6 SUCCESS NAMESPACE FILE SET MISMATCH\n"
        f"missing={sorted(expected_files-actual_files)}\n"
        f"extra={sorted(actual_files-expected_files)}"
    )

receipt = json.loads((out / "G6_RECEIPT.json").read_text(encoding="utf-8"))
if receipt.get("status") != "PASS_TD_G6_SOURCE_LIBRARY_EXACT":
    raise SystemExit(f"G6 receipt is not exact PASS: {receipt.get('status')!r}")

manifest = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
if manifest.get("status") != "MATERIALIZED_G6_V2_PASS__G7_PENDING":
    raise SystemExit(f"G6 manifest is not exact PASS/PENDING-G7: {manifest.get('status')!r}")

def sha(name):
    h = hashlib.sha256()
    with (out / name).open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()

values = "TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz"
meta = "TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz"

if sha(values) != receipt.get("values_sha256"):
    raise SystemExit("values artifact differs from G6 receipt SHA")
if sha(meta) != receipt.get("meta_sha256"):
    raise SystemExit("metadata artifact differs from G6 receipt SHA")

for key in (
    "biological_replay_authorized",
    "target_selection_authorized",
    "td60_authorized",
    "training_authorized",
):
    if receipt.get(key) is not False:
        raise SystemExit(f"forbidden authority in G6 receipt: {key}={receipt.get(key)!r}")
    if manifest.get(key) is not False:
        raise SystemExit(f"forbidden authority in G6 manifest: {key}={manifest.get(key)!r}")

print("POSTRUN_G6_PASS_CONTRACT: PASS")
PY
POST=$?
echo "postrun_pass_contract_exit=$POST" >> "$REC/RUN_RECORD.txt"
if [ "$POST" -ne 0 ]; then
    echo "POSTRUN G6 CONTRACT AUDIT FAILED; namespace remains spent and preserved." >> "$REC/RUN_RECORD.txt"
    exit "$POST"
fi
fi

# 14. STOP. No G7 until the external auditor has accepted this replacement G6 execution.
echo "G6 exit code $RC. STOP: no G7. Evidence in $REC/"
exit $RC
