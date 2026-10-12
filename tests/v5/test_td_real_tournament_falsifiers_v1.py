from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_real_tournament_case_ledger_v1 as L  # noqa: E402
import td_real_candidate_adapters_v1 as A  # noqa: E402
import td_real_tournament_falsifiers_v1 as F  # noqa: E402


def _ledger():
    return L.build_case_ledger([
        {"cell_id":"c1","donor_id":"d1","source":"HVS","operator":"op1","split":"TRAIN","support_state":"MEASURED_POSITIVE","query_id":"q1","neighborhood_id":"n1"},
        {"cell_id":"c2","donor_id":"d2","source":"HVS","operator":"op1","split":"TRAIN","support_state":"MEASURED_POSITIVE","query_id":"q1","neighborhood_id":"n1"},
        {"cell_id":"c3","donor_id":"d3","source":"SEA_AD","operator":"op2","split":"EVAL","support_state":"STRUCTURALLY_UNSUPPORTED","query_id":"q2","neighborhood_id":"n2"},
    ])


def _obs():
    return {
        "c1":{"shared_target":[1.0,0.0],"shared_student":[0.9,0.1]},
        "c2":{"shared_target":[0.0,1.0],"shared_student":[0.1,0.9]},
        "c3":{"shared_target":[1.0,1.0],"shared_student":[0.0,0.0]},
    }


def _baselines(payload):
    return {
        name: {r.cell_id:[0.5,0.5] for r in payload.records if r.support_state != "STRUCTURALLY_UNSUPPORTED"}
        for name in ("constant_train_mean","technical_operator_only","address_support_operator","identity_support_only")
    }


def test_falsifiers_emit_raw_case_and_donor_primary_deltas():
    ledger = _ledger(); payload = A.build_candidate_payload("C1_SHARED_EMERGENT", ledger, _obs())
    out = F.run_falsifiers(payload, ledger, _baselines(payload))
    assert set(out) == set(["constant_train_mean","technical_operator_only","address_support_operator","matched_wrong_cell","identity_support_only"])
    ev = out["constant_train_mean"]
    assert set(ev.per_donor_delta) == {"d1","d2"}
    assert len(ev.per_case_delta) == 2
    assert "d3" not in ev.per_donor_delta


def test_matched_wrong_cell_is_derived_from_ledger_and_cross_donor():
    ledger = _ledger(); payload = A.build_candidate_payload("C1_SHARED_EMERGENT", ledger, _obs())
    out = F.run_falsifiers(payload, ledger, _baselines(payload))
    ev = out["matched_wrong_cell"]
    assert ev.estimable_cases == 2
    assert ev.not_estimable_cases == 0
    assert all(delta > 0 for delta in ev.per_donor_delta.values())


def test_missing_mandatory_baseline_refuses_instead_of_cherry_picking():
    ledger = _ledger(); payload = A.build_candidate_payload("C1_SHARED_EMERGENT", ledger, _obs())
    baselines = _baselines(payload); baselines.pop("technical_operator_only")
    with pytest.raises(F.FalsifierError, match="missing mandatory falsifier"):
        F.run_falsifiers(payload, ledger, baselines)


def test_wrong_shape_or_missing_case_refuses():
    ledger = _ledger(); payload = A.build_candidate_payload("C1_SHARED_EMERGENT", ledger, _obs())
    baselines = _baselines(payload); baselines["constant_train_mean"].pop("c2")
    with pytest.raises(F.FalsifierError, match="missing baseline prediction"):
        F.run_falsifiers(payload, ledger, baselines)


def test_unsupported_cases_abstain_not_zero_fill():
    ledger = _ledger(); payload = A.build_candidate_payload("C1_SHARED_EMERGENT", ledger, _obs())
    out = F.run_falsifiers(payload, ledger, _baselines(payload))
    for ev in out.values():
        assert "c3" not in ev.per_case_delta
