"""Prospective terminal evidence assembly for current FULL104 masking qualification.

This module freezes how raw target-by-donor evidence maps into the already-frozen
V2 mechanical masking decision. It is deliberately outcome-agnostic: callers
supply matrices; this module defines only paired estimands and uncertainty.

Historical/smaller-run aggregation formulas are not authority here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import numpy as np

from .masking_qualification_decision_v1 import (
    IntervalEvidenceV1,
    MaskingPolicyDecisionEvidenceV1,
)
from .masking_qualification_decision_v2 import DECISION_RULE_ID

PRIMARY_DELTA_ESTIMAND_ID = "UNIFORM_MINUS_POLICY_PAIRED_TARGET_DONOR_V1"
PRIMARY_NULL_ESTIMAND_ID = "REAL_POLICY_MINUS_SAME_MASK_WITHIN_DONOR_SHUFFLED_TARGET_V1"
SOURCE_GUARDRAIL_ID = "SAME_PRIMARY_NULL_ESTIMAND_WITHIN_SOURCE_V1"
NEGATIVE_CONTROL_ESTIMAND_ID = "SHUFFLED_UNIFORM_MINUS_SHUFFLED_TARGETED_RIDGE_PAIRED_TARGET_DONOR_V1"
PLANTED_DETECT_ESTIMAND_ID = "PLANTED_PROXY_MINUS_SAME_VISIBLE_MASK_SHUFFLED_PROXY_V1"
PLANTED_AFTER_ESTIMAND_ID = "PLANTED_PROXY_AFTER_TARGETED_MASK_MINUS_SAME_MASK_SHUFFLED_PROXY_V1"
NONLINEAR_NULL_ESTIMAND_ID = "REAL_NONLINEAR_MINUS_SAME_MASK_WITHIN_DONOR_SHUFFLED_TARGET_V1"
TARGET_HETEROGENEITY_ID = "SOURCE_BALANCED_DONOR_MEAN_DELTA_PER_TARGET_V1"
TARGETING_COMPLEXITY_ID = "MEAN_EFFECTIVE_TARGETED_COUNT_OVER_TARGET_X_OUTER_FOLD_V1"
INTERVAL_METHOD_ID = "QUALIFICATION_PRECISION_AUTHORITY_V4_PAIRED_TARGET_DONOR_BOOTSTRAP_V1"


@dataclass(frozen=True)
class TerminalEvidenceAssemblySemanticsV1:
    authority_id: str = "JEPA_V5_FULL104_TERMINAL_EVIDENCE_ASSEMBLY_SEMANTICS_V1"
    decision_rule_id: str = DECISION_RULE_ID
    primary_delta_estimand_id: str = PRIMARY_DELTA_ESTIMAND_ID
    primary_null_estimand_id: str = PRIMARY_NULL_ESTIMAND_ID
    source_guardrail_id: str = SOURCE_GUARDRAIL_ID
    negative_control_estimand_id: str = NEGATIVE_CONTROL_ESTIMAND_ID
    planted_detect_estimand_id: str = PLANTED_DETECT_ESTIMAND_ID
    planted_after_estimand_id: str = PLANTED_AFTER_ESTIMAND_ID
    nonlinear_null_estimand_id: str = NONLINEAR_NULL_ESTIMAND_ID
    target_heterogeneity_id: str = TARGET_HETEROGENEITY_ID
    targeting_complexity_id: str = TARGETING_COMPLEXITY_ID
    interval_method_id: str = INTERVAL_METHOD_ID
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        expected = (
            self.decision_rule_id == DECISION_RULE_ID
            and self.primary_delta_estimand_id == PRIMARY_DELTA_ESTIMAND_ID
            and self.primary_null_estimand_id == PRIMARY_NULL_ESTIMAND_ID
            and self.source_guardrail_id == SOURCE_GUARDRAIL_ID
            and self.negative_control_estimand_id == NEGATIVE_CONTROL_ESTIMAND_ID
            and self.planted_detect_estimand_id == PLANTED_DETECT_ESTIMAND_ID
            and self.planted_after_estimand_id == PLANTED_AFTER_ESTIMAND_ID
            and self.nonlinear_null_estimand_id == NONLINEAR_NULL_ESTIMAND_ID
            and self.target_heterogeneity_id == TARGET_HETEROGENEITY_ID
            and self.targeting_complexity_id == TARGETING_COMPLEXITY_ID
            and self.interval_method_id == INTERVAL_METHOD_ID
        )
        if not expected:
            raise ValueError("terminal evidence assembly semantics drifted")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("terminal evidence mapping must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("terminal evidence assembly cannot authorize training")


def _matrix(value: Any, name: str) -> np.ndarray:
    out = np.asarray(value, dtype=np.float64)
    if out.ndim != 2 or out.shape[0] < 1 or out.shape[1] < 1:
        raise ValueError(f"{name} must be a nonempty target x donor matrix")
    if not np.all(np.isfinite(out)):
        raise ValueError(f"{name} must be finite")
    return out


def _aligned(reference: np.ndarray, value: Any, name: str) -> np.ndarray:
    out = _matrix(value, name)
    if out.shape != reference.shape:
        raise ValueError(f"{name} must align target x donor with primary evidence")
    return out


def _required_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a mechanically computed boolean")
    return value


def _interval(precision: Any, matrix: np.ndarray, donor_source_code: np.ndarray) -> IntervalEvidenceV1:
    observed = precision.interval(matrix, donor_source_code)
    return IntervalEvidenceV1(
        mean=float(observed.mean),
        lower_two_sided=float(observed.lower_two_sided),
        upper_two_sided=float(observed.upper_two_sided),
        lower_one_sided=float(observed.lower_one_sided),
        upper_one_sided=float(observed.upper_one_sided),
    )


def _source_upper_bounds(
    precision: Any,
    matrix: np.ndarray,
    donor_source_code: np.ndarray,
    source_names: Mapping[int, str],
) -> dict[str, float]:
    source = np.asarray(donor_source_code, dtype=np.int64)
    if source.ndim != 1 or source.size != matrix.shape[1]:
        raise ValueError("donor_source_code must align with donor columns")
    codes = sorted(set(map(int, source)))
    normalized_names = {int(k): str(v) for k, v in source_names.items()}
    if set(codes) != set(normalized_names):
        raise ValueError("source_names must exactly cover donor source codes")
    out: dict[str, float] = {}
    for code in codes:
        ix = np.flatnonzero(source == code)
        if ix.size == 0:
            raise ValueError("empty source stratum")
        local_source = np.zeros(ix.size, dtype=np.int64)
        interval = precision.interval(matrix[:, ix], local_source)
        name = normalized_names[code]
        if not name or name in out:
            raise ValueError("source names must be unique and nonempty")
        out[name] = float(interval.upper_one_sided)
    return out


def _source_balanced_target_means(matrix: np.ndarray, donor_source_code: np.ndarray) -> np.ndarray:
    source = np.asarray(donor_source_code, dtype=np.int64)
    if source.ndim != 1 or source.size != matrix.shape[1]:
        raise ValueError("donor_source_code must align with donor columns")
    codes = sorted(set(map(int, source)))
    if not codes:
        raise ValueError("at least one source stratum is required")
    per_source = []
    for code in codes:
        ix = np.flatnonzero(source == code)
        if ix.size == 0:
            raise ValueError("empty source stratum")
        per_source.append(matrix[:, ix].mean(axis=1))
    return np.mean(np.vstack(per_source), axis=0)


def assemble_policy_decision_evidence(
    *,
    policy_id: str,
    burden_numerator: int,
    burden_denominator: int,
    actual_policy_scores: Any,
    actual_uniform_scores: Any,
    shuffled_same_mask_scores: Any,
    negative_control_delta: Any,
    planted_detect_excess: Any,
    planted_after_mask_excess: Any,
    nonlinear_actual_scores: Any,
    nonlinear_shuffled_same_mask_scores: Any,
    effective_targeted_n_by_target_fold: Any,
    donor_source_code: Any,
    source_names: Mapping[int, str],
    precision: Any,
    raw_primary_evidence_sha256: str,
    raw_control_evidence_sha256: str,
    raw_nonlinear_evidence_sha256: str,
    replay_exact: bool,
    untreated_identity_exact: bool,
    no_privileged_metadata: bool,
) -> MaskingPolicyDecisionEvidenceV1:
    """Assemble one policy's decision evidence from frozen paired matrices.

    Score matrices are target x donor; each donor contributes only its held-out
    outer-fold score. Shuffled matrices use a deterministic within-donor
    permutation of the same target (or planted virtual target) under the identical
    already-selected mask. No policy may borrow another policy's shuffled null.

    Targeting complexity is target x outer-fold, not donor-weighted.
    """

    TerminalEvidenceAssemblySemanticsV1().validate()
    precision.validate()

    actual = _matrix(actual_policy_scores, "actual_policy_scores")
    uniform = _aligned(actual, actual_uniform_scores, "actual_uniform_scores")
    shuffled = _aligned(actual, shuffled_same_mask_scores, "shuffled_same_mask_scores")
    neg = _aligned(actual, negative_control_delta, "negative_control_delta")
    plant_detect = _aligned(actual, planted_detect_excess, "planted_detect_excess")
    plant_after = _aligned(actual, planted_after_mask_excess, "planted_after_mask_excess")
    nl_actual = _aligned(actual, nonlinear_actual_scores, "nonlinear_actual_scores")
    nl_shuffled = _aligned(actual, nonlinear_shuffled_same_mask_scores, "nonlinear_shuffled_same_mask_scores")

    donor_source = np.asarray(donor_source_code, dtype=np.int64)
    if donor_source.ndim != 1 or donor_source.size != actual.shape[1]:
        raise ValueError("donor_source_code must align with donor columns")

    precision.assert_sufficient(
        target_count=int(actual.shape[0]),
        donor_count=int(actual.shape[1]),
        outer_fold_count=4,
    )

    effective = np.asarray(effective_targeted_n_by_target_fold, dtype=np.float64)
    if effective.shape != (actual.shape[0], 4):
        raise ValueError("effective_targeted_n_by_target_fold must be target x four outer folds")
    if np.any(~np.isfinite(effective)) or np.any(effective < 0):
        raise ValueError("effective targeting counts must be finite and nonnegative")

    replay_ok = _required_bool(replay_exact, "replay_exact")
    identity_ok = _required_bool(untreated_identity_exact, "untreated_identity_exact")
    metadata_ok = _required_bool(no_privileged_metadata, "no_privileged_metadata")

    delta = uniform - actual
    residual = actual - shuffled
    nonlinear_residual = nl_actual - nl_shuffled
    target_delta = _source_balanced_target_means(delta, donor_source)

    evidence = MaskingPolicyDecisionEvidenceV1(
        policy_id=policy_id,
        burden_numerator=int(burden_numerator),
        burden_denominator=int(burden_denominator),
        raw_primary_evidence_sha256=raw_primary_evidence_sha256,
        raw_control_evidence_sha256=raw_control_evidence_sha256,
        raw_nonlinear_evidence_sha256=raw_nonlinear_evidence_sha256,
        precision_authority_sha256=precision.canonical_digest(),
        delta_vs_uniform=_interval(precision, delta, donor_source),
        excess_over_shuffled_null=_interval(precision, residual, donor_source),
        source_excess_upper_one_sided=_source_upper_bounds(
            precision, residual, donor_source, source_names
        ),
        target_delta_median=float(np.median(target_delta)),
        worst_target_delta=float(np.min(target_delta)),
        mean_effective_targeted_n=float(np.mean(effective)),
        negative_control_delta=_interval(precision, neg, donor_source),
        planted_detect_excess=_interval(precision, plant_detect, donor_source),
        planted_after_mask_excess=_interval(precision, plant_after, donor_source),
        nonlinear_excess_over_shuffled_null=_interval(
            precision, nonlinear_residual, donor_source
        ),
        replay_exact=replay_ok,
        untreated_identity_exact=identity_ok,
        no_privileged_metadata=metadata_ok,
        precision_requirements_met=True,
        terminal_outcomes_inspected_before_freeze=False,
    )
    evidence.validate()
    return evidence
