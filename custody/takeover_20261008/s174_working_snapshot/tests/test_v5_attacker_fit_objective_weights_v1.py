import numpy as np
import pytest

from sea_ad_jepa.v5.attacker_fit_objective_weights_v1 import (
    build_fit_weights,
    solve_weighted_ridge,
    weighted_ridge_sufficient_statistics,
)


def geometry():
    donor = np.array([0, 1, 1, 1, 2, 2])
    source = np.array([0, 0, 0, 0, 1, 1])
    return donor, source


def test_cell_weighted_matches_population_rows() -> None:
    donor, source = geometry()
    out = build_fit_weights(donor, source, objective="CURRENT_CELL_WEIGHTED")
    assert out.donor_mass[0] == pytest.approx(1 / 6)
    assert out.donor_mass[1] == pytest.approx(3 / 6)
    assert out.donor_mass[2] == pytest.approx(2 / 6)
    assert out.source_mass[0] == pytest.approx(4 / 6)


def test_production_matched_is_exactly_donor_uniform() -> None:
    donor, source = geometry()
    out = build_fit_weights(donor, source, objective="PRODUCTION_OBJECTIVE_MATCHED")
    assert list(out.donor_mass.values()) == pytest.approx([1 / 3] * 3)
    assert out.source_mass[0] == pytest.approx(2 / 3)
    assert out.source_mass[1] == pytest.approx(1 / 3)


def test_source_donor_balanced_is_equal_source_then_equal_donor() -> None:
    donor, source = geometry()
    out = build_fit_weights(donor, source, objective="SOURCE_DONOR_BALANCED_DIAGNOSTIC")
    assert out.source_mass[0] == pytest.approx(0.5)
    assert out.source_mass[1] == pytest.approx(0.5)
    assert out.donor_mass[0] == pytest.approx(0.25)
    assert out.donor_mass[1] == pytest.approx(0.25)
    assert out.donor_mass[2] == pytest.approx(0.5)


def test_duplicating_identical_rows_within_donor_does_not_change_production_moments() -> None:
    donor = np.array([0, 1])
    source = np.array([0, 1])
    X = np.array([[1.0, 2.0], [3.0, 4.0]])
    y = np.array([5.0, 7.0])
    w = build_fit_weights(donor, source, objective="PRODUCTION_OBJECTIVE_MATCHED").row_weight
    g1, r1, yy1 = weighted_ridge_sufficient_statistics(X, y, w)

    donor2 = np.array([0, 0, 0, 1])
    source2 = np.array([0, 0, 0, 1])
    X2 = np.vstack([X[0], X[0], X[0], X[1]])
    y2 = np.array([5.0, 5.0, 5.0, 7.0])
    w2 = build_fit_weights(donor2, source2, objective="PRODUCTION_OBJECTIVE_MATCHED").row_weight
    g2, r2, yy2 = weighted_ridge_sufficient_statistics(X2, y2, w2)
    assert np.allclose(g1, g2)
    assert np.allclose(r1, r2)
    assert yy1 == pytest.approx(yy2)


def test_donor_with_multiple_sources_fails_closed() -> None:
    with pytest.raises(ValueError, match="exactly one source"):
        build_fit_weights([0, 0], [0, 1], objective="PRODUCTION_OBJECTIVE_MATCHED")


def test_weighted_ridge_recovers_planted_linear_signal() -> None:
    X = np.array([[-2.0], [-1.0], [1.0], [2.0]])
    y = 3.0 * X[:, 0]
    donor = np.array([0, 0, 1, 1])
    source = np.array([0, 0, 1, 1])
    for objective in (
        "CURRENT_CELL_WEIGHTED",
        "PRODUCTION_OBJECTIVE_MATCHED",
        "SOURCE_DONOR_BALANCED_DIAGNOSTIC",
    ):
        w = build_fit_weights(donor, source, objective=objective).row_weight
        beta = solve_weighted_ridge(X, y, w, alpha=0.0)
        assert beta[0] == pytest.approx(3.0)
