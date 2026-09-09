"""Independent external-review RED cases for T0 R4 b08d02f7.

These cases are intentionally written against the producer candidate without
changing producer code.  They preserve concrete counterexamples found during the
R4 external review.

Standing terminals remain unchanged:
PRODUCTION_B2_NOT_RUN
DONOR_ROLE_GATE_SHUT
real_execution_ready=False
NUMERIC_CONFIRMATION_AT8_NOT_ACCESSED
"""

from __future__ import annotations

import hashlib
import inspect
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_estimability_preflight_v1 as pf  # noqa: E402
import t0_raw_source_row_authority_v1 as rs  # noqa: E402
import t0_technical_completeness_authority_v1 as tc  # noqa: E402
import t0_v20_row_count_authority_v1 as rc  # noqa: E402


def test_legacy_public_source_library_prover_must_not_accept_a_fabricated_vector():
    """R4 added a safe prover but left the old caller-vector prover public."""
    logical = {
        "rows": [{
            "canonical_cell_id": "C1",
            "donor_id": "D1",
            "expression_row": 3,
            "source_library": 7,
        }]
    }
    fabricated = [0] * (rc.SOURCE_FEATURE_COUNT - 1) + [7]
    provenance = {
        "source_sha256": rc.MTG_SOURCE_SHA256,
        "source_row_index": 3,
        "source_width": rc.SOURCE_FEATURE_COUNT,
        "canonical_cell_id": "C1",
        "donor_id": "D1",
        "matrix_slot": rc.MTG_SOURCE_MATRIX_SLOT,
    }
    with pytest.raises(AssertionError):
        rc.prove_source_library(
            logical=logical,
            logical_index=0,
            raw_source_row_values=fabricated,
            raw_source_provenance=provenance,
        )


def _write_forged_h5ad(path: Path) -> None:
    import h5py
    import numpy as np

    with h5py.File(path, "w") as handle:
        layer = handle.create_group("layers").create_group("UMIs")
        layer.attrs["encoding-type"] = "csr_matrix"
        layer.attrs["encoding-version"] = "0.1.0"
        layer.attrs["shape"] = np.asarray([1, rs.SOURCE_FEATURE_COUNT],
                                          dtype=np.int64)
        layer.create_dataset("data", data=np.asarray([7.0], dtype=np.float64))
        layer.create_dataset("indices", data=np.asarray([0], dtype=np.int32))
        layer.create_dataset("indptr", data=np.asarray([0, 1], dtype=np.int64))

        obs = handle.create_group("obs")
        obs.attrs["_index"] = "exp_component_name"
        obs.create_dataset("exp_component_name",
                           data=np.asarray(["C1"], dtype=h5py.string_dtype()))
        donor = obs.create_group("Donor ID")
        donor.create_dataset("categories",
                             data=np.asarray(["D1"], dtype=h5py.string_dtype()))
        donor.create_dataset("codes", data=np.asarray([0], dtype=np.int8))


def test_module_token_must_not_allow_a_forged_authenticated_source(tmp_path: Path):
    """The underscore token is a normal importable Python module attribute."""
    forged_path = tmp_path / "forged.h5ad"
    _write_forged_h5ad(forged_path)

    import h5py
    handle = h5py.File(forged_path, "r")
    try:
        # This must be impossible if the token is really an authentication
        # capability.  On R4 the module-level _HANDLE_TOKEN is directly usable.
        with pytest.raises(AssertionError):
            source = rs.AuthenticatedSource(
                rs._HANDLE_TOKEN,
                path=forged_path,
                sha256=rs.MTG_SOURCE_SHA256,
                bytes_read=32_978_570_763,
                handle=handle,
            )
            rs.prove_source_library_from_authenticated_source(
                source=source,
                logical={"rows": [{
                    "canonical_cell_id": "C1",
                    "donor_id": "D1",
                    "expression_row": 0,
                    "source_library": 7,
                }]},
                logical_index=0,
            )
    finally:
        handle.close()


def _csr_npz_one(value: int = 1) -> bytes:
    import numpy as np

    buffer = io.BytesIO()
    np.savez(
        buffer,
        data=np.asarray([value], dtype=np.int32),
        indices=np.asarray([0], dtype=np.int32),
        indptr=np.asarray([0, 1], dtype=np.int32),
        shape=np.asarray([1, rc.ADDRESS_SPACE_SIZE], dtype=np.int32),
        format=np.array(b"csr"),
    )
    return buffer.getvalue()


