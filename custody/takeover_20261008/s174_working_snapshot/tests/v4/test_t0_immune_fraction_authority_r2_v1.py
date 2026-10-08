"""R2 cases for IMMUNE_FRACTION production provenance and external verification.

Scope: verifies the integrity of this project's own derived data and provenance
records, in this repository. No third-party system, no network, no credentials
and no security control belonging to any system is involved. The only checks
exercised are our own digest comparisons and arithmetic invariants. See
docs/agent/T0_LANE_SECURITY_SCOPE.md.

Two defect classes are reproduced here.

The production entrypoint accepted assembled results and detached labels. It took
`rows` that a caller had already built, plus `membership_sha256`,
`complete_manifest_sha256` and `consumed_meta_sha256` as free-standing strings
that nothing tied to the bytes those digests claimed to describe. So a caller
could hand it correct-looking provenance for a population it never derived. The
production path must instead derive the rows itself from authenticated parents,
and the row-based builder must survive only as a test primitive.

The loader verified only its own two roots. It never received the parent
identities, so `stored == recomputed` could hold while both differed from what an
external reviewer expected. Every root the authority claims must satisfy
`stored == recomputed == externally expected`.
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

import t0_immune_fraction_authority_v1 as ifa  # noqa: E402
import t0_immune_fraction_formula_spec_v1 as spec  # noqa: E402

MATRIX = ifa.MTG_MATRIX_ID
OPERATOR = ifa.OP31_OPERATOR_INDEX
CODE_SHA = "c" * 64


def _csv(columns, rows) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def _meta(donors) -> bytes:
    return _csv(["selection_row", "canonical_cell_id", "donor_id", "expression_row",
                 "primary_row_weight", "source_library"],
                [[i, "C%d" % i, d, 100 + i, "8.06e-08", 9000 + i]
                 for i, d in enumerate(donors)])


class World:
    """46 donors, so the production geometry assertions are exercised for real."""

    def __init__(self) -> None:
        self.donors = ["D%02d" % i for i in range(46)]
        # 20,804 immune cells: 452 each for 44 donors, then 466 and 450.
        self.immune_per_donor = {d: 452 for d in self.donors}
        self.immune_per_donor["D44"] = 466
        self.immune_per_donor["D45"] = 450
        assert sum(self.immune_per_donor.values()) == 20_804
        # 638,150 op31 cells: 13,873 each for 45 donors, remainder to the last.
        self.op31_per_donor = {d: 13_873 for d in self.donors}
        self.op31_per_donor["D45"] = 638_150 - 13_873 * 45
        assert sum(self.op31_per_donor.values()) == 638_150

        cells = []
        for donor in self.donors:
            for index in range(self.immune_per_donor[donor]):
                cells.append(("%s-c%d" % (donor, index), donor))
        self.membership = _csv(
            ["source", "matrix_id", "operator_index", "donor_id", "cell_id"],
            [["SEA_AD", MATRIX, OPERATOR, donor, cell] for cell, donor in cells])

        # One op31 block per donor keeps the fixture small while preserving the
        # counts the production assertions check.
        self.op31 = {}
        for donor in self.donors:
            self.op31["op31/block-%05d" % self.donors.index(donor)] = _meta(
                [donor] * self.op31_per_donor[donor])
        self.foreign = {"op00/block-00000": ("HVS", 0, "HVS::19cd530b"),
                        "op32/block-00000": ("SEA_AD", 32, "sea_ad_pfc_rna_final_2026")}

    def _row(self, key, source, operator, matrix, meta_blob):
        return [key, source, operator, matrix,
                len(list(csv.DictReader(io.StringIO(meta_blob.decode())))), 999,
                "%s.counts.npz" % key, hashlib.sha256(b"counts").hexdigest(),
                "%s.meta.csv" % key, hashlib.sha256(meta_blob).hexdigest()]

    def complete_manifest(self) -> bytes:
        foreign_meta = _meta(["DF"])
        rows = [self._row("op00/block-00000", "HVS", 0, "HVS::19cd530b", foreign_meta)]
        for key in sorted(self.op31):
            rows.append(self._row(key, "SEA_AD", OPERATOR, MATRIX, self.op31[key]))
        rows.append(self._row("op32/block-00000", "SEA_AD", 32,
                              "sea_ad_pfc_rna_final_2026", foreign_meta))
        return _csv(["block_key", "source", "operator_index", "matrix_id", "rows",
                     "nnz", "counts_path", "counts_sha256", "meta_path",
                     "meta_sha256"], rows)

    def meta_by_path(self) -> dict[str, bytes]:
        return {"%s.meta.csv" % k: v for k, v in self.op31.items()}

    def geometry(self) -> dict[str, int]:
        return {"expected_total_blocks": len(self.op31) + 2,
                "expected_operators": 3,
                "expected_op31_blocks": len(self.op31)}


class SmallWorld(World):
    """Same shape, three donors. Keeps the suite fast.

    Production totals are asserted against the full-geometry world in
    test_the_production_constructor_derives_rows_from_authenticated_parents; every
    other case here is about provenance binding, not about the frozen counts, so
    it does not need 638,150 metadata rows to exercise.
    """

    def __init__(self) -> None:
        self.donors = ["D%02d" % i for i in range(3)]
        self.immune_per_donor = {"D00": 2, "D01": 3, "D02": 1}
        self.op31_per_donor = {"D00": 5, "D01": 6, "D02": 4}
        cells = []
        for donor in self.donors:
            for index in range(self.immune_per_donor[donor]):
                cells.append(("%s-c%d" % (donor, index), donor))
        self.membership = _csv(
            ["source", "matrix_id", "operator_index", "donor_id", "cell_id"],
            [["SEA_AD", MATRIX, OPERATOR, donor, cell] for cell, donor in cells])
        self.op31 = {}
        for donor in self.donors:
            self.op31["op31/block-%05d" % self.donors.index(donor)] = _meta(
                [donor] * self.op31_per_donor[donor])
        self.foreign = {"op00/block-00000": ("HVS", 0, "HVS::19cd530b"),
                        "op32/block-00000": ("SEA_AD", 32,
                                              "sea_ad_pfc_rna_final_2026")}

    def totals(self) -> dict[str, int]:
        return {"expected_donors": 3,
                "expected_immune_cells": sum(self.immune_per_donor.values()),
                "expected_op31_cells": sum(self.op31_per_donor.values())}


@pytest.fixture(scope="module")
def world() -> SmallWorld:
    return SmallWorld()


@pytest.fixture(scope="module")
def production_world() -> World:
    return World()


def _production(world: World, outdir, **overrides):
    kwargs = dict(
        membership_bytes=world.membership,
        expected_membership_sha256=hashlib.sha256(world.membership).hexdigest(),
        complete_manifest_bytes=world.complete_manifest(),
        expected_complete_manifest_sha256=hashlib.sha256(
            world.complete_manifest()).hexdigest(),
        meta_bytes_by_path=world.meta_by_path(),
        expected_formula_spec_root_sha256=spec.formula_spec_root(),
        derivation_code_sha256=CODE_SHA,
        **world.geometry())
    if hasattr(world, "totals"):
        kwargs.update(world.totals())
    kwargs.update(overrides)
    return ifa.build_production_authority(outdir, **kwargs)


# --- item 1: the frozen formula specification -------------------------------

def test_the_formula_specification_is_lawful() -> None:
    assert spec.assert_specification_lawful() is True


def test_the_specification_never_claims_recovered_v18_semantics() -> None:
    """It resolves an undefined required input; it does not recover one."""
    assert spec.RECOVERED_FROM_FROZEN_EXECUTABLE_V18 is False
    assert spec.SPECIFICATION_STATUS.startswith("EXPLICIT_SUCCESSOR_SPECIFICATION")
    assert "never be described as recovered" in spec.PROVENANCE_NOTE


def test_claiming_recovered_semantics_is_refused() -> None:
    original = spec.RECOVERED_FROM_FROZEN_EXECUTABLE_V18
    try:
        spec.RECOVERED_FROM_FROZEN_EXECUTABLE_V18 = True
        with pytest.raises(AssertionError) as excinfo:
            spec.assert_specification_lawful()
        assert spec.STOP_SPEC_PROVENANCE in str(excinfo.value)
    finally:
        spec.RECOVERED_FROM_FROZEN_EXECUTABLE_V18 = original


def test_the_specification_binds_the_reader_fit_substrate_fact() -> None:
    assert spec.PHASE2_SUBSTRATE_IS_READER_FIT is True
    assert tuple(spec.SUBSTRATE_EXCLUDES) == ("reader_validation", "reader_oracle")
    assert (spec.OP31_READER_FIT_CELLS + spec.OP31_READER_VALIDATION_CELLS
            + spec.OP31_READER_ORACLE_CELLS) == spec.OP31_ALL_PARTITION_CELLS


def test_breaking_the_partition_arithmetic_is_refused() -> None:
    """If the counts stop closing, the substrate claim is unsupported."""
    original = spec.OP31_READER_ORACLE_CELLS
    try:
        spec.OP31_READER_ORACLE_CELLS = original + 1
        with pytest.raises(AssertionError) as excinfo:
            spec.assert_specification_lawful()
        assert spec.STOP_SPEC_FIELD in str(excinfo.value)
    finally:
        spec.OP31_READER_ORACLE_CELLS = original


def test_the_specification_root_is_deterministic_and_binds_externally() -> None:
    root = spec.formula_spec_root()
    assert len(root) == 64 and root == spec.formula_spec_root()
    assert spec.assert_spec_root(root) is True
    with pytest.raises(AssertionError) as excinfo:
        spec.assert_spec_root("f" * 64)
    assert spec.STOP_SPEC_ROOT in str(excinfo.value)


def test_the_specification_root_moves_when_the_formula_moves() -> None:
    before = spec.formula_spec_root()
    original = spec.FORMULA
    try:
        spec.FORMULA = original + " (perturbed)"
        assert spec.formula_spec_root() != before
    finally:
        spec.FORMULA = original


def test_the_specification_declares_the_covariate_out_of_eligibility_scope() -> None:
    assert "MUST_NOT_FEED_TECHNICAL_COMPLETE" in spec.CONSUMPTION_SCOPE


# --- item 2: the production entrypoint derives from authenticated parents ----

def test_the_production_constructor_derives_rows_from_authenticated_parents(
        tmp_path, production_world: World) -> None:
    """One shot: bytes in, authenticated, selected, derived, asserted, packaged.

    This is the case that exercises the frozen production geometry with the real
    46 / 20,804 / 638,150 numbers, so it pays for the full-size fixture.
    """
    summary = _production(production_world, tmp_path / "pkg")
    assert summary["donor_count"] == 46
    assert summary["immune_cell_total"] == 20_804
    assert summary["op31_cell_total"] == 638_150
    assert summary["selected_op31_blocks"] == len(production_world.op31)
    assert summary["real_execution_ready"] is False
    assert len(summary["immune_fraction_root_sha256"]) == 64
    assert len(summary["package_root_sha256"]) == 64
    assert summary["formula_spec_root_sha256"] == spec.formula_spec_root()


def test_the_production_constructor_refuses_preassembled_rows(
        tmp_path, world: World) -> None:
    """Accepting a caller's rows means the authority did not derive them."""
    with pytest.raises(TypeError):
        ifa.build_production_authority(
            tmp_path / "pkg",
            rows=[{"donor_id": "D00", "immune_n_donor": 1,
                   "total_op31_n_donor": 2}],
            membership_bytes=world.membership,
            expected_membership_sha256=hashlib.sha256(world.membership).hexdigest(),
            complete_manifest_bytes=world.complete_manifest(),
            expected_complete_manifest_sha256=hashlib.sha256(
                world.complete_manifest()).hexdigest(),
            meta_bytes_by_path=world.meta_by_path(),
            expected_formula_spec_root_sha256=spec.formula_spec_root(),
            derivation_code_sha256=CODE_SHA,
            **world.geometry())


