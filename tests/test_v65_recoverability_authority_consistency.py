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


def test_rank_and_shell_policy_are_identical_across_contract_state_and_engine():
    contract=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_20260930.md").read_text()
    state=json.loads((ROOT/"results/v64/V65_PRIVILEGED_RECOVERABILITY_DECISION_STATE_V1.json").read_text())
    assert state["validation_rule"]["rank_choice"]=="LARGEST_CONTIGUOUS_ELIGIBLE_RANK_FROM_2_UPWARD"
    assert state["validation_rule"]["no_skipping_failed_lower_rank"] is True
    assert state["validation_rule"]["aggregate_and_incremental_shell_must_both_pass"] is True
    assert state["test_rule"]["aggregate_and_all_shells_through_selected_rank_must_pass"] is True
    assert "largest contiguous eligible rank" in contract
    assert "if rank 2 fails, lock rank 0" in contract.lower()
    assert "Incremental nested-shell requirement" in contract
    for shell in ("S_2 = P_2","S_4 = P_4 - P_2","S_8 = P_8 - P_4","S_16 = P_16 - P_8"):
        assert shell in contract

    m=_engine()
    sc=m.synthetic_scenarios()
    a,s=sc["full"]
    assert m.select_validation_rank(a,s)==16
    a,s=sc["partial"]
    assert m.select_validation_rank(a,s)==4
    a,s=sc["lower_fail"]
    assert m.select_validation_rank(a,s)==0


def test_aggregate_only_metrics_cannot_qualify_rank():
    m=_engine()
    sc=m.synthetic_scenarios()
    agg,shell=sc["partial"]
    assert m._validation_metric_set_eligible(agg[8])
    assert not m.validation_rank_eligible(agg[8],shell[8])
    assert m.select_validation_rank(agg,shell)==4


def test_superseded_smallest_rank_policy_cannot_be_live_authority():
    state=json.loads((ROOT/"results/v64/V65_PRIVILEGED_RECOVERABILITY_DECISION_STATE_V1.json").read_text())
    assert state["validation_rule"]["previous_rule"].endswith("SUPERSEDED_BEFORE_REAL_EXECUTION")
    contract=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_20260930.md").read_text()
    assert "previous smallest-eligible rule is superseded" in contract.lower()


def test_validation_and_test_materiality_semantics_match_contract():
    m=_engine()
    # VALIDATION: all donor deltas positive, median >= .05; not every donor must exceed .05.
    validation=[
        m.donor(.22,.10,.20),
        m.donor(.40,.10,.20),
        m.donor(.42,.10,.20),
        m.donor(.41,.10,.20),
    ]
    assert m._validation_metric_set_eligible(validation)

    # TEST does not inherit the VALIDATION-only 0.01 technical margin.
    test=[
        m.donor(.305,.300,.20),
        m.donor(.40,.10,.20),
        m.donor(.41,.10,.20),
        m.donor(.42,.10,.20),
    ]
    assert m._test_metric_set_confirmed(validation,test)
