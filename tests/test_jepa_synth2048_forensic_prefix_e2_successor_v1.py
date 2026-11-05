"""E2 read-only forensic prefix tests. E1 erasure RED deliberately remains open.

Physical POSIX fake bytes only; no model, optimizer, EMA, training or authority.
"""
from __future__ import annotations

from hashlib import sha256
import json

import pytest

from scripts.v5 import jepa_synth2048_atomic_checkpoint_bytes_v1 as c
from tests.test_jepa_synth2048_failed_onset_journal_macha_red import (
    RUN, _orphan_failure_evidence, _orphan_next_payload, _leftover_temp,
)

def setup(root):
    for u in range(4):
        c.save_opaque_bytes(root, update=u, payload=f"GOOD_U{u}".encode(), **RUN)


@pytest.mark.parametrize(("crash", "name"), [
    (_orphan_failure_evidence, c.FAIL_EVIDENCE),
    (_orphan_next_payload, "u00004.checkpoint"),
    (_leftover_temp, ".uncommitted-0123456789abcdef0123456789abcdef"),
], ids=["failure_evidence_without_receipt", "next_payload_without_receipt", "partial_temp"])
def test_forensic_returns_only_verified_good_prefix_and_describes_orphan(tmp_path, crash, name):
    root = tmp_path / "run"
    setup(root)
    crash(root)
    report = c.inspect_verified_prefix_read_only(root, **RUN)
    assert report["verified_checkpoint_prefix"] == [0, 1, 2, 3]
    assert report["has_uncommitted_orphans"] is True
    assert report["resume_authorized"] is False
    assert report["external_head_authenticated"] is False
    assert report["full_history_completeness_proved"] is False
    assert report["training_authorized"] is False
    assert len(report["uncommitted_orphans"]) == 1
    orphan = report["uncommitted_orphans"][0]
    raw = (root / name).read_bytes()
    assert orphan == {
        "name": name, "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
        "status": "UNCOMMITTED_UNVERIFIED", "resumable": False,
    }
    assert c.read_verified_bytes(root, update=3, **RUN) == b"GOOD_U3"
    with pytest.raises(c.StorageRefusal):
        c.verify_storage(root, **RUN)
    with pytest.raises(c.StorageRefusal):
        c.save_opaque_bytes(root, update=4, payload=b"NOT_AUTHORIZED", **RUN)


def test_zero_byte_temporary_orphan_still_allows_last_good_read(tmp_path):
    root = tmp_path / "run"
    setup(root)
    name = ".uncommitted-" + "f" * 32
    (root / name).write_bytes(b"")
    result = c.inspect_verified_prefix_read_only(root, **RUN)
    assert result["uncommitted_orphans"][0]["bytes"] == 0
    assert result["uncommitted_orphans"][0]["sha256"] == sha256(b"").hexdigest()
    assert c.read_verified_bytes(root, update=3, **RUN) == b"GOOD_U3"
    with pytest.raises(c.StorageRefusal):
        c.verify_storage(root, **RUN)


@pytest.mark.parametrize(("which", "alter"), [
    ("u00002.checkpoint", b"FAKE_CONTENT"),
    ("u00002.receipt.json", b'{"fake":"receipt"}'),
])
def test_corrupted_committed_prefix_never_accepted_as_good(tmp_path, which, alter):
    root = tmp_path / "run"
    setup(root)
    _orphan_failure_evidence(root)
    (root / which).write_bytes(alter)
    with pytest.raises(c.StorageRefusal):
        c.read_verified_bytes(root, update=3, **RUN)
    with pytest.raises(c.StorageRefusal):
        c.inspect_verified_prefix_read_only(root, **RUN)


def test_missing_middle_checkpoint_is_not_disguised_as_an_orphan(tmp_path):
    root = tmp_path / "run"
    setup(root)
    for ext in (".checkpoint", ".receipt.json"):
        (root / ("u00002" + ext)).unlink()
    with pytest.raises(c.StorageRefusal, match="FORENSIC_UNKNOWN_OR_GAPPED_FILES"):
        c.read_verified_bytes(root, update=1, **RUN)


def test_orphan_receipt_only_not_assumed_to_be_power_loss(tmp_path):
    root = tmp_path / "run"
    setup(root)
    (root / "u00004.receipt.json").write_bytes(b"RECEIPT_ONLY")
    with pytest.raises(c.StorageRefusal, match="ORPHAN_PAYLOAD_OR_RECEIPT"):
        c.read_verified_bytes(root, update=3, **RUN)


def test_symlink_and_unrecognized_extra_file_refused(tmp_path):
    root = tmp_path / "run"
    setup(root)
    marker = root / (".uncommitted-" + "1" * 32)
    marker.symlink_to(root / "u00000.checkpoint")
    with pytest.raises(c.StorageRefusal, match="FORENSIC_ORPHAN_UNSAFE_TYPE"):
        c.read_verified_bytes(root, update=3, **RUN)
    marker.unlink()
    (root / "suspicious_unknown").write_bytes(b"BAD")
    with pytest.raises(c.StorageRefusal, match="FORENSIC_UNKNOWN_OR_GAPPED_FILES"):
        c.read_verified_bytes(root, update=3, **RUN)


def test_clean_prefix_still_explicitly_not_training_or_resume(tmp_path):
    root = tmp_path / "run"
    setup(root)
    report = c.inspect_verified_prefix_read_only(root, **RUN)
    assert report["has_uncommitted_orphans"] is False
    assert report["verified_checkpoint_prefix"] == [0, 1, 2, 3]
    assert report["resume_authorized"] is False
    assert report["full_history_completeness_proved"] is False
    assert report["external_head_authenticated"] is False


def test_committed_failure_record_is_still_verified(tmp_path):
    root = tmp_path / "run"
    setup(root)
    c.save_failed_attempt_evidence(
        root, attempted_update=4, evidence_bytes=b"RAW_OPAQUE_STOP", **RUN)
    report = c.inspect_verified_prefix_read_only(root, **RUN)
    assert report["verified_checkpoint_prefix"] == [0, 1, 2, 3]
    assert report["uncommitted_orphans"] == []
    (root / c.FAIL_RECEIPT).write_bytes(b"BAD_RECEIPT")
    with pytest.raises(c.StorageRefusal):
        c.read_verified_bytes(root, update=3, **RUN)
