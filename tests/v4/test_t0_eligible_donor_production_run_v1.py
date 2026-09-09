"""Tests for the eligible-donor runner's parent replay.

The authority module is tested separately. What matters here is the layer that
consumes real parent authority packages.

After R6 these loaders no longer read a package's own root file and trust it.
They replay each parent through that authority's own loader, bound to expected
roots frozen in the committed runner. So the fixtures below have to be complete,
valid packages, and a test that wants to reach a defence-in-depth field check has
to supply matching expected roots to get past the identity check first. That is
the contract these tests now pin.

Scope: fixtures and this repository's own artifacts. No pathology value, no
sealed input, no numeric AT8 magnitude.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_age_sex_authority_v1 as ages  # noqa: E402
import t0_at8_availability_authority_v1 as at8  # noqa: E402
import t0_eligible_donor_authority_v1 as eld  # noqa: E402
import t0_eligible_donor_production_run_v1 as runner  # noqa: E402

AT8_PKG = ROOT / "outputs" / "t0_at8_availability_20260908"
AGE_SEX_PKG = ROOT / "outputs" / "t0_age_sex_20260908"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _at8_fixture(tmp_path, *, header="donor_id,AT8_available", rows=None,
                 name="at8"):
    """A complete, valid AT8-shaped package, with its roots returned.

    Written through the authority's own flat-package writer so the manifest and
    root file follow the real convention rather than a reimplementation of it.
    """
    body = rows if rows is not None else ["D1,True", "D2,False", "D3,True"]
    registry = (header + "\n" + "\n".join(body) + "\n").encode("utf-8")
    available = sum(1 for line in body if line.endswith(",True"))
    metadata = (json.dumps({
        "schema": at8.SCHEMA,
        "namespace": at8.NAMESPACE,
        "finalized": True,
        "real_execution_ready": False,
        "total_donor_count": len(body),
        "available_donor_count": available,
        "numeric_at8_value_parsed": False,
        "numeric_at8_value_retained": False,
        "numeric_at8_value_emitted": False,
        "membership_donor_set_sha256": "a" * 64,
    }, sort_keys=True, indent=2) + "\n").encode("utf-8")

    pkg = tmp_path / name
    package_root = at8._write_flat_package(
        pkg, {at8.REGISTRY: registry, at8.METADATA: metadata})
    return pkg, package_root, hashlib.sha256(registry).hexdigest()


def _load_at8(pkg, package_root, availability_root):
    return runner.load_at8_availability(
        pkg,
        expected_package_root_sha256=package_root,
        expected_availability_root_sha256=availability_root)


# ---------------------------------------------------------------------------
# The frozen expectations live in committed code, which is the R6 repair.
# ---------------------------------------------------------------------------

def test_the_runner_freezes_its_parent_identities_in_committed_code() -> None:
    """A substituted parent must be refused by identity, not by self-agreement."""
    for value in (runner.AT8_EXPECTED_PACKAGE_ROOT,
                  runner.AT8_EXPECTED_AVAILABILITY_ROOT,
                  runner.AGE_SEX_EXPECTED_PACKAGE_ROOT,
                  runner.AGE_SEX_EXPECTED_ROOT,
                  runner.AGE_SEX_EXPECTED_SOURCE_SHA256,
                  runner.AGE_SEX_EXPECTED_CANDIDATE_DONOR_SET):
        assert isinstance(value, str) and len(value) == 64
        assert all(c in "0123456789abcdef" for c in value)


def test_the_verification_flag_is_never_a_caller_literal() -> None:
    source = (ROOT / "scripts" / "v4"
              / "t0_eligible_donor_production_run_v1.py").read_text(
                  encoding="utf-8")
    assert "at8_availability_independently_verified=True" not in source


# ---------------------------------------------------------------------------
# The AT8 availability lane carries a boolean, and only a boolean.
#
# These reach the runner's own field checks by supplying the fixture's matching
# roots. Without that the identity check fires first and the field check would
# never be exercised -- the same trap that made an earlier mutation suite in this
# lane test nothing.
# ---------------------------------------------------------------------------

def test_a_valid_availability_package_replays_and_reports_its_roots(
        tmp_path) -> None:
    pkg, package_root, availability_root = _at8_fixture(tmp_path)
    loaded = _load_at8(pkg, package_root, availability_root)
    assert loaded["flags"] == {"D1": True, "D2": False, "D3": True}
    assert loaded["donors_covered"] == 3
    assert loaded["package_root_sha256"] == package_root
    assert loaded["availability_root_sha256"] == availability_root
    assert loaded["independently_verified"] is True
    assert loaded["expected_roots_supplied_externally"] is True


def test_a_substituted_availability_package_is_refused(tmp_path) -> None:
    """Self-consistent, and still refused, because identity comes from outside."""
    pkg, _package_root, _availability_root = _at8_fixture(
        tmp_path, rows=["D1,False", "D2,False", "D3,True"])
    with pytest.raises(AssertionError) as excinfo:
        runner.load_at8_availability(pkg)  # frozen production expectations
    assert at8.STOP_EXTERNAL_ROOT in str(excinfo.value)


def test_a_numeric_column_in_the_availability_lane_is_refused(
        tmp_path) -> None:
    pkg, package_root, availability_root = _at8_fixture(
        tmp_path, header="donor_id,AT8_available,at8_percent",
        rows=["D1,True,3.2", "D2,False,0.0"])
    with pytest.raises(AssertionError) as excinfo:
        _load_at8(pkg, package_root, availability_root)
    message = str(excinfo.value)
    assert ("MORE_THAN_A_BOOLEAN" in message
            or at8.STOP_PACKAGE in message)


def test_any_extra_column_in_the_availability_lane_is_refused(
        tmp_path) -> None:
    """Even an innocuous one: the permitted set is exact, not a denylist."""
    pkg, package_root, availability_root = _at8_fixture(
        tmp_path, header="donor_id,AT8_available,notes",
        rows=["D1,True,ok", "D2,False,ok"])
    with pytest.raises(AssertionError) as excinfo:
        _load_at8(pkg, package_root, availability_root)
    message = str(excinfo.value)
    assert ("MORE_THAN_A_BOOLEAN" in message
            or at8.STOP_PACKAGE in message)


@pytest.mark.parametrize("bad", ["1", "0", "yes", "true", "TRUE", "NA", ""])
def test_a_non_boolean_availability_flag_is_refused(tmp_path, bad) -> None:
    pkg, package_root, availability_root = _at8_fixture(
        tmp_path, rows=["D1,%s" % bad, "D2,False"])
    with pytest.raises(AssertionError) as excinfo:
        _load_at8(pkg, package_root, availability_root)
    message = str(excinfo.value)
    assert (eld.STOP_NOT_BOOLEAN in message or at8.STOP_PACKAGE in message)


def test_a_package_claiming_readiness_is_refused(tmp_path) -> None:
    pkg, _pr, _ar = _at8_fixture(tmp_path)
    path = pkg / at8.METADATA
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["real_execution_ready"] = True
    blob = (json.dumps(meta, sort_keys=True, indent=2) + "\n").encode("utf-8")
    package_root = at8._write_flat_package(
        pkg, {at8.REGISTRY: (pkg / at8.REGISTRY).read_bytes(),
              at8.METADATA: blob})
    availability_root = hashlib.sha256(
        (pkg / at8.REGISTRY).read_bytes()).hexdigest()
    with pytest.raises(AssertionError) as excinfo:
        _load_at8(pkg, package_root, availability_root)
    assert at8.STOP_PACKAGE in str(excinfo.value)


@pytest.mark.parametrize("flag", ["numeric_at8_value_parsed",
                                  "numeric_at8_value_retained",
                                  "numeric_at8_value_emitted"])
def test_a_package_claiming_it_parsed_a_magnitude_is_refused(
        tmp_path, flag) -> None:
    """The availability lane's whole point is that it never read a magnitude."""
    pkg, _pr, _ar = _at8_fixture(tmp_path)
    path = pkg / at8.METADATA
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta[flag] = True
    blob = (json.dumps(meta, sort_keys=True, indent=2) + "\n").encode("utf-8")
    registry = (pkg / at8.REGISTRY).read_bytes()
    package_root = at8._write_flat_package(
        pkg, {at8.REGISTRY: registry, at8.METADATA: blob})
    with pytest.raises(AssertionError) as excinfo:
        _load_at8(pkg, package_root, hashlib.sha256(registry).hexdigest())
    assert "CLAIMS_A_NUMERIC_VALUE" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Age and sex, against the real authority.
