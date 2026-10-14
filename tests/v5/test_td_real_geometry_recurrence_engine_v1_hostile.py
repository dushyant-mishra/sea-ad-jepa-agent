from __future__ import annotations

import pytest

import scripts.v5.td_real_geometry_recurrence_engine_v1 as G


BINDING = "a" * 64
NULL_RECEIPT = "c" * 64


def _qual():
    return {"schema": G.QUAL_SCHEMA, "status": G.QUAL_PASS, "known_truth_power_qualified": True}


def _row(donor, *, source="SEA_AD", estimability="ESTIMABLE", reason=None):
    return {
        "source": source,
        "donor_id": donor,
        "estimability_status": estimability,
        "estimability_reason": reason,
        "observed_displacement": 0.10 if estimability == "ESTIMABLE" else None,
        "null_displacements": [0.78, 0.80, 0.82] if estimability == "ESTIMABLE" else None,
        "null_semantics": G.NULL_SEMANTICS,
        "null_producer_receipt_sha256": NULL_RECEIPT,
        "input_binding_sha256": BINDING,
    }


def _reference(rows):
    estimable = [r["donor_id"] for r in rows if r["estimability_status"] == "ESTIMABLE"]
    return {
        "schema": G.REFERENCE_SCHEMA,
        "frozen": True,
        "qualified": True,
        "metric": G.PROJECTOR_METRIC,
        "orientation": G.ORIENTATION,
        "deciding_namespace_disjoint": True,
        "input_binding_sha256": BINDING,
        "reference_receipt_sha256": "b" * 64,
        "refit_margins": {d: 0.05 for d in estimable},
        "stability_margins": {d: 0.20 for d in estimable},
    }


def test_structurally_unsupported_donors_abstain_and_do_not_become_geometry_failure():
    rows = [_row(f"D{i:02d}") for i in range(7)]
    rows += [
        _row("D07", estimability="NOT_ESTIMABLE_STRUCTURAL_SUPPORT", reason="REQUIRED_GEOMETRY_NOT_PHYSICALLY_SUPPORTED"),
        _row("D08", estimability="NOT_ESTIMABLE_COLLISION_UNRESOLVED", reason="REQUIRED_ADDRESS_COLLISION_UNRESOLVED"),
    ]
    out = G.adjudicate_geometry_recurrence(
        rows=rows,
        metric=G.PROJECTOR_METRIC,
        required_sources=["SEA_AD"],
        decision_qualification=_qual(),
        reference_artifact=_reference(rows),
        alpha=0.01,
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["source_status"]["SEA_AD"] == "NOT_ESTIMABLE"
    assert out["source_details"]["SEA_AD"]["estimable_donor_count"] == 7
    assert out["source_details"]["SEA_AD"]["abstained_donor_count"] == 2
    assert out["source_details"]["SEA_AD"]["failed_biology"] is False


def test_unresolved_donor_is_not_allowed_to_carry_fake_numeric_geometry():
    rows = [_row(f"D{i:02d}") for i in range(8)]
    bad = _row("D08", estimability="NOT_ESTIMABLE_STRUCTURAL_SUPPORT", reason="NO_SUPPORT")
    bad["observed_displacement"] = 0.0
    with pytest.raises(G.GeometryRecurrenceError, match="non-estimable"):
        G.adjudicate_geometry_recurrence(
            rows=rows + [bad], metric=G.PROJECTOR_METRIC, required_sources=["SEA_AD"],
            decision_qualification=_qual(), reference_artifact=_reference(rows), alpha=0.01,
        )


def test_null_semantics_are_frozen_and_null_receipt_is_required():
    rows = [_row(f"D{i:02d}") for i in range(8)]
    rows[0]["null_semantics"] = "GLOBAL_SHUFFLE"
    with pytest.raises(G.GeometryRecurrenceError, match="null semantics"):
        G.adjudicate_geometry_recurrence(
            rows=rows, metric=G.PROJECTOR_METRIC, required_sources=["SEA_AD"],
            decision_qualification=_qual(), reference_artifact=_reference(rows), alpha=0.01,
        )


def test_all_rows_must_bind_same_frozen_null_producer_receipt():
    rows = [_row(f"D{i:02d}") for i in range(8)]
    rows[-1]["null_producer_receipt_sha256"] = "d" * 64
    with pytest.raises(G.GeometryRecurrenceError, match="null producer"):
        G.adjudicate_geometry_recurrence(
            rows=rows, metric=G.PROJECTOR_METRIC, required_sources=["SEA_AD"],
            decision_qualification=_qual(), reference_artifact=_reference(rows), alpha=0.01,
        )


def test_reference_roster_tracks_only_estimable_donors_not_abstained_donors():
    rows = [_row(f"D{i:02d}") for i in range(8)] + [
        _row("D08", estimability="NOT_ESTIMABLE_STRUCTURAL_SUPPORT", reason="NO_SUPPORT")
    ]
    ref = _reference(rows)
    ref["refit_margins"]["D08"] = 0.05
    ref["stability_margins"]["D08"] = 0.20
    with pytest.raises(G.GeometryRecurrenceError, match="estimable donor roster"):
        G.adjudicate_geometry_recurrence(
            rows=rows, metric=G.PROJECTOR_METRIC, required_sources=["SEA_AD"],
            decision_qualification=_qual(), reference_artifact=ref, alpha=0.01,
        )
