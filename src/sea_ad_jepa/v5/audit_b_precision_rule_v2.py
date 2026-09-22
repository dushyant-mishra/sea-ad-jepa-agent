"""Prospective Audit-B hybrid precision rule V2.

Scientific resolution
---------------------
Audit-B sample escalation is controlled by one predeclared primary burden cell:
RIDGE8_CONDITIONAL at the first (5%) burden rung.

Precision is sufficient when

    SE <= max(1/860, 0.05 * abs(mean))

where 860 is the exact uniform-mask cardinality at the 5% rung over the frozen
17,186-address strict core:

    1 target + floor((17,186 - 1) * 1/20) = 860.

The absolute floor prevents a precisely null/near-null burden effect from
producing arbitrarily large relative standard error merely because the mean is
near zero. It is fixed from mask geometry before N1; it is not estimated from an
Audit-B outcome.

The remaining 17 nonuniform policy x rung cells remain mandatory reports but do
not control N1 -> N2 -> N3 escalation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from typing import Any, Mapping, Sequence

import numpy as np

from .audit_b_production_burden_v1 import BURDEN_RUNGS, NONUNIFORM_POLICIES

STRICT_CORE_ADDRESSES = 17_186
PRIMARY_POLICY_ID = "RIDGE8_CONDITIONAL"
PRIMARY_RUNG = Fraction(1, 20)

RELATIVE_SE_TOLERANCE = Fraction(1, 20)
PRIMARY_MASK_CARDINALITY = (
    1
    + ((STRICT_CORE_ADDRESSES - 1) * PRIMARY_RUNG.numerator)
    // PRIMARY_RUNG.denominator
)
ABSOLUTE_SE_TOLERANCE = Fraction(1, PRIMARY_MASK_CARDINALITY)

PRECISION_ESTIMATOR_ID = (
    "HYBRID_ABSOLUTE_OR_RELATIVE_TARGET_SAMPLE_SE_V2"
)
ABSOLUTE_TOLERANCE_ORIGIN_ID = (
    "ONE_AVERAGE_MASKED_ADDRESS_SHARE_AT_PRIMARY_5_PERCENT_RUNG_V1"
)
ZERO_MEAN_RULE_ID = "ZERO_MEAN_USES_ABSOLUTE_SE_BRANCH_V1"
PRECISION_SCOPE_ID = "ONE_PREDECLARED_PRIMARY_BURDEN_STATISTIC_V1"
REPORTING_SCOPE_ID = "ALL_3_NONUNIFORM_X_6_RUNG_CELLS_REPORTED_V1"

SAMPLE_LEVEL_TO_N = {"N1": 256, "N2": 1024, "N3": 4096}
PRECISION_RULE_AUTHORITY_ID = "JEPA_V5_FULL104_AUDIT_B_PRECISION_RULE_AUTHORITY_V2"


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class AuditBPrecisionRuleAuthorityV2:
    authority_id: str = PRECISION_RULE_AUTHORITY_ID
    strict_core_addresses: int = STRICT_CORE_ADDRESSES
    precision_scope_id: str = PRECISION_SCOPE_ID
    reporting_scope_id: str = REPORTING_SCOPE_ID
    primary_policy_id: str = PRIMARY_POLICY_ID
    primary_rung_numerator: int = PRIMARY_RUNG.numerator
    primary_rung_denominator: int = PRIMARY_RUNG.denominator
    primary_mask_cardinality: int = PRIMARY_MASK_CARDINALITY
    precision_estimator_id: str = PRECISION_ESTIMATOR_ID
    relative_se_tolerance_numerator: int = RELATIVE_SE_TOLERANCE.numerator
    relative_se_tolerance_denominator: int = RELATIVE_SE_TOLERANCE.denominator
    absolute_se_tolerance_numerator: int = ABSOLUTE_SE_TOLERANCE.numerator
    absolute_se_tolerance_denominator: int = ABSOLUTE_SE_TOLERANCE.denominator
    absolute_tolerance_origin_id: str = ABSOLUTE_TOLERANCE_ORIGIN_ID
    zero_mean_rule_id: str = ZERO_MEAN_RULE_ID

    def validate(self) -> None:
        expected = {
            "authority_id": PRECISION_RULE_AUTHORITY_ID,
            "strict_core_addresses": STRICT_CORE_ADDRESSES,
            "precision_scope_id": PRECISION_SCOPE_ID,
            "reporting_scope_id": REPORTING_SCOPE_ID,
            "primary_policy_id": PRIMARY_POLICY_ID,
            "primary_rung_numerator": PRIMARY_RUNG.numerator,
            "primary_rung_denominator": PRIMARY_RUNG.denominator,
            "primary_mask_cardinality": PRIMARY_MASK_CARDINALITY,
            "precision_estimator_id": PRECISION_ESTIMATOR_ID,
            "relative_se_tolerance_numerator": RELATIVE_SE_TOLERANCE.numerator,
            "relative_se_tolerance_denominator": RELATIVE_SE_TOLERANCE.denominator,
            "absolute_se_tolerance_numerator": ABSOLUTE_SE_TOLERANCE.numerator,
            "absolute_se_tolerance_denominator": ABSOLUTE_SE_TOLERANCE.denominator,
            "absolute_tolerance_origin_id": ABSOLUTE_TOLERANCE_ORIGIN_ID,
            "zero_mean_rule_id": ZERO_MEAN_RULE_ID,
        }
        for name, value in expected.items():
            if getattr(self, name) != value:
                raise ValueError(f"{name} drifted from the reviewed precision rule")
        expected_cardinality = 1 + (
            (self.strict_core_addresses - 1) * self.primary_rung_numerator
        ) // self.primary_rung_denominator
        if self.primary_mask_cardinality != expected_cardinality:
            raise ValueError("primary mask cardinality is inconsistent with frozen geometry")
        if self.absolute_se_tolerance_denominator != self.primary_mask_cardinality:
            raise ValueError(
                "absolute SE tolerance must remain one average primary-mask address share"
            )

    def canonical_digest(self) -> str:
        self.validate()
        return hashlib.sha256(
            _canonical(
                {
                    "schema": "V5_AUDIT_B_PRECISION_RULE_AUTHORITY_V2",
                    **asdict(self),
                }
            )
        ).hexdigest()


@dataclass(frozen=True)
class PrecisionSummaryV2:
    policy_id: str
    rung_numerator: int
    rung_denominator: int
    n_targets: int
    mean_normalized_delta_detected: float
    target_sample_sd: float
    standard_error: float
    absolute_se_tolerance: float
    relative_se_tolerance: float
    relative_threshold: float
    applied_precision_threshold: float
    threshold_branch: str
    precision_passed: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def hybrid_precision_summary(
    *,
    policy_id: str,
    rung: Fraction,
    target_values: Sequence[float],
) -> PrecisionSummaryV2:
    if policy_id not in NONUNIFORM_POLICIES:
        raise ValueError("precision summary is defined for non-uniform policies only")
    if rung not in BURDEN_RUNGS:
        raise ValueError("rung must be one of the six frozen burden rungs")

    x = np.asarray(target_values, dtype=np.float64)
    if x.ndim != 1 or x.size < 2 or not np.all(np.isfinite(x)):
        raise ValueError("target_values must contain >=2 finite target-level values")

    mean = float(x.mean())
    sd = float(x.std(ddof=1))
    se = float(sd / np.sqrt(x.size))
    absolute = float(ABSOLUTE_SE_TOLERANCE)
    relative_tolerance = float(RELATIVE_SE_TOLERANCE)
    relative = relative_tolerance * abs(mean)
    threshold = max(absolute, relative)
    branch = "ABSOLUTE_FLOOR" if absolute >= relative else "RELATIVE_TO_ABS_MEAN"

    return PrecisionSummaryV2(
        policy_id=policy_id,
        rung_numerator=int(rung.numerator),
        rung_denominator=int(rung.denominator),
        n_targets=int(x.size),
        mean_normalized_delta_detected=mean,
        target_sample_sd=sd,
        standard_error=se,
        absolute_se_tolerance=absolute,
        relative_se_tolerance=relative_tolerance,
        relative_threshold=relative,
        applied_precision_threshold=threshold,
        threshold_branch=branch,
        precision_passed=bool(np.isfinite(se) and se <= threshold),
    )


def require_primary_summary(summary: PrecisionSummaryV2, *, sample_level: str) -> None:
    if sample_level not in SAMPLE_LEVEL_TO_N:
        raise ValueError("sample_level must be N1, N2, or N3")
    if summary.policy_id != PRIMARY_POLICY_ID:
        raise ValueError("escalation summary must use the frozen primary policy")
    if (summary.rung_numerator, summary.rung_denominator) != (
        PRIMARY_RUNG.numerator,
        PRIMARY_RUNG.denominator,
    ):
        raise ValueError("escalation summary must use the frozen primary burden rung")
    if summary.n_targets != SAMPLE_LEVEL_TO_N[sample_level]:
        raise ValueError("primary precision summary target count does not match sample level")


def escalation_decision_v2(
    summary: PrecisionSummaryV2,
    *,
    sample_level: str,
) -> dict[str, Any]:
    """Precision-only prefix escalation for the one frozen primary cell."""
    require_primary_summary(summary, sample_level=sample_level)

    if summary.precision_passed:
        return {
            "state": "SUFFICIENT_PRECISION",
            "sample_level": sample_level,
            "next_sample_authorized": None,
            "precision_scope_id": PRECISION_SCOPE_ID,
            "precision_estimator_id": PRECISION_ESTIMATOR_ID,
            "primary_policy_id": PRIMARY_POLICY_ID,
            "primary_rung": [PRIMARY_RUNG.numerator, PRIMARY_RUNG.denominator],
        }

    if sample_level == "N1":
        state, nxt = "ESCALATE_TO_N2", "N2"
    elif sample_level == "N2":
        state, nxt = "ESCALATE_TO_N3", "N3"
    else:
        state, nxt = "INSUFFICIENT_PRECISION_AT_N3", None
    return {
        "state": state,
        "sample_level": sample_level,
        "next_sample_authorized": nxt,
        "precision_scope_id": PRECISION_SCOPE_ID,
        "precision_estimator_id": PRECISION_ESTIMATOR_ID,
        "primary_policy_id": PRIMARY_POLICY_ID,
        "primary_rung": [PRIMARY_RUNG.numerator, PRIMARY_RUNG.denominator],
    }
