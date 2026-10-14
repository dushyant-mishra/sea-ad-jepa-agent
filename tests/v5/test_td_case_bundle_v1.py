from __future__ import annotations

import copy
import importlib.util


def _load():
    name = "scripts.v5.td_case_bundle_v1"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required CaseBundle module missing: {name}"
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _case():
    return {
        "schema": "JEPA_TD_EXECUTOR_CASE_BUNDLE_V1",
        "case_id": "CASE_0001",
        "candidate_id": "C1_SHARED_EMERGENT",
        "gate_id": "G2",
        "donor_id": "D001",
        "source": "HVS",
        "operator_id": "OP01",
        "support_state": "SUPPORTED",
        "support_universe_sha256": "1" * 64,
        "evidence_rights": ["RNA_COMPLEMENTARY"],
        "evidence_contract_sha256": "2" * 64,
        "observation_operator": {
            "assay": "snRNA-seq",
            "measured_vocabulary_sha256": "3" * 64,
            "count_depth": 1000,
            "detected_gene_count": 500,
            "normalization_library_count": 1200,
            "observation_operator_sha256": "4" * 64,
        },
        "input_binding_sha256": "5" * 64,
        "payload": {"measurement_receipt_sha256": "6" * 64},
    }


def test_real_shaped_executor_case_validates_without_synthetic_or_truth_identity():
    C = _load()
    out = C.validate_executor_case(_case())
    assert out["schema"] == "JEPA_TD_EXECUTOR_CASE_BUNDLE_V1"
    assert out["donor_id"] == "D001"
    assert out["source"] == "HVS"
    assert out["operator_id"] == "OP01"
    assert out["support_state"] == "SUPPORTED"
    assert out["observation_operator"]["normalization_library_count"] == 1200
    assert "synthetic" not in repr(out).lower()
    assert "truth" not in repr(out).lower()


def test_executor_case_rejects_truth_or_synthetic_mode_anywhere_in_nested_payload():
    C = _load()
    for mutation in (
        {"truth_label": "PASS"},
        {"synthetic": True},
        {"world_truth": {"gate_status": "FAIL"}},
    ):
        case = _case()
        case["payload"].update(mutation)
        try:
            C.validate_executor_case(case)
        except C.CaseBundleError as exc:
            assert "controller-only" in str(exc).lower() or "forbidden" in str(exc).lower()
        else:
            raise AssertionError(f"executor-visible truth/synthetic marker accepted: {mutation}")


def test_controller_truth_wraps_validated_case_but_does_not_mutate_executor_view():
    C = _load()
    case = _case()
    wrapped = C.bind_controller_truth(case, {"expected_gate_status": "PASS", "world_id": "KT_001"})
    assert wrapped["schema"] == "JEPA_TD_CONTROLLER_CASE_V1"
    assert wrapped["controller_truth"]["expected_gate_status"] == "PASS"
    assert wrapped["executor_case"] == C.validate_executor_case(case)
    assert "controller_truth" not in wrapped["executor_case"]


def test_case_preserves_support_and_observation_semantics_and_rejects_invalid_library_counts():
    C = _load()
    case = _case()
    case["support_state"] = "UNSUPPORTED_STRUCTURAL"
    out = C.validate_executor_case(case)
    assert out["support_state"] == "UNSUPPORTED_STRUCTURAL"

    bad = _case()
    bad["observation_operator"]["normalization_library_count"] = 999
    try:
        C.validate_executor_case(bad)
    except C.CaseBundleError as exc:
        assert "library" in str(exc).lower()
    else:
        raise AssertionError("normalization library smaller than stored count depth accepted")


def test_observation_operator_excludes_biological_identity_shortcuts():
    C = _load()
    for forbidden in ("donor_id", "dataset_embedding", "matrix_id"):
        case = _case()
        case["observation_operator"][forbidden] = "LEAK"
        try:
            C.validate_executor_case(case)
        except C.CaseBundleError as exc:
            assert "observation operator" in str(exc).lower()
        else:
            raise AssertionError(f"biological/arbitrary identity leaked into observation operator: {forbidden}")


def test_binding_hashes_must_be_exact_lowercase_sha256():
    C = _load()
    case = _case()
    case["input_binding_sha256"] = "not-a-hash"
    try:
        C.validate_executor_case(case)
    except C.CaseBundleError:
        pass
    else:
        raise AssertionError("malformed case binding accepted")


def test_controller_truth_requires_valid_status_when_present():
    C = _load()
    try:
        C.bind_controller_truth(_case(), {"expected_gate_status": "WINNER", "world_id": "KT_001"})
    except C.CaseBundleError as exc:
        assert "expected_gate_status" in str(exc)
    else:
        raise AssertionError("invalid known-truth gate status accepted")
