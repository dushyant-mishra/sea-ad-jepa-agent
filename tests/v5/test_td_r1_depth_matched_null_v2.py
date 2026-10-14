from __future__ import annotations

import importlib.util

import pytest


def _load():
    name = "scripts.v5.td_r1_depth_matched_null_v2"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required repair module missing: {name}"
    import scripts.v5.td_r1_depth_matched_null_v2 as R
    return R


def test_technical_library_size_world_does_not_qualify_against_depth_matched_null():
    R = _load()
    out = R.qualify_depth_matched_r1_null(seed=777)
    tech = out["worlds"]["TECHNICAL_LIBRARY_SIZE_ONLY"]
    assert tech["donors_defeating_null"] == 0
    assert tech["status"] == "PASS_TECHNICAL_NEGATIVE"


def test_planted_relational_biology_remains_detectable_after_depth_matching():
    R = _load()
    out = R.qualify_depth_matched_r1_null(seed=777)
    bio = out["worlds"]["PLANTED_RELATIONAL_BIOLOGY"]
    assert bio["donors_defeating_null"] >= 7
    assert bio["status"] == "PASS_PLANTED_POSITIVE"


def test_clean_negative_does_not_defeat_null():
    R = _load()
    out = R.qualify_depth_matched_r1_null(seed=777)
    clean = out["worlds"]["CLEAN_NEGATIVE"]
    assert clean["donors_defeating_null"] == 0


def test_null_blocks_on_prospectively_frozen_depth_strata_without_promoting_unqualified_detection_matching():
    R = _load()
    contract = R.null_contract()
    assert contract["null_semantics"] == "WITHIN_DONOR_DEPTH_BLOCK_PERMUTATION"
    assert contract["depth_block_rule"] == "FROZEN_QUANTILE_BINS"
    assert contract["detection_block_rule"] == "DESCRIPTIVE_ONLY__NOT_YET_QUALIFIED_FOR_NULL_MATCHING"
    assert contract["source_operator_support_preserved"] is True
    assert contract["view_rule_digest_required"] is True
    assert contract["eligibility_rule_digest_required"] is True


def test_tie_tolerance_is_frozen_and_zero_ties_are_not_imputed():
    R = _load()
    contract = R.null_contract()
    assert contract["tie_tolerance"] == 0.0
    assert contract["tie_semantics"] == "EXACT_DISTANCE_TIE_RETAINED_AS_ZERO"
    assert contract["both_tie_is_informative_agreement"] is False


def test_view_contract_rejects_duplicate_reversed_or_overlapping_pairs():
    R = _load()
    with pytest.raises(R.R1DepthMatchedNullError, match="duplicate|reversed"):
        R.validate_view_pairs([(1, 2), (2, 1)], [(3, 4)])
    with pytest.raises(R.R1DepthMatchedNullError, match="disjoint"):
        R.validate_view_pairs([(1, 2)], [(2, 3)])
    good = R.validate_view_pairs([(1, 2), (3, 4)], [(5, 6), (7, 8)])
    assert good["view_x_pairs"] == 2
    assert good["view_y_pairs"] == 2


def test_donor_source_identity_is_not_pooled_and_required_sources_do_not_compensate():
    R = _load()
    rows = [
        {"donor_id":"D1", "source":"HVS", "status":"SUPPORTED", "delta":0.2},
        {"donor_id":"D1", "source":"SEA_AD", "status":"SUPPORTED", "delta":0.2},
    ]
    with pytest.raises(R.R1DepthMatchedNullError, match="donor.*source|source.*donor"):
        R.summarize_source_recurrence(rows, required_sources=["HVS","SEA_AD"])

    rows = [
        {"donor_id":"H1", "source":"HVS", "status":"SUPPORTED", "delta":0.2},
        {"donor_id":"S1", "source":"SEA_AD", "status":"UNSUPPORTED", "delta":None},
    ]
    out = R.summarize_source_recurrence(rows, required_sources=["HVS","SEA_AD"])
    assert out["source_status"]["SEA_AD"] == "NOT_ESTIMABLE"
    assert out["overall_status"] == "NOT_ESTIMABLE"


def test_unsupported_donors_are_reported_not_silently_dropped():
    R = _load()
    rows = [
        {"donor_id":"D1", "source":"SEA_AD", "status":"SUPPORTED", "delta":0.2},
        {"donor_id":"D2", "source":"SEA_AD", "status":"UNSUPPORTED", "delta":None},
    ]
    out = R.summarize_source_recurrence(rows, required_sources=["SEA_AD"])
    assert out["source_details"]["SEA_AD"]["total_donor_count"] == 2
    assert out["source_details"]["SEA_AD"]["supported_donor_count"] == 1
    assert out["source_details"]["SEA_AD"]["unsupported_donor_count"] == 1


def test_human_r1_authority_stays_closed_even_after_known_truth_null_qualification():
    R = _load()
    out = R.qualify_depth_matched_r1_null(seed=777)
    assert out["status"] == "PASS_R1_DEPTH_MATCHED_NULL_KNOWN_TRUTH"
    assert out["human_r1_adjudication_authorized"] is False
    assert all(v is False for v in out["authority"].values())
