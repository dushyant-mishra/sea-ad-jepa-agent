"""Repaired G2 nontrivial biological-content decision mechanics.

This module preserves the prospectively frozen scientific law recovered from
PR #338/#341 while fail-closing human execution after hostile real-data review.
It is a diagnostic/mechanics layer only. Candidate-specific G2 baseline
applicability and required strata must come from a separately produced static
policy artifact before any human G2 adjudication can be authorized.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence


class G2DecisionV2Error(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_G2_CONTENT_DECISION_V2"
REFERENCE_SCHEMA = "JEPA_TD_REAL_G2_REFERENCE_MARGIN_V2"
METRIC = "HELD_OUT_DONOR_PRIMARY_ENDPOINT_SCORE"
ORIENTATION = "LARGER_IS_BETTER"
G2_GATE_ALPHA = 0.01
SUPPORT_STATES = {"SUPPORTED", "UNSUPPORTED_STRUCTURAL", "BLOCKED_EVIDENCE_CONTRACT"}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_REFERENCE_KINDS = {"U_MEASUREMENT", "MAX_U_REFIT_U_MEASUREMENT"}
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _token(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise G2DecisionV2Error(f"{label} must be a nonempty trimmed NUL-free string")
    return value


def _hex(value: object, label: str) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise G2DecisionV2Error(f"{label} must be lowercase 64-hex")
    return value


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise G2DecisionV2Error(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ArithmeticError(f"{label} is non-finite")
    return result


def minimum_donors_for_one_sided_resolution(alpha: float) -> int:
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)):
        raise G2DecisionV2Error("alpha must be numeric")
    alpha = float(alpha)
    if not math.isfinite(alpha) or not 0.0 < alpha < 1.0:
        raise G2DecisionV2Error("alpha must lie in (0,1)")
    n = 1
    while (0.5 ** n) > alpha:
        n += 1
    return n


def _one_sided_positive_p(positives: int, n_nonzero: int) -> float:
    if n_nonzero == 0:
        return 1.0
    return sum(math.comb(n_nonzero, j) for j in range(positives, n_nonzero + 1)) / (2.0 ** n_nonzero)


def _one_sided_negative_p(negatives: int, n_nonzero: int) -> float:
    if n_nonzero == 0:
        return 1.0
    return sum(math.comb(n_nonzero, j) for j in range(negatives, n_nonzero + 1)) / (2.0 ** n_nonzero)


def _baseline_ids(value) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise G2DecisionV2Error("diagnostic_baseline_ids must be a nonempty sequence")
    out = tuple(_token(item, "baseline id") for item in value)
    if len(set(out)) != len(out):
        raise G2DecisionV2Error("diagnostic baseline IDs must be unique")
    return out


def _required_strata(value) -> tuple[tuple[str, str], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise G2DecisionV2Error("required_strata must be a nonempty sequence")
    out: list[tuple[str, str]] = []
    for item in value:
        if isinstance(item, (str, bytes)) or not isinstance(item, Sequence) or len(item) != 2:
            raise G2DecisionV2Error("each required stratum must be (source, endpoint)")
        out.append((_token(item[0], "required source"), _token(item[1], "required endpoint")))
    if len(set(out)) != len(out):
        raise G2DecisionV2Error("required strata must be unique")
    return tuple(out)


def _unit_key(row: Mapping[str, object]) -> str:
    return f'{row["source"]}::{row["endpoint"]}::{row["donor_id"]}'


def _stratum_key(source: str, endpoint: str) -> str:
    return f"{source}::{endpoint}"


def _normalize_rows(rows, baseline_ids: tuple[str, ...]):
    fields = {
        "source", "endpoint", "donor_id", "candidate_score", "baseline_scores",
        "support_state", "input_binding_sha256",
    }
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise G2DecisionV2Error("rows must be a sequence")
    out: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    bindings: set[str] = set()
    numerical_failure: str | None = None

    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping) or set(raw) != fields:
            raise G2DecisionV2Error(f"rows[{index}] fields differ from frozen schema")
        source = _token(raw["source"], "source")
        endpoint = _token(raw["endpoint"], "endpoint")
        donor = _token(raw["donor_id"], "donor_id")
        key = (source, endpoint, donor)
        if key in seen:
            raise G2DecisionV2Error(f"duplicate source/endpoint/donor row: {key}")
        seen.add(key)
        support = _token(raw["support_state"], "support_state")
        if support not in SUPPORT_STATES:
            raise G2DecisionV2Error(f"unknown support_state: {support}")
        binding = _hex(raw["input_binding_sha256"], "input_binding_sha256")
        bindings.add(binding)

        if support == "SUPPORTED":
            scores = raw["baseline_scores"]
            if not isinstance(scores, Mapping) or set(scores) != set(baseline_ids):
                raise G2DecisionV2Error("supported row baseline family must exactly match diagnostic baseline family")
            try:
                candidate = _finite(raw["candidate_score"], "candidate_score")
                normalized_scores = {
                    _token(name, "baseline id"): _finite(value, f"baseline score {name}")
                    for name, value in scores.items()
                }
            except ArithmeticError as exc:
                numerical_failure = str(exc)
                candidate = None
                normalized_scores = {}
        else:
            # Unsupported/blocking rows are abstentions. No fake numeric score or
            # baseline vector is required merely to satisfy a schema.
            candidate = None
            normalized_scores = {}

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
        raise G2DecisionV2Error("all deciding rows must share one exact input binding")
    deciding_binding = next(iter(bindings)) if bindings else None
    return out, deciding_binding, numerical_failure


def _validate_reference(reference, *, supported_keys: set[str], deciding_binding: str | None):
    fields = {
        "schema", "frozen", "qualified", "metric", "orientation", "reference_kind",
        "input_binding_sha256", "reference_receipt_sha256", "producer_code_sha256", "margins",
    }
    if not isinstance(reference, Mapping) or set(reference) != fields:
        raise G2DecisionV2Error("frozen qualified G2 reference artifact with exact V2 fields is required")
    if reference["schema"] != REFERENCE_SCHEMA:
        raise G2DecisionV2Error("reference schema mismatch")
    if reference["frozen"] is not True or reference["qualified"] is not True:
        raise G2DecisionV2Error("reference must be frozen and qualified")
    if reference["metric"] != METRIC or reference["orientation"] != ORIENTATION:
        raise G2DecisionV2Error("reference metric/orientation mismatch")
    if reference["reference_kind"] not in _ALLOWED_REFERENCE_KINDS:
        return None, "NONDEGENERATE_SUBSTANTIVE_MARGIN_REQUIRED"
    binding = _hex(reference["input_binding_sha256"], "reference input binding")
    _hex(reference["reference_receipt_sha256"], "reference receipt")
    _hex(reference["producer_code_sha256"], "producer code")
    if deciding_binding is not None and binding != deciding_binding:
        raise G2DecisionV2Error("reference input binding must equal exact deciding input binding")
    raw = reference["margins"]
    if not isinstance(raw, Mapping):
        raise G2DecisionV2Error("reference margins must be a mapping")
    if set(raw) != supported_keys:
        raise G2DecisionV2Error("reference margin units must exactly match supported deciding units")
    margins: dict[str, float] = {}
    try:
        for key, value in raw.items():
            unit = _token(key, "reference unit key")
            margins[unit] = _finite(value, "reference margin")
    except ArithmeticError:
        return None, "NUMERICAL_FAILURE"
    if any(value <= 0.0 for value in margins.values()):
        return None, "NONDEGENERATE_SUBSTANTIVE_MARGIN_REQUIRED"
    return margins, None


def _diagnose_adjusted_deltas(deltas: Sequence[float]) -> dict:
    positives = sum(value > 0.0 for value in deltas)
    negatives = sum(value < 0.0 for value in deltas)
    ties = sum(value == 0.0 for value in deltas)
    n_nonzero = positives + negatives
    min_n = minimum_donors_for_one_sided_resolution(G2_GATE_ALPHA)
    p_pos = _one_sided_positive_p(positives, n_nonzero)
    p_neg = _one_sided_negative_p(negatives, n_nonzero)

    if n_nonzero >= min_n and positives > negatives and p_pos <= G2_GATE_ALPHA:
        status, reason = "PASS", "POSITIVE_MARGIN_ADJUSTED_RECURRENCE"
    elif n_nonzero >= min_n and negatives > positives and p_neg <= G2_GATE_ALPHA:
        status, reason = "FAIL", "ESTIMABLY_NONPOSITIVE"
    elif len(deltas) >= min_n and positives == 0 and all(value <= 0.0 for value in deltas):
        # Exact equality to the substantive margin is not evidence of a positive
        # biological increment. A fully observed nonpositive donor set is a FAIL,
        # not an artificial NE created by dropping zero ties from the sign count.
        status, reason = "FAIL", "ESTIMABLY_NONPOSITIVE"
    else:
        status, reason = "NOT_ESTIMABLE", "DIRECTION_NOT_RESOLVED_AT_FROZEN_ALPHA"

    return {
        "status": status,
        "reason": reason,
        "n_total_donors": len(deltas),
        "n_nonzero_donors": n_nonzero,
        "n_positive_donors": positives,
        "n_negative_donors": negatives,
        "n_tied_donors": ties,
        "minimum_nonzero_donors_for_resolution": min_n,
        "one_sided_positive_p": p_pos,
        "one_sided_negative_p": p_neg,
        "alpha": G2_GATE_ALPHA,
    }


def adjudicate_g2_mechanics_v2(*, rows, required_strata, diagnostic_baseline_ids, reference_artifact) -> dict:
    baseline_ids = _baseline_ids(diagnostic_baseline_ids)
    strata = _required_strata(required_strata)
    normalized, deciding_binding, numerical_failure = _normalize_rows(rows, baseline_ids)

    stratum_set = set(strata)
    extras = sorted({(row["source"], row["endpoint"]) for row in normalized} - stratum_set)
    if extras:
        raise G2DecisionV2Error(f"extra stratum rows are forbidden: {extras}")

    if numerical_failure is not None:
        return {
            "schema": SCHEMA,
            "status": "NUMERICAL_FAILURE",
            "reason": numerical_failure,
            "failed_biology": False,
            "mechanics_only": True,
            "human_g2_adjudication_authorized": False,
            "authority": dict(NO_AUTHORITY),
        }

    supported_keys = {_unit_key(row) for row in normalized if row["support_state"] == "SUPPORTED"}
    margins, reference_problem = _validate_reference(
        reference_artifact,
        supported_keys=supported_keys,
        deciding_binding=deciding_binding,
    )
    if reference_problem == "NUMERICAL_FAILURE":
        return {
            "schema": SCHEMA,
            "status": "NUMERICAL_FAILURE",
            "reason": "NONFINITE_REFERENCE_MARGIN",
            "failed_biology": False,
            "mechanics_only": True,
            "human_g2_adjudication_authorized": False,
            "authority": dict(NO_AUTHORITY),
        }
    if reference_problem is not None:
        return {
            "schema": SCHEMA,
            "status": "NOT_ESTIMABLE",
            "reason": reference_problem,
            "failed_biology": False,
            "mechanics_only": True,
            "human_g2_adjudication_authorized": False,
            "authority": dict(NO_AUTHORITY),
        }
    assert margins is not None

    stratum_status: dict[str, str] = {}
    details: dict[str, dict] = {}
    for source, endpoint in strata:
        name = _stratum_key(source, endpoint)
        local = [row for row in normalized if row["source"] == source and row["endpoint"] == endpoint]
        supported = [row for row in local if row["support_state"] == "SUPPORTED"]
        abstained = [row for row in local if row["support_state"] != "SUPPORTED"]
        if not supported:
            stratum_status[name] = "NOT_ESTIMABLE"
            details[name] = {
                "reason": "NO_SUPPORTED_DECIDING_DONORS",
                "supported_donor_count": 0,
                "abstained_donor_count": len(abstained),
                "n_tied_donors": 0,
                "one_sided_positive_p": 1.0,
                "one_sided_negative_p": 1.0,
            }
            continue

        adjusted: list[float] = []
        donor_details: list[dict] = []
        for row in supported:
            strongest_score = max(row["baseline_scores"].values())
            strongest_ids = sorted(
                baseline_id for baseline_id, score in row["baseline_scores"].items()
                if score == strongest_score
            )
            margin = margins[_unit_key(row)]
            delta = row["candidate_score"] - strongest_score - margin
            adjusted.append(delta)
            donor_details.append({
                "donor_id": row["donor_id"],
                "candidate_score": row["candidate_score"],
                "strongest_baseline_ids": strongest_ids,
                "strongest_baseline_score": strongest_score,
                "reference_margin": margin,
                "advantage_minus_margin": delta,
            })
        diagnosis = _diagnose_adjusted_deltas(adjusted)
        stratum_status[name] = diagnosis["status"]
        details[name] = {
            **diagnosis,
            "supported_donor_count": len(supported),
            "abstained_donor_count": len(abstained),
            "donor_details": donor_details,
        }

    if any(status == "FAIL" for status in stratum_status.values()):
        overall, reason = "FAIL", "REQUIRED_G2_STRATUM_ESTIMABLY_NONPOSITIVE"
    elif any(status == "NOT_ESTIMABLE" for status in stratum_status.values()):
        overall, reason = "NOT_ESTIMABLE", "REQUIRED_G2_STRATUM_UNRESOLVED"
    else:
        overall, reason = "PASS", "ALL_DIAGNOSTIC_G2_STRATA_POSITIVE_BEYOND_MARGIN"

    return {
        "schema": SCHEMA,
        "status": overall,
        "reason": reason,
        "failed_biology": overall == "FAIL",
        "metric": METRIC,
        "orientation": ORIENTATION,
        "gate_alpha": G2_GATE_ALPHA,
        "diagnostic_baseline_ids": list(baseline_ids),
        "required_strata": [list(item) for item in strata],
        "stratum_status": stratum_status,
        "stratum_details": details,
        "input_binding_sha256": deciding_binding,
        "mechanics_only": True,
        "human_g2_adjudication_authorized": False,
        "authority": dict(NO_AUTHORITY),
    }


def human_execution_readiness(*, policy_artifact) -> dict:
    # A caller-typed policy is intentionally not inspected for authority. The
    # future policy must be produced from the frozen candidate registry, support
    # registry and endpoint contract under a separate qualification surface.
    return {
        "schema": "JEPA_TD_REAL_G2_HUMAN_READINESS_V2",
        "status": "BLOCKED_G2_STATIC_POLICY_NOT_PRODUCED_AND_QUALIFIED",
        "reason": (
            "CANDIDATE_SPECIFIC_G2_APPLICABLE_BASELINE_AND_REQUIRED_STRATA_POLICY_MUST_BE_"
            "PRODUCED_FROM_FROZEN_REGISTRIES__CALLER_POLICY_HAS_NO_HUMAN_AUTHORITY"
        ),
        "caller_baseline_family_has_human_authority": False,
        "caller_required_strata_have_human_authority": False,
        "caller_alpha_has_human_authority": False,
        "typed_policy_artifact_has_human_authority": False,
        "human_g2_adjudication_authorized": False,
        "frozen_gate_alpha": G2_GATE_ALPHA,
        "policy_dependency": "STATIC_CANDIDATE_SPECIFIC_G2_POLICY_FROM_FROZEN_CANDIDATE_SUPPORT_AND_ENDPOINT_REGISTRIES",
        "authority": dict(NO_AUTHORITY),
    }
