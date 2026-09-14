from __future__ import annotations

import importlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = "sea_ad_jepa.v5.environment_preflight_v1"
AUTHORITY_PATH = "src/sea_ad_jepa/v5/environment_preflight_v1.py"


def _module():
    spec = importlib.util.find_spec(MODULE)
    assert spec is not None, "environment preflight module must exist"
    return importlib.import_module(MODULE)


def _receipt():
    return {
        "schema": "JEPA_V5_ENVIRONMENT_PREFLIGHT_RECEIPT_V1",
        "environment_name": "sea-ad-jepa-v3",
        "python_version": "3.12.14",
        "torch_version": "2.14.0+cpu",
        "cuda_required": False,
        "cuda_available": False,
        "cuda_device_name": None,
        "sea_ad_jepa_v5_import_ok": True,
        "tests_collected": 254,
        "tests_passed": 254,
        "tests_failures": 0,
        "tests_errors": 0,
        "tests_skipped": 0,
        "critical_expected": 29,
        "critical_executed_passed": 29,
        "critical_skipped": 0,
        "critical_missing": 0,
        "git_head": "1" * 40,
        "expected_git_head": "1" * 40,
        "git_head_matches_expected": True,
        "authority_files": [AUTHORITY_PATH],
        "authority_files_clean": True,
        "authority_bytes_match_head": True,
        "authority_source_bundle_sha256": "2" * 64,
        "core_autocrlf": "false",
        "gitattributes_present": True,
        "terminal": "PASS_V5_ENVIRONMENT_PREFLIGHT_V1",
    }


def test_environment_preflight_receipt_round_trip_is_fail_closed():
    m = _module()
    envelope = m.seal_environment_preflight_receipt_v1(_receipt())
    payload = m.validate_environment_preflight_v1(envelope)
    assert payload["terminal"] == "PASS_V5_ENVIRONMENT_PREFLIGHT_V1"
    assert payload["tests_errors"] == 0
    assert payload["critical_executed_passed"] == payload["critical_expected"]
    assert payload["training_authorized"] is False


def test_environment_preflight_rejects_collection_skip_dependency_head_dirty_or_eol_failures():
    m = _module()
    cases = [
        ("tests_errors", 1, "TEST_ERRORS"),
        ("critical_skipped", 1, "CRITICAL_TEST"),
        ("critical_missing", 1, "CRITICAL_TEST"),
        ("sea_ad_jepa_v5_import_ok", False, "IMPORT"),
        ("git_head_matches_expected", False, "HEAD"),
        ("authority_files_clean", False, "DIRTY"),
        ("authority_bytes_match_head", False, "EOL_OR_BYTE"),
        ("gitattributes_present", False, "GITATTRIBUTES"),
    ]
    for field, value, pattern in cases:
        bad = _receipt(); bad[field] = value
        with pytest.raises(m.EnvironmentPreflightStop, match=pattern):
            m.seal_environment_preflight_receipt_v1(bad)


def test_environment_preflight_rejects_missing_torch_and_cuda_when_required():
    m = _module()
    bad = _receipt(); bad["torch_version"] = None
    with pytest.raises(m.EnvironmentPreflightStop, match="TORCH"):
        m.seal_environment_preflight_receipt_v1(bad)
    bad = _receipt(); bad["cuda_required"] = True; bad["cuda_available"] = False; bad["cuda_device_name"] = None
    with pytest.raises(m.EnvironmentPreflightStop, match="CUDA"):
        m.seal_environment_preflight_receipt_v1(bad)


def test_live_environment_collector_checks_real_git_bytes_and_junit_execution(tmp_path):
    m = _module()
    junit = tmp_path / "junit.xml"
    junit.write_text(
        '<testsuites tests="1" failures="0" errors="0" skipped="0">'
        '<testsuite name="probe" tests="1" failures="0" errors="0" skipped="0">'
        '<testcase classname="probe" name="test_environment_probe" />'
        '</testsuite></testsuites>',
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"expected_test_ids": ["test_environment_probe"]}), encoding="utf-8")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    receipt = m.collect_environment_preflight_v1(
        root=ROOT,
        expected_head=head,
        junit_path=junit,
        critical_manifest_path=manifest,
        authority_paths=[AUTHORITY_PATH],
        cuda_required=False,
    )
    payload = m.validate_environment_preflight_v1(m.seal_environment_preflight_receipt_v1(receipt))
    assert payload["tests_collected"] == 1
    assert payload["critical_expected"] == 1
    assert payload["critical_executed_passed"] == 1
    assert payload["authority_bytes_match_head"] is True
