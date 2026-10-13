from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import td_real_gate_rule_registry_v1 as R
import td_real_tournament_contract_v1 as C


class ReadinessV2Error(ValueError):
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


def _matrix_v1_path() -> Path:
    return _root() / "results" / "target_discovery" / "real_tournament" / "TD_REAL_GATE_EXECUTOR_READINESS_MATRIX_V1.csv"


def decode_json(value: str):
    return json.loads(value)


def project_rows(matrix_path: Path | None = None) -> list[dict[str, str]]:
    contract = C.load_real_tournament_contract()
    registry = C.validate_candidate_registry(contract)
    R.validate_rule_registry()

    with (matrix_path or _matrix_v1_path()).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    projected: list[dict[str, str]] = []
    for source in rows:
        row = dict(source)
        candidate_id = row["candidate_id"]
        gate_id = row["gate_id"]
        if candidate_id not in registry or gate_id not in R.RULES:
            raise ReadinessV2Error(f"unknown candidate/gate in V1 matrix: {(candidate_id, gate_id)}")
        required = gate_id in registry[candidate_id]["required_gates"]
        if (row["required"] == "True") != required:
            raise ReadinessV2Error(f"required flag drift: {(candidate_id, gate_id)}")

        if not required:
            if row["readiness"] != "NOT_APPLICABLE":
                raise ReadinessV2Error(f"non-required V1 row is not NOT_APPLICABLE: {(candidate_id, gate_id)}")
            projected.append(row)
            continue

        rule = R.RULES[gate_id]
        if gate_id in R.CALLABLE_STRUCTURAL:
            if rule["readiness"] != "CALLABLE_NEEDS_QUALIFICATION":
                raise ReadinessV2Error(f"structural rule readiness drift: {gate_id}")
            row.update({
                "readiness": "CALLABLE_NEEDS_QUALIFICATION",
                "estimand": rule["estimand"],
                "estimand_requirement": "Frozen structural/provenance estimand materialized prospectively; independent outcome-blind qualification pending.",
                "pass_fail_not_estimable_rule": rule["decision_rule"],
                "threshold_source": rule["threshold_source"],
                "callable_implementation": rule["callable_implementation"],
                "qualified_gate_executor_sha256": "",
                "estimand_sha256": rule["estimand_sha256"],
                "decision_rule_sha256": rule["decision_rule_sha256"],
                "blocker": "OUTCOME_BLIND_QUALIFICATION_REQUIRED",
            })
        else:
            if rule["readiness"] != "RULE_NOT_MATERIALIZED":
                raise ReadinessV2Error(f"unearned rule promotion: {gate_id}")
            row.update({
                "readiness": "RULE_NOT_MATERIALIZED",
                "callable_implementation": "",
                "qualified_gate_executor_sha256": "",
                "estimand_sha256": "",
                "decision_rule_sha256": "",
                "blocker": "BLOCKED_PROSPECTIVE_RULE_REQUIRED",
            })
        projected.append(row)

    return projected


def audit(matrix_path: Path | None = None) -> dict:
    contract = C.load_real_tournament_contract()
    registry = C.validate_candidate_registry(contract)
    gate_universe = list(R.RULES)
    expected_rows = len(C.CANDIDATE_IDS) * len(gate_universe)
    expected_seen = {(candidate, gate) for candidate in C.CANDIDATE_IDS for gate in gate_universe}

    rows = project_rows(matrix_path)
    if len(rows) != expected_rows:
        raise ReadinessV2Error(f"matrix row count mismatch: {len(rows)} != {expected_rows}")

    seen = set()
    counts = Counter()
    required_count = 0
    callable_required = 0
    for row in rows:
        key = (row["candidate_id"], row["gate_id"])
        if key in seen:
            raise ReadinessV2Error(f"duplicate candidate×gate row: {key}")
        seen.add(key)
        readiness = row["readiness"]
        if readiness not in READINESS:
            raise ReadinessV2Error(f"unknown readiness: {readiness}")
        counts[readiness] += 1

        required = row["required"] == "True"
        if required:
            required_count += 1
            if row["primary_biological_unit"] != "donor":
                raise ReadinessV2Error(f"donor-primary unit drift: {key}")
            if row["source_semantics"] != "observation_operator_not_biological_replicate":
                raise ReadinessV2Error(f"source semantics drift: {key}")
            if decode_json(row["support_eligibility_rule"]) != contract["support_semantics"]:
                raise ReadinessV2Error(f"support semantics drift: {key}")
            if decode_json(row["mandatory_candidate_falsifiers"]) != registry[row["candidate_id"]]["mandatory_falsifiers"]:
                raise ReadinessV2Error(f"candidate falsifier drift: {key}")

            if row["gate_id"] in R.CALLABLE_STRUCTURAL:
                callable_required += 1
                if readiness != "CALLABLE_NEEDS_QUALIFICATION":
                    raise ReadinessV2Error(f"structural role not awaiting qualification: {key}")
                if not row["callable_implementation"] or not row["estimand_sha256"] or not row["decision_rule_sha256"]:
                    raise ReadinessV2Error(f"materialized structural identity missing: {key}")
                if row["qualified_gate_executor_sha256"]:
                    raise ReadinessV2Error(f"unearned qualified executor SHA: {key}")
                if row["blocker"] != "OUTCOME_BLIND_QUALIFICATION_REQUIRED":
                    raise ReadinessV2Error(f"structural qualification blocker drift: {key}")
            else:
                if readiness != "RULE_NOT_MATERIALIZED":
                    raise ReadinessV2Error(f"unearned nonstructural promotion: {key}")
                if row["blocker"] != "BLOCKED_PROSPECTIVE_RULE_REQUIRED":
                    raise ReadinessV2Error(f"prospective-rule blocker drift: {key}")
                if any(row[field] for field in (
                    "callable_implementation", "qualified_gate_executor_sha256",
                    "estimand_sha256", "decision_rule_sha256",
                )):
                    raise ReadinessV2Error(f"unearned nonstructural callable/hash identity: {key}")
        elif readiness != "NOT_APPLICABLE":
            raise ReadinessV2Error(f"non-required row must remain NOT_APPLICABLE: {key}")

    if seen != expected_seen:
        raise ReadinessV2Error("candidate×gate Cartesian coverage mismatch")

    expected_counts = {
        "CALLABLE_AND_QUALIFIED": 0,
        "CALLABLE_NEEDS_QUALIFICATION": callable_required,
        "RULE_NOT_MATERIALIZED": required_count - callable_required,
        "BLOCKED_ON_DEPENDENCY": 0,
        "NOT_APPLICABLE": expected_rows - required_count,
    }
    if dict(counts) != {key: value for key, value in expected_counts.items() if value}:
        normalized = {key: counts.get(key, 0) for key in expected_counts}
        if normalized != expected_counts:
            raise ReadinessV2Error(f"readiness count mismatch: {normalized} != {expected_counts}")

    return {
        "status": "PASS_OUTCOME_BLIND_READINESS_V2_PROJECTION",
        "candidate_gate_rows": expected_rows,
        "required_roles": required_count,
        "unique_gate_count": len(gate_universe),
        "materialized_structural_gates": sorted(R.CALLABLE_STRUCTURAL),
        "readiness_counts": expected_counts,
        "real_tournament_qualify_eligible": False,
        "authority": dict(contract["authority"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-matrix-json", action="store_true")
    args = parser.parse_args()
    if args.emit_matrix_json:
        print(json.dumps(project_rows(), sort_keys=True))
    else:
        print(json.dumps(audit(), sort_keys=True))


if __name__ == "__main__":
    main()
