"""Sol RED: do not reread all old checkpoint payloads every attempted update.

Synthetic opaque bytes ONLY: zero training/optimizer, zero GPU, no RNA.
Reopening, inspect_journal and forensic reads MUST still fresh-rehash all bytes.
The incremental writer cache may trust only exact unchanged filesystem metadata
for previously byte-verified content; any metadata change refuses further write.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v
from tests.test_jepa_synth2048_attempt_journal_v2_macha_red import (
    commit, open_run,
)


def _count_payload_reads(monkeypatch):
    real = v._read
    counts = {"reads": 0, "bytes": 0, "files": []}
    def wrapper(path, maximum, *, twin_ok=False):
        raw = real(path, maximum, twin_ok=twin_ok)
        if Path(path).name.endswith(".state.bin"):
            counts["reads"] += 1
            counts["bytes"] += len(raw)
            counts["files"].append(Path(path).name)
        return raw
    monkeypatch.setattr(v, "_read", wrapper)
    return counts


def test_red_old_payloads_cannot_be_sha_rehashed_quadratically_on_each_step(
        tmp_path, monkeypatch):
    root, backup = open_run(tmp_path, horizon=20)
    reads = _count_payload_reads(monkeypatch)
    for u in range(1, 19):
        commit(root, backup, u)
    # Old code rereads 1+2+...+18 two times per update (~342 reads).
    # New code should read each new state on first publication, not every
    # historical payload at each BEGIN and COMMIT. Includes occasional fresh
    # read when a new row is written, and no final expensive full scrub here.
    assert reads["reads"] <= 3 * 19, reads
    assert v.AUTHORITY.endswith("REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED")
    # Full strict verification is still available on demand.
    before = reads["reads"]
    report = v.inspect_journal(root, backup)
    assert report["last_reported_probe_pass_checkpoint_update"] == 18
    assert reads["reads"] - before >= 19
    assert report["last_neurally_healthy_checkpoint_proved"] is False


def test_old_checkpoint_mutation_refuses_writer_even_after_cache_hit(tmp_path):
    root, backup = open_run(tmp_path, horizon=5)
    commit(root, backup, 1)
    commit(root, backup, 2)
    path = root / "u00001.state.bin"
    original = path.read_bytes()
    path.write_bytes(b"Z" + original[1:])  # same size, changed mtime/ctime
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root, backup, update=3)
    report = v.inspect_forensic_prefix(root, backup)
    assert any(a["status"] == "EVIDENCE_DAMAGED__RECORD_INTACT"
               for a in report["anomalies"])
    assert report["last_reported_probe_pass_checkpoint_update"] == 2
    assert report["last_neurally_healthy_checkpoint_proved"] is False


def test_old_telemetry_mutation_refuses_writer_with_matching_length(tmp_path):
    root, backup = open_run(tmp_path, horizon=5)
    commit(root, backup, 1)
    commit(root, backup, 2)
    path = root / "u00001.telemetry.json"
    original = path.read_bytes()
    path.write_bytes(b"X" + original[1:])
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root, backup, update=3)
    report = v.inspect_forensic_prefix(root, backup)
    assert report["anomalies"]


def test_strict_inventory_rehashes_to_detect_payload_damage_without_stat_change(
        tmp_path, monkeypatch):
    root, backup = open_run(tmp_path, horizon=3)
    commit(root, backup, 1)
    # Instrument the byte reader, but not the cache metadata, on strict audit.
    reads = _count_payload_reads(monkeypatch)
    status = v.inspect_journal(root, backup)
    assert status["last_reported_probe_pass_checkpoint_update"] == 1
    assert reads["reads"] >= 2
    assert status["resume_authorized"] is False


def test_hard_link_change_cannot_launder_an_old_state(tmp_path):
    root, backup = open_run(tmp_path, horizon=3)
    commit(root, backup, 1)
    commit(root, backup, 2)
    alias = root / "unexpected-hardlink"
    os.link(root / "u00001.state.bin", alias)
    with pytest.raises(v.JournalRefusal):
        v.begin_attempt(root, backup, update=3)
    assert v.inspect_forensic_prefix(root, backup)["anomalies"]
