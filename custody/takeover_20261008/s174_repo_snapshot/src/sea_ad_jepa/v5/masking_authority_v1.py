"""Outcome-blind masking-policy authority with no built-in policy defaults."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping


def _nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value.strip()


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _positive_int(value: object, name: str) -> int:
    out = _nonnegative_int(value, name)
    if out < 1:
        raise ValueError(f"{name} must be a positive integer")
    return out


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class MaskingAuthorityV1:
    policy_id: str
    dependency_source_authority_id: str
    random_mixture_numerator: int
    structural_mixture_numerator: int
    mixture_denominator: int
    target_evidence_budget_authority_id: str
    rng_authority_id: str
    training_authorized: bool = False

    def validate(self) -> None:
        _nonempty(self.policy_id, "policy_id")
        _nonempty(self.dependency_source_authority_id, "dependency_source_authority_id")
        random_n = _nonnegative_int(self.random_mixture_numerator, "random_mixture_numerator")
        structural_n = _nonnegative_int(self.structural_mixture_numerator, "structural_mixture_numerator")
        denominator = _positive_int(self.mixture_denominator, "mixture_denominator")
        if random_n + structural_n != denominator:
            raise ValueError("mixture numerators must sum to mixture_denominator")
        _nonempty(self.target_evidence_budget_authority_id, "target_evidence_budget_authority_id")
        _nonempty(self.rng_authority_id, "rng_authority_id")
        if self.training_authorized is not False:
            raise ValueError("masking authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha256({"schema": "V5_MASKING_AUTHORITY_V1", **asdict(self), "training_authorized": False})
