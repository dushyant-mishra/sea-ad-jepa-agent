import numpy as np
import pytest

from sea_ad_jepa.v5.shortcut_consequence_curve_v1 import (
    BiologicalNegligibilityAuthorityV1,
    characterize_shortcut_consequence_curve,
    evaluate_biological_negligibility_frontier,
)


def authority(eps_num=2, eps_den=100):
    return BiologicalNegligibilityAuthorityV1(
        authority_id="fixture-epsilon",
        fidelity_functional_id="FIXTURE_BOUNDED_STATE_FIDELITY",
        epsilon_numerator=eps_num,
        epsilon_denominator=eps_den,
        scientific_rationale_id="FIXTURE_ONLY__NOT_PRODUCTION_AUTHORITY",
        scientific_rationale_sha256="a" * 64,
    )


def test_monotone_curve_yields_only_a_grid_frontier() -> None:
    curve = characterize_shortcut_consequence_curve(
        [0.0, 0.01, 0.02, 0.04],
        np.array([
            [1.00, 1.00, 1.00],
            [0.99, 0.99, 0.99],
            [0.97, 0.97, 0.97],
            [0.94, 0.94, 0.94],
        ]),
    )
    out = evaluate_biological_negligibility_frontier(curve, authority(2, 100))
    assert out.state == "GRID_FRONTIER_IDENTIFIED__NOT_TERMINAL_MARGIN_AUTHORITY"
    assert out.grid_frontier_residual == pytest.approx(0.01)
    assert out.first_exceeding_residual == pytest.approx(0.02)


def test_nonmonotone_consequence_curve_refuses_margin_freeze() -> None:
    curve = characterize_shortcut_consequence_curve(
        [0.0, 0.01, 0.02, 0.04],
        np.array([
            [1.00, 1.00],
            [0.97, 0.97],
            [0.99, 0.99],
            [0.94, 0.94],
        ]),
    )
    assert not curve.monotone_non_decreasing_harm
    out = evaluate_biological_negligibility_frontier(curve, authority())
    assert out.state == "NONMONOTONE_CONSEQUENCE_CURVE__NO_MARGIN_FREEZE"
    assert out.grid_frontier_residual is None


def test_grid_that_never_crosses_epsilon_is_not_extrapolated() -> None:
    curve = characterize_shortcut_consequence_curve(
        [0.0, 0.01, 0.02],
        np.array([[0.8, 0.8], [0.795, 0.795], [0.79, 0.79]]),
    )
    out = evaluate_biological_negligibility_frontier(curve, authority(5, 100))
    assert out.state == "GRID_DOES_NOT_REACH_BIOLOGICAL_CONSEQUENCE_BOUNDARY"
    assert out.first_exceeding_residual is None
    assert out.grid_frontier_residual == pytest.approx(0.02)


def test_epsilon_must_be_prospective_and_hash_bound() -> None:
    with pytest.raises(ValueError, match="freeze before terminal outcomes"):
        BiologicalNegligibilityAuthorityV1(
            authority_id="bad",
            fidelity_functional_id="S",
            epsilon_numerator=1,
            epsilon_denominator=100,
            scientific_rationale_id="bad",
            scientific_rationale_sha256="b" * 64,
            terminal_outcomes_inspected_before_freeze=True,
        ).validate()
    with pytest.raises(ValueError, match="SHA-256"):
        BiologicalNegligibilityAuthorityV1(
            authority_id="bad",
            fidelity_functional_id="S",
            epsilon_numerator=1,
            epsilon_denominator=100,
            scientific_rationale_id="bad",
            scientific_rationale_sha256="not-a-hash",
        ).validate()


def test_residual_grid_must_be_prospective_shape_not_unsorted_or_duplicate() -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        characterize_shortcut_consequence_curve(
            [0.0, 0.02, 0.01],
            np.ones((3, 2)),
        )
    with pytest.raises(ValueError, match="strictly increasing"):
        characterize_shortcut_consequence_curve(
            [0.0, 0.01, 0.01],
            np.ones((3, 2)),
        )


def test_fidelity_is_bounded_and_paired_across_levels() -> None:
    with pytest.raises(ValueError, match="bounded"):
        characterize_shortcut_consequence_curve(
            [0.0, 0.01],
            [[1.0, 0.9], [1.1, 0.8]],
        )
    with pytest.raises(ValueError, match="align residual"):
        characterize_shortcut_consequence_curve(
            [0.0, 0.01, 0.02],
            [[1.0, 0.9], [0.9, 0.8]],
        )
