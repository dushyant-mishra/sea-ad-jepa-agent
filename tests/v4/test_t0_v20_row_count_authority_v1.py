"""Adversarial cases for the T0 V20 row and count authority.

Scope: this module verifies the integrity of this project's own data-provenance
records, in this repository. No third-party system, no network, no credentials,
no cryptanalysis, and no security control belonging to any system is
circumvented. The only check being probed is our own SHA-256 comparison, and
these cases exist to show it cannot be satisfied by anything but the bytes it
claims to describe. See docs/agent/T0_LANE_SECURITY_SCOPE.md.

The obligation here is stronger than locating 20,804 rows. It is to establish
that the exact raw count rows and the full-row `source_library` values actually
consumed are the ones the frozen authorities bind. Three notions must stay
distinct and must not be substitutable for one another:

* `population_closure_root` — the exhaustive population scan and its closure
  properties;
* `logical_row_authority_root` — the 20,804 rows in frozen membership order with
  their bound metadata;
* `physical_read_plan_root` — an I/O ordering that may be sorted for locality but
  can never redefine the population or its order, because every entry carries
  its `logical_index` and the plan must restore the logical root exactly.

`source_library` is an integer sum of the FULL raw source row, computed before
projection. It is bound as an exact positive integer and never recomputed, so
substituting either the 41,238-address row sum or the 35,076-address projected
sum must be refused.

Written before the implementation.
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

import t0_v20_row_count_authority_v1 as rc  # noqa: E402

MATRIX_ID = "sea_ad_mtg_rna_final_2026"
OPERATOR = 31
FEATURE_AUTHORITY_ROOT = "81b570abb46d4406b746478c48c121ae3e9b524b8736b6548488e264d4bcb1cf"

MEMBERSHIP_COLUMNS = ["source", "matrix_id", "operator_index", "local_row", "donor_id",
                      "partition", "cell_id", "native_class", "broad_class", "stable_key"]
META_COLUMNS = ["selection_row", "canonical_cell_id", "donor_id", "expression_row",
                "primary_row_weight", "source_library"]


def _csv(columns: list[str], rows: list[list[object]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def _membership(cells: list[tuple[str, str]]) -> bytes:
    """`(cell_id, donor_id)` in a deliberate order — this order is the authority."""
    rows = []
    for index, (cell, donor) in enumerate(cells):
        rows.append(["SEA_AD", MATRIX_ID, OPERATOR, index, donor, "reader_fit", cell,
                     "Immune", "Non-neuronal and Non-neural", 1000 + index])
    return _csv(MEMBERSHIP_COLUMNS, rows)


def _meta(entries: list[tuple[int, str, str, int, int]]) -> bytes:
    """`(selection_row, cell_id, donor_id, expression_row, source_library)`."""
    rows = [[s, c, d, e, "8.06e-08", lib] for s, c, d, e, lib in entries]
    return _csv(META_COLUMNS, rows)


class World:
    """A small synthetic population: three blocks in one operator."""

    def __init__(self) -> None:
        self.membership = _membership([("C1", "D1"), ("C2", "D1"), ("C3", "D2")])
        # C3 lives in the LAST block, which is what an early-exiting scan misses.
        self.blocks = {
            "op31/block-00000": _meta([(10, "C1", "D1", 100, 9470),
                                       (11, "X1", "D9", 101, 5000)]),
            "op31/block-00001": _meta([(20, "C2", "D1", 200, 8123)]),
            "op31/block-00002": _meta([(30, "C3", "D2", 300, 7777),
                                       (31, "X2", "D9", 301, 6000)]),
        }
        self.counts = {key: ("counts-%s" % key).encode("utf-8") for key in self.blocks}

    def manifest(self, **overrides) -> bytes:
        rows = []
        for key in sorted(self.blocks):
            meta = self.blocks[key]
            counts = self.counts[key]
            rows.append([key, "SEA_AD", overrides.get("operator_index", OPERATOR),
                         overrides.get("matrix_id", MATRIX_ID),
                         len(list(csv.DictReader(io.StringIO(meta.decode())))),
                         999, "%s.counts.npz" % key,
                         hashlib.sha256(counts).hexdigest(),
                         "%s.meta.csv" % key,
                         hashlib.sha256(meta).hexdigest()])
        return _csv(["block_key", "source", "operator_index", "matrix_id", "rows", "nnz",
                     "counts_path", "counts_sha256", "meta_path", "meta_sha256"], rows)

    def meta_by_path(self) -> dict[str, bytes]:
        return {"%s.meta.csv" % key: blob for key, blob in self.blocks.items()}


@pytest.fixture()
def world() -> World:
    return World()


def _closure(world: World, **overrides):
    manifest = overrides.pop("block_manifest_bytes", world.manifest())
    membership = overrides.pop("membership_bytes", world.membership)
    kwargs = dict(membership_bytes=membership,
                  expected_membership_sha256=hashlib.sha256(membership).hexdigest(),
                  block_manifest_bytes=manifest,
                  expected_block_manifest_sha256=hashlib.sha256(manifest).hexdigest(),
                  meta_bytes_by_path=world.meta_by_path(),
                  operator_index=OPERATOR, matrix_id=MATRIX_ID)
    kwargs.update(overrides)
    return rc.build_population_closure(**kwargs)


def _logical(world: World, closure=None, **overrides):
    kwargs = dict(closure=closure or _closure(world),
                  membership_bytes=world.membership,
                  feature_authority_root_sha256=FEATURE_AUTHORITY_ROOT)
    kwargs.update(overrides)
    return rc.build_logical_row_authority(**kwargs)


# --------------------------------------------------------------------------
# Population closure: exhaustive, not early-exiting.
# --------------------------------------------------------------------------
def test_the_closure_scans_every_block_and_reports_its_counts(world: World) -> None:
    closure = _closure(world)
    assert closure["blocks_scanned"] == 3
    assert closure["metadata_rows_scanned"] == 5
    assert closure["target_cells"] == 3
    assert closure["missing"] == 0
    assert closure["duplicate_target_hits"] == 0
    assert sorted(closure["donors"]) == ["D1", "D2"]
    assert closure["population_closure_root_sha256"]


def test_a_target_only_in_the_last_block_is_still_found(world: World) -> None:
    """An early-exiting scan finds C1 and C2 and stops before C3."""
    closure = _closure(world)
    assert "C3" in closure["row_locations"]
    assert closure["row_locations"]["C3"]["block_key"] == "op31/block-00002"


def test_a_duplicate_appearing_only_in_the_last_block_is_detected(world: World) -> None:
    """The reason the scan must not stop once every target has been seen."""
    world.blocks["op31/block-00002"] = _meta([(30, "C3", "D2", 300, 7777),
                                              (32, "C1", "D1", 302, 9470)])
    world.counts["op31/block-00002"] = b"counts-op31/block-00002"
    with pytest.raises(AssertionError, match="DUPLICATE_TARGET"):
        _closure(world)


def test_a_missing_target_stops(world: World) -> None:
    world.blocks.pop("op31/block-00001")
    world.counts.pop("op31/block-00001")
    with pytest.raises(AssertionError, match="TARGET_NOT_FOUND"):
        _closure(world)


def test_a_manifest_block_for_the_wrong_operator_stops(world: World) -> None:
    with pytest.raises(AssertionError, match="OPERATOR_MISMATCH"):
        _closure(world, block_manifest_bytes=world.manifest(operator_index=25))


def test_a_manifest_block_for_the_wrong_matrix_stops(world: World) -> None:
    with pytest.raises(AssertionError, match="MATRIX_MISMATCH"):
        _closure(world, block_manifest_bytes=world.manifest(matrix_id="sea_ad_ang_rna_final_2026"))


def test_a_metadata_digest_mismatch_stops(world: World) -> None:
    tampered = dict(world.meta_by_path())
    key = "op31/block-00001.meta.csv"
    tampered[key] = tampered[key].replace(b"8123", b"9999")
    with pytest.raises(AssertionError, match="META_DIGEST"):
        _closure(world, meta_bytes_by_path=tampered)


def test_an_absent_metadata_member_stops(world: World) -> None:
    partial = dict(world.meta_by_path())
    partial.pop("op31/block-00002.meta.csv")
    with pytest.raises(AssertionError, match="META_ABSENT"):
        _closure(world, meta_bytes_by_path=partial)


def test_a_donor_outside_the_membership_is_not_admitted(world: World) -> None:
    """Rows for other donors exist in the blocks and must not enter the population."""
    closure = _closure(world)
    assert set(closure["row_locations"]) == {"C1", "C2", "C3"}
    assert "X1" not in closure["row_locations"]
    assert "D9" not in closure["donors"]


# --------------------------------------------------------------------------
# Logical row authority: frozen membership order and bound metadata.
# --------------------------------------------------------------------------
def test_the_logical_authority_follows_membership_order(world: World) -> None:
    logical = _logical(world)
    assert [row["canonical_cell_id"] for row in logical["rows"]] == ["C1", "C2", "C3"]
    assert [row["logical_index"] for row in logical["rows"]] == [0, 1, 2]
    assert logical["logical_row_authority_root_sha256"]


def test_permuting_membership_order_changes_the_logical_root(world: World) -> None:
    first = _logical(world)["logical_row_authority_root_sha256"]
    permuted = World()
    permuted.membership = _membership([("C2", "D1"), ("C1", "D1"), ("C3", "D2")])
    second = _logical(permuted)["logical_row_authority_root_sha256"]
    assert first != second


def test_all_six_phase2_metadata_fields_are_bound(world: World) -> None:
    logical = _logical(world)
    row = logical["rows"][0]
    for field in ("selection_row", "canonical_cell_id", "donor_id", "expression_row",
                  "primary_row_weight", "source_library"):
        assert field in row, field
    assert row["selection_row"] == 10
    assert row["expression_row"] == 100
    assert row["source_library"] == 9470
    # And which of them V20 actually consumes must be declared, not implied.
    assert set(logical["v20_consumed_fields"]) <= set(row)
    assert set(logical["audit_only_fields"]) <= set(row)
    assert not (set(logical["v20_consumed_fields"]) & set(logical["audit_only_fields"]))


def test_a_shifted_expression_row_changes_the_logical_root(world: World) -> None:
    first = _logical(world)["logical_row_authority_root_sha256"]
    shifted = World()
    shifted.blocks["op31/block-00000"] = _meta([(10, "C1", "D1", 101, 9470),
                                                (11, "X1", "D9", 102, 5000)])
    shifted.counts["op31/block-00000"] = b"counts-op31/block-00000"
    assert _logical(shifted)["logical_row_authority_root_sha256"] != first


def test_the_logical_authority_requires_the_feature_authority_root(world: World) -> None:
    with pytest.raises(AssertionError, match="FEATURE_AUTHORITY_ROOT_ABSENT"):
        _logical(world, feature_authority_root_sha256="")
    with pytest.raises(AssertionError, match="FEATURE_AUTHORITY_ROOT_MALFORMED"):
        _logical(world, feature_authority_root_sha256="not-a-digest")


# --------------------------------------------------------------------------
# source_library: exact positive integer, never recomputed.
# --------------------------------------------------------------------------
def test_source_library_is_bound_as_an_exact_positive_integer(world: World) -> None:
    logical = _logical(world)
    assert [row["source_library"] for row in logical["rows"]] == [9470, 8123, 7777]
    assert all(isinstance(row["source_library"], int) for row in logical["rows"])


@pytest.mark.parametrize("bad", ["0", "-5", "9470.5", "", "1e4", "nan"])
def test_a_non_integral_or_nonpositive_source_library_stops(world: World, bad) -> None:
    world.blocks["op31/block-00001"] = _csv(
        META_COLUMNS, [[20, "C2", "D1", 200, "8.06e-08", bad]])
    world.counts["op31/block-00001"] = b"counts-op31/block-00001"
    with pytest.raises(AssertionError, match="SOURCE_LIBRARY"):
        _logical(world)


def test_substituting_a_projected_or_address_space_sum_is_refused(world: World) -> None:
    """The two substitutions the frozen contract forbids.

    Phase2 computes `source_library` as an integer sum of the FULL raw source
    row, before source-to-address projection, so neither the 41,238-address
    stored row nor the 35,076-address T0 projection need sum to it.
    """
    logical = _logical(world)
    bound = logical["rows"][0]["source_library"]
    for label, candidate in (("41k row sum", 9001), ("35,076 projection sum", 8500)):
        with pytest.raises(AssertionError, match="SOURCE_LIBRARY_NOT_BOUND"):
            rc.assert_source_library_bound(
                logical=logical, logical_index=0, candidate_source_library=candidate)
    # The bound value itself is accepted, so the check discriminates.
    assert rc.assert_source_library_bound(
        logical=logical, logical_index=0, candidate_source_library=bound) is True


def test_normalisation_must_be_applied_exactly_once(world: World) -> None:
    """A double application is a different transform and must be detectable."""
    once = rc.normalise_once(raw_counts=[0, 1, 5, 250], source_library=9470)
    twice = rc.normalise_once(raw_counts=once, source_library=9470)
    assert once != twice
    with pytest.raises(AssertionError, match="NORMALIZATION_NOT_ONCE_ONLY"):
        rc.assert_normalised_once(values=twice, raw_counts=[0, 1, 5, 250],
                                  source_library=9470)
    assert rc.assert_normalised_once(values=once, raw_counts=[0, 1, 5, 250],
                                     source_library=9470) is True


# --------------------------------------------------------------------------
# Physical read plan: may reorder for I/O, may never redefine the population.
# --------------------------------------------------------------------------
def test_the_physical_plan_is_sorted_for_locality_but_carries_logical_index(
    world: World,
) -> None:
    logical = _logical(world)
    plan = rc.build_physical_read_plan(logical=logical)
    keys = [(entry["block_key"], entry["row_index"]) for entry in plan["plan"]]
    assert keys == sorted(keys)
    assert sorted(entry["logical_index"] for entry in plan["plan"]) == [0, 1, 2]
    assert plan["physical_read_plan_root_sha256"] != (
        logical["logical_row_authority_root_sha256"]
    )


def test_the_plan_must_restore_the_logical_root_exactly(world: World) -> None:
    logical = _logical(world)
    plan = rc.build_physical_read_plan(logical=logical)
    assert rc.assert_plan_restores_logical(
        plan=plan,
        expected_logical_root_sha256=logical["logical_row_authority_root_sha256"],
    ) is True


def test_a_plan_with_a_tampered_logical_index_cannot_restore(world: World) -> None:
    """This is what stops physical ordering from redefining the population."""
    logical = _logical(world)
    plan = rc.build_physical_read_plan(logical=logical)
    plan["plan"][0] = dict(plan["plan"][0])
    plan["plan"][0]["logical_index"] = 2
    with pytest.raises(AssertionError, match="LOGICAL_ORDER_NOT_RESTORABLE"):
        rc.assert_plan_restores_logical(
            plan=plan,
            expected_logical_root_sha256=logical["logical_row_authority_root_sha256"])


def test_a_plan_missing_a_row_cannot_restore(world: World) -> None:
    logical = _logical(world)
    plan = rc.build_physical_read_plan(logical=logical)
    plan["plan"] = plan["plan"][:-1]
    with pytest.raises(AssertionError, match="LOGICAL_ORDER_NOT_RESTORABLE"):
        rc.assert_plan_restores_logical(
            plan=plan,
            expected_logical_root_sha256=logical["logical_row_authority_root_sha256"])


def test_the_three_roots_are_distinct_and_not_interchangeable(world: World) -> None:
    closure = _closure(world)
    logical = _logical(world, closure=closure)
    plan = rc.build_physical_read_plan(logical=logical)
    roots = {closure["population_closure_root_sha256"],
             logical["logical_row_authority_root_sha256"],
             plan["physical_read_plan_root_sha256"]}
    assert len(roots) == 3
    # A physical root must never satisfy a logical expectation.
    with pytest.raises(AssertionError, match="LOGICAL_ORDER_NOT_RESTORABLE"):
        rc.assert_plan_restores_logical(
            plan=plan,
            expected_logical_root_sha256=plan["physical_read_plan_root_sha256"])


# --------------------------------------------------------------------------
# Counts payloads: bound by digest, and shaped as the address space demands.
# --------------------------------------------------------------------------
def test_a_counts_payload_must_match_its_bound_digest(world: World) -> None:
    logical = _logical(world)
    row = logical["rows"][0]
    authentic = world.counts["op31/block-00000"]
    assert rc.verify_counts_payload(
        logical=logical, logical_index=0, counts_bytes=authentic) is True
    with pytest.raises(AssertionError, match="COUNTS_PAYLOAD_DIGEST"):
        rc.verify_counts_payload(
            logical=logical, logical_index=0, counts_bytes=authentic + b"x")
    assert row["counts_sha256"] == hashlib.sha256(authentic).hexdigest()


def test_the_authority_does_not_claim_execution_readiness(world: World) -> None:
    closure = _closure(world)
    logical = _logical(world, closure=closure)
    plan = rc.build_physical_read_plan(logical=logical)
    for record in (closure, logical, plan):
        assert record["real_execution_ready"] is False


def test_the_three_roots_are_injective_over_delimiter_bearing_identities(
    world: World,
) -> None:
    """The same framing defect was fixed here pre-emptively, so prove it.

    Block keys and cell identities are external strings. Under a
    delimiter-joined framing a block key could absorb the next entry's marker,
    so all three roots use length prefixing.
    """
    closure = _closure(world)
    logical = _logical(world, closure=closure)
    plan = rc.build_physical_read_plan(logical=logical)

    shifted = {
        "schema": closure["schema"], "namespace": closure["namespace"],
        "operator_index": closure["operator_index"],
        "matrix_id": closure["matrix_id"],
    }
    # Two closures whose per-cell location strings differ only in where a
    # delimiter would have fallen must not share a root.
    a = rc._closure_root(31, "M", ["b1"], 1, {"c": _loc("x#1", 2)}, "a" * 64, "b" * 64)
    b = rc._closure_root(31, "M", ["b1"], 1, {"c": _loc("x", 12)}, "a" * 64, "b" * 64)
    assert a != b

    left = rc._closure_root(31, "M", ["b1|b=b2"], 1, {"c": _loc("k", 0)}, "a" * 64, "b" * 64)
    right = rc._closure_root(31, "M", ["b1", "b2"], 1, {"c": _loc("k", 0)}, "a" * 64, "b" * 64)
    assert left != right
    assert shifted["matrix_id"] == MATRIX_ID
    # And the three production roots remain mutually distinct after the change.
    assert len({closure["population_closure_root_sha256"],
                logical["logical_row_authority_root_sha256"],
                plan["physical_read_plan_root_sha256"]}) == 3


# --------------------------------------------------------------------------
# Type-substitution ambiguity, and the six substantive defects found by
# independent review. All of these fail against the pre-repair implementation.
# --------------------------------------------------------------------------
def test_the_roots_are_injective_over_types(world: World) -> None:
    """`str()` before hashing made 1 and "1" identical.

    Length prefixing closed delimiter ambiguity but not type ambiguity, and
    coercing with int() or str() inside the digest normalised the substitution
    away so the type tag bound nothing.
    """
    rows_typed = [{"logical_index": 0, "canonical_cell_id": "C", "donor_id": "D",
                   "block_key": "b", "row_index": 1, "selection_row": 2,
                   "expression_row": 3, "primary_row_weight": "w",
                   "source_library": 9470, "meta_path": "m.csv",
                   "meta_sha256": "m", "counts_path": "c.npz",
                   "counts_sha256": "c"}]
    rows_text = [dict(rows_typed[0], row_index="1", logical_index="0",
                      source_library="9470")]
    assert rc._logical_root(rows_typed, "f" * 64, "e" * 64) !=         rc._logical_root(rows_text, "f" * 64, "e" * 64)
    assert rc._closure_root(31, "M", ["b"], 1, {"c": _loc("k", 0)}, "a" * 64, "b" * 64) != (
        rc._closure_root("31", "M", ["b"], "1", {"c": _loc("k", "0")}, "a" * 64, "b" * 64))


def test_the_external_verifier_refuses_type_substitutions(world: World) -> None:
    """The verifier path, not merely the constructor."""
    logical = _logical(world)
    good = rc.assert_row_authority_lawful(
        logical=logical,
        expected_logical_row_authority_root_sha256=logical[
            "logical_row_authority_root_sha256"],
        expected_feature_authority_root_sha256=FEATURE_AUTHORITY_ROOT,
        expected_population_closure_root_sha256=logical[
            "population_closure_root_sha256"])
    assert good["rows"] == 3
    for field, replacement in (("row_index", "1"), ("logical_index", "0"),
                               ("source_library", "9470"), ("selection_row", "2")):
        forged = dict(logical)
        forged["rows"] = [dict(row) for row in logical["rows"]]
        forged["rows"][0][field] = replacement
        with pytest.raises(AssertionError, match="FIELD_SCHEMA_VIOLATION"):
            rc.assert_row_authority_lawful(
                logical=forged,
                expected_logical_row_authority_root_sha256=logical[
                    "logical_row_authority_root_sha256"],
                expected_feature_authority_root_sha256=FEATURE_AUTHORITY_ROOT,
                expected_population_closure_root_sha256=logical[
                    "population_closure_root_sha256"])


def test_the_membership_and_manifest_digests_are_required(world: World) -> None:
    """Arbitrary caller-supplied CSV bytes were accepted."""
    good_membership = hashlib.sha256(world.membership).hexdigest()
    good_manifest = hashlib.sha256(world.manifest()).hexdigest()
    assert _closure(world, expected_membership_sha256=good_membership,
                    expected_block_manifest_sha256=good_manifest)["target_cells"] == 3
    with pytest.raises(AssertionError, match="MEMBERSHIP_DIGEST"):
        _closure(world, expected_membership_sha256="0" * 64,
                 expected_block_manifest_sha256=good_manifest)
    with pytest.raises(AssertionError, match="BLOCK_MANIFEST_DIGEST"):
        _closure(world, expected_membership_sha256=good_membership,
                 expected_block_manifest_sha256="0" * 64)


def test_a_phase2_donor_disagreeing_with_membership_stops(world: World) -> None:
    """donor_id was emitted from membership while the metadata's was ignored."""
    world.blocks["op31/block-00000"] = _meta([(10, "C1", "D9", 100, 9470),
                                              (11, "X1", "D9", 101, 5000)])
    world.counts["op31/block-00000"] = b"counts-op31/block-00000"
    with pytest.raises(AssertionError, match="DONOR_IDENTITY_DISAGREES"):
        _closure(world)


