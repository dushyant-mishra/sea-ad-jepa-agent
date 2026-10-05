from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


def _sha(v: object, name: str) -> str:
    if not isinstance(v, str) or len(v) != 64 or v != v.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(v, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return v


def _id(v: object, name: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{name} must be nonempty")
    return v.strip()


def _digest(p: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(p, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()


@dataclass(frozen=True)
class BiologicalSpecificityAuthorityV1:
    authority_id: str
    qualification_design_sha256: str
    qualification_execution_sha256: str
    nuisance_class_sha256: str
    outcome_firewall_sha256: str
    claim_scope: str
    semantic_twin_boundary_acknowledged: bool
    passed: bool
    training_authorized: bool = False

    def _payload(self) -> dict[str, Any]:
        if self.training_authorized is not False:
            raise ValueError("biological-specificity authority cannot authorize training")
        if self.passed is not True:
            raise ValueError("biological-specificity qualification must be EXECUTED_PASS")
        if self.semantic_twin_boundary_acknowledged is not True:
            raise ValueError("same-RNA semantic-twin boundary must be acknowledged")
        return {
            "schema": "V5_BIOLOGICAL_SPECIFICITY_AUTHORITY_V1",
            "authority_id": _id(self.authority_id, "authority_id"),
            "qualification_design_sha256": _sha(self.qualification_design_sha256, "qualification_design_sha256"),
            "qualification_execution_sha256": _sha(self.qualification_execution_sha256, "qualification_execution_sha256"),
            "nuisance_class_sha256": _sha(self.nuisance_class_sha256, "nuisance_class_sha256"),
            "outcome_firewall_sha256": _sha(self.outcome_firewall_sha256, "outcome_firewall_sha256"),
            "claim_scope": _id(self.claim_scope, "claim_scope"),
            "semantic_twin_boundary_acknowledged": True,
            "passed": True,
            "training_authorized": False,
        }

    def validate(self) -> None:
        self._payload()

    def canonical_digest(self) -> str:
        return _digest(self._payload())
