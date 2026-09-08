"""Adversarial cases for the T0 IMMUNE_FRACTION authority.

Scope: this module verifies the integrity of this project's own derived data and
its provenance records, in this repository. No third-party system, no network, no
credentials and no security control belonging to any system is involved. The only
checks being probed are our own SHA-256 comparisons and our own arithmetic
invariants. See docs/agent/T0_LANE_SECURITY_SCOPE.md.

Two properties carry most of the weight here.

The integers are the authority and the fraction is derived. So the cases attack
the integers -- substitution, sign, ordering, cardinality, type -- rather than a
float, and they check that a float is never what gets bound.

The complete Phase2 manifest must be consumable. It spans 42 operators and its
first row is operator 0, so the authority authenticates it whole and then selects
operator 31 from inside those authenticated bytes. Authenticating a
pre-narrowed file instead would mean the bytes carrying the frozen digest are not
the bytes used, so that substitution is refused.
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

MATRIX = ifa.MTG_MATRIX_ID
OPERATOR = ifa.OP31_OPERATOR_INDEX
CODE_SHA = "a" * 64


def _csv(columns, rows) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def _membership(cells, *, operator=OPERATOR, matrix=MATRIX) -> bytes:
    return _csv(["source", "matrix_id", "operator_index", "donor_id", "cell_id"],
                [["SEA_AD", matrix, operator, donor, cell] for cell, donor in cells])


def _meta(donors) -> bytes:
    return _csv(["selection_row", "canonical_cell_id", "donor_id", "expression_row",
                 "primary_row_weight", "source_library"],
                [[i, "C%d" % i, d, 100 + i, "8.06e-08", 9000 + i]
                 for i, d in enumerate(donors)])


class World:
    """Two donors in operator 31, inside a manifest spanning four operators."""

    def __init__(self) -> None:
        self.membership = _membership([("C1", "D1"), ("C2", "D1"), ("C3", "D2")])
        self.op31 = {
            "op31/block-00000": _meta(["D1", "D1", "D2", "D2"]),
            "op31/block-00001": _meta(["D1", "D2"]),
        }
        self.foreign = {
            "op00/block-00000": ("HVS", 0, "HVS::19cd530b"),
            "op32/block-00000": ("SEA_AD", 32, "sea_ad_pfc_rna_final_2026"),
        }

    def _row(self, key, source, operator, matrix, meta_blob):
        return [key, source, operator, matrix,
                len(list(csv.DictReader(io.StringIO(meta_blob.decode())))), 999,
                "%s.counts.npz" % key, hashlib.sha256(b"counts").hexdigest(),
                "%s.meta.csv" % key, hashlib.sha256(meta_blob).hexdigest()]

    def complete_manifest(self) -> bytes:
        foreign_meta = _meta(["DF"])
        rows = []
        for key, (source, operator, matrix) in sorted(self.foreign.items()):
            if operator < OPERATOR:
                rows.append(self._row(key, source, operator, matrix, foreign_meta))
        for key in sorted(self.op31):
            rows.append(self._row(key, "SEA_AD", OPERATOR, MATRIX, self.op31[key]))
        for key, (source, operator, matrix) in sorted(self.foreign.items()):
            if operator > OPERATOR:
                rows.append(self._row(key, source, operator, matrix, foreign_meta))
        return _csv(["block_key", "source", "operator_index", "matrix_id", "rows",
                     "nnz", "counts_path", "counts_sha256", "meta_path",
                     "meta_sha256"], rows)

    def op31_only_manifest(self) -> bytes:
        rows = [self._row(k, "SEA_AD", OPERATOR, MATRIX, self.op31[k])
                for k in sorted(self.op31)]
        return _csv(["block_key", "source", "operator_index", "matrix_id", "rows",
                     "nnz", "counts_path", "counts_sha256", "meta_path",
                     "meta_sha256"], rows)

    def meta_by_path(self) -> dict[str, bytes]:
        return {"%s.meta.csv" % k: v for k, v in self.op31.items()}


@pytest.fixture()
def world() -> World:
    return World()


def _select(world: World, manifest=None, **overrides):
    payload = manifest if manifest is not None else world.complete_manifest()
    kwargs = dict(
        complete_manifest_bytes=payload,
        expected_complete_manifest_sha256=hashlib.sha256(payload).hexdigest(),
        expected_total_blocks=4, expected_operators=3, expected_op31_blocks=2)
    kwargs.update(overrides)
    return ifa.select_op31_blocks(**kwargs)


def _numerator(world: World, **overrides):
    kwargs = dict(membership_bytes=world.membership,
                  expected_membership_sha256=hashlib.sha256(
                      world.membership).hexdigest())
    kwargs.update(overrides)
    return ifa.immune_numerator_from_membership(**kwargs)


def _denominator(world: World):
    return ifa.op31_denominator_from_blocks(
        selected_blocks=_select(world), meta_bytes_by_path=world.meta_by_path())


# --- numerator --------------------------------------------------------------

def test_the_numerator_counts_accepted_immune_cells_per_donor(world: World) -> None:
    assert _numerator(world) == {"D1": 2, "D2": 1}


def test_a_membership_digest_mismatch_stops(world: World) -> None:
    with pytest.raises(AssertionError) as excinfo:
        _numerator(world, expected_membership_sha256="f" * 64)
    assert ifa.STOP_MEMBERSHIP_DIGEST in str(excinfo.value)


def test_a_membership_for_another_operator_is_refused(world: World) -> None:
    """Requiring the column and ignoring its value would admit another operator."""
    other = _membership([("C1", "D1")], operator=30)
    with pytest.raises(AssertionError) as excinfo:
        _numerator(world, membership_bytes=other,
                   expected_membership_sha256=hashlib.sha256(other).hexdigest())
    assert ifa.STOP_OPERATOR in str(excinfo.value)


def test_a_membership_for_another_matrix_is_refused(world: World) -> None:
    other = _membership([("C1", "D1")], matrix="sea_ad_pfc_rna_final_2026")
    with pytest.raises(AssertionError) as excinfo:
        _numerator(world, membership_bytes=other,
                   expected_membership_sha256=hashlib.sha256(other).hexdigest())
    assert ifa.STOP_MATRIX in str(excinfo.value)


def test_a_duplicate_membership_cell_is_refused(world: World) -> None:
    """A duplicate would inflate the numerator silently."""
    dup = _membership([("C1", "D1"), ("C1", "D1")])
    with pytest.raises(AssertionError):
        _numerator(world, membership_bytes=dup,
                   expected_membership_sha256=hashlib.sha256(dup).hexdigest())


def test_a_membership_missing_a_required_column_stops(world: World) -> None:
    broken = _csv(["source", "matrix_id", "operator_index", "donor_id"],
                  [["SEA_AD", MATRIX, OPERATOR, "D1"]])
    with pytest.raises(AssertionError) as excinfo:
        _numerator(world, membership_bytes=broken,
                   expected_membership_sha256=hashlib.sha256(broken).hexdigest())
    assert ifa.STOP_COLUMNS in str(excinfo.value)


# --- complete manifest consumption -----------------------------------------

def test_the_complete_multi_operator_manifest_is_accepted_and_filtered(
        world: World) -> None:
    """The real manifest's first row is operator 0; selection happens inside."""
    manifest = world.complete_manifest()
    operators = {int(r["operator_index"])
                 for r in csv.DictReader(io.StringIO(manifest.decode("utf-8")))}
    assert operators == {0, OPERATOR, 32}
    selected = _select(world)
    assert [b["block_key"] for b in selected] == sorted(world.op31)


