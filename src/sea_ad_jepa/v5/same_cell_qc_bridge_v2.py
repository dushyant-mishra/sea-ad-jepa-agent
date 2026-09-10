"""Complete-family bridge from same-cell probes into V5 QC qualification.

V1 could bridge a single passing intervention. V2 requires every frozen V5
technical intervention and binds a distinct threshold authority for each one.
A model cannot qualify by passing only its easiest perturbation.
"""
from __future__ import annotations

from typing import Mapping

from .same_cell_technical_intervention_probe_v1 import ALLOWED_INTERVENTIONS

CANONICAL_INTERVENTIONS = tuple(sorted(ALLOWED_INTERVENTIONS))


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value


def build_same_cell_measurement_qualification_v2(
    low_level_results_by_intervention: Mapping[str, Mapping[str, object]],
    *,
    intervention_authority_id: str,
    threshold_authority_ids: Mapping[str, str],
) -> dict[str, object]:
    if not isinstance(low_level_results_by_intervention, Mapping):
        raise ValueError("low_level_results_by_intervention must be a mapping")
    if set(low_level_results_by_intervention) != set(CANONICAL_INTERVENTIONS):
        raise RuntimeError("STOP_V5_SAME_CELL_INTERVENTION_SET_INCOMPLETE")
    if not isinstance(threshold_authority_ids, Mapping) or set(threshold_authority_ids) != set(CANONICAL_INTERVENTIONS):
        raise RuntimeError("STOP_V5_SAME_CELL_THRESHOLD_AUTHORITY_SET_INCOMPLETE")

    iid = _id(intervention_authority_id, "intervention_authority_id")
    threshold_ids: dict[str, str] = {}
    checks_by_intervention: dict[str, dict[str, bool]] = {}

    for intervention in CANONICAL_INTERVENTIONS:
        tid = _id(threshold_authority_ids[intervention], f"threshold_authority_ids[{intervention}]")
        threshold_ids[intervention] = tid
        result = low_level_results_by_intervention[intervention]
        if not isinstance(result, Mapping):
            raise ValueError(f"{intervention} low-level result must be a mapping")
        if result.get("passed") is not True:
            raise RuntimeError(f"STOP_V5_SAME_CELL_LOW_LEVEL_NOT_PASS: {intervention}")
        if result.get("intervention") != intervention:
            raise RuntimeError(f"STOP_V5_SAME_CELL_INTERVENTION_IDENTITY_SUBSTITUTION: {intervention}")
        if result.get("calibration_authority_id") != tid:
            raise ValueError(f"{intervention} calibration authority does not match threshold authority")
        checks = result.get("checks")
        if not isinstance(checks, Mapping) or not checks:
            raise ValueError(f"{intervention} low-level checks missing")
        if any(value is not True for value in checks.values()):
            raise RuntimeError(f"STOP_V5_SAME_CELL_LOW_LEVEL_CHECK_NOT_PASS: {intervention}")
        checks_by_intervention[intervention] = {str(k): True for k in sorted(checks)}

    return {
        "schema": "JEPA_V5_SAME_CELL_MEASUREMENT_QUALIFICATION_V2",
        "authority_id": iid,
        "threshold_authority_ids": threshold_ids,
        "interventions": CANONICAL_INTERVENTIONS,
        "checks_by_intervention": checks_by_intervention,
        "all_required_interventions_passed": True,
        "passed": True,
        "training_authorized": False,
    }
