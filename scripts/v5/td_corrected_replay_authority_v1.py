"""Replay-only authority binding and one-shot start-marker state machine."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


class AuthorityError(ValueError):
    pass


SCOPE = "TD_CORRECTED_REPLAY_EXECUTE_ONCE"
FORBIDDEN_FLAGS = (
    "g6_execution_authorized",
    "g7_execution_authorized",
    "target_selection_authorized",
    "td60_authorized",
    "stage4_authorized",
    "training_authorized",
)


@dataclass(frozen=True)
class BoundReplayAuthority:
    contract_sha256: str
    qualification_receipt_sha256: str
    implementation_commit: str
    namespace: Path
    authority_ids: tuple[str, str, str]


def _validate_one(
    authority: dict[str, Any],
    *,
    contract_sha256: str,
    qualification_receipt_sha256: str,
    implementation_commit: str,
    namespace: Path,
) -> str:
    if authority.get("scope") != SCOPE:
        raise AuthorityError(f"authority scope must be {SCOPE}")
    expected = {
        "contract_sha256": contract_sha256,
        "qualification_receipt_sha256": qualification_receipt_sha256,
        "implementation_commit": implementation_commit,
        "namespace": str(namespace),
    }
    for key, value in expected.items():
        if authority.get(key) != value:
            raise AuthorityError(f"authority {key} mismatch")
    if authority.get("replay_execution_authorized") is not True:
        raise AuthorityError("replay_execution_authorized must be true")
    for flag in FORBIDDEN_FLAGS:
        if authority.get(flag) is not False:
            raise AuthorityError(f"{flag} must be false")
    authority_id = authority.get("authority_id")
    if not isinstance(authority_id, str) or not authority_id:
        raise AuthorityError("authority_id is required")
    upper = authority_id.upper()
    if "G6_" in upper or "G7_" in upper or upper.startswith("G6") or upper.startswith("G7"):
        raise AuthorityError("predecessor authority may not be reused for corrected replay")
    return authority_id


def assert_fresh_namespace(path: Path) -> None:
    if path.exists():
        raise AuthorityError(f"replay namespace must be fresh and absent: {path}")


def bind_replay_authority(
    contract_sha256: str,
    qualification_receipt_sha256: str,
    implementation_commit: str,
    namespace: Path,
    owner_authority: dict[str, Any],
    runtime_authority: dict[str, Any],
    operational_authority: dict[str, Any],
) -> BoundReplayAuthority:
    assert_fresh_namespace(namespace)
    ids = tuple(
        _validate_one(
            authority,
            contract_sha256=contract_sha256,
            qualification_receipt_sha256=qualification_receipt_sha256,
            implementation_commit=implementation_commit,
            namespace=namespace,
        )
        for authority in (owner_authority, runtime_authority, operational_authority)
    )
    if len(set(ids)) != 3:
        raise AuthorityError("owner/runtime/operational authority IDs must be distinct")
    return BoundReplayAuthority(
        contract_sha256=contract_sha256,
        qualification_receipt_sha256=qualification_receipt_sha256,
        implementation_commit=implementation_commit,
        namespace=namespace,
        authority_ids=ids,
    )


def begin_attempt(bound: BoundReplayAuthority, namespace: Path) -> Path:
    if namespace != bound.namespace:
        raise AuthorityError("namespace does not match bound replay authority")
    assert_fresh_namespace(namespace)
    try:
        namespace.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise AuthorityError(f"replay namespace already exists: {namespace}") from exc
    marker = namespace / "TD_CORRECTED_REPLAY_EXECUTION_START.json"
    payload = {
        "schema": "JEPA_TD_CORRECTED_REPLAY_EXECUTION_START_V1",
        "scope": SCOPE,
        "contract_sha256": bound.contract_sha256,
        "qualification_receipt_sha256": bound.qualification_receipt_sha256,
        "implementation_commit": bound.implementation_commit,
        "namespace": str(namespace),
        "authority_ids": list(bound.authority_ids),
        "spent_authority": True,
        "target_selected": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }
    data = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(marker, flags, 0o444)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    return marker
