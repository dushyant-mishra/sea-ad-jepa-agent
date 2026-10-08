from __future__ import annotations

import inspect
import math
import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4.belief_geometry import covariance  # noqa: E402
from sea_ad_jepa.v4.oof_covariance import (  # noqa: E402
    construct_lrd,
    deterministic_fold_ids,
    fold_indices,
    lrd_gaussian_nll,
    positive_correlated_spectrum,
    select_correlated_rank,
    shared_architecture_rank,
    woodbury_quadratic_logdet,
)


def test_eight_fold_assignment_is_deterministic_balanced() -> None:
    first = deterministic_fold_ids(3072, 8)
    second = deterministic_fold_ids(3072, 8)
    torch.testing.assert_close(first, second)
    assert torch.bincount(first).tolist() == [384] * 8


def test_every_train_cell_is_held_out_exactly_once() -> None:
    folds = deterministic_fold_ids(3072, 8)
    counts = torch.zeros(3072, dtype=torch.int64)
    for fold in range(8):
        _, held_out = fold_indices(folds, fold)
        counts[held_out] += 1
    assert torch.all(counts == 1)


def test_ridge_prediction_is_cast_to_reppca_target_dtype() -> None:
    script = (PROJECT / "scripts/v4/stage81a3_rbb_oof_covariance_audit.py").read_text()
    assert "return prediction.to(target.dtype)" in script


def test_no_fold_predicts_its_fitting_cells() -> None:
    folds = deterministic_fold_ids(32, 8)
    for fold in range(8):
        fitting, held_out = fold_indices(folds, fold)
        assert not torch.isin(held_out, fitting).any()


def test_factor_labels_are_absent_from_fitting_surface() -> None:
    script = (PROJECT / "scripts/v4/stage81a3_rbb_oof_covariance_audit.py").read_text()
    assert "fixture.factors" not in script
    assert "factors" not in inspect.signature(construct_lrd).parameters


def test_lambda_norm_is_absent_from_covariance_fitting() -> None:
    script = (PROJECT / "scripts/v4/stage81a3_rbb_oof_covariance_audit.py").read_text()
    assert "fixture.lambda_norm" not in script


def test_oof_covariance_is_symmetric() -> None:
    matrix = covariance(torch.randn(30, 7))
    torch.testing.assert_close(matrix, matrix.T, rtol=0, atol=0)


def test_positive_correlated_spectrum_discards_nonpositive_values() -> None:
    matrix = torch.tensor([[2.0, 1.0], [1.0, 3.0]])
    values, vectors, residual = positive_correlated_spectrum(matrix)
    assert values.tolist() == [1.0]
    assert vectors.shape == (2, 1)
    torch.testing.assert_close(torch.diag(residual), torch.zeros(2, dtype=torch.float64))


def test_rank_selection_uses_squared_positive_energy() -> None:
    values = torch.tensor([4.0, 3.0, 2.0, 1.0, .5])
    rank, captured, reached = select_correlated_rank(values, target=.5, minimum=1, maximum=5)
    assert rank == 1
    assert captured == 16.0 / 30.25
    assert reached


def test_rank_selection_obeys_cap_32() -> None:
    values = torch.ones(100)
    rank, _, reached = select_correlated_rank(values, target=.5, minimum=4, maximum=32)
    assert rank == 32
    assert not reached


def test_lrd_diagonal_floor_is_positive() -> None:
    matrix = covariance(torch.randn(300, 12))
    result = construct_lrd(matrix, 4)
    assert result["floor"] > 0
    assert torch.all(result["diagonal"] >= result["floor"])


def test_lrd_covariance_is_positive_definite() -> None:
    matrix = covariance(torch.randn(300, 12))
    result = construct_lrd(matrix, 4)
    assert torch.linalg.eigvalsh(result["matrix"]).min() > 0
    assert math.isfinite(result["offdiagonal_energy_ratio"])
    assert math.isfinite(result["offdiagonal_reconstruction_explained_fraction"])


def test_woodbury_inverse_quadratic_matches_dense() -> None:
    torch.manual_seed(4)
    diagonal = torch.rand(7, dtype=torch.float64) + .5
    u = torch.randn(7, 3, dtype=torch.float64) * .2
    values = torch.randn(9, 7, dtype=torch.float64)
    quadratic, _ = woodbury_quadratic_logdet(values, diagonal, u)
    matrix = torch.diag(diagonal) + u @ u.T
    expected = (values * torch.linalg.solve(matrix, values.T).T).sum(1)
    torch.testing.assert_close(quadratic, expected, rtol=1e-10, atol=1e-10)


def test_matrix_determinant_lemma_matches_dense_logdet() -> None:
    torch.manual_seed(5)
    diagonal = torch.rand(7, dtype=torch.float64) + .5
    u = torch.randn(7, 3, dtype=torch.float64) * .2
    _, logdet = woodbury_quadratic_logdet(torch.zeros(1, 7), diagonal, u)
    expected = torch.linalg.slogdet(torch.diag(diagonal) + u @ u.T).logabsdet
    torch.testing.assert_close(logdet, expected, rtol=1e-10, atol=1e-10)


def test_lrd_nll_matches_dense_nll() -> None:
    torch.manual_seed(6)
    diagonal = torch.rand(7, dtype=torch.float64) + .5
    u = torch.randn(7, 3, dtype=torch.float64) * .2
    values = torch.randn(9, 7, dtype=torch.float64)
    actual = lrd_gaussian_nll(values, diagonal, u)
    matrix = torch.diag(diagonal) + u @ u.T
    inverse = torch.linalg.inv(matrix)
    quadratic = torch.einsum("bi,ij,bj->b", values, inverse, values)
    expected = .5 * (7 * math.log(2 * math.pi) + torch.linalg.slogdet(matrix).logabsdet + quadratic)
    torch.testing.assert_close(actual, expected, rtol=1e-10, atol=1e-10)


def test_shared_architecture_rank_rule_is_deterministic_and_ceil_median() -> None:
    ranks = {"RANDOM_40": [5, 6, 7, 8], "COEXPRESSION_BLOCK_40": [9, 10, 11, 12]}
    assert shared_architecture_rank(ranks) == 11
    assert shared_architecture_rank(ranks) == 11


def test_sealed_data_cannot_enter_rank_selection_api() -> None:
    assert set(inspect.signature(select_correlated_rank).parameters) == {
        "positive_values", "target", "minimum", "maximum"
    }
    script = (PROJECT / "scripts/v4/stage81a3_rbb_oof_covariance_audit.py").read_text()
    assert script.index("architecture_rank = shared_architecture_rank") < script.index("scores = score_covariances")


def test_runner_has_no_real_rna_surface() -> None:
    script = (PROJECT / "scripts/v4/stage81a3_rbb_oof_covariance_audit.py").read_text().lower()
    assert "h5ad" not in script and "real_rna_accessed\": false" in script


def test_runner_has_no_pathology_surface() -> None:
    script = (PROJECT / "scripts/v4/stage81a3_rbb_oof_covariance_audit.py").read_text().lower()
    assert "data/pathology" not in script and "pathology_opened\": false" in script
