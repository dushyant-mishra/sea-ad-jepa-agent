from __future__ import annotations

from dataclasses import replace

import pytest

from sea_ad_jepa.v5.address_universe_ladder_authority_v1 import AddressUniverseLadderAuthorityV1
from sea_ad_jepa.v5.anti_cheat_authority_bundle_v2 import AntiCheatAuthorityBundleV2
from sea_ad_jepa.v5.canonical_address_registry_authority_v1 import CanonicalAddressRegistryAuthorityV1
from sea_ad_jepa.v5.current_authority_closure_v2 import validate_current_v5_authority_closure_v2
from sea_ad_jepa.v5.current_authority_roots_v2 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2
from sea_ad_jepa.v5.current_masking_policy_authority_v2 import CurrentMaskingPolicyAuthorityV2
from sea_ad_jepa.v5.current_runtime_source_authority_v1 import CurrentRuntimeSourceAuthorityV1
from sea_ad_jepa.v5.current_target_address_provider_authority_v1 import (
    CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256,
    CurrentTargetAddressProviderAuthorityV1,
)
from sea_ad_jepa.v5.ema_timescale_authority_v2 import EmaTimescaleAuthorityV2
from sea_ad_jepa.v5.geometry_memorization_qualification_authority_v1 import (
    GeometryMemorizationQualificationAuthorityV1,
)
from sea_ad_jepa.v5.masking_qualification_design_authority_v1 import MaskingQualificationDesignAuthorityV1
from sea_ad_jepa.v5.masking_qualification_execution_authority_v1 import MaskingQualificationExecutionAuthorityV1
from sea_ad_jepa.v5.masking_qualification_execution_authority_v2 import MaskingQualificationExecutionAuthorityV2
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v1 import MaskingQualificationParametersAuthorityV1
from sea_ad_jepa.v5.masking_qualification_run_contract_v1 import MaskingQualificationRunContractV1
from sea_ad_jepa.v5.masking_rng_replay_authority_v1 import MaskingRngReplayAuthorityV1
from sea_ad_jepa.v5.measurement_robustness_authority_v2 import MeasurementRobustnessAuthorityV2
from sea_ad_jepa.v5.model_geometry_authority_v2 import ModelGeometryAuthorityV2
from sea_ad_jepa.v5.outer_split_authority_v1 import OuterDonorSplitAuthorityV1
from sea_ad_jepa.v5.precision_authority_v1 import QualificationPrecisionAuthorityV1
from sea_ad_jepa.v5.remaining_rna_execution_authority_v1 import RemainingRnaExecutionAuthorityV1
from sea_ad_jepa.v5.remaining_rna_necessity_v1 import RemainingRnaNecessityAuthorityV1
from sea_ad_jepa.v5.target_construction_authority_v1 import TargetConstructionAuthorityV1
from sea_ad_jepa.v5.target_evidence_budget_authority_v1 import TargetEvidenceBudgetAuthorityV1
from sea_ad_jepa.v5.target_identity_shortcut_gate_authority_v1 import TargetIdentityShortcutGateAuthorityV1
from sea_ad_jepa.v5.target_panel_authority_v1 import TargetPanelAuthorityV1
from sea_ad_jepa.v5.teacher_target_semantics_authority_v2 import TeacherTargetSemanticsAuthorityV2
from test_v5_current_authority_closure_v1 import Stub, fixtures, h


FULL = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
OBS = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
REGISTRY_RAW = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
STRICT_SCALAR = "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1"


