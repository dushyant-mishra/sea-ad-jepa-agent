"""Current target-address provider authority with an ENUMERATED policy vocabulary.

Successor to TargetAddressQueryAuthorityV1, which validates only that its policy fields
are nonempty strings -- so "anything", "TD60" or "trust_me_shared" all pass. That is
insufficient: arbitrary text can masquerade as a legitimate policy, and a historical
experiment name must never select behaviour.

This authority accepts only frozen current vocabulary, and refuses raw artifact hashes
where an authority digest is required.

Deliberately NOT in scope: width, depth, transformer geometry, mask fraction, optimizer,
EMA timescale, seed, proposal law.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple

# --- frozen current vocabulary ------------------------------------------------
# Provider family/version. No historical experiment name may appear here.
APPROVED_QUERY_PROVIDER_IDS: Tuple[str, ...] = ("V5_SHARED_ADDRESS_QUERY_PROVIDER_V1",)

# One shared trainable mechanism. A per-address independent table would be an imported
# biological memory and is deliberately absent; it would need its own authority.
APPROVED_PARAMETER_SHARING_POLICY_IDS: Tuple[str, ...] = (
    "SHARED_TRAINABLE_ADDRESS_QUERY_MECHANISM_V1",
)

# Provider parameters must be reachable from the real context/evidence -> prediction loss.
APPROVED_GRADIENT_POLICY_IDS: Tuple[str, ...] = (
    "CONTEXT_EVIDENCE_TO_PREDICTION_GRADIENT_REACHABLE_V1",
)

# All learned provider state plus the deterministic metadata needed to reproduce
# address -> query behaviour exactly across checkpoint/restart.
APPROVED_REPLAY_POLICY_IDS: Tuple[str, ...] = (
    "FULL_PROVIDER_STATE_DETERMINISTIC_REPLAY_V1",
)

# Raw artifact digests that are NOT authority digests. Supplying one of these where an
# authority digest is required is a role-splicing error and must fail closed.
KNOWN_RAW_ARTIFACT_SHA256: Tuple[str, ...] = (
    "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd",  # registry csv
    "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537",  # observation state npz
    "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29",  # full104 block manifest
)

_FORBIDDEN_NAME_FRAGMENTS = ("TD57", "TD59", "TD60")


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
        raise ValueError(
            f"{name} must be one of the approved current values {approved!r}, got {value!r}"
        )
    if any(tag in value.upper() for tag in _FORBIDDEN_NAME_FRAGMENTS):
        raise ValueError(f"{name} must not be selected by a historical experiment name")
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class CurrentTargetAddressProviderAuthorityV1:
    authority_id: str
    address_registry_authority_sha256: str
    query_provider_id: str
    query_artifact_sha256: str
    replay_policy_id: str
    parameter_sharing_policy_id: str
    gradient_policy_id: str
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")

        _sha(self.address_registry_authority_sha256, "address_registry_authority_sha256")
        if self.address_registry_authority_sha256 in KNOWN_RAW_ARTIFACT_SHA256:
            raise ValueError(
                "address_registry_authority_sha256 must be the canonical registry AUTHORITY "
                "digest, not a raw artifact file digest"
            )
        _sha(self.query_artifact_sha256, "query_artifact_sha256")

        _enum(self.query_provider_id, APPROVED_QUERY_PROVIDER_IDS, "query_provider_id")
        _enum(self.replay_policy_id, APPROVED_REPLAY_POLICY_IDS, "replay_policy_id")
        _enum(self.parameter_sharing_policy_id, APPROVED_PARAMETER_SHARING_POLICY_IDS,
              "parameter_sharing_policy_id")
        _enum(self.gradient_policy_id, APPROVED_GRADIENT_POLICY_IDS, "gradient_policy_id")

        if self.training_authorized is not False:
            raise ValueError("target-address provider authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_CURRENT_TARGET_ADDRESS_PROVIDER_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )
