from __future__ import annotations

import importlib
import importlib.util

import pytest

MODULE = "sea_ad_jepa.v5.d_shared_execution_firewall_v2"
AUTH_SHA = "f9568eb19a22f106b0be3ce0580bc1058695ca1a2de6dd2d0475c3240a6bbda2"
BINDING_SHA = "a" * 64
QIDS = (
    "shared_matched_null_exceedance",
    "shared_subspace_stability",
    "shared_held_donor_cross_view_predictability",
    "shared_independent_view_agreement",
    "shared_measurement_shortcut_increment",
)


def _module():
    spec = importlib.util.find_spec(MODULE)
    assert spec is not None, "D_shared execution firewall V2 module must exist"
    return importlib.import_module(MODULE)


def receipt():
    return {
        "schema": "JEPA_V5_D_SHARED_RAW_EXECUTION_RECEIPT_V1",
        "preoutcome_binding_schema": "JEPA_V5_FULL104_D_SHARED_PREOUTCOME_BINDING_V2",
        "preoutcome_binding_sha256": BINDING_SHA,
        "d_shared_authority_v2_sha256": AUTH_SHA,
        "population_mode": "FULL_READER_FIT_STREAM",
        "reader_fit_rows_used": 4_553_407,
        "unique_stable_keys_used": 4_553_407,
        "donors_used": 104,
        "operators_used": 42,
        "addresses": 41_238,
        "sampled_stratum_cap": None,
        "cells_per_stratum_cap": None,
        "row_cap": None,
        "rank_min": 1,
        "rank_max": 512,
        "matched_null_generator": "DETERMINISTIC_WITHIN_MATCHING_STRATUM_INDEPENDENT_VIEW_PERMUTATION_FULL_POPULATION_V1",
        "matching_tuple": ["donor", "operator", "Q_DEPTH", "Q_DETECT", "support_measurability"],
        "matching_state_discreteness_verified": True,
        "null_geometry": "FULL_REFIT_EVERY_REPLICATE",
        "full_refit_every_null_replicate_verified": True,
        "rng_replay_policy": "SHA256_PARENT_QUANTITY_RANK_REPLICATE_INDEX_V2",
        "decision_metric_population": "UNCONDITIONAL_OVER_DECLARED_EVALUATION_POPULATION",
        "estimator_failure_policy": "FAILURE_COUNTS_AS_NONQUALIFYING_AND_IS_REPORTED_SEPARATELY",
        "estimator_failures_in_denominator": True,
        "post_outcome_replication_extension": False,
        "rank_search_executed_before_metric_seal": False,
        "quantity_execution": {q: {"rank_min": 1, "rank_max": 512, "replicates_per_rank": 9784} for q in QIDS},
        "synthetic_data_used": False,
        "pathology_used": False,
        "protected_data_used": False,
        "checkpoint_outcomes_used": False,
        "d_private_execution_attempted": False,
        "d_obs_execution_attempted": False,
        "training_authorized": False,
    }


def test_v2_firewall_accepts_exact_d_shared_execution_contract():
    m = _module()
    out = m.DSharedExecutionFirewallV2(expected_preoutcome_binding_sha256=BINDING_SHA).validate(receipt())
    assert out["terminal"] == "PASS_V5_D_SHARED_EXECUTION_FIREWALL_V2"
    assert out["d_shared_metric_execution_validated"] is True
    assert out["training_authorized"] is False


def test_v2_firewall_rejects_v1_or_scalar_max_execution_semantics():
    m = _module(); r = receipt(); r["preoutcome_binding_schema"] = "JEPA_V5_FULL104_PRECISION_PREOUTCOME_BINDING_V1"
    with pytest.raises(m.DSharedExecutionStop, match="V2_PREOUTCOME_BINDING_REQUIRED"): m.DSharedExecutionFirewallV2(expected_preoutcome_binding_sha256=BINDING_SHA).validate(r)
    r = receipt(); r["donor_resamples"] = 4794
    with pytest.raises(m.DSharedExecutionStop, match="SCALAR_REPLICATE_AUTHORITY_FORBIDDEN"): m.DSharedExecutionFirewallV2(expected_preoutcome_binding_sha256=BINDING_SHA).validate(r)


def test_v2_firewall_rejects_per_quantity_count_or_rank_substitution():
    m = _module(); r = receipt(); r["quantity_execution"][QIDS[0]]["replicates_per_rank"] = 9783
    with pytest.raises(m.DSharedExecutionStop, match="QUANTITY_EXECUTION_MISMATCH"): m.DSharedExecutionFirewallV2(expected_preoutcome_binding_sha256=BINDING_SHA).validate(r)
    r = receipt(); r["rank_max"] = 511
    with pytest.raises(m.DSharedExecutionStop, match="RANK_ENVELOPE"): m.DSharedExecutionFirewallV2(expected_preoutcome_binding_sha256=BINDING_SHA).validate(r)


def test_v2_firewall_rejects_null_or_failure_semantic_substitution():
    m = _module(); r = receipt(); r["matched_null_generator"] = "OTHER"
    with pytest.raises(m.DSharedExecutionStop, match="MATCHED_NULL_GENERATOR"): m.DSharedExecutionFirewallV2(expected_preoutcome_binding_sha256=BINDING_SHA).validate(r)
    r = receipt(); r["estimator_failures_in_denominator"] = False
    with pytest.raises(m.DSharedExecutionStop, match="FAILURE_DROPPED"): m.DSharedExecutionFirewallV2(expected_preoutcome_binding_sha256=BINDING_SHA).validate(r)


def test_v2_firewall_rejects_forbidden_access_or_downstream_execution():
    m = _module(); r = receipt(); r["protected_data_used"] = True
    with pytest.raises(m.DSharedExecutionStop, match="FORBIDDEN_STATE"): m.DSharedExecutionFirewallV2(expected_preoutcome_binding_sha256=BINDING_SHA).validate(r)
    r = receipt(); r["d_private_execution_attempted"] = True
    with pytest.raises(m.DSharedExecutionStop, match="DOWNSTREAM_STAGE"): m.DSharedExecutionFirewallV2(expected_preoutcome_binding_sha256=BINDING_SHA).validate(r)
