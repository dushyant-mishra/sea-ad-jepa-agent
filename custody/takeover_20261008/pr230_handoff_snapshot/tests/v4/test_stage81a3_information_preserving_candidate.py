from __future__ import annotations

import inspect
import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import (  # noqa: E402
    FrozenPCA,
    LatentPredictor,
    PerceiverCrossAttention,
    V4AEncoderSkeleton,
    create_ema_target,
    flatten_slots,
    jepa_prediction_loss,
)
from sea_ad_jepa.v4.perceiver_encoder import _normalize_valid_gene_logits  # noqa: E402


def candidate_attention() -> PerceiverCrossAttention:
    torch.manual_seed(8120)
    return PerceiverCrossAttention(
        latent_slots=3,
        width=8,
        attention_heads=2,
        routing_mode="variance_normalized",
    ).eval()


def test_normalized_valid_gene_logits_have_unit_population_sd() -> None:
    model = candidate_attention()
    tokens = torch.randn(2, 7, 8)
    valid = torch.tensor([[True] * 7, [True, True, True, True, False, False, False]])
    _, _, _, logits = model.routing_diagnostics(tokens, valid)
    for cell in range(2):
        selected = logits[cell, :, :, valid[cell]]
        torch.testing.assert_close(
            selected.std(dim=-1, unbiased=False),
            torch.ones_like(selected[..., 0]),
            rtol=2e-5,
            atol=2e-5,
        )


def test_positive_affine_raw_logit_change_preserves_normalized_ranking_and_values() -> None:
    torch.manual_seed(8123)
    logits = torch.randn(2, 4, 3, 11)
    valid = torch.tensor([
        [True] * 11,
        [True, True, True, True, True, True, False, False, False, False, False],
    ])
    original = _normalize_valid_gene_logits(logits, valid)
    transformed = _normalize_valid_gene_logits(7.5 * logits + 13.0, valid)
    finite = valid[:, None, None, :].expand_as(original)
    torch.testing.assert_close(original[finite], transformed[finite], rtol=2e-5, atol=2e-5)
    assert torch.equal(original.argsort(dim=-1), transformed.argsort(dim=-1))


def test_invalid_and_hidden_genes_get_exactly_zero_probability() -> None:
    model = candidate_attention()
    tokens = torch.randn(1, 5, 8)
    valid = torch.tensor([[True, False, True, False, True]])
    _, attention = model(tokens, valid, return_attention=True)
    assert torch.count_nonzero(attention[..., ~valid[0]]) == 0


def test_attention_rows_sum_to_one_and_are_finite() -> None:
    model = candidate_attention()
    tokens = torch.randn(2, 4096, 8)
    valid = torch.ones(2, 4096, dtype=torch.bool)
    output, attention = model(tokens, valid, return_attention=True)
    assert torch.isfinite(output).all() and torch.isfinite(attention).all()
    torch.testing.assert_close(
        attention.sum(dim=-1), torch.ones_like(attention[..., 0]), rtol=1e-6, atol=1e-6
    )


def test_measured_zero_token_remains_attention_eligible() -> None:
    encoder = V4AEncoderSkeleton(gene_attention_mode="variance_normalized").eval()
    ids = torch.tensor([[1, 2, 3]])
    expression = torch.tensor([[0.0, 1.0, 0.0]])
    measured = torch.tensor([[True, True, False]])
    hidden = torch.zeros_like(measured)
    tokens = encoder.tokenizer(ids, expression)
    _, attention = encoder.cross_attention(tokens, measured, return_attention=True)
    assert torch.all(attention[..., 0] > 0)
    assert torch.count_nonzero(attention[..., 2]) == 0


def test_candidate_has_no_temperature_parameter() -> None:
    model = V4AEncoderSkeleton(gene_attention_mode="variance_normalized")
    assert all("temperature" not in name and "logit_scale" not in name for name, _ in model.named_parameters())


def test_historical_default_path_remains_native() -> None:
    model = V4AEncoderSkeleton()
    assert model.cross_attention.routing_mode == "native"
    assert sum(parameter.numel() for parameter in model.parameters()) == 730_752


