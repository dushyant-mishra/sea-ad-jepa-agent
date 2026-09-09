"""Adversarial tests for dataset-bound technical completeness."""

from __future__ import annotations

import hashlib
import inspect
import io
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_raw_source_row_authority_v1 as raw  # noqa: E402
import t0_technical_completeness_authority_v1 as tc  # noqa: E402
import t0_v20_feature_projection_authority_v1 as fp  # noqa: E402
import t0_v20_row_count_authority_v1 as rc  # noqa: E402


MATRIX_ID = "sea_ad_mtg_rna_final_2026"
MEMBERSHIP_SHA = "a" * 64
MANIFEST_SHA = "b" * 64
CODE_SHA = "d" * 64


def _csr_npz(rows: int, entries) -> bytes:
    import numpy as np

    by_row = [[] for _ in range(rows)]
    for row, column, value in entries:
        by_row[int(row)].append((int(column), int(value)))
    data, indices, indptr = [], [], [0]
    for record in by_row:
        for column, value in record:
            indices.append(column)
            data.append(value)
        indptr.append(len(data))
    buffer = io.BytesIO()
    np.savez(
        buffer,
        data=np.asarray(data, dtype=np.int32),
        indices=np.asarray(indices, dtype=np.int32),
        indptr=np.asarray(indptr, dtype=np.int32),
        shape=np.asarray([rows, 41_238], dtype=np.int32),
        format=np.array(b"csr"),
    )
    return buffer.getvalue()


def _feature_authority(count: int = tc.SCALAR_FEATURES):
    projection = [{
        "split_row_index": index,
        "molecular_address_id": "A%05d" % index,
        "molecular_address_index": index,
        "feature_role": "SCORING",
    } for index in range(count)]
    built = {
        "schema": fp.SCHEMA,
        "namespace": fp.NAMESPACE,
        "matrix_id": MATRIX_ID,
        "address_space_size": 41_238,
        "projection": projection,
        "projected_feature_count": count,
        "role_counts": {"SCORING": count},
        "projection_root_sha256": fp.projection_root(projection),
        "ordering": fp.ORDERING_CONTRACT,
        "source_feature_index_used": False,
        "real_execution_ready": False,
        "authority_binding": {
            "split_member_path": "fixture/split.csv",
            "split_sha256": "1" * 64,
            "registry_sha256": "2" * 64,
            "support_gzip_sha256": "3" * 64,
            "support_plain_sha256": "4" * 64,
            "stage81a2r_pin": "fixture-pin",
        },
    }
    built["feature_authority_root_sha256"] = fp.feature_authority_root(built)
    return built