def test_membership_operator_and_matrix_values_are_required(world: World) -> None:
    """Only the presence of the columns was checked, never their values."""
    rows = []
    for index, (cell, donor) in enumerate([("C1", "D1"), ("C2", "D1"), ("C3", "D2")]):
        rows.append(["SEA_AD", MATRIX_ID, 25, index, donor, "reader_fit", cell,
                     "Immune", "Non-neuronal and Non-neural", 1000 + index])
    wrong_operator = _csv(MEMBERSHIP_COLUMNS, rows)
    with pytest.raises(AssertionError, match="MEMBERSHIP_OPERATOR"):
        _closure(world, membership_bytes=wrong_operator,
                 expected_membership_sha256=hashlib.sha256(wrong_operator).hexdigest())

    rows = []
    for index, (cell, donor) in enumerate([("C1", "D1"), ("C2", "D1"), ("C3", "D2")]):
        rows.append(["SEA_AD", "sea_ad_ang_rna_final_2026", OPERATOR, index, donor,
                     "reader_fit", cell, "Immune", "Non-neuronal and Non-neural",
                     1000 + index])
    wrong_matrix = _csv(MEMBERSHIP_COLUMNS, rows)
    with pytest.raises(AssertionError, match="MEMBERSHIP_MATRIX"):
        _closure(world, membership_bytes=wrong_matrix,
                 expected_membership_sha256=hashlib.sha256(wrong_matrix).hexdigest())


