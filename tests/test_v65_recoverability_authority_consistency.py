from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def _engine():
    p=ROOT/"scripts/v64/privileged_recoverability_decision_engine_smoke_v1.py"
    spec=importlib.util.spec_from_file_location("v65_engine_consistency",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_rank_policy_is_identical_across_contract_state_and_engine():
    contract=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_20260930.md").read_text()
    state=json.loads((ROOT/"results/v64/V65_PRIVILEGED_RECOVERABILITY_DECISION_STATE_V1.json").read_text())
    assert state["validation_rule"]["rank_choice"]=="LARGEST_CONTIGUOUS_ELIGIBLE_RANK_FROM_2_UPWARD"
    assert state["validation_rule"]["no_skipping_failed_lower_rank"] is True
    assert "largest contiguous eligible rank" in contract
    assert "if rank 2 fails, lock rank 0" in contract.lower()

    m=_engine()
    good=[m.donor(.4,.05,.15) for _ in range(4)]
    fail=[m.donor(.4,.05,.15,geometry=False) for _ in range(4)]
    assert m.select_validation_rank({2:good,4:good,8:good,16:good})==16
    assert m.select_validation_rank({2:good,4:good,8:fail,16:good})==4
    assert m.select_validation_rank({2:fail,4:good,8:good,16:good})==0


def test_superseded_smallest_rank_policy_cannot_be_live_authority():
    state=json.loads((ROOT/"results/v64/V65_PRIVILEGED_RECOVERABILITY_DECISION_STATE_V1.json").read_text())
    assert state["validation_rule"]["previous_rule"].endswith("SUPERSEDED_BEFORE_REAL_EXECUTION")
    contract=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_20260930.md").read_text()
    assert "previous smallest-eligible rule is superseded" in contract.lower()
