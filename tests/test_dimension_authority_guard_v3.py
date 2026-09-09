from sea_ad_jepa.v5.dimension_authority_guard_v3 import DimensionAuthorityGuardV3

META = "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"

def good():
    return {
        "expression_binding_terminal": "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE",
        "metadata_sqlite_sha256": META,
        "block_manifest_sha256": "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29",
        "materialization_contract_sha256": "612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17",
        "materialization_audit_sha256": "9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf",
        "cells": 4553407,
        "donors": 104,
        "operators": 42,
        "matrices": 42,
        "blocks": 8915,
        "addresses": 41238,
        "cross_ledger_identity_mismatches": 0,
        "cross_ledger_missing_cells": 0,
        "test_fixture_mode": False,
        "synthetic_data_used": False,
        "pathology_used": False,
        "checkpoint_outcomes_used": False,
        "population_mode": "FULL_READER_FIT_STREAM",
        "estimand": "EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR",
        "null_geometry": "FULL_REFIT_EVERY_REPLICATE",
        "sampled_stratum_cap": None,
        "D_shared": 7,
        "D_private": 0,
        "D_total": 7,
        "D_obs": 3,
    }

def guard():
    return DimensionAuthorityGuardV3(META)

def test_pass():
    assert guard().validate(good())["passed"]

def test_old_shard_presence_terminal_is_rejected():
    x = good()
    x["expression_binding_terminal"] = "PASS_42_OF_42_PHYSICAL_SHARDS_BOUND"
    try:
        guard().validate(x)
    except RuntimeError as e:
        assert "FULL104_EXPRESSION_NOT_CLOSED" in str(e)
    else:
        raise AssertionError("old pilot terminal must fail")

def test_test_fixture_cannot_authorize_D():
    x = good()
    x["test_fixture_mode"] = True
    x["synthetic_data_used"] = True
    try:
        guard().validate(x)
    except RuntimeError as e:
        assert "TEST_FIXTURE" in str(e)
    else:
        raise AssertionError("fixture receipt must fail")

def test_cross_ledger_mismatch_fails():
    x = good()
    x["cross_ledger_identity_mismatches"] = 1
    try:
        guard().validate(x)
    except RuntimeError as e:
        assert "CROSS_LEDGER_IDENTITY" in str(e)
    else:
        raise AssertionError("identity mismatch must fail")
