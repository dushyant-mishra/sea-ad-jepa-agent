"""R1 V3 anchored-triplet recurrence executor with depth/detection-matched null.

The executor consumes already-constructed anchored-cell triplet order labels from
two frozen, address-disjoint views.  Its null breaks relation identity only
within donor/source/operator/support/depth-detection strata.  No protected human
outcomes are read and no downstream training authority is created.
"""
from __future__ import annotations

import hashlib
import math
import random
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence

from scripts.v5 import td_target_tournament_precision as P

SCHEMA = "JEPA_TD_REAL_R1_EXECUTION_CONTRACT_V3"
QUAL_SCHEMA = "JEPA_TD_REAL_R1_DECISION_QUALIFICATION_RECEIPT_V3"
QUAL_STATUS = "PASS_KNOWN_TRUTH_R1_DEPTH_MATCHED_NULL_V3"
REFERENCE_SCHEMA = "JEPA_TD_REAL_R1_REFERENCE_MARGIN_V3"
CANDIDATE = "C2_RELATIONAL_SHARED"
REQUIRED_SOURCES = ("HVS", "NPH52", "SEA_AD")
NULL_FIELDS = ("donor_id", "source", "operator_id", "support_stratum", "depth_detection_block")
NULL_SEMANTICS = "RELATION_ID_PERMUTATION_WITHIN_DEPTH_DETECTION_MATCHED_STRATUM"
METRIC = "DONOR_MEAN_EXACT_TRIPLET_ORDER_AGREEMENT"
ORIENTATION = "LARGER_IS_BETTER"
FAMILY_ALPHA = 0.01
NULL_DRAWS = 100
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


def _hash(v) -> bool:
    return isinstance(v, str) and HEX64.fullmatch(v) is not None


def _ne(reason: str) -> dict:
    return {
        "schema": "JEPA_TD_REAL_R1_DECISION_V3",
        "status": "NOT_ESTIMABLE",
        "reason": reason,
        "source_status": {},
        "source_details": {},
        "authority": dict(NO_AUTHORITY),
    }


def _contract(contract) -> tuple[dict | None, str | None]:
    fields = {
        "schema", "candidate_id", "required_sources", "view_rule_sha256", "tie_rule_sha256",
        "tie_tolerance", "null_stratum_fields", "null_semantics", "metric", "orientation",
        "family_alpha", "null_draws_per_donor", "frozen_before_values",
    }
    if not isinstance(contract, Mapping) or set(contract) != fields:
        return None, "R1_EXECUTION_CONTRACT_NOT_AUTHENTICATED"
    if contract.get("schema") != SCHEMA or contract.get("candidate_id") != CANDIDATE:
        return None, "R1_EXECUTION_CONTRACT_NOT_AUTHENTICATED"
    if contract.get("required_sources") != list(REQUIRED_SOURCES):
        return None, "R1_EXECUTION_CONTRACT_NOT_AUTHENTICATED"
    if not _hash(contract.get("view_rule_sha256")) or not _hash(contract.get("tie_rule_sha256")):
        return None, "R1_EXECUTION_CONTRACT_NOT_AUTHENTICATED"
    if contract.get("tie_tolerance") != 0.0:
        return None, "R1_EXECUTION_CONTRACT_NOT_AUTHENTICATED"
    if contract.get("null_stratum_fields") != list(NULL_FIELDS):
        return None, "NULL_STRATUM_CONTRACT_NOT_DEPTH_DETECTION_MATCHED"
    if contract.get("null_semantics") != NULL_SEMANTICS:
        return None, "R1_EXECUTION_CONTRACT_NOT_AUTHENTICATED"
    if contract.get("metric") != METRIC or contract.get("orientation") != ORIENTATION:
        return None, "R1_EXECUTION_CONTRACT_NOT_AUTHENTICATED"
    if contract.get("family_alpha") != FAMILY_ALPHA or contract.get("null_draws_per_donor") != NULL_DRAWS:
        return None, "R1_EXECUTION_CONTRACT_NOT_AUTHENTICATED"
    if contract.get("frozen_before_values") is not True:
        return None, "R1_EXECUTION_CONTRACT_NOT_AUTHENTICATED"
    return dict(contract), None


def _qualification(receipt) -> bool:
    fields = {
        "schema", "status", "producer_code_sha256", "qualification_worlds_sha256",
        "receipt_sha256", "technical_only_negative_passed", "planted_biology_positive_passed",
    }
    return bool(
        isinstance(receipt, Mapping)
        and set(receipt) == fields
        and receipt.get("schema") == QUAL_SCHEMA
        and receipt.get("status") == QUAL_STATUS
        and receipt.get("technical_only_negative_passed") is True
        and receipt.get("planted_biology_positive_passed") is True
        and all(_hash(receipt.get(k)) for k in ("producer_code_sha256", "qualification_worlds_sha256", "receipt_sha256"))
    )


def _normalize_rows(rows):
    fields = {
        "donor_id", "source", "operator_id", "support_stratum", "depth_detection_block",
        "relation_id", "view_a_order", "view_b_order", "input_binding_sha256",
    }
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence) or not rows:
        return None
    out = []
    seen = set()
    bindings = set()
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != fields:
            return None
        for key in ("donor_id", "source", "operator_id", "support_stratum", "depth_detection_block", "relation_id"):
            if not isinstance(row[key], str) or not row[key] or row[key] != row[key].strip():
                return None
        if row["source"] not in REQUIRED_SOURCES or row["support_stratum"] != "SUPPORTED":
            return None
        if row["view_a_order"] not in {-1, 0, 1} or row["view_b_order"] not in {-1, 0, 1}:
            return None
        if not _hash(row["input_binding_sha256"]):
            return None
        ident = (row["donor_id"], row["source"], row["operator_id"], row["support_stratum"], row["depth_detection_block"], row["relation_id"])
        if ident in seen:
            return None
        seen.add(ident)
        bindings.add(row["input_binding_sha256"])
        out.append(dict(row))
    if len(bindings) != 1:
        return None
    return out, next(iter(bindings))


def _validate_reference(reference, donors: set[str], binding: str):
    fields = {
        "schema", "frozen", "qualified", "metric", "orientation", "input_binding_sha256",
        "reference_receipt_sha256", "producer_qualification_receipt_sha256", "u_refit",
    }
    if not isinstance(reference, Mapping) or set(reference) != fields:
        return None
    if reference.get("schema") != REFERENCE_SCHEMA or reference.get("frozen") is not True or reference.get("qualified") is not True:
        return None
    if reference.get("metric") != METRIC or reference.get("orientation") != ORIENTATION or reference.get("input_binding_sha256") != binding:
        return None
    if not _hash(reference.get("reference_receipt_sha256")) or not _hash(reference.get("producer_qualification_receipt_sha256")):
        return None
    raw = reference.get("u_refit")
    if not isinstance(raw, Mapping) or set(raw) != donors:
        return None
    out = {}
    for donor, value in raw.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        value = float(value)
        if not math.isfinite(value) or value < 0:
            return None
        out[donor] = value
    return out


def _agreement(rows) -> float:
    return sum(r["view_a_order"] == r["view_b_order"] for r in rows) / len(rows)


