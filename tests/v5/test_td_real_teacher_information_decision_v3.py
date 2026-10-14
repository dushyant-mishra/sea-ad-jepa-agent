from __future__ import annotations

import importlib
import importlib.util

import pytest


def _load():
    name = "scripts.v5.td_real_teacher_information_decision_v3"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required repair module missing: {name}"
    return importlib.import_module(name)


def _reference(**updates):
    G = _load()
    item = {
        "schema": G.REFERENCE_SCHEMA,
        "frozen": True,
        "qualified": True,
        "metric": G.METRIC,
        "orientation": G.ORIENTATION,
        "reference_kind": "MAX_U_REFIT_U_MEASUREMENT",
        "input_binding_sha256": "a" * 64,
        "reference_receipt_sha256": "b" * 64,
        "producer_code_sha256": "c" * 64,
        "measurement_component_present": True,
        "measurement_component_non_degenerate": True,
        "donor_margins": {"D00": 0.2, "D01": 0.3},
    }
    item.update(updates)
    return item


def test_literal_v2_qualification_tokens_do_not_authorize_v3_human_decision():
    G = _load()
    out = G.human_execution_readiness(
        probe_qualification={
            "schema": "JEPA_TD_REAL_G6_TEACHER_INFORMATION_PROBE_QUALIFICATION_V1",
            "status": "PASS_KNOWN_TRUTH_G6_PROBE_QUALIFICATION",
            "human_fail_semantics_qualified": True,
        },
        decision_qualification={
            "schema": "JEPA_TD_REAL_G6_MARGIN_DECISION_QUALIFICATION_V2",
            "status": "PASS_KNOWN_TRUTH_G6_MARGIN_DECISION",
            "known_truth_power_qualified": True,
        },
        reference_artifact=_reference(),
    )
    assert out["status"] == "BLOCKED_G6_PRODUCED_QUALIFICATION_RECEIPT_REQUIRED"
    assert out["human_g6_adjudication_authorized"] is False


def test_zero_margin_is_not_a_substantive_margin_even_if_reference_is_typed_qualified():
    G = _load()
    ref = _reference(
        measurement_component_present=False,
        measurement_component_non_degenerate=False,
        reference_kind="U_REFIT",
        donor_margins={"D00": 0.0, "D01": 0.0},
    )
    out = G.validate_reference_for_future_human_use(ref)
    assert out["status"] == "NOT_ESTIMABLE_SUBSTANTIVE_MARGIN"
    assert out["human_use_authorized"] is False
    assert out["reason"] == "DEGENERATE_OR_ABSENT_MEASUREMENT_MARGIN"


def test_every_donor_substantive_margin_must_be_strictly_positive():
    G = _load()
    ref = _reference(donor_margins={"D00": 0.2, "D01": 0.0})
    out = G.validate_reference_for_future_human_use(ref)
    assert out["status"] == "NOT_ESTIMABLE_SUBSTANTIVE_MARGIN"
    assert out["reason"] == "NONPOSITIVE_DONOR_MARGIN"


def test_refit_only_reference_cannot_substitute_for_measurement_margin():
    G = _load()
    ref = _reference(reference_kind="U_REFIT")
    out = G.validate_reference_for_future_human_use(ref)
    assert out["status"] == "NOT_ESTIMABLE_SUBSTANTIVE_MARGIN"
    assert out["reason"] == "MEASUREMENT_COMPONENT_REQUIRED"


def test_future_reference_must_be_exactly_bound_and_produced_not_boolean_only():
    G = _load()
    for field in ("input_binding_sha256", "reference_receipt_sha256", "producer_code_sha256"):
        ref = _reference(**{field: "not-a-hash"})
        with pytest.raises(G.TeacherInformationDecisionV3Error, match=field.split("_")[0]):
            G.validate_reference_for_future_human_use(ref)


def test_non_degenerate_measurement_reference_can_be_reference_ready_but_not_human_decision_ready():
    G = _load()
    out = G.validate_reference_for_future_human_use(_reference())
    assert out["status"] == "REFERENCE_MECHANICALLY_READY__HUMAN_DECISION_STILL_BLOCKED"
    assert out["human_use_authorized"] is False


def test_g6_v3_explicitly_preserves_raw_metric_pending_separate_scale_contract():
    G = _load()
    assert G.METRIC == "DONOR_BALANCED_OUTER_MSE_DELTA"
    assert G.METRIC_SCALE_STATUS == "RAW_TARGET_UNITS__SCALE_SENSITIVITY_OPEN__NO_SILENT_METRIC_REWRITE"


def test_g6_v3_authority_remains_closed():
    G = _load()
    out = G.human_execution_readiness(
        probe_qualification={},
        decision_qualification={},
        reference_artifact=_reference(),
    )
    assert all(value is False for value in out["authority"].values())
