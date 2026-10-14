"""R1 V3 relational ruler and matched-null mechanics after hostile review.

This module restores historical TD57B depth/detection matching that was lost from
R1 V2's static null key.  It qualifies only mechanics/test-of-test behavior:
- exact tie-aware pair-order concordance distances;
- address-disjoint view custody by SHA-256;
- donor/source/operator/support/depth/detection matched relation-null blocks; and
- mandatory technical-confounding negative plus planted-relation positive worlds.

The historical scientific null reassigns *Y cell identities* within matched
blocks.  The relation-level cyclic-shift diagnostic here is therefore a
known-truth falsifier, not a human producer.  Human R1 remains fail-closed until
an independently qualified cell-identity producer owns measurability, triplet
construction and null generation.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence


class R1ExecutorV3Error(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_R1_EXECUTOR_MECHANICS_V3"
TIE_SEMANTICS = "EXACT_RATIONAL_DISTANCE_TIE_IS_UNRESOLVED"
MATCHED_NULL_PRESERVES = (
    "DONOR", "SOURCE", "OPERATOR", "SUPPORT_STRATUM", "DEPTH_BLOCK", "DETECTION_BLOCK"
)
HISTORICAL_NULL_PRODUCER = (
    "Y_CELL_IDENTITY_REASSIGNMENT_WITHIN_DONOR_SOURCE_OPERATOR_SUPPORT_DEPTH_DETECTION_BLOCK"
)
DIAGNOSTIC_NULL_PRODUCER = "RELATION_LEVEL_DETERMINISTIC_NONZERO_CYCLIC_SHIFT__KNOWN_TRUTH_ONLY"
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}

_ROW_FIELDS = {
    "relation_id", "donor_id", "source", "operator", "support_stratum",
    "depth_block", "detection_block", "q_x", "q_y",
}


def _token(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise R1ExecutorV3Error(f"{label} must be a nonempty trimmed NUL-free string")
    return value


def _sign(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value not in {-1, 0, 1}:
        raise R1ExecutorV3Error(f"{label} must be one of -1, 0, 1")
    return value


def concordance_distance(signs_a: Sequence[int], signs_b: Sequence[int], *, minimum_informative: int) -> tuple[int, int] | None:
    """Return exact rational numerator/denominator for TD56/57 concordance distance."""
    if isinstance(minimum_informative, bool) or not isinstance(minimum_informative, int) or minimum_informative <= 0:
        raise R1ExecutorV3Error("minimum_informative must be a positive integer")
    if isinstance(signs_a, (str, bytes)) or isinstance(signs_b, (str, bytes)):
        raise R1ExecutorV3Error("pair-order signs must be sequences")
    if not isinstance(signs_a, Sequence) or not isinstance(signs_b, Sequence) or len(signs_a) != len(signs_b):
        raise R1ExecutorV3Error("pair-order sign vectors must have equal length")
    informative = 0
    numerator = 0
    for index, (raw_a, raw_b) in enumerate(zip(signs_a, signs_b)):
        a = _sign(raw_a, f"signs_a[{index}]")
        b = _sign(raw_b, f"signs_b[{index}]")
        if a == 0 and b == 0:
            continue
        informative += 1
        numerator += abs(a - b)
    if informative < minimum_informative:
        return None
    return numerator, 2 * informative


def anchored_triplet_order_exact(d_ij: tuple[int, int] | None, d_ik: tuple[int, int] | None) -> int | None:
    """Exact q(i;j,k)=sign(d(i,j)-d(i,k)) by integer cross multiplication."""
    if d_ij is None or d_ik is None:
        return None
    try:
        n1, d1 = d_ij
        n2, d2 = d_ik
    except Exception as exc:
        raise R1ExecutorV3Error("distances must be exact numerator/denominator pairs") from exc
    for value, label in ((n1, "numerator"), (n2, "numerator"), (d1, "denominator"), (d2, "denominator")):
        if isinstance(value, bool) or not isinstance(value, int):
            raise R1ExecutorV3Error(f"distance {label} must be integer")
    if n1 < 0 or n2 < 0 or d1 <= 0 or d2 <= 0:
        raise R1ExecutorV3Error("distance fractions must be nonnegative with positive denominators")
    lhs = n1 * d2
    rhs = n2 * d1
    if lhs == rhs:
        return 0
    return 1 if lhs > rhs else -1


def _pair(raw, label: str) -> tuple[str, str]:
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence) or len(raw) != 2:
        raise R1ExecutorV3Error(f"{label} must contain exactly two address IDs")
    a = _token(raw[0], label)
    b = _token(raw[1], label)
    if a == b:
        raise R1ExecutorV3Error(f"{label} must contain two distinct addresses")
    return a, b


def freeze_view_contract(*, view_x_pairs, view_y_pairs) -> dict:
    if isinstance(view_x_pairs, (str, bytes)) or not isinstance(view_x_pairs, Sequence) or not view_x_pairs:
        raise R1ExecutorV3Error("view_x_pairs must be a nonempty sequence")
    if isinstance(view_y_pairs, (str, bytes)) or not isinstance(view_y_pairs, Sequence) or not view_y_pairs:
        raise R1ExecutorV3Error("view_y_pairs must be a nonempty sequence")
    x = [_pair(pair, f"view_x_pairs[{i}]") for i, pair in enumerate(view_x_pairs)]
    y = [_pair(pair, f"view_y_pairs[{i}]") for i, pair in enumerate(view_y_pairs)]
    if len(set(x)) != len(x) or len(set(y)) != len(y):
        raise R1ExecutorV3Error("duplicate pair coordinates are forbidden")
    x_addresses = {address for pair in x for address in pair}
    y_addresses = {address for pair in y for address in pair}
    if x_addresses & y_addresses:
        raise R1ExecutorV3Error("lawful molecular views must remain address-disjoint")
    payload = {
        "schema": "JEPA_TD_REAL_R1_VIEW_CONTRACT_V3",
        "view_x_pairs": [list(pair) for pair in x],
        "view_y_pairs": [list(pair) for pair in y],
        "address_binding_state": "REPAIRED_41K_ADDRESS_BOUND",
        "tie_semantics": TIE_SEMANTICS,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**payload, "view_contract_sha256": hashlib.sha256(canonical).hexdigest()}


def matched_null_block_key(*, donor_id, source, operator, support_stratum, depth_block, detection_block) -> tuple[str, ...]:
    return (
        _token(donor_id, "donor_id"),
        _token(source, "source"),
        _token(operator, "operator"),
        _token(support_stratum, "support_stratum"),
        _token(depth_block, "depth_block"),
        _token(detection_block, "detection_block"),
    )


def _normalize_relation_rows(rows) -> list[dict]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence) or not rows:
        raise R1ExecutorV3Error("relation rows must be a nonempty sequence")
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping) or set(raw) != _ROW_FIELDS:
            raise R1ExecutorV3Error(f"rows[{index}] fields differ from the frozen diagnostic schema")
        relation_id = _token(raw["relation_id"], "relation_id")
        donor = _token(raw["donor_id"], "donor_id")
        key = (donor, relation_id)
        if key in seen:
            raise R1ExecutorV3Error(f"duplicate donor/relation identity: {donor}/{relation_id}")
        seen.add(key)
        qx = _sign(raw["q_x"], "q_x")
        qy = _sign(raw["q_y"], "q_y")
        if qx == 0 or qy == 0:
            raise R1ExecutorV3Error("exact distance ties are unresolved and may not enter resolved relation-null rows")
        row = dict(raw)
        row["q_x"] = qx
        row["q_y"] = qy
        row["block_key"] = matched_null_block_key(
            donor_id=raw["donor_id"], source=raw["source"], operator=raw["operator"],
            support_stratum=raw["support_stratum"], depth_block=raw["depth_block"],
            detection_block=raw["detection_block"],
        )
        out.append(row)
    return out


def matched_relation_null_diagnostic(rows, *, nonzero_shifts: int) -> dict:
    """Known-truth relation-level matched-null diagnostic; not a human null producer."""
    if isinstance(nonzero_shifts, bool) or not isinstance(nonzero_shifts, int) or nonzero_shifts <= 0:
        raise R1ExecutorV3Error("nonzero_shifts must be a positive integer")
    normalized = _normalize_relation_rows(rows)
    observed = sum(row["q_x"] == row["q_y"] for row in normalized) / len(normalized)
    groups: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for index, row in enumerate(normalized):
        groups[row["block_key"]].append(index)

    null_values: list[float] = []
    for shift_index in range(1, nonzero_shifts + 1):
        permuted_qy = [row["q_y"] for row in normalized]
        for indices in groups.values():
            n = len(indices)
            if n < 2:
                continue
            shift = ((shift_index - 1) % (n - 1)) + 1
            original = [normalized[i]["q_y"] for i in indices]
            shifted = original[shift:] + original[:shift]
            for i, value in zip(indices, shifted):
                permuted_qy[i] = value
        null_values.append(
            sum(normalized[i]["q_x"] == permuted_qy[i] for i in range(len(normalized))) / len(normalized)
        )
    matched_max = max(null_values)
    delta = observed - matched_max
    return {
        "schema": "JEPA_TD_R1_MATCHED_RELATION_NULL_DIAGNOSTIC_V3",
        "status": "KNOWN_TRUTH_DIAGNOSTIC_ONLY",
        "observed_agreement": observed,
        "matched_null_values": null_values,
        "matched_null_max": matched_max,
        "observed_minus_matched_null_max": delta,
        "matched_null_preserves": list(MATCHED_NULL_PRESERVES),
        "diagnostic_null_producer": DIAGNOSTIC_NULL_PRODUCER,
        "historical_human_null_producer_required": HISTORICAL_NULL_PRODUCER,
        "technical_only_negative_passes": delta > 0.0,
        "human_r1_adjudication_authorized": False,
        "authority": dict(NO_AUTHORITY),
    }


def _technical_rows() -> list[dict]:
    rows: list[dict] = []
    for block, q in (("LOW", -1), ("HIGH", 1)):
        for i in range(8):
            rows.append({
                "relation_id": f"{block}-{i}", "donor_id": "D1", "source": "SEA_AD",
                "operator": "OP", "support_stratum": "S", "depth_block": block,
                "detection_block": block, "q_x": q, "q_y": q,
            })
    return rows


def _planted_rows() -> list[dict]:
    rows: list[dict] = []
    pattern = [-1, -1, 1, 1, -1, 1, -1, 1]
    for block in ("LOW", "HIGH"):
        for i, q in enumerate(pattern):
            rows.append({
                "relation_id": f"{block}-{i}", "donor_id": "D1", "source": "SEA_AD",
                "operator": "OP", "support_stratum": "S", "depth_block": block,
                "detection_block": block, "q_x": q, "q_y": q,
            })
    return rows


def qualify_r1_v3_mechanics() -> dict:
    technical = matched_relation_null_diagnostic(_technical_rows(), nonzero_shifts=7)
    planted = matched_relation_null_diagnostic(_planted_rows(), nonzero_shifts=7)
    worlds = {
        "TECHNICAL_BLOCK_CONFOUNDING": (
            "PASS" if technical["observed_minus_matched_null_max"] <= 0.0 else "FAIL"
        ),
        "PLANTED_WITHIN_BLOCK_RELATION": (
            "PASS" if planted["observed_minus_matched_null_max"] > 0.0 else "FAIL"
        ),
    }
    passed = all(value == "PASS" for value in worlds.values())
    return {
        "schema": "JEPA_TD_R1_V3_MECHANICS_KNOWN_TRUTH_QUALIFICATION",
        "status": "PASS_R1_V3_MECHANICS_KNOWN_TRUTH" if passed else "FAIL_R1_V3_MECHANICS_KNOWN_TRUTH",
        "worlds": worlds,
        "historical_null_law_restored": list(MATCHED_NULL_PRESERVES),
        "human_null_producer_status": "BLOCKED_PENDING_CELL_IDENTITY_PRODUCER_QUALIFICATION",
        "human_r1_adjudication_authorized": False,
        "authority": dict(NO_AUTHORITY),
    }


def human_execution_readiness(*, producer_receipt) -> dict:
    return {
        "schema": "JEPA_TD_REAL_R1_HUMAN_READINESS_V3",
        "status": "BLOCKED_R1_CELL_IDENTITY_NULL_PRODUCER_NOT_QUALIFIED",
        "reason": (
            "RELATION_LEVEL_MATCHED_NULL_IS_KNOWN_TRUTH_ONLY__HUMAN_R1_REQUIRES_INDEPENDENTLY_QUALIFIED_"
            "Y_CELL_IDENTITY_REASSIGNMENT_WITH_NULL_SPECIFIC_MEASURABILITY_AND_EXACT_VIEW_CUSTODY"
        ),
        "caller_relation_null_has_human_authority": False,
        "typed_producer_receipt_has_human_authority": False,
        "human_r1_adjudication_authorized": False,
        "tie_semantics": TIE_SEMANTICS,
        "required_null_preserves": list(MATCHED_NULL_PRESERVES),
        "authority": dict(NO_AUTHORITY),
    }
