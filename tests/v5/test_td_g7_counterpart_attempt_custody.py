import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "audit_td_relational_g7_s174_overlap_v2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("td_g7_v2_counterpart_attempt", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_physical_h5_auth_failure_prevents_s174_count_loader(monkeypatch, tmp_path):
    m = load_module()
    physical = tmp_path / "source.h5ad"
    counts = tmp_path / "x.counts.npz"
    physical.write_bytes(b"bad")
    counts.write_bytes(b"counts")

    calls = {"s174_count_loader": 0}

    def fail_physical(*args, **kwargs):
        raise RuntimeError("physical H5AD SHA mismatch")

    def forbidden_count_loader(*args, **kwargs):
        calls["s174_count_loader"] += 1
        raise AssertionError("S174 count loader must not run after physical-H5 authentication failure")

    monkeypatch.setattr(m.common, "verify_source_file", fail_physical)
    monkeypatch.setattr(m, "load_s174_count_matrix", forbidden_count_loader)

    with pytest.raises(RuntimeError, match="physical H5AD SHA mismatch"):
        m.open_authenticated_overlap_count_sources(
            physical_path=physical,
            physical_source_record={"bytes": 3, "sha256": "0" * 64},
            counts_path=counts,
            expected_counts_sha="1" * 64,
        )

    assert calls["s174_count_loader"] == 0


def test_g7_attempt_marker_spends_attempt_and_rejects_retry(tmp_path):
    m = load_module()
    out = tmp_path / "G7_RECEIPT.json"
    trace = {"preflight_result_sha256": "p", "authorization_sha256": "a"}

    marker = m.begin_g7_attempt(out, trace, "g6sha")
    assert marker.exists()
    rec = json.loads(marker.read_text(encoding="utf-8"))
    assert rec["status"] == "STARTED_NOT_A_PASS"
    assert rec["authority_trace"] == trace
    assert rec["g6_receipt_sha256"] == "g6sha"
    assert rec["biological_replay_authorized"] is False
    assert rec["training_authorized"] is False

    with pytest.raises(RuntimeError, match="already spent"):
        m.begin_g7_attempt(out, trace, "g6sha")


def test_g7_attempt_rejects_preexisting_final_receipt(tmp_path):
    m = load_module()
    out = tmp_path / "G7_RECEIPT.json"
    out.write_text("{}\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="already spent"):
        m.begin_g7_attempt(out, {}, "g6sha")


def test_g7_attempt_marker_path_is_sidecar_of_final_receipt(tmp_path):
    m = load_module()
    out = tmp_path / "nested" / "G7_RECEIPT.json"
    marker = m.g7_attempt_marker_path(out)
    assert marker == out.with_name("G7_RECEIPT.json.STARTED_NOT_A_PASS.json")
