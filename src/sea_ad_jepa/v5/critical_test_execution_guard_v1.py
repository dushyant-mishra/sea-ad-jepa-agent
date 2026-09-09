"""Fail-closed execution guard for critical V5 tests."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

PASS = "PASS_CRITICAL_TEST_EXECUTION_GUARD_V1"
STOP_MISSING = "STOP_CRITICAL_TEST_MISSING"
STOP_SKIPPED = "STOP_CRITICAL_TEST_SKIPPED"
STOP_FAILED = "STOP_CRITICAL_TEST_FAILED"
STOP_ERRORED = "STOP_CRITICAL_TEST_ERRORED"
STOP_DUPLICATE = "STOP_CRITICAL_TEST_DUPLICATE"
STOP_EMPTY = "STOP_CRITICAL_TEST_AUTHORITY_EMPTY"

@dataclass(frozen=True)
class CriticalTestReport:
    expected: int
    executed_passed: int
    skipped: int
    failed: int
    errored: int
    missing: int
    terminal: str

def _case_id(case: ET.Element) -> str:
    classname = case.attrib.get("classname", "").strip()
    name = case.attrib.get("name", "").strip()
    if not name:
        raise ValueError("JUnit testcase missing name")
    return f"{classname}::{name}" if classname else name

def validate_junit_critical_tests(
    junit_xml: str | Path, *, expected_test_ids: Iterable[str]
) -> CriticalTestReport:
    expected = tuple(expected_test_ids)
    if not expected or any(not isinstance(x, str) or not x.strip() for x in expected):
        raise RuntimeError(STOP_EMPTY)
    if len(set(expected)) != len(expected):
        raise RuntimeError(STOP_DUPLICATE)

    root = ET.parse(str(junit_xml)).getroot()
    cases: dict[str, ET.Element] = {}
    by_name: dict[str, list[ET.Element]] = {}
    for case in root.iter("testcase"):
        cid = _case_id(case)
        if cid in cases:
            raise RuntimeError(f"{STOP_DUPLICATE}:{cid}")
        cases[cid] = case
        by_name.setdefault(case.attrib.get("name", ""), []).append(case)

    passed = skipped = failed = errored = missing = 0
    for expected_id in expected:
        case = cases.get(expected_id)
        if case is None and "::" not in expected_id:
            matches = by_name.get(expected_id, [])
            if len(matches) == 1:
                case = matches[0]
            elif len(matches) > 1:
                raise RuntimeError(f"{STOP_DUPLICATE}:{expected_id}")
        if case is None:
            missing += 1
            continue
        if case.find("skipped") is not None:
            skipped += 1
        elif case.find("failure") is not None:
            failed += 1
        elif case.find("error") is not None:
            errored += 1
        else:
            passed += 1

    if missing:
        raise RuntimeError(f"{STOP_MISSING}:{missing}")
    if skipped:
        raise RuntimeError(f"{STOP_SKIPPED}:{skipped}")
    if failed:
        raise RuntimeError(f"{STOP_FAILED}:{failed}")
    if errored:
        raise RuntimeError(f"{STOP_ERRORED}:{errored}")
    return CriticalTestReport(len(expected), passed, skipped, failed, errored, missing, PASS)
