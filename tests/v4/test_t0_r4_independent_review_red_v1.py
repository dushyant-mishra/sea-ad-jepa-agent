"""Independent R4 red tests against producer candidate b08d02f7.

These tests are review evidence only.  They exercise this repository's own
provenance pipeline on synthetic local files and do not access pathology or run
production B2.
"""

from __future__ import annotations

import hashlib
import io
import os
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


def _write_h5(path: Path, *, cell: str, donor: str, entries: dict[int, int]) -> Path:
    import h5py
    import numpy as np

    with h5py.File(path, "w") as handle:
        layer = handle.create_group("layers").create_group("UMIs")
        layer.attrs["encoding-type"] = "csr_matrix"
        layer.attrs["encoding-version"] = "0.1.0"
        layer.attrs["shape"] = np.asarray([1, rs.SOURCE_FEATURE_COUNT], dtype=np.int64)
        cols = sorted(entries)
        layer.create_dataset("data", data=np.asarray([entries[c] for c in cols], dtype=np.float64))
        layer.create_dataset("indices", data=np.asarray(cols, dtype=np.int32))
        layer.create_dataset("indptr", data=np.asarray([0, len(cols)], dtype=np.int64))

        obs = handle.create_group("obs")
        obs.attrs["_index"] = "exp_component_name"
        obs.create_dataset("exp_component_name",
                           data=np.asarray([cell], dtype=h5py.string_dtype()))
        node = obs.create_group("Donor ID")
        node.create_dataset("categories",
                            data=np.asarray([donor], dtype=h5py.string_dtype()))
        node.create_dataset("codes", data=np.asarray([0], dtype=np.int8))
    return path


def _logical_raw(*, cell="C1", donor="D1", library=7):
    return {
        "rows": [{
            "logical_index": 0,
            "canonical_cell_id": cell,
            "donor_id": donor,
            "expression_row": 0,
            "source_library": library,
        }],
        "real_execution_ready": False,
    }


def test_r4_legacy_public_source_proof_still_accepts_a_fabricated_vector() -> None:
    """The R3 vulnerable helper remains public on the R4 candidate."""
    bound = 9470
    logical = {
        "rows": [{
            "canonical_cell_id": "C1",
            "donor_id": "D1",
            "expression_row": 100,
            "source_library": bound,
        }]
    }
    fabricated = [0] * (rc.SOURCE_FEATURE_COUNT - 1) + [bound]
    provenance = {
        "source_sha256": rc.MTG_SOURCE_SHA256,
        "source_row_index": 100,
        "source_width": rc.SOURCE_FEATURE_COUNT,
        "canonical_cell_id": "C1",
        "donor_id": "D1",
        "matrix_slot": rc.MTG_SOURCE_MATRIX_SLOT,
    }

    # A secure successor must make the superseded caller-vector path fail closed.
    with pytest.raises(AssertionError, match="AUTHENTICATED|CALLER|SUPERSEDED"):
        rc.prove_source_library(
            logical=logical,
            logical_index=0,
            raw_source_row_values=fabricated,
            raw_source_provenance=provenance,
        )


def test_r4_module_private_token_is_not_an_authentication_boundary(tmp_path: Path) -> None:
    """A leading underscore is convention, not access control in Python."""
    import h5py

    fake = _write_h5(tmp_path / "fake.h5ad", cell="C1", donor="D1", entries={1: 7})
    handle = h5py.File(fake, "r")
    try:
        # The token is directly reachable as a module attribute.
        forged = rs.AuthenticatedSource(
            rs._HANDLE_TOKEN,
            path=fake,
            sha256=rs.MTG_SOURCE_SHA256,
            bytes_read=32_978_570_763,
            handle=handle,
        )
        with pytest.raises(AssertionError, match="FORGED|AUTHENTIC"):
            rs.prove_source_library_from_authenticated_source(
                source=forged,
                logical=_logical_raw(library=7),
                logical_index=0,
            )
    finally:
        handle.close()


def test_r4_hash_then_reopen_can_parse_different_h5_bytes(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The source is hashed through one open, then reopened by pathname."""
    import h5py

    asset = _write_h5(tmp_path / "asset.h5ad", cell="ORIGINAL", donor="D0",
                      entries={1: 3})
    replacement = _write_h5(tmp_path / "replacement.h5ad", cell="C1", donor="D1",
                            entries={2: 7})
    original_digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    original_file = h5py.File
    swapped = {"done": False}

    def replacing_file(name, mode="r", *args, **kwargs):
        if str(name) == str(asset) and str(mode) == "r" and not swapped["done"]:
            os.replace(replacement, asset)
            swapped["done"] = True
        return original_file(name, mode, *args, **kwargs)

    monkeypatch.setattr(h5py, "File", replacing_file)
    source = rs.open_authenticated_source(asset, expected_sha256=original_digest)
    try:
        assert source.sha256 == original_digest
        assert hashlib.sha256(asset.read_bytes()).hexdigest() != original_digest
        # The proof now reads the replacement bytes while carrying the old digest.
        with pytest.raises(AssertionError, match="DIGEST|AUTHENTIC|CHANGED"):
            rs.prove_source_library_from_authenticated_source(
                source=source,
                logical=_logical_raw(library=7),
                logical_index=0,
                expected_source_sha256=original_digest,
            )
    finally:
        source.close()


def _csr_npz(rows: int, width: int, triples: list[tuple[int, int, int]]) -> bytes:
    import numpy as np
    from scipy import sparse

    rr = [r for r, _c, _v in triples]
    cc = [c for _r, c, _v in triples]
    vv = [v for _r, _c, v in triples]
    matrix = sparse.csr_matrix((vv, (rr, cc)), shape=(rows, width), dtype=np.int32)
    buf = io.BytesIO()
    sparse.save_npz(buf, matrix, compressed=True)
    return buf.getvalue()


def _technical_fixture():
    payload = _csr_npz(1, rc.ADDRESS_SPACE_SIZE, [(0, 0, 1), (0, 1, 2)])
    closure = "c" * 64
    feature = "4" * 64
    row = {
        "logical_index": 0,
        "canonical_cell_id": "C1",
        "donor_id": "D1",
        "block_key": "op31/block-00000",
        "row_index": 0,
        "selection_row": 0,
        "expression_row": 100,
        "primary_row_weight": "1",
        "source_library": 9470,
        "meta_path": "op31/block-00000.meta.csv",
        "meta_sha256": "a" * 64,
        "counts_path": "op31/block-00000.counts.npz",
        "counts_sha256": hashlib.sha256(payload).hexdigest(),
    }
    logical = {
        "rows": [row],
        "feature_authority_root_sha256": feature,
        "population_closure_root_sha256": closure,
        "real_execution_ready": False,
    }
    logical["logical_row_authority_root_sha256"] = rc._logical_root(
        logical["rows"], feature, closure)
    return logical, {row["counts_path"]: payload}


def test_r4_production_technical_path_must_require_full_35076_projection(
        tmp_path: Path) -> None:
    """A 2-position projection must never be lawful in the production constructor."""
    logical, payloads = _technical_fixture()
    projection = {
        "positions": [0, 1],
        "feature_authority_root_sha256": logical["feature_authority_root_sha256"],
    }
    with pytest.raises(AssertionError, match="35076|PROJECTION"):
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


def test_r4_technical_parent_contract_must_not_substitute_logical_for_physical_root(
        tmp_path: Path) -> None:
    """The physical-plan parent must be explicitly and externally bound."""
    logical, payloads = _technical_fixture()
    projection = {
        "positions": [0, 1],
        "feature_authority_root_sha256": logical["feature_authority_root_sha256"],
    }
    with pytest.raises(AssertionError, match="PHYSICAL|PARENT|SUBSTRATE"):
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
            expected_projection_positions=2,
        )


def test_r4_technical_path_must_bind_raw_source_proof_root() -> None:
    """Q_DEPTH cannot rely on a logical source_library without binding its byte proof."""
    import inspect

    params = inspect.signature(tc.build_production_authority).parameters
    assert "expected_raw_source_proof_root_sha256" in params


def _covariate(n: int, start: float, step: float, shape: int) -> list[float]:
    values = []
    for index in range(n):
        seed = ("t0-preflight|%d|%d" % (shape, index)).encode("utf-8")
        draw = int.from_bytes(hashlib.sha256(seed).digest()[:6], "big")
        values.append(start + step * (draw / float(1 << 48)) * 10.0)
    return values


def test_r4_records_root_must_not_round_away_rank_changing_values() -> None:
    """Distinct full-precision designs must not share a records authority root."""
    donors = ["D%02d" % i for i in range(18)]
    depth = _covariate(18, 9.0, 0.05, 2)
    detect = _covariate(18, 0.2, 0.01, 3)
    immune = _covariate(18, 0.01, 0.002, 1)

    base = {}
    for i, donor in enumerate(donors):
        base[donor] = {
            "age": float(70 + (i * 3) % 27),
            "sex": float(i % 2),
            "STATE_SCORE": depth[i],
            "IMMUNE_FRACTION": immune[i],
            "Q_DEPTH": depth[i],
            "Q_DETECT": detect[i],
        }

    deltas = [
        7.964587676033826e-13, -1.7389378567737648e-13,
        2.6261202308912513e-13, -4.0921674146125373e-13,
        -3.2252142966628703e-13, 7.282484171066354e-13,
        6.151022619481295e-14, -8.700925424493423e-13,
        -7.469551096794051e-13, 4.883923586387966e-13,
        -1.5757431607845338e-13, -2.1982356856552e-13,
        3.821449720649507e-13, 4.871924148533963e-13,
        1.758144596277964e-13, -7.933218823786483e-13,
        1.277036597077605e-13, 7.849922364848082e-13,
    ]
    changed = {d: dict(row) for d, row in base.items()}
    for donor, delta in zip(donors, deltas):
        changed[donor]["STATE_SCORE"] += delta

    root = pf.records_root(donors, base, pf.STAGE_B_FIELDS)
    changed_root = pf.records_root(donors, changed, pf.STAGE_B_FIELDS)
    assert root != changed_root, (
        "records_root rounded distinct rank-relevant values to the same authority"
    )

    # Discriminator: the correctly aligned design is rank deficient.
    with pytest.raises(AssertionError) as excinfo:
        pf.stage_b_state_designs(
            confirmation_order=donors, records=base,
            expected_records_root_sha256=root)
    assert pf.STOP_NOT_ESTIMABLE in str(excinfo.value)

    # The changed full-precision design is full rank. A root collision would let
    # it pass under the authority for the non-estimable design.
    result = pf.stage_b_state_designs(
        confirmation_order=donors, records=changed,
        expected_records_root_sha256=changed_root)
    assert result["checks"]["measurement"] == 7
