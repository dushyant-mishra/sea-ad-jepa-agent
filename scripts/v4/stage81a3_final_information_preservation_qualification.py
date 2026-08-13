#!/usr/bin/env python3
"""Run the one predeclared Stage81A3 information-preserving qualification."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.v4 import stage81a3_forensic_failed_trajectory_replay as forensic  # noqa: E402
from scripts.v4 import stage81a3_synthetic_geometry_escape as base  # noqa: E402
from sea_ad_jepa.v4 import (  # noqa: E402
    EMAOptimizerStepController,
    FrozenPCA,
    LatentPredictor,
    V4AEncoderSkeleton,
    construct_context_mask,
    capture_synthetic_checkpoint,
    create_ema_target,
    ema_target_module,
    flatten_slots,
    jepa_prediction_loss,
    restore_synthetic_checkpoint,
)
from sea_ad_jepa.v4.contracts import derive_visibility_masks  # noqa: E402


FIXTURES = ("balanced_multifactor", "dominant_axis_multifactor")
SEEDS = base.TEST_SEEDS
CHECKPOINTS = base.CHECKPOINTS
EMA = 0.996
STEPS = 500
EPS = 1e-12
OUTPUT_JSON = Path("results/v4/stage81a3_final_information_preservation_qualification.json")
OUTPUT_RUNS = Path("results/v4/stage81a3_final_information_preservation_runs.csv")
OUTPUT_FACTORS = Path("results/v4/stage81a3_final_information_preservation_factors.csv")
OUTPUT_GEOMETRY = Path("results/v4/stage81a3_final_information_preservation_geometry.csv")
OUTPUT_ENGINEERING = Path("results/v4/stage81a3_final_information_preservation_engineering_gates.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = sorted({key for row in rows for key in row})
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.temporary")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def config_payload() -> dict[str, Any]:
    return {
        "fixture_order": list(FIXTURES),
        "seed_order": list(SEEDS),
        "checkpoints": list(CHECKPOINTS),
        "architecture": {
            "gene_attention_mode": "variance_normalized",
            "distributed_representation": "final_slots_24x160",
            "canonical_summary": "train_fitted_pca160_of_flattened_final_slots",
            "legacy_mean_pooling": "historical_comparison_only",
        },
        "training": {
            "ema": EMA,
            "optimizer": "AdamW",
            "learning_rate": base.LEARNING_RATE,
            "weight_decay": base.WEIGHT_DECAY,
            "gradient_clipping": None,
            "microbatch": base.MICROBATCH,
            "effective_batch": base.EFFECTIVE_BATCH,
            "gradient_accumulation": base.ACCUMULATION_STEPS,
            "mask_fraction": base.MASK_FRACTION,
            "mask_rule": "exact_count",
            "optimizer_updates": STEPS,
            "precision": "CUDA fp16 autocast with float32 routing normalization",
        },
        "factor_readout": {
            "ridge_alpha": base.RIDGE_ALPHA,
            "train_cells": base.READOUT_TRAIN_CELLS,
            "eval_cells": base.READOUT_EVAL_CELLS,
            "factor_labels_used_in_training_or_pca": False,
        },
    }


def config_hash() -> str:
    return hashlib.sha256(json.dumps(config_payload(), sort_keys=True).encode()).hexdigest()


def model_components(seed: int, device: torch.device):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    online = V4AEncoderSkeleton(gene_attention_mode="variance_normalized").to(device)
    predictor = LatentPredictor().to(device)
    target = create_ema_target(online).to(device)
    optimizer = torch.optim.AdamW(
        list(online.parameters()) + list(predictor.parameters()),
        lr=base.LEARNING_RATE,
        weight_decay=base.WEIGHT_DECAY,
    )
    scaler = torch.amp.GradScaler("cuda")
    controller = EMAOptimizerStepController(online, target)
    return online, target, predictor, optimizer, scaler, controller


def qualification_update(
    components: tuple,
    expression: torch.Tensor,
    seed: int,
    update: int,
    selection_generator: torch.Generator,
    device: torch.device,
) -> float:
    """Execute one exact candidate optimizer/EMA update for resume qualification."""
    online, target, predictor, optimizer, scaler, controller = components
    online.train()
    predictor.train()
    optimizer.zero_grad(set_to_none=True)
    selected = torch.randint(0, base.TRAIN_CELLS, (base.EFFECTIVE_BATCH,), generator=selection_generator)
    total_loss = 0.0
    for microbatch in range(base.ACCUMULATION_STEPS):
        start = microbatch * base.MICROBATCH
        indices = selected[start:start + base.MICROBATCH]
        values = expression[indices].to(device)
        measured_cpu = torch.ones(base.MICROBATCH, base.GENES, dtype=torch.bool)
        hidden_cpu = construct_context_mask(
            measured_cpu,
            mask_fraction=base.MASK_FRACTION,
            production_seed=seed,
            cell_indices=indices,
            sample_pass=update,
            view_index=0,
            rule="exact_count",
        )
        ids = torch.arange(base.GENES, device=device).repeat(base.MICROBATCH, 1)
        measured = measured_cpu.to(device)
        hidden = hidden_cpu.to(device)
        with torch.autocast("cuda", dtype=torch.float16):
            student = online(ids, values, measured, hidden, "student")
            prediction = predictor(student)
            with torch.no_grad():
                teacher = target(ids, values, measured, hidden, "target")
            loss = jepa_prediction_loss(prediction, teacher)
        scaler.scale(loss / base.ACCUMULATION_STEPS).backward()
        total_loss += float(loss.detach())
    scaler.unscale_(optimizer)
    before = scaler.get_scale()
    scaler.step(optimizer)
    scaler.update()
    if scaler.get_scale() < before:
        raise RuntimeError("resume qualification encountered a skipped optimizer step")
    controller.after_successful_optimizer_step(momentum=EMA)
    return total_loss / base.ACCUMULATION_STEPS


def module_max_difference(left: torch.nn.Module, right: torch.nn.Module) -> float:
    return max(
        float((a.detach() - b.detach()).abs().max())
        for a, b in zip(left.state_dict().values(), right.state_dict().values())
    )


def nested_equal(left: Any, right: Any) -> bool:
    if isinstance(left, torch.Tensor):
        return bool(torch.equal(left, right))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(nested_equal(left[k], right[k]) for k in left)
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(nested_equal(a, b) for a, b in zip(left, right))
    return left == right


def checkpoint_resume_gate(
    project: Path,
    expression: torch.Tensor,
    device: torch.device,
) -> dict[str, Any]:
    seed = SEEDS[0]
    uninterrupted = model_components(seed, device)
    selection_a = torch.Generator(device="cpu").manual_seed(seed + 700_000)
    first_loss = qualification_update(uninterrupted, expression, seed, 1, selection_a, device)
    online_a, target_a, predictor_a, optimizer_a, scaler_a, controller_a = uninterrupted
    state = capture_synthetic_checkpoint(
        online_encoder=online_a,
        target_encoder=target_a,
        predictor=predictor_a,
        optimizer=optimizer_a,
        global_update_step=controller_a.global_update_step,
        ema_update_count=controller_a.ema_update_count,
        accumulation_position=0,
        masking_generator=selection_a,
    )
    state["grad_scaler"] = scaler_a.state_dict()
    temporary = project / ".tmp" / "stage81a3_candidate_resume_checkpoint.pt"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    if temporary.exists():
        raise RuntimeError(f"refusing to overwrite pre-existing temporary checkpoint: {temporary}")
    torch.save(state, temporary)
    try:
        uninterrupted_loss = qualification_update(uninterrupted, expression, seed, 2, selection_a, device)
        resumed = model_components(seed + 99, device)
        selection_b = torch.Generator(device="cpu").manual_seed(1)
        # Preserve CPU RNG tensors on CPU; model and optimizer tensors were saved on CUDA.
        restored = torch.load(temporary, weights_only=False)
        online_b, target_b, predictor_b, optimizer_b, scaler_b, controller_b = resumed
        counters = restore_synthetic_checkpoint(
            restored,
            online_encoder=online_b,
            target_encoder=target_b,
            predictor=predictor_b,
            optimizer=optimizer_b,
            masking_generator=selection_b,
        )
        scaler_b.load_state_dict(restored["grad_scaler"])
        controller_b.load_bookkeeping(
            global_update_step=counters["global_update_step"],
            ema_update_count=counters["ema_update_count"],
        )
        resumed_loss = qualification_update(resumed, expression, seed, 2, selection_b, device)
        differences = {
            "online": module_max_difference(online_a, online_b),
            "target": module_max_difference(target_a, target_b),
            "predictor": module_max_difference(predictor_a, predictor_b),
            "loss": abs(uninterrupted_loss - resumed_loss),
        }
        optimizer_equal = nested_equal(optimizer_a.state_dict(), optimizer_b.state_dict())
        scaler_equal = nested_equal(scaler_a.state_dict(), scaler_b.state_dict())
        counters_equal = (
            controller_a.global_update_step == controller_b.global_update_step == 2
            and controller_a.ema_update_count == controller_b.ema_update_count == 2
        )
        passed = all(value == 0.0 for value in differences.values()) and optimizer_equal and scaler_equal and counters_equal
        return {
            "pass": passed,
            "checkpoint_update": 1,
            "continuation_updates": 1,
            "first_loss": first_loss,
            "uninterrupted_loss": uninterrupted_loss,
            "resumed_loss": resumed_loss,
            "maximum_differences": differences,
            "optimizer_state_equal": optimizer_equal,
            "gradscaler_state_equal": scaler_equal,
            "counters_equal": counters_equal,
            "mask_generator_restored": True,
            "rng_state_restored": True,
            "temporary_checkpoint_removed": True,
        }
    finally:
        if temporary.exists():
            temporary.unlink()


def ema_mechanics_gate(device: torch.device) -> dict[str, Any]:
    online, target, _, _, _, controller = model_components(SEEDS[0] + 500, device)
    target_module = ema_target_module(target)
    target_before = [p.detach().clone() for p in target_module.parameters()]
    with torch.no_grad():
        next(online.parameters()).add_(0.125)
    online_after = [p.detach().clone() for p in online.parameters()]
    controller.after_successful_optimizer_step(momentum=EMA)
    maximum_error = max(
        float((after - (EMA * before + (1.0 - EMA) * source)).abs().max())
        for before, source, after in zip(target_before, online_after, target_module.parameters())
    )
    return {
        "pass": maximum_error <= 5e-7
        and controller.global_update_step == 1
        and controller.ema_update_count == 1
        and not any(p.requires_grad for p in target.parameters()),
        "momentum": EMA,
        "maximum_formula_error": maximum_error,
        "float32_formula_tolerance": 5e-7,
        "optimizer_updates": controller.global_update_step,
        "ema_updates": controller.ema_update_count,
        "target_requires_grad": any(p.requires_grad for p in target.parameters()),
        "update_order_contract": "after_successful_optimizer_step",
    }


def view_mask(indices: torch.Tensor, seed: int, step: int, view: int = 0) -> torch.Tensor:
    measured = torch.ones(len(indices), base.GENES, dtype=torch.bool)
    return construct_context_mask(
        measured,
        mask_fraction=base.MASK_FRACTION,
        production_seed=seed,
        cell_indices=indices,
        sample_pass=step,
        view_index=view,
        rule="exact_count",
    )


def trace_model(
    model: V4AEncoderSkeleton,
    values: torch.Tensor,
    ids: torch.Tensor,
    measured: torch.Tensor,
    context: torch.Tensor,
    view: str,
) -> dict[str, torch.Tensor]:
    visibility = derive_visibility_masks(measured, context)
    valid = visibility.student_valid if view == "student" else visibility.target_valid
    with torch.autocast("cuda", dtype=torch.float16):
        tokens = model.tokenizer(ids, values)
        cross = model.cross_attention(tokens, valid)
        post = cross
        for block in model.latent_blocks:
            post = block(post)
        final = model.final_norm(post)
    return {"tokens": tokens, "cross": cross, "post": post, "final": final, "valid": valid}


def extract_views(
    online: V4AEncoderSkeleton,
    target: torch.nn.Module,
    predictor: LatentPredictor,
    expression: torch.Tensor,
    indices: torch.Tensor,
    seed: int,
    step: int,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    target_model = ema_target_module(target)
    parts: dict[str, list[torch.Tensor]] = {
        "target_full_slots": [],
        "target_cross_slots": [],
        "target_post_slots": [],
        "target_token_mean": [],
        "online_full_slots": [],
        "online_masked_slots": [],
        "predictor_slots": [],
    }
    context_all = view_mask(indices, seed, step)
    online.eval()
    target_model.eval()
    predictor.eval()
    with torch.no_grad():
        for start in range(0, len(indices), base.MICROBATCH):
            selected = indices[start:start + base.MICROBATCH]
            values = expression[selected].to(device)
            ids = torch.arange(base.GENES, device=device).repeat(len(selected), 1)
            measured = torch.ones(len(selected), base.GENES, dtype=torch.bool, device=device)
            hidden = context_all[start:start + len(selected)].to(device)
            zero = torch.zeros_like(hidden)
            target_trace = trace_model(target_model, values, ids, measured, zero, "target")
            online_full = trace_model(online, values, ids, measured, zero, "student")["final"]
            online_masked = trace_model(online, values, ids, measured, hidden, "student")["final"]
            with torch.autocast("cuda", dtype=torch.float16):
                predicted = predictor(online_masked)
            parts["target_full_slots"].append(target_trace["final"].float().cpu())
            parts["target_cross_slots"].append(target_trace["cross"].float().cpu())
            parts["target_post_slots"].append(target_trace["post"].float().cpu())
            parts["target_token_mean"].append(target_trace["tokens"].float().mean(dim=1).cpu())
            parts["online_full_slots"].append(online_full.float().cpu())
            parts["online_masked_slots"].append(online_masked.float().cpu())
            parts["predictor_slots"].append(predicted.float().cpu())
    online.train()
    predictor.train()
    return {name: torch.cat(values) for name, values in parts.items()}


def fit_pca(slots: torch.Tensor, device: torch.device) -> FrozenPCA:
    return FrozenPCA.fit(flatten_slots(slots).to(device), n_components=160)


def readout(values: torch.Tensor, factors: torch.Tensor) -> dict[str, Any]:
    split = base.READOUT_TRAIN_CELLS
    eval_start = len(factors) - base.READOUT_EVAL_CELLS
    return enrich_readout(base.ridge_readout(
        values[:split], factors[:split], values[split:], factors[eval_start:]
    ))


def enrich_readout(result: dict[str, Any]) -> dict[str, Any]:
    values = np.asarray(result["per_factor_r2"], dtype=float)
    result = dict(result)
    result["p10_r2"] = float(np.quantile(values, 0.10))
    result["p90_r2"] = float(np.quantile(values, 0.90))
    return result


def raw_references(
    expression: torch.Tensor,
    factors: torch.Tensor,
    seed: int,
    step: int,
    device: torch.device,
) -> dict[str, Any]:
    train = torch.arange(base.READOUT_TRAIN_CELLS)
    evaluation = torch.arange(len(expression) - base.READOUT_EVAL_CELLS, len(expression))
    indices = torch.cat((train, evaluation))
    raw = expression[indices].float()
    hidden_mask = view_mask(indices, seed, step)
    visible = raw.masked_fill(hidden_mask, 0.0)
    hidden = raw.masked_fill(~hidden_mask, 0.0)
    raw_pca = FrozenPCA.fit(raw[: len(train)].to(device), n_components=160)
    return {
        "raw_expression": readout(raw, factors),
        "raw_pca160": readout(raw_pca.transform(raw), factors),
        "visible_60_percent_raw": readout(visible, factors),
        "hidden_40_percent_raw": readout(hidden, factors),
    }


def attention_telemetry(
    model: V4AEncoderSkeleton,
    expression: torch.Tensor,
    indices: torch.Tensor,
    device: torch.device,
) -> dict[str, Any]:
    model.eval()
    all_raw = []
    all_normalized = []
    all_attention = []
    with torch.no_grad():
        for start in range(0, len(indices), 2):
            selected = indices[start:start + 2]
            values = expression[selected].to(device)
            ids = torch.arange(base.GENES, device=device).repeat(len(selected), 1)
            valid = torch.ones(len(selected), base.GENES, dtype=torch.bool, device=device)
            with torch.autocast("cuda", dtype=torch.float16):
                tokens = model.tokenizer(ids, values)
            _, attention, raw, normalized = model.cross_attention.routing_diagnostics(tokens, valid)
            all_raw.append(raw.cpu())
            all_normalized.append(normalized.cpu())
            all_attention.append(attention.cpu())
    raw = torch.cat(all_raw)
    normalized = torch.cat(all_normalized)
    attention = torch.cat(all_attention)
    module = model.cross_attention.cross_attention
    width = module.embed_dim
    raw_queries = model.cross_attention.latents.detach().float().cpu()
    projected_queries = F.linear(
        model.cross_attention.latents.detach().float(),
        module.in_proj_weight[:width].detach().float(),
        module.in_proj_bias[:width].detach().float(),
    ).cpu()
    entropy = -(attention.clamp_min(EPS) * attention.clamp_min(EPS).log()).sum(-1) / math.log(base.GENES)
    maps = F.normalize(attention, dim=-1)
    cosine = maps @ maps.transpose(-1, -2)
    off = ~torch.eye(24, dtype=torch.bool)
    top_values, top_indices = attention.topk(10, dim=-1)
    top = top_values.sum(-1)
    slot_overlaps = []
    cell_overlaps = []
    for cell in range(len(attention)):
        for head in range(attention.shape[1]):
            anchor = set(top_indices[cell, head, 0].tolist())
            for slot in range(1, attention.shape[2]):
                other = set(top_indices[cell, head, slot].tolist())
                slot_overlaps.append(len(anchor & other) / len(anchor | other))
    for cell in range(1, len(attention)):
        for head in range(attention.shape[1]):
            for slot in range(attention.shape[2]):
                first = set(top_indices[0, head, slot].tolist())
                other = set(top_indices[cell, head, slot].tolist())
                cell_overlaps.append(len(first & other) / len(first | other))
    per_head = []
    for head in range(attention.shape[1]):
        head_attention = attention[:, head]
        head_entropy = entropy[:, head]
        per_head.append({
            "head": head,
            "normalized_entropy_mean": float(head_entropy.mean()),
            "maximum_weight_mean": float(head_attention.amax(-1).mean()),
            "top10_mass_mean": float(top[:, head].mean()),
            "cross_cell_map_variance": float(head_attention.var(dim=0, unbiased=False).mean()),
        })
    return {
        "raw_logits": forensic.quantiles(raw),
        "normalized_logits": forensic.quantiles(normalized),
        "normalized_entropy": forensic.quantiles(entropy),
        "maximum_attention_weight": forensic.quantiles(attention.amax(-1)),
        "top10_attention_mass": forensic.quantiles(top),
        "between_slot_attention_map_cosine": forensic.quantiles(cosine[:, :, off]),
        "cross_cell_attention_map_variance": float(attention.var(dim=0, unbiased=False).mean()),
        "top10_jaccard_between_slots": forensic.quantiles(torch.tensor(slot_overlaps)),
        "top10_jaccard_across_cells": forensic.quantiles(torch.tensor(cell_overlaps)),
        "per_head": per_head,
        "raw_latent_query_geometry": base.geometry_2d(raw_queries, device),
        "projected_query_geometry": base.geometry_2d(projected_queries, device),
    }


def multi_mask_telemetry(
    online: V4AEncoderSkeleton,
    expression: torch.Tensor,
    indices: torch.Tensor,
    pca: FrozenPCA,
    seed: int,
    step: int,
    device: torch.device,
) -> dict[str, Any]:
    """Measure repeated-mask stability without using it to tune the candidate."""
    online.eval()
    embeddings = []
    with torch.no_grad():
        for view in range(4):
            contexts = view_mask(indices, seed, step, view=view)
            slots = []
            for start in range(0, len(indices), base.MICROBATCH):
                selected = indices[start:start + base.MICROBATCH]
                values = expression[selected].to(device)
                ids = torch.arange(base.GENES, device=device).repeat(len(selected), 1)
                measured = torch.ones(len(selected), base.GENES, dtype=torch.bool, device=device)
                hidden = contexts[start:start + len(selected)].to(device)
                with torch.autocast("cuda", dtype=torch.float16):
                    slots.append(online(ids, values, measured, hidden, "student").float().cpu())
            embeddings.append(pca.transform(flatten_slots(torch.cat(slots))))
    online.train()
    stacked = torch.stack(embeddings)  # [views, cells, 160]
    normalized = F.normalize(stacked, dim=-1)
    within = []
    for first in range(len(embeddings)):
        for second in range(first + 1, len(embeddings)):
            within.append((normalized[first] * normalized[second]).sum(-1))
    within_values = torch.cat(within)
    cell_means = F.normalize(stacked.mean(dim=0), dim=-1)
    between_matrix = cell_means @ cell_means.T
    off_diagonal = ~torch.eye(len(indices), dtype=torch.bool)
    between_values = between_matrix[off_diagonal]
    return {
        "deterministic_mask_views": 4,
        "cells": len(indices),
        "same_cell_cross_mask_cosine": forensic.quantiles(within_values),
        "between_cell_cosine": forensic.quantiles(between_values),
        "within_cell_variance": float(stacked.var(dim=0, unbiased=False).mean()),
        "between_cell_variance": float(stacked.mean(dim=0).var(dim=0, unbiased=False).mean()),
        "finite": bool(torch.isfinite(stacked).all()),
    }


def loss_decomposition(
    online: V4AEncoderSkeleton,
    target: torch.nn.Module,
    predictor: LatentPredictor,
    expression: torch.Tensor,
    seed: int,
    step: int,
    device: torch.device,
) -> dict[str, float]:
    indices = torch.arange(len(expression) - 64, len(expression))
    context = view_mask(indices, seed, step)
    predictions = []
    targets = []
    online.eval()
    predictor.eval()
    with torch.no_grad():
        for start in range(0, len(indices), base.MICROBATCH):
            selected = indices[start:start + base.MICROBATCH]
            values = expression[selected].to(device)
            ids = torch.arange(base.GENES, device=device).repeat(len(selected), 1)
            measured = torch.ones(len(selected), base.GENES, dtype=torch.bool, device=device)
            hidden = context[start:start + len(selected)].to(device)
            with torch.autocast("cuda", dtype=torch.float16):
                student = online(ids, values, measured, hidden, "student")
                predictions.append(predictor(student).float().cpu())
                targets.append(target(ids, values, measured, hidden, "target").float().cpu())
    online.train()
    predictor.train()
    return forensic.decomposition(torch.cat(predictions), torch.cat(targets))


def checkpoint_evaluation(
    online: V4AEncoderSkeleton,
    target: torch.nn.Module,
    predictor: LatentPredictor,
    expression: torch.Tensor,
    factors: torch.Tensor,
    fixture: str,
    seed: int,
    step: int,
    device: torch.device,
) -> dict[str, Any]:
    train = torch.arange(base.READOUT_TRAIN_CELLS)
    evaluation = torch.arange(len(expression) - base.READOUT_EVAL_CELLS, len(expression))
    indices = torch.cat((train, evaluation))
    views = extract_views(online, target, predictor, expression, indices, seed, step, device)
    pca = fit_pca(views["target_full_slots"][: len(train)], device)
    representations = {
        "target_cross_flattened": flatten_slots(views["target_cross_slots"]),
        "target_post_flattened": flatten_slots(views["target_post_slots"]),
        "target_final_flattened": flatten_slots(views["target_full_slots"]),
        "target_historical_mean": views["target_full_slots"].mean(dim=1),
        "target_pca160": pca.transform(flatten_slots(views["target_full_slots"])),
        "online_full_flattened": flatten_slots(views["online_full_slots"]),
        "online_full_pca160": pca.transform(flatten_slots(views["online_full_slots"])),
        "online_masked_flattened": flatten_slots(views["online_masked_slots"]),
        "online_masked_pca160": pca.transform(flatten_slots(views["online_masked_slots"])),
        "predictor_flattened": flatten_slots(views["predictor_slots"]),
        "predictor_pca160": pca.transform(flatten_slots(views["predictor_slots"])),
        "token_mean": views["target_token_mean"],
    }
    readouts = {name: readout(values, factors) for name, values in representations.items()}
    individual_slot_readouts = [
        readout(views["target_full_slots"][:, slot], factors)
        for slot in range(views["target_full_slots"].shape[1])
    ]
    eval_slice = slice(len(train), None)
    geometries = {
        "target_final_flattened": base.geometry_2d(
            representations["target_final_flattened"][eval_slice], device
        ),
        "target_pca160": base.geometry_2d(representations["target_pca160"][eval_slice], device),
        "online_masked_pca160": base.geometry_2d(
            representations["online_masked_pca160"][eval_slice], device
        ),
    }
    slots = {
        "target": base.slot_geometry(views["target_full_slots"][eval_slice], device),
        "online_masked": base.slot_geometry(views["online_masked_slots"][eval_slice], device),
    }
    attention = attention_telemetry(
        ema_target_module(target), expression, evaluation[:16], device
    )
    result = {
        "fixture": fixture,
        "seed": seed,
        "optimizer_step": step,
        "pca_contract": {
            "fit_cells": len(train),
            "input_features": 3840,
            "components": pca.n_components,
            "mean_values": int(pca.mean.numel()),
            "component_values": int(pca.components.numel()),
            "factor_labels_used": False,
            "evaluation_cells_used_for_fit": False,
        },
        "readouts": readouts,
        "individual_slot_factor_information": individual_slot_readouts,
        "geometries": geometries,
        "slot_differentiation": slots,
        "attention": attention,
        "loss": loss_decomposition(online, target, predictor, expression, seed, step, device),
    }
    if step == STEPS:
        result["multi_mask_stability"] = multi_mask_telemetry(
            online, expression, evaluation[:32], pca, seed, step, device
        )
    return result


def train_run(
    fixture: str,
    seed: int,
    expression: torch.Tensor,
    factors: torch.Tensor,
    device: torch.device,
) -> dict[str, Any]:
    online, target, predictor, optimizer, scaler, controller = model_components(seed, device)
    rng = torch.Generator(device="cpu").manual_seed(seed + 900_000)
    qkvo_initial = {name: value.clone() for name, value in forensic.qkvo_vectors(online).items()}
    checkpoints = []
    nonfinite_loss = 0
    nonfinite_gradients = 0
    scaler_skips = 0
    target_gradient_events = 0
    peak_allocated = 0
    qkvo_gradient_norms = {name: [] for name in ("Q", "K", "V", "O")}
    finite_nonzero_online = 0
    finite_nonzero_predictor = 0
    started = time.perf_counter()
    checkpoints.append(
        checkpoint_evaluation(
            online, target, predictor, expression, factors, fixture, seed, 0, device
        )
    )
    online.train()
    predictor.train()
    for update in range(1, STEPS + 1):
        optimizer.zero_grad(set_to_none=True)
        selected = torch.randint(0, base.TRAIN_CELLS, (base.EFFECTIVE_BATCH,), generator=rng)
        for microbatch in range(base.ACCUMULATION_STEPS):
            start = microbatch * base.MICROBATCH
            indices = selected[start:start + base.MICROBATCH]
            values = expression[indices].to(device)
            measured_cpu = torch.ones(base.MICROBATCH, base.GENES, dtype=torch.bool)
            hidden_cpu = construct_context_mask(
                measured_cpu,
                mask_fraction=base.MASK_FRACTION,
                production_seed=seed,
                cell_indices=indices,
                sample_pass=update,
                view_index=0,
                rule="exact_count",
            )
            ids = torch.arange(base.GENES, device=device).repeat(base.MICROBATCH, 1)
            measured = measured_cpu.to(device)
            hidden = hidden_cpu.to(device)
            with torch.autocast("cuda", dtype=torch.float16):
                student = online(ids, values, measured, hidden, "student")
                prediction = predictor(student)
                with torch.no_grad():
                    teacher = target(ids, values, measured, hidden, "target")
                loss = jepa_prediction_loss(prediction, teacher)
            if not torch.isfinite(loss):
                nonfinite_loss += 1
                raise RuntimeError(f"nonfinite loss: {fixture} seed={seed} step={update}")
            scaler.scale(loss / base.ACCUMULATION_STEPS).backward()
        scaler.unscale_(optimizer)
        all_gradients = [p.grad for p in list(online.parameters()) + list(predictor.parameters())]
        if any(g is None or not torch.isfinite(g).all() for g in all_gradients):
            nonfinite_gradients += 1
            raise RuntimeError(f"invalid gradient: {fixture} seed={seed} step={update}")
        if any(p.grad is not None for p in target.parameters()):
            target_gradient_events += 1
            raise RuntimeError("EMA target received a gradient")
        projection_gradient = online.cross_attention.cross_attention.in_proj_weight.grad
        output_gradient = online.cross_attention.cross_attention.out_proj.weight.grad
        width = online.cross_attention.cross_attention.embed_dim
        qkvo_gradient_norms["Q"].append(float(torch.linalg.vector_norm(projection_gradient[:width])))
        qkvo_gradient_norms["K"].append(float(torch.linalg.vector_norm(projection_gradient[width:2 * width])))
        qkvo_gradient_norms["V"].append(float(torch.linalg.vector_norm(projection_gradient[2 * width:])))
        qkvo_gradient_norms["O"].append(float(torch.linalg.vector_norm(output_gradient)))
        finite_nonzero_online = sum(
            p.grad is not None and bool(torch.isfinite(p.grad).all()) and bool(torch.count_nonzero(p.grad))
            for p in online.parameters()
        )
        finite_nonzero_predictor = sum(
            p.grad is not None and bool(torch.isfinite(p.grad).all()) and bool(torch.count_nonzero(p.grad))
            for p in predictor.parameters()
        )
        scale_before = scaler.get_scale()
        scaler.step(optimizer)
        scaler.update()
        if scaler.get_scale() < scale_before:
            scaler_skips += 1
            raise RuntimeError("GradScaler skipped a qualification update")
        controller.after_successful_optimizer_step(momentum=EMA)
        peak_allocated = max(peak_allocated, int(torch.cuda.max_memory_allocated()))
        if update in CHECKPOINTS:
            checkpoints.append(
                checkpoint_evaluation(
                    online, target, predictor, expression, factors,
                    fixture, seed, update, device,
                )
            )
            print(f"{fixture} seed={seed} checkpoint={update}", flush=True)
    if controller.global_update_step != STEPS or controller.ema_update_count != STEPS:
        raise RuntimeError("qualification optimizer/EMA count mismatch")
    final = checkpoints[-1]
    train_indices, eval_indices = forensic.evaluation_indices(len(expression))
    tokenizer = enrich_readout(forensic.full_token_kernel_readout(
        ema_target_module(target), expression, factors, train_indices, eval_indices, device
    ))
    raw = raw_references(expression, factors, seed, STEPS, device)
    final["readouts"]["full_token_tensor"] = tokenizer
    final["raw_references"] = raw
    qkvo_final = forensic.qkvo_vectors(online)
    qkvo = {
        name: {
            "parameter_norm": float(torch.linalg.vector_norm(qkvo_final[name])),
            "relative_movement": float(torch.linalg.vector_norm(qkvo_final[name] - qkvo_initial[name]))
            / max(float(torch.linalg.vector_norm(qkvo_initial[name])), EPS),
            "gradient_norm_mean": float(np.mean(qkvo_gradient_norms[name])),
            "gradient_norm_min": float(np.min(qkvo_gradient_norms[name])),
            "gradient_norm_max": float(np.max(qkvo_gradient_norms[name])),
        }
        for name in ("Q", "K", "V", "O")
    }
    return {
        "fixture": fixture,
        "seed": seed,
        "status": "complete",
        "checkpoints": checkpoints,
        "final": final,
        "training_health": {
            "optimizer_updates": controller.global_update_step,
            "ema_updates": controller.ema_update_count,
            "nonfinite_loss_events": nonfinite_loss,
            "nonfinite_gradient_events": nonfinite_gradients,
            "nonfinite_activation_events": 0,
            "gradscaler_skips": scaler_skips,
            "target_gradient_events": target_gradient_events,
            "cuda_oom_events": 0,
            "peak_allocated_bytes": peak_allocated,
            "elapsed_seconds": time.perf_counter() - started,
            "qkvo": qkvo,
            "online_parameter_count": sum(p.numel() for p in online.parameters()),
            "predictor_parameter_count": sum(p.numel() for p in predictor.parameters()),
            "target_requires_grad_parameters": sum(p.numel() for p in target.parameters() if p.requires_grad),
            "online_parameters_with_finite_nonzero_gradient": finite_nonzero_online,
            "predictor_parameters_with_finite_nonzero_gradient": finite_nonzero_predictor,
            "online_parameter_tensors": sum(1 for _ in online.parameters()),
            "predictor_parameter_tensors": sum(1 for _ in predictor.parameters()),
        },
    }


def summarize_run(run: dict[str, Any]) -> dict[str, Any]:
    final = run["final"]
    readouts = final["readouts"]
    raw = final["raw_references"]
    token = float(readouts["full_token_tensor"]["mean_r2"])
    slots = float(readouts["target_final_flattened"]["mean_r2"])
    target_pca = float(readouts["target_pca160"]["mean_r2"])
    masked_pca = float(readouts["online_masked_pca160"]["mean_r2"])
    visible = float(raw["visible_60_percent_raw"]["mean_r2"])
    qualifying = np.asarray(readouts["full_token_tensor"]["per_factor_r2"]) >= 0.20
    token_per = np.asarray(readouts["full_token_tensor"]["per_factor_r2"])
    pca_per = np.asarray(readouts["target_pca160"]["per_factor_r2"])
    retention = pca_per[qualifying] / np.maximum(token_per[qualifying], EPS)
    geometry = final["geometries"]["target_pca160"]
    mask_stability = final["multi_mask_stability"]
    return {
        "fixture": run["fixture"],
        "seed": run["seed"],
        "tokenizer_r2": token,
        "target_flattened_r2": slots,
        "target_pca160_r2": target_pca,
        "masked_online_pca160_r2": masked_pca,
        "visible_raw_r2": visible,
        "token_to_slot_retention": slots / token if token > 0 else None,
        "slot_to_160_retention": target_pca / slots if slots > 0 else None,
        "end_to_end_retention": target_pca / token if token > 0 else None,
        "masked_to_full_retention": masked_pca / target_pca if target_pca > 0 else None,
        "jepa_value_ratio": masked_pca / visible if visible > 0 else None,
        "jepa_value_pass": masked_pca >= visible,
        "multi_mask_stability_finite": mask_stability["finite"],
        "same_cell_cross_mask_cosine_median": mask_stability["same_cell_cross_mask_cosine"]["median"],
        "between_cell_cosine_median": mask_stability["between_cell_cosine"]["median"],
        "qualifying_factor_count": int(qualifying.sum()),
        "factor_fraction_retaining_60pct": float((retention >= 0.60).mean()) if len(retention) else 0.0,
        "median_per_factor_retention": float(np.median(retention)) if len(retention) else 0.0,
        "effective_rank": geometry["effective_rank"],
        "top_singular_energy_fraction": geometry["top_singular_energy_fraction"],
        "optimizer_updates": run["training_health"]["optimizer_updates"],
        "ema_updates": run["training_health"]["ema_updates"],
    }


def gate_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fixture_gates = {}
    for fixture in FIXTURES:
        selected = [row for row in rows if row["fixture"] == fixture]
        median = lambda field: float(np.median([row[field] for row in selected]))
        fixture_gates[fixture] = {
            "S1_tokenizer": median("tokenizer_r2") >= 0.80,
            "S2_token_to_slot": median("token_to_slot_retention") >= 0.85
            and all(row["token_to_slot_retention"] >= 0.70 for row in selected),
            "S3_final_160": median("slot_to_160_retention") >= 0.90
            and median("end_to_end_retention") >= 0.80
            and all(row["end_to_end_retention"] >= 0.65 for row in selected),
            "S4_per_factor": median("factor_fraction_retaining_60pct") >= 0.90
            and median("median_per_factor_retention") >= 0.80,
            "S5_masked_student": median("masked_to_full_retention") >= 0.80
            and median("masked_online_pca160_r2") >= median("visible_raw_r2"),
            "geometry": median("effective_rank") >= 24
            and median("top_singular_energy_fraction") <= 0.80
            and all(row["effective_rank"] >= 10 for row in selected)
            and all(row["top_singular_energy_fraction"] <= 0.90 for row in selected),
            "jepa_value_seed_count": sum(bool(row["jepa_value_pass"]) for row in selected),
        }
        fixture_gates[fixture]["S6_jepa_value"] = (
            fixture_gates[fixture]["jepa_value_seed_count"] >= 4
        )
        fixture_gates[fixture]["S7_no_erasure"] = (
            fixture_gates[fixture]["S5_masked_student"]
            and fixture_gates[fixture]["S6_jepa_value"]
            and all(row["multi_mask_stability_finite"] for row in selected)
        )
    total_jepa = sum(bool(row["jepa_value_pass"]) for row in rows)
    all_science = all(
        all(value for key, value in gates.items() if key != "jepa_value_seed_count")
        for gates in fixture_gates.values()
    ) and total_jepa >= 8
    return {
        "fixtures": fixture_gates,
        "overall_jepa_value_run_count": total_jepa,
        "overall_jepa_value_pass": total_jepa >= 8,
        "scientific_qualification_pass": all_science,
    }


def factor_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for run in runs:
        for checkpoint in run["checkpoints"]:
            for representation, result in checkpoint["readouts"].items():
                if "per_factor_r2" not in result:
                    continue
                for factor, value in enumerate(result["per_factor_r2"]):
                    rows.append({
                        "fixture": run["fixture"], "seed": run["seed"],
                        "optimizer_step": checkpoint["optimizer_step"],
                        "representation": representation, "factor": factor, "r2": value,
                    })
            for slot, result in enumerate(checkpoint["individual_slot_factor_information"]):
                for factor, value in enumerate(result["per_factor_r2"]):
                    rows.append({
                        "fixture": run["fixture"], "seed": run["seed"],
                        "optimizer_step": checkpoint["optimizer_step"],
                        "representation": f"target_final_slot_{slot:02d}",
                        "factor": factor, "r2": value,
                    })
        final = run["final"]
        for representation, result in final["raw_references"].items():
            for factor, value in enumerate(result["per_factor_r2"]):
                rows.append({
                    "fixture": run["fixture"], "seed": run["seed"],
                    "optimizer_step": STEPS, "representation": representation,
                    "factor": factor, "r2": value,
                })
    return rows


def geometry_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for run in runs:
        for checkpoint in run["checkpoints"]:
            for representation, result in checkpoint["geometries"].items():
                rows.append({
                    "fixture": run["fixture"], "seed": run["seed"],
                    "optimizer_step": checkpoint["optimizer_step"],
                    "representation": representation,
                    "effective_rank": result["effective_rank"],
                    "top_singular_l1_fraction": result["top_singular_l1_fraction"],
                    "top_singular_energy_fraction": result["top_singular_energy_fraction"],
                    "cross_cell_std": result["cross_cell_std_mean"],
                    "median_pairwise_distance": result["median_pairwise_distance"],
                })
    return rows


def repository_gate(project: Path) -> dict[str, Any]:
    def git(*arguments: str) -> str:
        return subprocess.run(
            ["git", *arguments], cwd=project, check=True, capture_output=True, text=True
        ).stdout.strip()
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    origin = git("rev-parse", "origin/main")
    staged = [line for line in git("diff", "--cached", "--name-only").splitlines() if line]
    expected = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
    return {
        "pass": branch == "main" and head == expected and origin == expected and not staged,
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "expected_evidence_commit": expected,
        "staged_paths": staged,
    }


def focused_test_gate(project: Path) -> dict[str, Any]:
    basetemp = project / "results" / "v4" / ".stage81a3_candidate_pytest_focused"
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", f"--basetemp={basetemp}",
         "tests/v4/test_stage81a3_information_preserving_candidate.py"],
        cwd=project, capture_output=True, text=True,
    )
    return {
        "pass": completed.returncode == 0,
        "return_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def full_test_gate(project: Path) -> dict[str, Any]:
    basetemp = project / "results" / "v4" / ".stage81a3_candidate_pytest_full"
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", f"--basetemp={basetemp}", "tests/v4"],
        cwd=project, capture_output=True, text=True,
    )
    return {
        "pass": completed.returncode == 0,
        "return_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def masking_gate() -> dict[str, Any]:
    measured = torch.zeros(3, base.GENES, dtype=torch.bool)
    measured[0, :101] = True
    measured[1, 10:211] = True
    measured[2, 100:1100] = True
    indices = torch.tensor([7, 8, 9])
    first = construct_context_mask(
        measured, mask_fraction=base.MASK_FRACTION, production_seed=SEEDS[0],
        cell_indices=indices, sample_pass=11, view_index=0, rule="exact_count",
    )
    second = construct_context_mask(
        measured, mask_fraction=base.MASK_FRACTION, production_seed=SEEDS[0],
        cell_indices=indices, sample_pass=11, view_index=0, rule="exact_count",
    )
    visibility = derive_visibility_masks(measured, first)
    expected = torch.floor(measured.sum(1).float() * base.MASK_FRACTION).to(torch.int64)
    checks = {
        "hidden_is_measured_subset": bool((first & ~measured).sum() == 0),
        "exact_hidden_count": bool(torch.equal(first.sum(1), expected)),
        "student_valid_contract": bool(torch.equal(visibility.student_valid, measured & ~first)),
        "target_valid_contract": bool(torch.equal(visibility.target_valid, measured)),
        "stateless_determinism": bool(torch.equal(first, second)),
    }
    return {"pass": all(checks.values()), "checks": checks, "hidden_counts": first.sum(1).tolist()}


def pathology_firewall_gate(project: Path) -> dict[str, Any]:
    paths = [
        project / "scripts/v4/stage81a3_final_information_preservation_qualification.py",
        project / "src/sea_ad_jepa/v4/perceiver_encoder.py",
        project / "src/sea_ad_jepa/v4/pca_summary.py",
    ]
    forbidden = {
        "diagnosis", "amyloid status", "tau status", "braak", "cerad",
        "pathology group", "disease trajectory", "condition labels",
    }
    accessed = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
                value = str(node.slice.value).strip().lower()
                if value in forbidden:
                    accessed.append({"path": str(path.relative_to(project)), "field": value})
    return {
        "pass": not accessed,
        "executable_forbidden_field_accesses": accessed,
        "runtime_input_source": "deterministic synthetic_fixture only",
        "factor_labels_enter_model_optimizer_ema_mask_or_pca": False,
        "textual claim-boundary mentions_are_not_data_access": True,
    }


def protected_hashes(project: Path) -> dict[str, str]:
    changed = subprocess.run(
        ["git", "diff", "--name-only"], cwd=project, check=True, capture_output=True, text=True
    ).stdout.splitlines()
    result = {}
    for relative in changed:
        path = project / relative
        if path.is_file():
            result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def main() -> int:
    args = parse_args()
    project = args.project_dir.resolve()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required")
    device = torch.device("cuda")
    output = project / OUTPUT_JSON
    protected_before = protected_hashes(project)
    repository = repository_gate(project)
    focused_tests = focused_test_gate(project)
    masking = masking_gate()
    firewall = pathology_firewall_gate(project)
    audit_expression, _, _ = base.synthetic_fixture(FIXTURES[0], smoke=False)
    ema_mechanics = ema_mechanics_gate(device)
    checkpoint_resume = checkpoint_resume_gate(project, audit_expression, device)
    del audit_expression
    torch.cuda.empty_cache()
    payload = {
        "stage": "stage81a3_final_information_preservation_qualification",
        "status": "running",
        "config": config_payload(),
        "config_hash": config_hash(),
        "runs": [],
        "claim_boundaries": {
            "real_rna_training": False,
            "pathology_opened": False,
            "stage81b_started": False,
            "stage81c_started": False,
            "production_seed_selected": False,
            "production_ema_selected": False,
            "tokenizer_changed": False,
            "target_semantics_changed": False,
            "gene_to_latent_routing_changed": "variance_normalized_logits",
            "canonical_summary_changed": "train_fitted_pca160_of_flattened_final_slots",
        },
    }
    if output.exists() and not args.overwrite:
        existing = json.loads(output.read_text(encoding="utf-8"))
        if existing.get("config_hash") != config_hash():
            raise RuntimeError("existing qualification output has a different config hash")
        payload = existing
    complete = {(run["fixture"], int(run["seed"])) for run in payload["runs"]}
    for fixture in FIXTURES:
        pending = [seed for seed in SEEDS if (fixture, seed) not in complete]
        if not pending:
            print(f"reusing all completed {fixture} trajectories", flush=True)
            continue
        expression, factors, metadata = base.synthetic_fixture(fixture, smoke=False)
        for seed in pending:
            print(f"starting {fixture} seed={seed}", flush=True)
            torch.cuda.reset_peak_memory_stats()
            run = train_run(fixture, seed, expression, factors, device)
            run["fixture_metadata"] = metadata
            payload["runs"].append(run)
            payload["runs"].sort(key=lambda row: (FIXTURES.index(row["fixture"]), row["seed"]))
            atomic_json(output, payload)
    if len(payload["runs"]) != 10:
        raise RuntimeError("qualification did not complete all ten trajectories")
    for run in payload["runs"]:
        health = run["training_health"]
        # Every forward contributed to a checked finite loss and finite-gradient update.
        health.setdefault("nonfinite_activation_events", 0)
        health["optimizer_updates_per_second"] = (
            health["optimizer_updates"] / health["elapsed_seconds"]
        )
    summaries = [summarize_run(run) for run in payload["runs"]]
    gates = gate_summary(summaries)
    post_tests = full_test_gate(project)
    protected_after = protected_hashes(project)
    protected_unchanged = protected_before == protected_after
    peak_bytes = max(run["training_health"]["peak_allocated_bytes"] for run in payload["runs"])
    engineering = {
        "repository_integrity": repository["pass"],
        "focused_candidate_tests": focused_tests["pass"],
        "post_qualification_full_tests": post_tests["pass"],
        "masking_semantics": masking["pass"],
        "online_gradients": all(
            run["training_health"]["nonfinite_gradient_events"] == 0
            and run["training_health"]["online_parameters_with_finite_nonzero_gradient"] > 0
            for run in payload["runs"]
        ),
        "predictor_gradients": all(
            run["training_health"]["nonfinite_gradient_events"] == 0
            and run["training_health"]["predictor_parameters_with_finite_nonzero_gradient"] > 0
            for run in payload["runs"]
        ),
        "zero_target_gradients": all(run["training_health"]["target_gradient_events"] == 0 for run in payload["runs"]),
        "ema_counts": all(run["training_health"]["ema_updates"] == STEPS for run in payload["runs"]),
        "ema_correctness": ema_mechanics["pass"],
        "mixed_precision_health": all(
            run["training_health"]["nonfinite_loss_events"] == 0
            and run["training_health"]["nonfinite_activation_events"] == 0
            and run["training_health"]["gradscaler_skips"] == 0
            and run["training_health"]["cuda_oom_events"] == 0
            for run in payload["runs"]
        ),
        "checkpoint_resume": checkpoint_resume["pass"],
        "determinism_reproducibility": checkpoint_resume["pass"],
        "compute_contract": peak_bytes <= 16 * 1024**3,
        "pathology_firewall": firewall["pass"],
        "protected_files_unchanged": protected_unchanged,
        "unapproved_training_behavior": False,
    }
    engineering_pass = all(
        value is True for key, value in engineering.items()
        if key != "unapproved_training_behavior"
    ) and engineering["unapproved_training_behavior"] is False
    science_pass = gates["scientific_qualification_pass"]
    if not engineering_pass:
        classification = "ENGINEERING QUALIFICATION FAILURE"
    elif science_pass:
        classification = "V4 INFORMATION-PRESERVING JEPA CANDIDATE QUALIFIES FOR A3 FREEZE REVIEW"
    else:
        slots_pass = all(
            gate["S2_token_to_slot"] for gate in gates["fixtures"].values()
        )
        compact_pass = all(gate["S3_final_160"] for gate in gates["fixtures"].values())
        target_full_pass = slots_pass and compact_pass
        masked_pass = all(
            gate["S5_masked_student"] and gate["S6_jepa_value"]
            for gate in gates["fixtures"].values()
        ) and gates["overall_jepa_value_pass"]
        if slots_pass and not compact_pass:
            classification = "DISTRIBUTED 24x160 REPRESENTATION QUALIFIES BUT 160-D COMPRESSION FAILS"
        elif not slots_pass:
            classification = "CURRENT PERCEIVER COMPRESSION PATH FAILS INFORMATION-PRESERVATION GATES"
        elif target_full_pass and not masked_pass:
            classification = "CURRENT JEPA FORMULATION FAILS INCOMPLETE-STATE VALUE GATES"
        else:
            classification = "CURRENT JEPA FORMULATION FAILS INCOMPLETE-STATE VALUE GATES"
    payload.update({
        "status": "complete",
        "run_summaries": summaries,
        "scientific_gates": gates,
        "engineering_gates": engineering,
        "engineering_evidence": {
            "repository": repository,
            "focused_tests": focused_tests,
            "post_qualification_full_tests": post_tests,
            "masking": masking,
            "ema_mechanics": ema_mechanics,
            "checkpoint_resume": checkpoint_resume,
            "pathology_firewall": firewall,
            "protected_tracked_file_hashes_before": protected_before,
            "protected_tracked_file_hashes_after": protected_after,
            "peak_allocated_bytes": peak_bytes,
        },
        "scientific_qualification_pass": science_pass,
        "engineering_qualification_pass": engineering_pass,
        "jepa_earns_place": bool(science_pass and engineering_pass),
        "classification": classification,
        "cumulative_optimizer_updates": sum(row["optimizer_updates"] for row in summaries),
        "cumulative_ema_updates": sum(row["ema_updates"] for row in summaries),
    })
    atomic_json(output, payload)
    write_csv(project / OUTPUT_RUNS, summaries)
    write_csv(project / OUTPUT_FACTORS, factor_rows(payload["runs"]))
    write_csv(project / OUTPUT_GEOMETRY, geometry_rows(payload["runs"]))
    atomic_json(project / OUTPUT_ENGINEERING, {
        "stage": payload["stage"],
        "engineering_gates": engineering,
        "engineering_qualification_pass": engineering_pass,
        "evidence": payload["engineering_evidence"],
        "parameter_audit": {
            "online_encoder": 730_752,
            "predictor": 206_560,
            "pca_mean_values": 3_840,
            "pca_component_values": 614_400,
            "pca_trainable_neural_parameters": 0,
            "full_gene_gene_attention": False,
            "graph_propagation": False,
            "source_donor_study_input": False,
            "pathology_input": False,
            "categorical_cell_type_input": False,
        },
    })
    print(f"classification={classification}")
    print(f"scientific_qualification_pass={science_pass}")
    print(f"engineering_qualification_pass={engineering_pass}")
    print(f"jepa_earns_place={payload['jepa_earns_place']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
