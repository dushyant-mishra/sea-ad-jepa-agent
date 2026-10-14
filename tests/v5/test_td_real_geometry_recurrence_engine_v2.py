from __future__ import annotations

import importlib.util

import pytest


def _load():
    name = "scripts.v5.td_real_geometry_recurrence_engine_v2"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required repair module missing: {name}"
    import scripts.v5.td_real_geometry_recurrence_engine_v2 as G
    return G


def _row(donor, *, source="SEA_AD", observed=0.1, null_n=100, support="ESTIMABLE"):
    return {
        "source": source,
        "donor_id": donor,
        "estimability_status": support,
        "estimability_reason": None if support == "ESTIMABLE" else "STRUCTURAL_SUPPORT_ABSENT",
        "observed_displacement": observed if support == "ESTIMABLE" else None,
        "null_displacements": ([1.0] * null_n) if support == "ESTIMABLE" else None,
        "null_semantics": "DONOR_PRESERVING_IDENTITY_SHUFFLE_LOWER_ADVERSE_BOUND",
        "null_producer_receipt_sha256": "a" * 64,
        "input_binding_sha256": "b" * 64,
    }


def _reference(donors, *, refit=0.1, stability=0.5):
    return {
        "schema": "JEPA_TD_REAL_GEOMETRY_REFERENCE_MARGIN_V1",
        "frozen": True,
        "qualified": True,
        "metric": "PROJECTOR_RMS_PRINCIPAL_ANGLE_DISPLACEMENT",
        "orientation": "SMALLER_DISPLACEMENT_IS_MORE_STABLE",
        "deciding_namespace_disjoint": True,
        "input_binding_sha256": "b" * 64,
        "reference_receipt_sha256": "c" * 64,
        "refit_margins": {d: refit for d in donors},
        "stability_margins": {d: stability for d in donors},
    }


def test_rows_from_unrequested_sources_are_rejected_not_silently_dropped():
    G = _load()
    donors = [f"D{i:02d}" for i in range(8)]
    rows = [_row(d) for d in donors] + [_row("H00", source="HVS")]
    with pytest.raises(G.GeometryRecurrenceV2Error, match="extra source"):
        G.adjudicate_geometry_v2(
            rows=rows,
            required_sources=["SEA_AD"],
            reference_artifact=_reference(donors + ["H00"]),
            producer_qualification_receipt_sha256=None,
        )


def test_stability_failure_is_not_hidden_by_one_donor_underresolved_null():
    G = _load()
    donors = [f"D{i:02d}" for i in range(8)]
    rows = [_row(d, observed=1.0, null_n=(99 if i == 0 else 100)) for i, d in enumerate(donors)]
    out = G.adjudicate_geometry_v2(
        rows=rows,
        required_sources=["SEA_AD"],
        reference_artifact=_reference(donors, refit=0.1, stability=0.1),
        producer_qualification_receipt_sha256=None,
    )
    assert out["source_diagnostics"]["SEA_AD"]["stability_status"] == "FAIL"
    assert out["source_diagnostics"]["SEA_AD"]["null_status"] == "NOT_ESTIMABLE"
    assert out["diagnostic_status"] == "FAIL"
    assert out["status"] == "NOT_ESTIMABLE"


def test_nonorthogonal_alignment_transform_is_rejected():
    G = _load()
    transform = {
        "schema": "JEPA_TD_TRAIN_ONLY_ORTHOGONAL_PROCRUSTES_V1",
        "n_features": 2,
        "mean_a": [0.0, 0.0],
        "mean_b": [0.0, 0.0],
        "rotation": [[2.0, 0.0], [0.0, 1.0]],
        "fit_unit_count": 2,
        "heldout_unit_count": 1,
        "heldout_used_for_fit": False,
    }
    with pytest.raises(G.GeometryRecurrenceV2Error, match="orthogonal"):
        G.validated_aligned_rms_displacement(
            [[0.0, 0.0], [1.0, 0.0]],
            [[0.0, 0.0], [1.0, 0.0]],
            transform,
        )


def test_caller_typed_producer_receipt_cannot_authorize_human_geometry_verdict():
    G = _load()
    donors = [f"D{i:02d}" for i in range(8)]
    rows = [_row(d, observed=0.1) for d in donors]
    out = G.adjudicate_geometry_v2(
        rows=rows,
        required_sources=["SEA_AD"],
        reference_artifact=_reference(donors, refit=0.1, stability=0.5),
        producer_qualification_receipt_sha256="f" * 64,
    )
    assert out["diagnostic_status"] == "PASS"
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "SEALED_GEOMETRY_PRODUCER_QUALIFICATION_NOT_FROZEN"
    assert out["human_pass_fail_authorized"] is False


def test_alpha_is_frozen_not_caller_selected():
    G = _load()
    donors = [f"D{i:02d}" for i in range(8)]
    with pytest.raises(G.GeometryRecurrenceV2Error, match="alpha"):
        G.adjudicate_geometry_v2(
            rows=[_row(d) for d in donors],
            required_sources=["SEA_AD"],
            reference_artifact=_reference(donors),
            producer_qualification_receipt_sha256=None,
            alpha=0.05,
        )


def test_nonfinite_deciding_geometry_is_numerical_failure_not_biological_fail():
    G = _load()
    donors = [f"D{i:02d}" for i in range(8)]
    rows = [_row(d) for d in donors]
    rows[3]["observed_displacement"] = float("nan")
    out = G.adjudicate_geometry_v2(
        rows=rows,
        required_sources=["SEA_AD"],
        reference_artifact=_reference(donors),
        producer_qualification_receipt_sha256=None,
    )
    assert out["status"] == "NUMERICAL_FAILURE"
    assert out["human_pass_fail_authorized"] is False


def test_authority_remains_closed():
    G = _load()
    donors = [f"D{i:02d}" for i in range(8)]
    out = G.adjudicate_geometry_v2(
        rows=[_row(d) for d in donors],
        required_sources=["SEA_AD"],
        reference_artifact=_reference(donors),
        producer_qualification_receipt_sha256=None,
    )
    assert all(v is False for v in out["authority"].values())
