from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import audit_td_real_gate_executor_readiness_v2 as V2
import td_query_information_guard as Q
import td_real_gate_rule_registry_v1 as R
import td_real_tournament_contract_v1 as C


class ReadinessV3Error(ValueError):
    pass


_QUALIFICATION_FIELDS = {
    "schema",
    "status",
    "registry_sha256",
    "query_guard_sha256",
    "executor_bundle_sha256",
    "candidate_outcomes_opened",
    "real_tournament_authorized",
}


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _receipt_path() -> Path:
    return _root() / "results" / "target_discovery" / "real_tournament" / "TD_REAL_STRUCTURAL_GATE_QUALIFICATION_RECEIPT_V1.json"


def _file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_qualification_receipt(path: str | Path | None = None) -> dict:
    target = Path(path) if path is not None else _receipt_path()
    try:
        with target.open("r", encoding="utf-8") as handle:
            receipt = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessV3Error("structural qualification receipt unreadable") from exc
    return receipt


def _authenticate_receipt(receipt: dict) -> str:
    if not isinstance(receipt, dict) or set(receipt) != _QUALIFICATION_FIELDS:
        raise ReadinessV3Error("exact structural qualification receipt required")
    if receipt.get("schema") != "JEPA_TD_REAL_STRUCTURAL_GATE_QUALIFICATION_V1":
        raise ReadinessV3Error("structural qualification schema mismatch")
    if receipt.get("status") != "PASS_OUTCOME_BLIND_STRUCTURAL_EXECUTOR_MECHANICS":
        raise ReadinessV3Error("structural executor mechanics not qualified")
    if receipt.get("candidate_outcomes_opened") is not False:
        raise ReadinessV3Error("qualification receipt indicates candidate outcomes were opened")
    if receipt.get("real_tournament_authorized") is not False:
        raise ReadinessV3Error("qualification receipt may not grant real-tournament authority")

    registry_sha = _file_sha256(R.__file__)
    query_guard_sha = _file_sha256(Q.__file__)
    if receipt.get("registry_sha256") != registry_sha:
        raise ReadinessV3Error("structural registry SHA-256 mismatch")
    if receipt.get("query_guard_sha256") != query_guard_sha:
        raise ReadinessV3Error("query guard SHA-256 mismatch")
    bundle_sha = R.canonical_sha256({
        "query_guard_sha256": query_guard_sha,
        "registry_sha256": registry_sha,
    })
    if receipt.get("executor_bundle_sha256") != bundle_sha:
        raise ReadinessV3Error("structural executor bundle SHA-256 mismatch")
    return bundle_sha


def project_rows(*, qualification_receipt_path: str | Path | None = None) -> list[dict[str, str]]:
    receipt = load_qualification_receipt(qualification_receipt_path)
    bundle_sha = _authenticate_receipt(receipt)
    rows = V2.project_rows()
    projected: list[dict[str, str]] = []
    for source in rows:
        row = dict(source)
        if row["required"] == "True" and row["gate_id"] in R.CALLABLE_STRUCTURAL:
            if row["readiness"] != "CALLABLE_NEEDS_QUALIFICATION":
                raise ReadinessV3Error(
                    f"structural row is not qualification-pending before V3 promotion: {(row['candidate_id'], row['gate_id'])}"
                )
            rule = R.RULES[row["gate_id"]]
            if row["estimand_sha256"] != rule["estimand_sha256"] or row["decision_rule_sha256"] != rule["decision_rule_sha256"]:
                raise ReadinessV3Error(
                    f"structural gate identity drift: {(row['candidate_id'], row['gate_id'])}"
                )
            row.update({
                "readiness": "CALLABLE_AND_QUALIFIED",
                "callable_implementation": "td_real_gate_rule_registry_v1.execute_structural_gate",
                "qualified_gate_executor_sha256": bundle_sha,
                "blocker": "",
            })
        projected.append(row)
    return projected


def audit(*, qualification_receipt_path: str | Path | None = None) -> dict:
    contract = C.load_real_tournament_contract()
    rows = project_rows(qualification_receipt_path=qualification_receipt_path)
    counts = Counter(row["readiness"] for row in rows)
    required = [row for row in rows if row["required"] == "True"]
    qualified = [row for row in required if row["readiness"] == "CALLABLE_AND_QUALIFIED"]
    blocked = [row for row in required if row["readiness"] == "RULE_NOT_MATERIALIZED"]

    if len(rows) != 198 or len(required) != 117:
        raise ReadinessV3Error("candidate×gate matrix cardinality drift")
    if len(qualified) != 17 or {row["gate_id"] for row in qualified} != R.CALLABLE_STRUCTURAL:
        raise ReadinessV3Error("qualified structural role set drift")
    if len(blocked) != 100:
        raise ReadinessV3Error("unmaterialized required-role count drift")
    if any(row["gate_id"] in R.CALLABLE_STRUCTURAL for row in blocked):
        raise ReadinessV3Error("qualified structural role remained blocked")
    if any(
        row["readiness"] == "CALLABLE_AND_QUALIFIED" and row["gate_id"] not in R.CALLABLE_STRUCTURAL
        for row in rows
    ):
        raise ReadinessV3Error("unearned quantitative qualification")

    expected_counts = {
        "CALLABLE_AND_QUALIFIED": 17,
        "CALLABLE_NEEDS_QUALIFICATION": 0,
        "RULE_NOT_MATERIALIZED": 100,
        "BLOCKED_ON_DEPENDENCY": 0,
        "NOT_APPLICABLE": 81,
    }
    normalized = {key: counts.get(key, 0) for key in expected_counts}
    if normalized != expected_counts:
        raise ReadinessV3Error(f"readiness count drift: {normalized} != {expected_counts}")

    bundle_sha = load_qualification_receipt(qualification_receipt_path)["executor_bundle_sha256"]
    return {
        "status": "PASS_QUALIFIED_STRUCTURAL_EXECUTOR_READINESS_PROJECTION",
        "candidate_gate_rows": len(rows),
        "required_roles": len(required),
        "readiness_counts": expected_counts,
        "qualified_structural_unique_gates": sorted(R.CALLABLE_STRUCTURAL),
        "qualified_executor_bundle_sha256": bundle_sha,
        "unresolved_unique_gates": sorted(set(R.RULES) - R.CALLABLE_STRUCTURAL),
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
