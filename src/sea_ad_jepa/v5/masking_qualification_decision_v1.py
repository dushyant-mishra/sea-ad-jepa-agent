"""Mechanical masking-qualification decisions from bound evidence summaries.

The decision asks whether easy expression-proxy predictability has been reduced
to the within-donor shuffled/null level. It does not claim biological-state
recovery and it never tunes a policy after terminal outcomes are seen.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from typing import Any, Mapping, Sequence

POLICIES = ("UNIFORM_RANDOM", "TOP8_CORRELATION", "RIDGE8_CONDITIONAL", "PREFIX3_SELECTIVE")
POLICY_ORDER = {name: index for index, name in enumerate(POLICIES)}
DECISION_RULE_ID = "NULL_LEVEL_SHORTCUT_SUPPRESSION_WITH_PAIRED_DONOR_TARGET_UNCERTAINTY_V1"
POLICY_SELECTION_RULE_ID = "UNIFORM_IF_SUFFICIENT_ELSE_MIN_TARGETING_THEN_MAX_LOWER_BOUND_V1"


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


def _finite(value: object, name: str) -> float:
    import math
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite")
    return out


@dataclass(frozen=True)
class IntervalEvidenceV1:
    mean: float
    lower_two_sided: float
    upper_two_sided: float
    lower_one_sided: float
    upper_one_sided: float

    def validate(self) -> None:
        mean = _finite(self.mean, "mean")
        lower_two = _finite(self.lower_two_sided, "lower_two_sided")
        upper_two = _finite(self.upper_two_sided, "upper_two_sided")
        lower_one = _finite(self.lower_one_sided, "lower_one_sided")
        upper_one = _finite(self.upper_one_sided, "upper_one_sided")
        if lower_two > upper_two:
            raise ValueError("two-sided interval is reversed")
        if not lower_two <= mean <= upper_two:
            raise ValueError("mean must lie inside the two-sided interval")
        if lower_one > upper_one:
            raise ValueError("one-sided bounds are reversed")


@dataclass(frozen=True)
class MaskingPolicyDecisionEvidenceV1:
    policy_id: str
    burden_numerator: int
    burden_denominator: int
    raw_primary_evidence_sha256: str
    raw_control_evidence_sha256: str
    raw_nonlinear_evidence_sha256: str
    precision_authority_sha256: str

    delta_vs_uniform: IntervalEvidenceV1
    excess_over_shuffled_null: IntervalEvidenceV1
    source_excess_upper_one_sided: Mapping[str, float]
    source_delta_lower_one_sided: Mapping[str, float]
    target_delta_median: float
    worst_target_delta: float
    mean_effective_targeted_n: float
    total_effective_targeted_n: int
    targeting_complexity_observation_count: int

    negative_control_delta: IntervalEvidenceV1
    planted_detect_excess: IntervalEvidenceV1
    planted_after_mask_excess: IntervalEvidenceV1
    nonlinear_excess_over_shuffled_null: IntervalEvidenceV1
    null_noise_tolerance_ceiling: float
    negative_control_precision_passed: bool

    replay_exact: bool
    untreated_identity_exact: bool
    no_privileged_metadata: bool
    precision_requirements_met: bool
    terminal_outcomes_inspected_before_freeze: bool = False

    def validate(self) -> None:
        if self.policy_id not in POLICIES:
            raise ValueError("policy_id is not an approved masking arm")
        if (
            isinstance(self.burden_numerator, bool)
            or isinstance(self.burden_denominator, bool)
            or not isinstance(self.burden_numerator, int)
            or not isinstance(self.burden_denominator, int)
            or self.burden_numerator <= 0
            or self.burden_denominator <= 0
            or self.burden_numerator >= self.burden_denominator
        ):
            raise ValueError("burden must be an exact positive fraction below one")
        roots = (
            _sha(self.raw_primary_evidence_sha256, "raw_primary_evidence_sha256"),
            _sha(self.raw_control_evidence_sha256, "raw_control_evidence_sha256"),
            _sha(self.raw_nonlinear_evidence_sha256, "raw_nonlinear_evidence_sha256"),
            _sha(self.precision_authority_sha256, "precision_authority_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("decision evidence roots must be distinct")
        for interval in (
            self.delta_vs_uniform,
            self.excess_over_shuffled_null,
            self.negative_control_delta,
            self.planted_detect_excess,
            self.planted_after_mask_excess,
            self.nonlinear_excess_over_shuffled_null,
        ):
            interval.validate()
        if not self.source_excess_upper_one_sided:
            raise ValueError("source-specific null comparison is required")
        if not self.source_delta_lower_one_sided:
            raise ValueError("source-specific improvement comparison is required")
        if set(self.source_excess_upper_one_sided) != set(self.source_delta_lower_one_sided):
            raise ValueError("source-specific null and improvement maps must cover identical sources")
        for source, value in self.source_excess_upper_one_sided.items():
            if not isinstance(source, str) or not source:
                raise ValueError("source names must be nonempty")
            _finite(value, f"source_excess_upper_one_sided[{source}]")
            _finite(
                self.source_delta_lower_one_sided[source],
                f"source_delta_lower_one_sided[{source}]",
            )
        tolerance = _finite(self.null_noise_tolerance_ceiling, "null_noise_tolerance_ceiling")
        if tolerance <= 0.0:
            raise ValueError("null_noise_tolerance_ceiling must be positive")
        neg = self.negative_control_delta
        expected_negative_precision = bool(
            neg.lower_two_sided <= 0.0 <= neg.upper_two_sided
            and neg.lower_two_sided >= -tolerance
            and neg.upper_two_sided <= tolerance
        )
        if self.negative_control_precision_passed is not expected_negative_precision:
            raise ValueError(
                "negative_control_precision_passed disagrees with the frozen "
                "null-equivalence margin and negative-control interval"
            )
        for name in ("target_delta_median", "worst_target_delta", "mean_effective_targeted_n"):
            _finite(getattr(self, name), name)
        if self.mean_effective_targeted_n < 0:
            raise ValueError("mean_effective_targeted_n cannot be negative")
        if (
            isinstance(self.total_effective_targeted_n, bool)
            or not isinstance(self.total_effective_targeted_n, int)
            or self.total_effective_targeted_n < 0
        ):
            raise ValueError("total_effective_targeted_n must be a nonnegative integer")
        if (
            isinstance(self.targeting_complexity_observation_count, bool)
            or not isinstance(self.targeting_complexity_observation_count, int)
            or self.targeting_complexity_observation_count < 1
        ):
            raise ValueError("targeting_complexity_observation_count must be a positive integer")
        expected_mean = (
            float(self.total_effective_targeted_n)
            / float(self.targeting_complexity_observation_count)
        )
        if abs(float(self.mean_effective_targeted_n) - expected_mean) > 1e-12:
            raise ValueError(
                "mean_effective_targeted_n must equal exact total/count complexity"
            )
        for name in (
            "negative_control_precision_passed",
            "replay_exact", "untreated_identity_exact", "no_privileged_metadata",
            "precision_requirements_met", "terminal_outcomes_inspected_before_freeze",
        ):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name} must be boolean")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("decision design was not frozen before terminal outcomes")

    @property
    def burden(self) -> Fraction:
        self.validate()
        return Fraction(self.burden_numerator, self.burden_denominator)


@dataclass(frozen=True)
class MaskingPolicyDecisionReceiptV1:
    policy_id: str
    burden_numerator: int
    burden_denominator: int
    qualified: bool
    controls_passed: bool
    primary_null_level_passed: bool
    targeted_improvement_passed: bool
    heterogeneity_guardrail_passed: bool
    nonlinear_guardrail_passed: bool
    mean_effective_targeted_n: float
    delta_lower_one_sided: float
    decision_rule_id: str
    evidence_digest: str

    def canonical_digest(self) -> str:
        return _digest({"schema": "V5_MASKING_POLICY_DECISION_RECEIPT_V1", **asdict(self)})


@dataclass(frozen=True)
class MaskingRungDecisionReceiptV1:
    burden_numerator: int
    burden_denominator: int
    qualified: bool
    selected_policy_id: str
    policy_receipt_sha256: Mapping[str, str]
    policy_selection_rule_id: str = POLICY_SELECTION_RULE_ID

    def validate(self) -> None:
        if set(self.policy_receipt_sha256) != set(POLICIES):
            raise ValueError("rung receipt must bind exactly one receipt for every policy")
        for policy, digest in self.policy_receipt_sha256.items():
            if policy not in POLICIES:
                raise ValueError("unapproved policy in rung receipt")
            _sha(digest, f"policy_receipt_sha256[{policy}]")
        if self.policy_selection_rule_id != POLICY_SELECTION_RULE_ID:
            raise ValueError("policy_selection_rule_id mismatch")
        if self.selected_policy_id not in (*POLICIES, "NO_POLICY_QUALIFIED"):
            raise ValueError("selected_policy_id mismatch")
        if self.qualified != (self.selected_policy_id != "NO_POLICY_QUALIFIED"):
            raise ValueError("qualified flag and selected policy disagree")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({
            "schema": "V5_MASKING_RUNG_DECISION_RECEIPT_V1",
            **asdict(self),
            "policy_receipt_sha256": dict(sorted(self.policy_receipt_sha256.items())),
        })


def evaluate_policy(evidence: MaskingPolicyDecisionEvidenceV1) -> MaskingPolicyDecisionReceiptV1:
    evidence.validate()

    negative_ok = (
        evidence.negative_control_delta.lower_two_sided <= 0.0
        <= evidence.negative_control_delta.upper_two_sided
    )
    planted_ok = (
        evidence.planted_detect_excess.lower_one_sided > 0.0
        and evidence.planted_after_mask_excess.upper_one_sided <= 0.0
    )
    controls = (
        negative_ok
        and planted_ok
        and evidence.replay_exact
        and evidence.untreated_identity_exact
        and evidence.no_privileged_metadata
        and evidence.precision_requirements_met
    )

    primary_null = (
        evidence.excess_over_shuffled_null.upper_one_sided <= 0.0
        and all(float(v) <= 0.0 for v in evidence.source_excess_upper_one_sided.values())
    )

    if evidence.policy_id == "UNIFORM_RANDOM":
        improvement = True
        heterogeneity = True
    else:
        improvement = (
            evidence.delta_vs_uniform.lower_one_sided > 0.0
            and evidence.target_delta_median >= 0.0
        )
        heterogeneity = (
            evidence.worst_target_delta
            >= evidence.negative_control_delta.lower_two_sided
        )

    nonlinear = evidence.nonlinear_excess_over_shuffled_null.upper_one_sided <= 0.0
    qualified = controls and primary_null and improvement and heterogeneity and nonlinear

    raw = {
        "policy_id": evidence.policy_id,
        "burden_numerator": evidence.burden_numerator,
        "burden_denominator": evidence.burden_denominator,
        "raw_primary_evidence_sha256": evidence.raw_primary_evidence_sha256,
        "raw_control_evidence_sha256": evidence.raw_control_evidence_sha256,
        "raw_nonlinear_evidence_sha256": evidence.raw_nonlinear_evidence_sha256,
        "precision_authority_sha256": evidence.precision_authority_sha256,
        "delta_vs_uniform": asdict(evidence.delta_vs_uniform),
        "excess_over_shuffled_null": asdict(evidence.excess_over_shuffled_null),
        "source_excess_upper_one_sided": dict(evidence.source_excess_upper_one_sided),
        "target_delta_median": evidence.target_delta_median,
        "worst_target_delta": evidence.worst_target_delta,
        "mean_effective_targeted_n": evidence.mean_effective_targeted_n,
        "negative_control_delta": asdict(evidence.negative_control_delta),
        "planted_detect_excess": asdict(evidence.planted_detect_excess),
        "planted_after_mask_excess": asdict(evidence.planted_after_mask_excess),
        "nonlinear_excess_over_shuffled_null": asdict(evidence.nonlinear_excess_over_shuffled_null),
        "replay_exact": evidence.replay_exact,
        "untreated_identity_exact": evidence.untreated_identity_exact,
        "no_privileged_metadata": evidence.no_privileged_metadata,
        "precision_requirements_met": evidence.precision_requirements_met,
    }
    return MaskingPolicyDecisionReceiptV1(
        policy_id=evidence.policy_id,
        burden_numerator=evidence.burden_numerator,
        burden_denominator=evidence.burden_denominator,
        qualified=qualified,
        controls_passed=controls,
        primary_null_level_passed=primary_null,
        targeted_improvement_passed=improvement,
        heterogeneity_guardrail_passed=heterogeneity,
        nonlinear_guardrail_passed=nonlinear,
        mean_effective_targeted_n=float(evidence.mean_effective_targeted_n),
        delta_lower_one_sided=float(evidence.delta_vs_uniform.lower_one_sided),
        decision_rule_id=DECISION_RULE_ID,
        evidence_digest=_digest(raw),
    )


def select_policy(receipts: Sequence[MaskingPolicyDecisionReceiptV1]) -> str:
    """Select prospectively: uniform if sufficient, else least targeted qualifier."""

    by_policy = {receipt.policy_id: receipt for receipt in receipts}
    if len(by_policy) != len(receipts) or set(by_policy) != set(POLICIES):
        raise ValueError("exactly one decision receipt is required for every policy arm")
    burdens = {(r.burden_numerator, r.burden_denominator) for r in receipts}
    if len(burdens) != 1:
        raise ValueError("all policy receipts must belong to the same burden rung")

    if by_policy["UNIFORM_RANDOM"].qualified:
        return "UNIFORM_RANDOM"

    qualified = [
        r for r in receipts
        if r.policy_id != "UNIFORM_RANDOM" and r.qualified
    ]
    if not qualified:
        return "NO_POLICY_QUALIFIED"

    qualified.sort(
        key=lambda r: (
            float(r.mean_effective_targeted_n),
            -float(r.delta_lower_one_sided),
            POLICY_ORDER[r.policy_id],
        )
    )
    return qualified[0].policy_id


def evaluate_rung(
    evidence_by_policy: Sequence[MaskingPolicyDecisionEvidenceV1],
) -> MaskingRungDecisionReceiptV1:
    if len(evidence_by_policy) != len(POLICIES):
        raise ValueError("rung evaluation requires evidence for all four policy arms")
    receipts = [evaluate_policy(evidence) for evidence in evidence_by_policy]
    selected = select_policy(receipts)
    burdens = {(r.burden_numerator, r.burden_denominator) for r in receipts}
    if len(burdens) != 1:
        raise ValueError("all policy evidence must belong to the same burden rung")
    numerator, denominator = next(iter(burdens))
    policy_hashes = {r.policy_id: r.canonical_digest() for r in receipts}
    return MaskingRungDecisionReceiptV1(
        burden_numerator=numerator,
        burden_denominator=denominator,
        qualified=selected != "NO_POLICY_QUALIFIED",
        selected_policy_id=selected,
        policy_receipt_sha256=policy_hashes,
    )
