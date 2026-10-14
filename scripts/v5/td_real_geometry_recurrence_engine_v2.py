"""Repair layer for real-TD G9/S1/S2 geometry mechanics.

V1 correctly qualified several invariant-geometry and adverse-null mechanics, but
hostile real-data review found that human execution could still be steered by
caller-provided displacements/support labels/receipt strings. It also found two
mechanical defects: rows from extra sources were silently ignored and an
underresolved null caused an early source-level NOT_ESTIMABLE before an otherwise
estimable stability FAIL was evaluated.

V2 repairs those mechanics and fail-closes human execution until a separate
producer owns displacement, support, alignment and null generation.
"""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from scripts.v5 import td_real_geometry_recurrence_engine_v1 as V1
from scripts.v5 import td_target_tournament_precision as P


class GeometryRecurrenceV2Error(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_GEOMETRY_RECURRENCE_DECISION_V2"
NO_AUTHORITY = dict(V1.NO_AUTHORITY)
projector_rms_displacement = V1.projector_rms_displacement


def aligned_rms_displacement_v2(first, second, transform: Mapping) -> float:
    if not isinstance(transform, Mapping):
        raise GeometryRecurrenceV2Error("alignment transform must be a mapping")
    try:
        rotation = np.asarray(transform["rotation"], dtype=float)
    except Exception as exc:
        raise GeometryRecurrenceV2Error("alignment rotation must be finite matrix-like") from exc
    if rotation.ndim != 2 or rotation.shape[0] != rotation.shape[1] or not np.isfinite(rotation).all():
        raise GeometryRecurrenceV2Error("alignment rotation must be a finite square matrix")
    identity = np.eye(rotation.shape[0], dtype=float)
    if not np.allclose(rotation.T @ rotation, identity, rtol=1e-10, atol=1e-12):
        raise GeometryRecurrenceV2Error("alignment rotation must be orthogonal")
    return V1.aligned_rms_displacement(first, second, transform)


def _component(gate) -> str:
    if not gate["resolution_estimable"]:
        return "NOT_ESTIMABLE"
    return "PASS" if gate["pass"] else "FAIL"


def adjudicate_geometry_mechanics_v2(*, rows, metric, required_sources, reference_artifact, alpha: float = 0.01) -> dict:
    """Mechanical adjudication only; does not grant human execution authority."""
    metric = V1._token(metric, "metric")
    alpha_value = V1._number(alpha, "alpha")
    if not 0 < alpha_value < 1:
        raise GeometryRecurrenceV2Error("alpha must lie in (0,1)")

    normalized, deciding_binding, null_receipt = V1._normalize_rows(rows)
    sources = V1._required_sources(required_sources)
    source_set = set(sources)
    extras = sorted({row["source"] for row in normalized} - source_set)
    if extras:
        raise GeometryRecurrenceV2Error(f"extra source rows are forbidden: {extras}")

    estimable_donors = {row["donor_id"] for row in normalized if row["estimability_status"] == V1.ESTIMABLE}
    refit_margins, stability_margins = V1._validate_reference(
        reference_artifact,
        estimable_donors=estimable_donors,
        metric=metric,
        deciding_binding=deciding_binding,
    )

    min_null = V1.adverse_null_minimum_draws(alpha_value)
    source_status: dict[str, str] = {}
    source_details: dict[str, dict] = {}

    for source in sources:
        all_local = [row for row in normalized if row["source"] == source]
        local = [row for row in all_local if row["estimability_status"] == V1.ESTIMABLE]
        abstained = [row for row in all_local if row["estimability_status"] != V1.ESTIMABLE]
        counts = {
            "total_donor_count": len(all_local),
            "estimable_donor_count": len(local),
            "abstained_donor_count": len(abstained),
            "abstention_reasons": sorted({row["estimability_reason"] for row in abstained}),
        }
        if not all_local:
            source_status[source] = "NOT_ESTIMABLE"
            source_details[source] = {
                "reason": "NO_DECIDING_DONORS_FOR_REQUIRED_SOURCE",
                "null_defeat_status": "NOT_ESTIMABLE",
                "stability_status": "NOT_ESTIMABLE",
                "failed_biology": False,
                **counts,
            }
            continue
        if not local:
            source_status[source] = "NOT_ESTIMABLE"
            source_details[source] = {
                "reason": "NO_ESTIMABLE_DONORS_AFTER_SUPPORT_ABSTENTION",
                "null_defeat_status": "NOT_ESTIMABLE",
                "stability_status": "NOT_ESTIMABLE",
                "failed_biology": False,
                **counts,
            }
            continue

        # Stability remains estimable from observed displacement even when the
        # null producer is underresolved. Evaluate it first for every estimable
        # donor so an adverse stability result cannot be hidden by null NE.
        stability_rows = [
            {
                "donor_id": row["donor_id"],
                "delta": stability_margins[row["donor_id"]] - row["observed_displacement"],
            }
            for row in local
        ]
        stability_gate = P.sign_recurrence_gate(stability_rows, alpha_value)
        stability_status = _component(stability_gate)

        underresolved = [row["donor_id"] for row in local if len(row["null_displacements"]) < min_null]
        null_gate = None
        if underresolved:
            null_status = "NOT_ESTIMABLE"
        else:
            null_rows = []
            for row in local:
                adverse = V1.lower_adverse_null_bound(row["null_displacements"], alpha_value)
                if adverse is None:
                    raise AssertionError("null resolution was checked before adverse-bound computation")
                donor = row["donor_id"]
                null_rows.append({
                    "donor_id": donor,
                    "delta": adverse - row["observed_displacement"] - refit_margins[donor],
                })
            null_gate = P.sign_recurrence_gate(null_rows, alpha_value)
            null_status = _component(null_gate)

        if "FAIL" in {null_status, stability_status}:
            status = "FAIL"
            reason = "GEOMETRY_COMPONENT_FAILED"
        elif "NOT_ESTIMABLE" in {null_status, stability_status}:
            status = "NOT_ESTIMABLE"
            reason = "GEOMETRY_COMPONENT_UNRESOLVED"
        else:
            status = "PASS"
            reason = "BOTH_COMPONENTS_PASS"

        source_status[source] = status
        source_details[source] = {
            "reason": reason,
            "failed_biology": status == "FAIL",
            "null_defeat_status": null_status,
            "stability_status": stability_status,
            "null_defeat_sign_test": null_gate,
            "stability_sign_test": stability_gate,
            "minimum_null_draws_required": min_null,
            "underresolved_null_donors": underresolved,
            **counts,
        }

    if any(value == "FAIL" for value in source_status.values()):
        overall, reason = "FAIL", "REQUIRED_SOURCE_GEOMETRY_FAILED"
    elif any(value == "NOT_ESTIMABLE" for value in source_status.values()):
        overall, reason = "NOT_ESTIMABLE", "REQUIRED_SOURCE_GEOMETRY_UNRESOLVED"
    else:
        overall, reason = "PASS", "ALL_REQUIRED_SOURCES_MECHANICALLY_PASS"

    return {
        "schema": SCHEMA,
        "status": overall,
        "reason": reason,
        "metric": metric,
        "orientation": V1.ORIENTATION,
        "null_semantics": V1.NULL_SEMANTICS,
        "required_sources": sources,
        "source_status": source_status,
        "source_details": source_details,
        "input_binding_sha256": deciding_binding,
        "null_producer_receipt_sha256": null_receipt,
        "mechanics_only": True,
        "human_geometry_adjudication_authorized": False,
        "authority": dict(NO_AUTHORITY),
    }


def human_execution_readiness(*, producer_receipt) -> dict:
    # Deliberately do not treat a typed receipt mapping as qualification. A future
    # producer must be independently qualified on exact code/world/support/null
    # custody and then bound by a separate authority artifact.
    return {
        "schema": "JEPA_TD_REAL_GEOMETRY_HUMAN_READINESS_V2",
        "status": "BLOCKED_GEOMETRY_PRODUCER_NOT_INDEPENDENTLY_QUALIFIED",
        "reason": (
            "CALLER_COMPUTED_DISPLACEMENTS_SUPPORT_LABELS_ALIGNMENT_AND_NULL_RECEIPTS_HAVE_NO_HUMAN_AUTHORITY__"
            "PRODUCER_OWNED_IDENTITY_BOUND_GEOMETRY_PIPELINE_REQUIRED"
        ),
        "human_geometry_adjudication_authorized": False,
        "caller_support_labels_have_human_authority": False,
        "caller_displacements_have_human_authority": False,
        "caller_receipt_strings_have_human_authority": False,
        "eigengap_contract_status": "OPEN__NO_SILENT_THRESHOLD_INVENTION",
        "authority": dict(NO_AUTHORITY),
    }
