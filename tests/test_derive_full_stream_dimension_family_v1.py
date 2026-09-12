import importlib.util
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "scripts" / "v5_anticheat" / "derive_full_stream_dimension_family_v1.py"
spec = importlib.util.spec_from_file_location("derive_full_stream_dimension_family_v1", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def shared(rank, score, se, *, supported=True, heldout_supported=None):
    if heldout_supported is None:
        heldout_supported = supported
    return {
        "rank": rank,
        "held_donor_cross_view_mean": score,
        "held_donor_cross_view_se": se,
        "signal_above_full_refit_matched_null": supported,
        "donor_resampled_subspace_stability": supported,
        "held_donor_cross_view_predictability": heldout_supported,
        "independent_view_agreement": supported,
        "measurement_shortcut_increment_pass": supported,
    }


def private(rank, score, se, *, supported=True):
    return {
        "rank": rank,
        "held_donor_increment_mean": score,
        "held_donor_increment_se": se,
        "held_donor_increment_pass": supported,
        "held_operator_increment_pass": supported,
        "measurement_shortcut_increment_pass": supported,
        "same_cell_technical_intervention_stability_pass": supported,
    }


def obs(rank, score, se):
    return {
        "rank": rank,
        "held_operator_reconstruction_mean": score,
        "held_operator_reconstruction_se": se,
    }


def test_shared_selects_smallest_jointly_supported_prefix_within_one_se_of_best():
    rows = [
        shared(1, 0.70, 0.02),
        shared(2, 0.78, 0.02),
        shared(3, 0.79, 0.03),
        shared(4, 0.80, 0.02, supported=False),
    ]
    out = m.select_shared_dimension(rows)
    assert out["terminal"] == "PASS_D_SHARED_SELECTED"
    assert out["D_shared"] == 2
    assert out["contiguous_prefix_supported_through"] == 3
    assert out["one_se_threshold"] == 0.76
    assert out["search_boundary_supported"] is False


def test_shared_held_donor_predictability_is_a_required_joint_gate():
    rows = [
        shared(1, 0.70, 0.02),
        shared(2, 0.78, 0.02, supported=True, heldout_supported=False),
        shared(3, 0.79, 0.03),
    ]
    out = m.select_shared_dimension(rows)
    assert out["terminal"] == "PASS_D_SHARED_SELECTED"
    assert out["D_shared"] == 1
    assert out["contiguous_prefix_supported_through"] == 1
    assert out["search_boundary_supported"] is False


def test_shared_supported_boundary_requires_expansion_not_selection():
    rows = [shared(1, 0.70, 0.02), shared(2, 0.78, 0.02), shared(3, 0.79, 0.03)]
    out = m.select_shared_dimension(rows)
    assert out["terminal"] == "EXPAND_SHARED_SEARCH_ENVELOPE"
    assert out["D_shared"] is None
    assert out["contiguous_prefix_supported_through"] == 3
    assert out["search_boundary_supported"] is True


def test_shared_zero_is_lawful_when_first_positive_rank_fails_joint_support():
    rows = [shared(1, 0.70, 0.02, supported=False), shared(2, 0.75, 0.02, supported=False)]
    out = m.select_shared_dimension(rows)
    assert out["terminal"] == "PASS_D_SHARED_SELECTED"
    assert out["D_shared"] == 0
    assert out["contiguous_prefix_supported_through"] == 0


def test_private_candidate_uses_same_one_se_prefix_discipline_after_joint_checks():
    rows = [
        private(1, 0.05, 0.01),
        private(2, 0.08, 0.02),
        private(3, 0.081, 0.01, supported=False),
    ]
    out = m.select_private_dimension(rows)
    assert out["terminal"] == "PASS_D_PRIVATE_SELECTED"
    assert out["D_private"] == 2
    assert out["contiguous_prefix_supported_through"] == 2
    assert out["one_se_threshold"] == 0.06
    assert out["search_boundary_supported"] is False


def test_private_zero_is_lawful_and_supported_boundary_forces_expansion():
    zero = m.select_private_dimension([private(1, 0.02, 0.01, supported=False)])
    assert zero["D_private"] == 0
    assert zero["terminal"] == "PASS_D_PRIVATE_SELECTED"

    expand = m.select_private_dimension([private(1, 0.02, 0.01), private(2, 0.03, 0.01)])
    assert expand["D_private"] is None
    assert expand["terminal"] == "EXPAND_PRIVATE_SEARCH_ENVELOPE"
    assert expand["search_boundary_supported"] is True


def test_observation_rank_uses_smallest_rank_within_one_se_of_best_held_operator_score():
    rows = [obs(1, 0.70, 0.02), obs(2, 0.77, 0.03), obs(3, 0.76, 0.02), obs(4, 0.74, 0.02)]
    out = m.select_observation_dimension(rows)
    assert out["terminal"] == "PASS_D_OBS_SELECTED"
    assert out["D_obs"] == 2
    assert out["best_rank"] == 2
    assert out["one_se_threshold"] == 0.74


def test_observation_best_rank_at_search_boundary_requires_expansion():
    out = m.select_observation_dimension([obs(1, 0.70, 0.02), obs(2, 0.76, 0.02), obs(3, 0.80, 0.02)])
    assert out["terminal"] == "EXPAND_OBSERVATION_SEARCH_ENVELOPE"
    assert out["D_obs"] is None
    assert out["search_boundary_best"] is True


def test_nonconsecutive_rank_rows_are_rejected():
    try:
        m.select_shared_dimension([shared(1, 0.1, 0.01), shared(3, 0.2, 0.01, supported=False)])
    except ValueError as exc:
        assert "consecutive" in str(exc)
    else:
        raise AssertionError("nonconsecutive rank rows must fail")