def test_candidate_parameter_count_is_unchanged() -> None:
    model = V4AEncoderSkeleton(gene_attention_mode="variance_normalized")
    assert sum(parameter.numel() for parameter in model.parameters()) == 730_752


def test_online_and_predictor_receive_gradients_but_target_does_not() -> None:
    torch.manual_seed(8121)
    online = V4AEncoderSkeleton(gene_attention_mode="variance_normalized")
    predictor = LatentPredictor()
    target = create_ema_target(online)
    ids = torch.arange(12).repeat(2, 1)
    expression = torch.rand(2, 12)
    measured = torch.ones(2, 12, dtype=torch.bool)
    hidden = torch.zeros_like(measured)
    context = online(ids, expression, measured, hidden, "student")
    with torch.no_grad():
        target_slots = target(ids, expression, measured, hidden, "target")
    jepa_prediction_loss(predictor(context), target_slots).backward()
    assert all(parameter.grad is not None and torch.isfinite(parameter.grad).all() for parameter in online.parameters())
    assert all(parameter.grad is not None and torch.isfinite(parameter.grad).all() for parameter in predictor.parameters())
    assert all(parameter.grad is None for parameter in target.parameters())


def test_frozen_pca_is_train_fitted_and_transform_does_not_refit() -> None:
    torch.manual_seed(8122)
    train = torch.randn(20, 12)
    evaluation = torch.randn(5, 12) + 100.0
    pca = FrozenPCA.fit(train, n_components=5)
    torch.testing.assert_close(pca.mean, train.mean(dim=0))
    before_mean = pca.mean.clone()
    before_components = pca.components.clone()
    transformed = pca.transform(evaluation)
    assert transformed.shape == (5, 5)
    torch.testing.assert_close(pca.mean, before_mean, rtol=0.0, atol=0.0)
    torch.testing.assert_close(pca.components, before_components, rtol=0.0, atol=0.0)


def test_pca_fit_api_cannot_accept_factor_labels_or_eval_data() -> None:
    assert set(inspect.signature(FrozenPCA.fit).parameters) == {
        "training_values",
        "n_components",
    }


def test_flatten_slots_preserves_complete_pattern_not_arithmetic_mean() -> None:
    slots = torch.arange(2 * 24 * 160, dtype=torch.float32).reshape(2, 24, 160)
    flattened = flatten_slots(slots)
    assert flattened.shape == (2, 3840)
    torch.testing.assert_close(flattened, slots.reshape(2, 3840))
    assert flattened.shape[1] != slots.mean(dim=1).shape[1]


def test_candidate_mode_must_be_explicit() -> None:
    try:
        V4AEncoderSkeleton(gene_attention_mode="scaled")  # type: ignore[arg-type]
    except Exception:
        pass
    else:
        raise AssertionError("unregistered attention mode was silently accepted")


def test_online_and_target_use_the_same_normalized_routing_implementation() -> None:
    online = V4AEncoderSkeleton(gene_attention_mode="variance_normalized")
    target = create_ema_target(online)
    assert online.cross_attention.routing_mode == "variance_normalized"
    assert target.encoder.cross_attention.routing_mode == "variance_normalized"


def test_candidate_config_forbids_native_routing_and_factor_training() -> None:
    text = (PROJECT / "configs/v4/stage81a3_information_preserving_candidate.yaml").read_text(
        encoding="utf-8"
    )
    assert "gene_attention_mode: variance_normalized" in text
    assert "factor_labels_used_for_training: false" in text
    assert "canonical_summary: train_fitted_pca160_of_flattened_final_slots" in text


def test_cuda_fp16_candidate_forward_when_available() -> None:
    if not torch.cuda.is_available():
        return
    model = V4AEncoderSkeleton(gene_attention_mode="variance_normalized").cuda().eval()
    ids = torch.arange(128, device="cuda").repeat(2, 1)
    expression = torch.rand(2, 128, device="cuda")
    measured = torch.ones(2, 128, dtype=torch.bool, device="cuda")
    hidden = torch.zeros_like(measured)
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16):
        output = model(ids, expression, measured, hidden, "student")
    assert output.shape == (2, 24, 160)
    assert torch.isfinite(output).all()
