from __future__ import annotations

import importlib
import importlib.util

import pytest

MODULE = "sea_ad_jepa.v5.full104_feature_lineage_v1"
FULL104 = "eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad"
HIST_FEATURE = "c9a6ede6f33a4a9d4ce22cde0f1a8c0fb5e7e039bac3df364325c778487329ef"
HIST_MULTIVIEW = "d6f70ee1bca777f3d2cbd89dd560395cc46ec25f6a648ae4ba0fd6e77c1c2cf1"


def _module():
    spec = importlib.util.find_spec(MODULE)
    assert spec is not None, "FULL104 feature-lineage authority module must exist"
    return importlib.import_module(MODULE)


def _published_files():
    return {
        "A_full": "a" * 64,
        "B_full": "b" * 64,
        "A_views": "c" * 64,
        "B_views": "d" * 64,
        "physical_descriptors": "e" * 64,
        "ASSEMBLY_SEEN": "f" * 64,
        "rows": "0" * 64,
    }


def _receipt(classification="CERTIFIABLE_EXACT_DERIVATION"):
    repaired = classification == "CERTIFIABLE_WITH_MECHANICS_REPAIR_ONLY"
    return {
        "schema": "JEPA_V5_FULL104_FEATURE_LINEAGE_RECEIPT_V1",
        "certification_classification": classification,
        "full104_dimension_input_artifact_sha256": FULL104,
        "source_feature_matrix_root_sha256": HIST_FEATURE,
        "source_multiview_root_sha256": HIST_MULTIVIEW,
        "certified_feature_matrix_root_sha256": HIST_FEATURE,
        "certified_multiview_root_sha256": HIST_MULTIVIEW,
        "producer_script_sha256": {"scripts/v4/derive_full104_phase2_shared_state.py": "1" * 64},
        "producer_commit_sha256": "2" * 40,
        "transformation_contract_sha256": "3" * 64,
        "row_identity_digest_sha256": "4" * 64,
        "donor_identity_digest_sha256": "5" * 64,
        "operator_identity_digest_sha256": "6" * 64,
        "row_order_identity_digest_sha256": "7" * 64,
        "address_identity_digest_sha256": "8" * 64,
        "normalization_formula": "log1p(raw_count*10000/full_source_library)",
        "sketch_projection_semantics": "TWO_FROZEN_INDEPENDENT_SKETCHES_A_B",
        "visibility_channel_construction": "VALUE_AND_VISIBILITY_CHANNELS_256_PLUS_256",
        "view_count": 4,
        "visible_fraction": 0.60,
        "mask_fraction": 0.40,
        "pca_svd_feature_reduction_applied": False,
        "logical_name_to_content_sha256": _published_files(),
        "original_writer_replay_status": (
            "ORIGINAL_WRITER_HASH_UNRESOLVED__PUBLISHED_BYTES_AND_SEMANTICS_VERIFIED"
            if repaired
            else "EXACT_WRITER_REPLAY_VERIFIED"
        ),
        "location_identity_policy": "CONTENT_HASH_AND_LOGICAL_NAME_AUTHORITATIVE__ABSOLUTE_PATH_INFORMATIONAL_ONLY_V1",
        "historical_measurement_geometry_current_v5_authorized": False,
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
        "deterministic_reproduction_passed": not repaired,
        "mechanics_repair_applied": repaired,
        "mechanics_repair_receipt_sha256": ("9" * 64 if repaired else None),
        "semantic_transform_unchanged": True,
        "d_shared_outcomes_inspected": False,
        "d_shared_real_outcome_access_authorized": False,
        "training_authorized": False,
        "terminal": "PASS_FULL104_FEATURE_LINEAGE_V1",
    }


def test_exact_feature_lineage_round_trip_binds_full104_and_historical_roots():
    m = _module()
    envelope = m.seal_full104_feature_lineage_v1(_receipt())
    payload = m.validate_full104_feature_lineage_v1(envelope)
    assert payload["full104_dimension_input_artifact_sha256"] == FULL104
    assert payload["certified_feature_matrix_root_sha256"] == HIST_FEATURE
    assert payload["certified_multiview_root_sha256"] == HIST_MULTIVIEW
    assert payload["row_identity_closed"] is True and payload["address_identity_closed"] is True
    assert payload["historical_measurement_geometry_current_v5_authorized"] is False
    assert payload["d_shared_real_outcome_access_authorized"] is False


def test_feature_lineage_rejects_wrong_geometry_identity_or_shape():
    m = _module()
    for field, value in (("cells", 4_553_406), ("row_identity_mismatches", 1), ("address_identity_mismatches", 1)):
        bad = _receipt(); bad[field] = value
        with pytest.raises(m.FeatureLineageStop):
            m.seal_full104_feature_lineage_v1(bad)
    bad = _receipt(); bad["shapes"]["A_full"] = [4_553_407, 511]
    with pytest.raises(m.FeatureLineageStop, match="SHAPE"):
        m.seal_full104_feature_lineage_v1(bad)
    for field in ("donor_identity_digest_sha256", "operator_identity_digest_sha256", "row_order_identity_digest_sha256"):
        bad = _receipt(); bad.pop(field)
        with pytest.raises(m.FeatureLineageStop, match="IDENTITY"):
            m.seal_full104_feature_lineage_v1(bad)


