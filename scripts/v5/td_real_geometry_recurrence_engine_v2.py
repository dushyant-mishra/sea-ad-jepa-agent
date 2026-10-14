"""Geometry recurrence V2 trust-boundary consumer.

Consumes authenticated producer/support/reference/qualification artifacts.  It
cannot manufacture candidate geometry or support labels and keeps all human TD
authority closed.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence

from scripts.v5 import td_target_tournament_precision as P
from scripts.v5.td_real_geometry_recurrence_engine_v1 import lower_adverse_null_bound

FAMILY_ALPHA = 0.01
METRIC = "PROJECTOR_RMS_PRINCIPAL_ANGLE_DISPLACEMENT"
ORIENTATION = "SMALLER_DISPLACEMENT_IS_MORE_STABLE"
NULL_SEMANTICS = "DONOR_PRESERVING_IDENTITY_SHUFFLE_LOWER_ADVERSE_BOUND"
PRODUCER_SCHEMA = "JEPA_TD_REAL_GEOMETRY_PRODUCER_RECEIPT_V2"
SUPPORT_SCHEMA = "JEPA_TD_REAL_GEOMETRY_SUPPORT_ENVELOPE_V2"
REFERENCE_SCHEMA = "JEPA_TD_REAL_GEOMETRY_REFERENCE_MARGIN_V2"
QUAL_SCHEMA = "JEPA_TD_REAL_GEOMETRY_DECISION_QUALIFICATION_RECEIPT_V2"
QUAL_STATUS = "PASS_KNOWN_TRUTH_GEOMETRY_RECURRENCE_V2"
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
NONESTIMABLE = {"NOT_ESTIMABLE_STRUCTURAL_SUPPORT", "NOT_ESTIMABLE_COLLISION_UNRESOLVED"}


def _hash(v) -> bool:
    return isinstance(v, str) and HEX64.fullmatch(v) is not None


def _token(v) -> bool:
    return isinstance(v, str) and bool(v) and v == v.strip() and "\0" not in v


def _ne(reason: str, *, details=None) -> dict:
    return {
        "schema": "JEPA_TD_REAL_GEOMETRY_RECURRENCE_DECISION_V2",
        "status": "NOT_ESTIMABLE",
        "reason": reason,
        "source_status": {},
        "source_details": details or {},
        "family_alpha": FAMILY_ALPHA,
        "authority": dict(NO_AUTHORITY),
    }


def _validate_required_sources(value) -> list[str] | None:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        return None
    out = list(value)
    if any(not _token(v) for v in out) or len(set(out)) != len(out):
        return None
    return out


def _validate_producer(receipt, required_sources: list[str]):
    fields = {
        "schema", "receipt_sha256", "producer_code_sha256", "producer_qualification_receipt_sha256",
        "input_binding_sha256", "metric", "orientation", "null_semantics",
        "heldout_used_for_fit", "leakage_guard_qualified", "eigengap_policy_sha256",
        "null_namespace_sha256", "required_sources", "support_envelope_receipt_sha256",
    }
    if not isinstance(receipt, Mapping) or set(receipt) != fields:
        return None
    if receipt.get("schema") != PRODUCER_SCHEMA:
        return None
    for key in (
        "receipt_sha256", "producer_code_sha256", "producer_qualification_receipt_sha256",
        "input_binding_sha256", "eigengap_policy_sha256", "null_namespace_sha256",
        "support_envelope_receipt_sha256",
    ):
        if not _hash(receipt.get(key)):
            return None
    if receipt.get("metric") != METRIC or receipt.get("orientation") != ORIENTATION or receipt.get("null_semantics") != NULL_SEMANTICS:
        return None
    if receipt.get("heldout_used_for_fit") is not False or receipt.get("leakage_guard_qualified") is not True:
        return None
    if receipt.get("required_sources") != required_sources:
        return None
    return dict(receipt)


def _validate_support(envelope, producer, required_sources: list[str]):
    fields = {"schema", "receipt_sha256", "frozen_before_values", "source_donor_status"}
    if not isinstance(envelope, Mapping) or set(envelope) != fields:
        return None
    if envelope.get("schema") != SUPPORT_SCHEMA or envelope.get("frozen_before_values") is not True:
        return None
    if envelope.get("receipt_sha256") != producer["support_envelope_receipt_sha256"] or not _hash(envelope.get("receipt_sha256")):
        return None
    raw = envelope.get("source_donor_status")
    if not isinstance(raw, Mapping) or set(raw) != set(required_sources):
        return None
    out = {}
    for source in required_sources:
        donors = raw[source]
        if not isinstance(donors, Mapping) or not donors:
            return None
        local = {}
        for donor, status in donors.items():
            if not _token(donor) or status not in ({"ESTIMABLE"} | NONESTIMABLE):
                return None
            local[donor] = status
        out[source] = local
    return out


def _validate_qualification(receipt) -> bool:
    fields = {
        "schema", "status", "producer_code_sha256", "qualification_worlds_sha256",
        "receipt_sha256", "human_semantics_qualified",
    }
    return bool(
        isinstance(receipt, Mapping)
        and set(receipt) == fields
        and receipt.get("schema") == QUAL_SCHEMA
        and receipt.get("status") == QUAL_STATUS
        and receipt.get("human_semantics_qualified") is True
        and all(_hash(receipt.get(k)) for k in ("producer_code_sha256", "qualification_worlds_sha256", "receipt_sha256"))
    )


def _validate_reference(reference, producer, support_receipt: str, donors: set[str]):
    fields = {
        "schema", "frozen", "qualified", "metric", "orientation", "input_binding_sha256",
        "reference_receipt_sha256", "producer_receipt_sha256", "support_envelope_receipt_sha256",
        "refit_margins", "stability_margins",
    }
    if not isinstance(reference, Mapping) or set(reference) != fields:
        return None
    if reference.get("schema") != REFERENCE_SCHEMA or reference.get("frozen") is not True or reference.get("qualified") is not True:
        return None
    if reference.get("metric") != METRIC or reference.get("orientation") != ORIENTATION:
        return None
    if reference.get("input_binding_sha256") != producer["input_binding_sha256"] or not _hash(reference.get("input_binding_sha256")):
        return None
    if reference.get("producer_receipt_sha256") != producer["receipt_sha256"]:
        return None
    if reference.get("support_envelope_receipt_sha256") != support_receipt:
        return None
    if not _hash(reference.get("reference_receipt_sha256")):
        return None
    results = []
    for key in ("refit_margins", "stability_margins"):
        raw = reference.get(key)
        if not isinstance(raw, Mapping) or set(raw) != donors:
            return None
        vals = {}
        for donor, value in raw.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return None
            value = float(value)
            if not math.isfinite(value) or value < 0.0:
                return None
            vals[donor] = value
        results.append(vals)
    return tuple(results)


def _component(rows) -> str:
    gate = P.sign_recurrence_gate(rows, FAMILY_ALPHA)
    if not gate["resolution_estimable"]:
        return "NOT_ESTIMABLE"
    return "PASS" if gate["pass"] else "FAIL"


def adjudicate_geometry_recurrence_v2(*, rows, required_sources, producer_receipt, support_envelope, reference_artifact, decision_qualification_receipt) -> dict:
    sources = _validate_required_sources(required_sources)
    if sources is None:
        return _ne("REQUIRED_SOURCES_NOT_FROZEN")
    producer = _validate_producer(producer_receipt, sources)
    if producer is None:
        return _ne("GEOMETRY_PRODUCER_RECEIPT_NOT_QUALIFIED")
    support = _validate_support(support_envelope, producer, sources)
    if support is None:
        return _ne("SUPPORT_ENVELOPE_NOT_AUTHENTICATED")
    if not _validate_qualification(decision_qualification_receipt):
        return _ne("DECISION_QUALIFICATION_RECEIPT_NOT_AUTHENTICATED")
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        return _ne("DECIDING_ROWS_INVALID")

    row_sources = {r.get("source") for r in rows if isinstance(r, Mapping)}
    if not row_sources.issubset(set(sources)):
        return _ne("UNDECLARED_SOURCE_ROWS_PRESENT")

    normalized = []
    seen = set()
    for raw in rows:
        fields = {
            "source", "donor_id", "estimability_status", "estimability_reason",
            "geometry_conditioning_status", "observed_displacement", "null_displacements",
            "null_unique_nonidentity_draws", "producer_receipt_sha256", "input_binding_sha256",
        }
        if not isinstance(raw, Mapping) or set(raw) != fields:
            return _ne("DECIDING_ROWS_INVALID")
        source, donor = raw["source"], raw["donor_id"]
        if not _token(source) or not _token(donor) or (source, donor) in seen:
            return _ne("DECIDING_ROWS_INVALID")
        seen.add((source, donor))
        if source not in support or donor not in support[source]:
            return _ne("ROW_DONOR_OUTSIDE_FROZEN_SUPPORT_ENVELOPE")
        if raw["estimability_status"] != support[source][donor]:
            return _ne("ROW_SUPPORT_STATUS_MISMATCHES_FROZEN_ENVELOPE")
        if raw["producer_receipt_sha256"] != producer["receipt_sha256"] or raw["input_binding_sha256"] != producer["input_binding_sha256"]:
            return _ne("ROW_PRODUCER_OR_INPUT_BINDING_MISMATCH")
        status = raw["estimability_status"]
        cond = raw["geometry_conditioning_status"]
        if status == "ESTIMABLE":
            if cond != "WELL_CONDITIONED":
                if raw["observed_displacement"] is not None or raw["null_displacements"] is not None:
                    return _ne("DEGENERATE_GEOMETRY_CARRIES_NUMERIC_DECISION_VALUES")
                return _ne("DEGENERATE_GEOMETRY_NOT_ESTIMABLE")
            obs = raw["observed_displacement"]
            nulls = raw["null_displacements"]
            n_unique = raw["null_unique_nonidentity_draws"]
            if isinstance(obs, bool) or not isinstance(obs, (int, float)) or not math.isfinite(float(obs)) or float(obs) < 0:
                return _ne("DECIDING_ROWS_INVALID")
            if isinstance(nulls, (str, bytes)) or not isinstance(nulls, Sequence) or not nulls:
                return _ne("DECIDING_ROWS_INVALID")
            vals = []
            for v in nulls:
                if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)) or float(v) < 0:
                    return _ne("DECIDING_ROWS_INVALID")
                vals.append(float(v))
            if isinstance(n_unique, bool) or not isinstance(n_unique, int) or n_unique < 0 or n_unique > len(vals):
                return _ne("DECIDING_ROWS_INVALID")
            normalized.append({"source": source, "donor_id": donor, "observed": float(obs), "nulls": vals, "n_unique": n_unique})
        else:
            if raw["observed_displacement"] is not None or raw["null_displacements"] is not None or raw["null_unique_nonidentity_draws"] != 0:
                return _ne("NONESTIMABLE_ROW_CARRIES_NUMERIC_DECISION_VALUES")

    for source in sources:
        if {d for s, d in seen if s == source} != set(support[source]):
            return _ne("FROZEN_SUPPORT_ENVELOPE_DONOR_MISSING_FROM_ROWS")

    estimable_donors = {r["donor_id"] for r in normalized}
    ref = _validate_reference(reference_artifact, producer, support_envelope["receipt_sha256"], estimable_donors)
    if ref is None:
        return _ne("REFERENCE_ARTIFACT_NOT_AUTHENTICATED")
    refit, stability = ref

    source_status = {}
    source_details = {}
    for source in sources:
        local = [r for r in normalized if r["source"] == source]
        stability_rows = [
            {"donor_id": r["donor_id"], "delta": stability[r["donor_id"]] - r["observed"]}
            for r in local
        ]
        stability_status = _component(stability_rows) if stability_rows else "NOT_ESTIMABLE"

        null_underresolved = any(r["n_unique"] < math.ceil(1.0 / FAMILY_ALPHA) for r in local)
        if null_underresolved or not local:
            null_status = "NOT_ESTIMABLE"
        else:
            null_rows = []
            for r in local:
                adverse = lower_adverse_null_bound(r["nulls"], FAMILY_ALPHA)
                if adverse is None:
                    null_status = "NOT_ESTIMABLE"
                    break
                null_rows.append({"donor_id": r["donor_id"], "delta": adverse - r["observed"] - refit[r["donor_id"]]})
            else:
                null_status = _component(null_rows)
        if "FAIL" in {stability_status, null_status}:
            status = "FAIL"
        elif "NOT_ESTIMABLE" in {stability_status, null_status}:
            status = "NOT_ESTIMABLE"
        else:
            status = "PASS"
        source_status[source] = status
        source_details[source] = {
            "stability_status": stability_status,
            "null_defeat_status": null_status,
            "estimable_donor_count": len(local),
        }

    if any(v == "FAIL" for v in source_status.values()):
        overall, reason = "FAIL", "REQUIRED_SOURCE_GEOMETRY_FAILED"
    elif any(v == "NOT_ESTIMABLE" for v in source_status.values()):
        overall, reason = "NOT_ESTIMABLE", "REQUIRED_SOURCE_GEOMETRY_UNRESOLVED"
    else:
        overall, reason = "PASS", "ALL_REQUIRED_SOURCES_PASS"
    return {
        "schema": "JEPA_TD_REAL_GEOMETRY_RECURRENCE_DECISION_V2",
        "status": overall,
        "reason": reason,
        "metric": METRIC,
        "orientation": ORIENTATION,
        "family_alpha": FAMILY_ALPHA,
        "required_sources": sources,
        "source_status": source_status,
        "source_details": source_details,
        "producer_receipt_sha256": producer["receipt_sha256"],
        "support_envelope_receipt_sha256": support_envelope["receipt_sha256"],
        "authority": dict(NO_AUTHORITY),
    }
