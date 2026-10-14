"""Fail-closed geometry recurrence repair after hostile real-data review.

V2 preserves the useful V1 geometry arithmetic but removes human decision authority
from caller attestations. It also fixes source dropping, component short-circuiting,
alpha mutability, numerical-failure semantics, and orthogonality validation.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence

import numpy as np

from scripts.v5 import td_real_geometry_recurrence_engine_v1 as V1


class GeometryRecurrenceV2Error(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_GEOMETRY_RECURRENCE_DECISION_V2"
FAMILY_ALPHA = 0.01
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SEALED_GEOMETRY_PRODUCER_QUALIFICATION_SHA256: str | None = None

NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _hex(value: object, label: str) -> str:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise GeometryRecurrenceV2Error(f"{label} must be lowercase 64-hex")
    return value


def _token(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise GeometryRecurrenceV2Error(f"{label} must be a nonempty trimmed string")
    return value


def _base(*, status: str, reason: str, diagnostic_status: str | None = None,
          source_diagnostics: dict | None = None, binding: str | None = None) -> dict:
    return {
        "schema": SCHEMA,
        "status": status,
        "reason": reason,
        "diagnostic_status": diagnostic_status,
        "metric": V1.PROJECTOR_METRIC,
        "orientation": V1.ORIENTATION,
        "family_alpha": FAMILY_ALPHA,
        "source_diagnostics": {} if source_diagnostics is None else source_diagnostics,
        "input_binding_sha256": binding,
        "human_pass_fail_authorized": False,
        "claim_boundary": "DIAGNOSTIC_GEOMETRY_ONLY__SEALED_PRODUCER_REQUIRED_FOR_HUMAN_G9_S1_S2",
        "authority": dict(NO_AUTHORITY),
    }


def _sign_tail(successes: int, n: int) -> float:
    if n <= 0:
        return 1.0
    return sum(math.comb(n, k) for k in range(successes, n + 1)) / (2 ** n)


def _signed_component(values: list[float]) -> tuple[str, dict]:
    nonzero = [v for v in values if v != 0.0]
    n = len(nonzero)
    pos = sum(v > 0.0 for v in nonzero)
    neg = sum(v < 0.0 for v in nonzero)
    pos_p = _sign_tail(pos, n)
    neg_p = _sign_tail(neg, n)
    resolution = n > 0 and (0.5 ** n) <= FAMILY_ALPHA
    if resolution and pos_p <= FAMILY_ALPHA and not (neg_p <= FAMILY_ALPHA):
        status = "PASS"
    elif resolution and neg_p <= FAMILY_ALPHA and not (pos_p <= FAMILY_ALPHA):
        status = "FAIL"
    else:
        status = "NOT_ESTIMABLE"
    return status, {
        "n_nonzero": n,
        "positive_count": pos,
        "negative_count": neg,
        "positive_p": pos_p,
        "negative_p": neg_p,
        "alpha": FAMILY_ALPHA,
        "resolution_estimable": resolution,
    }


def validated_aligned_rms_displacement(first, second, transform: Mapping) -> float:
    if not isinstance(transform, Mapping):
        raise GeometryRecurrenceV2Error("alignment transform must be a mapping")
    rotation = np.asarray(transform.get("rotation"), dtype=float)
    n_features = transform.get("n_features")
    if isinstance(n_features, bool) or not isinstance(n_features, int) or n_features <= 0:
        raise GeometryRecurrenceV2Error("alignment n_features is invalid")
    if rotation.shape != (n_features, n_features) or not np.isfinite(rotation).all():
        raise GeometryRecurrenceV2Error("alignment rotation shape is invalid")
    ident = np.eye(n_features)
    if not np.allclose(rotation.T @ rotation, ident, rtol=0.0, atol=1e-10):
        raise GeometryRecurrenceV2Error("alignment rotation must be orthogonal")
    try:
        return V1.aligned_rms_displacement(first, second, transform)
    except V1.GeometryRecurrenceError as exc:
        raise GeometryRecurrenceV2Error(str(exc)) from exc


def _normalize_rows(rows, required_sources: list[str]) -> tuple[list[dict] | None, str | None]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise GeometryRecurrenceV2Error("rows must be a sequence")
    expected = {
        "source", "donor_id", "estimability_status", "estimability_reason",
        "observed_displacement", "null_displacements", "null_semantics",
        "null_producer_receipt_sha256", "input_binding_sha256",
    }
    out: list[dict] = []
    seen_donors: set[str] = set()
    bindings: set[str] = set()
    row_sources: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping) or set(raw) != expected:
            raise GeometryRecurrenceV2Error(f"rows[{index}] fields differ from frozen schema")
        source = _token(raw["source"], "source")
        row_sources.add(source)
        donor = _token(raw["donor_id"], "donor_id")
        if donor in seen_donors:
            raise GeometryRecurrenceV2Error(f"duplicate donor_id: {donor}")
        seen_donors.add(donor)
        binding = _hex(raw["input_binding_sha256"], "input binding")
        _hex(raw["null_producer_receipt_sha256"], "null producer receipt")
        bindings.add(binding)
        status = _token(raw["estimability_status"], "estimability status")
        if status != V1.ESTIMABLE and status not in V1.NONESTIMABLE:
            raise GeometryRecurrenceV2Error("estimability status is not allowed")
        if raw["null_semantics"] != V1.NULL_SEMANTICS:
            raise GeometryRecurrenceV2Error("null semantics mismatch")
        if status == V1.ESTIMABLE:
            observed = raw["observed_displacement"]
            if isinstance(observed, bool) or not isinstance(observed, (int, float, np.integer, np.floating)) or not math.isfinite(float(observed)):
                return None, binding
            if float(observed) < 0:
                raise GeometryRecurrenceV2Error("observed displacement must be nonnegative")
            nulls_raw = raw["null_displacements"]
            if isinstance(nulls_raw, (str, bytes)) or not isinstance(nulls_raw, Sequence) or not nulls_raw:
                raise GeometryRecurrenceV2Error("estimable rows require null displacements")
            nulls = []
            for value in nulls_raw:
                if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)) or not math.isfinite(float(value)):
                    return None, binding
                if float(value) < 0:
                    raise GeometryRecurrenceV2Error("null displacement must be nonnegative")
                nulls.append(float(value))
            reason = raw["estimability_reason"]
            if reason is not None:
                raise GeometryRecurrenceV2Error("estimable rows require estimability_reason=None")
            out.append({"source": source, "donor_id": donor, "status": status,
                        "observed": float(observed), "nulls": nulls})
        else:
            if not isinstance(raw["estimability_reason"], str) or not raw["estimability_reason"].strip():
                raise GeometryRecurrenceV2Error("non-estimable row requires reason")
            if raw["observed_displacement"] is not None or raw["null_displacements"] is not None:
                raise GeometryRecurrenceV2Error("non-estimable row cannot carry fake geometry")
            out.append({"source": source, "donor_id": donor, "status": status,
                        "observed": None, "nulls": None})
    extra = row_sources - set(required_sources)
    if extra:
        raise GeometryRecurrenceV2Error(f"extra source rows are forbidden: {sorted(extra)}")
    if len(bindings) > 1:
        raise GeometryRecurrenceV2Error("all rows must share one exact input binding")
    return out, (next(iter(bindings)) if bindings else None)


def _reference(reference_artifact: Mapping, *, donors: set[str], binding: str | None) -> tuple[dict[str, float] | None, dict[str, float] | None, bool]:
    required = {
        "schema", "frozen", "qualified", "metric", "orientation",
        "deciding_namespace_disjoint", "input_binding_sha256", "reference_receipt_sha256",
        "refit_margins", "stability_margins",
    }
    if not isinstance(reference_artifact, Mapping) or set(reference_artifact) != required:
        raise GeometryRecurrenceV2Error("exact reference artifact required")
    if reference_artifact["schema"] != V1.REFERENCE_SCHEMA:
        raise GeometryRecurrenceV2Error("reference schema mismatch")
    if reference_artifact["frozen"] is not True or reference_artifact["qualified"] is not True:
        raise GeometryRecurrenceV2Error("reference must be frozen and qualified")
    if reference_artifact["metric"] != V1.PROJECTOR_METRIC or reference_artifact["orientation"] != V1.ORIENTATION:
        raise GeometryRecurrenceV2Error("reference metric/orientation mismatch")
    if reference_artifact["deciding_namespace_disjoint"] is not True:
        raise GeometryRecurrenceV2Error("reference namespace must be disjoint")
    ref_binding = _hex(reference_artifact["input_binding_sha256"], "reference input binding")
    _hex(reference_artifact["reference_receipt_sha256"], "reference receipt")
    if binding is not None and ref_binding != binding:
        raise GeometryRecurrenceV2Error("reference input binding mismatch")

    def parse(key: str) -> tuple[dict[str, float] | None, bool]:
        raw = reference_artifact[key]
        if not isinstance(raw, Mapping) or set(raw) != donors:
            raise GeometryRecurrenceV2Error(f"{key} donor roster must match estimable donors exactly")
        out: dict[str, float] = {}
        for donor, value in raw.items():
            if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)) or not math.isfinite(float(value)):
                return None, False
            if float(value) < 0:
                raise GeometryRecurrenceV2Error(f"{key} margins must be nonnegative")
            out[donor] = float(value)
        return out, True

    refit, ok1 = parse("refit_margins")
    stability, ok2 = parse("stability_margins")
    return refit, stability, bool(ok1 and ok2)


def adjudicate_geometry_v2(*, rows, required_sources, reference_artifact,
                            producer_qualification_receipt_sha256=None,
                            alpha: float = FAMILY_ALPHA) -> dict:
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or float(alpha) != FAMILY_ALPHA:
        raise GeometryRecurrenceV2Error(f"alpha is frozen at {FAMILY_ALPHA}")
    if isinstance(required_sources, (str, bytes)) or not isinstance(required_sources, Sequence) or not required_sources:
        raise GeometryRecurrenceV2Error("required_sources must be a nonempty sequence")
    sources = [_token(v, "required source") for v in required_sources]
    if len(set(sources)) != len(sources):
        raise GeometryRecurrenceV2Error("required_sources must be unique")

    normalized, binding = _normalize_rows(rows, sources)
    if normalized is None:
        return _base(status="NUMERICAL_FAILURE", reason="NONFINITE_DECIDING_GEOMETRY", binding=binding)
    estimable = [r for r in normalized if r["status"] == V1.ESTIMABLE]
    donors = {r["donor_id"] for r in estimable}
    refit, stability, reference_finite = _reference(reference_artifact, donors=donors, binding=binding)
    if not reference_finite:
        return _base(status="NUMERICAL_FAILURE", reason="NONFINITE_REFERENCE_GEOMETRY", binding=binding)
    assert refit is not None and stability is not None

    min_null = V1.adverse_null_minimum_draws(FAMILY_ALPHA)
    source_diagnostics: dict[str, dict] = {}
    source_statuses: list[str] = []
    for source in sources:
        all_local = [r for r in normalized if r["source"] == source]
        local = [r for r in all_local if r["status"] == V1.ESTIMABLE]
        if not all_local or not local:
            source_diagnostics[source] = {
                "status": "NOT_ESTIMABLE",
                "null_status": "NOT_ESTIMABLE",
                "stability_status": "NOT_ESTIMABLE",
                "reason": "NO_ESTIMABLE_DONORS_FOR_REQUIRED_SOURCE",
            }
            source_statuses.append("NOT_ESTIMABLE")
            continue

        stability_values = [stability[r["donor_id"]] - r["observed"] for r in local]
        stability_status, stability_test = _signed_component(stability_values)

        if any(len(r["nulls"]) < min_null for r in local):
            null_status = "NOT_ESTIMABLE"
            null_test = {
                "reason": "ADVERSE_NULL_RESOLUTION_INSUFFICIENT",
                "minimum_null_draws_required": min_null,
            }
        else:
            null_values: list[float] = []
            for row in local:
                adverse = V1.lower_adverse_null_bound(row["nulls"], FAMILY_ALPHA)
                if adverse is None:
                    null_status = "NOT_ESTIMABLE"
                    null_test = {"reason": "ADVERSE_NULL_RESOLUTION_INSUFFICIENT"}
                    break
                null_values.append(adverse - row["observed"] - refit[row["donor_id"]])
            else:
                null_status, null_test = _signed_component(null_values)

        if "FAIL" in {null_status, stability_status}:
            source_status = "FAIL"
        elif "NOT_ESTIMABLE" in {null_status, stability_status}:
            source_status = "NOT_ESTIMABLE"
        else:
            source_status = "PASS"
        source_statuses.append(source_status)
        source_diagnostics[source] = {
            "status": source_status,
            "null_status": null_status,
            "stability_status": stability_status,
            "null_test": null_test,
            "stability_test": stability_test,
            "estimable_donor_count": len(local),
            "total_donor_count": len(all_local),
        }

    if any(s == "FAIL" for s in source_statuses):
        diagnostic = "FAIL"
    elif any(s == "NOT_ESTIMABLE" for s in source_statuses):
        diagnostic = "NOT_ESTIMABLE"
    else:
        diagnostic = "PASS"

    frozen = SEALED_GEOMETRY_PRODUCER_QUALIFICATION_SHA256
    if frozen is None:
        return _base(
            status="NOT_ESTIMABLE",
            reason="SEALED_GEOMETRY_PRODUCER_QUALIFICATION_NOT_FROZEN",
            diagnostic_status=diagnostic,
            source_diagnostics=source_diagnostics,
            binding=binding,
        )
    if producer_qualification_receipt_sha256 != frozen:
        return _base(
            status="NOT_ESTIMABLE",
            reason="SEALED_GEOMETRY_PRODUCER_QUALIFICATION_RECEIPT_MISMATCH",
            diagnostic_status=diagnostic,
            source_diagnostics=source_diagnostics,
            binding=binding,
        )
    return _base(
        status="NOT_ESTIMABLE",
        reason="HUMAN_GEOMETRY_MAPPING_NOT_IMPLEMENTED_IN_V2",
        diagnostic_status=diagnostic,
        source_diagnostics=source_diagnostics,
        binding=binding,
    )
