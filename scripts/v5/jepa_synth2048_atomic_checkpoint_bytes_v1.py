#!/usr/bin/env python3
"""Real POSIX write-once *opaque byte* checkpoint storage for synthetic V5.

This stores/verifies bytes, never proves they encode a valid model, completed
optimizer update, authorized training, external provenance or biology. No torch,
GPU, EMA, model serialization, training loop, or model state loading is present.

Requires Linux/WSL POSIX hardlink + directory fsync + fcntl advisory flock.
Fail closed on orphan payload, partial receipt, gaps, untrusted symlink or SHA.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import secrets
import stat
from typing import Iterator

from scripts.v5.jepa_synth2048_checkpoint_capture_prefreeze_v1 import (
    AUTHORITY, SOURCE_FIT_SHA256, SOURCE_V5_HEAD,
    canonical_checkpoint_steps, exact_integer,
)

SCHEMA = "JEPA_SYNTH2048_ATOMIC_OPAQUE_CHECKPOINT_BYTES_V1"
STATUS = "OPAQUE_BYTES_STORAGE_ONLY__NO_TRAINING_OR_RESUME_AUTHORITY"
MAX_PAYLOAD_BYTES = 512 * 1024 * 1024
MAX_FAILED_EVIDENCE_BYTES = 8 * 1024 * 1024
FAIL_EVIDENCE = "failed_attempt.evidence"
FAIL_RECEIPT = "failed_attempt.receipt.json"
FAIL_WRITE_INTENT = "failed_attempt.write_intent.json"
INTENT_STATUS = "WRITE_STARTED_LOCAL_ONLY__NOT_EXTERNAL_TRUST"
FAIL_STATUS = "UNTRUSTED_FAILED_ATTEMPT_EVIDENCE__NONRESUMABLE_STOP"
PAYLOAD_NAME = re.compile(r"u[0-9]{5}\.checkpoint\Z")
RECEIPT_NAME = re.compile(r"u[0-9]{5}\.receipt\.json\Z")
RUN_NAME = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
FORENSIC_TEMP_NAME = re.compile(r"\.uncommitted-[0-9a-f]{32}\Z")


class StorageRefusal(RuntimeError):
    pass


def require(ok: bool, code: str) -> None:
    if not bool(ok):
        raise StorageRefusal("REFUSE_ATOMIC_OPAQUE_V5__" + code)


def _json(data: object) -> bytes:
    return (json.dumps(data, sort_keys=True, ensure_ascii=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _sha(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _fsync_directory(root: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(root, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _regular_file_bytes(path: Path, *, max_bytes: int) -> bytes:
    require(path.is_file() and not path.is_symlink(), "MISSING_SYMLINK_OR_NOT_REGULAR")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        st = os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1, "UNTRUSTED_FILE_TYPE_OR_LINK")
        require(0 < st.st_size <= max_bytes, "FILE_SIZE_OUT_OF_SCOPE")
        with os.fdopen(os.dup(fd), "rb") as stream:
            raw = stream.read(max_bytes + 1)
        require(len(raw) == st.st_size, "RACED_OR_OVERSIZED_FILE")
        st_after = os.fstat(fd)
        require((st.st_ino, st.st_size, st.st_mtime_ns) ==
                (st_after.st_ino, st_after.st_size, st_after.st_mtime_ns),
                "FILE_MUTATED_DURING_READ")
        return raw
    finally:
        os.close(fd)


def _unique_file(root: Path, filename: str, raw: bytes) -> None:
    """Write temp/fsync, atomic no-clobber link, fsync directory."""
    require(0 < len(raw) <= MAX_PAYLOAD_BYTES, "PAYLOAD_SIZE_OUT_OF_SCOPE")
    dest = root / filename
    require(not dest.exists() and not dest.is_symlink(), "DESTINATION_ALREADY_PRESENT")
    tmp = root / (".uncommitted-" + secrets.token_hex(16))
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                 getattr(os, "O_NOFOLLOW", 0), 0o600)
    linked = False
    try:
        with os.fdopen(fd, "wb", closefd=True) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        # os.replace would clobber an existing checkpoint. link(O_EXCL) doesn't.
        os.link(tmp, dest, follow_symlinks=False)
        linked = True
        os.unlink(tmp)
        _fsync_directory(root)
    finally:
        if tmp.exists() or tmp.is_symlink():
            os.unlink(tmp)
        # After a crash between link and receipt, dest is a visible orphan.
        # Never erase or reinterpret the orphan as a valid checkpoint.
        if linked:
            require(dest.is_file(), "PUBLISH_LOST")


def _validate_root(root: Path) -> None:
    require(root.is_dir() and not root.is_symlink(), "ROOT_NOT_REAL_DIRECTORY")
    require(root.resolve() == root.absolute(), "ROOT_PATH_UNTRUSTED")


@contextmanager
def _locked(root: Path) -> Iterator[None]:
    _validate_root(root)
    p = root / ".writer.lock"
    fd = os.open(p, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        st = os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1, "LOCK_NOT_REGULAR")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def expected_run_lock(*, horizon: int, run_id: str,
                      source_head: str = SOURCE_V5_HEAD,
                      fit_sha: str = SOURCE_FIT_SHA256) -> dict:
    n = exact_integer(horizon, "HORIZON")
    require(n > 0 and type(run_id) is str and RUN_NAME.fullmatch(run_id),
            "HORIZON_OR_RUN_ID")
    require(source_head == SOURCE_V5_HEAD and fit_sha == SOURCE_FIT_SHA256,
            "SOURCE_OR_DATA_RIGHTS_CHANGED")
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "run_id": run_id,
        "horizon": n,
        "source_head": source_head,
        "fit_sha256": fit_sha,
        "training_authorized": False,
        "model_state_authenticated": False,
        "completed_optimizer_or_ema_proved": False,
        "external_trust_anchor_present": False,
        "authority": AUTHORITY,
    }



def _write_intent(lock: dict, *, attempted_update: int, kind: str,
                  prior_checkpoint_receipt_sha256: str | None) -> dict:
    require(kind in ("CHECKPOINT_WRITE", "FAILED_STOP_WRITE")
            and type(attempted_update) is int and attempted_update >= 0,
            "BAD_WRITE_INTENT")
    return {
        "schema": SCHEMA,
        "status": INTENT_STATUS,
        "run_lock_sha256": _sha(_json(lock)),
        "attempted_update": attempted_update,
        "kind": kind,
        "previous_checkpoint_receipt_sha256": prior_checkpoint_receipt_sha256,
        "training_authorized": False,
        "externally_authenticated": False,
    }


def _require_write_intent(root: Path, filename: str, expected: dict) -> None:
    raw = _regular_file_bytes(root / filename, max_bytes=2048)
    require(raw == _json(expected), "WRITE_INTENT_MISSING_OR_CHANGED")


def _head_proposal(lock: dict, receipts: list[dict], failure: dict | None) -> dict:
    """Local SHA-chain head for comparison with a separately retained record.

    The writer can fabricate this entire value. Only a genuinely external
    custodian can make this comparison evidence against full tail deletion.
    """
    prior = _sha(_json(receipts[-1])) if receipts else None
    return {
        "run_lock_sha256": _sha(_json(lock)),
        "record_counter": len(receipts) + (1 if failure is not None else 0),
        "last_checkpoint_update": receipts[-1]["update"] if receipts else None,
        "last_checkpoint_receipt_sha256": prior,
        "last_failed_attempt_update": (
            failure["attempted_update"] if failure is not None else None),
        "failed_attempt_receipt_sha256": (
            _sha(_json(failure)) if failure is not None else None),
    }


def read_local_head_proposal(root: Path, *, horizon: int, run_id: str) -> dict:
    """Read a *self-declared* current head to hand to an external custodian.

    DO NOT use a value fetched from the suspect directory as its own anchor.
    """
    root = Path(root)
    with _locked(root):
        lock = expected_run_lock(horizon=horizon, run_id=run_id)
        require(_regular_file_bytes(root / "run.lock.json", max_bytes=2048)
                == _json(lock), "RUN_BINDING_CHANGED")
        receipts = _scan(root, lock)
        failure = _failed_attempt_record(root, lock, receipts)
        head = _head_proposal(lock, receipts, failure)
        return {
            "head_sha256": _sha(_json(head)),
            "record_counter": head["record_counter"],
            "head": head,
            "status": "LOCAL_PROPOSAL_ONLY__NOT_EXTERNALLY_ATTESTED",
            "training_authorized": False,
        }


def compare_independent_expected_head(root: Path, *, horizon: int, run_id: str,
                                      expected_head_sha256: str,
                                      expected_record_counter: int) -> dict:
    """Fail closed against an independently retained expected head and count.

    The external record is NOT obtained or authenticated here. The caller
    must independently establish its issuer, immutability and freshness.
    """
    require(type(expected_head_sha256) is str and len(expected_head_sha256) == 64
            and all(c in "0123456789abcdef" for c in expected_head_sha256),
            "EXPECTED_HEAD_FORMAT")
    require(type(expected_record_counter) is int and expected_record_counter >= 1,
            "EXPECTED_COUNTER_FORMAT")
    current = read_local_head_proposal(root, horizon=horizon, run_id=run_id)
    require(current["head_sha256"] == expected_head_sha256
            and current["record_counter"] == expected_record_counter,
            "EXTERNAL_EXPECTED_HEAD_OR_COUNTER_MISMATCH")
    return {
        "status": "MATCHED_CALLER_SUPPLIED_EXPECTATION_ONLY",
        "matched_expected_head": True,
        "independent_custody_verified": False,
        "resume_authorized": False,
        "training_authorized": False,
        "authority": AUTHORITY,
    }


def _failed_attempt_record(root: Path, lock: dict, previous: list[dict]) -> dict | None:
    """Validate actual failed-attempt evidence bytes, never a resumable state."""
    data_path = root / FAIL_EVIDENCE
    receipt_path = root / FAIL_RECEIPT
    has_data = data_path.exists() or data_path.is_symlink()
    has_receipt = receipt_path.exists() or receipt_path.is_symlink()
    require(has_data == has_receipt, "ORPHAN_FAILED_ATTEMPT_EVIDENCE")
    if not has_data:
        return None
    require(bool(previous), "FAILURE_BEFORE_VALID_U0")
    data = _regular_file_bytes(data_path, max_bytes=MAX_FAILED_EVIDENCE_BYTES)
    receipt_bytes = _regular_file_bytes(receipt_path, max_bytes=4096)
    try:
        record = json.loads(receipt_bytes)
    except (ValueError, UnicodeError) as exc:
        raise StorageRefusal("REFUSE_ATOMIC_OPAQUE_V5__BAD_FAILURE_RECEIPT") from exc
    require(type(record) is dict and _json(record) == receipt_bytes,
            "NONCANONICAL_FAILURE_RECEIPT")
    expected_fields = {
        "schema", "status", "attempted_update", "last_valid_checkpoint_update",
        "run_lock_sha256", "evidence_sha256", "evidence_bytes",
        "previous_checkpoint_receipt_sha256", "resumable", "training_authorized",
        "external_authentication",
    }
    require(set(record) == expected_fields, "FAILURE_RECEIPT_FIELDS_CHANGED")
    attempted = record.get("attempted_update")
    require(type(attempted) is int
            and previous[-1]["update"] < attempted <= lock["horizon"] + 1,
            "BAD_FAILED_ATTEMPT_POSITION")
    require(record == {
        "schema": SCHEMA,
        "status": FAIL_STATUS,
        "attempted_update": attempted,
        "last_valid_checkpoint_update": previous[-1]["update"],
        "run_lock_sha256": _sha(_json(lock)),
        "evidence_sha256": _sha(data),
        "evidence_bytes": len(data),
        "previous_checkpoint_receipt_sha256": _sha(_json(previous[-1])),
        "resumable": False,
        "training_authorized": False,
        "external_authentication": False,
    }, "FAILED_EVIDENCE_SHA_OR_CHAIN_DRIFT")
    return record



def _uncommitted_descriptor(root: Path, filename: str, max_bytes: int) -> dict:
    """Read suspect orphan bytes without granting committed status.

    A missing/partial receipt cannot authenticate an orphaned payload.
    """
    path = root / filename
    require(path.is_file() and not path.is_symlink(),
            "FORENSIC_ORPHAN_UNSAFE_TYPE")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        st = os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1
                and 0 <= st.st_size <= max_bytes,
                "FORENSIC_ORPHAN_BAD_FILE")
        with os.fdopen(os.dup(fd), "rb") as stream:
            raw = stream.read(max_bytes + 1)
        end = os.fstat(fd)
        require(len(raw) == st.st_size
                and (st.st_ino, st.st_size, st.st_mtime_ns)
                == (end.st_ino, end.st_size, end.st_mtime_ns),
                "FORENSIC_ORPHAN_RACED")
        return {
            "name": filename, "bytes": len(raw), "sha256": _sha(raw),
            "status": "UNCOMMITTED_UNVERIFIED", "resumable": False,
        }
    finally:
        os.close(fd)


def _scan(root: Path, lock: dict, *,
          forensic_orphans: list[dict] | None = None) -> list[dict]:
    """Verify the committed prefix; forensic mode reports only trailing orphans."""
    expected = canonical_checkpoint_steps(lock["horizon"])
    allowed = {".writer.lock", "run.lock.json"}
    receipts: list[dict] = []
    prev_digest = None
    for u in expected:
        name = f"u{u:05d}"
        payload = root / (name + ".checkpoint")
        receipt = root / (name + ".receipt.json")
        p_exists = payload.exists() or payload.is_symlink()
        r_exists = receipt.exists() or receipt.is_symlink()
        if p_exists != r_exists:
            if forensic_orphans is not None and p_exists and not r_exists:
                # Only the next scheduled payload may be an orphan.
                allowed.add(payload.name)
                forensic_orphans.append(_uncommitted_descriptor(
                    root, payload.name, MAX_PAYLOAD_BYTES))
                break
            require(False, "ORPHAN_PAYLOAD_OR_RECEIPT")
        if not p_exists:
            # Later numbered checkpoints are rejected by the file allowlist.
            break
        raw = _regular_file_bytes(payload, max_bytes=MAX_PAYLOAD_BYTES)
        receipt_raw = _regular_file_bytes(receipt, max_bytes=4096)
        try:
            obj = json.loads(receipt_raw)
        except (ValueError, UnicodeError) as exc:
            raise StorageRefusal("REFUSE_ATOMIC_OPAQUE_V5__BAD_RECEIPT_JSON") from exc
        require(_json(obj) == receipt_raw and type(obj) is dict,
                "NONCANONICAL_RECEIPT")
        require(set(obj) == {"schema", "status", "update", "run_lock_sha256",
                              "payload_sha256", "payload_bytes", "previous_receipt_sha256",
                              "training_authorized"}, "RECEIPT_FIELDS")
        require(obj == {
            "schema": SCHEMA,
            "status": STATUS,
            "update": u,
            "run_lock_sha256": _sha(_json(lock)),
            "payload_sha256": _sha(raw),
            "payload_bytes": len(raw),
            "previous_receipt_sha256": prev_digest,
            "training_authorized": False,
        }, "CHECKPOINT_SHA_OR_PARENT_LINK_DRIFT")
        _require_write_intent(
            root, name + ".write_intent.json",
            _write_intent(lock, attempted_update=u, kind="CHECKPOINT_WRITE",
                          prior_checkpoint_receipt_sha256=prev_digest))
        prev_digest = _sha(receipt_raw)
        receipts.append(obj)
        allowed.update({payload.name, receipt.name, name + ".write_intent.json"})
    has_failure_data = (root / FAIL_EVIDENCE).exists() or (root / FAIL_EVIDENCE).is_symlink()
    has_failure_receipt = (root / FAIL_RECEIPT).exists() or (root / FAIL_RECEIPT).is_symlink()
    if has_failure_data and not has_failure_receipt and forensic_orphans is not None:
        # Data without commit-last receipt is only an unverified artifact.
        allowed.add(FAIL_EVIDENCE)
        forensic_orphans.append(_uncommitted_descriptor(
            root, FAIL_EVIDENCE, MAX_FAILED_EVIDENCE_BYTES))
    else:
        failure = _failed_attempt_record(root, lock, receipts)
        if failure is not None:
            _require_write_intent(
                root, FAIL_WRITE_INTENT,
                _write_intent(
                    lock, attempted_update=failure["attempted_update"],
                    kind="FAILED_STOP_WRITE",
                    prior_checkpoint_receipt_sha256=(
                        _sha(_json(receipts[-1])) if receipts else None)))
            allowed.update((FAIL_EVIDENCE, FAIL_RECEIPT, FAIL_WRITE_INTENT))
    # Read-only forensics can label an interrupted write-intent as an orphan.
    # It remains unverified and never enters the checkpoint receipt chain.
    if forensic_orphans is not None:
        next_step = expected[len(receipts)] if len(receipts) < len(expected) else None
        expected_intents = {}
        previous = _sha(_json(receipts[-1])) if receipts else None
        if next_step is not None:
            expected_intents[f"u{next_step:05d}.write_intent.json"] = (
                _write_intent(lock, attempted_update=next_step,
                              kind="CHECKPOINT_WRITE",
                              prior_checkpoint_receipt_sha256=previous))
        if receipts:
            for attempt in range(receipts[-1]["update"] + 1, lock["horizon"] + 2):
                # Only a single failed-stop intent for the immediate successor
                # is a plausible tail. Do not accept arbitrary backdating.
                if attempt != receipts[-1]["update"] + 1:
                    break
                expected_intents[FAIL_WRITE_INTENT] = (
                    _write_intent(lock, attempted_update=attempt,
                                  kind="FAILED_STOP_WRITE",
                                  prior_checkpoint_receipt_sha256=previous))
        for name, expected_obj in expected_intents.items():
            path = root / name
            if name not in allowed and (path.exists() or path.is_symlink()):
                _require_write_intent(root, name, expected_obj)
                allowed.add(name)
                forensic_orphans.append(_uncommitted_descriptor(
                    root, name, 2048))
    names = {p.name for p in root.iterdir()}
    if forensic_orphans is None:
        require(names == allowed, "UNEXPECTED_OR_GAPPED_FILES")
    else:
        for name in sorted(names - allowed):
            require(FORENSIC_TEMP_NAME.fullmatch(name) is not None,
                    "FORENSIC_UNKNOWN_OR_GAPPED_FILES")
            forensic_orphans.append(_uncommitted_descriptor(
                root, name, MAX_PAYLOAD_BYTES))
    return receipts


def verify_storage(root: Path, *, horizon: int, run_id: str,
                   source_head: str = SOURCE_V5_HEAD,
                   fit_sha: str = SOURCE_FIT_SHA256) -> dict:
    """Fresh-process verifiable SHA chain, not a trusted model/optimizer proof."""
    lock = expected_run_lock(horizon=horizon, run_id=run_id,
                             source_head=source_head, fit_sha=fit_sha)
    with _locked(Path(root)):
        raw = _regular_file_bytes(Path(root) / "run.lock.json", max_bytes=2048)
        require(raw == _json(lock), "RUN_BINDING_OR_HORIZON_CHANGED")
        receipts = _scan(Path(root), lock)
        failure = _failed_attempt_record(Path(root), lock, receipts)
    return {
        "schema": SCHEMA, "status": STATUS,
        "complete_captured_updates": [r["update"] for r in receipts],
        "failed_attempt_recorded_as_untrusted_stop": failure is not None,
        "failed_attempt_update": (failure["attempted_update"] if failure else None),
        "last_good_checkpoint_before_failure": (
            failure["last_valid_checkpoint_update"] if failure else None
        ),
        "failed_attempt_not_model_resumable": True,
        "latest_receipt_sha256": _sha(_json(receipts[-1])) if receipts else None,
        "physical_byte_sha_verified": True,
        "model_state_authenticated": False, "optimizer_or_ema_proved": False,
        "replay_determinism_proved": False, "training_authorized": False,
        "authority": AUTHORITY,
    }


def save_opaque_bytes(root: Path, *, horizon: int, run_id: str,
                      update: int, payload: bytes) -> dict:
    """Actual disk/fsync persistence; never label byte payload 'valid model'."""
    require(type(update) is int, "UPDATE_NOT_INTEGER")
    lock = expected_run_lock(horizon=horizon, run_id=run_id)
    require(type(payload) is bytes and 0 < len(payload) <= MAX_PAYLOAD_BYTES,
            "OPAQUE_BYTES_REQUIRED")
    root = Path(root)
    require(not root.is_symlink(), "SYMLINK_ROOT")
    root.mkdir(mode=0o700, parents=False, exist_ok=True)
    with _locked(root):
        marker = root / "run.lock.json"
        if not marker.exists() and not marker.is_symlink():
            # Only create initial binding if root has no other contents
            # beyond our advisory lock.
            require({p.name for p in root.iterdir()} == {".writer.lock"},
                    "RUN_ALREADY_HAS_UNBOUND_FILES")
            _unique_file(root, marker.name, _json(lock))
        require(_regular_file_bytes(marker, max_bytes=2048) == _json(lock),
                "RUN_BINDING_CHANGED")
        previous = _scan(root, lock)
        require(_failed_attempt_record(root, lock, previous) is None,
                "FAILED_RUN_CLOSED_NO_NEW_MODEL_SNAPSHOT")
        steps = canonical_checkpoint_steps(horizon)
        require(len(previous) < len(steps), "CHECKPOINT_SERIES_COMPLETE")
        require(update == steps[len(previous)], "SKIPPED_OR_DUPLICATE_CHECKPOINT")
        prev = _sha(_json(previous[-1])) if previous else None
        label = f"u{update:05d}"
        # Write-ahead *storage* intent. This is NOT evidence of a true
        # neural optimizer attempt, and is removable by the same writer.
        _unique_file(
            root, label + ".write_intent.json",
            _json(_write_intent(
                lock, attempted_update=update, kind="CHECKPOINT_WRITE",
                prior_checkpoint_receipt_sha256=prev)))
        _unique_file(root, label + ".checkpoint", payload)
        entry = {
            "schema": SCHEMA, "status": STATUS, "update": update,
            "run_lock_sha256": _sha(_json(lock)),
            "payload_sha256": _sha(payload), "payload_bytes": len(payload),
            "previous_receipt_sha256": prev, "training_authorized": False,
        }
        # Receipt is committed last: any crash before it causes a hard STOP.
        _unique_file(root, label + ".receipt.json", _json(entry))
        _scan(root, lock)
    return entry


def save_failed_attempt_evidence(
    root: Path, *, horizon: int, run_id: str,
    attempted_update: int, evidence_bytes: bytes,
) -> dict:
    """Durably keep one STOP observation after u0; NOT a checkpoint or gate.

    This does NOT observe optimizer state, gradients, EMA or biological context.
    Caller must supply genuine evidence separately. It cannot vouch for bytes.
    """
    require(type(attempted_update) is int, "FAILED_ATTEMPT_UPDATE_TYPE")
    require(type(evidence_bytes) is bytes
            and 0 < len(evidence_bytes) <= MAX_FAILED_EVIDENCE_BYTES,
            "FAILED_ATTEMPT_BYTES_REQUIRED")
    lock = expected_run_lock(horizon=horizon, run_id=run_id)
    root = Path(root)
    with _locked(root):
        require(_regular_file_bytes(root / "run.lock.json", max_bytes=2048)
                == _json(lock), "RUN_BINDING_CHANGED")
        previous = _scan(root, lock)
        require(bool(previous), "FAILURE_BEFORE_VALID_U0")
        require(_failed_attempt_record(root, lock, previous) is None,
                "FAILURE_ALREADY_RECORDED")
        require(previous[-1]["update"] < attempted_update <= horizon + 1,
                "FAILED_ATTEMPT_ORDER")
        record = {
            "schema": SCHEMA,
            "status": FAIL_STATUS,
            "attempted_update": attempted_update,
            "last_valid_checkpoint_update": previous[-1]["update"],
            "run_lock_sha256": _sha(_json(lock)),
            "evidence_sha256": _sha(evidence_bytes),
            "evidence_bytes": len(evidence_bytes),
            "previous_checkpoint_receipt_sha256": _sha(_json(previous[-1])),
            "resumable": False,
            "training_authorized": False,
            "external_authentication": False,
        }
        # The intent must precede *storage* of failure evidence. Actual
        # optimizer-attempt intent and external custody remain separate tasks.
        _unique_file(
            root, FAIL_WRITE_INTENT,
            _json(_write_intent(
                lock, attempted_update=attempted_update,
                kind="FAILED_STOP_WRITE",
                prior_checkpoint_receipt_sha256=_sha(_json(previous[-1])))))
        # Commit last. Abrupt death between writes leaves a refused orphan.
        _unique_file(root, FAIL_EVIDENCE, evidence_bytes)
        _unique_file(root, FAIL_RECEIPT, _json(record))
        _scan(root, lock)
    return record


def read_verified_failed_attempt_evidence(
    root: Path, *, horizon: int, run_id: str,
) -> bytes:
    """Returns SHA-checked STOP bytes without granting any model resume."""
    root = Path(root)
    with _locked(root):
        lock = expected_run_lock(horizon=horizon, run_id=run_id)
        require(_regular_file_bytes(root / "run.lock.json", max_bytes=2048)
                == _json(lock), "RUN_BINDING_CHANGED")
        previous = _scan(root, lock)
        require(_failed_attempt_record(root, lock, previous) is not None,
                "NO_FAILED_ATTEMPT")
        return _regular_file_bytes(root / FAIL_EVIDENCE,
                                   max_bytes=MAX_FAILED_EVIDENCE_BYTES)


def inspect_verified_prefix_read_only(root: Path, *, horizon: int,
                                      run_id: str) -> dict:
    """Recover receipt-verified prefix and document suspect orphaned tail bytes.

    This does not detect erased tail records without an independent external
    anchor. Resume always remains refused (Macha #561 E1 still open).
    """
    root = Path(root)
    with _locked(root):
        lock = expected_run_lock(horizon=horizon, run_id=run_id)
        require(_regular_file_bytes(root / "run.lock.json", max_bytes=2048)
                == _json(lock), "RUN_BINDING_CHANGED")
        orphans: list[dict] = []
        receipts = _scan(root, lock, forensic_orphans=orphans)
        return {
            "status": "FORENSIC_READ_ONLY__NO_RESUME_AUTHORITY",
            "verified_checkpoint_prefix": [r["update"] for r in receipts],
            "latest_verified_receipt_sha256": (
                _sha(_json(receipts[-1])) if receipts else None),
            "uncommitted_orphans": orphans,
            "has_uncommitted_orphans": bool(orphans),
            "external_head_authenticated": False,
            "full_history_completeness_proved": False,
            "resume_authorized": False,
            "training_authorized": False,
            "authority": AUTHORITY,
        }


def read_verified_bytes(root: Path, *, horizon: int, run_id: str,
                        update: int) -> bytes:
    """Read a committed prefix, even if a later write was interrupted.

    Strict verify_storage and both writer entry points still reject orphans.
    This is a forensic opaque-byte read, never a model load or resume.
    """
    require(type(update) is int, "UPDATE_NOT_INTEGER")
    root = Path(root)
    with _locked(root):
        lock = expected_run_lock(horizon=horizon, run_id=run_id)
        require(_regular_file_bytes(root / "run.lock.json", max_bytes=2048)
                == _json(lock), "RUN_BINDING_CHANGED")
        orphans: list[dict] = []
        checked = _scan(root, lock, forensic_orphans=orphans)
        matches = [r for r in checked if r["update"] == update]
        require(len(matches) == 1, "UPDATE_NOT_VERIFIED_OR_MISSING")
        data = _regular_file_bytes(root / f"u{update:05d}.checkpoint",
                                   max_bytes=MAX_PAYLOAD_BYTES)
        require(_sha(data) == matches[0]["payload_sha256"],
                "CHECKPOINT_CHANGED_AFTER_FORENSIC_SCAN")
    return data


def main() -> None:
    ap = argparse.ArgumentParser(description="Verify only; never train/restore model")
    ap.add_argument("--verify-root", required=True, type=Path)
    ap.add_argument("--horizon", required=True, type=int)
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()
    print(json.dumps(verify_storage(args.verify_root, horizon=args.horizon,
                                    run_id=args.run_id), sort_keys=True))


if __name__ == "__main__":
    main()
