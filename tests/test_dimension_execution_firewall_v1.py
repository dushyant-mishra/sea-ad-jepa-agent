import pytest

from sea_ad_jepa.v5.dimension_execution_firewall_v1 import (
    DimensionExecutionFirewallV1,
    DimensionExecutionStop,
)


def good():
    return {
        "population_mode": "FULL_READER_FIT_STREAM",
        "reader_fit_rows_used": 4553407,
        "unique_stable_keys_used": 4553407,
        "donors_used": 104,
        "operators_used": 42,
        "addresses": 41238,
        "expression_binding_terminal": "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE",
        "sampled_stratum_cap": None,
        "cells_per_stratum_cap": None,
        "row_cap": None,
        "full_null_geometry_refit": True,
        "null_geometry": "FULL_REFIT_EVERY_REPLICATE",
        "matched_null_preserves": ["donor", "operator", "Q_DEPTH", "Q_DETECT", "support_measurability"],
        "null_replicates_derived_from_error_budget": True,
        "donor_resamples_derived_from_error_budget": True,
        "null_replicates": 999,
        "donor_resamples": 1000,
        "final_authority_scripts": ["scripts/v5_anticheat/derive_full_stream_dimension_family_v1.py"],
        "synthetic_data_used": False,
        "pathology_used": False,
        "checkpoint_outcomes_used": False,
        "search_boundary_supported": False,
        "D_shared": 7,
        "D_private": 0,
        "D_total": 7,
        "D_obs": 3,
        "contiguous_prefix_supported_through": 7,
        "terminal": "PASS_DIMENSION_FAMILY_DERIVED",
    }


def test_full_stream_receipt_passes():
    out = DimensionExecutionFirewallV1().validate(good())
    assert out["passed"] and out["D_total"] == 7


def test_row_identity_only_terminal_cannot_replace_physical_full104_expression_closure():
    x = good()
    x["expression_binding_terminal"] = "PASS_FULL_READER_4553407_ROW_IDENTITY_CLOSURE"
    with pytest.raises(DimensionExecutionStop, match="EXPRESSION_BINDING_NOT_CLOSED"):
        DimensionExecutionFirewallV1().validate(x)


def test_one_se_selection_may_be_smaller_than_supported_prefix():
    x = good()
    x["D_shared"] = 5
    x["D_total"] = 5
    x["contiguous_prefix_supported_through"] = 7
    out = DimensionExecutionFirewallV1().validate(x)
    assert out["passed"] is True
    assert out["D_shared"] == 5


def test_historical_cap4_refit_null_cannot_be_final_authority():
    x = good()
    x["cells_per_stratum_cap"] = 4
    x["final_authority_scripts"] = ["scripts/v4/validate_full104_phase2_empirical_null_refit.py"]
    with pytest.raises(DimensionExecutionStop, match="SAMPLED_SUBSTRATE"):
        DimensionExecutionFirewallV1().validate(x)


def test_fixed_historical_replication_without_precision_rule_fails():
    x = good()
    x["null_replicates"] = 256
    x["null_replicates_derived_from_error_budget"] = False
    with pytest.raises(DimensionExecutionStop, match="NULL_REPLICATES_NOT_PRECISION_DERIVED"):
        DimensionExecutionFirewallV1().validate(x)


def test_historical_script_cannot_be_promoted_even_without_cap_field():
    x = good()
    x["final_authority_scripts"] = ["scripts/v4/independent_validate_full104_phase2_shared_level.py"]
    with pytest.raises(DimensionExecutionStop, match="HISTORICAL_DIAGNOSTIC_PROMOTED"):
        DimensionExecutionFirewallV1().validate(x)


def test_boundary_hit_expands_and_cannot_select_boundary():
    x = good()
    x["search_boundary_supported"] = True
    x["D_shared"] = None
    x["D_private"] = 0
    x["D_total"] = 0
    x["D_obs"] = 0
    x["contiguous_prefix_supported_through"] = 0
    x["terminal"] = "EXPAND_SEARCH_ENVELOPE"
    out = DimensionExecutionFirewallV1().validate(x)
    assert out["terminal"] == "PASS_D_EXECUTION_REQUIRES_SEARCH_EXPANSION"

    y = good()
    y["search_boundary_supported"] = True
    y["D_shared"] = 32
    y["terminal"] = "PASS_DIMENSION_FAMILY_DERIVED"
    with pytest.raises(DimensionExecutionStop, match="BOUNDARY_SELECTED_AS_D"):
        DimensionExecutionFirewallV1().validate(y)


def test_selected_dimension_cannot_exceed_supported_prefix():
    x = good()
    x["contiguous_prefix_supported_through"] = 5
    with pytest.raises(DimensionExecutionStop, match="NONCONTIGUOUS"):
        DimensionExecutionFirewallV1().validate(x)


def test_missing_qc_matching_fails():
    x = good()
    x["matched_null_preserves"] = ["donor", "operator", "Q_DEPTH", "support_measurability"]
    with pytest.raises(DimensionExecutionStop, match="MATCHING_INCOMPLETE"):
        DimensionExecutionFirewallV1().validate(x)