def build_v2():
    old = fixtures()
    rep = old["rep"]
    support = old["support"]
    weight_law = old["weight_law"]
    est = old["est"]
    schedule = h("v2-schedule")
    firewall = h("v2-firewall")

    registry = CanonicalAddressRegistryAuthorityV1(
        authority_id="V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_20260916",
        registry_sha256=REGISTRY_RAW,
        registry_row_count=41238,
        full104_block_manifest_sha256=FULL,
        observation_state_sha256=OBS,
        recovery_provenance="stage81a2r foundation molecular address registry derivation; injectivity audit docs/history/results/v4/stage81a2r_foundation_molecular_address_injectivity_audit.json",
        informative_path="results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv",
    )
    assert registry.canonical_digest() == CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256

    address = CurrentTargetAddressProviderAuthorityV1(
        authority_id="JEPA_V5_CURRENT_TARGET_ADDRESS_PROVIDER_AUTHORITY_V1",
        address_registry_authority_sha256=registry.canonical_digest(),
        query_provider_id="V5_SHARED_ADDRESS_QUERY_PROVIDER_V1",
        query_artifact_sha256=h("v2-query-artifact"),
        replay_policy_id="FULL_PROVIDER_STATE_DETERMINISTIC_REPLAY_V1",
        parameter_sharing_policy_id="SHARED_TRAINABLE_ADDRESS_QUERY_MECHANISM_V1",
        gradient_policy_id="CONTEXT_EVIDENCE_TO_PREDICTION_GRADIENT_REACHABLE_V1",
    )
    budget = TargetEvidenceBudgetAuthorityV1(
        authority_id="JEPA_V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1",
        support_estimability_authority_sha256=support.canonical_digest(),
        budget_semantics_id="MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1",
        rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
        mask_fraction_numerator=1,
        mask_fraction_denominator=10,
        min_retained_non_target_rna_count=1,
        infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
    )
    precision = QualificationPrecisionAuthorityV1(
        authority_id="JEPA_V5_QUALIFICATION_PRECISION_AUTHORITY_V1",
        support_estimability_authority_sha256=support.canonical_digest(),
        uncertainty_method_id="TARGET_CLUSTERED_BOOTSTRAP_V1",
        confidence_level_numerator=95,
        confidence_level_denominator=100,
        bootstrap_replicates=1000,
        min_target_count=2,
        min_target_fold_unit_count=8,
        min_outer_fold_count=4,
        insufficient_support_policy_id="FAIL_CLOSED_IF_BELOW_PRECISION_V1",
    )
    split = OuterDonorSplitAuthorityV1(
        authority_id="JEPA_V5_OUTER_DONOR_SPLIT_AUTHORITY_V1",
        full104_substrate_sha256=FULL,
        donor_registry_sha256=h("v2-donor-registry"),
        fold_assignment_artifact_sha256=h("v2-folds"),
        split_semantics_id="OUTER_HELD_DONOR_EVALUATION_V1",
        screening_scope_policy_id="SCREEN_AND_FIT_ON_OUTER_TRAIN_DONORS_ONLY_V1",
        heldout_scope_policy_id="HELDOUT_DONORS_EVALUATION_ONLY_V1",
        n_folds=4,
        n_donors=104,
    )
    panel = TargetPanelAuthorityV1(
        authority_id="JEPA_V5_TARGET_PANEL_AUTHORITY_V1",
        full104_substrate_sha256=FULL,
        canonical_registry_authority_sha256=registry.canonical_digest(),
        support_estimability_authority_sha256=support.canonical_digest(),
        eligible_universe_authority_sha256=h("v2-eligible-universe"),
        selector_artifact_sha256=h("v2-selector"),
        target_list_artifact_sha256=h("v2-target-list"),
        support_state_policy_id=STRICT_SCALAR,
        selection_policy_id="DETERMINISTIC_OUTCOME_BLIND_TARGET_PANEL_V1",
        outcome_firewall_policy_id="MASKING_QUALIFICATION_OUTCOME_NOT_USED_FOR_SELECTION_V1",
        target_count=64,
    )
    ladder = AddressUniverseLadderAuthorityV1(
        authority_id="JEPA_V5_ADDRESS_UNIVERSE_LADDER_AUTHORITY_V1",
        canonical_registry_authority_sha256=registry.canonical_digest(),
        support_estimability_authority_sha256=support.canonical_digest(),
        ladder_artifact_sha256=h("v2-ladder"),
        ordered_universe_ids=("QUALIFICATION_800_V1", "QUALIFICATION_6000_V1", "FULL_COMMON_CORE_17186_V1"),
        ordered_universe_sha256=(h("v2-u800"), h("v2-u6000"), h("v2-u17186")),
        ordered_universe_sizes=(800, 6000, 17186),
        support_state_policy_id=STRICT_SCALAR,
        terminal_policy_id="FULL_COMMON_CORE_MUST_BE_TERMINAL_V1",
    )
    rng = MaskingRngReplayAuthorityV1(
        authority_id="JEPA_V5_MASKING_RNG_REPLAY_AUTHORITY_V1",
        canonical_registry_authority_sha256=registry.canonical_digest(),
        outer_split_authority_sha256=split.canonical_digest(),
        target_panel_authority_sha256=panel.canonical_digest(),
        seed_namespace_id="V5_COMMON_RANDOM_BASE_MASK_V1",
        method_exclusion_policy_id="MASK_POLICY_ID_ABSENT_FROM_BASE_MASK_SEED_V1",
        replay_policy_id="DETERMINISTIC_EXACT_MASK_REPLAY_V1",
        global_seed=17,
    )
    masking = CurrentMaskingPolicyAuthorityV2(
        authority_id="JEPA_V5_CURRENT_MASKING_POLICY_AUTHORITY_V2",
        canonical_registry_authority_sha256=registry.canonical_digest(),
        support_estimability_authority_sha256=support.canonical_digest(),
        shortcut_artifact_sha256=h("v2-shortcut-artifact"),
        masking_policy_id="V5_UNIFORM_PLUS_SHORTCUT_COMASK_V2",
        target_evidence_budget_authority_id="V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1",
        target_evidence_budget_authority_sha256=budget.canonical_digest(),
        rng_replay_authority_id="V5_DETERMINISTIC_MASK_REPLAY_AUTHORITY_V1",
        eligibility_policy_id="SUPPORT_ESTIMABILITY_AUTHORITY_ELIGIBILITY_V1",
        fallback_policy_id="DETERMINISTIC_UNIFORM_FALLBACK_V1",
        rng_replay_authority_sha256=rng.canonical_digest(),
    )
    necessity = RemainingRnaNecessityAuthorityV1(
        authority_id="JEPA_V5_REMAINING_RNA_NECESSITY_AUTHORITY_V1",
        representation_authority_sha256=rep.canonical_digest(),
        support_estimability_authority_sha256=support.canonical_digest(),
        target_address_provider_authority_sha256=address.canonical_digest(),
        masking_authority_sha256=masking.canonical_digest(),
        precision_authority_sha256=precision.canonical_digest(),
        protocol_id="KEEP_QUERY_IDENTITY_AND_LAWFUL_GLOBAL_CONTEXT_FIXED__ABLATE_REMAINING_RNA_V1",
        metric_id="QUERY_LOCAL_LATENT_STATE_COSINE_SIMILARITY_V1",
        min_median_advantage_numerator=1,
        min_median_advantage_denominator=100,
        min_win_fraction_numerator=1,
        min_win_fraction_denominator=2,
        identity_only_comparator_id="QUERY_IDENTITY_ONLY_V1",
        global_context_no_rna_comparator_id="QUERY_IDENTITY_PLUS_LAWFUL_GLOBAL_CONTEXT_NO_REMAINING_RNA_V1",
        failure_semantics_id="FAIL_CLOSED_IF_REMAINING_RNA_NOT_NECESSARY_V1",
    )
    construction = TargetConstructionAuthorityV1(
        authority_id="JEPA_V5_TARGET_CONSTRUCTION_AUTHORITY_V1",
        representation_authority_sha256=rep.canonical_digest(),
        support_estimability_authority_sha256=support.canonical_digest(),
        target_address_provider_authority_sha256=address.canonical_digest(),
        implementation_source_sha256=h("v2-target-construction-source"),
        query_identity_policy_id="QUERY_IDENTITY_SUPPLIED_V1",
        query_scalar_policy_id="QUERY_SCALAR_WITHHELD_BEFORE_CONTEXT_MIXING_V1",
        non_query_rna_policy_id="NON_QUERY_LAWFUL_RNA_VISIBLE_V1",
        global_context_policy_id="LAWFUL_GLOBAL_BIOLOGICAL_CONTEXT_ALLOWED_V1",
        teacher_gradient_policy_id="TEACHER_STOPGRAD_V1",
        scalar_expression_objective_policy_id="SCALAR_EXPRESSION_OBJECTIVE_ABSENT_V1",
        target_state_policy_id="QUERY_LOCAL_BIOLOGICAL_LATENT_STATE_V1",
    )
    ema = EmaTimescaleAuthorityV2(
        authority_id="JEPA_V5_EMA_TIMESCALE_AUTHORITY_V2",
        base_training_estimand_sha256=est.canonical_digest(),
        schedule_authority_sha256=schedule,
        momentum_function_id="PRESENTATION_HALF_LIFE_EXPONENTIAL_V1",
        presentation_unit_id="AUTHORIZED_SCIENTIFIC_PRESENTATIONS_V1",
        half_life_presentations=100,
    )
    teacher = TeacherTargetSemanticsAuthorityV2(
        authority_id="JEPA_V5_TEACHER_TARGET_SEMANTICS_AUTHORITY_V2",
        representation_authority_sha256=rep.canonical_digest(),
        support_estimability_authority_sha256=support.canonical_digest(),
        teacher_input_support_authority_sha256=h("v2-teacher-input-support"),
        target_address_query_authority_sha256=address.canonical_digest(),
        student_visible_support_authority_sha256=h("v2-student-visible-support"),
        scientific_weight_authority_sha256=est.canonical_digest(),
        masking_authority_sha256=masking.canonical_digest(),
        ema_boundary_authority_sha256=ema.canonical_digest(),
        target_construction_authority_sha256=construction.canonical_digest(),
        gradient_boundary_authority_sha256=h("v2-gradient-boundary"),
        remaining_rna_necessity_authority_sha256=necessity.canonical_digest(),
        state_semantics_id="BIOLOGICAL_CELLULAR_LATENT_STATE_V1",
        query_local_semantics_id="QUERY_LOCAL_STATE_CONDITIONED_ON_CANONICAL_ADDRESS_V1",
        scalar_expression_objective_policy_id="HIDDEN_GENE_SCALAR_RECONSTRUCTION_FORBIDDEN_V1",
        route_sufficiency_policy_id="REMAINING_RNA_REQUIRED__IDENTITY_ONLY_AND_GLOBAL_ONLY_INSUFFICIENT_V1",
    )
    design = MaskingQualificationDesignAuthorityV1(
        authority_id="JEPA_V5_MASKING_QUALIFICATION_DESIGN_AUTHORITY_V1",
        full104_substrate_sha256=FULL,
        representation_authority_sha256=rep.canonical_digest(),
        support_estimability_authority_sha256=support.canonical_digest(),
        canonical_registry_authority_sha256=registry.canonical_digest(),
        teacher_target_semantics_authority_sha256=teacher.canonical_digest(),
        target_evidence_budget_authority_sha256=budget.canonical_digest(),
        precision_authority_sha256=precision.canonical_digest(),
        outer_split_authority_sha256=split.canonical_digest(),
        target_panel_authority_sha256=panel.canonical_digest(),
        address_universe_ladder_authority_sha256=ladder.canonical_digest(),
        rng_replay_authority_sha256=rng.canonical_digest(),
        qualification_runner_source_sha256=h("v2-mask-runner-source"),
        scientific_semantics_id="BIOLOGICAL_QUERY_LOCAL_STATE_NOT_SCALAR_EXPRESSION_V1",
        expression_attacker_role_id="ANTI_SHORTCUT_DIAGNOSTIC_ONLY_NOT_JEPA_LOSS_V1",
        policy_arms=("UNIFORM_RANDOM", "TOP8_CORRELATION", "RIDGE8_CONDITIONAL", "PREFIX3_SELECTIVE"),
        primary_attacker_id="RIDGE_EXPRESSION_PROXY_ATTACKER_V1",
        primary_attacker_application_policy_id="SAME_PRIMARY_ATTACKER_AND_SCORE_FOR_ALL_POLICY_ARMS_V1",
        secondary_attacker_id="NONLINEAR_TREE_ENSEMBLE_EXPRESSION_PROXY_CHALLENGE_V1",
        primary_score_id="SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1",
        paired_estimand_id="UNIFORM_MINUS_TARGETED_SCORE_AT_TARGET_X_OUTER_FOLD_V1",
        controls=(
            "PLANTED_SHORTCUT_POSITIVE_CONTROL_V1",
            "WITHIN_DONOR_SHUFFLED_NEGATIVE_CONTROL_V1",
            "UNTREATED_MASK_IDENTITY_CONTROL_V1",
            "DETERMINISTIC_REPLAY_CONTROL_V1",
            "NO_PRIVILEGED_METADATA_CONTROL_V1",
        ),
        nonlinear_retuning_policy_id="NONLINEAR_REPORTED_WITHOUT_POLICY_RETUNING_V1",
        pooled_mean_guardrail_id="NO_HARMFUL_SIGN_REVERSAL_HIDDEN_BY_POOLED_MEAN_V1",
    )
    params = MaskingQualificationParametersAuthorityV1(
        authority_id="JEPA_V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V1",
        primary_attacker_id="RIDGE_EXPRESSION_PROXY_ATTACKER_V1",
        primary_score_id="SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1",
        targeted_partner_cap=8,
        ridge_candidate_pool_count=64,
        ridge_score_feature_count=32,
        ridge_alpha_numerator=1,
        ridge_alpha_denominator=100,
        prefix_inner_fold_count=3,
        prefix_candidate_count=20,
        prefix_floor_numerator=5,
        prefix_floor_denominator=100,
        prefix_reduction_numerator=1,
        prefix_reduction_denominator=2,
    )
    run_contract = MaskingQualificationRunContractV1(
        authority_id="JEPA_V5_MASKING_QUALIFICATION_RUN_CONTRACT_V1",
        qualification_design_authority_sha256=design.canonical_digest(),
        qualification_parameters_authority_sha256=params.canonical_digest(),
        runner_source_sha256=design.qualification_runner_source_sha256,
        freeze_policy_id="FROZEN_BEFORE_QUALIFICATION_OUTCOMES_V1",
        support_state_policy_id=STRICT_SCALAR,
    )
    mask_exec = MaskingQualificationExecutionAuthorityV2(
        authority_id="JEPA_V5_MASKING_QUALIFICATION_EXECUTION_AUTHORITY_V2",
        run_contract_authority_sha256=run_contract.canonical_digest(),
        result_artifact_sha256=h("v2-mask-result"),
        execution_status="EXECUTED_PASS",
        selected_policy_id="RIDGE8_CONDITIONAL",
        terminal_universe_status_id="FULL_COMMON_CORE_17186_EXECUTED_V1",
        controls_status_id="ALL_REQUIRED_CONTROLS_EXECUTED_PASS_V1",
        nonlinear_status_id="NONLINEAR_CHALLENGE_REPORTED_WITHOUT_RETUNING_V1",
        precision_status_id="BOUND_PRECISION_REQUIREMENTS_MET_V1",
    )
    rna_exec = RemainingRnaExecutionAuthorityV1(
        authority_id="JEPA_V5_REMAINING_RNA_EXECUTION_AUTHORITY_V1",
        remaining_rna_necessity_authority_sha256=necessity.canonical_digest(),
        precision_authority_sha256=precision.canonical_digest(),
        target_construction_authority_sha256=construction.canonical_digest(),
        target_panel_authority_sha256=panel.canonical_digest(),
        outer_split_authority_sha256=split.canonical_digest(),
        healthy_teacher_source_authority_sha256=h("v2-healthy-teacher-source"),
        result_artifact_sha256=h("v2-rna-result"),
        evidence_source_id="HEALTHY_CURRENT_V5_TEACHER_V1",
        execution_status="EXECUTED_PASS",
        state_metric_id="QUERY_LOCAL_LATENT_STATE_COSINE_SIMILARITY_V1",
        comparator_set_id="FULL_RNA__IDENTITY_ONLY__IDENTITY_PLUS_LAWFUL_GLOBAL_NO_RNA_V1",
    )
    measurement = MeasurementRobustnessAuthorityV2(
        authority_id="JEPA_V5_MEASUREMENT_ROBUSTNESS_AUTHORITY_V2",
        representation_authority_sha256=rep.canonical_digest(),
        teacher_target_semantics_sha256=teacher.canonical_digest(),
        precision_authority_sha256=precision.canonical_digest(),
        perturbation_protocol_authority_sha256=h("v2-measurement-perturbation"),
        stratification_guardrail_authority_sha256=h("v2-measurement-stratification"),
        execution_source_sha256=h("v2-measurement-source"),
        result_artifact_sha256=h("v2-measurement-result"),
        primary_metric_id="QUERY_LOCAL_LATENT_STATE_COSINE_STABILITY_V1",
        perturbation_semantics_id="SAME_CELL_MEASUREMENT_DEPTH_PERTURBATION_V1",
        failure_semantics_id="FAIL_CLOSED_ON_STATE_INSTABILITY_OR_INSUFFICIENT_PRECISION_V1",
        execution_status="EXECUTED_PASS",
    )
    identity = TargetIdentityShortcutGateAuthorityV1(
        authority_id="JEPA_V5_TARGET_IDENTITY_SHORTCUT_GATE_AUTHORITY_V1",
        teacher_target_semantics_sha256=teacher.canonical_digest(),
        representation_authority_sha256=rep.canonical_digest(),
        base_training_estimand_sha256=est.canonical_digest(),
        masking_authority_sha256=masking.canonical_digest(),
        comparator_ids=("IDENTITY_ONLY_V1", "NO_IDENTITY_V1"),
        null_reference_id="DONOR_DISTINCT_NULL_V1",
        primary_metric_id="QUERY_LOCAL_LATENT_STATE_MARGIN_V1",
        molecular_memory_margin_numerator=1,
        molecular_memory_margin_denominator=10,
        max_identity_contribution_numerator=1,
        max_identity_contribution_denominator=2,
        rare_address_guardrail_authority_sha256=h("v2-rare-address-guardrail"),
        shared_current_failure_semantics_id="FAIL_CLOSED_ON_TARGET_IDENTITY_SHORTCUT_V1",
    )
    critical = Stub("v2-critical")
    protected = Stub("v2-protected")
    geometry_artifact = h("v2-geometry-artifact")
    mem = GeometryMemorizationQualificationAuthorityV1(
        authority_id="JEPA_V5_GEOMETRY_MEMORIZATION_QUALIFICATION_AUTHORITY_V1",
        geometry_artifact_sha256=geometry_artifact,
        protected_registry_authority_sha256=protected.canonical_digest(),
        execution_source_sha256=h("v2-mem-source"),
        result_artifact_sha256=h("v2-mem-result"),
        qualification_protocol_id="CURRENT_GEOMETRY_MEMORIZATION_CAPACITY_PREDICATE_V1",
        execution_status="EXECUTED_PASS",
    )
    geometry = ModelGeometryAuthorityV2(
        authority_id="JEPA_V5_MODEL_GEOMETRY_AUTHORITY_V2",
        qualified_dimension_authority_sha256=h("v2-dimension-authority"),
        dimension_selection_artifact_sha256=h("v2-dimension-selection"),
        rank_to_geometry_rule_authority_sha256=h("v2-rank-rule-authority"),
        geometry_artifact_sha256=geometry_artifact,
        protected_registry_authority_sha256=protected.canonical_digest(),
        memorization_qualification_authority_sha256=mem.canonical_digest(),
        geometry_schema_id="DATA_DERIVED_JEPA_GEOMETRY_V2",
        rank_to_geometry_rule_id="FROZEN_DATA_DERIVED_RANK_TO_GEOMETRY_RULE_V1",
        memorization_policy_id="GEOMETRY_SPECIFIC_MEMORIZATION_QUALIFICATION_REQUIRED_V1",
    )
    runtime = CurrentRuntimeSourceAuthorityV1(
        authority_id="JEPA_V5_CURRENT_RUNTIME_SOURCE_AUTHORITY_V1",
        source_manifest_sha256=h("v2-runtime-manifest"),
        source_root_sha256=h("v2-runtime-root"),
        runtime_environment_artifact_sha256=h("v2-runtime-env"),
        entrypoint_source_sha256=h("v2-runtime-entrypoint"),
        source_packaging_policy_id="MULTIFILE_SOURCE_MANIFEST_AND_ROOT_V1",
        entrypoint_policy_id="CURRENT_V5_ENTRYPOINT_ONLY__NO_V4_PRODUCTION_UPDATE_V1",
        runtime_abi_id="CPYTHON_RUNTIME_ABI_EXACTLY_RECORDED_V1",
    )
    anti = AntiCheatAuthorityBundleV2(
        authority_id="JEPA_V5_ANTI_CHEAT_AUTHORITY_BUNDLE_V2",
        target_identity_gate_authority_sha256=identity.canonical_digest(),
        masking_authority_sha256=masking.canonical_digest(),
        masking_qualification_execution_authority_sha256=mask_exec.canonical_digest(),
        remaining_rna_execution_authority_sha256=rna_exec.canonical_digest(),
        measurement_robustness_authority_sha256=measurement.canonical_digest(),
        observation_gradient_firewall_authority_sha256=firewall,
        critical_test_authority_sha256=critical.canonical_digest(),
    )
    return locals()


