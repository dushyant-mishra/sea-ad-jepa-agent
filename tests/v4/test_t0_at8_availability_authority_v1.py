"""Attacks on the T0 AT8 availability-only authority.

This lane is authorized to touch the frozen SEA-AD donor pathology source for
exactly one purpose: deciding whether the frozen field
`percent AT8 positive area_Grey matter` is present and non-missing for a donor.
It may not parse, retain, emit, log, rank, summarize, compare or model any
numeric AT8 value.

"Never parses the value" is a claim about behaviour, so the load-bearing test
here is metamorphic: replacing every numeric AT8 value with arbitrary different
numbers, while holding presence fixed, must produce a byte-identical package
root. The paired discriminating test blanks one value and requires the root to
change, so the predicate cannot pass by ignoring its input entirely.

Written before the implementation.
"""

from __future__ import annotations

import ast
import csv
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_at8_availability_authority_v1 as av  # noqa: E402

FIELD = "percent AT8 positive area_Grey matter"
ID = "Donor ID"


def _write_source(path: Path, rows: list[dict[str, str]]) -> str:
    """Write a synthetic pathology-shaped CSV and return its SHA-256."""
    columns = [ID, "Age at Death", "Sex", FIELD, "percent GFAP positive area_Grey matter"]
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
    return av.sha256_file(path)


def _rows(values: list[str]) -> list[dict[str, str]]:
    return [
        {ID: "D%02d" % index, "Age at Death": "80", "Sex": "Male", FIELD: value}
        for index, value in enumerate(values)
    ]


@pytest.fixture()
def source(tmp_path: Path):
    values = ["1.5", "", "12.25", "NA", "0", "  ", "7.125", "n/a"]
    path = tmp_path / "pathology.csv"
    digest = _write_source(path, _rows(values))
    return path, digest, values


# --------------------------------------------------------------------------
# The source must be authenticated before the field is ever consulted.
# --------------------------------------------------------------------------
def test_a_wrong_source_hash_stops_before_reading_the_field(source, tmp_path: Path) -> None:
    path, digest, _ = source
    with pytest.raises(AssertionError, match="PATHOLOGY_SOURCE_DIGEST"):
        av.build_availability_authority(
            outdir=tmp_path / "out",
            source_path=path,
            expected_source_sha256="0" * 64,
            membership_donor_ids=["D00"],
        )
    assert not (tmp_path / "out").exists(), "nothing may be emitted after a source STOP"


def test_the_frozen_field_must_exist_in_the_header(tmp_path: Path) -> None:
    path = tmp_path / "no_field.csv"
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write("Donor ID,Sex\nD00,Male\n")
    with pytest.raises(AssertionError, match="AT8_FIELD_ABSENT"):
        av.build_availability_authority(
            outdir=tmp_path / "out",
            source_path=path,
            expected_source_sha256=av.sha256_file(path),
            membership_donor_ids=["D00"],
        )


# --------------------------------------------------------------------------
# Availability must be derived, not assumed.
# --------------------------------------------------------------------------
def test_availability_is_derived_per_donor_including_missing_forms(source, tmp_path: Path) -> None:
    path, digest, values = source
    built = av.build_availability_authority(
        outdir=tmp_path / "out",
        source_path=path,
        expected_source_sha256=digest,
        membership_donor_ids=["D00", "D02"],
    )
    registry = {row["donor_id"]: row["AT8_available"] for row in built["registry"]}
    assert registry == {
        "D00": "True",   # "1.5"
        "D01": "False",  # empty
        "D02": "True",   # "12.25"
        "D03": "False",  # "NA"
        "D04": "True",   # "0" is a measured value, not missing
        "D05": "False",  # whitespace only
        "D06": "True",   # "7.125"
        "D07": "False",  # "n/a"
    }
    assert built["metadata"]["available_donor_count"] == 4
    assert built["metadata"]["total_donor_count"] == 8
    # A zero measurement must count as available; that is a semantic trap.
    assert registry["D04"] == "True"


def test_the_count_is_not_hardcoded_to_the_expected_production_value(
    source, tmp_path: Path
) -> None:
    """A fixture with known missingness must not report full availability."""
    path, digest, _ = source
    built = av.build_availability_authority(
        outdir=tmp_path / "out",
        source_path=path,
        expected_source_sha256=digest,
        membership_donor_ids=["D00"],
    )
    assert built["metadata"]["available_donor_count"] != built["metadata"]["total_donor_count"]


# --------------------------------------------------------------------------
# The load-bearing value-blindness proof.
# --------------------------------------------------------------------------
def test_perturbing_numeric_values_cannot_change_the_package(tmp_path: Path) -> None:
    """Metamorphic: presence fixed, magnitudes arbitrary, root byte-identical."""
    present = ["1.5", "", "12.25", "NA", "0", "7.125"]
    altered = ["999999.75", "", "-0.001", "NA", "48250", "3.14159"]
    assert [bool(v.strip()) for v in present] == [bool(v.strip()) for v in altered]

    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"
    d1 = _write_source(first, _rows(present))
    d2 = _write_source(second, _rows(altered))
    assert d1 != d2, "the two sources must genuinely differ in bytes"

    built_a = av.build_availability_authority(
        outdir=tmp_path / "out_a", source_path=first, expected_source_sha256=d1,
        membership_donor_ids=["D00"])
    built_b = av.build_availability_authority(
        outdir=tmp_path / "out_b", source_path=second, expected_source_sha256=d2,
        membership_donor_ids=["D00"])

    assert built_a["registry"] == built_b["registry"]
    assert (tmp_path / "out_a" / av.REGISTRY).read_bytes() == (
        tmp_path / "out_b" / av.REGISTRY
    ).read_bytes()
    assert built_a["availability_root_sha256"] == built_b["availability_root_sha256"], (
        "the availability root must not depend on any numeric AT8 value"
    )


