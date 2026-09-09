"""R4 red-before regressions for dataset-bound T0 inputs.

These cases are intentionally written against the producer head
ab61cf5599663c417d2b2c5ef95ca7e5a37a312c.  They cover only this project's
own provenance pipeline and use synthetic local fixtures.  No production B2 or
pathology value is accessed.

The governing rule is data-first: decision-bearing values must be derived from
the exact authenticated dataset substrate they claim to summarize, rather than
allowing caller-supplied values to travel beside correct-looking root strings.
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

import t0_estimability_preflight_v1 as pf  # noqa: E402
import t0_technical_completeness_authority_v1 as tc  # noqa: E402
import t0_v20_row_count_authority_v1 as rc  # noqa: E402


def _csv(columns, rows) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def test_r4_raw_source_proof_uses_authenticated_h5_bytes_not_a_caller_vector(
        tmp_path: Path) -> None:
    """The production proof API has no caller-supplied raw-row value argument."""
    import inspect
    import h5py
    import numpy as np

    source = tmp_path / "synthetic_mtg.h5ad"
    with h5py.File(source, "w") as handle:
        obs = handle.create_group("obs")
        obs.create_dataset("exp_component_name",
                           data=np.asarray([b"C0", b"C1"]))
        obs.create_dataset("Donor ID", data=np.asarray([b"D0", b"D1"]))
        layer = handle.create_group("layers/UMIs")
        layer.attrs["shape"] = np.asarray([2, 4], dtype=np.int64)
        layer.create_dataset("indptr", data=np.asarray([0, 2, 4], dtype=np.int64))
        layer.create_dataset("indices", data=np.asarray([0, 3, 1, 2], dtype=np.int64))
        layer.create_dataset("data", data=np.asarray([1, 2, 3, 4], dtype=np.int32))

    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    logical = {
        "rows": [{
            "canonical_cell_id": "C1",
            "donor_id": "D1",
            "expression_row": 1,
            "source_library": 7,
        }]
    }
    assert rc.prove_source_library_from_authenticated_h5_path(
        logical=logical, logical_index=0, source_path=source,
        expected_source_sha256=sha, expected_shape=(2, 4)) is True

    signature = inspect.signature(
        rc.prove_source_library_from_authenticated_h5_path)
    assert "raw_source_row_values" not in signature.parameters
    assert "raw_source_provenance" not in signature.parameters

    wrong = dict(logical)
    wrong["rows"] = [dict(logical["rows"][0], source_library=8)]
    with pytest.raises(AssertionError, match="SOURCE_LIBRARY_NOT_PROVEN"):
        rc.prove_source_library_from_authenticated_h5_path(
            logical=wrong, logical_index=0, source_path=source,
            expected_source_sha256=sha, expected_shape=(2, 4))

def test_r4_manifest_rows_and_nnz_are_required_not_optional_audit_labels() -> None:
    """The frozen Phase2 manifest makes rows/nnz authoritative execution geometry."""
    membership = _csv(
        ["cell_id", "donor_id", "operator_index", "matrix_id"],
        [["C1", "D1", "31", "sea_ad_mtg_rna_final_2026"]],
    )
    meta = _csv(
        ["canonical_cell_id", "donor_id"],
        [["C1", "D1"]],
    )
    meta_sha = hashlib.sha256(meta).hexdigest()
    # Deliberately omit rows and nnz.  ab61cf55 accepts this.
    manifest = _csv(
        ["block_key", "operator_index", "matrix_id", "meta_path", "meta_sha256",
         "counts_path", "counts_sha256"],
        [["op31/block-00000", "31", "sea_ad_mtg_rna_final_2026",
          "op31/block-00000.meta.csv", meta_sha,
          "op31/block-00000.counts.npz", "d" * 64]],
    )

    with pytest.raises(AssertionError, match="MANIFEST.*(rows|nnz)|MANIFEST_COLUMNS"):
        rc.build_population_closure(
            membership_bytes=membership,
            expected_membership_sha256=hashlib.sha256(membership).hexdigest(),
            block_manifest_bytes=manifest,
            expected_block_manifest_sha256=hashlib.sha256(manifest).hexdigest(),
            meta_bytes_by_path={"op31/block-00000.meta.csv": meta},
            operator_index=31,
            matrix_id="sea_ad_mtg_rna_final_2026",
        )


def test_r4_technical_completeness_refuses_detached_values_under_parent_root_strings(
        tmp_path: Path) -> None:
    """Parent root strings must not authorize caller-supplied Q inputs."""
    substrate = {
        "population_closure_root_sha256": "1" * 64,
        "logical_row_authority_root_sha256": "2" * 64,
        "physical_read_plan_root_sha256": "3" * 64,
        "feature_authority_root_sha256": "4" * 64,
        "projection_root_sha256": "5" * 64,
    }

    # On ab61cf55 this packages the fabricated tuple successfully.
    with pytest.raises(AssertionError, match="AUTHENTICATED|SUBSTRATE|DETACHED"):
        tc.build_authority(
            tmp_path / "pkg",
            cells_by_donor={"D1": [(9470, 3000)]},
            substrate=substrate,
            derivation_code_sha256="c" * 64,
            candidate_donors=["D1"],
        )


def _generic_values(n: int, salt: int) -> list[float]:
    import hashlib as _hashlib
    out = []
    for i in range(n):
        h = _hashlib.sha256(("r4|%d|%d" % (salt, i)).encode()).digest()
        out.append(int.from_bytes(h[:6], "big") / float(1 << 48))
    return out


def test_r4_estimability_refuses_unbound_positional_covariates_even_with_donor_ids() -> None:
    """A positional permutation can change rank, so donor identity/order is mandatory."""
    n = 18
    donors = ["D%02d" % i for i in range(n)]
    confirmation = {
        "donor_id": donors,
        "age": [70 + ((i * 7) % 27) for i in range(n)],
        "sex": [i % 2 for i in range(n)],
    }

    # These are all finite generic-position vectors.  On ab61cf55 donor_id is
    # silently ignored and the function accepts positional arrays.
    with pytest.raises(AssertionError, match="DONOR.*(ORDER|IDENTITY|ALIGN)|UNBOUND"):
        pf.stage_b_state_designs(
            confirmation=confirmation,
            state_score=_generic_values(n, 1),
            immune_fraction=_generic_values(n, 2),
            q_depth=[2.0 + v for v in _generic_values(n, 3)],
            q_detect=_generic_values(n, 4),
        )


def _bound_stage_b_inputs():
    n = 18
    donors = ["D%02d" % i for i in range(n)]
    confirmation = {
        "donor_id": donors,
        "age": [70 + ((i * 7) % 27) for i in range(n)],
        "sex": [i % 2 for i in range(n)],
    }
    roots = {
        "eligible_donor_authority_root_sha256": "1" * 64,
        "donor_role_authority_root_sha256": "2" * 64,
        "donor_metadata_authority_root_sha256": "3" * 64,
        "immune_fraction_authority_root_sha256": "4" * 64,
        "technical_completeness_authority_root_sha256": "5" * 64,
        "state_score_authority_root_sha256": "6" * 64,
    }
    return (
        confirmation,
        {d: v for d, v in zip(donors, _generic_values(n, 11))},
        {d: v for d, v in zip(donors, _generic_values(n, 12))},
        {d: 2.0 + v for d, v in zip(donors, _generic_values(n, 13))},
        {d: v for d, v in zip(donors, _generic_values(n, 14))},
        roots,
    )


def test_r4_bound_estimability_joins_every_covariate_by_donor_identity() -> None:
    confirmation, state, immune, depth, detect, roots = _bound_stage_b_inputs()
    result = pf.stage_b_state_designs_bound(
        confirmation=confirmation,
        state_score_by_donor=state,
        immune_fraction_by_donor=immune,
        q_depth_by_donor=depth,
        q_detect_by_donor=detect,
        authority_roots=roots,
        numerical_primitive_authority_root_sha256="a" * 64,
    )
    assert result["stage"] == "B_STATE_DESIGNS"
    assert result["donor_order"] == confirmation["donor_id"]
    assert result["checks"]["primary"] == 5
    assert result["checks"]["composition"] == 6
    assert result["checks"]["measurement"] == 7


def test_r4_bound_estimability_rejects_one_covariate_with_a_wrong_donor() -> None:
    confirmation, state, immune, depth, detect, roots = _bound_stage_b_inputs()
    wrong = dict(state)
    wrong.pop(confirmation["donor_id"][-1])
    wrong["NOT_A_CONFIRMATION_DONOR"] = 0.5
    with pytest.raises(AssertionError, match="DONOR_IDENTITY_OR_ORDER_UNBOUND"):
        pf.stage_b_state_designs_bound(
            confirmation=confirmation,
            state_score_by_donor=wrong,
            immune_fraction_by_donor=immune,
            q_depth_by_donor=depth,
            q_detect_by_donor=detect,
            authority_roots=roots,
            numerical_primitive_authority_root_sha256="a" * 64,
        )


def test_r4_bound_estimability_refuses_unbound_numerical_primitives() -> None:
    confirmation, state, immune, depth, detect, roots = _bound_stage_b_inputs()
    with pytest.raises(AssertionError, match="NUMERICAL_PRIMITIVE_AUTHORITY_UNBOUND"):
        pf.stage_b_state_designs_bound(
            confirmation=confirmation,
            state_score_by_donor=state,
            immune_fraction_by_donor=immune,
            q_depth_by_donor=depth,
            q_detect_by_donor=detect,
            authority_roots=roots,
            numerical_primitive_authority_root_sha256="not-an-authority-root",
        )
