#!/usr/bin/env python3
"""Run the single bounded Stage81A3 v4.1 IPB-JEPA feasibility study."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.v4 import stage81a3_forensic_failed_trajectory_replay as forensic  # noqa: E402
from scripts.v4 import stage81a3_real_rna_forward_smoke as real_smoke  # noqa: E402
from scripts.v4 import stage81a3_synthetic_geometry_escape as base  # noqa: E402
from sea_ad_jepa.v4 import (  # noqa: E402
    EMAOptimizerStepController,
    FrozenPCA,
    create_ema_target,
    ema_target_module,
)
from sea_ad_jepa.v4.ipb_jepa import (  # noqa: E402
    BlockPredictor,
    CorrelationGraph,
    GeneAnchorDecoder,
    IPBEncoder,
    TargetBlocks,
    block_jepa_loss,
    build_train_pearson_graph,
    gather_block_states,
    gene_anchor_loss,
    hidden_gene_indices,
    sample_target_blocks,
)


EVIDENCE_COMMIT = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
FIXTURES = ("balanced_multifactor", "dominant_axis_multifactor")
SEEDS = base.TEST_SEEDS[:2]
CONDITIONS = ("ipb_jepa", "anchor_only")
CHECKPOINTS = base.CHECKPOINTS
EMA = 0.996
STEPS = 500
MICROBATCH = 8
EFFECTIVE_BATCH = 256
ACCUMULATION = 32
BLOCKS = 16
GRAPH_K = 8
MASK_FRACTION = 0.40
OUTPUT_JSON = Path("results/v4/stage81a3_ipb_jepa_feasibility.json")
OUTPUT_RUNS = Path("results/v4/stage81a3_ipb_jepa_runs.csv")
OUTPUT_FACTORS = Path("results/v4/stage81a3_ipb_jepa_factors.csv")
OUTPUT_GENES = Path("results/v4/stage81a3_ipb_jepa_genes.csv")
OUTPUT_GEOMETRY = Path("results/v4/stage81a3_ipb_jepa_geometry.csv")
OUTPUT_REAL = Path("results/v4/stage81a3_ipb_jepa_real_forward_smoke.json")


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


def atomic_json(path: Path, payload: Any) -> None:
    atomic_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = sorted({key for row in rows for key in row})
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader(); writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def config_payload() -> dict[str, Any]:
    return {
        "stage": "stage81a3_ipb_jepa_feasibility",
        "evidence_commit": EVIDENCE_COMMIT,
        "fixtures": list(FIXTURES), "seeds": list(SEEDS),
        "conditions": list(CONDITIONS), "trajectories": 8,
        "architecture": {
            "genes": 4096, "width": 160, "heads": 4, "head_width": 40,
            "blocks": 6, "ffn_width": 320, "dropout": 0.10,
            "linear_attention": "ELU(x)+1 kernel, O(N*d_head^2)",
            "cell_tokens": 1, "perceiver_slots": 0,
        },
        "target_blocks": {"graph": "train-only absolute Pearson top-8 union", "count": 16,
                          "hidden_fraction": 0.40, "graph_is_model_input": False},
        "training": {"updates": 500, "ema": EMA, "optimizer": "AdamW",
                     "learning_rate": 1e-4, "weight_decay": 0.01,
                     "microbatch": MICROBATCH, "effective_batch": EFFECTIVE_BATCH,
                     "accumulation": ACCUMULATION, "precision": "CUDA fp16",
                     "variance_weight": 0.0, "covariance_weight": 0.0},
        "claim_boundaries": {"real_rna_training": False, "pathology_opened": False,
                             "stage81b_started": False, "stage81c_started": False,
                             "hyperparameter_sweep": False},
    }


def config_hash() -> str:
    return hashlib.sha256(json.dumps(config_payload(), sort_keys=True).encode()).hexdigest()


def graph_hash(graph: CorrelationGraph) -> str:
    digest = hashlib.sha256()
    for gene, (neighbors, weights) in enumerate(zip(graph.neighbors, graph.weights)):
        digest.update(gene.to_bytes(4, "little"))
        digest.update(neighbors.numpy().tobytes())
        digest.update(weights.numpy().tobytes())
    return digest.hexdigest()


def blocks_to(blocks: TargetBlocks, device: torch.device) -> TargetBlocks:
    return TargetBlocks(*(value.to(device) for value in (
        blocks.hidden_mask, blocks.indices, blocks.member_mask, blocks.fallback_counts
    )))


def model_components(seed: int, device: torch.device):
    torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False
    online = IPBEncoder().to(device)
    target = create_ema_target(online).to(device)
    predictor = BlockPredictor().to(device)
    decoder = GeneAnchorDecoder().to(device)
    return online, target, predictor, decoder


def enrich_readout(result: dict[str, Any]) -> dict[str, Any]:
    values = np.asarray(result["per_factor_r2"], dtype=float)
    result = dict(result)
    result.update({"p10_r2": float(np.quantile(values, .1)),
                   "p90_r2": float(np.quantile(values, .9)),
                   "minimum_r2": float(values.min()), "maximum_r2": float(values.max())})
    return result


def ridge_readout(values: torch.Tensor, factors: torch.Tensor) -> dict[str, Any]:
    split = base.READOUT_TRAIN_CELLS
    evaluation = len(factors) - base.READOUT_EVAL_CELLS
    return enrich_readout(base.ridge_readout(
        values[:split], factors[:split], values[split:], factors[evaluation:]
    ))


def feature_kernel_readout(
    features: torch.Tensor,
    factors: torch.Tensor,
    device: torch.device,
    *,
    chunk_features: int = 8192,
) -> dict[str, Any]:
    split = base.READOUT_TRAIN_CELLS
    train_kernel = torch.zeros(split, split, dtype=torch.float64)
    cross_kernel = torch.zeros(base.READOUT_EVAL_CELLS, split, dtype=torch.float64)
    flattened = features.reshape(len(features), -1)
    for start in range(0, flattened.shape[1], chunk_features):
        values = flattened[:, start:start + chunk_features].float()
        train = values[:split]
        evaluation = values[split:]
        mean = train.mean(0, keepdim=True)
        train = train - mean; evaluation = evaluation - mean
        train_kernel.add_((train @ train.T).double())
        cross_kernel.add_((evaluation @ train.T).double())
    evaluation = len(factors) - base.READOUT_EVAL_CELLS
    result = forensic.kernel_factor_readout(
        train_kernel, cross_kernel, factors[:split], factors[evaluation:]
    )
    return enrich_readout(result)


def geometry(values: torch.Tensor, device: torch.device) -> dict[str, Any]:
    return base.geometry_2d(values.float(), device)


def training_statistics(expression: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    train = expression[:base.TRAIN_CELLS].float()
    mean = train.mean(0)
    std = train.std(0, unbiased=False).clamp_min(1e-6)
    variance = train.var(0, unbiased=False)
    detection = (train > 0).float().mean(0)
    return mean, std, variance, detection


def graph_for_fixture(expression: torch.Tensor, device: torch.device) -> CorrelationGraph:
    print("building train-only absolute-Pearson top-8 graph", flush=True)
    graph = build_train_pearson_graph(expression[:base.TRAIN_CELLS].to(device), top_k=GRAPH_K)
    print(f"graph PASS hash={graph_hash(graph)}", flush=True)
    return graph


def evaluation_indices() -> torch.Tensor:
    return torch.cat((
        torch.arange(base.READOUT_TRAIN_CELLS),
        torch.arange(base.CELLS - base.READOUT_EVAL_CELLS, base.CELLS),
    ))


def raw_references(
    expression: torch.Tensor,
    factors: torch.Tensor,
    graph: CorrelationGraph,
    seed: int,
    device: torch.device,
) -> dict[str, Any]:
    indices = evaluation_indices()
    values = expression[indices].float()
    measured = torch.ones_like(values, dtype=torch.bool)
    blocks = sample_target_blocks(
        measured, graph, production_seed=seed, cell_indices=indices,
        sample_pass=500, view_index=0, mask_fraction=MASK_FRACTION,
        block_count=BLOCKS,
    )
    visible = values.masked_fill(blocks.hidden_mask, 0.0)
    hidden = values.masked_fill(~blocks.hidden_mask, 0.0)
    pca = FrozenPCA.fit(values[:base.READOUT_TRAIN_CELLS].to(device), n_components=160)
    return {
        "raw_full_expression": ridge_readout(values, factors),
        "raw_pca160": ridge_readout(pca.transform(values), factors),
        "visible_60_percent_raw": ridge_readout(visible, factors),
        "hidden_40_percent_raw": ridge_readout(hidden, factors),
        "mask_fallback_count": int(blocks.fallback_counts.sum()),
        "factor_labels_used_for_reference_fit": False,
    }


def forward_views(
    online: IPBEncoder,
    target: torch.nn.Module,
    expression: torch.Tensor,
    graph: CorrelationGraph,
    seed: int,
    step: int,
    device: torch.device,
    *,
    retain_tokens: bool,
    view_index: int = 0,
) -> dict[str, torch.Tensor]:
    indices = evaluation_indices()
    measured_cpu = torch.ones(len(indices), base.GENES, dtype=torch.bool)
    blocks_cpu = sample_target_blocks(
        measured_cpu, graph, production_seed=seed, cell_indices=indices,
        sample_pass=step, view_index=view_index, mask_fraction=MASK_FRACTION,
        block_count=BLOCKS,
    )
    parts: dict[str, list[torch.Tensor]] = {
        "target_cell": [], "online_full_cell": [], "online_masked_cell": [],
    }
    if retain_tokens:
        parts.update({"tokenizer": [], "target_genes": []})
    online.eval(); target.eval()
    with torch.no_grad():
        for start in range(0, len(indices), MICROBATCH):
            selected = indices[start:start + MICROBATCH]
            count = len(selected)
            values = expression[selected].to(device)
            ids = torch.arange(base.GENES, device=device).repeat(count, 1)
            measured = torch.ones_like(ids, dtype=torch.bool)
            hidden = blocks_cpu.hidden_mask[start:start + count].to(device)
            zero = torch.zeros_like(hidden)
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                teacher = target(ids, values, measured, zero, "target")
                full = online(ids, values, measured, zero, "target")
                masked = online(ids, values, measured, hidden, "student")
                if retain_tokens:
                    tokens = ema_target_module(target).tokenizer(ids, values)
            parts["target_cell"].append(teacher.cell_state.float().cpu())
            parts["online_full_cell"].append(full.cell_state.float().cpu())
            parts["online_masked_cell"].append(masked.cell_state.float().cpu())
            if retain_tokens:
                parts["tokenizer"].append(tokens.half().cpu())
                parts["target_genes"].append(teacher.gene_states.half().cpu())
    online.train()
    return {name: torch.cat(values) for name, values in parts.items()}


def checkpoint_audit(
    online: IPBEncoder,
    target: torch.nn.Module,
    expression: torch.Tensor,
    factors: torch.Tensor,
    graph: CorrelationGraph,
    seed: int,
    step: int,
    device: torch.device,
) -> dict[str, Any]:
    retain_tokens = step in (0, STEPS)
    views = forward_views(
        online, target, expression, graph, seed, step, device,
        retain_tokens=retain_tokens,
    )
    result: dict[str, Any] = {
        "optimizer_step": step,
        "readouts": {
            name: ridge_readout(value, factors)
            for name, value in views.items() if name.endswith("_cell")
        },
        "geometry": {
            name: geometry(value[base.READOUT_TRAIN_CELLS:], device)
            for name, value in views.items() if name.endswith("_cell")
        },
    }
    if retain_tokens:
        result["readouts"]["original_tokenizer_tensor"] = feature_kernel_readout(
            views["tokenizer"], factors, device
        )
        result["readouts"]["contextual_teacher_gene_tensor"] = feature_kernel_readout(
            views["target_genes"], factors, device
        )
        del views["tokenizer"], views["target_genes"]
    return result


def gradient_norm(parameters) -> float:
    total = 0.0
    for parameter in parameters:
        if parameter.grad is not None:
            total += float(parameter.grad.detach().float().square().sum())
    return math.sqrt(total)


def train_run(
    fixture: str,
    seed: int,
    condition: str,
    expression: torch.Tensor,
    factors: torch.Tensor,
    graph: CorrelationGraph,
    device: torch.device,
) -> tuple[
    dict[str, Any], list[dict[str, Any]],
    tuple[IPBEncoder, torch.nn.Module, BlockPredictor, GeneAnchorDecoder] | None,
]:
    online, target, predictor, decoder = model_components(seed, device)
    parameters = list(online.parameters()) + list(decoder.parameters())
    if condition == "ipb_jepa":
        parameters += list(predictor.parameters())
    optimizer = torch.optim.AdamW(parameters, lr=1e-4, weight_decay=0.01)
    scaler = torch.amp.GradScaler("cuda")
    controller = EMAOptimizerStepController(online, target)
    selection_generator = torch.Generator().manual_seed(seed + 901_000)
    mean, std, gene_variance, detection_frequency = training_statistics(expression)
    mean = mean.to(device); std = std.to(device)
    gene_ids = torch.arange(base.GENES, device=device).repeat(MICROBATCH, 1)
    checkpoints = [checkpoint_audit(
        online, target, expression, factors, graph, seed, 0, device
    )]
    telemetry = {"gene_loss": [], "block_loss": [], "minimum_denominator": [],
                 "online_gradient_norm": [], "predictor_gradient_norm": []}
    nonfinite_loss = nonfinite_gradients = scaler_skips = oom_events = 0
    target_gradient_events = 0
    fallback_count = 0
    started = time.perf_counter()
    torch.cuda.reset_peak_memory_stats(device)
    for update in range(1, STEPS + 1):
        optimizer.zero_grad(set_to_none=True)
        selected = torch.randint(0, base.TRAIN_CELLS, (EFFECTIVE_BATCH,), generator=selection_generator)
        measured_cpu = torch.ones(EFFECTIVE_BATCH, base.GENES, dtype=torch.bool)
        blocks_cpu = sample_target_blocks(
            measured_cpu, graph, production_seed=seed, cell_indices=selected,
            sample_pass=update, view_index=0, mask_fraction=MASK_FRACTION,
            block_count=BLOCKS,
        )
        fallback_count += int(blocks_cpu.fallback_counts.sum())
        update_gene = update_block = update_denominator = 0.0
        for micro in range(ACCUMULATION):
            start = micro * MICROBATCH
            batch_indices = selected[start:start + MICROBATCH]
            values = expression[batch_indices].to(device)
            measured = torch.ones(MICROBATCH, base.GENES, dtype=torch.bool, device=device)
            blocks = blocks_to(TargetBlocks(*(
                value[start:start + MICROBATCH] for value in (
                    blocks_cpu.hidden_mask, blocks_cpu.indices,
                    blocks_cpu.member_mask, blocks_cpu.fallback_counts,
                )
            )), device)
            hidden_ids = hidden_gene_indices(blocks.hidden_mask)
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                student = online(gene_ids, values, measured, blocks.hidden_mask, "student")
                predicted_value, predicted_detection = decoder(
                    student.cell_state, online.tokenizer.gene_identity, hidden_ids
                )
                batch = torch.arange(MICROBATCH, device=device)[:, None]
                standardized = (values[batch, hidden_ids] - mean[hidden_ids]) / std[hidden_ids]
                detected = values[batch, hidden_ids] > 0
                anchor = gene_anchor_loss(
                    predicted_value, predicted_detection, standardized, detected
                )
                block_loss = torch.zeros((), device=device)
                if condition == "ipb_jepa":
                    with torch.no_grad():
                        teacher = target(
                            gene_ids, values, measured, torch.zeros_like(measured), "target"
                        )
                        teacher_blocks = gather_block_states(teacher.gene_states, blocks)
                    prediction = predictor(
                        online.tokenizer.gene_identity, blocks,
                        student.gene_states, student.cell_state,
                        measured & ~blocks.hidden_mask,
                    )
                    block_loss = block_jepa_loss(prediction, teacher_blocks)
                loss = anchor["gene"] + block_loss
            if not torch.isfinite(loss):
                nonfinite_loss += 1
                raise RuntimeError(f"nonfinite loss {fixture} {seed} {condition} step={update}")
            scaler.scale(loss / ACCUMULATION).backward()
            update_gene += float(anchor["gene"].detach()) / ACCUMULATION
            update_block += float(block_loss.detach()) / ACCUMULATION
            update_denominator = min(
                update_denominator or float(student.minimum_denominator),
                float(student.minimum_denominator),
            )
        scaler.unscale_(optimizer)
        gradients = [parameter.grad for parameter in parameters if parameter.grad is not None]
        if not gradients or any(not torch.isfinite(item).all() for item in gradients):
            nonfinite_gradients += 1
            raise RuntimeError(f"nonfinite gradient {fixture} {seed} {condition} step={update}")
        if any(parameter.grad is not None for parameter in target.parameters()):
            target_gradient_events += 1
            raise RuntimeError("EMA target received gradients")
        telemetry["online_gradient_norm"].append(gradient_norm(online.parameters()))
        telemetry["predictor_gradient_norm"].append(gradient_norm(predictor.parameters()))
        before_scale = scaler.get_scale()
        scaler.step(optimizer); scaler.update()
        if scaler.get_scale() < before_scale:
            scaler_skips += 1
            continue
        controller.after_successful_optimizer_step(momentum=EMA)
        telemetry["gene_loss"].append(update_gene)
        telemetry["block_loss"].append(update_block)
        telemetry["minimum_denominator"].append(update_denominator)
        if update in CHECKPOINTS[1:]:
            audit = checkpoint_audit(
                online, target, expression, factors, graph, seed, update, device
            )
            checkpoints.append(audit)
            print(
                f"{fixture} seed={seed} {condition} step={update} "
                f"gene={update_gene:.5f} block={update_block:.5f} "
                f"masked_R2={audit['readouts']['online_masked_cell']['mean_r2']:.4f}",
                flush=True,
            )
    elapsed = time.perf_counter() - started
    final = checkpoints[-1]
    references = raw_references(expression, factors, graph, seed, device)
    tokenizer_r2 = final["readouts"]["original_tokenizer_tensor"]["mean_r2"]
    contextual_r2 = final["readouts"]["contextual_teacher_gene_tensor"]["mean_r2"]
    full_r2 = final["readouts"]["target_cell"]["mean_r2"]
    masked_r2 = final["readouts"]["online_masked_cell"]["mean_r2"]
    run = {
        "fixture": fixture, "seed": seed, "condition": condition,
        "graph_hash": graph_hash(graph), "config_hash": config_hash(),
        "checkpoints": checkpoints, "references": references,
        "final_metrics": {
            "token_encoder_retention": contextual_r2 / tokenizer_r2,
            "cell_retention": full_r2 / references["raw_pca160"]["mean_r2"],
            "masked_to_full": masked_r2 / full_r2,
            "masked_minus_visible_raw": masked_r2 - references["visible_60_percent_raw"]["mean_r2"],
        },
        "training": {
            "optimizer_updates": controller.global_update_step,
            "ema_updates": controller.ema_update_count,
            "nonfinite_loss_events": nonfinite_loss,
            "nonfinite_gradient_events": nonfinite_gradients,
            "target_gradient_events": target_gradient_events,
            "gradscaler_skips": scaler_skips, "cuda_oom_events": oom_events,
            "target_block_fallback_count": fallback_count,
            "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
            "elapsed_seconds": elapsed, "updates_per_second": STEPS / elapsed,
            "telemetry": telemetry,
        },
        "gene_training_statistics": {
            "variance": gene_variance.tolist(),
            "detection_frequency": detection_frequency.tolist(),
        },
    }
    gene_rows, molecular = evaluate_final_molecular_information(
        run, online, target, predictor, decoder, expression, factors, graph, device
    )
    run["final_molecular_audit"] = molecular
    retained = (
        (online, target, predictor, decoder)
        if fixture == FIXTURES[0] and seed == SEEDS[0] else None
    )
    return run, gene_rows, retained


def quantiles(values: np.ndarray) -> dict[str, float]:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if not len(finite):
        return {key: float("nan") for key in ("minimum", "p10", "p25", "median", "p75", "p90", "maximum")}
    return {
        "minimum": float(finite.min()), "p10": float(np.quantile(finite, .10)),
        "p25": float(np.quantile(finite, .25)), "median": float(np.median(finite)),
        "p75": float(np.quantile(finite, .75)), "p90": float(np.quantile(finite, .90)),
        "maximum": float(finite.max()),
    }


def evaluate_final_molecular_information(
    run: dict[str, Any],
    online: IPBEncoder,
    target: torch.nn.Module,
    predictor: BlockPredictor,
    decoder: GeneAnchorDecoder,
    expression: torch.Tensor,
    factors: torch.Tensor,
    graph: CorrelationGraph,
    device: torch.device,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    seed = int(run["seed"])
    condition = str(run["condition"])
    eval_indices = torch.arange(base.CELLS - base.READOUT_EVAL_CELLS, base.CELLS)
    measured_cpu = torch.ones(len(eval_indices), base.GENES, dtype=torch.bool)
    mean, std, variance, detection_frequency = training_statistics(expression)
    predictions = np.full((8, len(eval_indices), base.GENES), np.nan, dtype=np.float32)
    detection_logits = np.full_like(predictions, np.nan)
    mask_embeddings: list[torch.Tensor] = []
    mask_readouts: list[dict[str, Any]] = []
    block_rows = []
    online.eval(); target.eval(); predictor.eval(); decoder.eval()
    for view in range(8):
        blocks_cpu = sample_target_blocks(
            measured_cpu, graph, production_seed=seed, cell_indices=eval_indices,
            sample_pass=STEPS, view_index=view, mask_fraction=MASK_FRACTION,
            block_count=BLOCKS,
        )
        cells = []
        predicted_blocks_all = []
        teacher_blocks_all = []
        with torch.no_grad():
            for start in range(0, len(eval_indices), MICROBATCH):
                selected = eval_indices[start:start + MICROBATCH]
                count = len(selected)
                values = expression[selected].to(device)
                ids = torch.arange(base.GENES, device=device).repeat(count, 1)
                measured = torch.ones_like(ids, dtype=torch.bool)
                blocks = blocks_to(TargetBlocks(*(
                    value[start:start + count] for value in (
                        blocks_cpu.hidden_mask, blocks_cpu.indices,
                        blocks_cpu.member_mask, blocks_cpu.fallback_counts,
                    )
                )), device)
                hidden_ids = hidden_gene_indices(blocks.hidden_mask)
                with torch.autocast(device_type="cuda", dtype=torch.float16):
                    student = online(ids, values, measured, blocks.hidden_mask, "student")
                    value_hat, detection_hat = decoder(
                        student.cell_state, online.tokenizer.gene_identity, hidden_ids
                    )
                    if condition == "ipb_jepa":
                        teacher = target(ids, values, measured, torch.zeros_like(measured), "target")
                        teacher_blocks = gather_block_states(teacher.gene_states, blocks)
                        predicted_blocks = predictor(
                            online.tokenizer.gene_identity, blocks,
                            student.gene_states, student.cell_state,
                            measured & ~blocks.hidden_mask,
                        )
                cells.append(student.cell_state.float().cpu())
                rows = np.arange(start, start + count)[:, None]
                columns = hidden_ids.cpu().numpy()
                predictions[view, rows, columns] = value_hat.float().cpu().numpy()
                detection_logits[view, rows, columns] = detection_hat.float().cpu().numpy()
                if condition == "ipb_jepa":
                    predicted_blocks_all.append(predicted_blocks.float().cpu())
                    teacher_blocks_all.append(teacher_blocks.float().cpu())
        cell_values = torch.cat(cells)
        full_partition_views = forward_views(
            online, target, expression, graph, seed, STEPS, device,
            retain_tokens=False, view_index=view,
        )
        full_partition_masked = full_partition_views["online_masked_cell"]
        mask_embeddings.append(full_partition_masked[base.READOUT_TRAIN_CELLS:])
        mask_readouts.append(ridge_readout(full_partition_masked, factors))
        if condition == "ipb_jepa":
            predicted_blocks = torch.cat(predicted_blocks_all)
            teacher_blocks = torch.cat(teacher_blocks_all)
            residual = (predicted_blocks - teacher_blocks).square()
            block_rows.append({
                "view_index": view,
                "block_jepa_mse": float(residual.mean()),
                "teacher_block_variance": float(teacher_blocks.var(unbiased=False)),
                "predicted_block_variance": float(predicted_blocks.var(unbiased=False)),
                "block_residual_explained_fraction": float(
                    1.0 - residual.sum() / (teacher_blocks - teacher_blocks.mean()).square().sum().clamp_min(1e-12)
                ),
                "teacher_block_effective_rank": geometry(
                    teacher_blocks.reshape(-1, teacher_blocks.shape[-1]), device
                )["effective_rank"],
                "predicted_block_effective_rank": geometry(
                    predicted_blocks.reshape(-1, predicted_blocks.shape[-1]), device
                )["effective_rank"],
                "between_block_cosine": float(
                    F.cosine_similarity(
                        predicted_blocks[:, :-1], predicted_blocks[:, 1:], dim=-1
                    ).mean()
                ),
                "between_cell_variance": float(predicted_blocks.var(dim=0, unbiased=False).mean()),
            })
    values = expression[eval_indices].float().numpy()
    standardized = (values - mean.numpy()) / std.numpy()
    detected = values > 0
    gene_rows: list[dict[str, Any]] = []
    for gene in range(base.GENES):
        available = np.isfinite(predictions[:, :, gene])
        truth = np.broadcast_to(standardized[:, gene], available.shape)[available]
        value_hat = predictions[:, :, gene][available]
        detection_truth = np.broadcast_to(detected[:, gene], available.shape)[available]
        logits = detection_logits[:, :, gene][available]
        residual = np.square(truth - value_hat).sum()
        total = np.square(truth - truth.mean()).sum()
        gene_r2 = float(1.0 - residual / total) if total > 0 else float("nan")
        if np.unique(detection_truth).size == 2:
            auroc = float(roc_auc_score(detection_truth, logits))
            auprc = float(average_precision_score(detection_truth, logits))
        else:
            auroc = auprc = float("nan")
        gene_rows.append({
            "fixture": run["fixture"], "seed": seed, "condition": condition,
            "gene_index": gene, "hidden_observations": int(available.sum()),
            "expression_r2": gene_r2, "mae": float(np.mean(np.abs(truth - value_hat))),
            "detection_auroc": auroc, "detection_auprc": auprc,
            "training_expression_variance": float(variance[gene]),
            "training_detection_frequency": float(detection_frequency[gene]),
        })
    stacked = torch.stack(mask_embeddings)
    normalized = F.normalize(stacked, dim=-1)
    same_cosine = []
    same_l2 = []
    for first in range(8):
        for second in range(first + 1, 8):
            same_cosine.append((normalized[first] * normalized[second]).sum(-1))
            same_l2.append(torch.linalg.vector_norm(stacked[first] - stacked[second], dim=-1))
    same_l2_values = torch.cat(same_l2)
    cell_means = stacked.mean(0)
    between = torch.pdist(cell_means)
    summary = {
        "mask_views": 8,
        "factor_readouts": mask_readouts,
        "same_cell_cross_mask_cosine": quantiles(torch.cat(same_cosine).numpy()),
        "same_cell_cross_mask_l2": quantiles(same_l2_values.numpy()),
        "between_cell_distance": quantiles(between.numpy()),
        "same_to_between_distance_ratio": float(same_l2_values.median() / between.median()),
        "gene_summary": {
            metric: quantiles(np.asarray([row[metric] for row in gene_rows]))
            for metric in ("expression_r2", "mae", "detection_auroc", "detection_auprc")
        },
        "block_jepa": block_rows,
    }
    return gene_rows, summary


def prepare_exact_real_sample(project: Path) -> list[dict[str, Any]]:
    report = json.loads((project / "results/v4/stage81a2_freeze_report.json").read_text())
    if not report["stage81a2_pass"] or report["frozen_vocabulary_hash"] != real_smoke.VOCABULARY_HASH:
        raise RuntimeError("Frozen Stage81A2 contract is not valid")
    _, vocabulary_ids = real_smoke.vocabulary_contract(project)
    donors = real_smoke.train_donors(project)
    measurements = real_smoke.measurement_masks(project, vocabulary_ids)
    matrices = pd.read_csv(project / "results/v4/stage81a2_matrix_semantics_contract.csv")
    matrices["foundation_eligible"] = matrices.foundation_eligible.astype(str).str.lower().eq("true")
    candidates = real_smoke.h5_candidates(project, matrices, donors, real_smoke.SMOKE_SEED)
    hvs = real_smoke.balanced_select(real_smoke.load_h5_candidate_expression(
        project, candidates["HVS"], "HVS", vocabulary_ids, measurements["HVS_COMMON"]
    ), real_smoke.H5_SOURCE_TARGET)
    sea = real_smoke.balanced_select(real_smoke.load_h5_candidate_expression(
        project, candidates["SEA_AD"], "SEA_AD", vocabulary_ids, measurements["SEA_AD_COMMON"]
    ), real_smoke.H5_SOURCE_TARGET)
    nph = real_smoke.load_nph_cache(project, vocabulary_ids, measurements)
    rows = hvs + nph + sea
    rows.sort(key=lambda item: (
        item["source"], item["broad_cell_class"], item["selection_hash"], item["cell_id"]
    ))
    counts = pd.Series([row["source"] for row in rows]).value_counts().to_dict()
    donors_count = len({(row["source"], row["donor_id"]) for row in rows})
    if len(rows) != 502 or counts != {"NPH52": 246, "HVS": 128, "SEA_AD": 128} or donors_count != 109:
        raise RuntimeError(f"Exact prior real-RNA sample was not reconstructed: {len(rows)}, {counts}, {donors_count}")
    return rows


def centered_gram(values: torch.Tensor) -> torch.Tensor:
    values = values.float()
    values = values - values.mean(0, keepdim=True)
    return values @ values.T


def linear_cka(left: torch.Tensor, right: torch.Tensor) -> float:
    left_gram = centered_gram(left)
    right_gram = centered_gram(right)
    centering = lambda gram: gram - gram.mean(0, keepdim=True) - gram.mean(1, keepdim=True) + gram.mean()
    left_gram = centering(left_gram); right_gram = centering(right_gram)
    return float(
        (left_gram * right_gram).sum()
        / torch.sqrt(left_gram.square().sum() * right_gram.square().sum()).clamp_min(1e-12)
    )


def flattened_feature_gram(features: torch.Tensor, chunk: int = 8192) -> torch.Tensor:
    flattened = features.reshape(len(features), -1)
    gram = torch.zeros(len(features), len(features))
    for start in range(0, flattened.shape[1], chunk):
        values = flattened[:, start:start + chunk].float()
        values = values - values.mean(0, keepdim=True)
        gram.add_(values @ values.T)
    return gram


def gram_cka(left: torch.Tensor, right: torch.Tensor) -> float:
    center = lambda gram: gram - gram.mean(0, keepdim=True) - gram.mean(1, keepdim=True) + gram.mean()
    left = center(left.float()); right = center(right.float())
    return float((left * right).sum() / torch.sqrt(left.square().sum() * right.square().sum()).clamp_min(1e-12))


def real_token_gram_cka(
    target: torch.nn.Module,
    expression: torch.Tensor,
    measurement: torch.Tensor,
    device: torch.device,
) -> float:
    tokenizer_parts = []
    target_parts = []
    target_model = ema_target_module(target)
    with torch.no_grad():
        for start in range(0, len(expression), MICROBATCH):
            count = min(MICROBATCH, len(expression) - start)
            values = expression[start:start + count].to(device)
            measured = measurement[start:start + count].to(device)
            ids = torch.arange(base.GENES, device=device).repeat(count, 1)
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                tokenizer_parts.append(target_model.tokenizer(ids, values).half().cpu())
                target_parts.append(target(
                    ids, values, measured, torch.zeros_like(measured), "target"
                ).gene_states.half().cpu())
    tokenizer = torch.cat(tokenizer_parts)
    tokenizer_gram = flattened_feature_gram(tokenizer)
    del tokenizer, tokenizer_parts
    contextual = torch.cat(target_parts)
    contextual_gram = flattened_feature_gram(contextual)
    del contextual, target_parts
    return gram_cka(tokenizer_gram, contextual_gram)


def distance_and_knn(raw: torch.Tensor, embedding: torch.Tensor) -> dict[str, Any]:
    raw_distance = torch.cdist(raw.float(), raw.float())
    embedding_distance = torch.cdist(embedding.float(), embedding.float())
    upper = torch.triu_indices(len(raw), len(raw), offset=1)
    correlation = spearmanr(
        raw_distance[upper[0], upper[1]].numpy(),
        embedding_distance[upper[0], upper[1]].numpy(),
    ).statistic
    overlaps = {}
    for k in (10, 30):
        raw_neighbors = raw_distance.topk(k + 1, largest=False).indices[:, 1:]
        embedding_neighbors = embedding_distance.topk(k + 1, largest=False).indices[:, 1:]
        overlap = [
            len(set(first.tolist()) & set(second.tolist())) / k
            for first, second in zip(raw_neighbors, embedding_neighbors)
        ]
        overlaps[f"knn_{k}_overlap"] = float(np.mean(overlap))
    return {"pairwise_distance_spearman": float(correlation), **overlaps}


def real_forward_model(
    condition: str,
    components: tuple[IPBEncoder, torch.nn.Module, BlockPredictor, GeneAnchorDecoder],
    rows: list[dict[str, Any]],
    graph: CorrelationGraph,
    device: torch.device,
) -> dict[str, Any]:
    online, target, predictor, decoder = components
    modules = {"online": online, "target": target, "predictor": predictor, "decoder": decoder}
    before = {
        name: {key: value.detach().cpu().clone() for key, value in module.state_dict().items()}
        for name, module in modules.items()
    }
    expression = torch.from_numpy(np.stack([row["expression"] for row in rows])).float()
    measurement = torch.from_numpy(np.stack([row["measurement_mask"] for row in rows])).bool()
    cell_indices = torch.arange(len(rows))
    full_parts = []
    masked_views: list[torch.Tensor] = []
    finite = True
    online.eval(); target.eval(); predictor.eval(); decoder.eval()
    with torch.no_grad():
        for start in range(0, len(rows), MICROBATCH):
            count = min(MICROBATCH, len(rows) - start)
            values = expression[start:start + count].to(device)
            measured = measurement[start:start + count].to(device)
            ids = torch.arange(base.GENES, device=device).repeat(count, 1)
            zero = torch.zeros_like(measured)
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                output = target(ids, values, measured, zero, "target")
            full_parts.append(output.cell_state.float().cpu())
        full = torch.cat(full_parts)
        for view in range(8):
            blocks_cpu = sample_target_blocks(
                measurement, graph, production_seed=SEEDS[0], cell_indices=cell_indices,
                sample_pass=STEPS, view_index=view, mask_fraction=MASK_FRACTION,
                block_count=BLOCKS,
            )
            parts = []
            for start in range(0, len(rows), MICROBATCH):
                count = min(MICROBATCH, len(rows) - start)
                values = expression[start:start + count].to(device)
                measured = measurement[start:start + count].to(device)
                hidden = blocks_cpu.hidden_mask[start:start + count].to(device)
                ids = torch.arange(base.GENES, device=device).repeat(count, 1)
                with torch.autocast(device_type="cuda", dtype=torch.float16):
                    output = online(ids, values, measured, hidden, "student")
                parts.append(output.cell_state.float().cpu())
            masked_views.append(torch.cat(parts))
    finite = bool(torch.isfinite(full).all() and all(torch.isfinite(item).all() for item in masked_views))
    raw = expression.masked_fill(~measurement, 0.0)
    full_metrics = {"geometry": real_smoke.geometry_2d(full),
                    "raw_vs_embedding_linear_cka": linear_cka(raw, full),
                    **distance_and_knn(raw, full)}
    masked_metrics = []
    for view, values in enumerate(masked_views):
        masked_metrics.append({
            "view_index": view, "geometry": real_smoke.geometry_2d(values),
            "raw_vs_embedding_linear_cka": linear_cka(raw, values),
            **distance_and_knn(raw, values),
        })
    maximum_change = 0.0
    for name, module in modules.items():
        for key, value in module.state_dict().items():
            maximum_change = max(maximum_change, float((value.detach().cpu() - before[name][key]).abs().max()))
    if maximum_change != 0.0:
        raise RuntimeError("Real-RNA forward smoke changed model parameters")
    token_cka = real_token_gram_cka(target, expression, measurement, device)
    return {
        "condition": condition, "finite": finite,
        "full_view": full_metrics, "masked_views": masked_metrics,
        "zero_weight_change_max_abs_diff": maximum_change,
        "optimizer_steps": 0, "ema_updates": 0, "backward_calls": 0,
        "tokenizer_vs_contextual_gene_token_gram_cka": token_cka,
    }


def run_real_forward_smoke(
    project: Path,
    retained: dict[str, tuple[IPBEncoder, torch.nn.Module, BlockPredictor, GeneAnchorDecoder]],
    graph: CorrelationGraph,
    device: torch.device,
) -> dict[str, Any]:
    rows = prepare_exact_real_sample(project)
    results = [real_forward_model(condition, retained[condition], rows, graph, device)
               for condition in CONDITIONS]
    return {
        "stage": "Stage81A3_IPB_JEPA_real_RNA_forward_only_smoke",
        "sample": {
            "cells": len(rows),
            "sources": pd.Series([row["source"] for row in rows]).value_counts().to_dict(),
            "donors": len({(row["source"], row["donor_id"]) for row in rows}),
            "exact_previous_sample_reconstructed": True,
        },
        "models": results,
        "safety": {"pathology_opened": False, "optimizer_steps": 0,
                   "ema_updates": 0, "backward_calls": 0,
                   "real_rna_training": False},
    }


def factor_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for run in runs:
        for checkpoint in run["checkpoints"]:
            for representation, readout in checkpoint["readouts"].items():
                for factor, value in enumerate(readout["per_factor_r2"]):
                    rows.append({
                        "fixture": run["fixture"], "seed": run["seed"],
                        "condition": run["condition"],
                        "optimizer_step": checkpoint["optimizer_step"],
                        "representation": representation,
                        "factor_index": factor, "factor_r2": value,
                    })
    return rows


def geometry_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for run in runs:
        for checkpoint in run["checkpoints"]:
            for representation, item in checkpoint["geometry"].items():
                rows.append({
                    "fixture": run["fixture"], "seed": run["seed"],
                    "condition": run["condition"],
                    "optimizer_step": checkpoint["optimizer_step"],
                    "representation": representation,
                    "effective_rank": item["effective_rank"],
                    "top_singular_l1_fraction": item["top_singular_l1_fraction"],
                    "top_singular_energy_fraction": item["top_singular_energy_fraction"],
                    "cross_cell_std_mean": item["cross_cell_std_mean"],
                    "median_pairwise_distance": item["median_pairwise_distance"],
                    "concerning_geometry": (
                        item["effective_rank"] < 32
                        or item["top_singular_energy_fraction"] > .50
                    ),
                })
    return rows


def paired_jepa_deltas(runs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    indexed = {(run["fixture"], run["seed"], run["condition"]): run for run in runs}
    rows = []
    for fixture in FIXTURES:
        for seed in SEEDS:
            ipb = indexed[(fixture, seed, "ipb_jepa")]
            anchor = indexed[(fixture, seed, "anchor_only")]
            ipb_final = ipb["checkpoints"][-1]
            anchor_final = anchor["checkpoints"][-1]
            rows.append({
                "fixture": fixture, "seed": seed,
                "masked_factor_r2_delta": (
                    ipb_final["readouts"]["online_masked_cell"]["mean_r2"]
                    - anchor_final["readouts"]["online_masked_cell"]["mean_r2"]
                ),
                "full_factor_r2_delta": (
                    ipb_final["readouts"]["target_cell"]["mean_r2"]
                    - anchor_final["readouts"]["target_cell"]["mean_r2"]
                ),
                "contextual_token_r2_delta": (
                    ipb_final["readouts"]["contextual_teacher_gene_tensor"]["mean_r2"]
                    - anchor_final["readouts"]["contextual_teacher_gene_tensor"]["mean_r2"]
                ),
                "hidden_gene_median_r2_delta": (
                    ipb["final_molecular_audit"]["gene_summary"]["expression_r2"]["median"]
                    - anchor["final_molecular_audit"]["gene_summary"]["expression_r2"]["median"]
                ),
                "cross_mask_cosine_delta": (
                    ipb["final_molecular_audit"]["same_cell_cross_mask_cosine"]["median"]
                    - anchor["final_molecular_audit"]["same_cell_cross_mask_cosine"]["median"]
                ),
            })
    metrics = [key for key in rows[0] if key.endswith("_delta")]
    material = 0.01
    supported = False
    for metric in metrics:
        for fixture in FIXTURES:
            selected = [row[metric] for row in rows if row["fixture"] == fixture]
            other = [row[metric] for row in rows if row["fixture"] != fixture]
            if min(selected) >= material and np.mean(other) >= -material:
                supported = True
    return rows, supported


def classify(runs: list[dict[str, Any]], real_report: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    ipb = [run for run in runs if run["condition"] == "ipb_jepa"]
    anchor = [run for run in runs if run["condition"] == "anchor_only"]
    fixture_token = {
        fixture: float(np.median([run["final_metrics"]["token_encoder_retention"]
                                  for run in ipb if run["fixture"] == fixture]))
        for fixture in FIXTURES
    }
    fixture_cell = {
        fixture: float(np.median([run["final_metrics"]["cell_retention"]
                                  for run in ipb if run["fixture"] == fixture]))
        for fixture in FIXTURES
    }
    token_pass = all(value >= .95 for value in fixture_token.values()) and all(
        run["final_metrics"]["token_encoder_retention"] >= .90 for run in ipb
    )
    cell_pass = all(value >= .90 for value in fixture_cell.values()) and all(
        run["final_metrics"]["cell_retention"] >= .80 for run in ipb
    )
    masked_pass = all(
        run["final_metrics"]["masked_to_full"] >= .80
        and run["final_metrics"]["masked_minus_visible_raw"] >= 0
        for run in ipb
    )
    anchor_information_pass = all(
        run["final_metrics"]["cell_retention"] >= .80
        and run["final_metrics"]["masked_to_full"] >= .80
        for run in anchor
    )
    deltas, jepa_value = paired_jepa_deltas(runs)
    engineering = all(
        run["training"]["optimizer_updates"] == STEPS
        and run["training"]["ema_updates"] == STEPS
        and run["training"]["nonfinite_loss_events"] == 0
        and run["training"]["nonfinite_gradient_events"] == 0
        for run in runs
    ) and all(model["finite"] for model in real_report["models"])
    if not engineering:
        classification = "ENGINEERING OR NUMERICAL FAILURE"
    elif not token_pass:
        classification = "TOKEN-PRESERVING ENCODER STILL DESTROYS TOO MUCH INFORMATION"
    elif cell_pass and not masked_pass:
        classification = "FULL CELL STATE IS RICH BUT MASKED INFERENCE STILL FAILS"
    elif not cell_pass and not anchor_information_pass:
        classification = "BOTH IPB-JEPA AND ANCHOR-ONLY FAIL INFORMATION-PRESERVATION"
    elif token_pass and cell_pass and masked_pass and jepa_value:
        classification = "IPB-JEPA INFORMATION-PRESERVING FEASIBILITY STRONGLY SUPPORTED"
    elif anchor_information_pass and not jepa_value:
        classification = "ANCHOR-ONLY INFORMATION-PRESERVING MODEL OUTPERFORMS JEPA"
    else:
        classification = "FEASIBILITY INCONCLUSIVE"
    return classification, {
        "token_preservation_pass": token_pass,
        "fixture_token_retention_medians": fixture_token,
        "cell_information_pass": cell_pass,
        "fixture_cell_retention_medians": fixture_cell,
        "masked_inference_pass": masked_pass,
        "anchor_information_pass": anchor_information_pass,
        "engineering_and_real_forward_pass": engineering,
        "jepa_value_over_anchor": jepa_value,
        "jepa_materiality_guard_absolute_r2_or_metric_delta": 0.01,
        "paired_deltas": deltas,
    }


def append_documentation(project: Path, payload: dict[str, Any]) -> None:
    path = project / "docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md"
    heading = "## MRA-JEPA v4.1 IPB-JEPA FEASIBILITY STUDY"
    if heading in path.read_text(encoding="utf-8"):
        return
    gate = payload["feasibility_gates"]
    section = f"""

