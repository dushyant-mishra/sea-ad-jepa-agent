"""Successor masking-policy authority repairing the MaskingAuthorityV1 schema defect.

MaskingAuthorityV1 accepts free-form identifiers and binds no SHA roots, so any string can
masquerade as a policy and no artifact is actually pinned. That is the same weakness that
was repaired for the target-address provider authority, and it is repaired the same way:
enumerated vocabulary plus exact-root binding, failing closed on anything else.

SCHEMA REPAIR ONLY. No production masking policy is instantiated or frozen here; the V2
shortcut lane has not scientifically qualified. The frozen MaskingAuthorityV1 is untouched.

Mask burden deliberately does NOT live on this authority. V1 established that
MaskingAuthorityV1 references a separate target-evidence-budget authority; this successor
binds that authority by digest rather than absorbing its numbers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple

from .current_target_address_provider_authority_v1 import (
    CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256,
    KNOWN_RAW_ARTIFACT_SHA256,
)

APPROVED_MASKING_POLICY_IDS: Tuple[str, ...] = (
    "V5_UNIFORM_RANDOM_MASK_V1",
    "V5_UNIFORM_PLUS_SHORTCUT_COMASK_V2",
)
APPROVED_TARGET_EVIDENCE_BUDGET_AUTHORITY_IDS: Tuple[str, ...] = (
    "V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1",
)
APPROVED_RNG_REPLAY_AUTHORITY_IDS: Tuple[str, ...] = (
    "V5_DETERMINISTIC_MASK_REPLAY_AUTHORITY_V1",
)
APPROVED_ELIGIBILITY_POLICY_IDS: Tuple[str, ...] = (
    "SUPPORT_ESTIMABILITY_AUTHORITY_ELIGIBILITY_V1",
)
APPROVED_FALLBACK_POLICY_IDS: Tuple[str, ...] = (
    "DETERMINISTIC_UNIFORM_FALLBACK_V1",
    "DETERMINISTIC_CONSERVATIVE_EXPANSION_V1",
)

_FORBIDDEN_NAME_FRAGMENTS = ("TD57", "TD59", "TD60", "CORRMASK")

_ROLE_FIELDS = (
    "canonical_registry_authority_sha256",
    "support_estimability_authority_sha256",
    "shortcut_artifact_sha256",
    "target_evidence_budget_authority_sha256",
    "rng_replay_authority_sha256",
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
        raise ValueError(f"{name} must be one of the approved current values {approved!r}, got {value!r}")
    if any(t in value.upper() for t in _FORBIDDEN_NAME_FRAGMENTS):
        raise ValueError(f"{name} must not be selected by a historical experiment name")
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class CurrentMaskingPolicyAuthorityV2:
    authority_id: str
    canonical_registry_authority_sha256: str
    support_estimability_authority_sha256: str
    shortcut_artifact_sha256: str
    masking_policy_id: str
    target_evidence_budget_authority_id: str
    target_evidence_budget_authority_sha256: str
    rng_replay_authority_id: str
    eligibility_policy_id: str
    fallback_policy_id: str
    rng_replay_authority_sha256: str
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")

        for name in _ROLE_FIELDS:
            _sha(getattr(self, name), name)

        # exact root, allowlist of one -- an unknown digest fails closed
        if self.canonical_registry_authority_sha256 != CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256:
            raise ValueError(
                "canonical_registry_authority_sha256 must equal the current canonical "
                f"address-registry authority digest {CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256}"
            )
        # a raw artifact file digest is never an authority root
        for name in _ROLE_FIELDS:
            if getattr(self, name) in KNOWN_RAW_ARTIFACT_SHA256:
                raise ValueError(f"{name} must be an authority digest, not a raw artifact file digest")

        # role splicing: five distinct roles may never share one digest
        seen = [getattr(self, n) for n in _ROLE_FIELDS]
        if len(set(seen)) != len(seen):
            raise ValueError("authority roots must be distinct; roles may not share one digest")

        _enum(self.masking_policy_id, APPROVED_MASKING_POLICY_IDS, "masking_policy_id")
        _enum(self.target_evidence_budget_authority_id,
              APPROVED_TARGET_EVIDENCE_BUDGET_AUTHORITY_IDS, "target_evidence_budget_authority_id")
        _enum(self.rng_replay_authority_id, APPROVED_RNG_REPLAY_AUTHORITY_IDS, "rng_replay_authority_id")
        _enum(self.eligibility_policy_id, APPROVED_ELIGIBILITY_POLICY_IDS, "eligibility_policy_id")
        _enum(self.fallback_policy_id, APPROVED_FALLBACK_POLICY_IDS, "fallback_policy_id")

        if self.training_authorized is not False:
            raise ValueError("masking policy authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha({"schema": "V5_CURRENT_MASKING_POLICY_AUTHORITY_V2",
                               **asdict(self), "training_authorized": False})
