#!/usr/bin/env python3
"""Run the single bounded Stage81A3 RLC-CD full-vocabulary feasibility probe."""

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
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.v4 import stage81a3_forensic_failed_trajectory_replay as forensic  # noqa: E402
from scripts.v4 import stage81a3_synthetic_geometry_escape as historical  # noqa: E402
from sea_ad_jepa.v4.rlc_causal import (  # noqa: E402
    CausalAuxiliary,
    MaskBank,
    RLCModel,
    WhitenedPCABasis,
    build_mask_bank,
    fit_whitened_pca_gram,
    gpu_topk_absolute_correlation,
    rlc_loss,
)


ANCHOR = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
IPB_PARTIAL_SHA256 = "aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308"
SEED = 8114001
CELLS = 2048
TRAIN = 1536
READOUT_FIT = 256
READOUT_TEST = 256
GENES = 4096
FACTORS = 32
MECHANISMS = 12
WIDTH = 160
HIDDEN = 1638
BLOCKS = 4
MASK_VIEWS = 256
UPDATES = 100
EFFECTIVE_BATCH = 256
CHECKPOINTS = (0, 25, 50, 100)
CONDITIONS = ("RLC_BASE", "RLC_CF", "RLC_CAUSAL_DAG")
OUTPUT_JSON = Path("results/v4/stage81a3_rlc_causal_fast_probe.json")
OUTPUT_CONDITIONS = Path("results/v4/stage81a3_rlc_causal_conditions.csv")
OUTPUT_FACTORS = Path("results/v4/stage81a3_rlc_causal_factors.csv")
OUTPUT_GENES = Path("results/v4/stage81a3_rlc_causal_genes.csv")
OUTPUT_DAG = Path("results/v4/stage81a3_rlc_causal_dag.csv")

TRUE_EDGES = (
    (0, 3, .65), (0, 4, -.55), (1, 4, .70), (1, 5, -.60),
    (2, 5, .75), (2, 6, .55), (3, 7, .60), (4, 7, -.65),
    (4, 8, .50), (5, 8, .70), (5, 9, -.55), (6, 9, .65),
    (7, 10, .70), (8, 10, -.50), (8, 11, .60), (9, 11, .75),
)


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
        if os.path.exists(temporary): os.unlink(temporary)


def atomic_json(path: Path, payload: Any) -> None:
    atomic_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({key for row in rows for key in row})
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader(); writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def true_adjacency(device: torch.device) -> torch.Tensor:
    adjacency = torch.zeros(MECHANISMS, MECHANISMS, device=device)
    for source, target, weight in TRUE_EDGES:
        adjacency[source, target] = weight
    return adjacency


def generate_causal_values(
    exogenous: torch.Tensor,
    adjacency: torch.Tensor,
    intervention_node: torch.Tensor | None = None,
    intervention_raw_delta: torch.Tensor | None = None,
) -> torch.Tensor:
    values = torch.zeros_like(exogenous)
    for node in range(MECHANISMS):
        values[:, node] = 0.70 * exogenous[:, node] + values @ adjacency[:, node]
        if intervention_node is not None:
            intervene = intervention_node == node
            values[intervene, node] = values[intervene, node] + intervention_raw_delta[intervene]
    return values


