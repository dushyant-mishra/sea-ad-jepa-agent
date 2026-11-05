#!/usr/bin/env python3
"""Independent-directory-backed V5 journal V2 -- FAKE OPAQUE BYTES ONLY.

No optimizer, neural model, biological measurement, GPU, restore or training.
This is an append-only storage/state-machine substrate, NOT an authorized
trainer or an independently authenticated scientific checkpoint.

Macha repair of #570 (2026-11-05), still fake bytes and caller reports only:
  * Every probe-pass claim (u0 and each commit) carries a caller-reported,
    state-bound probe on the run panel; a probe that itself shows an exact
    collapse, non-finite values or inexact CELL arithmetic cannot commit.
  * Collapse evidence must cite the run panel and the run's own u0 reference.
  * The forensic reader continues past a damaged payload, telemetry or one
    damaged record copy, because the hash-linked record survives in the other
    copy; it stops only where no single intact record copy exists.
  * Crash recovery removes only provably redundant temp files (hard-link twins
    or byte prefixes of retained files), completes a fully durable failure
    outcome instead of downgrading it to an abort, surfaces an uncommitted
    collapse cause, and never collides with its own earlier quarantine.
  * Only the process that opened a run may advance it; a fresh process is
    refused until a verified restart path is separately authorized.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import fcntl
import json
from math import isfinite
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
MAX_RECORD = 256 * 1024
RECORD_NAME = re.compile(r"j[0-9]{8}\.json\Z")
STATE_NAME = re.compile(r"u[0-9]{5}\.state\.bin\Z")
TELEMETRY_NAME = re.compile(r"u[0-9]{5}\.telemetry\.json\Z")
TEMP_NAME = re.compile(r"\.uncommitted-[0-9a-f]{32}\Z")
RUN_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
SHA_NAME = re.compile(r"[0-9a-f]{64}\Z")
FINALS = {"STATE_COLLAPSED", "ATTEMPT_FAILED", "ATTEMPT_ABORTED"}
OUTCOMES = FINALS | {"UPDATE_COMMITTED"}
PROBED_STATES = {"RUN_OPEN", "UPDATE_COMMITTED"}
STATE_KINDS = PROBED_STATES | {"STATE_COLLAPSED"}
RECORD_FIELDS = {
    "schema", "kind", "seq", "previous_sha256", "run_lock_sha256", "update",
    "payload", "telemetry", "reported", "writer_session_sha256",
    "training_authorized",
}
MEASUREMENT_ORIGIN = "CALLER_REPORTED__NOT_PHYSICALLY_PROVED"
PROBE_METRICS = frozenset(cause.COLLAPSE_CAUSE_METRIC.values())
PROBE_FIELDS = frozenset({
    "state_update", "state_payload_sha256", "probe_panel_sha256",
    "operator_homogeneous_eval_mode", "identical_gene_sets", "metrics",
    "cell_distinct_row_count", "probe_cells", "nonfinite_values",
    "measurement_origin",
})
ABORT_FIELDS = {"reason", "quarantined", "intent", "self_reported",
                "runtime_abort_receipt", "uncommitted_typed_verdicts"}
VERDICT_KINDS = {"STATE_COLLAPSED_AFTER_STEP", "STATE_COLLAPSED_BEFORE_NEXT_STEP",
                 "ATTEMPT_ABORTED", "ATTEMPT_FAILED_NO_COMPLETED_STEP"}
# Process-lifetime writer capability. Only its SHA is written to RUN_OPEN, so a
# a fresh or forked process cannot continue a run whose opening process died.
# PID is bound at open time, because POSIX fork inherits Python module globals.
_SESSIONS: dict[str, tuple[int, str]] = {}
_SCAN_ERRORS = (OSError, KeyError, TypeError, ValueError, IndexError, AttributeError)


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


def _outside(root: Path, custody: Path) -> tuple[Path, Path]:
    root, custody = Path(root).absolute(), Path(custody).absolute()
    insist(root != custody and root not in custody.parents
           and custody not in root.parents, "CUSTODY_MUST_BE_OUTSIDE_RUN")
    return root, custody


def _paths(root: Path, custody: Path) -> tuple[Path, Path]:
    root, custody = _outside(root, custody)
    _dir(root)
    _dir(custody)
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


def _temp_twin(path: Path, st: os.stat_result) -> Path | None:
    """The uncommitted temp name still linked to this inode, if that is the
    only other link: the on-disk state after a crash between link and unlink."""
    if st.st_nlink != 2:
        return None
    for other in path.parent.iterdir():
        if other == path or TEMP_NAME.fullmatch(other.name) is None:
            continue
        try:
            o = os.lstat(other)
        except OSError:
            continue
        if stat.S_ISREG(o.st_mode) and (o.st_dev, o.st_ino) == (st.st_dev, st.st_ino):
            return other
    return None


def _read(path: Path, limit: int, *, twin_ok: bool = False) -> bytes:
    insist(path.is_file() and not path.is_symlink(), "FILE_MISSING_OR_UNSAFE")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        st = os.fstat(fd)
        links_ok = st.st_nlink == 1 or (twin_ok and _temp_twin(path, st) is not None)
        insist(stat.S_ISREG(st.st_mode) and links_ok
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


def _parse(raw: bytes, name: str) -> dict:
    try:
        record = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise JournalRefusal("REFUSE_ATTEMPT_JOURNAL_V2__BAD_JSON_" + name) from exc
    insist(type(record) is dict and _json(record) == raw, "NONCANONICAL_JSON")
    return record


def _receipt(root: Path, name: str, max_bytes: int) -> dict:
    return _parse(_read(root / name, max_bytes), "RECORD")


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
            telemetry: dict | None, reported: dict | None = None,
            writer: str | None = None) -> dict:
    return {
        "schema": SCHEMA, "kind": kind, "seq": seq,
        "previous_sha256": previous, "run_lock_sha256": _sha(_json(lock)),
        "update": update, "payload": payload, "telemetry": telemetry,
        "reported": reported, "writer_session_sha256": writer,
        "training_authorized": False,
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


# ---------------------------------------------------------------- probes

def _number(value: object) -> bool:
    return type(value) in (int, float) and isfinite(value) and value >= 0


def _validate_probe(probe: object, *, update: int, state_sha256: str,
                    lock: dict) -> dict:
    """A caller-reported, state-bound probe that does NOT show exact collapse.

    Passing means only NOT_COLLAPSED on the run panel. It is never evidence of
    healthy or learned biology. Low-rank states with small positive values
    pass; only exact zeros, non-finite values or inexact CELL arithmetic stop.
    """
    insist(type(probe) is dict and set(probe) == PROBE_FIELDS, "PROBE_FIELDS")
    insist(type(probe["state_update"]) is int
           and probe["state_update"] == update, "PROBE_NOT_OF_THIS_UPDATE")
    insist(probe["state_payload_sha256"] == state_sha256,
           "PROBE_NOT_BOUND_TO_STATE_BYTES")
    insist(probe["probe_panel_sha256"] == lock["panel_sha256"],
           "PROBE_PANEL_NOT_RUN_PANEL")
    insist(probe["operator_homogeneous_eval_mode"] is True
           and probe["identical_gene_sets"] is True, "PROBE_NOT_COMPARABLE")
    insist(probe["measurement_origin"] == MEASUREMENT_ORIGIN,
           "PROBE_CLAIMS_PHYSICAL_PROOF")
    metrics = probe["metrics"]
    insist(type(metrics) is dict and set(metrics) == PROBE_METRICS
           and all(_number(x) for x in metrics.values()), "PROBE_METRICS")
    cells, distinct, nonfinite = (probe["probe_cells"],
                                  probe["cell_distinct_row_count"],
                                  probe["nonfinite_values"])
    insist(all(type(x) is int for x in (cells, distinct, nonfinite))
           and cells >= 2 and 1 <= distinct <= cells and nonfinite >= 0,
           "PROBE_COUNTS")
    insist(nonfinite == 0, "PROBE_REPORTS_NONFINITE_STATE")
    # Exact witness: one distinct CELL row <=> exactly zero centered energy.
    insist((distinct == 1) == (metrics["cell_centered_energy"] == 0),
           "CELL_ENERGY_IS_NOT_AN_EXACT_WITNESS")
    insist(all(x > 0 for x in metrics.values()),
           "PROBE_SHOWS_EXACT_COLLAPSE__RECORD_STATE_COLLAPSED")
    return probe


def _validate_cause(item: object, *, update: int, kind: str, rows: list[dict],
                    lock: dict) -> dict:
    try:
        parsed = cause.validate_failed_attempt_onset_receipt(item)
    except cause.CaptureRefusal as exc:
        raise JournalRefusal("REFUSE_ATTEMPT_JOURNAL_V2__CAUSE_INVALID") from exc
    wanted = {"STATE_COLLAPSED": "STATE_COLLAPSED_AFTER_STEP",
              "ATTEMPT_FAILED": "ATTEMPT_FAILED_NO_COMPLETED_STEP",
              "ATTEMPT_ABORTED": "ATTEMPT_ABORTED"}[kind]
    insist(parsed["verdict_kind"] == wanted
           and parsed["attempt_update_index"] == update,
           "CAUSE_OUTCOME_WRONG_STATE")
    if kind == "STATE_COLLAPSED":
        insist(parsed["probed_state_update"] == update, "COLLAPSE_NOT_OF_THIS_STATE")
        evidence = item["collapse_evidence"]
        u0 = rows[0]["reported"]["metrics"] if rows and rows[0]["kind"] == "RUN_OPEN" else {}
        insist(evidence["probe_panel_sha256"] == lock["panel_sha256"],
               "COLLAPSE_PANEL_NOT_RUN_PANEL")
        insist(evidence["u0_reference"] == u0.get(evidence["metric"]),
               "COLLAPSE_U0_REFERENCE_NOT_RUN_U0")
    return parsed


def _typed_verdict(raw: bytes, update: int) -> str | None:
    """Verdict of an uncommitted typed cause, or None. Never a committed claim."""
    if len(raw) > MAX_TELEMETRY:
        return None
    try:
        item = _parse(raw, "QUARANTINE")
        parsed = cause.validate_failed_attempt_onset_receipt(item)
    except (JournalRefusal, cause.CaptureRefusal, *_SCAN_ERRORS):
        return None
    if parsed["attempt_update_index"] != update:
        return None
    return parsed["verdict_kind"]


# ---------------------------------------------------------------- record checks

def _check_structure(row: dict, rows: list[dict], lock: dict) -> None:
    """Everything provable from the record itself and its hash-linked chain."""
    allowed, u = _expected_next(rows, lock)
    insist(type(row) is dict and set(row) == RECORD_FIELDS, "RECORD_FIELD_SHAPE")
    insist(row["kind"] in allowed and type(row["update"]) is int
           and row["update"] == u, "ILLEGAL_ATTEMPT_TRANSITION")
    insist(row["schema"] == SCHEMA
           and type(row["seq"]) is int and row["seq"] == len(rows)
           and row["training_authorized"] is False
           and row["run_lock_sha256"] == _sha(_json(lock))
           and row["previous_sha256"] ==
           (_sha(_json(rows[-1])) if rows else None),
           "HEAD_CHAIN_OR_RUN_DRIFT")
    kind, payload, telemetry, reported = (
        row["kind"], row["payload"], row["telemetry"], row["reported"])
    writer = row["writer_session_sha256"]
    if kind == "RUN_OPEN":
        insist(type(writer) is str and SHA_NAME.fullmatch(writer) is not None,
               "RUN_OPEN_WITHOUT_WRITER_SESSION")
    elif kind in ("ATTEMPT_BEGIN", "UPDATE_COMMITTED"):
        insist(writer == rows[0]["writer_session_sha256"],
               "ATTEMPT_NOT_WRITTEN_BY_OPENING_PROCESS")
    else:
        insist(writer in (rows[0]["writer_session_sha256"], None),
               "UNKNOWN_WRITER_SESSION")
    if kind in STATE_KINDS:
        insist(type(payload) is dict and set(payload) == {"name", "sha256", "bytes"},
               "STATE_PAYLOAD_REQUIRED")
        insist(payload["name"] == f"u{u:05d}.state.bin"
               and type(payload["sha256"]) is str
               and SHA_NAME.fullmatch(payload["sha256"]) is not None
               and type(payload["bytes"]) is int
               and 0 < payload["bytes"] <= MAX_STATE,
               "STATE_PAYLOAD_REF_INVALID")
    else:
        insist(payload is None, "UNEXPECTED_STATE_PAYLOAD")
    if kind in OUTCOMES or kind == "RUN_OPEN":
        insist(type(telemetry) is dict
               and set(telemetry) == {"name", "sha256", "bytes"}
               and telemetry["name"] == f"u{u:05d}.telemetry.json"
               and type(reported) is dict
               and telemetry["sha256"] == _sha(_json(reported))
               and telemetry["bytes"] == len(_json(reported))
               and 0 < telemetry["bytes"] <= MAX_TELEMETRY,
               "TELEMETRY_RECEIPT_MISMATCH")
    else:
        insist(telemetry is None and reported is None,
               "UNEXPECTED_NON_OUTCOME_EVIDENCE")
    if kind in PROBED_STATES:
        _validate_probe(reported, update=u, state_sha256=payload["sha256"], lock=lock)
    elif kind in ("STATE_COLLAPSED", "ATTEMPT_FAILED"):
        _validate_cause(reported, update=u, kind=kind, rows=rows, lock=lock)
    elif kind == "ATTEMPT_ABORTED":
        item = reported
        insist(set(item) == ABORT_FIELDS
               and item["reason"] in ("PROCESS_INTERRUPTED", "RUNTIME_ABORT")
               and item["intent"] == u
               and item["self_reported"] is True
               and type(item["quarantined"]) is list
               and type(item["uncommitted_typed_verdicts"]) is list
               and all(x in VERDICT_KINDS for x in item["uncommitted_typed_verdicts"]),
               "ABORT_METADATA_INVALID")
        if item["reason"] == "RUNTIME_ABORT":
            insist(item["quarantined"] == []
                   and item["uncommitted_typed_verdicts"] == []
                   and type(item["runtime_abort_receipt"]) is dict,
                   "RUNTIME_ABORT_WITH_FALSE_QUARANTINE")
            _validate_cause(item["runtime_abort_receipt"], update=u,
                            kind="ATTEMPT_ABORTED", rows=rows, lock=lock)
        else:
            insist(item["runtime_abort_receipt"] is None and writer is None,
                   "CRASH_RECOVERY_NOT_RUNTIME_ABORT")
            seen = set()
            for entry in item["quarantined"]:
                insist(type(entry) is dict and set(entry) == {
                    "name", "sha256", "bytes", "status",
                }, "QUARANTINE_ENTRY_FIELDS")
                name = entry["name"]
                insist(type(name) is str and name not in ("", ".", "..")
                       and "/" not in name and chr(92) not in name
                       and name not in seen and name != "quarantine",
                       "QUARANTINE_ENTRY_PATH_OR_DUPLICATE")
                seen.add(name)
                insist(entry["status"] == "QUARANTINED_UNVERIFIED",
                       "QUARANTINE_CLAIMS_VERIFIED")
    if kind == "RUN_CLOSED":
        last = rows[-1]
        insist(last["kind"] in FINALS or
               (last["kind"] == "UPDATE_COMMITTED"
                and last["update"] == lock["planned_horizon"]),
               "FALSE_PLANNED_COMPLETE")


def _check_evidence(row: dict, root: Path, *, twin_ok: bool = False) -> None:
    """The files a structurally valid record points to are present and intact."""
    if row["payload"] is not None:
        ref = row["payload"]
        data = _read(root / ref["name"], MAX_STATE, twin_ok=twin_ok)
        insist(ref == _reference(data, ref["name"]), "STATE_PAYLOAD_CORRUPT")
    if row["telemetry"] is not None:
        ref = row["telemetry"]
        raw = _read(root / ref["name"], MAX_TELEMETRY, twin_ok=twin_ok)
        insist(ref == _reference(raw, ref["name"]), "TELEMETRY_CORRUPT")
    item = row["reported"]
    if row["kind"] == "ATTEMPT_ABORTED" and item["reason"] == "PROCESS_INTERRUPTED":
        qdir = root / "quarantine"
        insist(qdir.is_dir() and not qdir.is_symlink(),
               "QUARANTINE_DIR_MISSING_OR_UNSAFE")
        verdicts = set()
        for entry in item["quarantined"]:
            raw = _read(qdir / entry["name"], MAX_STATE, twin_ok=twin_ok)
            insist(entry == {
                "name": entry["name"], "sha256": _sha(raw), "bytes": len(raw),
                "status": "QUARANTINED_UNVERIFIED",
            }, "QUARANTINE_BYTES_SHA_DRIFT")
            verdict = _typed_verdict(raw, row["update"])
            if verdict is not None:
                verdicts.add(verdict)
        insist({p.name for p in qdir.iterdir()}
               == {e["name"] for e in item["quarantined"]},
               "QUARANTINE_UNKNOWN_OR_MISSING_FILES")
        insist(sorted(verdicts) == item["uncommitted_typed_verdicts"],
               "UNCOMMITTED_VERDICTS_NOT_DERIVED_FROM_QUARANTINE")


def _check_record(row: dict, rows: list[dict], lock: dict, root: Path) -> None:
    _check_structure(row, rows, lock)
    _check_evidence(row, root)


# ---------------------------------------------------------------- scans

def _scan(root: Path, custody: Path, lock: dict, *, tolerant: bool,
          permit_one_ahead: bool = False) -> tuple[list[dict], list[dict]]:
    """Strict journal/custody scan (both copies identical, all evidence intact)."""
    if tolerant:
        rows, issues, _damaged = _forensic_scan(root, custody, lock)
        return rows, issues
    local = _filenames(root)
    copies = _filenames(custody)
    rows: list[dict] = []
    for seq in range(max(len(local), len(copies))):
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
            row = _parse(raw, "RECORD")
            _check_record(row, rows, lock, root)
            rows.append(row)
        except (JournalRefusal, *_SCAN_ERRORS) as exc:
            raise JournalRefusal("REFUSE_ATTEMPT_JOURNAL_V2__" + str(exc)) from exc
    insist(len(copies) <= len(local), "EXTERNAL_CUSTODY_AHEAD_OF_LOCAL")
    return rows, []


def _forensic_scan(root: Path, custody: Path, lock: dict
                   ) -> tuple[list[dict], list[dict], set[int]]:
    """Longest chain of records with one intact, hash-linked copy.

    A damaged payload, telemetry or quarantine file marks only that record's
    evidence as damaged: the hash-linked record (kept in two places) remains
    valid, so later commits and collapse records stay visible. The chain ends
    only where no single structurally valid copy of the next record exists.
    """
    local, copies = set(_filenames(root)), set(_filenames(custody))
    rows: list[dict] = []
    anomalies: list[dict] = []
    damaged: set[int] = set()
    seq = 0
    while True:
        name = f"j{seq:08d}.json"
        present = [(where, d) for where, d, names in
                   (("LOCAL", root, local), ("EXTERNAL", custody, copies))
                   if name in names]
        if not present:
            break
        valid = []
        for where, d in present:
            try:
                raw = _read(d / name, MAX_RECORD, twin_ok=True)
                row = _parse(raw, "RECORD")
                _check_structure(row, rows, lock)
                valid.append((where, raw, row))
            except (JournalRefusal, *_SCAN_ERRORS) as exc:
                anomalies.append({"sequence": seq, "copy": where,
                                  "reason": str(exc),
                                  "status": "DAMAGED_RECORD_COPY"})
        if len({raw for _, raw, _ in valid}) != 1:
            anomalies.append({
                "sequence": seq,
                "reason": ("DIVERGENT_VALID_RECORD_COPIES" if valid
                           else "NO_INTACT_RECORD_COPY"),
                "status": "UNVERIFIED_TAIL__NO_RESUME"})
            break
        holders = sorted(where for where, _, _ in valid)
        if holders != ["EXTERNAL", "LOCAL"]:
            anomalies.append({"sequence": seq, "reason": "ONLY_ONE_INTACT_RECORD_COPY",
                              "intact_copies": holders,
                              "status": "SINGLE_COPY_EVIDENCE__NO_RESUME"})
        row = valid[0][2]
        try:
            _check_evidence(row, root, twin_ok=True)
        except (JournalRefusal, *_SCAN_ERRORS) as exc:
            damaged.add(seq)
            anomalies.append({"sequence": seq, "update": row["update"],
                              "kind": row["kind"], "reason": str(exc),
                              "status": "EVIDENCE_DAMAGED__RECORD_INTACT"})
        rows.append(row)
        seq += 1
    beyond = sorted(n for n in local | copies if int(n[1:9]) >= seq)
    if beyond:
        anomalies.append({"reason": "RECORDS_BEYOND_VERIFIABLE_CHAIN",
                          "names": beyond, "status": "UNVERIFIED_TAIL__NO_RESUME"})
    return rows, anomalies, damaged


# ---------------------------------------------------------------- writers

def _session_sha(root: Path) -> str | None:
    session = _SESSIONS.get(str(root))
    if session is None:
        return None
    opening_pid, token = session
    # A forked child inherits _SESSIONS unchanged; it is not the opening
    # process and cannot advance a run whose actual restart is unverified.
    if opening_pid != os.getpid():
        return None
    return _sha(token.encode("ascii"))


def _require_session(root: Path, rows: list[dict]) -> str:
    live = _session_sha(root)
    insist(bool(rows) and rows[0]["kind"] == "RUN_OPEN" and live is not None
           and live == rows[0]["writer_session_sha256"],
           "WRITER_IS_NOT_THE_OPENING_PROCESS__RESUME_NOT_AUTHORIZED")
    return live


def _append_row(root: Path, custody: Path, lock: dict, rows: list[dict],
                row: dict) -> dict:
    _check_record(row, rows, lock, root)
    name = f"j{len(rows):08d}.json"
    raw = _json(row)
    _write_once(root, name, raw, MAX_RECORD)
    # Mirrored after local commit. A crash here can leave exactly one local
    # record ahead; explicit reconcile copies it before further progress.
    _write_once(custody, name, raw, MAX_RECORD)
    return row


def _append(root: Path, custody: Path, lock: dict, rows: list[dict],
            kind: str, update: int, payload: dict | None = None,
            telemetry: dict | None = None, reported: dict | None = None,
            writer: str | None = None) -> dict:
    row = _record(kind=kind, seq=len(rows),
                  previous=_sha(_json(rows[-1])) if rows else None,
                  lock=lock, update=update, payload=payload,
                  telemetry=telemetry, reported=reported, writer=writer)
    return _append_row(root, custody, lock, rows, row)


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
    expected_external = {"run.lock.json"} | {
        f"j{row['seq']:08d}.json" for row in rows
    }
    external_extras = {p.name for p in custody.iterdir()} - expected_external
    insist(not external_extras, "EXTERNAL_CUSTODY_UNCOMMITTED_OR_UNKNOWN")
    qdir = root / "quarantine"
    if qdir.exists() or qdir.is_symlink():
        insist(qdir.is_dir() and not qdir.is_symlink(),
               "QUARANTINE_DIR_UNSAFE")
        described = set()
        for row in rows:
            if row["kind"] == "ATTEMPT_ABORTED":
                item = row["reported"]
                if item["reason"] == "PROCESS_INTERRUPTED":
                    described |= {r["name"] for r in item["quarantined"]}
        insist({p.name for p in qdir.iterdir()} == described,
               "QUARANTINE_NOT_LINKED_TO_ABORT")
    return lock, rows


def open_journal(root: Path, custody: Path, *, run_id: str, horizon: int,
                 panel_sha256: str, config_sha256: str, rights_sha256: str,
                 initial_state_bytes: bytes, initial_probe: dict | None = None) -> dict:
    """RUN_OPEN with durable, PROBED u0 bytes in the run and an outside copy.

    The u0 probe fixes the run's u0 references for every later collapse claim.
    The writer capability lives only in this process.
    """
    _outside(root, custody)
    lock = _run_lock(run_id=run_id, horizon=horizon,
                     panel_sha256=panel_sha256, config_sha256=config_sha256,
                     rights_sha256=rights_sha256)
    insist(type(initial_state_bytes) is bytes
           and 0 < len(initial_state_bytes) <= MAX_STATE, "U0_BYTES_REQUIRED")
    insist(initial_probe is not None, "U0_PROBE_REQUIRED")
    name = "u00000.state.bin"
    state_ref = _reference(initial_state_bytes, name)
    token = secrets.token_hex(32)
    row = _record(kind="RUN_OPEN", seq=0, previous=None, lock=lock, update=0,
                  payload=state_ref,
                  telemetry=_reference(_json(initial_probe), "u00000.telemetry.json")
                  if type(initial_probe) is dict else None,
                  reported=initial_probe, writer=_sha(token.encode("ascii")))
    _check_structure(row, [], lock)
    insist(len(_json(row)) <= MAX_RECORD, "RECORD_TOO_LARGE")
    root, custody = _outside(root, custody)
    insist(not root.is_symlink() and not custody.is_symlink(), "SYMLINK_ROOT")
    root.mkdir(mode=0o700, exist_ok=True)
    custody.mkdir(mode=0o700, exist_ok=True)
    root, custody = _paths(root, custody)
    with _lock(root):
        insist({p.name for p in root.iterdir()} == {".writer.lock"}
               and not any(custody.iterdir()), "RUN_ALREADY_INITIALIZED")
        raw = _json(lock)
        _write_once(root, "run.lock.json", raw, MAX_RECORD)
        _write_once(custody, "run.lock.json", raw, MAX_RECORD)
        _write_once(root, "u00000.telemetry.json", _json(initial_probe), MAX_TELEMETRY)
        _write_once(root, name, initial_state_bytes, MAX_STATE)
        _append_row(root, custody, lock, [], row)
        _SESSIONS[str(root)] = (os.getpid(), token)
        return {"status": "OPENED_FAKE_BYTES_ONLY", "horizon": horizon,
                "run_id": run_id, "writer_session": "THIS_PROCESS_ONLY",
                "training_authorized": False}


def begin_attempt(root: Path, custody: Path, *, update: int) -> dict:
    """Persist ATTEMPT_BEGIN before a caller would execute any neural step."""
    root, custody = _paths(root, custody)
    with _lock(root):
        lock, rows = _ready(root, custody)
        writer = _require_session(root, rows)
        allowed, expected = _expected_next(rows, lock)
        insist("ATTEMPT_BEGIN" in allowed
               and type(update) is int and update == expected,
               "ATTEMPT_NOT_NEXT_UPDATE")
        row = _append(root, custody, lock, rows, "ATTEMPT_BEGIN", update,
                      writer=writer)
        return {"status": row["kind"], "update": update,
                "real_optimizer_executed": False, "training_authorized": False}


def _outcome(root: Path, custody: Path, *, update: int, kind: str,
             state_bytes: bytes | None, telemetry: dict) -> dict:
    insist(kind in OUTCOMES and type(update) is int
           and type(telemetry) is dict, "OUTCOME_ARGUMENTS")
    root, custody = _paths(root, custody)
    with _lock(root):
        lock, rows = _ready(root, custody)
        writer = _require_session(root, rows)
        allowed, expected = _expected_next(rows, lock)
        insist(kind in allowed and update == expected,
               "OUTCOME_REQUIRES_MATCHING_BEGIN")
        state_ref = None
        if kind in STATE_KINDS:
            insist(type(state_bytes) is bytes
                   and 0 < len(state_bytes) <= MAX_STATE,
                   "FULL_STATE_BYTES_REQUIRED")
            state_ref = _reference(state_bytes, f"u{update:05d}.state.bin")
        else:
            insist(state_bytes is None, "UNEXPECTED_STATE_FOR_FAILURE")
        raw = _json(telemetry)
        insist(0 < len(raw) <= MAX_TELEMETRY, "TELEMETRY_TOO_LARGE")
        tname = f"u{update:05d}.telemetry.json"
        row = _record(kind=kind, seq=len(rows), previous=_sha(_json(rows[-1])),
                      lock=lock, update=update, payload=state_ref,
                      telemetry=_reference(raw, tname), reported=telemetry,
                      writer=writer)
        # Every logical claim and the record size are refused BEFORE any byte
        # is published, so a refused claim leaves nothing to quarantine.
        _check_structure(row, rows, lock)
        insist(len(_json(row)) <= MAX_RECORD, "RECORD_TOO_LARGE")
        # Cause first (small), then state, then the record: a crash leaves the
        # typed cause durable as early as possible.
        _write_once(root, tname, raw, MAX_TELEMETRY)
        if state_ref:
            _write_once(root, state_ref["name"], state_bytes, MAX_STATE)
        record = _append_row(root, custody, lock, rows, row)
        return {
            "status": record["kind"], "update": update,
            "state_bytes_stored": state_ref["bytes"] if state_ref else 0,
            "state_sha256": state_ref["sha256"] if state_ref else None,
            "resumable": False, "physical_neural_health_proved": False,
            "training_authorized": False,
        }


def commit_reported_update(root: Path, custody: Path, *, update: int,
                           state_bytes: bytes, panel_sha256: str | None = None,
                           probe: dict | None = None) -> dict:
    """Requires a reported, state-bound probe; NEVER proves healthy biology."""
    insist(type(state_bytes) is bytes, "STATE_BYTES_TYPE")
    insist(type(probe) is dict, "COMMIT_REQUIRES_STATE_BOUND_PROBE")
    insist(panel_sha256 is None or panel_sha256 == probe.get("probe_panel_sha256"),
           "COMMITTED_PROBE_INCONSISTENT")
    return _outcome(root, custody, update=update, kind="UPDATE_COMMITTED",
                    state_bytes=state_bytes, telemetry=probe)


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


def _runtime_abort_item(update: int, receipt: dict) -> dict:
    return {"reason": "RUNTIME_ABORT", "quarantined": [], "intent": update,
            "self_reported": True, "runtime_abort_receipt": receipt,
            "uncommitted_typed_verdicts": []}


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
    return _outcome(root, custody, update=update, kind="ATTEMPT_ABORTED",
                    state_bytes=None,
                    telemetry=_runtime_abort_item(update, reported_receipt))


# ---------------------------------------------------------------- crash recovery

def _retained_paths(*directories: Path) -> list[Path]:
    return [p for d in directories for p in d.iterdir()
            if TEMP_NAME.fullmatch(p.name) is None and p.name != ".writer.lock"
            and p.is_file() and not p.is_symlink()]


def _prefix_of_retained(raw: bytes, retained: list[Path], extra: list[bytes]) -> bool:
    if any(ref.startswith(raw) for ref in extra):
        return True
    for path in retained:
        try:
            if path.stat().st_size < len(raw):
                continue
            with open(path, "rb") as stream:
                if stream.read(len(raw)) == raw:
                    return True
        except OSError:
            continue
    return False


def _drop_redundant_temps(directory: Path, retained: list[Path],
                          extra: list[bytes] = ()) -> list[dict]:
    """Remove ONLY temp files whose bytes survive elsewhere; keep the rest.

    Redundant means a hard-link twin of a retained name (crash between link and
    unlink) or a byte prefix (including empty) of retained bytes (crash part-way
    through writing a copy). Nothing unique is ever deleted.
    """
    removed = []
    for path in sorted(directory.iterdir(), key=lambda p: p.name):
        if TEMP_NAME.fullmatch(path.name) is None:
            continue
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode):
            continue
        twin = None
        if st.st_nlink == 2:
            for other in directory.iterdir():
                if TEMP_NAME.fullmatch(other.name) is None:
                    o = os.lstat(other)
                    if (o.st_dev, o.st_ino) == (st.st_dev, st.st_ino):
                        twin = other.name
                        break
        if twin is None:
            if st.st_nlink != 1 or st.st_size > MAX_STATE:
                continue
            if not _prefix_of_retained(path.read_bytes(), retained, list(extra)):
                continue
        removed.append({"name": path.name, "bytes": st.st_size,
                        "reason": ("HARD_LINK_TWIN_OF_" + twin) if twin
                        else "PREFIX_OF_RETAINED_BYTES"})
        os.unlink(path)
    if removed:
        _fsync_dir(directory)
    return removed


def _clear_redundant_debris(root: Path, custody: Path) -> list[dict]:
    retained = _retained_paths(root, custody)
    removed = [dict(e, directory="RUN") for e in _drop_redundant_temps(root, retained)]
    removed += [dict(e, directory="EXTERNAL")
                for e in _drop_redundant_temps(custody, retained)]
    return removed


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
    for path in sorted(orphan, key=lambda p: p.name):
        insist(not path.is_symlink() and path.is_file(), "QUARANTINE_UNSAFE_FILE")
        raw = _read(path, MAX_STATE)
        target = qdir / path.name
        if target.exists() or target.is_symlink():
            # A crash during an earlier recovery: keep both, never overwrite.
            target = qdir / f"{path.name}.{_sha(raw)[:16]}"
        insist(not target.exists() and not target.is_symlink(),
               "QUARANTINE_NAME_CONFLICT")
        os.rename(path, target)
        _fsync_dir(root)
        _fsync_dir(qdir)
    labels: list[dict] = []
    for path in sorted(qdir.iterdir(), key=lambda p: p.name):
        insist(not path.is_symlink() and path.is_file(), "QUARANTINE_UNSAFE_FILE")
        raw = _read(path, MAX_STATE)
        labels.append({"name": path.name, "sha256": _sha(raw),
                       "bytes": len(raw), "status": "QUARANTINED_UNVERIFIED"})
    return labels


def _complete_durable_failure(root: Path, custody: Path, lock: dict,
                              rows: list[dict], update: int) -> dict | None:
    """Finish a failure outcome whose evidence files were fully durable.

    Only STATE_COLLAPSED, ATTEMPT_FAILED and RUNTIME_ABORT are completed; the
    record is a deterministic function of those files. A crashed COMMIT is
    never completed: an interrupted success claim is recorded as an abort.
    """
    tname, sname = f"u{update:05d}.telemetry.json", f"u{update:05d}.state.bin"
    tpath, spath = root / tname, root / sname
    qdir = root / "quarantine"
    if not tpath.is_file() or qdir.exists() or qdir.is_symlink():
        # An earlier recovery already chose to quarantine: do not second-guess it.
        return None
    try:
        raw = _read(tpath, MAX_TELEMETRY)
        item = _parse(raw, "TELEMETRY")
    except (JournalRefusal, *_SCAN_ERRORS):
        return None
    if set(item) == ABORT_FIELDS:
        kind = "ATTEMPT_ABORTED" if item.get("reason") == "RUNTIME_ABORT" else None
    else:
        verdict = _typed_verdict(raw, update)
        kind = {"STATE_COLLAPSED_AFTER_STEP": "STATE_COLLAPSED",
                "ATTEMPT_FAILED_NO_COMPLETED_STEP": "ATTEMPT_FAILED"}.get(verdict)
    if kind is None:
        return None
    state_ref = None
    if kind == "STATE_COLLAPSED":
        if not spath.is_file():
            return None
        try:
            state_ref = _reference(_read(spath, MAX_STATE), sname)
        except (JournalRefusal, *_SCAN_ERRORS):
            return None
    elif spath.exists() or spath.is_symlink():
        return None
    seq, previous = len(rows), _sha(_json(rows[-1]))
    live, completed = (
        _record(kind=kind, seq=seq, previous=previous, lock=lock, update=update,
                payload=state_ref, telemetry=_reference(raw, tname),
                reported=item, writer=w)
        for w in (rows[0]["writer_session_sha256"], None))
    try:
        _check_record(completed, rows, lock, root)
    except (JournalRefusal, *_SCAN_ERRORS):
        return None
    # A part-written live record is a prefix of the deterministic live record.
    _drop_redundant_temps(root, [], [_json(live)])
    leftovers = {p.name for p in root.iterdir()} - {
        ".writer.lock", "run.lock.json", "quarantine", tname, sname,
        *(f"j{r['seq']:08d}.json" for r in rows),
        *(r[k]["name"] for r in rows for k in ("payload", "telemetry") if r[k]),
    }
    if leftovers:
        return None
    _append_row(root, custody, lock, rows, completed)
    return completed


def reconcile_one_unmirrored_record(root: Path, custody: Path) -> dict:
    """Repair interrupted mirror *only* if exactly one valid local head ahead."""
    root, custody = _paths(root, custody)
    with _lock(root):
        lock = _binding(root, custody)
        removed = _clear_redundant_debris(root, custody)
        rows, issues = _scan(root, custody, lock, tolerant=False,
                             permit_one_ahead=True)
        insist(not issues and len(rows) >= 1, "CANNOT_RECONCILE")
        local = _filenames(root)
        copies = _filenames(custody)
        if removed and len(local) == len(copies):
            # Only a redundant twin or partial copy was left; nothing to mirror.
            return {"status": "NO_UNMIRRORED_RECORD", "sequence": None,
                    "redundant_debris_removed": removed,
                    "resume_authorized": False}
        insist(len(local) == len(copies) + 1, "NOT_EXACTLY_ONE_AHEAD")
        seq = len(copies)
        name = f"j{seq:08d}.json"
        _write_once(custody, name, _read(root / name, MAX_RECORD), MAX_RECORD)
        return {"status": "ONE_VERIFIED_LOCAL_RECORD_MIRRORED",
                "sequence": seq, "redundant_debris_removed": removed,
                "resume_authorized": False}


def recover_interrupted_attempt(root: Path, custody: Path) -> dict:
    """Finish a durable failure, else quarantine stray bytes and append ABORTED."""
    root, custody = _paths(root, custody)
    with _lock(root):
        lock = _binding(root, custody)
        removed = _clear_redundant_debris(root, custody)
        rows, issues = _scan(root, custody, lock, tolerant=False)
        insist(not issues and bool(rows) and
               rows[-1]["kind"] == "ATTEMPT_BEGIN",
               "NO_UNFINISHED_ATTEMPT")
        u = rows[-1]["update"]
        completed = _complete_durable_failure(root, custody, lock, rows, u)
        if completed is not None:
            return {"status": completed["kind"], "update": u,
                    "completed_by_crash_recovery": True, "quarantined": [],
                    "redundant_debris_removed": removed,
                    "training_authorized": False}
        labels = _quarantine(root, u, rows)
        verdicts = sorted({
            v for v in (_typed_verdict((root / "quarantine" / e["name"]).read_bytes(), u)
                        for e in labels) if v is not None})
        item = {"reason": "PROCESS_INTERRUPTED", "quarantined": labels,
                "intent": u, "self_reported": True,
                "runtime_abort_receipt": None,
                "uncommitted_typed_verdicts": verdicts}
        raw = _json(item)
        tname = f"u{u:05d}.telemetry.json"
        _write_once(root, tname, raw, MAX_TELEMETRY)
        record = _append(
            root, custody, lock, rows, "ATTEMPT_ABORTED", u,
            telemetry=_reference(raw, tname), reported=item, writer=None)
        return {"status": record["kind"], "update": u,
                "quarantined": labels, "uncommitted_typed_verdicts": verdicts,
                "redundant_debris_removed": removed,
                "training_authorized": False}


def close_run(root: Path, custody: Path) -> dict:
    root, custody = _paths(root, custody)
    with _lock(root):
        lock, rows = _ready(root, custody)
        allowed, u = _expected_next(rows, lock)
        insist("RUN_CLOSED" in allowed, "CANNOT_CLOSE_INCOMPLETE_ATTEMPT")
        live = _session_sha(root)
        writer = live if live == rows[0]["writer_session_sha256"] else None
        _append(root, custody, lock, rows, "RUN_CLOSED", u, writer=writer)
        return {"status": _status(rows + [{"kind": "RUN_CLOSED"}], lock),
                "training_authorized": False}


# ---------------------------------------------------------------- reports

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


def _report(rows: list[dict], lock: dict, anomalies: list[dict],
            damaged: set[int] = frozenset()) -> dict:
    readable = [r["update"] for r in rows
                if r["kind"] in PROBED_STATES and r["seq"] not in damaged]
    collapsed = [r["update"] for r in rows if r["kind"] == "STATE_COLLAPSED"]
    uncommitted = sorted({r["update"] for r in rows if r["kind"] == "ATTEMPT_ABORTED"
                          and any(v.startswith("STATE_COLLAPSED")
                                  for v in r["reported"]["uncommitted_typed_verdicts"])}
                         | {int(a["name"][1:6]) for a in anomalies
                            if a.get("uncommitted_typed_verdict", "").startswith(
                                "STATE_COLLAPSED")})
    status = _status(rows, lock)
    return {
        "schema": SCHEMA,
        "status": status + ("__STORAGE_ANOMALIES" if anomalies else ""),
        "planned_horizon": lock["planned_horizon"], "journal_records": len(rows),
        "verified_journal_head_sha256": _sha(_json(rows[-1])) if rows else None,
        # Last state with a reported NOT_COLLAPSED probe AND intact bytes.
        "last_reported_probe_pass_checkpoint_update": readable[-1] if readable else None,
        "probe_pass_states_with_damaged_evidence": [
            r["update"] for r in rows
            if r["kind"] in PROBED_STATES and r["seq"] in damaged],
        "collapsed_state_updates_nonresumable": collapsed,
        "uncommitted_collapse_evidence_updates": uncommitted,
        "anomalies": anomalies,
        "external_copy_is_separately_retained_unsigned": True,
        "history_authentication_against_malicious_writer": False,
        "every_completed_update_has_blob": not damaged,
        "actual_neural_health_proved": False,
        "last_neurally_healthy_checkpoint_proved": False,
        "resume_authorized": False, "training_authorized": False,
        "authority": AUTHORITY,
    }


def inspect_journal(root: Path, custody: Path) -> dict:
    """Strict inventory, not actual neural-state health or restore authority."""
    root, custody = _paths(root, custody)
    with _lock(root):
        lock, rows = _ready(root, custody)
        return _report(rows, lock, [])


def _forensic_binding(root: Path, custody: Path) -> tuple[dict, list[dict]]:
    """Use whichever run-lock copy is intact; every record re-checks its SHA."""
    found, issues = [], []
    for where, directory in (("LOCAL", root), ("EXTERNAL", custody)):
        try:
            raw = _read(directory / "run.lock.json", MAX_RECORD, twin_ok=True)
            lock = _parse(raw, "RUN_LOCK")
            insist(lock == _run_lock(
                run_id=lock["run_id"], horizon=lock["planned_horizon"],
                panel_sha256=lock["panel_sha256"],
                config_sha256=lock["config_sha256"],
                rights_sha256=lock["rights_sha256"]), "RUN_BINDING_DRIFT")
            found.append((raw, lock))
        except (JournalRefusal, *_SCAN_ERRORS) as exc:
            issues.append({"name": "run.lock.json", "copy": where, "reason": str(exc),
                           "status": "DAMAGED_RUN_LOCK_COPY"})
    insist(len({raw for raw, _ in found}) == 1, "NO_SINGLE_INTACT_RUN_LOCK")
    return found[0][1], issues


def _forensic(root: Path, custody: Path) -> tuple[dict, list[dict], list[dict], set[int]]:
    lock, lock_issues = _forensic_binding(root, custody)
    rows, issues, damaged = _forensic_scan(root, custody, lock)
    return lock, rows, lock_issues + issues, damaged


def inspect_forensic_prefix(root: Path, custody: Path) -> dict:
    """Longest hash-linked chain with one intact copy; damaged evidence is listed."""
    root, custody = _paths(root, custody)
    with _lock(root):
        lock, rows, issues, damaged = _forensic(root, custody)
        known_external = {"run.lock.json"} | {
            f"j{r['seq']:08d}.json" for r in rows
        }
        for p in sorted(custody.iterdir(), key=lambda v: v.name):
            if p.name not in known_external and not RECORD_NAME.fullmatch(p.name):
                issues.append({
                    "name": p.name, "reason": "EXTERNAL_CUSTODY_ORPHAN",
                    "status": "UNVERIFIED_TAIL__NO_RESUME",
                })
        known = {".writer.lock", "run.lock.json", "quarantine"}
        for row in rows:
            known.add(f"j{row['seq']:08d}.json")
            for field in ("payload", "telemetry"):
                if row[field]:
                    known.add(row[field]["name"])
        for p in sorted(root.iterdir(), key=lambda v: v.name):
            if p.name not in known and not RECORD_NAME.fullmatch(p.name):
                entry = {"name": p.name, "reason": "UNCOMMITTED_OR_UNVERIFIED_FILE",
                         "status": "UNVERIFIED_TAIL__NO_RESUME"}
                # A typed cause whose record was lost is still first evidence.
                if TELEMETRY_NAME.fullmatch(p.name):
                    try:
                        verdict = _typed_verdict(
                            _read(p, MAX_TELEMETRY, twin_ok=True), int(p.name[1:6]))
                    except (JournalRefusal, *_SCAN_ERRORS):
                        verdict = None
                    if verdict is not None:
                        entry["uncommitted_typed_verdict"] = verdict
                issues.append(entry)
        return _report(rows, lock, issues, damaged)


def _read_state(root: Path, custody: Path, kinds: set[str], update: int) -> bytes:
    root, custody = _paths(root, custody)
    with _lock(root):
        _lock_row, rows, _issues, _damaged = _forensic(root, custody)
        matches = [r for r in rows if r["kind"] in kinds and r["update"] == update]
        insist(type(update) is int and len(matches) == 1,
               "UPDATE_NOT_VERIFIED_COMMITTED_STATE")
        ref = matches[0]["payload"]
        raw = _read(root / ref["name"], MAX_STATE, twin_ok=True)
        insist(ref == _reference(raw, ref["name"]), "STATE_CHANGED_AFTER_SCAN")
        return raw


def read_forensic_opaque_state(root: Path, custody: Path, *, update: int) -> bytes:
    """Read SHA-linked bytes of a verified probe-pass state (u0 or a commit).

    Collapse payloads are NEVER returned as candidate healthy checkpoints.
    No model loader or resume call exists in this module.
    """
    return _read_state(root, custody, PROBED_STATES, update)


def read_forensic_collapsed_state(root: Path, custody: Path, *, update: int) -> bytes:
    """Read the SHA-linked collapsed onset state for analysis. NEVER resumable."""
    return _read_state(root, custody, {"STATE_COLLAPSED"}, update)