def _fixture(*, feature_count: int = tc.SCALAR_FEATURES,
             rows_delta: int = 0, nnz_delta: int = 0,
             duplicate_column: bool = False):
    feature = _feature_authority(feature_count)
    feature_root = feature["feature_authority_root_sha256"]

    block0_entries = [
        (0, 40_000, 5),       # C4: outside B1
        (1, 1, 2), (1, 35_075, 3),  # C2: two inside
    ]
    block1_entries = [
        (0, 0, 3), (0, 40_000, 7),  # C1: one inside
        (1, 2, 4), (1, 7, 6), (1, 9, 1),  # C3: three inside
    ]
    if duplicate_column:
        block1_entries.append((1, 7, 2))

    payloads = {
        "op31/block-00000.counts.npz": _csr_npz(2, block0_entries),
        "op31/block-00001.counts.npz": _csr_npz(2, block1_entries),
    }
    digests = {path: hashlib.sha256(blob).hexdigest()
               for path, blob in payloads.items()}

    # Frozen logical order is intentionally NOT block-major.
    specs = [
        ("C1", "D1", "op31/block-00001", 0, 100),
        ("C2", "D1", "op31/block-00000", 1, 200),
        ("C3", "D2", "op31/block-00001", 1, 300),
        ("C4", "D2", "op31/block-00000", 0, 400),
    ]
    rows = []
    locations = {}
    for logical_index, (cell, donor, block, row_index, library) in enumerate(specs):
        counts_path = block + ".counts.npz"
        meta_path = block + ".meta.csv"
        meta_sha = ("c" if block.endswith("00000") else "e") * 64
        row = {
            "logical_index": logical_index,
            "canonical_cell_id": cell,
            "donor_id": donor,
            "block_key": block,
            "row_index": row_index,
            "selection_row": logical_index,
            "expression_row": 1000 + logical_index,
            "primary_row_weight": "1",
            "source_library": library,
            "meta_path": meta_path,
            "meta_sha256": meta_sha,
            "counts_path": counts_path,
            "counts_sha256": digests[counts_path],
        }
        rows.append(row)
        locations[cell] = {
            "block_key": block,
            "row_index": row_index,
            "meta_path": meta_path,
            "meta_sha256": meta_sha,
            "counts_path": counts_path,
            "counts_sha256": digests[counts_path],
        }

    geometry = {
        "op31/block-00000": {"rows": 2 + rows_delta,
                             "nnz": len(block0_entries) + nnz_delta},
        "op31/block-00001": {"rows": 2,
                             "nnz": len(block1_entries)},
    }
    blocks = ["op31/block-00000", "op31/block-00001"]
    closure = {
        "operator_index": 31,
        "matrix_id": MATRIX_ID,
        "blocks": blocks,
        "metadata_rows_scanned": 4,
        "row_locations": locations,
        "membership_sha256": MEMBERSHIP_SHA,
        "block_manifest_sha256": MANIFEST_SHA,
        "block_geometry": geometry,
    }
    closure["population_closure_root_sha256"] = rc._closure_root(
        31, MATRIX_ID, blocks, 4, locations, MEMBERSHIP_SHA, MANIFEST_SHA,
        geometry)

    logical = {
        "rows": rows,
        "row_count": len(rows),
        "feature_authority_root_sha256": feature_root,
        "population_closure_root_sha256": closure[
            "population_closure_root_sha256"],
        "logical_row_authority_root_sha256": None,
        "real_execution_ready": False,
    }
    logical["logical_row_authority_root_sha256"] = rc._logical_root(
        rows, feature_root, logical["population_closure_root_sha256"])

    proofs = [{
        "logical_index": index,
        "expression_row": row["expression_row"],
        "canonical_cell_id": row["canonical_cell_id"],
        "donor_id": row["donor_id"],
        "source_library": row["source_library"],
        "stored_values_in_row": 2,
    } for index, row in enumerate(rows)]
    raw_authority = {
        "schema": raw.SCHEMA,
        "namespace": raw.NAMESPACE,
        "source_sha256": raw.MTG_SOURCE_SHA256,
        "digest_bytes_read": 32_978_570_763,
        "source_cells": raw.MTG_SOURCE_CELLS,
        "source_features": raw.SOURCE_FEATURE_COUNT,
        "matrix_slot": raw.UMI_SLOT,
        "logical_row_authority_root_sha256": logical[
            "logical_row_authority_root_sha256"],
        "population_closure_root_sha256": logical[
            "population_closure_root_sha256"],
        "feature_authority_root_sha256": feature_root,
        "proof_count": len(proofs),
        "proofs": tuple(proofs),
        "caller_supplied_values": False,
        "pathology_values_read": False,
        "real_execution_ready": False,
    }
    raw_authority["raw_source_proof_root_sha256"] = raw._proof_root(
        raw_authority)
    return logical, closure, raw_authority, feature, payloads


def _derive(**fixture_kwargs):
    logical, closure, raw_authority, feature, payloads = _fixture(
        **fixture_kwargs)
    rows = tc._derive_rows_from_payload_mapping_fixture(
        logical=logical,
        closure=closure,
        raw_source_authority=raw_authority,
        feature_authority=feature,
        payloads=payloads,
        expected_logical_root_sha256=logical[
            "logical_row_authority_root_sha256"],
        expected_closure_root_sha256=closure[
            "population_closure_root_sha256"],
        expected_membership_sha256=MEMBERSHIP_SHA,
        expected_block_manifest_sha256=MANIFEST_SHA,
        expected_raw_source_proof_root_sha256=raw_authority[
            "raw_source_proof_root_sha256"],
        expected_feature_authority_root_sha256=feature[
            "feature_authority_root_sha256"],
        expected_projection_root_sha256=feature[
            "projection_root_sha256"],
        expected_raw_proof_count=4,
    )
    return (logical, closure, raw_authority, feature, payloads, rows)


def test_frozen_formulas_are_exact() -> None:
    assert tc.Q_DEPTH_CELL_FORMULA == "log1p(source_library)"
    assert tc.Q_DETECT_CELL_FORMULA == "count_nonzero(A) / 35076"
    assert tc.SCALAR_FEATURES == 35_076
    assert "28,061" in tc.Q_DETECT_UNIVERSE


def test_q_depth_formula() -> None:
    assert tc.cell_q_depth(99) == pytest.approx(math.log1p(99))


def test_q_detect_formula_requires_full_width() -> None:
    row = [0] * tc.SCALAR_FEATURES
    row[0] = 1
    row[-1] = 2
    assert tc.cell_q_detect(row) == pytest.approx(2 / 35_076)


def test_threshold_free_predicate_remains_threshold_free() -> None:
    assert tc.assert_predicate_is_threshold_free() is True
    assert tc.technical_complete({"Q_DEPTH": 1.0, "Q_DETECT": 0.0},
                                 donor_id="D") is True


def test_block_major_derivation_uses_raw_proof_and_full_b1_projection() -> None:
    _logical, _closure, _raw, _feature, _payloads, rows = _derive()
    by_donor = {row["donor_id"]: row for row in rows}
    assert by_donor["D1"]["Q_DEPTH"] == pytest.approx(
        (math.log1p(100) + math.log1p(200)) / 2)
    assert by_donor["D1"]["Q_DETECT"] == pytest.approx(
        ((1 / 35_076) + (2 / 35_076)) / 2)
    assert by_donor["D2"]["Q_DETECT"] == pytest.approx(
        ((3 / 35_076) + 0.0) / 2)


def test_physical_block_order_does_not_redefine_logical_cell_order() -> None:
    _logical, _closure, _raw, _feature, _payloads, rows = _derive()
    by_donor = {row["donor_id"]: row for row in rows}
    assert by_donor["D1"]["cell_ids"] == ("C1", "C2")
    assert by_donor["D2"]["cell_ids"] == ("C3", "C4")


def test_each_phase2_block_is_parsed_once(monkeypatch) -> None:
    calls = []
    original = rc.parse_authenticated_counts_block

    def wrapped(**kwargs):
        calls.append(kwargs["expected_counts_sha256"])
        return original(**kwargs)

    monkeypatch.setattr(rc, "parse_authenticated_counts_block", wrapped)
    _derive()
    assert len(calls) == 2
    assert len(set(calls)) == 2


def test_manifest_nnz_must_match_actual_payload_even_when_all_roots_are_consistent() -> None:
    with pytest.raises(AssertionError) as excinfo:
        _derive(nnz_delta=1)
    assert rc.STOP_COUNTS_GEOMETRY in str(excinfo.value)


def test_manifest_rows_must_match_actual_payload_even_when_root_moves_with_it() -> None:
    with pytest.raises(AssertionError) as excinfo:
        _derive(rows_delta=1)
    assert rc.STOP_COUNTS_GEOMETRY in str(excinfo.value)


def test_duplicate_sparse_column_in_selected_row_is_refused() -> None:
    with pytest.raises(AssertionError) as excinfo:
        _derive(duplicate_column=True)
    assert tc.STOP_COUNTS_GEOMETRY in str(excinfo.value)


def test_production_b1_width_is_unconditionally_35076() -> None:
    with pytest.raises(AssertionError) as excinfo:
        _derive(feature_count=35_075)
    assert tc.STOP_PROJECTION_WIDTH in str(excinfo.value)


def test_wrong_raw_source_root_stops() -> None:
    logical, closure, raw_authority, feature, payloads = _fixture()
    with pytest.raises(AssertionError):
        tc._derive_rows_from_payload_mapping_fixture(
            logical=logical, closure=closure,
            raw_source_authority=raw_authority,
            feature_authority=feature, payloads=payloads,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_closure_root_sha256=closure[
                "population_closure_root_sha256"],
            expected_membership_sha256=MEMBERSHIP_SHA,
            expected_block_manifest_sha256=MANIFEST_SHA,
            expected_raw_source_proof_root_sha256="f" * 64,
            expected_feature_authority_root_sha256=feature[
                "feature_authority_root_sha256"],
            expected_projection_root_sha256=feature[
                "projection_root_sha256"],
            expected_raw_proof_count=4)


def test_wrong_feature_authority_root_stops() -> None:
    logical, closure, raw_authority, feature, payloads = _fixture()
    with pytest.raises(AssertionError):
        tc._derive_rows_from_payload_mapping_fixture(
            logical=logical, closure=closure,
            raw_source_authority=raw_authority,
            feature_authority=feature, payloads=payloads,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_closure_root_sha256=closure[
                "population_closure_root_sha256"],
            expected_membership_sha256=MEMBERSHIP_SHA,
            expected_block_manifest_sha256=MANIFEST_SHA,
            expected_raw_source_proof_root_sha256=raw_authority[
                "raw_source_proof_root_sha256"],
            expected_feature_authority_root_sha256="f" * 64,
            expected_projection_root_sha256=feature[
                "projection_root_sha256"],
            expected_raw_proof_count=4)


def test_tampered_counts_payload_stops() -> None:
    logical, closure, raw_authority, feature, payloads = _fixture()
    changed = dict(payloads)
    changed["op31/block-00000.counts.npz"] = _csr_npz(
        2, [(0, 40_000, 99), (1, 1, 2), (1, 35_075, 3)])
    with pytest.raises(AssertionError):
        tc._derive_rows_from_payload_mapping_fixture(
            logical=logical, closure=closure,
            raw_source_authority=raw_authority,
            feature_authority=feature, payloads=changed,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_closure_root_sha256=closure[
                "population_closure_root_sha256"],
            expected_membership_sha256=MEMBERSHIP_SHA,
            expected_block_manifest_sha256=MANIFEST_SHA,
            expected_raw_source_proof_root_sha256=raw_authority[
                "raw_source_proof_root_sha256"],
            expected_feature_authority_root_sha256=feature[
                "feature_authority_root_sha256"],
            expected_projection_root_sha256=feature[
                "projection_root_sha256"],
            expected_raw_proof_count=4)


def test_missing_counts_payload_stops() -> None:
    logical, closure, raw_authority, feature, payloads = _fixture()
    partial = dict(payloads)
    partial.pop("op31/block-00000.counts.npz")
    with pytest.raises(AssertionError):
        tc._derive_rows_from_payload_mapping_fixture(
            logical=logical, closure=closure,
            raw_source_authority=raw_authority,
            feature_authority=feature, payloads=partial,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_closure_root_sha256=closure[
                "population_closure_root_sha256"],
            expected_membership_sha256=MEMBERSHIP_SHA,
            expected_block_manifest_sha256=MANIFEST_SHA,
            expected_raw_source_proof_root_sha256=raw_authority[
                "raw_source_proof_root_sha256"],
            expected_feature_authority_root_sha256=feature[
                "feature_authority_root_sha256"],
            expected_projection_root_sha256=feature[
                "projection_root_sha256"],
            expected_raw_proof_count=4)


def test_parent_contract_binds_raw_source_and_has_no_fake_physical_plan() -> None:
    _logical, closure, raw_authority, feature, _payloads, rows = _derive()
    substrate = {
        "population_closure_root_sha256": closure[
            "population_closure_root_sha256"],
        "logical_row_authority_root_sha256": raw_authority[
            "logical_row_authority_root_sha256"],
        "feature_authority_root_sha256": feature[
            "feature_authority_root_sha256"],
        "projection_root_sha256": feature["projection_root_sha256"],
        "raw_source_proof_root_sha256": raw_authority[
            "raw_source_proof_root_sha256"],
    }
    root = tc.parent_contract_root(
        substrate=substrate, derivation_code_sha256=CODE_SHA)
    moved = dict(substrate)
    moved["raw_source_proof_root_sha256"] = "f" * 64
    assert tc.parent_contract_root(
        substrate=moved, derivation_code_sha256=CODE_SHA) != root
    assert "physical_read_plan_root_sha256" not in substrate


