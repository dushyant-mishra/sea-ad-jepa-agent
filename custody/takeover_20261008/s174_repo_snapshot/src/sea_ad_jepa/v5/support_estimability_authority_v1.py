"""Support/estimability invariants for current V5 without choosing target-component support."""
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
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class SupportEstimabilityAuthorityV1:
    authority_id: str
    full104_substrate_sha256: str
    measurement_support_authority_sha256: str
    comparable_common_core_artifact_sha256: str
    target_eligibility_rule_id: str
    missing_value_semantics_id: str
    common_core_role_semantics_id: str
    native_support_role_semantics_id: str
    support_to_latent_semantics_policy_id: str
    training_authorized: bool = False

    def validate(self) -> None:
        _nonempty(self.authority_id, "authority_id")
        _sha(self.full104_substrate_sha256, "full104_substrate_sha256")
        _sha(self.measurement_support_authority_sha256, "measurement_support_authority_sha256")
        _sha(self.comparable_common_core_artifact_sha256, "comparable_common_core_artifact_sha256")
        _nonempty(self.target_eligibility_rule_id, "target_eligibility_rule_id")
        _nonempty(self.missing_value_semantics_id, "missing_value_semantics_id")
        _nonempty(self.common_core_role_semantics_id, "common_core_role_semantics_id")
        _nonempty(self.native_support_role_semantics_id, "native_support_role_semantics_id")
        _nonempty(self.support_to_latent_semantics_policy_id, "support_to_latent_semantics_policy_id")
        if self.training_authorized is not False:
            raise ValueError("support/estimability authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha({"schema": "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1", **asdict(self), "training_authorized": False})
