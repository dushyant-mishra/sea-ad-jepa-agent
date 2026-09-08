"""R2 red cases for the four remaining B2 execution-authority defects.

Scope: this module verifies the integrity of this project's own data-provenance
records, in this repository. No third-party system, no network, no credentials,
no cryptanalysis, and no security control belonging to any system is involved.
The only check being probed is our own SHA-256 comparison and our own coordinate
bookkeeping. See docs/agent/T0_LANE_SECURITY_SCOPE.md.

These four cases are written to FAIL against head 6c6d841e. Each one reproduces a
defect an external review reported, so that the eventual repair is known to
discriminate rather than merely to look plausible. The defects:

1. The frozen complete Phase2 manifest cannot be consumed. It is the whole
   8,915-block, 42-operator manifest whose first row is operator 0, so
   authenticating it and then requiring every row to be operator 31 stops on row
   one. Passing a pre-filtered manifest avoids the stop but then the bytes cannot
   carry the frozen complete-manifest digest. The contract as written is
   internally impossible.

2. `prove_source_library` does not authenticate anything. It requires three
   provenance keys to be present, never verifies `source_sha256`, and never
   requires `source_row_index` to equal the bound `expression_row`. A fabricated
   vector with an arbitrary digest string proves the value as long as its sum
   matches.

3. `expression_row` is the row in the ORIGINAL H5 source matrix; `row_index` is
   the row within the materialized `block-*.counts.npz` payload. They are
   different coordinates. Only the former has a verifier, so nothing checks which
   row was actually selected from the materialized block.

4. `assert_plan_restores_logical` checks entry count, that the logical indices
   form a permutation, and that the carried logical-root string matches. It never
   compares an entry's `block_key`, `row_index`, `counts_path` or `counts_sha256`
   against the logical row its own `logical_index` names, so a plan entry's
   physical location can be changed while every check still passes.
"""

from __future__ import annotations

import csv
import hashlib
import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_v20_row_count_authority_v1 as rc  # noqa: E402

MATRIX_ID = "sea_ad_mtg_rna_final_2026"
OPERATOR = 31
FEATURE_AUTHORITY_ROOT = "538b73b8414f47c70507cb0c8b46a6d4787e019c49056e07d6b0238382cf99b8"

MEMBERSHIP_COLUMNS = ["source", "matrix_id", "operator_index", "local_row", "donor_id",
                      "partition", "cell_id", "native_class", "broad_class", "stable_key"]
META_COLUMNS = ["selection_row", "canonical_cell_id", "donor_id", "expression_row",
                "primary_row_weight", "source_library"]
MANIFEST_COLUMNS = ["block_key", "source", "operator_index", "matrix_id", "rows", "nnz",
                    "counts_path", "counts_sha256", "meta_path", "meta_sha256"]


def _csv(columns, rows) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def _membership(cells) -> bytes:
    rows = []
    for index, (cell, donor) in enumerate(cells):
        rows.append(["SEA_AD", MATRIX_ID, OPERATOR, index, donor, "reader_fit", cell,
                     "Immune", "Non-neuronal and Non-neural", 1000 + index])
    return _csv(MEMBERSHIP_COLUMNS, rows)


def _meta(entries) -> bytes:
    return _csv(META_COLUMNS,
                [[s, c, d, e, "8.06e-08", lib] for s, c, d, e, lib in entries])


