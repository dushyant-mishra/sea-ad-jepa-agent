"""#561 E1 scoped mechanical fix, plus a proof of the remaining external-trust gap.

All bytes are fake. A same-writer local intent is NOT an immutable external anchor.
No neural encoder, optimizer, EMA, GPU, sealed truth, training or resume.
"""
from __future__ import annotations

import json

import pytest

from scripts.v5 import jepa_synth2048_atomic_checkpoint_bytes_v1 as c

RUN = dict(horizon=8, run_id="e1-scoped")


def start(root):
    for u in range(4):
        c.save_opaque_bytes(root, update=u, payload=f"GOOD_U{u}".encode(), **RUN)


def stop(root):
    c.save_failed_attempt_evidence(
        root, attempted_update=4, evidence_bytes=b"FAKE_ONSET_U4", **RUN)


def erase_failure_files(root, *, intent=False):
    (root / c.FAIL_EVIDENCE).unlink()
    (root / c.FAIL_RECEIPT).unlink()
    if intent:
        (root / c.FAIL_WRITE_INTENT).unlink()


def test_storage_intent_records_local_write_before_failure_bytes(tmp_path):
    root = tmp_path / "run"
    start(root)
    stop(root)
    actual = json.loads((root / c.FAIL_WRITE_INTENT).read_text())
    assert actual["kind"] == "FAILED_STOP_WRITE"
    assert actual["attempted_update"] == 4
    assert actual["externally_authenticated"] is False
    assert actual["training_authorized"] is False
    assert c.verify_storage(root, **RUN)["failed_attempt_update"] == 4


def test_local_intent_blocks_deleting_only_failure_evidence(tmp_path):
    root = tmp_path / "run"
    start(root)
    stop(root)
    erase_failure_files(root)
    with pytest.raises(c.StorageRefusal, match="UNEXPECTED_OR_GAPPED_FILES"):
        c.verify_storage(root, **RUN)
    with pytest.raises(c.StorageRefusal):
        c.save_opaque_bytes(root, update=4, payload=b"REWRITE_BAD_STOP", **RUN)


def test_local_intent_blocks_deleting_last_good_receipt_only(tmp_path):
    root = tmp_path / "run"
    start(root)
    stop(root)
    erase_failure_files(root)
    (root / "u00003.checkpoint").unlink()
    (root / "u00003.receipt.json").unlink()
    with pytest.raises(c.StorageRefusal, match="UNEXPECTED_OR_GAPPED_FILES"):
        c.verify_storage(root, **RUN)


def test_removing_local_intent_as_well_reveals_still_open_external_gap(tmp_path):
    root = tmp_path / "run"
    start(root)
    stop(root)
    original_external_candidate = c.read_local_head_proposal(root, **RUN)
    assert original_external_candidate["record_counter"] == 5
    assert original_external_candidate["status"] == "LOCAL_PROPOSAL_ONLY__NOT_EXTERNALLY_ATTESTED"
    erase_failure_files(root, intent=True)
    # The attacker can erase all same-directory markers: local-only STOP is
    # NOT sufficient. Record this negative result, do not hide it.
    altered = c.verify_storage(root, **RUN)
    assert altered["failed_attempt_recorded_as_untrusted_stop"] is False
    with pytest.raises(c.StorageRefusal, match="EXTERNAL_EXPECTED_HEAD_OR_COUNTER_MISMATCH"):
        c.compare_independent_expected_head(
            root, expected_head_sha256=original_external_candidate["head_sha256"],
            expected_record_counter=original_external_candidate["record_counter"],
            **RUN)


