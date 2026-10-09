from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "v77" / "build_v78_marginal_authority.py"
BRIDGE = ROOT / "results" / "v78" / "V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"


def _load():
    spec = importlib.util.spec_from_file_location("v78_marginal_authority_canonical", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _write_csr(path: Path, n_cells: int, address: int, base_count: int) -> None:
    indices = np.full(n_cells, int(address), dtype=np.int32)
    data = np.arange(base_count, base_count + n_cells, dtype=np.int32)
    indptr = np.arange(n_cells + 1, dtype=np.int32)
    np.savez(path, indices=indices, indptr=indptr, format=np.asarray(b"csr"),
             shape=np.asarray([n_cells, 41238], dtype=np.int64), data=data)


def _fixture_cache(tmp_path: Path):
    bridge = json.loads(BRIDGE.read_text())
    cache = tmp_path / "cache"
    cache.mkdir()
    manifest_rows = []
    expected_cells = 0
    for row in bridge["rows"]:
        oi = int(row["operator_index"])
        n = 50 if oi == 0 else 1
        expected_cells += n
        stem = row["stem"]
        cp = cache / f"{stem}.counts.npz"
        mp = cache / f"{stem}.meta.npz"
        _write_csr(cp, n, oi, oi + 1)
        source_library = np.arange(1000 + oi, 1000 + oi + n, dtype=np.int64)
        np.savez(mp, source_library=source_library)
        manifest_rows.append({
            "matrix_id": row["matrix_id"],
            "counts_sha256": _sha(cp),
            "meta_sha256": _sha(mp),
        })
    manifest = {
        "schema": "foundation-train-loader-v1",
        "address_count": 41238,
        "authority_hashes": {"registry": "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"},
        "shards": manifest_rows,
    }
    manifest_path = tmp_path / "production_loader_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return cache, bridge, manifest_path, expected_cells


def test_cache_builder_derives_compact_authority_from_authenticated_shards(tmp_path):
    B = _load()
    cache, bridge, manifest_path, expected_cells = _fixture_cache(tmp_path)
    out = B.build_from_corrected_cache(cache, bridge, manifest_path, canonical=False)
    assert out["schema"] == B.SCHEMA
    assert out["canonical_corrected_train"] is False
    assert out["source"]["n_shards"] == 42
    assert out["source"]["paired_meta_manifest_verified"] is True
    assert out["rank_scrubbed_abundance"]["n_addresses"] == 41238
    assert out["rank_scrubbed_abundance"]["n_zero"] == 41238 - 42
    depth = out["depth_marginals"]
    assert depth["fallback_rule"] == B.FALLBACK_RULE
    assert depth["global"]["n_cells"] == expected_cells
    assert depth["operators"]["0"]["n_cells"] == 50
    assert depth["operators"]["1"]["n_cells"] == 1
    assert depth["sources"]["HVS"]["n_cells"] == 73
    assert depth["sources"]["SEA_AD"]["n_cells"] == 11
    assert depth["sources"]["NPH52"]["n_cells"] == 7
    assert depth["quantile_probs"][0] == 0.0
    assert depth["quantile_probs"][-1] == 1.0


def test_cache_builder_authenticates_paired_meta_not_just_count_presence(tmp_path):
    B = _load()
    cache, bridge, manifest_path, _ = _fixture_cache(tmp_path)
    stem = bridge["rows"][0]["stem"]
    mp = cache / f"{stem}.meta.npz"
    np.savez(mp, source_library=np.asarray([999], dtype=np.int64))
    with pytest.raises(RuntimeError, match="meta digest mismatch"):
        B.build_from_corrected_cache(cache, bridge, manifest_path, canonical=False)


def test_canonical_build_rejects_nonfrozen_loader_manifest(tmp_path):
    B = _load()
    cache, bridge, manifest_path, _ = _fixture_cache(tmp_path)
    with pytest.raises(RuntimeError, match="frozen loader manifest"):
        B.build_from_corrected_cache(cache, bridge, manifest_path, canonical=True)
