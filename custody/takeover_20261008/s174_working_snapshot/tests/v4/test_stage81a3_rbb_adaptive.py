from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest
import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4.rbb_adaptive import (
    R_MAX,
    RBBAdaptiveBelief,
    cross_replicate_targets,
    dense_covariance,
    fuse_gaussian_beliefs,
    mask_context_features,
    nested_visibility_masks,
    random_mask_bank,
    rbb_nll,
    structured_gaussian_terms,
)


@pytest.fixture(scope="module")
def case():
    torch.manual_seed(8114001)
    genes, width, batch = 64, 160, 2
    model = RBBAdaptiveBelief(vocabulary_size=genes, gradient_checkpointing=False)
    model.eval()
    ids = torch.arange(genes).repeat(batch, 1)
    expression = torch.randn(batch, genes)
    visible = torch.zeros(batch, genes, dtype=torch.bool)
    visible[:, :38] = True
    state = torch.randn(batch, width)
    context = torch.randn(batch, 512)
    prior_d = torch.full((width,), 0.8)
    prior_u = torch.zeros(width, R_MAX)
    noise = torch.full((width,), 0.2)
    return model, ids, expression, visible, state, context, prior_d, prior_u, noise


def run(case, expression=None, **kwargs):
    model, ids, values, visible, state, context, prior_d, prior_u, noise = case
    return model(
        ids, values if expression is None else expression, visible, state, context,
        prior_d, prior_u, noise, **kwargs,
    )


def test_01_no_cell_token(case):
    assert not hasattr(case[0].ledger, "cell_token")


def test_02_no_perceiver(case):
    assert "perceiver" not in type(case[0]).__name__.lower()
    assert all("perceiver" not in type(module).__name__.lower() for module in case[0].modules())


def test_03_no_learned_global_pooling(case):
    assert all("pool" not in name.lower() for name, _ in case[0].named_modules())


def test_04_ledger_preserves_requested_tokens(case):
    output = run(case)
    assert output.molecular_evidence_tokens.shape == (2, 64, 160)


def test_05_production_ledger_contract():
    model = RBBAdaptiveBelief(gradient_checkpointing=False)
    assert model.ledger.vocabulary_size == 4096


def test_06_hidden_expression_is_inaccessible(case):
    changed = case[2].clone()
    changed[~case[3]] = 1.0e5
    first, second = run(case), run(case, changed)
    assert torch.equal(first.posterior_missing_mean, second.posterior_missing_mean)
    assert torch.equal(first.correlated_activation_amplitudes, second.correlated_activation_amplitudes)


def test_07_measurement_state_distinguishes_zero_from_missing(case):
    embedding = case[0].ledger.measurement_state.weight.detach()
    assert not torch.equal(embedding[0], embedding[1])


def test_08_reppca_is_not_a_model_parameter(case):
    assert all("basis" not in name and "reppca" not in name for name, _ in case[0].named_parameters())


def test_09_visible_state_is_exact(case):
    output = run(case)
    assert torch.equal(output.visible_state, case[4])


def test_10_full_state_additivity():
    x, mean, analysis = torch.randn(3, 12), torch.randn(12), torch.randn(5, 12)
    visible = torch.zeros(12, dtype=torch.bool); visible[:7] = True
    hidden = ~visible
    full = (x - mean) @ analysis.T
    left = ((x - mean) * visible) @ analysis.T
    right = ((x - mean) * hidden) @ analysis.T
    assert torch.allclose(full, left + right, atol=1e-5)


def test_11_a_visible_targets_b_hidden():
    a, b = torch.ones(2, 4), torch.full((2, 4), 2.0)
    analysis, mean, hidden = torch.eye(4), torch.zeros(4), torch.ones(4, dtype=torch.bool)
    target_ab, _ = cross_replicate_targets(a, b, analysis, mean, hidden)
    assert torch.equal(target_ab, b)


def test_12_b_visible_targets_a_hidden():
    a, b = torch.ones(2, 4), torch.full((2, 4), 2.0)
    analysis, mean, hidden = torch.eye(4), torch.zeros(4), torch.ones(4, dtype=torch.bool)
    _, target_ba = cross_replicate_targets(a, b, analysis, mean, hidden)
    assert torch.equal(target_ba, a)


def test_13_factor_labels_absent_training_api():
    assert "factor" not in inspect.signature(RBBAdaptiveBelief.forward).parameters


def test_14_lambda_norm_absent_loss_api():
    assert "lambda" not in inspect.signature(rbb_nll).parameters


def test_15_rmax_fixed_at_32():
    assert R_MAX == 32
    with pytest.raises(ValueError):
        RBBAdaptiveBelief(vocabulary_size=64, rank=16)


def test_16_correlated_amplitudes_nonnegative(case):
    assert torch.all(run(case).correlated_activation_amplitudes >= 0)


def test_17_correlated_directions_normalized(case):
    norms = case[0].normalized_directions().norm(dim=0)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-6)


def test_18_zero_amplitudes_diagonalize_evidence(case):
    output = run(case, diagonalize_evidence=True)
    assert torch.count_nonzero(output.evidence_low_rank) == 0


def test_19_evidence_covariance_positive_definite(case):
    output = run(case)
    assert torch.linalg.eigvalsh(dense_covariance(output.evidence_diagonal, output.evidence_low_rank)).min() > 0


def test_20_posterior_covariance_positive_definite(case):
    output = run(case)
    assert torch.linalg.eigvalsh(dense_covariance(output.conditional_diagonal, output.conditional_low_rank)).min() > 0


def test_21_total_covariance_positive_definite(case):
    output = run(case)
    assert torch.linalg.eigvalsh(dense_covariance(output.total_diagonal, output.total_low_rank)).min() > 0


