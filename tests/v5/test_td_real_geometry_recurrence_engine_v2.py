from __future__ import annotations

import importlib
import importlib.util

import numpy as np
import pytest

import scripts.v5.td_real_geometry_recurrence_engine_v1 as V1


def _load():
    name = "scripts.v5.td_real_geometry_recurrence_engine_v2"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required repair module missing: {name}"
    return importlib.import_module(name)


def _nulls(center=0.8, n=100):
    return [center] * n


def _row(donor, *, source="SEA_AD", observed=0.1, n_null=100, status=V1.ESTIMABLE):
    return {
        "source": source,
        "donor_id": donor,
        "estimability_status": status,
        "estimability_reason": None if status == V1.ESTIMABLE else "STRUCTURAL",
        "observed_displacement": observed if status == V1.ESTIMABLE else None,
        "null_displacements": _nulls(n=n_null) if status == V1.ESTIMABLE else None,
        "null_semantics": V1.NULL_SEMANTICS,
        "null_producer_receipt_sha256": "c" * 64,
        "input_binding_sha256": "a" * 64,
    }


def _reference(rows, *, stability=0.2, refit=0.05):
    donors = [r["donor_id"] for r in rows if r["estimability_status"] == V1.ESTIMABLE]
    return {
        "schema": V1.REFERENCE_SCHEMA,
        "frozen": True,
        "qualified": True,
        "metric": V1.PROJECTOR_METRIC,
        "orientation": V1.ORIENTATION,
        "deciding_namespace_disjoint": True,
        "input_binding_sha256": "a" * 64,
        "reference_receipt_sha256": "b" * 64,
        "refit_margins": {d: refit for d in donors},
        "stability_margins": {d: stability for d in donors},
    }


def test_extra_source_rows_are_rejected_not_silently_dropped():
    G = _load()
    rows = [_row(f"S{i}") for i in range(8)] + [_row("H0", source="HVS")]
    with pytest.raises(G.GeometryRecurrenceV2Error, match="extra source"):
        G.adjudicate_geometry_mechanics_v2(
            rows=rows,
            metric=V1.PROJECTOR_METRIC,
            required_sources=["SEA_AD"],
            reference_artifact=_reference(rows),
            alpha=0.01,
        )


def test_underresolved_null_cannot_hide_estimable_stability_failure():
    G = _load()
    rows = [_row(f"D{i:02d}", observed=0.5, n_null=99 if i == 0 else 100) for i in range(8)]
    out = G.adjudicate_geometry_mechanics_v2(
        rows=rows,
        metric=V1.PROJECTOR_METRIC,
        required_sources=["SEA_AD"],
        reference_artifact=_reference(rows, stability=0.2),
        alpha=0.01,
    )
    assert out["source_details"]["SEA_AD"]["null_defeat_status"] == "NOT_ESTIMABLE"
    assert out["source_details"]["SEA_AD"]["stability_status"] == "FAIL"
    assert out["source_status"]["SEA_AD"] == "FAIL"
    assert out["status"] == "FAIL"


def test_underresolved_null_with_stable_geometry_remains_not_estimable_not_pass():
    G = _load()
    rows = [_row(f"D{i:02d}", observed=0.1, n_null=99 if i == 0 else 100) for i in range(8)]
    out = G.adjudicate_geometry_mechanics_v2(
        rows=rows,
        metric=V1.PROJECTOR_METRIC,
        required_sources=["SEA_AD"],
        reference_artifact=_reference(rows, stability=0.2),
        alpha=0.01,
    )
    assert out["source_details"]["SEA_AD"]["stability_status"] == "PASS"
    assert out["source_status"]["SEA_AD"] == "NOT_ESTIMABLE"
    assert out["status"] == "NOT_ESTIMABLE"


def test_nonorthogonal_forged_alignment_is_rejected():
    G = _load()
    transform = V1.fit_train_only_procrustes(
        train_a=[[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]],
        train_b=[[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]],
        train_unit_ids=["A", "B", "C"],
        heldout_unit_ids=["H"],
    )
    transform["rotation"] = [[2.0, 0.0], [0.0, 1.0]]
    with pytest.raises(G.GeometryRecurrenceV2Error, match="orthogonal"):
        G.aligned_rms_displacement_v2([[0.0, 0.0]], [[0.0, 0.0]], transform)


def test_typed_producer_receipt_cannot_authorize_human_geometry_execution():
    G = _load()
    out = G.human_execution_readiness(
        producer_receipt={
            "schema": "JEPA_TD_REAL_GEOMETRY_PRODUCER_RECEIPT_V1",
            "qualified": True,
            "producer_code_sha256": "1" * 64,
            "support_receipt_sha256": "2" * 64,
            "alignment_receipt_sha256": "3" * 64,
            "null_receipt_sha256": "4" * 64,
        }
    )
    assert out["status"] == "BLOCKED_GEOMETRY_PRODUCER_NOT_INDEPENDENTLY_QUALIFIED"
    assert out["human_geometry_adjudication_authorized"] is False


def test_support_abstention_labels_have_no_human_authority_without_producer():
    G = _load()
    out = G.human_execution_readiness(producer_receipt={})
    assert out["caller_support_labels_have_human_authority"] is False
    assert out["caller_displacements_have_human_authority"] is False


def test_geometry_v2_preserves_rotation_invariant_projector_metric():
    G = _load()
    a = np.eye(4)[:, :2]
    q = np.asarray([[0.0, -1.0], [1.0, 0.0]])
    assert G.projector_rms_displacement(a, a @ q) < 1e-10


def test_geometry_v2_authority_remains_closed():
    G = _load()
    out = G.human_execution_readiness(producer_receipt={})
    assert all(value is False for value in out["authority"].values())
