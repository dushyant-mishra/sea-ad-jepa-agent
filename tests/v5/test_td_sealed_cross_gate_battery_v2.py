from __future__ import annotations

import scripts.v5.td_sealed_cross_gate_battery_v2 as B


def test_manifest_binds_repaired_g7_v3_exact_head():
    m = B.world_manifest()
    assert m["sealed_before_execution"] is True
    assert m["exact_gate_heads"]["G7"] == "5a711f9a4ea0328445a05dadc1e011efb16a3c13"
    assert m["human_candidate_outcomes_used"] is False
    assert m["human_thresholds_imported"] is False


def test_sealed_exam_passes_all_predeclared_expectations_against_g7_v3():
    out = B.run_exam()
    assert out["status"] == "PASS_SEALED_CROSS_GATE_BATTERY_V2"
    assert out["all_expectations_met"] is True
    assert out["mismatches"] == []
    assert out["observed_gate_heads"] == out["exact_gate_heads"]


def test_g7_source_asymmetry_is_now_exercised_in_system_battery():
    out = B.run_exam()
    assert out["world_results"]["SOURCE_ASYMMETRY"]["G7"] == "NOT_ESTIMABLE"
    assert out["world_results"]["NO_ADDED_EVIDENCE"]["G7"] == "NOT_ESTIMABLE"
    assert out["world_results"]["SPARSE_SUPPORT"]["G7"] == "NOT_ESTIMABLE"


def test_authority_remains_off():
    out = B.run_exam()
    assert out["human_candidate_outcomes_used"] is False
    assert out["human_thresholds_imported"] is False
    assert out["synthetic_results_have_biological_authority"] is False
    assert all(value is False for value in out["authority"].values())
