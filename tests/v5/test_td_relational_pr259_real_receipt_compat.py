"""Canonical-machine compatibility check for the exact audited PR #259 V3 receipt bytes.

This test is inert unless both environment variables below are supplied. It creates no runtime value
authorization and does not execute G6/G7 or read expression data.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMMON = ROOT / "scripts" / "v5" / "td_relational_value_read_v2_common.py"

DRIVER_SHA = "62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae"
MAPPING_SHA = "6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0"


def load_common():
    spec = importlib.util.spec_from_file_location("td_v2_common_real_pr259", COMMON)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_exact_pr259_v3_receipts_are_accepted_without_value_authority():
    driver_env = os.environ.get("TD_PR259_PREFLIGHT_RESULT")
    mapping_env = os.environ.get("TD_PR259_MAPPING_RECEIPT")
    if not driver_env or not mapping_env:
        pytest.skip("set TD_PR259_PREFLIGHT_RESULT and TD_PR259_MAPPING_RECEIPT to exact PR259 files")

    driver = Path(driver_env)
    mapping = Path(mapping_env)
    assert driver.is_file(), driver
    assert mapping.is_file(), mapping
    assert sha256(driver) == DRIVER_SHA
    assert sha256(mapping) == MAPPING_SHA

    m = load_common()
    preflight, mapping_rec = m.load_bound_preflight(
        driver,
        mapping,
        expected_preflight_sha=DRIVER_SHA,
        expected_mapping_sha=MAPPING_SHA,
    )

    assert preflight["schema"] == "JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V3"
    assert preflight["status"] == "PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND"
    assert mapping_rec["schema"] == "JEPA_TD_RELATIONAL_MAPPING_PREFLIGHT_V3"
    assert mapping_rec["status"] == "PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND"
    for key in m.REQUIRED_MAPPING_CHECKS:
        assert preflight["mapping_checks"][key] is True
        assert mapping_rec["checks"][key] is True

    assert preflight["real_value_replay_authorized"] is False
    assert preflight["training_authorized"] is False
    assert mapping_rec["real_value_replay_authorized_by_this_receipt"] is False
    assert mapping_rec["training_authorized"] is False
