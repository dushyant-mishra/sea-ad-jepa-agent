"""Tests for the eligible-donor runner's parent loaders.

The authority module is tested separately. What matters here is the layer that
touches real authority packages on disk: whether it refuses a parent that has
grown a numeric column, whether it refuses a parent that does not cover the
candidate universe, and whether age and sex definedness is decided the way the
frozen predicate decides it.

Scope: fixtures only. No real pathology artifact, no sealed input.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "v4"))

import t0_eligible_donor_authority_v1 as eld  # noqa: E402
import t0_eligible_donor_production_run_v1 as runner  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _at8_pkg(tmp_path, *, rows=None, header="donor_id,AT8_available"):
    pkg = tmp_path / "at8"
    body = rows if rows is not None else ["D1,True", "D2,False", "D3,True"]
    _write(pkg / runner.AT8_REGISTRY, header + "\n" + "\n".join(body) + "\n")
    _write(pkg / runner.AT8_ROOT_FILE, "a" * 64 + "\n")
    return pkg


def _age_sex_pkg(tmp_path, rows):
    pkg = tmp_path / "agesex"
    _write(pkg / runner.AGE_SEX_REGISTRY,
           "donor_id,age,sex\n" + "\n".join(rows) + "\n")
    _write(pkg / runner.AGE_SEX_ROOT_FILE, "c" * 64 + "\n")
    return pkg


# ---------------------------------------------------------------------------
# The AT8 availability lane carries a boolean, and only a boolean.
#
# A numeric column appearing here would mean the availability lane had started
# carrying a magnitude, which is the one thing this lane exists to avoid. That is
# a specification failure to elevate, not a column to skip past.
# ---------------------------------------------------------------------------

def test_the_availability_lane_accepts_exactly_two_fields(tmp_path) -> None:
    loaded = runner.load_at8_availability(_at8_pkg(tmp_path))
    assert loaded["flags"] == {"D1": True, "D2": False, "D3": True}
    assert loaded["donors_covered"] == 3
    assert loaded["package_root_sha256"] == "a" * 64


def test_a_numeric_column_in_the_availability_lane_is_refused(
        tmp_path) -> None:
    pkg = _at8_pkg(tmp_path, header="donor_id,AT8_available,at8_percent",
                   rows=["D1,True,3.2", "D2,False,0.0"])
    with pytest.raises(AssertionError) as excinfo:
        runner.load_at8_availability(pkg)
    assert "MORE_THAN_A_BOOLEAN" in str(excinfo.value)


def test_any_extra_column_in_the_availability_lane_is_refused(
        tmp_path) -> None:
    """Even an innocuous-looking one: the permitted set is exact."""
    pkg = _at8_pkg(tmp_path, header="donor_id,AT8_available,notes",
                   rows=["D1,True,ok", "D2,False,ok"])
    with pytest.raises(AssertionError) as excinfo:
        runner.load_at8_availability(pkg)
    assert "MORE_THAN_A_BOOLEAN" in str(excinfo.value)


@pytest.mark.parametrize("bad", ["1", "0", "yes", "", "true", "TRUE", "NA"])
def test_a_non_boolean_availability_flag_is_refused(tmp_path, bad) -> None:
    pkg = _at8_pkg(tmp_path, rows=["D1,%s" % bad, "D2,False"])
    with pytest.raises(AssertionError) as excinfo:
        runner.load_at8_availability(pkg)
    assert eld.STOP_NOT_BOOLEAN in str(excinfo.value)


# ---------------------------------------------------------------------------
# Age and sex definedness, matched to the frozen predicate.
# ---------------------------------------------------------------------------

def test_age_and_sex_definedness_matches_the_frozen_predicate(
        tmp_path) -> None:
    pkg = _age_sex_pkg(tmp_path, [
        "D1,80,Female",       # both present
        "D2,,Male",           # age blank
        "D3,82,",             # sex blank
        "D4,nan,Female",      # age not finite
        "D5,inf,Male",        # age not finite
        "D6,not-a-number,F",  # age unparseable
        "D7,90,nan",          # sex is the string nan
        "D8,0,Female",        # zero is a finite age
    ])
    presence = runner.load_age_sex_presence(pkg)
    assert presence["age_present"] == {
        "D1": True, "D2": False, "D3": True, "D4": False, "D5": False,
        "D6": False, "D7": True, "D8": True}
    assert presence["sex_present"] == {
        "D1": True, "D2": True, "D3": False, "D4": True, "D5": True,
        "D6": True, "D7": False, "D8": True}


def test_no_age_or_sex_value_survives_the_presence_loader(tmp_path) -> None:
    """The loader returns booleans, and the values do not leave it."""
    pkg = _age_sex_pkg(tmp_path, ["D1,80,Female", "D2,82,Male"])
    presence = runner.load_age_sex_presence(pkg)
    serialised = json.dumps(presence)
    assert "80" not in serialised and "82" not in serialised
    assert "Female" not in serialised and "Male" not in serialised
    assert set(presence["age_present"].values()) <= {True, False}
    assert set(presence["sex_present"].values()) <= {True, False}


# ---------------------------------------------------------------------------
# Projection onto the candidate universe.
# ---------------------------------------------------------------------------

def test_a_broader_parent_is_projected_onto_the_universe() -> None:
    """The AT8 authority legitimately covers more donors than T0 studies."""
    broad = {"D%d" % i: True for i in range(1, 11)}
    projected = runner._project(broad, ["D2", "D5", "D7"], name="at8_available")
    assert projected == {"D2": True, "D5": True, "D7": True}


def test_a_parent_missing_a_candidate_donor_stops_with_the_parent_named(
) -> None:
    broad = {"D1": True, "D2": True}
    with pytest.raises(AssertionError) as excinfo:
        runner._project(broad, ["D1", "D2", "D3"], name="technical_complete")
    assert eld.STOP_PARENT_COVERAGE in str(excinfo.value)
    assert "technical_complete" in str(excinfo.value)
    assert "D3" in str(excinfo.value)


def test_projection_preserves_the_flag_values_it_narrows_to() -> None:
    """Narrowing must not change any answer, only which donors are asked."""
    broad = {"D1": True, "D2": False, "D3": True, "D4": False}
    projected = runner._project(broad, ["D2", "D3"], name="at8_available")
    assert projected == {"D2": False, "D3": True}


def test_a_projected_parent_is_accepted_by_the_authority_module() -> None:
    """The module refuses extras, so the runner's projection is what bridges it."""
    universe = ["H%02d.%03d" % (i // 10, i) for i in range(40)]
    broad = {d: True for d in universe + ["OUTSIDE_1", "OUTSIDE_2"]}
    with pytest.raises(AssertionError):
        eld.derive_eligible_donors(
            candidate_donors=universe, at8_available=broad,
            technical_complete=broad, age_present=broad, sex_present=broad)
    projected = runner._project(broad, universe, name="at8_available")
    rows = eld.derive_eligible_donors(
        candidate_donors=universe, at8_available=projected,
        technical_complete=projected, age_present=projected,
        sex_present=projected)
    assert len(rows) == 40
    assert sum(1 for r in rows if r["donor_role"] == "CONFIRMATION") == 18


# ---------------------------------------------------------------------------
# The candidate universe comes from the proven population, not from a caller.
# ---------------------------------------------------------------------------

def test_a_partial_population_package_cannot_close_the_universe(
        tmp_path) -> None:
    pkg = tmp_path / "b2"
    _write(pkg / "T0_B2_PRODUCTION_RUN_SUMMARY.json",
           json.dumps({"partial": True, "rows_proven": 10,
                       "population_raw_source_root_sha256": "b" * 64,
                       "package_root_sha256": "d" * 64}) + "\n")
    with pytest.raises(AssertionError) as excinfo:
        runner.load_candidate_universe(pkg)
    assert "partial smoke run" in str(excinfo.value)


def test_a_population_registry_shorter_than_its_claim_is_refused(
        tmp_path) -> None:
    pkg = tmp_path / "b2"
    _write(pkg / "T0_B2_PRODUCTION_RUN_SUMMARY.json",
           json.dumps({"partial": False, "rows_proven": 3,
                       "population_raw_source_root_sha256": "b" * 64,
                       "package_root_sha256": "d" * 64}) + "\n")
    _write(pkg / "T0_RAW_SOURCE_POPULATION_REGISTRY.csv",
           "logical_index,donor_id\n0,D1\n1,D2\n")
    with pytest.raises(AssertionError) as excinfo:
        runner.load_candidate_universe(pkg)
    assert "2 rows but the run proved 3" in str(excinfo.value)


def test_a_population_with_the_wrong_donor_count_is_refused(
        tmp_path) -> None:
    pkg = tmp_path / "b2"
    _write(pkg / "T0_B2_PRODUCTION_RUN_SUMMARY.json",
           json.dumps({"partial": False, "rows_proven": 3,
                       "population_raw_source_root_sha256": "b" * 64,
                       "package_root_sha256": "d" * 64}) + "\n")
    _write(pkg / "T0_RAW_SOURCE_POPULATION_REGISTRY.csv",
           "logical_index,donor_id\n0,D1\n1,D2\n2,D3\n")
    with pytest.raises(AssertionError) as excinfo:
        runner.load_candidate_universe(pkg)
    assert "3 donors in the population, expected 46" in str(excinfo.value)
