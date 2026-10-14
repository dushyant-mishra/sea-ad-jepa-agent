"""Outcome-blind common recurrence/stability mechanics for G9/S1/S2.

This module qualifies a reusable geometry decision engine before candidate-specific
human execution. It separates invariant geometry measurement, train-only alignment,
adverse-null recurrence, absolute stability, and lawful support abstention.

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
NULL_SEMANTICS = "DONOR_PRESERVING_IDENTITY_SHUFFLE_LOWER_ADVERSE_BOUND"
ESTIMABLE = "ESTIMABLE"
NONESTIMABLE = {
    "NOT_ESTIMABLE_STRUCTURAL_SUPPORT",
    "NOT_ESTIMABLE_COLLISION_UNRESOLVED",
}
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
    except Exception as exc:
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
    left = _orthonormal_columns(first, "first basis")
    right = _orthonormal_columns(second, "second basis")
    if left.shape != right.shape:
        raise GeometryRecurrenceError("subspace bases must have identical ambient dimension and rank")
    singular = np.linalg.svd(left.T @ right, compute_uv=False)
    singular = np.clip(singular, 0.0, 1.0)
    return float(np.sqrt(np.mean(np.maximum(0.0, 1.0 - singular * singular))))


def fit_train_only_procrustes(*, train_a, train_b, train_unit_ids, heldout_unit_ids) -> dict:
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
    u, _, vt = np.linalg.svd((a - mean_a).T @ (b - mean_b), full_matrices=False)
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
    return float(np.sqrt(np.mean((mapped - b) ** 2)))


def adverse_null_minimum_draws(alpha: float) -> int:
    a = _number(alpha, "alpha")
    if not 0 < a < 1:
        raise GeometryRecurrenceError("alpha must lie in (0,1)")
    return int(math.ceil(1.0 / a))


def lower_adverse_null_bound(values, alpha: float) -> float | None:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or not values:
        raise GeometryRecurrenceError("null_displacements must be a nonempty sequence")
    vals = sorted(_number(v, "null displacement", nonnegative=True) for v in values)
    if len(vals) < adverse_null_minimum_draws(alpha):
        return None
    rank = max(1, int(math.ceil(float(alpha) * len(vals))))
    return vals[rank - 1]


def _qualification_valid(value) -> bool:
    return bool(
        isinstance(value, Mapping)
        and value.get("schema") == QUAL_SCHEMA
        and value.get("status") == QUAL_PASS
        and value.get("known_truth_power_qualified") is True
    )


def _normalize_rows(rows) -> tuple[list[dict], str | None, str | None]:
    fields = {
        "source", "donor_id", "estimability_status", "estimability_reason",
        "observed_displacement", "null_displacements", "null_semantics",
        "null_producer_receipt_sha256", "input_binding_sha256",
    }
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise GeometryRecurrenceError("rows must be a sequence")
    out = []
    seen_donors = set()
    bindings = set()
    null_receipts = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping) or set(raw) != fields:
            raise GeometryRecurrenceError(f"rows[{index}] fields differ from frozen schema")
        source = _token(raw["source"], "source")
        donor = _token(raw["donor_id"], "donor_id")
        if donor in seen_donors:
            raise GeometryRecurrenceError(f"duplicate donor_id across geometry rows: {donor}")
        seen_donors.add(donor)
        status = _token(raw["estimability_status"], "estimability_status")
        if status != ESTIMABLE and status not in NONESTIMABLE:
            raise GeometryRecurrenceError("estimability_status is not allowed")
        reason = raw["estimability_reason"]
        if status == ESTIMABLE:
            if reason is not None:
                raise GeometryRecurrenceError("estimable rows must have estimability_reason=None")
            observed = _number(raw["observed_displacement"], "observed_displacement", nonnegative=True)
            nulls_raw = raw["null_displacements"]
            if isinstance(nulls_raw, (str, bytes)) or not isinstance(nulls_raw, Sequence) or not nulls_raw:
                raise GeometryRecurrenceError("estimable rows require nonempty null_displacements")
            nulls = [_number(v, "null displacement", nonnegative=True) for v in nulls_raw]
        else:
            if not isinstance(reason, str) or not reason.strip():
                raise GeometryRecurrenceError("non-estimable rows require a reason")
            if raw["observed_displacement"] is not None or raw["null_displacements"] is not None:
                raise GeometryRecurrenceError("non-estimable rows may not carry fake numeric geometry")
            observed, nulls = None, None
        if raw["null_semantics"] != NULL_SEMANTICS:
            raise GeometryRecurrenceError("null semantics differ from frozen donor-preserving adverse-null law")
        receipt = _hex(raw["null_producer_receipt_sha256"], "null_producer_receipt_sha256")
        binding = _hex(raw["input_binding_sha256"], "input_binding_sha256")
        null_receipts.add(receipt)
        bindings.add(binding)
        out.append({
            "source": source, "donor_id": donor,
            "estimability_status": status, "estimability_reason": reason,
            "observed_displacement": observed, "null_displacements": nulls,
            "null_semantics": NULL_SEMANTICS,
            "null_producer_receipt_sha256": receipt,
            "input_binding_sha256": binding,
        })
    if len(bindings) > 1:
        raise GeometryRecurrenceError("all deciding rows must share one exact input binding")
    if len(null_receipts) > 1:
        raise GeometryRecurrenceError("all rows must bind the same frozen null producer receipt")
    return out, (next(iter(bindings)) if bindings else None), (next(iter(null_receipts)) if null_receipts else None)


def _required_sources(value) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise GeometryRecurrenceError("required_sources must be a nonempty sequence")
    out = [_token(v, "required source") for v in value]
    if len(set(out)) != len(out):
        raise GeometryRecurrenceError("required_sources must be unique")
    return out


def _validate_reference(reference, *, estimable_donors: set[str], metric: str, deciding_binding: str | None) -> tuple[dict[str, float], dict[str, float]]:
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
        if set(out) != estimable_donors:
            raise GeometryRecurrenceError(f"{key} estimable donor roster must match deciding estimable donor roster exactly")
        return out
    return margins("refit_margins"), margins("stability_margins")


def adjudicate_geometry_recurrence(*, rows, metric, required_sources, decision_qualification, reference_artifact, alpha: float = 0.01) -> dict:
    metric = _token(metric, "metric")
    alpha_value = _number(alpha, "alpha")
    if not 0 < alpha_value < 1:
        raise GeometryRecurrenceError("alpha must lie in (0,1)")
    normalized, deciding_binding, null_receipt = _normalize_rows(rows)
    sources = _required_sources(required_sources)
    if not _qualification_valid(decision_qualification):
        return {
            "schema": "JEPA_TD_REAL_GEOMETRY_RECURRENCE_DECISION_V1",
            "status": "NOT_ESTIMABLE", "reason": "DECISION_KNOWN_TRUTH_NOT_QUALIFIED",
            "metric": metric, "source_status": {}, "source_details": {},
            "input_binding_sha256": deciding_binding,
            "null_producer_receipt_sha256": null_receipt,
            "authority": dict(NO_AUTHORITY),
        }
    estimable_donor_set = {r["donor_id"] for r in normalized if r["estimability_status"] == ESTIMABLE}
    refit_margins, stability_margins = _validate_reference(
        reference_artifact,
        estimable_donors=estimable_donor_set,
        metric=metric,
        deciding_binding=deciding_binding,
    )

    source_status = {}
    source_details = {}
    min_null = adverse_null_minimum_draws(alpha_value)
    for source in sources:
        all_local = [r for r in normalized if r["source"] == source]
        local = [r for r in all_local if r["estimability_status"] == ESTIMABLE]
        abstained = [r for r in all_local if r["estimability_status"] != ESTIMABLE]
        base_counts = {
            "total_donor_count": len(all_local),
            "estimable_donor_count": len(local),
            "abstained_donor_count": len(abstained),
            "abstention_reasons": sorted({r["estimability_reason"] for r in abstained}),
        }
        if not all_local:
            source_status[source] = "NOT_ESTIMABLE"
            source_details[source] = {
                "reason": "NO_DECIDING_DONORS_FOR_REQUIRED_SOURCE",
                "null_defeat_status": "NOT_ESTIMABLE", "stability_status": "NOT_ESTIMABLE",
                "failed_biology": False, **base_counts,
            }
            continue
        if any(len(r["null_displacements"]) < min_null for r in local):
            source_status[source] = "NOT_ESTIMABLE"
            source_details[source] = {
                "reason": "ADVERSE_NULL_RESOLUTION_INSUFFICIENT",
                "null_defeat_status": "NOT_ESTIMABLE", "stability_status": "NOT_ESTIMABLE",
                "minimum_null_draws_required": min_null, "failed_biology": False, **base_counts,
            }
            continue
        if not local:
            source_status[source] = "NOT_ESTIMABLE"
            source_details[source] = {
                "reason": "NO_ESTIMABLE_DONORS_AFTER_SUPPORT_ABSTENTION",
                "null_defeat_status": "NOT_ESTIMABLE", "stability_status": "NOT_ESTIMABLE",
                "failed_biology": False, **base_counts,
            }
            continue

        null_rows = []
        stability_rows = []
        donor_details = []
        for row in local:
            donor = row["donor_id"]
            observed = row["observed_displacement"]
            adverse = lower_adverse_null_bound(row["null_displacements"], alpha_value)
            if adverse is None:
                raise AssertionError("null resolution checked before donor loop")
            null_adjusted = adverse - observed - refit_margins[donor]
            stability_adjusted = stability_margins[donor] - observed
            null_rows.append({"donor_id": donor, "delta": null_adjusted})
            stability_rows.append({"donor_id": donor, "delta": stability_adjusted})
            donor_details.append({
                "donor_id": donor,
                "observed_displacement": observed,
                "adverse_null_bound": adverse,
                "adverse_null_alpha": alpha_value,
                "null_draw_count": len(row["null_displacements"]),
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
            "reason": (
                "BOTH_COMPONENTS_PASS" if status == "PASS"
                else "GEOMETRY_COMPONENT_FAILED" if status == "FAIL"
                else "DONOR_SIGN_RESOLUTION_INSUFFICIENT"
            ),
            "failed_biology": status == "FAIL",
            "null_defeat_status": null_status,
            "stability_status": stable_status,
            "null_defeat_sign_test": null_gate,
            "stability_sign_test": stability_gate,
            "donors": donor_details,
            **base_counts,
        }

    if any(v == "FAIL" for v in source_status.values()):
        overall, reason = "FAIL", "REQUIRED_SOURCE_GEOMETRY_FAILED"
    elif any(v == "NOT_ESTIMABLE" for v in source_status.values()):
        overall, reason = "NOT_ESTIMABLE", "REQUIRED_SOURCE_GEOMETRY_UNRESOLVED"
    else:
        overall, reason = "PASS", "ALL_REQUIRED_SOURCES_DEFEAT_ADVERSE_NULL_AND_MEET_STABILITY_MARGIN"
    return {
        "schema": "JEPA_TD_REAL_GEOMETRY_RECURRENCE_DECISION_V1",
        "status": overall,
        "reason": reason,
        "metric": metric,
        "orientation": ORIENTATION,
        "null_semantics": NULL_SEMANTICS,
        "required_sources": sources,
        "source_status": source_status,
        "source_details": source_details,
        "input_binding_sha256": deciding_binding,
        "null_producer_receipt_sha256": null_receipt,
        "noncompensating_across_required_sources": True,
        "claim_boundary": "COMMON_G9_S1_S2_GEOMETRY_ENGINE_ONLY__CANDIDATE_GEOMETRY_BINDING_STILL_REQUIRED",
        "authority": dict(NO_AUTHORITY),
    }


def _qual(ok=True):
    return {"schema": QUAL_SCHEMA, "status": QUAL_PASS if ok else "FAIL_KNOWN_TRUTH_GEOMETRY_RECURRENCE", "known_truth_power_qualified": bool(ok)}


def _nulls(center, n=100, spread=0.02):
    return [center - spread + (2.0 * spread * i / max(n - 1, 1)) for i in range(n)]


def _rows(*, observed=0.10, null=0.80, n_donors=8, source="SEA_AD", binding="a" * 64, n_null=100):
    return [{
        "source": source,
        "donor_id": f"{source}_D{i:02d}",
        "estimability_status": ESTIMABLE,
        "estimability_reason": None,
        "observed_displacement": observed,
        "null_displacements": _nulls(null, n=n_null),
        "null_semantics": NULL_SEMANTICS,
        "null_producer_receipt_sha256": "c" * 64,
        "input_binding_sha256": binding,
    } for i in range(n_donors)]


def _ref(rows, *, refit=0.05, stability=0.20, metric=PROJECTOR_METRIC, binding="a" * 64):
    donors = [r["donor_id"] for r in rows if r["estimability_status"] == ESTIMABLE]
    return {
        "schema": REFERENCE_SCHEMA,
        "frozen": True,
        "qualified": True,
        "metric": metric,
        "orientation": ORIENTATION,
        "deciding_namespace_disjoint": True,
        "input_binding_sha256": binding,
        "reference_receipt_sha256": "b" * 64,
        "refit_margins": {d: refit for d in donors},
        "stability_margins": {d: stability for d in donors},
    }


def qualify_known_truth_geometry_recurrence() -> dict:
    worlds = {}
    a = np.eye(4)[:, :2]
    theta = math.pi / 3
    q = np.asarray([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])
    worlds["ROTATED_SAME_SUBSPACE"] = "PASS" if projector_rms_displacement(a, a @ q) < 1e-10 else "FAIL"
    worlds["ORTHOGONAL_SUBSPACE"] = "PASS" if abs(projector_rms_displacement(a, np.eye(4)[:, 2:]) - 1.0) < 1e-10 else "FAIL"
    fixtures = {
        "RECURRENT_STABLE": (_rows(observed=0.10, null=0.80), 0.05, 0.20),
        "NULL_SHORTCUT": (_rows(observed=0.15, null=0.18), 0.10, 0.20),
        "UNSTABLE_DESPITE_NULL_DEFEAT": (_rows(observed=0.50, null=0.90), 0.05, 0.20),
        "UNDERPOWERED_SOURCE": (_rows(observed=0.10, null=0.80, n_donors=7), 0.05, 0.20),
        "UNDERRESOLVED_NULL": (_rows(observed=0.10, null=0.80, n_null=99), 0.05, 0.20),
    }
    for name, (rows, refit, stability) in fixtures.items():
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
        "UNDERRESOLVED_NULL": "NOT_ESTIMABLE",
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