def test_a_manifest_digest_mismatch_stops(world: World) -> None:
    with pytest.raises(AssertionError) as excinfo:
        _select(world, expected_complete_manifest_sha256="f" * 64)
    assert ifa.STOP_MANIFEST_DIGEST in str(excinfo.value)


def test_a_prefiltered_single_operator_manifest_is_refused(world: World) -> None:
    """Bytes narrowed to one operator cannot be the complete manifest."""
    filtered = world.op31_only_manifest()
    with pytest.raises(AssertionError) as excinfo:
        _select(world, manifest=filtered, expected_total_blocks=2,
                expected_operators=1)
    assert ifa.STOP_MANIFEST_PREFILTERED in str(excinfo.value)


def test_the_declared_complete_digest_cannot_describe_filtered_bytes(
        world: World) -> None:
    filtered = world.op31_only_manifest()
    with pytest.raises(AssertionError) as excinfo:
        _select(world, manifest=filtered,
                expected_complete_manifest_sha256=hashlib.sha256(
                    world.complete_manifest()).hexdigest())
    assert ifa.STOP_MANIFEST_DIGEST in str(excinfo.value)


@pytest.mark.parametrize("field,value", [
    ("expected_total_blocks", 99),
    ("expected_operators", 9),
    ("expected_op31_blocks", 99),
])
def test_a_manifest_geometry_mismatch_stops(world: World, field, value) -> None:
    """Geometry is asserted so a silently narrowed selection cannot pass."""
    with pytest.raises(AssertionError) as excinfo:
        _select(world, **{field: value})
    assert ifa.STOP_MANIFEST_GEOMETRY in str(excinfo.value)


