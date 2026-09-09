"""Independent attacks on the population-wide raw MTG source authority."""

from __future__ import annotations

import hashlib
import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_raw_source_row_authority_v1 as rs  # noqa: E402
import t0_v20_row_count_authority_v1 as rc  # noqa: E402


POPULATION = [
    ("C0", "D0", {7: 5, 11: 3}),
    ("C1", "D1", {3: 1, 36_600: 9}),
    ("C2", "D1", {0: 100}),
]


def _write_h5ad(path: Path, *, population=POPULATION,
                features=rs.SOURCE_FEATURE_COUNT,
                encoding="csr_matrix") -> Path:
    import h5py
    import numpy as np

    data, indices, indptr = [], [], [0]
    for _cell, _donor, entries in population:
        for column in sorted(entries):
            indices.append(column)
            data.append(entries[column])
        indptr.append(len(data))

    with h5py.File(path, "w") as handle:
        layer = handle.create_group("layers").create_group("UMIs")
        layer.attrs["encoding-type"] = encoding
        layer.attrs["shape"] = np.asarray(
            [len(population), features], dtype=np.int64)
        layer.create_dataset("data", data=np.asarray(data, dtype=np.float64))
        layer.create_dataset("indices", data=np.asarray(indices, dtype=np.int32))
        layer.create_dataset("indptr", data=np.asarray(indptr, dtype=np.int64))

        obs = handle.create_group("obs")
        obs.attrs["_index"] = "exp_component_name"
        obs.create_dataset(
            "exp_component_name",
            data=np.asarray([c for c, _, _ in population],
                            dtype=h5py.string_dtype()))
        donors = sorted({d for _, d, _ in population})
        donor = obs.create_group("Donor ID")
        donor.create_dataset(
            "categories", data=np.asarray(donors, dtype=h5py.string_dtype()))
        donor.create_dataset(
            "codes", data=np.asarray(
                [donors.index(d) for _, d, _ in population], dtype=np.int8))
        # Deliberately present: the proof must not read it.
        obs.create_dataset("Braak", data=np.asarray([5] * len(population)))
    return path


def _logical(*, library_delta: int = 0, cell_override=None, donor_override=None):
    feature_root = "4" * 64
    closure_root = "1" * 64
    rows = []
    for index, (cell, donor, entries) in enumerate(POPULATION):
        rows.append({
            "logical_index": index,
            "canonical_cell_id": (
                cell_override if index == 0 and cell_override is not None else cell),
            "donor_id": (
                donor_override if index == 0 and donor_override is not None else donor),
            "block_key": "op31/block-%05d" % index,
            "row_index": 0,
            "selection_row": index,
            "expression_row": index,
            "primary_row_weight": "1",
            "source_library": sum(entries.values()) + (
                library_delta if index == 0 else 0),
            "meta_path": "op31/block-%05d.meta.csv" % index,
            "meta_sha256": ("%x" % (10 + index)) * 64,
            "counts_path": "op31/block-%05d.counts.npz" % index,
            "counts_sha256": ("%x" % (13 + index)) * 64,
        })
    # Trim synthetic hex strings to 64 characters.
    for row in rows:
        row["meta_sha256"] = row["meta_sha256"][:64]
        row["counts_sha256"] = row["counts_sha256"][:64]
    logical = {
        "rows": rows,
        "row_count": len(rows),
        "feature_authority_root_sha256": feature_root,
        "population_closure_root_sha256": closure_root,
        "logical_row_authority_root_sha256": None,
        "real_execution_ready": False,
    }
    logical["logical_row_authority_root_sha256"] = rc._logical_root(
        rows, feature_root, closure_root)
    return logical


def _build_fixture(path: Path, logical=None):
    logical = logical or _logical()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    authority = rs._build_population_raw_source_authority_fixture(
        source_path=path,
        logical=logical,
        expected_logical_root_sha256=logical[
            "logical_row_authority_root_sha256"],
        expected_population_closure_root_sha256=logical[
            "population_closure_root_sha256"],
        expected_feature_authority_root_sha256=logical[
            "feature_authority_root_sha256"],
        expected_source_sha256=digest,
        expected_source_bytes=path.stat().st_size,
        expected_source_cells=len(POPULATION),
        expected_source_features=rs.SOURCE_FEATURE_COUNT,
        expected_logical_rows=len(POPULATION),
        chunk_bytes=1024,
    )
    return logical, digest, authority


def test_population_proof_covers_every_logical_row(tmp_path: Path) -> None:
    path = _write_h5ad(tmp_path / "mtg.h5ad")
    logical, digest, authority = _build_fixture(path)
    assert authority["proof_count"] == len(logical["rows"])
    assert [p["logical_index"] for p in authority["proofs"]] == [0, 1, 2]
    assert authority["source_sha256"] == digest
    assert authority["digest_bytes_read"] == path.stat().st_size
    assert authority["caller_supplied_values"] is False
    assert authority["pathology_values_read"] is False
    assert authority["real_execution_ready"] is False


def test_source_library_is_computed_from_same_authenticated_h5_rows(
        tmp_path: Path) -> None:
    path = _write_h5ad(tmp_path / "mtg.h5ad")
    _logical_obj, _digest, authority = _build_fixture(path)
    assert [p["source_library"] for p in authority["proofs"]] == [
        sum(entries.values()) for _, _, entries in POPULATION]


def test_wrong_bound_source_library_stops(tmp_path: Path) -> None:
    path = _write_h5ad(tmp_path / "mtg.h5ad")
    with pytest.raises(AssertionError) as excinfo:
        _build_fixture(path, _logical(library_delta=1))
    assert rs.STOP_LIBRARY in str(excinfo.value)


def test_wrong_bound_cell_identity_stops(tmp_path: Path) -> None:
    path = _write_h5ad(tmp_path / "mtg.h5ad")
    with pytest.raises(AssertionError) as excinfo:
        _build_fixture(path, _logical(cell_override="OTHER"))
    assert rs.STOP_ROW_IDENTITY in str(excinfo.value)


def test_wrong_bound_donor_identity_stops(tmp_path: Path) -> None:
    path = _write_h5ad(tmp_path / "mtg.h5ad")
    with pytest.raises(AssertionError) as excinfo:
        _build_fixture(path, _logical(donor_override="OTHER"))
    assert rs.STOP_ROW_IDENTITY in str(excinfo.value)


def test_wrong_source_digest_stops(tmp_path: Path) -> None:
    path = _write_h5ad(tmp_path / "mtg.h5ad")
    logical = _logical()
    with pytest.raises(AssertionError) as excinfo:
        rs._build_population_raw_source_authority_fixture(
            source_path=path, logical=logical,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_population_closure_root_sha256=logical[
                "population_closure_root_sha256"],
            expected_feature_authority_root_sha256=logical[
                "feature_authority_root_sha256"],
            expected_source_sha256="f" * 64,
            expected_source_bytes=path.stat().st_size,
            expected_source_cells=len(POPULATION),
            expected_source_features=rs.SOURCE_FEATURE_COUNT,
            expected_logical_rows=len(POPULATION))
    assert rs.STOP_SOURCE_DIGEST in str(excinfo.value)


def test_wrong_source_geometry_stops(tmp_path: Path) -> None:
    path = _write_h5ad(
        tmp_path / "mtg.h5ad", features=rs.SOURCE_FEATURE_COUNT - 1)
    logical = _logical()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(AssertionError) as excinfo:
        rs._build_population_raw_source_authority_fixture(
            source_path=path, logical=logical,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_population_closure_root_sha256=logical[
                "population_closure_root_sha256"],
            expected_feature_authority_root_sha256=logical[
                "feature_authority_root_sha256"],
            expected_source_sha256=digest,
            expected_source_bytes=path.stat().st_size,
            expected_source_cells=len(POPULATION),
            expected_source_features=rs.SOURCE_FEATURE_COUNT,
            expected_logical_rows=len(POPULATION))
    assert rs.STOP_SOURCE_SHAPE in str(excinfo.value)


def test_non_csr_umi_layer_stops(tmp_path: Path) -> None:
    path = _write_h5ad(tmp_path / "mtg.h5ad", encoding="csc_matrix")
    logical = _logical()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(AssertionError) as excinfo:
        rs._build_population_raw_source_authority_fixture(
            source_path=path, logical=logical,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_population_closure_root_sha256=logical[
                "population_closure_root_sha256"],
            expected_feature_authority_root_sha256=logical[
                "feature_authority_root_sha256"],
            expected_source_sha256=digest,
            expected_source_bytes=path.stat().st_size,
            expected_source_cells=len(POPULATION),
            expected_source_features=rs.SOURCE_FEATURE_COUNT,
            expected_logical_rows=len(POPULATION))
    assert rs.STOP_SLOT_ENCODING in str(excinfo.value)


