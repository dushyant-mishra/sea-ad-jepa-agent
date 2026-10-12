"""Fail-closed QUALIFY / EXECUTE_ONCE controller for the real target tournament."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Mapping


class RealTournamentControllerError(ValueError):
    pass


_ALLOWED_REPLAY = {"PASS", "FAIL", "NOT_ESTIMABLE"}
_AUTHORITY_KEYS = {
    "schema", "real_tournament_authorized", "single_attempt",
    "replay_receipt_sha256", "gate_executor_manifest_sha256",
    "target_selection_authorized", "td60_authorized", "stage4_authorized",
    "training_authorized",
}


def _is_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _validate_replay(replay_context: Mapping) -> None:
    if not isinstance(replay_context, Mapping):
        raise RealTournamentControllerError("replay context mapping required")
    if replay_context.get("relational_status") not in _ALLOWED_REPLAY:
        raise RealTournamentControllerError("replay relational_status must be PASS/FAIL/NOT_ESTIMABLE")
    if replay_context.get("externally_audited") is not True:
        raise RealTournamentControllerError("corrected replay must be externally audited before tournament qualification")
    if not _is_sha256(replay_context.get("receipt_sha256")):
        raise RealTournamentControllerError("replay receipt_sha256 must be lowercase SHA-256")


def _validate_manifest(manifest: Mapping) -> bool:
    if not isinstance(manifest, Mapping) or manifest.get("schema") != "JEPA_TD_REAL_GATE_EXECUTOR_READINESS_V1":
        raise RealTournamentControllerError("gate executor readiness manifest schema mismatch")
    if not _is_sha256(manifest.get("manifest_sha256")):
        raise RealTournamentControllerError("gate executor readiness manifest_sha256 must be lowercase SHA-256")
    ready = manifest.get("all_required_roles_materialized")
    if ready not in {True, False}:
        raise RealTournamentControllerError("all_required_roles_materialized must be boolean")
    return bool(ready)


def qualify(replay_context: Mapping, gate_executor_manifest: Mapping, *, namespace: str | Path) -> dict:
    _validate_replay(replay_context)
    ready = _validate_manifest(gate_executor_manifest)
    path = Path(namespace)
    if path.exists():
        raise RealTournamentControllerError("qualification requires a fresh nonexistent namespace")
    terminal = (
        "PASS_TD_REAL_TOURNAMENT_EXECUTOR_QUALIFICATION__NO_REAL_CANDIDATE_RESULTS__EXECUTION_AUTHORITY_REQUIRED"
        if ready
        else "BLOCKED_GATE_EXECUTOR_RULES_NOT_MATERIALIZED__NO_OUTCOME_READ"
    )
    return {
        "schema": "JEPA_TD_REAL_TOURNAMENT_QUALIFY_RECEIPT_V1",
        "terminal": terminal,
        "corrected_relational_replay_status": replay_context["relational_status"],
        "replay_receipt_sha256": replay_context["receipt_sha256"],
        "gate_executor_manifest_sha256": gate_executor_manifest["manifest_sha256"],
        "gate_executor_roles_ready": ready,
        "protected_values_read": False,
        "start_marker_created": False,
        "real_tournament_authorized": False,
        "target_selection_authorized": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }


def _validate_authority(authority: Mapping | None, replay_context: Mapping, manifest: Mapping) -> None:
    if not isinstance(authority, Mapping) or set(authority) != _AUTHORITY_KEYS:
        raise RealTournamentControllerError("exact execution authority record required")
    if authority.get("schema") != "JEPA_TD_REAL_TOURNAMENT_EXECUTION_AUTHORITY_V1":
        raise RealTournamentControllerError("execution authority schema mismatch")
    if authority.get("real_tournament_authorized") is not True or authority.get("single_attempt") is not True:
        raise RealTournamentControllerError("execution authority must authorize exactly one real tournament attempt")
    if authority.get("replay_receipt_sha256") != replay_context.get("receipt_sha256"):
        raise RealTournamentControllerError("execution authority replay binding mismatch")
    if authority.get("gate_executor_manifest_sha256") != manifest.get("manifest_sha256"):
        raise RealTournamentControllerError("execution authority gate-executor binding mismatch")
    for key in ("target_selection_authorized", "td60_authorized", "stage4_authorized", "training_authorized"):
        if authority.get(key) is not False:
            raise RealTournamentControllerError(f"execution authority must keep {key}=false")


def execute_once(replay_context: Mapping, gate_executor_manifest: Mapping, *, namespace: str | Path, authority: Mapping | None, runner: Callable[[Path], Mapping]) -> dict:
    _validate_replay(replay_context)
    ready = _validate_manifest(gate_executor_manifest)
    if not ready:
        raise RealTournamentControllerError("gate executors are not materialized; execution forbidden")
    _validate_authority(authority, replay_context, gate_executor_manifest)
    path = Path(namespace)
    if path.exists():
        raise RealTournamentControllerError("execution namespace already exists; one-shot namespace cannot be reused")
    path.mkdir(parents=True, exist_ok=False)
    marker = {
        "schema": "JEPA_TD_REAL_TOURNAMENT_START_MARKER_V1",
        "replay_receipt_sha256": replay_context["receipt_sha256"],
        "gate_executor_manifest_sha256": gate_executor_manifest["manifest_sha256"],
        "single_attempt": True,
    }
    (path / "START_MARKER.json").write_text(json.dumps(marker, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    try:
        result = runner(path)
        if not isinstance(result, Mapping):
            raise RealTournamentControllerError("runner must return mapping evidence")
        receipt = {
            "schema": "JEPA_TD_REAL_TOURNAMENT_EXECUTION_RECEIPT_V1",
            "terminal": "REAL_TARGET_TOURNAMENT_EXECUTION_COMPLETED__STOP_FOR_INDEPENDENT_AUDIT",
            "spent_authority": True,
            "start_marker_created": True,
            "candidate_receipts_present": "candidate_receipts" in result,
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        }
        (path / "EXECUTION_RECEIPT.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return receipt
    except Exception as exc:
        failure = {
            "schema": "JEPA_TD_REAL_TOURNAMENT_FAILURE_V1",
            "spent_authority": True,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        }
        (path / "FAILURE.json").write_text(json.dumps(failure, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        raise