def test_an_operator31_block_declaring_another_matrix_stops(world: World) -> None:
    world.op31["op31/block-00002"] = _meta(["D1"])
    manifest = world.complete_manifest().decode("utf-8").replace(
        "op31/block-00002.counts.npz", "op31/block-00002.counts.npz")
    rows = list(csv.DictReader(io.StringIO(manifest)))
    for row in rows:
        if row["block_key"] == "op31/block-00002":
            row["matrix_id"] = "sea_ad_pfc_rna_final_2026"
    rebuilt = _csv(list(rows[0]), [[r[c] for c in rows[0]] for r in rows])
    with pytest.raises(AssertionError) as excinfo:
        _select(world, manifest=rebuilt, expected_total_blocks=5,
                expected_operators=3, expected_op31_blocks=3)
    assert ifa.STOP_MATRIX in str(excinfo.value)


# --- denominator ------------------------------------------------------------

def test_the_denominator_counts_every_op31_cell_per_donor(world: World) -> None:
    counts, consumed = _denominator(world)
    assert counts == {"D1": 3, "D2": 3}
    assert len(consumed) == 2


def test_a_block_metadata_digest_mismatch_stops(world: World) -> None:
    metas = world.meta_by_path()
    metas["op31/block-00000.meta.csv"] = _meta(["D1"])
    with pytest.raises(AssertionError) as excinfo:
        ifa.op31_denominator_from_blocks(selected_blocks=_select(world),
                                         meta_bytes_by_path=metas)
    assert ifa.STOP_META_DIGEST in str(excinfo.value)


def test_an_absent_block_metadata_member_stops(world: World) -> None:
    metas = world.meta_by_path()
    metas.pop("op31/block-00001.meta.csv")
    with pytest.raises(AssertionError) as excinfo:
        ifa.op31_denominator_from_blocks(selected_blocks=_select(world),
                                         meta_bytes_by_path=metas)
    assert ifa.STOP_META_ABSENT in str(excinfo.value)


def test_a_row_count_disagreeing_with_the_manifest_stops(world: World) -> None:
    """Declared geometry and parsed geometry must agree."""
    selected = [dict(b) for b in _select(world)]
    selected[0]["rows"] = 99
    with pytest.raises(AssertionError) as excinfo:
        ifa.op31_denominator_from_blocks(selected_blocks=selected,
                                         meta_bytes_by_path=world.meta_by_path())
    assert ifa.STOP_MANIFEST_GEOMETRY in str(excinfo.value)


# --- binding the integers ---------------------------------------------------

def test_the_bound_rows_carry_exact_integers_not_a_fraction(world: World) -> None:
    numerator = _numerator(world)
    denominator, _ = _denominator(world)
    rows = ifa.build_immune_fraction(numerator_by_donor=numerator,
                                     denominator_by_donor=denominator)
    assert [r["donor_id"] for r in rows] == ["D1", "D2"]
    for row in rows:
        assert isinstance(row["immune_n_donor"], int)
        assert isinstance(row["total_op31_n_donor"], int)
        assert "IMMUNE_FRACTION" not in row
        assert not any(isinstance(v, float) for v in row.values())


def test_the_fraction_is_derived_from_the_bound_integers(world: World) -> None:
    rows = ifa.build_immune_fraction(numerator_by_donor={"D1": 2, "D2": 1},
                                     denominator_by_donor={"D1": 3, "D2": 3})
    assert ifa.immune_fraction_value(rows[0]) == pytest.approx(2 / 3)
    assert ifa.immune_fraction_value(rows[1]) == pytest.approx(1 / 3)


