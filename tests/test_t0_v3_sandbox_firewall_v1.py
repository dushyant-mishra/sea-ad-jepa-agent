import copy

import pytest

from sea_ad_jepa.v5.t0_v3_sandbox_firewall_v1 import validate_t0_v3_sandbox_receipt_v1


REQUIRED_STRESS_TESTS = [
    "STRICT_NULL_CALIBRATION",
    "CONTROLLED_POSITIVE_SIGNAL",
    "SAME_CELL_MEASUREMENT_INTERVENTION",
    "RARE_TAIL_FALSIFICATION",
    "BROAD_STATE_NON_DESTRUCTION",
    "CROSS_FIT_VARIANCE_INFLATION",
]


def valid_receipt():
    return {
        "schema": "JEPA_V5_T0_V3_SANDBOX_RECEIPT_V1",
        "candidate_id": "SAME_CELL_COUNTERFACTUAL_MEASUREMENT_V1",
        "terminal": "ELIGIBLE_FOR_FULL104_QUALIFICATION",
        "stress_tests_executed": REQUIRED_STRESS_TESTS,
        "historical_inputs_only": True,
        "synthetic_controls_used": True,
        "fresh_reader_validation_used": False,
        "fresh_at8_used": False,
        "oracle_or_protected_used": False,
        "rare_tail_terminal_preserved": "RARE_TAIL_UNDERDETERMINED_MEASUREMENT",
        "broad_state_used_as_acceptance_criterion": False,
        "permutation_significance_used_as_effect_magnitude": False,
        "effect_transport_claimed": False,
        "survivor_only_metrics_used": False,
        "unconditional_failure_accounting": True,
        "v5_numeric_thresholds_derived_from_t0": False,
        "v5_rank_rule_derived_from_t0": False,
        "v5_null_frozen_from_t0": False,
        "d_shared_outcomes_used": False,
        "d_shared_real_outcome_access_authorized": False,
        "training_authorized": False,
    }


def test_clean_t0_sandbox_can_only_promote_to_full104_qualification():
    out = validate_t0_v3_sandbox_receipt_v1(valid_receipt())
    assert out["passed"] is True
    assert out["terminal"] == "ELIGIBLE_FOR_FULL104_QUALIFICATION"
    assert out["t0_can_certify_v5"] is False
    assert out["d_shared_real_outcome_access_authorized"] is False
    assert out["training_authorized"] is False


def test_rejection_terminal_is_valid_and_does_not_escalate_authority():
    r = valid_receipt()
    r["terminal"] = "REJECT_CANDIDATE"
    out = validate_t0_v3_sandbox_receipt_v1(r)
    assert out["terminal"] == "REJECT_CANDIDATE"
    assert out["d_shared_real_outcome_access_authorized"] is False


def test_fresh_or_protected_t0_inputs_are_forbidden():
    for field in ("fresh_reader_validation_used", "fresh_at8_used", "oracle_or_protected_used"):
        r = valid_receipt()
        r[field] = True
        with pytest.raises(RuntimeError, match="STOP_T0_V3_SANDBOX_FORBIDDEN_INPUT"):
            validate_t0_v3_sandbox_receipt_v1(r)


def test_historical_terminals_and_non_tuning_rules_are_immutable():
    mutations = {
        "rare_tail_terminal_preserved": "PASS_RARE_TAIL",
        "broad_state_used_as_acceptance_criterion": True,
        "v5_numeric_thresholds_derived_from_t0": True,
        "v5_rank_rule_derived_from_t0": True,
        "v5_null_frozen_from_t0": True,
    }
    for field, value in mutations.items():
        r = valid_receipt()
        r[field] = value
        with pytest.raises(RuntimeError, match="STOP_T0_V3_SANDBOX"):
            validate_t0_v3_sandbox_receipt_v1(r)


def test_permutation_association_cannot_become_effect_transport():
    for field in ("permutation_significance_used_as_effect_magnitude", "effect_transport_claimed"):
        r = valid_receipt()
        r[field] = True
        with pytest.raises(RuntimeError, match="STOP_T0_V3_SANDBOX_EFFECT_TRANSPORT"):
            validate_t0_v3_sandbox_receipt_v1(r)


def test_survivor_only_or_missing_unconditional_failures_are_forbidden():
    r = valid_receipt()
    r["survivor_only_metrics_used"] = True
    with pytest.raises(RuntimeError, match="STOP_T0_V3_SANDBOX_FAILURE_ACCOUNTING"):
        validate_t0_v3_sandbox_receipt_v1(r)
    r = valid_receipt()
    r["unconditional_failure_accounting"] = False
    with pytest.raises(RuntimeError, match="STOP_T0_V3_SANDBOX_FAILURE_ACCOUNTING"):
        validate_t0_v3_sandbox_receipt_v1(r)


def test_v5_or_dshared_authority_escalation_is_impossible():
    for field in ("d_shared_outcomes_used", "d_shared_real_outcome_access_authorized", "training_authorized"):
        r = valid_receipt()
        r[field] = True
        with pytest.raises(RuntimeError, match="STOP_T0_V3_SANDBOX_AUTHORITY_ESCALATION"):
            validate_t0_v3_sandbox_receipt_v1(r)
    r = valid_receipt()
    r["terminal"] = "PASS_V5_QUALIFIED"
    with pytest.raises(RuntimeError, match="STOP_T0_V3_SANDBOX_TERMINAL"):
        validate_t0_v3_sandbox_receipt_v1(r)


def test_required_stress_tests_cannot_be_silently_omitted_for_eligibility():
    r = valid_receipt()
    r["stress_tests_executed"] = REQUIRED_STRESS_TESTS[:-1]
    with pytest.raises(RuntimeError, match="STOP_T0_V3_SANDBOX_STRESS_TEST_COVERAGE"):
        validate_t0_v3_sandbox_receipt_v1(r)