#
# The old fixture-based definedness test is gone, and its removal is the finding
# rather than a loss of coverage: the age/sex authority parses through
# `exact_age` and `exact_sex`, which refuse a non-finite age or an
# out-of-vocabulary sex. A donor with a missing covariate cannot be carried at
# all, so it is a parent STOP rather than an ineligible donor -- the same
# fail-closed rule the eligible-donor authority applies to coverage gaps.
# ---------------------------------------------------------------------------

def test_a_non_finite_age_cannot_be_carried_by_the_parent_at_all() -> None:
    for bad in ("", "nan", "inf", "-inf", "not-a-number", None):
        with pytest.raises(AssertionError):
            ages.exact_age(bad, what="age for D1")


def test_a_sex_outside_the_frozen_vocabulary_is_refused() -> None:
    for bad in ("", "F", "M", "unknown", "nan", None):
        with pytest.raises(AssertionError):
            ages.exact_sex(bad, what="sex for D1")


@pytest.mark.skipif(not AGE_SEX_PKG.is_dir(),
                    reason="the real age/sex package is absent")
def test_the_real_age_sex_parent_replays_and_emits_presence_only() -> None:
    loaded = runner.load_age_sex_presence(AGE_SEX_PKG)
    assert loaded["donors_covered"] == 46
    assert loaded["independently_verified"] is True
    assert loaded["expected_roots_supplied_externally"] is True
    assert loaded["package_root_sha256"] == runner.AGE_SEX_EXPECTED_PACKAGE_ROOT
    assert loaded["age_sex_root_sha256"] == runner.AGE_SEX_EXPECTED_ROOT
    # Presence is True for every donor because the parent refused anything else.
    assert set(loaded["age_present"].values()) == {True}
    assert set(loaded["sex_present"].values()) == {True}
    assert loaded["presence_is_proven_upstream_by_exact_age_and_exact_sex"]
    assert loaded["covariate_values_emitted"] is False
    # And no covariate value leaves the loader.
    serialised = json.dumps(loaded, sort_keys=True)
    for needle in ("Female", "Male", "\"age\": 8", "\"age\": 9"):
        assert needle not in serialised