class MultiOperatorWorld:
    """A population in operator 31, inside a manifest that spans four operators.

    This is the shape of the real frozen manifest: 8,915 blocks across 42
    operators, whose first row is operator 0 (HVS). The op31 rows are the ones
    T0 needs, and they must be selected from within the authenticated complete
    bytes rather than by authenticating a narrower file.
    """

    def __init__(self) -> None:
        self.membership = _membership([("C1", "D1"), ("C2", "D1"), ("C3", "D2")])
        self.op31_blocks = {
            "op31/block-00000": _meta([(10, "C1", "D1", 100, 9470),
                                       (11, "X1", "D9", 101, 5000)]),
            "op31/block-00001": _meta([(20, "C2", "D1", 200, 8123)]),
            "op31/block-00002": _meta([(30, "C3", "D2", 300, 7777)]),
        }
        # Foreign-operator blocks that the complete manifest necessarily carries.
        self.foreign_blocks = {
            "op00/block-00000": ("HVS", 0, "HVS::19cd530b-622c-4bd8-b738-dbf169412cb0"),
            "op30/block-00000": ("SEA_AD", 30, "sea_ad_mec_rna_final_2026"),
            "op32/block-00000": ("SEA_AD", 32, "sea_ad_pfc_rna_final_2026"),
        }
        self.counts = {k: ("counts-%s" % k).encode("utf-8") for k in self.op31_blocks}

    def _row(self, key, source, operator, matrix, meta_blob, counts_blob):
        return [key, source, operator, matrix,
                len(list(csv.DictReader(io.StringIO(meta_blob.decode())))), 999,
                "%s.counts.npz" % key, hashlib.sha256(counts_blob).hexdigest(),
                "%s.meta.csv" % key, hashlib.sha256(meta_blob).hexdigest()]

    def complete_manifest(self) -> bytes:
        """The whole manifest, operator 0 first, exactly like the frozen one."""
        rows = []
        foreign_meta = _meta([(1, "F1", "DF", 1, 111)])
        foreign_counts = b"counts-foreign"
        for key in sorted(self.foreign_blocks):
            source, operator, matrix = self.foreign_blocks[key]
            if operator > OPERATOR:
                continue
            rows.append(self._row(key, source, operator, matrix,
                                  foreign_meta, foreign_counts))
        for key in sorted(self.op31_blocks):
            rows.append(self._row(key, "SEA_AD", OPERATOR, MATRIX_ID,
                                  self.op31_blocks[key], self.counts[key]))
        for key in sorted(self.foreign_blocks):
            source, operator, matrix = self.foreign_blocks[key]
            if operator <= OPERATOR:
                continue
            rows.append(self._row(key, source, operator, matrix,
                                  foreign_meta, foreign_counts))
        return _csv(MANIFEST_COLUMNS, rows)

    def op31_only_manifest(self) -> bytes:
        rows = [self._row(key, "SEA_AD", OPERATOR, MATRIX_ID,
                          self.op31_blocks[key], self.counts[key])
                for key in sorted(self.op31_blocks)]
        return _csv(MANIFEST_COLUMNS, rows)

    def meta_by_path(self) -> dict[str, bytes]:
        return {"%s.meta.csv" % k: v for k, v in self.op31_blocks.items()}


@pytest.fixture()
def world() -> MultiOperatorWorld:
    return MultiOperatorWorld()


def _closure_from(manifest: bytes, world: MultiOperatorWorld, **overrides):
    kwargs = dict(
        membership_bytes=world.membership,
        expected_membership_sha256=hashlib.sha256(world.membership).hexdigest(),
        block_manifest_bytes=manifest,
        expected_block_manifest_sha256=hashlib.sha256(manifest).hexdigest(),
        meta_bytes_by_path=world.meta_by_path(),
        operator_index=OPERATOR, matrix_id=MATRIX_ID)
    kwargs.update(overrides)
    return rc.build_population_closure(**kwargs)


def _logical(world: MultiOperatorWorld, closure):
    return rc.build_logical_row_authority(
        closure=closure, membership_bytes=world.membership,
        feature_authority_root_sha256=FEATURE_AUTHORITY_ROOT)


# ---------------------------------------------------------------------------
# RED 1 — the complete manifest must be consumable.
# ---------------------------------------------------------------------------

def test_the_authenticated_complete_manifest_is_accepted_and_filtered_internally(
        world: MultiOperatorWorld) -> None:
    """The frozen manifest spans 42 operators; op31 must be selected inside it.

    Requiring every row of the authenticated complete manifest to be operator 31
    makes the production contract impossible: the real manifest's first row is
    operator 0. Selection has to happen within the authenticated bytes.
    """
    manifest = world.complete_manifest()
    operators = {int(r["operator_index"])
                 for r in csv.DictReader(io.StringIO(manifest.decode("utf-8")))}
    assert operators == {0, 30, 31, 32}, "fixture must span several operators"

    closure = _closure_from(manifest, world)
    # Only the operator-31 blocks may be scanned, and all of them must be.
    assert closure["blocks_scanned"] == len(world.op31_blocks)
    assert closure["population_size"] == 3


def test_a_prefiltered_manifest_cannot_stand_in_for_the_complete_one(
        world: MultiOperatorWorld) -> None:
    """Narrowing the file first means the frozen digest describes other bytes.

    The complete-manifest digest and a filtered manifest's digest cannot both be
    the authority for the same run, so declaring the former while supplying the
    latter must be refused.
    """
    filtered = world.op31_only_manifest()
    with pytest.raises(AssertionError):
        _closure_from(
            filtered, world,
            expected_block_manifest_sha256=hashlib.sha256(
                world.complete_manifest()).hexdigest())


