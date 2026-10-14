"""Fail-closed G2 content-decision repair after hostile real-data review.

V2 derives the complete nuisance/falsifier family from the frozen production
candidate registry, binds all deciding rows to a frozen claim envelope, requires
a nondegenerate independent same-metric margin, and separates positive,
negative, and inconclusive donor recurrence. It does not authorize human G2.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence


class G2DecisionV2Error(ValueError):
    pass


FAMILY_ALPHA = 0.01
METRIC = "HELD_OUT_DONOR_PRIMARY_ENDPOINT_SCORE"
ORIENTATION = "LARGER_IS_BETTER"
REFERENCE_SCHEMA = "JEPA_TD_REAL_G2_REFERENCE_MARGIN_V2"
ENVELOPE_SCHEMA = "JEPA_TD_REAL_G2_CLAIM_ENVELOPE_V2"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SUPPORT_STATES = {"SUPPORTED", "UNSUPPORTED_STRUCTURAL", "BLOCKED_EVIDENCE_CONTRACT"}
SEALED_G2_DECISION_QUALIFICATION_SHA256: str | None = None

BASELINES_BY_CANDIDATE = {
    "C1_SHARED_EMERGENT": (
        "constant_train_mean", "technical_operator_only", "address_support_operator",
        "matched_wrong_cell", "identity_support_only",
    ),
    "C2_RELATIONAL_SHARED": (
        "constant_train_mean", "technical_operator_only", "address_support_operator",
        "matched_wrong_cell", "fine_neighborhood_wrong_cell", "identity_support_only",
    ),
    "C3_QUERY_MEASURED": (
        "constant_train_mean", "technical_operator_only", "address_support_operator",
        "matched_wrong_cell", "q_count_only", "q_address_only", "query_agnostic",
        "wrong_q", "technical_plus_q", "q_excluded_teacher",
    ),
    "C6_SHARED_QUERY_COMPOSITE": (
        "constant_train_mean", "technical_operator_only", "address_support_operator",
        "matched_wrong_cell", "identity_support_only", "q_count_only", "q_address_only",
        "query_agnostic", "wrong_q", "technical_plus_q", "q_excluded_teacher",
    ),
    "C4_STRUCTURED_COMPOSITE": (
        "constant_train_mean", "technical_operator_only", "address_support_operator",
        "matched_wrong_cell", "fine_neighborhood_wrong_cell", "identity_support_only",
        "q_count_only", "q_address_only", "query_agnostic", "wrong_q",
        "technical_plus_q", "q_excluded_teacher",
    ),
    "C5_REGULATORY_SPECIALIST": (
        "constant_train_mean", "technical_operator_only", "address_support_operator",
        "matched_wrong_cell",
    ),
}

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
        raise G2DecisionV2Error(f"{label} must be lowercase 64-hex")
    return value


def _token(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise G2DecisionV2Error(f"{label} must be a nonempty trimmed string")
    return value


def baseline_ids_for_candidate(candidate_id: str) -> tuple[str, ...]:
    candidate_id = _token(candidate_id, "candidate_id")
    if candidate_id not in BASELINES_BY_CANDIDATE:
        raise G2DecisionV2Error(f"unknown candidate_id: {candidate_id}")
    return BASELINES_BY_CANDIDATE[candidate_id]


def _unit_key(source: str, endpoint: str, donor: str) -> str:
    return f"{source}::{endpoint}::{donor}"


def _base(*, status: str, reason: str, binding: str | None,
          diagnostic_status: str | None = None, stratum_details: dict | None = None) -> dict:
    return {
        "schema": "JEPA_TD_REAL_G2_CONTENT_DECISION_V2",
        "status": status,
        "reason": reason,
        "diagnostic_status": diagnostic_status,
        "metric": METRIC,
        "orientation": ORIENTATION,
        "family_alpha": FAMILY_ALPHA,
        "input_binding_sha256": binding,
        "stratum_details": {} if stratum_details is None else stratum_details,
        "human_pass_fail_authorized": False,
        "authority": dict(NO_AUTHORITY),
    }


def _validate_envelope(envelope: Mapping, *, candidate_id: str) -> tuple[dict[str, dict], str]:
    required = {
        "schema", "candidate_id", "input_binding_sha256",
        "claim_envelope_receipt_sha256", "frozen_before_values", "units",
    }
    if not isinstance(envelope, Mapping) or set(envelope) != required:
        raise G2DecisionV2Error("exact claim envelope fields required")
    if envelope["schema"] != ENVELOPE_SCHEMA or envelope["candidate_id"] != candidate_id:
        raise G2DecisionV2Error("claim envelope candidate/schema mismatch")
    if envelope["frozen_before_values"] is not True:
        raise G2DecisionV2Error("claim envelope must be frozen before values")
    binding = _hex(envelope["input_binding_sha256"], "claim envelope input binding")
    _hex(envelope["claim_envelope_receipt_sha256"], "claim envelope receipt")
    units = envelope["units"]
    if isinstance(units, (str, bytes)) or not isinstance(units, Sequence) or not units:
        raise G2DecisionV2Error("claim envelope units must be nonempty")
    out: dict[str, dict] = {}
    for raw in units:
        if not isinstance(raw, Mapping) or set(raw) != {"source", "endpoint", "donor_id", "support_state"}:
            raise G2DecisionV2Error("claim envelope unit fields differ from schema")
        source = _token(raw["source"], "source")
        endpoint = _token(raw["endpoint"], "endpoint")
        donor = _token(raw["donor_id"], "donor_id")
        support = _token(raw["support_state"], "support_state")
        if support not in SUPPORT_STATES:
            raise G2DecisionV2Error("claim envelope support state invalid")
        key = _unit_key(source, endpoint, donor)
        if key in out:
            raise G2DecisionV2Error("claim envelope unit roster contains duplicates")
        out[key] = {"source": source, "endpoint": endpoint, "donor_id": donor, "support_state": support}
    return out, binding


def _normalize_rows(rows, *, candidate_id: str, envelope_units: dict[str, dict], binding: str):
    baselines = baseline_ids_for_candidate(candidate_id)
    fields = {
        "source", "endpoint", "donor_id", "candidate_score", "baseline_scores",
        "support_state", "input_binding_sha256",
    }
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise G2DecisionV2Error("rows must be a sequence")
    normalized = {}
    numerical_failure = False
    for raw in rows:
        if not isinstance(raw, Mapping) or set(raw) != fields:
            raise G2DecisionV2Error("deciding row fields differ from schema")
        source = _token(raw["source"], "source")
        endpoint = _token(raw["endpoint"], "endpoint")
        donor = _token(raw["donor_id"], "donor_id")
        key = _unit_key(source, endpoint, donor)
        if key not in envelope_units:
            raise G2DecisionV2Error("deciding unit not present in claim envelope")
        if key in normalized:
            raise G2DecisionV2Error("duplicate deciding unit")
        if _hex(raw["input_binding_sha256"], "row input binding") != binding:
            raise G2DecisionV2Error("row input binding differs from claim envelope")
        support = _token(raw["support_state"], "support_state")
        if support != envelope_units[key]["support_state"]:
            raise G2DecisionV2Error("row support state differs from frozen claim envelope support state")
        scores = raw["baseline_scores"]
        if not isinstance(scores, Mapping) or set(scores) != set(baselines):
            raise G2DecisionV2Error("supported row baseline family must exactly match frozen candidate baseline family")
        candidate = raw["candidate_score"]
        if isinstance(candidate, bool) or not isinstance(candidate, (int, float)) or not math.isfinite(float(candidate)):
            numerical_failure = True
            candidate_value = None
        else:
            candidate_value = float(candidate)
        norm_scores = {}
        for baseline in baselines:
            value = scores[baseline]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                numerical_failure = True
                norm_scores[baseline] = None
            else:
                norm_scores[baseline] = float(value)
        normalized[key] = {
            "source": source, "endpoint": endpoint, "donor_id": donor,
            "support_state": support, "candidate_score": candidate_value,
            "baseline_scores": norm_scores,
        }
    if set(normalized) != set(envelope_units):
        raise G2DecisionV2Error("deciding unit roster must exactly match frozen claim envelope unit roster")
    return normalized, baselines, numerical_failure


def _validate_reference(reference: Mapping, *, supported_keys: set[str], binding: str) -> tuple[dict[str, float] | None, str | None]:
    required = {
        "schema", "frozen", "qualified", "metric", "orientation", "input_binding_sha256",
        "reference_receipt_sha256", "independent_non_degenerate_reference", "margins",
    }
    if not isinstance(reference, Mapping) or set(reference) != required:
        raise G2DecisionV2Error("exact G2 V2 reference artifact required")
    if reference["schema"] != REFERENCE_SCHEMA:
        raise G2DecisionV2Error("reference schema mismatch")
    if reference["frozen"] is not True or reference["qualified"] is not True:
        raise G2DecisionV2Error("reference must be frozen and qualified")
    if reference["metric"] != METRIC or reference["orientation"] != ORIENTATION:
        raise G2DecisionV2Error("reference metric/orientation mismatch")
    if _hex(reference["input_binding_sha256"], "reference input binding") != binding:
        raise G2DecisionV2Error("reference input binding mismatch")
    _hex(reference["reference_receipt_sha256"], "reference receipt")
    margins = reference["margins"]
    if not isinstance(margins, Mapping) or set(margins) != supported_keys:
        raise G2DecisionV2Error("reference margin unit roster must exactly match supported claim-envelope units")
    out = {}
    numerical = False
    for key, value in margins.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            numerical = True
        else:
            out[key] = float(value)
    if numerical:
        return None, "NUMERICAL_FAILURE"
    if reference["independent_non_degenerate_reference"] is not True or not out or any(v <= 0.0 for v in out.values()):
        return out, "NONDEGENERATE_SUBSTANTIVE_MARGIN_NOT_ESTABLISHED"
    return out, None


def _tail(successes: int, n: int) -> float:
    return sum(math.comb(n, k) for k in range(successes, n + 1)) / (2 ** n) if n else 1.0


def _recurrence(values: list[float]) -> tuple[str, dict]:
    nonzero = [v for v in values if v != 0.0]
    n = len(nonzero)
    pos = sum(v > 0.0 for v in nonzero)
    neg = sum(v < 0.0 for v in nonzero)
    pos_p, neg_p = _tail(pos, n), _tail(neg, n)
    resolution = n > 0 and (0.5 ** n) <= FAMILY_ALPHA
    if resolution and pos_p <= FAMILY_ALPHA and neg_p > FAMILY_ALPHA:
        diagnostic = "ADVANTAGE_RECURRENT_BEYOND_MARGIN"
    elif resolution and neg_p <= FAMILY_ALPHA and pos_p > FAMILY_ALPHA:
        diagnostic = "NONADVANTAGE_RECURRENT_BEYOND_MARGIN"
    else:
        diagnostic = "INCONCLUSIVE"
    return diagnostic, {
        "n_nonzero": n, "positive_count": pos, "negative_count": neg,
        "positive_p": pos_p, "negative_p": neg_p, "alpha": FAMILY_ALPHA,
        "resolution_estimable": resolution,
    }


def adjudicate_g2_v2(*, candidate_id, rows, claim_envelope, reference_artifact,
                      external_qualification_receipt_sha256=None, alpha: float = FAMILY_ALPHA) -> dict:
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or float(alpha) != FAMILY_ALPHA:
        raise G2DecisionV2Error(f"alpha is frozen at {FAMILY_ALPHA}")
    candidate_id = _token(candidate_id, "candidate_id")
    envelope_units, binding = _validate_envelope(claim_envelope, candidate_id=candidate_id)
    normalized, baselines, numerical = _normalize_rows(
        rows, candidate_id=candidate_id, envelope_units=envelope_units, binding=binding
    )
    if numerical:
        return _base(status="NUMERICAL_FAILURE", reason="NONFINITE_DECIDING_SCORE", binding=binding)
    supported_keys = {key for key, unit in envelope_units.items() if unit["support_state"] == "SUPPORTED"}
    margins, ref_problem = _validate_reference(reference_artifact, supported_keys=supported_keys, binding=binding)
    if ref_problem == "NUMERICAL_FAILURE":
        return _base(status="NUMERICAL_FAILURE", reason="NONFINITE_REFERENCE_MARGIN", binding=binding)
    if ref_problem == "NONDEGENERATE_SUBSTANTIVE_MARGIN_NOT_ESTABLISHED":
        return _base(status="NOT_ESTIMABLE", reason=ref_problem, binding=binding)
    assert margins is not None

    strata = sorted({(unit["source"], unit["endpoint"]) for unit in envelope_units.values()})
    details = {}
    stratum_diagnostics = []
    for source, endpoint in strata:
        keys = [k for k, unit in envelope_units.items() if unit["source"] == source and unit["endpoint"] == endpoint]
        supported = [k for k in keys if envelope_units[k]["support_state"] == "SUPPORTED"]
        unsupported = [k for k in keys if k not in supported]
        adjusted = []
        donors = []
        for key in supported:
            row = normalized[key]
            strongest = max(row["baseline_scores"].values())
            value = row["candidate_score"] - strongest - margins[key]
            adjusted.append(value)
            donors.append({"donor_id": row["donor_id"], "advantage_minus_margin": value})
        if not supported:
            diagnostic, stats = "NOT_ESTIMABLE", {"reason": "NO_SUPPORTED_DONORS"}
        else:
            diagnostic, stats = _recurrence(adjusted)
        details[f"{source}::{endpoint}"] = {
            "diagnostic_status": diagnostic,
            "supported_donor_count": len(supported),
            "unsupported_donor_count": len(unsupported),
            "donor_details": donors,
            "recurrence": stats,
        }
        stratum_diagnostics.append(diagnostic)

    if any(v == "NONADVANTAGE_RECURRENT_BEYOND_MARGIN" for v in stratum_diagnostics):
        overall_diag = "FAIL"
    elif any(v in {"INCONCLUSIVE", "NOT_ESTIMABLE"} for v in stratum_diagnostics):
        overall_diag = "INCONCLUSIVE"
    else:
        overall_diag = "PASS"

    frozen = SEALED_G2_DECISION_QUALIFICATION_SHA256
    if frozen is None:
        return _base(
            status="NOT_ESTIMABLE",
            reason="SEALED_G2_DECISION_QUALIFICATION_NOT_FROZEN",
            binding=binding,
            diagnostic_status=overall_diag,
            stratum_details=details,
        )
    if external_qualification_receipt_sha256 != frozen:
        return _base(
            status="NOT_ESTIMABLE",
            reason="SEALED_G2_DECISION_QUALIFICATION_RECEIPT_MISMATCH",
            binding=binding,
            diagnostic_status=overall_diag,
            stratum_details=details,
        )
    return _base(
        status="NOT_ESTIMABLE",
        reason="HUMAN_G2_MAPPING_NOT_IMPLEMENTED_IN_V2",
        binding=binding,
        diagnostic_status=overall_diag,
        stratum_details=details,
    )
