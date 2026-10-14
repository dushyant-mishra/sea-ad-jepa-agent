"""G2 V2 nontrivial-content decision consumer.

Scientific choices (baseline family, required strata, metric, input, support
universe and family alpha) are frozen in authenticated upstream artifacts.  The
consumer never turns absence of significant positive recurrence into biological
FAIL: negative evidence is tested separately at the same protected alpha.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence

from scripts.v5 import td_target_tournament_precision as P

FAMILY_ALPHA = 0.01
METRIC = "HELD_OUT_DONOR_PRIMARY_ENDPOINT_SCORE"
ORIENTATION = "LARGER_IS_BETTER"
COMPARATOR_RULE = "ALL_FROZEN_BASELINES_SEPARATELY_NONCOMPENSATING"
CONTRACT_SCHEMA = "JEPA_TD_REAL_G2_DECISION_CONTRACT_V2"
BASELINE_SCHEMA = "JEPA_TD_REAL_G2_BASELINE_FAMILY_V2"
SUPPORT_SCHEMA = "JEPA_TD_REAL_G2_SUPPORT_ENVELOPE_V2"
REFERENCE_SCHEMA = "JEPA_TD_REAL_G2_REFERENCE_MARGIN_V2"
QUAL_SCHEMA = "JEPA_TD_REAL_G2_DECISION_QUALIFICATION_RECEIPT_V2"
QUAL_STATUS = "PASS_KNOWN_TRUTH_G2_DECISION_V2"
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


def _hash(v) -> bool:
    return isinstance(v, str) and HEX64.fullmatch(v) is not None


def _token(v) -> bool:
    return isinstance(v, str) and bool(v) and v == v.strip() and "\0" not in v


def _ne(reason: str, *, component_status=None) -> dict:
    return {
        "schema": "JEPA_TD_REAL_G2_CONTENT_DECISION_V2",
        "status": "NOT_ESTIMABLE",
        "reason": reason,
        "component_status": component_status or {},
        "component_details": {},
        "family_alpha": FAMILY_ALPHA,
        "authority": dict(NO_AUTHORITY),
    }


def _numfail(reason: str) -> dict:
    return {
        "schema": "JEPA_TD_REAL_G2_CONTENT_DECISION_V2",
        "status": "NUMERICAL_FAILURE",
        "reason": reason,
        "component_status": {},
        "component_details": {},
        "family_alpha": FAMILY_ALPHA,
        "authority": dict(NO_AUTHORITY),
    }


def _baseline_family(manifest):
    fields = {"schema", "candidate_id", "baseline_ids", "receipt_sha256", "producer_code_sha256", "frozen_before_values"}
    if not isinstance(manifest, Mapping) or set(manifest) != fields:
        return None
    if manifest.get("schema") != BASELINE_SCHEMA or manifest.get("frozen_before_values") is not True:
        return None
    if not _token(manifest.get("candidate_id")) or not _hash(manifest.get("receipt_sha256")) or not _hash(manifest.get("producer_code_sha256")):
        return None
    raw = manifest.get("baseline_ids")
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence) or not raw:
        return None
    ids = list(raw)
    if any(not _token(v) for v in ids) or len(set(ids)) != len(ids):
        return None
    return {**dict(manifest), "baseline_ids": ids}


def _contract(contract, baseline):
    fields = {
        "schema", "candidate_id", "metric", "orientation", "metric_manifest_sha256",
        "input_binding_sha256", "baseline_ids", "baseline_family_receipt_sha256",
        "required_strata", "comparator_rule", "family_alpha",
        "support_envelope_receipt_sha256", "contract_receipt_sha256", "frozen_before_values",
    }
    if not isinstance(contract, Mapping) or set(contract) != fields:
        return None
    if contract.get("schema") != CONTRACT_SCHEMA or contract.get("frozen_before_values") is not True:
        return None
    if contract.get("candidate_id") != baseline["candidate_id"] or contract.get("baseline_ids") != baseline["baseline_ids"]:
        return None
    if contract.get("baseline_family_receipt_sha256") != baseline["receipt_sha256"]:
        return None
    if contract.get("metric") != METRIC or contract.get("orientation") != ORIENTATION or contract.get("comparator_rule") != COMPARATOR_RULE:
        return None
    if contract.get("family_alpha") != FAMILY_ALPHA:
        return None
    for key in ("metric_manifest_sha256", "input_binding_sha256", "support_envelope_receipt_sha256", "contract_receipt_sha256"):
        if not _hash(contract.get(key)):
            return None
    raw = contract.get("required_strata")
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence) or not raw:
        return None
    strata = []
    for item in raw:
        if isinstance(item, (str, bytes)) or not isinstance(item, Sequence) or len(item) != 2:
            return None
        source, endpoint = item
        if not _token(source) or not _token(endpoint):
            return None
        strata.append((source, endpoint))
    if len(set(strata)) != len(strata):
        return None
    return {**dict(contract), "required_strata": strata}


def _support(envelope, contract):
    fields = {"schema", "receipt_sha256", "frozen_before_values", "source_endpoint_donor_status"}
    if not isinstance(envelope, Mapping) or set(envelope) != fields:
        return None
    if envelope.get("schema") != SUPPORT_SCHEMA or envelope.get("frozen_before_values") is not True:
        return None
    if envelope.get("receipt_sha256") != contract["support_envelope_receipt_sha256"] or not _hash(envelope.get("receipt_sha256")):
        return None
    raw = envelope.get("source_endpoint_donor_status")
    if not isinstance(raw, Mapping):
        return None
    expected = {f"{s}::{e}" for s, e in contract["required_strata"]}
    if set(raw) != expected:
        return None
    out = {}
    for stratum in expected:
        donors = raw[stratum]
        if not isinstance(donors, Mapping) or not donors:
            return None
        local = {}
        for donor, state in donors.items():
            if not _token(donor) or state not in SUPPORT_STATES:
                return None
            local[donor] = state
        out[stratum] = local
    return out


def _qualification(receipt) -> bool:
    fields = {"schema", "status", "producer_code_sha256", "qualification_worlds_sha256", "receipt_sha256", "human_semantics_qualified"}
    return bool(
        isinstance(receipt, Mapping)
        and set(receipt) == fields
        and receipt.get("schema") == QUAL_SCHEMA
        and receipt.get("status") == QUAL_STATUS
        and receipt.get("human_semantics_qualified") is True
        and all(_hash(receipt.get(k)) for k in ("producer_code_sha256", "qualification_worlds_sha256", "receipt_sha256"))
    )


def _rows(rows, contract, baseline, support):
    fields = {"source", "endpoint", "donor_id", "candidate_score", "baseline_scores", "input_binding_sha256"}
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        return "INVALID", None
    expected_strata = set(contract["required_strata"])
    seen = set()
    out = {}
    for raw in rows:
        if not isinstance(raw, Mapping) or set(raw) != fields:
            return "INVALID", None
        source, endpoint, donor = raw.get("source"), raw.get("endpoint"), raw.get("donor_id")
        if not _token(source) or not _token(endpoint) or not _token(donor):
            return "INVALID", None
        if (source, endpoint) not in expected_strata:
            return "EXTRA_STRATUM", None
        skey = f"{source}::{endpoint}"
        if donor not in support[skey] or support[skey][donor] != "SUPPORTED":
            return "SUPPORT_MISMATCH", None
        ident = (source, endpoint, donor)
        if ident in seen:
            return "INVALID", None
        seen.add(ident)
        if raw.get("input_binding_sha256") != contract["input_binding_sha256"]:
            return "INVALID", None
        candidate = raw.get("candidate_score")
        if isinstance(candidate, bool) or not isinstance(candidate, (int, float)) or not math.isfinite(float(candidate)):
            return "NUMERICAL_FAILURE", None
        scores = raw.get("baseline_scores")
        if not isinstance(scores, Mapping) or set(scores) != set(baseline["baseline_ids"]):
            return "INVALID", None
        normalized = {}
        for bid, value in scores.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                return "NUMERICAL_FAILURE", None
            normalized[bid] = float(value)
        out[ident] = {"candidate": float(candidate), "baselines": normalized}
    # Every prospectively SUPPORTED donor must have exactly one deciding row.
    expected_supported = {
        (s, e, donor)
        for s, e in contract["required_strata"]
        for donor, state in support[f"{s}::{e}"].items()
        if state == "SUPPORTED"
    }
    if set(out) != expected_supported:
        return "MISSING_SUPPORTED_ROWS", None
    return "OK", out


def _reference(reference, contract, baseline, support):
    fields = {
        "schema", "frozen", "qualified", "metric", "orientation", "metric_manifest_sha256",
        "input_binding_sha256", "decision_contract_receipt_sha256", "baseline_family_receipt_sha256",
        "support_envelope_receipt_sha256", "reference_receipt_sha256", "producer_code_sha256",
        "producer_qualification_receipt_sha256", "margin_units_sha256", "margin_is_non_degenerate", "margins",
    }
    if not isinstance(reference, Mapping) or set(reference) != fields:
        return None
    if reference.get("schema") != REFERENCE_SCHEMA or reference.get("frozen") is not True or reference.get("qualified") is not True:
        return None
    checks = {
        "metric": METRIC,
        "orientation": ORIENTATION,
        "metric_manifest_sha256": contract["metric_manifest_sha256"],
        "input_binding_sha256": contract["input_binding_sha256"],
        "decision_contract_receipt_sha256": contract["contract_receipt_sha256"],
        "baseline_family_receipt_sha256": baseline["receipt_sha256"],
        "support_envelope_receipt_sha256": contract["support_envelope_receipt_sha256"],
    }
    if any(reference.get(k) != v for k, v in checks.items()):
        return None
    for key in ("reference_receipt_sha256", "producer_code_sha256", "producer_qualification_receipt_sha256", "margin_units_sha256"):
        if not _hash(reference.get(key)):
            return None
    raw = reference.get("margins")
    if not isinstance(raw, Mapping):
        return None
    expected = {
        f"{s}::{e}::{donor}::{bid}"
        for s, e in contract["required_strata"]
        for donor, state in support[f"{s}::{e}"].items()
        if state == "SUPPORTED"
        for bid in baseline["baseline_ids"]
    }
    if set(raw) != expected:
        return None
    margins = {}
    for key, value in raw.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0.0:
            return None
        margins[key] = float(value)
    if reference.get("margin_is_non_degenerate") is not True or not any(v > 0.0 for v in margins.values()):
        return "DEGENERATE"
    return margins


def _component(deltas, alpha_eff: float):
    positive = P.sign_recurrence_gate(deltas, alpha_eff)
    negative = P.sign_recurrence_gate(
        [{"donor_id": row["donor_id"], "delta": -row["delta"]} for row in deltas], alpha_eff
    )
    if positive["pass"]:
        return "PASS", positive, negative
    if negative["pass"]:
        return "FAIL", positive, negative
    # Exact all-nonpositive data are a substantively resolved negative result even
    # when ties would otherwise reduce the sign-test n. This is not a direction
    # shortcut: the deltas already include the strictly positive frozen margin.
    if deltas and all(row["delta"] <= 0.0 for row in deltas):
        return "FAIL", positive, negative
    return "NOT_ESTIMABLE", positive, negative


def adjudicate_g2_v2(*, rows, decision_contract, baseline_family_manifest, support_envelope, reference_artifact, decision_qualification_receipt) -> dict:
    baseline = _baseline_family(baseline_family_manifest)
    if baseline is None:
        return _ne("BASELINE_FAMILY_NOT_AUTHENTICATED")
    contract = _contract(decision_contract, baseline)
    if contract is None:
        return _ne("DECISION_CONTRACT_NOT_AUTHENTICATED")
    support = _support(support_envelope, contract)
    if support is None:
        return _ne("SUPPORT_ENVELOPE_NOT_AUTHENTICATED")
    if not _qualification(decision_qualification_receipt):
        return _ne("DECISION_QUALIFICATION_RECEIPT_NOT_AUTHENTICATED")
    reference = _reference(reference_artifact, contract, baseline, support)
    if reference is None:
        return _ne("REFERENCE_ARTIFACT_NOT_AUTHENTICATED")
    if reference == "DEGENERATE":
        return _ne("NON_DEGENERATE_SUBSTANTIVE_MARGIN_REQUIRED")
    row_status, normalized = _rows(rows, contract, baseline, support)
    if row_status == "NUMERICAL_FAILURE":
        return _numfail("NONFINITE_DECIDING_SCORE")
    if row_status == "EXTRA_STRATUM":
        return _ne("UNDECLARED_STRATUM_ROWS_PRESENT")
    if row_status != "OK":
        return _ne("DECIDING_ROWS_DO_NOT_MATCH_FROZEN_SUPPORT_ENVELOPE")

    n_components = len(contract["required_strata"]) * len(baseline["baseline_ids"])
    alpha_eff = FAMILY_ALPHA / n_components
    component_status = {}
    component_details = {}
    for source, endpoint in contract["required_strata"]:
        skey = f"{source}::{endpoint}"
        donors = [d for d, state in support[skey].items() if state == "SUPPORTED"]
        for bid in baseline["baseline_ids"]:
            name = f"{skey}::{bid}"
            deltas = []
            for donor in donors:
                row = normalized[(source, endpoint, donor)]
                margin = reference[f"{skey}::{donor}::{bid}"]
                deltas.append({"donor_id": donor, "delta": row["candidate"] - row["baselines"][bid] - margin})
            status, positive, negative = _component(deltas, alpha_eff)
            component_status[name] = status
            component_details[name] = {
                "positive_recurrence": positive,
                "negative_recurrence": negative,
                "supported_donor_count": len(donors),
            }

    statuses = list(component_status.values())
    if "FAIL" in statuses:
        overall, reason = "FAIL", "AT_LEAST_ONE_MANDATORY_BASELINE_NOT_BEATEN_BEYOND_MARGIN"
    elif "NOT_ESTIMABLE" in statuses:
        overall, reason = "NOT_ESTIMABLE", "INCONCLUSIVE_DONOR_RECURRENCE_AT_FROZEN_ALPHA"
    else:
        overall, reason = "PASS", "ALL_MANDATORY_BASELINES_BEAT_IN_ALL_REQUIRED_STRATA"
    return {
        "schema": "JEPA_TD_REAL_G2_CONTENT_DECISION_V2",
        "status": overall,
        "reason": reason,
        "metric": METRIC,
        "orientation": ORIENTATION,
        "family_alpha": FAMILY_ALPHA,
        "alpha_eff": alpha_eff,
        "baseline_family_receipt_sha256": baseline["receipt_sha256"],
        "decision_contract_receipt_sha256": contract["contract_receipt_sha256"],
        "support_envelope_receipt_sha256": support_envelope["receipt_sha256"],
        "component_status": component_status,
        "component_details": component_details,
        "authority": dict(NO_AUTHORITY),
    }