def _one_row_logical(*, source_library: int = 9999):
    payload = _csr_npz_one()
    row = {
        "logical_index": 0,
        "canonical_cell_id": "C1",
        "donor_id": "D1",
        "block_key": "op31/block-00000",
        "row_index": 0,
        "selection_row": 0,
        "expression_row": 0,
        "primary_row_weight": "1",
        "source_library": source_library,
        "meta_path": "op31/block-00000.meta.csv",
        "meta_sha256": "a" * 64,
        "counts_path": "op31/block-00000.counts.npz",
        "counts_sha256": hashlib.sha256(payload).hexdigest(),
    }
    closure = "1" * 64
    feature = "4" * 64
    logical = {
        "rows": [row],
        "row_count": 1,
        "feature_authority_root_sha256": feature,
        "population_closure_root_sha256": closure,
        "logical_row_authority_root_sha256": None,
        "real_execution_ready": False,
    }
    logical["logical_row_authority_root_sha256"] = rc._logical_root(
        logical["rows"], feature, closure)
    return logical, {row["counts_path"]: payload}


def test_technical_completeness_must_require_raw_source_proof_for_q_depth(tmp_path: Path):
    """A recomputed logical root alone must not make source_library H5-proven."""
    logical, payloads = _one_row_logical(source_library=9999)
    projection = {
        "positions": [0],
        "feature_authority_root_sha256": logical["feature_authority_root_sha256"],
    }
    with pytest.raises(AssertionError):
        tc.build_production_authority(
            tmp_path / "pkg",
            logical=logical,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_closure_root_sha256=logical[
                "population_closure_root_sha256"],
            counts_payload_bytes_by_path=payloads,
            projection=projection,
            expected_projection_root_sha256=tc.projection_root(projection),
            derivation_code_sha256="d" * 64,
            candidate_donors=["D1"],
        )


def test_production_projection_width_must_be_35076_without_an_opt_in_argument():
    """The production default may not silently accept a one-position projection."""
    logical, payloads = _one_row_logical()
    projection = {
        "positions": [0],
        "feature_authority_root_sha256": logical["feature_authority_root_sha256"],
    }
    with pytest.raises(AssertionError):
        tc.derive_rows_from_authenticated_parents(
            logical=logical,
            expected_logical_root_sha256=logical[
                "logical_row_authority_root_sha256"],
            expected_closure_root_sha256=logical[
                "population_closure_root_sha256"],
            counts_payload_bytes_by_path=payloads,
            projection=projection,
            expected_projection_root_sha256=tc.projection_root(projection),
        )


def test_technical_completeness_must_not_invent_a_physical_plan_parent(tmp_path: Path):
    """No physical plan is supplied, so no physical-plan root may be fabricated."""
    logical, payloads = _one_row_logical()
    projection = {
        "positions": [0],
        "feature_authority_root_sha256": logical["feature_authority_root_sha256"],
    }
    summary = tc.build_production_authority(
        tmp_path / "pkg",
        logical=logical,
        expected_logical_root_sha256=logical[
            "logical_row_authority_root_sha256"],
        expected_closure_root_sha256=logical[
            "population_closure_root_sha256"],
        counts_payload_bytes_by_path=payloads,
        projection=projection,
        expected_projection_root_sha256=tc.projection_root(projection),
        derivation_code_sha256="d" * 64,
        candidate_donors=["D1"],
    )
    meta = json.loads((tmp_path / "pkg" / tc.METADATA).read_text())
    assert meta["substrate"]["physical_read_plan_root_sha256"] != (
        logical["logical_row_authority_root_sha256"])
    assert summary["real_execution_ready"] is False


def test_preflight_root_must_bind_the_records_root():
    """Same ranks over different donor-bound records must be different authorities."""
    a = {
        "stage": "B_STATE_DESIGNS",
        "checks": {"primary": 5, "composition": 6, "measurement": 7},
        "records_root_sha256": "a" * 64,
        "donor_bound": True,
    }
    b = dict(a)
    b["records_root_sha256"] = "b" * 64
    assert pf.preflight_root([a]) != pf.preflight_root([b])


def test_safe_source_factory_must_not_hash_one_path_open_then_reopen_that_path():
    """Source authentication should consume one descriptor, not two path opens."""
    source = inspect.getsource(rs.open_authenticated_source)
    assert 'h5py.File(str(asset), "r")' not in source