def test_a_duplicate_membership_cell_stops(world: World) -> None:
    """A dict keyed on cell_id silently redefined the population."""
    duplicated = _membership([("C1", "D1"), ("C1", "D1"), ("C3", "D2")])
    with pytest.raises(AssertionError, match="MEMBERSHIP_CELL_NOT_UNIQUE"):
        _closure(world, membership_bytes=duplicated,
                 expected_membership_sha256=hashlib.sha256(duplicated).hexdigest())


# --------------------------------------------------------------------------
# The substantive requirement: source_library proven against the authenticated
# FULL RAW SOURCE ROW, not against the metadata that declares it.
# --------------------------------------------------------------------------
def _loc(block_key, row_index) -> dict:
    """A row-location record shaped like the closure's own.

    The closure root now binds meta_path and counts_path too, because both are
    consumed on the execution path and must not travel unbound.
    """
    return {"block_key": block_key, "row_index": row_index,
            "meta_path": "%s.meta.csv" % block_key,
            "meta_sha256": "c" * 64,
            "counts_path": "%s.counts.npz" % block_key,
            "counts_sha256": "d" * 64}


def _raw_provenance(width: int = 36_601, logical=None, logical_index: int = 0) -> dict:
    """A lawful provenance record for the bound row.

    The proof contract authenticates the source asset, the matrix slot and the
    row/cell/donor identity, so a placeholder digest and an arbitrary row index
    no longer constitute provenance.
    """
    row = logical["rows"][int(logical_index)] if logical is not None else {}
    return {"source_sha256": rc.MTG_SOURCE_SHA256,
            "matrix_slot": rc.MTG_SOURCE_MATRIX_SLOT,
            "source_row_index": int(row.get("expression_row", 0)),
            "canonical_cell_id": str(row.get("canonical_cell_id", "")),
            "donor_id": str(row.get("donor_id", "")),
            "source_width": width}


