#!/usr/bin/env python3
"""Prospective count-noise vs rare-biology qualification contract; NO RNA/learning.

This pre-registration guard never reads a matrix, fits a distribution,
generates a synthetic world, opens outcomes, or grants scientific PASS.
"""
from __future__ import annotations

import copy
import json

SCHEMA = "DEV2048_V2_COUNT_NULL_AND_JOINT_REALISM_PREFREEZE_V1"
HOLD = "PREGENERATION_ONLY__NO_AUTHENTICATED_REAL_MATCH__NO_BIOLOGY_PASS"
AUTHORITY = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"

# G0-G6 are intentionally conjunctive. A zero-rate match cannot mask a
# covariance, donor, support-state, or technical-null failure.
REQUIRED_GATES = (
    "G0_AUTHENTICATED_TRAIN_ONLY_SOURCE_AND_RIGHTS",
    "G1_MATCHED_PHYSICAL_SUPPORT_COUNTS_AND_DEPTH",
    "G2_REAL_SYNTHETIC_MARGINAL_DISTRIBUTIONS",
    "G3_JOINT_GENE_CLASS_DONOR_AND_OPERATOR_REALISM",
    "G4_FROZEN_TECHNICAL_NULL_CALIBRATION",
    "G5_RARE_PROGRAM_DETECTION_AND_FALSE_POSITIVE_CONTROL",
    "G6_HELDOUT_DONOR_SOURCE_AND_INDEPENDENT_REVIEW",
)


def _frozen_manifest() -> dict[str, object]:
    """Immutable design requirements, not measurements or success claims."""
    return {
        "schema": SCHEMA,
        "status": HOLD,
        "authority": AUTHORITY,
        "purpose": [
            "synthetic controlled known truth for JEPA rare and perturbation evaluation",
            "realistic but non-identifying measured RNA count and covariance behavior",
            "separate rare coexpression from sequencing depth and count variability",
        ],
        "real_reference": {
            "only_authorized_train_donors": True,
            "issuer_and_access_rights_authenticated": False,
            "raw_umi_counts_available": False,
            "source_and_operator_matching_verified": False,
            "no_new_raw_real_rna_access": True,
        },
        "physical_support_states": [
            "MEASURED_ZERO",
            "STRUCTURALLY_UNMEASURED",
            "DETECTION_PROBABILITY",
            "COLLISION_UNRESOLVED",
            "RIGHTS_WITHHELD",
        ],
        "count_units": "RAW_UMI_WHEN_AUTHORIZED_ELSE_NOT_ESTIMABLE",
        "reject_log1p10k_as_integer_counts": True,
        "strata_required": [
            "source_operator", "donor", "cell_class", "library_depth",
            "gene_measured_support",
        ],
        "predeclared_comparison_metrics": [
            "measured_zero_point_mass", "library_size_distribution",
            "detected_gene_count_distribution", "per_gene_detection_rate",
            "per_gene_positive_count_tail", "per_gene_overdispersion",
            "signed_conditional_gene_covariance", "eigenspectrum",
            "class_and_within_class_topology", "donor_by_class_recurrence",
            "source_operator_transfer",
        ],
        "technical_null": {
            "baselines": [
                "depth_offset_poisson", "depth_offset_negative_binomial",
                "class_source_operator_conditional_count_null",
                "ordinary_coexpression_preserving_matched_null",
            ],
            "fit_only_on_rights_permitted_training_donors": True,
            "never_fit_to_candidate_rare_outcomes": True,
            "heldout_donor_predictive_calibration_required": True,
            "depth_matched_technical_pseudorarity_control_required": True,
        },
        "rare_program_check": {
            "signal": "multi_gene_conditional_tail_coactivity_not_single_gene_outlier",
            "separate_rare_from_perturbation": True,
            "cross_donor_recurrence_required": True,
            "independent_operator_source_recurrence_when_estimable": True,
            "matched_wrong_q_and_null_query_controls_required": True,
            "query_values_and_query_locus_atac_withheld_from_student": True,
            "familywise_or_fdr_rule_prefrozen_before_scores": True,
            "planted_truth_used_only_after_new_world_is_approved": True,
            "real_rare_biology_requires_separate_independent_validation": True,
        },
        "multiple_testing_rule": "TO_BE_PREFROZEN_WITH_INDEPENDENT_REVIEW",
        "numeric_acceptance_bands": "NOT_FROZEN__NO_DATA_PEEKING",
        "iteration_policy": {
            "finite_versions_and_heldout_separation_required": True,
            "no_tuning_to_heldout_real_or_rare_program_results": True,
            "no_automatic_promotion_after_one_metric_match": True,
        },
        "gates": {key: "NOT_ESTIMABLE__NO_APPROVED_EXECUTION" for key in REQUIRED_GATES},
        "world_generated": False,
        "real_data_evaluated": False,
        "distributions_fitted": False,
        "rare_program_test_executed": False,
        "scientifically_qualified": False,
        "generator_authorized": False,
        "model_trained": False,
    }


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("DEV2048_COUNT_NULL_PREFREEZE_REFUSAL:" + reason)


def validate_manifest(manifest: dict[str, object]) -> None:
    """Reject tampered gate/authority claims, even under python -O."""
    _require(type(manifest) is dict, "NOT_A_MANIFEST")
    _require(manifest.get("schema") == SCHEMA, "SCHEMA")
    _require(manifest.get("status") == HOLD, "PREMATURE_PASS")
    _require(manifest.get("authority") == AUTHORITY, "AUTHORITY")
    _require(type(manifest.get("gates")) is dict and
             list(manifest["gates"]) == list(REQUIRED_GATES), "MISSING_GATE")
    for key in REQUIRED_GATES:
        _require(manifest["gates"][key] ==
                 "NOT_ESTIMABLE__NO_APPROVED_EXECUTION", "PREMATURE_GATE_PASS")
    for key in ("world_generated", "real_data_evaluated", "distributions_fitted",
                "rare_program_test_executed", "scientifically_qualified",
                "generator_authorized", "model_trained"):
        _require(manifest.get(key) is False, "UNAUTHORIZED_EXECUTION:" + key)
    _require(manifest == _frozen_manifest(), "FROZEN_PREFREEZE_SPEC_MUTATED")


def frozen_manifest() -> dict[str, object]:
    result = _frozen_manifest()
    validate_manifest(result)
    return copy.deepcopy(result)


def main() -> None:
    print(json.dumps(frozen_manifest(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
