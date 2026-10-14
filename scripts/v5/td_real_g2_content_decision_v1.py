"""Outcome-blind G2 nontrivial biological-content decision mechanics.

This module qualifies only the decision machinery. It does not read human
candidate outcomes and cannot authorize real TD or target selection.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence

from scripts.v5 import td_target_tournament_precision as P


class G2DecisionError(ValueError):
    pass


QUAL_SCHEMA = "JEPA_TD_REAL_G2_CONTENT_QUALIFICATION_V1"
QUAL_PASS = "PASS_KNOWN_TRUTH_G2"
REFERENCE_SCHEMA = "JEPA_TD_REAL_G2_REFERENCE_MARGIN_V1"
METRIC = "HELD_OUT_DONOR_PRIMARY_ENDPOINT_SCORE"
ORIENTATION = "LARGER_IS_BETTER"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SUPPORT_STATES = {"SUPPORTED", "UNSUPPORTED_STRUCTURAL", "BLOCKED_EVIDENCE_CONTRACT"}
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise G2DecisionError(f"{label} must be finite numeric")
    out = float(value)
    if not math.isfinite(out):
        raise G2DecisionError(f"{label} must be finite numeric")
    return out


def _token(value, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise G2DecisionError(f"{label} must be a nonempty trimmed NUL-free string")
    return value


def _hex(value, label: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise G2DecisionError(f"{label} must be lowercase 64-hex")
    return value


def _unit_key(row: Mapping) -> str:
    return f'{row["source"]}::{row["endpoint"]}::{row["donor_id"]}'


def _stratum_key(source: str, endpoint: str) -> str:
    return f"{source}::{endpoint}"


def _baseline_ids(value) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise G2DecisionError("frozen baseline ids must be a nonempty sequence")
    out = tuple(_token(v, "baseline id") for v in value)
    if len(set(out)) != len(out):
        raise G2DecisionError("frozen baseline ids must be unique")
    return out


def _required_strata(value) -> tuple[tuple[str, str], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise G2DecisionError("required_strata must be a nonempty sequence")
    out = []
    for item in value:
        if isinstance(item, (str, bytes)) or not isinstance(item, Sequence) or len(item) != 2:
            raise G2DecisionError("each required stratum must be (source, endpoint)")
        source = _token(item[0], "required source")
        endpoint = _token(item[1], "required endpoint")
        out.append((source, endpoint))
    if len(set(out)) != len(out):
        raise G2DecisionError("required_strata must be unique")
    return tuple(out)


def _normalize_rows(rows, baseline_ids: tuple[str, ...]) -> tuple[list[dict], str | None]:
    fields = {
        "source", "endpoint", "donor_id", "candidate_score", "baseline_scores",
        "support_state", "input_binding_sha256",
    }
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise G2DecisionError("rows must be a sequence")
    out = []
    seen = set()
    bindings = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping) or set(raw) != fields:
            raise G2DecisionError(f"rows[{index}] fields differ from frozen schema")
        source = _token(raw["source"], "source")
        endpoint = _token(raw["endpoint"], "endpoint")
        donor = _token(raw["donor_id"], "donor_id")
        key = (source, endpoint, donor)
        if key in seen:
            raise G2DecisionError(f"duplicate source/endpoint/donor row: {key}")
        seen.add(key)
        support = _token(raw["support_state"], "support_state")
        if support not in SUPPORT_STATES:
            raise G2DecisionError(f"unknown support_state: {support}")
        binding = _hex(raw["input_binding_sha256"], "input_binding_sha256")
        bindings.add(binding)
        candidate = _number(raw["candidate_score"], "candidate_score")
        scores = raw["baseline_scores"]
        if not isinstance(scores, Mapping):
            raise G2DecisionError("baseline_scores must be a mapping")
        if support == "SUPPORTED" and set(scores) != set(baseline_ids):
            raise G2DecisionError("supported row baseline family must exactly match frozen baseline ids")
        normalized_scores = {}
        for baseline_id, value in scores.items():
            baseline = _token(baseline_id, "baseline id")
            if baseline not in baseline_ids:
                raise G2DecisionError("baseline score contains non-frozen baseline")
            normalized_scores[baseline] = _number(value, f"baseline score {baseline}")
        out.append({
            "source": source,
            "endpoint": endpoint,
            "donor_id": donor,
            "candidate_score": candidate,
            "baseline_scores": normalized_scores,
            "support_state": support,
            "input_binding_sha256": binding,
        })
    if len(bindings) > 1:
        raise G2DecisionError("all deciding rows must share one exact input binding")
    return out, (next(iter(bindings)) if bindings else None)


def _qualification_valid(value) -> bool:
    return bool(
        isinstance(value, Mapping)
        and value.get("schema") == QUAL_SCHEMA
        and value.get("status") == QUAL_PASS
        and value.get("known_truth_power_qualified") is True
    )


def _validate_reference(reference, *, supported_unit_keys: set[str], deciding_binding: str | None) -> dict[str, float]:
    required = {
        "schema", "frozen", "qualified", "metric", "orientation",
        "input_binding_sha256", "reference_namespace_disjoint", "reference_receipt_sha256",
        "margins",
    }
    if not isinstance(reference, Mapping) or set(reference) != required:
        raise G2DecisionError("a frozen qualified G2 reference artifact with exact fields is required")
    if reference["schema"] != REFERENCE_SCHEMA:
        raise G2DecisionError("reference schema mismatch")
    if reference["frozen"] is not True or reference["qualified"] is not True:
        raise G2DecisionError("reference artifact must be frozen and qualified")
    if reference["metric"] != METRIC or reference["orientation"] != ORIENTATION:
        raise G2DecisionError("reference metric/orientation mismatch")
    if reference["reference_namespace_disjoint"] is not True:
        raise G2DecisionError("reference and deciding namespaces must be disjoint")
    ref_binding = _hex(reference["input_binding_sha256"], "reference input binding")
    _hex(reference["reference_receipt_sha256"], "reference receipt")
    if deciding_binding is not None and ref_binding != deciding_binding:
        raise G2DecisionError("reference input binding must equal exact deciding input binding")
    raw_margins = reference["margins"]
    if not isinstance(raw_margins, Mapping):
        raise G2DecisionError("reference margins must be a mapping")
    margins = {
        _token(key, "reference unit key"): _number(value, "reference margin")
        for key, value in raw_margins.items()
    }
    if any(value < 0 for value in margins.values()):
        raise G2DecisionError("reference margins must be nonnegative")
    if set(margins) != supported_unit_keys:
        raise G2DecisionError("reference margin units must exactly match supported deciding source/endpoint/donor units")
    return margins


def _component_status(stats: Mapping) -> str:
    if not stats["resolution_estimable"]:
        return "NOT_ESTIMABLE"
    return "PASS" if stats["pass"] else "FAIL"


def _combine_noncompensating(statuses: Sequence[str]) -> str:
    if "FAIL" in statuses:
        return "FAIL"
    if "NOT_ESTIMABLE" in statuses:
        return "NOT_ESTIMABLE"
    return "PASS"


def adjudicate_g2(
    *, rows, required_strata, frozen_baseline_ids, decision_qualification,
    reference_artifact, alpha: float = 0.01,
) -> dict:
    alpha_value = _number(alpha, "alpha")
    if not 0 < alpha_value < 1:
        raise G2DecisionError("alpha must lie in (0,1)")
    baseline_ids = _baseline_ids(frozen_baseline_ids)
    strata = _required_strata(required_strata)
    normalized, deciding_binding = _normalize_rows(rows, baseline_ids)

    if not _qualification_valid(decision_qualification):
        return {
            "schema": "JEPA_TD_REAL_G2_CONTENT_DECISION_V1",
            "status": "NOT_ESTIMABLE",
            "reason": "DECISION_KNOWN_TRUTH_NOT_QUALIFIED",
            "stratum_status": {},
            "stratum_details": {},
            "input_binding_sha256": deciding_binding,
            "authority": dict(NO_AUTHORITY),
        }

    supported_unit_keys = {
        _unit_key(row) for row in normalized if row["support_state"] == "SUPPORTED"
    }
    margins = _validate_reference(
        reference_artifact,
        supported_unit_keys=supported_unit_keys,
        deciding_binding=deciding_binding,
    )

    stratum_status = {}
    stratum_details = {}
    for source, endpoint in strata:
        name = _stratum_key(source, endpoint)
        local = [row for row in normalized if row["source"] == source and row["endpoint"] == endpoint]
        supported = [row for row in local if row["support_state"] == "SUPPORTED"]
        abstained = [row for row in local if row["support_state"] != "SUPPORTED"]
        if not supported:
            status = "NOT_ESTIMABLE"
            stratum_status[name] = status
            stratum_details[name] = {
                "reason": "NO_SUPPORTED_DECIDING_DONORS",
                "supported_donor_count": 0,
                "abstained_donor_count": len(abstained),
                "strongest_baseline_ids": [],
            }
            continue

        donor_rows = []
        strongest_ids = []
        donor_details = []
        for row in supported:
            scores = row["baseline_scores"]
            strongest_score = max(scores.values())
            strongest_id = sorted(
                baseline_id for baseline_id, score in scores.items() if score == strongest_score
            )[0]
            margin = margins[_unit_key(row)]
            raw_advantage = row["candidate_score"] - strongest_score
            adjusted = raw_advantage - margin
            donor_rows.append({"donor_id": row["donor_id"], "delta": adjusted})
            strongest_ids.append(strongest_id)
            donor_details.append({
                "donor_id": row["donor_id"],
                "candidate_score": row["candidate_score"],
                "strongest_baseline_id": strongest_id,
                "strongest_baseline_score": strongest_score,
                "reference_margin": margin,
                "advantage_minus_margin": adjusted,
            })
        stats = P.sign_recurrence_gate(donor_rows, alpha_value)
        status = _component_status(stats)
        stratum_status[name] = status
        stratum_details[name] = {
            "supported_donor_count": len(supported),
            "abstained_donor_count": len(abstained),
            "strongest_baseline_ids": strongest_ids,
            "donor_details": donor_details,
            "raw_sufficient_statistics": dict(stats),
        }

    overall = _combine_noncompensating(list(stratum_status.values()))
    return {
        "schema": "JEPA_TD_REAL_G2_CONTENT_DECISION_V1",
        "status": overall,
        "metric": METRIC,
        "orientation": ORIENTATION,
        "frozen_baseline_ids": list(baseline_ids),
        "stratum_status": stratum_status,
        "stratum_details": stratum_details,
        "input_binding_sha256": deciding_binding,
        "authority": dict(NO_AUTHORITY),
    }


def qualify_known_truth_g2() -> dict:
    baseline_ids = ("constant_train_mean", "technical_operator_only", "address_support_operator")
    binding = "1" * 64

    def rows(candidate: float, donors: int = 8, unsupported: int = 0):
        out = []
        for i in range(donors):
            out.append({
                "source": "SYNTH",
                "endpoint": "PRIMARY",
                "donor_id": f"D{i:02d}",
                "candidate_score": candidate,
                "baseline_scores": {name: 0.20 for name in baseline_ids},
                "support_state": "UNSUPPORTED_STRUCTURAL" if i < unsupported else "SUPPORTED",
                "input_binding_sha256": binding,
            })
        return out

    qual = {"schema": QUAL_SCHEMA, "status": QUAL_PASS, "known_truth_power_qualified": True}

    def reference(current_rows, margin: float = 0.10):
        return {
            "schema": REFERENCE_SCHEMA,
            "frozen": True,
            "qualified": True,
            "metric": METRIC,
            "orientation": ORIENTATION,
            "input_binding_sha256": binding,
            "reference_namespace_disjoint": True,
            "reference_receipt_sha256": "2" * 64,
            "margins": {
                _unit_key(row): margin
                for row in current_rows
                if row["support_state"] == "SUPPORTED"
            },
        }

    worlds = {}
    cases = {
        "BIOLOGICAL_SIGNAL_BEYOND_BASELINES": rows(0.80),
        "SHORTCUT_ONLY": rows(0.20),
        "TINY_ADVANTAGE_BELOW_MARGIN": rows(0.26),
        "UNDERPOWERED_SUPPORTED_DONORS": rows(0.80, donors=6),
        "STRUCTURAL_SUPPORT_LOSS": rows(0.80, donors=8, unsupported=2),
    }
    for name, current_rows in cases.items():
        result = adjudicate_g2(
            rows=current_rows,
            required_strata=[("SYNTH", "PRIMARY")],
            frozen_baseline_ids=baseline_ids,
            decision_qualification=qual,
            reference_artifact=reference(current_rows),
            alpha=0.01,
        )
        worlds[name] = result["status"]

    expected = {
        "BIOLOGICAL_SIGNAL_BEYOND_BASELINES": "PASS",
        "SHORTCUT_ONLY": "FAIL",
        "TINY_ADVANTAGE_BELOW_MARGIN": "FAIL",
        "UNDERPOWERED_SUPPORTED_DONORS": "NOT_ESTIMABLE",
        "STRUCTURAL_SUPPORT_LOSS": "NOT_ESTIMABLE",
    }
    qualified = worlds == expected
    return {
        "schema": QUAL_SCHEMA,
        "status": QUAL_PASS if qualified else "FAIL_KNOWN_TRUTH_G2",
        "known_truth_power_qualified": qualified,
        "worlds": worlds,
        "authority": dict(NO_AUTHORITY),
    }
