from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "td_v79_realization_binding_v1.py"
BINDING = ROOT / "results" / "target_discovery" / "synthetic_crosswalk" / "TD_V79_REALIZATION_BINDING_V1.json"
CROSSWALK = ROOT / "results" / "target_discovery" / "synthetic_crosswalk" / "TD_V79_SYNTHETIC_CROSSWALK_V1.json"


def load_module():
    spec = importlib.util.spec_from_file_location("td_v79_realization_binding_v1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_committed_realization_binding_passes():
    m = load_module()
    binding = load_json(BINDING)
    out = m.validate_realization_binding(binding)
    assert out["world_count"] == 12
    assert out["root_manifest_sha256"] == "84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de"
    assert out["directory_digest_sha256"] == "40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286"
    assert out["target_discovery_truth_binding_ready"] is True


def test_world_mapping_matches_frozen_crosswalk_order():
    m = load_module()
    binding = load_json(BINDING)
    crosswalk = load_json(CROSSWALK)
    m.validate_realization_binding(binding)
    m.validate_crosswalk_compatibility(binding, crosswalk)
    assert tuple(binding["worlds"]) == m.EXACT_WORLDS
    assert [binding["worlds"][w]["index"] for w in m.EXACT_WORLDS] == list(range(12))
    assert len({binding["worlds"][w]["opaque_world_id"] for w in m.EXACT_WORLDS}) == 12


def test_every_world_has_exact_future_evidence_pin():
    m = load_module()
    binding = load_json(BINDING)
    for world in m.EXACT_WORLDS:
        pin = m.expected_world_evidence_pin(binding, world)
        rec = binding["worlds"][world]
        assert pin == {
            "world": world,
            "opaque_world_id": rec["opaque_world_id"],
            "truth_manifest_sha256": rec["truth_manifest_sha256"],
            "scientific_truth_sha256": rec["scientific_truth_sha256"],
            "fit_manifest_sha256": rec["fit_manifest_sha256"],
        }


@pytest.mark.parametrize("field", [
    "realization_audit_head",
    "realization_authority_head",
    "synthetic_contract_sha256",
    "pairing_amendment_sha256",
    "generator_bundle_sha256",
    "root_manifest_sha256",
    "world_set_directory_digest_sha256",
    "complete_ledger_sha256",
    "audit_freeze_receipt_sha256",
    "blinded_fit_index_sha256",
])
def test_top_level_authority_tampering_fails(field):
    m = load_module()
    binding = load_json(BINDING)
    binding[field] = "0" * (40 if field.endswith("_head") else 64)
    with pytest.raises(m.RealizationBindingError):
        m.validate_realization_binding(binding)


@pytest.mark.parametrize("key", ["opaque_world_id", "truth_manifest_sha256", "scientific_truth_sha256", "fit_manifest_sha256"])
def test_world_pin_tampering_fails(key):
    m = load_module()
    binding = load_json(BINDING)
    binding["worlds"]["Q08_SPARSE_DETECTION"][key] = "bad"
    with pytest.raises(m.RealizationBindingError):
        m.validate_realization_binding(binding)


def test_q10_q11_pair_is_bound_as_same_non_operator_truth_plus_operator_only_delta():
    m = load_module()
    binding = load_json(BINDING)
    m.validate_realization_binding(binding)
    pair = binding["paired_counterfactual_proof"]
    assert pair["q10_world"] == "Q10_S174_DESIGN_IMBALANCE"
    assert pair["q11_world"] == "Q11_OMITTED_OPERATOR"
    assert pair["non_operator_generated_outputs_identical"] is True
    assert pair["q11_only_additional_truth_paths"] == [
        "truth/operator_offsets/detection.npy",
        "truth/operator_offsets/positive.npy",
    ]


def test_pair_proof_cannot_be_weakened():
    m = load_module()
    binding = load_json(BINDING)
    for mutation in (
        lambda b: b["paired_counterfactual_proof"].update(non_operator_generated_outputs_identical=False),
        lambda b: b["paired_counterfactual_proof"].update(design_sha256="0" * 64),
        lambda b: b["paired_counterfactual_proof"].update(support_sha256="0" * 64),
        lambda b: b["paired_counterfactual_proof"].update(q11_only_additional_truth_paths=[]),
    ):
        bad = copy.deepcopy(binding)
        mutation(bad)
        with pytest.raises(m.RealizationBindingError):
            m.validate_realization_binding(bad)


def test_consumption_boundary_cannot_turn_realization_into_target_authority():
    m = load_module()
    binding = load_json(BINDING)
    assert binding["consumption_boundary"]["synthetic_target_candidate_results_available"] is False
    for key in binding["authority"]:
        bad = copy.deepcopy(binding)
        bad["authority"][key] = True
        with pytest.raises(m.RealizationBindingError):
            m.validate_realization_binding(bad)


def test_synthetic_asymmetry_is_frozen_after_realization():
    m = load_module()
    binding = load_json(BINDING)
    boundary = binding["consumption_boundary"]
    assert boundary == {
        "realized_truth_bytes_audited": True,
        "target_discovery_truth_binding_ready": True,
        "synthetic_target_candidate_results_available": False,
        "synthetic_pass_can_establish_human_biology": False,
        "synthetic_fail_can_falsify_applicable_target_claim": True,
        "synthetic_can_rescue_real_fail": False,
        "synthetic_can_resolve_real_not_estimable": False,
    }


def test_crosswalk_world_mismatch_fails_compatibility():
    m = load_module()
    binding = load_json(BINDING)
    crosswalk = load_json(CROSSWALK)
    crosswalk["worlds"]["Q08_SPARSE_DETECTION"]["index"] = 99
    with pytest.raises(m.RealizationBindingError):
        m.validate_crosswalk_compatibility(binding, crosswalk)
