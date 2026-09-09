"""Attacks on the byte-to-row raw-source proof.

Scope: verifies the integrity of this project's own provenance records, in this
repository. No third-party system, no network, no credentials and no security
control belonging to any system is involved.

The defect this replaces was label authentication. The previous
`prove_source_library` took `raw_source_row_values` plus a provenance mapping
from the caller, compared the caller's labels to the bound row, and summed the
caller's vector. A fabricated vector proved `source_library` as long as its sum
matched and its labels were right.

The centrepiece here is `test_a_fully_labelled_fabricated_row_cannot_prove_source_library`:
a fabricated row carrying the correct sum, the correct frozen source digest, the
correct cell and donor identity, the correct `expression_row`, the correct source
width and the correct `layers/UMIs` slot name must still fail, because none of its
values came out of authenticated bytes.

The suite builds a small synthetic H5AD shaped like the real asset, so it runs
without the 33 GB production file and never skips.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_raw_source_row_authority_v1 as rs  # noqa: E402

CELLS = 6
FEATURES = rs.SOURCE_FEATURE_COUNT

# (cell, donor, {column: count}) shaped like real op31 rows.
POPULATION = [
    ("CCACACTCAGGCCCTA-L8TX_210430_01_G04-1153814211", "H19.33.004",
     {7: 5, 11: 3, 20000: 40}),
    ("GATTCGATCATAGCAC-L8TX_210513_01_A10-1153814239", "H19.33.004",
     {3: 1, 36600: 9}),
    ("TATACCTTCCCATACC-L8TX_210430_01_G04-1153814211", "H19.33.004",
     {0: 100}),
    ("FOREIGN-CELL-1", "H20.33.999", {5: 7}),
    ("FOREIGN-CELL-2", "H20.33.999", {6: 8}),
    ("FOREIGN-CELL-3", "H20.33.999", {9: 2}),
]


def _write_h5ad(path: Path, *, population=POPULATION, features=FEATURES,
                encoding="csr_matrix", data_dtype="float64") -> Path:
    """A synthetic H5AD shaped exactly like the frozen asset.

    Real `layers/UMIs` is a CSR group with data, indices and indptr, an
    `encoding-type` of csr_matrix and a shape attribute, and its data is float64
    holding integral values. `obs` is indexed by `exp_component_name` with
    `Donor ID` stored as a categorical group.
    """
    import h5py
    import numpy as np

    data, indices, indptr = [], [], [0]
    for _cell, _donor, entries in population:
        for column in sorted(entries):
            indices.append(column)
            data.append(entries[column])
        indptr.append(len(data))

    with h5py.File(str(path), "w") as handle:
        layer = handle.create_group("layers").create_group("UMIs")
        layer.attrs["encoding-type"] = encoding
        layer.attrs["encoding-version"] = "0.1.0"
        layer.attrs["shape"] = np.asarray([len(population), features],
                                          dtype=np.int64)
        layer.create_dataset("data", data=np.asarray(data, dtype=data_dtype))
        layer.create_dataset("indices", data=np.asarray(indices, dtype=np.int32))
        layer.create_dataset("indptr", data=np.asarray(indptr, dtype=np.int64))

        obs = handle.create_group("obs")
        obs.attrs["_index"] = "exp_component_name"
        obs.create_dataset(
            "exp_component_name",
            data=np.asarray([c for c, _, _ in population],
                            dtype=h5py.string_dtype()))
        donors = sorted({d for _, d, _ in population})
        node = obs.create_group("Donor ID")
        node.create_dataset("categories",
                            data=np.asarray(donors, dtype=h5py.string_dtype()))
        node.create_dataset(
            "codes",
            data=np.asarray([donors.index(d) for _, d, _ in population],
                            dtype=np.int8))
        # A pathology column, present exactly as in the real asset, to make the
        # no-read guarantee meaningful rather than vacuous.
        obs.create_dataset("Braak", data=np.asarray([5] * len(population),
                                                    dtype=np.int64))
    return path


def _logical(rows):
    return {"rows": rows, "row_count": len(rows), "real_execution_ready": False}


def _row(index: int, *, library=None, cell=None, donor=None, expression_row=None):
    name, who, entries = POPULATION[index]
    return {
        "logical_index": 0,
        "canonical_cell_id": cell if cell is not None else name,
        "donor_id": donor if donor is not None else who,
        "expression_row": expression_row if expression_row is not None else index,
        "source_library": (library if library is not None
                           else sum(entries.values())),
        "block_key": "op31/block-00000",
        "row_index": 0,
        "meta_path": "op31/block-00000.meta.csv",
        "meta_sha256": "a" * 64,
        "counts_path": "op31/block-00000.counts.npz",
        "counts_sha256": "b" * 64,
        "selection_row": 10,
        "primary_row_weight": "8.06e-08",
    }


@pytest.fixture()
def asset(tmp_path) -> Path:
    return _write_h5ad(tmp_path / "mtg.h5ad")


@pytest.fixture()
def source(asset: Path):
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    handle = rs.open_authenticated_source(asset, expected_sha256=digest)
    yield handle
    handle.close()


# --- the defect this module exists to close ---------------------------------

def test_a_fully_labelled_fabricated_row_cannot_prove_source_library(
        source, asset: Path) -> None:
    """Every label correct, values fabricated. It must still fail.

    This is the attack the previous label-authenticating proof passed. The
    fabricated vector has the correct total, and the accompanying provenance
    names the correct frozen source digest, the correct `layers/UMIs` slot, the
    correct `expression_row`, the correct source width and the correct cell and
    donor identity.
    """
    _cell, _donor, entries = POPULATION[0]
    correct_total = sum(entries.values())
    fabricated = [0] * (FEATURES - 1) + [correct_total]
    assert sum(fabricated) == correct_total
    assert len(fabricated) == rs.SOURCE_FEATURE_COUNT

    provenance = {
        "source_sha256": rs.MTG_SOURCE_SHA256,
        "matrix_slot": rs.UMI_SLOT,
        "source_row_index": 0,
        "source_width": rs.SOURCE_FEATURE_COUNT,
        "canonical_cell_id": POPULATION[0][0],
        "donor_id": POPULATION[0][1],
    }

    # There is no parameter through which the vector can enter. That is the
    # structural property: not a check that could be skipped, but an absent door.
    with pytest.raises(TypeError):
        rs.prove_source_library_from_authenticated_source(
            source=source, logical=_logical([_row(0)]), logical_index=0,
            raw_source_row_values=fabricated,
            raw_source_provenance=provenance)

    # And an explicit refusal, so the removed parameter cannot quietly return.
    with pytest.raises(AssertionError) as excinfo:
        rs.refuse_caller_supplied_values(
            raw_source_row_values=fabricated, raw_source_provenance=provenance)
    assert rs.STOP_CALLER_VALUES in str(excinfo.value)


def test_the_proof_reports_that_no_caller_values_were_used(source) -> None:
    proof = rs.prove_source_library_from_authenticated_source(
        source=source, logical=_logical([_row(0)]), logical_index=0,
        expected_source_sha256=source.sha256)
    assert proof["caller_supplied_values"] is False
    assert proof["proof"] == "BYTE_TO_ROW_FROM_AUTHENTICATED_H5AD"
    assert proof["digest_bytes_read"] > 0


# --- the handle cannot be forged --------------------------------------------

def test_a_handle_cannot_be_constructed_without_authentication(asset: Path) -> None:
    with pytest.raises(AssertionError) as excinfo:
        rs.AuthenticatedSource(object(), path=asset, sha256="a" * 64,
                               bytes_read=1, handle=None)
    assert rs.STOP_HANDLE_FORGED in str(excinfo.value)


def test_a_look_alike_source_object_is_refused(source) -> None:
    """Otherwise label authentication returns through the handle."""

    class LookAlike:
        sha256 = rs.MTG_SOURCE_SHA256
        digest_bytes_read = 32_978_570_763
        path = "anything"

        def __init__(self, real):
            self.h5 = real.h5

    with pytest.raises(AssertionError) as excinfo:
        rs.prove_source_library_from_authenticated_source(
            source=LookAlike(source), logical=_logical([_row(0)]),
            logical_index=0, expected_source_sha256=rs.MTG_SOURCE_SHA256)
    assert rs.STOP_HANDLE_FORGED in str(excinfo.value)


def test_a_subclass_without_the_token_is_refused(source) -> None:
    genuine = source

    class Sneaky(rs.AuthenticatedSource):
        def __init__(self):
            self.sha256 = rs.MTG_SOURCE_SHA256
            self.digest_bytes_read = 1
            self.path = genuine.path
            self._h5 = genuine.h5

    with pytest.raises(AssertionError) as excinfo:
        rs.prove_source_library_from_authenticated_source(
            source=Sneaky(), logical=_logical([_row(0)]), logical_index=0,
            expected_source_sha256=rs.MTG_SOURCE_SHA256)
    assert rs.STOP_HANDLE_FORGED in str(excinfo.value)


# --- asset authentication ---------------------------------------------------

def test_a_wrong_asset_digest_stops(asset: Path) -> None:
    with pytest.raises(AssertionError) as excinfo:
        rs.open_authenticated_source(asset, expected_sha256="f" * 64)
    assert rs.STOP_SOURCE_DIGEST in str(excinfo.value)


def test_an_absent_asset_stops(tmp_path) -> None:
    with pytest.raises(AssertionError) as excinfo:
        rs.open_authenticated_source(tmp_path / "missing.h5ad",
                                     expected_sha256="f" * 64)
    assert rs.STOP_SOURCE_ABSENT in str(excinfo.value)


def test_the_whole_asset_is_digested(asset: Path, source) -> None:
    """A skipped or partial digest is visible in the recorded byte count."""
    assert source.digest_bytes_read == asset.stat().st_size


def test_a_proof_against_a_different_expected_digest_stops(source) -> None:
    """The handle's identity must equal what the proof expects."""
    with pytest.raises(AssertionError) as excinfo:
        rs.prove_source_library_from_authenticated_source(
            source=source, logical=_logical([_row(0)]), logical_index=0,
            expected_source_sha256="e" * 64)
    assert rs.STOP_SOURCE_DIGEST in str(excinfo.value)


