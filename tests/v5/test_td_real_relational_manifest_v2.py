from __future__ import annotations

import pytest

import scripts.v5.td_real_relational_manifest_v2 as R


def _pair(pair_id, a, b):
    return {
        "pair_id": pair_id,
        "member_address_ids": [a, b],
        "address_binding_state": "REPAIRED_41K_ADDRESS_BOUND",
    }


def _manifest():
    return {
        "schema": "JEPA_TD_REAL_RELATIONAL_MANIFEST_V2",
        "frozen": True,
        "candidate_id": "C2_RELATIONAL_SHARED",
        "relation_family": "SCALE_FREE_TRIPLET_ORDER",
        "scale_class": "GLOBAL_SCALE_FREE",
        "required_sources": ["HVS", "NPH52", "SEA_AD"],
        "lawful_views": [
            {"view_id": "VIEW_X", "pair_coordinates": [_pair("X1", "A1", "A2"), _pair("X2", "A3", "A4")]},
            {"view_id": "VIEW_Y", "pair_coordinates": [_pair("Y1", "B1", "B2"), _pair("Y2", "B3", "B4")]},
        ],
        "minimum_informative_pair_coordinates": 1,
        "relation_construction": {
            "object": "ANCHORED_CELL_TRIPLET_ORDER",
            "distance_formula": "TIE_AWARE_PAIR_ORDER_CONCORDANCE",
            "anchor_comparator_rule": "SAME_DONOR_SOURCE_OPERATOR_SUPPORT_STRATUM",
            "comparator_pair_order": "UNORDERED_CANONICAL_CELL_ID_ORDER",
            "relation_formula": "SIGN_D_IJ_MINUS_D_IK",
            "relation_identity": "ANCHOR_CELL_ID_PLUS_CANONICAL_COMPARATOR_CELL_IDS",
        },
        "null_permutation_unit": "RELATION_ID_WITHIN_DONOR_SOURCE_OPERATOR_SUPPORT_STRATUM",
        "support_semantics": {
            "measured_zero": "VALID_MEASUREMENT",
            "unresolved_or_unsupported": "ABSTAIN",
            "imputation": "FORBIDDEN",
        },
    }


def test_valid_manifest_freezes_anchored_cell_triplet_object():
    out = R.derive_relational_contract(_manifest())
    assert out["relation_construction"]["object"] == "ANCHORED_CELL_TRIPLET_ORDER"
    assert out["relation_construction"]["relation_formula"] == "SIGN_D_IJ_MINUS_D_IK"
    assert out["recurrence_statistic"] == "DONOR_MEAN_EXACT_TRIPLET_ORDER_AGREEMENT"
    assert out["recurrence_orientation"] == "LARGER_IS_BETTER"


def test_molecular_pair_coordinate_binds_exactly_two_repaired_addresses():
    m = _manifest(); m["lawful_views"][0]["pair_coordinates"][0]["member_address_ids"] = ["A1", "A2", "A3"]
    with pytest.raises(R.RelationalManifestError, match="exactly two"):
        R.derive_relational_contract(m)
    m = _manifest(); m["lawful_views"][0]["pair_coordinates"][0]["address_binding_state"] = "PRE_REPAIR_GENE_SYMBOL_ONLY"
    with pytest.raises(R.RelationalManifestError, match="REPAIRED_41K_ADDRESS_BOUND"):
        R.derive_relational_contract(m)


def test_views_must_be_molecularly_disjoint():
    m = _manifest(); m["lawful_views"][1]["pair_coordinates"][0]["member_address_ids"] = ["A1", "B2"]
    with pytest.raises(R.RelationalManifestError, match="disjoint"):
        R.derive_relational_contract(m)


def test_v1_three_address_relation_unit_semantics_are_rejected():
    m = _manifest(); m["relation_units"] = [{"relation_id":"R1","member_address_ids":["A","B","C"],"address_binding_state":"REPAIRED_41K_ADDRESS_BOUND"}]
    with pytest.raises(R.RelationalManifestError, match="fields"):
        R.derive_relational_contract(m)


def test_relation_object_cannot_be_changed_to_molecular_triplet():
    m = _manifest(); m["relation_construction"]["object"] = "THREE_MOLECULAR_ADDRESSES"
    with pytest.raises(R.RelationalManifestError, match="anchored cell triplet"):
        R.derive_relational_contract(m)


def test_null_preserves_operator_as_well_as_donor_source_support():
    m = _manifest(); m["null_permutation_unit"] = "RELATION_ID_WITHIN_DONOR_SOURCE_SUPPORT_STRATUM"
    with pytest.raises(R.RelationalManifestError, match="operator"):
        R.derive_relational_contract(m)


def test_minimum_informative_coordinate_count_is_positive_and_attainable_per_view():
    m = _manifest(); m["minimum_informative_pair_coordinates"] = 0
    with pytest.raises(R.RelationalManifestError, match="minimum_informative"):
        R.derive_relational_contract(m)
    m = _manifest(); m["minimum_informative_pair_coordinates"] = 3
    with pytest.raises(R.RelationalManifestError, match="exceeds"):
        R.derive_relational_contract(m)


def test_required_sources_and_scale_remain_closed():
    m = _manifest(); m["required_sources"] = ["HVS", "SEA_AD"]
    with pytest.raises(R.RelationalManifestError, match="HVS.*NPH52.*SEA_AD"):
        R.derive_relational_contract(m)
    m = _manifest(); m["scale_class"] = "NEAREST_THIRD_FINE_LOCAL"
    with pytest.raises(R.RelationalManifestError, match="fine locality"):
        R.derive_relational_contract(m)


def test_decision_law_requires_adverse_null_and_separate_same_metric_reference():
    out = R.derive_relational_contract(_manifest())
    assert out["adverse_null_summary_rule"] == "PER_DONOR_UPPER_QUANTILE_AT_EXTERNALLY_FROZEN_GATE_ALPHA"
    assert out["substantive_reference_rule"] == "SEPARATELY_QUALIFIED_SAME_METRIC_U_REFIT_REQUIRED"
    assert out["human_pass_authorized"] is False


def test_all_authority_remains_false():
    out = R.derive_relational_contract(_manifest())
    assert all(value is False for value in out["authority"].values())
