"""Macha RED against #564 head 5cd20a41 (on #563 0acbf164; tests only; code UNCHANGED).

The forensic read must recover the last healthy checkpoint whenever its own receipt chain is
intact. Two realistic cases still make every read refuse.

E3a, damage to a LATER file. Disk corruption or a partial copy of the newest checkpoint u3
(payload or receipt) makes reading the intact u2 refuse, because the whole scan refuses.
If collapse onset was at u3, the last healthy state is lost together with the onset.
(This is the descendant-to-ancestor direction. Corrupting u2 and refusing u3 is correct
and stays so.)

E3b, a failure between sparse checkpoints (a #564 regression of the #563 E2 fix).
#553's grid checkpoints every fifth update after u40, and the writer accepts a failed
attempt anywhere in (last checkpoint, horizon+1]. A crash while recording a failure at u43
(last checkpoint u40) leaves `failed_attempt.write_intent.json` for attempt 43. The forensic
reader expects only attempt 41, so it refuses, and u40 becomes unreadable. The same crash
at #563 reads u40.

Repair-agnostic: the intact prefix must be readable as opaque bytes, while strict
verification and resume still refuse.

Fake bytes only. No model, optimizer, training, GPU or Stage 4.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import pytest

from scripts.v5 import jepa_synth2048_atomic_checkpoint_bytes_v1 as c

RUN8 = dict(horizon=8, run_id="macha-e3a")
RUN60 = dict(horizon=60, run_id="macha-e3b")


def _good(root, run, last):
    for u in c.canonical_checkpoint_steps(run["horizon"]):
        if u > last:
            break
        c.save_opaque_bytes(root, update=u, payload=f"GOOD_U{u}".encode(), **run)


def _flip_last_byte(path):
    raw = bytearray(path.read_bytes())
    raw[-1] ^= 0x01
    path.write_bytes(bytes(raw))


@pytest.mark.parametrize("damaged", ["u00003.checkpoint", "u00003.receipt.json"])
def test_red_damage_to_newest_checkpoint_must_not_hide_intact_last_healthy(tmp_path, damaged):
    root = tmp_path / "run"
    _good(root, RUN8, 3)
    _flip_last_byte(root / damaged)
    with pytest.raises(c.StorageRefusal):
        c.verify_storage(root, **RUN8)          # strict still refuses: correct
    try:
        assert c.read_verified_bytes(root, update=2, **RUN8) == b"GOOD_U2"
    except c.StorageRefusal as exc:
        pytest.fail(f"intact u2 unreadable because later {damaged} is damaged: {exc}")


@pytest.mark.parametrize("crash_before", [c.FAIL_EVIDENCE, c.FAIL_RECEIPT])
def test_red_crash_recording_a_failure_between_sparse_checkpoints_keeps_last_good(
        tmp_path, monkeypatch, crash_before):
    root = tmp_path / "run"
    _good(root, RUN60, 40)
    original = c._unique_file

    def die(dirpath, name, raw):
        if name == crash_before:
            raise RuntimeError("KILLED_DURING_FAILURE_RECORD")
        return original(dirpath, name, raw)

    monkeypatch.setattr(c, "_unique_file", die)
    with pytest.raises(RuntimeError, match="KILLED_DURING_FAILURE_RECORD"):
        c.save_failed_attempt_evidence(root, attempted_update=43,
                                       evidence_bytes=b"ONSET_U43", **RUN60)
    monkeypatch.setattr(c, "_unique_file", original)
    with pytest.raises(c.StorageRefusal):
        c.verify_storage(root, **RUN60)         # strict still refuses: correct
    try:
        assert c.read_verified_bytes(root, update=40, **RUN60) == b"GOOD_U40"
    except c.StorageRefusal as exc:
        pytest.fail(f"crash recording failed u43 makes last good u40 unreadable: {exc}")
