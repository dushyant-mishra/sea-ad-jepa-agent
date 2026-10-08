"""Prospective numeric parameters for canonical FULL104 masking qualification.

These values are outcome-relevant and therefore must be frozen before qualification
outcomes are inspected. The schema supplies no production defaults.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple

PRIMARY_ATTACKER_ID = "RIDGE_EXPRESSION_PROXY_ATTACKER_V1"
PRIMARY_SCORE_ID = "SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1"


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _unit_fraction(num: object, den: object, name: str, *, allow_zero: bool) -> Tuple[int, int]:
    numerator = _nonnegative_int(num, f"{name}_numerator")
    denominator = _positive_int(den, f"{name}_denominator")
    if numerator > denominator or (numerator == 0 and not allow_zero):
        bound = "[0,1]" if allow_zero else "(0,1]"
        raise ValueError(f"{name} must lie in {bound}")
    return numerator, denominator


def _positive_fraction(num: object, den: object, name: str) -> Tuple[int, int]:
    numerator = _positive_int(num, f"{name}_numerator")
    denominator = _positive_int(den, f"{name}_denominator")
    return numerator, denominator


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class MaskingQualificationParametersAuthorityV1:
    authority_id: str
    primary_attacker_id: str
    primary_score_id: str
    targeted_partner_cap: int
    ridge_candidate_pool_count: int
    ridge_score_feature_count: int
    ridge_alpha_numerator: int
    ridge_alpha_denominator: int
    prefix_inner_fold_count: int
    prefix_candidate_count: int
    prefix_floor_numerator: int
    prefix_floor_denominator: int
    prefix_reduction_numerator: int
    prefix_reduction_denominator: int
    training_authorized: bool = False

    @property
    def ridge_alpha(self) -> float:
        self.validate()
        return self.ridge_alpha_numerator / self.ridge_alpha_denominator

    @property
    def prefix_floor(self) -> float:
        self.validate()
        return self.prefix_floor_numerator / self.prefix_floor_denominator

    @property
    def prefix_reduction(self) -> float:
        self.validate()
        return self.prefix_reduction_numerator / self.prefix_reduction_denominator

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        if self.primary_attacker_id != PRIMARY_ATTACKER_ID:
            raise ValueError(f"primary_attacker_id must equal {PRIMARY_ATTACKER_ID}")
        if self.primary_score_id != PRIMARY_SCORE_ID:
            raise ValueError(f"primary_score_id must equal {PRIMARY_SCORE_ID}")
        cap = _positive_int(self.targeted_partner_cap, "targeted_partner_cap")
        candidate_pool = _positive_int(self.ridge_candidate_pool_count, "ridge_candidate_pool_count")
        _positive_int(self.ridge_score_feature_count, "ridge_score_feature_count")
        if candidate_pool < cap:
            raise ValueError("ridge_candidate_pool_count must be at least targeted_partner_cap")
        _positive_fraction(self.ridge_alpha_numerator, self.ridge_alpha_denominator, "ridge_alpha")
        if self.prefix_inner_fold_count != 3:
            raise ValueError("prefix_inner_fold_count must equal 3 for PREFIX3_SELECTIVE")
        _positive_int(self.prefix_candidate_count, "prefix_candidate_count")
        _unit_fraction(self.prefix_floor_numerator, self.prefix_floor_denominator, "prefix_floor", allow_zero=True)
        _unit_fraction(
            self.prefix_reduction_numerator,
            self.prefix_reduction_denominator,
            "prefix_reduction",
            allow_zero=False,
        )
        if self.training_authorized is not False:
            raise ValueError("masking qualification parameters cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )
