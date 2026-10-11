#!/usr/bin/env bash
# Canonical qualification of the TD G6/G7 full custody successor.
# Runs in a fresh, clean, detached worktree at the exact implementation head and writes every log to $1, outside
# that worktree. It never edits the qualification worktree. On any failure it preserves the output and stops.
# No real owner decision, no runtime authorization, no G6/G7 execution, no expression or count array is read.
set -u
# usage: qualification_runner.sh <out dir> <qualification worktree> <expected implementation head> [prior candidate]
OUT=$1
Q=$2
EXPECT=$3
PRIOR=${4:-}
BASE=d8fa3024e06e265b77353c8382453e7ccbf2350f
PR259=/d/jepa_td_real_g6_20261011/pr259_authority
REAL_SAMPLE_FREEZE="/d/Jepa project/exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv"
FOCUSED="tests/v5/test_td_relational_value_read_v2_common.py
tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py
tests/v5/test_audit_td_relational_g7_s174_overlap_v2.py
tests/v5/test_td_g7_counterpart_attempt_custody.py
tests/v5/test_td_g6g7_owner_decision_binding.py
tests/v5/test_td_g6g7_pr259_physical_pins.py
tests/v5/test_td_v2_strict_raw_count_semantics.py
tests/v5/test_td_v2_sample_a_row_order.py
tests/v5/test_td_g6_synthetic_end_to_end.py
tests/v5/test_td_g6_global_row_binding.py
tests/v5/test_td_g7_g6_prerequisite.py
tests/v5/test_td_g7_synthetic_end_to_end.py
tests/v5/test_td_g7_g6_artifact_semantics.py"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT"
cd "$Q" || { echo "STOP: no qualification worktree" > "$OUT/QUAL_STOP.txt"; exit 1; }

head=$(git rev-parse HEAD)
{
  echo "utc_start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "qualification_worktree=$Q"
  echo "initial_exact_head=$head"
  echo "expected_implementation_head=$EXPECT"
  echo "inherited_base=$BASE"
  echo "prior_qualified_candidate=${PRIOR:-none}"
  echo "tracked_status_before=[$(git status --short --untracked-files=no)]"
  echo "untracked_before=[$(git status --short | grep '^??' | tr '\n' ' ')]"
  python -c "import sys,numpy,pandas,scipy,h5py,pytest;print('python', sys.version.split()[0]);print('numpy', numpy.__version__);print('pandas', pandas.__version__);print('scipy', scipy.__version__);print('h5py', h5py.__version__);print('pytest', pytest.__version__)"
  echo "python_executable=$(python -c 'import sys;print(sys.executable)')"
} > "$OUT/QUAL_00_environment.txt" 2>&1
if [ "$head" != "$EXPECT" ] || [ -n "$(git status --short --untracked-files=no)" ]; then
  echo "STOP: qualification worktree is not the clean expected head" >> "$OUT/QUAL_00_environment.txt"; exit 1
fi

# 1. complete focused suite (every repair, preservation and synthetic end-to-end test)
python -m pytest -q -p no:cacheprovider -rA $FOCUSED > "$OUT/QUAL_01_full_focused_suite.txt" 2>&1
rc1=$?
echo "# exit=$rc1" >> "$OUT/QUAL_01_full_focused_suite.txt"

# 2. exact production metadata-schema compatibility: real authenticated Sample-A freeze, no value read.
{
  echo "# exact real Sample-A freeze compatibility"
  echo "# path=$REAL_SAMPLE_FREEZE"
  sha256sum "$REAL_SAMPLE_FREEZE"
  python - "$REAL_SAMPLE_FREEZE" <<'PY'
import hashlib, importlib.util, sys
from pathlib import Path
import pandas as pd

path = Path(sys.argv[1])
expected_sha = "79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6"
actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
if actual_sha != expected_sha:
    raise SystemExit(f"sample freeze SHA mismatch: {actual_sha} != {expected_sha}")
frame = pd.read_csv(path, dtype=str)
if "global_row" in frame.columns:
    raise SystemExit("unexpected physical global_row column in authenticated production freeze")
required = {"sample", "sample_row", "source", "matrix_id", "operator_index", "local_row", "donor_id", "cell_id"}
missing = sorted(required - set(frame.columns))
if missing:
    raise SystemExit(f"authenticated production freeze missing G6 source columns: {missing}")

g6_path = Path("scripts/v5/materialize_td_relational_corrected_sampleA_v2.py").resolve()
spec = importlib.util.spec_from_file_location("td_g6_real_schema_qualification", g6_path)
g6 = importlib.util.module_from_spec(spec); spec.loader.exec_module(g6)
sample_a = g6.select_sample_a(frame, enforce_geometry=True)
rows = sample_a["global_row"].astype(int).tolist()
if rows != list(range(25_000)):
    raise SystemExit("derived Sample-A global_row is not exactly 0..24999")
print("PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING")
print("rows", len(sample_a), "source_counts", sample_a.source.value_counts().to_dict())
PY
} > "$OUT/QUAL_02_real_sample_freeze_schema.txt" 2>&1
rc_schema=$?
echo "# exit=$rc_schema" >> "$OUT/QUAL_02_real_sample_freeze_schema.txt"

