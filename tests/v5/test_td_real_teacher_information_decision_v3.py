from __future__ import annotations

import importlib.util

import pytest


def _load():
    name = "scripts.v5.td_real_teacher_information_decision_v3"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required repair module missing: {name}"
    import scripts.v5.td_real_teacher_information_decision_v3 as D
    return D


def _probe(values, *, binding="a" * 64):
    return {
        "status": "PASS",
        "input_binding_sha256": binding,
        "donor_deltas": [
            {"donor_id": f"D{i:02d}", "delta": float(v)}
            for i, v in enumerate(values)
        ],
    }


def _reference(values, *, binding="a" * 64, kind="U_MEASUREMENT"):
    return {
        "schema": "JEPA_TD_REAL_G6_REFERENCE_MARGIN_V3",
        "frozen": True,
        "qualified": True,
        "metric": "DONOR_BALANCED_OUTER_MSE_DELTA",
        "orientation": "STUDENT_MSE_MINUS_TEACHER_MSE__LARGER_IS_BETTER",
        "reference_kind": kind,
        "donor_margins": {f"D{i:02d}": float(v) for i, v in enumerate(values)},
        "input_binding_sha256": binding,
        "reference_receipt_sha256": "b" * 64,
        "independent_non_degenerate_reference": True,
    }


def test_zero_margin_cannot_reduce_g6_to_direction_only():
    D = _load()
    out = D.adjudicate_g6_v3(
        probe_result=_probe([1.0] * 8),
        reference_artifact=_reference([0.0] * 8, kind="U_REFIT"),
        external_qualification_receipt_sha256=None,
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "NONDEGENERATE_SUBSTANTIVE_MARGIN_NOT_ESTABLISHED"
    assert out["human_pass_fail_authorized"] is False


def test_literal_caller_qualification_cannot_authorize_human_pass_or_fail():
    D = _load()
    out = D.adjudicate_g6_v3(
        probe_result=_probe([1.0] * 8),
        reference_artifact=_reference([0.25] * 8),
        external_qualification_receipt_sha256="c" * 64,
    )
    assert out["diagnostic_status"] == "ADVANTAGE_RECURRENT_BEYOND_MARGIN"
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "SEALED_EXTERNAL_DECISION_QUALIFICATION_NOT_FROZEN"
    assert out["human_pass_fail_authorized"] is False


def test_nonsignificant_positive_pattern_is_inconclusive_not_biological_fail():
    D = _load()
    values = [1.0] * 9 + [-1.0]
    out = D.adjudicate_g6_v3(
        probe_result=_probe(values),
        reference_artifact=_reference([0.25] * 10),
        external_qualification_receipt_sha256=None,
        alpha=0.01,
    )
    assert out["diagnostic_status"] == "INCONCLUSIVE"
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["human_pass_fail_authorized"] is False


def test_recurrent_negative_margin_adjusted_signal_is_distinct_from_no_demonstration():
    D = _load()
    out = D.adjudicate_g6_v3(
        probe_result=_probe([0.0] * 8),
        reference_artifact=_reference([0.25] * 8),
        external_qualification_receipt_sha256=None,
    )
    assert out["diagnostic_status"] == "NONADVANTAGE_RECURRENT_BEYOND_MARGIN"
    assert out["status"] == "NOT_ESTIMABLE"


def test_reference_requires_exact_binding_and_positive_independent_margin():
    D = _load()
    with pytest.raises(D.TeacherInformationDecisionV3Error, match="binding"):
        D.adjudicate_g6_v3(
            probe_result=_probe([1.0] * 8, binding="a" * 64),
            reference_artifact=_reference([0.25] * 8, binding="c" * 64),
            external_qualification_receipt_sha256=None,
        )
    ref = _reference([0.25] * 8)
    ref["independent_non_degenerate_reference"] = False
    out = D.adjudicate_g6_v3(
        probe_result=_probe([1.0] * 8),
        reference_artifact=ref,
        external_qualification_receipt_sha256=None,
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "NONDEGENERATE_SUBSTANTIVE_MARGIN_NOT_ESTABLISHED"


def test_nonfinite_inputs_are_numerical_failure_not_exception_or_biological_fail():
    D = _load()
    probe = _probe([1.0] * 8)
    probe["donor_deltas"][3]["delta"] = float("nan")
    out = D.adjudicate_g6_v3(
        probe_result=probe,
        reference_artifact=_reference([0.25] * 8),
        external_qualification_receipt_sha256=None,
    )
    assert out["status"] == "NUMERICAL_FAILURE"
    assert out["human_pass_fail_authorized"] is False


def test_authority_remains_closed():
    D = _load()
    out = D.adjudicate_g6_v3(
        probe_result=_probe([1.0] * 8),
        reference_artifact=_reference([0.25] * 8),
        external_qualification_receipt_sha256=None,
    )
    assert all(v is False for v in out["authority"].values())
