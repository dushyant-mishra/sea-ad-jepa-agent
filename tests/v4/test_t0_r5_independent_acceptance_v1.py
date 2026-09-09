"""Independent R4 STOP attacks converted to R5 acceptance assertions."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_estimability_preflight_v1 as pf  # noqa: E402
import t0_raw_source_row_authority_v1 as rs  # noqa: E402
import t0_technical_completeness_authority_v1 as tc  # noqa: E402
import t0_v20_row_count_authority_v1 as rc  # noqa: E402


def test_r4_a_legacy_public_vector_prover_is_gone() -> None:
    assert not hasattr(rc, "prove_source_library")
    assert hasattr(rc, "_prove_source_library_fixture_values")


def test_r4_b_and_c_no_caller_authenticated_handle_or_token_exists() -> None:
    assert not hasattr(rs, "AuthenticatedSource")
    assert not hasattr(rs, "_HANDLE_TOKEN")
    assert not hasattr(rs, "open_authenticated_source")
    sig = inspect.signature(rs.build_population_raw_source_authority)
    assert "source" not in sig.parameters
    assert "source_path" in sig.parameters


def test_r4_d_hash_and_h5_consume_the_same_open_descriptor() -> None:
    source = inspect.getsource(rs._build_population_raw_source_authority)
    assert 'with open(asset, "rb") as stream' in source
    assert 'h5py.File(stream, "r")' in source
    assert 'h5py.File(str(asset)' not in source
    assert 'h5py.File(asset' not in source


def test_r4_b_technical_completeness_requires_population_raw_source_authority() -> None:
    sig = inspect.signature(tc.build_production_authority)
    assert "raw_source_authority" in sig.parameters
    assert "expected_raw_source_proof_root_sha256" in sig.parameters
    assert "cells_by_donor" not in sig.parameters
    assert "counts_payload_bytes_by_path" not in sig.parameters


def test_r4_e_production_projection_has_no_permissive_width_argument() -> None:
    sig = inspect.signature(tc.build_production_authority)
    assert "feature_authority" in sig.parameters
    assert "expected_projection_positions" not in sig.parameters
    assert "projection" not in sig.parameters
    assert "scalar_features" not in sig.parameters
    assert "address_space_size" not in sig.parameters
    source = inspect.getsource(tc._production_projection_positions)
    assert "SCALAR_FEATURES" in source


def test_r4_f_physical_plan_is_not_fabricated_as_a_parent() -> None:
    source = inspect.getsource(tc.parent_contract_root)
    assert "physical_read_plan_root_sha256" not in source
    assert "raw_source_proof_root_sha256" in source
    build_source = inspect.getsource(tc.build_production_authority)
    assert "physical_read_plan_root_sha256" not in build_source


def _stage_a_fixture():
    return {
        "stage": pf.STAGES[0],
        "checks": {
            "DISCOVERY": 4,
            "CONFIRMATION": 4,
            "DISCOVERY_LOODO_FOLDS": 1,
        },
        "loodo_ranks": {0: 4},
        "donor_bound": True,
        "discovery_records_root_sha256": "1" * 64,
        "confirmation_records_root_sha256": "2" * 64,
        "discovery_order": ["D0", "D1"],
        "confirmation_order": ["C0", "C1"],
    }


def _stage_b_fixture(root: str):
    return {
        "stage": pf.STAGES[1],
        "checks": {"primary": 5, "composition": 6, "measurement": 7},
        "residual_df": {"primary": 13, "composition": 12, "measurement": 11},
        "donor_bound": True,
        "records_root_sha256": root,
        "confirmation_order": ["C0", "C1"],
    }


def test_r4_g_preflight_root_binds_checked_records_identity() -> None:
    a = _stage_a_fixture()
    b1 = _stage_b_fixture("a" * 64)
    b2 = _stage_b_fixture("b" * 64)
    assert pf.preflight_root([a, b1]) != pf.preflight_root([a, b2])


def test_r4_h_counts_geometry_is_mandatory_on_block_production_interface() -> None:
    sig = inspect.signature(rc.parse_authenticated_counts_block)
    assert sig.parameters["declared_rows"].default is inspect._empty
    assert sig.parameters["declared_nnz"].default is inspect._empty
    source = inspect.getsource(tc._derive_block_major_rows)
    assert "parse_authenticated_counts_block" in source
    assert 'declared_rows=int(geometry["rows"])' in source
    assert 'declared_nnz=int(geometry["nnz"])' in source