def test_public_production_builder_refuses_a_partial_population_before_io(
        tmp_path: Path) -> None:
    path = _write_h5ad(tmp_path / "mtg.h5ad")
    logical = _logical()
    with pytest.raises(AssertionError) as excinfo:
        rs.build_population_raw_source_authority(
            source_path=path, logical=logical,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_population_closure_root_sha256=logical[
                "population_closure_root_sha256"],
            expected_feature_authority_root_sha256=logical[
                "feature_authority_root_sha256"],
            expected_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    assert rs.STOP_PROOF_COUNT in str(excinfo.value)


def test_proof_verifier_establishes_stored_recomputed_expected(
        tmp_path: Path) -> None:
    path = _write_h5ad(tmp_path / "mtg.h5ad")
    logical, digest, authority = _build_fixture(path)
    result = rs.assert_population_raw_source_authority_lawful(
        authority=authority, logical=logical,
        expected_raw_source_proof_root_sha256=authority[
            "raw_source_proof_root_sha256"],
        expected_logical_root_sha256=logical[
            "logical_row_authority_root_sha256"],
        expected_population_closure_root_sha256=logical[
            "population_closure_root_sha256"],
        expected_feature_authority_root_sha256=logical[
            "feature_authority_root_sha256"],
        expected_source_sha256=digest,
        expected_source_bytes=path.stat().st_size,
        expected_source_cells=len(POPULATION),
        expected_source_features=rs.SOURCE_FEATURE_COUNT,
        expected_proof_count=len(POPULATION))
    assert result["proof_count"] == len(POPULATION)


def test_mutating_any_proven_library_moves_or_invalidates_root(
        tmp_path: Path) -> None:
    path = _write_h5ad(tmp_path / "mtg.h5ad")
    logical, digest, authority = _build_fixture(path)
    moved = dict(authority)
    moved["proofs"] = [dict(p) for p in authority["proofs"]]
    moved["proofs"][0]["source_library"] += 1
    with pytest.raises(AssertionError):
        rs.assert_population_raw_source_authority_lawful(
            authority=moved, logical=logical,
            expected_raw_source_proof_root_sha256=authority[
                "raw_source_proof_root_sha256"],
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_population_closure_root_sha256=logical[
                "population_closure_root_sha256"],
            expected_feature_authority_root_sha256=logical[
                "feature_authority_root_sha256"],
            expected_source_sha256=digest,
            expected_source_bytes=path.stat().st_size,
            expected_source_cells=len(POPULATION),
            expected_source_features=rs.SOURCE_FEATURE_COUNT,
            expected_proof_count=len(POPULATION))


def test_proof_root_binds_logical_root(tmp_path: Path) -> None:
    path = _write_h5ad(tmp_path / "mtg.h5ad")
    _logical_obj, _digest, authority = _build_fixture(path)
    moved = dict(authority)
    moved["logical_row_authority_root_sha256"] = "f" * 64
    assert rs._proof_root(moved) != authority["raw_source_proof_root_sha256"]


def test_pathology_field_is_present_but_not_permitted(tmp_path: Path) -> None:
    path = _write_h5ad(tmp_path / "mtg.h5ad")
    _build_fixture(path)
    assert rs.PERMITTED_OBS_FIELDS == ("exp_component_name", "Donor ID")
    assert rs.assert_no_pathology_read() is True


def test_widening_permitted_obs_fields_stops() -> None:
    original = rs.PERMITTED_OBS_FIELDS
    try:
        rs.PERMITTED_OBS_FIELDS = original + ("Braak",)
        with pytest.raises(AssertionError) as excinfo:
            rs.assert_no_pathology_read()
        assert rs.STOP_OBS_FIELD in str(excinfo.value)
    finally:
        rs.PERMITTED_OBS_FIELDS = original


def test_production_api_has_no_handle_or_value_vector_parameters() -> None:
    sig = inspect.signature(rs.build_population_raw_source_authority)
    assert "source" not in sig.parameters
    assert "raw_source_row_values" not in sig.parameters
    assert "raw_source_provenance" not in sig.parameters
    assert not hasattr(rs, "AuthenticatedSource")
    assert not hasattr(rs, "_HANDLE_TOKEN")
    assert not hasattr(rs, "open_authenticated_source")
    assert not hasattr(rs, "prove_source_library_from_authenticated_source")


def test_hash_and_hdf5_use_the_same_open_file_object() -> None:
    source = inspect.getsource(rs._build_population_raw_source_authority)
    assert 'with open(asset, "rb") as stream' in source
    assert 'h5py.File(stream, "r")' in source
    assert 'h5py.File(str(asset)' not in source
    assert 'h5py.File(asset' not in source


def test_caller_supplied_values_are_explicitly_refused() -> None:
    with pytest.raises(AssertionError) as excinfo:
        rs.refuse_caller_supplied_values(
            raw_source_row_values=[7], raw_source_provenance={"x": 1})
    assert rs.STOP_CALLER_VALUES in str(excinfo.value)


def test_frozen_real_asset_identity_and_geometry_are_unchanged() -> None:
    assert rs.MTG_SOURCE_SHA256 == (
        "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79")
    assert rs.MTG_SOURCE_BYTES == 32_978_570_763
    assert rs.MTG_SOURCE_CELLS == 1_178_694
    assert rs.SOURCE_FEATURE_COUNT == 36_601
    assert rs.PRODUCTION_LOGICAL_ROWS == 20_804
    assert rs.UMI_SLOT == "layers/UMIs"
