"""Fixed-source, prospectively margin-calibrated masking qualification decision.

The current V4 semantic rule keeps the pre-terminal null-equivalence margin from
PrecisionAuthorityV4, uses that same frozen margin for target-level heterogeneity,
and never lets the realized negative-control interval move the target-harm floor.
Targeted improvements must clear source-specific lower-bound guardrails for every
observed source.

Within one burden rung, targeting complexity is measured as the mean number of
effective targeted partners over target x outer-fold cells. Because each cell is
an integer count, differences smaller than one full effective partner per cell on
average are prospectively treated as complexity-equivalent; efficacy lower bound
then decides among those policies. A full one-partner average advantage remains
material. This rule is frozen before terminal outcomes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from typing import Mapping, Sequence

from .masking_qualification_decision_v1 import (
    MaskingPolicyDecisionEvidenceV1,
    POLICIES,
    POLICY_ORDER,
)

DECISION_RULE_ID = "FIXED_SOURCE_NULL_EQUIVALENCE_SOURCE_BENEFIT_PROSPECTIVE_HETEROGENEITY_AND_MATERIAL_TARGETING_V4"
POLICY_SELECTION_RULE_ID = "UNIFORM_IF_SUFFICIENT_ELSE_ONE_EFFECTIVE_PARTNER_MATERIALITY_THEN_MAX_LOWER_BOUND_V2"
TARGET_HETEROGENEITY_GUARDRAIL_ID = "WORST_TARGET_DELTA_GE_NEGATIVE_FROZEN_NULL_EQUIVALENCE_MARGIN_V1"
TARGETING_COMPLEXITY_MATERIALITY_ID = "ONE_EFFECTIVE_PARTNER_PER_TARGET_FOLD_MEAN_V1"
TARGETING_COMPLEXITY_MATERIALITY_NUMERATOR = 1
TARGETING_COMPLEXITY_MATERIALITY_DENOMINATOR = 1


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
    mean_effective_targeted_n: float
    delta_lower_one_sided: float
    decision_rule_id: str
    evidence_digest: str

    def canonical_digest(self) -> str:
        return _digest({"schema": "V5_MASKING_POLICY_DECISION_RECEIPT_V4", **asdict(self)})


@dataclass(frozen=True)
class MaskingRungDecisionReceiptV2:
    burden_numerator: int
    burden_denominator: int
    qualified: bool
    selected_policy_id: str
    policy_receipt_sha256: Mapping[str, str]
    decision_rule_id: str = DECISION_RULE_ID
    policy_selection_rule_id: str = POLICY_SELECTION_RULE_ID
    target_heterogeneity_guardrail_id: str = TARGET_HETEROGENEITY_GUARDRAIL_ID
    targeting_complexity_materiality_id: str = TARGETING_COMPLEXITY_MATERIALITY_ID
    targeting_complexity_materiality_numerator: int = TARGETING_COMPLEXITY_MATERIALITY_NUMERATOR
    targeting_complexity_materiality_denominator: int = TARGETING_COMPLEXITY_MATERIALITY_DENOMINATOR

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
        if self.target_heterogeneity_guardrail_id != TARGET_HETEROGENEITY_GUARDRAIL_ID:
            raise ValueError("target_heterogeneity_guardrail_id mismatch")
        if self.targeting_complexity_materiality_id != TARGETING_COMPLEXITY_MATERIALITY_ID:
            raise ValueError("targeting_complexity_materiality_id mismatch")
        if (
            self.targeting_complexity_materiality_numerator,
            self.targeting_complexity_materiality_denominator,
        ) != (
            TARGETING_COMPLEXITY_MATERIALITY_NUMERATOR,
            TARGETING_COMPLEXITY_MATERIALITY_DENOMINATOR,
        ):
            raise ValueError("targeting complexity materiality mismatch")
        for digest in self.policy_receipt_sha256.values():
            if not isinstance(digest, str) or len(digest) != 64:
                raise ValueError("policy receipt roots must be SHA-256 digests")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({
            "schema": "V5_MASKING_RUNG_DECISION_RECEIPT_V4",
            **asdict(self),
            "policy_receipt_sha256": dict(sorted(self.policy_receipt_sha256.items())),
        })


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
        heterogeneity = (
            evidence.worst_target_delta
            >= -tolerance
        )

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
        "source_excess_upper_one_sided": dict(evidence.source_excess_upper_one_sided),
        "source_delta_lower_one_sided": dict(evidence.source_delta_lower_one_sided),
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
        mean_effective_targeted_n=float(evidence.mean_effective_targeted_n),
        delta_lower_one_sided=float(evidence.delta_vs_uniform.lower_one_sided),
        decision_rule_id=DECISION_RULE_ID,
        evidence_digest=_digest(raw),
    )


def select_policy_v2(receipts: Sequence[MaskingPolicyDecisionReceiptV2]) -> str:
    by_policy = {receipt.policy_id: receipt for receipt in receipts}
    if len(by_policy) != len(receipts) or set(by_policy) != set(POLICIES):
        raise ValueError("exactly one decision receipt is required for every policy arm")
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
    materiality = float(
        Fraction(
            TARGETING_COMPLEXITY_MATERIALITY_NUMERATOR,
            TARGETING_COMPLEXITY_MATERIALITY_DENOMINATOR,
        )
    )
    min_targeting = min(float(r.mean_effective_targeted_n) for r in qualified)
    complexity_equivalent = [
        r
        for r in qualified
        if float(r.mean_effective_targeted_n) - min_targeting < materiality
    ]
    complexity_equivalent.sort(
        key=lambda r: (
            -float(r.delta_lower_one_sided),
            float(r.mean_effective_targeted_n),
            POLICY_ORDER[r.policy_id],
        )
    )
    return complexity_equivalent[0].policy_id


def evaluate_rung_v2(
    evidence_by_policy: Sequence[MaskingPolicyDecisionEvidenceV1],
) -> MaskingRungDecisionReceiptV2:
    if len(evidence_by_policy) != len(POLICIES):
        raise ValueError("rung evaluation requires evidence for all four policy arms")
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
