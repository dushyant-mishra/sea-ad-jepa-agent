from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "v77" / "build_v78_repaired_s174_marginal_authority.py"
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
    count_rows = []
    meta_rows = []
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
        count_rows.append({"file": cp.name, "sha256": _sha(cp)})
        meta_rows.append({"file": mp.name, "sha256": _sha(mp)})

    corrected = {
        "schema": "V77_REAL_TRAIN_EXPRESSION_CALIBRATION_V1",
        "source": {
            "cache": "fixture://corrected-s174",
            "n_shards": 42,
            "shard_digests": count_rows,
            "pathology_blind": True,
            "train_only": True,
            "read_only": True,
            "metadata_fields": ["source_library"],
        },
    }
    corrected_path = tmp_path / "V77_REAL_TRAIN_EXPRESSION_CALIBRATION_V1.json"
    corrected_path.write_text(json.dumps(corrected, indent=2) + "\n")

    meta_digest = {
        "schema": "V78_S174_SHARD_META_DIGEST_V1",
        "claim_class": "CUSTODY_DERIVATION__NON_AUTHORIZING",
        "source_archive": {"filename": "fixture.rar", "size_bytes": 1, "sha256": "a" * 64},
        "corrected_calibration": {"path": corrected_path.name, "sha256": _sha(corrected_path)},
        "n_meta_shards": 42,
        "rows": meta_rows,
    }
    meta_path = tmp_path / "V78_S174_SHARD_META_DIGEST_V1.json"
    meta_path.write_text(json.dumps(meta_digest, indent=2) + "\n")
    return cache, bridge, corrected_path, meta_path, expected_cells


def test_cache_builder_derives_compact_authority_from_repaired_s174_receipts(tmp_path):
    B = _load()
    cache, bridge, corrected_path, meta_path, expected_cells = _fixture_cache(tmp_path)
    out = B.build_from_corrected_cache(
        cache, bridge, corrected_path, meta_path, canonical=False
    )
    assert out["schema"] == B.SCHEMA
    assert out["canonical_corrected_train"] is False
    assert out["source"]["n_shards"] == 42
    assert out["source"]["paired_meta_manifest_verified"] is True
    assert out["source"]["corrected_calibration_sha256"] == _sha(corrected_path)
    assert out["source"]["meta_digest_manifest_sha256"] == _sha(meta_path)
    abundance = out["rank_scrubbed_abundance"]
    assert abundance["n_addresses"] == 41238
    assert abundance["n_zero"] == 41238 - 42
    assert abundance["n_positive"] == 42
    assert "positive_abundance_sorted" not in abundance
    assert len(abundance["positive_abundance_quantile_probs"]) == 1001
    assert len(abundance["positive_abundance_quantiles"]) == 1001
    reconstructed = B.assign_rank_scrubbed_abundance(abundance, seed=7302, n_addresses=41238)
    assert reconstructed.shape == (41238,)
    assert np.count_nonzero(reconstructed) == 42
    depth = out["depth_marginals"]
    assert depth["fallback_rule"] == B.FALLBACK_RULE
    assert depth["global"]["n_cells"] == expected_cells
    assert depth["operators"]["0"]["n_cells"] == 50
    assert depth["operators"]["1"]["n_cells"] == 1
    assert depth["sources"]["HVS"]["n_cells"] == 73
    assert depth["sources"]["SEA_AD"]["n_cells"] == 11
    assert depth["sources"]["NPH52"]["n_cells"] == 7


def test_cache_builder_authenticates_paired_meta_from_repaired_archive_receipt(tmp_path):
    B = _load()
    cache, bridge, corrected_path, meta_path, _ = _fixture_cache(tmp_path)
    stem = bridge["rows"][0]["stem"]
    np.savez(cache / f"{stem}.meta.npz", source_library=np.asarray([999], dtype=np.int64))
    with pytest.raises(RuntimeError, match="meta digest mismatch"):
        B.build_from_corrected_cache(cache, bridge, corrected_path, meta_path, canonical=False)


def test_cache_builder_authenticates_corrected_count_receipt_not_old_loader_manifest(tmp_path):
    B = _load()
    cache, bridge, corrected_path, meta_path, _ = _fixture_cache(tmp_path)
    stem = bridge["rows"][0]["stem"]
    _write_csr(cache / f"{stem}.counts.npz", 50, 999, 1)
    with pytest.raises(RuntimeError, match="count digest mismatch"):
        B.build_from_corrected_cache(cache, bridge, corrected_path, meta_path, canonical=False)


def test_canonical_build_rejects_nonfrozen_corrected_calibration_and_meta_receipt(tmp_path):
    B = _load()
    cache, bridge, corrected_path, meta_path, _ = _fixture_cache(tmp_path)
    with pytest.raises(RuntimeError, match="corrected S174 calibration"):
        B.build_from_corrected_cache(cache, bridge, corrected_path, meta_path, canonical=True)
