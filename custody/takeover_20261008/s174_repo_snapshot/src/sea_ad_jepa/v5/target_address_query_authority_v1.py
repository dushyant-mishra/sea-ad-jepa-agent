"""Target-address query authority with no built-in provider or sharing choice."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping


def _nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value.strip()


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class TargetAddressQueryAuthorityV1:
    authority_id: str
    address_registry_authority_sha256: str
    query_provider_id: str
    query_artifact_sha256: str
    replay_policy_id: str
    parameter_sharing_policy_id: str
    gradient_policy_id: str
    training_authorized: bool = False

    def validate(self) -> None:
        _nonempty(self.authority_id, "authority_id")
        _sha(
            self.address_registry_authority_sha256,
            "address_registry_authority_sha256",
        )
        _nonempty(self.query_provider_id, "query_provider_id")
        _sha(self.query_artifact_sha256, "query_artifact_sha256")
        _nonempty(self.replay_policy_id, "replay_policy_id")
        _nonempty(self.parameter_sharing_policy_id, "parameter_sharing_policy_id")
        _nonempty(self.gradient_policy_id, "gradient_policy_id")
        if self.training_authorized is not False:
            raise ValueError("target-address authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_TARGET_ADDRESS_QUERY_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )
