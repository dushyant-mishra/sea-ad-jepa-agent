"""Hash-bound primary-representation contract with no built-in representation choice."""
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
class PrimaryRepresentationAuthorityV1:
    authority_id: str
    substrate_authority_sha256: str
    support_authority_sha256: str
    feature_artifact_sha256: str
    feature_selection_artifact_sha256: str
    representation_semantics_id: str
    primary_channel_role_id: str
    observation_channel_policy_id: str
    training_authorized: bool = False

    def validate(self) -> None:
        _nonempty(self.authority_id, "authority_id")
        _sha(self.substrate_authority_sha256, "substrate_authority_sha256")
        _sha(self.support_authority_sha256, "support_authority_sha256")
        _sha(self.feature_artifact_sha256, "feature_artifact_sha256")
        _sha(
            self.feature_selection_artifact_sha256,
            "feature_selection_artifact_sha256",
        )
        _nonempty(self.representation_semantics_id, "representation_semantics_id")
        _nonempty(self.primary_channel_role_id, "primary_channel_role_id")
        _nonempty(self.observation_channel_policy_id, "observation_channel_policy_id")
        if self.training_authorized is not False:
            raise ValueError("representation authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_PRIMARY_REPRESENTATION_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )
