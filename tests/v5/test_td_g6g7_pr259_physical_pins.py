"""Item 2: the runtime-authorization gate accepts only the exact physical PR #259 receipt bytes and the exact replay
manifest bytes. A semantically identical but reserialized copy is refused even when an authorization object was
built around the altered bytes. Synthetic fixtures only (see td_g6g7_gate_fixtures)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_g6g7_gate_fixtures as F  # noqa: E402

PR259_DRIVER = "62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae"
PR259_MAPPING = "6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0"
REPLAY_MANIFEST = "4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660"


def test_gate_pins_are_the_exact_audited_physical_shas():
    m = F.load_common()
    assert m.PR259_DRIVER_SHA256 == PR259_DRIVER
    assert m.PR259_MAPPING_SHA256 == PR259_MAPPING
    assert m.EXPECTED_INPUT_HASHES["replay_manifest_sha256"] == REPLAY_MANIFEST


def test_pristine_pinned_bytes_are_accepted(tmp_path, monkeypatch):
    m = F.load_common()
    b = F.build_gate(tmp_path, m, monkeypatch)
    rec = F.call_gate(m, b)
    assert rec["preflight_result_sha256"] == F.sha(b.preflight)
    assert rec["replay_manifest_sha256"] == F.sha(b.replay_manifest)


@pytest.mark.parametrize("which", ["preflight", "mapping"])
def test_reserialized_receipt_with_authorization_built_around_it_is_refused(tmp_path, monkeypatch, which):
    m = F.load_common()
    b = F.build_gate(tmp_path, m, monkeypatch)
    path = getattr(b, which)
    original = json.loads(path.read_text(encoding="utf-8"))
    F.write_json(path, original, indent=4)  # same JSON semantics, different physical bytes
    assert json.loads(path.read_text(encoding="utf-8")) == original
    F.rewrite_authorization(m, b)  # the authorization now binds the altered bytes' SHA
    with pytest.raises(RuntimeError, match="PR #259"):
        F.call_gate(m, b)


def test_reserialized_replay_manifest_with_authorization_built_around_it_is_refused(tmp_path, monkeypatch):
    m = F.load_common()
    b = F.build_gate(tmp_path, m, monkeypatch)
    raw = b.replay_manifest.read_bytes()
    b.replay_manifest.write_bytes(raw.replace(b"\n", b"\r\n"))  # same CSV rows, different physical bytes
    F.rewrite_authorization(m, b)
    with pytest.raises(RuntimeError, match="replay manifest"):
        F.call_gate(m, b)


def test_gate_refuses_when_no_replay_manifest_is_supplied(tmp_path, monkeypatch):
    m = F.load_common()
    b = F.build_gate(tmp_path, m, monkeypatch)
    with pytest.raises(RuntimeError, match="replay manifest"):
        F.call_gate(m, b, replay_manifest_path=None)


def test_authorization_must_bind_the_replay_manifest_sha(tmp_path, monkeypatch):
    m = F.load_common()
    b = F.build_gate(tmp_path, m, monkeypatch)
    F.rewrite_authorization(m, b, replay_manifest_sha256="0" * 64)
    with pytest.raises(RuntimeError, match="replay_manifest_sha256"):
        F.call_gate(m, b)