def test_22_woodbury_inverse_parity():
    torch.manual_seed(2)
    d = torch.rand(3, 8) + .5; u = torch.randn(3, 8, 3) * .1; x = torch.randn(3, 8)
    _, q, _ = structured_gaussian_terms(x, d, u)
    dense = torch.stack([x[i] @ torch.linalg.solve(dense_covariance(d[i], u[i]), x[i]) for i in range(3)])
    assert torch.allclose(q, dense, atol=2e-5)


def test_23_woodbury_logdet_parity():
    torch.manual_seed(3)
    d = torch.rand(2, 8) + .5; u = torch.randn(2, 8, 3) * .1; x = torch.randn(2, 8)
    _, _, logdet = structured_gaussian_terms(x, d, u)
    dense = torch.stack([torch.linalg.slogdet(dense_covariance(d[i], u[i])).logabsdet for i in range(2)])
    assert torch.allclose(logdet, dense, atol=2e-5)


def test_24_structured_nll_dense_parity():
    torch.manual_seed(4)
    d = torch.rand(2, 8) + .5; u = torch.randn(2, 8, 3) * .1; x = torch.randn(2, 8)
    nll, _, _ = structured_gaussian_terms(x, d, u)
    dense = torch.stack([
        .5 * (8 * torch.log(torch.tensor(2 * torch.pi)) + torch.linalg.slogdet(dense_covariance(d[i], u[i])).logabsdet + x[i] @ torch.linalg.solve(dense_covariance(d[i], u[i]), x[i]))
        for i in range(2)
    ])
    assert torch.allclose(nll, dense, atol=2e-5)


def test_25_fusion_dense_parity():
    torch.manual_seed(5)
    m = torch.randn(2, 8); pd = torch.rand(8) + .5; pu = torch.randn(8, 3) * .1
    ed = torch.rand(2, 8) + .5; eu = torch.randn(2, 8, 3) * .1
    mean, d, u = fuse_gaussian_beliefs(m, pd, pu, ed, eu)
    for i in range(2):
        p, e = dense_covariance(pd, pu), dense_covariance(ed[i], eu[i])
        covariance = torch.linalg.inv(torch.linalg.inv(p) + torch.linalg.inv(e))
        expected = covariance @ torch.linalg.solve(e, m[i])
        assert torch.allclose(dense_covariance(d[i], u[i]), covariance, atol=2e-4)
        assert torch.allclose(mean[i], expected, atol=2e-4)


def test_26_weak_evidence_stays_near_prior():
    m = torch.ones(1, 4); pd = torch.ones(4); pu = torch.zeros(4, 1)
    mean, _, _ = fuse_gaussian_beliefs(m, pd, pu, torch.full((1, 4), 1e6), torch.zeros(1, 4, 1))
    assert mean.abs().max() < 1e-4


def test_27_precision_increases_evidence_influence():
    m = torch.ones(1, 4); pd = torch.ones(4); pu = torch.zeros(4, 1); u = torch.zeros(1, 4, 1)
    weak = fuse_gaussian_beliefs(m, pd, pu, torch.full((1, 4), 10.0), u)[0]
    strong = fuse_gaussian_beliefs(m, pd, pu, torch.full((1, 4), .1), u)[0]
    assert strong.mean() > weak.mean()


def test_28_visible_state_never_changes(case):
    before = case[4].clone(); _ = run(case)
    assert torch.equal(case[4], before)


def test_29_measurement_noise_separate(case):
    output = run(case)
    assert torch.equal(output.total_diagonal, output.conditional_diagonal + output.measurement_noise_diagonal)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA required")
def test_30_mixed_precision_forward_backward_finite():
    device = torch.device("cuda")
    model = RBBAdaptiveBelief(vocabulary_size=32, gradient_checkpointing=False).to(device).train()
    ids = torch.arange(32, device=device)[None]; x = torch.randn(1, 32, device=device)
    visible = torch.zeros(1, 32, dtype=torch.bool, device=device); visible[:, :20] = True
    with torch.autocast("cuda", dtype=torch.float16):
        output = model(ids, x, visible, torch.zeros(1, 160, device=device), torch.zeros(1, 512, device=device), torch.ones(160, device=device), torch.zeros(160, 32, device=device), torch.ones(160, device=device))
        loss = rbb_nll(output, torch.randn(1, 160, device=device))
    loss.backward()
    assert torch.isfinite(loss) and all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())


def test_31_nested_masks_are_nested():
    masks = nested_visibility_masks(torch.arange(20))
    assert torch.all(masks[.4] <= masks[.6]) and torch.all(masks[.6] <= masks[.8]) and torch.all(masks[.8] <= masks[1.0])


def test_32_random_mask_bank_deterministic():
    first = random_mask_bank(genes=64, hidden_count=26, views=8)
    second = random_mask_bank(genes=64, hidden_count=26, views=8)
    assert torch.equal(first, second) and torch.all(first.sum(1) == 26)


def test_33_mask_context_has_no_expression_argument():
    assert "expression" not in inspect.signature(mask_context_features).parameters


def test_34_no_oracle_mask_surface():
    source = inspect.getsource(random_mask_bank).lower() + inspect.getsource(mask_context_features).lower()
    assert "oracle" not in source and "factor" not in source


def test_35_real_rna_inaccessible():
    source = Path(inspect.getfile(RBBAdaptiveBelief)).read_text(encoding="utf-8").lower()
    assert "h5ad" not in source and "anndata" not in source and "cellxgene" not in source


def test_36_pathology_inaccessible():
    source = Path(inspect.getfile(RBBAdaptiveBelief)).read_text(encoding="utf-8").lower()
    assert "pathology" not in source and "amyloid" not in source and "disease" not in source
