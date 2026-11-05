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
FAIL_STATUS = "UNTRUSTED_FAILED_ATTEMPT_EVIDENCE__NONRESUMABLE_STOP"
PAYLOAD_NAME = re.compile(r"u[0-9]{5}\.checkpoint\Z")
RECEIPT_NAME = re.compile(r"u[0-9]{5}\.receipt\.json\Z")
RUN_NAME = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")


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


def _scan(root: Path, lock: dict) -> list[dict]:
    """Verify strict linked receipt prefix, exact SHA and no orphans."""
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
        require(p_exists == r_exists, "ORPHAN_PAYLOAD_OR_RECEIPT")
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
        prev_digest = _sha(receipt_raw)
        receipts.append(obj)
        allowed.update({payload.name, receipt.name})
    failure = _failed_attempt_record(root, lock, receipts)
    if failure is not None:
        allowed.update((FAIL_EVIDENCE, FAIL_RECEIPT))
    names = {p.name for p in root.iterdir()}
    require(names == allowed, "UNEXPECTED_OR_GAPPED_FILES")
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


def read_verified_bytes(root: Path, *, horizon: int, run_id: str,
                        update: int) -> bytes:
    """Return only SHA-verified opaque data, not a loaded or authorized model."""
    require(type(update) is int, "UPDATE_NOT_INTEGER")
    root = Path(root)
    with _locked(root):
        lock = expected_run_lock(horizon=horizon, run_id=run_id)
        require(_regular_file_bytes(root / "run.lock.json", max_bytes=2048)
                == _json(lock), "RUN_BINDING_CHANGED")
        checked = _scan(root, lock)
        require(update in [r["update"] for r in checked],
                "UPDATE_NOT_VERIFIED_OR_MISSING")
        data = _regular_file_bytes(root / f"u{update:05d}.checkpoint",
                                   max_bytes=MAX_PAYLOAD_BYTES)
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
