"""Degenerate-input tests for the V69 receipt-bound acquisition contract.

Every assertion here is paired with a reachable failing outcome: each test drives
the utility into a distinct *failure* state and proves the utility refuses to emit
PASS. The happy-path test proves PASS is itself reachable, so none of these checks
is a tautology that cannot fail.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

_MOD_PATH = Path(__file__).resolve().parents[1] / "scripts" / "v69" / "acquire_remote_object_v1.py"
_spec = importlib.util.spec_from_file_location("v69_acq", _MOD_PATH)
acq = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(acq)


def _ident(length, lm="Tue, 04 Oct 2022 18:36:52 GMT", status="200"):
    return {
        "http_status": status,
        "content_length": length,
        "last_modified": lm,
        "etag": None,
        "accept_ranges": "bytes",
        "raw_header_sha256": "0" * 64,
    }


def _patch(monkeypatch, idents, writer):
    seq = list(idents)
    calls = {"n": 0}

    def fake_head(url, timeout=120):
        i = min(calls["n"], len(seq) - 1)
        calls["n"] += 1
        return seq[i]

    def fake_fetch(url, dest, expect_bytes, max_attempts=12):
        writer(Path(dest), expect_bytes)
        return [{"attempt": 1, "curl_returncode": 0, "bytes_after":
                 Path(dest).stat().st_size if Path(dest).exists() else 0}]

    monkeypatch.setattr(acq, "head", fake_head)
    monkeypatch.setattr(acq, "fetch", fake_fetch)


def test_pass_is_reachable(tmp_path, monkeypatch):
    payload = b"x" * 1024

    def w(dest, n):
        dest.write_bytes(payload)

    _patch(monkeypatch, [_ident(len(payload)), _ident(len(payload))], w)
    r = acq.acquire("http://example/x", tmp_path / "x.bin", "L", "lic", "rec")
    assert r["status"] == "PASS__BYTE_COMPLETE_AND_DIGESTED"
    assert r["sha256"] == hashlib.sha256(payload).hexdigest()
    assert r["local_bytes"] == len(payload)


def test_truncated_download_is_refused(tmp_path, monkeypatch):
    """A tool that 'succeeds' on a short file must NOT yield a PASS receipt."""

    def w(dest, n):
        dest.write_bytes(b"y" * (n - 7))

    _patch(monkeypatch, [_ident(1024), _ident(1024)], w)
    r = acq.acquire("http://example/x", tmp_path / "x.bin", "L", "lic", "rec")
    assert r["status"] == "INCOMPLETE__LOCAL_BYTES_NE_REMOTE_CONTENT_LENGTH"
    assert r["bytes_missing"] == 7
    assert r["sha256"] is None, "a truncated file must never carry an authenticated digest"


def test_absent_remote_length_cannot_pass(tmp_path, monkeypatch):
    def w(dest, n):
        dest.write_bytes(b"z" * 10)

    _patch(monkeypatch, [_ident(None), _ident(None)], w)
    r = acq.acquire("http://example/x", tmp_path / "x.bin", "L", "lic", "rec")
    assert r["status"] == "REMOTE_LENGTH_UNAVAILABLE__NO_PASS_POSSIBLE"
    assert r["sha256"] is None
    assert not (tmp_path / "x.bin").exists(), "must not download without authoritative length"


def test_remote_object_changing_midrun_is_refused(tmp_path, monkeypatch):
    payload = b"q" * 512

    def w(dest, n):
        dest.write_bytes(payload)

    _patch(monkeypatch,
           [_ident(512, lm="Mon, 01 Jan 2020 00:00:00 GMT"),
            _ident(512, lm="Tue, 02 Feb 2021 00:00:00 GMT")], w)
    r = acq.acquire("http://example/x", tmp_path / "x.bin", "L", "lic", "rec")
    assert r["status"] == "REMOTE_OBJECT_CHANGED_DURING_ACQUISITION"
    assert r["sha256"] is None


def test_local_larger_than_remote_aborts_without_pass(tmp_path, monkeypatch):
    def w(dest, n):
        dest.write_bytes(b"w" * (n + 100))

    _patch(monkeypatch, [_ident(256), _ident(256)], w)
    r = acq.acquire("http://example/x", tmp_path / "x.bin", "L", "lic", "rec")
    assert r["status"] == "INCOMPLETE__LOCAL_BYTES_NE_REMOTE_CONTENT_LENGTH"
    assert r["bytes_missing"] == -100
    assert r["sha256"] is None


def test_receipt_never_fabricates_a_number(tmp_path, monkeypatch):
    """Unmeasured fields stay null; the receipt must not invent a size or digest."""

    def w(dest, n):
        pass  # nothing downloaded at all

    _patch(monkeypatch, [_ident(2048), _ident(2048)], w)
    r = acq.acquire("http://example/x", tmp_path / "x.bin", "L", "lic", "rec")
    assert r["status"] == "INCOMPLETE__LOCAL_BYTES_NE_REMOTE_CONTENT_LENGTH"
    assert r["local_bytes"] == 0
    assert r["sha256"] is None
    json.dumps(r)  # receipt must be serialisable