def test_external_expected_head_detects_tail_rewind_if_retained_independently(tmp_path):
    root = tmp_path / "run"
    start(root)
    stop(root)
    external_candidate = c.read_local_head_proposal(root, **RUN)
    erase_failure_files(root, intent=True)
    for suffix in (".checkpoint", ".receipt.json", ".write_intent.json"):
        (root / ("u00003" + suffix)).unlink()
    # All same-run artifacts are internally consistent again. Trusted
    # external expectation catches the change; source itself cannot authenticate.
    assert c.verify_storage(root, **RUN)["complete_captured_updates"] == [0, 1, 2]
    with pytest.raises(c.StorageRefusal, match="EXTERNAL_EXPECTED_HEAD_OR_COUNTER_MISMATCH"):
        c.compare_independent_expected_head(
            root, expected_head_sha256=external_candidate["head_sha256"],
            expected_record_counter=external_candidate["record_counter"], **RUN)


def test_matching_self_supplied_expected_head_does_not_grant_trust(tmp_path):
    root = tmp_path / "run"
    start(root)
    stop(root)
    candidate = c.read_local_head_proposal(root, **RUN)
    result = c.compare_independent_expected_head(
        root, expected_head_sha256=candidate["head_sha256"],
        expected_record_counter=candidate["record_counter"], **RUN)
    assert result["matched_expected_head"] is True
    assert result["independent_custody_verified"] is False
    assert result["resume_authorized"] is False
    assert result["training_authorized"] is False


@pytest.mark.parametrize(("value", "count"), [
    ("0" * 63, 5), ("G" * 64, 5), ("0" * 64, True),
    ("0" * 64, "5"), ("0" * 64, 0)
])
def test_malformed_expected_record_refuses(tmp_path, value, count):
    root = tmp_path / "run"
    start(root)
    with pytest.raises(c.StorageRefusal):
        c.compare_independent_expected_head(
            root, expected_head_sha256=value,
            expected_record_counter=count, **RUN)


def test_different_run_id_cannot_use_same_external_head(tmp_path):
    root = tmp_path / "run"
    start(root)
    candidate = c.read_local_head_proposal(root, **RUN)
    with pytest.raises(c.StorageRefusal, match="RUN_BINDING_CHANGED"):
        c.compare_independent_expected_head(
            root, horizon=8, run_id="other-run",
            expected_head_sha256=candidate["head_sha256"],
            expected_record_counter=candidate["record_counter"])


def test_corrupt_local_intent_refuses_both_normal_and_forensic_reads(tmp_path):
    root = tmp_path / "run"
    start(root)
    (root / "u00002.write_intent.json").write_bytes(b"WRONG")
    with pytest.raises(c.StorageRefusal, match="WRITE_INTENT_MISSING_OR_CHANGED"):
        c.verify_storage(root, **RUN)
    assert c.read_verified_bytes(root, update=1, **RUN) == b"GOOD_U1"
    report = c.inspect_verified_prefix_read_only(root, **RUN)
    assert report["verified_checkpoint_prefix"] == [0, 1]
    assert report["first_damaged_checkpoint_update"] == 2
    with pytest.raises(c.StorageRefusal):
        c.read_verified_bytes(root, update=2, **RUN)
    assert report["resume_authorized"] is False


def test_crash_after_write_intent_before_checkpoint_still_recovers_last_good(tmp_path, monkeypatch):
    root = tmp_path / "run"
    start(root)
    original = c._unique_file
    def crash_before_payload(dirpath, name, raw):
        if name == "u00004.checkpoint":
            raise RuntimeError("KILLED_AFTER_WRITE_INTENT")
        return original(dirpath, name, raw)
    monkeypatch.setattr(c, "_unique_file", crash_before_payload)
    with pytest.raises(RuntimeError, match="KILLED_AFTER_WRITE_INTENT"):
        c.save_opaque_bytes(root, update=4, payload=b"UNCOMMITTED_U4", **RUN)
    assert (root / "u00004.write_intent.json").is_file()
    assert c.read_verified_bytes(root, update=3, **RUN) == b"GOOD_U3"
    audit = c.inspect_verified_prefix_read_only(root, **RUN)
    assert any(x["name"] == "u00004.write_intent.json" for x in audit["uncommitted_orphans"])
    assert audit["resume_authorized"] is False
    with pytest.raises(c.StorageRefusal):
        c.verify_storage(root, **RUN)
