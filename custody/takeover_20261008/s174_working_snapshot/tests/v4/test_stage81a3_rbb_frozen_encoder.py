from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest
import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src")); sys.path.insert(0, str(PROJECT / "scripts" / "v4"))

import stage81a3_rbb_frozen_encoder_probe as runner  # noqa: E402
from sea_ad_jepa.v4.rbb_adaptive import R_MAX, RBBAdaptiveBelief, rbb_nll  # noqa: E402


def small_model() -> RBBAdaptiveBelief:
    torch.manual_seed(8114001)
    model = RBBAdaptiveBelief(vocabulary_size=16, gradient_checkpointing=False)
    model.freeze_molecular_ledger()
    return model


def test_01_tokenizer_frozen():
    assert all(not p.requires_grad for p in small_model().ledger.tokenizer.parameters())


def test_02_all_six_encoder_blocks_frozen():
    model = small_model(); assert len(model.ledger.blocks) == 6
    assert all(not p.requires_grad for block in model.ledger.blocks for p in block.parameters())


def test_03_encoder_layernorms_frozen():
    model = small_model(); assert all(not p.requires_grad for name, p in model.ledger.named_parameters() if "norm" in name)


def test_04_encoder_ffns_frozen():
    model = small_model(); assert all(not p.requires_grad for name, p in model.ledger.named_parameters() if ".ffn." in name)


def test_05_attention_projections_frozen():
    model = small_model(); assert all(not p.requires_grad for name, p in model.ledger.named_parameters() if ".attention." in name)


def test_06_optimizer_excludes_molecular_parameters():
    model = small_model(); optimizer = torch.optim.AdamW(list(model.belief_parameters()), lr=1e-4, weight_decay=.01)
    audit = runner.optimizer_audit(model, optimizer); assert audit["optimizer_frozen_id_intersection_count"] == 0


def test_07_molecular_ledger_detached():
    model = small_model().train(); ids = torch.arange(16)[None]; x = torch.randn(1, 16); visible = torch.ones(1, 16, dtype=torch.bool)
    ledger, _ = model.encode_molecular_ledger(ids, x, visible); assert not ledger.requires_grad


def test_08_frozen_gradients_zero_after_backward():
    model = small_model(); sum(p.square().sum() for p in model.belief_parameters()).backward()
    assert runner.maximum_frozen_gradient(model) == 0


def test_09_frozen_hash_unchanged_after_optimizer_step():
    model = small_model(); before = runner.frozen_hashes(model); optimizer = torch.optim.AdamW(list(model.belief_parameters()), lr=1e-4)
    loss = sum(p.square().sum() for p in model.belief_parameters()); loss.backward(); optimizer.step()
    assert runner.frozen_hashes(model) == before


def test_10_frozen_hash_unchanged_after_150_mini_steps():
    model = small_model(); before = runner.frozen_hashes(model); optimizer = torch.optim.AdamW(list(model.belief_parameters()), lr=1e-4)
    parameter = next(model.belief_parameters())
    for _ in range(150):
        optimizer.zero_grad(); parameter.square().mean().backward(); optimizer.step()
    assert runner.frozen_hashes(model) == before


def test_11_step0_initialization_deterministic():
    assert runner.frozen_hashes(small_model()) == runner.frozen_hashes(small_model())


def test_12_same_mask_bank_contract():
    assert runner.base.HIDDEN == 1638 and runner.base.VISIBLE == 2458
    assert len(runner.base.random_mask_bank()) == 128


def test_13_same_seed():
    assert runner.base.SEED == 8114001


def test_14_same_optimizer_hyperparameters():
    text = inspect.getsource(runner.main) + inspect.getsource(runner.train_belief_only)
    assert "lr=1e-4" in text and "weight_decay=.01" in text and "base.UPDATES + 1" in text


def test_15_same_rmax():
    assert R_MAX == 32


def test_16_same_prior_helper_reused():
    assert "base.frozen_family_statistics" in inspect.getsource(runner.main)


def test_17_same_measurement_noise_reused():
    assert 'prior["noise_diagonal"]' in inspect.getsource(runner.train_belief_only)


def test_18_same_belief_architecture_reused():
    assert "RBBAdaptiveBelief" in inspect.getsource(runner.main)
    assert not (PROJECT / "src/sea_ad_jepa/v4/rbb_frozen.py").exists()


def test_19_same_nll_reused():
    assert "base.rbb_nll" in inspect.getsource(runner.train_belief_only)


def test_20_same_visible_state_contract():
    assert "base.make_microbatch" in inspect.getsource(runner.train_belief_only)


def test_21_same_cross_replicate_target():
    source = inspect.getsource(runner.base.make_microbatch)
    assert "fixture.x_b[indices]" in source and "fixture.x_a[indices]" in source


def test_22_hidden_expression_inaccessible():
    source = inspect.getsource(RBBAdaptiveBelief.forward)
    assert "visible_mask" in source and "encode_molecular_ledger" in source


def test_23_factor_labels_absent_training():
    assert "fixture.factors" not in inspect.getsource(runner.train_belief_only)


def test_24_lambda_norm_absent_training():
    assert "lambda_norm" not in inspect.getsource(runner.train_belief_only)


def test_25_no_real_rna():
    source = Path(runner.__file__).read_text().lower(); assert "anndata" not in source and "h5ad" not in source and "cellxgene" not in source


def test_26_no_pathology():
    source = Path(runner.__file__).read_text().lower(); assert "amyloid" not in source and "pathology" not in inspect.getsource(runner.train_belief_only).lower()


def test_27_correlated_amplitudes_persisted():
    source = inspect.getsource(runner.main); assert "amplitude_{rank:02d}" in source and "range(R_MAX)" in source


def test_28_replicate_factor_consistency_persisted():
    source = inspect.getsource(runner.main); assert "prediction_correlation" in source and "b_factor_r2_under_a_map" in source


def test_29_counterfactual_direction_uncertainty_persisted():
    source = inspect.getsource(runner.evaluate_counterfactual); assert "changed_direction_variance" in source


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA required")
def test_30_mixed_precision_belief_backward_finite():
    device = torch.device("cuda"); model = small_model().to(device).train()
    ids = torch.arange(16, device=device)[None]; x = torch.randn(1, 16, device=device); visible = torch.ones(1, 16, dtype=torch.bool, device=device)
    with torch.autocast("cuda", dtype=torch.float16):
        output = model(ids, x, visible, torch.zeros(1, 160, device=device), torch.zeros(1, 512, device=device), torch.ones(160, device=device), torch.zeros(160, 32, device=device), torch.ones(160, device=device))
        loss = rbb_nll(output, torch.randn(1, 160, device=device))
    loss.backward(); assert torch.isfinite(loss) and runner.maximum_frozen_gradient(model) == 0


def test_31_counterfactual_direction_matches_covariance_dtype():
    source = inspect.getsource(runner.evaluate_counterfactual)
    assert "unit.to(counterfactual[2].dtype)" in source
