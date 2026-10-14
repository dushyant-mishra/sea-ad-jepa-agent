from __future__ import annotations

import copy
import importlib.util

from scripts.v5 import td_execution_manifest_v1 as M
from scripts.v5 import td_qualification_registry_v1 as R


def _load():
    name = "scripts.v5.td_target_qualification_bundle_v1"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required target bundle module missing: {name}"
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _manifest():
    return M.build_execution_manifest(
        R.load_registry(), mode="SYNTHETIC_REHEARSAL", requested_gates=["G2", "G6", "R1"]
    )


def _gate_receipts():
    return {
        gate: {
            "gate_id": gate,
            "status": "PASS" if gate != "R1" else "NOT_ESTIMABLE",
            "receipt_sha256": (str(i + 1) * 64)[:64],
        }
        for i, gate in enumerate(["G2", "G6", "R1"])
    }


def _tournament(selection="NONE", candidate_id=None):
    return {
        "schema": "JEPA_TD_AUTHENTICATED_TOURNAMENT_OUTPUT_V1",
        "selection": selection,
        "candidate_id": candidate_id,
        "receipt_sha256": "a" * 64,
    }


def _policies():
    return {
        "canonical_addresses_sha256": "b" * 64,
        "support_estimability_map_sha256": "c" * 64,
        "evidence_right_ladder_sha256": "d" * 64,
        "required_source_strata_sha256": "e" * 64,
        "falsifier_policy_sha256": "f" * 64,
        "nuisance_baseline_policy_sha256": "1" * 64,
        "uncertainty_reference_policy_sha256": "2" * 64,
        "relational_semantics_sha256": "3" * 64,
        "observation_operator_contract_sha256": "4" * 64,
    }


def test_none_is_valid_first_class_target_bundle_outcome():
    T = _load()
    bundle = T.build_target_qualification_bundle(
        tournament_output=_tournament(),
        execution_manifest=_manifest(),
        gate_receipts=_gate_receipts(),
        policy_identities=_policies(),
        canonical_addresses=[],
        known_limitations=["R1 remained NOT_ESTIMABLE in this rehearsal"],
    )
    assert bundle["schema"] == "JEPA_TD_TARGET_QUALIFICATION_BUNDLE_V1"
    assert bundle["selected_candidate"] is None
    assert bundle["selection"] == "NONE"
    assert bundle["canonical_addresses"] == []
    assert len(bundle["bundle_sha256"]) == 64


def test_selected_candidate_requires_nonempty_identity_and_canonical_addresses():
    T = _load()
    good = T.build_target_qualification_bundle(
        tournament_output=_tournament("SELECTED", "C1"),
        execution_manifest=_manifest(),
        gate_receipts=_gate_receipts(),
        policy_identities=_policies(),
        canonical_addresses=["ENSG000001::RNA"],
        known_limitations=["synthetic rehearsal only"],
    )
    assert good["selected_candidate"] == "C1"
    for bad_candidate, bad_addresses in ((None, ["A"]), ("C1", [])):
        try:
            T.build_target_qualification_bundle(
                tournament_output=_tournament("SELECTED", bad_candidate),
                execution_manifest=_manifest(), gate_receipts=_gate_receipts(),
                policy_identities=_policies(), canonical_addresses=bad_addresses,
                known_limitations=["x"],
            )
        except T.TargetBundleError:
            pass
        else:
            raise AssertionError("selected target without full identity/address contract accepted")


def test_gate_receipts_must_exactly_match_execution_manifest_gate_set():
    T = _load()
    receipts = _gate_receipts(); receipts.pop("R1")
    try:
        T.build_target_qualification_bundle(
            tournament_output=_tournament(), execution_manifest=_manifest(), gate_receipts=receipts,
            policy_identities=_policies(), canonical_addresses=[], known_limitations=["x"],
        )
    except T.TargetBundleError as exc:
        assert "gate receipt" in str(exc).lower()
    else:
        raise AssertionError("target bundle accepted incomplete gate receipts")


def test_known_limitations_are_mandatory_and_cannot_be_silently_dropped():
    T = _load()
    try:
        T.build_target_qualification_bundle(
            tournament_output=_tournament(), execution_manifest=_manifest(), gate_receipts=_gate_receipts(),
            policy_identities=_policies(), canonical_addresses=[], known_limitations=[],
        )
    except T.TargetBundleError as exc:
        assert "limitation" in str(exc).lower()
    else:
        raise AssertionError("bundle without persistent limitations accepted")


def test_bundle_digest_changes_on_scientific_field_mutation_and_validation_detects_tamper():
    T = _load()
    bundle = T.build_target_qualification_bundle(
        tournament_output=_tournament(), execution_manifest=_manifest(), gate_receipts=_gate_receipts(),
        policy_identities=_policies(), canonical_addresses=[], known_limitations=["x"],
    )
    tampered = copy.deepcopy(bundle)
    tampered["known_limitations"][0] = "different"
    assert T.compute_bundle_sha256(tampered) != bundle["bundle_sha256"]
    try:
        T.validate_target_qualification_bundle(tampered)
    except T.TargetBundleError as exc:
        assert "digest" in str(exc).lower() or "sha" in str(exc).lower()
    else:
        raise AssertionError("tampered target bundle validated")


def test_policy_identity_set_is_exact_and_hash_bound():
    T = _load()
    bad = _policies(); bad.pop("observation_operator_contract_sha256")
    try:
        T.build_target_qualification_bundle(
            tournament_output=_tournament(), execution_manifest=_manifest(), gate_receipts=_gate_receipts(),
            policy_identities=bad, canonical_addresses=[], known_limitations=["x"],
        )
    except T.TargetBundleError:
        pass
    else:
        raise AssertionError("target bundle accepted incomplete policy identities")


def test_target_bundle_never_grants_training_or_stage4_authority():
    T = _load()
    bundle = T.build_target_qualification_bundle(
        tournament_output=_tournament(), execution_manifest=_manifest(), gate_receipts=_gate_receipts(),
        policy_identities=_policies(), canonical_addresses=[], known_limitations=["x"],
    )
    assert all(v is False for v in bundle["authority"].values())
    assert bundle["execution_mode"] == "SYNTHETIC_REHEARSAL"
    assert bundle["downstream_human_eligible"] is False
