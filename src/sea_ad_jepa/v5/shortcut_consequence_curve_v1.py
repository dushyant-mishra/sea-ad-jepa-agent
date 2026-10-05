"""Prospective shortcut-consequence curve for G5 margin justification.

This module does not choose epsilon_bio and does not freeze a terminal shortcut
margin. It characterizes how a bounded, pathology-blind state-fidelity
functional changes over a prospectively fixed residual-shortcut sweep.

A grid frontier is emitted only when:
- epsilon_bio comes from a separately hash-bound prospective authority; and
- mean harm is monotone nondecreasing across the declared residual grid.

The grid frontier remains a calibration result, not terminal masking authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Any

import numpy as np


@dataclass(frozen=True)
class BiologicalNegligibilityAuthorityV1:
    authority_id: str
    fidelity_functional_id: str
    epsilon_numerator: int
    epsilon_denominator: int
    scientific_rationale_id: str
    scientific_rationale_sha256: str
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    @property
    def epsilon(self) -> Fraction:
        return Fraction(self.epsilon_numerator, self.epsilon_denominator)

    def validate(self) -> None:
        for name in ("authority_id", "fidelity_functional_id", "scientific_rationale_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be nonempty")
        for name, value in (
            ("epsilon_numerator", self.epsilon_numerator),
            ("epsilon_denominator", self.epsilon_denominator),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
        if self.epsilon_numerator <= 0 or self.epsilon_denominator <= 0:
            raise ValueError("epsilon must be a positive exact fraction")
        if self.epsilon_numerator > self.epsilon_denominator:
            raise ValueError("epsilon cannot exceed the bounded fidelity range")
        sha = self.scientific_rationale_sha256
        if not isinstance(sha, str) or len(sha) != 64 or sha != sha.lower():
            raise ValueError("scientific_rationale_sha256 must be lowercase SHA-256")
        try:
            int(sha, 16)
        except ValueError as exc:
            raise ValueError("scientific_rationale_sha256 must be lowercase SHA-256") from exc
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("epsilon_bio must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("biological negligibility authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        payload = {
            "schema": "V5_BIOLOGICAL_NEGLIGIBILITY_AUTHORITY_V1",
            "authority_id": self.authority_id,
            "fidelity_functional_id": self.fidelity_functional_id,
            "epsilon": [self.epsilon.numerator, self.epsilon.denominator],
            "scientific_rationale_id": self.scientific_rationale_id,
            "scientific_rationale_sha256": self.scientific_rationale_sha256,
            "terminal_outcomes_inspected_before_freeze": False,
            "training_authorized": False,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True)
class ShortcutConsequenceCurveV1:
    residual_level: np.ndarray
    fidelity_by_level_unit: np.ndarray
    mean_fidelity: np.ndarray
    absolute_mean_change_from_zero: np.ndarray
    mean_absolute_paired_change_from_zero: np.ndarray
    harm_increment: np.ndarray
    monotone_non_decreasing_harm: bool

    def __post_init__(self) -> None:
        for name in (
            "residual_level",
            "mean_fidelity",
            "absolute_mean_change_from_zero",
            "mean_absolute_paired_change_from_zero",
            "harm_increment",
        ):
            arr = np.array(getattr(self, name), dtype=np.float64, copy=True)
            if arr.ndim != 1 or not np.all(np.isfinite(arr)):
                raise ValueError(f"{name} must be a finite vector")
            arr.flags.writeable = False
            object.__setattr__(self, name, arr)
        x = np.array(self.fidelity_by_level_unit, dtype=np.float64, copy=True)
        if x.ndim != 2 or x.shape[0] != self.residual_level.size or x.shape[1] < 1:
            raise ValueError("fidelity_by_level_unit must be level x paired-unit")
        if not np.all(np.isfinite(x)) or np.any((x < 0.0) | (x > 1.0)):
            raise ValueError("fidelity values must be finite and bounded in [0,1]")
        x.flags.writeable = False
        object.__setattr__(self, "fidelity_by_level_unit", x)


@dataclass(frozen=True)
class ConsequenceFrontierV1:
    state: str
    epsilon: float
    grid_frontier_residual: float | None
    first_exceeding_residual: float | None
    authority_sha256: str
    monotone_non_decreasing_harm: bool


def characterize_shortcut_consequence_curve(
    residual_level: Any,
    fidelity_by_level_unit: Any,
) -> ShortcutConsequenceCurveV1:
    r = np.asarray(residual_level, dtype=np.float64)
    s = np.asarray(fidelity_by_level_unit, dtype=np.float64)
    if r.ndim != 1 or r.size < 2 or not np.all(np.isfinite(r)):
        raise ValueError("residual_level must be a finite vector with >=2 levels")
    if r[0] != 0.0 or np.any(r < 0.0) or np.any(np.diff(r) <= 0.0):
        raise ValueError("residual levels must start at zero and be strictly increasing")
    if s.ndim != 2 or s.shape[0] != r.size or s.shape[1] < 1:
        raise ValueError("fidelity_by_level_unit must align residual levels and contain paired units")
    if not np.all(np.isfinite(s)) or np.any((s < 0.0) | (s > 1.0)):
        raise ValueError("fidelity must be finite and bounded in [0,1]")

    mean = s.mean(axis=1)
    mean_change = np.abs(mean - mean[0])
    paired_harm = np.mean(np.abs(s - s[0:1, :]), axis=1)
    increments = np.diff(paired_harm)
    monotone = bool(np.all(increments >= -1e-15))
    return ShortcutConsequenceCurveV1(
        residual_level=r,
        fidelity_by_level_unit=s,
        mean_fidelity=mean,
        absolute_mean_change_from_zero=mean_change,
        mean_absolute_paired_change_from_zero=paired_harm,
        harm_increment=increments,
        monotone_non_decreasing_harm=monotone,
    )


def evaluate_biological_negligibility_frontier(
    curve: ShortcutConsequenceCurveV1,
    authority: BiologicalNegligibilityAuthorityV1,
) -> ConsequenceFrontierV1:
    authority.validate()
    eps = float(authority.epsilon)

    if not curve.monotone_non_decreasing_harm:
        return ConsequenceFrontierV1(
            state="NONMONOTONE_CONSEQUENCE_CURVE__NO_MARGIN_FREEZE",
            epsilon=eps,
            grid_frontier_residual=None,
            first_exceeding_residual=None,
            authority_sha256=authority.canonical_digest(),
            monotone_non_decreasing_harm=False,
        )

    acceptable = curve.mean_absolute_paired_change_from_zero < eps
    # The zero-residual reference must necessarily be acceptable for epsilon>0.
    if not bool(acceptable[0]):
        raise AssertionError("zero-residual reference is not inside positive epsilon")
    bad = np.flatnonzero(~acceptable)
    if bad.size == 0:
        return ConsequenceFrontierV1(
            state="GRID_DOES_NOT_REACH_BIOLOGICAL_CONSEQUENCE_BOUNDARY",
            epsilon=eps,
            grid_frontier_residual=float(curve.residual_level[-1]),
            first_exceeding_residual=None,
            authority_sha256=authority.canonical_digest(),
            monotone_non_decreasing_harm=True,
        )

    first_bad = int(bad[0])
    frontier = float(curve.residual_level[first_bad - 1])
    return ConsequenceFrontierV1(
        state="GRID_FRONTIER_IDENTIFIED__NOT_TERMINAL_MARGIN_AUTHORITY",
        epsilon=eps,
        grid_frontier_residual=frontier,
        first_exceeding_residual=float(curve.residual_level[first_bad]),
        authority_sha256=authority.canonical_digest(),
        monotone_non_decreasing_harm=True,
    )