def test_changing_presence_does_change_the_package(tmp_path: Path) -> None:
    """The paired discriminator: the predicate must actually read its input."""
    present = ["1.5", "12.25", "0"]
    blanked = ["1.5", "", "0"]
    first, second = tmp_path / "a.csv", tmp_path / "b.csv"
    d1 = _write_source(first, _rows(present))
    d2 = _write_source(second, _rows(blanked))
    built_a = av.build_availability_authority(
        outdir=tmp_path / "out_a", source_path=first, expected_source_sha256=d1,
        membership_donor_ids=["D00"])
    built_b = av.build_availability_authority(
        outdir=tmp_path / "out_b", source_path=second, expected_source_sha256=d2,
        membership_donor_ids=["D00"])
    assert built_a["availability_root_sha256"] != built_b["availability_root_sha256"]
    assert built_a["metadata"]["available_donor_count"] == 3
    assert built_b["metadata"]["available_donor_count"] == 2


# --------------------------------------------------------------------------
# No outcome value may survive into the package, in any form.
# --------------------------------------------------------------------------
def test_no_emitted_byte_contains_an_outcome_value(tmp_path: Path) -> None:
    distinctive = ["48250.171875", "93317.5", "70241.25"]
    path = tmp_path / "pathology.csv"
    digest = _write_source(path, _rows(distinctive))
    outdir = tmp_path / "out"
    av.build_availability_authority(
        outdir=outdir, source_path=path, expected_source_sha256=digest,
        membership_donor_ids=["D00"])

    emitted = b"".join(p.read_bytes() for p in sorted(outdir.rglob("*")) if p.is_file())
    for value in distinctive:
        assert value.encode() not in emitted, value
        assert value.split(".")[0].encode() not in emitted, value
    # The registry carries exactly the two authorized columns.
    header = (outdir / av.REGISTRY).read_text(encoding="utf-8").splitlines()[0]
    assert header == "donor_id,AT8_available"


def test_the_module_never_converts_the_field_numerically() -> None:
    """Structural proof to complement the behavioural one.

    A numeric conversion anywhere in this module would be a latent leak even if
    today's code path does not emit the result.
    """
    tree = ast.parse(Path(av.__file__).read_text(encoding="utf-8"))
    forbidden = {"float", "int", "to_numeric", "read_csv", "astype", "mean", "sum"}
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name in forbidden:
                found.add(name)
    assert not found, f"numeric/bulk-parse calls present: {sorted(found)}"
    assert "pandas" not in Path(av.__file__).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Membership resolution and package integrity.
# --------------------------------------------------------------------------
def test_every_membership_donor_must_resolve(source, tmp_path: Path) -> None:
    path, digest, _ = source
    with pytest.raises(AssertionError, match="MEMBERSHIP_DONOR_UNRESOLVED"):
        av.build_availability_authority(
            outdir=tmp_path / "out", source_path=path, expected_source_sha256=digest,
            membership_donor_ids=["D00", "NOT_A_DONOR"])


def test_a_membership_donor_without_at8_is_reported_not_silently_dropped(
    source, tmp_path: Path
) -> None:
    path, digest, _ = source
    built = av.build_availability_authority(
        outdir=tmp_path / "out", source_path=path, expected_source_sha256=digest,
        membership_donor_ids=["D00", "D01"])
    assert built["metadata"]["membership_donor_count"] == 2
    assert built["metadata"]["membership_donors_available"] == 1
    assert built["metadata"]["membership_fully_available"] is False


def test_duplicate_donor_identity_stops(tmp_path: Path) -> None:
    rows = _rows(["1.0", "2.0"])
    rows[1][ID] = rows[0][ID]
    path = tmp_path / "dupe.csv"
    digest = _write_source(path, rows)
    with pytest.raises(AssertionError, match="DONOR_IDENTITY_NOT_UNIQUE"):
        av.build_availability_authority(
            outdir=tmp_path / "out", source_path=path, expected_source_sha256=digest,
            membership_donor_ids=["D00"])


def test_the_package_is_tamper_evident(source, tmp_path: Path) -> None:
    path, digest, _ = source
    outdir = tmp_path / "out"
    built = av.build_availability_authority(
        outdir=outdir, source_path=path, expected_source_sha256=digest,
        membership_donor_ids=["D00"])
    assert av.load_availability_authority(outdir)["availability_root_sha256"] == (
        built["availability_root_sha256"]
    )
    registry = outdir / av.REGISTRY
    registry.write_bytes(registry.read_bytes().replace(b"False", b"True", 1))
    with pytest.raises(AssertionError):
        av.load_availability_authority(outdir)


def test_the_authority_does_not_claim_execution_readiness(source, tmp_path: Path) -> None:
    path, digest, _ = source
    built = av.build_availability_authority(
        outdir=tmp_path / "out", source_path=path, expected_source_sha256=digest,
        membership_donor_ids=["D00"])
    meta = built["metadata"]
    assert meta["real_execution_ready"] is False
    assert meta["outcome_values_read"] is False
    assert meta["namespace"] == av.NAMESPACE
    assert meta["at8_field"] == FIELD
    assert meta["source_sha256"] == digest


def test_an_existing_nonempty_output_directory_stops(source, tmp_path: Path) -> None:
    path, digest, _ = source
    outdir = tmp_path / "out"
    outdir.mkdir()
    (outdir / "stray.txt").write_text("x", encoding="utf-8")
    with pytest.raises(AssertionError, match="OUTPUT_NOT_EMPTY"):
        av.build_availability_authority(
            outdir=outdir, source_path=path, expected_source_sha256=digest,
            membership_donor_ids=["D00"])
