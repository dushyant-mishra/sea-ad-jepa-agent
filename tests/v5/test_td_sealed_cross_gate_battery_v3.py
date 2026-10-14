from __future__ import annotations

import importlib.util


def _load():
    name = "scripts.v5.td_sealed_cross_gate_battery_v3"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required sealed battery missing: {name}"
    import scripts.v5.td_sealed_cross_gate_battery_v3 as B
    return B


def test_manifest_binds_all_repaired_exact_gate_heads():
    B = _load()
    m = B.world_manifest()
    assert m["sealed_before_execution"] is True
    assert m["exact_gate_heads"] == {
        "G8": "95dd474a02ce571722df9e8f08b42e81af2e8736",
        "G6": "aa36d56bfdd92335a516e329817411a66da917c9",
        "G7": "5a711f9a4ea0328445a05dadc1e011efb16a3c13",
        "G9": "a28f158007f20df1b0c9329915220a1a71ae7aec",
        "G2": "49edb657e2653532eca9365976f5b3b9f14b4467",
        "R1": "a0a1d060faff9a7a38e8f331302f17dac6610f51",
        "INCREMENT": "b7c317c640aa231a7d5ec1fa12271a39bfee86e6",
    }
    assert m["human_candidate_outcomes_used"] is False
    assert m["human_thresholds_imported"] is False


def test_sealed_v3_exam_passes_cross_gate_hostile_invariants():
    B = _load()
    out = B.run_exam()
    assert out["status"] == "PASS_SEALED_CROSS_GATE_BATTERY_V3"
    assert out["mismatches"] == []
    assert out["observed_gate_heads"] == out["exact_gate_heads"]


def test_caller_steering_is_blocked_across_repaired_gates():
    B = _load()
    out = B.run_exam()["invariants"]
    assert out["CALLER_STEERING"]["G2"] == "REJECTED"
    assert out["CALLER_STEERING"]["G6"] == "FAIL_CLOSED"
    assert out["CALLER_STEERING"]["G9"] == "FAIL_CLOSED"


def test_zero_margin_never_creates_human_authority():
    B = _load()
    out = B.run_exam()["invariants"]
    assert out["ZERO_MARGIN"]["G2"] == "NOT_ESTIMABLE"
    assert out["ZERO_MARGIN"]["G6"] == "NOT_ESTIMABLE"


def test_support_and_source_asymmetry_do_not_get_rescued():
    B = _load()
    out = B.run_exam()["invariants"]
    assert out["SUPPORT_ATTRITION"]["G2"] == "REJECTED"
    assert out["SOURCE_ASYMMETRY"]["G7"] == "NOT_ESTIMABLE"
    assert out["SOURCE_ASYMMETRY"]["G9"] in {"FAIL", "NOT_ESTIMABLE"}
    assert out["SOURCE_ASYMMETRY"]["R1"] == "NOT_ESTIMABLE"


def test_technical_depth_confound_is_blocked_in_r1_and_g8():
    B = _load()
    out = B.run_exam()["invariants"]
    assert out["TECHNICAL_DEPTH_CONFOUND"]["R1"] == "PASS_TECHNICAL_NEGATIVE"
    assert out["TECHNICAL_DEPTH_CONFOUND"]["G8"] == "REFERENCE_GENERATION_BLOCKED"


def test_numerical_failure_is_not_biological_fail():
    B = _load()
    out = B.run_exam()["invariants"]
    assert out["NUMERICAL_FAILURE"]["G2"] == "NUMERICAL_FAILURE"
    assert out["NUMERICAL_FAILURE"]["G6"] == "NUMERICAL_FAILURE"
    assert out["NUMERICAL_FAILURE"]["G9"] == "NUMERICAL_FAILURE"


def test_all_repaired_surfaces_remain_without_human_authority():
    B = _load()
    out = B.run_exam()
    assert out["human_candidate_outcomes_used"] is False
    assert out["human_thresholds_imported"] is False
    assert out["synthetic_results_have_biological_authority"] is False
    assert all(v is False for v in out["authority"].values())
