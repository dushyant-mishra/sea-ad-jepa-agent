#!/usr/bin/env python3
"""Replay one trapped trajectory with diagnostic-only forensic instrumentation."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.v4 import stage81a3_synthetic_geometry_escape as base  # noqa: E402
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


FIXTURE = "balanced_multifactor"
SEED = 8114001
EMA = 0.996
CHECKPOINTS = base.CHECKPOINTS
LOGIT_CHECKPOINTS = (0, 20, 100, 300, 500)
DEEP_CHECKPOINTS = (0, 100, 300, 500)
FORENSIC_CELLS = 16
MASK_VIEWS = 8
EPS = 1e-12
PRIOR_PATH = Path("results/v4/stage81a3_ema_bootstrap_disambiguation.json")
OUTPUT_JSON = Path("results/v4/stage81a3_forensic_failed_trajectory_replay.json")
OUTPUT_LOSS = Path("results/v4/stage81a3_forensic_loss_decomposition.csv")
OUTPUT_QKVO = Path("results/v4/stage81a3_forensic_attention_qkvo.csv")
OUTPUT_TOKEN = Path("results/v4/stage81a3_forensic_token_information.csv")
OUTPUT_MASK = Path("results/v4/stage81a3_forensic_mask_sensitivity.csv")
REPLAY_TOLERANCES = {
    "jepa_diagnostic_loss": 1e-6,
    "effective_rank": 5e-3,
    "online_effective_rank": 5e-3,
    "top_singular_energy_fraction": 1e-5,
    "online_top_singular_energy_fraction": 1e-5,
    "known_factor_heldout_mean_r2": 2.5e-2,
    "online_known_factor_heldout_mean_r2": 2.5e-2,
    "slot_cosine": 1e-5,
    "slot_variance": 1e-5,
    "online_target_distance": 1e-4,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument(
        "--finalize-existing",
        action="store_true",
        help="Re-evaluate replay agreement and classification without training.",
    )
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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = sorted({key for row in rows for key in row})
    temporary = path.with_name(f".{path.name}.temporary")
    path.parent.mkdir(parents=True, exist_ok=True)
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def quantiles(values: torch.Tensor | np.ndarray) -> dict[str, float]:
    array = np.asarray(values, dtype=float).reshape(-1)
    return {
        "minimum": float(array.min()),
        "p01": float(np.quantile(array, 0.01)),
        "p05": float(np.quantile(array, 0.05)),
        "p10": float(np.quantile(array, 0.10)),
        "median": float(np.median(array)),
        "mean": float(array.mean()),
        "p90": float(np.quantile(array, 0.90)),
        "p95": float(np.quantile(array, 0.95)),
        "p99": float(np.quantile(array, 0.99)),
        "maximum": float(array.max()),
        "standard_deviation": float(array.std()),
    }


def prior_run(project: Path) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
    payload = json.loads((project / PRIOR_PATH).read_text(encoding="utf-8"))
    run = next(
        item for item in payload["runs"]
        if item["fixture"] == FIXTURE and int(item["seed"]) == SEED
    )
    if payload["configuration"]["ema"]["fixed_momentum"] != EMA:
        raise RuntimeError("Prior forensic comparator is not EMA 0.996")
    return run, {int(row["optimizer_step"]): row for row in run["trajectory"]}


def evaluate_replay_agreement(
    trajectory: list[dict[str, Any]],
    prior_by_step: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    rows = []
    for row in trajectory:
        step = int(row["optimizer_step"])
        comparison = prior_by_step[step]
        differences = {
            field: abs(float(row[field]) - float(comparison[field]))
            for field in REPLAY_TOLERANCES
        }
        field_pass = {
            field: differences[field] <= tolerance
            for field, tolerance in REPLAY_TOLERANCES.items()
        }
        rows.append({
            "optimizer_step": step,
            "absolute_differences": differences,
            "field_pass": field_pass,
            "maximum_absolute_difference": max(differences.values()),
        })
    return {
        "pass": all(all(row["field_pass"].values()) for row in rows),
        "tolerances_by_field": REPLAY_TOLERANCES,
        "tolerance_interpretation": (
            "Numerical replay tolerances by diagnostic; these are not scientific "
            "effect thresholds. Factor-readout R2 is least stable because it is a "
            "separate held-out ridge solve on narrow representations."
        ),
        "maximum_absolute_difference": max(row["maximum_absolute_difference"] for row in rows),
        "per_checkpoint": rows,
    }


def classify_forensics(
    forensic: dict[str, Any],
    trajectory: list[dict[str, Any]],
) -> tuple[str, str, dict[str, Any]]:
    final = forensic["500"]
    final_loss = final["loss_decomposition"]["full_slots"]
    token_r2 = float(final["full_token_factor_readout"]["mean_r2"])
    cross_r2 = float(final["stage_factor_readouts"]["cross_attention_mean"]["mean_r2"])
    raw_r2 = float(final["raw_factor_readouts"]["full_raw_expression"]["mean_r2"])
    final_trajectory = next(row for row in trajectory if int(row["optimizer_step"]) == 500)
    attention = final_trajectory["target_cross_attention_summary"]
    entropy = float(attention["normalized_entropy"]["median"])
    slot_map_cosine = float(attention["between_slot_attention_map_cosine"]["median"])

    objective_shortcut = float(final_loss["residual_explained_fraction"]) <= 0.0
    tokenizer_loss = token_r2 <= 0.0 and raw_r2 > 0.0
    attention_loss = (
        token_r2 >= 0.5
        and cross_r2 <= 0.0
        and entropy >= 0.999
        and slot_map_cosine >= 0.999
    )
    evidence = {
        "objective_target_shortcut_strongly_supported": objective_shortcut,
        "attention_routing_bottleneck_strongly_supported": attention_loss,
        "tokenizer_information_bottleneck_strongly_supported": tokenizer_loss,
        "final_residual_explained_fraction": final_loss["residual_explained_fraction"],
        "final_full_token_factor_mean_r2": token_r2,
        "final_cross_attention_factor_mean_r2": cross_r2,
        "final_raw_expression_factor_mean_r2": raw_r2,
        "final_attention_normalized_entropy_median": entropy,
        "final_between_slot_attention_map_cosine_median": slot_map_cosine,
    }
    if sum((objective_shortcut, attention_loss, tokenizer_loss)) > 1:
        classification = "MULTIPLE MECHANISMS SUPPORTED"
    elif objective_shortcut:
        classification = "OBJECTIVE / TARGET SHORTCUT STRONGLY SUPPORTED"
    elif attention_loss:
        classification = "ATTENTION ROUTING BOTTLENECK STRONGLY SUPPORTED"
    elif tokenizer_loss:
        classification = "TOKENIZER INFORMATION BOTTLENECK STRONGLY SUPPORTED"
    else:
        classification = "FORENSIC RESULT INCONCLUSIVE"

    recommendations = {
        "TOKENIZER INFORMATION BOTTLENECK STRONGLY SUPPORTED":
            "TOKENIZATION / GENE-VALUE FUSION REVIEW JUSTIFIED",
        "ATTENTION ROUTING BOTTLENECK STRONGLY SUPPORTED":
            "NEXT CAUSAL TEST SHOULD TARGET Q/K ROUTING BOOTSTRAP, NOT TOKENIZATION",
        "OBJECTIVE / TARGET SHORTCUT STRONGLY SUPPORTED":
            "NEXT CAUSAL TEST SHOULD MODIFY TARGET SEMANTICS, NOT TOKENIZATION",
    }
    return (
        classification,
        recommendations.get(classification, "ONE HUMAN-APPROVED CAUSAL INTERVENTION IS REQUIRED"),
        evidence,
    )


def finalize_existing(project: Path, prior_by_step: dict[int, dict[str, Any]]) -> int:
    path = project / OUTPUT_JSON
    payload = json.loads(path.read_text(encoding="utf-8"))
    replay = evaluate_replay_agreement(payload["trajectory"], prior_by_step)
    if replay["pass"]:
        classification, recommendation, evidence = classify_forensics(
            payload["forensic_checkpoints"], payload["trajectory"]
        )
        payload["status"] = "complete"
        payload["classification"] = classification
        payload["recommendation"] = recommendation
        payload["mechanism_evidence"] = evidence
    else:
        payload["status"] = "replay_mismatch"
        payload["classification"] = "REPLAY MISMATCH"
        payload["recommendation"] = "STOP SCIENTIFIC INTERPRETATION"
        payload.pop("mechanism_evidence", None)
    payload["replay_agreement"] = replay
    atomic_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        f"replay_pass={replay['pass']} "
        f"max_abs_diff={replay['maximum_absolute_difference']:.3e}"
    )
    print(f"classification={payload['classification']}")
    print(f"recommendation={payload['recommendation']}")
    return 0 if replay["pass"] else 2


def evaluation_indices(n_cells: int) -> tuple[torch.Tensor, torch.Tensor]:
    train = torch.arange(base.READOUT_TRAIN_CELLS)
    evaluation = torch.arange(n_cells - base.READOUT_EVAL_CELLS, n_cells)
    return train, evaluation


def mask_for_indices(indices: torch.Tensor, checkpoint: int, view: int = 0) -> torch.Tensor:
    measurement = torch.ones(len(indices), base.GENES, dtype=torch.bool)
    return construct_context_mask(
        measurement,
        mask_fraction=base.MASK_FRACTION,
        production_seed=SEED,
        cell_indices=indices,
        sample_pass=checkpoint,
        view_index=view,
        rule="exact_count",
    )


def prediction_target_tensors(
    online: V4AEncoderSkeleton,
    target: torch.nn.Module,
    predictor: LatentPredictor,
    expression: torch.Tensor,
    indices: torch.Tensor,
    checkpoint: int,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    context_all = mask_for_indices(indices, checkpoint)
    predictions: list[torch.Tensor] = []
    targets: list[torch.Tensor] = []
    online.eval()
    predictor.eval()
    with torch.no_grad():
        for start in range(0, len(indices), base.MICROBATCH):
            end = min(start + base.MICROBATCH, len(indices))
            values = expression[indices[start:end]].to(device)
            context = context_all[start:end].to(device)
            measured = torch.ones_like(context)
            ids = torch.arange(base.GENES, device=device).repeat(end - start, 1)
            with torch.autocast("cuda", dtype=torch.float16):
                context_latents = online(ids, values, measured, context, "student")
                predictions.append(predictor(context_latents).float().cpu())
                targets.append(target(ids, values, measured, context, "target").float().cpu())
    online.train()
    predictor.train()
    return torch.cat(predictions), torch.cat(targets)


def decomposition(prediction: torch.Tensor, target: torch.Tensor) -> dict[str, float]:
    mu_prediction = prediction.mean(dim=0, keepdim=True)
    mu_target = target.mean(dim=0, keepdim=True)
    prediction_centered = prediction - mu_prediction
    target_centered = target - mu_target
    total = float((prediction - target).square().mean())
    common = float((mu_prediction - mu_target).square().mean())
    residual = float((prediction_centered - target_centered).square().mean())
    target_variance = float(target_centered.square().mean())
    error = abs(total - common - residual)
    normalized = residual / (target_variance + EPS)
    return {
        "total_mse": total,
        "common_mse": common,
        "residual_mse": residual,
        "target_residual_variance": target_variance,
        "normalized_residual_error": normalized,
        "residual_explained_fraction": 1.0 - normalized,
        "decomposition_absolute_reconstruction_error": error,
        "decomposition_relative_reconstruction_error": error / max(abs(total), EPS),
    }


def loss_decomposition_rows(
    prediction: torch.Tensor,
    target: torch.Tensor,
    checkpoint: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [{"optimizer_step": checkpoint, "level": "full_slots", "slot": None,
             **decomposition(prediction, target)}]
    slot_records = []
    for slot in range(prediction.shape[1]):
        record = {"optimizer_step": checkpoint, "level": "corresponding_slot", "slot": slot,
                  **decomposition(prediction[:, slot], target[:, slot])}
        rows.append(record)
        slot_records.append(record)
    pooled = decomposition(prediction.mean(dim=1), target.mean(dim=1))
    rows.append({"optimizer_step": checkpoint, "level": "mean_pooled", "slot": None, **pooled})
    fields = ("common_mse", "residual_mse", "normalized_residual_error", "residual_explained_fraction")
    summary = {
        "full_slots": rows[0],
        "mean_pooled": rows[-1],
        "slot_summary": {
            field: {
                "minimum": min(record[field] for record in slot_records),
                "median": float(np.median([record[field] for record in slot_records])),
                "maximum": max(record[field] for record in slot_records),
            }
            for field in fields
        },
    }
    return rows, summary


def qkvo_vectors(
    model: V4AEncoderSkeleton,
    *,
    gradients: bool = False,
) -> dict[str, torch.Tensor]:
    attention = model.cross_attention.cross_attention
    width = attention.embed_dim
    weight = attention.in_proj_weight.grad if gradients else attention.in_proj_weight.detach()
    bias = attention.in_proj_bias.grad if gradients else attention.in_proj_bias.detach()
    out_weight = attention.out_proj.weight.grad if gradients else attention.out_proj.weight.detach()
    out_bias = attention.out_proj.bias.grad if gradients else attention.out_proj.bias.detach()
    output: dict[str, torch.Tensor] = {}
    for index, name in enumerate(("Q", "K", "V")):
        if weight is None or bias is None:
            output[name] = torch.zeros(width * width + width, device=attention.in_proj_weight.device)
        else:
            output[name] = torch.cat((
                weight[index * width:(index + 1) * width].float().reshape(-1),
                bias[index * width:(index + 1) * width].float().reshape(-1),
            ))
    if out_weight is None or out_bias is None:
        output["O"] = torch.zeros(
            attention.out_proj.weight.numel() + attention.out_proj.bias.numel(),
            device=attention.out_proj.weight.device,
        )
    else:
        output["O"] = torch.cat((out_weight.float().reshape(-1), out_bias.float().reshape(-1)))
    return output


def qkvo_checkpoint_rows(
    model: V4AEncoderSkeleton,
    initial: dict[str, torch.Tensor],
    gradient_intervals: dict[str, list[dict[str, float]]],
    update_intervals: dict[str, list[float]],
    cumulative_update: dict[str, float],
    checkpoint: int,
) -> list[dict[str, Any]]:
    current = qkvo_vectors(model)
    rows = []
    for name in ("Q", "K", "V", "O"):
        movement = float(torch.linalg.vector_norm(current[name] - initial[name]))
        interval = gradient_intervals[name]
        rows.append({
            "optimizer_step": checkpoint,
            "projection": name,
            "parameter_count": int(current[name].numel()),
            "parameter_norm": float(torch.linalg.vector_norm(current[name])),
            "absolute_movement_from_initialization": movement,
            "relative_movement_from_initialization": movement
            / max(float(torch.linalg.vector_norm(initial[name])), EPS),
            "mean_gradient_norm_since_previous_checkpoint": (
                float(np.mean([row["norm"] for row in interval])) if interval else 0.0
            ),
            "mean_finite_gradient_element_fraction": (
                float(np.mean([row["finite_fraction"] for row in interval])) if interval else 0.0
            ),
            "mean_nonzero_gradient_element_fraction": (
                float(np.mean([row["nonzero_fraction"] for row in interval])) if interval else 0.0
            ),
            "mean_optimizer_update_norm_since_previous_checkpoint": (
                float(np.mean(update_intervals[name])) if update_intervals[name] else 0.0
            ),
            "cumulative_sum_optimizer_update_norm": cumulative_update[name],
        })
    lookup = {row["projection"]: row for row in rows}
    for row in rows:
        row["Q_relative_movement_over_V"] = (
            lookup["Q"]["relative_movement_from_initialization"]
            / max(lookup["V"]["relative_movement_from_initialization"], EPS)
        )
        row["K_relative_movement_over_V"] = (
            lookup["K"]["relative_movement_from_initialization"]
            / max(lookup["V"]["relative_movement_from_initialization"], EPS)
        )
        row["Q_update_norm_over_V"] = (
            lookup["Q"]["mean_optimizer_update_norm_since_previous_checkpoint"]
            / max(lookup["V"]["mean_optimizer_update_norm_since_previous_checkpoint"], EPS)
        )
        row["K_update_norm_over_V"] = (
            lookup["K"]["mean_optimizer_update_norm_since_previous_checkpoint"]
            / max(lookup["V"]["mean_optimizer_update_norm_since_previous_checkpoint"], EPS)
        )
    return rows


def geometry_of_vectors(values: torch.Tensor, device: torch.device) -> dict[str, Any]:
    geometry = base.geometry_2d(values.detach().float().cpu(), device)
    normalized = F.normalize(values.detach().float().cpu(), dim=-1)
    cosine = normalized @ normalized.T
    off_diagonal = ~torch.eye(len(values), dtype=torch.bool)
    geometry.update({
        "norms": quantiles(torch.linalg.vector_norm(values.detach().float().cpu(), dim=-1)),
        "pairwise_cosine": quantiles(cosine[off_diagonal]),
    })
    return geometry


def query_geometry(model: V4AEncoderSkeleton, device: torch.device) -> dict[str, Any]:
    attention = model.cross_attention.cross_attention
    width = attention.embed_dim
    queries = model.cross_attention.latents.detach()
    weight_q = attention.in_proj_weight[:width].detach()
    bias_q = attention.in_proj_bias[:width].detach()
    projected = F.linear(queries, weight_q, bias_q)
    return {
        "raw_learned_queries": geometry_of_vectors(queries, device),
        "W_Q_projected_queries": geometry_of_vectors(projected, device),
    }


def logits_and_keys(
    model: V4AEncoderSkeleton,
    expression: torch.Tensor,
    indices: torch.Tensor,
    device: torch.device,
) -> tuple[dict[str, Any], dict[str, Any]]:
    model.eval()
    attention = model.cross_attention.cross_attention
    width = attention.embed_dim
    heads = attention.num_heads
    head_width = width // heads
    all_logits: list[torch.Tensor] = []
    key_rank = []
    key_cosines = []
    all_keys: list[torch.Tensor] = []
    with torch.no_grad():
        for start in range(0, len(indices), 2):
            selected = indices[start:start + 2]
            values = expression[selected].to(device)
            ids = torch.arange(base.GENES, device=device).repeat(len(selected), 1)
            with torch.autocast("cuda", dtype=torch.float16):
                tokens = model.tokenizer(ids, values)
            queries = model.cross_attention.latents.unsqueeze(0).expand(len(selected), -1, -1)
            q = F.linear(queries.float(), attention.in_proj_weight[:width].float(),
                         attention.in_proj_bias[:width].float())
            k = F.linear(tokens.float(), attention.in_proj_weight[width:2 * width].float(),
                         attention.in_proj_bias[width:2 * width].float())
            q = q.reshape(len(selected), 24, heads, head_width).permute(0, 2, 1, 3)
            k_heads = k.reshape(len(selected), base.GENES, heads, head_width).permute(0, 2, 1, 3)
            logits = torch.matmul(q, k_heads.transpose(-1, -2)) / math.sqrt(head_width)
            all_logits.append(logits.float().cpu())
            all_keys.append(k.float().cpu())
            for cell_keys in k.float().cpu():
                key_rank.append(base.geometry_2d(cell_keys, device)["effective_rank"])
                sampled = F.normalize(cell_keys[::16], dim=-1)
                cosine = sampled @ sampled.T
                key_cosines.append(cosine[~torch.eye(len(sampled), dtype=torch.bool)])
    logits = torch.cat(all_logits)
    keys = torch.cat(all_keys)
    per_head = []
    for head in range(heads):
        values = logits[:, head]
        per_head.append({
            "head": head,
            "logits": quantiles(values),
            "variance_across_genes_given_cell_slot": quantiles(values.var(dim=-1, unbiased=False)),
            "variance_across_slots_given_cell_gene": quantiles(values.var(dim=1, unbiased=False)),
            "variance_across_cells_given_slot_gene": quantiles(values.var(dim=0, unbiased=False)),
        })
    return ({
        "cells": len(indices),
        "heads": heads,
        "slots": 24,
        "genes": base.GENES,
        "per_head": per_head,
        "all_heads_logits": quantiles(logits),
    }, {
        "across_gene_effective_rank_per_cell": quantiles(np.asarray(key_rank)),
        "sampled_across_gene_pairwise_cosine": quantiles(torch.cat(key_cosines)),
        "cross_cell_key_std_mean": float(keys.std(dim=0, unbiased=False).mean()),
        "identity_value_key_decomposition": (
            "not exact: identity and value contributions are fused and passed through "
            "tokenizer LayerNorm before the linear W_K projection"
        ),
    })


def kernel_factor_readout(
    train_kernel: torch.Tensor,
    eval_train_kernel: torch.Tensor,
    train_factors: torch.Tensor,
    eval_factors: torch.Tensor,
) -> dict[str, Any]:
    kernel = train_kernel.double()
    cross = eval_train_kernel.double()
    y_train = train_factors.double()
    y_eval = eval_factors.double()
    y_mean = y_train.mean(dim=0, keepdim=True)
    alpha = base.RIDGE_ALPHA
    weights = torch.linalg.solve(
        kernel + alpha * torch.eye(len(kernel), dtype=torch.double),
        y_train - y_mean,
    )
    prediction = cross @ weights + y_mean
    residual = (y_eval - prediction).square().sum(dim=0)
    total = (y_eval - y_eval.mean(dim=0, keepdim=True)).square().sum(dim=0).clamp_min(EPS)
    r2 = 1.0 - residual / total
    return {
        "mean_r2": float(r2.mean()),
        "median_r2": float(r2.median()),
        "per_factor_r2": [float(value) for value in r2],
        "r2_distribution": quantiles(r2),
        "ridge_alpha": alpha,
    }


def full_token_kernel_readout(
    model: V4AEncoderSkeleton,
    expression: torch.Tensor,
    factors: torch.Tensor,
    train_indices: torch.Tensor,
    eval_indices: torch.Tensor,
    device: torch.device,
) -> dict[str, Any]:
    model.eval()
    n_train = len(train_indices)
    train_kernel = torch.zeros(n_train, n_train, dtype=torch.float64)
    eval_train_kernel = torch.zeros(len(eval_indices), n_train, dtype=torch.float64)
    all_indices = torch.cat((train_indices, eval_indices))
    chunk_genes = 128
    with torch.no_grad():
        for gene_start in range(0, base.GENES, chunk_genes):
            gene_end = min(gene_start + chunk_genes, base.GENES)
            parts = []
            ids_one = torch.arange(gene_start, gene_end, device=device)
            for cell_start in range(0, len(all_indices), base.MICROBATCH):
                selected = all_indices[cell_start:cell_start + base.MICROBATCH]
                values = expression[selected, gene_start:gene_end].to(device)
                ids = ids_one.repeat(len(selected), 1)
                with torch.autocast("cuda", dtype=torch.float16):
                    tokens = model.tokenizer(ids, values).float().cpu()
                parts.append(tokens)
            features = torch.cat(parts).reshape(len(all_indices), -1)
            train = features[:n_train]
            evaluation = features[n_train:]
            mean = train.mean(dim=0, keepdim=True)
            train = train - mean
            evaluation = evaluation - mean
            train_kernel += (train @ train.T).double()
            eval_train_kernel += (evaluation @ train.T).double()
    return kernel_factor_readout(
        train_kernel,
        eval_train_kernel,
        factors[train_indices],
        factors[eval_indices],
    ) | {
        "kernel_definition": "sum over centered 4096x160 tokenizer features",
        "feature_centering": "training-cell mean per tokenizer feature",
        "chunk_genes": chunk_genes,
        "full_token_tensor_persisted": False,
    }


def stage_factor_readouts(
    model: V4AEncoderSkeleton,
    expression: torch.Tensor,
    factors: torch.Tensor,
    train_indices: torch.Tensor,
    eval_indices: torch.Tensor,
    device: torch.device,
) -> dict[str, Any]:
    model.eval()
    indices = torch.cat((train_indices, eval_indices))
    outputs = {"token_mean": [], "cross_attention_mean": [], "final_target_mean": []}
    with torch.no_grad():
        for start in range(0, len(indices), base.MICROBATCH):
            selected = indices[start:start + base.MICROBATCH]
            values = expression[selected].to(device)
            ids = torch.arange(base.GENES, device=device).repeat(len(selected), 1)
            valid = torch.ones(len(selected), base.GENES, dtype=torch.bool, device=device)
            with torch.autocast("cuda", dtype=torch.float16):
                tokens = model.tokenizer(ids, values)
                cross = model.cross_attention(tokens, valid)
                latents = cross
                for block in model.latent_blocks:
                    latents = block(latents)
                final = model.final_norm(latents)
            outputs["token_mean"].append(tokens.float().mean(dim=1).cpu())
            outputs["cross_attention_mean"].append(cross.float().mean(dim=1).cpu())
            outputs["final_target_mean"].append(final.float().mean(dim=1).cpu())
    result = {}
    split = len(train_indices)
    for name, parts in outputs.items():
        values = torch.cat(parts)
        result[name] = base.ridge_readout(
            values[:split], factors[train_indices], values[split:], factors[eval_indices]
        )
    return result


def raw_factor_readouts(
    expression: torch.Tensor,
    factors: torch.Tensor,
    train_indices: torch.Tensor,
    eval_indices: torch.Tensor,
    checkpoint: int,
) -> dict[str, Any]:
    indices = torch.cat((train_indices, eval_indices))
    context = mask_for_indices(indices, checkpoint)
    values = expression[indices].float()
    visible = values.masked_fill(context, 0.0)
    hidden = values.masked_fill(~context, 0.0)
    split = len(train_indices)
    output = {}
    for name, matrix in (("full_raw_expression", values), ("visible_60_percent_raw_expression", visible),
                         ("hidden_40_percent_raw_expression", hidden)):
        output[name] = base.ridge_readout(
            matrix[:split], factors[train_indices], matrix[split:], factors[eval_indices]
        )
    return output


def squared_distance_ratio(values: torch.Tensor) -> dict[str, float]:
    """Compare all within-cell mask pairs with same-mask between-cell pairs."""
    cells, masks = values.shape[:2]
    flat = values.reshape(cells, masks, -1).float()
    within = []
    for cell in range(cells):
        within.append(torch.pdist(flat[cell]).square())
    between = []
    for mask in range(masks):
        between.append(torch.pdist(flat[:, mask]).square())
    within_mean = float(torch.cat(within).mean())
    between_mean = float(torch.cat(between).mean())
    return {
        "mean_within_cell_squared_distance_across_mask_pairs": within_mean,
        "mean_between_cell_squared_distance_within_matching_mask": between_mean,
        "mask_sensitivity_ratio": within_mean / max(between_mean, EPS),
        "definition": "mean within-cell squared distance over all 28 mask pairs divided by mean between-cell squared distance within each matching mask",
    }


def token_mask_distance_ratio(
    model: V4AEncoderSkeleton,
    expression: torch.Tensor,
    indices: torch.Tensor,
    masks: torch.Tensor,
    device: torch.device,
) -> dict[str, float]:
    total = len(indices) * MASK_VIEWS
    distance = torch.zeros(total, total, dtype=torch.float64)
    chunk_genes = 128
    with torch.no_grad():
        for gene_start in range(0, base.GENES, chunk_genes):
            gene_end = min(gene_start + chunk_genes, base.GENES)
            ids_one = torch.arange(gene_start, gene_end, device=device)
            parts = []
            for cell in range(len(indices)):
                values = expression[indices[cell], gene_start:gene_end].to(device).repeat(MASK_VIEWS, 1)
                ids = ids_one.repeat(MASK_VIEWS, 1)
                with torch.autocast("cuda", dtype=torch.float16):
                    tokens = model.tokenizer(ids, values).float()
                visible = ~masks[cell, :, gene_start:gene_end].to(device)
                parts.append((tokens * visible.unsqueeze(-1)).reshape(MASK_VIEWS, -1).cpu())
            features = torch.cat(parts)
            norms = features.square().sum(dim=1, keepdim=True)
            distance += (norms + norms.T - 2.0 * features @ features.T).double().clamp_min(0)
    shaped = distance.reshape(len(indices), MASK_VIEWS, len(indices), MASK_VIEWS)
    within = [shaped[cell, :, cell, :][torch.triu(torch.ones(MASK_VIEWS, MASK_VIEWS, dtype=torch.bool), diagonal=1)]
              for cell in range(len(indices))]
    between = []
    cell_pairs = torch.triu(torch.ones(len(indices), len(indices), dtype=torch.bool), diagonal=1)
    for mask in range(MASK_VIEWS):
        between.append(shaped[:, mask, :, mask][cell_pairs])
    within_mean = float(torch.cat(within).mean())
    between_mean = float(torch.cat(between).mean())
    return {
        "mean_within_cell_squared_distance_across_mask_pairs": within_mean,
        "mean_between_cell_squared_distance_within_matching_mask": between_mean,
        "mask_sensitivity_ratio": within_mean / max(between_mean, EPS),
        "definition": "visible tokenizer tensors; same transparent squared-distance ratio as other stages",
        "full_token_tensor_persisted": False,
    }


def mask_sensitivity(
    online: V4AEncoderSkeleton,
    predictor: LatentPredictor,
    expression: torch.Tensor,
    indices: torch.Tensor,
    checkpoint: int,
    device: torch.device,
) -> dict[str, Any]:
    masks = torch.stack([
        mask_for_indices(indices, checkpoint, view) for view in range(MASK_VIEWS)
    ], dim=1)
    raw = expression[indices].float().unsqueeze(1).repeat(1, MASK_VIEWS, 1).masked_fill(masks, 0.0)
    online.eval()
    predictor.eval()
    slots = []
    predictions = []
    full_slots = []
    with torch.no_grad():
        for cell in range(len(indices)):
            values = expression[indices[cell]].to(device).repeat(MASK_VIEWS, 1)
            context = masks[cell].to(device)
            measured = torch.ones_like(context)
            ids = torch.arange(base.GENES, device=device).repeat(MASK_VIEWS, 1)
            with torch.autocast("cuda", dtype=torch.float16):
                context_slots = online(ids, values, measured, context, "student")
                predicted = predictor(context_slots)
                full = online(ids[:1], values[:1], measured[:1], torch.zeros_like(context[:1]), "student")
            slots.append(context_slots.float().cpu())
            predictions.append(predicted.float().cpu())
            full_slots.append(full.float().cpu())
    slot_tensor = torch.stack(slots)
    prediction_tensor = torch.stack(predictions)
    full = torch.cat(full_slots)
    pooled = slot_tensor.mean(dim=2)
    predicted_pooled = prediction_tensor.mean(dim=2)
    full_pooled = full.mean(dim=1)
    cosine = F.cosine_similarity(
        pooled,
        full_pooled.unsqueeze(1).expand_as(pooled),
        dim=-1,
    )
    l2 = torch.linalg.vector_norm(pooled - full_pooled.unsqueeze(1), dim=-1)
    centered_full = full_pooled - full_pooled.mean(dim=0, keepdim=True)
    centered_masked = pooled - pooled.mean(dim=0, keepdim=True)
    return {
        "cells": len(indices),
        "masks_per_cell": MASK_VIEWS,
        "raw_visible_expression": squared_distance_ratio(raw),
        "visible_tokenizer_tensor": token_mask_distance_ratio(
            online, expression, indices, masks, device
        ),
        "online_context_slots": squared_distance_ratio(slot_tensor),
        "pooled_online_context": squared_distance_ratio(pooled),
        "predictor_output": squared_distance_ratio(prediction_tensor),
        "full_vs_masked_pooled_online": {
            "cosine_similarity": quantiles(cosine),
            "l2_distance": quantiles(l2),
            "centered_residual_mse": float(
                (centered_masked - centered_full.unsqueeze(1)).square().mean()
            ),
        },
    }


def forensic_checkpoint(
    online: V4AEncoderSkeleton,
    target: torch.nn.Module,
    predictor: LatentPredictor,
    expression: torch.Tensor,
    factors: torch.Tensor,
    checkpoint: int,
    device: torch.device,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    train_indices, eval_indices = evaluation_indices(len(expression))
    prediction, target_latents = prediction_target_tensors(
        online, target, predictor, expression, eval_indices, checkpoint, device
    )
    loss_rows, loss_summary = loss_decomposition_rows(prediction, target_latents, checkpoint)
    result: dict[str, Any] = {"loss_decomposition": loss_summary}
    target_model = ema_target_module(target)
    forensic_indices = eval_indices[:FORENSIC_CELLS]
    if checkpoint in LOGIT_CHECKPOINTS:
        logits, keys = logits_and_keys(target_model, expression, forensic_indices, device)
        result["pre_softmax_logits"] = logits
        result["key_geometry"] = keys
        result["query_geometry"] = query_geometry(target_model, device)
    if checkpoint in DEEP_CHECKPOINTS:
        result["full_token_factor_readout"] = full_token_kernel_readout(
            target_model, expression, factors, train_indices, eval_indices, device
        )
        result["stage_factor_readouts"] = stage_factor_readouts(
            target_model, expression, factors, train_indices, eval_indices, device
        )
        result["raw_factor_readouts"] = raw_factor_readouts(
            expression, factors, train_indices, eval_indices, checkpoint
        )
        result["multi_mask_sensitivity"] = mask_sensitivity(
            online, predictor, expression, forensic_indices, checkpoint, device
        )
    online.train()
    predictor.train()
    return loss_rows, result


def main() -> int:
    args = parse_args()
    project = args.project_dir.resolve()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required")
    device = torch.device("cuda")
    prior, prior_by_step = prior_run(project)
    if args.finalize_existing:
        return finalize_existing(project, prior_by_step)
    expression, factors, fixture_metadata = base.synthetic_fixture(FIXTURE, smoke=False)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    online = V4AEncoderSkeleton().to(device)
    predictor = LatentPredictor().to(device)
    target = create_ema_target(online).to(device)
    optimizer = torch.optim.AdamW(
        list(online.parameters()) + list(predictor.parameters()),
        lr=base.LEARNING_RATE,
        weight_decay=base.WEIGHT_DECAY,
    )
    scaler = torch.amp.GradScaler("cuda")
    controller = EMAOptimizerStepController(online, target)
    rng = torch.Generator(device="cpu").manual_seed(SEED + 900_000)
    qkvo_initial = {name: value.clone() for name, value in qkvo_vectors(online).items()}
    gradient_intervals = {name: [] for name in ("Q", "K", "V", "O")}
    update_intervals = {name: [] for name in ("Q", "K", "V", "O")}
    cumulative_update = {name: 0.0 for name in ("Q", "K", "V", "O")}
    metric_interval = {"loss": [], "gradient_norm": [], "ema_update_norm": []}
    trajectory = []
    loss_rows: list[dict[str, Any]] = []
    qkvo_rows: list[dict[str, Any]] = []
    forensic: dict[str, Any] = {}
    nonfinite = 0

    def record_checkpoint(step: int) -> None:
        row, _, _ = base.checkpoint_metrics(
            online, target, predictor, expression, factors,
            fixture=FIXTURE, seed=SEED, step=step, interval=metric_interval,
            nonfinite_events=nonfinite, device=device, smoke=False,
        )
        trajectory.append(row)
        rows, details = forensic_checkpoint(
            online, target, predictor, expression, factors, step, device
        )
        loss_rows.extend(rows)
        forensic[str(step)] = details
        qkvo_rows.extend(qkvo_checkpoint_rows(
            online, qkvo_initial, gradient_intervals, update_intervals,
            cumulative_update, step
        ))
        print(
            f"step={step} loss={row['jepa_diagnostic_loss']:.6f} "
            f"rank={row['effective_rank']:.4f} "
            f"residual_explained={details['loss_decomposition']['full_slots']['residual_explained_fraction']:.4f}",
            flush=True,
        )

    record_checkpoint(0)
    online.train()
    predictor.train()
    for update in range(1, 501):
        optimizer.zero_grad(set_to_none=True)
        selected = torch.randint(0, base.TRAIN_CELLS, (base.EFFECTIVE_BATCH,), generator=rng)
        update_loss = 0.0
        for microbatch in range(base.ACCUMULATION_STEPS):
            indices = selected[microbatch * base.MICROBATCH:(microbatch + 1) * base.MICROBATCH]
            values = expression[indices].to(device)
            measurement_cpu = torch.ones(base.MICROBATCH, base.GENES, dtype=torch.bool)
            context_cpu = construct_context_mask(
                measurement_cpu,
                mask_fraction=base.MASK_FRACTION,
                production_seed=SEED,
                cell_indices=indices,
                sample_pass=update,
                view_index=0,
                rule="exact_count",
            )
            context = context_cpu.to(device)
            measured = measurement_cpu.to(device)
            ids = torch.arange(base.GENES, device=device).repeat(base.MICROBATCH, 1)
            with torch.autocast("cuda", dtype=torch.float16):
                context_latents = online(ids, values, measured, context, "student")
                prediction = predictor(context_latents)
                with torch.no_grad():
                    target_latents = target(ids, values, measured, context, "target")
                loss = jepa_prediction_loss(prediction, target_latents)
            if not torch.isfinite(loss):
                nonfinite += 1
                raise RuntimeError(f"nonfinite loss at update {update}")
            scaler.scale(loss / base.ACCUMULATION_STEPS).backward()
            update_loss += float(loss.detach()) / base.ACCUMULATION_STEPS
        scaler.unscale_(optimizer)
        gradients = qkvo_vectors(online, gradients=True)
        for name, values in gradients.items():
            finite = torch.isfinite(values)
            gradient_intervals[name].append({
                "norm": float(torch.linalg.vector_norm(torch.where(finite, values, torch.zeros_like(values)))),
                "finite_fraction": float(finite.float().mean()),
                "nonzero_fraction": float((finite & values.ne(0)).float().mean()),
            })
        total_gradient = base.parameter_gradient_norm(
            list(online.parameters()) + list(predictor.parameters())
        )
        before = {name: values.clone() for name, values in qkvo_vectors(online).items()}
        scale_before = scaler.get_scale()
        scaler.step(optimizer)
        scaler.update()
        if scaler.get_scale() < scale_before:
            nonfinite += 1
            raise RuntimeError(f"GradScaler skipped update {update}")
        after = qkvo_vectors(online)
        for name in after:
            movement = float(torch.linalg.vector_norm(after[name] - before[name]))
            update_intervals[name].append(movement)
            cumulative_update[name] += movement
        gap = ema_parameter_health(online, target).online_target_parameter_l2_distance
        controller.after_successful_optimizer_step(momentum=EMA)
        metric_interval["loss"].append(update_loss)
        metric_interval["gradient_norm"].append(total_gradient)
        metric_interval["ema_update_norm"].append((1.0 - EMA) * gap)
        if update in CHECKPOINTS:
            record_checkpoint(update)
            metric_interval = {"loss": [], "gradient_norm": [], "ema_update_norm": []}
            gradient_intervals = {name: [] for name in gradient_intervals}
            update_intervals = {name: [] for name in update_intervals}

    if controller.global_update_step != 500 or controller.ema_update_count != 500:
        raise RuntimeError("optimizer/EMA replay count mismatch")
    replay_agreement = evaluate_replay_agreement(trajectory, prior_by_step)
    maximum_replay_difference = replay_agreement["maximum_absolute_difference"]
    replay_pass = replay_agreement["pass"]
    if not replay_pass:
        classification = "REPLAY MISMATCH"
        recommendation = "STOP SCIENTIFIC INTERPRETATION"
        mechanism_evidence = None
    else:
        classification, recommendation, mechanism_evidence = classify_forensics(
            forensic, trajectory
        )
    payload = {
        "stage": "stage81a3_single_trajectory_forensic_replay",
        "status": "complete" if replay_pass else "replay_mismatch",
        "contract": {
            "fixture": FIXTURE,
            "seed": SEED,
            "cells": len(expression),
            "genes": base.GENES,
            "latent_factors": base.FACTORS,
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
            "training_loss": "raw JEPA MSE unchanged",
            "optimizer_updates": controller.global_update_step,
            "ema_updates": controller.ema_update_count,
            "architecture_changed": False,
            "training_objective_changed": False,
        },
        "fixture_metadata": fixture_metadata,
        "replay_agreement": replay_agreement,
        "trajectory": trajectory,
        "forensic_checkpoints": forensic,
        "loss_decomposition_rows": loss_rows,
        "qkvo_rows": qkvo_rows,
        "classification": classification,
        "recommendation": recommendation,
        "nonfinite_events": nonfinite,
        "claim_boundaries": {
            "stage81a3_complete": False,
            "ready_for_stage81b": False,
            "real_rna_optimizer_steps": 0,
            "real_rna_ema_updates": 0,
            "real_rna_model_training": False,
            "synthetic_forensic_optimizer_steps": controller.global_update_step,
            "synthetic_forensic_ema_updates": controller.ema_update_count,
            "pathology_opened": False,
            "stage81b_started": False,
            "stage81c_started": False,
            "production_seed_selected": False,
            "architecture_changed": False,
            "training_objective_changed": False,
        },
    }
    if mechanism_evidence is not None:
        payload["mechanism_evidence"] = mechanism_evidence
    token_rows = []
    mask_rows = []
    for checkpoint, details in forensic.items():
        if "full_token_factor_readout" in details:
            token_rows.append({
                "optimizer_step": int(checkpoint),
                "representation": "full_token_linear_kernel",
                **{key: value for key, value in details["full_token_factor_readout"].items()
                   if not isinstance(value, (dict, list))},
            })
            for name, result in details["stage_factor_readouts"].items():
                token_rows.append({"optimizer_step": int(checkpoint), "representation": name,
                                   **{key: value for key, value in result.items() if not isinstance(value, (dict, list))}})
            for name, result in details["raw_factor_readouts"].items():
                token_rows.append({"optimizer_step": int(checkpoint), "representation": name,
                                   **{key: value for key, value in result.items() if not isinstance(value, (dict, list))}})
            for stage, result in details["multi_mask_sensitivity"].items():
                if isinstance(result, dict) and "mask_sensitivity_ratio" in result:
                    mask_rows.append({"optimizer_step": int(checkpoint), "stage": stage, **result})
    atomic_text(project / OUTPUT_JSON, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_csv(project / OUTPUT_LOSS, loss_rows)
    write_csv(project / OUTPUT_QKVO, qkvo_rows)
    write_csv(project / OUTPUT_TOKEN, token_rows)
    write_csv(project / OUTPUT_MASK, mask_rows)
    print(f"replay_pass={replay_pass} max_abs_diff={maximum_replay_difference:.3e}")
    print(f"classification={classification}")
    print(f"recommendation={recommendation}")
    return 0 if replay_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
