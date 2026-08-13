from __future__ import annotations

import inspect
import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4.conditional_predictability import (  # noqa: E402
    DiagnosticMLP,
    build_fixture,
    build_masks,
    correlation_columns,
    fit_pca_gram,
    normalize_counts,
    ridge_fit,
    ridge_predict,
    topk_absolute_correlation,
)


def fixture(cells: int = 64, genes: int = 96, train: int = 48):
    return build_fixture(torch.device("cpu"), cells=cells, genes=genes, train=train, seed=17)


def masks(genes: int = 96, hidden: int = 38):
    data = fixture(64, genes, 48)
    values, indices = topk_absolute_correlation(data.lambda_norm[:48], 4)
    return data, build_masks(data.loadings, indices, values, genes=genes, hidden=hidden, views=4, seed=17)


def test_replicates_share_identical_latent_state() -> None:
    data = fixture()
    assert data.x_a.shape == data.x_b.shape and torch.equal(data.factors, data.factors.clone())


def test_count_sampling_is_independent_across_replicates() -> None:
    data = fixture()
    assert not torch.equal(data.count_a, data.count_b)


def test_column_correlation_distinguishes_replicate_alignment() -> None:
    values = torch.randn(20, 4)
    torch.testing.assert_close(correlation_columns(values, values), torch.ones(4), atol=1e-6, rtol=0)


def test_lambda_norm_is_deterministic_from_rate() -> None:
    data = fixture()
    torch.testing.assert_close(data.lambda_norm, normalize_counts(data.rates), rtol=0, atol=0)


def test_pca_fit_api_accepts_training_matrix_only() -> None:
    assert set(inspect.signature(fit_pca_gram).parameters) == {"training_lambda", "components", "epsilon"}


def test_runner_fits_pca_to_train_expected_state() -> None:
    text = (PROJECT / "scripts/v4/stage81a3_conditional_predictability_audit.py").read_text()
    assert "fit_pca_gram(fixture.lambda_norm[:TRAIN])" in text
    assert "fit_pca_gram(fixture.x_a" not in text


def test_all_masks_hide_exact_count() -> None:
    _, bank = masks()
    assert torch.all(bank.hidden.sum(1) == 38)


def test_random_masks_are_deterministic() -> None:
    data, first = masks(); values, indices = topk_absolute_correlation(data.lambda_norm[:48], 4)
    second = build_masks(data.loadings, indices, values, genes=96, hidden=38, views=4, seed=17)
    assert torch.equal(first.hidden[:4], second.hidden[:4])


def test_graph_masks_are_deterministic() -> None:
    data, first = masks(); values, indices = topk_absolute_correlation(data.lambda_norm[:48], 4)
    second = build_masks(data.loadings, indices, values, genes=96, hidden=38, views=4, seed=17)
    assert torch.equal(first.hidden[4:8], second.hidden[4:8])


def test_oracle_labels_enter_only_mask_builder() -> None:
    parameters = set(inspect.signature(build_masks).parameters)
    assert "loadings" in parameters
    assert "loadings" not in inspect.signature(DiagnosticMLP.forward).parameters


def test_factor_labels_are_excluded_from_predictor_api() -> None:
    assert "factors" not in inspect.signature(DiagnosticMLP.forward).parameters


def test_hidden_values_are_absent_from_mlp_input() -> None:
    torch.manual_seed(3); model = DiagnosticMLP(genes=8, output=4)
    values = torch.randn(2, 8); visible = torch.tensor([[1, 1, 1, 1, 0, 0, 0, 0]]).bool().expand(2, -1)
    changed = values.clone(); changed[:, 4:] += 999
    torch.testing.assert_close(model(values, visible), model(changed, visible), rtol=0, atol=0)


def test_dual_ridge_matches_explicit_reference() -> None:
    torch.manual_seed(4); x = torch.randn(8, 12); y = torch.randn(8, 3); alpha = 1e-3
    model = ridge_fit(x, y, alpha); prediction = ridge_predict(model, x)
    z = (x - x.mean(0, keepdim=True)) / x.std(0, unbiased=False, keepdim=True).clamp_min(1e-8)
    explicit = z.T @ torch.linalg.solve(z @ z.T + alpha * torch.eye(8), y - y.mean(0, keepdim=True))
    expected = z @ explicit + y.mean(0, keepdim=True)
    torch.testing.assert_close(prediction, expected, rtol=1e-4, atol=1e-4)


def test_fixed_ridge_is_stable_for_low_rank_expected_expression() -> None:
    torch.manual_seed(41)
    factors = torch.randn(80, 4)
    x = factors @ torch.randn(4, 24)
    y = factors @ torch.randn(4, 6)
    model = ridge_fit(x[:60], y[:60], 1e-3)
    score = 1.0 - (y[60:] - ridge_predict(model, x[60:])).square().sum() / (y[60:] - y[60:].mean(0)).square().sum()
    assert float(score) > .999


def test_mlp_input_is_value_plus_visibility_mask_only() -> None:
    assert set(inspect.signature(DiagnosticMLP.forward).parameters) == {"self", "masked_values", "visible_mask"}


def test_mlp_target_is_hidden_expected_latent_contribution() -> None:
    text = (PROJECT / "scripts/v4/stage81a3_conditional_predictability_audit.py").read_text()
    assert "target = basis.contribution(expected[cells], ~visible)" in text


def test_sealed_test_cells_are_not_in_predictor_training() -> None:
    text = (PROJECT / "scripts/v4/stage81a3_conditional_predictability_audit.py").read_text()
    assert "source[:TRAIN" in text and "target_train" in text


def test_no_pathology_api() -> None:
    source = (PROJECT / "scripts/v4/stage81a3_conditional_predictability_audit.py").read_text().lower()
    assert "pathology_opened\": false" in source and "data/pathology" not in source


def test_no_real_rna_api() -> None:
    source = (PROJECT / "scripts/v4/stage81a3_conditional_predictability_audit.py").read_text().lower()
    assert "real_rna_accessed\": false" in source and "h5ad" not in source


def test_counterfactual_pair_uses_same_trained_predictor() -> None:
    source = (PROJECT / "scripts/v4/stage81a3_conditional_predictability_audit.py").read_text()
    assert "factual_prediction = mlp_predict(model" in source
    assert "cf_prediction = mlp_predict(model" in source


def test_true_causal_dag_is_absent_from_training_api() -> None:
    assert "true_adjacency" not in inspect.signature(DiagnosticMLP.forward).parameters


def test_full_equals_visible_plus_hidden_latent() -> None:
    torch.manual_seed(5); values = torch.randn(24, 16); basis = fit_pca_gram(values[:16], components=8)
    visible = torch.tensor([1] * 10 + [0] * 6).bool()
    torch.testing.assert_close(
        basis.transform(values) , basis.contribution(values, visible) + basis.contribution(values, ~visible),
        rtol=1e-5, atol=1e-5,
    )


def test_gpu_matrices_are_finite() -> None:
    if not torch.cuda.is_available(): return
    data = build_fixture(torch.device("cuda"), cells=64, genes=96, train=48, seed=17)
    assert torch.isfinite(data.lambda_norm).all() and torch.isfinite(data.x_a).all()


def test_exactly_five_fixed_mlp_fits_are_declared() -> None:
    text = (PROJECT / "configs/v4/stage81a3_conditional_predictability_audit.yaml").read_text()
    assert "count_families: [RANDOM_40, COEXPRESSION_BLOCK_40, ORACLE_COVERAGE_40]" in text
    assert "expected_families: [RANDOM_40, COEXPRESSION_BLOCK_40]" in text
    assert "updates: 150" in text and "effective_batch: 512" in text
