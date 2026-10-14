"""Outcome-blind common recurrence/stability mechanics for G9/S1/S2.

This module qualifies a reusable geometry decision engine before candidate-specific
human execution.  It deliberately separates:
  * invariant geometry measurement;
  * train-only coordinate alignment;
  * adverse-null recurrence;
  * absolute stability relative to independent refit/measurement variation.

No human candidate values are read and no real-TD authority is granted.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence

import numpy as np

from scripts.v5 import td_target_tournament_precision as P


class GeometryRecurrenceError(ValueError):
    pass


QUAL_SCHEMA = "JEPA_TD_REAL_GEOMETRY_RECURRENCE_QUALIFICATION_V1"
QUAL_PASS = "PASS_KNOWN_TRUTH_GEOMETRY_RECURRENCE"
REFERENCE_SCHEMA = "JEPA_TD_REAL_GEOMETRY_REFERENCE_MARGIN_V1"
PROJECTOR_METRIC = "PROJECTOR_RMS_PRINCIPAL_ANGLE_DISPLACEMENT"
ORIENTATION = "SMALLER_DISPLACEMENT_IS_MORE_STABLE"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _number(value, label: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise GeometryRecurrenceError(f"{label} must be finite numeric")
    out = float(value)
    if not math.isfinite(out):
        raise GeometryRecurrenceError(f"{label} must be finite numeric")
    if nonnegative and out < 0:
        raise GeometryRecurrenceError(f"{label} must be nonnegative")
    return out


def _token(value, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise GeometryRecurrenceError(f"{label} must be a nonempty trimmed NUL-free string")
    return value


def _hex(value, label: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise GeometryRecurrenceError(f"{label} must be lowercase 64-hex")
    return value


def _matrix(value, label: str) -> np.ndarray:
    try:
        arr = np.asarray(value, dtype=float)
    except Exception as exc:  # pragma: no cover
        raise GeometryRecurrenceError(f"{label} must be numeric matrix-like") from exc
    if arr.ndim != 2 or arr.shape[0] == 0 or arr.shape[1] == 0 or not np.isfinite(arr).all():
        raise GeometryRecurrenceError(f"{label} must be a nonempty finite 2D matrix")
    return arr


def _orthonormal_columns(value, label: str) -> np.ndarray:
    arr = _matrix(value, label)
    if arr.shape[0] < arr.shape[1]:
        raise GeometryRecurrenceError(f"{label} ambient dimension must be >= rank")
    if np.linalg.matrix_rank(arr) != arr.shape[1]:
        raise GeometryRecurrenceError(f"{label} columns must have full rank")
    q, _ = np.linalg.qr(arr, mode="reduced")
    return q


def projector_rms_displacement(first, second) -> float:
    """Orthogonal-invariant equal-rank subspace displacement in [0,1].

    sqrt(mean(sin(theta_i)^2)), where theta_i are principal angles.  This is
    exactly invariant to sign/order/orthogonal rotation within the same subspace.
    """
    left = _orthonormal_columns(first, "first basis")
    right = _orthonormal_columns(second, "second basis")
    if left.shape != right.shape:
        raise GeometryRecurrenceError("subspace bases must have identical ambient dimension and rank")
    singular = np.linalg.svd(left.T @ right, compute_uv=False)
    singular = np.clip(singular, 0.0, 1.0)
    return float(np.sqrt(np.mean(np.maximum(0.0, 1.0 - singular * singular))))


def fit_train_only_procrustes(*, train_a, train_b, train_unit_ids, heldout_unit_ids) -> dict:
    """Fit an orthogonal mapping using training units only.

    Unit identities are explicit so an overlap with the held-out evaluation set
    is a hard error rather than silent alignment leakage.
    """
    a = _matrix(train_a, "train_a")
    b = _matrix(train_b, "train_b")
    if a.shape != b.shape:
        raise GeometryRecurrenceError("train_a and train_b must have identical shape")
    if isinstance(train_unit_ids, (str, bytes)) or not isinstance(train_unit_ids, Sequence):
        raise GeometryRecurrenceError("train_unit_ids must be a sequence")
    if isinstance(heldout_unit_ids, (str, bytes)) or not isinstance(heldout_unit_ids, Sequence):
        raise GeometryRecurrenceError("heldout_unit_ids must be a sequence")
    train_ids = [_token(v, "train_unit_id") for v in train_unit_ids]
    held_ids = [_token(v, "heldout_unit_id") for v in heldout_unit_ids]
    if len(train_ids) != a.shape[0] or len(set(train_ids)) != len(train_ids):
        raise GeometryRecurrenceError("train_unit_ids must uniquely match training rows")
    if len(set(held_ids)) != len(held_ids):
        raise GeometryRecurrenceError("heldout_unit_ids must be unique")
    if set(train_ids) & set(held_ids):
        raise GeometryRecurrenceError("heldout units may not influence the alignment fit")
    mean_a = a.mean(axis=0)
    mean_b = b.mean(axis=0)
    ac = a - mean_a
    bc = b - mean_b
    u, _, vt = np.linalg.svd(ac.T @ bc, full_matrices=False)
    rotation = u @ vt
    return {
        "schema": "JEPA_TD_TRAIN_ONLY_ORTHOGONAL_PROCRUSTES_V1",
        "n_features": int(a.shape[1]),
        "mean_a": mean_a.tolist(),
        "mean_b": mean_b.tolist(),
        "rotation": rotation.tolist(),
        "fit_unit_count": len(train_ids),
        "heldout_unit_count": len(held_ids),
        "heldout_used_for_fit": False,
    }


def aligned_rms_displacement(first, second, transform: Mapping) -> float:
    a = _matrix(first, "first coordinates")
    b = _matrix(second, "second coordinates")
    if a.shape != b.shape:
        raise GeometryRecurrenceError("coordinate matrices must have identical shape")
    required = {
        "schema", "n_features", "mean_a", "mean_b", "rotation",
        "fit_unit_count", "heldout_unit_count", "heldout_used_for_fit",
    }
    if not isinstance(transform, Mapping) or set(transform) != required:
        raise GeometryRecurrenceError("invalid frozen Procrustes transform")
    if transform["schema"] != "JEPA_TD_TRAIN_ONLY_ORTHOGONAL_PROCRUSTES_V1" or transform["heldout_used_for_fit"] is not False:
        raise GeometryRecurrenceError("alignment transform is not train-only")
    n_features = int(transform["n_features"])
    if a.shape[1] != n_features:
        raise GeometryRecurrenceError("coordinate feature dimension does not match transform")
    mean_a = np.asarray(transform["mean_a"], dtype=float)
    mean_b = np.asarray(transform["mean_b"], dtype=float)
    rotation = np.asarray(transform["rotation"], dtype=float)
    if mean_a.shape != (n_features,) or mean_b.shape != (n_features,) or rotation.shape != (n_features, n_features):
        raise GeometryRecurrenceError("alignment transform shapes are invalid")
    mapped = (a - mean_a) @ rotation + mean_b
    residual = mapped - b
    return float(np.sqrt(np.mean(residual * residual)))


def _qualification_valid(value) -> bool:
    return bool(
        isinstance(value, Mapping)
        and value.get("schema") == QUAL_SCHEMA
        and value.get("status") == QUAL_PASS
        and value.get("known_truth_power_qualified") is True
    )


def _normalize_rows(rows) -> tuple[list[dict], str | None]:
    fields = {"source", "donor_id", "observed_displacement", "null_displacements", "input_binding_sha256"}
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise GeometryRecurrenceError("rows must be a sequence")
    out: list[dict] = []
    seen_donors: set[str] = set()
    bindings: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping) or set(raw) != fields:
            raise GeometryRecurrenceError(f"rows[{index}] fields differ from frozen schema")
        source = _token(raw["source"], "source")
        donor = _token(raw["donor_id"], "donor_id")
        if donor in seen_donors:
            raise GeometryRecurrenceError(f"duplicate donor_id across geometry rows: {donor}")
        seen_donors.add(donor)
        observed = _number(raw["observed_displacement"], "observed_displacement", nonnegative=True)
        nulls = raw["null_displacements"]
        if isinstance(nulls, (str, bytes)) or not isinstance(nulls, Sequence) or not nulls:
            raise GeometryRecurrenceError("null_displacements must be a nonempty sequence")
        normalized_nulls = [_number(v, "null displacement", nonnegative=True) for v in nulls]
        binding = _hex(raw["input_binding_sha256"], "input_binding_sha256")
        bindings.add(binding)
        out.append({
            "source": source,
            "donor_id": donor,
            "observed_displacement": observed,
            "null_displacements": normalized_nulls,
            "input_binding_sha256": binding,
        })
    if len(bindings) > 1:
        raise GeometryRecurrenceError("all deciding rows must share one exact input binding")
    return out, (next(iter(bindings)) if bindings else None)


def _required_sources(value) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise GeometryRecurrenceError("required_sources must be a nonempty sequence")
    out = [_token(v, "required source") for v in value]
    if len(set(out)) != len(out):
        raise GeometryRecurrenceError("required_sources must be unique")
    return out


def _validate_reference(reference, *, donors: set[str], metric: str, deciding_binding: str | None) -> tuple[dict[str, float], dict[str, float]]:
    required = {
        "schema", "frozen", "qualified", "metric", "orientation",
        "deciding_namespace_disjoint", "input_binding_sha256", "reference_receipt_sha256",
        "refit_margins", "stability_margins",
    }
    if not isinstance(reference, Mapping) or set(reference) != required:
        raise GeometryRecurrenceError("a frozen qualified geometry reference artifact with exact fields is required")
    if reference["schema"] != REFERENCE_SCHEMA:
        raise GeometryRecurrenceError("reference schema mismatch")
    if reference["frozen"] is not True or reference["qualified"] is not True:
        raise GeometryRecurrenceError("reference artifact must be frozen and qualified")
    if reference["metric"] != metric:
        raise GeometryRecurrenceError("reference metric must equal the frozen deciding metric")
    if reference["orientation"] != ORIENTATION:
        raise GeometryRecurrenceError("reference orientation mismatch")
    if reference["deciding_namespace_disjoint"] is not True:
        raise GeometryRecurrenceError("reference and deciding namespaces must be disjoint")
    ref_binding = _hex(reference["input_binding_sha256"], "reference input_binding_sha256")
    _hex(reference["reference_receipt_sha256"], "reference_receipt_sha256")
    if deciding_binding is not None and ref_binding != deciding_binding:
        raise GeometryRecurrenceError("reference input binding must equal exact deciding input binding")

    def margins(key: str) -> dict[str, float]:
        raw = reference[key]
        if not isinstance(raw, Mapping):
            raise GeometryRecurrenceError(f"{key} must be a mapping")
        out = {_token(k, f"{key} donor"): _number(v, f"{key} margin", nonnegative=True) for k, v in raw.items()}
        if set(out) != donors:
            raise GeometryRecurrenceError(f"{key} donor roster must match deciding donor roster exactly")
        return out

    return margins("refit_margins"), margins("stability_margins")


def adjudicate_geometry_recurrence(
    *, rows, metric, required_sources, decision_qualification, reference_artifact, alpha: float = 0.01
) -> dict:
    metric = _token(metric, "metric")
    alpha_value = _number(alpha, "alpha")
    if not 0 < alpha_value < 1:
        raise GeometryRecurrenceError("alpha must lie in (0,1)")
    normalized, deciding_binding = _normalize_rows(rows)
    sources = _required_sources(required_sources)
    if not _qualification_valid(decision_qualification):
        return {
            "schema": "JEPA_TD_REAL_GEOMETRY_RECURRENCE_DECISION_V1",
            "status": "NOT_ESTIMABLE", "reason": "DECISION_KNOWN_TRUTH_NOT_QUALIFIED",
            "metric": metric, "source_status": {}, "source_details": {},
            "input_binding_sha256": deciding_binding, "authority": dict(NO_AUTHORITY),
        }
    donor_set = {row["donor_id"] for row in normalized}
    refit_margins, stability_margins = _validate_reference(
        reference_artifact, donors=donor_set, metric=metric, deciding_binding=deciding_binding
    )

    source_status: dict[str, str] = {}
    source_details: dict[str, dict] = {}
    for source in sources:
        local = [row for row in normalized if row["source"] == source]
        if not local:
            source_status[source] = "NOT_ESTIMABLE"
            source_details[source] = {
                "reason": "NO_DECIDING_DONORS_FOR_REQUIRED_SOURCE",
                "null_defeat_status": "NOT_ESTIMABLE", "stability_status": "NOT_ESTIMABLE",
                "donor_count": 0,
            }
            continue
        null_rows = []
        stability_rows = []
        donor_details = []
        for row in local:
            donor = row["donor_id"]
            observed = row["observed_displacement"]
            null_median = float(np.median(np.asarray(row["null_displacements"], dtype=float)))
            null_advantage = null_median - observed
            null_adjusted = null_advantage - refit_margins[donor]
            stability_adjusted = stability_margins[donor] - observed
            null_rows.append({"donor_id": donor, "delta": null_adjusted})
            stability_rows.append({"donor_id": donor, "delta": stability_adjusted})
            donor_details.append({
                "donor_id": donor,
                "observed_displacement": observed,
                "null_median_displacement": null_median,
                "refit_margin": refit_margins[donor],
                "stability_margin": stability_margins[donor],
                "null_advantage_minus_refit": null_adjusted,
                "stability_margin_minus_observed": stability_adjusted,
            })
        null_gate = P.sign_recurrence_gate(null_rows, alpha_value)
        stability_gate = P.sign_recurrence_gate(stability_rows, alpha_value)

        def component(gate) -> str:
            if not gate["resolution_estimable"]:
                return "NOT_ESTIMABLE"
            return "PASS" if gate["pass"] else "FAIL"

        null_status = component(null_gate)
        stable_status = component(stability_gate)
        if "FAIL" in {null_status, stable_status}:
            status = "FAIL"
        elif "NOT_ESTIMABLE" in {null_status, stable_status}:
            status = "NOT_ESTIMABLE"
        else:
            status = "PASS"
        source_status[source] = status
        source_details[source] = {
            "donor_count": len(local),
            "null_defeat_status": null_status,
            "stability_status": stable_status,
            "null_defeat_sign_test": null_gate,
            "stability_sign_test": stability_gate,
            "donors": donor_details,
        }

    if any(v == "FAIL" for v in source_status.values()):
        overall, reason = "FAIL", "REQUIRED_SOURCE_GEOMETRY_FAILED"
    elif any(v == "NOT_ESTIMABLE" for v in source_status.values()):
        overall, reason = "NOT_ESTIMABLE", "REQUIRED_SOURCE_GEOMETRY_UNRESOLVED"
    else:
        overall, reason = "PASS", "ALL_REQUIRED_SOURCES_DEFEAT_NULL_AND_MEET_STABILITY_MARGIN"
    return {
        "schema": "JEPA_TD_REAL_GEOMETRY_RECURRENCE_DECISION_V1",
        "status": overall, "reason": reason,
        "metric": metric, "orientation": ORIENTATION,
        "required_sources": sources,
        "source_status": source_status, "source_details": source_details,
        "input_binding_sha256": deciding_binding,
        "noncompensating_across_required_sources": True,
        "claim_boundary": "COMMON_G9_S1_S2_GEOMETRY_ENGINE_ONLY__CANDIDATE_GEOMETRY_BINDING_STILL_REQUIRED",
        "authority": dict(NO_AUTHORITY),
    }


def _qual(ok=True):
    return {"schema": QUAL_SCHEMA, "status": QUAL_PASS if ok else "FAIL_KNOWN_TRUTH_GEOMETRY_RECURRENCE", "known_truth_power_qualified": bool(ok)}


def _rows(*, observed=0.10, null=0.80, n_donors=8, source="SEA_AD", binding="a" * 64):
    return [{
        "source": source,
        "donor_id": f"{source}_D{i:02d}",
        "observed_displacement": observed,
        "null_displacements": [null - 0.02, null, null + 0.02],
        "input_binding_sha256": binding,
    } for i in range(n_donors)]


def _ref(rows, *, refit=0.05, stability=0.20, metric=PROJECTOR_METRIC, binding="a" * 64):
    donors = [r["donor_id"] for r in rows]
    return {
        "schema": REFERENCE_SCHEMA, "frozen": True, "qualified": True,
        "metric": metric, "orientation": ORIENTATION, "deciding_namespace_disjoint": True,
        "input_binding_sha256": binding, "reference_receipt_sha256": "b" * 64,
        "refit_margins": {d: refit for d in donors},
        "stability_margins": {d: stability for d in donors},
    }


def qualify_known_truth_geometry_recurrence() -> dict:
    worlds: dict[str, str] = {}
    a = np.eye(4)[:, :2]
    theta = math.pi / 3
    q = np.asarray([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])
    worlds["ROTATED_SAME_SUBSPACE"] = "PASS" if projector_rms_displacement(a, a @ q) < 1e-10 else "FAIL"
    worlds["ORTHOGONAL_SUBSPACE"] = "PASS" if abs(projector_rms_displacement(a, np.eye(4)[:, 2:]) - 1.0) < 1e-10 else "FAIL"

    recurrent = _rows(observed=0.10, null=0.80, n_donors=8)
    null_shortcut = _rows(observed=0.15, null=0.18, n_donors=8)
    unstable = _rows(observed=0.50, null=0.90, n_donors=8)
    underpowered = _rows(observed=0.10, null=0.80, n_donors=7)
    for name, rows, refit, stability in (
        ("RECURRENT_STABLE", recurrent, 0.05, 0.20),
        ("NULL_SHORTCUT", null_shortcut, 0.10, 0.20),
        ("UNSTABLE_DESPITE_NULL_DEFEAT", unstable, 0.05, 0.20),
        ("UNDERPOWERED_SOURCE", underpowered, 0.05, 0.20),
    ):
        worlds[name] = adjudicate_geometry_recurrence(
            rows=rows,
            metric=PROJECTOR_METRIC,
            required_sources=["SEA_AD"],
            decision_qualification=_qual(True),
            reference_artifact=_ref(rows, refit=refit, stability=stability),
            alpha=0.01,
        )["status"]
    expected = {
        "ROTATED_SAME_SUBSPACE": "PASS",
        "ORTHOGONAL_SUBSPACE": "PASS",
        "RECURRENT_STABLE": "PASS",
        "NULL_SHORTCUT": "FAIL",
        "UNSTABLE_DESPITE_NULL_DEFEAT": "FAIL",
        "UNDERPOWERED_SOURCE": "NOT_ESTIMABLE",
    }
    passed = worlds == expected
    return {
        "schema": QUAL_SCHEMA,
        "status": QUAL_PASS if passed else "FAIL_KNOWN_TRUTH_GEOMETRY_RECURRENCE",
        "known_truth_power_qualified": bool(passed),
        "worlds": worlds,
        "historical_threshold_imported": False,
        "candidate_specific_geometry_frozen": False,
        "authority": dict(NO_AUTHORITY),
    }
