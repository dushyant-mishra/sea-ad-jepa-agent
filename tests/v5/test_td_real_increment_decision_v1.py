from __future__ import annotations

import pytest

import scripts.v5.td_real_increment_decision_v1 as I

BINDING = "a" * 64


def _rows(donors=8, source="SEA_AD", endpoint="PRIMARY", scores=None, support="SUPPORTED"):
    scores = scores or {"C1": 0.2, "C2": 0.8, "C3": 0.3, "C6": 0.9, "C4": 1.0}
    return [
        {
            "source": source,
            "endpoint": endpoint,
            "donor_id": f"D{i:02d}",
            "scores": dict(scores),
            "support_state": support,
            "input_binding_sha256": BINDING,
        }
        for i in range(donors)
    ]


def _ref(rows, margin=0.1, binding=BINDING):
    return {
        "schema": I.REFERENCE_SCHEMA,
        "qualified": True,
        "metric": I.METRIC,
        "orientation": I.ORIENTATION,
        "input_binding_sha256": binding,
        "reference_receipt_sha256": "b" * 64,
        "margins": {
            f'{r["source"]}::{r["endpoint"]}::{r["donor_id"]}': margin
            for r in rows if r["support_state"] == "SUPPORTED"
        },
    }


def _qual(ok=True):
    return {
        "schema": I.QUAL_SCHEMA,
        "status": I.QUAL_PASS if ok else "FAIL_KNOWN_TRUTH_INCREMENT",
        "known_truth_power_qualified": bool(ok),
    }


def test_r4_is_c2_over_independently_qualified_c1():
    rows = _rows()
    out = I.adjudicate_increment(
        gate="R4", rows=rows, required_strata=[("SEA_AD", "PRIMARY")],
        prerequisite_statuses={"C1": "PASS"}, reference_artifact=_ref(rows),
        decision_qualification=_qual(), alpha=0.01,
    )
    assert out["status"] == "PASS"
    assert out["comparators"] == ["C1"]


def test_c6_must_beat_c1_and_c3_separately_not_only_a_selected_constituent():
    rows = _rows(scores={"C1": 0.2, "C2": 0.8, "C3": 0.95, "C6": 0.9, "C4": 1.0})
    out = I.adjudicate_increment(
        gate="C6", rows=rows, required_strata=[("SEA_AD", "PRIMARY")],
        prerequisite_statuses={"C1": "PASS", "C3": "PASS"},
        reference_artifact=_ref(rows, margin=0.01), decision_qualification=_qual(), alpha=0.01,
    )
    assert out["status"] == "FAIL"
    assert out["comparator_statuses"]["C1"] == "PASS"
    assert out["comparator_statuses"]["C3"] == "FAIL"


def test_c4_has_only_c6_comparator_and_c6_must_already_pass():
    rows = _rows()
    with pytest.raises(I.IncrementDecisionError, match="C6"):
        I.adjudicate_increment(
            gate="C4", rows=rows, required_strata=[("SEA_AD", "PRIMARY")],
            prerequisite_statuses={"C1": "PASS", "C2": "PASS", "C3": "PASS", "C6": "FAIL"},
            reference_artifact=_ref(rows), decision_qualification=_qual(), alpha=0.01,
        )
    out = I.adjudicate_increment(
        gate="C4", rows=rows, required_strata=[("SEA_AD", "PRIMARY")],
        prerequisite_statuses={"C6": "PASS"}, reference_artifact=_ref(rows),
        decision_qualification=_qual(), alpha=0.01,
    )
    assert out["comparators"] == ["C6"]


def test_direction_without_noise_relative_margin_fails():
    rows = _rows(scores={"C1": 0.2, "C2": 0.25, "C3": 0.2, "C6": 0.3, "C4": 0.4})
    out = I.adjudicate_increment(
        gate="R4", rows=rows, required_strata=[("SEA_AD", "PRIMARY")],
        prerequisite_statuses={"C1": "PASS"}, reference_artifact=_ref(rows, margin=0.1),
        decision_qualification=_qual(), alpha=0.01,
    )
    assert out["status"] == "FAIL"


def test_required_source_strata_are_noncompensating():
    rows = _rows(source="SEA_AD") + _rows(source="NPH52", scores={"C1": 0.8, "C2": 0.7, "C3": 0.2, "C6": 0.9, "C4": 1.0})
    out = I.adjudicate_increment(
        gate="R4", rows=rows, required_strata=[("SEA_AD", "PRIMARY"), ("NPH52", "PRIMARY")],
        prerequisite_statuses={"C1": "PASS"}, reference_artifact=_ref(rows, margin=0.01),
        decision_qualification=_qual(), alpha=0.01,
    )
    assert out["status"] == "FAIL"
    assert out["stratum_status"]["SEA_AD::PRIMARY"] == "PASS"
    assert out["stratum_status"]["NPH52::PRIMARY"] == "FAIL"


def test_support_loss_is_not_estimable_not_zero_filled():
    rows = _rows()
    rows[0] = {**rows[0], "support_state": "UNSUPPORTED_STRUCTURAL"}
    out = I.adjudicate_increment(
        gate="R4", rows=rows, required_strata=[("SEA_AD", "PRIMARY")],
        prerequisite_statuses={"C1": "PASS"}, reference_artifact=_ref(rows),
        decision_qualification=_qual(), alpha=0.01,
    )
    assert out["status"] == "NOT_ESTIMABLE"


def test_reference_is_bound_to_exact_realization_and_unit():
    rows = _rows()
    with pytest.raises(I.IncrementDecisionError, match="binding"):
        I.adjudicate_increment(
            gate="R4", rows=rows, required_strata=[("SEA_AD", "PRIMARY")],
            prerequisite_statuses={"C1": "PASS"}, reference_artifact=_ref(rows, binding="c" * 64),
            decision_qualification=_qual(), alpha=0.01,
        )
    ref = _ref(rows)
    ref["margins"].pop("SEA_AD::PRIMARY::D00")
    with pytest.raises(I.IncrementDecisionError, match="margin"):
        I.adjudicate_increment(
            gate="R4", rows=rows, required_strata=[("SEA_AD", "PRIMARY")],
            prerequisite_statuses={"C1": "PASS"}, reference_artifact=ref,
            decision_qualification=_qual(), alpha=0.01,
        )


def test_unqualified_known_truth_cannot_issue_human_fail():
    rows = _rows(scores={"C1": 0.9, "C2": 0.1, "C3": 0.2, "C6": 0.3, "C4": 0.4})
    out = I.adjudicate_increment(
        gate="R4", rows=rows, required_strata=[("SEA_AD", "PRIMARY")],
        prerequisite_statuses={"C1": "PASS"}, reference_artifact=_ref(rows),
        decision_qualification=_qual(False), alpha=0.01,
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "DECISION_KNOWN_TRUTH_NOT_QUALIFIED"


def test_known_truth_qualification_covers_each_gate_and_abstention():
    q = I.qualify_known_truth_increment_decision()
    assert q["status"] == I.QUAL_PASS
    assert q["worlds"]["R4_TRUE_INCREMENT"] == "PASS"
    assert q["worlds"]["C6_BEATS_C1_NOT_C3"] == "FAIL"
    assert q["worlds"]["C4_WITHOUT_QUALIFIED_C6"] == "NOT_ESTIMABLE"
    assert q["worlds"]["SUPPORT_LOSS"] == "NOT_ESTIMABLE"
    assert all(v is False for v in q["authority"].values())
