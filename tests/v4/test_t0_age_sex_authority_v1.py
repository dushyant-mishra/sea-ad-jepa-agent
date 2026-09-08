"""Adversarial cases for the T0 age/sex demographics authority.

Scope: verifies the integrity of this project's own derived data and provenance
records, in this repository. No third-party system, no network, no credentials
and no security control belonging to any system is involved.

This authority reads the frozen SEA-AD MTG donor table, which also carries the
AT8 magnitude and every other pathology endpoint. So the property that matters is
what it does NOT emit, and the suite checks that a pathology field cannot reach
the emitted schema even when the source row is full of them.

The second property is degeneracy visibility. `nuisance_design` builds
`[1, age_c, age_c^2, sex]` and refuses a set whose sex encoding is not complete
binary, so a single-sex donor set is a loud build-time failure rather than a
silent rank deficiency. The composition is reported so the condition is visible
before the split is computed.
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

import t0_age_sex_authority_v1 as ags  # noqa: E402

CODE_SHA = "b" * 64

# Columns shaped like the real frozen source, pathology endpoints included, so
# the no-leak checks are exercised against a realistic row rather than a
# convenient one.
SOURCE_COLUMNS = [ags.DONOR_ID_FIELD, ags.AGE_FIELD, ags.SEX_FIELD,
                  "Braak", "Thal", "CERAD score",
                  "percent AT8 positive area_Grey matter",
                  "percent 6e10 positive area_Grey matter",
                  "guhcl pTau_Grey matter"]


def _source(donors) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(SOURCE_COLUMNS)
    for donor, age, sex in donors:
        writer.writerow([donor, age, sex, "V", "3", "Frequent",
                         "1.2345", "0.987", "5.5"])
    return buffer.getvalue().encode("utf-8")


@pytest.fixture()
def source() -> bytes:
    return _source([("D1", 90, "Female"), ("D2", 78, "Male"),
                    ("D3", 84, "Female"), ("OTHER", 65, "Male")])


def _read(source_bytes: bytes, **overrides):
    kwargs = dict(source_bytes=source_bytes,
                  expected_source_sha256=hashlib.sha256(source_bytes).hexdigest(),
                  candidate_donors=["D1", "D2", "D3"])
    kwargs.update(overrides)
    return ags.read_demographics(**kwargs)


def _membership(donors) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["source", "matrix_id", "operator_index", "donor_id", "cell_id"])
    for index, donor in enumerate(donors):
        writer.writerow(["SEA_AD", "sea_ad_mtg_rna_final_2026", 31, donor,
                         "%s-c%d" % (donor, index)])
    return buffer.getvalue().encode("utf-8")


# --- source authentication and column scope ---------------------------------

def test_the_two_columns_are_read_for_the_candidate_donors(source: bytes) -> None:
    rows = _read(source)
    assert [r["donor_id"] for r in rows] == ["D1", "D2", "D3"]
    assert rows[0] == {"donor_id": "D1", "age": 90, "sex": "Female"}


def test_a_source_digest_mismatch_stops(source: bytes) -> None:
    with pytest.raises(AssertionError) as excinfo:
        _read(source, expected_source_sha256="f" * 64)
    assert ags.STOP_SOURCE_DIGEST in str(excinfo.value)


def test_donors_outside_the_candidate_universe_are_ignored(source: bytes) -> None:
    """The source covers 84 donors; the candidate universe is 46 of them."""
    rows = _read(source)
    assert "OTHER" not in {r["donor_id"] for r in rows}


def test_a_candidate_absent_from_the_source_stops(source: bytes) -> None:
    with pytest.raises(AssertionError) as excinfo:
        _read(source, candidate_donors=["D1", "D2", "D3", "MISSING"])
    assert ags.STOP_DONOR_SET in str(excinfo.value)
    assert "MISSING" in str(excinfo.value)


def test_a_duplicate_donor_in_the_source_stops() -> None:
    dup = _source([("D1", 90, "Female"), ("D1", 91, "Female")])
    with pytest.raises(AssertionError) as excinfo:
        _read(dup, candidate_donors=["D1"])
    assert ags.STOP_DUPLICATE_DONOR in str(excinfo.value)


def test_a_source_missing_a_permitted_column_stops() -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([ags.DONOR_ID_FIELD, ags.AGE_FIELD])
    writer.writerow(["D1", 90])
    broken = buffer.getvalue().encode("utf-8")
    with pytest.raises(AssertionError) as excinfo:
        _read(broken, candidate_donors=["D1"])
    assert ags.STOP_COLUMNS in str(excinfo.value)


def test_only_three_source_fields_are_permitted() -> None:
    assert ags.PERMITTED_SOURCE_FIELDS == (
        ags.DONOR_ID_FIELD, ags.AGE_FIELD, ags.SEX_FIELD)


# --- value vocabularies -----------------------------------------------------

@pytest.mark.parametrize("bad_age", ["", "90+", "unknown", "-1", "90.5", "nan"])
def test_an_unusable_age_stops(bad_age) -> None:
    """The frozen column is clean int64, so no coercion is offered."""
    payload = _source([("D1", bad_age, "Female")])
    with pytest.raises(AssertionError) as excinfo:
        _read(payload, candidate_donors=["D1"])
    assert ags.STOP_AGE_INVALID in str(excinfo.value)


@pytest.mark.parametrize("bad_sex", ["", "F", "female", "Unknown", "M"])
def test_a_sex_outside_the_frozen_vocabulary_stops(bad_sex) -> None:
    """nuisance_design requires complete binary 0/1, so the vocabulary is fixed."""
    payload = _source([("D1", 90, bad_sex)])
    with pytest.raises(AssertionError) as excinfo:
        _read(payload, candidate_donors=["D1"])
    assert ags.STOP_SEX_INVALID in str(excinfo.value)


def test_the_frozen_sex_vocabulary_is_exactly_two_values() -> None:
    assert ags.SEX_VOCABULARY == ("Female", "Male")


# --- no pathology leaves this module ----------------------------------------

def test_the_emitted_schema_carries_no_pathology_field() -> None:
    assert ags.assert_no_pathology_in_emitted_schema() is True
    assert ags.EMITTED_FIELDS == ("donor_id", "age", "sex")


@pytest.mark.parametrize("leaked", [
    "percent AT8 positive area_Grey matter",
    "Braak",
    "guhcl pTau_Grey matter",
    "percent 6e10 positive area_Grey matter",
])
def test_a_pathology_field_in_the_emitted_schema_is_refused(leaked) -> None:
    """The source is the pathology table, so the guarantee is about the output."""
    with pytest.raises(AssertionError) as excinfo:
        ags.assert_no_pathology_in_emitted_schema(("donor_id", "age", "sex", leaked))
    assert ags.STOP_PATHOLOGY_LEAK in str(excinfo.value)


def test_no_pathology_value_appears_in_the_emitted_rows(source: bytes) -> None:
    rows = _read(source)
    emitted = {key for row in rows for key in row}
    assert emitted == {"donor_id", "age", "sex"}
    # The source row carried 1.2345 as its AT8 magnitude; it must appear nowhere.
    assert not any("1.2345" in str(value) for row in rows for value in row.values())


# --- degeneracy visibility --------------------------------------------------

def test_the_sex_composition_is_reported(source: bytes) -> None:
    rows = _read(source)
    assert ags.sex_composition(rows) == {"Female": 2, "Male": 1}


def test_a_single_sex_set_is_visible_in_the_composition() -> None:
    """It is not refused here; it is made visible before the split is computed.

    The refusal belongs to nuisance_design inside the role authority, where it
    is a loud build-time design failure rather than a biological
    NOT_MEASURABLE. Reporting it here is what lets it be seen first.
    """
    payload = _source([("D1", 90, "Female"), ("D2", 88, "Female")])
    rows = _read(payload, candidate_donors=["D1", "D2"])
    composition = ags.sex_composition(rows)
    assert composition == {"Female": 2, "Male": 0}
    assert min(composition.values()) == 0


# --- ordering and roots -----------------------------------------------------

def test_ordering_is_deterministic_by_utf8_bytes() -> None:
    payload = _source([("Db", 80, "Male"), ("Da", 81, "Female"),
                       ("DC", 82, "Male")])
    rows = _read(payload, candidate_donors=["Db", "Da", "DC"])
    assert [r["donor_id"] for r in rows] == sorted(
        ["Db", "Da", "DC"], key=lambda d: d.encode("utf-8"))


def test_the_root_is_deterministic(source: bytes) -> None:
    assert ags.age_sex_root(_read(source)) == ags.age_sex_root(_read(source))


def test_the_root_moves_when_an_age_moves() -> None:
    a = _read(_source([("D1", 90, "Female")]), candidate_donors=["D1"])
    b = _read(_source([("D1", 91, "Female")]), candidate_donors=["D1"])
    assert ags.age_sex_root(a) != ags.age_sex_root(b)


def test_the_root_moves_when_a_sex_moves() -> None:
    a = _read(_source([("D1", 90, "Female")]), candidate_donors=["D1"])
    b = _read(_source([("D1", 90, "Male")]), candidate_donors=["D1"])
    assert ags.age_sex_root(a) != ags.age_sex_root(b)


def test_donor_identity_collisions_do_not_share_a_root() -> None:
    left = ({"donor_id": "a|b", "age": 90, "sex": "Female"},)
    right = ({"donor_id": "a", "age": 90, "sex": "Female"},
             {"donor_id": "b", "age": 90, "sex": "Female"})
    assert ags.age_sex_root(left) != ags.age_sex_root(right)


def test_an_age_and_its_string_spelling_do_not_share_a_root() -> None:
    assert ags._typed(90) != ags._typed("90")


def test_the_typed_framing_refuses_a_float() -> None:
    with pytest.raises(AssertionError) as excinfo:
        ags._typed(90.0)
    assert ags.STOP_FIELD_SCHEMA in str(excinfo.value)


# --- package round trip -----------------------------------------------------

def _build(tmp_path, source_bytes, **overrides):
    """Build through the authenticated-membership path.

    A bare `candidate_donors` list is refused by the production constructor,
    because it would let this correct source be paired with the wrong subset of
    donors. So the helper supplies the provenance the contract requires.
    """
    donors = overrides.pop("donors", ["D1", "D2", "D3"])
    membership = _membership(donors)
    kwargs = dict(source_bytes=source_bytes,
                  expected_source_sha256=hashlib.sha256(source_bytes).hexdigest(),
                  membership_bytes=membership,
                  expected_membership_sha256=hashlib.sha256(membership).hexdigest(),
                  derivation_code_sha256=CODE_SHA, expected_donors=len(donors))
    kwargs.update(overrides)
    return ags.build_production_authority(tmp_path / "pkg", **kwargs)


def test_the_production_path_authenticates_and_packages(tmp_path,
                                                        source: bytes) -> None:
    summary = _build(tmp_path, source)
    assert summary["donor_count"] == 3
    assert summary["sex_composition"] == {"Female": 2, "Male": 1}
    assert summary["real_execution_ready"] is False


def test_a_wrong_expected_donor_count_stops(tmp_path, source: bytes) -> None:
    with pytest.raises(AssertionError) as excinfo:
        _build(tmp_path, source, expected_donors=46)
    assert ags.STOP_DONOR_SET in str(excinfo.value)


def test_the_package_round_trips_with_external_source_binding(
        tmp_path, source: bytes) -> None:
    summary = _build(tmp_path, source)
    loaded = ags.load_authority(
        tmp_path / "pkg",
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_age_sex_root_sha256=summary["age_sex_root_sha256"],
        expected_source_sha256=hashlib.sha256(source).hexdigest(),
        expected_derivation_code_sha256=CODE_SHA)
    assert [r["donor_id"] for r in loaded["rows"]] == ["D1", "D2", "D3"]


def test_the_loader_refuses_a_wrong_source_expectation(tmp_path,
                                                       source: bytes) -> None:
    summary = _build(tmp_path, source)
    with pytest.raises(AssertionError) as excinfo:
        ags.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_age_sex_root_sha256=summary["age_sex_root_sha256"],
            expected_source_sha256="f" * 64)
    assert ags.STOP_ROOT_MISMATCH in str(excinfo.value)


def test_a_tampered_registry_is_caught_on_load(tmp_path, source: bytes) -> None:
    summary = _build(tmp_path, source)
    registry = tmp_path / "pkg" / ags.REGISTRY
    registry.write_bytes(registry.read_bytes().replace(b"D1,90,", b"D1,91,"))
    with pytest.raises(AssertionError) as excinfo:
        ags.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_age_sex_root_sha256=summary["age_sex_root_sha256"],
            expected_source_sha256=hashlib.sha256(source).hexdigest())
    assert ags.STOP_ROOT_MISMATCH in str(excinfo.value)


def test_an_absent_package_member_stops(tmp_path, source: bytes) -> None:
    summary = _build(tmp_path, source)
    (tmp_path / "pkg" / ags.METADATA).unlink()
    with pytest.raises(AssertionError) as excinfo:
        ags.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_age_sex_root_sha256=summary["age_sex_root_sha256"],
            expected_source_sha256=hashlib.sha256(source).hexdigest())
    assert ags.STOP_PACKAGE_MEMBER in str(excinfo.value)


def test_the_metadata_declares_no_at8_and_records_the_composition(
        tmp_path, source: bytes) -> None:
    _build(tmp_path, source)
    meta = json.loads((tmp_path / "pkg" / ags.METADATA).read_text(encoding="utf-8"))
    assert meta["numeric_at8_value_read"] is False
    assert meta["numeric_at8_value_emitted"] is False
    assert meta["pathology_fields_in_emitted_schema"] is False
    assert meta["source_fields_read"] == list(ags.PERMITTED_SOURCE_FIELDS)
    assert meta["sex_composition"] == {"Female": 2, "Male": 1}
    assert "must not be altered to rescue it" in meta["nuisance_design_note"]
    assert meta["ordering"] == "DONOR_ID_ASCENDING_BY_UTF8_BYTES"
    assert meta["real_execution_ready"] is False


# ---------------------------------------------------------------------------
# The candidate donor set must be authenticated, not caller-supplied.
#
# External review found the gap: `candidate_donors` arrived as a free list that
# nothing tied to the accepted membership or to a frozen candidate-universe
# identity. So the correct 84-donor pathology source could be paired with the
# wrong subset of 46 donors, and the resulting authority would look perfectly
# well-formed. This is the same class as the detached digest labels removed from
# the IMMUNE_FRACTION production path: an input that names a population without
# being bound to it.
# ---------------------------------------------------------------------------

def test_the_candidate_set_can_be_derived_from_authenticated_membership(
        tmp_path, source: bytes) -> None:
    """Bytes in: the donor universe comes from the membership, not the caller."""
    membership = _membership(["D1", "D2", "D3"])
    summary = ags.build_production_authority(
        tmp_path / "pkg",
        source_bytes=source,
        expected_source_sha256=hashlib.sha256(source).hexdigest(),
        membership_bytes=membership,
        expected_membership_sha256=hashlib.sha256(membership).hexdigest(),
        derivation_code_sha256=CODE_SHA, expected_donors=3)
    assert summary["donor_count"] == 3
    assert summary["candidate_donor_set_sha256"] == ags.candidate_donor_set_digest(
        ["D1", "D2", "D3"])


def test_a_wrong_membership_expectation_stops_the_derivation(
        tmp_path, source: bytes) -> None:
    membership = _membership(["D1", "D2", "D3"])
    with pytest.raises(AssertionError) as excinfo:
        ags.build_production_authority(
            tmp_path / "pkg", source_bytes=source,
            expected_source_sha256=hashlib.sha256(source).hexdigest(),
            membership_bytes=membership,
            expected_membership_sha256="f" * 64,
            derivation_code_sha256=CODE_SHA, expected_donors=3)
    assert ags.STOP_MEMBERSHIP_DIGEST in str(excinfo.value)


def test_a_caller_supplied_list_must_match_a_frozen_universe_digest(
        tmp_path, source: bytes) -> None:
    """The alternative path: bind the list to an externally frozen identity."""
    digest = ags.candidate_donor_set_digest(["D1", "D2", "D3"])
    summary = ags.build_production_authority(
        tmp_path / "pkg", source_bytes=source,
        expected_source_sha256=hashlib.sha256(source).hexdigest(),
        candidate_donors=["D1", "D2", "D3"],
        expected_candidate_donor_set_sha256=digest,
        derivation_code_sha256=CODE_SHA, expected_donors=3)
    assert summary["candidate_donor_set_sha256"] == digest


def test_a_caller_supplied_list_that_misses_the_frozen_universe_is_refused(
        tmp_path, source: bytes) -> None:
    """The exact defect: the right source paired with the wrong subset."""
    frozen = ags.candidate_donor_set_digest(["D1", "D2", "D3"])
    with pytest.raises(AssertionError) as excinfo:
        ags.build_production_authority(
            tmp_path / "pkg", source_bytes=source,
            expected_source_sha256=hashlib.sha256(source).hexdigest(),
            candidate_donors=["D1", "D2"],
            expected_candidate_donor_set_sha256=frozen,
            derivation_code_sha256=CODE_SHA, expected_donors=2)
    assert ags.STOP_CANDIDATE_UNIVERSE in str(excinfo.value)


def test_an_unbound_candidate_list_is_refused_outright(tmp_path,
                                                       source: bytes) -> None:
    """Neither authenticated membership nor a frozen digest means no provenance."""
    with pytest.raises(AssertionError) as excinfo:
        ags.build_production_authority(
            tmp_path / "pkg", source_bytes=source,
            expected_source_sha256=hashlib.sha256(source).hexdigest(),
            candidate_donors=["D1", "D2", "D3"],
            derivation_code_sha256=CODE_SHA, expected_donors=3)
    assert ags.STOP_CANDIDATE_UNIVERSE in str(excinfo.value)


def test_the_donor_set_digest_is_injective_over_delimiters() -> None:
    """The collision class that broke an earlier donor-set digest."""
    assert ags.candidate_donor_set_digest(["a|b"]) != \
        ags.candidate_donor_set_digest(["a", "b"])


def test_the_donor_set_digest_is_order_independent() -> None:
    assert ags.candidate_donor_set_digest(["D2", "D1"]) == \
        ags.candidate_donor_set_digest(["D1", "D2"])


def test_a_duplicate_in_the_candidate_set_is_refused() -> None:
    with pytest.raises(AssertionError) as excinfo:
        ags.candidate_donor_set_digest(["D1", "D1"])
    assert ags.STOP_DUPLICATE_DONOR in str(excinfo.value)


def test_the_loader_binds_the_candidate_universe_digest(tmp_path,
                                                        source: bytes) -> None:
    membership = _membership(["D1", "D2", "D3"])
    summary = ags.build_production_authority(
        tmp_path / "pkg", source_bytes=source,
        expected_source_sha256=hashlib.sha256(source).hexdigest(),
        membership_bytes=membership,
        expected_membership_sha256=hashlib.sha256(membership).hexdigest(),
        derivation_code_sha256=CODE_SHA, expected_donors=3)
    with pytest.raises(AssertionError) as excinfo:
        ags.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_age_sex_root_sha256=summary["age_sex_root_sha256"],
            expected_source_sha256=hashlib.sha256(source).hexdigest(),
            expected_candidate_donor_set_sha256="f" * 64)
    assert ags.STOP_CANDIDATE_UNIVERSE in str(excinfo.value)