def test_the_complete_manifest_subset_geometry_is_asserted(
        world: MultiOperatorWorld) -> None:
    """A silently narrowed selection must not pass.

    If the manifest loses op31 blocks, the closure must refuse rather than close a
    smaller population, so the expected subset size has to be part of the
    contract.
    """
    reduced = dict(world.op31_blocks)
    reduced.pop("op31/block-00002")
    world.op31_blocks = reduced
    with pytest.raises(AssertionError):
        _closure_from(world.complete_manifest(), world,
                      expected_op31_block_count=3)


# ---------------------------------------------------------------------------
# RED 2 — source_library must be proven from an AUTHENTICATED raw source row.
# ---------------------------------------------------------------------------

def test_a_fabricated_raw_row_with_a_matching_sum_does_not_prove_source_library(
        world: MultiOperatorWorld) -> None:
    """Carrying a `source_sha256` string is not authentication.

    The bound value for C1 is 9,470. A vector of zeros with a single 9,470 sums
    correctly, and its provenance dictionary names a digest that was never
    checked against anything. Proof must require the digest to match the frozen
    MTG source asset.
    """
    logical = _logical(world, _closure_from(world.complete_manifest(), world))
    fabricated = [0] * 1999 + [9470]
    with pytest.raises(AssertionError):
        rc.prove_source_library(
            logical=logical, logical_index=0,
            raw_source_row_values=fabricated,
            raw_source_provenance={
                "source_sha256": "e" * 64,          # never verified
                "source_row_index": 4,              # not the bound expression_row
                "source_width": len(fabricated),
            },
            expected_source_sha256=(
                "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79"),
        )


def test_the_proving_row_index_must_equal_the_bound_expression_row(
        world: MultiOperatorWorld) -> None:
    """A correct sum read from the wrong source row proves nothing."""
    logical = _logical(world, _closure_from(world.complete_manifest(), world))
    bound = logical["rows"][0]["expression_row"]
    values = [0] * 1999 + [logical["rows"][0]["source_library"]]
    with pytest.raises(AssertionError):
        rc.prove_source_library(
            logical=logical, logical_index=0,
            raw_source_row_values=values,
            raw_source_provenance={
                "source_sha256": (
                    "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79"),
                "source_row_index": bound + 1,
                "source_width": len(values),
                "canonical_cell_id": "C1",
                "donor_id": "D1",
                "matrix_slot": "layers/UMIs",
            },
            expected_source_sha256=(
                "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79"),
        )


def test_the_proving_row_identity_must_match_the_bound_cell_and_donor(
        world: MultiOperatorWorld) -> None:
    """The historical materializer checks cell and donor at the source row."""
    logical = _logical(world, _closure_from(world.complete_manifest(), world))
    row = logical["rows"][0]
    values = [0] * 1999 + [row["source_library"]]
    with pytest.raises(AssertionError):
        rc.prove_source_library(
            logical=logical, logical_index=0,
            raw_source_row_values=values,
            raw_source_provenance={
                "source_sha256": (
                    "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79"),
                "source_row_index": row["expression_row"],
                "source_width": len(values),
                "canonical_cell_id": "SOMEONE_ELSE",
                "donor_id": row["donor_id"],
                "matrix_slot": "layers/UMIs",
            },
            expected_source_sha256=(
                "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79"),
        )


def test_the_matrix_slot_must_be_the_raw_umi_layer(
        world: MultiOperatorWorld) -> None:
    """Proving from a normalised slot would not be a raw-count proof."""
    logical = _logical(world, _closure_from(world.complete_manifest(), world))
    row = logical["rows"][0]
    values = [0] * 1999 + [row["source_library"]]
    with pytest.raises(AssertionError):
        rc.prove_source_library(
            logical=logical, logical_index=0,
            raw_source_row_values=values,
            raw_source_provenance={
                "source_sha256": (
                    "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79"),
                "source_row_index": row["expression_row"],
                "source_width": len(values),
                "canonical_cell_id": row["canonical_cell_id"],
                "donor_id": row["donor_id"],
                "matrix_slot": "layers/lognorm",
            },
            expected_source_sha256=(
                "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79"),
        )


# ---------------------------------------------------------------------------
# RED 3 — expression_row and row_index are different coordinates.
# ---------------------------------------------------------------------------

def test_the_materialized_block_row_is_verified_by_row_index(
        world: MultiOperatorWorld) -> None:
    """Selecting a row from `block-*.counts.npz` is a row_index operation.

    The Phase2 producer enumerates `local` within the block payload while
    `expression_row` addresses the original H5 matrix. Verifying the block
    selection against `expression_row` checks the wrong coordinate, so a verifier
    bound to `row_index` has to exist.
    """
    logical = _logical(world, _closure_from(world.complete_manifest(), world))
    row = logical["rows"][0]
    assert row["row_index"] != row["expression_row"], (
        "fixture must keep the two coordinates distinct")
    assert rc.verify_selected_block_row(
        logical=logical, logical_index=0,
        selected_row_index=row["row_index"],
        row_values=[0] * rc.ADDRESS_SPACE_SIZE,
    ) is True


