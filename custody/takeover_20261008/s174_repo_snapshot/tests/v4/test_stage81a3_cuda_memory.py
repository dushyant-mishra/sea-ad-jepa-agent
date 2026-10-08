from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import (
    EMAOptimizerStepController,
    LatentPredictor,
    V4AEncoderSkeleton,
    construct_context_mask,
    create_ema_target,
    jepa_prediction_loss,
)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA unavailable")
def test_actual_v4_microbatch8_fp16_memory_and_accumulation_smoke() -> None:
    device = torch.device("cuda")
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(device)
    torch.manual_seed(8110)
    online = V4AEncoderSkeleton().to(device).train()
    predictor = LatentPredictor().to(device).train()
    target = create_ema_target(online).to(device)
    optimizer = torch.optim.AdamW(
        list(online.parameters()) + list(predictor.parameters()), lr=1e-4
    )
    controller = EMAOptimizerStepController(online, target)
    scaler = torch.amp.GradScaler("cuda")
    optimizer.zero_grad(set_to_none=True)
    batch, genes, accumulation_steps = 8, 4096, 2
    gene_ids = torch.arange(genes).repeat(batch, 1)
    measurement_cpu = torch.ones(batch, genes, dtype=torch.bool)
    context_cpu = construct_context_mask(
        measurement_cpu, mask_fraction=0.4, production_seed=8111,
        cell_indices=torch.arange(batch), sample_pass=0, view_index=0,
        rule="exact_count",
    )
    gene_ids = gene_ids.to(device)
    measurement = measurement_cpu.to(device)
    context = context_cpu.to(device)
    losses = []
    for microbatch in range(accumulation_steps):
        expression = torch.rand(batch, genes, device=device)
        with torch.autocast(device_type="cuda", dtype=torch.float16):
            online_latents = online(
                gene_ids, expression, measurement, context, "student"
            )
            prediction = predictor(online_latents)
            target_latents = target(
                gene_ids, expression, measurement, context, "target"
            )
            loss = jepa_prediction_loss(prediction, target_latents) / accumulation_steps
        assert torch.isfinite(loss)
        scaler.scale(loss).backward()
        losses.append(float(loss.detach()))
        assert controller.ema_update_count == 0
    scaler.unscale_(optimizer)
    gradients = [parameter.grad for parameter in online.parameters() if parameter.grad is not None]
    assert gradients and all(torch.isfinite(gradient).all() for gradient in gradients)
    scaler.step(optimizer)
    scaler.update()
    controller.after_successful_optimizer_step(momentum=0.5)
    assert controller.global_update_step == 1
    assert controller.ema_update_count == 1
    peak_allocated = torch.cuda.max_memory_allocated(device)
    peak_reserved = torch.cuda.max_memory_reserved(device)
    assert peak_allocated > 0 and peak_reserved >= peak_allocated
    print(
        f"CUDA_STAGE81A3 batch={batch} accumulation={accumulation_steps} "
        f"peak_allocated_bytes={peak_allocated} peak_reserved_bytes={peak_reserved} "
        f"losses={losses}"
    )
