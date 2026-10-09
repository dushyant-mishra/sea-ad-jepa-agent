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
CORRECTED_CAL = ROOT / "results" / "v77" / "s174_replay" / "V77_REAL_TRAIN_EXPRESSION_CALIBRATION_V1.json"
EXPECTED_REGISTRY_SHA = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"


def _load():
    assert BUILDER.exists(), f"missing V78 authority builder: {BUILDER.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location("v78_marginal_authority", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _source(**updates):
    rec = {
        "cache": "fixture://corrected-train",
        "pathology_blind": True,
        "train_only": True,
        "read_only": True,
        "registry_sha256": EXPECTED_REGISTRY_SHA,
        "n_addresses": 41238,
        "shard_digests": [
            {"file": f"{i:02d}.counts.npz", "sha256": (f"{i:02x}" * 32)[:64]}
            for i in range(42)
        ],
        "fields_read": ["cell_id", "source_library", "library_size", "detected_addresses"],
    }
    rec.update(updates)
    return rec


def test_source_governance_requires_train_readonly_pathology_blind():
    B = _load()
    for key in ("pathology_blind", "train_only", "read_only"):
        src = _source(**{key: False})
        with pytest.raises(PermissionError):
            B.validate_source_contract(src, canonical=True)


def test_source_governance_rejects_pathology_and_query_like_fields():
    B = _load()
    bad = ["braak_stage", "CERAD", "diagnosis", "disease_status", "target_gene", "query_identity"]
    for name in bad:
        src = _source(fields_read=["cell_id", name])
        with pytest.raises(PermissionError):
            B.validate_source_contract(src, canonical=True)


def test_canonical_source_binds_registry_and_all_42_shards():
    B = _load()
    assert B.validate_source_contract(_source(), canonical=True)["n_shards"] == 42
    with pytest.raises(RuntimeError):
        B.validate_source_contract(_source(registry_sha256="0" * 64), canonical=True)
    with pytest.raises(RuntimeError):
        B.validate_source_contract(_source(shard_digests=_source()["shard_digests"][:-1]), canonical=True)


def test_rank_scrubbed_abundance_contains_distribution_not_identity_map():
    B = _load()
    means = np.array([8.0, 1.0, 0.0, 3.0, 12.0, 2.0], dtype=np.float64)
    rec = B.build_rank_scrubbed_abundance(means)
    text = json.dumps(rec).lower()
    assert rec["identity_scrubbed"] is True
    assert rec["n_addresses"] == len(means)
    assert rec["positive_abundance_sorted"] == [1.0, 2.0, 3.0, 8.0, 12.0]
    assert "address_id" not in text
    assert "ensembl" not in text
    assert "symbol" not in text
    assert "mapping" not in text


def test_abundance_assignment_is_deterministic_permutation_and_metadata_free():
    B = _load()
    authority = B.build_rank_scrubbed_abundance(np.array([1., 2., 3., 4., 5., 6.]))
    a = B.assign_rank_scrubbed_abundance(authority, seed=7302, n_addresses=6)
    b = B.assign_rank_scrubbed_abundance(authority, seed=7302, n_addresses=6)
    assert np.array_equal(a, b)
    assert sorted(a.tolist()) == authority["positive_abundance_sorted"]
    assert B.ABUNDANCE_PERMUTATION_STREAM == 14000


def test_fallback_order_is_exactly_operator_then_source_then_global():
    B = _load()
    assert B.choose_depth_stratum(operator_n=50, source_n=51) == "operator"
    assert B.choose_depth_stratum(operator_n=49, source_n=50) == "source"
    assert B.choose_depth_stratum(operator_n=0, source_n=49) == "global"
    with pytest.raises(ValueError):
        B.choose_depth_stratum(operator_n=-1, source_n=100)


def test_compact_authority_rejects_raw_identity_maps_and_runtime_cache_access():
    B = _load()
    safe = {
        "schema": B.SCHEMA,
        "source": {"source_receipt_sha256": "a" * 64, "n_shards": 42},
        "rank_scrubbed_abundance": {"identity_scrubbed": True, "positive_abundance_sorted": [1.0]},
        "depth_marginals": {"fallback_rule": B.FALLBACK_RULE},
    }
    B.validate_runtime_authority(safe)
    unsafe = json.loads(json.dumps(safe)); unsafe["rank_scrubbed_abundance"]["address_to_abundance"] = {"0": 1.0}
    with pytest.raises(PermissionError):
        B.validate_runtime_authority(unsafe)
    unsafe2 = json.loads(json.dumps(safe)); unsafe2["source"]["cache"] = "D:/real/cache"
    with pytest.raises(PermissionError):
        B.validate_runtime_authority(unsafe2)


def test_real_build_fails_closed_without_exact_cache_and_operator_mapping(tmp_path):
    B = _load()
    missing = tmp_path / "missing-cache"
    with pytest.raises(FileNotFoundError):
        B.build_from_corrected_cache(missing, operator_mapping=None)


def test_operator_bridge_exactly_covers_corrected_s174_shards():
    bridge = json.loads(BRIDGE.read_text())
    cal = json.loads(CORRECTED_CAL.read_text())
    assert bridge["schema"] == "V78_S174_SHARD_OPERATOR_BRIDGE_V1"
    assert bridge["claim_class"] == "CUSTODY_DERIVATION__NON_AUTHORIZING"
    assert bridge["source_bundle"]["sha256"] == "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444"
    assert bridge["source_member"]["sha256"] == "1814a22c8ae01ee94a6fe132546a029af01a7d762384d53c152f37cb545787c1"
    rows = bridge["rows"]
    assert len(rows) == 42
    assert sorted(r["operator_index"] for r in rows) == list(range(42))
    assert len({r["matrix_id"] for r in rows}) == 42
    assert len({r["stem"] for r in rows}) == 42
    for r in rows:
        expected = hashlib.sha256(("corrected|" + r["matrix_id"]).encode()).hexdigest()[:16]
        assert r["stem"] == expected
    corrected_stems = {
        Path(r["file"]).name.removesuffix(".counts.npz")
        for r in cal["source"]["shard_digests"]
    }
    assert {r["stem"] for r in rows} == corrected_stems
    assert {r["source"] for r in rows} == {"HVS", "SEA_AD", "NPH52"}


def test_operator_bridge_is_accepted_only_when_complete_and_unique():
    B = _load()
    bridge = json.loads(BRIDGE.read_text())
    rec = B.validate_operator_bridge(bridge)
    assert rec["n_operators"] == 42
    assert rec["operator_indices"] == list(range(42))
    bad = json.loads(json.dumps(bridge)); bad["rows"] = bad["rows"][:-1]
    with pytest.raises(RuntimeError):
        B.validate_operator_bridge(bad)
    dup = json.loads(json.dumps(bridge)); dup["rows"][1]["stem"] = dup["rows"][0]["stem"]
    with pytest.raises(RuntimeError):
        B.validate_operator_bridge(dup)