def test_source_library_is_proven_against_the_authenticated_raw_row(world: World) -> None:
    logical = _logical(world)
    bound = logical["rows"][0]["source_library"]
    raw = [0] * 36_600 + [bound]
    assert sum(raw) == bound
    assert rc._prove_source_library_fixture_values(
        logical=logical, logical_index=0, raw_source_row_values=raw,
        raw_source_provenance=_raw_provenance(logical=logical)) is True


def test_a_raw_row_summing_to_the_wrong_total_stops(world: World) -> None:
    logical = _logical(world)
    raw = [0] * 36_600 + [logical["rows"][0]["source_library"] + 1]
    with pytest.raises(AssertionError, match="SOURCE_LIBRARY_NOT_PROVEN"):
        rc._prove_source_library_fixture_values(
            logical=logical, logical_index=0, raw_source_row_values=raw,
            raw_source_provenance=_raw_provenance(logical=logical))


def test_a_row_of_address_space_width_is_refused_as_the_raw_source_row(
    world: World,
) -> None:
    """The stored 41,238-address row is not the full raw source row.

    Phase2 computes source_library before projection, so a row of address-space
    width cannot be the thing that produced it and must not be offered as proof
    even if its sum happened to match.
    """
    logical = _logical(world)
    bound = logical["rows"][0]["source_library"]
    projected = [0] * (rc.ADDRESS_SPACE_SIZE - 1) + [bound]
    with pytest.raises(AssertionError, match="RAW_ROW_WIDTH_IS_ADDRESS_SPACE"):
        rc._prove_source_library_fixture_values(
            logical=logical, logical_index=0, raw_source_row_values=projected,
            raw_source_provenance=_raw_provenance(width=rc.ADDRESS_SPACE_SIZE, logical=logical))


