"""Base-learning scientific estimand binding, independent of sampling and rank qualification."""
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
class BaseTrainingEstimandAuthorityV1:
    authority_id: str
    population_authority_sha256: str
    support_estimability_authority_sha256: str
    support_eligibility_authority_sha256: str
    estimand_id: str
    scientific_weight_artifact_sha256: str
    scientific_weight_schema_id: str
    weight_normalization_id: str
    weight_unit_id: str
    training_authorized: bool = False

    def validate(self) -> None:
        _nonempty(self.authority_id, "authority_id")
        _sha(self.population_authority_sha256, "population_authority_sha256")
        _sha(self.support_estimability_authority_sha256, "support_estimability_authority_sha256")
        _sha(
            self.support_eligibility_authority_sha256,
            "support_eligibility_authority_sha256",
        )
        _nonempty(self.estimand_id, "estimand_id")
        _sha(
            self.scientific_weight_artifact_sha256,
            "scientific_weight_artifact_sha256",
        )
        _nonempty(self.scientific_weight_schema_id, "scientific_weight_schema_id")
        _nonempty(self.weight_normalization_id, "weight_normalization_id")
        _nonempty(self.weight_unit_id, "weight_unit_id")
        if self.training_authorized is not False:
            raise ValueError("base estimand authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_BASE_TRAINING_ESTIMAND_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )
