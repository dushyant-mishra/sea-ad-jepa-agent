from __future__ import annotations

import importlib.util


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


def test_null_blocks_on_prospectively_frozen_depth_detection_strata():
    R = _load()
    contract = R.null_contract()
    assert contract["null_semantics"] == "WITHIN_DONOR_DEPTH_DETECTION_BLOCK_PERMUTATION"
    assert contract["depth_block_rule"] == "FROZEN_QUANTILE_BINS"
    assert contract["detection_block_rule"] == "FROZEN_DETECTED_ADDRESS_BIN"
    assert contract["source_operator_support_preserved"] is True
    assert contract["view_rule_digest_required"] is True


def test_tie_tolerance_is_frozen_and_zero_ties_are_not_imputed():
    R = _load()
    contract = R.null_contract()
    assert contract["tie_tolerance"] == 0.0
    assert contract["tie_semantics"] == "EXACT_DISTANCE_TIE_RETAINED_AS_ZERO"


def test_human_r1_authority_stays_closed_even_after_known_truth_null_qualification():
    R = _load()
    out = R.qualify_depth_matched_r1_null(seed=777)
    assert out["status"] == "PASS_R1_DEPTH_MATCHED_NULL_KNOWN_TRUTH"
    assert out["human_r1_adjudication_authorized"] is False
    assert all(v is False for v in out["authority"].values())