def call_v2(f):
    return validate_current_v5_authority_closure_v2(
        full104_substrate_sha256=FULL,
        representation=f["rep"],
        support_estimability=f["support"],
        canonical_address_registry=f["registry"],
        base_training_weight_law=f["weight_law"],
        base_training_estimand=f["est"],
        target_address=f["address"],
        target_evidence_budget=f["budget"],
        precision=f["precision"],
        outer_split=f["split"],
        target_panel=f["panel"],
        address_universe_ladder=f["ladder"],
        masking_rng_replay=f["rng"],
        masking_qualification_design=f["design"],
        masking_qualification_parameters=f["params"],
        masking_qualification_run_contract=f["run_contract"],
        masking_qualification_execution=f["mask_exec"],
        masking=f["masking"],
        target_construction=f["construction"],
        remaining_rna_necessity=f["necessity"],
        remaining_rna_execution=f["rna_exec"],
        teacher_target=f["teacher"],
        schedule_authority_sha256=f["schedule"],
        ema=f["ema"],
        measurement_robustness=f["measurement"],
        target_identity_gate=f["identity"],
        anti_cheat=f["anti"],
        model_geometry=f["geometry"],
        geometry_memorization_qualification=f["mem"],
        protected_registry=f["protected"],
        critical_test=f["critical"],
        observation_gradient_firewall_authority_sha256=f["firewall"],
        runtime_source=f["runtime"],
    )


