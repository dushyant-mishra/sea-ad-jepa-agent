"""Same-cell technical intervention anti-cheat probe for prospective V5.

The probe asks a causal question: when only observation conditions change for
an otherwise identical cell, does z_bio remain stable while z_obs is allowed to
respond? It computes diagnostics without choosing thresholds. Qualification is
fail-closed unless an explicit, prospectively frozen threshold authority is
provided.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

ALLOWED_INTERVENTIONS = frozenset(
    {"SUPPORT_FAMILY", "MASK_IDENTITY", "EVIDENCE_FRACTION", "MEASUREMENT_DEPTH"}
)


def _matrix(value: object, name: str) -> np.ndarray:
    out = np.asarray(value, dtype=np.float64)
    if out.ndim != 2 or out.shape[0] < 2 or out.shape[1] < 1:
        raise ValueError(f"{name} must be a finite 2-D matrix with >=2 rows")
    if not np.isfinite(out).all():
        raise ValueError(f"{name} must be finite")
    return out


def _keys(value: Sequence[object], n: int) -> tuple[str, ...]:
    out = tuple(str(x) for x in value)
    if len(out) != n or len(set(out)) != n or any(not x for x in out):
        raise ValueError("stable_cell_keys must be unique nonempty values aligned to rows")
    return out


def _cosine_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Return row-wise cosine similarity with explicit zero-vector semantics.

    Two exact zero vectors are identical and therefore score 1.0.  If exactly
    one side is zero there is no shared direction, so the score is 0.0 rather
    than being silently promoted to perfect similarity.  Nonzero rows are
    rescaled by their maximum absolute component before computing norms; this
    keeps the calculation stable for finite extreme and subnormal magnitudes
    without changing direction.
    """
    a_scale = np.max(np.abs(a), axis=1)
    b_scale = np.max(np.abs(b), axis=1)
    a_zero = a_scale == 0
    b_zero = b_scale == 0

    out = np.zeros(len(a), dtype=np.float64)
    both_zero = a_zero & b_zero
    out[both_zero] = 1.0

    nonzero = ~(a_zero | b_zero)
    if np.any(nonzero):
        aa = a[nonzero] / a_scale[nonzero, None]
        bb = b[nonzero] / b_scale[nonzero, None]
        denom = np.linalg.norm(aa, axis=1) * np.linalg.norm(bb, axis=1)
        out[nonzero] = np.sum(aa * bb, axis=1) / denom
    return np.clip(out, -1.0, 1.0)


def _relative_l2(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    scale = np.linalg.norm(a, axis=1)
    scale = np.maximum(scale, 1e-12)
    return np.linalg.norm(b - a, axis=1) / scale


def summarize_same_cell_intervention(
    *,
    stable_cell_keys: Sequence[object],
    intervention: str,
    z_bio_baseline: object,
    z_bio_perturbed: object,
    z_obs_baseline: object,
    z_obs_perturbed: object,
) -> dict[str, object]:
    if intervention not in ALLOWED_INTERVENTIONS:
        raise ValueError(f"unsupported technical intervention {intervention!r}")
    bb = _matrix(z_bio_baseline, "z_bio_baseline")
    bp = _matrix(z_bio_perturbed, "z_bio_perturbed")
    ob = _matrix(z_obs_baseline, "z_obs_baseline")
    op = _matrix(z_obs_perturbed, "z_obs_perturbed")
    if bb.shape != bp.shape:
        raise ValueError("z_bio baseline/perturbed shapes differ")
    if ob.shape != op.shape:
        raise ValueError("z_obs baseline/perturbed shapes differ")
    if len(bb) != len(ob):
        raise ValueError("z_bio and z_obs row counts differ")
    keys = _keys(stable_cell_keys, len(bb))
    bio_rel = _relative_l2(bb, bp)
    obs_rel = _relative_l2(ob, op)
    bio_cos = _cosine_rows(bb, bp)
    ratio = bio_rel / np.maximum(obs_rel, 1e-12)
    return {
        "schema": "JEPA_V5_SAME_CELL_TECHNICAL_INTERVENTION_SUMMARY_V1",
        "intervention": intervention,
        "cells": len(keys),
        "stable_cell_keys_unique": True,
        "bio_median_relative_l2": float(np.median(bio_rel)),
        "bio_p95_relative_l2": float(np.quantile(bio_rel, 0.95)),
        "bio_median_cosine": float(np.median(bio_cos)),
        "obs_median_relative_l2": float(np.median(obs_rel)),
        "obs_p05_relative_l2": float(np.quantile(obs_rel, 0.05)),
        "bio_to_obs_median_delta_ratio": float(np.median(ratio)),
        "thresholds_applied": False,
    }


@dataclass(frozen=True)
class SameCellInterventionThresholdAuthorityV1:
    max_bio_median_relative_l2: float
    max_bio_p95_relative_l2: float
    min_bio_median_cosine: float
    min_obs_median_relative_l2: float
    max_bio_to_obs_median_delta_ratio: float
    calibration_authority_id: str

    def validate(self) -> None:
        for name in (
            "max_bio_median_relative_l2",
            "max_bio_p95_relative_l2",
            "min_obs_median_relative_l2",
            "max_bio_to_obs_median_delta_ratio",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be explicit finite nonnegative numeric")
        cosine = self.min_bio_median_cosine
        if isinstance(cosine, bool) or not isinstance(cosine, (int, float)) or not -1.0 <= float(cosine) <= 1.0:
            raise ValueError("min_bio_median_cosine must lie in [-1,1]")
        if not isinstance(self.calibration_authority_id, str) or not self.calibration_authority_id:
            raise ValueError("calibration_authority_id must be explicit and nonempty")


def qualify_same_cell_intervention(
    summary: Mapping[str, object],
    *,
    thresholds: SameCellInterventionThresholdAuthorityV1,
) -> dict[str, object]:
    thresholds.validate()
    if summary.get("schema") != "JEPA_V5_SAME_CELL_TECHNICAL_INTERVENTION_SUMMARY_V1":
        raise ValueError("unexpected same-cell intervention summary schema")
    checks = {
        "bio_median_relative_l2": float(summary["bio_median_relative_l2"])
        <= thresholds.max_bio_median_relative_l2,
        "bio_p95_relative_l2": float(summary["bio_p95_relative_l2"])
        <= thresholds.max_bio_p95_relative_l2,
        "bio_median_cosine": float(summary["bio_median_cosine"])
        >= thresholds.min_bio_median_cosine,
        "obs_median_relative_l2": float(summary["obs_median_relative_l2"])
        >= thresholds.min_obs_median_relative_l2,
        "bio_to_obs_median_delta_ratio": float(
            summary["bio_to_obs_median_delta_ratio"]
        )
        <= thresholds.max_bio_to_obs_median_delta_ratio,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise RuntimeError(f"STOP_SAME_CELL_TECHNICAL_INTERVENTION_ANTI_CHEAT: {failed}")
    return {
        "passed": True,
        "intervention": summary["intervention"],
        "calibration_authority_id": thresholds.calibration_authority_id,
        "checks": checks,
    }