def causal_fixture(device: torch.device) -> dict[str, torch.Tensor | dict[str, Any]]:
    started = time.perf_counter()
    torch.manual_seed(SEED + 101); torch.cuda.manual_seed_all(SEED + 101)
    generator = torch.Generator(device=device).manual_seed(SEED + 101)
    exogenous = torch.randn(CELLS, MECHANISMS, generator=generator, device=device)
    independent = torch.randn(CELLS, FACTORS - MECHANISMS, generator=generator, device=device)
    adjacency = true_adjacency(device)
    causal_raw = generate_causal_values(exogenous, adjacency)
    causal_mean = causal_raw[:TRAIN].mean(0)
    causal_std = causal_raw[:TRAIN].std(0, unbiased=False).clamp_min(1e-6)
    intervention_node = torch.arange(CELLS, device=device) % MECHANISMS
    intervention_delta = torch.where(
        (torch.arange(CELLS, device=device) // MECHANISMS) % 2 == 0,
        torch.ones(CELLS, device=device), -torch.ones(CELLS, device=device),
    )
    counterfactual_raw = generate_causal_values(
        exogenous, adjacency, intervention_node, intervention_delta * causal_std[intervention_node]
    )
    causal = (causal_raw - causal_mean) / causal_std
    causal_cf = (counterfactual_raw - causal_mean) / causal_std
    factors = torch.cat((causal, independent), dim=1)
    factors_cf = torch.cat((causal_cf, independent), dim=1)
    loadings = torch.zeros(FACTORS, GENES, device=device)
    module_size = 224
    for factor in range(FACTORS):
        start = (factor * 257 + 31) % GENES
        indices = (start + torch.arange(module_size, device=device) * 17) % GENES
        signs = torch.where(torch.arange(module_size, device=device) % 2 == 0, 1.0, -1.0)
        amplitude = 0.34 + 0.08 * torch.rand(module_size, generator=generator, device=device)
        loadings[factor, indices] += signs * amplitude
    baseline = -1.8 + .45 * torch.randn(GENES, generator=generator, device=device)
    library = torch.exp(
        math.log(5500.0) + .55 * torch.randn(CELLS, generator=generator, device=device)
    ).clamp(1200, 25000)

    def rates(latent: torch.Tensor) -> torch.Tensor:
        return torch.softmax(baseline + latent @ loadings, dim=1) * library[:, None]

    factual_rates = rates(factors)
    counterfactual_rates = rates(factors_cf)
    poisson_state = torch.cuda.get_rng_state(device)
    factual_counts = torch.poisson(factual_rates)
    torch.cuda.set_rng_state(poisson_state, device)
    counterfactual_counts = torch.poisson(counterfactual_rates)

    def normalize(counts: torch.Tensor) -> torch.Tensor:
        return torch.log1p(counts * (10_000.0 / counts.sum(1, keepdim=True).clamp_min(1.0)))

    factual = normalize(factual_counts)
    counterfactual = normalize(counterfactual_counts)
    return {
        "factual": factual, "counterfactual": counterfactual,
        "factors": factors, "factors_cf": factors_cf,
        "exogenous": exogenous, "intervention_node": intervention_node,
        "intervention_delta": intervention_delta, "true_adjacency": adjacency,
        "metadata": {
            "generation_seconds": time.perf_counter() - started,
            "matched_count_randomness": "CUDA RNG state restored before counterfactual torch.poisson",
            "library_size_identical_within_pair": True,
            "independent_factors_identical_within_pair": True,
            "factor_labels_used_for_training": False,
            "true_dag_used_for_training": False,
        },
    }


def block_tensors(
    centered: torch.Tensor,
    basis: WhitenedPCABasis,
    bank: MaskBank,
    view_indices: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    visible = bank.visible[view_indices]
    blocks = bank.block_masks[view_indices]
    u_visible = (centered * visible) @ basis.whitened.T
    true_blocks = torch.matmul(centered[:, None, :] * blocks, basis.whitened.T)
    signatures = torch.matmul(blocks.float(), basis.whitened.abs().T)
    signatures = signatures / blocks.sum(2, keepdim=True).clamp_min(1)
    return (
        visible, u_visible, true_blocks, signatures,
        bank.block_indices[view_indices], bank.block_members[view_indices],
    )


def model_forward(
    model: RLCModel,
    causal: CausalAuxiliary | None,
    expression: torch.Tensor,
    centered: torch.Tensor,
    basis: WhitenedPCABasis,
    bank: MaskBank,
    view_indices: torch.Tensor,
) -> dict[str, torch.Tensor]:
    visible, u_visible, targets, signatures, indices, members = block_tensors(
        centered, basis, bank, view_indices
    )
    gene_ids = torch.arange(GENES, device=expression.device).repeat(len(expression), 1)
    causal_context = causal.context(u_visible) if causal is not None else None
    completed, predicted, denominator = model(
        gene_ids, expression, visible, indices, members, signatures, u_visible,
        causal_context,
    )
    return {
        "completed": completed, "predicted_blocks": predicted,
        "true_blocks": targets, "u_visible": u_visible,
        "u_full": basis.transform(expression), "minimum_denominator": denominator,
    }


def condition_loss(
    condition: str,
    model: RLCModel,
    causal: CausalAuxiliary | None,
    factual: torch.Tensor,
    counterfactual: torch.Tensor,
    basis: WhitenedPCABasis,
    bank: MaskBank,
    view_indices: torch.Tensor,
    intervention_node: torch.Tensor,
    intervention_delta: torch.Tensor,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    factual_output = model_forward(
        model, causal, factual, factual - basis.mean, basis, bank, view_indices
    )
    factual_loss = rlc_loss(
        factual_output["completed"], factual_output["predicted_blocks"],
        factual_output["u_full"], factual_output["true_blocks"],
    )
    metrics = {"factual_rlc": factual_loss["rlc"]}
    if condition == "RLC_BASE":
        return factual_loss["rlc"], metrics | factual_output
    counterfactual_output = model_forward(
        model, causal, counterfactual, counterfactual - basis.mean, basis, bank, view_indices
    )
    counterfactual_loss = rlc_loss(
        counterfactual_output["completed"], counterfactual_output["predicted_blocks"],
        counterfactual_output["u_full"], counterfactual_output["true_blocks"],
    )
    delta_pred = counterfactual_output["completed"] - factual_output["completed"]
    delta_true = counterfactual_output["u_full"] - factual_output["u_full"]
    counterfactual_delta = F.smooth_l1_loss(delta_pred, delta_true, beta=1.0)
    total = factual_loss["rlc"] + counterfactual_loss["rlc"] + .25 * counterfactual_delta
    metrics.update({"counterfactual_rlc": counterfactual_loss["rlc"], "counterfactual_delta": counterfactual_delta})
    if condition == "RLC_CAUSAL_DAG":
        if causal is None: raise RuntimeError("causal condition requires auxiliary")
        intervention = F.one_hot(intervention_node, MECHANISMS).float() * intervention_delta[:, None]
        response = causal.propagate(intervention)
        mechanism_delta = causal.mechanism(counterfactual_output["u_visible"]) - causal.mechanism(factual_output["u_visible"])
        mechanism_loss = F.smooth_l1_loss(mechanism_delta, response, beta=1.0)
        graph_delta = causal.response(response)
        graph_loss = F.smooth_l1_loss(graph_delta, delta_true, beta=1.0)
        acyclic = causal.acyclicity()
        sparse = causal.adjacency().abs().mean()
        total = total + .10 * mechanism_loss + .10 * graph_loss + .01 * acyclic + .001 * sparse
        metrics.update({"mechanism": mechanism_loss, "graph_counterfactual": graph_loss,
                        "acyclicity": acyclic, "sparsity": sparse})
    return total, metrics | factual_output


def summarize(values: torch.Tensor | np.ndarray) -> dict[str, float]:
    array = torch.as_tensor(values).detach().float().flatten().cpu()
    finite = array[torch.isfinite(array)]
    if not len(finite):
        return {key: float("nan") for key in (
            "minimum", "p10", "p25", "median", "mean", "p75", "p90", "maximum"
        )}
    return {
        "minimum": float(finite.min()), "p10": float(torch.quantile(finite, .10)),
        "p25": float(torch.quantile(finite, .25)), "median": float(finite.median()),
        "mean": float(finite.mean()), "p75": float(torch.quantile(finite, .75)),
        "p90": float(torch.quantile(finite, .90)), "maximum": float(finite.max()),
    }


def gpu_ridge_readout(
    fit_values: torch.Tensor,
    fit_factors: torch.Tensor,
    test_values: torch.Tensor,
    test_factors: torch.Tensor,
    *,
    alpha: float = 1.0e-3,
) -> dict[str, Any]:
    x_fit = fit_values.float()
    x_test = test_values.float()
    y_fit = fit_factors.float()
    y_test = test_factors.float()
    x_mean = x_fit.mean(0, keepdim=True)
    x_std = x_fit.std(0, unbiased=False, keepdim=True).clamp_min(1e-8)
    y_mean = y_fit.mean(0, keepdim=True)
    x_fit = (x_fit - x_mean) / x_std
    x_test = (x_test - x_mean) / x_std
    if x_fit.shape[1] <= len(x_fit):
        identity = torch.eye(x_fit.shape[1], device=x_fit.device)
        weights = torch.linalg.solve(x_fit.T @ x_fit + alpha * identity, x_fit.T @ (y_fit - y_mean))
    else:
        identity = torch.eye(len(x_fit), device=x_fit.device)
        dual = torch.linalg.solve(x_fit @ x_fit.T + alpha * identity, y_fit - y_mean)
        weights = x_fit.T @ dual
    prediction = x_test @ weights + y_mean
    residual = (y_test - prediction).square().sum(0)
    total = (y_test - y_test.mean(0, keepdim=True)).square().sum(0).clamp_min(1e-12)
    r2 = 1.0 - residual / total
    return {**summarize(r2), "per_factor_r2": [float(value) for value in r2.cpu()],
            "ridge_alpha": alpha}


def factor_readout(values: torch.Tensor, factors: torch.Tensor) -> dict[str, Any]:
    return gpu_ridge_readout(
        values[:READOUT_FIT], factors[:READOUT_FIT],
        values[READOUT_FIT:], factors[READOUT_FIT:],
    )


def target_audit(
    expression: torch.Tensor,
    basis: WhitenedPCABasis,
    bank: MaskBank,
    device: torch.device,
) -> dict[str, Any]:
    indices = torch.arange(TRAIN, CELLS, device=device)
    views = torch.arange(len(indices), device=device) % MASK_VIEWS
    centered = expression[indices] - basis.mean
    _, visible, blocks, _, _, _ = block_tensors(centered, basis, bank, views)
    full = basis.transform(expression[indices])
    error = (full - visible - blocks.sum(1)).abs()
    normalized = F.normalize(blocks, dim=-1)
    cosine = normalized @ normalized.transpose(1, 2)
    off = ~torch.eye(BLOCKS, dtype=torch.bool, device=device)
    block_flat = blocks.reshape(-1, WIDTH)
    geometry = historical.geometry_2d(block_flat, device)
    report = {
        "maximum_absolute_reconstruction_error": float(error.max()),
        "median_absolute_reconstruction_error": float(error.median()),
        "p99_absolute_reconstruction_error": float(torch.quantile(error.flatten(), .99)),
        "tolerance": 1.0e-4,
        "pass": bool(error.max() <= 1.0e-4),
        "block_coordinate_variance": summarize(blocks.var(dim=(0, 1), unbiased=False)),
        "between_cell_variance": float(blocks.var(dim=0, unbiased=False).mean()),
        "between_block_cosine": summarize(cosine[:, off]),
        "block_effective_rank": geometry["effective_rank"],
        "prior_pathological_cosine_reproduced": bool(cosine[:, off].median() >= .998),
    }
    return report


def fit_linear_completion(
    expression: torch.Tensor,
    basis: WhitenedPCABasis,
    bank: MaskBank,
    device: torch.device,
) -> dict[str, torch.Tensor | float]:
    centered = expression[:TRAIN] - basis.mean
    views = torch.arange(TRAIN, device=device) % 128
    _, visible, blocks, signatures, _, _ = block_tensors(centered, basis, bank, views)
    design = torch.cat((
        visible[:, None].expand(-1, BLOCKS, -1), signatures,
    ), dim=-1).reshape(-1, WIDTH * 2).float()
    targets = blocks.reshape(-1, WIDTH).float()
    mean = design.mean(0, keepdim=True)
    std = design.std(0, unbiased=False, keepdim=True).clamp_min(1e-8)
    normalized = (design - mean) / std
    identity = torch.eye(normalized.shape[1], device=device)
    weights = torch.linalg.solve(
        normalized.T @ normalized + 1.0e-3 * identity,
        normalized.T @ targets,
    )
    return {"mean": mean, "std": std, "weights": weights, "alpha": 1.0e-3}


def linear_complete(
    linear: dict[str, torch.Tensor | float],
    visible: torch.Tensor,
    signatures: torch.Tensor,
) -> torch.Tensor:
    design = torch.cat((visible[:, None].expand(-1, BLOCKS, -1), signatures), dim=-1)
    normalized = (design.float() - linear["mean"]) / linear["std"]
    predicted = normalized @ linear["weights"]
    return visible + predicted.sum(1)


def initialize_models(condition: str, device: torch.device) -> tuple[RLCModel, CausalAuxiliary | None]:
    torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    model = RLCModel().to(device)
    causal = None
    if condition == "RLC_CAUSAL_DAG":
        torch.manual_seed(SEED + 17); torch.cuda.manual_seed_all(SEED + 17)
        causal = CausalAuxiliary().to(device)
    return model, causal


def memory_probe(
    fixture: dict[str, Any],
    basis: WhitenedPCABasis,
    bank: MaskBank,
    device: torch.device,
) -> tuple[int, list[dict[str, Any]]]:
    rows = []
    chosen = None
    for microbatch in (64, 48, 40, 32, 24, 16, 8):
        torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(device)
        model, causal = initialize_models("RLC_CAUSAL_DAG", device)
        successful = False
        error = None
        try:
            indices = torch.arange(microbatch, device=device)
            views = indices % MASK_VIEWS
            with torch.autocast("cuda", dtype=torch.float16):
                loss, _ = condition_loss(
                    "RLC_CAUSAL_DAG", model, causal,
                    fixture["factual"][indices], fixture["counterfactual"][indices],
                    basis, bank, views, fixture["intervention_node"][indices],
                    fixture["intervention_delta"][indices],
                )
            loss.backward()
            successful = bool(torch.isfinite(loss))
        except torch.cuda.OutOfMemoryError as exc:
            error = type(exc).__name__
        allocated = torch.cuda.max_memory_allocated(device)
        reserved = torch.cuda.max_memory_reserved(device)
        eligible = successful and allocated <= 13.0 * 1024**3
        rows.append({
            "microbatch": microbatch, "successful": successful,
            "peak_allocated_bytes": allocated, "peak_reserved_bytes": reserved,
            "under_13gb": allocated <= 13.0 * 1024**3, "eligible": eligible,
            "error": error,
        })
        del model, causal
        torch.cuda.empty_cache()
        if eligible and chosen is None:
            chosen = microbatch
    if chosen is None:
        raise RuntimeError("No authorized microbatch fits the 13 GB memory bound")
    return chosen, rows


def batch_chunks(indices: torch.Tensor, microbatch: int):
    for start in range(0, len(indices), microbatch):
        yield indices[start:start + microbatch]


def fixed_batch_schedule(device: torch.device) -> torch.Tensor:
    generator = torch.Generator(device=device).manual_seed(SEED + 303)
    return torch.randint(0, TRAIN, (UPDATES, EFFECTIVE_BATCH), generator=generator, device=device)


def mask_schedule(indices: torch.Tensor, update: int) -> torch.Tensor:
    return ((indices * 131 + update * 17 + 23) % MASK_VIEWS).long()


def representation_geometry(values: torch.Tensor, device: torch.device) -> dict[str, Any]:
    return historical.geometry_2d(values.detach().float().cpu(), device)


def readout_partition(fixture: dict[str, Any]) -> tuple[torch.Tensor, torch.Tensor]:
    return fixture["factual"][TRAIN:], fixture["factors"][TRAIN:]


def evaluate_completed(
    model: RLCModel,
    causal: CausalAuxiliary | None,
    expression: torch.Tensor,
    factors: torch.Tensor,
    basis: WhitenedPCABasis,
    bank: MaskBank,
    microbatch: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    model.eval()
    if causal is not None: causal.eval()
    outputs = []
    views_all = 128 + torch.arange(len(expression), device=expression.device) % 128
    with torch.no_grad():
        for start in range(0, len(expression), microbatch):
            end = min(start + microbatch, len(expression))
            with torch.autocast("cuda", dtype=torch.float16):
                output = model_forward(
                    model, causal, expression[start:end],
                    expression[start:end] - basis.mean, basis, bank, views_all[start:end],
                )
            outputs.append(output["completed"].float())
    completed = torch.cat(outputs)
    model.train()
    if causal is not None: causal.train()
    return completed, {
        "factor_readout": factor_readout(completed, factors),
        "geometry": representation_geometry(completed[READOUT_FIT:], expression.device),
    }


def feature_kernel_readout(features: torch.Tensor, factors: torch.Tensor) -> dict[str, Any]:
    split = READOUT_FIT
    train_kernel = torch.zeros(split, split, dtype=torch.float64)
    cross_kernel = torch.zeros(READOUT_TEST, split, dtype=torch.float64)
    flattened = features.reshape(len(features), -1)
    for start in range(0, flattened.shape[1], 8192):
        values = flattened[:, start:start + 8192].float()
        training = values[:split]
        testing = values[split:]
        mean = training.mean(0, keepdim=True)
        training = training - mean; testing = testing - mean
        train_kernel += (training @ training.T).double()
        cross_kernel += (testing @ training.T).double()
    result = forensic.kernel_factor_readout(
        train_kernel, cross_kernel, factors[:split].cpu(), factors[split:].cpu()
    )
    values = np.asarray(result["per_factor_r2"], dtype=float)
    result.update({
        "p10": float(np.quantile(values, .10)), "p25": float(np.quantile(values, .25)),
        "p75": float(np.quantile(values, .75)), "p90": float(np.quantile(values, .90)),
        "minimum": float(values.min()), "maximum": float(values.max()),
    })
    return result


def contextual_token_audit(
    model: RLCModel,
    expression: torch.Tensor,
    factors: torch.Tensor,
    microbatch: int,
) -> dict[str, Any]:
    model.eval()
    all_visible = torch.ones(len(expression), GENES, dtype=torch.bool, device=expression.device)
    tokenizer_parts = []
    contextual_parts = []
    with torch.no_grad():
        for start in range(0, len(expression), microbatch):
            end = min(start + microbatch, len(expression))
            values = expression[start:end]
            ids = torch.arange(GENES, device=expression.device).repeat(len(values), 1)
            with torch.autocast("cuda", dtype=torch.float16):
                tokenizer_parts.append(model.encoder.tokenizer(ids, values).half().cpu())
                contextual_parts.append(
                    model.encoder(ids, values, all_visible[start:end]).gene_states.half().cpu()
                )
    tokenizer = feature_kernel_readout(torch.cat(tokenizer_parts), factors)
    contextual = feature_kernel_readout(torch.cat(contextual_parts), factors)
    model.train()
    return {
        "tokenizer": tokenizer, "contextual": contextual,
        "retention": contextual["mean_r2"] / tokenizer["mean_r2"],
        "pass": contextual["mean_r2"] / tokenizer["mean_r2"] >= .95,
        "full_token_tensor_persisted": False,
    }


def nvidia_utilization() -> float | None:
    try:
        output = subprocess.check_output([
            "nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"
        ], text=True, timeout=5)
        return float(output.strip().splitlines()[0])
    except Exception:
        return None


def train_condition(
    condition: str,
    fixture: dict[str, Any],
    basis: WhitenedPCABasis,
    bank: MaskBank,
    schedule: torch.Tensor,
    microbatch: int,
    initial_token_audit: dict[str, Any],
    device: torch.device,
) -> tuple[dict[str, Any], RLCModel, CausalAuxiliary | None]:
    model, causal = initialize_models(condition, device)
    parameters = list(model.parameters()) + ([] if causal is None else list(causal.parameters()))
    optimizer = torch.optim.AdamW(parameters, lr=1e-4, weight_decay=.01)
    scaler = torch.amp.GradScaler("cuda")
    expression, factors = readout_partition(fixture)
    _, checkpoint = evaluate_completed(
        model, causal, expression, factors, basis, bank, microbatch
    )
    checkpoints = [{"optimizer_step": 0, **checkpoint, "token_audit": initial_token_audit}]
    telemetry = []
    nonfinite = skips = 0
    cpu_preparation = total_wall = 0.0
    torch.cuda.reset_peak_memory_stats(device)
    started = time.perf_counter()
    for update in range(1, UPDATES + 1):
        step_started = time.perf_counter()
        prep_started = time.perf_counter()
        selected = schedule[update - 1]
        views = mask_schedule(selected, update)
        cpu_preparation += time.perf_counter() - prep_started
        optimizer.zero_grad(set_to_none=True)
        loss_sums: dict[str, float] = {}
        forward_ms = backward_ms = 0.0
        for chunk in batch_chunks(torch.arange(EFFECTIVE_BATCH, device=device), microbatch):
            indices = selected[chunk]
            chunk_views = views[chunk]
            forward_start = torch.cuda.Event(enable_timing=True)
            forward_end = torch.cuda.Event(enable_timing=True)
            backward_end = torch.cuda.Event(enable_timing=True)
            forward_start.record()
            with torch.autocast("cuda", dtype=torch.float16):
                loss, metrics = condition_loss(
                    condition, model, causal,
                    fixture["factual"][indices], fixture["counterfactual"][indices],
                    basis, bank, chunk_views, fixture["intervention_node"][indices],
                    fixture["intervention_delta"][indices],
                )
                scaled_loss = loss * (len(indices) / EFFECTIVE_BATCH)
            forward_end.record()
            if not torch.isfinite(loss):
                nonfinite += 1
                raise RuntimeError(f"nonfinite loss {condition} update={update}")
            scaler.scale(scaled_loss).backward()
            backward_end.record(); torch.cuda.synchronize()
            forward_ms += forward_start.elapsed_time(forward_end)
            backward_ms += forward_end.elapsed_time(backward_end)
            for key, value in metrics.items():
                if value.ndim == 0:
                    loss_sums[key] = loss_sums.get(key, 0.0) + float(value.detach()) * len(indices) / EFFECTIVE_BATCH
        scaler.unscale_(optimizer)
        gradients = [parameter.grad for parameter in parameters if parameter.grad is not None]
        if not gradients or any(not torch.isfinite(gradient).all() for gradient in gradients):
            raise RuntimeError(f"nonfinite gradient {condition} update={update}")
        optimizer_start = torch.cuda.Event(enable_timing=True)
        optimizer_end = torch.cuda.Event(enable_timing=True)
        optimizer_start.record(); before_scale = scaler.get_scale()
        scaler.step(optimizer); scaler.update(); optimizer_end.record(); torch.cuda.synchronize()
        if scaler.get_scale() < before_scale:
            skips += 1
            raise RuntimeError(f"GradScaler skipped authorized update {condition} {update}")
        wall = time.perf_counter() - step_started; total_wall += wall
        if update in (1, 25, 50, 100):
            telemetry.append({
                "optimizer_step": update, "losses": loss_sums,
                "step_seconds": wall, "examples_per_second": EFFECTIVE_BATCH / wall,
                "mask_index_selection_seconds": cpu_preparation,
                "forward_ms": forward_ms, "backward_ms": backward_ms,
                "optimizer_ms": optimizer_start.elapsed_time(optimizer_end),
                "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
                "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
                "gpu_utilization_percent": nvidia_utilization(),
            })
        if update in CHECKPOINTS[1:]:
            _, audit = evaluate_completed(
                model, causal, expression, factors, basis, bank, microbatch
            )
            checkpoints.append({"optimizer_step": update, **audit})
            print(
                f"{condition} step={update} R2={audit['factor_readout']['mean']:.4f} "
                f"loss={float(loss):.5f}", flush=True,
            )
    final_token = contextual_token_audit(model, expression, factors, microbatch)
    checkpoints[-1]["token_audit"] = final_token
    elapsed = time.perf_counter() - started
    return ({
        "condition": condition, "optimizer_updates": UPDATES,
        "checkpoints": checkpoints, "performance_telemetry": telemetry,
        "nonfinite_events": nonfinite, "gradscaler_skips": skips,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
        "training_seconds": elapsed, "mean_examples_per_second": UPDATES * EFFECTIVE_BATCH / elapsed,
        "cpu_preparation_seconds": cpu_preparation,
        "cpu_preparation_fraction": cpu_preparation / total_wall,
        "cpu_bottleneck": cpu_preparation / total_wall > .20,
        "accumulation_chunks": math.ceil(EFFECTIVE_BATCH / microbatch),
    }, model, causal)


def reference_audits(
    fixture: dict[str, Any],
    basis: WhitenedPCABasis,
    bank: MaskBank,
    linear: dict[str, torch.Tensor | float],
    device: torch.device,
) -> tuple[dict[str, Any], dict[str, torch.Tensor]]:
    expression = fixture["factual"][TRAIN:]
    counterfactual = fixture["counterfactual"][TRAIN:]
    factors = fixture["factors"][TRAIN:]
    factors_cf = fixture["factors_cf"][TRAIN:]
    views = 128 + torch.arange(len(expression), device=device) % 128
    _, visible, _, signatures, _, _ = block_tensors(
        expression - basis.mean, basis, bank, views
    )
    ordinary = basis.ordinary(expression)
    whitened = basis.transform(expression)
    linear_completed = linear_complete(linear, visible, signatures)
    outputs = {
        "raw_full_expression": expression,
        "pca160_full": ordinary,
        "whitened_pca160_full": whitened,
        "visible_only": visible,
        "linear_completion": linear_completed,
        "counterfactual_full_state": basis.transform(counterfactual),
    }
    report = {
        "raw_full_expression": factor_readout(expression, factors),
        "pca160_full": factor_readout(ordinary, factors),
        "whitened_pca160_full": factor_readout(whitened, factors),
        "visible_only": factor_readout(visible, factors),
        "linear_completion": factor_readout(linear_completed, factors),
        "counterfactual_full_state": factor_readout(basis.transform(counterfactual), factors_cf),
    }
    return report, outputs


def final_condition_states(
    models: dict[str, tuple[RLCModel, CausalAuxiliary | None]],
    fixture: dict[str, Any],
    basis: WhitenedPCABasis,
    bank: MaskBank,
    microbatch: int,
) -> dict[str, torch.Tensor]:
    expression, factors = readout_partition(fixture)
    output = {}
    for condition, (model, causal) in models.items():
        completed, _ = evaluate_completed(
            model, causal, expression, factors, basis, bank, microbatch
        )
        output[condition] = completed
    return output


def gene_reconstruction_rows(
    fixture: dict[str, Any],
    basis: WhitenedPCABasis,
    states: dict[str, torch.Tensor],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    truth = fixture["factual"][TRAIN + READOUT_FIT:]
    training_variance = fixture["factual"][:TRAIN].var(0, unbiased=False)
    predictions = {}
    for name, values in states.items():
        test = values[READOUT_FIT:]
        predictions[name] = basis.reconstruct(basis.inverse_whitening(test))
    rows = []
    for name, predicted in predictions.items():
        residual = (truth - predicted).square().sum(0)
        total = (truth - truth.mean(0, keepdim=True)).square().sum(0)
        r2 = torch.where(total > 0, 1.0 - residual / total, torch.nan)
        mae = (truth - predicted).abs().mean(0)
        for gene in range(GENES):
            rows.append({
                "representation": name, "gene_index": gene,
                "expression_r2": float(r2[gene]), "mae": float(mae[gene]),
                "training_variance": float(training_variance[gene]),
            })
    quartiles = torch.quantile(training_variance, torch.tensor([.25, .5, .75], device=truth.device))
    summaries = {}
    for name in predictions:
        subset = [row for row in rows if row["representation"] == name]
        r2 = torch.tensor([row["expression_r2"] for row in subset])
        mae = torch.tensor([row["mae"] for row in subset])
        summaries[name] = {"all_genes": {"r2": summarize(r2), "mae": summarize(mae)}}
        variance = training_variance.cpu()
        groups = {
            "variance_q1": variance <= quartiles[0].cpu(),
            "variance_q2": (variance > quartiles[0].cpu()) & (variance <= quartiles[1].cpu()),
            "variance_q3": (variance > quartiles[1].cpu()) & (variance <= quartiles[2].cpu()),
            "variance_q4": variance > quartiles[2].cpu(),
            "top_10_percent_variable": variance >= torch.quantile(variance, .90),
            "bottom_10_percent_nonzero_variance": (variance > 0) & (variance <= torch.quantile(variance[variance > 0], .10)),
        }
        for group, mask in groups.items():
            summaries[name][group] = {"r2": summarize(r2[mask]), "mae": summarize(mae[mask])}
    return rows, summaries


def fit_factor_map(values: torch.Tensor, factors: torch.Tensor) -> dict[str, torch.Tensor]:
    fit_values = values[:READOUT_FIT].float()
    fit_factors = factors[TRAIN:TRAIN + READOUT_FIT].float()
    mean = fit_values.mean(0, keepdim=True)
    std = fit_values.std(0, unbiased=False, keepdim=True).clamp_min(1e-8)
    y_mean = fit_factors.mean(0, keepdim=True)
    normalized = (fit_values - mean) / std
    identity = torch.eye(normalized.shape[1], device=values.device)
    weights = torch.linalg.solve(
        normalized.T @ normalized + 1e-3 * identity,
        normalized.T @ (fit_factors - y_mean),
    )
    return {"mean": mean, "std": std, "y_mean": y_mean, "weights": weights}


def apply_factor_map(mapping: dict[str, torch.Tensor], values: torch.Tensor) -> torch.Tensor:
    return ((values - mapping["mean"]) / mapping["std"]) @ mapping["weights"] + mapping["y_mean"]


def descendants(adjacency: torch.Tensor, node: int) -> set[int]:
    found = {node}
    frontier = [node]
    while frontier:
        source = frontier.pop()
        for target in torch.where(adjacency[source] != 0)[0].tolist():
            if target not in found:
                found.add(target); frontier.append(target)
    return found


def counterfactual_audit(
    models: dict[str, tuple[RLCModel, CausalAuxiliary | None]],
    fixture: dict[str, Any],
    basis: WhitenedPCABasis,
    bank: MaskBank,
    microbatch: int,
) -> dict[str, Any]:
    test = torch.arange(TRAIN + READOUT_FIT, CELLS, device=basis.mean.device)
    views = 128 + torch.arange(len(test), device=basis.mean.device) % 128
    factual = fixture["factual"][test]
    counterfactual = fixture["counterfactual"][test]
    true_delta = basis.transform(counterfactual) - basis.transform(factual)
    factor_mapping = fit_factor_map(basis.transform(fixture["factual"][TRAIN:]), fixture["factors"])
    report = {}
    for condition, (model, causal) in models.items():
        factual_parts, counterfactual_parts = [], []
        model.eval()
        if causal is not None: causal.eval()
        with torch.no_grad():
            for start in range(0, len(test), microbatch):
                end = min(start + microbatch, len(test))
                with torch.autocast("cuda", dtype=torch.float16):
                    factual_parts.append(model_forward(
                        model, causal, factual[start:end], factual[start:end] - basis.mean,
                        basis, bank, views[start:end],
                    )["completed"].float())
                    counterfactual_parts.append(model_forward(
                        model, causal, counterfactual[start:end], counterfactual[start:end] - basis.mean,
                        basis, bank, views[start:end],
                    )["completed"].float())
        predicted_delta = torch.cat(counterfactual_parts) - torch.cat(factual_parts)
        residual = (true_delta - predicted_delta).square().sum()
        total = (true_delta - true_delta.mean(0, keepdim=True)).square().sum().clamp_min(1e-12)
        coordinate_correlations = []
        for coordinate in range(WIDTH):
            first, second = predicted_delta[:, coordinate], true_delta[:, coordinate]
            coordinate_correlations.append(float(torch.corrcoef(torch.stack((first, second)))[0, 1]))
        predicted_factor_delta = (
            apply_factor_map(factor_mapping, torch.cat(counterfactual_parts))
            - apply_factor_map(factor_mapping, torch.cat(factual_parts))
        )
        true_factor_delta = fixture["factors_cf"][test] - fixture["factors"][test]
        affected_error, unaffected_error = [], []
        true_graph = fixture["true_adjacency"]
        for row, node in enumerate(fixture["intervention_node"][test].tolist()):
            affected = descendants(true_graph, node)
            unaffected = set(range(MECHANISMS)) - affected
            affected_error.extend((predicted_factor_delta[row, list(affected)] - true_factor_delta[row, list(affected)]).abs().tolist())
            unaffected_error.extend((predicted_factor_delta[row, list(unaffected)] - true_factor_delta[row, list(unaffected)]).abs().tolist())
        report[condition] = {
            "delta_r2": float(1.0 - residual / total),
            "cosine": summarize(F.cosine_similarity(predicted_delta, true_delta, dim=1)),
            "l2_error": summarize(torch.linalg.vector_norm(predicted_delta - true_delta, dim=1)),
            "per_coordinate_correlation": summarize(torch.tensor(coordinate_correlations)),
            "effect_norm_calibration_ratio": float(
                torch.linalg.vector_norm(predicted_delta, dim=1).mean()
                / torch.linalg.vector_norm(true_delta, dim=1).mean().clamp_min(1e-12)
            ),
            "affected_descendant_factor_mae": float(np.mean(affected_error)),
            "non_descendant_factor_mae": float(np.mean(unaffected_error)),
        }
    return report


def dag_audit(causal: CausalAuxiliary, true_graph: torch.Tensor) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    learned = causal.adjacency().detach().float().cpu()
    truth = (true_graph.detach().cpu() != 0)
    off = ~torch.eye(MECHANISMS, dtype=torch.bool)
    scores = learned.abs()[off].numpy()
    labels = truth[off].numpy().astype(int)
    auroc = float(roc_auc_score(labels, scores))
    auprc = float(average_precision_score(labels, scores))
    flat_indices = torch.nonzero(off, as_tuple=False)
    top = torch.topk(learned.abs()[off], 16).indices
    predicted = torch.zeros_like(truth)
    for index in top.tolist():
        source, target = flat_indices[index].tolist(); predicted[source, target] = True
    tp = int((predicted & truth).sum())
    precision = tp / 16; recall = tp / 16
    undirected_recovered = 0
    correct_direction = 0
    for source, target, _ in TRUE_EDGES:
        if predicted[source, target] or predicted[target, source]:
            undirected_recovered += 1
            correct_direction += int(predicted[source, target])
    rows = [{
        "source": source, "target": target,
        "learned_weight": float(learned[source, target]),
        "absolute_weight": float(abs(learned[source, target])),
        "true_edge": bool(truth[source, target]),
        "top16_learned_edge": bool(predicted[source, target]),
    } for source in range(MECHANISMS) for target in range(MECHANISMS) if source != target]
    return ({
        "acyclicity": float(causal.acyclicity().detach()),
        "mean_absolute_edge_weight": float(learned[off].abs().mean()),
        "edge_sparsity_fraction_below_1e-3": float((learned[off].abs() < 1e-3).float().mean()),
        "edge_ranking_auroc": auroc, "edge_ranking_auprc": auprc,
        "top16_precision": precision, "top16_recall": recall,
        "top16_f1": precision, "structural_hamming_distance": int((predicted ^ truth).sum()),
        "correct_direction_fraction_among_recovered_adjacencies": (
            correct_direction / undirected_recovered if undirected_recovered else None
        ),
        "encouraging_auroc_above_0_65": auroc > .65,
    }, rows)


def completion_metrics(
    references: dict[str, Any],
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    full = references["pca160_full"]
    visible = references["visible_only"]
    denominator = full["mean"] - visible["mean"]
    output = {}
    for run in runs:
        completed = run["checkpoints"][-1]["factor_readout"]
        fraction = (completed["mean"] - visible["mean"]) / denominator if denominator > .05 else None
        informative = np.asarray(full["per_factor_r2"]) >= .20
        improvement = np.asarray(completed["per_factor_r2"]) > np.asarray(visible["per_factor_r2"])
        output[run["condition"]] = {
            "completed_mean_r2": completed["mean"],
            "visible_mean_r2": visible["mean"], "full_mean_r2": full["mean"],
            "completion_fraction": fraction,
            "informative_factor_count": int(informative.sum()),
            "informative_factor_improvement_fraction": float(improvement[informative].mean()) if informative.any() else None,
        }
    return output


def classify(
    references: dict[str, Any],
    runs: list[dict[str, Any]],
    completion: dict[str, Any],
    counterfactual: dict[str, Any],
    dag: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    base = completion["RLC_BASE"]
    base_promising = (
        base["completed_mean_r2"] >= base["visible_mean_r2"] + .05
        and base["completion_fraction"] is not None and base["completion_fraction"] >= .20
        and base["informative_factor_improvement_fraction"] is not None
        and base["informative_factor_improvement_fraction"] >= .75
    )
    final = {run["condition"]: run["checkpoints"][-1]["factor_readout"]["mean"] for run in runs}
    linear_beats = references["linear_completion"]["mean"] >= max(final.values())
    token_pass = all(run["checkpoints"][-1]["token_audit"]["pass"] for run in runs)
    cf_helps = counterfactual["RLC_CF"]["delta_r2"] > counterfactual["RLC_BASE"]["delta_r2"]
    dag_helps = (
        counterfactual["RLC_CAUSAL_DAG"]["delta_r2"] > counterfactual["RLC_CF"]["delta_r2"]
        and final["RLC_CAUSAL_DAG"] >= final["RLC_CF"] - .02
        and dag["edge_ranking_auroc"] > .65
    )
    engineering = all(
        run["optimizer_updates"] == 100 and run["nonfinite_events"] == 0
        and run["gradscaler_skips"] == 0 for run in runs
    )
    if not engineering:
        classification = "ENGINEERING / NUMERICAL FAILURE"
    elif not token_pass:
        classification = "TOKEN-PRESERVING ENCODER REGRESSED"
    elif base_promising and dag_helps:
        classification = "RLC FEASIBLE - CAUSAL DAG AUXILIARY ADDS VALUE"
    elif base_promising and cf_helps:
        classification = "RLC FEASIBLE - COUNTERFACTUAL AUGMENTATION HELPS, DAG DOES NOT"
    elif base_promising:
        classification = "RLC FEASIBLE - CAUSAL AUXILIARIES NOT NEEDED"
    elif linear_beats:
        classification = "LINEAR COMPLETION MATCHES OR BEATS NEURAL RLC"
    else:
        classification = "RLC TARGET VALID BUT NEURAL COMPLETION FAILS"
    return classification, {
        "base_fast_completion_gate": base_promising,
        "linear_matches_or_beats_neural": linear_beats,
        "counterfactual_augmentation_improves_delta_r2": cf_helps,
        "causal_dag_adds_value": dag_helps,
        "contextual_token_gate": token_pass,
        "engineering_gate": engineering,
    }


def factor_rows(references: dict[str, Any], runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for representation, readout in references.items():
        for factor, value in enumerate(readout["per_factor_r2"]):
            rows.append({"condition": "REFERENCE", "optimizer_step": None,
                         "representation": representation, "factor_index": factor, "factor_r2": value})
    for run in runs:
        for checkpoint in run["checkpoints"]:
            for factor, value in enumerate(checkpoint["factor_readout"]["per_factor_r2"]):
                rows.append({"condition": run["condition"],
                             "optimizer_step": checkpoint["optimizer_step"],
                             "representation": "completed_state", "factor_index": factor,
                             "factor_r2": value})
    return rows


def append_documentation(project: Path, payload: dict[str, Any]) -> None:
    path = project / "docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md"
    heading = "## RLC-CD FAST FULL-VOCABULARY FEASIBILITY PROBE"
    if heading in path.read_text(encoding="utf-8"):
        return
    section = f"""

{heading}

The learned CELL-token IPB candidate was stopped after three completed trajectories because
the tokenizer and contextual gene tensor remained rich while the 160-dimensional learned
cell state and masked inference moved decisively away from the information-preservation
requirements. Its partial JSON remains frozen locally at SHA-256
`{IPB_PARTIAL_SHA256}` and is not treated as a completed qualification.

RLC-CD removed the CELL token, Perceiver slots, global teacher matching, and learned pooling.
It retained the frozen tokenizer and six-layer token-preserving linear-attention encoder,
while defining the cell state in a factual-TRAIN-fitted 160-dimensional whitened PCA system.
The visible molecular contribution entered exactly; the neural predictor estimated only four
missing block contributions. A TRAIN-only ridge completion baseline was evaluated on unseen
mask-bank views. The target decomposition passed={payload['target_audit']['pass']} with
maximum absolute error {payload['target_audit']['maximum_absolute_reconstruction_error']:.3g}.

Exactly three matched 100-update synthetic conditions were run: base residual completion,
paired counterfactual completion, and paired completion with a learned 12-node acyclic latent
mechanism auxiliary. The true generator DAG and factor labels were evaluation-only. No real
RNA, pathology, EMA, production weights, checkpoint selection, seed selection, or parameter
sweep was used.

The visible-only, linear, three neural, per-factor, per-gene, intervention-delta, learned-DAG,
token-retention, numerical, GPU-memory, and CPU-preparation results are recorded in
`results/v4/stage81a3_rlc_causal_fast_probe.json` and its compact CSV companions.
Final bounded classification: **{payload['classification']}**. The no-automatic-follow-up hard
stop remains active pending human review.
"""
    atomic_text(path, path.read_text(encoding="utf-8") + section)


def main() -> int:
    args = parse_args()
    project = args.project_dir.resolve(); os.chdir(project)
    if not torch.cuda.is_available(): raise RuntimeError("Locked CUDA runtime is required")
    if OUTPUT_JSON.exists() and not args.overwrite:
        raise RuntimeError(f"Output exists: {OUTPUT_JSON}")
    partial = project / "results/v4/stage81a3_ipb_jepa_feasibility.json"
    if file_hash(partial) != IPB_PARTIAL_SHA256:
        raise RuntimeError("Stopped IPB partial evidence hash changed")
    device = torch.device("cuda")
    torch.set_float32_matmul_precision("high")
    torch.backends.cuda.matmul.allow_tf32 = True
    timings: dict[str, float] = {}

    fixture = causal_fixture(device)
    timings["synthetic_generation_seconds"] = fixture["metadata"]["generation_seconds"]
    started = time.perf_counter()
    basis = fit_whitened_pca_gram(fixture["factual"][:TRAIN], components=WIDTH, epsilon=1e-6)
    timings["pca_seconds"] = time.perf_counter() - started
    started = time.perf_counter()
    neighbors, weights = gpu_topk_absolute_correlation(fixture["factual"][:TRAIN], top_k=8)
    timings["correlation_topk_seconds"] = time.perf_counter() - started
    started = time.perf_counter()
    bank = build_mask_bank(neighbors, weights, views=MASK_VIEWS, genes=GENES,
                           hidden_count=HIDDEN, blocks=BLOCKS, seed=SEED).to(device)
    timings["mask_bank_seconds"] = time.perf_counter() - started
    del neighbors, weights
    torch.cuda.empty_cache()

    audit = target_audit(fixture["factual"], basis, bank, device)
    payload: dict[str, Any] = {
        "stage": "Stage81A3_RLC_CD_fast_full_vocabulary_probe",
        "anchor": ANCHOR,
        "stopped_ipb_partial": {"sha256": IPB_PARTIAL_SHA256, "completed_runs": 3,
                                "preserved": True, "final_classification_valid": False},
        "target_audit": audit, "timings": timings, "runs": [],
        "stage81a3_complete": False, "stage81b_started": False,
    }
    if not audit["pass"] or audit["prior_pathological_cosine_reproduced"]:
        payload["classification"] = "RLC TARGET AUDIT FAILS"
        atomic_json(OUTPUT_JSON, payload)
        print("RLC TARGET AUDIT FAILS", flush=True)
        return 0

    started = time.perf_counter()
    linear = fit_linear_completion(fixture["factual"], basis, bank, device)
    timings["linear_baseline_fit_seconds"] = time.perf_counter() - started
    references, reference_states = reference_audits(fixture, basis, bank, linear, device)
    microbatch, memory_rows = memory_probe(fixture, basis, bank, device)
    initial_model, _ = initialize_models("RLC_BASE", device)
    expression, factors = readout_partition(fixture)
    initial_token = contextual_token_audit(initial_model, expression, factors, microbatch)
    del initial_model
    schedule = fixed_batch_schedule(device)
    models = {}
    for condition in CONDITIONS:
        print(f"starting {condition} (trajectory {len(payload['runs']) + 1}/3)", flush=True)
        run, model, causal = train_condition(
            condition, fixture, basis, bank, schedule, microbatch, initial_token, device
        )
        payload["runs"].append(run); models[condition] = (model, causal)
        atomic_json(OUTPUT_JSON, payload)

    final_states = final_condition_states(models, fixture, basis, bank, microbatch)
    completion = completion_metrics(references, payload["runs"])
    states_for_genes = {
        "visible_only": reference_states["visible_only"],
        "linear_completion": reference_states["linear_completion"],
        "full_pca160": reference_states["whitened_pca160_full"],
        **final_states,
    }
    started = time.perf_counter()
    gene_rows, gene_summary = gene_reconstruction_rows(fixture, basis, states_for_genes)
    counterfactual = counterfactual_audit(models, fixture, basis, bank, microbatch)
    dag, dag_rows = dag_audit(models["RLC_CAUSAL_DAG"][1], fixture["true_adjacency"])
    timings["final_readouts_seconds"] = time.perf_counter() - started
    classification, gates = classify(references, payload["runs"], completion, counterfactual, dag)
    utilizations = [row["gpu_utilization_percent"] for run in payload["runs"]
                    for row in run["performance_telemetry"] if row["gpu_utilization_percent"] is not None]
    payload.update({
        "reference_information": references,
        "linear_baseline": {"alpha": 1e-3, "train_mask_views": [0, 127],
                            "evaluation_mask_views": [128, 255]},
        "memory_probe": memory_rows, "selected_microbatch": microbatch,
        "effective_batch": EFFECTIVE_BATCH,
        "completion": completion, "gene_reconstruction_summary": gene_summary,
        "counterfactual_evaluation": counterfactual, "learned_dag_evaluation": dag,
        "scientific_gates": gates, "classification": classification,
        "mean_training_gpu_utilization_percent": float(np.mean(utilizations)) if utilizations else None,
        "optimizer_updates": sum(run["optimizer_updates"] for run in payload["runs"]),
        "safety": {"real_rna_optimizer_steps": 0, "real_rna_ema_updates": 0,
                   "real_rna_backward_calls": 0, "pathology_opened": False,
                   "true_causal_dag_used_for_training": False,
                   "true_causal_dag_used_for_evaluation": True,
                   "factor_labels_used_for_model_training": False,
                   "cell_token_used": False, "perceiver_used": False,
                   "visible_latent_contribution_hard_preserved": True,
                   "masks_precomputed_before_training": True,
                   "full_correlation_matrix_retained_during_training": False,
                   "hyperparameter_sweep": False},
    })
    write_csv(OUTPUT_CONDITIONS, [{
        "condition": run["condition"], "optimizer_updates": run["optimizer_updates"],
        "final_mean_factor_r2": run["checkpoints"][-1]["factor_readout"]["mean"],
        "completion_fraction": completion[run["condition"]]["completion_fraction"],
        "counterfactual_delta_r2": counterfactual[run["condition"]]["delta_r2"],
        "training_seconds": run["training_seconds"],
        "peak_allocated_bytes": run["peak_allocated_bytes"],
        "peak_reserved_bytes": run["peak_reserved_bytes"],
    } for run in payload["runs"]])
    write_csv(OUTPUT_FACTORS, factor_rows(references, payload["runs"]))
    write_csv(OUTPUT_GENES, gene_rows)
    write_csv(OUTPUT_DAG, dag_rows)
    atomic_json(OUTPUT_JSON, payload)
    append_documentation(project, payload)
    print(json.dumps({
        "classification": classification, "trajectories": len(payload["runs"]),
        "optimizer_updates": payload["optimizer_updates"],
        "microbatch": microbatch, "pathology_opened": False,
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
