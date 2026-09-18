"""Paired target-and-donor uncertainty for FULL104 masking qualification."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

import numpy as np

METHOD_ID = "PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE_BOOTSTRAP_V2"
INSUFFICIENT_POLICY_ID = "FAIL_CLOSED_IF_BELOW_PRECISION_V2"


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
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class QualificationPrecisionAuthorityV2:
    authority_id: str
    support_estimability_authority_sha256: str
    target_panel_authority_sha256: str
    outer_split_authority_sha256: str
    uncertainty_method_id: str
    confidence_level_numerator: int
    confidence_level_denominator: int
    bootstrap_replicates: int
    bootstrap_seed: int
    min_target_count: int
    min_donor_count: int
    min_outer_fold_count: int
    insufficient_support_policy_id: str
    terminal_outcomes_inspected: bool = False
    training_authorized: bool = False

    @property
    def confidence_level(self) -> float:
        self.validate()
        return self.confidence_level_numerator / self.confidence_level_denominator

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = (
            _sha(self.support_estimability_authority_sha256, "support_estimability_authority_sha256"),
            _sha(self.target_panel_authority_sha256, "target_panel_authority_sha256"),
            _sha(self.outer_split_authority_sha256, "outer_split_authority_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("precision authority role roots must be distinct")
        if self.uncertainty_method_id != METHOD_ID:
            raise ValueError("uncertainty_method_id mismatch")
        if self.insufficient_support_policy_id != INSUFFICIENT_POLICY_ID:
            raise ValueError("insufficient_support_policy_id mismatch")
        if (
            isinstance(self.confidence_level_numerator, bool)
            or isinstance(self.confidence_level_denominator, bool)
            or not isinstance(self.confidence_level_numerator, int)
            or not isinstance(self.confidence_level_denominator, int)
            or self.confidence_level_denominator <= 0
            or not 0 < self.confidence_level_numerator < self.confidence_level_denominator
        ):
            raise ValueError("confidence level must be an exact rational strictly between zero and one")
        for name in ("bootstrap_replicates", "min_target_count", "min_donor_count", "min_outer_fold_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if isinstance(self.bootstrap_seed, bool) or not isinstance(self.bootstrap_seed, int) or self.bootstrap_seed < 0:
            raise ValueError("bootstrap_seed must be a nonnegative integer")
        if self.terminal_outcomes_inspected is not False:
            raise ValueError("precision parameters must be frozen before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("precision authority cannot authorize training")

    def assert_sufficient(self, *, target_count: int, donor_count: int, outer_fold_count: int) -> None:
        self.validate()
        observed = {
            "target_count": target_count,
            "donor_count": donor_count,
            "outer_fold_count": outer_fold_count,
        }
        required = {
            "target_count": self.min_target_count,
            "donor_count": self.min_donor_count,
            "outer_fold_count": self.min_outer_fold_count,
        }
        for name, value in observed.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < required[name]:
                raise ValueError(f"{name} is below the frozen precision requirement")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_QUALIFICATION_PRECISION_AUTHORITY_V2", **asdict(self)})


@dataclass(frozen=True)
class BootstrapIntervalV2:
    mean: float
    lower_two_sided: float
    upper_two_sided: float
    lower_one_sided: float
    upper_one_sided: float
    confidence_level: float
    bootstrap_replicates: int
    bootstrap_seed: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def source_balanced_mean(matrix: np.ndarray, donor_source_code: np.ndarray) -> float:
    values = np.asarray(matrix, dtype=np.float64)
    source = np.asarray(donor_source_code)
    if values.ndim != 2 or source.ndim != 1 or values.shape[1] != source.size:
        raise ValueError("matrix must be target x donor and align with donor_source_code")
    if values.shape[0] == 0 or source.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("precision matrix must be nonempty and finite")
    source_means = []
    for code in sorted(set(map(int, source))):
        donor_ix = np.flatnonzero(source == code)
        if donor_ix.size == 0:
            raise ValueError("empty source stratum")
        source_means.append(float(values[:, donor_ix].mean()))
    return float(np.mean(source_means))


def paired_target_donor_bootstrap(
    matrix: np.ndarray,
    donor_source_code: np.ndarray,
    *,
    replicates: int,
    seed: int,
    confidence_level: float,
) -> BootstrapIntervalV2:
    """Bootstrap paired target x donor evidence, resampling donors within source."""

    values = np.asarray(matrix, dtype=np.float64)
    source = np.asarray(donor_source_code)
    if values.ndim != 2 or source.ndim != 1 or values.shape[1] != source.size:
        raise ValueError("matrix must be target x donor and align with donor_source_code")
    if values.shape[0] < 1 or source.size < 1 or not np.all(np.isfinite(values)):
        raise ValueError("bootstrap matrix must be nonempty and finite")
    if isinstance(replicates, bool) or not isinstance(replicates, int) or replicates < 1:
        raise ValueError("replicates must be positive")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be nonnegative")
    if not 0.0 < float(confidence_level) < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")

    source_groups = [np.flatnonzero(source == code) for code in sorted(set(map(int, source)))]
    if any(group.size == 0 for group in source_groups):
        raise ValueError("every source needs at least one donor")
    rng = np.random.default_rng(seed)
    n_targets = values.shape[0]
    boot = np.empty(replicates, dtype=np.float64)
    for b in range(replicates):
        target_ix = rng.integers(0, n_targets, size=n_targets)
        source_means = []
        for donors in source_groups:
            sampled_donors = donors[rng.integers(0, donors.size, size=donors.size)]
            source_means.append(float(values[np.ix_(target_ix, sampled_donors)].mean()))
        boot[b] = float(np.mean(source_means))

    alpha = 1.0 - float(confidence_level)
    lower_two, upper_two = np.quantile(boot, [alpha / 2.0, 1.0 - alpha / 2.0])
    lower_one = float(np.quantile(boot, alpha))
    upper_one = float(np.quantile(boot, 1.0 - alpha))
    return BootstrapIntervalV2(
        mean=source_balanced_mean(values, source),
        lower_two_sided=float(lower_two),
        upper_two_sided=float(upper_two),
        lower_one_sided=lower_one,
        upper_one_sided=upper_one,
        confidence_level=float(confidence_level),
        bootstrap_replicates=replicates,
        bootstrap_seed=seed,
    )
