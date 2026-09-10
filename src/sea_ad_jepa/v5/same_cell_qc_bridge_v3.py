"""Artifact-bound same-cell measurement qualification for V5.

V3 preserves the complete-intervention semantics of V2 and additionally binds
all four low-level intervention results to immutable artifact digests. This
prevents a passing family report from being paired later with different probe
outputs that happen to share intervention names and threshold authorities.

This module never grants production training authority.
"""
from __future__ import annotations

from typing import Mapping

from .same_cell_qc_bridge_v2 import (
    CANONICAL_INTERVENTIONS,
    build_same_cell_measurement_qualification_v2,
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


def build_same_cell_measurement_qualification_v3(
    low_level_results_by_intervention: Mapping[str, Mapping[str, object]],
    *,
    low_level_artifact_sha256_by_intervention: Mapping[str, str],
    intervention_authority_id: str,
    threshold_authority_ids: Mapping[str, str],
) -> dict[str, object]:
    """Build a complete same-cell family report bound to exact child artifacts."""
    v2 = build_same_cell_measurement_qualification_v2(
        low_level_results_by_intervention,
        intervention_authority_id=intervention_authority_id,
        threshold_authority_ids=threshold_authority_ids,
    )
    if not isinstance(low_level_artifact_sha256_by_intervention, Mapping):
        raise ValueError("low_level_artifact_sha256_by_intervention must be a mapping")
    if set(low_level_artifact_sha256_by_intervention) != set(CANONICAL_INTERVENTIONS):
        raise RuntimeError("STOP_V5_SAME_CELL_ARTIFACT_SET_INCOMPLETE")

    artifacts = {
        intervention: _sha(
            low_level_artifact_sha256_by_intervention[intervention],
            f"low_level_artifact_sha256_by_intervention[{intervention}]",
        )
        for intervention in CANONICAL_INTERVENTIONS
    }
    return {
        "schema": "JEPA_V5_SAME_CELL_MEASUREMENT_QUALIFICATION_V3",
        "authority_id": v2["authority_id"],
        "threshold_authority_ids": v2["threshold_authority_ids"],
        "interventions": v2["interventions"],
        "checks_by_intervention": v2["checks_by_intervention"],
        "low_level_artifact_sha256_by_intervention": artifacts,
        "all_required_interventions_passed": True,
        "passed": True,
        "training_authorized": False,
    }
