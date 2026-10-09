from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "v77" / "run_v78_signed_detection_marginal_tournament.py"
E2 = ROOT / "results" / "v77" / "V77_CLASS_PROPAGATION_TOURNAMENT_V1.json"
BRIDGE = ROOT / "results" / "v78" / "V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"
EXPECTED_REGISTRY_SHA = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
EXPECTED_CAL_SHA = "f6ba2c725a5437cc8455fff418027d36efe9ea9430fbd0a5765df62dedca6068"
EXPECTED_META_SEM_SHA = "b876e13526f51d5a4199ca750ad09065c5ab8a20aeca39dff3d8c385f2241f46"
EXPECTED_ARCHIVE_SHA = "88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f"


def _load():
    spec = importlib.util.spec_from_file_location("v78_gate", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _bridge_sha():
    R = _load()
    return R.MARGINAL.validate_operator_bridge(json.loads(BRIDGE.read_text()))["bridge_sha256"]


def _canonical_authority(path: Path):
    path.write_text(json.dumps({
        "schema": "V78_MARGINAL_AUTHORITY_V1",
        "source": {
            "source_receipt_sha256": "a" * 64,
            "n_shards": 42,
            "n_cells": 4726,
            "registry_sha256": EXPECTED_REGISTRY_SHA,
            "corrected_calibration_sha256": EXPECTED_CAL_SHA,
            "meta_digest_semantic_sha256": EXPECTED_META_SEM_SHA,
            "repaired_archive_sha256": EXPECTED_ARCHIVE_SHA,
            "operator_bridge_sha256": _bridge_sha(),
            "paired_meta_manifest_verified": True,
            "fields_read": ["counts.indices", "counts.indptr", "counts.data", "meta.source_library"],
        },
        "rank_scrubbed_abundance": {
            "identity_scrubbed": True,
            "rank_scrubbed": True,
            "n_addresses": 41238,
            "n_zero": 0,
            "positive_abundance_sorted": [1.0] * 41238,
            "assignment_stream": 14000,
        },
        "depth_marginals": {"fallback_rule": "operator_if_n>=50_else_source_if_n>=50_else_global"},
        "canonical_corrected_train": True,
        "training_authorized": False,
    }))
    return path


def test_gate_is_blocked_when_canonical_f3_authority_is_missing(tmp_path):
    R = _load()
    rec = R.preexecution_gate(E2, BRIDGE, tmp_path / "missing.json", tmp_path / "missing-cache")
    assert rec["status"] == "BLOCKED"
    assert "canonical_f3_marginal_authority" in rec["blockers"]
    assert rec["training_authorized"] is False
    with pytest.raises(PermissionError):
        R.require_execution_authority(rec)


def test_gate_authenticates_repaired_s174_authority_roots_before_physical_cache_gate(tmp_path):
    R = _load()
    authority = _canonical_authority(tmp_path / "authority.json")
    rec = R.preexecution_gate(E2, BRIDGE, authority, tmp_path / "missing-cache")
    assert rec["status"] == "BLOCKED"
    assert rec["details"]["marginal_authority"]["status"] == "AUTHENTICATED"
    checks = rec["details"]["marginal_authority"]["provenance_checks"]
    assert checks["corrected_calibration_sha256"] is True
    assert checks["meta_digest_semantic_sha256"] is True
    assert checks["repaired_archive_sha256"] is True
    assert "authenticated_corrected_train_cache_bytes" in rec["blockers"]


def test_gate_rejects_stale_loader_manifest_only_provenance(tmp_path):
    R = _load()
    p = _canonical_authority(tmp_path / "authority.json")
    rec = json.loads(p.read_text())
    rec["source"].pop("corrected_calibration_sha256")
    rec["source"].pop("meta_digest_semantic_sha256")
    rec["source"].pop("repaired_archive_sha256")
    rec["source"]["loader_manifest_sha256"] = "2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328"
    p.write_text(json.dumps(rec))
    gate = R.preexecution_gate(E2, BRIDGE, p, tmp_path / "missing-cache")
    assert gate["details"]["marginal_authority"]["status"] == "REJECTED"
    assert "canonical_f3_marginal_authority" in gate["blockers"]


def test_gate_refuses_noncanonical_or_training_authorizing_marginal_artifact(tmp_path):
    R = _load()
    p = _canonical_authority(tmp_path / "authority.json")
    rec = json.loads(p.read_text())
    rec["canonical_corrected_train"] = False
    rec["training_authorized"] = True
    p.write_text(json.dumps(rec))
    gate = R.preexecution_gate(E2, BRIDGE, p, tmp_path / "cache")
    assert gate["status"] == "BLOCKED"
    assert "canonical_f3_marginal_authority" in gate["blockers"]
    assert "training_authorization_contamination" in gate["blockers"]


def test_gate_rejects_missing_paired_meta_provenance(tmp_path):
    R = _load()
    p = _canonical_authority(tmp_path / "authority.json")
    rec = json.loads(p.read_text())
    rec["source"].pop("paired_meta_manifest_verified")
    p.write_text(json.dumps(rec))
    gate = R.preexecution_gate(E2, BRIDGE, p, tmp_path / "missing-cache")
    assert gate["status"] == "BLOCKED"
    assert "canonical_f3_marginal_authority" in gate["blockers"]
    assert gate["details"]["marginal_authority"]["status"] == "REJECTED"