@pytest.mark.parametrize("bad", [-1, 1.5, float("nan")])
def test_non_integral_or_negative_raw_counts_stop(world: World, bad) -> None:
    """The bad value sits inside a row of lawful source width.

    A short row would now be refused on width before its values were examined,
    which would make this case pass for the wrong reason.
    """
    logical = _logical(world)
    raw = [bad] + [0] * 36_600
    assert len(raw) == rc.SOURCE_FEATURE_COUNT
    with pytest.raises(AssertionError, match="RAW_COUNTS_NOT_NONNEGATIVE_INTEGERS"):
        rc._prove_source_library_fixture_values(
            logical=logical, logical_index=0, raw_source_row_values=raw,
            raw_source_provenance=_raw_provenance(logical=logical))


def test_the_raw_row_provenance_must_be_bound(world: World) -> None:
    logical = _logical(world)
    raw = [0] * 36_600 + [logical["rows"][0]["source_library"]]
    for missing in ("source_sha256", "source_row_index", "source_width"):
        provenance = {k: v for k, v in _raw_provenance().items() if k != missing}
        with pytest.raises(AssertionError, match="RAW_ROW_PROVENANCE"):
            rc._prove_source_library_fixture_values(
                logical=logical, logical_index=0, raw_source_row_values=raw,
                raw_source_provenance=provenance)
    mismatched = dict(_raw_provenance(), source_width=99)
    with pytest.raises(AssertionError, match="RAW_ROW_PROVENANCE"):
        rc._prove_source_library_fixture_values(
            logical=logical, logical_index=0, raw_source_row_values=raw,
            raw_source_provenance=mismatched)


