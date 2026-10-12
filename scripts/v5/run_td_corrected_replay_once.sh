#!/usr/bin/env bash
# Corrected TD56 -> TD57B -> TD57C -> TD59 replay launcher. It is fail-closed and runs at most one attempt.
#
# usage: run_td_corrected_replay_once.sh QUALIFY <authority commit> <operational SHA-256> [<ratification commit> <ratification SHA-256>]
#        run_td_corrected_replay_once.sh EXECUTE_ONCE <authority commit> <operational SHA-256> \
#             <launch-acceptance commit> <launch-acceptance SHA-256> <ratification commit> <ratification SHA-256>
#
# Run it from Git Bash on Windows, from a clean checkout of <authority commit>. That commit holds the replay
# package code, the frozen contract and the fresh replay-only authority records. Custody and git checks run here.
# Every Python step runs inside WSL in the pinned historical-numerics environment, because the executors are
# byte-exact on Linux with it.
#
# QUALIFY runs these checks, then stops before the start marker:
#   - contract, predecessors, executors, structural estimability, owner ratification and authority;
#   - no corrected value is opened and no replay kernel runs;
#   - nothing is written to the replay namespace.
# EXECUTE_ONCE additionally requires the committed external launch-audit acceptance and the ratification. It then
# runs the orchestrator once and validates the evidence. The orchestrator repeats the pure checks, reads the detected
# field from the parsed ratification, and checks the support bundle before it writes the attempt ledger and marker.
# One attempt only: the attempt ledger, any earlier EXECUTE_ONCE run record and the namespace each refuse another.
# No path here invokes G6, G7, a target tournament, TD60, Stage 4 or training.
#
# Exit codes:
#   - 64: launcher STOP before any marker;
#   - 3: QUALIFY passed except pending owner ratification;
#   - otherwise the step's own code.
set -u
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'  # never let Git Bash rewrite /mnt/... arguments to wsl.exe
STOP_CODE=64
MODE=${1:-}
AUTH_COMMIT=${2:-}
EXPECTED_OP_SHA=${3:-}
REPO="D:/Jepa project"
NAMESPACE=D:/jepa_td_corrected_replay_20261012/REPLAY_OUT_V1
RUNBASE=D:/jepa_td_corrected_replay_20261012
G6NS=D:/jepa_td_real_g6_20261011/G6_OUT_ff4a21f9
G7NS=D:/jepa_td_real_g6_20261011/G7_OUT_8d41fb98
ARCHIVE="D:/Jepa project/JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip"
SUPPORT_BUNDLE="D:/Jepa project/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip"
FREEZE="D:/Jepa project/exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv"
WSL_PY=/home/dushyant_mishra/miniconda3/envs/td-replay-hist/bin/python
PY_VERSIONS="python=3.13.5 numpy=2.3.5 scipy=1.17.0 pandas=2.2.3"
AUTH_DIR=custody/owner_decisions/20261012
OWNER_REL=$AUTH_DIR/TD_CORRECTED_REPLAY_OWNER_DECISION_V1.json
RUNTIME_REL=$AUTH_DIR/TD_CORRECTED_REPLAY_RUNTIME_AUTHORIZATION_V1.json
OP_REL=$AUTH_DIR/TD_CORRECTED_REPLAY_OPERATIONAL_AUTHORIZATION_V1.json
ACC_REL=$AUTH_DIR/TD_CORRECTED_REPLAY_LAUNCH_AUDIT_ACCEPTANCE_V1.json
RAT_REL=$AUTH_DIR/TD_CORRECTED_REPLAY_DECISION_RATIFICATION_V1.json
EQUIV_REL=custody/target_discovery/corrected_replay_20261012/TD_CORRECTED_REPLAY_EQUIVALENCE_RECEIPT_V1.json
ENV_LOCK_REL=target_discovery/iterations/corrected_replay_20261012/TD_REPLAY_ENV_WSL_PIP_FREEZE.txt
fail() { echo "STOP before any filesystem change: $*"; exit $STOP_CODE; }
wslpath_of() { local p=${1//\\//}; local d=$(echo "${p:0:1}" | tr 'A-Z' 'a-z'); echo "/mnt/$d${p:2}"; }
blob_sha() { git -C "$REPO" cat-file blob "$1:$2" 2>/dev/null | sha256sum | cut -c1-64; }

# 0. pure checks: arguments, launcher checkout, audited SHAs read straight from git objects, fresh namespace, WSL env
case "$MODE" in
  QUALIFY) { [ $# -eq 3 ] || [ $# -eq 5 ]; } || fail "QUALIFY takes <authority commit> <operational SHA> [<ratification commit> <ratification SHA>]"
           RAT_COMMIT=${4:-}; EXPECTED_RAT_SHA=${5:-}; ACC_COMMIT=""; EXPECTED_ACC_SHA="" ;;
  EXECUTE_ONCE) [ $# -eq 7 ] || fail "EXECUTE_ONCE takes <authority commit> <op SHA> <acceptance commit> <acceptance SHA> <ratification commit> <ratification SHA>"
           ACC_COMMIT=$4; EXPECTED_ACC_SHA=$5; RAT_COMMIT=$6; EXPECTED_RAT_SHA=$7 ;;
  *) fail "mode must be QUALIFY or EXECUTE_ONCE" ;;
esac
[[ "$AUTH_COMMIT" =~ ^[0-9a-f]{40}$ && "$EXPECTED_OP_SHA" =~ ^[0-9a-f]{64}$ ]] || fail "bad authority commit/operational SHA"
LAUNCH_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -W 2>/dev/null || pwd)
[ "$(git -C "$LAUNCH_ROOT" rev-parse HEAD)" = "$AUTH_COMMIT" ] || fail "launcher checkout HEAD is not the authority commit"
[ -z "$(git -C "$LAUNCH_ROOT" status --porcelain --ignored)" ] || fail "launcher checkout is not clean (including ignored files)"
[ "$(blob_sha "$AUTH_COMMIT" "$OP_REL")" = "$EXPECTED_OP_SHA" ] || fail "operational authorization at $AUTH_COMMIT is not the audited SHA"
if [ -n "$RAT_COMMIT" ]; then
  [[ "$RAT_COMMIT" =~ ^[0-9a-f]{40}$ && "$EXPECTED_RAT_SHA" =~ ^[0-9a-f]{64}$ ]] || fail "bad ratification commit/SHA"
  [ "$(blob_sha "$RAT_COMMIT" "$RAT_REL")" = "$EXPECTED_RAT_SHA" ] || fail "decision ratification at $RAT_COMMIT is missing or not the given SHA"
fi
if [ "$MODE" = "EXECUTE_ONCE" ]; then
  [[ "$ACC_COMMIT" =~ ^[0-9a-f]{40}$ && "$EXPECTED_ACC_SHA" =~ ^[0-9a-f]{64}$ ]] || fail "bad acceptance commit/SHA"
  [ "$(blob_sha "$ACC_COMMIT" "$ACC_REL")" = "$EXPECTED_ACC_SHA" ] || fail "launch-audit acceptance at $ACC_COMMIT is missing or not the given SHA"
fi
[ -e "$NAMESPACE" ] && fail "replay namespace already exists (attempt spent or occupied): $NAMESPACE"
[ -e "$RUNBASE/TD_CORRECTED_REPLAY_ATTEMPT_LEDGER_V1.json" ] && fail "attempt ledger exists: the one corrected-replay attempt is spent"
for r in "$RUNBASE"/launch_EXECUTE_ONCE_*/record/RUN_RECORD.txt; do
  [ -e "$r" ] && fail "an earlier EXECUTE_ONCE reached the orchestrator ($r): the attempt is spent"
done
[ "$(wsl.exe -e "$WSL_PY" -c "import sys,numpy,scipy,pandas;print('python='+sys.version.split()[0],'numpy='+numpy.__version__,'scipy='+scipy.__version__,'pandas='+pandas.__version__)" 2>/dev/null | tr -d '\r\0')" = "$PY_VERSIONS" ] \
  || fail "WSL replay environment is not the pinned one: $PY_VERSIONS"
[ "$(wsl.exe -e "$WSL_PY" -m pip freeze --all 2>/dev/null | tr -d '\r\0' | sha256sum | cut -c1-64)" = "$(sha256sum "$LAUNCH_ROOT/$ENV_LOCK_REL" | cut -c1-64)" ] \
  || fail "WSL replay environment does not match the committed full pip-freeze lock"

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
RUNROOT=$RUNBASE/launch_${MODE}_$STAMP
[ -e "$RUNROOT" ] && fail "run directory exists: $RUNROOT"
mkdir -p "$RUNROOT/authority" "$RUNROOT/predecessors" "$RUNROOT/record"
REC=$RUNROOT/record
stop() { echo "STOP before any start marker: $*" | tee -a "$REC/PRECONDITION_STOP.txt"; exit $STOP_CODE; }
pin() { [ -f "$1" ] && [ "$(sha256sum "$1" | cut -c1-64)" = "$2" ] || stop "pin mismatch or missing: $1"; echo "MATCH $2 $1" >> "$REC/PRECONDITION_PINS.txt"; }
{ echo "mode=$MODE utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) authority_commit=$AUTH_COMMIT op_sha=$EXPECTED_OP_SHA"
  echo "acceptance=${ACC_COMMIT:-none}:${EXPECTED_ACC_SHA:-none} ratification=${RAT_COMMIT:-none}:${EXPECTED_RAT_SHA:-none}"
  echo "launch_root=$LAUNCH_ROOT namespace=$NAMESPACE runroot=$RUNROOT wsl_python=$WSL_PY versions=[$PY_VERSIONS]"; } > "$REC/LAUNCH_CONTEXT.txt"

# 1. predecessor evidence and authority, materialized from immutable commits and pinned
PRE=$RUNROOT/predecessors; AU=$RUNROOT/authority
git -C "$REPO" cat-file blob 17a68667174ae8583305c546639dced7dded94d9:docs/agent/TD_G6_EXTERNAL_ACCEPTANCE_ff4a21f9_20261011.json > "$PRE/G6_ACCEPTANCE.json" || stop "G6 acceptance"
git -C "$REPO" cat-file blob 0b50938e48f7c257b362a0c66899bc1caa0d27a1:docs/agent/TD_G7_CELL_ID_NAMESPACE_DIAGNOSTIC_20261012/STAGE3_TRANSFORMS.json > "$PRE/DIAG_TRANSFORMS.json" || stop "diagnostic"
git -C "$REPO" cat-file blob 0b50938e48f7c257b362a0c66899bc1caa0d27a1:docs/agent/TD_G7_CELL_ID_NAMESPACE_DIAGNOSTIC_20261012/TD_G7_CELL_ID_NAMESPACE_DIAGNOSTIC_RESULT.md > "$PRE/DIAG_RESULT.md" || stop "diagnostic result"
git -C "$REPO" cat-file blob bffba425ec41c584b01c9a5e71178241ec5ee523:docs/agent/TD_G7_SUCCESSOR_EXECUTION_20261012/SPENT_AUTHORITY_RECORD_8d41fb98.json > "$PRE/G7_SPENT.json" || stop "spent record"
pin "$PRE/G6_ACCEPTANCE.json" 89932183a2c7b56d1e3ae42264ea3f3b3ae9001d865cfa93604b46f0db2129fb
pin "$PRE/DIAG_TRANSFORMS.json" f7378b2a872b558c76bad2b1b7f4c201a3e30c38f4f63e25f73c76826129daca
pin "$PRE/DIAG_RESULT.md" 208684bcca51680a107433cc22764cc2227a847da37a023d632ec1469bd04298
git -C "$REPO" cat-file blob "$AUTH_COMMIT:$OWNER_REL" > "$AU/owner.json" || stop "owner decision"
git -C "$REPO" cat-file blob "$AUTH_COMMIT:$RUNTIME_REL" > "$AU/runtime.json" || stop "runtime authorization"
git -C "$REPO" cat-file blob "$AUTH_COMMIT:$OP_REL" > "$AU/operational.json" || stop "operational authorization"
pin "$AU/operational.json" "$EXPECTED_OP_SHA"
git -C "$REPO" cat-file blob "$AUTH_COMMIT:$EQUIV_REL" > "$PRE/EQUIVALENCE_RECEIPT.json" || stop "equivalence receipt"
RAT_ARG=()
if [ -n "$RAT_COMMIT" ]; then
  git -C "$REPO" cat-file blob "$RAT_COMMIT:$RAT_REL" > "$AU/ratification.json" || stop "ratification"
  pin "$AU/ratification.json" "$EXPECTED_RAT_SHA"; RAT_ARG=(--ratification "$(wslpath_of "$AU/ratification.json")")
fi
ACC_ARGS=()
if [ "$MODE" = "EXECUTE_ONCE" ]; then
  git -C "$REPO" cat-file blob "$ACC_COMMIT:$ACC_REL" > "$AU/acceptance.json" || stop "acceptance"
  pin "$AU/acceptance.json" "$EXPECTED_ACC_SHA"
  ACC_ARGS=(--acceptance "$(wslpath_of "$AU/acceptance.json")" --expected-acceptance-sha256 "$EXPECTED_ACC_SHA")
fi
IMPL=$(sed -n 's/.*"implementation_commit_sha": "\([0-9a-f]\{40\}\)".*/\1/p' "$AU/runtime.json" | head -1)
[[ "$IMPL" =~ ^[0-9a-f]{40}$ ]] || stop "runtime authorization lacks implementation_commit_sha"
git -C "$REPO" merge-base --is-ancestor "$IMPL" "$AUTH_COMMIT" || stop "implementation commit is not an ancestor of the authority commit"
git -C "$LAUNCH_ROOT" diff --quiet "$IMPL" "$AUTH_COMMIT" -- scripts/v5 target_discovery/iterations/corrected_replay_20261012 || stop "replay code differs between the implementation and authority commits"

WL=$(wslpath_of "$LAUNCH_ROOT"); WREC=$(wslpath_of "$REC")
wpy() { wsl.exe -e env PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 "$WSL_PY" "$WL/scripts/v5/$1" "${@:2}"; }

# 2. QUALIFY: contract, predecessors, executors, structural estimability, ratification, namespace freshness
wpy td_corrected_replay_gate_v1.py qualify --archive "$(wslpath_of "$ARCHIVE")" --g6-namespace "$(wslpath_of "$G6NS")" \
  --g6-acceptance "$(wslpath_of "$PRE/G6_ACCEPTANCE.json")" --g7-namespace "$(wslpath_of "$G7NS")" \
  --diagnostic-transforms "$(wslpath_of "$PRE/DIAG_TRANSFORMS.json")" --diagnostic-result "$(wslpath_of "$PRE/DIAG_RESULT.md")" \
  --spent-record "$(wslpath_of "$PRE/G7_SPENT.json")" --sample-freeze "$(wslpath_of "$FREEZE")" \
  --namespace "$(wslpath_of "$NAMESPACE")" --record "$WREC/QUALIFY_RECEIPT.json" \
  --equivalence-receipt "$(wslpath_of "$PRE/EQUIVALENCE_RECEIPT.json")" --implementation-commit "$IMPL" \
  --support-bundle "$(wslpath_of "$SUPPORT_BUNDLE")" "${RAT_ARG[@]}" > "$REC/QUALIFY_STDOUT.txt" 2> "$REC/QUALIFY_STDERR.txt"
QRC=$?
[ $QRC -eq 0 ] || [ $QRC -eq 3 ] || stop "QUALIFY failed (exit $QRC; see QUALIFY_STDERR.txt)"

# 3. replay-only authority (and, in EXECUTE_ONCE, the external launch-audit acceptance)
wpy td_corrected_replay_gate_v1.py authority --owner "$(wslpath_of "$AU/owner.json")" --runtime "$(wslpath_of "$AU/runtime.json")" \
  --operational "$(wslpath_of "$AU/operational.json")" --expected-operational-sha256 "$EXPECTED_OP_SHA" \
  --implementation-commit "$IMPL" --equivalence-receipt "$(wslpath_of "$PRE/EQUIVALENCE_RECEIPT.json")" \
  --record "$WREC/AUTHORITY_CHECK.json" "${ACC_ARGS[@]}" > "$REC/AUTHORITY_STDOUT.txt" 2> "$REC/AUTHORITY_STDERR.txt" \
  || stop "authority check failed (see AUTHORITY_STDERR.txt)"
[ -e "$NAMESPACE" ] && stop "replay namespace appeared during qualification"

if [ "$MODE" = "QUALIFY" ]; then
  echo "QUALIFY_DONE exit=$QRC utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) (0 = PASS; 3 = pending owner ratification). No start marker; no corrected value opened." | tee "$REC/QUALIFY_RESULT.txt"
  exit $QRC
fi

# 4. EXECUTE_ONCE: requires a ratified QUALIFY PASS; the orchestrator creates the start marker before any protected step
[ $QRC -eq 0 ] || stop "EXECUTE_ONCE requires a ratified QUALIFY PASS"
echo "execute_start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$REC/RUN_RECORD.txt"
wpy td_corrected_replay_execute_v1.py --namespace "$(wslpath_of "$NAMESPACE")" --archive "$(wslpath_of "$ARCHIVE")" \
  --support-bundle "$(wslpath_of "$SUPPORT_BUNDLE")" --g6-values "$(wslpath_of "$G6NS/TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz")" \
  --g6-meta "$(wslpath_of "$G6NS/TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz")" --sample-freeze "$(wslpath_of "$FREEZE")" \
  --python "$WSL_PY" --implementation-commit "$IMPL" --qualify-receipt "$WREC/QUALIFY_RECEIPT.json" \
  --authority-check "$WREC/AUTHORITY_CHECK.json" --ratification "$(wslpath_of "$AU/ratification.json")" \
  > "$REC/execute.stdout.txt" 2> "$REC/execute.stderr.txt"
XRC=$?
echo "execute_exit=$XRC execute_end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$REC/RUN_RECORD.txt"
wpy td_corrected_replay_evidence_v1.py --namespace "$(wslpath_of "$NAMESPACE")" --out "$WREC/EVIDENCE_VERDICT.json" \
  --launch-record "$WREC" > "$REC/evidence.stdout.txt" 2> "$REC/evidence.stderr.txt"
echo "evidence_exit=$? utc=$(date -u +%Y-%m-%dT%H:%M:%SZ). STOP for external outcome audit; no rerun or repair." | tee -a "$REC/RUN_RECORD.txt"
exit $XRC
