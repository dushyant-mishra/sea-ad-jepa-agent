import json

import pytest

from sea_ad_jepa.v5.prospective_precision_authority_v1 import (
    PrecisionAuthorityStop,
    canonical_precision_authority_bytes,
    derive_hoeffding_fixed_n,
    validate_precision_authority_v1,
)


def authority():
    quantities = []
    for i, (qid, lo, hi, tol, kind) in enumerate([
        ("shared_matched_null_exceedance", 0.0, 1.0, 0.025, "null"),
        ("shared_subspace_stability", 0.0, 1.0, 0.05, "donor"),
        ("shared_held_donor_cross_view_predictability", -1.0, 1.0, 0.05, "donor"),
        ("shared_independent_view_agreement", 0.0, 1.0, 0.05, "donor"),
        ("shared_measurement_shortcut_increment", -1.0, 1.0, 0.05, "donor"),
        ("private_held_donor_increment", -1.0, 1.0, 0.05, "donor"),
        ("private_held_operator_increment", -1.0, 1.0, 0.05, "operator"),
        ("private_measurement_shortcut_increment", -1.0, 1.0, 0.05, "donor"),
        ("private_same_cell_technical_intervention_stability", 0.0, 1.0, 0.05, "donor"),
        ("observation_held_operator_reconstruction", 0.0, 1.0, 0.05, "operator"),
    ]):
        alpha = 0.005
        quantities.append({
            "quantity_id": qid,
            "resampling_kind": kind,
            "lower_bound": lo,
            "upper_bound": hi,
            "absolute_precision_tolerance": tol,
            "risk_allocation": alpha,
            "replicates": derive_hoeffding_fixed_n(hi - lo, tol, alpha),
        })
    return {
        "schema": "JEPA_V5_PROSPECTIVE_DIMENSION_PRECISION_AUTHORITY_V1",
        "status": "FROZEN_BEFORE_DIMENSION_OUTCOME_ACCESS",
        "method": "HOEFFDING_FIXED_N_V1",
        "familywise_precision_risk": 0.05,
        "risk_allocation_method": "BONFERRONI_EQUAL_10",
        "decision_metric_population": "UNCONDITIONAL_OVER_DECLARED_EVALUATION_POPULATION",
        "estimator_failure_policy": "FAILURE_COUNTS_AS_NONQUALIFYING_AND_IS_REPORTED_SEPARATELY",
        "survivor_only_intervals_forbidden": True,
        "precision_is_not_effect_criterion": True,
        "post_outcome_replication_tuning_forbidden": True,
        "gate_ablation_required": True,
        "redundancy_identity_check_required": True,
        "rng_replay_policy": "SHA256_PARENT_QUANTITY_REPLICATE_INDEX_V1",
        "outcomes_inspected_before_freeze": False,
        "checkpoint_outcomes_used": False,
        "pathology_used": False,
        "protected_data_used": False,
        "training_authorized": False,
        "dimension_outcomes_used": False,
        "quantities": quantities,
    }


def test_hoeffding_fixed_n_is_derived_not_inherited():
    assert derive_hoeffding_fixed_n(1.0, 0.025, 0.005) == 4794
    assert derive_hoeffding_fixed_n(1.0, 0.05, 0.005) == 1199
    assert derive_hoeffding_fixed_n(2.0, 0.05, 0.005) == 4794
    assert derive_hoeffding_fixed_n(1.0, 0.025, 0.005) not in {256, 999, 1000}


def test_frozen_authority_passes_and_reports_execution_counts():
    out = validate_precision_authority_v1(authority())
    assert out["terminal"] == "PASS_V5_PROSPECTIVE_PRECISION_AUTHORITY_V1"
    assert out["full_refit_null_replicates"] == 4794
    assert out["donor_resamples"] == 4794
    assert out["operator_resamples"] == 4794
    assert out["quantity_count"] == 10


def test_hand_entered_historical_count_cannot_masquerade_as_precision_derived():
    x = authority()
    x["quantities"][0]["replicates"] = 999
    with pytest.raises(PrecisionAuthorityStop, match="REPLICATE_COUNT_MISMATCH"):
        validate_precision_authority_v1(x)


def test_familywise_risk_allocation_must_close_exactly():
    x = authority()
    x["quantities"][0]["risk_allocation"] = 0.004
    with pytest.raises(PrecisionAuthorityStop, match="RISK_ALLOCATION_MISMATCH"):
        validate_precision_authority_v1(x)


def test_duplicate_quantity_id_fails_closed():
    x = authority()
    x["quantities"][1]["quantity_id"] = x["quantities"][0]["quantity_id"]
    with pytest.raises(PrecisionAuthorityStop, match="DUPLICATE_QUANTITY"):
        validate_precision_authority_v1(x)


@pytest.mark.parametrize(
    "field",
    ["outcomes_inspected_before_freeze", "checkpoint_outcomes_used", "pathology_used", "protected_data_used", "dimension_outcomes_used"],
)
def test_any_pre_freeze_outcome_or_protected_access_fails(field):
    x = authority()
    x[field] = True
    with pytest.raises(PrecisionAuthorityStop, match="PRE_FREEZE_ACCESS"):
        validate_precision_authority_v1(x)


def test_conditional_or_survivor_only_semantics_fail():
    x = authority()
    x["decision_metric_population"] = "CONDITIONAL_ON_ESTIMATOR_SUCCESS"
    with pytest.raises(PrecisionAuthorityStop, match="UNCONDITIONAL"):
        validate_precision_authority_v1(x)

    y = authority()
    y["survivor_only_intervals_forbidden"] = False
    with pytest.raises(PrecisionAuthorityStop, match="SURVIVOR_ONLY"):
        validate_precision_authority_v1(y)


def test_precision_cannot_be_relabelled_as_effect_threshold():
    x = authority()
    x["precision_is_not_effect_criterion"] = False
    with pytest.raises(PrecisionAuthorityStop, match="PRECISION_EFFECT_CONFLATION"):
        validate_precision_authority_v1(x)


def test_canonical_bytes_are_order_stable():
    x = authority()
    a = canonical_precision_authority_bytes(x)
    shuffled = json.loads(json.dumps(x))
    shuffled = dict(reversed(list(shuffled.items())))
    b = canonical_precision_authority_bytes(shuffled)
    assert a == b
    assert a.endswith(b"\n")