def test_complete_v2_graph_closes_with_exact_root_vocabulary() -> None:
    f = build_v2(); out = call_v2(f)
    assert tuple(out["authority_roots"]) == CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2
    assert out["training_authorized"] is False


@pytest.mark.parametrize("field", ["mask_exec", "rna_exec", "measurement", "mem"])
def test_any_failed_execution_blocks_v2_closure(field: str) -> None:
    f = build_v2()
    if field == "mask_exec":
        f[field] = replace(f[field], execution_status="EXECUTED_FAIL", selected_policy_id="NO_POLICY_QUALIFIED")
        f["anti"] = replace(f["anti"], masking_qualification_execution_authority_sha256=f[field].canonical_digest())
    elif field == "rna_exec":
        f[field] = replace(f[field], execution_status="EXECUTED_FAIL")
        f["anti"] = replace(f["anti"], remaining_rna_execution_authority_sha256=f[field].canonical_digest())
    elif field == "measurement":
        f[field] = replace(f[field], execution_status="EXECUTED_FAIL")
        f["anti"] = replace(f["anti"], measurement_robustness_authority_sha256=f[field].canonical_digest())
    else:
        f[field] = replace(f[field], execution_status="EXECUTED_FAIL")
        f["geometry"] = replace(f["geometry"], memorization_qualification_authority_sha256=f[field].canonical_digest())
    with pytest.raises(ValueError, match="EXECUTED_PASS"):
        call_v2(f)