def test_passing_the_h5_source_row_as_the_block_row_is_refused(
        world: MultiOperatorWorld) -> None:
    logical = _logical(world, _closure_from(world.complete_manifest(), world))
    row = logical["rows"][0]
    with pytest.raises(AssertionError):
        rc.verify_selected_block_row(
            logical=logical, logical_index=0,
            selected_row_index=row["expression_row"],
            row_values=[0] * rc.ADDRESS_SPACE_SIZE,
        )


def test_passing_the_block_row_as_the_h5_source_row_is_refused(
        world: MultiOperatorWorld) -> None:
    """The reverse conflation must fail too, or the two checks are substitutable."""
    logical = _logical(world, _closure_from(world.complete_manifest(), world))
    row = logical["rows"][0]
    with pytest.raises(AssertionError):
        rc.verify_selected_row(
            logical=logical, logical_index=0,
            row_values=[0] * rc.ADDRESS_SPACE_SIZE,
            selected_expression_row=row["row_index"],
        )


# ---------------------------------------------------------------------------
# RED 4 — the physical plan must actually restore the logical rows.
# ---------------------------------------------------------------------------

def test_a_relocated_plan_entry_is_caught_by_external_verification(
        world: MultiOperatorWorld) -> None:
    """Preserving the indices and the carried root is not restoration.

    Every logical index still forms a permutation and the carried logical-root
    string is untouched, so the existing restoration check passes while the entry
    points at a different block and row. Restoration has to compare each entry
    against the logical row its own `logical_index` names.
    """
    logical = _logical(world, _closure_from(world.complete_manifest(), world))
    plan = rc.build_physical_read_plan(logical=logical)

    tampered = dict(plan)
    entries = [dict(entry) for entry in plan["plan"]]
    victim, donor = entries[0], entries[-1]
    assert victim["block_key"] != donor["block_key"]
    victim["block_key"] = donor["block_key"]
    victim["row_index"] = donor["row_index"]
    victim["counts_path"] = donor["counts_path"]
    victim["counts_sha256"] = donor["counts_sha256"]
    tampered["plan"] = entries

    # The indices are still a permutation and the carried root is unchanged.
    assert sorted(e["logical_index"] for e in entries) == list(range(len(entries)))
    assert tampered["logical_row_authority_root_sha256"] == \
        logical["logical_row_authority_root_sha256"]

    with pytest.raises(AssertionError):
        rc.assert_plan_restores_logical(
            plan=tampered,
            expected_logical_root_sha256=logical["logical_row_authority_root_sha256"],
            logical=logical,
        )


def test_the_physical_plan_root_is_externally_verified(
        world: MultiOperatorWorld) -> None:
    """A stored root that nothing compares against is not a verification."""
    logical = _logical(world, _closure_from(world.complete_manifest(), world))
    plan = rc.build_physical_read_plan(logical=logical)
    assert rc.assert_physical_plan_lawful(
        plan=plan,
        expected_physical_root_sha256=plan["physical_read_plan_root_sha256"],
        expected_logical_root_sha256=logical["logical_row_authority_root_sha256"],
        logical=logical,
    ) is True
    with pytest.raises(AssertionError):
        rc.assert_physical_plan_lawful(
            plan=plan,
            expected_physical_root_sha256="f" * 64,
            expected_logical_root_sha256=logical["logical_row_authority_root_sha256"],
            logical=logical,
        )


def test_the_population_closure_root_is_externally_verified(
        world: MultiOperatorWorld) -> None:
    """The third root needs its own external verifier, like the logical one."""
    closure = _closure_from(world.complete_manifest(), world)
    assert rc.assert_closure_lawful(
        closure=closure,
        expected_closure_root_sha256=closure["population_closure_root_sha256"],
        expected_membership_sha256=hashlib.sha256(world.membership).hexdigest(),
        expected_block_manifest_sha256=hashlib.sha256(
            world.complete_manifest()).hexdigest(),
    ) is True
    with pytest.raises(AssertionError):
        rc.assert_closure_lawful(
            closure=closure,
            expected_closure_root_sha256="f" * 64,
            expected_membership_sha256=hashlib.sha256(world.membership).hexdigest(),
            expected_block_manifest_sha256=hashlib.sha256(
                world.complete_manifest()).hexdigest(),
        )