# --- slot, geometry and row selection ---------------------------------------

def test_the_umi_slot_must_be_csr(tmp_path) -> None:
    path = _write_h5ad(tmp_path / "csc.h5ad", encoding="csc_matrix")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with rs.open_authenticated_source(path, expected_sha256=digest) as handle:
        with pytest.raises(AssertionError) as excinfo:
            rs.source_geometry(handle)
        assert rs.STOP_SLOT_ENCODING in str(excinfo.value)


def test_the_source_width_must_be_the_source_feature_space(tmp_path) -> None:
    """41,238 is the address space; 36,601 is the source feature space."""
    path = _write_h5ad(tmp_path / "narrow.h5ad", features=41_238)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with rs.open_authenticated_source(path, expected_sha256=digest) as handle:
        with pytest.raises(AssertionError) as excinfo:
            rs.read_raw_row(handle, 0)
        assert rs.STOP_SOURCE_SHAPE in str(excinfo.value)


def test_the_geometry_is_read_from_the_asset(source) -> None:
    rows, width = rs.source_geometry(source)
    assert rows == len(POPULATION)
    assert width == rs.SOURCE_FEATURE_COUNT


@pytest.mark.parametrize("bad_row", [-1, len(POPULATION), 10_000])
def test_a_row_outside_the_asset_stops(source, bad_row) -> None:
    with pytest.raises(AssertionError) as excinfo:
        rs.read_raw_row(source, bad_row)
    assert rs.STOP_ROW_RANGE in str(excinfo.value)


