"""Prospective qualification precision authority for current V5.

No production sample-size or confidence value is supplied by this module. A
prospective authority instance must provide them before scientific outcomes are
inspected.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_UNCERTAINTY_METHOD_IDS: Tuple[str, ...] = (
    "TARGET_CLUSTERED_BOOTSTRAP_V1",
)
APPROVED_INSUFFICIENT_SUPPORT_POLICY_IDS: Tuple[str, ...] = (
    "FAIL_CLOSED_IF_BELOW_PRECISION_V1",
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
    return value


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class QualificationPrecisionAuthorityV1:
    authority_id: str
    support_estimability_authority_sha256: str
    uncertainty_method_id: str
    confidence_level_numerator: int
    confidence_level_denominator: int
    bootstrap_replicates: int
    min_target_count: int
    min_target_fold_unit_count: int
    min_outer_fold_count: int
    insufficient_support_policy_id: str
    training_authorized: bool = False

    @property
    def confidence_level(self) -> float:
        self.validate()
        return self.confidence_level_numerator / self.confidence_level_denominator

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        _sha(self.support_estimability_authority_sha256, "support_estimability_authority_sha256")
        _enum(self.uncertainty_method_id, APPROVED_UNCERTAINTY_METHOD_IDS, "uncertainty_method_id")
        _enum(
            self.insufficient_support_policy_id,
            APPROVED_INSUFFICIENT_SUPPORT_POLICY_IDS,
            "insufficient_support_policy_id",
        )
        numerator = _nonnegative_int(self.confidence_level_numerator, "confidence_level_numerator")
        denominator = _positive_int(self.confidence_level_denominator, "confidence_level_denominator")
        if numerator == 0 or numerator >= denominator:
            raise ValueError("confidence level must lie strictly between zero and one")
        _positive_int(self.bootstrap_replicates, "bootstrap_replicates")
        _positive_int(self.min_target_count, "min_target_count")
        _positive_int(self.min_target_fold_unit_count, "min_target_fold_unit_count")
        _positive_int(self.min_outer_fold_count, "min_outer_fold_count")
        if self.training_authorized is not False:
            raise ValueError("qualification precision authority cannot authorize training")

    def assert_sufficient(self, *, target_count: int, target_fold_unit_count: int, outer_fold_count: int) -> None:
        self.validate()
        observed = {
            "target_count": target_count,
            "target_fold_unit_count": target_fold_unit_count,
            "outer_fold_count": outer_fold_count,
        }
        required = {
            "target_count": self.min_target_count,
            "target_fold_unit_count": self.min_target_fold_unit_count,
            "outer_fold_count": self.min_outer_fold_count,
        }
        for name, value in observed.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < required[name]:
                raise ValueError(f"{name} is below the frozen precision requirement")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_QUALIFICATION_PRECISION_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )
