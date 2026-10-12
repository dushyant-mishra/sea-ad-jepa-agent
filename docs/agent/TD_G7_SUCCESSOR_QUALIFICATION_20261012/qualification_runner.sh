#!/usr/bin/env bash
# Canonical qualification of the TD G7 successor: G6 historical-row binding plus the accepted-G6 predecessor bridge.
# It runs in a fresh, clean, detached worktree at the exact implementation head and writes every log to $1, outside
# that worktree. It never edits the qualification worktree. On any failure it preserves the output and stops.
# It never runs G7, never creates a G7 start marker, receipt or output, never creates owner, runtime or G7 authority,
# and never opens an H5AD file or the S174 count cache.
set -u
# usage: qualification_runner.sh <out dir> <qualification worktree> <expected implementation head>
OUT=$1
Q=$2
EXPECT=$3
BASE=ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0       # accepted G6 producer; successor branch point
RED=9a87cc8efe54e471ded3ee711972ef494e242e01        # RED commit: new tests, G7 still f8e52710
PY=C:/Users/dushy/anaconda3/python.exe
RUN=/d/jepa_td_real_g6_20261011
P=$RUN/pr259_authority_g7_ff4a21f9
G6NS=$RUN/G6_OUT_ff4a21f9
OLD_G6NS=$RUN/G6_OUT_fafd4309
FREEZE="D:/Jepa project/exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv"
PROVENANCE="D:/Jepa project/results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz"
COLLISION="D:/Jepa project-stage81a3r-20260814/results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz"
FX=tests/v5/fixtures/td_g7_successor
NEW=tests/v5/test_td_g7_successor_global_row_and_g6_bridge.py
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
tests/v5/test_td_g7_g6_artifact_semantics.py
$NEW"
GLOBAL_ROW_TESTS="$NEW::test_g7_binds_global_row_from_freeze_file_position_before_filtering
$NEW::test_g7_and_accepted_g6_selectors_agree_on_historical_rows
$NEW::test_g7_refuses_a_freeze_missing_required_columns
$NEW::test_g7_validates_an_explicit_global_row_like_g6"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT"
cd "$Q" || { echo "STOP: no qualification worktree" > "$OUT/QUAL_STOP.txt"; exit 1; }

head=$(git rev-parse HEAD)
{
  echo "utc_start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "qualification_worktree=$Q"
  echo "initial_exact_head=$head"
  echo "expected_implementation_head=$EXPECT"
  echo "accepted_g6_producer_and_branch_point=$BASE"
  echo "red_commit=$RED"
  echo "tracked_status_before=[$(git status --short --untracked-files=no)]"
  echo "untracked_before=[$(git status --short | grep '^??' | tr '\n' ' ')]"
  "$PY" -c "import sys,numpy,pandas,scipy,h5py,pytest;print('python', sys.version.split()[0]);print('numpy', numpy.__version__);print('pandas', pandas.__version__);print('scipy', scipy.__version__);print('h5py', h5py.__version__);print('pytest', pytest.__version__)"
  echo "python_executable=$("$PY" -c 'import sys;print(sys.executable)')"
} > "$OUT/QUAL_00_environment.txt" 2>&1
if [ "$head" != "$EXPECT" ] || [ -n "$(git status --short --untracked-files=no)" ]; then
  echo "STOP: qualification worktree is not the clean expected head" >> "$OUT/QUAL_00_environment.txt"; exit 1
fi
( cd "$G6NS" && ls -la && sha256sum * ) > "$OUT/ACCEPTED_G6_NAMESPACE_BEFORE.txt" 2>&1

# 1. complete focused suite: every existing G6/G7 test plus the successor tests
"$PY" -m pytest -q -p no:cacheprovider -rA $FOCUSED > "$OUT/QUAL_01_full_focused_suite.txt" 2>&1
rc1=$?
echo "# exit=$rc1" >> "$OUT/QUAL_01_full_focused_suite.txt"

# 2. G7 global-row regression, RED -> GREEN. RED: the same four tests from an archive of the RED commit (old G7);
#    they must fail. GREEN: the same four tests at the qualified head; they must pass.
RED_TREE="$OUT/_red_tree_tmp"
rm -rf "$RED_TREE"; mkdir -p "$RED_TREE"
{
  echo "# RED: git archive $RED scripts/v5 tests/v5; G7 canonical SHA in the RED tree:"
  git archive "$RED" scripts/v5 tests/v5 | tar -x -C "$RED_TREE"
  "$PY" -c "import importlib.util,sys;s=importlib.util.spec_from_file_location('c',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(m.canonical_text_sha256(sys.argv[2]))" \
    "$RED_TREE/scripts/v5/td_relational_value_read_v2_common.py" "$RED_TREE/scripts/v5/audit_td_relational_g7_s174_overlap_v2.py"
  ( cd "$RED_TREE" && "$PY" -m pytest -q -p no:cacheprovider -rA $GLOBAL_ROW_TESTS )
  echo "# red_exit=$?"
} > "$OUT/QUAL_02a_global_row_RED_at_red_commit.txt" 2>&1
rm -rf "$RED_TREE"
red_failed=$(grep -cE "^FAILED tests/v5/test_td_g7_successor_global_row_and_g6_bridge.py::" "$OUT/QUAL_02a_global_row_RED_at_red_commit.txt")
"$PY" -m pytest -q -p no:cacheprovider -rA $GLOBAL_ROW_TESTS > "$OUT/QUAL_02b_global_row_GREEN_at_head.txt" 2>&1
rc2=$?
echo "# exit=$rc2" >> "$OUT/QUAL_02b_global_row_GREEN_at_head.txt"
rc_red=$(( red_failed == 4 ? 0 : 1 ))
echo "# red_failed_tests=$red_failed (required 4)" >> "$OUT/QUAL_02a_global_row_RED_at_red_commit.txt"

# 3. predecessor bridge and authority-separation tests (the complete successor test file)
"$PY" -m pytest -q -p no:cacheprovider -rA "$NEW" > "$OUT/QUAL_03_successor_bridge_and_authority_tests.txt" 2>&1
rc3=$?
echo "# exit=$rc3" >> "$OUT/QUAL_03_successor_bridge_and_authority_tests.txt"

# 4. real-file G7 pre-marker gate: G7's own selector, load_inputs, producer continuity and accepted-G6 bridge on the
#    authenticated real inputs; read-only negative probes. No G7 marker, receipt or output; no H5AD.
{
  echo "# command: $PY scripts/v5/qualify_td_g7_real_sample_a_premarker.py (real pinned inputs)"
  sha256sum "$FREEZE" "$P/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv" "$PROVENANCE" "$COLLISION" "$P/S174_REBUILD_FREEZE_V1.json" \
    "$G6NS/G6_RECEIPT.json" "$FX/TD_G6_EXTERNAL_ACCEPTANCE_ff4a21f9_20261011.json" "$P/PREFLIGHT_RESULT.json" \
    "$P/TD_RELATIONAL_MAPPING_PREFLIGHT.json" "$FX/TD_G6G7_OWNER_DECISION_ff4a21f9.json" \
    "$FX/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json" "$OLD_G6NS/G6_EXECUTION_START.json"
} > "$OUT/QUAL_04_real_g7_premarker_gate_inputs.txt" 2>&1
"$PY" scripts/v5/qualify_td_g7_real_sample_a_premarker.py \
  --sample-freeze "$FREEZE" --replay-manifest "$P/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv" \
  --provenance "$PROVENANCE" --collision-ledger "$COLLISION" --macha-freeze "$P/S174_REBUILD_FREEZE_V1.json" \
  --g6-receipt "$G6NS/G6_RECEIPT.json" --g6-acceptance "$FX/TD_G6_EXTERNAL_ACCEPTANCE_ff4a21f9_20261011.json" \
  --preflight-result "$P/PREFLIGHT_RESULT.json" --mapping-receipt "$P/TD_RELATIONAL_MAPPING_PREFLIGHT.json" \
  --old-owner-decision "$FX/TD_G6G7_OWNER_DECISION_ff4a21f9.json" \
  --old-runtime-authorization "$FX/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json" \
  --old-g6-namespace "$OLD_G6NS" > "$OUT/QUAL_04_real_g7_premarker_gate.json" 2> "$OUT/QUAL_04_real_g7_premarker_gate.stderr.txt"
rc4=$?
echo "# exit=$rc4" >> "$OUT/QUAL_04_real_g7_premarker_gate.stderr.txt"

# 5. exact required PR #259 compatibility command against the immutable PR #259 blobs materialized for the G7 run
{
  echo "# command: python -m pytest -q tests/v5/test_td_relational_pr259_real_receipt_compat.py -rs"
  echo "# TD_PR259_PREFLIGHT_RESULT=$P/PREFLIGHT_RESULT.json"
  echo "# TD_PR259_MAPPING_RECEIPT=$P/TD_RELATIONAL_MAPPING_PREFLIGHT.json"
  sha256sum "$P/PREFLIGHT_RESULT.json" "$P/TD_RELATIONAL_MAPPING_PREFLIGHT.json" "$P/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv"
} > "$OUT/QUAL_05_real_pr259_compat.txt" 2>&1
TD_PR259_PREFLIGHT_RESULT="$P/PREFLIGHT_RESULT.json" TD_PR259_MAPPING_RECEIPT="$P/TD_RELATIONAL_MAPPING_PREFLIGHT.json" \
  "$PY" -m pytest -q -p no:cacheprovider tests/v5/test_td_relational_pr259_real_receipt_compat.py -rs >> "$OUT/QUAL_05_real_pr259_compat.txt" 2>&1
