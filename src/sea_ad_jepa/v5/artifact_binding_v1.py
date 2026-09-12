from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Mapping


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def artifact_sha256(payload: object) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


def _parents(parent_sha256: Mapping[str, object]) -> dict[str, str]:
    if not isinstance(parent_sha256, Mapping):
        raise ValueError("parent_sha256 must be a mapping")
    out: dict[str, str] = {}
    for key, value in parent_sha256.items():
        if not isinstance(key, str) or not key:
            raise ValueError("parent names must be nonempty strings")
        out[key] = _sha(value, f"parent_sha256[{key}]")
    return dict(sorted(out.items()))


def seal_artifact(schema: str, payload: Mapping[str, object], parent_sha256: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(schema, str) or not schema:
        raise ValueError("schema must be nonempty")
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    body = {
        "schema": schema,
        "payload": deepcopy(dict(payload)),
        "parent_sha256": _parents(parent_sha256),
    }
    return {**body, "artifact_sha256": artifact_sha256(body)}


def validate_artifact(
    envelope: Mapping[str, object],
    *,
    expected_schema: str,
    expected_parents: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(envelope, Mapping) or set(envelope) != {"schema", "payload", "parent_sha256", "artifact_sha256"}:
        raise ValueError("artifact envelope schema mismatch")
    if envelope.get("schema") != expected_schema:
        raise RuntimeError("STOP_V5_ARTIFACT_SCHEMA_MISMATCH")
    observed_parents = _parents(envelope.get("parent_sha256"))
    wanted_parents = _parents(expected_parents)
    if observed_parents != wanted_parents:
        raise RuntimeError("STOP_V5_ARTIFACT_PARENT_MISMATCH")
    payload = envelope.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("artifact payload must be a mapping")
    body = {
        "schema": envelope["schema"],
        "payload": dict(payload),
        "parent_sha256": observed_parents,
    }
    observed_digest = _sha(envelope.get("artifact_sha256"), "artifact_sha256")
    expected_digest = artifact_sha256(body)
    if observed_digest != expected_digest:
        raise RuntimeError("STOP_V5_ARTIFACT_DIGEST_MISMATCH")
    return deepcopy(dict(payload))
