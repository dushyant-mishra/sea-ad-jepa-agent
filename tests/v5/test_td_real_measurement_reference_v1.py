from __future__ import annotations

import math

import pytest

import scripts.v5.td_real_measurement_reference_v1 as M


def test_minimum_calibration_size_is_derived_from_alpha_not_guessed():
    assert M.minimum_calibration_size(0.01) == 99
    assert M.minimum_calibration_size(0.005) == 199
    assert M.minimum_calibration_size(0.01 / 3.0) == 299


def test_distribution_free_upper_prediction_bound_uses_conformal_rank():
    scores = [float(i) for i in range(99)]
    out = M.upper_prediction_bound(scores, alpha=0.01)
    assert out["status"] == "PASS_REFERENCE_CALIBRATED"
    assert out["n_calibration"] == 99
    assert out["rank_1_based"] == 99
    assert out["upper_bound"] == 98.0


def test_too_few_calibration_replicates_is_not_estimable():
    out = M.upper_prediction_bound([float(i) for i in range(98)], alpha=0.01)
    assert out["status"] == "NOT_ESTIMABLE_CALIBRATION_RESOLUTION"
    assert out["required_n"] == 99


def test_nonfinite_or_negative_displacements_fail_closed():
    with pytest.raises(M.MeasurementReferenceError):
        M.upper_prediction_bound([0.0, float("nan")] * 50, alpha=0.01)
    with pytest.raises(M.MeasurementReferenceError):
        M.upper_prediction_bound([0.0, -1.0] * 50, alpha=0.01)


def test_exact_binomial_thinning_preserves_support_and_integer_semantics():
    counts = [[0, 1, 3], [5, 0, 2]]
    a = M.thin_integer_counts(counts, fraction=0.5, seed_namespace="CAL_A", seed=11)
    b = M.thin_integer_counts(counts, fraction=0.5, seed_namespace="CAL_A", seed=11)
    assert a == b
    for row_in, row_out in zip(counts, a):
        for n, x in zip(row_in, row_out):
            assert isinstance(x, int)
            assert 0 <= x <= n
            if n == 0:
                assert x == 0


def test_invalid_raw_counts_or_fraction_fail_before_thinning():
    with pytest.raises(M.MeasurementReferenceError):
        M.thin_integer_counts([[1.5]], fraction=0.5, seed_namespace="A", seed=1)
    with pytest.raises(M.MeasurementReferenceError):
        M.thin_integer_counts([[-1]], fraction=0.5, seed_namespace="A", seed=1)
    with pytest.raises(M.MeasurementReferenceError):
        M.thin_integer_counts([[1]], fraction=1.0, seed_namespace="A", seed=1)


def test_calibration_and_deciding_seed_namespaces_must_be_disjoint():
    with pytest.raises(M.MeasurementReferenceError, match="disjoint"):
        M.validate_seed_namespaces(
            calibration_namespaces=["CAL_A", "CAL_B"],
            deciding_namespace="CAL_B",
            null_namespace="NULL",
        )
    M.validate_seed_namespaces(
        calibration_namespaces=["CAL_A", "CAL_B"],
        deciding_namespace="DECIDE",
        null_namespace="NULL",
    )


def test_g8_depth_family_derives_bonferroni_resolution_and_never_relaxes():
    calibration = {
        "0.25": [0.1] * 299,
        "0.50": [0.2] * 299,
        "0.75": [0.3] * 299,
    }
    out = M.build_depth_reference(calibration, family_alpha=0.01)
    assert out["depths"] == ["0.25", "0.50", "0.75"]
    assert math.isclose(out["alpha_eff"], 0.01 / 3.0)
    assert out["required_n_per_depth"] == 299
    assert out["status"] == "PASS_MEASUREMENT_REFERENCE_CALIBRATED"
    assert out["authority"] == {
        "value_read_authorized": False,
        "real_tournament_authorized": False,
        "target_selection_authorized": False,
        "representation_selection_authorized": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }
