"""Prospective terminal evidence assembly for current FULL104 masking qualification.

This module freezes how one policy arm's raw target-by-donor terminal evidence maps
into the V2 mechanical masking decision. Raw evidence is normalized into an
immutable bundle whose cryptographic roots are computed from the actual arrays and
their target/donor/source/fold identities. Callers cannot supply unrelated raw
SHA-256 strings.

Historical/smaller-run aggregation formulas are not authority here.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from .masking_qualification_decision_v1 import (
    IntervalEvidenceV1,
    MaskingPolicyDecisionEvidenceV1,
    POLICIES,
)
from .masking_qualification_decision_v2 import DECISION_RULE_ID
from .precision_authority_v4 import QualificationPrecisionAuthorityV4

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
RAW_EVIDENCE_SCHEMA_ID = "V5_FULL104_TERMINAL_POLICY_RAW_EVIDENCE_V1"


def _json_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _immutable_matrix(value: Any, name: str, *, dtype: str = "<f8") -> np.ndarray:
    out = np.array(value, dtype=np.dtype(dtype), order="C", copy=True)
    if out.ndim != 2 or out.shape[0] < 1 or out.shape[1] < 1:
        raise ValueError(f"{name} must be a nonempty matrix")
    if np.issubdtype(out.dtype, np.floating) and not np.all(np.isfinite(out)):
        raise ValueError(f"{name} must be finite")
    out.flags.writeable = False
    return out


def _immutable_vector(value: Any, name: str, *, dtype: str = "<i8") -> np.ndarray:
    out = np.array(value, dtype=np.dtype(dtype), order="C", copy=True)
    if out.ndim != 1 or out.size < 1:
        raise ValueError(f"{name} must be a nonempty vector")
    out.flags.writeable = False
    return out


def _array_digest(role: str, value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    header = json.dumps(
        {"role": role, "dtype": array.dtype.str, "shape": list(array.shape)},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    h = hashlib.sha256()
    h.update(header)
    h.update(b"\0")
    h.update(array.tobytes(order="C"))
    return h.hexdigest()


def _string_sequence(value: Sequence[Any], name: str, expected: int) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be a sequence, not one string")
    out = tuple(str(item) for item in value)
    if len(out) != expected:
        raise ValueError(f"{name} must align with its evidence axis")
    if any(not item for item in out):
        raise ValueError(f"{name} entries must be nonempty")
    if len(set(out)) != len(out):
        raise ValueError(f"{name} entries must be unique")
    return out


def _sequence_digest(role: str, value: Sequence[str]) -> str:
    return _json_digest({"role": role, "values": list(value)})


def _sha256_value(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _sha256_grid(
    value: Sequence[Sequence[Any]],
    name: str,
    *,
    rows: int,
    cols: int = 4,
) -> tuple[tuple[str, ...], ...]:
    if isinstance(value, (str, bytes)) or len(value) != rows:
        raise ValueError(f"{name} must contain one row per target")
    out = []
    for i, row in enumerate(value):
        if isinstance(row, (str, bytes)) or len(row) != cols:
            raise ValueError(f"{name}[{i}] must contain exactly {cols} fold roots")
        out.append(
            tuple(_sha256_value(item, f"{name}[{i}]") for item in row)
        )
    return tuple(out)


def _sha256_grid_digest(role: str, value: Sequence[Sequence[str]]) -> str:
    return _json_digest({"role": role, "values": [list(row) for row in value]})


def _required_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a mechanically computed boolean")
    return value


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
    raw_evidence_schema_id: str = RAW_EVIDENCE_SCHEMA_ID
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
            and self.raw_evidence_schema_id == RAW_EVIDENCE_SCHEMA_ID
        )
        if not expected:
            raise ValueError("terminal evidence assembly semantics drifted")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("terminal evidence mapping must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("terminal evidence assembly cannot authorize training")


@dataclass(frozen=True)
class TerminalPolicyRawEvidenceV1:
    """Immutable one-policy raw evidence with roots derived from the evidence itself."""

    policy_id: str
    burden_numerator: int
    burden_denominator: int
    target_ids: Sequence[Any]
    donor_ids: Sequence[Any]
    donor_source_code: Any
    donor_outer_fold: Any
    source_names: Mapping[int, str]
    policy_mask_sha256_by_target_fold: Sequence[Sequence[Any]]
    mechanical_control_receipt_sha256: str
    actual_policy_scores: Any
    actual_uniform_scores: Any
    shuffled_same_mask_scores: Any
    negative_control_delta: Any
    planted_detect_excess: Any
    planted_after_mask_excess: Any
    nonlinear_actual_scores: Any
    nonlinear_shuffled_same_mask_scores: Any
    effective_targeted_n_by_target_fold: Any
    replay_exact: bool
    untreated_identity_exact: bool
    no_privileged_metadata: bool

    def __post_init__(self) -> None:
        for name in (
            "actual_policy_scores",
            "actual_uniform_scores",
            "shuffled_same_mask_scores",
            "negative_control_delta",
            "planted_detect_excess",
            "planted_after_mask_excess",
            "nonlinear_actual_scores",
            "nonlinear_shuffled_same_mask_scores",
            "effective_targeted_n_by_target_fold",
        ):
            object.__setattr__(self, name, _immutable_matrix(getattr(self, name), name))
        object.__setattr__(
            self,
            "donor_source_code",
            _immutable_vector(self.donor_source_code, "donor_source_code"),
        )
        object.__setattr__(
            self,
            "donor_outer_fold",
            _immutable_vector(self.donor_outer_fold, "donor_outer_fold"),
        )
        actual = self.actual_policy_scores
        object.__setattr__(
            self,
            "target_ids",
            _string_sequence(self.target_ids, "target_ids", actual.shape[0]),
        )
        object.__setattr__(
            self,
            "donor_ids",
            _string_sequence(self.donor_ids, "donor_ids", actual.shape[1]),
        )
        normalized_names = {int(k): str(v) for k, v in self.source_names.items()}
        object.__setattr__(self, "source_names", MappingProxyType(normalized_names))
        object.__setattr__(
            self,
            "policy_mask_sha256_by_target_fold",
            _sha256_grid(
                self.policy_mask_sha256_by_target_fold,
                "policy_mask_sha256_by_target_fold",
                rows=actual.shape[0],
            ),
        )
        self.validate()

    def validate(self) -> None:
        if self.policy_id not in POLICIES:
            raise ValueError("policy_id is not an approved masking arm")
        _sha256_value(
            self.mechanical_control_receipt_sha256,
            "mechanical_control_receipt_sha256",
        )
        if (
            isinstance(self.burden_numerator, bool)
            or isinstance(self.burden_denominator, bool)
            or not isinstance(self.burden_numerator, int)
            or not isinstance(self.burden_denominator, int)
        ):
            raise ValueError("burden numerator/denominator must be integers")
        burden = Fraction(self.burden_numerator, self.burden_denominator)
        if not 0 < burden < 1:
            raise ValueError("burden must be an exact positive fraction below one")

        actual = self.actual_policy_scores
        expected = actual.shape
        if expected[1] != 104:
            raise ValueError("terminal FULL104 evidence must contain exactly 104 donors")
        for name in (
            "actual_uniform_scores",
            "shuffled_same_mask_scores",
            "negative_control_delta",
            "planted_detect_excess",
            "planted_after_mask_excess",
            "nonlinear_actual_scores",
            "nonlinear_shuffled_same_mask_scores",
        ):
            if getattr(self, name).shape != expected:
                raise ValueError(f"{name} must align target x donor with primary evidence")
        if self.effective_targeted_n_by_target_fold.shape != (expected[0], 4):
            raise ValueError(
                "effective_targeted_n_by_target_fold must be target x four outer folds"
            )
        if np.any(self.effective_targeted_n_by_target_fold < 0):
            raise ValueError("effective targeting counts must be nonnegative")
        if self.donor_source_code.size != expected[1]:
            raise ValueError("donor_source_code must align with donor columns")
        if self.donor_outer_fold.size != expected[1]:
            raise ValueError("donor_outer_fold must align with donor columns")
        if set(map(int, self.donor_outer_fold)) != {0, 1, 2, 3}:
            raise ValueError("terminal donor_outer_fold must contain all four outer folds")
        source_codes = set(map(int, self.donor_source_code))
        if source_codes != set(self.source_names):
            raise ValueError("source_names must exactly cover donor source codes")
        if any(not value for value in self.source_names.values()):
            raise ValueError("source names must be nonempty")
        if len(set(self.source_names.values())) != len(self.source_names):
            raise ValueError("source names must be unique")
        _required_bool(self.replay_exact, "replay_exact")
        _required_bool(self.untreated_identity_exact, "untreated_identity_exact")
        _required_bool(self.no_privileged_metadata, "no_privileged_metadata")

    def _axis_roots(self) -> dict[str, str]:
        return {
            "target_ids": _sequence_digest("target_ids", self.target_ids),
            "donor_ids": _sequence_digest("donor_ids", self.donor_ids),
            "donor_source_code": _array_digest("donor_source_code", self.donor_source_code),
            "donor_outer_fold": _array_digest("donor_outer_fold", self.donor_outer_fold),
            "source_names": _json_digest(
                {
                    "role": "source_names",
                    "values": [
                        [int(k), self.source_names[k]]
                        for k in sorted(self.source_names)
                    ],
                }
            ),
        }

    def primary_evidence_digest(self) -> str:
        self.validate()
        return _json_digest(
            {
                "schema": RAW_EVIDENCE_SCHEMA_ID + "__PRIMARY",
                "policy_id": self.policy_id,
                "mechanical_control_receipt_sha256": self.mechanical_control_receipt_sha256,
                "burden": [self.burden_numerator, self.burden_denominator],
                "axes": self._axis_roots(),
                "policy_mask_sha256_by_target_fold": _sha256_grid_digest(
                    "policy_mask_sha256_by_target_fold",
                    self.policy_mask_sha256_by_target_fold,
                ),
                "actual_policy_scores": _array_digest(
                    "actual_policy_scores", self.actual_policy_scores
                ),
                "actual_uniform_scores": _array_digest(
                    "actual_uniform_scores", self.actual_uniform_scores
                ),
                "shuffled_same_mask_scores": _array_digest(
                    "shuffled_same_mask_scores", self.shuffled_same_mask_scores
                ),
                "effective_targeted_n_by_target_fold": _array_digest(
                    "effective_targeted_n_by_target_fold",
                    self.effective_targeted_n_by_target_fold,
                ),
                "replay_exact": self.replay_exact,
                "untreated_identity_exact": self.untreated_identity_exact,
                "no_privileged_metadata": self.no_privileged_metadata,
            }
        )

    def control_evidence_digest(self) -> str:
        self.validate()
        return _json_digest(
            {
                "schema": RAW_EVIDENCE_SCHEMA_ID + "__CONTROL",
                "policy_id": self.policy_id,
                "mechanical_control_receipt_sha256": self.mechanical_control_receipt_sha256,
                "burden": [self.burden_numerator, self.burden_denominator],
                "axes": self._axis_roots(),
                "negative_control_delta": _array_digest(
                    "negative_control_delta", self.negative_control_delta
                ),
                "planted_detect_excess": _array_digest(
                    "planted_detect_excess", self.planted_detect_excess
                ),
                "planted_after_mask_excess": _array_digest(
                    "planted_after_mask_excess", self.planted_after_mask_excess
                ),
            }
        )

    def nonlinear_evidence_digest(self) -> str:
        self.validate()
        return _json_digest(
            {
                "schema": RAW_EVIDENCE_SCHEMA_ID + "__NONLINEAR",
                "policy_id": self.policy_id,
                "mechanical_control_receipt_sha256": self.mechanical_control_receipt_sha256,
                "burden": [self.burden_numerator, self.burden_denominator],
                "axes": self._axis_roots(),
                "policy_mask_sha256_by_target_fold": _sha256_grid_digest(
                    "policy_mask_sha256_by_target_fold",
                    self.policy_mask_sha256_by_target_fold,
                ),
                "nonlinear_actual_scores": _array_digest(
                    "nonlinear_actual_scores", self.nonlinear_actual_scores
                ),
                "nonlinear_shuffled_same_mask_scores": _array_digest(
                    "nonlinear_shuffled_same_mask_scores",
                    self.nonlinear_shuffled_same_mask_scores,
                ),
            }
        )

    def canonical_digest(self) -> str:
        self.validate()
        return _json_digest(
            {
                "schema": RAW_EVIDENCE_SCHEMA_ID,
                "primary": self.primary_evidence_digest(),
                "control": self.control_evidence_digest(),
                "nonlinear": self.nonlinear_evidence_digest(),
            }
        )


def _interval(
    precision: Any, matrix: np.ndarray, donor_source_code: np.ndarray
) -> IntervalEvidenceV1:
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


def _source_balanced_target_means(
    matrix: np.ndarray, donor_source_code: np.ndarray
) -> np.ndarray:
    source = np.asarray(donor_source_code, dtype=np.int64)
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
    raw_evidence: TerminalPolicyRawEvidenceV1,
    precision: QualificationPrecisionAuthorityV4,
) -> MaskingPolicyDecisionEvidenceV1:
    """Assemble one policy's decision evidence from a hash-bound raw bundle."""

    TerminalEvidenceAssemblySemanticsV1().validate()
    if not isinstance(raw_evidence, TerminalPolicyRawEvidenceV1):
        raise ValueError("raw_evidence must be TerminalPolicyRawEvidenceV1")
    if not isinstance(precision, QualificationPrecisionAuthorityV4):
        raise ValueError("precision must be QualificationPrecisionAuthorityV4")
    raw_evidence.validate()
    precision.validate()

    actual = raw_evidence.actual_policy_scores
    uniform = raw_evidence.actual_uniform_scores
    shuffled = raw_evidence.shuffled_same_mask_scores
    neg = raw_evidence.negative_control_delta
    plant_detect = raw_evidence.planted_detect_excess
    plant_after = raw_evidence.planted_after_mask_excess
    nl_actual = raw_evidence.nonlinear_actual_scores
    nl_shuffled = raw_evidence.nonlinear_shuffled_same_mask_scores
    donor_source = raw_evidence.donor_source_code
    effective = raw_evidence.effective_targeted_n_by_target_fold

    outer_fold_count = len(set(map(int, raw_evidence.donor_outer_fold)))
    precision.assert_sufficient(
        target_count=int(actual.shape[0]),
        donor_count=int(actual.shape[1]),
        outer_fold_count=outer_fold_count,
    )

    delta = uniform - actual
    residual = actual - shuffled
    nonlinear_residual = nl_actual - nl_shuffled
    target_delta = _source_balanced_target_means(delta, donor_source)

    evidence = MaskingPolicyDecisionEvidenceV1(
        policy_id=raw_evidence.policy_id,
        burden_numerator=raw_evidence.burden_numerator,
        burden_denominator=raw_evidence.burden_denominator,
        raw_primary_evidence_sha256=raw_evidence.primary_evidence_digest(),
        raw_control_evidence_sha256=raw_evidence.control_evidence_digest(),
        raw_nonlinear_evidence_sha256=raw_evidence.nonlinear_evidence_digest(),
        precision_authority_sha256=precision.canonical_digest(),
        delta_vs_uniform=_interval(precision, delta, donor_source),
        excess_over_shuffled_null=_interval(precision, residual, donor_source),
        source_excess_upper_one_sided=_source_upper_bounds(
            precision, residual, donor_source, raw_evidence.source_names
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
        replay_exact=raw_evidence.replay_exact,
        untreated_identity_exact=raw_evidence.untreated_identity_exact,
        no_privileged_metadata=raw_evidence.no_privileged_metadata,
        precision_requirements_met=True,
        terminal_outcomes_inspected_before_freeze=False,
    )
    evidence.validate()
    return evidence