def test_a_donor_set_disagreement_stops() -> None:
    """The two counts come from independent authorities, so they must agree."""
    with pytest.raises(AssertionError) as excinfo:
        ifa.build_immune_fraction(numerator_by_donor={"D1": 1, "D3": 1},
                                  denominator_by_donor={"D1": 2, "D2": 2})
    assert ifa.STOP_DONOR_SETS_DIFFER in str(excinfo.value)
    assert "D3" in str(excinfo.value) and "D2" in str(excinfo.value)


def test_a_numerator_exceeding_its_denominator_stops() -> None:
    with pytest.raises(AssertionError) as excinfo:
        ifa.build_immune_fraction(numerator_by_donor={"D1": 5},
                                  denominator_by_donor={"D1": 3})
    assert ifa.STOP_EXCEEDS_DENOMINATOR in str(excinfo.value)


@pytest.mark.parametrize("numerator,denominator", [(0, 3), (3, 0)])
def test_a_nonpositive_count_stops(numerator, denominator) -> None:
    """A donor in the accepted membership has immune cells by construction."""
    with pytest.raises(AssertionError) as excinfo:
        ifa.build_immune_fraction(numerator_by_donor={"D1": numerator},
                                  denominator_by_donor={"D1": denominator})
    assert ifa.STOP_NOT_POSITIVE in str(excinfo.value)


@pytest.mark.parametrize("bad", [True, 1.5, "2.0", "-1", "", None])
def test_a_count_that_is_not_an_exact_nonnegative_integer_stops(bad) -> None:
    """A float or a bool must not be coerced into an exact count."""
    with pytest.raises(AssertionError) as excinfo:
        ifa.build_immune_fraction(numerator_by_donor={"D1": bad},
                                  denominator_by_donor={"D1": 10})
    assert ifa.STOP_NOT_INTEGER in str(excinfo.value)


# --- roots ------------------------------------------------------------------

def test_the_root_is_deterministic_and_order_independent_of_input_mapping() -> None:
    a = ifa.build_immune_fraction(numerator_by_donor={"D1": 1, "D2": 2},
                                  denominator_by_donor={"D1": 10, "D2": 20})
    b = ifa.build_immune_fraction(numerator_by_donor={"D2": 2, "D1": 1},
                                  denominator_by_donor={"D2": 20, "D1": 10})
    assert ifa.immune_fraction_root(a) == ifa.immune_fraction_root(b)


def test_the_root_moves_when_any_count_moves() -> None:
    base = ifa.build_immune_fraction(numerator_by_donor={"D1": 1, "D2": 2},
                                     denominator_by_donor={"D1": 10, "D2": 20})
    moved = ifa.build_immune_fraction(numerator_by_donor={"D1": 1, "D2": 3},
                                      denominator_by_donor={"D1": 10, "D2": 20})
    assert ifa.immune_fraction_root(base) != ifa.immune_fraction_root(moved)


def test_a_numerator_denominator_swap_changes_the_root() -> None:
    """Framing must distinguish the two positions, not just the multiset."""
    a = ifa.build_immune_fraction(numerator_by_donor={"D1": 2},
                                  denominator_by_donor={"D1": 10})
    b = ifa.build_immune_fraction(numerator_by_donor={"D1": 10},
                                  denominator_by_donor={"D1": 10})
    assert ifa.immune_fraction_root(a) != ifa.immune_fraction_root(b)


def test_donor_identity_collisions_do_not_share_a_root() -> None:
    """The delimiter collision class that broke earlier authority roots."""
    a = ifa.build_immune_fraction(numerator_by_donor={"a|b": 1},
                                  denominator_by_donor={"a|b": 10})
    b = ifa.build_immune_fraction(numerator_by_donor={"a": 1, "b": 1},
                                  denominator_by_donor={"a": 10, "b": 10})
    assert ifa.immune_fraction_root(a) != ifa.immune_fraction_root(b)


def test_an_integer_and_its_string_spelling_do_not_share_a_root() -> None:
    assert ifa._typed(2) != ifa._typed("2")
    assert ifa._typed(True) != ifa._typed(1)


def test_the_typed_framing_refuses_a_float() -> None:
    with pytest.raises(AssertionError) as excinfo:
        ifa._typed(0.5)
    assert ifa.STOP_FIELD_SCHEMA in str(excinfo.value)


# --- production invariants --------------------------------------------------

