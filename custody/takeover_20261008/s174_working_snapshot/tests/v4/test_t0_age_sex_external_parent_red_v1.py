"""External red tests for age/sex candidate-universe binding.

Target producing head:
24b2c9ffc0ab2d63061c20af8829bcb86114b11a

The pathology metadata source is authenticated, but the current production
constructor accepts the 46 candidate donors as a free caller-supplied list.
That permits a lawful source to be paired with the wrong subset of donors.

These tests intentionally fail until the candidate universe is derived from an
authenticated parent (preferred: accepted broad-IMMUNE membership) or checked
against an externally frozen candidate-universe root.
"""
from __future__ import annotations

import csv
import hashlib
import inspect
import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_age_sex_authority_v1 as age_sex  # noqa: E402

CODE_SHA = "c" * 64


def _csv(columns, rows):
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(columns)
    w.writerows(rows)
    return s.getvalue().encode("utf-8")


def _source():
    return _csv(
        ["Donor ID", "Age at Death", "Sex", "percent AT8 positive area_Grey matter"],
        [
            ["D1", 80, "Female", "1.1"],
            ["D2", 81, "Male", "2.2"],
            ["D3", 82, "Female", "3.3"],
        ],
    )


def test_production_constructor_must_bind_candidate_universe_to_authenticated_parent():
    sig = inspect.signature(age_sex.build_production_authority)
    names = set(sig.parameters)
    has_membership_parent = {
        "membership_bytes",
        "expected_membership_sha256",
    }.issubset(names)
    has_candidate_root = (
        "expected_candidate_universe_root_sha256" in names
        or "expected_candidate_donor_set_sha256" in names
    )
    assert has_membership_parent or has_candidate_root, (
        "candidate_donors is currently a detached caller input; production must "
        "derive it from authenticated membership or verify it against an "
        "externally frozen candidate-universe identity"
    )


def test_arbitrary_subset_of_authenticated_source_must_not_be_accepted(tmp_path):
    raw = _source()

    # D1/D2 are a valid two-donor subset of the authenticated source bytes, but
    # no accepted T0 candidate authority says this is the candidate universe.
    # Current code accepts it when expected_donors is overridden to 2.
    with pytest.raises(AssertionError):
        age_sex.build_production_authority(
            tmp_path / "pkg",
            source_bytes=raw,
            expected_source_sha256=hashlib.sha256(raw).hexdigest(),
            candidate_donors=["D1", "D2"],
            derivation_code_sha256=CODE_SHA,
            expected_donors=2,
        )


def test_loader_must_require_external_candidate_parent_identity():
    sig = inspect.signature(age_sex.load_authority)
    names = set(sig.parameters)
    assert (
        "expected_membership_sha256" in names
        or "expected_candidate_universe_root_sha256" in names
        or "expected_candidate_donor_set_sha256" in names
    ), "loader binds source identity but not the parent that defines which donors belong"


def test_pathology_magnitude_remains_out_of_emitted_schema():
    assert age_sex.assert_no_pathology_in_emitted_schema() is True
    assert tuple(age_sex.EMITTED_FIELDS) == ("donor_id", "age", "sex")