def test_package_round_trip_recomputes_semantic_and_parent_roots(tmp_path: Path) -> None:
    logical, closure, raw_authority, feature, _payloads, rows = _derive()
    substrate = {
        "population_closure_root_sha256": closure[
            "population_closure_root_sha256"],
        "logical_row_authority_root_sha256": logical[
            "logical_row_authority_root_sha256"],
        "feature_authority_root_sha256": feature[
            "feature_authority_root_sha256"],
        "projection_root_sha256": feature["projection_root_sha256"],
        "raw_source_proof_root_sha256": raw_authority[
            "raw_source_proof_root_sha256"],
    }
    out = tmp_path / "pkg"
    summary = tc._write_package(
        out, rows=rows, substrate=substrate,
        derivation_code_sha256=CODE_SHA)
    loaded = tc.load_authority(
        out,
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_completeness_root_sha256=summary[
            "completeness_root_sha256"],
        expected_parent_contract_root_sha256=summary[
            "parent_contract_root_sha256"])
    assert loaded["completeness_root_sha256"] == summary[
        "completeness_root_sha256"]
    assert loaded["rows"][0]["cell_ids"]


def test_registry_preserves_exact_floats_and_cell_ids(tmp_path: Path) -> None:
    logical, closure, raw_authority, feature, _payloads, rows = _derive()
    substrate = {
        "population_closure_root_sha256": closure[
            "population_closure_root_sha256"],
        "logical_row_authority_root_sha256": logical[
            "logical_row_authority_root_sha256"],
        "feature_authority_root_sha256": feature[
            "feature_authority_root_sha256"],
        "projection_root_sha256": feature["projection_root_sha256"],
        "raw_source_proof_root_sha256": raw_authority[
            "raw_source_proof_root_sha256"],
    }
    out = tmp_path / "pkg"
    tc._write_package(out, rows=rows, substrate=substrate,
                      derivation_code_sha256=CODE_SHA)
    columns, records = tc._rows((out / tc.REGISTRY).read_bytes())
    assert "Q_DEPTH_HEX" in columns and "Q_DETECT_HEX" in columns
    assert "cell_ids_json" in columns
    assert tuple(json.loads(records[0]["cell_ids_json"])) == rows[0]["cell_ids"]
    assert float.fromhex(records[0]["Q_DEPTH_HEX"]) == rows[0]["Q_DEPTH"]


def test_production_signature_has_no_detached_values_or_fake_geometry_knobs() -> None:
    sig = inspect.signature(tc.build_production_authority)
    forbidden = {
        "cells_by_donor", "substrate", "counts_payload_bytes_by_path",
        "projection", "candidate_donors", "expected_projection_positions",
        "scalar_features", "address_space_size", "physical_read_plan_root_sha256",
    }
    assert forbidden.isdisjoint(sig.parameters)
    for required in (
            "closure", "raw_source_authority", "feature_authority",
            "phase2_expression_root", "expected_raw_source_proof_root_sha256",
            "expected_membership_sha256", "expected_block_manifest_sha256"):
        assert required in sig.parameters


def test_public_production_derivation_demands_complete_raw_population(tmp_path: Path) -> None:
    logical, closure, raw_authority, feature, payloads = _fixture()
    root = tmp_path / "phase2"
    for relative, blob in payloads.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
    with pytest.raises(AssertionError) as excinfo:
        tc.derive_rows_from_authenticated_parents(
            logical=logical, closure=closure,
            raw_source_authority=raw_authority,
            feature_authority=feature,
            phase2_expression_root=root,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_closure_root_sha256=closure[
                "population_closure_root_sha256"],
            expected_membership_sha256=MEMBERSHIP_SHA,
            expected_block_manifest_sha256=MANIFEST_SHA,
            expected_raw_source_proof_root_sha256=raw_authority[
                "raw_source_proof_root_sha256"],
            expected_feature_authority_root_sha256=feature[
                "feature_authority_root_sha256"],
            expected_projection_root_sha256=feature[
                "projection_root_sha256"])
    assert raw.STOP_PROOF_COUNT in str(excinfo.value)


def test_detached_value_entrypoint_is_private_only() -> None:
    assert hasattr(tc, "_build_rows_from_values")
    assert hasattr(tc, "_build_authority_from_values")
    assert not hasattr(tc, "build_rows")
    assert not hasattr(tc, "build_authority")
