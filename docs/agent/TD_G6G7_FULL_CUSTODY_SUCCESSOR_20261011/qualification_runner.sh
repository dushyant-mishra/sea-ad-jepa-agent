#!/usr/bin/env bash
# Canonical qualification of the TD G6/G7 full custody successor.
# Runs in a fresh, clean, detached worktree at the exact implementation head and writes every log to $1, outside
# that worktree. It never edits the qualification worktree. On any failure it preserves the output and stops.
# No real owner decision, no runtime authorization, no G6/G7 execution, no expression or count array is read: the
# only real files read are the three PR #259 value-blind receipts/manifest (JSON/CSV metadata).
set -u
Q=/d/jepa_wt_td_g6g7_qual_20261011
OUT=$1
EXPECT=43cac77da52446f6391874eb8f5be7ce3ed4e0f7
BASE=d8fa3024e06e265b77353c8382453e7ccbf2350f
PR259=/d/jepa_wt_td_g4g5_v4_20261010/results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split
FOCUSED="tests/v5/test_td_relational_value_read_v2_common.py
tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py
tests/v5/test_audit_td_relational_g7_s174_overlap_v2.py
tests/v5/test_td_g7_counterpart_attempt_custody.py
tests/v5/test_td_g6g7_owner_decision_binding.py
tests/v5/test_td_g6g7_pr259_physical_pins.py
tests/v5/test_td_v2_strict_raw_count_semantics.py
tests/v5/test_td_v2_sample_a_row_order.py
tests/v5/test_td_g6_synthetic_end_to_end.py
tests/v5/test_td_g7_g6_prerequisite.py
tests/v5/test_td_g7_synthetic_end_to_end.py"
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

# 2. the exact required compatibility command against the ORIGINAL physical PR #259 files (a skip is not a PASS)
{
  echo "# command: python -m pytest -q tests/v5/test_td_relational_pr259_real_receipt_compat.py -rs"
  echo "# TD_PR259_PREFLIGHT_RESULT=$PR259/PREFLIGHT_RESULT.json"
  echo "# TD_PR259_MAPPING_RECEIPT=$PR259/TD_RELATIONAL_MAPPING_PREFLIGHT.json"
  echo "# provenance of the files: PR #259 PASS record commit a075b472 in /d/jepa_wt_td_g4g5_v4_20261010"
  sha256sum "$PR259/PREFLIGHT_RESULT.json" "$PR259/TD_RELATIONAL_MAPPING_PREFLIGHT.json" "$PR259/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv"
  echo "# git: $(git -C /d/jepa_wt_td_g4g5_v4_20261010 status --short -- results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split | tr '\n' ' ')(empty = files identical to commit)"
} > "$OUT/QUAL_02_real_pr259_compat.txt" 2>&1
TD_PR259_PREFLIGHT_RESULT="$PR259/PREFLIGHT_RESULT.json" TD_PR259_MAPPING_RECEIPT="$PR259/TD_RELATIONAL_MAPPING_PREFLIGHT.json" \
  python -m pytest -q tests/v5/test_td_relational_pr259_real_receipt_compat.py -rs >> "$OUT/QUAL_02_real_pr259_compat.txt" 2>&1
rc2=$?
echo "# exit=$rc2" >> "$OUT/QUAL_02_real_pr259_compat.txt"
python - "$PR259/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv" >> "$OUT/QUAL_02_real_pr259_compat.txt" 2>&1 <<'PY'
import hashlib, importlib.util, sys
spec = importlib.util.spec_from_file_location("c", "scripts/v5/td_relational_value_read_v2_common.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
actual = hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()
print("# replay manifest pin check:", "MATCH" if actual == m.EXPECTED_INPUT_HASHES["replay_manifest_sha256"] else "MISMATCH", actual)
PY

# 3. changed-file inventory from the inherited PR #268 head, and exact final SHA-256 of every changed file
{
  echo "# git diff --name-status $BASE $head"
  git diff --name-status "$BASE" "$head"
  echo "# git diff --stat"
  git diff --stat "$BASE" "$head" | tail -1
  echo "# raw SHA-256 (bytes at $head) and LF-canonical SHA-256 (as bound by code_identity) of the production scripts"
  python - <<'PY'
import hashlib, subprocess
for p in ("scripts/v5/td_relational_value_read_v2_common.py", "scripts/v5/materialize_td_relational_corrected_sampleA_v2.py",
          "scripts/v5/audit_td_relational_g7_s174_overlap_v2.py"):
    raw = open(p, "rb").read()
    blob = subprocess.check_output(["git", "show", f"HEAD:{p}"])
    print(p, "raw", hashlib.sha256(raw).hexdigest(), "canonical", hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
          "git_blob_sha256", hashlib.sha256(blob).hexdigest())
PY
  echo "# SHA-256 of every changed test file at $head"
  git diff --name-only "$BASE" "$head" -- tests | while read -r f; do sha256sum "$f"; done
} > "$OUT/QUAL_03_changed_files_and_hashes.txt" 2>&1

# 4. no real owner decision, runtime authorization or G6/G7 output exists in the qualified tree
{
  echo "# files mentioning the owner-decision schema (expected: code and tests only)"
  git grep -l "JEPA_TD_RELATIONAL_G6_G7_OWNER_DECISION_V1" "$head" -- . | sed "s/^$head://"
  echo "# files mentioning the V2 runtime-authorization schema (expected: code, tests, template docs only)"
  git grep -l "JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2" "$head" -- . | sed "s/^$head://"
  echo "# tracked G6/G7 V2 output files (expected: none)"
  git ls-files | grep -E "G6_EXECUTION_START|G6_RECEIPT|TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2|STARTED_NOT_A_PASS" || echo "none"
} > "$OUT/QUAL_04_no_real_authority_or_execution.txt" 2>&1

{
  echo "final_exact_head=$(git rev-parse HEAD)"
  echo "tracked_status_after=[$(git status --short --untracked-files=no)]"
  echo "untracked_after=[$(git status --short | grep '^??' | tr '\n' ' ')]"
  echo "focused_suite_exit=$rc1"
  echo "real_pr259_compat_exit=$rc2"
  echo "utc_end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/QUAL_05_final_state.txt" 2>&1
exit $(( rc1 != 0 || rc2 != 0 ))
