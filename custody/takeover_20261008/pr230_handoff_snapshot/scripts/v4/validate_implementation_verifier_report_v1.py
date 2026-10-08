#!/usr/bin/env python3
"""Mechanical, fail-closed validator for MANDATORY_IMPLEMENTATION_VERIFIER_V1 reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "jepa-implementation-verifier-report-v1"
PASS = "PASS_IMPLEMENTATION_VERIFIER"
STOP_PREFIX = "STOP_IMPLEMENTATION_VERIFIER_"
REQUIRED = {
    "schema", "gate", "base_commit", "implementation_commit", "verifier_agent_identity",
    "controlling_contracts", "authority_hashes", "changed_files", "conclusion_bearing_symbols",
    "requirement_matrix", "independent_reference_summary", "independent_reference_uses_production_helper",
    "verifier_tests", "mutation_tests", "production_tests_observed", "coverage_complete",
    "independence_confirmed", "verifier_verdict", "stop_reason", "timestamp",
}
ROW_REQUIRED = {
    "requirement_id", "contract_source", "contract_text_or_formula", "production_file",
    "production_symbol", "production_lines_or_blob_sha", "independent_check_method",
    "independent_reference_file_or_inline_method", "adversarial_test", "mutation_attack",
    "applicable_mutations", "mutations_executed", "mutations_detected", "mutations_not_detected",
    "mutation_detected", "verdict", "notes",
}


def _nonempty(value, label: str) -> None:
    if not value:
        raise ValueError(f"empty {label}")


def validate_report(report: dict) -> dict[str, str]:
    if type(report) is not dict or set(report) != REQUIRED or report["schema"] != SCHEMA:
        raise ValueError("report schema/fields mismatch")
    for key in ("coverage_complete", "independence_confirmed", "independent_reference_uses_production_helper"):
        if type(report[key]) is not bool:
            raise ValueError(f"{key} must be built-in bool")
    for key in ("gate", "base_commit", "implementation_commit", "verifier_agent_identity",
                "controlling_contracts", "authority_hashes", "changed_files", "conclusion_bearing_symbols",
                "requirement_matrix", "independent_reference_summary", "verifier_tests", "mutation_tests",
                "production_tests_observed", "timestamp"):
        _nonempty(report[key], key)
    if report["independent_reference_uses_production_helper"]:
        raise ValueError("production helper cannot be independent reference")
    for row in report["requirement_matrix"]:
        if type(row) is not dict or set(row) != ROW_REQUIRED:
            raise ValueError("requirement row schema mismatch")
        if type(row["mutation_detected"]) is not bool:
            raise ValueError("mutation_detected must be built-in bool")
        for key in ("requirement_id", "contract_source", "contract_text_or_formula", "production_file",
                    "production_symbol", "production_lines_or_blob_sha", "independent_check_method",
                    "independent_reference_file_or_inline_method", "adversarial_test", "mutation_attack",
                    "applicable_mutations", "mutations_executed"):
            _nonempty(row[key], f"requirement.{key}")
        applicable = set(row["applicable_mutations"])
        executed = set(row["mutations_executed"])
        detected = set(row["mutations_detected"])
        survived = set(row["mutations_not_detected"])
        if not applicable <= executed or not applicable <= detected or survived or not row["mutation_detected"]:
            if report["verifier_verdict"] == PASS:
                raise ValueError("STOP_IMPLEMENTATION_VERIFIER_MUTATION_SURVIVED")
        if row["verdict"] != "PASS" and report["verifier_verdict"] == PASS:
            raise ValueError("requirement did not pass")
    verdict = report["verifier_verdict"]
    if verdict == PASS:
        if report["coverage_complete"] is not True or report["independence_confirmed"] is not True:
            raise ValueError("PASS requires complete independent coverage")
        if report["stop_reason"] is not None:
            raise ValueError("PASS cannot carry stop_reason")
    elif not (isinstance(verdict, str) and verdict.startswith(STOP_PREFIX) and report["stop_reason"]):
        raise ValueError("invalid verifier terminal")
    return {"schema": SCHEMA, "verdict": verdict, "structurally_valid": "true"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    result = validate_report(json.loads(args.report.read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
