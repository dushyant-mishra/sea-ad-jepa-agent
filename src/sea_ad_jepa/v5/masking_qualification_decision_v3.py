"""Masking decision V3 requiring nonlinear attacker competence."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Mapping, Sequence

from .masking_qualification_decision_v1 import (
    MaskingPolicyDecisionEvidenceV1,
    POLICIES,
    POLICY_ORDER,
)
from .masking_qualification_decision_v2 import evaluate_policy_v2
from .masking_nonlinear_challenge_receipt_v1 import NonlinearChallengeReceiptV1

DECISION_RULE_ID = "NULL_NOISE_CALIBRATED_SHORTCUT_SUPPRESSION_WITH_NONLINEAR_COMPETENCE_V3"
POLICY_SELECTION_RULE_ID = "UNIFORM_IF_SUFFICIENT_ELSE_MIN_TARGETING_THEN_MAX_LOWER_BOUND_V1"


def _digest(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class MaskingPolicyDecisionReceiptV3:
    policy_id: str
    burden_numerator: int
    burden_denominator: int
    qualified: bool
    primary_v2_receipt_sha256: str
    nonlinear_competence_receipt_sha256: str
    mean_effective_targeted_n: float
    delta_lower_one_sided: float
    decision_rule_id: str = DECISION_RULE_ID

    def canonical_digest(self) -> str:
        return _digest({"schema": "V5_MASKING_POLICY_DECISION_RECEIPT_V3", **asdict(self)})


@dataclass(frozen=True)
class MaskingRungDecisionReceiptV3:
    burden_numerator: int
    burden_denominator: int
    qualified: bool
    selected_policy_id: str
    policy_receipt_sha256: Mapping[str, str]
    decision_rule_id: str = DECISION_RULE_ID
    policy_selection_rule_id: str = POLICY_SELECTION_RULE_ID

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

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({
            "schema": "V5_MASKING_RUNG_DECISION_RECEIPT_V3",
            **asdict(self),
            "policy_receipt_sha256": dict(sorted(self.policy_receipt_sha256.items())),
        })


def evaluate_policy_v3(
    evidence: MaskingPolicyDecisionEvidenceV1,
    nonlinear_receipt: NonlinearChallengeReceiptV1,
) -> MaskingPolicyDecisionReceiptV3:
    evidence.validate()
    nonlinear_receipt.validate()
    if nonlinear_receipt.policy_id != evidence.policy_id:
        raise ValueError("nonlinear receipt policy does not match primary evidence")
    if (
        nonlinear_receipt.burden_numerator,
        nonlinear_receipt.burden_denominator,
    ) != (
        evidence.burden_numerator,
        evidence.burden_denominator,
    ):
        raise ValueError("nonlinear receipt burden does not match primary evidence")
    primary = evaluate_policy_v2(evidence)
    qualified = primary.qualified and nonlinear_receipt.qualified
    return MaskingPolicyDecisionReceiptV3(
        policy_id=evidence.policy_id,
        burden_numerator=evidence.burden_numerator,
        burden_denominator=evidence.burden_denominator,
        qualified=qualified,
        primary_v2_receipt_sha256=primary.canonical_digest(),
        nonlinear_competence_receipt_sha256=nonlinear_receipt.canonical_digest(),
        mean_effective_targeted_n=float(primary.mean_effective_targeted_n),
        delta_lower_one_sided=float(primary.delta_lower_one_sided),
    )


def _select(receipts: Sequence[MaskingPolicyDecisionReceiptV3]) -> str:
    by_policy = {r.policy_id: r for r in receipts}
    if len(by_policy) != len(receipts) or set(by_policy) != set(POLICIES):
        raise ValueError("exactly one policy receipt is required for every arm")
    burdens = {(r.burden_numerator, r.burden_denominator) for r in receipts}
    if len(burdens) != 1:
        raise ValueError("all policy receipts must belong to one burden rung")
    if by_policy["UNIFORM_RANDOM"].qualified:
        return "UNIFORM_RANDOM"
    qualified = [r for r in receipts if r.policy_id != "UNIFORM_RANDOM" and r.qualified]
    if not qualified:
        return "NO_POLICY_QUALIFIED"
    qualified.sort(key=lambda r: (
        float(r.mean_effective_targeted_n),
        -float(r.delta_lower_one_sided),
        POLICY_ORDER[r.policy_id],
    ))
    return qualified[0].policy_id


def evaluate_rung_v3(
    evidence_by_policy: Sequence[MaskingPolicyDecisionEvidenceV1],
    nonlinear_receipts: Sequence[NonlinearChallengeReceiptV1],
) -> MaskingRungDecisionReceiptV3:
    if len(evidence_by_policy) != len(POLICIES) or len(nonlinear_receipts) != len(POLICIES):
        raise ValueError("rung V3 needs primary and nonlinear evidence for all four policies")
    nl = {r.policy_id: r for r in nonlinear_receipts}
    if set(nl) != set(POLICIES):
        raise ValueError("nonlinear receipts must cover every policy exactly once")
    receipts = [evaluate_policy_v3(e, nl[e.policy_id]) for e in evidence_by_policy]
    selected = _select(receipts)
    burdens = {(r.burden_numerator, r.burden_denominator) for r in receipts}
    num, den = next(iter(burdens))
    return MaskingRungDecisionReceiptV3(
        burden_numerator=num,
        burden_denominator=den,
        qualified=selected != "NO_POLICY_QUALIFIED",
        selected_policy_id=selected,
        policy_receipt_sha256={r.policy_id: r.canonical_digest() for r in receipts},
    )