def _seed(*parts: str) -> int:
    payload = "\0".join(parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")


def _donor_null(rows, donor: str, n_draws: int) -> list[float] | None:
    donor_rows = [r for r in rows if r["donor_id"] == donor]
    strata = defaultdict(list)
    for row in donor_rows:
        key = tuple(row[field] for field in NULL_FIELDS)
        strata[key].append(row)
    if any(len(group) < 2 for group in strata.values()):
        return None

    identity_signature = tuple(
        tuple(range(len(strata[key]))) for key in sorted(strata)
    )
    seen = set()
    scores = []
    attempts = 0
    max_attempts = n_draws * 100
    ordered_keys = sorted(strata)
    while len(scores) < n_draws and attempts < max_attempts:
        draw = attempts
        attempts += 1
        signature_parts = []
        permuted_by_key = {}
        for key in ordered_keys:
            group = strata[key]
            idx = list(range(len(group)))
            rng = random.Random(_seed("R1_V3", donor, str(draw), *key))
            rng.shuffle(idx)
            signature_parts.append(tuple(idx))
            permuted_by_key[key] = idx
        signature = tuple(signature_parts)
        if signature == identity_signature or signature in seen:
            continue
        seen.add(signature)
        total = 0
        agree = 0
        for key in ordered_keys:
            group = strata[key]
            perm = permuted_by_key[key]
            ys = [group[j]["view_b_order"] for j in perm]
            for row, y in zip(group, ys):
                total += 1
                agree += row["view_a_order"] == y
        scores.append(agree / total)
    return scores if len(scores) == n_draws else None


def _upper_adverse(values: Sequence[float], alpha: float) -> float | None:
    n = len(values)
    # Need at least ceil(1/alpha) distinct non-identity draws for the protected tail.
    if n < math.ceil(1.0 / alpha):
        return None
    rank = math.ceil((n + 1) * (1.0 - alpha))
    if rank > n:
        return None
    return sorted(values)[rank - 1]


def _evaluate(rows, *, sources: Sequence[str], u_refit: Mapping[str, float]):
    source_status = {}
    source_details = {}
    for source in sources:
        local = [r for r in rows if r["source"] == source]
        donors = sorted({r["donor_id"] for r in local})
        if not donors:
            source_status[source] = "NOT_ESTIMABLE"
            source_details[source] = {"reason": "NO_REQUIRED_SOURCE_ROWS"}
            continue
        deltas = []
        technical_rejected = True
        for donor in donors:
            drows = [r for r in local if r["donor_id"] == donor]
            observed = _agreement(drows)
            nulls = _donor_null(local, donor, NULL_DRAWS)
            if nulls is None:
                deltas = None
                break
            adverse = _upper_adverse(nulls, FAMILY_ALPHA)
            if adverse is None:
                deltas = None
                break
            delta = observed - adverse - u_refit[donor]
            deltas.append({"donor_id": donor, "delta": delta})
            technical_rejected = technical_rejected and delta <= 0.0
        if deltas is None:
            source_status[source] = "NOT_ESTIMABLE"
            source_details[source] = {"reason": "NULL_TAIL_NOT_RESOLVED", "technical_only_shortcut_rejected": False}
            continue
        gate = P.sign_recurrence_gate(deltas, FAMILY_ALPHA)
        if not gate["resolution_estimable"]:
            status = "NOT_ESTIMABLE"
        elif gate["pass"]:
            status = "PASS"
        else:
            status = "FAIL"
        source_status[source] = status
        source_details[source] = {
            "donor_count": len(donors),
            "technical_only_shortcut_rejected": technical_rejected,
            "sign_test": gate,
        }
    if any(v == "FAIL" for v in source_status.values()):
        overall = "FAIL"
    elif any(v == "NOT_ESTIMABLE" for v in source_status.values()):
        overall = "NOT_ESTIMABLE"
    else:
        overall = "PASS"
    return overall, source_status, source_details


def adjudicate_r1_v3(*, rows, contract, decision_qualification_receipt, reference_artifact, required_sources) -> dict:
    frozen, error = _contract(contract)
    if error:
        return _ne(error)
    if required_sources != list(REQUIRED_SOURCES):
        return _ne("REQUIRED_SOURCE_SCOPE_MISMATCH")
    if not _qualification(decision_qualification_receipt):
        return _ne("DECISION_QUALIFICATION_RECEIPT_NOT_AUTHENTICATED")
    normalized = _normalize_rows(rows)
    if normalized is None:
        return _ne("RELATION_ROWS_INVALID")
    clean, binding = normalized
    present = {r["source"] for r in clean}
    if present != set(REQUIRED_SOURCES):
        return _ne("REQUIRED_SOURCE_RELATIONAL_EVIDENCE_UNRESOLVED")
    donors = {r["donor_id"] for r in clean}
    u_refit = _validate_reference(reference_artifact, donors, binding)
    if u_refit is None:
        return _ne("REFERENCE_ARTIFACT_NOT_AUTHENTICATED")
    overall, source_status, source_details = _evaluate(clean, sources=REQUIRED_SOURCES, u_refit=u_refit)
    reason = {
        "PASS": "ALL_REQUIRED_SOURCES_DEFEAT_DEPTH_MATCHED_NULL_AND_U_REFIT",
        "FAIL": "RELATIONAL_RECURRENCE_NOT_ESTABLISHED_BEYOND_DEPTH_MATCHED_NULL",
        "NOT_ESTIMABLE": "REQUIRED_SOURCE_RELATIONAL_EVIDENCE_UNRESOLVED",
    }[overall]
    return {
        "schema": "JEPA_TD_REAL_R1_DECISION_V3",
        "status": overall,
        "reason": reason,
        "metric": METRIC,
        "orientation": ORIENTATION,
        "source_status": source_status,
        "source_details": source_details,
        "authority": dict(NO_AUTHORITY),
    }


def _known_truth_rows(*, technical_only: bool):
    pattern = (1, 1, -1, 1, -1, -1, 1, -1, 1, 1, 1, -1)
    rows = []
    for source in REQUIRED_SOURCES:
        for di in range(8):
            donor = f"{source}_D{di:02d}"
            for block in ("LOW_DEPTH", "HIGH_DEPTH"):
                for ri, planted in enumerate(pattern):
                    x = (1 if block == "HIGH_DEPTH" else -1) if technical_only else planted
                    rows.append({
                        "donor_id": donor, "source": source, "operator_id": f"{source}_OP1",
                        "support_stratum": "SUPPORTED", "depth_detection_block": block,
                        "relation_id": f"{donor}:{block}:R{ri}", "view_a_order": x, "view_b_order": x,
                        "input_binding_sha256": "a" * 64,
                    })
    return rows


def qualify_r1_depth_matched_null_v3() -> dict:
    technical = _known_truth_rows(technical_only=True)
    biology = _known_truth_rows(technical_only=False)
    donors = {r["donor_id"] for r in technical}
    margins = {d: 0.01 for d in donors}
    t_status, _, _ = _evaluate(technical, sources=REQUIRED_SOURCES, u_refit=margins)
    b_status, _, _ = _evaluate(biology, sources=REQUIRED_SOURCES, u_refit=margins)
    status = QUAL_STATUS if (t_status == "FAIL" and b_status == "PASS") else "NOT_QUALIFIED"
    return {
        "schema": QUAL_SCHEMA,
        "status": status,
        "technical_only_negative": t_status,
        "planted_biology_positive": b_status,
        "null_stratum_fields": list(NULL_FIELDS),
        "null_draws_per_donor": NULL_DRAWS,
        "authority": dict(NO_AUTHORITY),
    }
