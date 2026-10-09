from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "v77" / "run_v78_signed_detection_marginal_tournament.py"
E2 = ROOT / "results" / "v77" / "V77_CLASS_PROPAGATION_TOURNAMENT_V1.json"
BRIDGE = ROOT / "results" / "v78" / "V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"


def _load():
    spec = importlib.util.spec_from_file_location("v78_gate", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _canonical_authority(path: Path):
    path.write_text(json.dumps({
        "schema": "V78_MARGINAL_AUTHORITY_V1",
        "source": {"source_receipt_sha256": "a" * 64, "n_shards": 42},
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
    rec = R.preexecution_gate(
        e2_reference=E2,
        operator_bridge=BRIDGE,
        marginal_authority=tmp_path / "missing.json",
        corrected_cache_root=tmp_path / "missing-cache",
    )
    assert rec["status"] == "BLOCKED"
    assert "canonical_f3_marginal_authority" in rec["blockers"]
    assert rec["training_authorized"] is False
    with pytest.raises(PermissionError):
        R.require_execution_authority(rec)


def test_gate_remains_blocked_if_summary_like_authority_claims_canonical_without_cache(tmp_path):
    R = _load()
    authority = _canonical_authority(tmp_path / "authority.json")
    rec = R.preexecution_gate(
        e2_reference=E2,
        operator_bridge=BRIDGE,
        marginal_authority=authority,
        corrected_cache_root=tmp_path / "missing-cache",
    )
    assert rec["status"] == "BLOCKED"
    assert "authenticated_corrected_train_cache_bytes" in rec["blockers"]
    assert rec["f0_f2_early_execution_authorized"] is False


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
