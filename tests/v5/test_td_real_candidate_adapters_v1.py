from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_real_tournament_case_ledger_v1 as L  # noqa: E402
import td_real_candidate_adapters_v1 as A  # noqa: E402


def _ledger():
    return L.build_case_ledger([
        {"cell_id":"c1","donor_id":"d1","source":"HVS","operator":"op1","split":"TRAIN","support_state":"MEASURED_POSITIVE","query_id":"q1","neighborhood_id":"n1"},
        {"cell_id":"c2","donor_id":"d2","source":"HVS","operator":"op1","split":"TRAIN","support_state":"MEASURED_ZERO","query_id":"q1","neighborhood_id":"n1"},
    ])


def _obs():
    return {
        "c1": {"shared_target":[1.0],"shared_student":[0.8],"query_target":[2.0],"query_student":[1.7],"relational_target":[0.2],"relational_student":[0.1],"regulatory_target":[3.0],"regulatory_student":[2.5],"regulatory_support":True},
        "c2": {"shared_target":[0.0],"shared_student":[0.1],"query_target":[1.0],"query_student":[0.9],"relational_target":[0.3],"relational_student":[0.2],"regulatory_target":[2.0],"regulatory_student":[1.9],"regulatory_support":True},
    }


def test_c1_c3_c6_field_firewalls_exclude_relational_inputs():
    ledger = _ledger()
    obs = _obs()
    for candidate in ("C1_SHARED_EMERGENT", "C3_QUERY_MEASURED", "C6_SHARED_QUERY_COMPOSITE"):
        payload = A.build_candidate_payload(candidate, ledger, obs, replay_context=None)
        assert "relational_target" not in payload.allowed_fields
        assert all("relational_target" not in r.values for r in payload.records)


def test_query_candidates_refuse_student_query_scalar_leakage():
    ledger = _ledger()
    obs = _obs()
    obs["c1"]["query_scalar_student"] = 7.0
    with pytest.raises(A.CandidateAdapterError, match="query_scalar_student"):
        A.build_candidate_payload("C3_QUERY_MEASURED", ledger, obs, replay_context=None)


def test_relational_candidates_require_active_replay_context():
    ledger = _ledger()
    obs = _obs()
    with pytest.raises(A.CandidateAdapterError, match="relational replay context"):
        A.build_candidate_payload("C2_RELATIONAL_SHARED", ledger, obs, replay_context={"relational_status":"FAIL"})
    payload = A.build_candidate_payload("C2_RELATIONAL_SHARED", ledger, obs, replay_context={"relational_status":"PASS","receipt_sha256":"a"*64})
    assert "relational_target" in payload.allowed_fields


def test_c5_is_specialist_and_cannot_be_foundation_rescue():
    payload = A.build_candidate_payload("C5_REGULATORY_SPECIALIST", _ledger(), _obs(), replay_context=None)
    assert payload.foundation is False
    assert payload.foundation_rescue is False


def test_unknown_or_missing_observation_fails_closed():
    with pytest.raises(A.CandidateAdapterError):
        A.build_candidate_payload("C0_UNKNOWN", _ledger(), _obs(), replay_context=None)
    obs = _obs(); obs.pop("c2")
    with pytest.raises(A.CandidateAdapterError, match="missing observation"):
        A.build_candidate_payload("C1_SHARED_EMERGENT", _ledger(), obs, replay_context=None)