@pytest.mark.parametrize("index", [0, 1, 2])
def test_the_library_is_computed_from_the_authenticated_row(source, index) -> None:
    total, stored = rs.read_raw_row(source, index)
    assert total == sum(POPULATION[index][2].values())
    assert stored == len(POPULATION[index][2])


# --- row identity -----------------------------------------------------------

def test_the_source_row_identity_must_match_the_bound_cell(source) -> None:
    with pytest.raises(AssertionError) as excinfo:
        rs.prove_source_library_from_authenticated_source(
            source=source, logical=_logical([_row(0, cell="SOMEONE-ELSE")]),
            logical_index=0, expected_source_sha256=source.sha256)
    assert rs.STOP_ROW_IDENTITY in str(excinfo.value)


def test_the_source_row_identity_must_match_the_bound_donor(source) -> None:
    with pytest.raises(AssertionError) as excinfo:
        rs.prove_source_library_from_authenticated_source(
            source=source, logical=_logical([_row(0, donor="H20.33.999")]),
            logical_index=0, expected_source_sha256=source.sha256)
    assert rs.STOP_ROW_IDENTITY in str(excinfo.value)


def test_reading_the_wrong_expression_row_is_caught_by_identity(source) -> None:
    """A correct total read at the wrong row proves nothing.

    Row 3 belongs to a different donor, so pointing row 0's bound identity at it
    fails on identity before any total is compared.
    """
    with pytest.raises(AssertionError) as excinfo:
        rs.prove_source_library_from_authenticated_source(
            source=source, logical=_logical([_row(0, expression_row=3)]),
            logical_index=0, expected_source_sha256=source.sha256)
    assert rs.STOP_ROW_IDENTITY in str(excinfo.value)


def test_the_row_identity_reads_only_permitted_obs_fields(source) -> None:
    identity = rs.read_row_identity(source, 0)
    assert set(identity) == {"canonical_cell_id", "donor_id"}
    assert rs.assert_no_pathology_read() is True
    assert tuple(rs.PERMITTED_OBS_FIELDS) == ("exp_component_name", "Donor ID")


