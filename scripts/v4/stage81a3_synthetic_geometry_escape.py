#!/usr/bin/env python3
"""Test whether the unchanged v4 JEPA escapes narrow initialization synthetically."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.v4.stage81a3_diagnose_initialization_geometry import (  # noqa: E402
    cross_attention_diagnostics,
    geometry_2d,
    slot_geometry,
    summarize_stages,
    trace_encoder,
)
from sea_ad_jepa.v4 import (  # noqa: E402
    EMAOptimizerStepController,
    LatentPredictor,
    V4AEncoderSkeleton,
    construct_context_mask,
    create_ema_target,
    ema_parameter_health,
    ema_target_module,
    jepa_prediction_loss,
)


EVIDENCE_COMMIT = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
FIXTURES = ("balanced_multifactor", "dominant_axis_multifactor")
FIXTURE_SEEDS = {"balanced_multifactor": 8113901, "dominant_axis_multifactor": 8113902}
TEST_SEEDS = (8114001, 8114002, 8114003, 8114004, 8114005)
CHECKPOINTS = (0, 20, 50, 100, 200, 300, 500)
TRACE_CHECKPOINTS = (0, 100, 300, 500)
GENES = 4096
CELLS = 8192
FACTORS = 32
TRAIN_CELLS = 7168
READOUT_TRAIN_CELLS = 256
READOUT_EVAL_CELLS = 256
TRACE_CELLS = 64
MICROBATCH = 8
EFFECTIVE_BATCH = 256
ACCUMULATION_STEPS = 32
MASK_FRACTION = 0.40
EMA_MOMENTUM = 0.99925
LEARNING_RATE = 1.0e-4
WEIGHT_DECAY = 0.01
RIDGE_ALPHA = 1.0e-3
PROJECTION_SEED = 8113951


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("results/v4/stage81a3_synthetic_geometry_escape.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("results/v4/stage81a3_synthetic_geometry_escape_trajectory.csv"),
    )
    parser.add_argument("--device", choices=("cuda",), default="cuda")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def config_payload(*, smoke: bool) -> dict[str, Any]:
    return {
        "evidence_commit": EVIDENCE_COMMIT,
        "fixtures": list(FIXTURES if not smoke else FIXTURES[:1]),
        "fixture_seeds": FIXTURE_SEEDS,
        "test_only_initialization_seeds": list(TEST_SEEDS if not smoke else TEST_SEEDS[:1]),
        "checkpoints": list(CHECKPOINTS if not smoke else (0, 1)),
        "trace_checkpoints": list(TRACE_CHECKPOINTS if not smoke else (0, 1)),
        "genes": GENES,
        "cells": CELLS if not smoke else 512,
        "latent_factors": FACTORS,
        "architecture": {
            "gene_identity_dim": 48,
            "width": 160,
            "latent_slots": 24,
            "latent_blocks": 2,
            "attention_heads": 4,
            "dropout": 0.10,
        },
        "masking": {
            "rule": "exact_count",
            "fraction": MASK_FRACTION,
            "one_view_per_synthetic_use": True,
            "all_genes_measured": True,
        },
        "optimizer": {
            "name": "AdamW",
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "gradient_clipping": None,
            "label": "SYNTHETIC TEST SETTING - NOT PRODUCTION HYPERPARAMETER",
        },
        "batching": {
            "physical_microbatch": MICROBATCH,
            "effective_batch": EFFECTIVE_BATCH,
            "gradient_accumulation_microbatches": ACCUMULATION_STEPS,
            "mixed_precision": "CUDA fp16",
        },
        "ema": {
            "fixed_momentum": EMA_MOMENTUM,
            "updates_per_successful_optimizer_update": 1,
            "label": "TEST-ONLY EMA FOR GEOMETRY-ESCAPE DIAGNOSTIC",
        },
        "training_objective": {
            "primary": "mean((predicted_target - target_latents.detach()) ** 2)",
            "variance_training_weight": 0.0,
            "covariance_training_weight": 0.0,
            "contrastive_weight": 0.0,
            "reconstruction_weight": 0.0,
            "supervised_weight": 0.0,
        },
        "factor_readout": {
            "method": "held-out linear ridge regression",
            "ridge_alpha": RIDGE_ALPHA,
            "training_cells": READOUT_TRAIN_CELLS if not smoke else 64,
            "evaluation_cells": READOUT_EVAL_CELLS if not smoke else 64,
            "factors_never_used_in_training": True,
        },
        "synthetic_only": True,
        "real_rna_accessed": False,
        "pathology_opened": False,
    }


def config_hash(config: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode("utf-8")).hexdigest()


def synthetic_fixture(name: str, *, smoke: bool) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    """Create sparse nonnegative counts, then normalize each cell to 10,000/log1p."""
    n_cells = 512 if smoke else CELLS
    generator = torch.Generator(device="cpu").manual_seed(FIXTURE_SEEDS[name])
    factors = torch.randn(n_cells, FACTORS, generator=generator)
    if name == "dominant_axis_multifactor":
        shared = factors[:, :1]
        factors[:, 1:] = 0.35 * shared + math.sqrt(1.0 - 0.35**2) * factors[:, 1:]
    elif name != "balanced_multifactor":
        raise ValueError(name)

    loadings = torch.zeros(FACTORS, GENES)
    module_size = 224
    overlap_stride = 128
    for factor_index in range(FACTORS):
        start = (factor_index * overlap_stride) % GENES
        indices = torch.tensor([(start + offset) % GENES for offset in range(module_size)])
        signs = torch.ones(module_size)
        signs[module_size // 2:] = -1.0
        signs = signs[torch.randperm(module_size, generator=generator)]
        amplitude = 0.34 + 0.08 * torch.rand(module_size, generator=generator)
        if name == "dominant_axis_multifactor" and factor_index == 0:
            amplitude *= 2.25
        loadings[factor_index, indices] += signs * amplitude
    baseline = -1.8 + 0.45 * torch.randn(GENES, generator=generator)
    expressions: list[torch.Tensor] = []
    nonzero = 0
    total_counts = 0.0
    chunk_size = 256
    for start in range(0, n_cells, chunk_size):
        end = min(start + chunk_size, n_cells)
        log_propensity = baseline + factors[start:end] @ loadings
        proportions = torch.softmax(log_propensity, dim=1)
        libraries = torch.exp(
            math.log(5500.0) + 0.55 * torch.randn(end - start, generator=generator)
        ).clamp(1200.0, 25000.0)
        rates = proportions * libraries[:, None]
        counts = torch.poisson(rates, generator=generator)
        library = counts.sum(dim=1, keepdim=True).clamp_min(1.0)
        normalized = torch.log1p(counts * (10000.0 / library))
        expressions.append(normalized.to(torch.float16))
        nonzero += int(torch.count_nonzero(counts))
        total_counts += float(counts.sum())
    expression = torch.cat(expressions)
    metadata = {
        "fixture": name,
        "generator_seed": FIXTURE_SEEDS[name],
        "cells": n_cells,
        "genes": GENES,
        "latent_factors": FACTORS,
        "module_size": module_size,
        "module_stride": overlap_stride,
        "partially_overlapping_modules": True,
        "correlated_factors": name == "dominant_axis_multifactor",
        "dominant_factor_multiplier": 2.25 if name == "dominant_axis_multifactor" else 1.0,
        "nonzero_fraction_before_normalization": nonzero / (n_cells * GENES),
        "zero_fraction_before_normalization": 1.0 - nonzero / (n_cells * GENES),
        "mean_library_size": total_counts / n_cells,
        "normalization": "per-cell library-size normalize to 10000, then log1p",
        "nonnegative_count_like_before_normalization": True,
        "measured_zeros_present": True,
    }
    return expression, factors, metadata


def ridge_readout(
    train_x: torch.Tensor,
    train_y: torch.Tensor,
    eval_x: torch.Tensor,
    eval_y: torch.Tensor,
) -> dict[str, Any]:
    x_train = train_x.detach().float().cpu().double()
    x_eval = eval_x.detach().float().cpu().double()
    y_train = train_y.detach().float().cpu().double()
    y_eval = eval_y.detach().float().cpu().double()
    x_mean = x_train.mean(0, keepdim=True)
    x_std = x_train.std(0, unbiased=False, keepdim=True).clamp_min(1e-8)
    y_mean = y_train.mean(0, keepdim=True)
    x_train = (x_train - x_mean) / x_std
    x_eval = (x_eval - x_mean) / x_std
    y_centered = y_train - y_mean
    if x_train.shape[1] <= x_train.shape[0]:
        identity = torch.eye(x_train.shape[1], dtype=x_train.dtype)
        weights = torch.linalg.solve(x_train.T @ x_train + RIDGE_ALPHA * identity, x_train.T @ y_centered)
    else:
        identity = torch.eye(x_train.shape[0], dtype=x_train.dtype)
        dual = torch.linalg.solve(x_train @ x_train.T + RIDGE_ALPHA * identity, y_centered)
        weights = x_train.T @ dual
    prediction = x_eval @ weights + y_mean
    residual = (y_eval - prediction).square().sum(dim=0)
    total = (y_eval - y_eval.mean(dim=0, keepdim=True)).square().sum(dim=0).clamp_min(1e-12)
    r2 = 1.0 - residual / total
    return {
        "mean_r2": float(r2.mean()),
        "median_r2": float(r2.median()),
        "minimum_r2": float(r2.min()),
        "maximum_r2": float(r2.max()),
        "per_factor_r2": [float(value) for value in r2],
    }


def fixture_references(
    expression: torch.Tensor,
    factors: torch.Tensor,
    device: torch.device,
    *,
    smoke: bool,
) -> dict[str, Any]:
    readout_train = 64 if smoke else READOUT_TRAIN_CELLS
    readout_eval = 64 if smoke else READOUT_EVAL_CELLS
    eval_start = expression.shape[0] - readout_eval
    train_index = torch.arange(readout_train)
    eval_index = torch.arange(eval_start, expression.shape[0])
    geometry_index = torch.arange(min(256, expression.shape[0]))
    input_geometry = geometry_2d(expression[geometry_index].float(), device)
    raw_readout = ridge_readout(
        expression[train_index], factors[train_index], expression[eval_index], factors[eval_index]
    )
    generator = torch.Generator(device="cpu").manual_seed(PROJECTION_SEED)
    projection = torch.randn(GENES, 160, generator=generator) / math.sqrt(GENES)
    projected_train = expression[train_index].float() @ projection
    projected_eval = expression[eval_index].float() @ projection
    projected_geometry = geometry_2d(expression[geometry_index].float() @ projection, device)
    projected_readout = ridge_readout(
        projected_train, factors[train_index], projected_eval, factors[eval_index]
    )
    return {
        "geometry_audit_cells": int(len(geometry_index)),
        "normalized_input_geometry": input_geometry,
        "normalized_expression_factor_readout": raw_readout,
        "random_projection": {
            "seed": PROJECTION_SEED,
            "definition": "iid Gaussian 4096x160 scaled by 1/sqrt(4096)",
            "geometry": projected_geometry,
            "factor_readout": projected_readout,
            "diagnostic_reference_not_model_competitor": True,
        },
        "fixed_factor_readout_partition": {
            "train_indices": [0, readout_train - 1],
            "evaluation_indices": [eval_start, expression.shape[0] - 1],
            "partition_fixed_before_model_training": True,
        },
    }


def parameter_gradient_norm(parameters: Iterable[torch.nn.Parameter]) -> float:
    squared = 0.0
    for parameter in parameters:
        if parameter.grad is not None:
            squared += float(parameter.grad.detach().float().square().sum())
    return math.sqrt(squared)


def extract_embeddings(
    model: V4AEncoderSkeleton,
    expression: torch.Tensor,
    indices: torch.Tensor,
    device: torch.device,
) -> torch.Tensor:
    output: list[torch.Tensor] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(indices), MICROBATCH):
            selected = indices[start:start + MICROBATCH]
            values = expression[selected].to(device)
            batch = len(selected)
            measured = torch.ones(batch, GENES, dtype=torch.bool, device=device)
            context = torch.zeros_like(measured)
            gene_ids = torch.arange(GENES, device=device).repeat(batch, 1)
            with torch.autocast("cuda", dtype=torch.float16):
                output.append(model(gene_ids, values, measured, context, "target").float().cpu())
    return torch.cat(output)


def diagnostic_loss(
    online: V4AEncoderSkeleton,
    target: torch.nn.Module,
    predictor: LatentPredictor,
    expression: torch.Tensor,
    indices: torch.Tensor,
    seed: int,
    checkpoint: int,
    device: torch.device,
) -> float:
    losses = []
    online.eval()
    predictor.eval()
    with torch.no_grad():
        for start in range(0, len(indices), MICROBATCH):
            selected = indices[start:start + MICROBATCH]
            values = expression[selected].to(device)
            batch = len(selected)
            measurement_cpu = torch.ones(batch, GENES, dtype=torch.bool)
            context_cpu = construct_context_mask(
                measurement_cpu,
                mask_fraction=MASK_FRACTION,
                production_seed=seed,
                cell_indices=selected,
                sample_pass=checkpoint,
                view_index=0,
                rule="exact_count",
            )
            measured = measurement_cpu.to(device)
            context = context_cpu.to(device)
            gene_ids = torch.arange(GENES, device=device).repeat(batch, 1)
            with torch.autocast("cuda", dtype=torch.float16):
                prediction = predictor(online(gene_ids, values, measured, context, "student"))
                target_latents = target(gene_ids, values, measured, context, "target")
                losses.append(float(jepa_prediction_loss(prediction, target_latents)))
    return float(np.mean(losses))


def checkpoint_metrics(
    online: V4AEncoderSkeleton,
    target: torch.nn.Module,
    predictor: LatentPredictor,
    expression: torch.Tensor,
    factors: torch.Tensor,
    *,
    fixture: str,
    seed: int,
    step: int,
    interval: dict[str, list[float]],
    nonfinite_events: int,
    device: torch.device,
    smoke: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any] | None]:
    readout_train = 64 if smoke else READOUT_TRAIN_CELLS
    readout_eval = 64 if smoke else READOUT_EVAL_CELLS
    eval_start = expression.shape[0] - readout_eval
    train_index = torch.arange(readout_train)
    eval_index = torch.arange(eval_start, expression.shape[0])
    combined_index = torch.cat((train_index, eval_index))
    target_module = ema_target_module(target)
    target_slots = extract_embeddings(target_module, expression, combined_index, device)
    online_slots = extract_embeddings(online, expression, combined_index, device)
    split = readout_train
    target_pooled = target_slots.mean(dim=1)
    online_pooled = online_slots.mean(dim=1)
    target_geometry = geometry_2d(target_pooled[split:], device)
    online_geometry = geometry_2d(online_pooled[split:], device)
    target_slots_geometry = slot_geometry(target_slots[split:], device)
    online_slots_geometry = slot_geometry(online_slots[split:], device)
    target_factor = ridge_readout(
        target_pooled[:split], factors[train_index], target_pooled[split:], factors[eval_index]
    )
    online_factor = ridge_readout(
        online_pooled[:split], factors[train_index], online_pooled[split:], factors[eval_index]
    )
    loss_indices = eval_index[: min(64, len(eval_index))]
    row: dict[str, Any] = {
        "fixture": fixture,
        "seed": seed,
        "optimizer_step": step,
        "jepa_diagnostic_loss": diagnostic_loss(
            online, target, predictor, expression, loss_indices, seed, step, device
        ),
        "effective_rank": target_geometry["effective_rank"],
        "top_singular_l1_fraction": target_geometry["top_singular_l1_fraction"],
        "top_singular_energy_fraction": target_geometry["top_singular_energy_fraction"],
        "cross_cell_std": target_geometry["cross_cell_std_mean"],
        "median_pairwise_distance": target_geometry["median_pairwise_distance"],
        "slot_cosine": target_slots_geometry["within_cell_slot_cosine_mean"],
        "slot_variance": target_slots_geometry["within_cell_slot_variance_mean"],
        "corresponding_slot_cross_cell_std": target_slots_geometry[
            "corresponding_slot_cross_cell_std_mean"
        ],
        "median_per_slot_effective_rank": target_slots_geometry["per_slot_effective_rank"]["median"],
        "known_factor_heldout_mean_r2": target_factor["mean_r2"],
        "known_factor_heldout_median_r2": target_factor["median_r2"],
        "online_effective_rank": online_geometry["effective_rank"],
        "online_top_singular_l1_fraction": online_geometry["top_singular_l1_fraction"],
        "online_top_singular_energy_fraction": online_geometry["top_singular_energy_fraction"],
        "online_slot_cosine": online_slots_geometry["within_cell_slot_cosine_mean"],
        "online_slot_variance": online_slots_geometry["within_cell_slot_variance_mean"],
        "online_known_factor_heldout_mean_r2": online_factor["mean_r2"],
        "online_target_distance": ema_parameter_health(
            online, target
        ).online_target_parameter_l2_distance,
        "mean_ema_update_norm_since_previous_checkpoint": (
            float(np.mean(interval["ema_update_norm"])) if interval["ema_update_norm"] else 0.0
        ),
        "mean_gradient_norm_since_previous_checkpoint": (
            float(np.mean(interval["gradient_norm"])) if interval["gradient_norm"] else 0.0
        ),
        "mean_training_jepa_loss_since_previous_checkpoint": (
            float(np.mean(interval["loss"])) if interval["loss"] else None
        ),
        "nonfinite_events": nonfinite_events,
        "target_factor_readout": target_factor,
        "online_factor_readout": online_factor,
        "target_pooled_geometry": target_geometry,
        "online_pooled_geometry": online_geometry,
        "target_slot_geometry": target_slots_geometry,
        "online_slot_geometry": online_slots_geometry,
        "frozen_no_learning_control": None,
    }
    stage_rows: list[dict[str, Any]] = []
    attention: dict[str, Any] | None = None
    if step in (TRACE_CHECKPOINTS if not smoke else (0, 1)):
        trace_index = eval_index[: min(TRACE_CELLS, len(eval_index))]
        trace_expression = expression[trace_index].float()
        trace_measurement = torch.ones(len(trace_index), GENES, dtype=torch.bool)
        stages, _, _ = trace_encoder(
            target_module,
            trace_expression,
            trace_measurement,
            device,
            capture_attention=False,
        )
        summarized, details = summarize_stages(stages, device)
        for stage in summarized:
            stage_rows.append({"fixture": fixture, "seed": seed, "optimizer_step": step, **stage})
        attention = cross_attention_diagnostics(
            target_module, trace_expression, trace_measurement, device
        )
        row["target_stage_geometry"] = details
        row["target_cross_attention_summary"] = attention
    online.train()
    predictor.train()
    return row, stage_rows, attention


def train_one(
    expression: torch.Tensor,
    factors: torch.Tensor,
    fixture: str,
    seed: int,
    device: torch.device,
    *,
    smoke: bool,
) -> dict[str, Any]:
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    online = V4AEncoderSkeleton().to(device)
    predictor = LatentPredictor().to(device)
    target = create_ema_target(online).to(device)
    if any(parameter.requires_grad for parameter in ema_target_module(target).parameters()):
        raise RuntimeError("EMA target parameters are not frozen")
    parameters = list(online.parameters()) + list(predictor.parameters())
    optimizer = torch.optim.AdamW(
        parameters, lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
    )
    scaler = torch.amp.GradScaler("cuda")
    controller = EMAOptimizerStepController(online, target)
    maximum_step = 1 if smoke else CHECKPOINTS[-1]
    checkpoints = (0, 1) if smoke else CHECKPOINTS
    rng = torch.Generator(device="cpu").manual_seed(seed + 900_000)
    rows: list[dict[str, Any]] = []
    stage_rows: list[dict[str, Any]] = []
    interval = {"loss": [], "gradient_norm": [], "ema_update_norm": []}
    nonfinite_events = 0
    start_time = time.time()
    initial, initial_stages, _ = checkpoint_metrics(
        online, target, predictor, expression, factors,
        fixture=fixture, seed=seed, step=0, interval=interval,
        nonfinite_events=nonfinite_events, device=device, smoke=smoke,
    )
    initial["frozen_no_learning_control"] = {
        "equivalent_checkpoint_geometry_is_constant_by_construction": True,
        "reference_optimizer_step": 0,
    }
    rows.append(initial)
    stage_rows.extend(initial_stages)
    print(
        f"{fixture} seed={seed} step=0 target_rank={initial['effective_rank']:.4f} "
        f"online_rank={initial['online_effective_rank']:.4f} "
        f"target_factor_r2={initial['known_factor_heldout_mean_r2']:.4f}",
        flush=True,
    )
    online.train()
    predictor.train()
    train_limit = min(TRAIN_CELLS, expression.shape[0] - (64 if smoke else READOUT_EVAL_CELLS))
    for update in range(1, maximum_step + 1):
        optimizer.zero_grad(set_to_none=True)
        selected = torch.randint(0, train_limit, (EFFECTIVE_BATCH,), generator=rng)
        update_loss = 0.0
        finite = True
        for microbatch in range(ACCUMULATION_STEPS):
            indices = selected[microbatch * MICROBATCH:(microbatch + 1) * MICROBATCH]
            values = expression[indices].to(device)
            measurement_cpu = torch.ones(MICROBATCH, GENES, dtype=torch.bool)
            context_cpu = construct_context_mask(
                measurement_cpu,
                mask_fraction=MASK_FRACTION,
                production_seed=seed,
                cell_indices=indices,
                sample_pass=update,
                view_index=0,
                rule="exact_count",
            )
            measured = measurement_cpu.to(device)
            context = context_cpu.to(device)
            gene_ids = torch.arange(GENES, device=device).repeat(MICROBATCH, 1)
            with torch.autocast("cuda", dtype=torch.float16):
                online_latents = online(gene_ids, values, measured, context, "student")
                prediction = predictor(online_latents)
                with torch.no_grad():
                    target_latents = target(gene_ids, values, measured, context, "target")
                loss = jepa_prediction_loss(prediction, target_latents)
                scaled_loss = loss / ACCUMULATION_STEPS
            if not torch.isfinite(loss):
                finite = False
                break
            scaler.scale(scaled_loss).backward()
            update_loss += float(loss.detach()) / ACCUMULATION_STEPS
        if not finite:
            nonfinite_events += 1
            optimizer.zero_grad(set_to_none=True)
            raise RuntimeError(f"nonfinite loss at {fixture} seed={seed} update={update}")
        scaler.unscale_(optimizer)
        gradient_norm = parameter_gradient_norm(parameters)
        if not math.isfinite(gradient_norm):
            nonfinite_events += 1
            raise RuntimeError(f"nonfinite gradient at {fixture} seed={seed} update={update}")
        pre_gap = ema_parameter_health(online, target).online_target_parameter_l2_distance
        scale_before = scaler.get_scale()
        scaler.step(optimizer)
        scaler.update()
        if scaler.get_scale() < scale_before:
            nonfinite_events += 1
            raise RuntimeError(f"GradScaler skipped optimizer update {update}")
        post_optimizer_gap = ema_parameter_health(online, target).online_target_parameter_l2_distance
        controller.after_successful_optimizer_step(momentum=EMA_MOMENTUM)
        interval["loss"].append(update_loss)
        interval["gradient_norm"].append(gradient_norm)
        interval["ema_update_norm"].append((1.0 - EMA_MOMENTUM) * post_optimizer_gap)
        if update in checkpoints:
            row, stages, _ = checkpoint_metrics(
                online, target, predictor, expression, factors,
                fixture=fixture, seed=seed, step=update, interval=interval,
                nonfinite_events=nonfinite_events, device=device, smoke=smoke,
            )
            row["pre_optimizer_online_target_distance"] = pre_gap
            rows.append(row)
            stage_rows.extend(stages)
            print(
                f"{fixture} seed={seed} step={update} loss={row['jepa_diagnostic_loss']:.6f} "
                f"target_rank={row['effective_rank']:.4f} "
                f"online_rank={row['online_effective_rank']:.4f} "
                f"target_factor_r2={row['known_factor_heldout_mean_r2']:.4f} "
                f"online_factor_r2={row['online_known_factor_heldout_mean_r2']:.4f}",
                flush=True,
            )
            interval = {"loss": [], "gradient_norm": [], "ema_update_norm": []}
    if controller.global_update_step != maximum_step or controller.ema_update_count != maximum_step:
        raise RuntimeError("optimizer/EMA update count mismatch")
    return {
        "fixture": fixture,
        "seed": seed,
        "optimizer_updates": maximum_step,
        "ema_updates": controller.ema_update_count,
        "nonfinite_events": nonfinite_events,
        "elapsed_seconds": time.time() - start_time,
        "trajectory": rows,
        "stage_trajectory": stage_rows,
        "target_requires_grad_false": True,
        "gradient_clipping": None,
    }


def trajectory_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for run in payload.get("runs", []):
        for row in run["trajectory"]:
            rows.append({
                key: value for key, value in row.items()
                if not isinstance(value, (dict, list))
            })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    columns = sorted({key for row in rows for key in row})
    temporary = path.with_name(f".{path.name}.temporary")
    path.parent.mkdir(parents=True, exist_ok=True)
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def aggregate(payload: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "effective_rank",
        "top_singular_l1_fraction",
        "top_singular_energy_fraction",
        "known_factor_heldout_mean_r2",
        "slot_cosine",
        "slot_variance",
    )
    output: list[dict[str, Any]] = []
    rows = trajectory_rows(payload)
    for fixture in FIXTURES:
        for checkpoint in CHECKPOINTS:
            selected = [
                row for row in rows
                if row["fixture"] == fixture and int(row["optimizer_step"]) == checkpoint
            ]
            if not selected:
                continue
            record: dict[str, Any] = {
                "fixture": fixture,
                "optimizer_step": checkpoint,
                "seeds": len(selected),
            }
            for field in fields:
                values = np.asarray([float(row[field]) for row in selected])
                record[field] = {
                    "mean": float(values.mean()),
                    "median": float(np.median(values)),
                    "minimum": float(values.min()),
                    "maximum": float(values.max()),
                }
            output.append(record)
    completed = payload.get("runs", [])
    rank_increase = 0
    energy_decrease = 0
    loss_decrease = 0
    positive_factor_readout = 0
    for run in completed:
        initial = run["trajectory"][0]
        final = run["trajectory"][-1]
        rank_increase += int(final["effective_rank"] > initial["effective_rank"])
        energy_decrease += int(
            final["top_singular_energy_fraction"]
            < initial["top_singular_energy_fraction"]
        )
        loss_decrease += int(final["jepa_diagnostic_loss"] < initial["jepa_diagnostic_loss"])
        positive_factor_readout += int(final["known_factor_heldout_mean_r2"] > 0.0)
    trapped = sum(
        int(
            run["trajectory"][-1]["effective_rank"]
            <= run["trajectory"][0]["effective_rank"]
            and run["trajectory"][-1]["top_singular_energy_fraction"]
            >= run["trajectory"][0]["top_singular_energy_fraction"]
        )
        for run in completed
    )
    return {
        "by_fixture_checkpoint": output,
        "descriptive_direction_counts": {
            "completed_runs": len(completed),
            "target_effective_rank_increased": rank_increase,
            "target_top_singular_energy_decreased": energy_decrease,
            "jepa_diagnostic_loss_decreased": loss_decrease,
            "positive_final_target_factor_readout": positive_factor_readout,
        },
        "clear_broadening_count": 0 if rank_increase == 0 and energy_decrease == 0 else None,
        "trapped_or_narrow_count": trapped,
        "counting_rule": (
            "Post-run descriptive directions, not a predeclared numerical threshold: "
            "trapped/narrow requires non-increasing target rank and non-decreasing "
            "target top-singular energy from step 0 to the final checkpoint."
        ),
        "numerical_failure_count": sum(int(run["nonfinite_events"] > 0) for run in payload["runs"]),
    }


def classify_completed_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Apply the contract's qualitative decision table after all evidence exists."""
    runs = payload["runs"]
    initial_final = [(run["trajectory"][0], run["trajectory"][-1]) for run in runs]
    all_loss_learned = all(final["jepa_diagnostic_loss"] < initial["jepa_diagnostic_loss"] for initial, final in initial_final)
    all_rank_narrowed = all(final["effective_rank"] <= initial["effective_rank"] for initial, final in initial_final)
    all_energy_concentrated = all(
        final["top_singular_energy_fraction"] >= initial["top_singular_energy_fraction"]
        for initial, final in initial_final
    )
    all_numerically_finite = all(run["nonfinite_events"] == 0 for run in runs)
    if all_numerically_finite and all_loss_learned and all_rank_narrowed and all_energy_concentrated:
        decision = "C. GEOMETRY REMAINS TRAPPED"
        recommendation = "CURRENT ARCHITECTURE SHOWS SYNTHETIC GEOMETRY-ESCAPE FAILURE"
        end_state = "SYNTHETIC GEOMETRY REMAINS TRAPPED"
    elif not all_numerically_finite:
        decision = "D. NUMERICAL / MECHANICAL FAILURE"
        recommendation = "REPORT EXACT MECHANICAL FAILURE"
        end_state = "SYNTHETIC GEOMETRY ESCAPE TEST FAILED MECHANICALLY"
    else:
        decision = "B. PARTIAL / UNSTABLE GEOMETRY ESCAPE"
        recommendation = "ARCHITECTURE REQUIRES HUMAN REVIEW"
        end_state = "SYNTHETIC GEOMETRY ESCAPE PARTIAL OR UNSTABLE"
    return {
        "decision": decision,
        "recommendation": recommendation,
        "end_state": end_state,
        "observed_evidence": {
            "all_runs_jepa_loss_decreased": all_loss_learned,
            "all_runs_target_effective_rank_nonincreasing": all_rank_narrowed,
            "all_runs_target_top_singular_energy_nondecreasing": all_energy_concentrated,
            "maximum_final_target_factor_mean_r2": max(
                final["known_factor_heldout_mean_r2"] for _, final in initial_final
            ),
            "all_runs_numerically_finite": all_numerically_finite,
        },
        "interpretation_boundary": (
            "Synthetic mechanics evidence only; this is not biological validation and "
            "does not authorize an automatic redesign."
        ),
    }


