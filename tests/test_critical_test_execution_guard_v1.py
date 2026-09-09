from pathlib import Path
import pytest

from sea_ad_jepa.v5.critical_test_execution_guard_v1 import (
    PASS,
    STOP_MISSING,
    STOP_SKIPPED,
    validate_junit_critical_tests,
)

def write_xml(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "junit.xml"
    p.write_text(f"<testsuite>{body}</testsuite>", encoding="utf-8")
    return p

def test_all_expected_critical_tests_must_execute_and_pass(tmp_path: Path):
    p = write_xml(
        tmp_path,
        '<testcase classname="t" name="torch_grad"/>'
        '<testcase classname="t" name="cuda_rng"/>',
    )
    r = validate_junit_critical_tests(
        p, expected_test_ids=["t::torch_grad", "t::cuda_rng"]
    )
    assert r.terminal == PASS and r.executed_passed == 2

def test_skipped_critical_test_is_not_green(tmp_path: Path):
    p = write_xml(
        tmp_path,
        '<testcase classname="t" name="torch_grad"><skipped/></testcase>',
    )
    with pytest.raises(RuntimeError, match=STOP_SKIPPED):
        validate_junit_critical_tests(p, expected_test_ids=["torch_grad"])

def test_missing_critical_test_is_not_green(tmp_path: Path):
    p = write_xml(tmp_path, '<testcase classname="t" name="other"/>')
    with pytest.raises(RuntimeError, match=STOP_MISSING):
        validate_junit_critical_tests(p, expected_test_ids=["torch_grad"])