def test_feature_lineage_rejects_capping_sampling_outcome_adaptation_or_nondeterminism():
    m = _module()
    for field in ("filtering_applied", "cell_capping_applied", "sampling_applied", "pathology_used", "protected_data_used", "checkpoint_outcomes_used", "adaptive_outcome_choice_used", "d_shared_outcomes_inspected"):
        bad = _receipt(); bad[field] = True
        with pytest.raises(m.FeatureLineageStop):
            m.seal_full104_feature_lineage_v1(bad)
    bad = _receipt(); bad["deterministic_reproduction_passed"] = False
    with pytest.raises(m.FeatureLineageStop, match="DETERMINISTIC"):
        m.seal_full104_feature_lineage_v1(bad)


def test_feature_lineage_rejects_incomplete_transform_disclosure_or_geometry_authorization():
    m = _module()
    for field in ("normalization_formula", "sketch_projection_semantics", "visibility_channel_construction"):
        bad = _receipt(); bad.pop(field)
        with pytest.raises(m.FeatureLineageStop, match="TRANSFORM"):
            m.seal_full104_feature_lineage_v1(bad)
    bad = _receipt(); bad["pca_svd_feature_reduction_applied"] = True
    with pytest.raises(m.FeatureLineageStop, match="TRANSFORM"):
        m.seal_full104_feature_lineage_v1(bad)
    bad = _receipt(); bad["historical_measurement_geometry_current_v5_authorized"] = True
    with pytest.raises(m.FeatureLineageStop, match="MEASUREMENT_GEOMETRY"):
        m.seal_full104_feature_lineage_v1(bad)


def test_historical_feature_lineage_rejects_frozen_geometry_or_transform_substitution():
    m = _module()
    bad = _receipt(); bad["visible_fraction"] = 0.50; bad["mask_fraction"] = 0.50
    with pytest.raises(m.FeatureLineageStop, match="TRANSFORM"):
        m.seal_full104_feature_lineage_v1(bad)
    for field in ("clipping_applied", "winsorization_applied", "imputation_applied"):
        bad = _receipt(); bad[field] = True
        with pytest.raises(m.FeatureLineageStop, match="TRANSFORM"):
            m.seal_full104_feature_lineage_v1(bad)


def test_feature_lineage_rejects_noncertifiable_derivation_and_root_substitution():
    m = _module()
    bad = _receipt("NOT_CERTIFIABLE_REBUILD_FROM_AUTHENTICATED_FULL104_REQUIRED")
    with pytest.raises(m.FeatureLineageStop, match="REBUILD_REQUIRED"):
        m.seal_full104_feature_lineage_v1(bad)
    bad = _receipt(); bad["source_feature_matrix_root_sha256"] = "7" * 64
    with pytest.raises(m.FeatureLineageStop, match="SOURCE_ROOT"):
        m.seal_full104_feature_lineage_v1(bad)


def test_mechanics_repair_classification_requires_explicit_repair_receipt_and_semantic_identity():
    m = _module()
    good = _receipt("CERTIFIABLE_WITH_MECHANICS_REPAIR_ONLY")
    payload = m.validate_full104_feature_lineage_v1(m.seal_full104_feature_lineage_v1(good))
    assert payload["mechanics_repair_applied"] is True
    assert payload["deterministic_reproduction_passed"] is False
    assert payload["certified_feature_matrix_root_sha256"] == HIST_FEATURE
    assert payload["certified_multiview_root_sha256"] == HIST_MULTIVIEW
    assert payload["original_writer_replay_status"] == "ORIGINAL_WRITER_HASH_UNRESOLVED__PUBLISHED_BYTES_AND_SEMANTICS_VERIFIED"
    bad = _receipt("CERTIFIABLE_WITH_MECHANICS_REPAIR_ONLY"); bad["mechanics_repair_receipt_sha256"] = None
    with pytest.raises(m.FeatureLineageStop, match="REPAIR_RECEIPT"):
        m.seal_full104_feature_lineage_v1(bad)
    bad = _receipt("CERTIFIABLE_WITH_MECHANICS_REPAIR_ONLY"); bad["semantic_transform_unchanged"] = False
    with pytest.raises(m.FeatureLineageStop, match="SEMANTIC_TRANSFORM"):
        m.seal_full104_feature_lineage_v1(bad)
    bad = _receipt("CERTIFIABLE_WITH_MECHANICS_REPAIR_ONLY"); bad["deterministic_reproduction_passed"] = True
    with pytest.raises(m.FeatureLineageStop, match="WRITER|DETERMINISTIC"):
        m.seal_full104_feature_lineage_v1(bad)
    for field in ("certified_feature_matrix_root_sha256", "certified_multiview_root_sha256"):
        bad = _receipt("CERTIFIABLE_WITH_MECHANICS_REPAIR_ONLY"); bad[field] = "a" * 64
        with pytest.raises(m.FeatureLineageStop, match="ROOT"):
            m.seal_full104_feature_lineage_v1(bad)
