"""FULL104 donor-target precision authority V4 with a real interval-width gate.

The 128-target panel is a prospective planning size, not proof of adequate
precision. V4 binds the pre-FULL104 32-target primary and nonlinear summaries
used only for planning, then requires the actual FULL104 paired donor-target
intervals to meet an explicit width ceiling before any masking PASS can issue.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from .precision_authority_v2 import paired_target_donor_bootstrap

METHOD_ID = "PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE_BOOTSTRAP_V2"
INSUFFICIENT_POLICY_ID = "FAIL_CLOSED_IF_BELOW_PRECISION_OR_INTERVAL_WIDTH_V4"
PLANNING_POLICY_ID = "HISTORICAL_32_TARGET_VARIANCE_FOR_SAMPLE_SIZE_PLANNING_ONLY_V1"
CONFIDENCE_NUMERATOR = 95
CONFIDENCE_DENOMINATOR = 100
BOOTSTRAP_REPLICATES = 4096
MIN_TARGET_COUNT = 128
MIN_DONOR_COUNT = 104
MIN_OUTER_FOLD_COUNT = 4
MAX_HALF_WIDTH_NUMERATOR = 3
MAX_HALF_WIDTH_DENOMINATOR = 1000
SEED_NAMESPACE = "V5_FULL104_PRECISION_ROOT_DERIVED_V4"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


@dataclass(frozen=True)
class QualificationPrecisionAuthorityV4:
    authority_id: str
    support_estimability_authority_sha256: str
    target_panel_authority_sha256: str
    outer_split_authority_sha256: str
    historical_primary32_summary_sha256: str
    historical_nonlinear32_summary_sha256: str
    uncertainty_method_id: str = METHOD_ID
    planning_policy_id: str = PLANNING_POLICY_ID
    confidence_level_numerator: int = CONFIDENCE_NUMERATOR
    confidence_level_denominator: int = CONFIDENCE_DENOMINATOR
    bootstrap_replicates: int = BOOTSTRAP_REPLICATES
    min_target_count: int = MIN_TARGET_COUNT
    min_donor_count: int = MIN_DONOR_COUNT
    min_outer_fold_count: int = MIN_OUTER_FOLD_COUNT
    max_two_sided_half_width_numerator: int = MAX_HALF_WIDTH_NUMERATOR
    max_two_sided_half_width_denominator: int = MAX_HALF_WIDTH_DENOMINATOR
    insufficient_support_policy_id: str = INSUFFICIENT_POLICY_ID
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    @property
    def confidence_level(self) -> float:
        self.validate()
        return self.confidence_level_numerator / self.confidence_level_denominator

    @property
    def max_two_sided_half_width(self) -> float:
        self.validate()
        return self.max_two_sided_half_width_numerator / self.max_two_sided_half_width_denominator

    @property
    def bootstrap_seed(self) -> int:
        self.validate()
        payload = {
            "schema": "V5_FULL104_PRECISION_ROOT_DERIVED_SEED_V4",
            "namespace": SEED_NAMESPACE,
            "support_estimability_authority_sha256": self.support_estimability_authority_sha256,
            "target_panel_authority_sha256": self.target_panel_authority_sha256,
            "outer_split_authority_sha256": self.outer_split_authority_sha256,
            "historical_primary32_summary_sha256": self.historical_primary32_summary_sha256,
            "historical_nonlinear32_summary_sha256": self.historical_nonlinear32_summary_sha256,
        }
        return int.from_bytes(hashlib.sha256(_canonical(payload)).digest()[:8], "big")

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = (
            _sha(self.support_estimability_authority_sha256, "support_estimability_authority_sha256"),
            _sha(self.target_panel_authority_sha256, "target_panel_authority_sha256"),
            _sha(self.outer_split_authority_sha256, "outer_split_authority_sha256"),
            _sha(self.historical_primary32_summary_sha256, "historical_primary32_summary_sha256"),
            _sha(self.historical_nonlinear32_summary_sha256, "historical_nonlinear32_summary_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("precision V4 roots must be role-distinct")
        if self.uncertainty_method_id != METHOD_ID:
            raise ValueError("uncertainty_method_id mismatch")
        if self.planning_policy_id != PLANNING_POLICY_ID:
            raise ValueError("planning_policy_id mismatch")
        if (self.confidence_level_numerator, self.confidence_level_denominator) != (95, 100):
            raise ValueError("confidence level must remain 95/100")
        if self.bootstrap_replicates != 4096:
            raise ValueError("bootstrap_replicates must remain 4096")
        if self.min_target_count != 128:
            raise ValueError("min_target_count must remain 128")
        if self.min_donor_count != 104:
            raise ValueError("min_donor_count must remain 104")
        if self.min_outer_fold_count != 4:
            raise ValueError("min_outer_fold_count must remain 4")
        if (
            self.max_two_sided_half_width_numerator,
            self.max_two_sided_half_width_denominator,
        ) != (3, 1000):
            raise ValueError("max two-sided half-width must remain the pre-FULL104 value 3/1000")
        if self.insufficient_support_policy_id != INSUFFICIENT_POLICY_ID:
            raise ValueError("insufficient_support_policy_id mismatch")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("precision V4 must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("precision authority cannot authorize training")

    def assert_sufficient(self, *, target_count: int, donor_count: int, outer_fold_count: int) -> None:
        self.validate()
        if target_count < self.min_target_count:
            raise ValueError("target_count is below frozen precision requirement")
        if donor_count < self.min_donor_count:
            raise ValueError("donor_count is below frozen precision requirement")
        if outer_fold_count < self.min_outer_fold_count:
            raise ValueError("outer_fold_count is below frozen precision requirement")

    def interval(self, matrix, donor_source_code):
        self.validate()
        return paired_target_donor_bootstrap(
            matrix,
            donor_source_code,
            replicates=self.bootstrap_replicates,
            seed=self.bootstrap_seed,
            confidence_level=self.confidence_level,
        )

    def assert_interval_precise(self, interval: Any, *, label: str) -> None:
        self.validate()
        if not isinstance(label, str) or not label.strip():
            raise ValueError("label must be nonempty")
        lo = float(interval.lower_two_sided)
        hi = float(interval.upper_two_sided)
        if not (lo <= hi):
            raise ValueError(f"{label} interval is reversed")
        half_width = (hi - lo) / 2.0
        if half_width > self.max_two_sided_half_width + 1e-15:
            raise ValueError(
                f"{label} interval half-width {half_width:.12g} exceeds frozen "
                f"precision ceiling {self.max_two_sided_half_width:.12g}"
            )

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({
            "schema": "V5_QUALIFICATION_PRECISION_AUTHORITY_V4",
            **asdict(self),
            "bootstrap_seed": self.bootstrap_seed,
        })
