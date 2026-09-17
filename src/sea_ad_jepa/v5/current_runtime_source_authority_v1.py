"""Exact current-V5 runtime source and environment authority.

This authority binds the reviewed multifile source package, runtime environment,
and exact current-V5 entrypoint. Historical V4 production_update is explicitly
inadmissible. The authority records runtime provenance only and cannot authorize
training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_SOURCE_PACKAGING_POLICY_IDS: Tuple[str, ...] = (
    "MULTIFILE_SOURCE_MANIFEST_AND_ROOT_V1",
)
APPROVED_ENTRYPOINT_POLICY_IDS: Tuple[str, ...] = (
    "CURRENT_V5_ENTRYPOINT_ONLY__NO_V4_PRODUCTION_UPDATE_V1",
)
APPROVED_RUNTIME_ABI_IDS: Tuple[str, ...] = (
    "CPYTHON_RUNTIME_ABI_EXACTLY_RECORDED_V1",
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _enum(value: object, approved: Tuple[str, ...], name: str) -> str:
    if not isinstance(value, str) or value not in approved:
        raise ValueError(f"{name} must be one of {approved!r}, got {value!r}")
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class CurrentRuntimeSourceAuthorityV1:
    authority_id: str
    source_manifest_sha256: str
    source_root_sha256: str
    runtime_environment_artifact_sha256: str
    entrypoint_source_sha256: str
    source_packaging_policy_id: str
    entrypoint_policy_id: str
    runtime_abi_id: str
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")

        root_fields = (
            "source_manifest_sha256",
            "source_root_sha256",
            "runtime_environment_artifact_sha256",
            "entrypoint_source_sha256",
        )
        roots = [_sha(getattr(self, name), name) for name in root_fields]
        if len(set(roots)) != len(roots):
            raise ValueError("runtime-source authority roots must be distinct")

        _enum(
            self.source_packaging_policy_id,
            APPROVED_SOURCE_PACKAGING_POLICY_IDS,
            "source_packaging_policy_id",
        )
        _enum(self.entrypoint_policy_id, APPROVED_ENTRYPOINT_POLICY_IDS, "entrypoint_policy_id")
        _enum(self.runtime_abi_id, APPROVED_RUNTIME_ABI_IDS, "runtime_abi_id")

        if self.training_authorized is not False:
            raise ValueError("runtime source authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_CURRENT_RUNTIME_SOURCE_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )
