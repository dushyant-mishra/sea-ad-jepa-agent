"""Outcome-blind FULL104 control-calibration precision plan V2.

V2 repairs a role-identity defect in V1: the calibration path consumed the raw
fold-assignment receipt digest but stored it in a field named
outer_split_authority_sha256. V2 names that role correctly and also binds the
authenticated calibration-cache manifest used to produce the control matrices.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from .precision_authority_v2 import paired_target_donor_bootstrap

METHOD_ID = "PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE_BOOTSTRAP_V2"
CONFIDENCE_NUMERATOR = 95
CONFIDENCE_DENOMINATOR = 100
BOOTSTRAP_REPLICATES = 4096
DONOR_COUNT = 104
SEED_NAMESPACE = "V5_FULL104_CONTROL_CALIBRATION_PRECISION_V2"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


@dataclass(frozen=True)
class ControlCalibrationPrecisionPlanV2:
    authority_id: str
    census_authority_sha256: str
    support_estimability_authority_sha256: str
    target_eligibility_receipt_sha256: str
    fold_assignment_artifact_sha256: str
    calibration_cache_manifest_sha256: str
    uncertainty_method_id: str = METHOD_ID
    confidence_level_numerator: int = CONFIDENCE_NUMERATOR
    confidence_level_denominator: int = CONFIDENCE_DENOMINATOR
    bootstrap_replicates: int = BOOTSTRAP_REPLICATES
    donor_count: int = DONOR_COUNT
    terminal_policy_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        roots = tuple(
            _sha(getattr(self, name), name)
            for name in (
                "census_authority_sha256",
                "support_estimability_authority_sha256",
                "target_eligibility_receipt_sha256",
                "fold_assignment_artifact_sha256",
                "calibration_cache_manifest_sha256",
            )
        )
        if len(set(roots)) != 5:
            raise ValueError("control-calibration precision V2 roots must be role-distinct")
        if self.uncertainty_method_id != METHOD_ID:
            raise ValueError("uncertainty_method_id mismatch")
        if (self.confidence_level_numerator, self.confidence_level_denominator) != (95, 100):
            raise ValueError("confidence level must remain 95/100")
        if self.bootstrap_replicates != 4096:
            raise ValueError("bootstrap_replicates must remain 4096")
        if self.donor_count != 104:
            raise ValueError("donor_count must remain FULL104 value 104")
        if self.terminal_policy_outcomes_inspected_before_freeze is not False:
            raise ValueError("control-calibration precision must freeze before terminal policy outcomes")
        if self.training_authorized is not False:
            raise ValueError("control-calibration precision cannot authorize training")

    def bind_calibration_cache(self, cache_manifest: Any) -> None:
        self.validate()
        cache_manifest.validate()
        if cache_manifest.canonical_digest() != self.calibration_cache_manifest_sha256:
            raise ValueError("control-calibration precision binds a different cache manifest")
        if getattr(cache_manifest, "terminal_masking_qualification_authorized", None) is not False:
            raise ValueError("control-calibration cache unexpectedly authorizes terminal masking")
        expected = {
            "census_authority_sha256": self.census_authority_sha256,
            "support_estimability_authority_sha256": self.support_estimability_authority_sha256,
            "target_eligibility_receipt_sha256": self.target_eligibility_receipt_sha256,
            "split_receipt_sha256": self.fold_assignment_artifact_sha256,
        }
        for field, value in expected.items():
            if getattr(cache_manifest, field, None) != value:
                raise ValueError(f"control-calibration cache disagrees with precision plan role {field}")

    @property
    def confidence_level(self) -> float:
        self.validate()
        return self.confidence_level_numerator / self.confidence_level_denominator

    def bootstrap_seed(self, target_count: int) -> int:
        self.validate()
        if target_count not in (128, 256, 512, 1024):
            raise ValueError("target_count must be a frozen panel-calibration rung")
        payload = {
            "schema": "V5_CONTROL_CALIBRATION_BOOTSTRAP_SEED_V2",
            "namespace": SEED_NAMESPACE,
            "authority_sha256": self.canonical_digest(),
            "target_count": target_count,
        }
        return int.from_bytes(hashlib.sha256(_canonical(payload)).digest()[:8], "big")

    def interval(self, matrix, donor_source_code, *, target_count: int):
        self.validate()
        import numpy as np

        arr = np.asarray(matrix)
        if arr.ndim != 2 or arr.shape[0] != target_count:
            raise ValueError("control-calibration matrix target dimension must equal target_count")
        if arr.shape[1] != self.donor_count:
            raise ValueError("control-calibration matrix donor dimension must equal 104")
        return paired_target_donor_bootstrap(
            arr,
            donor_source_code,
            replicates=self.bootstrap_replicates,
            seed=self.bootstrap_seed(target_count),
            confidence_level=self.confidence_level,
        )

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_CONTROL_CALIBRATION_PRECISION_PLAN_V2", **asdict(self)})
