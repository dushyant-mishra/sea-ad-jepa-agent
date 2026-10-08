"""Frozen FULL104 donor-and-target precision authority V3."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from .precision_authority_v2 import paired_target_donor_bootstrap

METHOD_ID = "PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE_BOOTSTRAP_V2"
INSUFFICIENT_POLICY_ID = "FAIL_CLOSED_IF_BELOW_PRECISION_V2"
CONFIDENCE_NUMERATOR = 95
CONFIDENCE_DENOMINATOR = 100
BOOTSTRAP_REPLICATES = 4096
MIN_TARGET_COUNT = 128
MIN_DONOR_COUNT = 104
MIN_OUTER_FOLD_COUNT = 4
SEED_NAMESPACE = "V5_FULL104_PRECISION_ROOT_DERIVED_V3"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


@dataclass(frozen=True)
class QualificationPrecisionAuthorityV3:
    authority_id: str
    support_estimability_authority_sha256: str
    target_panel_authority_sha256: str
    outer_split_authority_sha256: str
    uncertainty_method_id: str = METHOD_ID
    confidence_level_numerator: int = CONFIDENCE_NUMERATOR
    confidence_level_denominator: int = CONFIDENCE_DENOMINATOR
    bootstrap_replicates: int = BOOTSTRAP_REPLICATES
    min_target_count: int = MIN_TARGET_COUNT
    min_donor_count: int = MIN_DONOR_COUNT
    min_outer_fold_count: int = MIN_OUTER_FOLD_COUNT
    insufficient_support_policy_id: str = INSUFFICIENT_POLICY_ID
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    @property
    def confidence_level(self) -> float:
        self.validate()
        return self.confidence_level_numerator / self.confidence_level_denominator

    @property
    def bootstrap_seed(self) -> int:
        self.validate()
        payload = {
            "schema": "V5_FULL104_PRECISION_ROOT_DERIVED_SEED_V3",
            "namespace": SEED_NAMESPACE,
            "support_estimability_authority_sha256": self.support_estimability_authority_sha256,
            "target_panel_authority_sha256": self.target_panel_authority_sha256,
            "outer_split_authority_sha256": self.outer_split_authority_sha256,
        }
        return int.from_bytes(hashlib.sha256(_canonical(payload)).digest()[:8], "big")

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = (
            _sha(self.support_estimability_authority_sha256, "support_estimability_authority_sha256"),
            _sha(self.target_panel_authority_sha256, "target_panel_authority_sha256"),
            _sha(self.outer_split_authority_sha256, "outer_split_authority_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("precision roots must be role-distinct")
        if self.uncertainty_method_id != METHOD_ID:
            raise ValueError("uncertainty_method_id mismatch")
        if (self.confidence_level_numerator, self.confidence_level_denominator) != (
            CONFIDENCE_NUMERATOR, CONFIDENCE_DENOMINATOR
        ):
            raise ValueError("confidence level must remain 95/100")
        if self.bootstrap_replicates != BOOTSTRAP_REPLICATES:
            raise ValueError("bootstrap_replicates must remain 4096")
        if self.min_target_count != MIN_TARGET_COUNT:
            raise ValueError("min_target_count must remain 128")
        if self.min_donor_count != MIN_DONOR_COUNT:
            raise ValueError("min_donor_count must remain 104")
        if self.min_outer_fold_count != MIN_OUTER_FOLD_COUNT:
            raise ValueError("min_outer_fold_count must remain 4")
        if self.insufficient_support_policy_id != INSUFFICIENT_POLICY_ID:
            raise ValueError("insufficient_support_policy_id mismatch")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("precision authority must freeze before terminal outcomes")
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

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_QUALIFICATION_PRECISION_AUTHORITY_V3", **asdict(self), "bootstrap_seed": self.bootstrap_seed})