def test_masking_budget_splice_is_rejected_at_top_level() -> None:
    f = build_v2()
    f["masking"] = replace(f["masking"], target_evidence_budget_authority_sha256=h("wrong-budget"))
    with pytest.raises(ValueError, match="target evidence budget authority root mismatch"):
        call_v2(f)


def test_geometry_memorization_must_match_selected_geometry_artifact() -> None:
    f = build_v2()
    f["mem"] = replace(f["mem"], geometry_artifact_sha256=h("wrong-geometry-artifact"))
    f["geometry"] = replace(f["geometry"], memorization_qualification_authority_sha256=f["mem"].canonical_digest())
    with pytest.raises(ValueError, match="geometry artifact root mismatch"):
        call_v2(f)


def test_legacy_masking_execution_v1_is_rejected() -> None:
    f = build_v2()
    legacy = MaskingQualificationExecutionAuthorityV1(
        authority_id="JEPA_V5_MASKING_QUALIFICATION_EXECUTION_AUTHORITY_V1",
        qualification_design_authority_sha256=f["design"].canonical_digest(),
        execution_source_sha256=h("legacy-mask-execution-source"),
        result_artifact_sha256=h("legacy-mask-result"),
        execution_status="EXECUTED_PASS",
        selected_policy_id="RIDGE8_CONDITIONAL",
        terminal_universe_status_id="FULL_COMMON_CORE_17186_EXECUTED_V1",
        controls_status_id="ALL_REQUIRED_CONTROLS_EXECUTED_PASS_V1",
        nonlinear_status_id="NONLINEAR_CHALLENGE_REPORTED_WITHOUT_RETUNING_V1",
        precision_status_id="BOUND_PRECISION_REQUIREMENTS_MET_V1",
    )
    f["mask_exec"] = legacy
    f["anti"] = replace(f["anti"], masking_qualification_execution_authority_sha256=legacy.canonical_digest())
    with pytest.raises(ValueError, match="MaskingQualificationExecutionAuthorityV2"):
        call_v2(f)