def test_the_production_geometry_is_asserted() -> None:
    rows = ifa.build_immune_fraction(
        numerator_by_donor={"D%d" % i: 1 for i in range(46)},
        denominator_by_donor={"D%d" % i: 2 for i in range(46)})
    with pytest.raises(AssertionError) as excinfo:
        ifa.assert_production_geometry(rows)
    assert ifa.STOP_PRODUCTION_GEOMETRY in str(excinfo.value)


def test_the_production_donor_count_is_asserted() -> None:
    rows = ifa.build_immune_fraction(numerator_by_donor={"D1": 1},
                                     denominator_by_donor={"D1": 2})
    with pytest.raises(AssertionError) as excinfo:
        ifa.assert_production_geometry(rows)
    assert ifa.STOP_PRODUCTION_GEOMETRY in str(excinfo.value)


def test_the_frozen_production_constants_are_the_verified_ones() -> None:
    """These were each verified independently, so pin them."""
    assert ifa.COMPLETE_MANIFEST_SHA256 == (
        "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29")
    assert ifa.COMPLETE_MANIFEST_BLOCKS == 8915
    assert ifa.COMPLETE_MANIFEST_OPERATORS == 42
    assert ifa.OP31_BLOCKS == 1247
    assert ifa.PRODUCTION_DONORS == 46
    assert ifa.PRODUCTION_IMMUNE_CELLS == 20804
    assert ifa.PRODUCTION_OP31_CELLS == 638150


def test_the_denominator_population_equals_the_reader_fit_partition() -> None:
    """Records the verification that settled the denominator question.

    The op31 store holds 638,150 cells; the canonical SQLite reports op31
    reader_fit 638,150, reader_validation 173,736, reader_oracle 121,386. So the
    substrate is exactly reader_fit, the two candidate denominators coincide, and
    reader_validation and reader_oracle are excluded by count.
    """
    assert ifa.DENOMINATOR_EQUALS_READER_FIT_PARTITION is True
    assert ifa.OP31_ALL_PARTITIONS_CELLS == (
        ifa.PRODUCTION_OP31_CELLS
        + ifa.OP31_READER_VALIDATION_CELLS_EXCLUDED
        + ifa.OP31_READER_ORACLE_CELLS_EXCLUDED)


def test_the_formula_is_declared_a_successor_specification() -> None:
    """V18 states the covariate in prose; the formula is not recovered semantics."""
    assert ifa.FORMULA_SPECIFICATION_STATUS.startswith("SUCCESSOR_SPECIFICATION")
    assert "prose" in ifa.FORMULA_PROVENANCE


# --- package round trip -----------------------------------------------------

def test_the_package_round_trips_and_binds_both_roots(tmp_path, world: World) -> None:
    numerator = _numerator(world)
    denominator, consumed = _denominator(world)
    rows = ifa.build_immune_fraction(numerator_by_donor=numerator,
                                     denominator_by_donor=denominator)
    out = tmp_path / "pkg"
    summary = ifa.build_authority(
        out, rows=rows, membership_sha256=hashlib.sha256(world.membership).hexdigest(),
        complete_manifest_sha256=hashlib.sha256(world.complete_manifest()).hexdigest(),
        selected_op31_blocks=2, consumed_meta_sha256=consumed,
        derivation_code_sha256=CODE_SHA, check_production_geometry=False)
    loaded = ifa.load_authority(
        out,
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_immune_fraction_root_sha256=summary["immune_fraction_root_sha256"])
    assert [r["donor_id"] for r in loaded["rows"]] == ["D1", "D2"]
    assert loaded["metadata"]["fraction_stored"] is False
    assert loaded["metadata"]["real_execution_ready"] is False


def test_the_loader_refuses_a_wrong_package_root(tmp_path, world: World) -> None:
    numerator = _numerator(world)
    denominator, consumed = _denominator(world)
    rows = ifa.build_immune_fraction(numerator_by_donor=numerator,
                                     denominator_by_donor=denominator)
    out = tmp_path / "pkg"
    summary = ifa.build_authority(
        out, rows=rows, membership_sha256=hashlib.sha256(world.membership).hexdigest(),
        complete_manifest_sha256=hashlib.sha256(world.complete_manifest()).hexdigest(),
        selected_op31_blocks=2, consumed_meta_sha256=consumed,
        derivation_code_sha256=CODE_SHA, check_production_geometry=False)
    with pytest.raises(AssertionError) as excinfo:
        ifa.load_authority(
            out, expected_package_root_sha256="f" * 64,
            expected_immune_fraction_root_sha256=summary[
                "immune_fraction_root_sha256"])
    assert ifa.STOP_ROOT_MISMATCH in str(excinfo.value)