def test_the_production_constructor_refuses_a_detached_metadata_digest_label(
        tmp_path, world: World) -> None:
    """Digests must be computed from the supplied bytes, not asserted alongside."""
    with pytest.raises(TypeError):
        ifa.build_production_authority(
            tmp_path / "pkg",
            consumed_meta_sha256={"op31/block-00000.meta.csv": "d" * 64},
            membership_bytes=world.membership,
            expected_membership_sha256=hashlib.sha256(world.membership).hexdigest(),
            complete_manifest_bytes=world.complete_manifest(),
            expected_complete_manifest_sha256=hashlib.sha256(
                world.complete_manifest()).hexdigest(),
            meta_bytes_by_path=world.meta_by_path(),
            expected_formula_spec_root_sha256=spec.formula_spec_root(),
            derivation_code_sha256=CODE_SHA,
            **world.geometry())


def test_a_wrong_membership_expectation_stops_the_production_path(
        tmp_path, world: World) -> None:
    with pytest.raises(AssertionError) as excinfo:
        _production(world, tmp_path / "pkg", expected_membership_sha256="f" * 64)
    assert ifa.STOP_MEMBERSHIP_DIGEST in str(excinfo.value)


def test_a_wrong_manifest_expectation_stops_the_production_path(
        tmp_path, world: World) -> None:
    with pytest.raises(AssertionError) as excinfo:
        _production(world, tmp_path / "pkg",
                    expected_complete_manifest_sha256="f" * 64)
    assert ifa.STOP_MANIFEST_DIGEST in str(excinfo.value)


