"""Fixed-source, prospectively margin-calibrated masking qualification decision.

The current V5 semantic rule uses a pre-terminal equivalence margin frozen
in PrecisionAuthorityV4. The terminal negative-control interval must fit inside
that fixed margin; its observed width can never enlarge either the null bar or
the target-heterogeneity floor. Targeted improvements must clear source-specific
lower-bound guardrails. Targeting complexity is bound as an exact integer total
over the target x outer-fold grid. Among qualified targeted policies, only the
smallest possible nonzero complexity difference -- one total effective targeted
event over the entire bound grid -- is treated as equivalent before the effect
lower bound breaks the tie.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Mapping, Sequence

from .masking_qualification_decision_v1 import (
    MaskingPolicyDecisionEvidenceV1,
    POLICIES,
    POLICY_ORDER,
)
from .precision_authority_v4 import QualificationPrecisionAuthorityV4

DECISION_RULE_ID = "FIXED_SOURCE_NULL_EQUIVALENCE_SOURCE_BENEFIT_FIXED_HETEROGENEITY_AND_DISCRETE_TARGETING_SHORTCUT_SUPPRESSION_V5"
POLICY_SELECTION_RULE_ID = "UNIFORM_IF_SUFFICIENT_ELSE_MIN_EXACT_TARGETING_WITHIN_ONE_TOTAL_EVENT_EQUIVALENCE_THEN_MAX_LOWER_BOUND_V3"
TARGET_HETEROGENEITY_FLOOR_RULE_ID = "WORST_TARGET_NO_WORSE_THAN_NEGATIVE_FROZEN_NULL_EQUIVALENCE_MARGIN_V1"
TARGETING_COMPLEXITY_MATERIALITY_RULE_ID = "ONE_TOTAL_EFFECTIVE_TARGET_EVENT_OVER_BOUND_TARGET_X_FOLD_GRID_V2"
TARGETING_COMPLEXITY_EQUIVALENCE_EVENTS = 1


def _digest(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class MaskingPolicyDecisionReceiptV2:
    policy_id: str
    burden_numerator: int
    burden_denominator: int
    qualified: bool
    controls_passed: bool
    negative_control_precision_passed: bool
    primary_null_level_passed: bool
    targeted_improvement_passed: bool
    source_improvement_guardrail_passed: bool
    heterogeneity_guardrail_passed: bool
    nonlinear_guardrail_passed: bool
    null_noise_tolerance: float
    target_heterogeneity_floor: float
    target_heterogeneity_floor_rule_id: str
    mean_effective_targeted_n: float
    total_effective_targeted_n: int
    targeting_complexity_observation_count: int
    delta_lower_one_sided: float
    decision_rule_id: str
    evidence_digest: str

    def canonical_digest(self) -> str:
        return _digest({"schema": "V5_MASKING_POLICY_DECISION_RECEIPT_V5", **asdict(self)})


@dataclass(frozen=True)
class MaskingRungDecisionReceiptV2:
    burden_numerator: int
    burden_denominator: int
    qualified: bool
    selected_policy_id: str
    policy_receipt_sha256: Mapping[str, str]
    decision_rule_id: str = DECISION_RULE_ID
    policy_selection_rule_id: str = POLICY_SELECTION_RULE_ID
    targeting_complexity_materiality_rule_id: str = TARGETING_COMPLEXITY_MATERIALITY_RULE_ID
    targeting_complexity_equivalence_events: int = TARGETING_COMPLEXITY_EQUIVALENCE_EVENTS

    def validate(self) -> None:
        if set(self.policy_receipt_sha256) != set(POLICIES):
            raise ValueError("rung receipt must bind exactly one receipt for every policy")
        if self.selected_policy_id not in (*POLICIES, "NO_POLICY_QUALIFIED"):
            raise ValueError("selected_policy_id mismatch")
        if self.qualified != (self.selected_policy_id != "NO_POLICY_QUALIFIED"):
            raise ValueError("qualified flag and selected policy disagree")
        if self.decision_rule_id != DECISION_RULE_ID:
            raise ValueError("decision_rule_id mismatch")
        if self.policy_selection_rule_id != POLICY_SELECTION_RULE_ID:
            raise ValueError("policy_selection_rule_id mismatch")
        if self.targeting_complexity_materiality_rule_id != TARGETING_COMPLEXITY_MATERIALITY_RULE_ID:
            raise ValueError("targeting_complexity_materiality_rule_id mismatch")
        if self.targeting_complexity_equivalence_events != TARGETING_COMPLEXITY_EQUIVALENCE_EVENTS:
            raise ValueError("targeting_complexity_equivalence_events mismatch")
        for digest in self.policy_receipt_sha256.values():
            if not isinstance(digest, str) or len(digest) != 64 or digest != digest.lower():
                raise ValueError("policy receipt roots must be lowercase SHA-256 digests")
            try:
                int(digest, 16)
            except ValueError as exc:
                raise ValueError("policy receipt roots must be lowercase SHA-256 digests") from exc

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({
            "schema": "V5_MASKING_RUNG_DECISION_RECEIPT_V5",
            **asdict(self),
            "policy_receipt_sha256": dict(sorted(self.policy_receipt_sha256.items())),
        })


def _bind_precision_authority(
    evidence: MaskingPolicyDecisionEvidenceV1,
    precision: QualificationPrecisionAuthorityV4,
) -> None:
    if not isinstance(precision, QualificationPrecisionAuthorityV4):
        raise ValueError("precision must be QualificationPrecisionAuthorityV4")
    precision.validate()
    evidence.validate()
    if evidence.precision_authority_sha256 != precision.canonical_digest():
        raise ValueError("decision evidence binds a different precision authority")
    if (
        evidence.null_equivalence_margin_numerator,
        evidence.null_equivalence_margin_denominator,
    ) != (
        precision.null_equivalence_margin_numerator,
        precision.null_equivalence_margin_denominator,
    ):
        raise ValueError("decision evidence exact null-equivalence margin disagrees with precision authority")
    if float(evidence.null_noise_tolerance_ceiling) != precision.null_equivalence_margin:
        raise ValueError("decision evidence null-noise ceiling disagrees with precision authority")


def null_noise_tolerance(evidence: MaskingPolicyDecisionEvidenceV1) -> float:
    """Return the prospectively frozen equivalence margin.

    The terminal negative-control width never defines or enlarges this margin.
    Its only role is to pass the separately frozen precision/equivalence check.
    """

    evidence.validate()
    return float(evidence.null_noise_tolerance_ceiling)


def evaluate_policy_v2(
    evidence: MaskingPolicyDecisionEvidenceV1,
) -> MaskingPolicyDecisionReceiptV2:
    evidence.validate()
    tolerance = null_noise_tolerance(evidence)

    negative_ok = bool(evidence.negative_control_precision_passed)
    planted_ok = (
        evidence.planted_detect_excess.lower_one_sided > tolerance
        and evidence.planted_after_mask_excess.upper_one_sided <= tolerance
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
        evidence.excess_over_shuffled_null.upper_one_sided <= tolerance
        and all(
            float(value) <= tolerance
            for value in evidence.source_excess_upper_one_sided.values()
        )
    )

    target_heterogeneity_floor = -tolerance

    if evidence.policy_id == "UNIFORM_RANDOM":
        source_improvement_guardrail = True
        improvement = True
        heterogeneity = True
    else:
        source_improvement_guardrail = all(
            float(value) >= 0.0
            for value in evidence.source_delta_lower_one_sided.values()
        )
        improvement = (
            evidence.delta_vs_uniform.lower_one_sided > 0.0
            and evidence.target_delta_median >= 0.0
            and source_improvement_guardrail
        )
        heterogeneity = evidence.worst_target_delta >= target_heterogeneity_floor

    nonlinear = (
        evidence.nonlinear_excess_over_shuffled_null.upper_one_sided <= tolerance
    )
    qualified = controls and primary_null and improvement and heterogeneity and nonlinear

    raw = {
        "policy_id": evidence.policy_id,
        "burden_numerator": evidence.burden_numerator,
        "burden_denominator": evidence.burden_denominator,
        "raw_primary_evidence_sha256": evidence.raw_primary_evidence_sha256,
        "raw_control_evidence_sha256": evidence.raw_control_evidence_sha256,
        "raw_nonlinear_evidence_sha256": evidence.raw_nonlinear_evidence_sha256,
        "precision_authority_sha256": evidence.precision_authority_sha256,
        "null_noise_tolerance": tolerance,
        "target_heterogeneity_floor": target_heterogeneity_floor,
        "target_heterogeneity_floor_rule_id": TARGET_HETEROGENEITY_FLOOR_RULE_ID,
        "source_excess_upper_one_sided": dict(evidence.source_excess_upper_one_sided),
        "source_delta_lower_one_sided": dict(evidence.source_delta_lower_one_sided),
        "total_effective_targeted_n": evidence.total_effective_targeted_n,
        "targeting_complexity_observation_count": evidence.targeting_complexity_observation_count,
        "negative_control_precision_passed": evidence.negative_control_precision_passed,
        "replay_exact": evidence.replay_exact,
        "untreated_identity_exact": evidence.untreated_identity_exact,
        "no_privileged_metadata": evidence.no_privileged_metadata,
        "precision_requirements_met": evidence.precision_requirements_met,
    }
    return MaskingPolicyDecisionReceiptV2(
        policy_id=evidence.policy_id,
        burden_numerator=evidence.burden_numerator,
        burden_denominator=evidence.burden_denominator,
        qualified=qualified,
        controls_passed=controls,
        negative_control_precision_passed=negative_ok,
        primary_null_level_passed=primary_null,
        targeted_improvement_passed=improvement,
        source_improvement_guardrail_passed=source_improvement_guardrail,
        heterogeneity_guardrail_passed=heterogeneity,
        nonlinear_guardrail_passed=nonlinear,
        null_noise_tolerance=tolerance,
        target_heterogeneity_floor=target_heterogeneity_floor,
        target_heterogeneity_floor_rule_id=TARGET_HETEROGENEITY_FLOOR_RULE_ID,
        mean_effective_targeted_n=float(evidence.mean_effective_targeted_n),
        total_effective_targeted_n=int(evidence.total_effective_targeted_n),
        targeting_complexity_observation_count=int(evidence.targeting_complexity_observation_count),
        delta_lower_one_sided=float(evidence.delta_vs_uniform.lower_one_sided),
        decision_rule_id=DECISION_RULE_ID,
        evidence_digest=_digest(raw),
    )


def select_policy_v2(receipts: Sequence[MaskingPolicyDecisionReceiptV2]) -> str:
    by_policy = {receipt.policy_id: receipt for receipt in receipts}
    if len(by_policy) != len(receipts) or set(by_policy) != set(POLICIES):
        raise ValueError("exactly one decision receipt is required for every policy arm")
    if any(r.decision_rule_id != DECISION_RULE_ID for r in receipts):
        raise ValueError("all policy receipts must use the current decision rule")
    if any(r.target_heterogeneity_floor_rule_id != TARGET_HETEROGENEITY_FLOOR_RULE_ID for r in receipts):
        raise ValueError("all policy receipts must use the current target-heterogeneity floor rule")
    observation_counts = set()
    for receipt in receipts:
        complexity = float(receipt.mean_effective_targeted_n)
        effect = float(receipt.delta_lower_one_sided)
        total = receipt.total_effective_targeted_n
        count = receipt.targeting_complexity_observation_count
        if not math.isfinite(complexity) or complexity < 0.0:
            raise ValueError("mean_effective_targeted_n must be finite and nonnegative")
        if (
            isinstance(total, bool)
            or not isinstance(total, int)
            or total < 0
        ):
            raise ValueError("total_effective_targeted_n must be a nonnegative integer")
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or count < 1
        ):
            raise ValueError("targeting_complexity_observation_count must be a positive integer")
        expected_mean = float(total) / float(count)
        if abs(complexity - expected_mean) > 1e-12:
            raise ValueError("mean targeting complexity is off the exact target x fold lattice")
        observation_counts.add(count)
        if not math.isfinite(effect):
            raise ValueError("delta_lower_one_sided must be finite")
    if len(observation_counts) != 1:
        raise ValueError("all policy receipts must bind the same target x fold complexity grid")
    burdens = {(r.burden_numerator, r.burden_denominator) for r in receipts}
    if len(burdens) != 1:
        raise ValueError("all policy receipts must belong to the same burden rung")
    if by_policy["UNIFORM_RANDOM"].qualified:
        return "UNIFORM_RANDOM"
    qualified = [
        r for r in receipts if r.policy_id != "UNIFORM_RANDOM" and r.qualified
    ]
    if not qualified:
        return "NO_POLICY_QUALIFIED"
    minimum_total = min(r.total_effective_targeted_n for r in qualified)
    complexity_equivalent = [
        r
        for r in qualified
        if r.total_effective_targeted_n - minimum_total
        <= TARGETING_COMPLEXITY_EQUIVALENCE_EVENTS
    ]
    complexity_equivalent.sort(
        key=lambda r: (
            -float(r.delta_lower_one_sided),
            POLICY_ORDER[r.policy_id],
        )
    )
    return complexity_equivalent[0].policy_id


def evaluate_rung_v2(
    evidence_by_policy: Sequence[MaskingPolicyDecisionEvidenceV1],
    *,
    precision: QualificationPrecisionAuthorityV4,
) -> MaskingRungDecisionReceiptV2:
    if len(evidence_by_policy) != len(POLICIES):
        raise ValueError("rung evaluation requires evidence for all four policy arms")
    for evidence in evidence_by_policy:
        _bind_precision_authority(evidence, precision)
    receipts = [evaluate_policy_v2(e) for e in evidence_by_policy]
    selected = select_policy_v2(receipts)
    burdens = {(r.burden_numerator, r.burden_denominator) for r in receipts}
    if len(burdens) != 1:
        raise ValueError("all policy evidence must belong to the same burden rung")
    num, den = next(iter(burdens))
    return MaskingRungDecisionReceiptV2(
        burden_numerator=num,
        burden_denominator=den,
        qualified=selected != "NO_POLICY_QUALIFIED",
        selected_policy_id=selected,
        policy_receipt_sha256={r.policy_id: r.canonical_digest() for r in receipts},
    )
