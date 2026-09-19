"""Prospective null-equivalence margin authority for FULL104 masking qualification.

This authority freezes the absolute equivalence scale before terminal FULL104
masking outcomes are opened. Historical masking material is bound only as a
scale-context sanity check; it carries no current FULL104 data, target, fold,
burden, seed, row-cap, policy-selection, PASS, runtime, or training authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from typing import Mapping, Any

PRIMARY_SCORE_ID = "SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1"
HISTORICAL_SCALE_CONTEXT_SHA256 = "2b2cebd922e8a6c37a67f58fda10b3069a76a4bc00d1f9e8636fbcb1d8ac6dd6"
HISTORICAL_ROLE_ID = (
    "HISTORICAL_MASKING_SCALE_CONTEXT_ONLY__NO_FULL104_DATA_TARGET_FOLD_BURDEN_"
    "SEED_ROW_CAP_POLICY_PASS_RUNTIME_OR_TRAINING_AUTHORITY_V1"
)
MARGIN_SELECTION_POLICY_ID = (
    "PROSPECTIVE_ABSOLUTE_SCORE_EQUIVALENCE_0P001__HISTORICAL_SCALE_CONTEXT_"
    "SANITY_CHECK_ONLY_V1"
)
MARGIN_NUMERATOR = 1
MARGIN_DENOMINATOR = 1000


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: Mapping[str, Any]) -> str:
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
class NullEquivalenceMarginAuthorityV1:
    authority_id: str
    historical_scale_context_artifact_sha256: str
    primary_score_id: str = PRIMARY_SCORE_ID
    historical_role_id: str = HISTORICAL_ROLE_ID
    margin_selection_policy_id: str = MARGIN_SELECTION_POLICY_ID
    margin_numerator: int = MARGIN_NUMERATOR
    margin_denominator: int = MARGIN_DENOMINATOR
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    @property
    def margin(self) -> float:
        self.validate()
        return float(Fraction(self.margin_numerator, self.margin_denominator))

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        historical = _sha(
            self.historical_scale_context_artifact_sha256,
            "historical_scale_context_artifact_sha256",
        )
        if historical != HISTORICAL_SCALE_CONTEXT_SHA256:
            raise ValueError("historical scale-context artifact is not the frozen exact byte source")
        if self.primary_score_id != PRIMARY_SCORE_ID:
            raise ValueError("primary_score_id mismatch")
        if self.historical_role_id != HISTORICAL_ROLE_ID:
            raise ValueError("historical_role_id mismatch")
        if self.margin_selection_policy_id != MARGIN_SELECTION_POLICY_ID:
            raise ValueError("margin_selection_policy_id mismatch")
        if (
            isinstance(self.margin_numerator, bool)
            or isinstance(self.margin_denominator, bool)
            or not isinstance(self.margin_numerator, int)
            or not isinstance(self.margin_denominator, int)
            or (self.margin_numerator, self.margin_denominator)
            != (MARGIN_NUMERATOR, MARGIN_DENOMINATOR)
        ):
            raise ValueError("null-equivalence margin must remain exactly 1/1000")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("margin authority must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("margin authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_NULL_EQUIVALENCE_MARGIN_AUTHORITY_V1",
                **asdict(self),
                "margin": self.margin,
            }
        )
