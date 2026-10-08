from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

from sea_ad_jepa.v5 import full104_pass1_physical_binding_v1 as binding


def write_registry(path: Path, width: int) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("molecular_address_index", "molecular_address_id"),
        )
        writer.writeheader()
        for index in range(width):
            writer.writerow(
                {
                    "molecular_address_index": index,
                    "molecular_address_id": f"addr-{index}",
                }
            )


def write_meta(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=binding.META_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_fixture(
    tmp_path: Path,
    monkeypatch,
    *,
    duplicate_selection: bool = False,
    pass1_core: np.ndarray | None = None,
    donor_src: np.ndarray | None = None,
    corrupt_support: bool = False,
):
    root = tmp_path / "level4"
    root.mkdir()
    registry = tmp_path / "registry.csv"
    observation = tmp_path / "observation.npz"
    pass1 = tmp_path / "pass1.npz"

    write_registry(registry, 4)
    obs = np.asarray(
        [
            [1, 1, 1, 0],
            [1, 2, 1, 0],
        ],
        dtype=np.uint8,
    )
    np.savez(observation, observation_state=obs)

    selections = ([0, 1], [1, 3]) if duplicate_selection else ([0, 1], [2, 3])
    sources = ("SRC_A", "SRC_B")
    donors = ("D0", "D1")
    matrices = (
        np.asarray([[1, 0, 2, 0], [0, 3, 0, 4]], dtype=np.int64),
        np.asarray([[5, 0, 0, 1], [0, 2, 6, 0]], dtype=np.int64),
    )
    manifest_rows = []
    for block_index, dense in enumerate(matrices):
        counts_path = root / f"counts_{block_index}.npz"
        matrix = sp.csr_matrix(dense)
        sp.save_npz(counts_path, matrix)
        meta_path = root / f"meta_{block_index}.csv"
        block_rows = []
        for local_row, selection_row in enumerate(selections[block_index]):
            block_rows.append(
                {
                    "selection_row": selection_row,
                    "canonical_cell_id": f"cell-{block_index}-{local_row}",
                    "donor_id": donors[block_index],
                    "expression_row": local_row,
                    "primary_row_weight": 1.0,
                    "source_library": 100,
                }
            )
        write_meta(meta_path, block_rows)
        manifest_rows.append(
            {
                "block_key": f"block-{block_index}",
                "source": sources[block_index],
                "operator_index": str(block_index),
                "matrix_id": f"matrix-{block_index}",
                "rows": "2",
                "nnz": str(matrix.nnz),
                "counts_path": counts_path.name,
                "counts_sha256": binding.sha256_file(counts_path),
                "meta_path": meta_path.name,
                "meta_sha256": binding.sha256_file(meta_path),
            }
        )

    manifest = root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=binding.MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(manifest_rows)

    core = np.asarray([0, 2], dtype=np.int64)
    cell_donor = np.asarray([0, 0, 1, 1], dtype=np.int64)
    # core columns are 0 and 2
    cell_nnz_core = np.asarray([2, 0, 1, 1], dtype=np.int64)
    donor_addr_nnz = np.asarray(
        [
            [1, 1, 1, 1],
            [1, 1, 1, 1],
        ],
        dtype=np.int64,
    )
    if corrupt_support:
        donor_addr_nnz[1, 2] += 1
    if pass1_core is None:
        pass1_core = core
    if donor_src is None:
        donor_src = np.asarray([0, 1], dtype=np.int64)
    np.savez(
        pass1,
        cell_donor=cell_donor,
        cell_nnz_core=cell_nnz_core,
        donor_addr_nnz=donor_addr_nnz,
        donor_src=donor_src,
        duniq=np.asarray(["D0", "D1"]),
        core=np.asarray(pass1_core, dtype=np.int64),
    )

    monkeypatch.setattr(binding, "FULL104_BLOCK_MANIFEST_SHA256", binding.sha256_file(manifest))
    monkeypatch.setattr(binding, "CANONICAL_REGISTRY_SHA256", binding.sha256_file(registry))
    monkeypatch.setattr(binding, "OBSERVATION_STATE_SHA256", binding.sha256_file(observation))
    monkeypatch.setattr(binding, "EXPECTED_BLOCKS", 2)
    monkeypatch.setattr(binding, "EXPECTED_ROWS", 4)
    monkeypatch.setattr(binding, "EXPECTED_DONORS", 2)
    monkeypatch.setattr(binding, "EXPECTED_OPERATORS", 2)
    monkeypatch.setattr(binding, "EXPECTED_ADDRESSES", 4)
    monkeypatch.setattr(binding, "EXPECTED_CORE", 2)
    monkeypatch.setattr(binding, "SOURCE_NAMES", ("SRC_A", "SRC_B"))

    return root, registry, observation, pass1


def verify(paths):
    root, registry, observation, pass1 = paths
    return binding.verify_pass1_against_physical_full104(
        pass1_path=pass1,
        level4_root=root,
        registry_path=registry,
        observation_state_path=observation,
    )


def test_pass1_physical_binding_happy_path(tmp_path, monkeypatch):
    receipt = verify(build_fixture(tmp_path, monkeypatch))
    assert receipt.block_count == 2
    assert receipt.row_count == 4
    assert receipt.donor_count == 2
    assert receipt.strict_core_state_code == 1
    assert receipt.training_authorized is False
    assert receipt.protected_outcomes_authorized is False
    assert receipt.terminal_masking_outcomes_inspected is False
    assert len(receipt.canonical_digest()) == 64


def test_stale_pass1_core_cannot_bind_to_current_observation_state(tmp_path, monkeypatch):
    paths = build_fixture(
        tmp_path,
        monkeypatch,
        pass1_core=np.asarray([0, 1], dtype=np.int64),
    )
    with pytest.raises(ValueError, match="strict core does not rederive"):
        verify(paths)


def test_stale_pass1_support_cannot_bind_to_current_count_blocks(tmp_path, monkeypatch):
    paths = build_fixture(tmp_path, monkeypatch, corrupt_support=True)
    with pytest.raises(ValueError, match="donor/core support does not rederive"):
        verify(paths)


def test_pass1_donor_source_substitution_fails(tmp_path, monkeypatch):
    paths = build_fixture(
        tmp_path,
        monkeypatch,
        donor_src=np.asarray([1, 0], dtype=np.int64),
    )
    with pytest.raises(ValueError, match="donor/source identity disagrees"):
        verify(paths)


def test_duplicate_physical_selection_row_fails(tmp_path, monkeypatch):
    paths = build_fixture(tmp_path, monkeypatch, duplicate_selection=True)
    with pytest.raises(ValueError, match="duplicate physical selection_row"):
        verify(paths)


def test_physical_counts_hash_corruption_fails(tmp_path, monkeypatch):
    root, registry, observation, pass1 = build_fixture(tmp_path, monkeypatch)
    with (root / "counts_0.npz").open("ab") as handle:
        handle.write(b"corruption")
    with pytest.raises(ValueError, match="FULL104 counts hash mismatch"):
        verify((root, registry, observation, pass1))


def test_pass1_is_not_authority_from_shape_alone(tmp_path, monkeypatch):
    root, registry, observation, pass1 = build_fixture(tmp_path, monkeypatch)
    with np.load(pass1, allow_pickle=False) as data:
        payload = {name: np.asarray(data[name]) for name in data.files}
    payload["cell_donor"] = payload["cell_donor"].copy()
    payload["cell_donor"][0] = 1
    np.savez(pass1, **payload)
    with pytest.raises(ValueError, match="cell_donor does not rederive"):
        verify((root, registry, observation, pass1))
