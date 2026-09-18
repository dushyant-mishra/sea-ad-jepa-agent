"""Burden-free FULL104 target-evidence budget template.

This successor removes the need to instantiate a concrete burden merely to freeze
the prospective masking design. Its template_digest is intentionally compatible
with TargetEvidenceBudgetAuthorityV2.template_digest for the same non-fraction
fields. Concrete rung budgets are derived only from the frozen template plus a
lawful burden-ladder rung.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Tuple

MIN_RETAINED_POLICY_ID = "NO_ADDITIONAL_RETAINED_COUNT_FLOOR__FROZEN_BURDEN_LADDER_OWNS_MASK_FRACTION_V1"


from .target_evidence_budget_authority_v2 import (
    REQUIRED_EXCLUDED_OBSERVATION_STATE_IDS,
    TargetEvidenceBudgetAuthorityV2,
)


@dataclass(frozen=True)
class TargetEvidenceBudgetTemplateAuthorityV1:
    authority_id: str
    support_estimability_authority_sha256: str
    support_semantics_id: str
    census_authority_sha256: str
    full104_block_manifest_sha256: str
    observation_state_sha256: str
    terminal_universe_id: str
    budget_semantics_id: str
    eligibility_rule_id: str
    rounding_policy_id: str
    min_retained_non_target_address_count: int
    min_retained_policy_id: str
    infeasible_policy_id: str
    excluded_observation_state_ids: Tuple[str, ...] = REQUIRED_EXCLUDED_OBSERVATION_STATE_IDS
    measured_zero_is_measured_evidence: bool = True
    training_authorized: bool = False

    def _carrier(self) -> TargetEvidenceBudgetAuthorityV2:
        """Return a zero-burden carrier used only to reuse V2 validation/digest rules."""
        return TargetEvidenceBudgetAuthorityV2(
            authority_id=self.authority_id,
            support_estimability_authority_sha256=self.support_estimability_authority_sha256,
            support_semantics_id=self.support_semantics_id,
            census_authority_sha256=self.census_authority_sha256,
            full104_block_manifest_sha256=self.full104_block_manifest_sha256,
            observation_state_sha256=self.observation_state_sha256,
            terminal_universe_id=self.terminal_universe_id,
            budget_semantics_id=self.budget_semantics_id,
            eligibility_rule_id=self.eligibility_rule_id,
            rounding_policy_id=self.rounding_policy_id,
            mask_fraction_numerator=0,
            mask_fraction_denominator=1,
            min_retained_non_target_address_count=self.min_retained_non_target_address_count,
            infeasible_policy_id=self.infeasible_policy_id,
            excluded_observation_state_ids=tuple(self.excluded_observation_state_ids),
            measured_zero_is_measured_evidence=self.measured_zero_is_measured_evidence,
            training_authorized=self.training_authorized,
        )

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        self._carrier().validate()
        if self.min_retained_non_target_address_count != 0:
            raise ValueError("current FULL104 template forbids an additional retained-count floor")
        if self.min_retained_policy_id != MIN_RETAINED_POLICY_ID:
            raise ValueError("min_retained_policy_id mismatch")
        if self.training_authorized is not False:
            raise ValueError("target evidence-budget template cannot authorize training")

    def carrier_template_digest(self) -> str:
        """V2 non-fraction semantics digest used only to validate derived rung budgets."""
        self.validate()
        return self._carrier().template_digest()

    def template_digest(self) -> str:
        """Canonical FULL104 template digest including the explicit retained-floor policy."""
        self.validate()
        payload = dict(asdict(self))
        payload["excluded_observation_state_ids"] = list(self.excluded_observation_state_ids)
        raw = json.dumps(
            {"schema": "V5_TARGET_EVIDENCE_BUDGET_TEMPLATE_AUTHORITY_V1", **payload},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def canonical_digest(self) -> str:
        return self.template_digest()

    def with_fraction(self, numerator: int, denominator: int) -> TargetEvidenceBudgetAuthorityV2:
        self.validate()
        budget = TargetEvidenceBudgetAuthorityV2(
            authority_id=self.authority_id,
            support_estimability_authority_sha256=self.support_estimability_authority_sha256,
            support_semantics_id=self.support_semantics_id,
            census_authority_sha256=self.census_authority_sha256,
            full104_block_manifest_sha256=self.full104_block_manifest_sha256,
            observation_state_sha256=self.observation_state_sha256,
            terminal_universe_id=self.terminal_universe_id,
            budget_semantics_id=self.budget_semantics_id,
            eligibility_rule_id=self.eligibility_rule_id,
            rounding_policy_id=self.rounding_policy_id,
            mask_fraction_numerator=int(numerator),
            mask_fraction_denominator=int(denominator),
            min_retained_non_target_address_count=self.min_retained_non_target_address_count,
            infeasible_policy_id=self.infeasible_policy_id,
            excluded_observation_state_ids=tuple(self.excluded_observation_state_ids),
            measured_zero_is_measured_evidence=self.measured_zero_is_measured_evidence,
            training_authorized=False,
        )
        budget.validate()
        if budget.template_digest() != self.carrier_template_digest():
            raise ValueError("derived rung budget changed the frozen non-fraction budget semantics")
        return budget

    def as_payload(self) -> dict:
        self.validate()
        return {
            "schema": "V5_TARGET_EVIDENCE_BUDGET_TEMPLATE_AUTHORITY_V1",
            **asdict(self),
            "excluded_observation_state_ids": list(self.excluded_observation_state_ids),
            "template_sha256": self.template_digest(),
            "training_authorized": False,
        }
