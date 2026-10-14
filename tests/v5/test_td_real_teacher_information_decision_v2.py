from __future__ import annotations

import pytest

import scripts.v5.td_real_teacher_information_decision_v2 as D


def _probe(deltas, *, status="PASS"):
    return {
        "status": status,
        "donor_deltas": [
            {"donor_id": f"D{i:02d}", "delta": float(value)}
            for i, value in enumerate(deltas)
        ],
        "claim_boundary": "FINITE_LINEAR_DIAGNOSTIC_ONLY__NO_INFORMATION_THEORETIC_ABSENCE_CLAIM",
    }


def _qualification():
    return {
        "schema": "JEPA_TD_REAL_G6_TEACHER_INFORMATION_PROBE_QUALIFICATION_V1",
        "status": "PASS_KNOWN_TRUTH_G6_PROBE_QUALIFICATION",
        "human_fail_semantics_qualified": True,
        "probe_scope": "MATCHED_MULTI_OUTPUT_RIDGE_OPERATIONAL_DIAGNOSTIC",
    }


def _reference(margins):
    return {
        "schema": "JEPA_TD_REAL_G6_REFERENCE_MARGIN_V1",
        "frozen": True,
        "qualified": True,
        "metric": "DONOR_BALANCED_OUTER_MSE_DELTA",
        "orientation": "STUDENT_MSE_MINUS_TEACHER_MSE__LARGER_IS_BETTER",
        "reference_kind": "MAX_U_REFIT_U_MEASUREMENT",
        "donor_margins": {
            f"D{i:02d}": float(value) for i, value in enumerate(margins)
        },
        "deciding_namespace_disjoint": True,
        "input_binding_sha256": "a" * 64,
        "reference_receipt_sha256": "b" * 64,
    }


def test_raw_positive_probe_is_not_enough_without_reference_margin():
    with pytest.raises(D.TeacherInformationDecisionError, match="reference"):
        D.adjudicate_g6_human_decision(
            probe_result=_probe([1.0] * 8),
            probe_qualification=_qualification(),
            reference_artifact=None,
            alpha=0.01,
        )


def test_probe_qualification_is_required_before_fail_semantics():
    q = _qualification()
    q["human_fail_semantics_qualified"] = False
    out = D.adjudicate_g6_human_decision(
        probe_result=_probe([-1.0] * 8, status="FAIL"),
        probe_qualification=q,
        reference_artifact=_reference([0.1] * 8),
        alpha=0.01,
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "PROBE_REJECTION_POWER_NOT_QUALIFIED"


def test_reference_metric_and_orientation_must_match_g6_delta():
    ref = _reference([0.1] * 8)
    ref["metric"] = "COSINE_DISTANCE"
    with pytest.raises(D.TeacherInformationDecisionError, match="metric"):
        D.adjudicate_g6_human_decision(
            probe_result=_probe([1.0] * 8),
            probe_qualification=_qualification(),
            reference_artifact=ref,
            alpha=0.01,
        )


def test_reference_must_be_frozen_qualified_and_deciding_disjoint():
    for key, value in (
        ("frozen", False),
        ("qualified", False),
        ("deciding_namespace_disjoint", False),
    ):
        ref = _reference([0.1] * 8)
        ref[key] = value
        with pytest.raises(D.TeacherInformationDecisionError):
            D.adjudicate_g6_human_decision(
                probe_result=_probe([1.0] * 8),
                probe_qualification=_qualification(),
                reference_artifact=ref,
                alpha=0.01,
            )


def test_reference_donor_roster_must_match_probe_exactly():
    ref = _reference([0.1] * 8)
    ref["donor_margins"].pop("D07")
    with pytest.raises(D.TeacherInformationDecisionError, match="donor"):
        D.adjudicate_g6_human_decision(
            probe_result=_probe([1.0] * 8),
            probe_qualification=_qualification(),
            reference_artifact=ref,
            alpha=0.01,
        )


def test_positive_raw_deltas_below_margin_cannot_pass():
    out = D.adjudicate_g6_human_decision(
        probe_result=_probe([0.5] * 8),
        probe_qualification=_qualification(),
        reference_artifact=_reference([0.75] * 8),
        alpha=0.01,
    )
    assert out["status"] == "FAIL"
    assert all(row["raw_delta"] > 0 for row in out["donor_contrasts"])
    assert all(row["margin_adjusted_delta"] < 0 for row in out["donor_contrasts"])


def test_teacher_advantage_beyond_margin_can_pass():
    out = D.adjudicate_g6_human_decision(
        probe_result=_probe([1.0] * 8),
        probe_qualification=_qualification(),
        reference_artifact=_reference([0.25] * 8),
        alpha=0.01,
    )
    assert out["status"] == "PASS"
    assert out["sign_test"]["pass"] is True
    assert all(row["margin_adjusted_delta"] > 0 for row in out["donor_contrasts"])


def test_underpowered_margin_adjusted_positive_result_is_not_estimable():
    out = D.adjudicate_g6_human_decision(
        probe_result=_probe([1.0] * 7),
        probe_qualification=_qualification(),
        reference_artifact=_reference([0.25] * 7),
        alpha=0.01,
    )
    assert out["status"] == "NOT_ESTIMABLE"


def test_nonestimable_probe_stays_nonestimable_without_false_failure():
    out = D.adjudicate_g6_human_decision(
        probe_result=_probe([], status="NOT_ESTIMABLE"),
        probe_qualification=_qualification(),
        reference_artifact=_reference([]),
        alpha=0.01,
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "PROBE_NOT_ESTIMABLE"


def test_authority_remains_off():
    out = D.adjudicate_g6_human_decision(
        probe_result=_probe([1.0] * 8),
        probe_qualification=_qualification(),
        reference_artifact=_reference([0.25] * 8),
        alpha=0.01,
    )
    assert all(value is False for value in out["authority"].values())