@pytest.mark.skipif(not AGE_SEX_PKG.is_dir(),
                    reason="the real age/sex package is absent")
def test_a_substituted_age_sex_package_is_refused(tmp_path) -> None:
    import shutil
    pkg = tmp_path / "agesex"
    shutil.copytree(AGE_SEX_PKG, pkg)
    registry = pkg / ages.REGISTRY
    lines = registry.read_text(encoding="utf-8").splitlines()
    cells = lines[1].split(",")
    cells[1] = str(int(cells[1]) + 1)
    lines[1] = ",".join(cells)
    _write(registry, "\n".join(lines) + "\n")
    with pytest.raises(AssertionError) as excinfo:
        runner.load_age_sex_presence(pkg)
    assert ages.STOP_ROOT_MISMATCH in str(excinfo.value)


@pytest.mark.skipif(not AT8_PKG.is_dir(),
                    reason="the real AT8 package is absent")
def test_the_real_at8_parent_replays_against_the_frozen_roots() -> None:
    loaded = runner.load_at8_availability(AT8_PKG)
    assert loaded["donors_covered"] == 84
    assert loaded["package_root_sha256"] == runner.AT8_EXPECTED_PACKAGE_ROOT
    assert loaded["availability_root_sha256"] == (
        runner.AT8_EXPECTED_AVAILABILITY_ROOT)
    assert loaded["independently_verified"] is True
    assert loaded["numeric_at8_value_parsed"] is False


# ---------------------------------------------------------------------------
# Projection onto the candidate universe. Unchanged by R6.
# ---------------------------------------------------------------------------

def test_a_broader_parent_is_projected_onto_the_universe() -> None:
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
    broad = {"D1": True, "D2": False, "D3": True, "D4": False}
    projected = runner._project(broad, ["D2", "D3"], name="at8_available")
    assert projected == {"D2": False, "D3": True}


def test_a_projected_parent_is_accepted_by_the_authority_module() -> None:
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
