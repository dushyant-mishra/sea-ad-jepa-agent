"""Same-cell technical intervention anti-cheat probe for prospective V5.

The probe asks a causal question: when only observation conditions change for
an otherwise identical cell, does z_bio remain stable while z_obs is allowed to
respond? It computes diagnostics without choosing thresholds. Qualification is
fail-closed unless an explicit, prospectively frozen threshold authority is
provided.  Receipt helpers bind provenance and explicitly prevent this probe
from becoming D_shared execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .artifact_binding_v1 import seal_artifact, validate_artifact

ALLOWED_INTERVENTIONS = frozenset(
    {"SUPPORT_FAMILY", "MASK_IDENTITY", "EVIDENCE_FRACTION", "MEASUREMENT_DEPTH"}
)
_RECEIPT_SCHEMA = "JEPA_V5_SAME_CELL_MEASUREMENT_INTERVENTION_RECEIPT_V1"
_RECEIPT_AUTHORITY = "MEASUREMENT_ROBUSTNESS_ONLY__NOT_D_SHARED_AUTHORITY"


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
    """Return row-wise cosine similarity with explicit zero-vector semantics."""
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
        "bio_to_obs_median_delta_ratio": float(summary["bio_to_obs_median_delta_ratio"])
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


def _positive_strength(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("intervention_strength must be explicit positive finite numeric")
    out = float(value)
    if not np.isfinite(out) or out <= 0.0:
        raise ValueError("intervention_strength must be explicit positive finite numeric")
    return out


def _receipt_payload(
    *,
    summary: Mapping[str, object],
    intervention_strength: object,
    intervention_strength_frozen_before_execution: bool,
    stable_row_identity_preserved: bool,
    donor_identity_preserved: bool,
    operator_identity_preserved: bool,
    source_identity_preserved: bool,
    d_shared_outcomes_used: bool,
    protected_data_used: bool,
    pathology_used: bool,
    training_authorized: bool,
) -> dict[str, object]:
    if not isinstance(summary, Mapping) or summary.get("schema") != "JEPA_V5_SAME_CELL_TECHNICAL_INTERVENTION_SUMMARY_V1":
        raise ValueError("unexpected same-cell intervention summary schema")
    frozen = {
        "intervention_strength_frozen_before_execution": intervention_strength_frozen_before_execution,
        "stable_row_identity_preserved": stable_row_identity_preserved,
        "donor_identity_preserved": donor_identity_preserved,
        "operator_identity_preserved": operator_identity_preserved,
        "source_identity_preserved": source_identity_preserved,
    }
    failed = sorted(name for name, value in frozen.items() if value is not True)
    if failed:
        raise RuntimeError(f"STOP_SAME_CELL_RECEIPT_IDENTITY_OR_PLAN_NOT_FROZEN:{','.join(failed)}")
    forbidden = {
        "d_shared_outcomes_used": d_shared_outcomes_used,
        "protected_data_used": protected_data_used,
        "pathology_used": pathology_used,
        "training_authorized": training_authorized,
    }
    bad = sorted(name for name, value in forbidden.items() if value is not False)
    if bad:
        raise RuntimeError(f"STOP_SAME_CELL_RECEIPT_FORBIDDEN:{','.join(bad)}")
    return {
        "summary": dict(summary),
        "intervention": summary["intervention"],
        "intervention_strength": _positive_strength(intervention_strength),
        **frozen,
        **forbidden,
        "authority_classification": _RECEIPT_AUTHORITY,
        "d_shared_real_outcome_access_authorized": False,
    }


def seal_same_cell_intervention_receipt_v1(
    *,
    summary: Mapping[str, object],
    parent_sha256: str,
    intervention_plan_sha256: str,
    intervention_strength: object,
    intervention_strength_frozen_before_execution: bool,
    stable_row_identity_preserved: bool,
    donor_identity_preserved: bool,
    operator_identity_preserved: bool,
    source_identity_preserved: bool,
    d_shared_outcomes_used: bool = False,
    protected_data_used: bool = False,
    pathology_used: bool = False,
    training_authorized: bool = False,
) -> dict[str, object]:
    payload = _receipt_payload(
        summary=summary,
        intervention_strength=intervention_strength,
        intervention_strength_frozen_before_execution=intervention_strength_frozen_before_execution,
        stable_row_identity_preserved=stable_row_identity_preserved,
        donor_identity_preserved=donor_identity_preserved,
        operator_identity_preserved=operator_identity_preserved,
        source_identity_preserved=source_identity_preserved,
        d_shared_outcomes_used=d_shared_outcomes_used,
        protected_data_used=protected_data_used,
        pathology_used=pathology_used,
        training_authorized=training_authorized,
    )
    return seal_artifact(
        _RECEIPT_SCHEMA,
        payload,
        {
            "measurement_parent_sha256": parent_sha256,
            "intervention_plan_sha256": intervention_plan_sha256,
        },
    )


def validate_same_cell_intervention_receipt_v1(
    envelope: Mapping[str, object],
    *,
    parent_sha256: str,
    intervention_plan_sha256: str,
) -> dict[str, object]:
    payload = validate_artifact(
        envelope,
        expected_schema=_RECEIPT_SCHEMA,
        expected_parents={
            "measurement_parent_sha256": parent_sha256,
            "intervention_plan_sha256": intervention_plan_sha256,
        },
    )
    checked = _receipt_payload(
        summary=payload.get("summary"),
        intervention_strength=payload.get("intervention_strength"),
        intervention_strength_frozen_before_execution=payload.get("intervention_strength_frozen_before_execution"),
        stable_row_identity_preserved=payload.get("stable_row_identity_preserved"),
        donor_identity_preserved=payload.get("donor_identity_preserved"),
        operator_identity_preserved=payload.get("operator_identity_preserved"),
        source_identity_preserved=payload.get("source_identity_preserved"),
        d_shared_outcomes_used=payload.get("d_shared_outcomes_used"),
        protected_data_used=payload.get("protected_data_used"),
        pathology_used=payload.get("pathology_used"),
        training_authorized=payload.get("training_authorized"),
    )
    if payload.get("authority_classification") != _RECEIPT_AUTHORITY or payload.get("d_shared_real_outcome_access_authorized") is not False:
        raise RuntimeError("STOP_SAME_CELL_RECEIPT_AUTHORITY_ESCALATION")
    return checked