def test_a_wrong_formula_spec_expectation_stops_the_production_path(
        tmp_path, world: World) -> None:
    """The authority must bind the specification it was built against."""
    with pytest.raises(AssertionError) as excinfo:
        _production(world, tmp_path / "pkg",
                    expected_formula_spec_root_sha256="f" * 64)
    assert spec.STOP_SPEC_ROOT in str(excinfo.value)


def test_the_production_path_asserts_the_frozen_geometry(
        tmp_path, world: World) -> None:
    """A short population must not be packaged as production."""
    short = dict(world.meta_by_path())
    short.pop(sorted(short)[-1])
    with pytest.raises(AssertionError):
        _production(world, tmp_path / "pkg", meta_bytes_by_path=short)


def test_the_row_builder_remains_available_only_as_a_test_primitive() -> None:
    """It may stay, but it must be marked private so production cannot use it."""
    assert hasattr(ifa, "_build_immune_fraction_rows")
    assert ifa._build_immune_fraction_rows.__name__.startswith("_")


# --- item 3: external verification of every claimed root --------------------

def test_the_loader_binds_every_parent_identity(tmp_path, world: World) -> None:
    out = tmp_path / "pkg"
    summary = _production(world, out)
    loaded = ifa.load_authority(
        out,
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_immune_fraction_root_sha256=summary["immune_fraction_root_sha256"],
        expected_membership_sha256=hashlib.sha256(world.membership).hexdigest(),
        expected_complete_manifest_sha256=hashlib.sha256(
            world.complete_manifest()).hexdigest(),
        expected_formula_spec_root_sha256=spec.formula_spec_root(),
        expected_derivation_code_sha256=CODE_SHA,
    )
    assert len(loaded["rows"]) == len(world.donors)
    assert loaded["parent_contract_root_sha256"] == summary[
        "parent_contract_root_sha256"]


