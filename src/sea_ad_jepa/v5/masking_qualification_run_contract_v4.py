"""Final prospective FULL104 masking run contract V4.

V4 refuses provisional target-panel and nonlinear sampling authorities.  It
requires control-calibrated sizing/sampling receipts and their source roles in
addition to the V3 masking roots.  Terminal masking-policy outcomes must remain
unopened when this contract is frozen.
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
DECISION_RULE_ID = "NULL_NOISE_CALIBRATED_SHORTCUT_SUPPRESSION_WITH_PAIRED_DONOR_TARGET_UNCERTAINTY_V2"
EXPECTED_FULL104_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_OBSERVATION_STATE_SHA256 = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
TERMINAL_EXECUTION_INPUT_ROLE_ID = "AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1"
CALIBRATION_CACHE_ROLE_ID = "CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1"


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


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


@dataclass(frozen=True)
class MaskingQualificationRunContractV4:
    authority_id: str

    qualification_design_authority_sha256: str
    qualification_parameters_authority_sha256: str

    full104_block_manifest_sha256: str
    observation_state_sha256: str
    support_estimability_authority_sha256: str
    census_authority_sha256: str
    control_calibration_cache_manifest_sha256: str

    target_evidence_budget_template_sha256: str
    burden_ladder_authority_sha256: str

    outer_split_authority_sha256: str
    target_panel_sizing_plan_sha256: str
    control_calibration_precision_plan_sha256: str
    target_panel_sizing_receipt_sha256: str
    target_panel_authority_sha256: str
    precision_authority_sha256: str

    nonlinear_sampling_calibration_plan_sha256: str
    nonlinear_sampling_calibration_receipt_sha256: str
    nonlinear_challenge_authority_sha256: str
    rng_replay_authority_sha256: str

    machine_worktree_checkpoint_sha256: str

    canonical_reference_source_sha256: str
    full104_streaming_execution_source_sha256: str
    target_panel_sizing_source_sha256: str
    control_calibration_precision_source_sha256: str
    control_capacity_calibration_source_sha256: str
    control_calibration_cache_builder_source_sha256: str
    control_calibration_cache_evaluator_source_sha256: str
    target_panel_authority_source_sha256: str
    precision_evaluator_source_sha256: str
    donor_evidence_source_sha256: str
    control_executor_source_sha256: str
    nonlinear_sampling_calibration_source_sha256: str
    nonlinear_authority_source_sha256: str
    nonlinear_executor_source_sha256: str
    decision_evaluator_source_sha256: str
    execution_authority_source_sha256: str
    anti_spillover_test_source_sha256: str

    execution_source_role_id: str
    execution_input_role_id: str
    decision_rule_id: str
    freeze_policy_id: str
    support_state_policy_id: str
    terminal_universe_id: str

    terminal_outcomes_inspected_before_freeze: bool = False
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def _roots(self) -> Tuple[Tuple[str, str], ...]:
        names = (
            "qualification_design_authority_sha256",
            "qualification_parameters_authority_sha256",
            "full104_block_manifest_sha256",
            "observation_state_sha256",
            "support_estimability_authority_sha256",
            "census_authority_sha256",
            "control_calibration_cache_manifest_sha256",
            "target_evidence_budget_template_sha256",
            "burden_ladder_authority_sha256",
            "outer_split_authority_sha256",
            "target_panel_sizing_plan_sha256",
            "control_calibration_precision_plan_sha256",
            "target_panel_sizing_receipt_sha256",
            "target_panel_authority_sha256",
            "precision_authority_sha256",
            "nonlinear_sampling_calibration_plan_sha256",
            "nonlinear_sampling_calibration_receipt_sha256",
            "nonlinear_challenge_authority_sha256",
            "rng_replay_authority_sha256",
            "machine_worktree_checkpoint_sha256",
            "canonical_reference_source_sha256",
            "full104_streaming_execution_source_sha256",
            "target_panel_sizing_source_sha256",
            "control_calibration_precision_source_sha256",
            "control_capacity_calibration_source_sha256",
            "control_calibration_cache_builder_source_sha256",
            "control_calibration_cache_evaluator_source_sha256",
            "target_panel_authority_source_sha256",
            "precision_evaluator_source_sha256",
            "donor_evidence_source_sha256",
            "control_executor_source_sha256",
            "nonlinear_sampling_calibration_source_sha256",
            "nonlinear_authority_source_sha256",
            "nonlinear_executor_source_sha256",
            "decision_evaluator_source_sha256",
            "execution_authority_source_sha256",
            "anti_spillover_test_source_sha256",
        )
        return tuple((name, getattr(self, name)) for name in names)

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        seen: dict[str, str] = {}
        for name, value in self._roots():
            digest = _sha(value, name)
            if digest in seen:
                raise ValueError(f"run-contract roots must be role-distinct: {name} duplicates {seen[digest]}")
            seen[digest] = name
        if self.full104_block_manifest_sha256 != EXPECTED_FULL104_BLOCK_MANIFEST_SHA256:
            raise ValueError("terminal FULL104 block-manifest root mismatch")
        if self.observation_state_sha256 != EXPECTED_OBSERVATION_STATE_SHA256:
            raise ValueError("terminal observation-state root mismatch")
        if self.execution_source_role_id != EXECUTION_SOURCE_ROLE_ID:
            raise ValueError("execution_source_role_id mismatch")
        if self.execution_input_role_id != TERMINAL_EXECUTION_INPUT_ROLE_ID:
            raise ValueError("execution_input_role_id must require the authenticated FULL104 Level-4 stream")
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

    def assert_terminal_execution_input_role(self, runtime_role_id: str) -> None:
        self.validate()
        if runtime_role_id == CALIBRATION_CACHE_ROLE_ID:
            raise ValueError("calibration cache is forbidden as terminal masking qualification input")
        if runtime_role_id != TERMINAL_EXECUTION_INPUT_ROLE_ID:
            raise ValueError("terminal execution input role is not the authenticated FULL104 Level-4 stream")

    def bind_parameters(self, parameters: Any) -> None:
        self.validate()
        if _live_digest(parameters, "parameters") != self.qualification_parameters_authority_sha256:
            raise ValueError("parameters authority root mismatch")

    def bind_evidence_budget_template(self, budget_template: Any) -> None:
        self.validate()
        if getattr(budget_template, "training_authorized", False) is not False:
            raise ValueError("evidence-budget template unexpectedly authorizes training")
        budget_template.validate()
        if not hasattr(budget_template, "template_digest"):
            raise ValueError("final run contract requires a burden-free evidence-budget template")
        if _sha(budget_template.template_digest(), "budget template digest") != self.target_evidence_budget_template_sha256:
            raise ValueError("evidence-budget template root mismatch")
        if getattr(budget_template, "full104_block_manifest_sha256", None) != self.full104_block_manifest_sha256:
            raise ValueError("evidence-budget template binds a different FULL104 substrate")
        if getattr(budget_template, "observation_state_sha256", None) != self.observation_state_sha256:
            raise ValueError("evidence-budget template binds a different observation state")
        if getattr(budget_template, "support_estimability_authority_sha256", None) != self.support_estimability_authority_sha256:
            raise ValueError("evidence-budget template binds a different support authority")
        if getattr(budget_template, "census_authority_sha256", None) != self.census_authority_sha256:
            raise ValueError("evidence-budget template binds a different census authority")

    def bind_burden_ladder(self, ladder: Any) -> None:
        self.validate()
        if _live_digest(ladder, "burden ladder") != self.burden_ladder_authority_sha256:
            raise ValueError("burden-ladder authority root mismatch")
        if getattr(ladder, "census_authority_sha256", None) != self.census_authority_sha256:
            raise ValueError("burden ladder binds a different census authority")

    def bind_rng_replay(self, rng_replay: Any) -> None:
        self.validate()
        if _live_digest(rng_replay, "RNG replay") != self.rng_replay_authority_sha256:
            raise ValueError("RNG replay authority root mismatch")
        if getattr(rng_replay, "outer_split_authority_sha256", None) != self.outer_split_authority_sha256:
            raise ValueError("RNG replay binds a different outer split")
        if getattr(rng_replay, "target_panel_authority_sha256", None) != self.target_panel_authority_sha256:
            raise ValueError("RNG replay binds a different target panel")
        if getattr(rng_replay, "burden_ladder_authority_sha256", None) != self.burden_ladder_authority_sha256:
            raise ValueError("RNG replay binds a different burden ladder")

    def bind_design(self, design: Any) -> None:
        self.validate()
        if _live_digest(design, "qualification design") != self.qualification_design_authority_sha256:
            raise ValueError("qualification design authority root mismatch")
        if not hasattr(design, "target_evidence_budget_template_sha256"):
            raise ValueError("final run contract requires qualification DesignAuthorityV2 or later")
        if hasattr(design, "target_evidence_budget_authority_sha256"):
            raise ValueError("final design may not freeze one concrete evidence-budget burden")
        expected = {
            "full104_substrate_sha256": self.full104_block_manifest_sha256,
            "support_estimability_authority_sha256": self.support_estimability_authority_sha256,
            "target_evidence_budget_template_sha256": self.target_evidence_budget_template_sha256,
            "burden_ladder_authority_sha256": self.burden_ladder_authority_sha256,
            "precision_authority_sha256": self.precision_authority_sha256,
            "outer_split_authority_sha256": self.outer_split_authority_sha256,
            "target_panel_authority_sha256": self.target_panel_authority_sha256,
            "rng_replay_authority_sha256": self.rng_replay_authority_sha256,
        }
        for field, root in expected.items():
            if getattr(design, field, None) != root:
                raise ValueError(f"qualification design binds a different {field}")

    def bind_control_calibration_provenance(
        self,
        cache_manifest: Any,
        outer_split: Any,
        sizing_plan: Any,
    ) -> None:
        self.validate()
        if _live_digest(cache_manifest, "control calibration cache") != self.control_calibration_cache_manifest_sha256:
            raise ValueError("control calibration cache root mismatch")
        if getattr(cache_manifest, "cache_role_id", None) != CALIBRATION_CACHE_ROLE_ID:
            raise ValueError("control calibration cache role mismatch")
        if getattr(cache_manifest, "terminal_masking_qualification_authorized", None) is not False:
            raise ValueError("control calibration cache unexpectedly authorizes terminal masking")
        if getattr(cache_manifest, "full104_block_manifest_sha256", None) != self.full104_block_manifest_sha256:
            raise ValueError("control calibration cache is bound to a different FULL104 substrate")
        if getattr(cache_manifest, "census_authority_sha256", None) != self.census_authority_sha256:
            raise ValueError("control calibration cache is bound to a different census authority")
        if getattr(cache_manifest, "support_estimability_authority_sha256", None) != self.support_estimability_authority_sha256:
            raise ValueError("control calibration cache is bound to a different support authority")
        if _live_digest(outer_split, "outer split") != self.outer_split_authority_sha256:
            raise ValueError("outer split authority root mismatch")
        if getattr(outer_split, "full104_substrate_sha256", None) != self.full104_block_manifest_sha256:
            raise ValueError("outer split is bound to a different FULL104 substrate")
        if getattr(outer_split, "fold_assignment_artifact_sha256", None) != getattr(cache_manifest, "split_receipt_sha256", None):
            raise ValueError("calibration cache uses a different fold-assignment receipt")
        if _live_digest(sizing_plan, "target-panel sizing plan") != self.target_panel_sizing_plan_sha256:
            raise ValueError("target-panel sizing plan root mismatch")
        if getattr(sizing_plan, "target_eligibility_receipt_sha256", None) != getattr(cache_manifest, "target_eligibility_receipt_sha256", None):
            raise ValueError("calibration cache uses a different target-eligibility receipt")

    def bind_target_panel(self, panel: Any, sizing_plan: Any, sizing_receipt: Any) -> None:
        self.validate()
        if _live_digest(sizing_plan, "target-panel sizing plan") != self.target_panel_sizing_plan_sha256:
            raise ValueError("target-panel sizing plan root mismatch")
        if _live_digest(sizing_receipt, "target-panel sizing receipt") != self.target_panel_sizing_receipt_sha256:
            raise ValueError("target-panel sizing receipt root mismatch")
        if _live_digest(panel, "target panel") != self.target_panel_authority_sha256:
            raise ValueError("target-panel authority root mismatch")
        required = (
            "target_panel_sizing_plan_sha256",
            "target_panel_sizing_receipt_sha256",
        )
        for field in required:
            if not hasattr(panel, field):
                raise ValueError("final run contract requires control-calibrated TargetPanelAuthorityV3")
        if panel.target_panel_sizing_plan_sha256 != self.target_panel_sizing_plan_sha256:
            raise ValueError("target panel binds different sizing plan")
        if panel.target_panel_sizing_receipt_sha256 != self.target_panel_sizing_receipt_sha256:
            raise ValueError("target panel binds different sizing receipt")
        if sizing_receipt.selected_target_count != panel.target_count:
            raise ValueError("calibrated target count disagrees with target panel")

    def bind_precision(self, precision: Any) -> None:
        self.validate()
        if _live_digest(precision, "precision") != self.precision_authority_sha256:
            raise ValueError("precision authority root mismatch")
        if not hasattr(precision, "target_panel_sizing_receipt_sha256"):
            raise ValueError("final run contract requires precision authority V4 or later")
        if precision.target_panel_sizing_receipt_sha256 != self.target_panel_sizing_receipt_sha256:
            raise ValueError("precision authority binds different target sizing receipt")
        if precision.target_panel_authority_sha256 != self.target_panel_authority_sha256:
            raise ValueError("precision authority binds different target panel")

    def bind_nonlinear(self, nonlinear: Any, calibration_plan: Any, calibration_receipt: Any) -> None:
        self.validate()
        if _live_digest(calibration_plan, "nonlinear sampling calibration plan") != self.nonlinear_sampling_calibration_plan_sha256:
            raise ValueError("nonlinear sampling calibration plan root mismatch")
        required_plan_fields = (
            "target_panel_authority_sha256",
            "precision_authority_sha256",
            "outer_split_authority_sha256",
            "primary_parameters_authority_sha256",
            "model_capacity_authority_sha256",
            "calibration_cache_manifest_sha256",
            "calibration_evaluator_source_sha256",
        )
        if any(not hasattr(calibration_plan, field) for field in required_plan_fields):
            raise ValueError("final run contract requires nonlinear sampling calibration plan V2 or later")
        if calibration_plan.target_panel_authority_sha256 != self.target_panel_authority_sha256:
            raise ValueError("nonlinear calibration plan binds different target panel")
        if calibration_plan.precision_authority_sha256 != self.precision_authority_sha256:
            raise ValueError("nonlinear calibration plan binds different precision authority")
        if calibration_plan.outer_split_authority_sha256 != self.outer_split_authority_sha256:
            raise ValueError("nonlinear calibration plan binds different outer split")
        if calibration_plan.primary_parameters_authority_sha256 != self.qualification_parameters_authority_sha256:
            raise ValueError("nonlinear calibration plan binds different primary parameters")
        if calibration_plan.calibration_cache_manifest_sha256 != self.control_calibration_cache_manifest_sha256:
            raise ValueError("nonlinear calibration plan binds different calibration cache")
        if _live_digest(calibration_receipt, "nonlinear sampling calibration receipt") != self.nonlinear_sampling_calibration_receipt_sha256:
            raise ValueError("nonlinear sampling calibration receipt root mismatch")
        required_receipt_fields = (
            "calibration_cache_manifest_sha256",
            "precision_authority_sha256",
            "model_capacity_authority_sha256",
        )
        if any(not hasattr(calibration_receipt, field) for field in required_receipt_fields):
            raise ValueError("final run contract requires nonlinear sampling calibration receipt V2 or later")
        if calibration_receipt.calibration_cache_manifest_sha256 != self.control_calibration_cache_manifest_sha256:
            raise ValueError("nonlinear calibration receipt binds different calibration cache")
        if calibration_receipt.precision_authority_sha256 != self.precision_authority_sha256:
            raise ValueError("nonlinear calibration receipt binds different precision authority")
        if calibration_receipt.model_capacity_authority_sha256 != calibration_plan.model_capacity_authority_sha256:
            raise ValueError("nonlinear calibration receipt binds different model-capacity authority")
        if _live_digest(nonlinear, "nonlinear challenge") != self.nonlinear_challenge_authority_sha256:
            raise ValueError("nonlinear challenge authority root mismatch")
        if not hasattr(nonlinear, "sampling_calibration_receipt_sha256"):
            raise ValueError("final run contract requires nonlinear challenge authority V3 or later")
        if nonlinear.sampling_calibration_plan_sha256 != self.nonlinear_sampling_calibration_plan_sha256:
            raise ValueError("nonlinear authority binds different calibration plan")
        if nonlinear.sampling_calibration_receipt_sha256 != self.nonlinear_sampling_calibration_receipt_sha256:
            raise ValueError("nonlinear authority binds different calibration receipt")
        if nonlinear.target_panel_authority_sha256 != self.target_panel_authority_sha256:
            raise ValueError("nonlinear authority binds different target panel")
        if nonlinear.primary_parameters_authority_sha256 != self.qualification_parameters_authority_sha256:
            raise ValueError("nonlinear authority binds different primary parameters")
        if nonlinear.outer_split_authority_sha256 != self.outer_split_authority_sha256:
            raise ValueError("nonlinear authority binds different outer split")

    def bind_execution_sources(self, **live_sources: str) -> None:
        self.validate()
        expected = {
            "canonical_reference_source_sha256": "canonical_reference_live_sha256",
            "full104_streaming_execution_source_sha256": "full104_streaming_execution_live_sha256",
            "target_panel_sizing_source_sha256": "target_panel_sizing_live_sha256",
            "control_calibration_precision_source_sha256": "control_calibration_precision_live_sha256",
            "control_capacity_calibration_source_sha256": "control_capacity_calibration_live_sha256",
            "control_calibration_cache_builder_source_sha256": "control_calibration_cache_builder_live_sha256",
            "control_calibration_cache_evaluator_source_sha256": "control_calibration_cache_evaluator_live_sha256",
            "target_panel_authority_source_sha256": "target_panel_authority_live_sha256",
            "precision_evaluator_source_sha256": "precision_evaluator_live_sha256",
            "donor_evidence_source_sha256": "donor_evidence_live_sha256",
            "control_executor_source_sha256": "control_executor_live_sha256",
            "nonlinear_sampling_calibration_source_sha256": "nonlinear_sampling_calibration_live_sha256",
            "nonlinear_authority_source_sha256": "nonlinear_authority_live_sha256",
            "nonlinear_executor_source_sha256": "nonlinear_executor_live_sha256",
            "decision_evaluator_source_sha256": "decision_evaluator_live_sha256",
            "execution_authority_source_sha256": "execution_authority_live_sha256",
            "anti_spillover_test_source_sha256": "anti_spillover_test_live_sha256",
        }
        if set(live_sources) != set(expected.values()):
            raise ValueError("live source role set is incomplete or contains unknown roles")
        for field, arg in expected.items():
            live = _sha(live_sources[arg], arg)
            if getattr(self, field) != live:
                raise ValueError(f"{field} does not match its live source role")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema":"V5_MASKING_QUALIFICATION_RUN_CONTRACT_V4", **asdict(self)})