def main() -> int:
    args = parse_args()
    project = args.project_dir.resolve()
    output_json = project / args.output_json
    output_csv = project / args.output_csv
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required by the synthetic geometry-escape contract")
    device = torch.device("cuda")
    config = config_payload(smoke=args.smoke)
    signature = config_hash(config)
    if output_json.exists() and not args.overwrite:
        payload = json.loads(output_json.read_text(encoding="utf-8"))
        if payload.get("configuration_hash") != signature:
            raise RuntimeError("Existing output configuration differs; use a separate output or --overwrite")
    else:
        payload = {
            "stage": "stage81a3_synthetic_geometry_escape",
            "status": "running",
            "configuration": config,
            "configuration_hash": signature,
            "device": {
                "torch": torch.__version__,
                "cuda": torch.version.cuda,
                "name": torch.cuda.get_device_name(0),
            },
            "fixture_metadata": {},
            "fixture_references": {},
            "runs": [],
            "classification": "pending_human_interpretation",
            "claim_boundaries": {
                "real_rna_optimizer_steps": 0,
                "real_rna_ema_updates": 0,
                "real_rna_model_training": False,
                "synthetic_training_only": True,
                "pathology_opened": False,
                "stage81b_started": False,
                "stage81c_started": False,
                "stage81a3_complete": False,
                "ready_for_stage81b": False,
            },
        }
    completed = {(run["fixture"], int(run["seed"])) for run in payload["runs"]}
    fixtures = FIXTURES if not args.smoke else FIXTURES[:1]
    seeds = TEST_SEEDS if not args.smoke else TEST_SEEDS[:1]
    for fixture in fixtures:
        print(f"Generating deterministic fixture: {fixture}", flush=True)
        expression, factors, metadata = synthetic_fixture(fixture, smoke=args.smoke)
        payload["fixture_metadata"][fixture] = metadata
        if fixture not in payload["fixture_references"]:
            print(f"Auditing input/reference geometry: {fixture}", flush=True)
            payload["fixture_references"][fixture] = fixture_references(
                expression, factors, device, smoke=args.smoke
            )
            atomic_json(output_json, payload)
        for seed in seeds:
            if (fixture, seed) in completed:
                print(f"Reusing completed run: {fixture} seed={seed}", flush=True)
                continue
            print(f"Starting synthetic training: {fixture} seed={seed}", flush=True)
            run = train_one(expression, factors, fixture, seed, device, smoke=args.smoke)
            payload["runs"].append(run)
            payload["runs"].sort(key=lambda item: (item["fixture"], item["seed"]))
            payload["aggregate"] = aggregate(payload)
            atomic_json(output_json, payload)
            write_csv(output_csv, trajectory_rows(payload))
            print(f"Persisted compact completed run: {fixture} seed={seed}", flush=True)
        del expression, factors
        torch.cuda.empty_cache()
    expected_runs = len(fixtures) * len(seeds)
    if len(payload["runs"]) != expected_runs:
        raise RuntimeError(f"Expected {expected_runs} completed runs; observed {len(payload['runs'])}")
    payload["aggregate"] = aggregate(payload)
    payload["classification"] = classify_completed_evidence(payload)
    payload["status"] = "complete_scientifically_classified"
    payload["all_seeds_preserved"] = True
    payload["seed_selected"] = False
    payload["production_hyperparameters_selected"] = False
    atomic_json(output_json, payload)
    write_csv(output_csv, trajectory_rows(payload))
    print(f"Wrote: {output_json}")
    print(f"Wrote: {output_csv}")
    print(f"completed_runs={len(payload['runs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