def test_widening_the_permitted_obs_fields_is_refused() -> None:
    """The asset's obs carries Braak, Thal and CERAD; none may be read."""
    original = rs.PERMITTED_OBS_FIELDS
    try:
        rs.PERMITTED_OBS_FIELDS = original + ("Braak",)
        with pytest.raises(AssertionError) as excinfo:
            rs.assert_no_pathology_read()
        assert rs.STOP_OBS_FIELD in str(excinfo.value)
    finally:
        rs.PERMITTED_OBS_FIELDS = original


# --- count semantics --------------------------------------------------------

@pytest.mark.parametrize("bad_entries,marker", [
    ({7: -5}, rs.STOP_COUNTS),
    ({7: 1.5}, rs.STOP_COUNTS),
])
def test_non_integral_or_negative_stored_counts_stop(tmp_path, bad_entries,
                                                     marker) -> None:
    population = [(POPULATION[0][0], POPULATION[0][1], bad_entries)]
    path = _write_h5ad(tmp_path / "bad.h5ad", population=population)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with rs.open_authenticated_source(path, expected_sha256=digest) as handle:
        with pytest.raises(AssertionError) as excinfo:
            rs.read_raw_row(handle, 0)
        assert marker in str(excinfo.value)


def test_integral_float64_counts_are_accepted(source) -> None:
    """The real asset stores UMIs as float64 with integral values."""
    total, _ = rs.read_raw_row(source, 0)
    assert isinstance(total, int)
    assert total == sum(POPULATION[0][2].values())


def test_a_row_with_no_stored_values_sums_to_zero(tmp_path) -> None:
    population = [(POPULATION[0][0], POPULATION[0][1], {})]
    path = _write_h5ad(tmp_path / "empty.h5ad", population=population)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with rs.open_authenticated_source(path, expected_sha256=digest) as handle:
        assert rs.read_raw_row(handle, 0) == (0, 0)


# --- the proven total must equal the bound value ----------------------------

def test_a_bound_library_that_disagrees_with_the_authenticated_row_stops(
        source) -> None:
    correct = sum(POPULATION[0][2].values())
    with pytest.raises(AssertionError) as excinfo:
        rs.prove_source_library_from_authenticated_source(
            source=source, logical=_logical([_row(0, library=correct + 1)]),
            logical_index=0, expected_source_sha256=source.sha256)
    assert rs.STOP_LIBRARY in str(excinfo.value)


@pytest.mark.parametrize("index", [0, 1, 2])
def test_a_genuine_row_proves_its_bound_library(source, index) -> None:
    proof = rs.prove_source_library_from_authenticated_source(
        source=source, logical=_logical([_row(index)]), logical_index=0,
        expected_source_sha256=source.sha256)
    assert proof["source_library"] == sum(POPULATION[index][2].values())
    assert proof["canonical_cell_id"] == POPULATION[index][0]
    assert proof["donor_id"] == POPULATION[index][1]
    assert proof["matrix_slot"] == "layers/UMIs"
    assert proof["real_execution_ready"] is False


# --- proof root -------------------------------------------------------------

def test_the_proof_root_is_deterministic_and_order_independent(source) -> None:
    proofs = [rs.prove_source_library_from_authenticated_source(
        source=source, logical=_logical([_row(i)]), logical_index=0,
        expected_source_sha256=source.sha256) for i in (0, 1, 2)]
    assert rs.raw_source_proof_root(proofs) == rs.raw_source_proof_root(
        list(reversed(proofs)))


def test_the_proof_root_moves_with_any_proven_field(source) -> None:
    proof = rs.prove_source_library_from_authenticated_source(
        source=source, logical=_logical([_row(0)]), logical_index=0,
        expected_source_sha256=source.sha256)
    baseline = rs.raw_source_proof_root([proof])
    for field, value in (("expression_row", 5), ("source_library", 999),
                         ("canonical_cell_id", "OTHER"), ("donor_id", "OTHER")):
        moved = dict(proof)
        moved[field] = value
        assert rs.raw_source_proof_root([moved]) != baseline


def test_the_typed_framing_refuses_a_float() -> None:
    with pytest.raises(AssertionError) as excinfo:
        rs._typed(1.5)
    assert rs.STOP_FIELD_SCHEMA in str(excinfo.value)


def test_the_frozen_asset_identity_is_the_verified_one() -> None:
    assert rs.MTG_SOURCE_SHA256 == (
        "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79")
    assert rs.MTG_SOURCE_CELLS == 1_178_694
    assert rs.SOURCE_FEATURE_COUNT == 36_601
    assert rs.UMI_SLOT == "layers/UMIs"
