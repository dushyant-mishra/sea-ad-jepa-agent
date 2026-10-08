from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v77/v77_measure_oracle_ceilings_v2.py"


def _mod():
    assert SCRIPT.exists(), "v2 sparse oracle successor must exist"
    spec = importlib.util.spec_from_file_location("v77_oracle_v2", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fixture(tmp_path: Path) -> Path:
    root = tmp_path / "world"
    truth = root / "hidden_truth"
    obs = root / "observable_raw" / "FULLSCALE_V2_CANONICAL_sharded"
    truth.mkdir(parents=True)
    obs.mkdir(parents=True)

    # Four cells, six addresses. CSR rows:
    # c0 [10,0,30,0,0,0]
    # c1 [0,20,20,0,0,0]
    # c2 [5,5,0,10,0,0]
    # c3 [0,0,0,0,40,10]
    indices = np.array([0, 2, 1, 2, 0, 1, 3, 4, 5], dtype=np.int32)
    data = np.array([10, 30, 20, 20, 5, 5, 10, 40, 10], dtype=np.int32)
    indptr = np.array([0, 2, 4, 7, 9], dtype=np.int64)
    np.savez_compressed(
        obs / "RNA_SPARSE_000000000_000000004.npz",
        indices=indices,
        data=data,
        indptr=indptr,
        n_addresses=np.int64(6),
        global_cell_index=np.arange(4, dtype=np.int64),
        cell_id=np.array(["c0", "c1", "c2", "c3"]),
        support_count=np.array([6, 6, 6, 6], dtype=np.int32),
        library_target=np.array([40, 40, 20, 50], dtype=np.int64),
        detected_target=np.array([2, 2, 3, 2], dtype=np.int64),
    )

    manifest = {
        "schema": "V77_FULLSCALE_CANONICAL_RNA_OBSERVER_MANIFEST_V2",
        "n_cells": 4,
        "n_addresses": 6,
        "enabled_components": ["C1", "C2"],
        "module_address_sets": {
            "C1_A": [0, 1],
            "C1_B": [2, 3],
            "C1_AB": [4],
            "C2_local": [5],
        },
        "shards": [
            {
                "file": "RNA_SPARSE_000000000_000000004.npz",
                "start": 0,
                "stop": 4,
                "cells": 4,
                "nnz": 9,
            }
        ],
    }
    (obs / "FULLSCALE_V2_MANIFEST.json").write_text(json.dumps(manifest) + "\n")

    np.savez_compressed(
        truth / "TRUTH_000000000_000000004.npz",
        global_cell_index=np.arange(4, dtype=np.int64),
        cell_id=np.array(["c0", "c1", "c2", "c3"]),
        z_global=np.arange(12, dtype=np.float32).reshape(4, 3),
        z_query=np.arange(8, dtype=np.float32).reshape(4, 2),
        z_reg_shared=np.arange(8, dtype=np.float32).reshape(4, 2),
        z_reg_private=np.arange(8, dtype=np.float32).reshape(4, 2),
        c_state_a=np.array([0, 1, 0, 1], dtype=np.int8),
        c_state_b=np.array([0, 0, 1, 1], dtype=np.int8),
        z_gain=np.array([-1.0, -0.5, 0.5, 1.0], dtype=np.float32),
    )
    (truth / "TRUTH_MANIFEST.json").write_text(
        json.dumps(
            {
                "enabled_components": ["C1", "C2"],
                "shards": [{"file": "TRUTH_000000000_000000004.npz"}],
            }
        )
        + "\n"
    )
    return root


def test_sparse_module_projection_uses_full_library_cpm_log1p(tmp_path: Path) -> None:
    mod = _mod()
    root = _fixture(tmp_path)
    world = mod.load_v2_world(root)

    assert world.n_cells == 4
    assert world.n_addresses == 6
    assert world.module_names == ["C1_A", "C1_B", "C1_AB", "C2_local"]
    assert world.module_scores.shape == (4, 4)

    # Module means include zero-valued member genes. c0 C1_A is
    # (log1p(10/40*1e4) + 0) / 2.
    expected = np.log1p(2500.0) / 2.0
    assert np.isclose(world.module_scores[0, 0], expected)

    # c3 has C1_AB address 4 with 40/50 of its library.
    assert np.isclose(world.module_scores[3, 2], np.log1p(8000.0))
    # c3 C2_local address 5 has 10/50.
    assert np.isclose(world.module_scores[3, 3], np.log1p(2000.0))


def test_projection_dimension_is_number_of_planted_modules_not_address_count(tmp_path: Path) -> None:
    mod = _mod()
    world = mod.load_v2_world(_fixture(tmp_path))
    assert world.module_scores.shape[1] == 4
    assert world.module_scores.shape[1] < world.n_addresses
    assert world.design_matrix_policy == "PLANTED_MODULE_SCORES_ONLY__NO_41238_FREE_REGRESSORS"


def test_v2_loader_rejects_missing_or_mismatched_module_addresses(tmp_path: Path) -> None:
    mod = _mod()
    root = _fixture(tmp_path)
    p = root / "observable_raw" / "FULLSCALE_V2_CANONICAL_sharded" / "FULLSCALE_V2_MANIFEST.json"
    m = json.loads(p.read_text())
    m["module_address_sets"]["C1_A"] = [0, 99]
    p.write_text(json.dumps(m) + "\n")
    try:
        mod.load_v2_world(root)
    except ValueError as exc:
        assert "module address out of range" in str(exc)
    else:
        raise AssertionError("out-of-range module address must fail closed")
