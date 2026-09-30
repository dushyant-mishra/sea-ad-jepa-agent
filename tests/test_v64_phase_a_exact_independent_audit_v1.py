from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_phase_a_independent_audit_accepts_structure_but_keeps_phase_b_stopped():
    p=json.loads((ROOT/"results/v64/V64_PHASE_A_EXACT_INDEPENDENT_AUDIT_V1.json").read_text())
    assert p["sampler_qualification"]["real_edge_comparisons"]==64
    assert p["sampler_qualification"]["non_empty_comparisons"]==42
    assert p["sampler_qualification"]["algebra_only_total"]==0
    assert p["sampler_qualification"]["oracle_only_total"]==0
    assert p["phase_A"]["retained_primary_CONTROL_A"]==13510
    assert p["phase_A"]["CONTROL_B_succeeded_while_A_failed_NOT_RESCUED"]==2271
    assert p["singleton_admissible_set_caveat"]["CONTROL_A_exactly_one_admissible_start"]==344
    assert p["singleton_admissible_set_caveat"]["structurally_degenerate_A_B_null_edges"]==167
    assert p["decision"]["phase_B"].startswith("STOPPED")
    assert p["decision"]["training"]=="OFF"

def test_old_15646_is_not_reinterpreted_as_control_b_rescue():
    p=json.loads((ROOT/"results/v64/V64_PHASE_A_EXACT_INDEPENDENT_AUDIT_V1.json").read_text())
    assert p["superseded_15646"]["status"]=="NOT_SAME_ESTIMAND__DO_NOT_EXPLAIN_BY_A_OR_B_ARITHMETIC_ALONE"
    assert len(p["superseded_15646"]["old_executor_known_contract_violations"])>=6

def test_singleton_contract_forbids_randomized_null_overclaim():
    t=(ROOT/"docs/agent/V64_DOWNSTREAM_CONTROL_RANDOMNESS_STRATA_CONTRACT_20260930.md").read_text()
    assert "FORCED_SINGLETON_SUPPORT_1" in t
    assert "not described as randomized" in t
    assert "contributes no evidence" in t
    assert "before Phase B" in t
