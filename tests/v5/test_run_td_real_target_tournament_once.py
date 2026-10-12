from __future__ import annotations
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"/"v5"))
import run_td_real_target_tournament_once as R


def replay(status="FAIL"):
    return {"relational_status":status,"receipt_sha256":"a"*64,"externally_audited":True}

def manifest(ready=False):
    return {"schema":"JEPA_TD_REAL_GATE_EXECUTOR_READINESS_V1","all_required_roles_materialized":ready,"manifest_sha256":"b"*64}

def test_qualify_is_outcome_blind_and_blocks_missing_gate_executors(tmp_path):
    out=R.qualify(replay(),manifest(False),namespace=tmp_path/"out")
    assert out["terminal"]=="BLOCKED_GATE_EXECUTOR_RULES_NOT_MATERIALIZED__NO_OUTCOME_READ"
    assert out["protected_values_read"] is False
    assert not (tmp_path/"out").exists()

def test_qualify_ready_requires_no_execution_authority_and_creates_no_marker(tmp_path):
    out=R.qualify(replay(),manifest(True),namespace=tmp_path/"out")
    assert out["terminal"]=="PASS_TD_REAL_TOURNAMENT_EXECUTOR_QUALIFICATION__NO_REAL_CANDIDATE_RESULTS__EXECUTION_AUTHORITY_REQUIRED"
    assert out["real_tournament_authorized"] is False
    assert not (tmp_path/"out").exists()

def test_qualify_refuses_unaudited_or_invalid_replay(tmp_path):
    bad=replay(); bad["externally_audited"]=False
    with pytest.raises(R.RealTournamentControllerError,match="externally audited"):
        R.qualify(bad,manifest(True),namespace=tmp_path/"out")
    bad=replay("MAYBE")
    with pytest.raises(R.RealTournamentControllerError,match="relational_status"):
        R.qualify(bad,manifest(True),namespace=tmp_path/"out")

def test_execute_once_refuses_without_exact_authority_before_start_marker(tmp_path):
    with pytest.raises(R.RealTournamentControllerError,match="execution authority"):
        R.execute_once(replay(),manifest(True),namespace=tmp_path/"out",authority=None,runner=lambda _: {})
    assert not (tmp_path/"out").exists()

def test_execute_once_marks_namespace_before_runner_and_cannot_reuse(tmp_path):
    ns=tmp_path/"out"; auth={"schema":"JEPA_TD_REAL_TOURNAMENT_EXECUTION_AUTHORITY_V1","real_tournament_authorized":True,"single_attempt":True,"replay_receipt_sha256":"a"*64,"gate_executor_manifest_sha256":"b"*64,"target_selection_authorized":False,"td60_authorized":False,"stage4_authorized":False,"training_authorized":False}
    seen={}
    def runner(path):
        seen["marker"]=(path/"START_MARKER.json").exists()
        return {"candidate_receipts":{}}
    result=R.execute_once(replay(),manifest(True),namespace=ns,authority=auth,runner=runner)
    assert seen["marker"] is True
    assert result["spent_authority"] is True
    with pytest.raises(R.RealTournamentControllerError,match="namespace"):
        R.execute_once(replay(),manifest(True),namespace=ns,authority=auth,runner=runner)
