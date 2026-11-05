#!/usr/bin/env python3
"""Independent-directory-backed V5 journal V2 -- FAKE OPAQUE BYTES ONLY.

No optimizer, neural model, biological measurement, GPU, restore or training.
This is an append-only storage/state-machine substrate, NOT an authorized
trainer or an independently authenticated scientific checkpoint.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import fcntl
import json
import os
from pathlib import Path
import re
import secrets
import stat
from typing import Iterator

from scripts.v5 import jepa_synth2048_checkpoint_capture_prefreeze_v1 as cause

SCHEMA = "JEPA_SYNTH2048_ATTEMPT_JOURNAL_V2"
AUTHORITY = cause.AUTHORITY
MAX_STATE = 512 * 1024 * 1024
MAX_TELEMETRY = 8 * 1024 * 1024
MAX_RECORD = 8192
RECORD_NAME = re.compile(r"j[0-9]{8}\.json\Z")
STATE_NAME = re.compile(r"u[0-9]{5}\.state\.bin\Z")
TELEMETRY_NAME = re.compile(r"u[0-9]{5}\.telemetry\.json\Z")
RUN_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
SHA_NAME = re.compile(r"[0-9a-f]{64}\Z")
FINALS = {"STATE_COLLAPSED", "ATTEMPT_FAILED", "ATTEMPT_ABORTED"}
OUTCOMES = FINALS | {"UPDATE_COMMITTED"}


class JournalRefusal(RuntimeError):
    pass


def insist(ok: bool, name: str) -> None:
    if not bool(ok):
        raise JournalRefusal("REFUSE_ATTEMPT_JOURNAL_V2__" + name)


def _json(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def _sha(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _dir(path: Path) -> None:
    insist(path.is_dir() and not path.is_symlink()
           and path.resolve() == path.absolute(), "DIRECTORY_UNTRUSTED")


def _paths(root: Path, custody: Path) -> tuple[Path, Path]:
    root, custody = Path(root).absolute(), Path(custody).absolute()
    _dir(root)
    _dir(custody)
    insist(root != custody and root not in custody.parents
           and custody not in root.parents, "CUSTODY_MUST_BE_OUTSIDE_RUN")
    return root, custody


def _fsync_dir(root: Path) -> None:
    fd = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                 | getattr(os, "O_NOFOLLOW", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextmanager
def _lock(root: Path) -> Iterator[None]:
    _dir(root)
    p = root / ".writer.lock"
    fd = os.open(p, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        st = os.fstat(fd)
        insist(stat.S_ISREG(st.st_mode) and st.st_nlink == 1, "UNSAFE_LOCK")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _read(path: Path, limit: int) -> bytes:
    insist(path.is_file() and not path.is_symlink(), "FILE_MISSING_OR_UNSAFE")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        st = os.fstat(fd)
        insist(stat.S_ISREG(st.st_mode) and st.st_nlink == 1
               and 0 < st.st_size <= limit, "FILE_SIZE_OR_TYPE")
        with os.fdopen(os.dup(fd), "rb") as stream:
            raw = stream.read(limit + 1)
        end = os.fstat(fd)
        insist(len(raw) == st.st_size and
               (st.st_ino, st.st_size, st.st_mtime_ns) ==
               (end.st_ino, end.st_size, end.st_mtime_ns),
               "FILE_RACED")
        return raw
    finally:
        os.close(fd)


def _write_once(root: Path, name: str, raw: bytes, maximum: int) -> None:
    insist(0 < len(raw) <= maximum, "PAYLOAD_SIZE")
    dest = root / name
    insist(not dest.exists() and not dest.is_symlink(), "NO_CLOBBER")
    tmp = root / (".uncommitted-" + secrets.token_hex(16))
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                 | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(tmp, dest, follow_symlinks=False)
        os.unlink(tmp)
        _fsync_dir(root)
    finally:
        if tmp.exists() or tmp.is_symlink():
            tmp.unlink()


def _receipt(root: Path, name: str, max_bytes: int) -> dict:
    raw = _read(root / name, max_bytes)
    try:
        record = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise JournalRefusal("REFUSE_ATTEMPT_JOURNAL_V2__BAD_JSON") from exc
    insist(type(record) is dict and _json(record) == raw,
           "NONCANONICAL_JSON")
    return record


def _run_lock(*, run_id: str, horizon: int, panel_sha256: str,
              config_sha256: str, rights_sha256: str) -> dict:
    insist(type(run_id) is str and RUN_ID.fullmatch(run_id) is not None,
           "RUN_ID")
    insist(type(horizon) is int and 1 <= horizon <= 99999, "HORIZON")
    for name, val in (("PANEL", panel_sha256), ("CONFIG", config_sha256),
                      ("RIGHTS", rights_sha256)):
        insist(type(val) is str and SHA_NAME.fullmatch(val) is not None, name)
    return {
        "schema": SCHEMA, "run_id": run_id, "planned_horizon": horizon,
        "schedule": "EVERY_SUCCESSFUL_UPDATE",
        "panel_sha256": panel_sha256, "config_sha256": config_sha256,
        "rights_sha256": rights_sha256,
        "external_copy": "SEPARATE_OUTSIDE_RUN_DIR__UNSIGNED",
        "true_neural_state_verified": False, "training_authorized": False,
        "authority": AUTHORITY,
    }


def _binding(root: Path, custody: Path) -> dict:
    first = _read(root / "run.lock.json", MAX_RECORD)
    insist(first == _read(custody / "run.lock.json", MAX_RECORD),
           "EXTERNAL_RUN_BINDING_MISMATCH")
    lock = _receipt(root, "run.lock.json", MAX_RECORD)
    insist(lock.get("schema") == SCHEMA
           and lock.get("schedule") == "EVERY_SUCCESSFUL_UPDATE"
           and lock.get("authority") == AUTHORITY,
           "RUN_BINDING_INVALID")
    insist(lock == _run_lock(
        run_id=lock["run_id"], horizon=lock["planned_horizon"],
        panel_sha256=lock["panel_sha256"],
        config_sha256=lock["config_sha256"],
        rights_sha256=lock["rights_sha256"]), "RUN_BINDING_DRIFT")
    return lock


def _filenames(root: Path) -> list[str]:
    return sorted(p.name for p in root.iterdir() if RECORD_NAME.fullmatch(p.name))


def _reference(raw: bytes, name: str) -> dict:
    return {"name": name, "sha256": _sha(raw), "bytes": len(raw)}


def _record(*, kind: str, seq: int, previous: str | None,
            lock: dict, update: int, payload: dict | None,
            telemetry: dict | None, reported: dict | None = None) -> dict:
    return {
        "schema": SCHEMA, "kind": kind, "seq": seq,
        "previous_sha256": previous, "run_lock_sha256": _sha(_json(lock)),
        "update": update, "payload": payload, "telemetry": telemetry,
        "reported": reported, "training_authorized": False,
    }


def _expected_next(rows: list[dict], lock: dict) -> tuple[set[str], int]:
    if not rows:
        return {"RUN_OPEN"}, 0
    end = rows[-1]
    kind, update = end["kind"], end["update"]
    if kind == "RUN_OPEN":
        return {"ATTEMPT_BEGIN"}, 1
    if kind == "ATTEMPT_BEGIN":
        return OUTCOMES, update
    if kind == "UPDATE_COMMITTED":
        if update == lock["planned_horizon"]:
            return {"RUN_CLOSED"}, update
        return {"ATTEMPT_BEGIN"}, update + 1
    if kind in FINALS:
        return {"RUN_CLOSED"}, update
    return set(), -1


def _check_record(row: dict, rows: list[dict], lock: dict, root: Path) -> None:
    allowed, u = _expected_next(rows, lock)
    insist(type(row) is dict and set(row) == {
        "schema", "kind", "seq", "previous_sha256", "run_lock_sha256",
        "update", "payload", "telemetry", "reported", "training_authorized",
    }, "RECORD_FIELD_SHAPE")
    insist(row["kind"] in allowed and type(row["update"]) is int
           and row["update"] == u, "ILLEGAL_ATTEMPT_TRANSITION")
    insist(row["schema"] == SCHEMA
           and type(row["seq"]) is int and row["seq"] == len(rows)
           and row["training_authorized"] is False
           and row["run_lock_sha256"] == _sha(_json(lock))
           and row["previous_sha256"] ==
           (_sha(_json(rows[-1])) if rows else None),
           "HEAD_CHAIN_OR_RUN_DRIFT")
    kind = row["kind"]
    payload = row["payload"]
    telemetry = row["telemetry"]
    reported = row["reported"]
    if kind in ("RUN_OPEN", "UPDATE_COMMITTED", "STATE_COLLAPSED"):
        insist(type(payload) is dict and set(payload) == {"name","sha256","bytes"},
               "STATE_PAYLOAD_REQUIRED")
        insist(payload["name"] == f"u{u:05d}.state.bin"
               and type(payload["sha256"]) is str
               and SHA_NAME.fullmatch(payload["sha256"]) is not None
               and type(payload["bytes"]) is int
               and 0 < payload["bytes"] <= MAX_STATE,
               "STATE_PAYLOAD_REF_INVALID")
        data = _read(root / payload["name"], MAX_STATE)
        insist(payload == _reference(data, payload["name"]),
               "STATE_PAYLOAD_CORRUPT")
    else:
        insist(payload is None, "UNEXPECTED_STATE_PAYLOAD")
    if kind in OUTCOMES:
        insist(type(telemetry) is dict
               and set(telemetry) == {"name","sha256","bytes"}
               and telemetry["name"] == f"u{u:05d}.telemetry.json",
               "TELEMETRY_REQUIRED")
        raw = _read(root / telemetry["name"], MAX_TELEMETRY)
        insist(telemetry == _reference(raw, telemetry["name"]),
               "TELEMETRY_CORRUPT")
        try:
            item = json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise JournalRefusal("REFUSE_ATTEMPT_JOURNAL_V2__BAD_TELEMETRY") from exc
        insist(type(item) is dict and raw == _json(item) and reported == item,
               "TELEMETRY_RECEIPT_MISMATCH")
        if kind == "UPDATE_COMMITTED":
            insist(set(item) == {
                "verdict", "state_update", "state_payload_sha256",
                "panel_sha256", "measurement_origin",
            } and item == {
                "verdict": "NOT_COLLAPSED_ONLY",
                "state_update": u,
                "state_payload_sha256": payload["sha256"],
                "panel_sha256": lock["panel_sha256"],
                "measurement_origin": "CALLER_REPORTED__NOT_PHYSICALLY_PROVED",
            }, "FALSE_HEALTHY_PROBE")
        elif kind in ("STATE_COLLAPSED", "ATTEMPT_FAILED"):
            try:
                parsed = cause.validate_failed_attempt_onset_receipt(item)
            except cause.CaptureRefusal as exc:
                raise JournalRefusal("REFUSE_ATTEMPT_JOURNAL_V2__CAUSE_INVALID") from exc
            insisting = (
                parsed["verdict_kind"] == "STATE_COLLAPSED_AFTER_STEP"
                and parsed["probed_state_update"] == u
                if kind == "STATE_COLLAPSED"
                else parsed["verdict_kind"] == "ATTEMPT_FAILED_NO_COMPLETED_STEP"
            )
            insist(insisting and parsed["attempt_update_index"] == u,
                   "OUTCOME_NOT_MATCHING_STATE")
        elif kind == "ATTEMPT_ABORTED":
            insist(set(item) == {"reason","quarantined","intent","self_reported",
                                 "runtime_abort_receipt"}
                   and item["reason"] in ("PROCESS_INTERRUPTED", "RUNTIME_ABORT")
                   and item["intent"] == u
                   and item["self_reported"] is True
                   and type(item["quarantined"]) is list,
                   "ABORT_METADATA_INVALID")
            if item["reason"] == "RUNTIME_ABORT":
                insist(item["quarantined"] == []
                       and type(item["runtime_abort_receipt"]) is dict,
                       "RUNTIME_ABORT_WITH_FALSE_QUARANTINE")
                try:
                    parsed = cause.validate_failed_attempt_onset_receipt(
                        item["runtime_abort_receipt"])
                except cause.CaptureRefusal as exc:
                    raise JournalRefusal(
                        "REFUSE_ATTEMPT_JOURNAL_V2__RUNTIME_ABORT_CAUSE_INVALID") from exc
                insist(parsed["verdict_kind"] == "ATTEMPT_ABORTED"
                       and parsed["attempt_update_index"] == u,
                       "RUNTIME_ABORT_STATE_INDEX_INVALID")
            else:
                insist(item["runtime_abort_receipt"] is None,
                       "CRASH_RECOVERY_NOT_RUNTIME_ABORT")
    else:
        insist(telemetry is None and reported is None,
               "UNEXPECTED_NON_OUTCOME_EVIDENCE")
    if kind == "RUN_CLOSED":
        last = rows[-1]
        insist(last["kind"] in FINALS or
               (last["kind"] == "UPDATE_COMMITTED"
                and last["update"] == lock["planned_horizon"]),
               "FALSE_PLANNED_COMPLETE")


def _scan(root: Path, custody: Path, lock: dict, *, tolerant: bool,
          permit_one_ahead: bool = False) -> tuple[list[dict], list[dict]]:
    """Strict journal/custody scan; optional forensic prefix on first anomaly."""
    local = _filenames(root)
    copies = _filenames(custody)
    rows: list[dict] = []
    issues: list[dict] = []
    length = max(len(local), len(copies))
    for seq in range(length):
        name = f"j{seq:08d}.json"
        try:
            insist(seq < len(local) and local[seq] == name,
                   "MISSING_OR_GAPPED_LOCAL_RECORD")
            raw = _read(root / name, MAX_RECORD)
            if seq < len(copies):
                insist(copies[seq] == name
                       and raw == _read(custody / name, MAX_RECORD),
                       "EXTERNAL_HEAD_DIVERGED_OR_LOCAL_ERASED")
            else:
                insist(permit_one_ahead and seq == len(copies)
                       and len(local) == len(copies) + 1,
                       "EXTERNAL_HEAD_MISSING_RECORD")
            row = _receipt(root, name, MAX_RECORD)
            _check_record(row, rows, lock, root)
            rows.append(row)
        except (JournalRefusal, OSError, KeyError, TypeError) as exc:
            if not tolerant:
                raise JournalRefusal(
                    "REFUSE_ATTEMPT_JOURNAL_V2__" + str(exc)) from exc
            issues.append({"sequence": seq, "reason": str(exc),
                           "status": "UNVERIFIED_TAIL__NO_RESUME"})
            break
    if not issues and len(copies) > len(local):
        issue = {"reason": "EXTERNAL_CUSTODY_AHEAD_OF_LOCAL",
                 "status": "UNVERIFIED_TAIL__NO_RESUME"}
        if tolerant:
            issues.append(issue)
        else:
            insist(False, "EXTERNAL_CUSTODY_AHEAD_OF_LOCAL")
    return rows, issues


def _append(root: Path, custody: Path, lock: dict, rows: list[dict],
            kind: str, update: int, payload: dict | None = None,
            telemetry: dict | None = None, reported: dict | None = None) -> dict:
    row = _record(kind=kind, seq=len(rows),
                  previous=_sha(_json(rows[-1])) if rows else None,
                  lock=lock, update=update, payload=payload,
                  telemetry=telemetry, reported=reported)
    _check_record(row, rows, lock, root)
    name = f"j{len(rows):08d}.json"
    raw = _json(row)
    _write_once(root, name, raw, MAX_RECORD)
    # Mirrored after local commit. A crash here can leave exactly one local
    # record ahead; explicit reconcile copies it before further progress.
    _write_once(custody, name, raw, MAX_RECORD)
    return row


def _ready(root: Path, custody: Path) -> tuple[dict, list[dict]]:
    lock = _binding(root, custody)
    rows, issues = _scan(root, custody, lock, tolerant=False)
    insist(not issues, "INCOMPLETE_HEAD")
    # Orphan/missing uncommitted payload is never silently adopted.
    accounted = {".writer.lock", "run.lock.json", "quarantine"}
    for row in rows:
        accounted.add(f"j{row['seq']:08d}.json")
        if row["payload"]:
            accounted.add(row["payload"]["name"])
        if row["telemetry"]:
            accounted.add(row["telemetry"]["name"])
    extras = {p.name for p in root.iterdir()} - accounted
    insist(not extras, "UNCOMMITTED_OR_UNKNOWN_FILES_PRESENT")
    return lock, rows


def _create_roots(root: Path, custody: Path) -> tuple[Path, Path]:
    root, custody = Path(root).absolute(), Path(custody).absolute()
    insist(root != custody and root not in custody.parents
           and custody not in root.parents, "CUSTODY_MUST_BE_OUTSIDE_RUN")
    insist(not root.is_symlink() and not custody.is_symlink(), "SYMLINK_ROOT")
    root.mkdir(mode=0o700, exist_ok=True)
    custody.mkdir(mode=0o700, exist_ok=True)
    return _paths(root, custody)


def open_journal(root: Path, custody: Path, *, run_id: str, horizon: int,
                 panel_sha256: str, config_sha256: str, rights_sha256: str,
                 initial_state_bytes: bytes) -> dict:
    """RUN_OPEN plus durable u0 bytes in local run & separate journal head."""
    lock = _run_lock(run_id=run_id, horizon=horizon,
                     panel_sha256=panel_sha256, config_sha256=config_sha256,
                     rights_sha256=rights_sha256)
    insist(type(initial_state_bytes) is bytes
           and 0 < len(initial_state_bytes) <= MAX_STATE, "U0_BYTES_REQUIRED")
    root, custody = _create_roots(root, custody)
    with _lock(root):
        insist({p.name for p in root.iterdir()} == {".writer.lock"}
               and not any(custody.iterdir()), "RUN_ALREADY_INITIALIZED")
        raw = _json(lock)
        _write_once(root, "run.lock.json", raw, MAX_RECORD)
        _write_once(custody, "run.lock.json", raw, MAX_RECORD)
        name = "u00000.state.bin"
        _write_once(root, name, initial_state_bytes, MAX_STATE)
        _append(root, custody, lock, [], "RUN_OPEN", 0,
                payload=_reference(initial_state_bytes, name))
        return {"status": "OPENED_FAKE_BYTES_ONLY", "horizon": horizon,
                "run_id": run_id, "training_authorized": False}


def begin_attempt(root: Path, custody: Path, *, update: int) -> dict:
    """Persist ATTEMPT_BEGIN before a caller would execute any neural step."""
    root, custody = _paths(root, custody)
    with _lock(root):
        lock, rows = _ready(root, custody)
        allowed, expected = _expected_next(rows, lock)
        insist("ATTEMPT_BEGIN" in allowed
               and type(update) is int and update == expected,
               "ATTEMPT_NOT_NEXT_UPDATE")
        row = _append(root, custody, lock, rows, "ATTEMPT_BEGIN", update)
        return {"status": row["kind"], "update": update,
                "real_optimizer_executed": False, "training_authorized": False}


def _outcome(root: Path, custody: Path, *, update: int, kind: str,
             state_bytes: bytes | None, telemetry: dict) -> dict:
    insist(kind in OUTCOMES and type(update) is int
           and type(telemetry) is dict, "OUTCOME_ARGUMENTS")
    root, custody = _paths(root, custody)
    with _lock(root):
        lock, rows = _ready(root, custody)
        allowed, expected = _expected_next(rows, lock)
        insist(kind in allowed and update == expected,
               "OUTCOME_REQUIRES_MATCHING_BEGIN")
        state_ref = None
        if kind in ("UPDATE_COMMITTED", "STATE_COLLAPSED"):
            insist(type(state_bytes) is bytes
                   and 0 < len(state_bytes) <= MAX_STATE,
                   "FULL_STATE_BYTES_REQUIRED")
            filename = f"u{update:05d}.state.bin"
            state_ref = _reference(state_bytes, filename)
        else:
            insist(state_bytes is None, "UNEXPECTED_STATE_FOR_FAILURE")
        # Validate ALL logical claims *before* physically publishing
        # any bytes. _check_record also validates the actual SHA-linked files.
        if kind == "UPDATE_COMMITTED":
            insist(telemetry == {
                "verdict": "NOT_COLLAPSED_ONLY",
                "state_update": update,
                "state_payload_sha256": state_ref["sha256"],
                "panel_sha256": lock["panel_sha256"],
                "measurement_origin": "CALLER_REPORTED__NOT_PHYSICALLY_PROVED",
            }, "COMMITTED_PROBE_INCONSISTENT")
        elif kind in ("STATE_COLLAPSED", "ATTEMPT_FAILED"):
            try:
                parsed = cause.validate_failed_attempt_onset_receipt(telemetry)
            except cause.CaptureRefusal as exc:
                raise JournalRefusal("REFUSE_ATTEMPT_JOURNAL_V2__INVALID_TYPED_CAUSE") from exc
            insist(parsed["attempt_update_index"] == update
                   and parsed["verdict_kind"] == (
                       "STATE_COLLAPSED_AFTER_STEP" if kind == "STATE_COLLAPSED"
                       else "ATTEMPT_FAILED_NO_COMPLETED_STEP"),
                   "CAUSE_OUTCOME_WRONG_STATE")
        elif kind == "ATTEMPT_ABORTED":
            insist(set(telemetry) == {
                "reason", "quarantined", "intent", "self_reported",
                "runtime_abort_receipt",
            } and telemetry["reason"] == "RUNTIME_ABORT"
                   and telemetry["quarantined"] == []
                   and telemetry["intent"] == update
                   and telemetry["self_reported"] is True
                   and type(telemetry["runtime_abort_receipt"]) is dict,
                   "ABORT_MUST_HAVE_RUNTIME_CAUSE")
        if state_ref:
            _write_once(root, state_ref["name"], state_bytes, MAX_STATE)
        raw = _json(telemetry)
        insist(0 < len(raw) <= MAX_TELEMETRY, "TELEMETRY_TOO_LARGE")
        tname = f"u{update:05d}.telemetry.json"
        _write_once(root, tname, raw, MAX_TELEMETRY)
        record = _append(
            root, custody, lock, rows, kind, update, payload=state_ref,
            telemetry=_reference(raw, tname), reported=telemetry)
        return {
            "status": record["kind"], "update": update,
            "state_bytes_stored": state_ref["bytes"] if state_ref else 0,
            "state_sha256": state_ref["sha256"] if state_ref else None,
            "resumable": False, "physical_neural_health_proved": False,
            "training_authorized": False,
        }


def commit_reported_update(root: Path, custody: Path, *, update: int,
                           state_bytes: bytes, panel_sha256: str) -> dict:
    """Requires *reported* passing probe; NEVER proves real healthy biology."""
    insist(type(state_bytes) is bytes, "STATE_BYTES_TYPE")
    return _outcome(
        root, custody, update=update, kind="UPDATE_COMMITTED",
        state_bytes=state_bytes, telemetry={
            "verdict": "NOT_COLLAPSED_ONLY", "state_update": update,
            "state_payload_sha256": _sha(state_bytes),
            "panel_sha256": panel_sha256,
            "measurement_origin": "CALLER_REPORTED__NOT_PHYSICALLY_PROVED",
        })


def record_collapsed_state(root: Path, custody: Path, *, update: int,
                           state_bytes: bytes, reported_receipt: dict) -> dict:
    """Store full-size nonresumable forensic onset state, including >8 MiB."""
    return _outcome(root, custody, update=update, kind="STATE_COLLAPSED",
                    state_bytes=state_bytes, telemetry=reported_receipt)


def record_failed_attempt(root: Path, custody: Path, *, update: int,
                          reported_receipt: dict) -> dict:
    """Mechanical failure with NO completed step. No model resume."""
    return _outcome(root, custody, update=update, kind="ATTEMPT_FAILED",
                    state_bytes=None, telemetry=reported_receipt)


def record_runtime_abort(root: Path, custody: Path, *, update: int,
                         reported_receipt: dict) -> dict:
    """Persist a typed non-scientific OOM/exception STOP; no successful step."""
    insist(type(reported_receipt) is dict, "RUNTIME_ABORT_RECEIPT_REQUIRED")
    try:
        parsed = cause.validate_failed_attempt_onset_receipt(reported_receipt)
    except cause.CaptureRefusal as exc:
        raise JournalRefusal("REFUSE_ATTEMPT_JOURNAL_V2__INVALID_ABORT_CAUSE") from exc
    insist(parsed["verdict_kind"] == "ATTEMPT_ABORTED"
           and parsed["attempt_update_index"] == update,
           "RUNTIME_ABORT_NOT_ABORTED")
    return _outcome(
        root, custody, update=update, kind="ATTEMPT_ABORTED",
        state_bytes=None, telemetry={
            "reason": "RUNTIME_ABORT",
            "quarantined": [], "intent": update, "self_reported": True,
            "runtime_abort_receipt": reported_receipt,
        })


def _quarantine(root: Path, update: int, rows: list[dict]) -> list[dict]:
    """Preserve every orphan; never silently unlink or declare it successful."""
    known = {".writer.lock", "run.lock.json", "quarantine"}
    for row in rows:
        known.add(f"j{row['seq']:08d}.json")
        for key in ("payload", "telemetry"):
            if row[key]:
                known.add(row[key]["name"])
    orphan = [p for p in root.iterdir() if p.name not in known]
    qdir = root / "quarantine"
    if qdir.exists():
        _dir(qdir)
    else:
        qdir.mkdir(mode=0o700)
        _fsync_dir(root)
    # Handle a prior crash *during quarantine*, without deleting evidence.
    orphan += [p for p in qdir.iterdir()]
    labels: list[dict] = []
    for path in sorted(orphan, key=lambda p: p.name):
        insist(not path.is_symlink() and path.is_file()
               and not path.is_dir(), "QUARANTINE_UNSAFE_FILE")
        raw = _read(path, MAX_STATE)
        target = qdir / path.name
        if path.parent != qdir:
            insist(not target.exists() and not target.is_symlink(),
                   "QUARANTINE_NAME_CONFLICT")
            os.rename(path, target)
            _fsync_dir(root)
            _fsync_dir(qdir)
        labels.append({"name": path.name, "sha256": _sha(raw),
                       "bytes": len(raw), "status": "QUARANTINED_UNVERIFIED"})
    return labels


def reconcile_one_unmirrored_record(root: Path, custody: Path) -> dict:
    """Repair interrupted mirror *only* if exactly one valid local head ahead."""
    root, custody = _paths(root, custody)
    with _lock(root):
        lock = _binding(root, custody)
        rows, issues = _scan(root, custody, lock, tolerant=False,
                             permit_one_ahead=True)
        insist(not issues and len(rows) >= 1, "CANNOT_RECONCILE")
        local = _filenames(root)
        copies = _filenames(custody)
        insist(len(local) == len(copies) + 1, "NOT_EXACTLY_ONE_AHEAD")
        seq = len(copies)
        name = f"j{seq:08d}.json"
        _write_once(custody, name, _read(root / name, MAX_RECORD), MAX_RECORD)
        return {"status": "ONE_VERIFIED_LOCAL_RECORD_MIRRORED",
                "sequence": seq, "resume_authorized": False}


def recover_interrupted_attempt(root: Path, custody: Path) -> dict:
    """Quarantine stray bytes and append ABORTED; no deletion, no next step."""
    root, custody = _paths(root, custody)
    with _lock(root):
        lock = _binding(root, custody)
        rows, issues = _scan(root, custody, lock, tolerant=False)
        insist(not issues and bool(rows) and
               rows[-1]["kind"] == "ATTEMPT_BEGIN",
               "NO_UNFINISHED_ATTEMPT")
        u = rows[-1]["update"]
        labels = _quarantine(root, u, rows)
        item = {"reason": "PROCESS_INTERRUPTED", "quarantined": labels,
                "intent": u, "self_reported": True,
                "runtime_abort_receipt": None}
        raw = _json(item)
        tname = f"u{u:05d}.telemetry.json"
        _write_once(root, tname, raw, MAX_TELEMETRY)
        record = _append(
            root, custody, lock, rows, "ATTEMPT_ABORTED", u,
            telemetry=_reference(raw, tname), reported=item)
        return {"status": record["kind"], "update": u,
                "quarantined": labels, "training_authorized": False}


def close_run(root: Path, custody: Path) -> dict:
    root, custody = _paths(root, custody)
    with _lock(root):
        lock, rows = _ready(root, custody)
        allowed, u = _expected_next(rows, lock)
        insist("RUN_CLOSED" in allowed, "CANNOT_CLOSE_INCOMPLETE_ATTEMPT")
        final = rows[-1]["kind"]
        _append(root, custody, lock, rows, "RUN_CLOSED", u)
        return {"status": ("COMPLETE_REPORTED_ONLY" if
                final == "UPDATE_COMMITTED" else
                "STOPPED_COLLAPSED" if final == "STATE_COLLAPSED" else
                "STOPPED_FAILED" if final == "ATTEMPT_FAILED" else
                "ABORTED_RECOVERED"), "training_authorized": False}


def _status(rows: list[dict], lock: dict) -> str:
    if not rows:
        return "UNVERIFIED"
    last = rows[-1]
    if last["kind"] == "RUN_CLOSED":
        previous = rows[-2]
        if previous["kind"] == "UPDATE_COMMITTED":
            return "COMPLETE_REPORTED_ONLY"
        return ("STOPPED_COLLAPSED" if previous["kind"] == "STATE_COLLAPSED"
                else "STOPPED_FAILED" if previous["kind"] == "ATTEMPT_FAILED"
                else "ABORTED_RECOVERED")
    return "TERMINATED_UNEXPECTEDLY__NOT_PLANNED_COMPLETE"


def inspect_journal(root: Path, custody: Path) -> dict:
    """Strict inventory, not actual neural-state health or restore authority."""
    root, custody = _paths(root, custody)
    with _lock(root):
        lock, rows = _ready(root, custody)
        return _report(rows, lock, [])


def _report(rows: list[dict], lock: dict, anomalies: list[dict]) -> dict:
    commits = [r["update"] for r in rows if r["kind"] == "UPDATE_COMMITTED"]
    collapsed = [r["update"] for r in rows if r["kind"] == "STATE_COLLAPSED"]
    return {
        "schema": SCHEMA, "status": _status(rows, lock),
        "planned_horizon": lock["planned_horizon"], "journal_records": len(rows),
        "verified_journal_head_sha256": _sha(_json(rows[-1])) if rows else None,
        "last_reported_probe_pass_checkpoint_update": (
            commits[-1] if commits else 0 if rows else None),
        "collapsed_state_updates_nonresumable": collapsed,
        "anomalies": anomalies,
        "external_copy_is_separately_retained_unsigned": True,
        "history_authentication_against_malicious_writer": False,
        "every_completed_update_has_blob": True,
        "actual_neural_health_proved": False,
        "last_neurally_healthy_checkpoint_proved": False,
        "resume_authorized": False, "training_authorized": False,
        "authority": AUTHORITY,
    }


def inspect_forensic_prefix(root: Path, custody: Path) -> dict:
    """Maximal paired SHA-verified event prefix, stop at first damaged record."""
    root, custody = _paths(root, custody)
    with _lock(root):
        lock = _binding(root, custody)
        rows, issues = _scan(root, custody, lock, tolerant=True)
        known = {".writer.lock", "run.lock.json", "quarantine"}
        for row in rows:
            known.add(f"j{row['seq']:08d}.json")
            for field in ("payload", "telemetry"):
                if row[field]:
                    known.add(row[field]["name"])
        for p in sorted(root.iterdir(), key=lambda v: v.name):
            if p.name not in known and not RECORD_NAME.fullmatch(p.name):
                issues.append({
                    "name": p.name, "reason": "UNCOMMITTED_OR_UNVERIFIED_FILE",
                    "status": "UNVERIFIED_TAIL__NO_RESUME",
                })
        return _report(rows, lock, issues)


def read_forensic_opaque_state(root: Path, custody: Path, *, update: int) -> bytes:
    """Read SHA-linked bytes from a verified committed checkpoint only.

    Collapse payloads are NEVER returned as candidate healthy checkpoints.
    No model loader or resume call exists in this module.
    """
    root, custody = _paths(root, custody)
    with _lock(root):
        lock = _binding(root, custody)
        rows, _issues = _scan(root, custody, lock, tolerant=True)
        matches = [r for r in rows if r["kind"] == "UPDATE_COMMITTED"
                   and r["update"] == update]
        if update == 0:
            matches = [r for r in rows if r["kind"] == "RUN_OPEN"]
        insist(len(matches) == 1, "UPDATE_NOT_VERIFIED_COMMITTED_STATE")
        ref = matches[0]["payload"]
        raw = _read(root / ref["name"], MAX_STATE)
        insist(ref == _reference(raw, ref["name"]), "STATE_CHANGED_AFTER_SCAN")
        return raw