{heading}

The earlier 24-slot global Perceiver candidate was rejected because early gene-to-slot
compression and global teacher/student agreement erased information despite low JEPA loss.
This human-authorized v4.1 study instead used the unchanged information-rich tokenizer, six
token-preserving ELU+1 linear-attention blocks, one learned 160-dimensional cell token,
train-only absolute-Pearson graphs for masking only, sixteen disjoint hidden blocks, an EMA
teacher block target, and a cell-state-only bilinear hidden-gene anchor. The matched control
used the same encoder, masks, decoder, and EMA mechanics without the block-JEPA loss.

Exactly eight synthetic trajectories were run: two fixtures, the first two frozen historical
seeds, and the two predeclared objectives, each for 500 optimizer updates. No ninth run,
hyperparameter sweep, checkpoint selection, graph message passing, variance/covariance
training penalty, or real-RNA optimization was performed. Compact outputs preserve all
32 factor readouts, all 4,096 per-gene audits, eight-mask robustness, geometry, block,
gradient, numerical, throughput, and memory telemetry.

The exact prior pathology-blind 502-cell RNA smoke sample was reconstructed (128 HVS,
246 NPH, 128 SEA-AD; 109 source-qualified training donors). The predeclared balanced-fixture,
first-seed step-500 IPB-JEPA and anchor-only states were evaluated forward-only with zero
optimizer steps, EMA updates, and backward calls. This is engineering and broad molecular-
geometry evidence only, not biological, disease, pathology, or generalization evidence.

