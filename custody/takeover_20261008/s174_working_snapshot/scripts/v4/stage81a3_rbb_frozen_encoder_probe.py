#!/usr/bin/env python3
"""Single-variable frozen-molecular-ledger follow-up to the RBB probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import stage81a3_rbb_adaptive_correlated_probe as base  # noqa: E402
from sea_ad_jepa.v4.conditional_predictability import (  # noqa: E402
    r2_columns,
    ridge_fit,
    ridge_predict,
    topk_absolute_correlation,
)
from sea_ad_jepa.v4.rbb_adaptive import (  # noqa: E402
    RBBAdaptiveBelief,
    R_MAX,
    fuse_gaussian_beliefs,
    nested_visibility_masks,
    rbb_nll,
    structured_gaussian_terms,
)

PREVIOUS_REPORT = Path("results/v4/stage81a3_rbb_adaptive_correlated_probe.json")
PREVIOUS_REPORT_HASH = "c73440b97830f4dc09467797aaefe5d59d99649fa6c98c6ed60cb23e82e083d3"
PREVIOUS_STEP0 = 1.0020574895396623
PREVIOUS_STEP150 = 0.8811191875486374
MILESTONES = (0, 25, 50, 100, 150)
MICROBATCH = 64
OUTPUTS = {
    "json": Path("results/v4/stage81a3_rbb_frozen_encoder_probe.json"),
    "retention": Path("results/v4/stage81a3_rbb_frozen_encoder_retention.csv"),
    "calibration": Path("results/v4/stage81a3_rbb_frozen_encoder_calibration.csv"),
    "activity": Path("results/v4/stage81a3_rbb_frozen_encoder_correlated_activity.csv"),
    "replicate": Path("results/v4/stage81a3_rbb_frozen_encoder_replicate.csv"),
    "counterfactual": Path("results/v4/stage81a3_rbb_frozen_encoder_counterfactual.csv"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    return parser.parse_args()


def module_hash(module: torch.nn.Module, *, exclude_prefix: str | None = None) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(module.state_dict().items()):
        if exclude_prefix and name.startswith(exclude_prefix):
            continue
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode()); digest.update(str(tensor.dtype).encode())
        digest.update(str(tuple(tensor.shape)).encode()); digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def frozen_hashes(model: RBBAdaptiveBelief) -> dict[str, str]:
    return {
        "tokenizer": module_hash(model.ledger.tokenizer),
        "encoder_without_tokenizer": module_hash(model.ledger, exclude_prefix="tokenizer."),
        "complete_molecular_ledger": module_hash(model.ledger),
    }


def maximum_frozen_gradient(model: RBBAdaptiveBelief) -> float:
    values = [float(parameter.grad.detach().abs().max()) for parameter in model.ledger.parameters() if parameter.grad is not None]
    return max(values, default=0.0)


def dropout_diagnostic(model: RBBAdaptiveBelief, fixture: Any, hidden: torch.Tensor, device: torch.device) -> dict[str, float]:
    cpu_state, cuda_state = torch.random.get_rng_state(), torch.cuda.get_rng_state(device)
    selected = torch.arange(2, device=device); values = fixture.x_a[selected]
    ids = torch.arange(base.GENES, device=device)[None].expand(2, -1)
    visible = (~hidden)[None].expand(2, -1)
    with torch.no_grad():
        model.ledger.train(); train_a = model.ledger(ids, values, visible)[0]
        train_b = model.ledger(ids, values, visible)[0]
        model.ledger.eval(); eval_a = model.ledger(ids, values, visible)[0]
        eval_b = model.ledger(ids, values, visible)[0]
    torch.random.set_rng_state(cpu_state); torch.cuda.set_rng_state(cuda_state, device)
    model.train()
    return {
        "train_mode_repeated_rms_difference": float((train_a.float() - train_b.float()).square().mean().sqrt()),
        "eval_mode_repeated_rms_difference": float((eval_a.float() - eval_b.float()).square().mean().sqrt()),
        "primary_training_mode": "train",
        "dropout_probability": 0.10,
        "rng_restored_after_diagnostic": True,
    }


def optimizer_audit(model: RBBAdaptiveBelief, optimizer: torch.optim.Optimizer) -> dict[str, Any]:
    all_parameters = list(model.parameters()); frozen = list(model.ledger.parameters())
    trainable = list(model.belief_parameters())
    optimized = [parameter for group in optimizer.param_groups for parameter in group["params"]]
    overlap = {id(parameter) for parameter in optimized} & {id(parameter) for parameter in frozen}
    if overlap: raise RuntimeError("optimizer contains frozen molecular parameters")
    if {id(p) for p in optimized} != {id(p) for p in trainable}:
        raise RuntimeError("optimizer parameter group differs from belief parameter set")
    return {
        "total_model_parameters": sum(p.numel() for p in all_parameters),
        "frozen_molecular_parameters": sum(p.numel() for p in frozen),
        "trainable_belief_parameters": sum(p.numel() for p in trainable),
        "optimizer_parameter_count": sum(p.numel() for p in optimized),
        "optimizer_frozen_id_intersection_count": len(overlap),
    }


def retention_row(step: int, model: RBBAdaptiveBelief, fixture: Any, device: torch.device) -> dict[str, Any]:
    result = base.token_information(model, fixture, MICROBATCH, device)
    return {
        "step": step,
        "tokenizer_mean_factor_r2": result["tokenizer"]["mean_r2"],
        "contextual_mean_factor_r2": result["contextual"]["mean_r2"],
        "retention_ratio": result["retention_ratio"],
        "tokenizer_median_factor_r2": result["tokenizer"]["median_r2"],
        "contextual_median_factor_r2": result["contextual"]["median_r2"],
    }


def train_belief_only(
    model: RBBAdaptiveBelief,
    fixture: Any,
    basis: Any,
    banks: dict[str, torch.Tensor],
    priors: dict[str, Any],
    optimizer: torch.optim.Optimizer,
    initial_hashes: dict[str, str],
    initial_retention: dict[str, Any],
    device: torch.device,
    milestone_callback=None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    scaler = torch.amp.GradScaler("cuda")
    generator = torch.Generator().manual_seed(base.SEED + 4242)
    retention = [initial_retention]
    hash_audit = [{"step": 0, **initial_hashes}]
    telemetry = [{"update": 0, "family": base.FAMILIES[0], **base.telemetry_point(model, fixture, basis, banks[base.FAMILIES[0]][0].to(device), priors[base.FAMILIES[0]], device)}]
    gradient_audit = []
    if milestone_callback is not None:
        milestone_callback(0, retention, hash_audit, gradient_audit, telemetry)
    started = time.perf_counter(); examples = 0; nonfinite = 0
    torch.cuda.reset_peak_memory_stats(device)
    for update in range(1, base.UPDATES + 1):
        family = base.FAMILIES[(update - 1) % 2]
        hidden = banks[family][((update - 1) // 2) % 128].to(device); prior = priors[family]
        selected = torch.randint(base.TRAIN, (base.EFFECTIVE_BATCH,), generator=generator).to(device)
        directions = torch.arange(base.EFFECTIVE_BATCH, device=device) % 2
        optimizer.zero_grad(set_to_none=True); cursor = 0; update_loss = 0.0
        for _ in range(4):
            indices = selected[cursor:cursor + MICROBATCH]; direction = directions[cursor:cursor + MICROBATCH]; cursor += MICROBATCH
            expression, visible_state, target = base.make_microbatch(fixture, basis, indices, direction, hidden)
            visible = (~hidden)[None].expand(MICROBATCH, -1)
            ids = torch.arange(base.GENES, device=device)[None].expand(MICROBATCH, -1)
            with torch.autocast("cuda", dtype=torch.float16):
                output = model(ids, expression, visible, visible_state, base.mask_context(basis, hidden, prior, MICROBATCH), prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"])
                loss = base.rbb_nll(output, target) * .25
            if not torch.isfinite(loss): nonfinite += 1; raise FloatingPointError(f"nonfinite loss at {update}")
            scaler.scale(loss).backward(); update_loss += float(loss.detach())
        if update in (1, 25, 150):
            maximum = maximum_frozen_gradient(model); gradient_audit.append({"step": update, "maximum_absolute_frozen_gradient": maximum})
            if maximum != 0: raise RuntimeError("GRADIENT FIREWALL FAILURE")
        scaler.step(optimizer); scaler.update(); examples += base.EFFECTIVE_BATCH
        if update in MILESTONES[1:]:
            current_hashes = frozen_hashes(model); hash_audit.append({"step": update, **current_hashes})
            if current_hashes != initial_hashes: raise RuntimeError("GRADIENT FIREWALL FAILURE")
            current_retention = retention_row(update, model, fixture, device); retention.append(current_retention)
            if current_retention["retention_ratio"] < .95:
                raise RuntimeError("frozen hashes stable but token retention fell below 0.95")
            point = base.telemetry_point(model, fixture, basis, hidden, prior, device)
            telemetry.append({"update": update, "family": family, "training_nll": update_loss, **point})
            if milestone_callback is not None:
                milestone_callback(update, retention, hash_audit, gradient_audit, telemetry)
            print(f"update={update} retention={current_retention['retention_ratio']:.6f} nll={point['nll_per_dimension']:.6f}", flush=True)
    elapsed = time.perf_counter() - started
    return retention, hash_audit, {
        "telemetry": telemetry, "gradient_audit": gradient_audit,
        "updates": base.UPDATES, "molecular_encoder_updates": 0, "examples": examples,
        "wall_seconds": elapsed, "examples_per_second": examples / elapsed,
        "seconds_per_update": elapsed / base.UPDATES, "microbatch": MICROBATCH,
        "accumulation_microbatches": 4, "effective_batch": base.EFFECTIVE_BATCH,
        "peak_allocated_gb": torch.cuda.max_memory_allocated(device) / 2**30,
        "peak_reserved_gb": torch.cuda.max_memory_reserved(device) / 2**30,
        "nonfinite_events": nonfinite, "frozen_hash_audit": hash_audit,
    }


def evaluate_counterfactual(model: RBBAdaptiveBelief, fixture: Any, basis: Any, hidden: torch.Tensor, prior: dict[str, Any], device: torch.device) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    indices = torch.arange(base.CELLS - 256, base.CELLS, device=device); runs = []
    model.eval()
    with torch.no_grad():
        for expression in (fixture.x_a, fixture.x_a_cf):
            beliefs, diagonals, low_ranks = [], [], []
            for start in range(0, len(indices), MICROBATCH):
                selected = indices[start:start + MICROBATCH]; values = expression[selected]
                visible = (~hidden)[None].expand(len(selected), -1); ids = torch.arange(base.GENES, device=device)[None].expand(len(selected), -1)
                state = basis.contribution(values, ~hidden)
                with torch.autocast("cuda", dtype=torch.float16):
                    output = model(ids, values, visible, state, base.mask_context(basis, hidden, prior, len(selected)), prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"])
                beliefs.append(output.belief_mean.cpu()); diagonals.append(output.total_diagonal.cpu()); low_ranks.append(output.total_low_rank.cpu())
            runs.append((torch.cat(beliefs), torch.cat(diagonals), torch.cat(low_ranks)))
    factual, counterfactual = runs; predicted = counterfactual[0] - factual[0]
    truth = (basis.transform(fixture.lambda_norm_cf[-256:], whiten=True) - basis.transform(fixture.lambda_norm[-256:], whiten=True)).cpu()
    scores = r2_columns(truth, predicted); cosine = torch.nn.functional.cosine_similarity(predicted, truth)
    unit = truth / truth.norm(dim=1, keepdim=True).clamp_min(1e-12)
    unit = unit.to(counterfactual[2].dtype)
    direction_variance = (counterfactual[1] * unit.square()).sum(1) + (torch.einsum("bdr,bd->br", counterfactual[2], unit).square()).sum(1)
    rows = [{"cell": int(index), "delta_cosine": float(cosine[index]), "true_effect_norm": float(truth[index].norm()), "predicted_effect_norm": float(predicted[index].norm()), "changed_direction_variance": float(direction_variance[index]), "changed_direction_std": float(direction_variance[index].sqrt())} for index in range(len(truth))]
    return rows, {"coordinate_delta_r2": base.summarize(scores), "cosine": base.summarize(cosine), "effect_norm_ratio": float(predicted.norm(dim=1).mean() / truth.norm(dim=1).mean().clamp_min(1e-12)), "changed_direction_variance": base.summarize(direction_variance)}


def append_readout(payload: dict[str, Any]) -> None:
    path = Path("docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md")
    marker = "## RBB-JEPA Frozen-Encoder Gradient-Interference Probe"
    existing = path.read_text(encoding="utf-8")
    if marker in existing: raise RuntimeError("frozen-encoder readout already exists")
    previous = payload["comparison"]["trainable_encoder"]
    frozen = payload["comparison"]["frozen_encoder"]
    section = f"""

