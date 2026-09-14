from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RECON_AUTHORITY_PATH = ROOT / "docs" / "agent" / "V5_FULL104_RECONNAISSANCE_AUTHORITY_V1.json"
FULL104 = "eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad"
HIST_FEATURE = "c9a6ede6f33a4a9d4ce22cde0f1a8c0fb5e7e039bac3df364325c778487329ef"
HIST_MULTIVIEW = "d6f70ee1bca777f3d2cbd89dd560395cc46ec25f6a648ae4ba0fd6e77c1c2cf1"


def _recon_receipt() -> dict[str, object]:
    return {
        "schema": "JEPA_V5_FULL104_RECONNAISSANCE_RECEIPT_V1",
        "full104_dimension_input_artifact_sha256": FULL104,
        "cells": 4_553_407,
        "donors": 104,
        "operators": 42,
        "addresses": 41_238,
        "diagnostics_completed": [
            "donor_operator_source_study_technology_counts",
            "depth_detection_distributions",
            "sparsity_zero_support_missingness",
            "feature_variance_covariance_conditioning",
            "effective_rank_redundancy",
            "view_overlap_redundancy",
            "donor_heterogeneity_leverage",
            "technical_variable_correlations",
            "cell_state_support_across_donors",
            "matched_null_stratum_size_singleton_rates",
            "matching_state_discreteness",
            "operator_source_dataset_variance_dominance",
            "control_estimability",
            "io_memory_parallelization_mechanics",
        ],
        "d_shared_outcomes_inspected": False,
        "rank_selection_inspected": False,
        "decision_bearing_effects_inspected": False,
        "pathology_used": False,
        "protected_data_used": False,
        "checkpoint_outcomes_used": False,
        "training_authorized": False,
        "terminal": "PASS_FULL104_OUTCOME_BLIND_RECONNAISSANCE_V1",
    }


def _feature_receipt() -> dict[str, object]:
    return {
        "schema": "JEPA_V5_FULL104_FEATURE_LINEAGE_RECEIPT_V1",
        "certification_classification": "CERTIFIABLE_EXACT_DERIVATION",
        "full104_dimension_input_artifact_sha256": FULL104,
        "source_feature_matrix_root_sha256": HIST_FEATURE,
        "source_multiview_root_sha256": HIST_MULTIVIEW,
        "certified_feature_matrix_root_sha256": HIST_FEATURE,
        "certified_multiview_root_sha256": HIST_MULTIVIEW,
        "producer_script_sha256": {"scripts/v4/derive_full104_phase2_shared_state.py": "1" * 64},
        "producer_commit_sha256": "2" * 40,
        "transformation_contract_sha256": "3" * 64,
        "row_identity_digest_sha256": "4" * 64,
        "address_identity_digest_sha256": "5" * 64,
        "cells": 4_553_407,
        "donors": 104,
        "operators": 42,
        "addresses": 41_238,
        "shapes": {
            "A_full": [4_553_407, 512],
            "B_full": [4_553_407, 512],
            "A_views": [4_553_407, 4, 512],
            "B_views": [4_553_407, 4, 512],
        },
        "row_identity_closed": True,
        "row_identity_mismatches": 0,
        "row_identity_missing": 0,
        "address_identity_closed": True,
        "address_identity_mismatches": 0,
        "a_b_view_partition_disjoint": True,
        "view_construction_reproduced": True,
        "filtering_applied": False,
        "cell_capping_applied": False,
        "sampling_applied": False,
        "clipping_applied": False,
        "winsorization_applied": False,
        "imputation_applied": False,
        "pathology_used": False,
        "protected_data_used": False,
        "checkpoint_outcomes_used": False,
        "adaptive_outcome_choice_used": False,
        "deterministic_reproduction_passed": True,
        "mechanics_repair_applied": False,
        "mechanics_repair_receipt_sha256": None,
        "semantic_transform_unchanged": True,
        "d_shared_outcomes_inspected": False,
        "d_shared_real_outcome_access_authorized": False,
        "training_authorized": False,
        "terminal": "PASS_FULL104_FEATURE_LINEAGE_V1",
    }


def test_reconnaissance_cannot_pass_without_hash_bound_diagnostic_evidence():
    m = importlib.import_module("sea_ad_jepa.v5.full104_reconnaissance_authority_v1")
    authority = json.loads(RECON_AUTHORITY_PATH.read_text(encoding="utf-8"))
    receipt = _recon_receipt()
    # A list saying diagnostics ran is not evidence. Every declared diagnostic must
    # have a bound digest and the complete evidence collection needs a root digest.
    with pytest.raises(m.Full104ReconnaissanceStop, match="EVIDENCE"):
        m.seal_full104_reconnaissance_receipt_v1(authority, receipt)


def test_feature_lineage_requires_donor_operator_identity_and_complete_transform_disclosure():
    m = importlib.import_module("sea_ad_jepa.v5.full104_feature_lineage_v1")
    receipt = _feature_receipt()
    # Row/address identity alone cannot prove donor/operator assignment, and a
    # transformation contract hash cannot substitute for explicit disclosure of
    # all potentially meaning-changing transforms.
    with pytest.raises(m.FeatureLineageStop, match="IDENTITY|TRANSFORM"):
        m.seal_full104_feature_lineage_v1(receipt)
