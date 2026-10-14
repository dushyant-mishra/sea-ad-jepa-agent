from __future__ import annotations

import pytest

import scripts.v5.td_real_teacher_information_decision_v2 as D


def _probe(deltas, *, status="PASS", binding="a" * 64):
    return {
        "status": status,
        "input_binding_sha256": binding,
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


def _decision_qualification(ok=True):
    return {
        "schema": D.DECISION_QUAL_SCHEMA,
        "status": D.DECISION_QUAL_PASS if ok else "FAIL_KNOWN_TRUTH_G6_MARGIN_DECISION",
        "known_truth_power_qualified": bool(ok),
    }


def _reference(margins, *, binding="a" * 64):
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
        "input_binding_sha256": binding,
        "reference_receipt_sha256": "b" * 64,
    }


def _decide(*, probe, ref, probe_qual=None, decision_qual=None, alpha=0.01):
    return D.adjudicate_g6_human_decision(
        probe_result=probe,
        probe_qualification=_qualification() if probe_qual is None else probe_qual,
        decision_qualification=_decision_qualification() if decision_qual is None else decision_qual,
        reference_artifact=ref,
        alpha=alpha,
    )


def test_raw_positive_probe_is_not_enough_without_reference_margin():
    with pytest.raises(D.TeacherInformationDecisionError, match="reference"):
        _decide(probe=_probe([1.0] * 8), ref=None)


def test_probe_qualification_is_required_before_fail_semantics():
    q = _qualification()
    q["human_fail_semantics_qualified"] = False
    out = _decide(probe=_probe([-1.0] * 8, status="FAIL"), ref=_reference([0.1] * 8), probe_qual=q)
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "PROBE_REJECTION_POWER_NOT_QUALIFIED"


def test_margin_decision_known_truth_qualification_is_required_before_fail_or_pass():
    out = _decide(
        probe=_probe([1.0] * 8),
        ref=_reference([0.1] * 8),
        decision_qual=_decision_qualification(False),
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "MARGIN_DECISION_KNOWN_TRUTH_NOT_QUALIFIED"


def test_reference_metric_and_orientation_must_match_g6_delta():
    ref = _reference([0.1] * 8)
    ref["metric"] = "COSINE_DISTANCE"
    with pytest.raises(D.TeacherInformationDecisionError, match="metric"):
        _decide(probe=_probe([1.0] * 8), ref=ref)


def test_reference_must_be_frozen_qualified_and_deciding_disjoint():
    for key, value in (("frozen", False), ("qualified", False), ("deciding_namespace_disjoint", False)):
        ref = _reference([0.1] * 8)
        ref[key] = value
        with pytest.raises(D.TeacherInformationDecisionError):
            _decide(probe=_probe([1.0] * 8), ref=ref)


def test_reference_donor_roster_must_match_probe_exactly():
    ref = _reference([0.1] * 8)
    ref["donor_margins"].pop("D07")
    with pytest.raises(D.TeacherInformationDecisionError, match="donor"):
        _decide(probe=_probe([1.0] * 8), ref=ref)


def test_reference_input_binding_must_match_probe_exactly():
    with pytest.raises(D.TeacherInformationDecisionError, match="binding"):
        _decide(probe=_probe([1.0] * 8, binding="a" * 64), ref=_reference([0.25] * 8, binding="c" * 64))


def test_positive_raw_deltas_below_margin_cannot_pass():
    out = _decide(probe=_probe([0.5] * 8), ref=_reference([0.75] * 8))
    assert out["status"] == "FAIL"
    assert all(row["raw_delta"] > 0 for row in out["donor_contrasts"])
    assert all(row["margin_adjusted_delta"] < 0 for row in out["donor_contrasts"])


def test_teacher_advantage_beyond_margin_can_pass():
    out = _decide(probe=_probe([1.0] * 8), ref=_reference([0.25] * 8))
    assert out["status"] == "PASS"
    assert out["sign_test"]["pass"] is True
    assert out["input_binding_sha256"] == "a" * 64
    assert all(row["margin_adjusted_delta"] > 0 for row in out["donor_contrasts"])


def test_underpowered_margin_adjusted_positive_result_is_not_estimable():
    out = _decide(probe=_probe([1.0] * 7), ref=_reference([0.25] * 7))
    assert out["status"] == "NOT_ESTIMABLE"


def test_nonestimable_probe_stays_nonestimable_without_false_failure():
    out = _decide(probe=_probe([], status="NOT_ESTIMABLE"), ref=_reference([]))
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "PROBE_NOT_ESTIMABLE"


def test_known_truth_margin_decision_qualification_covers_positive_negative_margin_and_underpower():
    q = D.qualify_known_truth_g6_margin_decision()
    assert q["status"] == D.DECISION_QUAL_PASS
    assert q["worlds"] == {
        "ADVANTAGE_BEYOND_MARGIN": "PASS",
        "RAW_POSITIVE_BELOW_MARGIN": "FAIL",
        "NO_ADVANTAGE": "FAIL",
        "UNDERPOWERED_POSITIVE": "NOT_ESTIMABLE",
    }
    assert all(value is False for value in q["authority"].values())


def test_authority_remains_off():
    out = _decide(probe=_probe([1.0] * 8), ref=_reference([0.25] * 8))
    assert all(value is False for value in out["authority"].values())