# --------------------------------------------------------------------------
# Selected-row verification: geometry, semantics, bounds, correspondence.
# --------------------------------------------------------------------------
def test_the_selected_row_must_have_address_space_width(world: World) -> None:
    logical = _logical(world)
    row = logical["rows"][0]
    good = [0] * rc.ADDRESS_SPACE_SIZE
    assert rc.verify_selected_row(
        logical=logical, logical_index=0, row_values=good,
        selected_expression_row=row["expression_row"]) is True
    with pytest.raises(AssertionError, match="ROW_WIDTH"):
        rc.verify_selected_row(
            logical=logical, logical_index=0, row_values=[0] * 100,
            selected_expression_row=row["expression_row"])


@pytest.mark.parametrize("bad", [[-1], [0.5], [float("inf")]])
def test_a_selected_row_with_illegal_count_semantics_stops(world: World, bad) -> None:
    logical = _logical(world)
    values = bad + [0] * (rc.ADDRESS_SPACE_SIZE - len(bad))
    with pytest.raises(AssertionError, match="ROW_COUNTS_NOT_NONNEGATIVE_INTEGERS"):
        rc.verify_selected_row(
            logical=logical, logical_index=0, row_values=values,
            selected_expression_row=logical["rows"][0]["expression_row"])


def test_selecting_the_wrong_row_stops_even_with_correct_block_bytes(
    world: World,
) -> None:
    """Authentic payload, wrong row: the correspondence must be checked."""
    logical = _logical(world)
    bound = logical["rows"][0]["expression_row"]
    assert rc.verify_counts_payload(
        logical=logical, logical_index=0,
        counts_bytes=world.counts["op31/block-00000"]) is True
    with pytest.raises(AssertionError, match="SELECTED_ROW_NOT_BOUND"):
        rc.verify_selected_row(
            logical=logical, logical_index=0, row_values=[0] * rc.ADDRESS_SPACE_SIZE,
            selected_expression_row=bound + 1)


def test_an_expression_row_outside_the_population_bounds_stops(world: World) -> None:
    logical = _logical(world)
    with pytest.raises(AssertionError, match="EXPRESSION_ROW_OUT_OF_BOUNDS"):
        rc.verify_selected_row(
            logical=logical, logical_index=0, row_values=[0] * rc.ADDRESS_SPACE_SIZE,
            selected_expression_row=-1, expression_row_upper_bound=4_553_407)
    with pytest.raises(AssertionError, match="EXPRESSION_ROW_OUT_OF_BOUNDS"):
        rc.verify_selected_row(
            logical=logical, logical_index=0, row_values=[0] * rc.ADDRESS_SPACE_SIZE,
            selected_expression_row=4_553_407, expression_row_upper_bound=4_553_407)