def test_a_tampered_registry_is_caught_on_load(tmp_path, world: World) -> None:
    numerator = _numerator(world)
    denominator, consumed = _denominator(world)
    rows = ifa.build_immune_fraction(numerator_by_donor=numerator,
                                     denominator_by_donor=denominator)
    out = tmp_path / "pkg"
    summary = ifa.build_authority(
        out, rows=rows, membership_sha256=hashlib.sha256(world.membership).hexdigest(),
        complete_manifest_sha256=hashlib.sha256(world.complete_manifest()).hexdigest(),
        selected_op31_blocks=2, consumed_meta_sha256=consumed,
        derivation_code_sha256=CODE_SHA, check_production_geometry=False)
    registry = out / ifa.REGISTRY
    registry.write_bytes(registry.read_bytes().replace(b"D1,2,3", b"D1,3,3"))
    with pytest.raises(AssertionError) as excinfo:
        ifa.load_authority(
            out, expected_package_root_sha256=summary["package_root_sha256"],
            expected_immune_fraction_root_sha256=summary[
                "immune_fraction_root_sha256"])
    assert ifa.STOP_ROOT_MISMATCH in str(excinfo.value)


def test_an_absent_package_member_stops(tmp_path, world: World) -> None:
    numerator = _numerator(world)
    denominator, consumed = _denominator(world)
    rows = ifa.build_immune_fraction(numerator_by_donor=numerator,
                                     denominator_by_donor=denominator)
    out = tmp_path / "pkg"
    summary = ifa.build_authority(
        out, rows=rows, membership_sha256=hashlib.sha256(world.membership).hexdigest(),
        complete_manifest_sha256=hashlib.sha256(world.complete_manifest()).hexdigest(),
        selected_op31_blocks=2, consumed_meta_sha256=consumed,
        derivation_code_sha256=CODE_SHA, check_production_geometry=False)
    (out / ifa.METADATA).unlink()
    with pytest.raises(AssertionError) as excinfo:
        ifa.load_authority(
            out, expected_package_root_sha256=summary["package_root_sha256"],
            expected_immune_fraction_root_sha256=summary[
                "immune_fraction_root_sha256"])
    assert ifa.STOP_PACKAGE_MEMBER in str(excinfo.value)


def test_writing_into_a_nonempty_directory_is_refused(tmp_path, world: World) -> None:
    out = tmp_path / "pkg"
    out.mkdir()
    (out / "stray.txt").write_text("x", encoding="utf-8")
    rows = ifa.build_immune_fraction(numerator_by_donor={"D1": 1},
                                     denominator_by_donor={"D1": 2})
    with pytest.raises(AssertionError) as excinfo:
        ifa.build_authority(
            out, rows=rows, membership_sha256="a" * 64,
            complete_manifest_sha256="b" * 64, selected_op31_blocks=1,
            consumed_meta_sha256={}, derivation_code_sha256=CODE_SHA,
            check_production_geometry=False)
    assert ifa.STOP_PACKAGE_MEMBER in str(excinfo.value)


def test_the_metadata_declares_the_covariate_is_not_an_eligibility_input(
        tmp_path, world: World) -> None:
    """It must never be mistaken for a technical_complete input."""
    numerator = _numerator(world)
    denominator, consumed = _denominator(world)
    rows = ifa.build_immune_fraction(numerator_by_donor=numerator,
                                     denominator_by_donor=denominator)
    out = tmp_path / "pkg"
    ifa.build_authority(
        out, rows=rows, membership_sha256=hashlib.sha256(world.membership).hexdigest(),
        complete_manifest_sha256=hashlib.sha256(world.complete_manifest()).hexdigest(),
        selected_op31_blocks=2, consumed_meta_sha256=consumed,
        derivation_code_sha256=CODE_SHA, check_production_geometry=False)
    meta = json.loads((out / ifa.METADATA).read_text(encoding="utf-8"))
    assert "MUST_NOT_FEED_TECHNICAL_COMPLETE" in meta["eligibility_role"]
    assert meta["pathology_values_read"] is False
    assert meta["derivation_code_byte_semantics"] == "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES"