# 3. exact required compatibility command against the immutable PR #259 blobs materialized for the first run.
{
  echo "# command: python -m pytest -q tests/v5/test_td_relational_pr259_real_receipt_compat.py -rs"
  echo "# TD_PR259_PREFLIGHT_RESULT=$PR259/PREFLIGHT_RESULT.json"
  echo "# TD_PR259_MAPPING_RECEIPT=$PR259/TD_RELATIONAL_MAPPING_PREFLIGHT.json"
  sha256sum "$PR259/PREFLIGHT_RESULT.json" "$PR259/TD_RELATIONAL_MAPPING_PREFLIGHT.json" "$PR259/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv"
} > "$OUT/QUAL_03_real_pr259_compat.txt" 2>&1
TD_PR259_PREFLIGHT_RESULT="$PR259/PREFLIGHT_RESULT.json" TD_PR259_MAPPING_RECEIPT="$PR259/TD_RELATIONAL_MAPPING_PREFLIGHT.json" \
  python -m pytest -q tests/v5/test_td_relational_pr259_real_receipt_compat.py -rs >> "$OUT/QUAL_03_real_pr259_compat.txt" 2>&1
rc2=$?
echo "# exit=$rc2" >> "$OUT/QUAL_03_real_pr259_compat.txt"
python - "$PR259/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv" >> "$OUT/QUAL_03_real_pr259_compat.txt" 2>&1 <<'PY'
import hashlib, importlib.util, sys
spec = importlib.util.spec_from_file_location("c", "scripts/v5/td_relational_value_read_v2_common.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
actual = hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()
print("# replay manifest pin check:", "MATCH" if actual == m.EXPECTED_INPUT_HASHES["replay_manifest_sha256"] else "MISMATCH", actual)
PY

# 4. changed-file inventory and exact hashes.
{
  echo "# git diff --name-status $BASE $head"
  git diff --name-status "$BASE" "$head"
  echo "# git diff --stat"
  git diff --stat "$BASE" "$head" | tail -1
  if [ -n "$PRIOR" ]; then
    echo "# git diff --name-status $PRIOR $head (from the prior qualified implementation candidate)"
    git diff --name-status "$PRIOR" "$head"
    git diff --stat "$PRIOR" "$head" | tail -1
  fi
  echo "# raw SHA-256 and LF-canonical SHA-256 of production scripts"
  python - <<'PY'
import hashlib, subprocess
for p in ("scripts/v5/td_relational_value_read_v2_common.py", "scripts/v5/materialize_td_relational_corrected_sampleA_v2.py",
          "scripts/v5/audit_td_relational_g7_s174_overlap_v2.py"):
    raw = open(p, "rb").read()
    blob = subprocess.check_output(["git", "show", f"HEAD:{p}"])
    canonical = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    print(p, "raw", hashlib.sha256(raw).hexdigest(), "canonical", hashlib.sha256(canonical).hexdigest(),
          "git_blob_sha256", hashlib.sha256(blob).hexdigest())
PY
  echo "# SHA-256 of every changed test file at $head"
  git diff --name-only "$BASE" "$head" -- tests | while read -r f; do sha256sum "$f"; done
} > "$OUT/QUAL_04_changed_files_and_hashes.txt" 2>&1

# 5. no successor authority or replacement G6 output exists in the qualified tree.
{
  echo "# tracked G6/G7 V2 output files (expected: none)"
  git ls-files | grep -E "G6_EXECUTION_START|G6_RECEIPT|TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2|STARTED_NOT_A_PASS" || echo "none"
  echo "# old fafd4309 authority records remain historical and are not successor authority"
  git ls-files custody/owner_decisions/20261011/TD_G6G7_OWNER_DECISION_fafd4309.json custody/owner_decisions/20261011/TD_G6G7_RUNTIME_AUTHORIZATION_fafd4309.json
} > "$OUT/QUAL_05_no_successor_authority_or_execution.txt" 2>&1

{
  echo "final_exact_head=$(git rev-parse HEAD)"
  echo "tracked_status_after=[$(git status --short --untracked-files=no)]"
  echo "untracked_after=[$(git status --short | grep '^??' | tr '\n' ' ')]"
  echo "focused_suite_counts=[$(grep -E '(passed|failed|skipped|error)' "$OUT/QUAL_01_full_focused_suite.txt" | grep -v '^#' | tail -1)]"
  echo "real_sample_freeze_schema_exit=$rc_schema"
  echo "real_pr259_compat_counts=[$(grep -E '(passed|failed|skipped|error)' "$OUT/QUAL_03_real_pr259_compat.txt" | grep -v '^#' | tail -1)]"
  echo "focused_suite_exit=$rc1"
  echo "real_pr259_compat_exit=$rc2"
  echo "utc_end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/QUAL_06_final_state.txt" 2>&1
exit $(( rc1 != 0 || rc_schema != 0 || rc2 != 0 ))
