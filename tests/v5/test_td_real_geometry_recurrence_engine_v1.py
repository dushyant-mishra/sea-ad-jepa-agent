from __future__ import annotations

import math

import numpy as np
import pytest

import scripts.v5.td_real_geometry_recurrence_engine_v1 as G


BINDING = "a" * 64


def _qual(ok=True):
    return {
        "schema": G.QUAL_SCHEMA,
        "status": G.QUAL_PASS if ok else "FAIL_KNOWN_TRUTH_GEOMETRY_RECURRENCE",
        "known_truth_power_qualified": bool(ok),
    }


def _rows(*, sources=("SEA_AD",), observed=0.10, null=0.80, n_donors=8, binding=BINDING):
    rows = []
    for source in sources:
        for i in range(n_donors):
            rows.append(
                {
                    "source": source,
                    "donor_id": f"{source}_D{i:02d}",
                    "observed_displacement": float(observed),
                    "null_displacements": [float(null - 0.02), float(null), float(null + 0.02)],
                    "input_binding_sha256": binding,
                }
            )
    return rows


def _reference(rows, *, refit=0.05, stability=0.20, binding=BINDING, metric=G.PROJECTOR_METRIC):
    donors = [r["donor_id"] for r in rows]
    return {
        "schema": G.REFERENCE_SCHEMA,
        "frozen": True,
        "qualified": True,
        "metric": metric,
        "orientation": G.ORIENTATION,
        "deciding_namespace_disjoint": True,
        "input_binding_sha256": binding,
        "reference_receipt_sha256": "b" * 64,
        "refit_margins": {d: float(refit) for d in donors},
        "stability_margins": {d: float(stability) for d in donors},
    }


def test_projector_displacement_is_rotation_invariant_within_same_subspace():
    a = np.eye(4)[:, :2]
    theta = math.pi / 3
    q = np.asarray([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])
    b = a @ q
    assert G.projector_rms_displacement(a, b) == pytest.approx(0.0, abs=1e-12)


def test_projector_displacement_is_maximal_for_orthogonal_equal_rank_subspaces():
    a = np.eye(4)[:, :2]
    b = np.eye(4)[:, 2:]
    assert G.projector_rms_displacement(a, b) == pytest.approx(1.0, abs=1e-12)


def test_procrustes_fit_uses_train_units_only_and_generalizes_to_heldout_rotation():
    train_a = np.asarray([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [-1.0, 1.0]])
    held_a = np.asarray([[2.0, 1.0], [-1.0, 2.0]])
    theta = math.pi / 4
    q = np.asarray([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])
    train_b = train_a @ q
    held_b = held_a @ q
    transform = G.fit_train_only_procrustes(
        train_a=train_a,
        train_b=train_b,
        train_unit_ids=["T0", "T1", "T2", "T3"],
        heldout_unit_ids=["H0", "H1"],
    )
    assert G.aligned_rms_displacement(held_a, held_b, transform) == pytest.approx(0.0, abs=1e-12)


def test_procrustes_rejects_alignment_leakage_from_heldout_units():
    with pytest.raises(G.GeometryRecurrenceError, match="heldout"):
        G.fit_train_only_procrustes(
            train_a=np.eye(2),
            train_b=np.eye(2),
            train_unit_ids=["X", "Y"],
            heldout_unit_ids=["Y", "Z"],
        )


def test_recurrent_and_stable_geometry_passes_in_each_required_source():
    rows = _rows(sources=("SEA_AD", "NPH52"))
    out = G.adjudicate_geometry_recurrence(
        rows=rows,
        metric=G.PROJECTOR_METRIC,
        required_sources=["SEA_AD", "NPH52"],
        decision_qualification=_qual(),
        reference_artifact=_reference(rows),
        alpha=0.01,
    )
    assert out["status"] == "PASS"
    assert set(out["source_status"]) == {"SEA_AD", "NPH52"}
    assert all(v == "PASS" for v in out["source_status"].values())


def test_null_defeat_cannot_rescue_geometry_that_exceeds_stability_margin():
    rows = _rows(observed=0.50, null=0.90)
    out = G.adjudicate_geometry_recurrence(
        rows=rows,
        metric=G.PROJECTOR_METRIC,
        required_sources=["SEA_AD"],
        decision_qualification=_qual(),
        reference_artifact=_reference(rows, refit=0.05, stability=0.20),
        alpha=0.01,
    )
    assert out["status"] == "FAIL"
    assert out["source_details"]["SEA_AD"]["null_defeat_status"] == "PASS"
    assert out["source_details"]["SEA_AD"]["stability_status"] == "FAIL"


def test_stability_cannot_rescue_geometry_that_does_not_defeat_adverse_null():
    rows = _rows(observed=0.15, null=0.18)
    out = G.adjudicate_geometry_recurrence(
        rows=rows,
        metric=G.PROJECTOR_METRIC,
        required_sources=["SEA_AD"],
        decision_qualification=_qual(),
        reference_artifact=_reference(rows, refit=0.10, stability=0.20),
        alpha=0.01,
    )
    assert out["status"] == "FAIL"
    assert out["source_details"]["SEA_AD"]["null_defeat_status"] == "FAIL"
    assert out["source_details"]["SEA_AD"]["stability_status"] == "PASS"


def test_underpowered_required_source_is_not_estimable_and_cannot_be_averaged_away():
    rows = _rows(sources=("SEA_AD",), n_donors=8) + _rows(sources=("HVS",), n_donors=7)
    out = G.adjudicate_geometry_recurrence(
        rows=rows,
        metric=G.PROJECTOR_METRIC,
        required_sources=["SEA_AD", "HVS"],
        decision_qualification=_qual(),
        reference_artifact=_reference(rows),
        alpha=0.01,
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["source_status"]["SEA_AD"] == "PASS"
    assert out["source_status"]["HVS"] == "NOT_ESTIMABLE"


def test_reference_binding_must_match_exact_deciding_realization():
    rows = _rows()
    with pytest.raises(G.GeometryRecurrenceError, match="binding"):
        G.adjudicate_geometry_recurrence(
            rows=rows,
            metric=G.PROJECTOR_METRIC,
            required_sources=["SEA_AD"],
            decision_qualification=_qual(),
            reference_artifact=_reference(rows, binding="c" * 64),
            alpha=0.01,
        )


def test_unqualified_known_truth_decision_cannot_issue_human_fail():
    rows = _rows(observed=0.9, null=0.2)
    out = G.adjudicate_geometry_recurrence(
        rows=rows,
        metric=G.PROJECTOR_METRIC,
        required_sources=["SEA_AD"],
        decision_qualification=_qual(False),
        reference_artifact=_reference(rows),
        alpha=0.01,
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "DECISION_KNOWN_TRUTH_NOT_QUALIFIED"


def test_known_truth_qualification_covers_rotation_instability_null_failure_and_underpower():
    q = G.qualify_known_truth_geometry_recurrence()
    assert q["status"] == G.QUAL_PASS
    assert q["worlds"] == {
        "ROTATED_SAME_SUBSPACE": "PASS",
        "ORTHOGONAL_SUBSPACE": "PASS",
        "RECURRENT_STABLE": "PASS",
        "NULL_SHORTCUT": "FAIL",
        "UNSTABLE_DESPITE_NULL_DEFEAT": "FAIL",
        "UNDERPOWERED_SOURCE": "NOT_ESTIMABLE",
    }
    assert all(v is False for v in q["authority"].values())
