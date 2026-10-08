"""Successor masking-policy authority repairing the MaskingAuthorityV1 schema defect.

Masking policy selects *which* eligible evidence is additionally masked. Numeric
burden remains owned by TargetEvidenceBudgetAuthorityV1. V2 binds exact current
registry/support/budget/replay roots and can revalidate the live support, budget,
and RNG authorities so well-formed placeholder hashes cannot satisfy closure.
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
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


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
        if self.canonical_registry_authority_sha256 != CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256:
            raise ValueError(
                "canonical_registry_authority_sha256 must equal the current canonical "
                f"address-registry authority digest {CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256}"
            )
        for name in _ROLE_FIELDS:
            if getattr(self, name) in KNOWN_RAW_ARTIFACT_SHA256:
                raise ValueError(f"{name} must be an authority digest, not a raw artifact file digest")
        seen = [getattr(self, name) for name in _ROLE_FIELDS]
        if len(set(seen)) != len(seen):
            raise ValueError("authority roots must be distinct; roles may not share one digest")

        _enum(self.masking_policy_id, APPROVED_MASKING_POLICY_IDS, "masking_policy_id")
        _enum(
            self.target_evidence_budget_authority_id,
            APPROVED_TARGET_EVIDENCE_BUDGET_AUTHORITY_IDS,
            "target_evidence_budget_authority_id",
        )
        _enum(self.rng_replay_authority_id, APPROVED_RNG_REPLAY_AUTHORITY_IDS, "rng_replay_authority_id")
        _enum(self.eligibility_policy_id, APPROVED_ELIGIBILITY_POLICY_IDS, "eligibility_policy_id")
        _enum(self.fallback_policy_id, APPROVED_FALLBACK_POLICY_IDS, "fallback_policy_id")
        if self.training_authorized is not False:
            raise ValueError("masking policy authority cannot authorize training")

    def bind_live_authorities(
        self,
        *,
        support_estimability: Any,
        target_evidence_budget: Any,
        rng_replay: Any,
    ) -> None:
        self.validate()
        observed_support = _live_digest(support_estimability, "support estimability")
        if observed_support != self.support_estimability_authority_sha256:
            raise ValueError("support estimability authority root mismatch")
        observed_budget = _live_digest(target_evidence_budget, "target evidence budget")
        if observed_budget != self.target_evidence_budget_authority_sha256:
            raise ValueError("target evidence budget authority root mismatch")
        observed_rng = _live_digest(rng_replay, "rng replay")
        if observed_rng != self.rng_replay_authority_sha256:
            raise ValueError("rng replay authority root mismatch")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_CURRENT_MASKING_POLICY_AUTHORITY_V2",
                **asdict(self),
                "training_authorized": False,
            }
        )
