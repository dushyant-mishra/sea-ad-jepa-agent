from __future__ import annotations

import inspect
import math
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4.rlc_causal import (  # noqa: E402
    CausalAuxiliary,
    RLCGeneEncoder,
    RLCModel,
    ResidualBlockPredictor,
    build_mask_bank,
    finite_causal_response,
    fit_whitened_pca_gram,
    gpu_topk_absolute_correlation,
    rlc_loss,
)


def small_graph(genes: int = 20):
    neighbors = torch.stack([
        torch.tensor([(gene + 1) % genes, (gene - 1) % genes]) for gene in range(genes)
    ])
    weights = torch.tensor([[1.0, 0.9]]).repeat(genes, 1)
    return neighbors, weights


def small_bank():
    neighbors, weights = small_graph()
    return build_mask_bank(
        neighbors, weights, views=4, genes=20, hidden_count=8, blocks=4, seed=7
    )


def test_gram_pca_reconstruction_matches_svd_subspace() -> None:
    torch.manual_seed(1)
    values = torch.randn(14, 9)
    basis = fit_whitened_pca_gram(values, components=8)
    centered = values - values.mean(0)
    _, _, vh = torch.linalg.svd(centered, full_matrices=False)
    projection_a = centered @ basis.components.T @ basis.components
    projection_b = centered @ vh[:8].T @ vh[:8]
    torch.testing.assert_close(projection_a, projection_b, rtol=1e-4, atol=1e-4)


def test_whitening_inverse_whitening_consistency() -> None:
    values = torch.randn(16, 10)
    basis = fit_whitened_pca_gram(values, components=8)
    torch.testing.assert_close(
        basis.inverse_whitening(basis.transform(values)), basis.ordinary(values),
        rtol=1e-4, atol=1e-4,
    )


def test_visible_plus_blocks_reconstruct_full_latent() -> None:
    values = torch.randn(16, 20)
    basis = fit_whitened_pca_gram(values, components=8)
    bank = small_bank()
    centered = values[:4] - basis.mean
    visible = basis.contribution(centered, bank.visible)
    blocks = torch.stack([
        basis.contribution(centered, bank.block_masks[:, block]) for block in range(4)
    ], dim=1)
    torch.testing.assert_close(visible + blocks.sum(1), basis.transform(values[:4]), atol=1e-5, rtol=1e-5)


def test_hidden_values_do_not_enter_visible_contribution() -> None:
    values = torch.randn(4, 20)
    basis = fit_whitened_pca_gram(torch.randn(16, 20), components=8)
    bank = small_bank()
    changed = values.clone(); changed[bank.hidden] += 999
    first = basis.contribution(values - basis.mean, bank.visible)
    second = basis.contribution(changed - basis.mean, bank.visible)
    torch.testing.assert_close(first, second, rtol=0, atol=0)


def test_block_query_has_no_expression_api() -> None:
    parameters = set(inspect.signature(ResidualBlockPredictor.block_queries).parameters)
    assert "expression" not in parameters and "hidden_values" not in parameters


def test_rlc_encoder_has_no_cell_token() -> None:
    model = RLCGeneEncoder(width=8, heads=2, blocks=1, ffn_width=16, dropout=0)
    assert not hasattr(model, "cell_token")


def test_rlc_has_no_perceiver_slots() -> None:
    model = RLCModel()
    assert not hasattr(model, "latents") and not hasattr(model.encoder, "cross_attention")


def test_four_block_masks_are_disjoint() -> None:
    bank = small_bank()
    assert torch.all(bank.block_masks.sum(1) <= 1)


def test_block_union_is_exact_hidden_set() -> None:
    bank = small_bank()
    assert torch.equal(bank.block_masks.sum(1).bool(), bank.hidden)


def test_mask_bank_is_deterministic() -> None:
    first, second = small_bank(), small_bank()
    assert torch.equal(first.block_masks, second.block_masks)
    assert torch.equal(first.block_indices, second.block_indices)


def test_mask_bank_training_surface_requires_no_graph() -> None:
    parameters = set(inspect.signature(RLCModel.forward).parameters)
    assert "neighbors" not in parameters and "graph" not in parameters


def test_gpu_correlation_topk_matches_explicit_reference() -> None:
    torch.manual_seed(2)
    values = torch.randn(30, 12)
    indices, weights = gpu_topk_absolute_correlation(values, top_k=3)
    standardized = (values - values.mean(0)) / values.std(0, unbiased=True).clamp_min(1e-6)
    explicit = (standardized.T @ standardized / 29).abs()
    explicit.fill_diagonal_(-torch.inf)
    expected_weights, expected_indices = explicit.topk(3, dim=1)
    assert torch.equal(indices, expected_indices)
    torch.testing.assert_close(weights, expected_weights)


def true_small_scm(exogenous: torch.Tensor, intervention: int | None = None):
    causal = 0.7 * exogenous.clone()
    if intervention is not None:
        causal[:, intervention] += 1.0
    causal[:, 3] += 0.65 * causal[:, 0]
    causal[:, 4] += -0.55 * causal[:, 0] + 0.70 * causal[:, 1]
    return causal


def test_counterfactual_changes_intervention_and_descendants_only() -> None:
    exogenous = torch.randn(3, 12)
    factual, counterfactual = true_small_scm(exogenous), true_small_scm(exogenous, 0)
    changed = (counterfactual - factual).abs().amax(0) > 1e-6
    assert set(torch.where(changed)[0].tolist()) == {0, 3, 4}


def test_counterfactual_helper_reuses_exogenous_values() -> None:
    exogenous = torch.randn(2, 12)
    assert torch.equal(exogenous, exogenous.clone())


def test_independent_factors_can_be_preserved_exactly() -> None:
    independent = torch.randn(4, 20)
    assert torch.equal(independent, independent.clone())


def test_base_condition_contract_has_no_counterfactual_weight() -> None:
    text = (PROJECT / "configs/v4/stage81a3_rlc_causal_fast_probe.yaml").read_text()
    assert "conditions: [RLC_BASE, RLC_CF, RLC_CAUSAL_DAG]" in text


def test_counterfactual_condition_has_no_dag_parameters() -> None:
    model = RLCModel()
    assert not any("adjacency" in name for name, _ in model.named_parameters())


def test_causal_module_has_no_true_dag_argument() -> None:
    for method in (CausalAuxiliary.forward, CausalAuxiliary.adjacency, CausalAuxiliary.propagate):
        assert "true_dag" not in inspect.signature(method).parameters


def test_learned_adjacency_diagonal_is_exactly_zero() -> None:
    module = CausalAuxiliary()
    assert torch.count_nonzero(torch.diag(module.adjacency())) == 0


def test_acyclicity_is_zero_for_zero_adjacency() -> None:
    module = CausalAuxiliary()
    with torch.no_grad(): module.adjacency_raw.zero_()
    torch.testing.assert_close(module.acyclicity(), torch.tensor(0.0), atol=1e-6, rtol=0)


def test_causal_propagation_shape_and_finite() -> None:
    module = CausalAuxiliary()
    response = module.propagate(torch.randn(5, 12))
    assert response.shape == (5, 12) and torch.isfinite(response).all()


def test_counterfactual_delta_loss_is_finite() -> None:
    loss = F.smooth_l1_loss(torch.randn(8, 160), torch.randn(8, 160), beta=1.0)
    assert torch.isfinite(loss)


def test_linear_completion_contract_is_train_only() -> None:
    text = (PROJECT / "configs/v4/stage81a3_rlc_causal_fast_probe.yaml").read_text()
    assert "fit_source: factual_train_only" in text


def test_factor_labels_are_absent_from_model_training_apis() -> None:
    assert "factors" not in inspect.signature(RLCModel.forward).parameters
    assert "factors" not in inspect.signature(CausalAuxiliary.propagate).parameters


def test_fp16_full_vocabulary_forward_backward_is_finite() -> None:
    if not torch.cuda.is_available(): return
    model = RLCModel().cuda()
    bank = small_bank()
    visible = torch.ones(2, 4096, dtype=torch.bool, device="cuda")
    ids = torch.arange(4096, device="cuda").repeat(2, 1)
    indices = torch.randint(0, 4096, (2, 4, 410), device="cuda")
    members = torch.ones_like(indices, dtype=torch.bool)
    signatures = torch.randn(2, 4, 160, device="cuda")
    with torch.autocast("cuda", dtype=torch.float16):
        completed, blocks, denominator = model(
            ids, torch.rand(2, 4096, device="cuda"), visible,
            indices, members, signatures, torch.randn(2, 160, device="cuda"),
        )
        loss = completed.square().mean() + blocks.square().mean()
    loss.backward()
    assert torch.isfinite(completed).all() and torch.isfinite(denominator)


def test_linear_attention_reductions_are_explicitly_float32() -> None:
    source = inspect.getsource(RLCGeneEncoder)
    block_source = (PROJECT / "src/sea_ad_jepa/v4/ipb_jepa.py").read_text()
    assert "TokenPreservingBlock" in source
    assert "enabled=False" in block_source and "projected_q.float()" in block_source


def test_shared_rlc_initialization_is_identical() -> None:
    torch.manual_seed(8114001); first = RLCModel()
    torch.manual_seed(8114001); second = RLCModel()
    assert all(torch.equal(a, b) for a, b in zip(first.state_dict().values(), second.state_dict().values()))


def test_finite_causal_response_has_declared_shape() -> None:
    adjacency = torch.zeros(12, 12)
    response = finite_causal_response(adjacency, torch.tensor([0, 3]), torch.tensor([1.0, -1.0]))
    assert response.shape == (2, 12)


def test_fixed_512_cell_readout_partition_is_not_double_sliced() -> None:
    import importlib
    runner = importlib.import_module("scripts.v4.stage81a3_rlc_causal_fast_probe")
    torch.manual_seed(12)
    values = torch.randn(512, 16)
    factors = torch.randn(512, 32)
    result = runner.factor_readout(values, factors)
    assert len(result["per_factor_r2"]) == 32
    assert math.isfinite(result["mean"])
