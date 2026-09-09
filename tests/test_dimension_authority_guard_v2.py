from sea_ad_jepa.v5.dimension_authority_guard_v2 import DimensionAuthorityGuardV2

def good():
    return {
        "expression_location_terminal": "PASS_FULL_READER_4553407_ROW_IDENTITY_CLOSURE",
        "metadata_sha256": "meta",
        "production_loader_manifest_sha256": "loader",
        "cells": 4553407,
        "reader_fit_identity_rows_matched": 4553407,
        "unique_stable_keys": 4553407,
        "donors": 104,
        "shards_bound": 42,
        "addresses": 41238,
        "population_mode": "FULL_READER_FIT_STREAM",
        "estimand": "EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR",
        "null_geometry": "FULL_REFIT_EVERY_REPLICATE",
        "sampled_stratum_cap": None,
        "synthetic_data_used": False,
        "pathology_used": False,
        "checkpoint_outcomes_used": False,
        "D_shared": 7,
        "D_private": 0,
        "D_total": 7,
        "D_obs": 3,
    }

def guard():
    return DimensionAuthorityGuardV2("meta", "loader")

def test_pass():
    assert guard().validate(good())["passed"]

def test_old_42_shard_terminal_is_not_enough():
    x = good()
    x["expression_location_terminal"] = "PASS_42_OF_42_PHYSICAL_SHARDS_BOUND"
    try:
        guard().validate(x)
    except RuntimeError as e:
        assert "ROW_IDENTITY_NOT_CLOSED" in str(e)
    else:
        raise AssertionError("old terminal must fail")

def test_4726_row_partial_cache_is_rejected():
    x = good()
    x["reader_fit_identity_rows_matched"] = 4726
    try:
        guard().validate(x)
    except RuntimeError as e:
        assert "ROW_CLOSURE" in str(e)
    else:
        raise AssertionError("partial cache must fail")
