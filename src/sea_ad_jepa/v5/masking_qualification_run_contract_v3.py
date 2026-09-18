"""Prospective FULL104 masking run contract V3.

V3 extends the source-role separation from V2 and binds the successor
parameter, burden, precision and decision machinery.  It is intentionally
unable to authorize execution from placeholders or free status strings.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple

FREEZE_POLICY_ID = "FROZEN_BEFORE_QUALIFICATION_OUTCOMES_V1"
STRICT_SUPPORT_POLICY_ID = "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1"
TERMINAL_UNIVERSE_ID = "FULL_COMMON_CORE_17186_V1"
EXECUTION_SOURCE_ROLE_ID = "FULL104_STREAMING_EXECUTION_V1"
DECISION_RULE_ID = "NULL_LEVEL_SHORTCUT_SUPPRESSION_WITH_PAIRED_DONOR_TARGET_UNCERTAINTY_V1"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


@dataclass(frozen=True)
class MaskingQualificationRunContractV3:
    authority_id: str

    qualification_design_authority_sha256: str
    qualification_parameters_authority_sha256: str

    full104_block_manifest_sha256: str
    observation_state_sha256: str
    support_estimability_authority_sha256: str
    census_authority_sha256: str

    target_evidence_budget_template_sha256: str
    burden_ladder_authority_sha256: str

    outer_split_authority_sha256: str
    target_panel_authority_sha256: str
    precision_authority_sha256: str
    rng_replay_authority_sha256: str

    machine_worktree_checkpoint_sha256: str

    canonical_reference_source_sha256: str
    full104_streaming_execution_source_sha256: str
    precision_evaluator_source_sha256: str
    donor_evidence_source_sha256: str
    control_executor_source_sha256: str
    decision_evaluator_source_sha256: str
    anti_spillover_test_source_sha256: str

    execution_source_role_id: str
    decision_rule_id: str
    freeze_policy_id: str
    support_state_policy_id: str
    terminal_universe_id: str

    terminal_outcomes_inspected_before_freeze: bool = False
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def _roots(self) -> Tuple[Tuple[str, str], ...]:
        return (
            ("qualification_design_authority_sha256", self.qualification_design_authority_sha256),
            ("qualification_parameters_authority_sha256", self.qualification_parameters_authority_sha256),
            ("full104_block_manifest_sha256", self.full104_block_manifest_sha256),
            ("observation_state_sha256", self.observation_state_sha256),
            ("support_estimability_authority_sha256", self.support_estimability_authority_sha256),
            ("census_authority_sha256", self.census_authority_sha256),
            ("target_evidence_budget_template_sha256", self.target_evidence_budget_template_sha256),
            ("burden_ladder_authority_sha256", self.burden_ladder_authority_sha256),
            ("outer_split_authority_sha256", self.outer_split_authority_sha256),
            ("target_panel_authority_sha256", self.target_panel_authority_sha256),
            ("precision_authority_sha256", self.precision_authority_sha256),
            ("rng_replay_authority_sha256", self.rng_replay_authority_sha256),
            ("machine_worktree_checkpoint_sha256", self.machine_worktree_checkpoint_sha256),
            ("canonical_reference_source_sha256", self.canonical_reference_source_sha256),
            ("full104_streaming_execution_source_sha256", self.full104_streaming_execution_source_sha256),
            ("precision_evaluator_source_sha256", self.precision_evaluator_source_sha256),
            ("donor_evidence_source_sha256", self.donor_evidence_source_sha256),
            ("control_executor_source_sha256", self.control_executor_source_sha256),
            ("decision_evaluator_source_sha256", self.decision_evaluator_source_sha256),
            ("anti_spillover_test_source_sha256", self.anti_spillover_test_source_sha256),
        )

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        seen: dict[str, str] = {}
        for name, value in self._roots():
            digest = _sha(value, name)
            if digest in seen:
                raise ValueError(
                    f"run-contract roots must be role-distinct: {name} duplicates {seen[digest]}"
                )
            seen[digest] = name
        if self.execution_source_role_id != EXECUTION_SOURCE_ROLE_ID:
            raise ValueError("execution_source_role_id mismatch")
        if self.decision_rule_id != DECISION_RULE_ID:
            raise ValueError("decision_rule_id mismatch")
        if self.freeze_policy_id != FREEZE_POLICY_ID:
            raise ValueError("freeze_policy_id mismatch")
        if self.support_state_policy_id != STRICT_SUPPORT_POLICY_ID:
            raise ValueError("support_state_policy_id mismatch")
        if self.terminal_universe_id != TERMINAL_UNIVERSE_ID:
            raise ValueError("terminal_universe_id mismatch")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("run contract must freeze before terminal outcomes")
        if self.protected_outcomes_authorized is not False:
            raise ValueError("run contract cannot authorize protected outcomes")
        if self.training_authorized is not False:
            raise ValueError("run contract cannot authorize training")

    def bind_parameters(self, parameters: Any) -> None:
        self.validate()
        if _live_digest(parameters, "parameters") != self.qualification_parameters_authority_sha256:
            raise ValueError("parameters authority root mismatch")

    def bind_burden_ladder(self, ladder: Any) -> None:
        self.validate()
        if _live_digest(ladder, "burden ladder") != self.burden_ladder_authority_sha256:
            raise ValueError("burden ladder authority root mismatch")
        if getattr(ladder, "census_authority_sha256", None) != self.census_authority_sha256:
            raise ValueError("burden ladder is bound to a different census authority")

    def bind_precision(self, precision: Any) -> None:
        self.validate()
        if _live_digest(precision, "precision") != self.precision_authority_sha256:
            raise ValueError("precision authority root mismatch")

    def bind_execution_sources(
        self,
        *,
        canonical_reference_live_sha256: str,
        full104_streaming_execution_live_sha256: str,
        precision_evaluator_live_sha256: str,
        donor_evidence_live_sha256: str,
        control_executor_live_sha256: str,
        decision_evaluator_live_sha256: str,
        anti_spillover_test_live_sha256: str,
    ) -> None:
        self.validate()
        observed = {
            "canonical_reference_source_sha256": _sha(canonical_reference_live_sha256, "canonical_reference_live_sha256"),
            "full104_streaming_execution_source_sha256": _sha(full104_streaming_execution_live_sha256, "full104_streaming_execution_live_sha256"),
            "precision_evaluator_source_sha256": _sha(precision_evaluator_live_sha256, "precision_evaluator_live_sha256"),
            "donor_evidence_source_sha256": _sha(donor_evidence_live_sha256, "donor_evidence_live_sha256"),
            "control_executor_source_sha256": _sha(control_executor_live_sha256, "control_executor_live_sha256"),
            "decision_evaluator_source_sha256": _sha(decision_evaluator_live_sha256, "decision_evaluator_live_sha256"),
            "anti_spillover_test_source_sha256": _sha(anti_spillover_test_live_sha256, "anti_spillover_test_live_sha256"),
        }
        for field, live in observed.items():
            if getattr(self, field) != live:
                raise ValueError(f"{field} does not match its live source role")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_MASKING_QUALIFICATION_RUN_CONTRACT_V3", **asdict(self)})
