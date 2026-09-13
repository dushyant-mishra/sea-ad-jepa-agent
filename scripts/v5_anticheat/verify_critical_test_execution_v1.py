#!/usr/bin/env python3
"""Verify that every frozen V5 critical test actually executed and passed."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.critical_test_execution_guard_v1 import validate_junit_critical_tests

SCHEMA = "JEPA_V5_CRITICAL_TEST_MANIFEST_V1"


def load_expected_test_ids(path: str | Path) -> tuple[str, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"schema", "expected_test_ids"}:
        raise ValueError("critical-test manifest schema mismatch")
    if payload["schema"] != SCHEMA:
        raise ValueError("unexpected critical-test manifest schema")
    ids = payload["expected_test_ids"]
    if not isinstance(ids, list) or not ids or any(not isinstance(x, str) or not x.strip() for x in ids):
        raise ValueError("expected_test_ids must be a nonempty list of strings")
    if len(set(ids)) != len(ids):
        raise ValueError("expected_test_ids must be unique")
    return tuple(ids)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    expected = load_expected_test_ids(args.manifest)
    report = validate_junit_critical_tests(args.junit, expected_test_ids=expected)
    print(report.terminal)
    print(f"expected={report.expected} executed_passed={report.executed_passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
