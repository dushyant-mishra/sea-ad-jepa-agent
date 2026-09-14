from __future__ import annotations

import importlib

import pytest

FULL104 = "eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad"
AUTH_V2 = "f9568eb19a22f106b0be3ce0580bc1058695ca1a2de6dd2d0475c3240a6bbda2"


def _m():
    return importlib.import_module("sea_ad_jepa.v5.d_shared_matching_state_resolution_v1")


def _receipt() -> dict[str, object]:
    return {
        "schema": "JEPA_V5_D_SHARED_MATCHING_STATE_RESOLUTION_RECEIPT_V1",
        "d_shared_authority_v2_sha256": AUTH_V2,
        "full104_dimension_input_artifact_sha256": FULL104,
        "resolution_classification": "LOSSLESS_DISCRETE_PREIMAGE_VERIFIED",
        "q_depth_source_semantics": "log1p(source_library)",
        "q_depth_discrete_state": "Q_DEPTH_COUNT=round(expm1(Q_DEPTH))",
        "q_depth_rows_checked": 4_553_407,
        "q_depth_reconstruction_mismatches": 0,
        "q_depth_integer_domain_valid": True,
        "q_detect_source_semantics": "nonzero/max(scalar_support_count,1)",
        "q_detect_discrete_state": "Q_DETECT_COUNT=round(Q_DETECT*max(SCALAR_SUPPORT_COUNT,1))",
        "q_detect_rows_checked": 4_553_407,
        "q_detect_reconstruction_mismatches": 0,
        "q_detect_integer_domain_valid": True,
        "support_measurability_redundant_with_operator": True,
        "support_measurability_operator_identity_sha256": "1" * 64,
        "effective_matching_tuple": ["donor", "operator", "Q_DEPTH_COUNT", "Q_DETECT_COUNT"],
        "arbitrary_binning_used": False,
        "bin_edges": None,
        "occupancy": {
            "cells_total": 4_553_407,
            "strata_total": 400_000,
            "cells_in_singleton_strata": 100_000,
            "strata_size_1": 100_000,
            "cells_in_size_2_3_strata": 250_000,
            "strata_size_2_3": 100_000,
            "cells_in_size_4_7_strata": 500_000,
            "strata_size_4_7": 100_000,
            "cells_in_size_ge_8_strata": 3_703_407,
            "strata_size_ge_8": 100_000,
            "stratum_size_min": 1,
            "stratum_size_median": 4.0,
            "stratum_size_p95": 100.0,
            "stratum_size_max": 1000,
        },
        "d_shared_outcomes_inspected": False,
        "rank_selection_inspected": False,
        "decision_bearing_effects_inspected": False,
        "training_authorized": False,
        "terminal": "PASS_D_SHARED_MATCHING_STATE_LOSSLESS_PREIMAGE_V1",
    }


def test_lossless_discrete_preimage_receipt_is_sealable_but_does_not_authorize_execution():
    m = _m()
    envelope = m.seal_d_shared_matching_state_resolution_v1(_receipt())
    payload = m.validate_d_shared_matching_state_resolution_v1(envelope)
    assert payload["resolution_classification"] == "LOSSLESS_DISCRETE_PREIMAGE_VERIFIED"
    assert payload["effective_matching_tuple"] == ["donor", "operator", "Q_DEPTH_COUNT", "Q_DETECT_COUNT"]
    assert payload["d_shared_real_outcome_access_authorized"] is False
    assert payload["training_authorized"] is False


def test_matching_state_resolution_rejects_arbitrary_bins_and_redundant_support_key():
    m = _m()
    bad = _receipt()
    bad["arbitrary_binning_used"] = True
    bad["bin_edges"] = {"Q_DEPTH": [0.0, 1.0], "Q_DETECT": [0.0, 1.0]}
    with pytest.raises(m.MatchingStateResolutionStop, match="BIN"):
        m.seal_d_shared_matching_state_resolution_v1(bad)

    bad = _receipt()
    bad["effective_matching_tuple"] = ["donor", "operator", "Q_DEPTH_COUNT", "Q_DETECT_COUNT", "support_measurability"]
    with pytest.raises(m.MatchingStateResolutionStop, match="REDUNDANT|TUPLE"):
        m.seal_d_shared_matching_state_resolution_v1(bad)


def test_matching_state_resolution_rejects_lossy_preimage_or_outcome_feedback():
    m = _m()
    bad = _receipt()
    bad["q_depth_reconstruction_mismatches"] = 1
    with pytest.raises(m.MatchingStateResolutionStop, match="Q_DEPTH"):
        m.seal_d_shared_matching_state_resolution_v1(bad)

    bad = _receipt()
    bad["q_detect_integer_domain_valid"] = False
    with pytest.raises(m.MatchingStateResolutionStop, match="Q_DETECT"):
        m.seal_d_shared_matching_state_resolution_v1(bad)

    bad = _receipt()
    bad["d_shared_outcomes_inspected"] = True
    with pytest.raises(m.MatchingStateResolutionStop, match="OUTCOME"):
        m.seal_d_shared_matching_state_resolution_v1(bad)


def test_matching_state_resolution_rejects_internally_inconsistent_stratum_occupancy():
    m = _m()
    bad = _receipt()
    bad["occupancy"]["strata_size_1"] = 99_999
    with pytest.raises(m.MatchingStateResolutionStop, match="OCCUPANCY"):
        m.seal_d_shared_matching_state_resolution_v1(bad)

    bad = _receipt()
    bad["occupancy"]["strata_size_2_3"] = 50_000
    with pytest.raises(m.MatchingStateResolutionStop, match="OCCUPANCY"):
        m.seal_d_shared_matching_state_resolution_v1(bad)

    bad = _receipt()
    bad["occupancy"]["strata_total"] = 399_999
    with pytest.raises(m.MatchingStateResolutionStop, match="OCCUPANCY"):
        m.seal_d_shared_matching_state_resolution_v1(bad)


def test_continuous_state_terminal_requires_v3_and_cannot_pass_as_lossless():
    m = _m()
    receipt = _receipt()
    receipt.update(
        {
            "resolution_classification": "CONTINUOUS_STATE_REQUIRES_V3_NULL",
            "q_depth_reconstruction_mismatches": 10,
            "q_detect_reconstruction_mismatches": 20,
            "terminal": "STOP_D_SHARED_CONTINUOUS_MATCHING_STATE_REQUIRES_V3_NULL",
        }
    )
    with pytest.raises(m.MatchingStateResolutionStop, match="V3_NULL"):
        m.seal_d_shared_matching_state_resolution_v1(receipt)