def test_the_loader_accepts_one_parent_contract_root(tmp_path, world: World) -> None:
    """A single externally accepted root may stand in for the individual ones."""
    out = tmp_path / "pkg"
    summary = _production(world, out)
    loaded = ifa.load_authority(
        out,
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_immune_fraction_root_sha256=summary["immune_fraction_root_sha256"],
        expected_parent_contract_root_sha256=summary["parent_contract_root_sha256"],
    )
    assert len(loaded["rows"]) == len(world.donors)


@pytest.mark.parametrize("field", [
    "expected_membership_sha256",
    "expected_complete_manifest_sha256",
    "expected_formula_spec_root_sha256",
    "expected_derivation_code_sha256",
])
def test_the_loader_refuses_a_wrong_parent_identity(tmp_path, world: World,
                                                    field) -> None:
    """stored == recomputed is not enough; it must equal the external expectation."""
    out = tmp_path / "pkg"
    summary = _production(world, out)
    kwargs = dict(
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_immune_fraction_root_sha256=summary["immune_fraction_root_sha256"],
        expected_membership_sha256=hashlib.sha256(world.membership).hexdigest(),
        expected_complete_manifest_sha256=hashlib.sha256(
            world.complete_manifest()).hexdigest(),
        expected_formula_spec_root_sha256=spec.formula_spec_root(),
        expected_derivation_code_sha256=CODE_SHA,
    )
    kwargs[field] = "f" * 64
    with pytest.raises(AssertionError) as excinfo:
        ifa.load_authority(out, **kwargs)
    assert ifa.STOP_PARENT_IDENTITY in str(excinfo.value)


def test_the_loader_refuses_a_wrong_parent_contract_root(tmp_path,
                                                         world: World) -> None:
    out = tmp_path / "pkg"
    summary = _production(world, out)
    with pytest.raises(AssertionError) as excinfo:
        ifa.load_authority(
            out,
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_immune_fraction_root_sha256=summary[
                "immune_fraction_root_sha256"],
            expected_parent_contract_root_sha256="f" * 64,
        )
    assert ifa.STOP_PARENT_IDENTITY in str(excinfo.value)


def test_the_loader_requires_some_external_parent_expectation(tmp_path,
                                                              world: World) -> None:
    """Verifying only its own roots would leave the parents unbound."""
    out = tmp_path / "pkg"
    summary = _production(world, out)
    with pytest.raises(AssertionError) as excinfo:
        ifa.load_authority(
            out,
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_immune_fraction_root_sha256=summary[
                "immune_fraction_root_sha256"],
        )
    assert ifa.STOP_PARENT_IDENTITY in str(excinfo.value)


def test_a_stored_parent_identity_that_disagrees_with_the_recomputed_root_stops(
        tmp_path, world: World) -> None:
    """stored == recomputed must hold too, not just recomputed == expected."""
    out = tmp_path / "pkg"
    summary = _production(world, out)
    meta_path = out / ifa.METADATA
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["membership_sha256"] = "e" * 64
    with io.open(meta_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(meta, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # The package root moves because a member changed, which is itself caught.
    with pytest.raises(AssertionError):
        ifa.load_authority(
            out,
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_immune_fraction_root_sha256=summary[
                "immune_fraction_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"],
        )


def test_the_parent_contract_root_moves_with_any_parent_identity(
        tmp_path, world: World) -> None:
    a = _production(world, tmp_path / "a")
    b = _production(world, tmp_path / "b", derivation_code_sha256="d" * 64)
    assert a["parent_contract_root_sha256"] != b["parent_contract_root_sha256"]
    # The derived integers are unchanged, so the value root must not move.
    assert a["immune_fraction_root_sha256"] == b["immune_fraction_root_sha256"]
