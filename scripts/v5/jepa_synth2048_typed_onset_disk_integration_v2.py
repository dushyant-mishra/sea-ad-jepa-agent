#!/usr/bin/env python3
"""Versioned non-training bridge: reported failure cause -> fsynced opaque journal.

This is NOT a trainer, full V5 checkpoint, physical gradient probe, external
trust anchor, signed chain or independent scientific verdict. The older raw
byte writer is kept for original #555/#559/#561 regression compatibility.
Use this typed API only for a prospective reviewed integration, never to
claim a user-supplied receipt is a measured neural observation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from scripts.v5 import jepa_synth2048_checkpoint_capture_prefreeze_v1 as r
from scripts.v5 import jepa_synth2048_atomic_checkpoint_bytes_v1 as d

SCHEMA = "JEPA_SYNTH2048_TYPED_FAILED_ONSET_DISK_BRIDGE_V2"
AUTHORITY = r.AUTHORITY


class TypedOnsetRefusal(ValueError):
    pass


def require(ok: bool, code: str) -> None:
    if not bool(ok):
        raise TypedOnsetRefusal("REFUSE_V5_TYPED_ONSET_DISK_V2__" + code)


def _canonical_bytes(value: dict) -> bytes:
    # The same canonical JSON encoding used by the physical write-once journal.
    return d._json(value)


def _validate_and_copy(receipt: Mapping[str, object]) -> tuple[dict, dict]:
    require(type(receipt) is dict, "EXACT_RECEIPT_DICTIONARY_REQUIRED")
    # Never accept nested arrays, alternate fields, or an uncaused failure.
    try:
        result = r.validate_failed_attempt_onset_receipt(receipt)
    except r.CaptureRefusal as exc:
        raise TypedOnsetRefusal("REFUSE_V5_TYPED_ONSET_DISK_V2__" + str(exc)) from exc
    # Roundtrip ensures the disk record is stable, JSON-only (no NaN), and
    # exact, not a mutable caller reference. This does NOT authenticate input.
    try:
        raw = _canonical_bytes(receipt)
        copy = json.loads(raw)
    except (ValueError, TypeError, OverflowError) as exc:
        raise TypedOnsetRefusal(
            "REFUSE_V5_TYPED_ONSET_DISK_V2__NONCANONICAL_TELEMETRY") from exc
    require(type(copy) is dict and copy == receipt, "TELEMETRY_JSON_ROUNDTRIP_CHANGED")
    return copy, result


def _check_index_and_horizon(*, horizon: int, completed: list[int],
                             attempted: int) -> None:
    require(bool(completed), "U0_CHECKPOINT_REQUIRED")
    last = completed[-1]
    require(attempted == last + 1, "FAILED_ATTEMPT_NOT_NEXT_COMPLETED_STEP")
    require(attempted <= horizon + 1, "ATTEMPT_BEYOND_PLANNED_HORIZON")
    # Beyond u40 physical writer may checkpoint sparsely; a failed attempt
    # following an unseen successful update is NOT proven by these bytes.
    # Refuse unless the immediately preceding successful update is recorded.


def save_typed_failed_onset(
    root: Path, *, horizon: int, run_id: str, failed_receipt: dict,
) -> dict:
    """Physically fsync a canonical cause-checked failure receipt as STOP bytes.

    The storage journal's existing lock/intent/receipt/chain checks remain
    authoritative only for byte custody, not true tensor measurements.
    """
    receipt, logical = _validate_and_copy(failed_receipt)
    current = d.verify_storage(Path(root), horizon=horizon, run_id=run_id)
    require(not current["failed_attempt_recorded_as_untrusted_stop"],
            "FAILED_ONSET_ALREADY_PRESENT")
    _check_index_and_horizon(
        horizon=horizon, completed=current["complete_captured_updates"],
        attempted=receipt["update_index"])
    saved = d.save_failed_attempt_evidence(
        Path(root), horizon=horizon, run_id=run_id,
        attempted_update=receipt["update_index"],
        evidence_bytes=_canonical_bytes(receipt))
    require(saved["resumable"] is False
            and saved["training_authorized"] is False
            and saved["attempted_update"] == receipt["update_index"],
            "PHYSICAL_STOP_PROMOTED")
    # Read back through the actual disk integrity path before reporting success.
    verified = read_typed_failed_onset(Path(root), horizon=horizon, run_id=run_id)
    require(verified["cause"] == logical["failure_cause"],
            "ROUNDTRIP_CAUSE_MISMATCH")
    return verified


def read_typed_failed_onset(root: Path, *, horizon: int, run_id: str) -> dict:
    """Read bytes physically verified by #559 and validate #562 reported cause."""
    raw = d.read_verified_failed_attempt_evidence(
        Path(root), horizon=horizon, run_id=run_id)
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise TypedOnsetRefusal("REFUSE_V5_TYPED_ONSET_DISK_V2__BAD_STOP_JSON") from exc
    require(type(value) is dict and raw == _canonical_bytes(value),
            "STOP_NOT_CANONICAL_JSON")
    receipt, logical = _validate_and_copy(value)
    physical = d.verify_storage(Path(root), horizon=horizon, run_id=run_id)
    require(physical["failed_attempt_recorded_as_untrusted_stop"] is True,
            "STOP_NOT_ON_PHYSICAL_JOURNAL")
    require(physical["failed_attempt_update"] == receipt["update_index"],
            "STOP_INDEX_DIFFERS_FROM_PHYSICAL_JOURNAL")
    require(physical["last_good_checkpoint_before_failure"] is not None
            and receipt["update_index"] ==
                physical["last_good_checkpoint_before_failure"] + 1,
            "STOP_NOT_AFTER_LAST_COMMITTED_CHECKPOINT")
    return {
        "schema": SCHEMA,
        "status": "TYPED_REPORTED_CAUSE_STORED_AND_SHA_VERIFIED__NO_MODEL_PROOF",
        "failed_attempt_update": receipt["update_index"],
        "cause": logical["failure_cause"],
        "cause_origin": logical["failure_cause_origin"],
        "last_good_checkpoint_update": physical["last_good_checkpoint_before_failure"],
        "collapse_probe_self_reported": logical["collapse_probe_self_reported"],
        "typed_failure_bytes_physically_sha_verified": True,
        "cause_physically_measured_from_neural_tensors": False,
        "actual_successful_updates_physically_proved": False,
        "full_model_payload_or_adam_verified": False,
        "external_head_authenticated": False,
        "model_resume_authorized": False,
        "training_authorized": False,
        "authority": AUTHORITY,
    }


def inspect_run_without_promoting_early_stop(
    root: Path, *, horizon: int, run_id: str,
) -> dict:
    """Classify a clean incomplete run as incomplete, never planned success."""
    disk = d.verify_storage(Path(root), horizon=horizon, run_id=run_id)
    checkpoints = disk["complete_captured_updates"]
    failure = disk["failed_attempt_recorded_as_untrusted_stop"]
    planned_reached = bool(checkpoints) and checkpoints[-1] == horizon
    cause = read_typed_failed_onset(root, horizon=horizon, run_id=run_id) if failure else None
    return {
        "schema": SCHEMA,
        "status": (
            "TYPED_STOP_RECORDED__NOT_RESUMABLE" if failure else
            "PLANNED_STORAGE_HORIZON_REACHED__NOT_MODEL_PROOF" if planned_reached else
            "INCOMPLETE_RUN_WITHOUT_RECORDED_STOP__NOT_PLANNED_SUCCESS"
        ),
        "planned_horizon": horizon,
        "last_recorded_checkpoint": checkpoints[-1] if checkpoints else None,
        "failure": cause,
        "early_stop_not_silently_called_planned": not failure and not planned_reached,
        "internal_sha_only": True,
        "physical_gradient_ema_adam_proved": False,
        "model_resume_authorized": False,
        "training_authorized": False,
        "authority": AUTHORITY,
    }


def inspect_forensic_prefix_only(root: Path, *, horizon: int, run_id: str) -> dict:
    """Read #563/#564 forensic prefix without interpreting uncommitted STOP."""
    report = d.inspect_verified_prefix_read_only(
        Path(root), horizon=horizon, run_id=run_id)
    require(report["resume_authorized"] is False, "FORENSIC_PROMOTED")
    return {
        "schema": SCHEMA,
        "status": "FORENSIC_PREFIX_ONLY__UNCOMMITTED_STOP_CAUSE_NOT_ESTABLISHED",
        "last_good_checkpoint_update": (
            report["verified_checkpoint_prefix"][-1]
            if report["verified_checkpoint_prefix"] else None),
        "uncommitted_orphans": report["uncommitted_orphans"],
        "last_good_model_state_proved": False,
        "external_head_authenticated": False,
        "model_resume_authorized": False,
        "training_authorized": False,
        "authority": AUTHORITY,
    }