Final gates: token preservation={gate['token_preservation_pass']}; cell information=
{gate['cell_information_pass']}; masked inference={gate['masked_inference_pass']}; JEPA value
over anchor={gate['jepa_value_over_anchor']}. Final bounded classification:
**{payload['classification']}**.

The hard stop remains active. No additional architecture, mask, graph, seed, objective,
regularizer, EMA, duration, or real-data training experiment is authorized by this task.
"""
    atomic_text(path, path.read_text(encoding="utf-8") + section)


def main() -> int:
    args = parse_args()
    project = args.project_dir.resolve()
    os.chdir(project)
    if not torch.cuda.is_available():
        raise RuntimeError("The locked CUDA runtime is required")
    if OUTPUT_JSON.exists() and not args.overwrite:
        raise RuntimeError(f"Output exists: {OUTPUT_JSON}; use --overwrite only for the authorized exact rerun")
    device = torch.device("cuda")
    payload: dict[str, Any] = {
        "stage": "Stage81A3_MRA_JEPA_v4.1_IPB_JEPA_feasibility",
        "config": config_payload(), "config_hash": config_hash(),
        "runs": [], "gene_rows_file": str(OUTPUT_GENES),
        "stage81a3_complete": False, "stage81b_started": False,
    }
    all_gene_rows: list[dict[str, Any]] = []
    retained: dict[str, tuple[IPBEncoder, torch.nn.Module, BlockPredictor, GeneAnchorDecoder]] = {}
    retained_graph = None
    order = [
        (FIXTURES[1], SEEDS[0]), (FIXTURES[1], SEEDS[1]),
        (FIXTURES[0], SEEDS[1]), (FIXTURES[0], SEEDS[0]),
    ]
    for fixture, seed in order:
        expression, factors, fixture_metadata = base.synthetic_fixture(fixture, smoke=False)
        graph = graph_for_fixture(expression, device)
        for condition in CONDITIONS:
            print(f"starting authorized trajectory {len(payload['runs']) + 1}/8: {fixture} {seed} {condition}", flush=True)
            run, gene_rows, kept = train_run(
                fixture, seed, condition, expression, factors, graph, device
            )
            run["fixture_metadata"] = fixture_metadata
            payload["runs"].append(run); all_gene_rows.extend(gene_rows)
            if kept is not None:
                retained[condition] = kept
                retained_graph = graph
            atomic_json(OUTPUT_JSON, payload)
            torch.cuda.empty_cache()
    if len(payload["runs"]) != 8 or set(retained) != set(CONDITIONS) or retained_graph is None:
        raise RuntimeError("Exact eight-run or predeclared real-model retention contract failed")
    real_report = run_real_forward_smoke(project, retained, retained_graph, device)
    atomic_json(OUTPUT_REAL, real_report)
    classification, gates = classify(payload["runs"], real_report)
    payload.update({
        "real_forward_smoke_file": str(OUTPUT_REAL),
        "feasibility_gates": gates, "classification": classification,
        "cumulative_synthetic_optimizer_updates": sum(
            run["training"]["optimizer_updates"] for run in payload["runs"]
        ),
        "cumulative_synthetic_ema_updates": sum(
            run["training"]["ema_updates"] for run in payload["runs"]
        ),
        "safety": {"real_rna_optimizer_steps": 0, "real_rna_ema_updates": 0,
                   "real_rna_backward_calls": 0, "real_rna_cells": 502,
                   "pathology_opened": False, "stage81b_started": False,
                   "stage81c_started": False, "production_seed_selected": False,
                   "production_ema_selected": False, "hyperparameter_sweep": False,
                   "graph_used_as_model_input": False,
                   "graph_used_only_for_target_block_sampling": True},
    })
    write_csv(OUTPUT_RUNS, [{
        "fixture": run["fixture"], "seed": run["seed"], "condition": run["condition"],
        **run["final_metrics"],
        "optimizer_updates": run["training"]["optimizer_updates"],
        "ema_updates": run["training"]["ema_updates"],
        "peak_allocated_bytes": run["training"]["peak_allocated_bytes"],
        "elapsed_seconds": run["training"]["elapsed_seconds"],
    } for run in payload["runs"]])
    write_csv(OUTPUT_FACTORS, factor_rows(payload["runs"]))
    write_csv(OUTPUT_GENES, all_gene_rows)
    write_csv(OUTPUT_GEOMETRY, geometry_rows(payload["runs"]))
    atomic_json(OUTPUT_JSON, payload)
    append_documentation(project, payload)
    print(json.dumps({
        "classification": classification, "trajectories": len(payload["runs"]),
        "optimizer_updates": payload["cumulative_synthetic_optimizer_updates"],
        "ema_updates": payload["cumulative_synthetic_ema_updates"],
        "real_rna_cells": 502, "pathology_opened": False,
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