{marker}

This single-variable forensic follow-up reconstructed the original seed-{base.SEED} step-0 model,
verified retention parity, froze and detached the full molecular ledger, and applied exactly 150
optimizer updates only to the unchanged RBB belief machinery. Training-mode dropout 0.10 was
preserved; the frozen state hashes remained identical and frozen gradients remained zero.

Trainable-encoder retention changed from `{previous['step0_retention']:.6f}` to
`{previous['step150_retention']:.6f}`. Frozen-encoder retention changed from
`{frozen['step0_retention']:.6f}` to `{frozen['step150_retention']:.6f}`.

Primary classification: **{payload['classification']}**.

Correlated component: **{payload['secondary_findings']['correlated_component']}**. Point-state
recovery: **{payload['secondary_findings']['point_state_recovery']}**. Counterfactual sidecar:
**{payload['secondary_findings']['counterfactual_sidecar']}**.

This remains synthetic forensic evidence, not biological validation, Stage81A3 completion, or
authorization for Stage81B, real-RNA training, or pathology access.
"""
    base.atomic_text(path, existing.rstrip() + section + "\n")


def main() -> int:
    args = parse_args(); os.chdir(args.project_dir.resolve())
    if any(path.exists() for path in OUTPUTS.values()): raise RuntimeError("frozen-encoder output exists; continuation forbidden")
    if base.file_hash(PREVIOUS_REPORT) != PREVIOUS_REPORT_HASH: raise RuntimeError("previous RBB report hash changed")
    previous = json.loads(PREVIOUS_REPORT.read_text())
    if previous["classification"] != "TOKEN-PRESERVING ENCODER REGRESSED": raise RuntimeError("previous classification changed")
    if not torch.cuda.is_available(): raise RuntimeError("locked CUDA runtime required")
    device = torch.device("cuda"); torch.set_float32_matmul_precision("high"); torch.backends.cuda.matmul.allow_tf32 = True
    torch.manual_seed(base.SEED); torch.cuda.manual_seed_all(base.SEED); total_started = time.perf_counter(); prep_started = time.perf_counter()
    basis = base.load_basis(device); fixture = base.build_fixture(device); priors = base.frozen_family_statistics(device)
    weights, neighbors = topk_absolute_correlation(.5 * (fixture.x_a[:base.TRAIN] + fixture.x_b[:base.TRAIN]), 8)
    banks = {"RANDOM_40": base.random_mask_bank().pin_memory(), "COEXPRESSION_BLOCK_40": base.block_mask_bank(neighbors, weights).pin_memory()}
    precision_bias, correlation_bias, initialization = base.initialization_biases(priors)
    model = RBBAdaptiveBelief(diagonal_precision_bias=precision_bias, correlated_amplitude_bias=correlation_bias).to(device)
    initial_hashes = frozen_hashes(model); dropout = dropout_diagnostic(model, fixture, banks["RANDOM_40"][0].to(device), device)
    step0 = retention_row(0, model, fixture, device)
    parity_difference = abs(step0["retention_ratio"] - PREVIOUS_STEP0)
    if parity_difference > .01:
        payload = {"stage": "stage81a3_rbb_frozen_encoder_probe", "classification": "INITIALIZATION PARITY FAILURE", "step0": step0, "absolute_retention_difference": parity_difference, "optimizer_updates": 0}
        base.atomic_json(OUTPUTS["json"], payload); return 2
    model.freeze_molecular_ledger(); model.train()
    optimizer = torch.optim.AdamW(list(model.belief_parameters()), lr=1e-4, weight_decay=.01)
    parameter_audit = optimizer_audit(model, optimizer); preparation_seconds = time.perf_counter() - prep_started
    retention, hash_audit, training = train_belief_only(model, fixture, basis, banks, priors, optimizer, initial_hashes, step0, device)

    evaluations: dict[str, list[dict[str, Any]]] = {family: [] for family in base.FAMILIES}
    calibration_rows, activity_rows, replicate_rows = [], [], []
    for family in base.FAMILIES:
        for view in range(4):
            print(f"evaluating {family} view={view}", flush=True)
            result = base.evaluate_mask(model, fixture, basis, banks[family][view].to(device), priors[family], MICROBATCH, device)
            representations = {}
            for name in ("visible", "raw", "diagonalized", "belief"):
                values = result[name]; half = len(values) // 2
                validation = torch.cat((values[:base.VALIDATION], values[half:half + base.VALIDATION]))
                sealed_values = torch.cat((values[base.VALIDATION:half], values[half + base.VALIDATION:]))
                representations[name] = base.representation_readout(validation, sealed_values, fixture.factors.cpu())
            sealed = torch.cat((torch.arange(base.VALIDATION, base.VALIDATION + base.SEALED), torch.arange(3 * base.VALIDATION, 4 * base.VALIDATION)))
            target = result["target"][sealed]; residual = target - (result["belief"][sealed] - result["visible"][sealed]); marginal = result["marginal"][sealed]
            row = {"family": family, "view": view, "prior_nll": float(result["prior_nll"][sealed].mean()), "diagonalized_nll": float(result["diag_nll"][sealed].mean()), "full_nll": float(result["full_nll"][sealed].mean()), "joint_scale_full": float(result["full_mahal"][sealed].mean() / base.WIDTH), **{f"marginal_{k}": v for k, v in base.marginal_calibration(residual, marginal).items()}, "uncertainty_error_spearman": base.spearman(result["trace"][sealed], result["squared_error"][sealed]), "gaussian_severe_fraction": base.gaussianity(residual, marginal)["severe_fraction"], **{f"{name}_factor_r2": value["mean"] for name, value in representations.items()}}
            evaluations[family].append(row); calibration_rows.append(row)
            amplitudes = result["amplitudes"][sealed]
            for index in range(len(amplitudes)):
                activity = {"family": family, "view": view, "example": index, "sum_amplitude_squared": float(amplitudes[index].square().sum()), "correlated_covariance_energy": float(result["corr_energy"][sealed][index]), "effective_correlated_rank": float(result["effective_rank"][sealed][index])}
                activity.update({f"amplitude_{rank:02d}": float(amplitudes[index, rank]) for rank in range(R_MAX)}); activity_rows.append(activity)
            if view == 0:
                a, b = result["belief_a"], result["belief_b"]; factors_val = fixture.factors[base.TRAIN:base.TRAIN + base.VALIDATION].cpu(); factors_test = fixture.factors[-base.SEALED:].cpu()
                map_a = ridge_fit(a[:base.VALIDATION], factors_val, 1e-3); pred_a = ridge_predict(map_a, a[base.VALIDATION:]); pred_b = ridge_predict(map_a, b[base.VALIDATION:])
                scores_a, scores_b = r2_columns(factors_test, pred_a), r2_columns(factors_test, pred_b)
                for factor in range(base.FACTORS):
                    correlation = float(torch.corrcoef(torch.stack((pred_a[:, factor], pred_b[:, factor])))[0, 1])
                    replicate_rows.append({"family": family, "factor": factor, "a_factor_r2": float(scores_a[factor]), "b_factor_r2_under_a_map": float(scores_b[factor]), "prediction_correlation": correlation, "belief_mean_state_cosine": float(torch.nn.functional.cosine_similarity(a[base.VALIDATION:], b[base.VALIDATION:]).mean()), "paired_standardized_l2": float(((a[base.VALIDATION:] - b[base.VALIDATION:]) / torch.cat((a[base.VALIDATION:], b[base.VALIDATION:])).std(0).clamp_min(1e-8)).square().sum(1).sqrt().mean())})

    family_summary = {}
    for family, rows in evaluations.items():
        family_summary[family] = {key: float(np.median([row[key] for row in rows])) for key in rows[0] if key not in ("family", "view")}

    order = torch.randperm(base.GENES, generator=torch.Generator().manual_seed(base.SEED + 812)).to(device); nested = nested_visibility_masks(order); observation = []
    model.eval()
    with torch.no_grad():
        for fraction, visible_one in nested.items():
            medians = []
            indices = torch.arange(base.CELLS - 128, base.CELLS, device=device); hidden = ~visible_one
            for start in range(0, len(indices), MICROBATCH):
                selected = indices[start:start + MICROBATCH]; values = fixture.x_a[selected]; state = basis.contribution(values, visible_one)
                ids = torch.arange(base.GENES, device=device)[None].expand(len(selected), -1); visible = visible_one[None].expand(len(selected), -1); prior = priors["RANDOM_40"]
                with torch.autocast("cuda", dtype=torch.float16): output = model(ids, values, visible, state, base.mask_context(basis, hidden, prior, len(selected)), prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"])
                medians.append((output.total_diagonal + output.total_low_rank.square().sum(-1)).cpu())
            values = torch.cat(medians); observation.append({"visible_fraction": fraction, "median_trace": float(values.sum(1).median()), "median_marginal_uncertainty": float(values.median()), "coordinate_medians": values.median(0).values})
    observation = sorted(observation, key=lambda row: row["visible_fraction"], reverse=True); stack = torch.stack([row.pop("coordinate_medians") for row in observation]); monotonic = float(((stack[1:] >= stack[:-1]).all(0)).float().mean())
    cf_rows, cf_summary = evaluate_counterfactual(model, fixture, basis, banks["COEXPRESSION_BLOCK_40"][0].to(device), priors["COEXPRESSION_BLOCK_40"], device)

    no_harm = all(family_summary[f]["belief_factor_r2"] >= family_summary[f]["visible_factor_r2"] - .01 for f in base.FAMILIES)
    proper = all(family_summary[f]["full_nll"] < family_summary[f]["prior_nll"] for f in base.FAMILIES)
    joint = all(.80 <= family_summary[f]["joint_scale_full"] <= 1.25 for f in base.FAMILIES)
    marginal = all(.58 <= family_summary[f]["marginal_coverage_1sigma"] <= .78 and .88 <= family_summary[f]["marginal_coverage_1_96sigma"] <= .99 for f in base.FAMILIES)
    uncertainty = all(family_summary[f]["uncertainty_error_spearman"] > 0 for f in base.FAMILIES)
    retention_pass = all(row["retention_ratio"] >= .95 for row in retention) and abs(retention[-1]["retention_ratio"] - retention[0]["retention_ratio"]) <= .005
    hashes_pass = all({k: row[k] for k in initial_hashes} == initial_hashes for row in hash_audit); gradients_pass = all(row["maximum_absolute_frozen_gradient"] == 0 for row in training["gradient_audit"])
    if retention_pass and hashes_pass and gradients_pass and proper and joint and marginal and uncertainty and no_harm: classification = "GRADIENT INTERFERENCE CONFIRMED; FROZEN MOLECULAR LEDGER SUPPORTS RBB BELIEF"
    elif retention_pass and not (proper and joint and marginal and no_harm): classification = "RBB BELIEF FAILS EVEN WITH FROZEN MOLECULAR REPRESENTATION"
    elif not hashes_pass or not gradients_pass: classification = "GRADIENT FIREWALL FAILURE"
    else: classification = "ENGINEERING / NUMERICAL FAILURE"
    correlated = "EARNED" if family_summary["COEXPRESSION_BLOCK_40"]["full_nll"] < family_summary["COEXPRESSION_BLOCK_40"]["diagonalized_nll"] - 1e-4 else "NOT EARNED"
    point_delta = max(abs(family_summary[f]["belief_factor_r2"] - family_summary[f]["visible_factor_r2"]) for f in base.FAMILIES)
    point = "MEANINGFUL" if point_delta >= .01 else "NEGLIGIBLE"
    counterfactual = "SUPPORTED" if cf_summary["coordinate_delta_r2"]["median"] > 0 and cf_summary["cosine"]["median"] > .5 else "NOT SUPPORTED"
    prep_fraction = preparation_seconds / max(time.perf_counter() - total_started, 1e-12)
    payload = {"stage": "stage81a3_rbb_frozen_encoder_probe", "anchor": base.ANCHOR, "classification": classification, "previous_report_sha256": PREVIOUS_REPORT_HASH, "step0_initialization_parity": {"previous_retention": PREVIOUS_STEP0, "reconstructed_retention": retention[0]["retention_ratio"], "absolute_difference": abs(retention[0]["retention_ratio"] - PREVIOUS_STEP0), "pass": True}, "initial_frozen_hashes": initial_hashes, "dropout_semantics": dropout, "optimizer_audit": parameter_audit, "retention": retention, "training": training, "family_summary": family_summary, "observation_removal": {"rows": observation, "nondecreasing_coordinate_fraction": monotonic, "pass": monotonic >= .75}, "counterfactual": cf_summary, "comparison": {"trainable_encoder": {"step0_retention": PREVIOUS_STEP0, "step150_retention": PREVIOUS_STEP150, "family_summary": previous["family_summary"]}, "frozen_encoder": {"step0_retention": retention[0]["retention_ratio"], "step150_retention": retention[-1]["retention_ratio"], "family_summary": family_summary}}, "gates": {"step0_parity": True, "frozen_hashes_unchanged": hashes_pass, "frozen_gradients_zero": gradients_pass, "token_retention": retention_pass, "proper_score": proper, "joint_calibration": joint, "marginal_calibration": marginal, "uncertainty_error": uncertainty, "no_harm": no_harm}, "secondary_findings": {"correlated_component": correlated, "point_state_recovery": point, "counterfactual_sidecar": counterfactual}, "performance": {**{k: training[k] for k in ("microbatch", "accumulation_microbatches", "effective_batch", "updates", "examples", "peak_allocated_gb", "peak_reserved_gb", "examples_per_second", "seconds_per_update", "wall_seconds")}, "mean_gpu_utilization": None, "cpu_preparation_fraction": prep_fraction}, "governance": {"stage81a3_complete": False, "ready_for_stage81b": False, "frozen_encoder_models_trained": 1, "belief_optimizer_updates": 150, "molecular_encoder_optimizer_updates": 0, "real_rna_accessed": False, "pathology_opened": False, "preservation_regularizer_added": False, "hyperparameter_sweep": False, "seed_sweep": False}}
    base.atomic_csv(OUTPUTS["retention"], retention); base.atomic_csv(OUTPUTS["calibration"], calibration_rows); base.atomic_csv(OUTPUTS["activity"], activity_rows); base.atomic_csv(OUTPUTS["replicate"], replicate_rows); base.atomic_csv(OUTPUTS["counterfactual"], cf_rows); base.atomic_json(OUTPUTS["json"], payload); append_readout(payload)
    print(json.dumps({"classification": classification, "gates": payload["gates"], "secondary": payload["secondary_findings"]}, indent=2), flush=True)
    return 0


if __name__ == "__main__": raise SystemExit(main())
