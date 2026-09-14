from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path

import pytest

from sea_ad_jepa.v5 import full104_dimension_interface_v1 as full104

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = ROOT / "docs" / "agent" / "V5_PROSPECTIVE_D_SHARED_AUTHORITY_V2.json"
MODULE = "sea_ad_jepa.v5.d_shared_authority_v2"


def _module():
    spec = importlib.util.find_spec(MODULE)
    assert spec is not None, "D_shared V2 authority module must exist"
    return importlib.import_module(MODULE)


def _authority():
    assert AUTHORITY_PATH.exists(), "V2 authority artifact must exist"
    return json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))


def _receipt():
    return {
        "schema": "JEPA_V5_FULL104_EXPRESSION_BLOCK_BINDING_V4",
        "status": "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE",
        "block_manifest_sha256": full104.EXPECTED_BLOCK_MANIFEST_SHA256,
        "materialization_contract_sha256": full104.EXPECTED_CONTRACT_SHA256,
        "materialization_audit_sha256": full104.EXPECTED_AUDIT_SHA256,
        "metadata_sqlite_sha256": full104.EXPECTED_METADATA_SQLITE_SHA256,
        "selection_sha256": full104.EXPECTED_SELECTION_SHA256,
        "selection_manifest_sha256": full104.EXPECTED_SELECTION_MANIFEST_SHA256,
        "cells": 4_553_407, "donors": 104, "operators": 42, "matrices": 42, "blocks": 8_915, "addresses": 41_238,
        "cross_ledger_identity_mismatches": 0, "cross_ledger_missing_cells": 0,
        "test_fixture_mode": False, "synthetic_data_used": False, "pathology_used": False,
        "checkpoint_outcomes_used": False, "training_authorized": False,
    }


def test_v2_authority_module_and_artifact_exist():
    _module(); authority = _authority(); assert authority["schema"] == "JEPA_V5_PROSPECTIVE_D_SHARED_AUTHORITY_V2"


def test_v2_plan_carries_per_quantity_counts_not_scalar_execution_authority():
    m = _module(); authority = _authority(); sha = __import__("hashlib").sha256(AUTHORITY_PATH.read_bytes()).hexdigest()
    plan = m.bind_d_shared_execution_plan_v2(authority, authority_sha256=sha)
    assert set(plan["quantity_plan"]) == {"shared_matched_null_exceedance","shared_subspace_stability","shared_held_donor_cross_view_predictability","shared_independent_view_agreement","shared_measurement_shortcut_increment"}
    assert {row["replicates_per_rank"] for row in plan["quantity_plan"].values()} == {9784}
    assert plan["rank_min"] == 1 and plan["rank_max"] == 512
    assert not any(k in plan for k in ("donor_resamples","operator_resamples","null_replicates"))


def test_v2_authority_freezes_rank_multiplicity_generator_and_effect_rule():
    m = _module(); validated = m.validate_d_shared_authority_v2(_authority())
    assert validated["rank_count"] == 512
    assert validated["alpha_per_quantity_rank"] == pytest.approx(0.05/(10*512), rel=0, abs=1e-15)
    assert validated["matched_null_generator"] == "DETERMINISTIC_WITHIN_MATCHING_STRATUM_INDEPENDENT_VIEW_PERMUTATION_FULL_POPULATION_V1"
    assert validated["effect_criterion"] == "SIMULTANEOUS_LOWER_BOUND_STRICTLY_GT_ZERO_V1"


def test_v2_authority_rejects_wrong_count_and_outcome_access():
    m = _module(); authority = _authority(); bad = json.loads(json.dumps(authority)); bad["quantities"][0]["replicates_per_rank"] -= 1
    with pytest.raises(m.DSharedAuthorityStop, match="REPLICATE_COUNT"): m.validate_d_shared_authority_v2(bad)
    bad = json.loads(json.dumps(authority)); bad["outcomes_inspected_before_freeze"] = True
    with pytest.raises(m.DSharedAuthorityStop, match="PRE_FREEZE_ACCESS"): m.validate_d_shared_authority_v2(bad)


def test_v2_authority_rejects_nonfull_rank_envelope_and_generator_substitution():
    m = _module(); authority = _authority(); bad = json.loads(json.dumps(authority)); bad["rank_max"] = 511
    with pytest.raises(m.DSharedAuthorityStop, match="RANK_ENVELOPE"): m.validate_d_shared_authority_v2(bad)
    bad = json.loads(json.dumps(authority)); bad["matched_null_generator"] = "OTHER"
    with pytest.raises(m.DSharedAuthorityStop, match="MATCHED_NULL_GENERATOR"): m.validate_d_shared_authority_v2(bad)


def test_v2_full104_binding_is_d_shared_only_and_rejects_v1_as_execution_authority():
    m = _module(); authority = _authority(); sha = __import__("hashlib").sha256(AUTHORITY_PATH.read_bytes()).hexdigest(); envelope = full104.seal_full104_dimension_input(_receipt())
    out = m.bind_full104_d_shared_preoutcome_v2(authority, authority_sha256=sha, full104_dimension_envelope=envelope, full104_artifact_sha256=envelope["artifact_sha256"], dimension_interface_sha256=authority["dimension_interface_sha256"], superseded_v1_precision_sha256="cc4ac4d5116fa81990f1c3bd0497fc578eda86bb2d7d3cd2747abcf7ffcf9428", superseded_v1_cross_binding_sha256="eccc30f9f5d01f7905a0740982d678d0ce45532a08cd5a61c51f5448b63b3d3a")
    assert out["schema"] == "JEPA_V5_FULL104_D_SHARED_PREOUTCOME_BINDING_V2"
    assert out["d_shared_metric_execution_authorized"] is True
    assert out["d_private_execution_authorized"] is False and out["d_obs_execution_authorized"] is False
    assert out["training_authorized"] is False and out["protected_data_authorized"] is False
