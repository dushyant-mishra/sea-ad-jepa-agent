import numpy as np
import pytest

from sea_ad_jepa.v5.latent_state_decomposition_v1 import crossfit_latent_state_decomposition


def fixture(with_interaction: bool):
    rng = np.random.default_rng(4)
    address_effect = np.array([[0.0, 0.0], [2.0, 0.0], [-1.0, 1.0]])
    context_effect = np.array([[0.0, 0.0], [0.0, 2.0], [1.0, -1.0], [-2.0, 0.0]])
    interaction = rng.normal(size=(3, 4, 2)) * (2.0 if with_interaction else 0.0)
    rows = []
    for rep in range(4):
        for a in range(3):
            for c in range(4):
                y = address_effect[a] + context_effect[c] + interaction[a, c]
                rows.append((f"a{a}", f"c{c}", rep, y))
    state = np.vstack([r[3] for r in rows])
    address = [r[0] for r in rows]
    context = [r[1] for r in rows]
    fold = [r[2] for r in rows]
    return state, address, context, fold


def test_joint_crossfit_detects_repeated_query_context_interaction() -> None:
    args = fixture(True)
    out = crossfit_latent_state_decomposition(*args)
    assert out.unseen_joint_rows == 0
    assert out.joint_skill_vs_grand > out.additive_skill_vs_grand
    assert out.joint_increment_over_additive > 0
    assert out.oof_joint_sse == pytest.approx(0.0, abs=1e-20)


def test_without_interaction_additive_and_joint_are_equivalent() -> None:
    args = fixture(False)
    out = crossfit_latent_state_decomposition(*args)
    assert out.oof_additive_sse == pytest.approx(0.0, abs=1e-20)
    assert out.oof_joint_sse == pytest.approx(0.0, abs=1e-20)
    assert out.joint_increment_over_additive == pytest.approx(0.0, abs=1e-15)


def test_unseen_joint_pairs_are_counted_not_silently_called_interaction() -> None:
    state = np.array([[0.0], [1.0], [2.0], [3.0]])
    address = ["a", "a", "b", "b"]
    context = ["x", "y", "x", "y"]
    fold = [0, 1, 0, 1]
    out = crossfit_latent_state_decomposition(state, address, context, fold)
    assert out.unseen_joint_rows == 4


def test_no_in_sample_fallback_when_only_one_fold() -> None:
    with pytest.raises(ValueError, match="at least two folds"):
        crossfit_latent_state_decomposition(
            [[0.0], [1.0]], ["a", "a"], ["c", "c"], [0, 0]
        )


def test_constant_teacher_state_is_non_estimable_not_perfect() -> None:
    with pytest.raises(ValueError, match="not estimable"):
        crossfit_latent_state_decomposition(
            np.ones((4, 2)), ["a", "a", "b", "b"], ["x", "y", "x", "y"], [0, 1, 0, 1]
        )
