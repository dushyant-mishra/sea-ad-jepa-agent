"""Source-aware terminal evidence-convergence adjudicator for real-TD G7.

V3 preserves V2's evidence-right semantics, same-metric reference binding,
known-truth qualification and donor-primary sign recurrence, while making
required-source noncompensation explicit and self-enforcing.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence

from scripts.v5 import td_target_tournament_precision as P


class G7DecisionError(ValueError):
    pass


QUAL_SCHEMA = "JEPA_TD_REAL_G7_TERMINAL_DECISION_QUALIFICATION_V3"
QUAL_PASS = "PASS_KNOWN_TRUTH_G7_TERMINAL_DECISION_V3"
REFERENCE_SCHEMA = "JEPA_TD_REAL_G7_TERMINAL_REFERENCE_MARGIN_V2"
METRIC = "TERMINAL_PENULTIMATE_TO_FULL_DISPLACEMENT"
ORIENTATION = "SMALLER_IS_MORE_CONVERGED"
REFERENCE_KINDS = {"U_REFIT", "U_MEASUREMENT", "MAX_U_REFIT_U_MEASUREMENT"}
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
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise G7DecisionError(f"{label} must be finite numeric")
    out = float(value)
    if not math.isfinite(out):
        raise G7DecisionError(f"{label} must be finite numeric")
    if nonnegative and out < 0.0:
        raise G7DecisionError(f"{label} must be nonnegative")
    return out


def _token(value, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise G7DecisionError(f"{label} must be a nonempty trimmed string")
    return value


def _hex(value, label: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise G7DecisionError(f"{label} must be lowercase 64-hex")
    return value


def _qualification_valid(value) -> bool:
    return bool(
        isinstance(value, Mapping)
        and value.get("schema") == QUAL_SCHEMA
        and value.get("status") == QUAL_PASS
        and value.get("known_truth_power_qualified") is True
    )


def _normalize_required_sources(required_sources) -> list[str]:
    if isinstance(required_sources, (str, bytes)) or not isinstance(required_sources, Sequence):
        raise G7DecisionError("required_sources must be a sequence")
    normalized = [_token(value, "required source") for value in required_sources]
    if not normalized:
        raise G7DecisionError("required_sources must not be empty")
    if len(set(normalized)) != len(normalized):
        raise G7DecisionError("required_sources must be unique")
    return sorted(normalized)


def _normalize_rows(rows):
    fields = {
        "source",
        "donor_id",
        "terminal_displacement",
        "penultimate_supported_evidence",
        "full_supported_evidence",
        "added_supported_evidence",
        "input_binding_sha256",
    }
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise G7DecisionError("rows must be a sequence")
    out = []
    seen: set[tuple[str, str]] = set()
    bindings: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping) or set(raw) != fields:
            raise G7DecisionError(f"rows[{index}] fields differ from frozen schema")
        source = _token(raw["source"], "source")
        donor = _token(raw["donor_id"], "donor_id")
        key = (source, donor)
        if key in seen:
            raise G7DecisionError(f"duplicate source/donor unit: {source}/{donor}")
        seen.add(key)
        binding = _hex(raw["input_binding_sha256"], "input_binding_sha256")
        bindings.add(binding)
        displacement = _number(raw["terminal_displacement"], "terminal_displacement", nonnegative=True)
        pen = raw["penultimate_supported_evidence"]
        full = raw["full_supported_evidence"]
        added = raw["added_supported_evidence"]
        for label, value in (
            ("penultimate support", pen),
            ("full support", full),
            ("added support", added),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise G7DecisionError(f"{label} must be a nonnegative integer")
        if full < pen:
            raise G7DecisionError("full support cannot be lower than penultimate support")
        if added != full - pen:
            raise G7DecisionError("added support must equal full support minus penultimate support")
        out.append(
            {
                "source": source,
                "donor_id": donor,
                "terminal_displacement": displacement,
                "penultimate_supported_evidence": pen,
                "full_supported_evidence": full,
                "added_supported_evidence": added,
                "input_binding_sha256": binding,
            }
        )
    if len(bindings) > 1:
        raise G7DecisionError("all rows must bind a single deciding input realization")
    return out, (next(iter(bindings)) if bindings else None)


def _unit_key(source: str, donor: str) -> str:
    return f"{source}::{donor}"


def _reference(reference, deciding_units: set[str], deciding_binding: str | None) -> dict[str, float]:
    required = {
        "schema",
        "frozen",
        "qualified",
        "metric",
        "orientation",
        "reference_kind",
        "deciding_namespace_disjoint",
        "input_binding_sha256",
        "reference_receipt_sha256",
        "unit_margins",
    }
    if not isinstance(reference, Mapping) or set(reference) != required:
        raise G7DecisionError("a frozen qualified reference artifact with exact fields is required")
    if reference["schema"] != REFERENCE_SCHEMA:
        raise G7DecisionError("reference schema mismatch")
    if reference["frozen"] is not True or reference["qualified"] is not True:
        raise G7DecisionError("reference artifact must be frozen and qualified")
    if reference["metric"] != METRIC:
        raise G7DecisionError("reference metric is not commensurate with G7 terminal displacement")
    if reference["orientation"] != ORIENTATION:
        raise G7DecisionError("reference orientation mismatch")
    if reference["reference_kind"] not in REFERENCE_KINDS:
        raise G7DecisionError("reference_kind is not allowed")
    if reference["deciding_namespace_disjoint"] is not True:
        raise G7DecisionError("reference and deciding namespaces must be disjoint")
    ref_binding = _hex(reference["input_binding_sha256"], "reference input_binding_sha256")
    _hex(reference["reference_receipt_sha256"], "reference_receipt_sha256")
    if deciding_binding is not None and ref_binding != deciding_binding:
        raise G7DecisionError("reference input binding must equal the exact deciding input binding")
    raw = reference["unit_margins"]
    if not isinstance(raw, Mapping):
        raise G7DecisionError("reference unit_margins must be a mapping")
    margins = {
        _token(key, "reference source/donor unit"): _number(value, f"reference margin {key}", nonnegative=True)
        for key, value in raw.items()
    }
    if set(margins) != deciding_units:
        raise G7DecisionError("reference margin roster must match deciding source/donor units exactly")
    return margins


def adjudicate_g7_terminal_v3(
    *, rows, required_sources, decision_qualification, reference_artifact, alpha: float = 0.01
) -> dict:
    alpha_value = _number(alpha, "alpha")
    if not 0.0 < alpha_value < 1.0:
        raise G7DecisionError("alpha must lie in (0,1)")
    required = _normalize_required_sources(required_sources)
    normalized, deciding_binding = _normalize_rows(rows)

    if not _qualification_valid(decision_qualification):
        return {
            "schema": "JEPA_TD_REAL_G7_TERMINAL_DECISION_V3",
            "status": "NOT_ESTIMABLE",
            "reason": "DECISION_KNOWN_TRUTH_NOT_QUALIFIED",
            "source_status": {},
            "source_details": {},
            "authority": dict(NO_AUTHORITY),
        }

    observed_sources = {row["source"] for row in normalized}
    extra_sources = observed_sources - set(required)
    if extra_sources:
        raise G7DecisionError("rows contain source values outside the frozen required_sources roster")

    deciding_units = {_unit_key(row["source"], row["donor_id"]) for row in normalized}
    margins = _reference(reference_artifact, deciding_units, deciding_binding)

    by_source = defaultdict(list)
    for row in normalized:
        by_source[row["source"]].append(row)

    source_status: dict[str, str] = {}
    source_details: dict[str, dict] = {}
    for source in required:
        source_rows = by_source.get(source, [])
        if not source_rows:
            source_status[source] = "NOT_ESTIMABLE"
            source_details[source] = {
                "reason": "REQUIRED_SOURCE_ABSENT",
                "donor_count": 0,
                "donors_with_added_support": 0,
                "donor_contrasts": [],
                "sign_test": None,
            }
            continue

        supported = [row for row in source_rows if row["added_supported_evidence"] > 0]
        if not supported:
            source_status[source] = "NOT_ESTIMABLE"
            source_details[source] = {
                "reason": "NO_DONORS_WITH_ADDED_SUPPORTED_EVIDENCE",
                "donor_count": len(source_rows),
                "donors_with_added_support": 0,
                "donor_contrasts": [],
                "sign_test": None,
            }
            continue

        contrasts = [
            {
                "source": source,
                "donor_id": row["donor_id"],
                "terminal_displacement": row["terminal_displacement"],
                "substantive_margin": margins[_unit_key(source, row["donor_id"])],
                "margin_adjusted_convergence": margins[_unit_key(source, row["donor_id"])] - row["terminal_displacement"],
                "added_supported_evidence": row["added_supported_evidence"],
            }
            for row in supported
        ]
        sign = P.sign_recurrence_gate(
            [{"donor_id": row["donor_id"], "delta": row["margin_adjusted_convergence"]} for row in contrasts],
            alpha_value,
        )
        if not sign["resolution_estimable"]:
            status, reason = "NOT_ESTIMABLE", "DONOR_SIGN_RESOLUTION_INSUFFICIENT"
        elif sign["pass"]:
            status, reason = "PASS", "TERMINAL_CHANGE_WITHIN_QUALIFIED_MARGIN"
        else:
            status, reason = "FAIL", "TERMINAL_CHANGE_EXCEEDS_QUALIFIED_MARGIN"
        source_status[source] = status
        source_details[source] = {
            "reason": reason,
            "donor_count": len(source_rows),
            "donors_with_added_support": len(supported),
            "donor_contrasts": contrasts,
            "sign_test": sign,
        }

    if any(status == "FAIL" for status in source_status.values()):
        overall_status, overall_reason = "FAIL", "REQUIRED_SOURCE_NONCONVERGENCE"
    elif any(status == "NOT_ESTIMABLE" for status in source_status.values()):
        overall_status, overall_reason = "NOT_ESTIMABLE", "REQUIRED_SOURCE_NOT_ESTIMABLE"
    else:
        overall_status, overall_reason = "PASS", "ALL_REQUIRED_SOURCES_CONVERGED"

    return {
        "schema": "JEPA_TD_REAL_G7_TERMINAL_DECISION_V3",
        "status": overall_status,
        "reason": overall_reason,
        "metric": METRIC,
        "orientation": ORIENTATION,
        "reference_kind": reference_artifact["reference_kind"],
        "required_sources": required,
        "input_binding_sha256": deciding_binding,
        "source_status": source_status,
        "source_details": source_details,
        "claim_boundary": "TERMINAL_EVIDENCE_CONVERGENCE_ONLY__NO_ADJACENT_MONOTONICITY__NO_DEPTH_SUBSTITUTION__REQUIRED_SOURCES_NONCOMPENSATING",
        "authority": dict(NO_AUTHORITY),
    }


def _qual(ok=True):
    return {
        "schema": QUAL_SCHEMA,
        "status": QUAL_PASS if ok else "FAIL_KNOWN_TRUTH_G7_V3",
        "known_truth_power_qualified": bool(ok),
    }


def _rows(source, n=8, displacement=0.02, added=1, binding="1" * 64):
    return [
        {
            "source": source,
            "donor_id": f"{source}_D{i:02d}",
            "terminal_displacement": displacement,
            "penultimate_supported_evidence": 10,
            "full_supported_evidence": 10 + added,
            "added_supported_evidence": added,
            "input_binding_sha256": binding,
        }
        for i in range(n)
    ]


def _ref(rows, margin=0.1, binding="1" * 64):
    return {
        "schema": REFERENCE_SCHEMA,
        "frozen": True,
        "qualified": True,
        "metric": METRIC,
        "orientation": ORIENTATION,
        "reference_kind": "U_REFIT",
        "deciding_namespace_disjoint": True,
        "input_binding_sha256": binding,
        "reference_receipt_sha256": "2" * 64,
        "unit_margins": {_unit_key(row["source"], row["donor_id"]): margin for row in rows},
    }


def qualify_known_truth_g7_v3() -> dict:
    worlds: dict[str, str] = {}
    fixtures = {
        "ALL_REQUIRED_SOURCES_CONVERGED": (_rows("SEA_AD") + _rows("NPH52"), ["SEA_AD", "NPH52"]),
        "ONE_SOURCE_NONCONVERGED": (_rows("SEA_AD") + _rows("NPH52", displacement=0.5), ["SEA_AD", "NPH52"]),
        "ONE_SOURCE_UNDERPOWERED": (_rows("SEA_AD") + _rows("HVS", n=7), ["SEA_AD", "HVS"]),
        "ONE_SOURCE_NO_ADDED_SUPPORT": (_rows("SEA_AD") + _rows("HVS", displacement=0.0, added=0), ["SEA_AD", "HVS"]),
        "MISSING_REQUIRED_SOURCE": (_rows("SEA_AD"), ["SEA_AD", "NPH52"]),
    }
    for name, (rows, sources) in fixtures.items():
        worlds[name] = adjudicate_g7_terminal_v3(
            rows=rows,
            required_sources=sources,
            decision_qualification=_qual(),
            reference_artifact=_ref(rows),
            alpha=0.01,
        )["status"]
    expected = {
        "ALL_REQUIRED_SOURCES_CONVERGED": "PASS",
        "ONE_SOURCE_NONCONVERGED": "FAIL",
        "ONE_SOURCE_UNDERPOWERED": "NOT_ESTIMABLE",
        "ONE_SOURCE_NO_ADDED_SUPPORT": "NOT_ESTIMABLE",
        "MISSING_REQUIRED_SOURCE": "NOT_ESTIMABLE",
    }
    passed = worlds == expected
    return {
        "schema": QUAL_SCHEMA,
        "status": QUAL_PASS if passed else "FAIL_KNOWN_TRUTH_G7_V3",
        "known_truth_power_qualified": bool(passed),
        "worlds": worlds,
        "synthetic_margin_has_human_threshold_authority": False,
        "authority": dict(NO_AUTHORITY),
    }
