from fractions import Fraction

import numpy as np
import pytest

from sea_ad_jepa.v5.audit_b_production_burden_v1 import (
    BURDEN_RUNGS,
    NONUNIFORM_POLICIES,
    POLICIES,
    DonorBurdenObservationV1,
    escalation_decision,
    measure_plan_burden,
    precision_summary,
    source_balanced_target_value,
)


def _plans():
    # Target 0 and address 1 are common-random uniform mask. Targeted arms swap
    # address 1 for one different address while keeping exact cardinality.
    base = {0, 1}
    return {
        "_base_mask": {"mask": base, "mask_cardinality": 2},
        "UNIFORM_RANDOM": {
            "mask": base,
            "added_vs_base": [],
            "dropped_vs_base": [],
        },
        "TOP8_CORRELATION": {
            "mask": {0, 2},
            "added_vs_base": [2],
            "dropped_vs_base": [1],
        },
        "RIDGE8_CONDITIONAL": {
            "mask": {0, 3},
            "added_vs_base": [3],
            "dropped_vs_base": [1],
        },
        "PREFIX3_SELECTIVE": {
            "mask": {0, 4},
            "added_vs_base": [4],
            "dropped_vs_base": [1],
        },
    }


def test_exact_heldout_burden_uses_added_minus_dropped_and_uniform_denominator() -> None:
    # 21 addresses makes the 5% rung exactly one non-target co-mask address:
    # floor((21-1) * 1/20) = 1, plus the target => mask cardinality 2.
    core = np.arange(21)
    # donor 0 held out. Uniform B2 burden = address0 + address1 = 10 + 20 = 30.
    nnz = np.zeros((2, 21), dtype=float)
    umi = np.zeros((2, 21), dtype=float)
    nnz[:, :5] = np.array([[10, 20, 50, 35, 5], [1, 2, 3, 4, 5]], dtype=float)
    umi[:, :5] = np.array([[100, 200, 500, 350, 50], [10, 20, 30, 40, 50]], dtype=float)
    rows = measure_plan_burden(
        target_col=0,
        fold_index=0,
        plans=_plans(),
        heldout_donors=[0],
        fold_by_donor=[0, 1],
        donor_source_code=[0, 1],
        core_addresses=core,
        donor_nnz=nnz,
        donor_umi=umi,
        rung=Fraction(1, 20),
    )
    by_policy = {r.policy_id: r for r in rows}
    assert set(by_policy) == set(POLICIES)
    assert by_policy["UNIFORM_RANDOM"].delta_detected_burden == 0.0
    assert by_policy["TOP8_CORRELATION"].uniform_detected_burden == 30.0
    assert by_policy["TOP8_CORRELATION"].delta_detected_burden == 30.0
    assert by_policy["TOP8_CORRELATION"].normalized_delta_detected == pytest.approx(1.0)
    assert by_policy["RIDGE8_CONDITIONAL"].delta_detected_burden == 15.0
    assert by_policy["RIDGE8_CONDITIONAL"].normalized_delta_detected == pytest.approx(0.5)
    assert by_policy["PREFIX3_SELECTIVE"].delta_detected_burden == -15.0
    assert by_policy["PREFIX3_SELECTIVE"].normalized_delta_detected == pytest.approx(-0.5)


def test_target_address_must_be_in_uniform_base_and_never_in_swap_sets() -> None:
    plans = _plans()
    plans["_base_mask"] = {"mask": {1, 2}, "mask_cardinality": 2}
    with pytest.raises(ValueError, match="contain the target"):
        measure_plan_burden(
            target_col=0,
            fold_index=0,
            plans=plans,
            heldout_donors=[0],
            fold_by_donor=[0],
            donor_source_code=[0],
            core_addresses=np.arange(21),
            donor_nnz=np.ones((1, 21)),
            donor_umi=np.ones((1, 21)),
            rung=Fraction(1, 20),
        )

    plans = _plans()
    plans["TOP8_CORRELATION"]["added_vs_base"] = [0]
    plans["TOP8_CORRELATION"]["dropped_vs_base"] = [1]
    with pytest.raises(ValueError, match="Target|target"):
        measure_plan_burden(
            target_col=0,
            fold_index=0,
            plans=plans,
            heldout_donors=[0],
            fold_by_donor=[0],
            donor_source_code=[0],
            core_addresses=np.arange(21),
            donor_nnz=np.ones((1, 21)),
            donor_umi=np.ones((1, 21)),
            rung=Fraction(1, 20),
        )


def test_zero_uniform_detected_burden_fails_closed() -> None:
    with pytest.raises(ValueError, match="not estimable"):
        measure_plan_burden(
            target_col=0,
            fold_index=0,
            plans=_plans(),
            heldout_donors=[0],
            fold_by_donor=[0],
            donor_source_code=[0],
            core_addresses=np.arange(21),
            donor_nnz=np.zeros((1, 21)),
            donor_umi=np.ones((1, 21)),
            rung=Fraction(1, 20),
        )


def _row(donor, source, value):
    return DonorBurdenObservationV1(
        target_col=7,
        fold_index=0,
        donor_code=donor,
        source_code=source,
        policy_id="TOP8_CORRELATION",
        rung_numerator=1,
        rung_denominator=20,
        uniform_detected_burden=100.0,
        delta_detected_burden=value * 100.0,
        normalized_delta_detected=value,
        uniform_umi_burden=100.0,
        delta_umi_burden=value * 100.0,
        normalized_delta_umi=value,
    )


def test_source_balanced_target_value_is_not_cell_or_donor_pooled() -> None:
    # Source 0 has two donors averaging 0.3; source 1 has one donor at 0.9.
    # Source-balanced result is (0.3 + 0.9)/2 = 0.6, not pooled-donor 0.5.
    rows = [_row(0, 0, 0.2), _row(1, 0, 0.4), _row(2, 1, 0.9)]
    assert source_balanced_target_value(
        rows, expected_source_codes=[0, 1]
    ) == pytest.approx(0.6)


def test_missing_required_source_cannot_disappear() -> None:
    with pytest.raises(ValueError, match="required source"):
        source_balanced_target_value([_row(0, 0, 0.2)], expected_source_codes=[0, 1])


def test_precision_summary_uses_target_units_and_zero_mean_fails_closed() -> None:
    out = precision_summary(
        policy_id="TOP8_CORRELATION",
        rung=Fraction(1, 20),
        target_values=[0.1, 0.2, 0.3, 0.4],
    )
    expected_sd = np.std([0.1, 0.2, 0.3, 0.4], ddof=1)
    assert out.standard_error == pytest.approx(expected_sd / 2.0)
    assert out.relative_standard_error == pytest.approx(out.standard_error / 0.25)

    zero = precision_summary(
        policy_id="TOP8_CORRELATION",
        rung=Fraction(1, 20),
        target_values=[-1.0, 1.0],
    )
    assert zero.relative_standard_error is None
    assert zero.relative_standard_error_state == "UNDEFINED_ZERO_MEAN__FAIL_CLOSED"
    assert not zero.precision_passed


def _all_summaries(*, fail_one=False):
    out = []
    for policy in NONUNIFORM_POLICIES:
        for rung in BURDEN_RUNGS:
            values = [1.0, 1.0, 1.0, 1.0]
            if fail_one and policy == NONUNIFORM_POLICIES[0] and rung == BURDEN_RUNGS[0]:
                values = [0.0, 0.0, 0.0, 1.0]
            out.append(
                precision_summary(
                    policy_id=policy,
                    rung=rung,
                    target_values=values,
                )
            )
    return out


def test_escalation_requires_every_policy_x_rung_cell_to_meet_precision() -> None:
    good = escalation_decision(_all_summaries(), sample_level="N1")
    assert good["state"] == "SUFFICIENT_PRECISION"
    assert good["next_sample_authorized"] is None

    n1 = escalation_decision(_all_summaries(fail_one=True), sample_level="N1")
    assert n1["state"] == "ESCALATE_TO_N2"
    assert n1["next_sample_authorized"] == "N2"

    n2 = escalation_decision(_all_summaries(fail_one=True), sample_level="N2")
    assert n2["state"] == "ESCALATE_TO_N3"
    assert n2["next_sample_authorized"] == "N3"

    n3 = escalation_decision(_all_summaries(fail_one=True), sample_level="N3")
    assert n3["state"] == "INSUFFICIENT_PRECISION_AT_N3"
    assert n3["next_sample_authorized"] is None


def test_escalation_rejects_incomplete_or_duplicate_precision_grid() -> None:
    summaries = _all_summaries()
    with pytest.raises(ValueError, match="every nonuniform policy"):
        escalation_decision(summaries[:-1], sample_level="N1")
    with pytest.raises(ValueError, match="every nonuniform policy"):
        escalation_decision(summaries + [summaries[0]], sample_level="N1")


def test_training_donor_cannot_be_passed_as_heldout() -> None:
    # fold 0 authenticates donor 0 only. Supplying donor 1 would measure burden
    # on training-side material and must fail before any burden is computed.
    with pytest.raises(ValueError, match="exactly match authenticated fold membership"):
        measure_plan_burden(
            target_col=0,
            fold_index=0,
            plans=_plans(),
            heldout_donors=[1],
            fold_by_donor=[0, 1],
            donor_source_code=[0, 1],
            core_addresses=np.arange(21),
            donor_nnz=np.ones((2, 21)),
            donor_umi=np.ones((2, 21)),
            rung=Fraction(1, 20),
        )


def test_partial_heldout_fold_cannot_be_silently_subsampled() -> None:
    # Both donors 0 and 1 belong to fold 0; evaluating only one would change the
    # donor-weighted estimand and is therefore refused.
    with pytest.raises(ValueError, match="exactly match authenticated fold membership"):
        measure_plan_burden(
            target_col=0,
            fold_index=0,
            plans=_plans(),
            heldout_donors=[0],
            fold_by_donor=[0, 0, 1],
            donor_source_code=[0, 1, 1],
            core_addresses=np.arange(21),
            donor_nnz=np.ones((3, 21)),
            donor_umi=np.ones((3, 21)),
            rung=Fraction(1, 20),
        )


def test_zero_mean_rse_stops_instead_of_driving_escalation() -> None:
    summaries = _all_summaries()
    summaries[0] = precision_summary(
        policy_id=NONUNIFORM_POLICIES[0],
        rung=BURDEN_RUNGS[0],
        target_values=[-1.0, 1.0],
    )
    with pytest.raises(ValueError, match="STOP_ZERO_MEAN_RULE_UNRESOLVED"):
        escalation_decision(summaries, sample_level="N1")


def test_plan_swap_lists_must_match_actual_mask() -> None:
    plans = _plans()
    plans["TOP8_CORRELATION"]["added_vs_base"] = [3]  # actual mask adds 2
    with pytest.raises(ValueError, match="do not match the actual mask"):
        measure_plan_burden(
            target_col=0,
            fold_index=0,
            plans=plans,
            heldout_donors=[0],
            fold_by_donor=[0],
            donor_source_code=[0],
            core_addresses=np.arange(21),
            donor_nnz=np.ones((1, 21)),
            donor_umi=np.ones((1, 21)),
            rung=Fraction(1, 20),
        )


def test_rung_label_must_match_mask_cardinality() -> None:
    # _plans() contains target + one co-mask address, valid at 5% for 21 addresses
    # but not at 50%, where ten non-target addresses are required.
    with pytest.raises(ValueError, match="frozen rung arithmetic"):
        measure_plan_burden(
            target_col=0,
            fold_index=0,
            plans=_plans(),
            heldout_donors=[0],
            fold_by_donor=[0],
            donor_source_code=[0],
            core_addresses=np.arange(21),
            donor_nnz=np.ones((1, 21)),
            donor_umi=np.ones((1, 21)),
            rung=Fraction(1, 2),
        )
