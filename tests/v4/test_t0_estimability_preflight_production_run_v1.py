"""Tests for the Stage A estimability preflight production runner.

Stage A answers whether the frozen nuisance design is estimable on the assigned
roles and on every discovery LOODO fold. Two things need pinning: that it stays
pathology-blind and emits no covariate value, and that a rank deficiency is a
STOP rather than something reported and passed over.

Scope: fixtures and this repository's own artifacts. No pathology value, no
response, no numeric AT8.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_estimability_preflight_production_run_v1 as prerun  # noqa: E402
import t0_estimability_preflight_v1 as pre  # noqa: E402

PKG = ROOT / "outputs" / "t0_estimability_preflight_20260909"


# ---------------------------------------------------------------------------
# The emitted report carries ranks and identities, never a covariate value.
# ---------------------------------------------------------------------------

def test_the_leak_guard_scans_values_and_not_field_names() -> None:
    """A field name may legitimately contain a pathology token.

    `at8_availability_root_sha256` is a parent identity the report is required
    to bind. An earlier version of this guard scanned the serialised report as
    one string and refused that field, which is the same crude-substring error
    that once flagged an `age_present` header as an age value.
    """
    assert prerun.assert_no_covariate_value_in_report(
        {"at8_availability_root_sha256": "a" * 64,
         "technical_completeness_root_sha256": "b" * 64,
         "confirmation_nuisance_rank": 4}) is True


@pytest.mark.parametrize("leak", [
    {"sex": "Female"},
    {"donors": [{"sex": "Male"}]},
    {"nested": {"deep": {"value": "female"}}},
    {"endpoint": "braak_stage_iv"},
    {"endpoint": "percent AT8 positive area"},
    {"endpoint": "CERAD score"},
])
def test_a_covariate_or_pathology_value_in_the_report_is_refused(leak) -> None:
    with pytest.raises(AssertionError) as excinfo:
        prerun.assert_no_covariate_value_in_report(leak)
    assert prerun.STOP_COVARIATE_LEAK in str(excinfo.value)


def test_the_guard_walks_lists_and_nested_dictionaries() -> None:
    assert prerun.assert_no_covariate_value_in_report(
        {"a": [1, 2, {"b": ["x", None, 3.5]}], "c": True}) is True


# ---------------------------------------------------------------------------
# Estimability is a property of the design, and a deficiency is a STOP.
# ---------------------------------------------------------------------------

def test_a_single_sex_role_set_is_refused_rather_than_reported() -> None:
    """A loud design failure, never a biological NOT_MEASURABLE."""
    ages = [70.0 + i for i in range(20)]
    with pytest.raises(AssertionError) as excinfo:
        pre.nuisance_design(ages, [0.0] * 20)
    assert pre.STOP_SEX_NOT_BINARY in str(excinfo.value)


def test_the_frozen_design_is_quadratic_in_age_and_four_columns() -> None:
    ages = [65.0, 72.0, 80.0, 88.0, 95.0, 100.0]
    sexes = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    design = pre.nuisance_design(ages, sexes)
    assert len(design) == 6
    assert all(len(row) == 4 for row in design), "expected [1, age_c, age_c^2, sex]"
    assert pre.assert_full_rank(design, what="fixture") == 4


def test_a_rank_deficient_design_stops() -> None:
    """Two distinct ages cannot support a quadratic plus an intercept."""
    with pytest.raises(AssertionError) as excinfo:
        pre.assert_full_rank(
            pre.nuisance_design([70.0, 70.0, 80.0, 80.0],
                                [0.0, 1.0, 0.0, 1.0]),
            what="two distinct ages")
    assert pre.STOP_NOT_ESTIMABLE in str(excinfo.value)


def test_no_forbidden_remedy_is_declared() -> None:
    assert pre.assert_no_forbidden_remedy_declared() is True


# ---------------------------------------------------------------------------
# Stage A only, and it refuses a response.
# ---------------------------------------------------------------------------

def test_stages_b_and_c_refuse_a_response() -> None:
    """Estimability must not be computed with the outcome in hand."""
    for stage in (pre.stage_b_state_designs, pre.stage_c_tail_designs):
        with pytest.raises(AssertionError) as excinfo:
            stage(**{("confirmation_order"
                      if stage is pre.stage_b_state_designs
                      else "tail_order"): ("D1",)},
                  records={}, expected_records_root_sha256="0" * 64,
                  response=[1.0])
        assert pre.STOP_RESPONSE_PRESENT in str(excinfo.value)


def test_the_runner_declares_stage_a_only_and_says_why() -> None:
    source = (ROOT / "scripts" / "v4"
              / "t0_estimability_preflight_production_run_v1.py").read_text(
                  encoding="utf-8")
    assert "stages_b_and_c_run" in source
    assert "stages_b_and_c_reason" in source
    assert '"response_supplied": False' in source


# ---------------------------------------------------------------------------
# The production report, if it has been generated in this checkout.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not PKG.is_dir(), reason="the preflight has not been run")
def test_the_production_report_passes_its_own_leak_guard() -> None:
    report = json.loads((PKG / prerun.REPORT).read_text(encoding="utf-8"))
    assert prerun.assert_no_covariate_value_in_report(report) is True


@pytest.mark.skipif(not PKG.is_dir(), reason="the preflight has not been run")
def test_the_production_report_records_full_rank_everywhere() -> None:
    report = json.loads((PKG / prerun.REPORT).read_text(encoding="utf-8"))
    assert report["confirmation_donors"] == 18
    assert report["discovery_donors"] == 28
    assert report["confirmation_nuisance_rank"] == 4
    assert report["discovery_nuisance_rank"] == 4
    assert report["discovery_loodo_folds"] == 28
    assert report["all_loodo_folds_full_rank"] is True
    assert set(report["discovery_loodo_fold_ranks"].values()) == {4}
    assert report["nuisance_design_columns"] == 4
    assert report["donor_bound"] is True


@pytest.mark.skipif(not PKG.is_dir(), reason="the preflight has not been run")
def test_the_production_report_keeps_every_gate_closed() -> None:
    report = json.loads((PKG / prerun.REPORT).read_text(encoding="utf-8"))
    for flag in ("response_supplied", "pathology_values_read",
                 "numeric_at8_value_read", "covariate_values_emitted",
                 "real_execution_ready", "stages_b_and_c_run",
                 "sex_labels_emitted"):
        assert report[flag] is False, flag


@pytest.mark.skipif(not PKG.is_dir(), reason="the preflight has not been run")
def test_the_production_report_states_the_accurate_byte_semantics() -> None:
    """No new artifact may propagate the Git-blob mislabel."""
    report = json.loads((PKG / prerun.REPORT).read_text(encoding="utf-8"))
    assert "GIT_BLOB" not in report["code_byte_semantics"].replace(
        "NOT_GIT_BLOB_FRAMED", "")
    assert report["code_byte_semantics"].startswith(
        "SHA256_OVER_LF_NORMALIZED_FILE_CONTENT")


@pytest.mark.skipif(not PKG.is_dir(), reason="the preflight has not been run")
def test_the_production_report_binds_its_parents() -> None:
    report = json.loads((PKG / prerun.REPORT).read_text(encoding="utf-8"))
    for field in ("eligible_donor_root_sha256", "donor_role_root_sha256",
                  "age_sex_root_sha256", "at8_availability_root_sha256",
                  "technical_completeness_root_sha256",
                  "population_raw_source_root_sha256"):
        value = report["parents"][field]
        assert isinstance(value, str) and len(value) == 64, field
        assert all(c in "0123456789abcdef" for c in value), field
