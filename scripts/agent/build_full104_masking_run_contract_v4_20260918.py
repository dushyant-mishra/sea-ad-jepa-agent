#!/usr/bin/env python3
"""Build the final FULL104 MaskingQualificationRunContractV4 from live artifacts.

This builder accepts concrete artifact paths only. It does not accept caller-entered
role digests, does not inspect terminal masking outcomes, and cannot authorize
training. Historical artifacts may appear only behind current authorities that
explicitly re-authorize their limited role.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import fields
import hashlib
import json
from pathlib import Path
from typing import Any

from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha, sha256_file
from sea_ad_jepa.v5.full104_control_calibration_cache_evaluator_v1 import load_control_calibration_cache
from sea_ad_jepa.v5.masking_burden_ladder_authority_v2 import MaskingBurdenLadderAuthorityV2
from sea_ad_jepa.v5.masking_nonlinear_challenge_authority_v3 import NonlinearMaskingChallengeAuthorityV3
from sea_ad_jepa.v5.masking_qualification_design_authority_v2 import MaskingQualificationDesignAuthorityV2
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v3 import MaskingQualificationParametersAuthorityV3
from sea_ad_jepa.v5.masking_qualification_run_contract_v4 import (
    DECISION_RULE_ID,
    EXECUTION_SOURCE_ROLE_ID,
    FREEZE_POLICY_ID,
    STRICT_SUPPORT_POLICY_ID,
    TERMINAL_EXECUTION_INPUT_ROLE_ID,
    TERMINAL_UNIVERSE_ID,
    MaskingQualificationRunContractV4,
)
from sea_ad_jepa.v5.masking_rng_replay_authority_v2 import MaskingRngReplayAuthorityV2
from sea_ad_jepa.v5.nonlinear_capacity_model_authority_v1 import NonlinearCapacityModelAuthorityV1
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v2 import (
    NonlinearSamplingCalibrationPlanV2,
    NonlinearSamplingCalibrationReceiptV2,
)
from sea_ad_jepa.v5.outer_split_authority_v1 import OuterDonorSplitAuthorityV1
from sea_ad_jepa.v5.precision_authority_v4 import QualificationPrecisionAuthorityV4
from sea_ad_jepa.v5.control_calibration_precision_authority_v2 import ControlCalibrationPrecisionPlanV2
from sea_ad_jepa.v5.target_evidence_budget_template_authority_v1 import TargetEvidenceBudgetTemplateAuthorityV1
from sea_ad_jepa.v5.target_panel_authority_v3 import TargetPanelAuthorityV3
from sea_ad_jepa.v5.target_panel_selector_v2 import TargetPanelSelectionReceiptV2
from sea_ad_jepa.v5.target_panel_sizing_authority_v2 import (
    TargetPanelSizingPlanAuthorityV2,
    TargetPanelSizingReceiptV2,
)

EXPECTED_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_OBSERVATION_STATE_SHA256 = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256 = "cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08"

SOURCE_ROLES = {
    "canonical_reference_live_sha256": "src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py",
    "full104_streaming_execution_live_sha256": "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py",
    "target_panel_sizing_live_sha256": "src/sea_ad_jepa/v5/target_panel_sizing_authority_v2.py",
    "control_calibration_precision_live_sha256": "src/sea_ad_jepa/v5/control_calibration_precision_authority_v2.py",
    "control_capacity_calibration_live_sha256": "src/sea_ad_jepa/v5/control_capacity_calibration_receipt_v1.py",
    "control_calibration_cache_builder_live_sha256": "scripts/agent/build_full104_control_calibration_cache_v1.py",
    "control_calibration_cache_evaluator_live_sha256": "src/sea_ad_jepa/v5/full104_control_calibration_cache_evaluator_v1.py",
    "target_panel_authority_live_sha256": "src/sea_ad_jepa/v5/target_panel_authority_v3.py",
    "precision_evaluator_live_sha256": "src/sea_ad_jepa/v5/precision_authority_v4.py",
    "donor_evidence_live_sha256": "src/sea_ad_jepa/v5/masking_donor_evidence_v1.py",
    "control_executor_live_sha256": "src/sea_ad_jepa/v5/masking_control_executor_v1.py",
    "nonlinear_sampling_calibration_live_sha256": "src/sea_ad_jepa/v5/nonlinear_sampling_calibration_authority_v2.py",
    "nonlinear_authority_live_sha256": "src/sea_ad_jepa/v5/masking_nonlinear_challenge_authority_v3.py",
    "nonlinear_executor_live_sha256": "src/sea_ad_jepa/v5/masking_nonlinear_challenge_executor_v1.py",
    "decision_evaluator_live_sha256": "src/sea_ad_jepa/v5/masking_qualification_decision_v2.py",
    "terminal_evidence_assembly_live_sha256": "src/sea_ad_jepa/v5/masking_terminal_evidence_assembly_v1.py",
    "terminal_mechanical_controls_live_sha256": "src/sea_ad_jepa/v5/masking_terminal_mechanical_controls_v1.py",
    "terminal_one_rung_executor_live_sha256": "src/sea_ad_jepa/v5/masking_terminal_one_rung_executor_v1.py",
    "execution_authority_live_sha256": "src/sea_ad_jepa/v5/masking_qualification_execution_authority_v4.py",
    "anti_spillover_test_live_sha256": "tests/test_v5_full104_masking_anti_spillover_v2.py",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def semantic_sha256(payload: dict[str, Any]) -> str:
    semantic = copy.deepcopy(payload)
    semantic.pop("checkpoint_semantic_sha256", None)
    raw = json.dumps(
        semantic, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def typed(payload: dict[str, Any], cls: type, digest_field: str, *, conversions=None):
    names = {item.name for item in fields(cls)}
    missing = names - set(payload)
    if missing:
        raise SystemExit(f"{cls.__name__} missing fields: {sorted(missing)[:5]}")
    values = {name: payload[name] for name in names}
    if conversions is not None:
        values = conversions(values)
    obj = cls(**values)
    obj.validate()
    if payload.get(digest_field) != obj.canonical_digest():
        raise SystemExit(f"{cls.__name__} digest mismatch")
    return obj


def template_typed(payload: dict[str, Any]) -> TargetEvidenceBudgetTemplateAuthorityV1:
    if payload.get("schema") != "V5_TARGET_EVIDENCE_BUDGET_TEMPLATE_AUTHORITY_V1":
        raise SystemExit("target evidence-budget template V1 is required")
    names = {item.name for item in fields(TargetEvidenceBudgetTemplateAuthorityV1)}
    values = {name: payload[name] for name in names}
    values["excluded_observation_state_ids"] = tuple(values["excluded_observation_state_ids"])
    obj = TargetEvidenceBudgetTemplateAuthorityV1(**values)
    obj.validate()
    if payload.get("template_sha256") != obj.template_digest():
        raise SystemExit("target evidence-budget template digest mismatch")
    if payload.get("fraction_frozen_here") is not False:
        raise SystemExit("target evidence-budget template must remain burden-free")
    return obj


def sizing_receipt_typed(payload: dict[str, Any]) -> TargetPanelSizingReceiptV2:
    if payload.get("schema") != "V5_TARGET_PANEL_SIZING_RECEIPT_V2":
        raise SystemExit("target-panel sizing receipt V2 is required")
    obj = TargetPanelSizingReceiptV2(
        plan_authority_sha256=str(payload["plan_authority_sha256"]),
        selected_target_count=int(payload["selected_target_count"]),
        evaluated_counts=tuple(map(int, payload["evaluated_counts"])),
        verdict_digest_by_count={int(k): str(v) for k, v in payload["verdict_digest_by_count"].items()},
        real_masking_policy_outcomes_inspected=bool(payload.get("real_masking_policy_outcomes_inspected", False)),
        training_authorized=bool(payload.get("training_authorized", False)),
    )
    obj.validate()
    if payload.get("receipt_sha256") != obj.canonical_digest():
        raise SystemExit("target-panel sizing receipt digest mismatch")
    return obj


def nonlinear_receipt_typed(payload: dict[str, Any]) -> NonlinearSamplingCalibrationReceiptV2:
    if payload.get("schema") != "V5_NONLINEAR_SAMPLING_CALIBRATION_RECEIPT_V2":
        raise SystemExit("nonlinear sampling calibration receipt V2 is required")
    obj = NonlinearSamplingCalibrationReceiptV2(
        plan_authority_sha256=str(payload["plan_authority_sha256"]),
        calibration_cache_manifest_sha256=str(payload["calibration_cache_manifest_sha256"]),
        precision_authority_sha256=str(payload["precision_authority_sha256"]),
        model_capacity_authority_sha256=str(payload["model_capacity_authority_sha256"]),
        selected_max_cells_per_donor=int(payload["selected_max_cells_per_donor"]),
        evaluated_caps=tuple(map(int, payload["evaluated_caps"])),
        verdict_digest_by_cap={int(k): str(v) for k, v in payload["verdict_digest_by_cap"].items()},
        real_masking_policy_outcomes_inspected=bool(payload.get("real_masking_policy_outcomes_inspected", False)),
        training_authorized=bool(payload.get("training_authorized", False)),
    )
    obj.validate()
    if payload.get("receipt_sha256") != obj.canonical_digest():
        raise SystemExit("nonlinear sampling calibration receipt digest mismatch")
    return obj


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--support-authority", type=Path, required=True)
    p.add_argument("--parameters-authority", type=Path, required=True)
    p.add_argument("--census-authority", type=Path, required=True)
    p.add_argument("--cache-dir", type=Path, required=True)
    p.add_argument("--target-evidence-budget-template", type=Path, required=True)
    p.add_argument("--burden-ladder-authority", type=Path, required=True)
    p.add_argument("--outer-split-authority", type=Path, required=True)
    p.add_argument("--target-panel-sizing-plan", type=Path, required=True)
    p.add_argument("--control-calibration-precision-plan", type=Path, required=True)
    p.add_argument("--target-panel-sizing-receipt", type=Path, required=True)
    p.add_argument("--target-panel-authority", type=Path, required=True)
    p.add_argument("--target-selection-receipt", type=Path, required=True)
    p.add_argument("--precision-authority", type=Path, required=True)
    p.add_argument("--model-capacity-authority", type=Path, required=True)
    p.add_argument("--nonlinear-sampling-plan", type=Path, required=True)
    p.add_argument("--nonlinear-sampling-receipt", type=Path, required=True)
    p.add_argument("--nonlinear-authority", type=Path, required=True)
    p.add_argument("--rng-authority", type=Path, required=True)
    p.add_argument("--design-authority", type=Path, required=True)
    p.add_argument("--machine-checkpoint", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    support = load(args.support_authority)
    if canonical_sha(support) != EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256:
        raise SystemExit("support authority is not the exact current semantic authority")
    if support.get("schema") != "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1":
        raise SystemExit("support authority schema mismatch")
    support_sha = sha256_file(args.support_authority)
    if support.get("full104_substrate_sha256") != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("support authority binds a different FULL104 substrate")
    if support.get("training_authorized") is not False:
        raise SystemExit("support authority unexpectedly authorizes training")

    parameters_payload = load(args.parameters_authority)
    if parameters_payload.get("schema") != "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3":
        raise SystemExit("FULL104-bound masking parameter authority V3 is required")
    parameters = typed(parameters_payload, MaskingQualificationParametersAuthorityV3, "parameter_authority_sha256")

    census = load(args.census_authority)
    if census.get("schema") != "V5_FULL104_READONLY_CENSUS_AUTHORITY_V2":
        raise SystemExit("census authority V2 is required")
    census_semantic = dict(census)
    census_root = census_semantic.pop("census_authority_sha256", None)
    if census_root != canonical_sha(census_semantic):
        raise SystemExit("census authority digest mismatch")
    if census.get("training_authorized") is not False or census.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("census authority is not outcome-blind/training-off")
    substrate = census.get("substrate", {})
    if substrate.get("full104_block_manifest_sha256") != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("census authority binds a different FULL104 substrate")
    if substrate.get("operator_address_observation_state_sha256") != EXPECTED_OBSERVATION_STATE_SHA256:
        raise SystemExit("census authority binds a different observation state")
    if census.get("support_estimability_authority", {}).get("sha256") != support_sha:
        raise SystemExit("census authority binds a different support authority")

    cache = load_control_calibration_cache(args.cache_dir)
    cache.manifest.assert_calibration_only()
    if cache.manifest.census_authority_sha256 != census_root:
        raise SystemExit("calibration cache binds a different census authority")
    if cache.manifest.support_estimability_authority_sha256 != support_sha:
        raise SystemExit("calibration cache binds a different support authority")

    budget = template_typed(load(args.target_evidence_budget_template))
    burden = typed(load(args.burden_ladder_authority), MaskingBurdenLadderAuthorityV2, "authority_sha256")
    outer = typed(load(args.outer_split_authority), OuterDonorSplitAuthorityV1, "authority_sha256")

    sizing_plan_payload = load(args.target_panel_sizing_plan)
    if sizing_plan_payload.get("schema") != "V5_TARGET_PANEL_SIZING_PLAN_AUTHORITY_V2":
        raise SystemExit("target-panel sizing plan V2 is required")
    sizing_plan = typed(sizing_plan_payload, TargetPanelSizingPlanAuthorityV2, "authority_sha256")
    if sizing_plan.census_authority_sha256 != census_root:
        raise SystemExit("target-panel sizing plan binds a different census authority")

    precision_plan_payload = load(args.control_calibration_precision_plan)
    if precision_plan_payload.get("schema") != "V5_CONTROL_CALIBRATION_PRECISION_PLAN_V2":
        raise SystemExit("control-calibration precision plan V2 is required")
    precision_plan = typed(precision_plan_payload, ControlCalibrationPrecisionPlanV2, "authority_sha256")
    precision_plan.bind_calibration_cache(cache.manifest)

    sizing_receipt = sizing_receipt_typed(load(args.target_panel_sizing_receipt))
    panel = typed(load(args.target_panel_authority), TargetPanelAuthorityV3, "authority_sha256")
    selection_payload = load(args.target_selection_receipt)
    if selection_payload.get("schema") != "V5_TARGET_PANEL_SELECTION_RECEIPT_V2":
        raise SystemExit("target-panel selection receipt V2 is required")
    selection = typed(
        selection_payload,
        TargetPanelSelectionReceiptV2,
        "receipt_sha256",
        conversions=lambda values: {
            **values,
            "selected_target_cols": tuple(map(int, values["selected_target_cols"])),
        },
    )
    if panel.target_selection_receipt_sha256 != selection.canonical_digest():
        raise SystemExit("target panel binds a different target-selection receipt")
    if selection.target_count != panel.target_count:
        raise SystemExit("target-selection receipt count disagrees with final target panel")
    if selection.eligibility_receipt_sha256 != cache.manifest.target_eligibility_receipt_sha256:
        raise SystemExit("target-selection receipt binds a different eligibility receipt")
    if tuple(map(int, selection.selected_target_cols)) != tuple(map(int, cache.target_cols[: panel.target_count])):
        raise SystemExit("target-selection receipt does not match authenticated cache target prefix")
    precision = typed(load(args.precision_authority), QualificationPrecisionAuthorityV4, "authority_sha256")

    model = typed(
        load(args.model_capacity_authority),
        NonlinearCapacityModelAuthorityV1,
        "authority_sha256",
    )
    model.bind_primary_parameters(parameters)

    nonlinear_plan_payload = load(args.nonlinear_sampling_plan)
    if nonlinear_plan_payload.get("schema") != "V5_NONLINEAR_SAMPLING_CALIBRATION_PLAN_V2":
        raise SystemExit("nonlinear sampling calibration plan V2 is required")
    nonlinear_plan = typed(nonlinear_plan_payload, NonlinearSamplingCalibrationPlanV2, "authority_sha256")
    nonlinear_plan.bind_current_roots(
        panel=panel,
        precision=precision,
        outer_split=outer,
        parameters=parameters,
        model=model,
        cache_manifest=cache.manifest,
    )
    nonlinear_receipt = nonlinear_receipt_typed(load(args.nonlinear_sampling_receipt))
    if nonlinear_receipt.model_capacity_authority_sha256 != model.canonical_digest():
        raise SystemExit("nonlinear sampling receipt binds a different model-capacity authority")
    nonlinear = typed(load(args.nonlinear_authority), NonlinearMaskingChallengeAuthorityV3, "authority_sha256")
    rng = typed(load(args.rng_authority), MaskingRngReplayAuthorityV2, "authority_sha256")
    design = typed(load(args.design_authority), MaskingQualificationDesignAuthorityV2, "authority_sha256")

    checkpoint = load(args.machine_checkpoint)
    if checkpoint.get("schema") != "JEPA_WORK_CHECKPOINT_V1":
        raise SystemExit("machine checkpoint schema mismatch")
    checkpoint_root = str(checkpoint.get("checkpoint_semantic_sha256", ""))
    if checkpoint_root != semantic_sha256(checkpoint):
        raise SystemExit("machine checkpoint semantic digest mismatch")

    live_sources: dict[str, str] = {}
    for role, relative in SOURCE_ROLES.items():
        path = args.repo / relative
        if not path.is_file():
            raise SystemExit(f"missing live source role {role}: {path}")
        live_sources[role] = sha256_file(path)

    contract = MaskingQualificationRunContractV4(
        authority_id="JEPA_V5_FULL104_MASKING_QUALIFICATION_RUN_CONTRACT_V4",
        qualification_design_authority_sha256=design.canonical_digest(),
        qualification_parameters_authority_sha256=parameters.canonical_digest(),
        full104_block_manifest_sha256=EXPECTED_BLOCK_MANIFEST_SHA256,
        observation_state_sha256=EXPECTED_OBSERVATION_STATE_SHA256,
        support_estimability_authority_sha256=support_sha,
        census_authority_sha256=str(census_root),
        control_calibration_cache_manifest_sha256=cache.manifest_sha256,
        target_evidence_budget_template_sha256=budget.template_digest(),
        burden_ladder_authority_sha256=burden.canonical_digest(),
        outer_split_authority_sha256=outer.canonical_digest(),
        target_panel_sizing_plan_sha256=sizing_plan.canonical_digest(),
        control_calibration_precision_plan_sha256=precision_plan.canonical_digest(),
        target_panel_sizing_receipt_sha256=sizing_receipt.canonical_digest(),
        target_panel_authority_sha256=panel.canonical_digest(),
        precision_authority_sha256=precision.canonical_digest(),
        nonlinear_sampling_calibration_plan_sha256=nonlinear_plan.canonical_digest(),
        nonlinear_sampling_calibration_receipt_sha256=nonlinear_receipt.canonical_digest(),
        nonlinear_challenge_authority_sha256=nonlinear.canonical_digest(),
        rng_replay_authority_sha256=rng.canonical_digest(),
        machine_worktree_checkpoint_sha256=checkpoint_root,
        canonical_reference_source_sha256=live_sources["canonical_reference_live_sha256"],
        full104_streaming_execution_source_sha256=live_sources["full104_streaming_execution_live_sha256"],
        target_panel_sizing_source_sha256=live_sources["target_panel_sizing_live_sha256"],
        control_calibration_precision_source_sha256=live_sources["control_calibration_precision_live_sha256"],
        control_capacity_calibration_source_sha256=live_sources["control_capacity_calibration_live_sha256"],
        control_calibration_cache_builder_source_sha256=live_sources["control_calibration_cache_builder_live_sha256"],
        control_calibration_cache_evaluator_source_sha256=live_sources["control_calibration_cache_evaluator_live_sha256"],
        target_panel_authority_source_sha256=live_sources["target_panel_authority_live_sha256"],
        precision_evaluator_source_sha256=live_sources["precision_evaluator_live_sha256"],
        donor_evidence_source_sha256=live_sources["donor_evidence_live_sha256"],
        control_executor_source_sha256=live_sources["control_executor_live_sha256"],
        nonlinear_sampling_calibration_source_sha256=live_sources["nonlinear_sampling_calibration_live_sha256"],
        nonlinear_authority_source_sha256=live_sources["nonlinear_authority_live_sha256"],
        nonlinear_executor_source_sha256=live_sources["nonlinear_executor_live_sha256"],
        decision_evaluator_source_sha256=live_sources["decision_evaluator_live_sha256"],
        terminal_evidence_assembly_source_sha256=live_sources["terminal_evidence_assembly_live_sha256"],
        terminal_mechanical_controls_source_sha256=live_sources["terminal_mechanical_controls_live_sha256"],
        terminal_one_rung_executor_source_sha256=live_sources["terminal_one_rung_executor_live_sha256"],
        execution_authority_source_sha256=live_sources["execution_authority_live_sha256"],
        anti_spillover_test_source_sha256=live_sources["anti_spillover_test_live_sha256"],
        execution_source_role_id=EXECUTION_SOURCE_ROLE_ID,
        execution_input_role_id=TERMINAL_EXECUTION_INPUT_ROLE_ID,
        decision_rule_id=DECISION_RULE_ID,
        freeze_policy_id=FREEZE_POLICY_ID,
        support_state_policy_id=STRICT_SUPPORT_POLICY_ID,
        terminal_universe_id=TERMINAL_UNIVERSE_ID,
    )
    design.bind_live_authorities(
        target_evidence_budget_template=budget,
        burden_ladder=burden,
        precision=precision,
        outer_split=outer,
        target_panel=panel,
        rng_replay=rng,
    )

    contract.validate()
    contract.bind_machine_checkpoint_semantic(checkpoint)
    contract.bind_parameters(parameters)
    contract.bind_evidence_budget_template(budget)
    contract.bind_burden_ladder(burden)
    contract.bind_rng_replay(rng)
    contract.bind_design(design)
    contract.bind_control_calibration_provenance(cache.manifest, outer, sizing_plan)
    contract.bind_control_calibration_precision_plan(precision_plan, cache.manifest)
    contract.bind_target_panel(panel, sizing_plan, sizing_receipt)
    contract.bind_precision(precision)
    contract.bind_nonlinear(nonlinear, nonlinear_plan, nonlinear_receipt)
    contract.bind_execution_sources(**live_sources)
    contract.assert_terminal_execution_input_role(TERMINAL_EXECUTION_INPUT_ROLE_ID)

    payload = {
        "schema": "V5_MASKING_QUALIFICATION_RUN_CONTRACT_V4",
        **contract.__dict__,
        "run_contract_sha256": contract.canonical_digest(),
        "terminal_outcomes_inspected_before_freeze": False,
        "protected_outcomes_authorized": False,
        "training_authorized": False,
        "builder_policy": "PATH_ONLY_INPUTS__NO_CALLER_ENTERED_ROLE_DIGESTS__CURRENT_FULL104_ROOT_CLOSURE_V1",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(payload["run_contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
