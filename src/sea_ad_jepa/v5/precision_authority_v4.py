"""FULL104 precision authority V4 bound to control-calibrated target count.

The terminal estimand is explicitly conditional on the three observed source
populations (HVS, NPH52, SEA_AD). Sources are not treated as exchangeable draws
from a superpopulation; uncertainty resamples targets and donors within each
fixed source and reports source-specific guardrails separately.

V4 also freezes the prospective residual-equivalence margin. The terminal
negative-control confidence interval must fit wholly inside +/- that margin.
Its observed width can therefore never enlarge the masking qualification bar.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from typing import Any, Mapping

from .precision_authority_v2 import paired_target_donor_bootstrap

METHOD_ID = "PAIRED_TARGET_AND_DONOR_WITHIN_FIXED_SOURCE_BOOTSTRAP_V4"
SOURCE_POPULATION_FRAME_ID = "FIXED_OBSERVED_SOURCES_HVS_NPH52_SEA_AD_V1"
SOURCE_AGGREGATION_ESTIMAND_ID = "EQUAL_WEIGHT_MEAN_OVER_FIXED_HVS_NPH52_SEA_AD_SOURCES_V1"
INSUFFICIENT_POLICY_ID = "FAIL_CLOSED_IF_BELOW_PRECISION_V2"
NEGATIVE_CONTROL_PRECISION_POLICY_ID = (
    "NEGATIVE_CONTROL_95CI_MUST_CONTAIN_ZERO_AND_FIT_INSIDE_FROZEN_EQUIVALENCE_MARGIN_V1"
)
CONFIDENCE_NUMERATOR = 95
CONFIDENCE_DENOMINATOR = 100
BOOTSTRAP_REPLICATES = 4096
SEED_NAMESPACE = "V5_FULL104_PRECISION_ROOT_DERIVED_V4"


def _sha(v, n):
    if not isinstance(v, str) or len(v) != 64 or v != v.lower():
        raise ValueError(f"{n} must be a lowercase SHA-256 digest")
    try:
        int(v, 16)
    except ValueError as e:
        raise ValueError(f"{n} must be a lowercase SHA-256 digest") from e
    return v


def _canonical(p):
    return json.dumps(
        p, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def _digest(p):
    return hashlib.sha256(_canonical(p)).hexdigest()


@dataclass(frozen=True)
class QualificationPrecisionAuthorityV4:
    authority_id: str
    support_estimability_authority_sha256: str
    target_panel_authority_sha256: str
    target_panel_sizing_receipt_sha256: str
    outer_split_authority_sha256: str
    required_target_count: int
    null_equivalence_margin_numerator: int
    null_equivalence_margin_denominator: int
    uncertainty_method_id: str = METHOD_ID
    source_population_frame_id: str = SOURCE_POPULATION_FRAME_ID
    source_aggregation_estimand_id: str = SOURCE_AGGREGATION_ESTIMAND_ID
    confidence_level_numerator: int = CONFIDENCE_NUMERATOR
    confidence_level_denominator: int = CONFIDENCE_DENOMINATOR
    bootstrap_replicates: int = BOOTSTRAP_REPLICATES
    min_donor_count: int = 104
    min_outer_fold_count: int = 4
    insufficient_support_policy_id: str = INSUFFICIENT_POLICY_ID
    negative_control_precision_policy_id: str = NEGATIVE_CONTROL_PRECISION_POLICY_ID
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    @property
    def confidence_level(self):
        self.validate()
        return self.confidence_level_numerator / self.confidence_level_denominator

    @property
    def null_equivalence_margin(self) -> float:
        self.validate()
        return float(
            Fraction(
                self.null_equivalence_margin_numerator,
                self.null_equivalence_margin_denominator,
            )
        )

    @property
    def bootstrap_seed(self):
        self.validate()
        return int.from_bytes(
            hashlib.sha256(
                _canonical(
                    {
                        "schema": "V5_FULL104_PRECISION_ROOT_DERIVED_SEED_V4",
                        "namespace": SEED_NAMESPACE,
                        "support": self.support_estimability_authority_sha256,
                        "panel": self.target_panel_authority_sha256,
                        "sizing": self.target_panel_sizing_receipt_sha256,
                        "split": self.outer_split_authority_sha256,
                        "source_population_frame_id": self.source_population_frame_id,
                        "source_aggregation_estimand_id": self.source_aggregation_estimand_id,
                        "null_equivalence_margin": [
                            self.null_equivalence_margin_numerator,
                            self.null_equivalence_margin_denominator,
                        ],
                    }
                )
            ).digest()[:8],
            "big",
        )

    def validate(self):
        roots = tuple(
            _sha(getattr(self, n), n)
            for n in (
                "support_estimability_authority_sha256",
                "target_panel_authority_sha256",
                "target_panel_sizing_receipt_sha256",
                "outer_split_authority_sha256",
            )
        )
        if len(set(roots)) != len(roots):
            raise ValueError("precision V4 roots must be role-distinct")
        if self.required_target_count not in (128, 256, 512, 1024):
            raise ValueError(
                "required_target_count must come from calibrated target-panel ladder"
            )
        for name in (
            "null_equivalence_margin_numerator",
            "null_equivalence_margin_denominator",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(
                    "null equivalence margin must be a positive exact rational"
                )
        margin = Fraction(
            self.null_equivalence_margin_numerator,
            self.null_equivalence_margin_denominator,
        )
        if margin >= 1:
            raise ValueError("null equivalence margin must be strictly below one")
        if self.uncertainty_method_id != METHOD_ID:
            raise ValueError("uncertainty_method_id mismatch")
        if self.source_population_frame_id != SOURCE_POPULATION_FRAME_ID:
            raise ValueError("source_population_frame_id mismatch")
        if self.source_aggregation_estimand_id != SOURCE_AGGREGATION_ESTIMAND_ID:
            raise ValueError("source_aggregation_estimand_id mismatch")
        if (self.confidence_level_numerator, self.confidence_level_denominator) != (
            95,
            100,
        ):
            raise ValueError("confidence level must remain 95/100")
        if self.bootstrap_replicates != 4096:
            raise ValueError("bootstrap_replicates must remain 4096")
        if self.min_donor_count != 104 or self.min_outer_fold_count != 4:
            raise ValueError("donor/fold minima must remain FULL104 values")
        if self.insufficient_support_policy_id != INSUFFICIENT_POLICY_ID:
            raise ValueError("insufficient_support_policy_id mismatch")
        if self.negative_control_precision_policy_id != NEGATIVE_CONTROL_PRECISION_POLICY_ID:
            raise ValueError("negative_control_precision_policy_id mismatch")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("precision authority must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("precision authority cannot authorize training")

    def bind_target_panel(self, panel: Any, sizing_receipt: Any):
        self.validate()
        panel.validate()
        sizing_receipt.validate()
        if panel.canonical_digest() != self.target_panel_authority_sha256:
            raise ValueError("target panel root mismatch")
        if sizing_receipt.canonical_digest() != self.target_panel_sizing_receipt_sha256:
            raise ValueError("sizing receipt root mismatch")
        if (
            panel.target_count != self.required_target_count
            or sizing_receipt.selected_target_count != self.required_target_count
        ):
            raise ValueError(
                "precision target count disagrees with calibrated panel"
            )

    def assert_sufficient(
        self, *, target_count: int, donor_count: int, outer_fold_count: int
    ):
        self.validate()
        if target_count < self.required_target_count:
            raise ValueError("target_count below calibrated precision requirement")
        if donor_count < 104:
            raise ValueError("donor_count below FULL104 precision requirement")
        if outer_fold_count < 4:
            raise ValueError("outer_fold_count below FULL104 precision requirement")

    def negative_control_precision_passed(self, interval: Any) -> bool:
        """Require the terminal negative-control 95% CI to be precise and null-like."""

        self.validate()
        interval.validate()
        margin = self.null_equivalence_margin
        lo = float(interval.lower_two_sided)
        hi = float(interval.upper_two_sided)
        return bool(
            lo <= 0.0 <= hi
            and lo >= -margin
            and hi <= margin
        )

    def assert_negative_control_precision(self, interval: Any) -> None:
        if not self.negative_control_precision_passed(interval):
            raise ValueError(
                "negative-control 95% interval must contain zero and fit wholly "
                "inside the frozen null-equivalence margin"
            )

    def interval(self, matrix, donor_source_code):
        self.validate()
        return paired_target_donor_bootstrap(
            matrix,
            donor_source_code,
            replicates=self.bootstrap_replicates,
            seed=self.bootstrap_seed,
            confidence_level=self.confidence_level,
        )

    def canonical_digest(self):
        self.validate()
        return _digest(
            {
                "schema": "V5_QUALIFICATION_PRECISION_AUTHORITY_V4",
                **asdict(self),
                "bootstrap_seed": self.bootstrap_seed,
                "null_equivalence_margin": self.null_equivalence_margin,
            }
        )
