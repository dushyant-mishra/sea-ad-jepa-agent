"""Prospective V5 representation-collapse diagnostics and fail-closed guard.

The summary computes geometry only. Scientific thresholds are external and must
be frozen before a candidate checkpoint outcome is inspected. No threshold is
selected here and this module never grants training authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

_ALLOWED_THRESHOLD_PROVENANCE = frozenset({
    "PROSPECTIVE_PREMODEL",
    "INDEPENDENT_CALIBRATION",
})


def _num(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be explicit numeric")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite")
    return out


def summarize_representation_geometry(embedding: object) -> dict[str, object]:
    """Return scale/rank diagnostics without deciding whether they are adequate."""
    x = np.asarray(embedding, dtype=np.float64)
    if x.ndim != 2 or x.shape[0] < 3 or x.shape[1] < 2:
        raise ValueError("embedding must be finite n x d with n>=3 and d>=2")
    if not np.isfinite(x).all():
        raise ValueError("embedding must be finite")

    centered = x - np.mean(x, axis=0, dtype=np.float64)
    variances = np.var(x, axis=0, ddof=1)
    max_var = float(np.max(variances))
    numerical_tol = 64.0 * np.finfo(np.float64).eps * max(max_var, np.finfo(np.float64).tiny)
    active = variances > numerical_tol

    singular = np.linalg.svd(centered, compute_uv=False)
    eigen = (singular * singular) / float(x.shape[0] - 1)
    total = float(np.sum(eigen, dtype=np.float64))
    if total > 0.0:
        effective_rank = float((total * total) / np.sum(eigen * eigen, dtype=np.float64))
        top_fraction = float(eigen[0] / total)
    else:
        effective_rank = 0.0
        top_fraction = 1.0
    rank_reference = min(x.shape[1], x.shape[0] - 1)

    return {
        "schema": "JEPA_V5_REPRESENTATION_GEOMETRY_SUMMARY_V1",
        "rows": int(x.shape[0]),
        "dimensions": int(x.shape[1]),
        "rank_reference_dimensions": int(rank_reference),
        "centered_rms": float(np.sqrt(np.mean(np.sum(centered * centered, axis=1), dtype=np.float64))),
        "total_variance": total,
        "active_dimensions": int(np.sum(active)),
        "active_dimension_fraction": float(np.mean(active)),
        "effective_rank": effective_rank,
        "effective_rank_fraction": float(effective_rank / rank_reference),
        "top_variance_fraction": top_fraction,
        "coordinate_variance_min": float(np.min(variances)),
        "coordinate_variance_median": float(np.median(variances)),
        "coordinate_variance_max": max_var,
        "active_dimension_numerical_tolerance": numerical_tol,
        "thresholds_applied": False,
    }


@dataclass(frozen=True)
class RepresentationCollapseThresholdAuthorityV1:
    minimum_centered_rms: float
    minimum_active_dimension_fraction: float
    minimum_effective_rank_fraction: float
    maximum_top_variance_fraction: float
    calibration_authority_id: str
    thresholds_frozen_before_candidate_model_outcome: bool
    threshold_provenance: str

    def validate(self) -> None:
        if not isinstance(self.calibration_authority_id, str) or not self.calibration_authority_id.strip():
            raise ValueError("calibration_authority_id must be nonempty")
        if self.thresholds_frozen_before_candidate_model_outcome is not True:
            raise ValueError("collapse thresholds must be frozen before candidate-model outcome")
        if self.threshold_provenance not in _ALLOWED_THRESHOLD_PROVENANCE:
            raise ValueError("collapse threshold provenance must be prospective or independently calibrated")
        if _num(self.minimum_centered_rms, "minimum_centered_rms") < 0:
            raise ValueError("minimum_centered_rms must be nonnegative")
        for name in ("minimum_active_dimension_fraction", "minimum_effective_rank_fraction"):
            value = _num(getattr(self, name), name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0,1]")
        top = _num(self.maximum_top_variance_fraction, "maximum_top_variance_fraction")
        if not 0.0 < top <= 1.0:
            raise ValueError("maximum_top_variance_fraction must lie in (0,1]")


def qualify_representation_against_collapse(
    summary: object,
    *,
    authority: RepresentationCollapseThresholdAuthorityV1,
    representation_id: str,
) -> dict[str, object]:
    authority.validate()
    if not isinstance(summary, dict) or summary.get("schema") != "JEPA_V5_REPRESENTATION_GEOMETRY_SUMMARY_V1":
        raise ValueError("unexpected representation summary schema")
    if not isinstance(representation_id, str) or not representation_id.strip():
        raise ValueError("representation_id must be nonempty")

    checks = {
        "centered_rms": _num(summary.get("centered_rms"), "centered_rms") >= authority.minimum_centered_rms,
        "active_dimension_fraction": _num(summary.get("active_dimension_fraction"), "active_dimension_fraction") >= authority.minimum_active_dimension_fraction,
        "effective_rank_fraction": _num(summary.get("effective_rank_fraction"), "effective_rank_fraction") >= authority.minimum_effective_rank_fraction,
        "top_variance_fraction": _num(summary.get("top_variance_fraction"), "top_variance_fraction") <= authority.maximum_top_variance_fraction,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise RuntimeError(f"STOP_V5_REPRESENTATION_COLLAPSE: {representation_id}: {failed}")
    return {
        "schema": "JEPA_V5_REPRESENTATION_COLLAPSE_QUALIFICATION_V1",
        "passed": True,
        "representation_id": representation_id,
        "checks": checks,
        "calibration_authority_id": authority.calibration_authority_id,
        "threshold_provenance": authority.threshold_provenance,
        "training_authorized": False,
    }
