from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

from sea_ad_jepa.v5 import full104_physical_shakedown_v1 as physical


MANIFEST_COLUMNS = physical.MANIFEST_COLUMNS
META_COLUMNS = physical.META_COLUMNS


def sha(path: Path) -> str:
    return physical.sha256_file(path)


def write_registry(path: Path, width: int) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("molecular_address_index", "molecular_address_id"),
        )
        writer.writeheader()
        for i in range(width):
            writer.writerow(
                {
                    "molecular_address_index": i,
                    "molecular_address_id": f"addr-{i}",
                }
            )


def write_meta(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=META_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_fixture(tmp_path: Path, monkeypatch, *, duplicate: bool = False):
    root = tmp_path / "level4"
    root.mkdir()
    registry = tmp_path / "registry.csv"
    obs = tmp_path / "observation.bin"
    obs.write_bytes(b"current-observation-state")
    width = 4
    write_registry(registry, width)

    manifest_rows = []
    selection_by_block = ([0, 1], [1, 3]) if duplicate else ([0, 1], [2, 3])
    source_by_block = ("SRC_A", "SRC_B")
    donor_by_block = ("D0", "D1")
    for block_index in range(2):
        counts = sp.csr_matrix(
            np.asarray(
                [
                    [1 + block_index, 0, 2, 0],
                    [0, 3, 0, 4 + block_index],
                ],
                dtype=np.int64,
            )
        )
        counts_path = root / f"counts_{block_index}.npz"
        sp.save_npz(counts_path, counts)

        meta_path = root / f"meta_{block_index}.csv"
        selection = selection_by_block[block_index]
        write_meta(
            meta_path,
            [
                {
                    "selection_row": selection[0],
                    "canonical_cell_id": f"cell-{block_index}-0",
                    "donor_id": donor_by_block[block_index],
                    "expression_row": 0,
                    "primary_row_weight": 1.0,
                    "source_library": 100,
                },
                {
                    "selection_row": selection[1],
                    "canonical_cell_id": f"cell-{block_index}-1",
                    "donor_id": donor_by_block[block_index],
                    "expression_row": 1,
                    "primary_row_weight": 1.0,
                    "source_library": 120,
                },
            ],
        )
        manifest_rows.append(
            {
                "block_key": f"block-{block_index}",
                "source": source_by_block[block_index],
                "operator_index": str(block_index),
                "matrix_id": f"matrix-{block_index}",
                "rows": "2",
                "nnz": str(counts.nnz),
                "counts_path": counts_path.name,
                "counts_sha256": sha(counts_path),
                "meta_path": meta_path.name,
                "meta_sha256": sha(meta_path),
            }
        )

    manifest = root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(manifest_rows)

    monkeypatch.setattr(physical, "FULL104_BLOCK_MANIFEST_SHA256", sha(manifest))
    monkeypatch.setattr(physical, "CANONICAL_REGISTRY_SHA256", sha(registry))
    monkeypatch.setattr(physical, "OBSERVATION_STATE_SHA256", sha(obs))
    monkeypatch.setattr(physical, "EXPECTED_BLOCKS", 2)
    monkeypatch.setattr(physical, "EXPECTED_ROWS", 4)
    monkeypatch.setattr(physical, "EXPECTED_DONORS", 2)
    monkeypatch.setattr(physical, "EXPECTED_OPERATORS", 2)
    monkeypatch.setattr(physical, "EXPECTED_ADDRESSES", width)
    monkeypatch.setattr(physical, "EXPECTED_SOURCES", ("SRC_A", "SRC_B"))
    monkeypatch.setattr(physical, "_gpu_memory_used_mib_for_current_pid", lambda: None)
    return root, registry, obs, manifest_rows


def test_physical_shakedown_streams_authenticated_fixture_and_normalizes(tmp_path, monkeypatch):
    root, registry, obs, _ = build_fixture(tmp_path, monkeypatch)
    real_log1p = np.log1p
    normalized_sizes = []

    def capture_log1p(values):
        normalized_sizes.append(np.asarray(values).size)
        return real_log1p(values)

    monkeypatch.setattr(physical.np, "log1p", capture_log1p)
    receipt = physical.run_physical_shakedown(
        level4_root=root,
        registry_path=registry,
        observation_state_path=obs,
    )
    assert receipt.block_count == 2
    assert receipt.row_count == 4
    assert receipt.donor_count == 2
    assert receipt.operator_count == 2
    assert receipt.address_count == 4
    assert receipt.total_nnz > 0
    assert sum(normalized_sizes) == receipt.total_nnz
    assert receipt.rows_per_second > 0
    assert receipt.training_authorized is False
    assert receipt.terminal_masking_outcomes_inspected is False


def test_physical_shakedown_fails_on_counts_hash_corruption(tmp_path, monkeypatch):
    root, registry, obs, _ = build_fixture(tmp_path, monkeypatch)
    with (root / "counts_0.npz").open("ab") as handle:
        handle.write(b"corruption")
    with pytest.raises(ValueError, match="counts hash mismatch"):
        physical.run_physical_shakedown(
            level4_root=root,
            registry_path=registry,
            observation_state_path=obs,
        )


def test_physical_shakedown_fails_on_duplicate_selection_row(tmp_path, monkeypatch):
    root, registry, obs, _ = build_fixture(tmp_path, monkeypatch, duplicate=True)
    with pytest.raises(ValueError, match="duplicate selection_row"):
        physical.run_physical_shakedown(
            level4_root=root,
            registry_path=registry,
            observation_state_path=obs,
        )


def test_physical_shakedown_fails_on_historical_manifest_root(tmp_path, monkeypatch):
    root, registry, obs, _ = build_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(physical, "FULL104_BLOCK_MANIFEST_SHA256", hashlib.sha256(b"historical").hexdigest())
    with pytest.raises(ValueError, match="block manifest root mismatch"):
        physical.run_physical_shakedown(
            level4_root=root,
            registry_path=registry,
            observation_state_path=obs,
        )


def test_physical_shakedown_driver_is_nonterminal_and_pass1_independent():
    source = Path("scripts/agent/run_full104_physical_shakedown_v1.py").read_text(
        encoding="utf-8"
    )
    compile(source, "scripts/agent/run_full104_physical_shakedown_v1.py", "exec")
    assert "run_physical_shakedown" in source
    assert "--level4-root" in source
    assert "--registry" in source
    assert "--observation-state" in source
    assert "--worktree" in source
    assert "live_clean_scientific_head" in source
    assert "allowed_relative_paths" in source
    assert "--pass1" not in source
    assert '"terminal_masking_authorized": False' in source
    assert '"training_authorized": False' in source