rc5=$?
echo "# exit=$rc5" >> "$OUT/QUAL_05_real_pr259_compat.txt"

# 6. changed-file inventory and exact hashes
{
  echo "# git diff --name-status $BASE $head"
  git diff --name-status "$BASE" "$head"
  git diff --stat "$BASE" "$head" | tail -1
  echo "# raw SHA-256, LF-canonical SHA-256 and git-blob SHA-256 of production scripts"
  "$PY" - <<'PY'
import hashlib, subprocess
for p in ("scripts/v5/td_relational_value_read_v2_common.py", "scripts/v5/materialize_td_relational_corrected_sampleA_v2.py",
          "scripts/v5/audit_td_relational_g7_s174_overlap_v2.py", "scripts/v5/qualify_td_g7_real_sample_a_premarker.py"):
    raw = open(p, "rb").read()
    blob = subprocess.check_output(["git", "show", f"HEAD:{p}"])
    canonical = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    print(p, "raw", hashlib.sha256(raw).hexdigest(), "canonical", hashlib.sha256(canonical).hexdigest(),
          "git_blob_sha256", hashlib.sha256(blob).hexdigest())
PY
  echo "# SHA-256 of every changed test and fixture file at $head"
  git diff --name-only "$BASE" "$head" -- tests | while read -r f; do sha256sum "$f"; done
} > "$OUT/QUAL_06_changed_files_and_hashes.txt" 2>&1

# 7. no G7 execution, no G7 output, no new authority
{
  echo "# accepted G6 namespace after (must equal before)"
  ( cd "$G6NS" && ls -la && sha256sum * )
  echo "# G7 output directories under $RUN (expected: none)"
  ls -d "$RUN"/G7_OUT* 2>/dev/null || echo "none"
  echo "# tracked G6/G7 output files (expected: none)"
  git ls-files | grep -E "G6_EXECUTION_START|G6_RECEIPT|G7_RECEIPT|TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2|STARTED_NOT_A_PASS" || echo "none"
  echo "# custody/owner-decision files changed since $BASE (expected: none)"
  git diff --name-only "$BASE" "$head" -- custody || true
  echo "# end"
} > "$OUT/QUAL_07_no_execution_no_authority.txt" 2>&1
( cd "$G6NS" && ls -la && sha256sum * ) > "$OUT/ACCEPTED_G6_NAMESPACE_AFTER.txt" 2>&1
cmp -s "$OUT/ACCEPTED_G6_NAMESPACE_BEFORE.txt" "$OUT/ACCEPTED_G6_NAMESPACE_AFTER.txt"
rc_ns=$?
[ -z "$(ls -d "$RUN"/G7_OUT* 2>/dev/null)" ]
rc_g7out=$?

{
  echo "final_exact_head=$(git rev-parse HEAD)"
  echo "tracked_status_after=[$(git status --short --untracked-files=no)]"
  echo "untracked_after=[$(git status --short | grep '^??' | tr '\n' ' ')]"
  echo "focused_suite_counts=[$(grep -E '(passed|failed|skipped|error)' "$OUT/QUAL_01_full_focused_suite.txt" | grep -v '^#' | tail -1)]"
  echo "global_row_red_failed=$red_failed (required 4)"
  echo "global_row_green_counts=[$(grep -E '(passed|failed|error)' "$OUT/QUAL_02b_global_row_GREEN_at_head.txt" | grep -v '^#' | tail -1)]"
  echo "successor_test_file_counts=[$(grep -E '(passed|failed|error)' "$OUT/QUAL_03_successor_bridge_and_authority_tests.txt" | grep -v '^#' | tail -1)]"
  echo "real_g7_premarker_gate_terminal=[$(grep -o '"terminal": "[^"]*"' "$OUT/QUAL_04_real_g7_premarker_gate.json")]"
  echo "real_pr259_compat_counts=[$(grep -E '(passed|failed|skipped|error)' "$OUT/QUAL_05_real_pr259_compat.txt" | grep -v '^#' | tail -1)]"
  echo "exits: focused=$rc1 red_rule=$rc_red green=$rc2 successor_file=$rc3 real_gate=$rc4 pr259=$rc5 g6_namespace_unchanged=$rc_ns no_g7_output=$rc_g7out"
  echo "utc_end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/QUAL_08_final_state.txt" 2>&1
exit $(( rc1 != 0 || rc_red != 0 || rc2 != 0 || rc3 != 0 || rc4 != 0 || rc5 != 0 || rc_ns != 0 || rc_g7out != 0 ))
