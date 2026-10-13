from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import td_real_tournament_contract_v1 as C


class ReadinessAuditError(ValueError):
    pass


READINESS = {
    "CALLABLE_AND_QUALIFIED",
    "CALLABLE_NEEDS_QUALIFICATION",
    "RULE_NOT_MATERIALIZED",
    "BLOCKED_ON_DEPENDENCY",
    "NOT_APPLICABLE",
}


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _matrix_path() -> Path:
    return _root() / "results" / "target_discovery" / "real_tournament" / "TD_REAL_GATE_EXECUTOR_READINESS_MATRIX_V1.csv"


def _summary_path() -> Path:
    return _root() / "results" / "target_discovery" / "real_tournament" / "TD_REAL_GATE_EXECUTOR_READINESS_MATRIX_V1_SUMMARY.json"


def audit(matrix_path: Path | None = None, summary_path: Path | None = None) -> dict:
    contract = C.load_real_tournament_contract()
    registry = C.validate_candidate_registry(contract)
    gate_universe = list(dict.fromkeys(g for candidate in C.CANDIDATE_IDS for g in registry[candidate]["required_gates"]))

    with (matrix_path or _matrix_path()).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected_rows = len(C.CANDIDATE_IDS) * len(gate_universe)
    if len(rows) != expected_rows:
        raise ReadinessAuditError(f"matrix row count mismatch: {len(rows)} != {expected_rows}")

    seen = set()
    counts = Counter()
    required_count = 0
    for row in rows:
        key = (row["candidate_id"], row["gate_id"])
        if key in seen:
            raise ReadinessAuditError(f"duplicate candidate×gate row: {key}")
        seen.add(key)
        if row["candidate_id"] not in registry or row["gate_id"] not in gate_universe:
            raise ReadinessAuditError(f"unknown candidate/gate: {key}")
        readiness = row["readiness"]
        if readiness not in READINESS:
            raise ReadinessAuditError(f"unknown readiness class: {readiness}")
        required = row["required"] == "True"
        expected_required = row["gate_id"] in registry[row["candidate_id"]]["required_gates"]
        if required != expected_required:
            raise ReadinessAuditError(f"required flag drift: {key}")
        counts[readiness] += 1
        if required:
            required_count += 1
            if readiness != "RULE_NOT_MATERIALIZED":
                raise ReadinessAuditError(f"unsupported readiness promotion without executor evidence: {key}")
            if row["primary_biological_unit"] != "donor":
                raise ReadinessAuditError(f"donor-primary unit drift: {key}")
            if row["source_semantics"] != "observation_operator_not_biological_replicate":
                raise ReadinessAuditError(f"source semantics drift: {key}")
            support = json.loads(row["support_eligibility_rule"])
            if support != contract["support_semantics"]:
                raise ReadinessAuditError(f"support semantics drift: {key}")
            if row["blocker"] != "BLOCKED_PROSPECTIVE_RULE_REQUIRED":
                raise ReadinessAuditError(f"missing prospective-rule blocker: {key}")
            if any(row[field] for field in (
                "callable_implementation", "qualified_gate_executor_sha256",
                "estimand_sha256", "decision_rule_sha256",
            )):
                raise ReadinessAuditError(f"unearned callable/hash identity: {key}")
        elif readiness != "NOT_APPLICABLE":
            raise ReadinessAuditError(f"non-required gate must be NOT_APPLICABLE: {key}")

    expected_seen = {(candidate, gate) for candidate in C.CANDIDATE_IDS for gate in gate_universe}
    if seen != expected_seen:
        raise ReadinessAuditError("candidate×gate Cartesian coverage mismatch")

    with (summary_path or _summary_path()).open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    expected_counts = {
        "CALLABLE_AND_QUALIFIED": 0,
        "CALLABLE_NEEDS_QUALIFICATION": 0,
        "RULE_NOT_MATERIALIZED": required_count,
        "BLOCKED_ON_DEPENDENCY": 0,
        "NOT_APPLICABLE": expected_rows - required_count,
    }
    if summary.get("readiness_counts") != expected_counts:
        raise ReadinessAuditError("summary readiness counts mismatch")
    if summary.get("candidate_gate_row_count") != expected_rows or summary.get("required_role_count") != required_count:
        raise ReadinessAuditError("summary row/required counts mismatch")
    if summary.get("real_tournament_qualify_eligible") is not False:
        raise ReadinessAuditError("real tournament QUALIFY must remain ineligible")
    authority = summary.get("authority")
    if not isinstance(authority, dict) or any(value is not False for value in authority.values()):
        raise ReadinessAuditError("readiness summary must grant no authority")

    return {
        "status": "PASS_OUTCOME_BLIND_READINESS_MATRIX_STRUCTURE",
        "candidate_gate_rows": expected_rows,
        "required_roles": required_count,
        "readiness_counts": expected_counts,
        "real_tournament_qualify_eligible": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
