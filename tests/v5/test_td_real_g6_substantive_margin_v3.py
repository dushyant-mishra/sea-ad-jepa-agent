from __future__ import annotations

import importlib.util


def _load(name: str):
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required G6 V3 repair module missing: {name}"
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _probe(n=8, delta=1.0):
    return {
        "status": "PASS",
        "input_binding_sha256": "a" * 64,
        "donor_deltas": [{"donor_id": f"D{i:02d}", "delta": float(delta)} for i in range(n)],
        "claim_boundary": "FINITE_LINEAR_DIAGNOSTIC_ONLY__NO_INFORMATION_THEORETIC_ABSENCE_CLAIM",
    }


def _reference(n=8, margin=0.25, *, kind="U_MEASUREMENT"):
    return {
        "schema": "JEPA_TD_REAL_G6_REFERENCE_MARGIN_V2",
        "frozen": True,
        "qualified": True,
        "metric": "DONOR_BALANCED_OUTER_MSE_DELTA",
        "orientation": "STUDENT_MSE_MINUS_TEACHER_MSE__LARGER_IS_BETTER",
        "reference_kind": kind,
        "donor_margins": {f"D{i:02d}": float(margin) for i in range(n)},
        "deciding_namespace_disjoint": True,
        "input_binding_sha256": "a" * 64,
        "reference_receipt_sha256": "b" * 64,
        "producer_code_sha256": "c" * 64,
        "producer_qualification_receipt_sha256": "d" * 64,
        "margin_units_sha256": "e" * 64,
        "margin_is_non_degenerate": margin > 0.0,
    }


def _qual_receipt():
    return {
        "schema": "JEPA_TD_REAL_G6_DECISION_QUALIFICATION_RECEIPT_V3",
        "status": "PASS_KNOWN_TRUTH_G6_MARGIN_DECISION_V3",
        "producer_code_sha256": "f" * 64,
        "qualification_worlds_sha256": "1" * 64,
        "receipt_sha256": "2" * 64,
        "human_semantics_qualified": True,
    }


def test_zero_margin_cannot_reduce_g6_to_direction_only():
    G = _load("scripts.v5.td_real_teacher_information_decision_v3")
    out = G.adjudicate_g6_human_decision_v3(
        probe_result=_probe(delta=0.001),
        reference_artifact=_reference(margin=0.0, kind="U_REFIT"),
        decision_qualification_receipt=_qual_receipt(),
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "NON_DEGENERATE_SUBSTANTIVE_MARGIN_REQUIRED"


def test_literal_typed_qualification_tokens_are_not_sufficient():
    G = _load("scripts.v5.td_real_teacher_information_decision_v3")
    fake = {
        "schema": "JEPA_TD_REAL_G6_DECISION_QUALIFICATION_RECEIPT_V3",
        "status": "PASS_KNOWN_TRUTH_G6_MARGIN_DECISION_V3",
        "human_semantics_qualified": True,
    }
    out = G.adjudicate_g6_human_decision_v3(
        probe_result=_probe(), reference_artifact=_reference(), decision_qualification_receipt=fake
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "DECISION_QUALIFICATION_RECEIPT_NOT_AUTHENTICATED"


def test_reference_requires_producer_and_units_custody_not_boolean_qualified_only():
    G = _load("scripts.v5.td_real_teacher_information_decision_v3")
    broken = _reference()
    broken.pop("producer_qualification_receipt_sha256")
    out = G.adjudicate_g6_human_decision_v3(
        probe_result=_probe(), reference_artifact=broken, decision_qualification_receipt=_qual_receipt()
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "REFERENCE_ARTIFACT_NOT_AUTHENTICATED"


def test_alpha_is_frozen_not_caller_tunable():
    G = _load("scripts.v5.td_real_teacher_information_decision_v3")
    assert G.FAMILY_ALPHA == 0.01
    try:
        G.adjudicate_g6_human_decision_v3(
            probe_result=_probe(), reference_artifact=_reference(),
            decision_qualification_receipt=_qual_receipt(), alpha=0.05
        )
    except TypeError:
        pass
    else:
        raise AssertionError("G6 V3 must not expose caller-tunable alpha")


def test_positive_advantage_above_authenticated_nonzero_margin_can_pass():
    G = _load("scripts.v5.td_real_teacher_information_decision_v3")
    out = G.adjudicate_g6_human_decision_v3(
        probe_result=_probe(delta=1.0), reference_artifact=_reference(margin=0.25),
        decision_qualification_receipt=_qual_receipt()
    )
    assert out["status"] == "PASS"


def test_raw_positive_below_margin_is_fail_only_after_authenticated_decision_semantics():
    G = _load("scripts.v5.td_real_teacher_information_decision_v3")
    out = G.adjudicate_g6_human_decision_v3(
        probe_result=_probe(delta=0.5), reference_artifact=_reference(margin=0.75),
        decision_qualification_receipt=_qual_receipt()
    )
    assert out["status"] == "FAIL"


def test_authority_remains_closed():
    G = _load("scripts.v5.td_real_teacher_information_decision_v3")
    out = G.adjudicate_g6_human_decision_v3(
        probe_result=_probe(), reference_artifact=_reference(), decision_qualification_receipt=_qual_receipt()
    )
    assert all(value is False for value in out["authority"].values())
