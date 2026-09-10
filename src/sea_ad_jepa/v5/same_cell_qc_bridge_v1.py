"""Bridge low-level same-cell intervention results into the V5 QC closure schema.

The low-level probe deliberately reports only its calibration authority. The QC
closure requires separate binding of the intervention authority and the threshold
authority. This bridge is fail-closed and never grants training authority.
"""
from __future__ import annotations

from typing import Mapping


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value


def build_same_cell_measurement_qualification(
    low_level_result: Mapping[str, object],
    *,
    intervention_authority_id: str,
    threshold_authority_id: str,
) -> dict[str, object]:
    if not isinstance(low_level_result, Mapping):
        raise ValueError("low_level_result must be a mapping")
    iid = _id(intervention_authority_id, "intervention_authority_id")
    tid = _id(threshold_authority_id, "threshold_authority_id")

    if low_level_result.get("passed") is not True:
        raise RuntimeError("STOP_V5_SAME_CELL_LOW_LEVEL_NOT_PASS")
    if low_level_result.get("calibration_authority_id") != tid:
        raise ValueError("low-level calibration authority does not match threshold authority")

    intervention = low_level_result.get("intervention")
    if not isinstance(intervention, str) or not intervention:
        raise ValueError("low-level intervention identity missing")

    checks = low_level_result.get("checks")
    if not isinstance(checks, Mapping) or not checks:
        raise ValueError("low-level checks missing")
    if any(value is not True for value in checks.values()):
        raise RuntimeError("STOP_V5_SAME_CELL_LOW_LEVEL_CHECK_NOT_PASS")

    return {
        "schema": "JEPA_V5_SAME_CELL_MEASUREMENT_QUALIFICATION_V1",
        "authority_id": iid,
        "threshold_authority_id": tid,
        "intervention": intervention,
        "passed": True,
        "training_authorized": False,
    }
