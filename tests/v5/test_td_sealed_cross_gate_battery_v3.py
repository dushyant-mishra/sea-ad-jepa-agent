from __future__ import annotations

import importlib
import importlib.util


def _load():
    name = "scripts.v5.td_sealed_cross_gate_battery_v3"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required system requalification module missing: {name}"
    return importlib.import_module(name)


def test_v3_manifest_freezes_exact_repaired_gate_heads_before_exam():
    B = _load()
    manifest = B.world_manifest()
    assert manifest["sealed_before_execution"] is True
    assert manifest["human_candidate_outcomes_used"] is False
    assert manifest["human_thresholds_imported"] is False
    assert manifest["exact_gate_heads"] == {
        "R1": "949d76ff03cb57c5a88fef9efdb79fced9154024",
        "G6": "4110d4478c3353d86740dd135d62460ff7a7611f",
        "G7": "5a711f9a4ea0328445a05dadc1e011efb16a3c13",
        "G9": "8d6b23a18051f64463ee9b2649f4fe5fc7123f0d",
        "G2": "42df903d6190b7aa1b8eb65d810ab813cd327445",
        "G8": "95dd474a02ce571722df9e8f08b42e81af2e8736",
        "INCREMENT": "b7c317c640aa231a7d5ec1fa12271a39bfee86e6",
    }


def test_v3_preserves_prior_sealed_world_expectations_for_unchanged_diagnostic_paths():
    B = _load()
    receipt = B.run_exam()
    assert receipt["legacy_worlds_all_expectations_met"] is True
    assert receipt["legacy_world_mismatches"] == []


def test_macha_repair_traps_all_match_predeclared_statuses():
    B = _load()
    receipt = B.run_exam()
    assert receipt["repair_traps"] == {
        "G8_REFERENCE_GENERATION": "BLOCKED_G8_STATISTICAL_CONTRACT_NOT_QUALIFIED",
        "G6_ZERO_MARGIN": "NOT_ESTIMABLE_SUBSTANTIVE_MARGIN",
        "G6_TYPED_QUALIFICATION": "BLOCKED_G6_PRODUCED_QUALIFICATION_RECEIPT_REQUIRED",
        "GEOMETRY_TYPED_PRODUCER": "BLOCKED_GEOMETRY_PRODUCER_NOT_INDEPENDENTLY_QUALIFIED",
        "GEOMETRY_NULL_NE_STABILITY_FAIL": "FAIL",
        "R1_MECHANICS_KNOWN_TRUTH": "PASS_R1_V3_MECHANICS_KNOWN_TRUTH",
        "R1_TYPED_PRODUCER": "BLOCKED_R1_CELL_IDENTITY_NULL_PRODUCER_NOT_QUALIFIED",
        "G2_NINE_OF_TEN_POSITIVE": "NOT_ESTIMABLE",
        "G2_TYPED_POLICY": "BLOCKED_G2_STATIC_POLICY_NOT_PRODUCED_AND_QUALIFIED",
    }


def test_exact_heads_observed_equal_frozen_heads():
    B = _load()
    receipt = B.run_exam()
    assert receipt["observed_gate_heads"] == receipt["exact_gate_heads"]


def test_v3_system_requalification_passes_only_as_mechanics_and_firewall_exam():
    B = _load()
    receipt = B.run_exam()
    assert receipt["status"] == "PASS_SEALED_CROSS_GATE_BATTERY_V3"
    assert receipt["all_expectations_met"] is True
    assert receipt["human_candidate_outcomes_used"] is False
    assert receipt["human_thresholds_imported"] is False
    assert receipt["synthetic_results_have_biological_authority"] is False
    assert all(value is False for value in receipt["authority"].values())
