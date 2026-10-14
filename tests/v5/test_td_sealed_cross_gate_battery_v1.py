from __future__ import annotations

import json

import scripts.v5.td_sealed_cross_gate_battery_v1 as B


def test_world_manifest_is_sealed_and_independent_of_human_outcomes():
    manifest = B.world_manifest()
    assert manifest["schema"] == "JEPA_TD_SEALED_CROSS_GATE_BATTERY_V1"
    assert manifest["sealed_before_execution"] is True
    assert manifest["human_candidate_outcomes_used"] is False
    assert manifest["human_thresholds_imported"] is False
    assert manifest["seed_namespace"] == "TD_SEALED_CROSS_GATE_V1_20261014"
    assert len(manifest["worlds"]) >= 8
    assert len({w["seed"] for w in manifest["worlds"]}) == len(manifest["worlds"])
    assert all(v is False for v in manifest["authority"].values())


def test_exam_runs_exact_frozen_gate_heads_and_matches_known_truth():
    out = B.run_exam()
    assert out["status"] == "PASS_SEALED_CROSS_GATE_BATTERY_V1"
    assert out["all_expectations_met"] is True
    assert out["exact_gate_heads"] == {
        "R1": "1df20029defaa2bcd7a51869c1026ac6075b1323",
        "G6": "bb1e35d33deb52236829012be452e4c4d8b362fc",
        "G7": "d90047308d633e259195a54501a230373b36d043",
        "G9": "6e5182e2dc4e8e263e8cbd309aed6494b5ea7a55",
        "G2": "c174d05215f14bda5292c07559b10445bc17d86c",
        "INCREMENT": "b7c317c640aa231a7d5ec1fa12271a39bfee86e6",
    }
    assert all(v is False for v in out["authority"].values())


def test_sparse_support_world_abstains_across_applicable_gates():
    out = B.run_exam()
    world = out["world_results"]["SPARSE_SUPPORT"]
    assert world["R1"] == "NOT_ESTIMABLE_SUPPORT"
    assert world["G7"] == "NOT_ESTIMABLE"
    assert world["G9"] == "NOT_ESTIMABLE"
    assert world["G2"] == "NOT_ESTIMABLE"
    assert world["R4"] == "NOT_ESTIMABLE"


def test_small_positive_margin_world_cannot_pass_by_direction_alone():
    out = B.run_exam()
    world = out["world_results"]["MARGIN_TRAP"]
    assert world["G6"] == "FAIL"
    assert world["G2"] == "FAIL"
    assert world["R4"] == "FAIL"


def test_source_asymmetry_is_noncompensating():
    out = B.run_exam()
    world = out["world_results"]["SOURCE_ASYMMETRY"]
    assert world["G9"] == "NOT_ESTIMABLE"
    assert world["G2"] == "FAIL"
    assert world["R4"] == "FAIL"


def test_adverse_null_tail_trap_is_not_rescued_by_null_median():
    out = B.run_exam()
    assert out["world_results"]["ADVERSE_NULL_TAIL_TRAP"]["G9"] == "FAIL"


def test_no_added_evidence_is_not_called_convergence():
    out = B.run_exam()
    assert out["world_results"]["NO_ADDED_EVIDENCE"]["G7"] == "NOT_ESTIMABLE"


def test_c6_must_beat_both_constituents():
    out = B.run_exam()
    assert out["world_results"]["C6_PARTIAL_INCREMENT"]["C6"] == "FAIL"


def test_cross_stratum_relational_pairing_is_contract_error():
    out = B.run_exam()
    assert out["world_results"]["RELATIONAL_STRATUM_MISMATCH"]["R1"] == "CONTRACT_ERROR"


def test_receipt_is_canonical_json_serializable():
    out = B.run_exam()
    encoded = json.dumps(out, sort_keys=True, separators=(",", ":"))
    assert "PASS_SEALED_CROSS_GATE_BATTERY_V1" in encoded
