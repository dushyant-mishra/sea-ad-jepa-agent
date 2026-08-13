#!/usr/bin/env python3
"""Run the one authorized 150-update synthetic RBB-JEPA feasibility probe."""

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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v4.belief_geometry import covariance, marginal_shape  # noqa: E402
from sea_ad_jepa.v4.conditional_predictability import (  # noqa: E402
    _graph_hidden,
    build_fixture,
    r2_columns,
    ridge_fit,
    ridge_predict,
    topk_absolute_correlation,
)
from sea_ad_jepa.v4.masking import keyed_mask_seed  # noqa: E402
from sea_ad_jepa.v4.oof_covariance import construct_lrd  # noqa: E402
from sea_ad_jepa.v4.rbb_adaptive import (  # noqa: E402
    R_MAX,
    RBBAdaptiveBelief,
    dense_covariance,
    fuse_gaussian_beliefs,
    mask_context_features,
    nested_visibility_masks,
    random_mask_bank,
    rbb_nll,
    structured_gaussian_terms,
)
from sea_ad_jepa.v4.reproducible_state import ReproducibleBasis  # noqa: E402


ANCHOR = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
SEED = 8114001
CELLS, GENES, FACTORS = 4096, 4096, 32
TRAIN, VALIDATION, SEALED = 3072, 512, 512
WIDTH, HIDDEN, VISIBLE = 160, 1638, 2458
UPDATES, EFFECTIVE_BATCH = 150, 256
TELEMETRY_STEPS = (0, 25, 50, 100, 150)
FAMILIES = ("RANDOM_40", "COEXPRESSION_BLOCK_40")
MEMORY_CANDIDATES = (64, 48, 40, 32, 24, 16, 8)
MAX_ALLOCATED_GB = 13.0
BASIS_HASH = "ea07915a043ed8b8c3e38fe56ba2e3b9095bf4f0db3804773ae9394f3fbeab9c"
EXPECTED_HASHES = {
    "results/v4/stage81a3_ipb_jepa_feasibility.json": "aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308",
    "results/v4/stage81a3_rlc_causal_fast_probe.json": "ac3e8a69964bfa11f5d8211f373e20c6476534095850dc48e8851ea9b42ab8fc",
    "results/v4/stage81a3_conditional_predictability_audit.json": "fae778621cbec948c0a238998d2683aae09be680b1c96f7ed4f2b6b8cc7ed6f5",
    "results/v4/stage81a3_reproducible_state_basis.pt": BASIS_HASH,
    "results/v4/stage81a3_rbb_belief_geometry_audit.json": "9e3986ec12767e8d04acdb9ac921c88a4f288ca20b3c4da4abf24fcdbe444b59",
    "results/v4/stage81a3_rbb_oof_covariance_audit.json": "7a5042125860f2c598a28038f41fa3211074bf21d9e204dc6386b5246982a87f",
    "results/v4/stage81a3_rbb_validation_covariance_audit.json": "03d0e36d405150851753be333067ee553d17e847fce50a2d983b83f0b4777239",
}
OUTPUTS = {
    "json": Path("results/v4/stage81a3_rbb_adaptive_correlated_probe.json"),
    "factors": Path("results/v4/stage81a3_rbb_adaptive_factors.csv"),
    "calibration": Path("results/v4/stage81a3_rbb_adaptive_calibration.csv"),
    "activity": Path("results/v4/stage81a3_rbb_adaptive_correlated_activity.csv"),
    "counterfactual": Path("results/v4/stage81a3_rbb_adaptive_counterfactual.csv"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    return parser.parse_args()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def atomic_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = sorted({key for row in rows for key in row})
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader(); writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def summarize(values: torch.Tensor) -> dict[str, float]:
    values = values.detach().double().flatten().cpu()
    return {
        "mean": float(values.mean()), "median": float(values.median()),
        "p05": float(torch.quantile(values, .05)), "p90": float(torch.quantile(values, .90)),
        "p95": float(torch.quantile(values, .95)), "p99": float(torch.quantile(values, .99)),
        "minimum": float(values.min()), "maximum": float(values.max()),
    }


def load_basis(device: torch.device) -> ReproducibleBasis:
    payload = torch.load(OUTPUTS["json"].parent / "stage81a3_reproducible_state_basis.pt", map_location=device, weights_only=False)
    if payload["anchor"] != ANCHOR or int(payload["seed"]) != SEED:
        raise RuntimeError("RepPCA provenance mismatch")
    return ReproducibleBasis(payload["mean"], payload["vectors"], payload["eigenvalues"], payload["epsilon"])


def frozen_family_statistics(device: torch.device) -> dict[str, dict[str, torch.Tensor | float]]:
    payload = torch.load(
        "results/v4/stage81a3_rbb_covariance_matrices.pt", map_location="cpu", weights_only=False
    )
    if payload["anchor"] != ANCHOR or payload["basis_sha256"] != BASIS_HASH:
        raise RuntimeError("frozen covariance provenance mismatch")
    result = {}
    for family in FAMILIES:
        priors = [payload["matrices"][f"{family}__{view}__prior"] for view in range(4)]
        noises = [payload["matrices"][f"{family}__{view}__noise"] for view in range(4)]
        prior = torch.stack(priors).mean(0)
        lrd = construct_lrd(prior, R_MAX)
        noise_diagonal = torch.stack([torch.diag(value) for value in noises]).mean(0).clamp_min(1e-6)
        u = lrd["u"].float().to(device)
        diagonal = lrd["diagonal"].float().to(device)
        matrix = torch.diag(diagonal) + u @ u.T
        offdiag = matrix - torch.diag(torch.diag(matrix))
        result[family] = {
            "prior_diagonal": diagonal,
            "prior_low_rank": u,
            "prior_marginal": torch.diag(matrix),
            "noise_diagonal": noise_diagonal.float().to(device),
            "prior_correlated_energy": float(offdiag.square().sum()),
            "prior_lrd_floor": float(lrd["floor"]),
            "prior_lrd_floor_count": int(lrd["floor_count"]),
        }
    return result


def block_mask_bank(
    neighbors: torch.Tensor,
    weights: torch.Tensor,
    *,
    views: int = 128,
) -> torch.Tensor:
    rows = []
    for view in range(views):
        seed = keyed_mask_seed(production_seed=SEED, cell_index=1, sample_pass=0, view_index=view)
        hidden, _ = _graph_hidden(neighbors, weights, GENES, HIDDEN, seed)
        rows.append(hidden)
    result = torch.stack(rows)
    if not torch.all(result.sum(1) == HIDDEN):
        raise RuntimeError("block mask bank violated exact hidden count")
    return result


def initialization_biases(
    priors: dict[str, dict[str, torch.Tensor | float]],
) -> tuple[float, float, dict[str, float]]:
    marginal = torch.cat([priors[name]["prior_marginal"].float() for name in FAMILIES])
    tau = 0.10 / (VISIBLE * float(marginal.median()))
    precision_bias = math.log(math.expm1(tau))
    generator = torch.Generator().manual_seed(SEED + 919)
    directions = torch.linalg.qr(torch.randn(WIDTH, R_MAX, generator=generator), mode="reduced").Q
    unit_covariance = directions @ directions.T
    unit_covariance.fill_diagonal_(0)
    unit_energy = float(unit_covariance.square().sum())
    target_energy = 0.10 * min(float(priors[name]["prior_correlated_energy"]) for name in FAMILIES)
    amplitude = max((target_energy / max(unit_energy, 1e-30)) ** .25, 1e-6)
    correlation_bias = math.log(math.expm1(amplitude))
    return precision_bias, correlation_bias, {
        "softplus_diagonal_precision_per_gene": tau,
        "diagonal_precision_bias": precision_bias,
        "initial_correlated_amplitude": amplitude,
        "correlated_amplitude_bias": correlation_bias,
        "target_correlated_energy": target_energy,
    }


def mask_context(
    basis: ReproducibleBasis,
    hidden: torch.Tensor,
    prior: dict[str, torch.Tensor | float],
    batch: int,
) -> torch.Tensor:
    value = mask_context_features(
        basis.analysis, hidden, prior["prior_diagonal"], prior["prior_low_rank"]
    )
    return value[None].expand(batch, -1)


def make_microbatch(
    fixture: Any,
    basis: ReproducibleBasis,
    indices: torch.Tensor,
    directions: torch.Tensor,
    hidden: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    source_a = directions == 0
    expression = torch.where(source_a[:, None], fixture.x_a[indices], fixture.x_b[indices])
    target_source = torch.where(source_a[:, None], fixture.x_b[indices], fixture.x_a[indices])
    visible = ~hidden
    visible_state = basis.contribution(expression, visible)
    target = basis.contribution(target_source, hidden)
    return expression, visible_state, target


def batch_schedule(microbatch: int) -> list[int]:
    full, remainder = divmod(EFFECTIVE_BATCH, microbatch)
    schedule = [microbatch] * full + ([remainder] if remainder else [])
    if any(size % 2 for size in schedule) or sum(schedule) != EFFECTIVE_BATCH:
        raise RuntimeError("microbatch schedule cannot preserve symmetric directions")
    return schedule


def probe_memory(
    model: RBBAdaptiveBelief,
    fixture: Any,
    basis: ReproducibleBasis,
    hidden: torch.Tensor,
    prior: dict[str, torch.Tensor | float],
    device: torch.device,
) -> tuple[int, list[dict[str, Any]]]:
    cpu_state, cuda_state = torch.random.get_rng_state(), torch.cuda.get_rng_state(device)
    reports = []
    selected = None
    for candidate in MEMORY_CANDIDATES:
        torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(device); model.zero_grad(set_to_none=True)
        status, error = "pass", None
        expression = visible_state = target = None
        try:
            indices = torch.arange(candidate, device=device) % TRAIN
            directions = torch.arange(candidate, device=device) % 2
            expression, visible_state, target = make_microbatch(fixture, basis, indices, directions, hidden)
            visible = (~hidden)[None].expand(candidate, -1)
            ids = torch.arange(GENES, device=device)[None].expand(candidate, -1)
            with torch.autocast("cuda", dtype=torch.float16):
                output = model(
                    ids, expression, visible, visible_state,
                    mask_context(basis, hidden, prior, candidate),
                    prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"],
                )
                loss = rbb_nll(output, target)
            loss.backward()
            if not torch.isfinite(loss):
                raise FloatingPointError("nonfinite probe loss")
        except torch.cuda.OutOfMemoryError as exc:
            status, error = "oom", str(exc)
        allocated = torch.cuda.max_memory_allocated(device) / 2**30
        reserved = torch.cuda.max_memory_reserved(device) / 2**30
        if status == "pass" and allocated > MAX_ALLOCATED_GB:
            status = "over_limit"
        reports.append({
            "microbatch": candidate, "status": status, "peak_allocated_gb": allocated,
            "peak_reserved_gb": reserved, "error": error,
        })
        model.zero_grad(set_to_none=True)
        del expression, visible_state, target
        torch.cuda.empty_cache()
        if status == "pass":
            selected = candidate; break
    torch.random.set_rng_state(cpu_state); torch.cuda.set_rng_state(cuda_state, device)
    if selected is None:
        raise RuntimeError("no memory-probe microbatch satisfied the 13 GiB contract")
    return selected, reports


def kernel_readout(train_kernel: torch.Tensor, cross_kernel: torch.Tensor, train_y: torch.Tensor, test_y: torch.Tensor) -> dict[str, Any]:
    y_mean = train_y.double().mean(0, keepdim=True)
    weights = torch.linalg.solve(
        train_kernel + 1e-3 * torch.eye(len(train_kernel), dtype=torch.float64),
        train_y.double() - y_mean,
    )
    prediction = cross_kernel @ weights + y_mean
    scores = r2_columns(test_y.double(), prediction)
    return {"mean_r2": float(scores.mean()), "median_r2": float(scores.median()), "per_factor_r2": [float(x) for x in scores]}


def token_information(
    model: RBBAdaptiveBelief,
    fixture: Any,
    microbatch: int,
    device: torch.device,
) -> dict[str, Any]:
    train_idx = torch.arange(256, device=device)
    eval_idx = torch.arange(CELLS - 256, CELLS, device=device)
    indices = torch.cat((train_idx, eval_idx))
    with tempfile.TemporaryDirectory(prefix="stage81a3-rbb-token-") as directory:
        shape = (512, GENES, WIDTH)
        tokenizer_map = np.memmap(Path(directory) / "tokenizer.bin", dtype=np.float16, mode="w+", shape=shape)
        contextual_map = np.memmap(Path(directory) / "contextual.bin", dtype=np.float16, mode="w+", shape=shape)
        model.eval()
        with torch.no_grad():
            for start in range(0, len(indices), microbatch):
                selected = indices[start:start + microbatch]
                values = fixture.x_a[selected]
                ids = torch.arange(GENES, device=device)[None].expand(len(selected), -1)
                visible = torch.ones(len(selected), GENES, dtype=torch.bool, device=device)
                with torch.autocast("cuda", dtype=torch.float16):
                    tokens = model.ledger.tokenizer(ids, values)
                    contextual, _ = model.ledger(ids, values, visible)
                tokenizer_map[start:start + len(selected)] = tokens.float().cpu().numpy().astype(np.float16)
                contextual_map[start:start + len(selected)] = contextual.float().cpu().numpy().astype(np.float16)
        results = {}
        for name, memory in (("tokenizer", tokenizer_map), ("contextual", contextual_map)):
            train_kernel = torch.zeros(256, 256, dtype=torch.float64)
            cross_kernel = torch.zeros(256, 256, dtype=torch.float64)
            for gene_start in range(0, GENES, 64):
                chunk = torch.from_numpy(np.asarray(memory[:, gene_start:gene_start + 64], dtype=np.float32)).reshape(512, -1)
                train = chunk[:256]; evaluation = chunk[256:]
                mean = train.mean(0, keepdim=True); train = train - mean; evaluation = evaluation - mean
                train_kernel += (train @ train.T).double(); cross_kernel += (evaluation @ train.T).double()
            results[name] = kernel_readout(train_kernel, cross_kernel, fixture.factors[train_idx].cpu(), fixture.factors[eval_idx].cpu())
        results["retention_ratio"] = results["contextual"]["mean_r2"] / max(results["tokenizer"]["mean_r2"], 1e-12)
        tokenizer_map.flush(); contextual_map.flush()
        del chunk, train, evaluation, memory
        tokenizer_map._mmap.close(); contextual_map._mmap.close()
        del tokenizer_map, contextual_map
        return results


def representation_readout(validation: torch.Tensor, sealed: torch.Tensor, factors: torch.Tensor) -> dict[str, Any]:
    model = ridge_fit(validation, factors[TRAIN:TRAIN + VALIDATION].repeat(len(validation) // VALIDATION, 1), 1e-3)
    truth = factors[-SEALED:].repeat(len(sealed) // SEALED, 1)
    scores = r2_columns(truth, ridge_predict(model, sealed))
    return {"mean": float(scores.mean()), "median": float(scores.median()), "per_factor": [float(x) for x in scores]}


def effective_rank(low_rank: torch.Tensor) -> torch.Tensor:
    values = low_rank.square().sum(1).clamp_min(1e-30)
    probabilities = values / values.sum(1, keepdim=True).clamp_min(1e-30)
    return torch.exp(-(probabilities * probabilities.log()).sum(1))


def marginal_calibration(residual: torch.Tensor, marginal_variance: torch.Tensor) -> dict[str, float]:
    standardized = residual / marginal_variance.sqrt().clamp_min(1e-8)
    return {
        "standardized_variance": float(standardized.var(0, unbiased=False).mean()),
        "coverage_1sigma": float((standardized.abs() <= 1).float().mean()),
        "coverage_1_96sigma": float((standardized.abs() <= 1.96).float().mean()),
        "mse_to_predicted_variance": float(residual.square().mean() / marginal_variance.mean()),
    }


def gaussianity(residual: torch.Tensor, marginal_variance: torch.Tensor) -> dict[str, Any]:
    z = residual / marginal_variance.sqrt().clamp_min(1e-8)
    centered = z - z.mean(0)
    scale = centered.std(0, unbiased=False).clamp_min(1e-8)
    skew = (centered / scale).pow(3).mean(0)
    kurtosis = (centered / scale).pow(4).mean(0) - 3
    severe = (skew.abs() > 1) | (kurtosis > 3)
    return {"skewness": summarize(skew), "excess_kurtosis": summarize(kurtosis), "severe_fraction": float(severe.float().mean())}


def spearman(x: torch.Tensor, y: torch.Tensor) -> float:
    def ranks(values: torch.Tensor) -> torch.Tensor:
        return torch.argsort(torch.argsort(values)).float()
    return float(torch.corrcoef(torch.stack((ranks(x.flatten()), ranks(y.flatten()))))[0, 1])


def evaluate_mask(
    model: RBBAdaptiveBelief,
    fixture: Any,
    basis: ReproducibleBasis,
    hidden: torch.Tensor,
    prior: dict[str, torch.Tensor | float],
    microbatch: int,
    device: torch.device,
) -> dict[str, Any]:
    indices = torch.arange(TRAIN, CELLS, device=device)
    collected: dict[str, list[torch.Tensor]] = {name: [] for name in (
        "target", "visible", "raw", "belief", "diagonalized", "full_nll", "diag_nll", "prior_nll",
        "full_mahal", "diag_mahal", "trace", "logdet", "marginal", "amplitudes", "corr_energy",
        "effective_rank", "squared_error", "belief_a", "belief_b",
    )}
    model.eval()
    with torch.no_grad():
        for direction in (0, 1):
            direction_beliefs = []
            for start in range(0, len(indices), microbatch):
                selected = indices[start:start + microbatch]
                directions = torch.full((len(selected),), direction, dtype=torch.long, device=device)
                expression, visible_state, target = make_microbatch(fixture, basis, selected, directions, hidden)
                visible = (~hidden)[None].expand(len(selected), -1)
                ids = torch.arange(GENES, device=device)[None].expand(len(selected), -1)
                with torch.autocast("cuda", dtype=torch.float16):
                    output = model(ids, expression, visible, visible_state, mask_context(basis, hidden, prior, len(selected)), prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"])
                diagonal_mean, diagonal_d, diagonal_u = fuse_gaussian_beliefs(
                    output.evidence_mean, prior["prior_diagonal"], prior["prior_low_rank"],
                    output.evidence_diagonal, torch.zeros_like(output.evidence_low_rank),
                )
                full_residual = target - output.posterior_missing_mean
                diagonal_residual = target - diagonal_mean
                full_nll, full_mahal, logdet = structured_gaussian_terms(full_residual, output.total_diagonal, output.total_low_rank)
                diagonal_total_d = diagonal_d + prior["noise_diagonal"]
                diag_nll, diag_mahal, _ = structured_gaussian_terms(diagonal_residual, diagonal_total_d, diagonal_u)
                prior_nll, _, _ = structured_gaussian_terms(target, (prior["prior_diagonal"] + prior["noise_diagonal"])[None].expand(len(target), -1), prior["prior_low_rank"][None].expand(len(target), -1, -1))
                marginal = output.total_diagonal + output.total_low_rank.square().sum(-1)
                corr_matrix = output.evidence_low_rank @ output.evidence_low_rank.transpose(-1, -2)
                corr_matrix = corr_matrix - torch.diag_embed(torch.diagonal(corr_matrix, dim1=-2, dim2=-1))
                values = {
                    "target": target, "visible": visible_state,
                    "raw": visible_state + output.evidence_mean, "belief": output.belief_mean,
                    "diagonalized": visible_state + diagonal_mean,
                    "full_nll": full_nll / WIDTH, "diag_nll": diag_nll / WIDTH, "prior_nll": prior_nll / WIDTH,
                    "full_mahal": full_mahal, "diag_mahal": diag_mahal,
                    "trace": marginal.sum(-1), "logdet": logdet, "marginal": marginal,
                    "amplitudes": output.correlated_activation_amplitudes,
                    "corr_energy": corr_matrix.square().sum((-1, -2)),
                    "effective_rank": effective_rank(output.evidence_low_rank),
                    "squared_error": full_residual.square().sum(-1),
                }
                for name, value in values.items(): collected[name].append(value.float().cpu())
                direction_beliefs.append(output.belief_mean.float().cpu())
            collected["belief_a" if direction == 0 else "belief_b"].append(torch.cat(direction_beliefs))
    return {name: torch.cat(parts) for name, parts in collected.items() if parts}


def telemetry_point(model: RBBAdaptiveBelief, fixture: Any, basis: ReproducibleBasis, hidden: torch.Tensor, prior: dict[str, Any], device: torch.device) -> dict[str, float]:
    model.eval()
    with torch.no_grad():
        indices = torch.arange(TRAIN, TRAIN + 32, device=device); directions = torch.arange(32, device=device) % 2
        expression, visible_state, target = make_microbatch(fixture, basis, indices, directions, hidden)
        visible = (~hidden)[None].expand(32, -1); ids = torch.arange(GENES, device=device)[None].expand(32, -1)
        with torch.autocast("cuda", dtype=torch.float16):
            output = model(ids, expression, visible, visible_state, mask_context(basis, hidden, prior, 32), prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"])
            loss = rbb_nll(output, target)
    model.train()
    return {"nll_per_dimension": float(loss), "mean_amplitude": float(output.correlated_activation_amplitudes.mean()), "mean_trace": float((output.total_diagonal + output.total_low_rank.square().sum(-1)).sum(-1).mean())}


def train_model(model: RBBAdaptiveBelief, fixture: Any, basis: ReproducibleBasis, banks: dict[str, torch.Tensor], priors: dict[str, Any], microbatch: int, device: torch.device) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=.01)
    scaler = torch.amp.GradScaler("cuda")
    generator = torch.Generator().manual_seed(SEED + 4242)
    schedule = batch_schedule(microbatch)
    telemetry = [{
        "update": 0,
        "family": FAMILIES[0],
        **telemetry_point(
            model, fixture, basis, banks[FAMILIES[0]][0].to(device), priors[FAMILIES[0]], device
        ),
    }]
    started = time.perf_counter(); examples = 0; nonfinite = 0
    torch.cuda.reset_peak_memory_stats(device)
    for update in range(1, UPDATES + 1):
        family = FAMILIES[(update - 1) % 2]
        hidden = banks[family][((update - 1) // 2) % 128].to(device)
        prior = priors[family]
        selected = torch.randint(TRAIN, (EFFECTIVE_BATCH,), generator=generator).to(device)
        directions = torch.arange(EFFECTIVE_BATCH, device=device) % 2
        optimizer.zero_grad(set_to_none=True)
        cursor, update_loss = 0, 0.0
        for size in schedule:
            idx, direction = selected[cursor:cursor + size], directions[cursor:cursor + size]
            cursor += size
            expression, visible_state, target = make_microbatch(fixture, basis, idx, direction, hidden)
            visible = (~hidden)[None].expand(size, -1); ids = torch.arange(GENES, device=device)[None].expand(size, -1)
            with torch.autocast("cuda", dtype=torch.float16):
                output = model(ids, expression, visible, visible_state, mask_context(basis, hidden, prior, size), prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"])
                loss = rbb_nll(output, target) * (size / EFFECTIVE_BATCH)
            if not torch.isfinite(loss):
                nonfinite += 1; raise FloatingPointError(f"nonfinite loss at update {update}")
            scaler.scale(loss).backward(); update_loss += float(loss.detach())
        scaler.step(optimizer); scaler.update(); examples += EFFECTIVE_BATCH
        if update in TELEMETRY_STEPS:
            point = telemetry_point(model, fixture, basis, hidden, prior, device)
            telemetry.append({"update": update, "family": family, "training_nll": update_loss, **point})
            print(f"update={update} family={family} nll={point['nll_per_dimension']:.6f}", flush=True)
    elapsed = time.perf_counter() - started
    return telemetry, {
        "updates": UPDATES, "examples": examples, "wall_seconds": elapsed,
        "examples_per_second": examples / elapsed, "seconds_per_update": elapsed / UPDATES,
        "peak_allocated_gb": torch.cuda.max_memory_allocated(device) / 2**30,
        "peak_reserved_gb": torch.cuda.max_memory_reserved(device) / 2**30,
        "nonfinite_events": nonfinite, "microbatch": microbatch,
        "accumulation_microbatches": schedule, "effective_batch": EFFECTIVE_BATCH,
    }


def append_readout(payload: dict[str, Any]) -> None:
    path = Path("docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md")
    marker = "## RBB-JEPA Adaptive Correlated Belief Feasibility"
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Stage81A3 Calibration and Synthetic Mechanics Readout\n"
    if marker in existing:
        raise RuntimeError("RBB feasibility readout already exists; continuation/rerun is forbidden")
    section = f"""

{marker}

One synthetic model (seed `{SEED}`) received exactly `{UPDATES}` optimizer updates. The visible
molecular state was factual and hard-preserved; only the missing RepPCA contribution was inferred
probabilistically. Conditional and measurement uncertainty remained separate, and coordinated
uncertainty used context-adaptive rank-{R_MAX} capacity. Random missingness was allowed to remain
approximately diagonal, while coherent missingness could activate shared uncertainty. The full
4,096 x 160 gene-token molecular evidence ledger remained available. Correlated directions are
not called pathways, exact missing expression was not a target, and no real RNA or pathology was
accessed.

Primary classification: **{payload['classification']}**.

Token retention passed: `{payload['gates']['token_retention_pass']}`. No-harm passed for both mask
families: `{payload['gates']['no_harm_pass']}`. Proper-score comparison against prior-only passed:
`{payload['gates']['proper_score_pass']}`. Joint calibration passed: `{payload['gates']['joint_calibration_pass']}`.

This is one bounded synthetic feasibility result, not biological validation, not Stage81A3
completion, and not authorization for Stage81B or real-data training.
"""
    atomic_text(path, existing.rstrip() + section + "\n")


def main() -> int:
    args = parse_args(); os.chdir(args.project_dir.resolve())
    if not torch.cuda.is_available(): raise RuntimeError("locked CUDA runtime required")
    if any(path.exists() for path in OUTPUTS.values()):
        raise RuntimeError("RBB probe output already exists; rerun/continuation is forbidden")
    actual_hashes = {path: file_hash(Path(path)) for path in EXPECTED_HASHES}
    if actual_hashes != EXPECTED_HASHES: raise RuntimeError("prior evidence hash changed")
    validation = json.loads(Path("results/v4/stage81a3_rbb_validation_covariance_audit.json").read_text())
    if validation["classification"] != "CORRELATED GAUSSIAN SUPPORTED, BUT RANK-9 LRD UNDEREXPRESSIVE":
        raise RuntimeError("validation covariance classification changed")
    device = torch.device("cuda"); torch.set_float32_matmul_precision("high")
    torch.backends.cuda.matmul.allow_tf32 = True; torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    total_started = time.perf_counter(); preparation_started = time.perf_counter()
    basis = load_basis(device); fixture = build_fixture(device)
    priors = frozen_family_statistics(device)
    weights, neighbors = topk_absolute_correlation(.5 * (fixture.x_a[:TRAIN] + fixture.x_b[:TRAIN]), 8)
    banks = {
        "RANDOM_40": random_mask_bank().pin_memory(),
        "COEXPRESSION_BLOCK_40": block_mask_bank(neighbors, weights).pin_memory(),
    }
    mask_hashes = {name: hashlib.sha256(bank.numpy().tobytes()).hexdigest() for name, bank in banks.items()}
    precision_bias, correlation_bias, initialization = initialization_biases(priors)
    model = RBBAdaptiveBelief(diagonal_precision_bias=precision_bias, correlated_amplitude_bias=correlation_bias).to(device)
    initialization["parameter_count"] = sum(parameter.numel() for parameter in model.parameters())
    preparation_seconds = time.perf_counter() - preparation_started
    probe_hidden = banks["RANDOM_40"][0].to(device)
    microbatch, memory_reports = probe_memory(model, fixture, basis, probe_hidden, priors["RANDOM_40"], device)
    print(f"memory probe selected microbatch={microbatch}", flush=True)
    token_step0 = token_information(model, fixture, microbatch, device)
    model.train(); telemetry, accounting = train_model(model, fixture, basis, banks, priors, microbatch, device)
    token_step150 = token_information(model, fixture, microbatch, device)

    evaluations: dict[str, list[dict[str, Any]]] = {family: [] for family in FAMILIES}
    factor_rows: list[dict[str, Any]] = []; calibration_rows: list[dict[str, Any]] = []
    activity_rows: list[dict[str, Any]] = []
    for family in FAMILIES:
        for view in range(4):
            print(f"evaluating {family} view={view}", flush=True)
            result = evaluate_mask(model, fixture, basis, banks[family][view].to(device), priors[family], microbatch, device)
            representations = {}
            for name in ("visible", "raw", "diagonalized", "belief"):
                values = result[name]
                half = len(values) // 2
                validation_values = torch.cat((values[:VALIDATION], values[half:half + VALIDATION]))
                sealed_values = torch.cat((values[VALIDATION:half], values[half + VALIDATION:]))
                representations[name] = representation_readout(validation_values, sealed_values, fixture.factors.cpu())
                for factor, score in enumerate(representations[name]["per_factor"]):
                    factor_rows.append({"family": family, "view": view, "representation": name, "factor": factor, "r2": score})
            sealed_start = VALIDATION
            sealed = torch.cat((torch.arange(sealed_start, VALIDATION + SEALED), torch.arange(VALIDATION + SEALED + sealed_start, 2 * (VALIDATION + SEALED))))
            target = result["target"][sealed]; belief_error = target - (result["belief"][sealed] - result["visible"][sealed])
            marginal = result["marginal"][sealed]
            full_mahal = result["full_mahal"][sealed]
            diag_mahal = result["diag_mahal"][sealed]
            row = {
                "family": family, "view": view,
                "prior_nll": float(result["prior_nll"][sealed].mean()),
                "diagonalized_nll": float(result["diag_nll"][sealed].mean()),
                "full_nll": float(result["full_nll"][sealed].mean()),
                "joint_scale_full": float(full_mahal.mean() / WIDTH),
                "joint_scale_diagonalized": float(diag_mahal.mean() / WIDTH),
                **{f"marginal_{k}": v for k, v in marginal_calibration(belief_error, marginal).items()},
                "uncertainty_error_spearman": spearman(result["trace"][sealed], result["squared_error"][sealed]),
                "coordinate_variance_error_spearman": spearman(marginal.mean(0), belief_error.square().mean(0)),
                "gaussian_severe_fraction": gaussianity(belief_error, marginal)["severe_fraction"],
                "visible_factor_r2": representations["visible"]["mean"],
                "raw_factor_r2": representations["raw"]["mean"],
                "diagonalized_factor_r2": representations["diagonalized"]["mean"],
                "belief_factor_r2": representations["belief"]["mean"],
            }
            evaluations[family].append(row); calibration_rows.append(row)
            amps = result["amplitudes"][sealed]; energies = result["corr_energy"][sealed]; ranks = result["effective_rank"][sealed]
            for index in range(len(amps)):
                activity_rows.append({"family": family, "view": view, "example": index, "sum_amplitude_squared": float(amps[index].square().sum()), "correlated_covariance_energy": float(energies[index]), "effective_correlated_rank": float(ranks[index])})

    family_summary = {}
    for family, rows in evaluations.items():
        median = lambda key: float(np.median([row[key] for row in rows]))
        family_summary[family] = {key: median(key) for key in rows[0] if key not in ("family", "view")}
    full_coordinates = basis.transform(fixture.lambda_norm, whiten=True).cpu()
    full_xa = basis.transform(fixture.x_a, whiten=True).cpu(); full_xb = basis.transform(fixture.x_b, whiten=True).cpu()
    reference_readouts = {
        "full_lambda_norm": representation_readout(full_coordinates[TRAIN:TRAIN + VALIDATION], full_coordinates[-SEALED:], fixture.factors.cpu()),
        "full_x_a": representation_readout(full_xa[TRAIN:TRAIN + VALIDATION], full_xa[-SEALED:], fixture.factors.cpu()),
        "full_x_b": representation_readout(full_xb[TRAIN:TRAIN + VALIDATION], full_xb[-SEALED:], fixture.factors.cpu()),
    }
    full_expected = reference_readouts["full_lambda_norm"]["mean"]
    recovered = {}
    for family in FAMILIES:
        visible_r2, belief_r2 = family_summary[family]["visible_factor_r2"], family_summary[family]["belief_factor_r2"]
        recovered[family] = (belief_r2 - visible_r2) / (full_expected - visible_r2) if full_expected - visible_r2 > .02 else None

    observation_rows = []
    order = torch.randperm(GENES, generator=torch.Generator().manual_seed(SEED + 812)).to(device)
    nested = nested_visibility_masks(order)
    model.eval()
    with torch.no_grad():
        for fraction, visible_one in nested.items():
            hidden = ~visible_one; traces, marginals, ranks, logdets = [], [], [], []
            indices = torch.arange(CELLS - 128, CELLS, device=device)
            for start in range(0, len(indices), microbatch):
                selected = indices[start:start + microbatch]; expression = fixture.x_a[selected]
                visible_state = basis.contribution(expression, visible_one)
                ids = torch.arange(GENES, device=device)[None].expand(len(selected), -1); visible = visible_one[None].expand(len(selected), -1)
                with torch.autocast("cuda", dtype=torch.float16):
                    output = model(ids, expression, visible, visible_state, mask_context(basis, hidden, priors["RANDOM_40"], len(selected)), priors["RANDOM_40"]["prior_diagonal"], priors["RANDOM_40"]["prior_low_rank"], priors["RANDOM_40"]["noise_diagonal"])
                marginal = output.total_diagonal + output.total_low_rank.square().sum(-1)
                _, _, logdet = structured_gaussian_terms(torch.zeros_like(output.belief_mean), output.total_diagonal, output.total_low_rank)
                traces.append(marginal.sum(-1).cpu()); marginals.append(marginal.cpu()); ranks.append(effective_rank(output.evidence_low_rank).cpu()); logdets.append(logdet.cpu())
            observation_rows.append({"visible_fraction": fraction, "median_trace": float(torch.cat(traces).median()), "median_logdet": float(torch.cat(logdets).median()), "median_marginal_uncertainty": float(torch.cat(marginals).median()), "median_effective_rank": float(torch.cat(ranks).median()), "coordinate_medians": torch.cat(marginals).median(0).values})
    ordered_observation = sorted(observation_rows, key=lambda row: row["visible_fraction"], reverse=True)
    coordinate_stack = torch.stack([row.pop("coordinate_medians") for row in ordered_observation])
    removal_fraction = float(((coordinate_stack[1:] >= coordinate_stack[:-1]).all(0)).float().mean())

    hidden = banks["COEXPRESSION_BLOCK_40"][0].to(device); prior = priors["COEXPRESSION_BLOCK_40"]
    cf_indices = torch.arange(CELLS - 256, CELLS, device=device); cf_beliefs = []
    with torch.no_grad():
        for expression in (fixture.x_a, fixture.x_a_cf):
            parts = []
            for start in range(0, len(cf_indices), microbatch):
                selected = cf_indices[start:start + microbatch]; values = expression[selected]
                visible = (~hidden)[None].expand(len(selected), -1); ids = torch.arange(GENES, device=device)[None].expand(len(selected), -1)
                state = basis.contribution(values, ~hidden)
                with torch.autocast("cuda", dtype=torch.float16):
                    output = model(ids, values, visible, state, mask_context(basis, hidden, prior, len(selected)), prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"])
                parts.append(output.belief_mean.cpu())
            cf_beliefs.append(torch.cat(parts))
    predicted_delta = cf_beliefs[1] - cf_beliefs[0]
    true_delta = (basis.transform(fixture.lambda_norm_cf[-256:], whiten=True) - basis.transform(fixture.lambda_norm[-256:], whiten=True)).cpu()
    delta_r2 = r2_columns(true_delta, predicted_delta)
    cosine = torch.nn.functional.cosine_similarity(predicted_delta, true_delta)
    counterfactual_rows = [
        {"coordinate": coordinate, "delta_r2": float(delta_r2[coordinate])}
        for coordinate in range(WIDTH)
    ]
    counterfactual_summary = {"delta_r2": summarize(delta_r2), "cosine": summarize(cosine), "effect_norm_calibration": float(predicted_delta.norm(dim=1).mean() / true_delta.norm(dim=1).mean().clamp_min(1e-12))}

    no_harm = all(family_summary[f]["belief_factor_r2"] >= family_summary[f]["visible_factor_r2"] - .01 for f in FAMILIES)
    proper = all(family_summary[f]["full_nll"] < family_summary[f]["prior_nll"] for f in FAMILIES)
    joint = all(.80 <= family_summary[f]["joint_scale_full"] <= 1.25 for f in FAMILIES)
    marginal = all(.58 <= family_summary[f]["marginal_coverage_1sigma"] <= .78 and .88 <= family_summary[f]["marginal_coverage_1_96sigma"] <= .99 for f in FAMILIES)
    gaussian = all(family_summary[f]["gaussian_severe_fraction"] < .25 for f in FAMILIES)
    uncertainty = all(family_summary[f]["uncertainty_error_spearman"] > 0 for f in FAMILIES)
    token_pass = token_step0["retention_ratio"] >= .95 and token_step150["retention_ratio"] >= .95
    correlated_value = family_summary["COEXPRESSION_BLOCK_40"]["full_nll"] < family_summary["COEXPRESSION_BLOCK_40"]["diagonalized_nll"]
    belief_pass = token_pass and no_harm and proper and joint and marginal and gaussian and uncertainty
    positive_recovery = any(value is not None and value > 0 for value in recovered.values())
    if not token_pass: classification = "TOKEN-PRESERVING ENCODER REGRESSED"
    elif not belief_pass: classification = "RBB-JEPA BELIEF INFERENCE FAILS"
    elif correlated_value and positive_recovery: classification = "RBB-JEPA ADAPTIVE CORRELATED BELIEF STRONGLY SUPPORTED"
    elif correlated_value: classification = "RBB-JEPA BELIEF SUPPORTED; CORRELATED CAPACITY USED SELECTIVELY"
    elif all(abs(family_summary[f]["belief_factor_r2"] - family_summary[f]["visible_factor_r2"]) < .01 for f in FAMILIES): classification = "RBB-JEPA CALIBRATED BELIEF SUPPORTED, POINT INFERENCE ADDS LITTLE"
    else: classification = "RBB-JEPA BELIEF SUPPORTED, CORRELATED COMPONENT UNNECESSARY"

    replicate = {}
    for family in FAMILIES:
        result = evaluate_mask(model, fixture, basis, banks[family][0].to(device), priors[family], microbatch, device)
        a, b = result["belief_a"][VALIDATION:], result["belief_b"][VALIDATION:]
        replicate[family] = {"mean_state_cosine": float(torch.nn.functional.cosine_similarity(a, b).mean()), "paired_standardized_l2": float(((a - b) / torch.cat((a, b)).std(0).clamp_min(1e-8)).square().sum(1).sqrt().mean()), "coordinate_correlation": summarize(torch.tensor([torch.corrcoef(torch.stack((a[:, i], b[:, i])))[0, 1] for i in range(WIDTH)]))}

    payload = {
        "stage": "stage81a3_rbb_adaptive_correlated_probe", "anchor": ANCHOR,
        "classification": classification, "seed": SEED,
        "prior_evidence_hashes": actual_hashes,
        "fixture": {"cells": CELLS, "genes": GENES, "factors": FACTORS, "train": TRAIN, "validation": VALIDATION, "sealed": SEALED, "paired_replicates": True},
        "basis": {"sha256": BASIS_HASH, "width": WIDTH, "frozen": True},
        "architecture": {"ledger_shape": ["B", GENES, WIDTH], "blocks": 6, "heads": 4, "ffn": 320, "dropout": .10, "r_max": R_MAX, "cell_token": False, "perceiver": False, "learned_global_pooling": False, "conditional_compact_rank": 2 * R_MAX},
        "mask_contract": {"hidden": HIDDEN, "visible": VISIBLE, "banks": {name: len(value) for name, value in banks.items()}, "hashes": mask_hashes, "alternation": "deterministic random/block", "graph_role": "mask construction only"},
        "prior": {family: {key: value for key, value in prior.items() if isinstance(value, (float, int))} for family, prior in priors.items()},
        "measurement_noise": {"representation": "frozen diagonal", "learned": False},
        "initialization": initialization, "memory_probe": memory_reports,
        "training": accounting, "telemetry": telemetry,
        "token_information": {"step_0": token_step0, "step_150": token_step150},
        "reference_factor_information": reference_readouts,
        "family_summary": family_summary, "recovered_biological_gap": recovered,
        "observation_removal": {"rows": ordered_observation, "nondecreasing_coordinate_fraction": removal_fraction, "pass": removal_fraction >= .75},
        "replicate_consistency": replicate,
        "counterfactual": counterfactual_summary,
        "gates": {"engineering_pass": True, "token_retention_pass": token_pass, "no_harm_pass": no_harm, "proper_score_pass": proper, "joint_calibration_pass": joint, "marginal_calibration_pass": marginal, "uncertainty_error_pass": uncertainty, "gaussian_adequacy_pass": gaussian, "observation_removal_pass": removal_fraction >= .75},
        "timing": {"preparation_seconds": preparation_seconds, "total_wall_seconds": time.perf_counter() - total_started, "cpu_preparation_fraction": preparation_seconds / max(time.perf_counter() - total_started, 1e-12), "mean_gpu_utilization": None, "mean_gpu_utilization_note": "not sampled; CUDA allocation and throughput recorded"},
        "governance": {"stage81a3_complete": False, "ready_for_stage81b": False, "models_trained": 1, "optimizer_updates": UPDATES, "real_rna_accessed": False, "real_rna_optimizer_steps": 0, "pathology_opened": False, "visible_state_hard_preserved": True, "molecular_ledger_retained": True, "belief_uncertainty_explicit": True, "correlated_uncertainty_adaptive": True, "exact_gene_reconstruction_objective": False, "factor_labels_used_for_training": False, "lambda_norm_used_for_training": False, "true_dag_used_for_training": False, "hyperparameter_sweep": False, "seed_sweep": False},
    }
    atomic_csv(OUTPUTS["factors"], factor_rows); atomic_csv(OUTPUTS["calibration"], calibration_rows)
    atomic_csv(OUTPUTS["activity"], activity_rows); atomic_csv(OUTPUTS["counterfactual"], counterfactual_rows)
    atomic_json(OUTPUTS["json"], payload); append_readout(payload)
    print(json.dumps({"classification": classification, "gates": payload["gates"], "updates": UPDATES}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
