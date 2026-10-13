from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.v5 import audit_td_real_gate_executor_readiness_v3 as V3
from scripts.v5 import td_real_directional_gate_executors_v2 as D
from scripts.v5 import td_real_gate_rule_registry_v1 as R
from scripts.v5 import td_real_tournament_contract_v1 as C


class ReadinessV4Error(ValueError):
    pass


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _receipt_path() -> Path:
    return _root() / "results" / "target_discovery" / "real_tournament" / "TD_REAL_DIRECTIONAL_GATES_V2_QUALIFICATION_RECEIPT.json"


def load_qualification_receipt(path: str | Path | None = None) -> dict:
    target = Path(path) if path is not None else _receipt_path()
    try:
        with target.open("r", encoding="utf-8") as handle:
            receipt = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessV4Error("V2 directional qualification receipt unreadable") from exc
    return receipt


def project_rows(*, qualification_receipt_path: str | Path | None = None) -> list[dict[str, str]]:
    receipt = load_qualification_receipt(qualification_receipt_path)
    try:
        bundle_sha = D.authenticate_qualification_receipt(receipt)
    except D.DirectionalGateError as exc:
        raise ReadinessV4Error(str(exc)) from exc

    rows = V3.project_rows()
    projected: list[dict[str, str]] = []
    for source in rows:
        row = dict(source)
        if row["required"] == "True" and row["gate_id"] in D.CLEARED_V2_GATES:
            if row["readiness"] != "RULE_NOT_MATERIALIZED":
                raise ReadinessV4Error(
                    f"V2-cleared role was not blocked before promotion: {(row['candidate_id'], row['gate_id'])}"
                )
            rule = D.RULES[row["gate_id"]]
            row.update({
                "readiness": "CALLABLE_AND_QUALIFIED",
                "callable_implementation": "td_real_directional_gate_executors_v2.execute_directional_gate",
                "estimand_sha256": rule["estimand_sha256"],
                "decision_rule_sha256": rule["decision_rule_sha256"],
                "qualified_gate_executor_sha256": bundle_sha,
                "blocker": "",
            })
        projected.append(row)
    return projected


def audit(*, qualification_receipt_path: str | Path | None = None) -> dict:
    rows = project_rows(qualification_receipt_path=qualification_receipt_path)
    contract = C.load_real_tournament_contract()
    counts = Counter(row["readiness"] for row in rows)
    required = [row for row in rows if row["required"] == "True"]
    qualified = [row for row in required if row["readiness"] == "CALLABLE_AND_QUALIFIED"]
    newly = [row for row in qualified if row["gate_id"] in D.CLEARED_V2_GATES]
    blocked = [row for row in required if row["readiness"] == "RULE_NOT_MATERIALIZED"]

    if len(rows) != 198 or len(required) != 117:
        raise ReadinessV4Error("candidate×gate matrix cardinality drift")
    if len(newly) != 49 or {row["gate_id"] for row in newly} != D.CLEARED_V2_GATES:
        raise ReadinessV4Error("V2-cleared candidate×gate role set drift")
    if len(qualified) != 66 or {row["gate_id"] for row in qualified} != (R.CALLABLE_STRUCTURAL | D.CLEARED_V2_GATES):
        raise ReadinessV4Error("qualified gate set drift")
    if len(blocked) != 51 or {row["gate_id"] for row in blocked} != D.BLOCKED_V2_GATES:
        raise ReadinessV4Error("blocked prospective role set drift")
    if any(row["gate_id"] in D.BLOCKED_V2_GATES and row["readiness"] != "RULE_NOT_MATERIALIZED" for row in required):
        raise ReadinessV4Error("blocked V2 rule was promoted")

    expected_counts = {
        "CALLABLE_AND_QUALIFIED": 66,
        "CALLABLE_NEEDS_QUALIFICATION": 0,
        "RULE_NOT_MATERIALIZED": 51,
        "BLOCKED_ON_DEPENDENCY": 0,
        "NOT_APPLICABLE": 81,
    }
    normalized = {key: counts.get(key, 0) for key in expected_counts}
    if normalized != expected_counts:
        raise ReadinessV4Error(f"readiness count drift: {normalized} != {expected_counts}")

    return {
        "status": "PASS_QUALIFIED_V2_DIRECTIONAL_STRUCTURAL_EXECUTOR_READINESS_PROJECTION",
        "candidate_gate_rows": len(rows),
        "required_roles": len(required),
        "newly_qualified_role_count": len(newly),
        "newly_qualified_unique_gates": sorted(D.CLEARED_V2_GATES),
        "blocked_unique_gates": sorted(D.BLOCKED_V2_GATES),
        "readiness_counts": expected_counts,
        "qualified_unique_gates": sorted(R.CALLABLE_STRUCTURAL | D.CLEARED_V2_GATES),
        "real_tournament_qualify_eligible": False,
        "authority": dict(contract["authority"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt")
    parser.add_argument("--emit-matrix-json", action="store_true")
    args = parser.parse_args()
    if args.emit_matrix_json:
        print(json.dumps(project_rows(qualification_receipt_path=args.receipt), sort_keys=True))
    else:
        print(json.dumps(audit(qualification_receipt_path=args.receipt), sort_keys=True))


if __name__ == "__main__":
    main()
