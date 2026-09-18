#!/usr/bin/env python3
"""Build the prospectively frozen FULL104 masking preexecution authority pack.

This builder consumes only pre-terminal-outcome authorities/receipts. It creates
no masking result, selects no masking policy, opens no protected outcome and
cannot authorize training.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, fields
import json
from pathlib import Path
from typing import Any

import numpy as np

from sea_ad_jepa.v5.address_universe_ladder_authority_v1 import AddressUniverseLadderAuthorityV1
from sea_ad_jepa.v5.canonical_address_registry_authority_v1 import CanonicalAddressRegistryAuthorityV1
from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha, sha256_file
from sea_ad_jepa.v5.masking_burden_ladder_authority_v2 import MaskingBurdenLadderAuthorityV2
from sea_ad_jepa.v5.masking_nonlinear_challenge_authority_v2 import NonlinearMaskingChallengeAuthorityV2
from sea_ad_jepa.v5.masking_qualification_design_authority_v1 import (
    APPROVED_POLICY_ARMS, REQUIRED_CONTROLS,
)
from sea_ad_jepa.v5.masking_qualification_design_authority_v2 import MaskingQualificationDesignAuthorityV2
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v2 import MaskingQualificationParametersAuthorityV2
from sea_ad_jepa.v5.masking_rng_replay_authority_v2 import MaskingRngReplayAuthorityV2
from sea_ad_jepa.v5.masking_target_semantics_authority_v1 import (
    MaskingTargetSemanticsAuthorityV1, verify_target_construction_source,
)
from sea_ad_jepa.v5.outer_split_authority_v1 import OuterDonorSplitAuthorityV1
from sea_ad_jepa.v5.precision_authority_v4 import QualificationPrecisionAuthorityV4
from sea_ad_jepa.v5.primary_representation_authority_v1 import PrimaryRepresentationAuthorityV1
from sea_ad_jepa.v5.support_estimability_authority_v1 import SupportEstimabilityAuthorityV1
from sea_ad_jepa.v5.target_evidence_budget_authority_v2 import TargetEvidenceBudgetAuthorityV2
from sea_ad_jepa.v5.target_panel_authority_v2 import TargetPanelAuthorityV2
from sea_ad_jepa.v5.target_panel_selector_v2 import TargetPanelSelectionReceiptV2, select_target_cols
from sea_ad_jepa.v5.target_panel_sizing_authority_v1 import TargetPanelSizingAuthorityV1

FULL104_MANIFEST = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
OBSERVATION_STATE = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
EXPECTED_SOURCE_FOLD_COUNTS = (
    (11, 10, 10, 10),  # HVS
    (5, 4, 4, 4),      # NPH52
    (12, 12, 11, 11),  # SEA_AD
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dataclass_kwargs(cls: type, payload: dict[str, Any]) -> dict[str, Any]:
    names = {item.name for item in fields(cls)}
    return {name: payload[name] for name in names if name in payload}


def authority_payload(schema: str, obj: Any, digest_field: str = "authority_sha256") -> dict[str, Any]:
    obj.validate()
    payload = {"schema": schema, **asdict(obj), digest_field: obj.canonical_digest()}
    if hasattr(obj, "random_seed"):
        payload["random_seed"] = obj.random_seed
    if hasattr(obj, "global_seed"):
        payload["global_seed"] = obj.global_seed
    if hasattr(obj, "bootstrap_seed"):
        payload["bootstrap_seed"] = obj.bootstrap_seed
    return payload


def validate_receipt(payload: dict[str, Any], schema: str) -> str:
    if payload.get("schema") != schema:
        raise ValueError(f"receipt schema mismatch: expected {schema}")
    if payload.get("terminal_masking_outcomes_inspected") is not False:
        raise ValueError("terminal masking outcomes must remain unopened")
    declared = payload.get("receipt_sha256")
    semantic = dict(payload)
    semantic.pop("receipt_sha256", None)
    if declared != canonical_sha(semantic):
        raise ValueError(f"{schema} receipt digest mismatch")
    return str(declared)


def representation_from_json(payload: dict[str, Any]) -> PrimaryRepresentationAuthorityV1:
    if payload.get("schema") != "V5_PRIMARY_REPRESENTATION_AUTHORITY_V1":
        raise ValueError("representation schema mismatch")
    obj = PrimaryRepresentationAuthorityV1(**dataclass_kwargs(PrimaryRepresentationAuthorityV1, payload))
    obj.validate()
    return obj


def support_from_json(payload: dict[str, Any]) -> SupportEstimabilityAuthorityV1:
    if payload.get("schema") != "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1":
        raise ValueError("support schema mismatch")
    obj = SupportEstimabilityAuthorityV1(**dataclass_kwargs(SupportEstimabilityAuthorityV1, payload))
    obj.validate()
    return obj


def registry_from_json(payload: dict[str, Any]) -> CanonicalAddressRegistryAuthorityV1:
    if payload.get("schema") != "V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_V1":
        raise ValueError("canonical registry schema mismatch")
    obj = CanonicalAddressRegistryAuthorityV1(
        authority_id=payload["authority_id"],
        registry_sha256=payload["ADDRESS_REGISTRY"]["sha256"],
        registry_row_count=int(payload["ADDRESS_REGISTRY"]["row_count"]),
        full104_block_manifest_sha256=payload["FULL104_SUBSTRATE"]["sha256"],
        observation_state_sha256=payload["OPERATOR_ADDRESS_OBSERVATION_STATE"]["sha256"],
        recovery_provenance=payload["ADDRESS_REGISTRY"]["recovery_provenance"],
        informative_path=payload["ADDRESS_REGISTRY"].get("informative_path", ""),
        ordering_invariant=payload["ADDRESS_REGISTRY"]["ordering_invariant"],
        identifier_invariant=payload["ADDRESS_REGISTRY"]["identifier_invariant"],
    )
    obj.validate()
    if obj.canonical_digest() != payload.get("canonical_authority_digest"):
        raise ValueError("canonical registry authority digest mismatch")
    return obj


def parameter_from_json(payload: dict[str, Any]) -> MaskingQualificationParametersAuthorityV2:
    if payload.get("schema") != "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V2":
        raise ValueError("parameter authority schema mismatch")
    obj = MaskingQualificationParametersAuthorityV2(
        **dataclass_kwargs(MaskingQualificationParametersAuthorityV2, payload)
    )
    obj.validate()
    if obj.canonical_digest() != payload.get("parameter_authority_sha256"):
        raise ValueError("parameter authority digest mismatch")
    return obj


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--census-authority", type=Path, required=True)
    p.add_argument("--split-receipt", type=Path, required=True)
    p.add_argument("--target-eligibility", type=Path, required=True)
    p.add_argument("--representation-authority", type=Path, required=True)
    p.add_argument("--support-authority", type=Path, required=True)
    p.add_argument("--canonical-registry-authority", type=Path, required=True)
    p.add_argument("--parameter-authority", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    census = load_json(args.census_authority)
    split = load_json(args.split_receipt)
    eligibility = load_json(args.target_eligibility)
    representation = representation_from_json(load_json(args.representation_authority))
    support = support_from_json(load_json(args.support_authority))
    registry = registry_from_json(load_json(args.canonical_registry_authority))
    parameters = parameter_from_json(load_json(args.parameter_authority))

    if census.get("schema") != "V5_FULL104_READONLY_CENSUS_AUTHORITY_V2":
        raise SystemExit("census V2 authority is required")
    if census.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("census authority indicates terminal outcomes were inspected")
    census_sha = str(census.get("census_authority_sha256", ""))
    if len(census_sha) != 64:
        raise SystemExit("census authority digest is missing")

    split_receipt_sha = validate_receipt(
        split, "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1"
    )
    eligibility_sha = validate_receipt(
        eligibility, "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1"
    )
    if split.get("pass1_npz_sha256") != census["substrate"]["pass1_npz_sha256"]:
        raise SystemExit("split receipt is bound to a different census pass1 NPZ")
    if eligibility.get("pass1_npz_sha256") != census["substrate"]["pass1_npz_sha256"]:
        raise SystemExit("eligibility receipt is bound to a different census pass1 NPZ")
    if eligibility.get("split_receipt_sha256") != split_receipt_sha:
        raise SystemExit("target eligibility is bound to a different split receipt")

    if representation.substrate_authority_sha256 != FULL104_MANIFEST:
        raise SystemExit("representation authority is not bound to FULL104")
    if support.full104_substrate_sha256 != FULL104_MANIFEST:
        raise SystemExit("support authority is not bound to FULL104")
    if registry.full104_block_manifest_sha256 != FULL104_MANIFEST:
        raise SystemExit("canonical registry is not bound to FULL104")
    if registry.observation_state_sha256 != OBSERVATION_STATE:
        raise SystemExit("canonical registry observation-state root mismatch")

    representation_sha = representation.canonical_digest()
    support_sha = support.canonical_digest()
    registry_sha = registry.canonical_digest()

    donor_ids = list(split["donor_ids"])
    source_codes = list(map(int, split["donor_source_code"]))
    folds = list(map(int, split["fold_by_donor"]))
    source_names = list(split["source_names"])
    if len(donor_ids) != 104 or len(source_codes) != 104 or len(folds) != 104:
        raise SystemExit("split receipt does not contain exactly 104 donors")
    if len(set(donor_ids)) != 104:
        raise SystemExit("split receipt donor IDs are not unique")
    if split.get("fold_sizes") != [28, 26, 25, 25]:
        raise SystemExit("split fold sizes mismatch")
    observed_source_fold_counts = []
    for source_code in range(len(source_names)):
        counts = tuple(
            sum(1 for sc, fold in zip(source_codes, folds) if sc == source_code and fold == k)
            for k in range(4)
        )
        observed_source_fold_counts.append(counts)
    if tuple(observed_source_fold_counts) != EXPECTED_SOURCE_FOLD_COUNTS:
        raise SystemExit(
            f"source-stratified fold counts mismatch: {observed_source_fold_counts!r}"
        )

    donor_registry_sha = canonical_sha({
        "schema": "V5_FULL104_DONOR_REGISTRY_RECEIPT_V1",
        "donor_ids": donor_ids,
        "donor_source_code": source_codes,
        "source_names": source_names,
    })
    fold_assignment_sha = canonical_sha({
        "schema": "V5_FULL104_DONOR_FOLD_ASSIGNMENT_V1",
        "donor_ids": donor_ids,
        "fold_by_donor": folds,
        "split_id": split["split_id"],
        "split_receipt_sha256": split_receipt_sha,
    })
    outer_split = OuterDonorSplitAuthorityV1(
        authority_id="JEPA_V5_FULL104_OUTER_DONOR_SPLIT_AUTHORITY_V1",
        full104_substrate_sha256=FULL104_MANIFEST,
        donor_registry_sha256=donor_registry_sha,
        fold_assignment_artifact_sha256=fold_assignment_sha,
        split_semantics_id="OUTER_HELD_DONOR_EVALUATION_V1",
        screening_scope_policy_id="SCREEN_AND_FIT_ON_OUTER_TRAIN_DONORS_ONLY_V1",
        heldout_scope_policy_id="HELDOUT_DONORS_EVALUATION_ONLY_V1",
        n_folds=4,
        n_donors=104,
    )
    outer_split.validate()
    outer_split_sha = outer_split.canonical_digest()

    eligible_cols = tuple(map(int, eligibility["eligible_target_cols_all_folds"]))
    strict_core = tuple(map(int, eligibility["strict_core_cols"]))
    if len(eligible_cols) != 17053 or len(strict_core) != 17186:
        raise SystemExit("target eligibility/core cardinality mismatch")

    sizing = TargetPanelSizingAuthorityV1(
        authority_id="JEPA_V5_FULL104_TARGET_PANEL_SIZING_AUTHORITY_V1",
        census_authority_sha256=census_sha,
        target_eligibility_receipt_sha256=eligibility_sha,
        sizing_rule_id="NEXT_POWER_OF_TWO_AT_LEAST_FULL104_DONOR_COUNT_V1",
        independent_donor_count=104,
        eligible_target_count=17053,
        target_count=128,
    )
    sizing.validate()
    sizing_sha = sizing.canonical_digest()

    selected = select_target_cols(
        eligible_cols,
        target_count=sizing.target_count,
        eligibility_receipt_sha256=eligibility_sha,
    )
    selection = TargetPanelSelectionReceiptV2(
        eligibility_receipt_sha256=eligibility_sha,
        target_count=sizing.target_count,
        selected_target_cols=selected,
    )
    selection.validate()
    selection_sha = selection.canonical_digest()

    selector_source = args.repo / "src/sea_ad_jepa/v5/target_panel_selector_v2.py"
    panel = TargetPanelAuthorityV2(
        authority_id="JEPA_V5_FULL104_TARGET_PANEL_AUTHORITY_V2",
        full104_substrate_sha256=FULL104_MANIFEST,
        canonical_registry_authority_sha256=registry_sha,
        support_estimability_authority_sha256=support_sha,
        target_eligibility_receipt_sha256=eligibility_sha,
        target_panel_sizing_authority_sha256=sizing_sha,
        target_selection_receipt_sha256=selection_sha,
        selector_source_sha256=sha256_file(selector_source),
        support_state_policy_id="STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
        selection_policy_id="DETERMINISTIC_HASH_RANKED_ELIGIBLE_TARGET_PANEL_V2",
        outcome_firewall_policy_id="MASKING_QUALIFICATION_OUTCOME_NOT_USED_FOR_SELECTION_V1",
        target_count=128,
    )
    panel.bind_sizing_and_selection(sizing, selection)
    panel_sha = panel.canonical_digest()

    budget_template = TargetEvidenceBudgetAuthorityV2(
        authority_id="JEPA_V5_FULL104_TARGET_EVIDENCE_BUDGET_TEMPLATE_V2",
        support_estimability_authority_sha256=support_sha,
        support_semantics_id="STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
        census_authority_sha256=census_sha,
        full104_block_manifest_sha256=FULL104_MANIFEST,
        observation_state_sha256=OBSERVATION_STATE,
        terminal_universe_id="FULL_COMMON_CORE_17186_V1",
        budget_semantics_id="MASK_FRACTION_OF_STRICT_MEASURED_NON_TARGET_ADDRESSES_V1",
        eligibility_rule_id="VALUE_INDEPENDENT_ELIGIBILITY__MEASURED_ZERO_IS_MEASURED_EVIDENCE_V1",
        rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
        mask_fraction_numerator=1,
        mask_fraction_denominator=20,
        min_retained_non_target_address_count=0,
        infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
    )
    budget_template.validate()
    budget_template_sha = budget_template.template_digest()

    burden = MaskingBurdenLadderAuthorityV2(
        authority_id="JEPA_V5_FULL104_MASKING_BURDEN_LADDER_AUTHORITY_V2",
        census_authority_sha256=census_sha,
    )
    burden.validate()
    burden_sha = burden.canonical_digest()

    core_sha = canonical_sha({
        "schema": "V5_FULL104_STRICT_COMMON_CORE_COLS_V1",
        "strict_core_cols": list(strict_core),
    })
    universe = AddressUniverseLadderAuthorityV1(
        authority_id="JEPA_V5_FULL104_ADDRESS_UNIVERSE_LADDER_AUTHORITY_V1",
        canonical_registry_authority_sha256=registry_sha,
        support_estimability_authority_sha256=support_sha,
        ladder_artifact_sha256=eligibility_sha,
        ordered_universe_ids=("FULL_COMMON_CORE_17186_V1",),
        ordered_universe_sha256=(core_sha,),
        ordered_universe_sizes=(17186,),
        support_state_policy_id="STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
        terminal_policy_id="FULL_COMMON_CORE_MUST_BE_TERMINAL_V1",
    )
    universe.validate()
    universe_sha = universe.canonical_digest()

    primary32 = args.repo / "analysis/v5_masking_successor_spike_20260917/results/outer5200_32_unified_summary.csv"
    nonlinear32 = args.repo / "analysis/v5_masking_successor_spike_20260917/results/outer5200_nonlinear32_summary.csv"
    precision = QualificationPrecisionAuthorityV4(
        authority_id="JEPA_V5_FULL104_QUALIFICATION_PRECISION_AUTHORITY_V4",
        support_estimability_authority_sha256=support_sha,
        target_panel_authority_sha256=panel_sha,
        outer_split_authority_sha256=outer_split_sha,
        historical_primary32_summary_sha256=sha256_file(primary32),
        historical_nonlinear32_summary_sha256=sha256_file(nonlinear32),
    )
    precision.validate()
    precision_sha = precision.canonical_digest()

    rng = MaskingRngReplayAuthorityV2(
        authority_id="JEPA_V5_FULL104_MASKING_RNG_REPLAY_AUTHORITY_V2",
        canonical_registry_authority_sha256=registry_sha,
        outer_split_authority_sha256=outer_split_sha,
        target_panel_authority_sha256=panel_sha,
        burden_ladder_authority_sha256=burden_sha,
    )
    rng.validate()
    rng_sha = rng.canonical_digest()

    historical_nl_script = args.repo / "analysis/v5_masking_successor_spike_20260917/scripts/outer5200_nonlinear_probe32.py"
    nonlinear = NonlinearMaskingChallengeAuthorityV2(
        authority_id="JEPA_V5_FULL104_NONLINEAR_CHALLENGE_AUTHORITY_V2",
        primary_parameters_authority_sha256=parameters.canonical_digest(),
        outer_split_authority_sha256=outer_split_sha,
        target_panel_authority_sha256=panel_sha,
        historical_nonlinear_script_sha256=sha256_file(historical_nl_script),
        historical_nonlinear_summary_sha256=sha256_file(nonlinear32),
    )
    nonlinear.bind_primary_parameters(parameters)
    nonlinear_sha = nonlinear.canonical_digest()

    target_construction_source = args.repo / "src/sea_ad_jepa/v5/target_construction_authority_v1.py"
    target_semantics = MaskingTargetSemanticsAuthorityV1(
        authority_id="JEPA_V5_FULL104_MASKING_TARGET_SEMANTICS_AUTHORITY_V1",
        representation_authority_sha256=representation_sha,
        support_estimability_authority_sha256=support_sha,
        canonical_registry_authority_sha256=registry_sha,
        target_construction_authority_source_sha256=sha256_file(target_construction_source),
    )
    verify_target_construction_source(
        target_semantics, target_construction_source.read_text(encoding="utf-8")
    )
    target_semantics_sha = target_semantics.canonical_digest()

    runner_source = args.repo / "src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py"
    design = MaskingQualificationDesignAuthorityV2(
        authority_id="JEPA_V5_FULL104_MASKING_QUALIFICATION_DESIGN_AUTHORITY_V2",
        full104_substrate_sha256=FULL104_MANIFEST,
        representation_authority_sha256=representation_sha,
        support_estimability_authority_sha256=support_sha,
        canonical_registry_authority_sha256=registry_sha,
        masking_target_semantics_authority_sha256=target_semantics_sha,
        target_evidence_budget_template_sha256=budget_template_sha,
        precision_authority_sha256=precision_sha,
        outer_split_authority_sha256=outer_split_sha,
        target_panel_authority_sha256=panel_sha,
        address_universe_ladder_authority_sha256=universe_sha,
        rng_replay_authority_sha256=rng_sha,
        qualification_runner_source_sha256=sha256_file(runner_source),
        scientific_semantics_id="BIOLOGICAL_QUERY_LOCAL_STATE_NOT_SCALAR_EXPRESSION_V1",
        expression_attacker_role_id="ANTI_SHORTCUT_DIAGNOSTIC_ONLY_NOT_JEPA_LOSS_V1",
        policy_arms=APPROVED_POLICY_ARMS,
        primary_attacker_id="RIDGE_EXPRESSION_PROXY_ATTACKER_V1",
        primary_attacker_application_policy_id="SAME_PRIMARY_ATTACKER_AND_SCORE_FOR_ALL_POLICY_ARMS_V1",
        secondary_attacker_id="NONLINEAR_TREE_ENSEMBLE_EXPRESSION_PROXY_CHALLENGE_V1",
        primary_score_id="SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1",
        paired_estimand_id="UNIFORM_MINUS_TARGETED_SCORE_AT_TARGET_X_OUTER_FOLD_V1",
        controls=REQUIRED_CONTROLS,
        nonlinear_retuning_policy_id="NONLINEAR_REPORTED_WITHOUT_POLICY_RETUNING_V1",
        pooled_mean_guardrail_id="NO_HARMFUL_SIGN_REVERSAL_HIDDEN_BY_POOLED_MEAN_V1",
    )
    design.validate()
    design_sha = design.canonical_digest()

    pack = {
        "schema": "V5_FULL104_MASKING_PREEXECUTION_AUTHORITY_PACK_V1",
        "status": "PROSPECTIVE_AUTHORITIES_BOUND__TERMINAL_MASKING_OUTCOMES_UNOPENED__TRAINING_OFF",
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
        "roots": {
            "representation_authority_sha256": representation_sha,
            "support_estimability_authority_sha256": support_sha,
            "canonical_registry_authority_sha256": registry_sha,
            "census_authority_sha256": census_sha,
            "outer_split_authority_sha256": outer_split_sha,
            "target_panel_sizing_authority_sha256": sizing_sha,
            "target_selection_receipt_sha256": selection_sha,
            "target_panel_authority_sha256": panel_sha,
            "target_evidence_budget_template_sha256": budget_template_sha,
            "burden_ladder_authority_sha256": burden_sha,
            "address_universe_ladder_authority_sha256": universe_sha,
            "precision_authority_sha256": precision_sha,
            "rng_replay_authority_sha256": rng_sha,
            "masking_parameters_authority_sha256": parameters.canonical_digest(),
            "nonlinear_challenge_authority_sha256": nonlinear_sha,
            "masking_target_semantics_authority_sha256": target_semantics_sha,
            "masking_design_authority_sha256": design_sha,
        },
        "instances": {
            "outer_split": authority_payload("V5_OUTER_DONOR_SPLIT_AUTHORITY_V1", outer_split),
            "target_panel_sizing": authority_payload("V5_TARGET_PANEL_SIZING_AUTHORITY_V1", sizing),
            "target_selection": {
                "schema": "V5_TARGET_PANEL_SELECTION_RECEIPT_V2",
                **asdict(selection),
                "selected_target_cols": list(selection.selected_target_cols),
                "receipt_sha256": selection_sha,
                "selector_source_sha256": sha256_file(selector_source),
            },
            "target_panel": authority_payload("V5_TARGET_PANEL_AUTHORITY_V2", panel),
            "burden_ladder": authority_payload("V5_MASKING_BURDEN_LADDER_AUTHORITY_V2", burden),
            "address_universe_ladder": authority_payload("V5_ADDRESS_UNIVERSE_LADDER_AUTHORITY_V1", universe),
            "precision": authority_payload("V5_QUALIFICATION_PRECISION_AUTHORITY_V4", precision),
            "rng_replay": authority_payload("V5_MASKING_RNG_REPLAY_AUTHORITY_V2", rng),
            "nonlinear_challenge": authority_payload("V5_NONLINEAR_MASKING_CHALLENGE_AUTHORITY_V2", nonlinear),
            "masking_target_semantics": authority_payload("V5_MASKING_TARGET_SEMANTICS_AUTHORITY_V1", target_semantics),
            "masking_design": authority_payload("V5_MASKING_QUALIFICATION_DESIGN_AUTHORITY_V2", design),
            "budget_template": {
                "schema": "V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V2_TEMPLATE",
                "authority_id": budget_template.authority_id,
                "template_sha256": budget_template_sha,
                "support_estimability_authority_sha256": support_sha,
                "census_authority_sha256": census_sha,
                "full104_block_manifest_sha256": FULL104_MANIFEST,
                "observation_state_sha256": OBSERVATION_STATE,
                "terminal_universe_id": budget_template.terminal_universe_id,
                "budget_semantics_id": budget_template.budget_semantics_id,
                "eligibility_rule_id": budget_template.eligibility_rule_id,
                "rounding_policy_id": budget_template.rounding_policy_id,
                "min_retained_non_target_address_count": 0,
                "no_concrete_rung_selected": True,
                "training_authorized": False,
            },
        },
        "selected_target_cols": list(selected),
        "global_mask_seed": rng.global_seed,
        "precision_bootstrap_seed": precision.bootstrap_seed,
        "nonlinear_seed": nonlinear.random_seed,
    }
    pack["pack_sha256"] = canonical_sha(pack)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(pack["pack_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
