"""Adversarial cases for the T0 IMMUNE support-count authority.

Scope: verifies the integrity of this project's own derived data and provenance
records, in this repository. No third-party system, no network, no credentials
and no security control belonging to any system is involved.

The load-bearing property is WHICH population `cells` counts. It is the accepted
broad-IMMUNE support -- 46 donors summing to exactly 20,804 -- and not the
638,150 all-op31 count. Against the all-op31 count every donor would clear the
frozen 80-cell floor trivially and the tail flag would carry no information, so
the suite pins the totals and pins the floor's scope.
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
if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_immune_support_count_authority_v1 as sup  # noqa: E402

MATRIX = sup.MTG_MATRIX_ID
OPERATOR = sup.OP31_OPERATOR_INDEX
CODE_SHA = "a" * 64


def _membership(cells, *, operator=OPERATOR, matrix=MATRIX) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["source", "matrix_id", "operator_index", "donor_id", "cell_id"])
    for cell, donor in cells:
        writer.writerow(["SEA_AD", matrix, operator, donor, cell])
    return buffer.getvalue().encode("utf-8")


@pytest.fixture()
def membership() -> bytes:
    return _membership([("c1", "D1"), ("c2", "D1"), ("c3", "D1"),
                        ("c4", "D2"), ("c5", "D2")])


def _counts(membership_bytes: bytes, **overrides):
    kwargs = dict(membership_bytes=membership_bytes,
                  expected_membership_sha256=hashlib.sha256(
                      membership_bytes).hexdigest())
    kwargs.update(overrides)
    return sup.support_counts_from_membership(**kwargs)


# --- derivation from the accepted membership --------------------------------

def test_counts_are_per_donor_accepted_immune_cells(membership: bytes) -> None:
    assert _counts(membership) == {"D1": 3, "D2": 2}


def test_a_membership_digest_mismatch_stops(membership: bytes) -> None:
    with pytest.raises(AssertionError) as excinfo:
        _counts(membership, expected_membership_sha256="f" * 64)
    assert sup.STOP_MEMBERSHIP_DIGEST in str(excinfo.value)


def test_a_membership_for_another_operator_is_refused() -> None:
    other = _membership([("c1", "D1")], operator=30)
    with pytest.raises(AssertionError) as excinfo:
        _counts(other)
    assert sup.STOP_OPERATOR in str(excinfo.value)


def test_a_membership_for_another_matrix_is_refused() -> None:
    other = _membership([("c1", "D1")], matrix="sea_ad_pfc_rna_final_2026")
    with pytest.raises(AssertionError) as excinfo:
        _counts(other)
    assert sup.STOP_MATRIX in str(excinfo.value)


def test_a_duplicate_cell_is_refused() -> None:
    """A duplicate would inflate a donor's support silently."""
    dup = _membership([("c1", "D1"), ("c1", "D1")])
    with pytest.raises(AssertionError) as excinfo:
        _counts(dup)
    assert sup.STOP_DUPLICATE_CELL in str(excinfo.value)


def test_a_membership_missing_a_required_column_stops() -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["source", "matrix_id", "operator_index", "donor_id"])
    writer.writerow(["SEA_AD", MATRIX, OPERATOR, "D1"])
    broken = buffer.getvalue().encode("utf-8")
    with pytest.raises(AssertionError) as excinfo:
        _counts(broken)
    assert sup.STOP_COLUMNS in str(excinfo.value)


# --- binding the rows -------------------------------------------------------

def test_rows_are_exact_integers_in_deterministic_order() -> None:
    rows = sup.build_support_rows(counts_by_donor={"D2": 2, "D1": 3})
    assert [r["donor_id"] for r in rows] == ["D1", "D2"]
    for row in rows:
        assert isinstance(row["cells"], int)
        assert isinstance(row["tail_measurable"], bool)


def test_the_candidate_donor_set_must_match_exactly() -> None:
    """A donor missing from the support would silently leave the design."""
    with pytest.raises(AssertionError) as excinfo:
        sup.build_support_rows(counts_by_donor={"D1": 1},
                               candidate_donors=["D1", "D2"])
    assert sup.STOP_DONOR_SET in str(excinfo.value)
    assert "D2" in str(excinfo.value)


def test_a_donor_outside_the_candidate_universe_is_refused() -> None:
    with pytest.raises(AssertionError) as excinfo:
        sup.build_support_rows(counts_by_donor={"D1": 1, "D9": 1},
                               candidate_donors=["D1"])
    assert sup.STOP_DONOR_SET in str(excinfo.value)
    assert "D9" in str(excinfo.value)


@pytest.mark.parametrize("bad", [0, -1, True, 1.5, "2.0", "", None])
def test_a_count_that_is_not_an_exact_positive_integer_stops(bad) -> None:
    with pytest.raises(AssertionError) as excinfo:
        sup.build_support_rows(counts_by_donor={"D1": bad})
    assert sup.STOP_NOT_INTEGER in str(excinfo.value)


# --- the 80-cell floor stays tail-only --------------------------------------

def test_the_tail_flag_is_the_frozen_eighty_cell_rule() -> None:
    rows = sup.build_support_rows(counts_by_donor={"D1": 79, "D2": 80, "D3": 81})
    flags = {r["donor_id"]: r["tail_measurable"] for r in rows}
    assert flags == {"D1": False, "D2": True, "D3": True}


def test_the_tail_floor_scope_cannot_widen() -> None:
    """The frozen role rule says tail measurability must not affect roles."""
    assert sup.assert_tail_floor_stays_in_scope() is True
    original = sup.TAIL_FLOOR_SCOPE
    try:
        sup.TAIL_FLOOR_SCOPE = "ELIGIBILITY_AND_TAIL"
        with pytest.raises(AssertionError) as excinfo:
            sup.assert_tail_floor_stays_in_scope()
        assert sup.STOP_FLOOR_SCOPE in str(excinfo.value)
    finally:
        sup.TAIL_FLOOR_SCOPE = original


def test_changing_the_frozen_floor_is_refused() -> None:
    original = sup.TAIL_MIN_CELLS
    try:
        sup.TAIL_MIN_CELLS = 50
        with pytest.raises(AssertionError) as excinfo:
            sup.assert_tail_floor_stays_in_scope()
        assert sup.STOP_FLOOR_SCOPE in str(excinfo.value)
    finally:
        sup.TAIL_MIN_CELLS = original


def test_a_sub_floor_donor_is_still_a_lawful_support_row() -> None:
    """The floor gates tail measurability, never membership in the population.

    H20.33.037 has 67 immune cells in production. It must remain an eligible,
    lawful donor with tail_measurable False.
    """
    rows = sup.build_support_rows(counts_by_donor={"H20.33.037": 67})
    assert rows[0]["cells"] == 67
    assert rows[0]["tail_measurable"] is False


# --- production geometry ----------------------------------------------------

def test_the_production_geometry_pins_forty_six_donors_and_20804_cells() -> None:
    assert sup.PRODUCTION_DONORS == 46
    assert sup.PRODUCTION_IMMUNE_CELLS == 20_804


def test_a_wrong_donor_count_stops() -> None:
    rows = sup.build_support_rows(counts_by_donor={"D1": 20_804})
    with pytest.raises(AssertionError) as excinfo:
        sup.assert_production_geometry(rows)
    assert sup.STOP_GEOMETRY in str(excinfo.value)


def test_a_wrong_cell_total_stops() -> None:
    rows = sup.build_support_rows(
        counts_by_donor={"D%02d" % i: 1 for i in range(46)})
    with pytest.raises(AssertionError) as excinfo:
        sup.assert_production_geometry(rows)
    assert sup.STOP_GEOMETRY in str(excinfo.value)


def test_the_all_op31_total_is_not_the_support_total() -> None:
    """Guards the population confusion this authority exists to prevent."""
    rows = sup.build_support_rows(
        counts_by_donor={"D%02d" % i: 13_873 for i in range(46)})
    with pytest.raises(AssertionError) as excinfo:
        sup.assert_production_geometry(rows)
    assert sup.STOP_GEOMETRY in str(excinfo.value)


# --- roots ------------------------------------------------------------------

def test_the_root_is_deterministic_and_input_order_independent() -> None:
    a = sup.build_support_rows(counts_by_donor={"D1": 1, "D2": 2})
    b = sup.build_support_rows(counts_by_donor={"D2": 2, "D1": 1})
    assert sup.support_root(a) == sup.support_root(b)


def test_the_root_moves_when_a_count_moves() -> None:
    a = sup.build_support_rows(counts_by_donor={"D1": 1})
    b = sup.build_support_rows(counts_by_donor={"D1": 2})
    assert sup.support_root(a) != sup.support_root(b)


def test_donor_identity_collisions_do_not_share_a_root() -> None:
    a = sup.build_support_rows(counts_by_donor={"a|b": 1})
    b = sup.build_support_rows(counts_by_donor={"a": 1, "b": 1})
    assert sup.support_root(a) != sup.support_root(b)


def test_the_root_binds_the_frozen_floor() -> None:
    """Two authorities computed under different floors must not share a root."""
    rows = sup.build_support_rows(counts_by_donor={"D1": 100})
    before = sup.support_root(rows)
    original = sup.TAIL_MIN_CELLS
    try:
        sup.TAIL_MIN_CELLS = 50
        assert sup.support_root(rows) != before
    finally:
        sup.TAIL_MIN_CELLS = original


def test_the_typed_framing_refuses_a_float() -> None:
    with pytest.raises(AssertionError) as excinfo:
        sup._typed(1.5)
    assert sup.STOP_FIELD_SCHEMA in str(excinfo.value)


# --- package round trip -----------------------------------------------------

def _build(tmp_path, membership_bytes, **overrides):
    kwargs = dict(membership_bytes=membership_bytes,
                  expected_membership_sha256=hashlib.sha256(
                      membership_bytes).hexdigest(),
                  derivation_code_sha256=CODE_SHA,
                  expected_donors=2, expected_cells=5)
    kwargs.update(overrides)
    return sup.build_production_authority(tmp_path / "pkg", **kwargs)


def test_the_production_path_derives_and_packages(tmp_path,
                                                  membership: bytes) -> None:
    summary = _build(tmp_path, membership)
    assert summary["donor_count"] == 2
    assert summary["cell_total"] == 5
    assert summary["real_execution_ready"] is False


def test_the_package_round_trips_with_external_parent_binding(
        tmp_path, membership: bytes) -> None:
    summary = _build(tmp_path, membership)
    loaded = sup.load_authority(
        tmp_path / "pkg",
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_support_root_sha256=summary["support_root_sha256"],
        expected_membership_sha256=hashlib.sha256(membership).hexdigest(),
        expected_derivation_code_sha256=CODE_SHA)
    assert [r["donor_id"] for r in loaded["rows"]] == ["D1", "D2"]


def test_the_loader_refuses_a_wrong_membership_expectation(
        tmp_path, membership: bytes) -> None:
    summary = _build(tmp_path, membership)
    with pytest.raises(AssertionError) as excinfo:
        sup.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_support_root_sha256=summary["support_root_sha256"],
            expected_membership_sha256="f" * 64)
    assert sup.STOP_ROOT_MISMATCH in str(excinfo.value)


def test_a_tampered_registry_is_caught_on_load(tmp_path,
                                               membership: bytes) -> None:
    summary = _build(tmp_path, membership)
    registry = tmp_path / "pkg" / sup.REGISTRY
    registry.write_bytes(registry.read_bytes().replace(b"D1,3,", b"D1,4,"))
    with pytest.raises(AssertionError) as excinfo:
        sup.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_support_root_sha256=summary["support_root_sha256"],
            expected_membership_sha256=hashlib.sha256(membership).hexdigest())
    assert sup.STOP_ROOT_MISMATCH in str(excinfo.value)


def test_writing_into_a_nonempty_directory_is_refused(tmp_path,
                                                      membership: bytes) -> None:
    out = tmp_path / "pkg"
    out.mkdir()
    (out / "stray.txt").write_text("x", encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        _build(tmp_path, membership)
    assert sup.STOP_PACKAGE_MEMBER in str(excinfo.value)


def test_the_metadata_declares_its_role_and_its_limits(tmp_path,
                                                       membership: bytes) -> None:
    _build(tmp_path, membership)
    meta = json.loads((tmp_path / "pkg" / sup.METADATA).read_text(encoding="utf-8"))
    assert "SOLE_LAWFUL_SOURCE" in meta["role_consumption"]
    assert "NOT_AN_ELIGIBILITY_INPUT" in meta["eligibility_role"]
    assert meta["not_the_all_op31_population"] is True
    assert meta["tail_floor_scope"] == sup.TAIL_FLOOR_SCOPE
    assert meta["pathology_values_read"] is False
    assert meta["real_execution_ready"] is False
