from __future__ import annotations

import importlib.util


def _load(name: str):
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required geometry V2 repair module missing: {name}"
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _producer(required_sources=("SEA_AD",)):
    return {
        "schema": "JEPA_TD_REAL_GEOMETRY_PRODUCER_RECEIPT_V2",
        "receipt_sha256": "1" * 64,
        "producer_code_sha256": "2" * 64,
        "producer_qualification_receipt_sha256": "3" * 64,
        "input_binding_sha256": "a" * 64,
        "metric": "PROJECTOR_RMS_PRINCIPAL_ANGLE_DISPLACEMENT",
        "orientation": "SMALLER_DISPLACEMENT_IS_MORE_STABLE",
        "null_semantics": "DONOR_PRESERVING_IDENTITY_SHUFFLE_LOWER_ADVERSE_BOUND",
        "heldout_used_for_fit": False,
        "leakage_guard_qualified": True,
        "eigengap_policy_sha256": "4" * 64,
        "null_namespace_sha256": "5" * 64,
        "required_sources": list(required_sources),
        "support_envelope_receipt_sha256": "6" * 64,
    }


def _support_contract(source="SEA_AD", donors=None, statuses=None):
    donors = donors or [f"D{i:02d}" for i in range(8)]
    statuses = statuses or {d: "ESTIMABLE" for d in donors}
    return {
        "schema": "JEPA_TD_REAL_GEOMETRY_SUPPORT_ENVELOPE_V2",
        "receipt_sha256": "6" * 64,
        "frozen_before_values": True,
        "source_donor_status": {source: {d: statuses[d] for d in donors}},
    }


def _reference(donors=None):
    donors = donors or [f"D{i:02d}" for i in range(8)]
    return {
        "schema": "JEPA_TD_REAL_GEOMETRY_REFERENCE_MARGIN_V2",
        "frozen": True,
        "qualified": True,
        "metric": "PROJECTOR_RMS_PRINCIPAL_ANGLE_DISPLACEMENT",
        "orientation": "SMALLER_DISPLACEMENT_IS_MORE_STABLE",
        "input_binding_sha256": "a" * 64,
        "reference_receipt_sha256": "7" * 64,
        "producer_receipt_sha256": "1" * 64,
        "support_envelope_receipt_sha256": "6" * 64,
        "refit_margins": {d: 0.05 for d in donors},
        "stability_margins": {d: 0.20 for d in donors},
    }


def _qual():
    return {
        "schema": "JEPA_TD_REAL_GEOMETRY_DECISION_QUALIFICATION_RECEIPT_V2",
        "status": "PASS_KNOWN_TRUTH_GEOMETRY_RECURRENCE_V2",
        "producer_code_sha256": "8" * 64,
        "qualification_worlds_sha256": "9" * 64,
        "receipt_sha256": "b" * 64,
        "human_semantics_qualified": True,
    }


def _rows(source="SEA_AD", observed=0.10, null_center=0.80, n_null=100, donors=None):
    donors = donors or [f"D{i:02d}" for i in range(8)]
    nulls = [null_center + (i - n_null/2) * 1e-4 for i in range(n_null)]
    return [{
        "source": source,
        "donor_id": donor,
        "estimability_status": "ESTIMABLE",
        "estimability_reason": None,
        "geometry_conditioning_status": "WELL_CONDITIONED",
        "observed_displacement": observed,
        "null_displacements": list(nulls),
        "null_unique_nonidentity_draws": n_null,
        "producer_receipt_sha256": "1" * 64,
        "input_binding_sha256": "a" * 64,
    } for donor in donors]


def test_extra_source_rows_are_rejected_not_silently_dropped():
    G = _load("scripts.v5.td_real_geometry_recurrence_engine_v2")
    rows = _rows() + _rows(source="HVS", donors=["H00"])
    out = G.adjudicate_geometry_recurrence_v2(
        rows=rows, required_sources=["SEA_AD"], producer_receipt=_producer(),
        support_envelope=_support_contract(), reference_artifact=_reference(),
        decision_qualification_receipt=_qual(),
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "UNDECLARED_SOURCE_ROWS_PRESENT"


def test_support_status_must_match_frozen_envelope_so_unstable_donor_cannot_be_relabelled_abstained():
    G = _load("scripts.v5.td_real_geometry_recurrence_engine_v2")
    rows = _rows()
    rows[-1]["estimability_status"] = "NOT_ESTIMABLE_STRUCTURAL_SUPPORT"
    rows[-1]["estimability_reason"] = "CALLER_DROPPED"
    rows[-1]["observed_displacement"] = None
    rows[-1]["null_displacements"] = None
    rows[-1]["null_unique_nonidentity_draws"] = 0
    out = G.adjudicate_geometry_recurrence_v2(
        rows=rows, required_sources=["SEA_AD"], producer_receipt=_producer(),
        support_envelope=_support_contract(), reference_artifact=_reference(),
        decision_qualification_receipt=_qual(),
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "ROW_SUPPORT_STATUS_MISMATCHES_FROZEN_ENVELOPE"


def test_one_donor_short_of_null_draws_does_not_hide_estimable_stability_fail():
    G = _load("scripts.v5.td_real_geometry_recurrence_engine_v2")
    rows = _rows(observed=0.50, null_center=0.90)
    rows[0]["null_displacements"] = rows[0]["null_displacements"][:99]
    rows[0]["null_unique_nonidentity_draws"] = 99
    out = G.adjudicate_geometry_recurrence_v2(
        rows=rows, required_sources=["SEA_AD"], producer_receipt=_producer(),
        support_envelope=_support_contract(), reference_artifact=_reference(),
        decision_qualification_receipt=_qual(),
    )
    assert out["status"] == "FAIL"
    assert out["source_details"]["SEA_AD"]["stability_status"] == "FAIL"
    assert out["source_details"]["SEA_AD"]["null_defeat_status"] == "NOT_ESTIMABLE"


def test_underresolved_nonidentity_null_is_not_biological_fail_when_stability_passes():
    G = _load("scripts.v5.td_real_geometry_recurrence_engine_v2")
    rows = _rows(observed=0.10)
    rows[0]["null_displacements"] = rows[0]["null_displacements"][:99]
    rows[0]["null_unique_nonidentity_draws"] = 99
    out = G.adjudicate_geometry_recurrence_v2(
        rows=rows, required_sources=["SEA_AD"], producer_receipt=_producer(),
        support_envelope=_support_contract(), reference_artifact=_reference(),
        decision_qualification_receipt=_qual(),
    )
    assert out["status"] == "NOT_ESTIMABLE"


def test_degenerate_geometry_cannot_carry_numeric_displacement():
    G = _load("scripts.v5.td_real_geometry_recurrence_engine_v2")
    rows = _rows()
    rows[0]["geometry_conditioning_status"] = "DEGENERATE_SUBSPACE"
    out = G.adjudicate_geometry_recurrence_v2(
        rows=rows, required_sources=["SEA_AD"], producer_receipt=_producer(),
        support_envelope=_support_contract(), reference_artifact=_reference(),
        decision_qualification_receipt=_qual(),
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "DEGENERATE_GEOMETRY_CARRIES_NUMERIC_DECISION_VALUES"


def test_producer_receipt_must_authenticate_leakage_and_fit_custody():
    G = _load("scripts.v5.td_real_geometry_recurrence_engine_v2")
    bad = _producer(); bad["heldout_used_for_fit"] = True
    out = G.adjudicate_geometry_recurrence_v2(
        rows=_rows(), required_sources=["SEA_AD"], producer_receipt=bad,
        support_envelope=_support_contract(), reference_artifact=_reference(),
        decision_qualification_receipt=_qual(),
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "GEOMETRY_PRODUCER_RECEIPT_NOT_QUALIFIED"


def test_alpha_is_frozen_and_authority_remains_closed():
    G = _load("scripts.v5.td_real_geometry_recurrence_engine_v2")
    assert G.FAMILY_ALPHA == 0.01
    out = G.adjudicate_geometry_recurrence_v2(
        rows=_rows(), required_sources=["SEA_AD"], producer_receipt=_producer(),
        support_envelope=_support_contract(), reference_artifact=_reference(),
        decision_qualification_receipt=_qual(),
    )
    assert all(v is False for v in out["authority"].values())
