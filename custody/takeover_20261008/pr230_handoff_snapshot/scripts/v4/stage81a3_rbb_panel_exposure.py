#!/usr/bin/env python3
"""One authorized belief-only structural-panel exposure probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import stage81a3_rbb_adaptive_correlated_probe as base  # noqa: E402
import stage81a3_rbb_frozen_encoder_probe as frozen  # noqa: E402
import stage81a3_rbb_frozen_recovery as recovery  # noqa: E402
import stage81a3_rbb_structural_panel_audit as structural  # noqa: E402
from sea_ad_jepa.v4.conditional_predictability import (  # noqa: E402
    r2_columns, ridge_fit, ridge_predict, topk_absolute_correlation,
)
from sea_ad_jepa.v4.measurement_state import MeasurementState  # noqa: E402
from sea_ad_jepa.v4.rbb_adaptive import RBBAdaptiveBelief, R_MAX, rbb_nll  # noqa: E402


SEED = base.SEED
UPDATES = 150
STRATUM_SIZE = 32
EFFECTIVE_BATCH = 256
MICROBATCH = 32
MILESTONES = (0, 25, 50, 100, 150)
STRATA = (
    "ORDINARY_RANDOM_40", "ORDINARY_BLOCK_40",
    "STRUCTURAL_RANDOM_P80", "STRUCTURAL_RANDOM_P60", "STRUCTURAL_RANDOM_P40",
    "STRUCTURAL_COHERENT_P80", "STRUCTURAL_COHERENT_P60", "STRUCTURAL_COHERENT_P40",
)
STRUCTURAL_FRACTIONS = ("P80", "P60", "P40")
PRIOR_EVIDENCE = {
    **structural.PRIOR_EVIDENCE,
    "results/v4/stage81a3_rbb_structural_panel_audit.json": "4a6fb3e78fc9ccc87b600d5a1ff8f49fecfe4643f3c16657ac9f9293f34ce9ac",
}
OUTPUTS = {
    "json": Path("results/v4/stage81a3_rbb_panel_exposure.json"),
    "checkpoint": Path("results/v4/stage81a3_rbb_panel_exposure_checkpoint.pt"),
    "training": Path("results/v4/stage81a3_rbb_panel_exposure_training.csv"),
    "structural": Path("results/v4/stage81a3_rbb_panel_exposure_structural.csv"),
    "ordinary": Path("results/v4/stage81a3_rbb_panel_exposure_ordinary.csv"),
    "cross": Path("results/v4/stage81a3_rbb_panel_exposure_cross_panel.csv"),
    "correlated": Path("results/v4/stage81a3_rbb_panel_exposure_correlated.csv"),
    "scalar": Path("results/v4/stage81a3_rbb_panel_exposure_scalar_control.csv"),
}


def tensor_state_hash(state: dict[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        value = state[name].detach().cpu().contiguous()
        digest.update(name.encode()); digest.update(str(value.dtype).encode())
        digest.update(str(tuple(value.shape)).encode()); digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def belief_hash(model: RBBAdaptiveBelief) -> str:
    return tensor_state_hash({name: value for name, value in model.state_dict().items() if not name.startswith("ledger.")})


def mask_hash(bank: torch.Tensor) -> str:
    return hashlib.sha256(bank.cpu().contiguous().numpy().tobytes()).hexdigest()


def verify_prior_evidence() -> dict[str, str]:
    actual = {path: structural.sha256(Path(path)) for path in PRIOR_EVIDENCE}
    if actual != PRIOR_EVIDENCE:
        raise RuntimeError("prior evidence hash mismatch")
    return actual


def build_banks(fixture: Any) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
    """Build fixed ordinary and TRAIN-only panel banks without labels or SEALED data."""
    average = .5 * (fixture.x_a[:base.TRAIN] + fixture.x_b[:base.TRAIN])
    weights, neighbors = topk_absolute_correlation(average, 8)
    ordinary = {
        "ORDINARY_RANDOM_40": base.random_mask_bank(),
        "ORDINARY_BLOCK_40": base.block_mask_bank(neighbors, weights),
    }
    recovery_metadata = torch.load(structural.CHECKPOINT, map_location="cpu", weights_only=False)["metadata"]
    ordinary_expected = {
        "ORDINARY_RANDOM_40": recovery_metadata["mask_bank_sha256"]["RANDOM_40"],
        "ORDINARY_BLOCK_40": recovery_metadata["mask_bank_sha256"]["COEXPRESSION_BLOCK_40"],
    }
    ordinary_actual = {name: mask_hash(bank) for name, bank in ordinary.items()}
    if ordinary_actual != ordinary_expected:
        raise RuntimeError("ordinary mask bank changed")
    banks = dict(ordinary)
    for family in ("RANDOM", "COHERENT"):
        masks = {fraction: [] for fraction in STRUCTURAL_FRACTIONS}
        for view in range(128):
            if family == "RANDOM":
                order = torch.randperm(base.GENES, generator=torch.Generator().manual_seed(SEED + 2003 * view + 71))
                panels = structural.panel_masks(order, measured_prefix=True)
            else:
                order = structural.connected_order(neighbors.cpu(), weights.cpu(), SEED + 2017 * view + 89)
                panels = structural.panel_masks(order, measured_prefix=False)
            for fraction in STRUCTURAL_FRACTIONS:
                masks[fraction].append(panels[fraction])
        for fraction, values in masks.items():
            banks[f"STRUCTURAL_{family}_{fraction}"] = torch.stack(values)
    hashes = {name: mask_hash(bank) for name, bank in banks.items()}
    audit = {
        "hashes": hashes, "ordinary_hashes_match_recovery": True,
        "structural_masks_per_stratum": 128, "train_only": True,
        "factor_labels_used": False, "sealed_used": False,
        "p20_present": False,
        "exact_counts": {
            name: sorted(set(int(x) for x in (bank.sum(1) if name.startswith("STRUCTURAL") else (~bank).sum(1)).tolist()))
            for name, bank in banks.items()
        },
    }
    return banks, audit


def initialize_model(device: torch.device, priors: dict[str, Any]) -> tuple[RBBAdaptiveBelief, dict[str, str], str]:
    torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    precision_bias, correlation_bias, _ = base.initialization_biases(priors)
    model = RBBAdaptiveBelief(diagonal_precision_bias=precision_bias, correlated_amplitude_bias=correlation_bias).to(device)
    hashes = frozen.frozen_hashes(model)
    recovery_report = json.loads(structural.RECOVERY_REPORT.read_text(encoding="utf-8"))
    if hashes != recovery_report["molecular_hashes_step0"]:
        raise RuntimeError("molecular initialization mismatch")
    initial_belief_hash = belief_hash(model)
    model.freeze_molecular_ledger()
    return model, hashes, initial_belief_hash


def load_preexposure_model(device: torch.device, priors: dict[str, Any]) -> RBBAdaptiveBelief:
    model, _, _ = initialize_model(device, priors)
    checkpoint = torch.load(structural.CHECKPOINT, map_location=device, weights_only=False)
    missing, unexpected = model.load_state_dict(checkpoint["belief_state_dict"], strict=False)
    if unexpected or any(not name.startswith("ledger.") for name in missing):
        raise RuntimeError("pre-exposure checkpoint key mismatch")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    model.eval()
    return model


def stratum_contract(name: str, panel_row: torch.Tensor, batch: int, device: torch.device) -> tuple[MeasurementState, torch.Tensor, str]:
    if name.startswith("ORDINARY"):
        hidden = panel_row.to(device)
        measured = torch.ones(batch, base.GENES, dtype=torch.bool, device=device)
        training_hidden = hidden[None].expand(batch, -1)
        family = "RANDOM_40" if name == "ORDINARY_RANDOM_40" else "COEXPRESSION_BLOCK_40"
    else:
        measured_one = panel_row.to(device)
        measured = measured_one[None].expand(batch, -1)
        training_hidden = torch.zeros_like(measured)
        hidden = ~measured_one
        family = "RANDOM_40" if "_RANDOM_" in name else "COEXPRESSION_BLOCK_40"
    state = MeasurementState(measured, training_hidden, torch.ones(base.GENES, dtype=torch.bool, device=device))
    return state, hidden, family


def stratum_batch(
    name: str,
    panel_row: torch.Tensor,
    fixture: Any,
    basis: Any,
    indices: torch.Tensor,
    device: torch.device,
) -> tuple[torch.Tensor, MeasurementState, torch.Tensor, str]:
    directions = torch.arange(len(indices), device=device) % 2
    source_a = directions == 0
    expression = torch.where(source_a[:, None], fixture.x_a[indices], fixture.x_b[indices])
    independent_reference = torch.where(source_a[:, None], fixture.x_b[indices], fixture.x_a[indices])
    state, hidden, family = stratum_contract(name, panel_row, len(indices), device)
    target = basis.contribution(independent_reference, hidden)
    return expression, state, target, family


def optimizer_audit(model: RBBAdaptiveBelief, optimizer: torch.optim.Optimizer) -> dict[str, Any]:
    molecular = {id(parameter) for parameter in model.ledger.parameters()}
    optimized = {id(parameter) for group in optimizer.param_groups for parameter in group["params"]}
    return {
        "molecular_parameters": sum(p.numel() for p in model.ledger.parameters()),
        "belief_parameters": sum(p.numel() for p in model.belief_parameters()),
        "optimized_parameters": sum(p.numel() for group in optimizer.param_groups for p in group["params"]),
        "molecular_optimizer_overlap": len(molecular & optimized),
    }


def maximum_molecular_gradient(model: RBBAdaptiveBelief) -> float:
    values = [float(p.grad.detach().abs().max()) for p in model.ledger.parameters() if p.grad is not None]
    return max(values, default=0.0)


def telemetry_strata(model: Any, fixture: Any, basis: Any, banks: dict[str, torch.Tensor], priors: dict[str, Any], update: int, device: torch.device) -> list[dict[str, Any]]:
    rows = []; was_training = model.training; model.eval()
    with torch.no_grad():
        indices = torch.arange(32, device=device)
        for stratum in STRATA:
            expression, state, target, family = stratum_batch(stratum, banks[stratum][update % 128], fixture, basis, indices, device)
            with torch.autocast("cuda", dtype=torch.float16):
                output = structural.forward_contract(model, expression, state, basis, priors[family])
            residual = target - output.posterior_missing_mean
            marginal = output.total_diagonal + output.total_low_rank.square().sum(-1)
            _, mahal, _ = base.structured_gaussian_terms(residual, output.total_diagonal, output.total_low_rank)
            rows.append({
                "update": update, "stratum": stratum,
                "nll": float(rbb_nll(output, target)),
                "mean_predicted_variance": float(marginal.mean()),
                "mean_squared_error": float(residual.square().mean()),
                "joint_scale": float((mahal / base.WIDTH).mean()),
            })
    model.train(was_training)
    return rows


def train(
    model: RBBAdaptiveBelief,
    fixture: Any,
    basis: Any,
    banks: dict[str, torch.Tensor],
    priors: dict[str, Any],
    optimizer: torch.optim.Optimizer,
    initial_hashes: dict[str, str],
    device: torch.device,
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    generator = torch.Generator().manual_seed(SEED + 5003)
    scaler = torch.amp.GradScaler("cuda"); telemetry = telemetry_strata(model, fixture, basis, banks, priors, 0, device)
    retention = [frozen.retention_row(0, model, fixture, device)]
    hash_rows = [{"update": 0, **initial_hashes}]; gradient_rows = []
    started = time.perf_counter(); examples = 0; nonfinite = 0
    torch.cuda.reset_peak_memory_stats(device); model.train()
    for update in range(1, UPDATES + 1):
        optimizer.zero_grad(set_to_none=True)
        sampled = torch.randint(base.TRAIN, (len(STRATA), STRATUM_SIZE), generator=generator).to(device)
        for position, stratum in enumerate(STRATA):
            expression, state, target, family = stratum_batch(stratum, banks[stratum][(update - 1) % 128], fixture, basis, sampled[position], device)
            with torch.autocast("cuda", dtype=torch.float16):
                output = structural.forward_contract(model, expression, state, basis, priors[family])
                loss = rbb_nll(output, target) / len(STRATA)
            if not torch.isfinite(loss):
                nonfinite += 1; raise FloatingPointError(f"nonfinite loss at update {update}")
            scaler.scale(loss).backward(); examples += len(expression)
        if update in (1, 25, 150):
            maximum = maximum_molecular_gradient(model); gradient_rows.append({"update": update, "maximum_absolute_molecular_gradient": maximum})
            if maximum != 0:
                raise RuntimeError("GRADIENT FIREWALL FAILURE")
        scaler.step(optimizer); scaler.update()
        if update in MILESTONES[1:]:
            current = frozen.frozen_hashes(model); hash_rows.append({"update": update, **current})
            if current != initial_hashes:
                raise RuntimeError("GRADIENT FIREWALL FAILURE")
            retention.append(frozen.retention_row(update, model, fixture, device))
            telemetry.extend(telemetry_strata(model, fixture, basis, banks, priors, update, device))
            payload.update({"status": f"update_{update}_persisted", "training_telemetry": telemetry, "retention": retention, "molecular_hash_trajectory": hash_rows, "gradient_firewall": gradient_rows})
            base.atomic_csv(OUTPUTS["training"], telemetry); base.atomic_json(OUTPUTS["json"], payload)
            print(f"update={update} retention={retention[-1]['retention_ratio']:.6f}", flush=True)
    elapsed = time.perf_counter() - started
    return telemetry, retention, hash_rows, {
        "updates": UPDATES, "belief_optimizer_updates": UPDATES, "molecular_optimizer_updates": 0,
        "examples": examples, "effective_batch": EFFECTIVE_BATCH, "microbatch": MICROBATCH,
        "accumulation_microbatches": len(STRATA), "nonfinite_events": nonfinite,
        "wall_seconds": elapsed, "examples_per_second": examples / elapsed,
        "seconds_per_update": elapsed / UPDATES,
        "peak_allocated_gb": torch.cuda.max_memory_allocated(device) / 2**30,
        "peak_reserved_gb": torch.cuda.max_memory_reserved(device) / 2**30,
        "gradient_firewall": gradient_rows,
    }


def save_checkpoint(model: RBBAdaptiveBelief, metadata: dict[str, Any]) -> str:
    state = {name: value.detach().cpu() for name, value in model.state_dict().items() if not name.startswith("ledger.")}
    metadata = {**metadata, "contains_molecular_weights": False, "belief_tensor_count": len(state)}
    return recovery.atomic_checkpoint(OUTPUTS["checkpoint"], {"belief_state_dict": state, "metadata": metadata})


def ordinary_evaluation(
    model: Any, fixture: Any, basis: Any, banks: dict[str, torch.Tensor], priors: dict[str, Any], device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows = []; correlated = []; summaries = {}
    for stratum, family in (("ORDINARY_RANDOM_40", "RANDOM_40"), ("ORDINARY_BLOCK_40", "COEXPRESSION_BLOCK_40")):
        family_rows = []
        for view in range(4):
            result = base.evaluate_mask(model, fixture, basis, banks[stratum][view].to(device), priors[family], MICROBATCH, device)
            sealed = torch.cat((torch.arange(base.VALIDATION, 2 * base.VALIDATION), torch.arange(3 * base.VALIDATION, 4 * base.VALIDATION)))
            target = result["target"][sealed]
            residual = target - (result["belief"][sealed] - result["visible"][sealed])
            marginal = result["marginal"][sealed]
            factors = {}
            for name in ("visible", "belief", "diagonalized"):
                values = result[name]; half = len(values) // 2
                validation_values = torch.cat((values[:base.VALIDATION], values[half:half + base.VALIDATION]))
                sealed_values = torch.cat((values[base.VALIDATION:half], values[half + base.VALIDATION:]))
                factors[name] = base.representation_readout(validation_values, sealed_values, fixture.factors.cpu())
            gaussian = base.gaussianity(residual, marginal)
            mapping = ridge_fit(result["belief_a"][:base.VALIDATION], fixture.factors[base.TRAIN:base.TRAIN + base.VALIDATION].cpu(), 1e-3)
            pred_a = ridge_predict(mapping, result["belief_a"][base.VALIDATION:])
            pred_b = ridge_predict(mapping, result["belief_b"][base.VALIDATION:])
            factor_correlations = torch.stack([torch.corrcoef(torch.stack((pred_a[:, index], pred_b[:, index])))[0, 1] for index in range(base.FACTORS)])
            scale = torch.cat((result["belief_a"][base.VALIDATION:], result["belief_b"][base.VALIDATION:])).std(0).clamp_min(1e-8)
            row = {
                "family": family, "view": view,
                "nll": float(result["full_nll"][sealed].mean()), "prior_nll": float(result["prior_nll"][sealed].mean()),
                "diagonalized_nll": float(result["diag_nll"][sealed].mean()),
                "joint_scale": float(result["full_mahal"][sealed].mean() / base.WIDTH),
                "uncertainty_error_spearman": base.spearman(result["trace"][sealed], result["squared_error"][sealed]),
                "visible_factor_r2": factors["visible"]["mean"], "belief_factor_r2": factors["belief"]["mean"],
                "belief_minus_visible_factor_r2": factors["belief"]["mean"] - factors["visible"]["mean"],
                "coverage_1sigma": base.marginal_calibration(residual, marginal)["coverage_1sigma"],
                "coverage_1_96sigma": base.marginal_calibration(residual, marginal)["coverage_1_96sigma"],
                "gaussian_severe_fraction": gaussian["severe_fraction"],
                "gaussian_skewness_median": gaussian["skewness"]["median"],
                "gaussian_excess_kurtosis_median": gaussian["excess_kurtosis"]["median"],
                "belief_state_cosine": float(torch.nn.functional.cosine_similarity(result["belief_a"][base.VALIDATION:], result["belief_b"][base.VALIDATION:]).mean()),
                "replicate_factor_prediction_correlation": float(factor_correlations.mean()),
                "replicate_paired_standardized_distance": float((((result["belief_a"][base.VALIDATION:] - result["belief_b"][base.VALIDATION:]) / scale).square().sum(1).sqrt()).mean()),
            }
            family_rows.append(row); rows.append(row)
            amplitudes = result["amplitudes"][sealed]
            for rank in range(R_MAX):
                correlated.append({"condition": family, "view": view, "panel": "P40", "rank": rank, "nll_minus_diagonalized": row["nll"] - row["diagonalized_nll"], "mean_correlated_energy": float(result["corr_energy"][sealed].mean()), "median_effective_rank": float(result["effective_rank"][sealed].median()), **{f"amplitude_{key}": value for key, value in base.summarize(amplitudes[:, rank]).items()}})
        summaries[family] = {key: float(np.median([row[key] for row in family_rows])) for key in family_rows[0] if key not in ("family", "view")}
    return rows, correlated, summaries


def structural_result_row(family: str, view: int, panel: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "family": family, "view": view, "panel": panel, "measured_genes": structural.PANEL_COUNTS[panel],
        "nll": result["nll"], "prior_nll": result["prior_nll"], "diagonalized_nll": result["diagonalized_nll"],
        "joint_scale": result["joint_scale"], "standardized_variance": result["standardized_variance"],
        "coverage_1sigma": result["coverage_1sigma"], "coverage_1_96sigma": result["coverage_1_96sigma"],
        "uncertainty_error_spearman": result["uncertainty_error_spearman"],
        "visible_factor_r2": result["factors"]["visible"]["mean"], "belief_factor_r2": result["factors"]["belief"]["mean"],
        "belief_minus_visible_factor_r2": result["factors"]["belief"]["mean"] - result["factors"]["visible"]["mean"],
        "synthetic_full_expected_factor_r2": result["factors"]["synthetic_full_expected"]["mean"],
        "recoverable_gap_fraction": (
            (result["factors"]["belief"]["mean"] - result["factors"]["visible"]["mean"])
            / max(result["factors"]["synthetic_full_expected"]["mean"] - result["factors"]["visible"]["mean"], 1e-12)
        ),
        "median_trace": result["median_trace"], "median_logdet": result["median_logdet"],
        "gaussian_severe_fraction": result["gaussianity"]["severe_fraction"],
        "gaussian_skewness_median": result["gaussianity"]["skewness"]["median"],
        "gaussian_excess_kurtosis_median": result["gaussianity"]["excess_kurtosis"]["median"],
        "mean_correlated_energy": result["mean_correlated_energy"], "median_correlated_rank": result["median_correlated_rank"],
    }


def structural_evaluation(
    model: Any, fixture: Any, basis: Any, priors: dict[str, Any], panels: dict[str, Any], device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows = []; correlated = []; coordinate_stacks = {family: [] for family in structural.FAMILIES}
    for family in structural.FAMILIES:
        prior = priors["RANDOM_40" if family == "RANDOM_STRUCTURAL" else "COEXPRESSION_BLOCK_40"]
        for view, masks in enumerate(panels[family]):
            view_coordinates = []
            for panel in structural.PANEL_ORDER:
                print(f"post {family} view={view} panel={panel}", flush=True)
                result = structural.panel_forward(model, fixture, basis, prior, masks[panel], device, retain=True)
                row = structural_result_row(family, view, panel, result); rows.append(row)
                arrays = result["arrays"]; half = len(arrays["belief"]) // 2
                a_validation = arrays["belief"][:base.VALIDATION]; a_sealed = arrays["belief"][base.VALIDATION:half]
                b_sealed = arrays["belief"][half + base.VALIDATION:]
                mapping = ridge_fit(a_validation, fixture.factors[base.TRAIN:base.TRAIN + base.VALIDATION].cpu(), 1e-3)
                pred_a, pred_b = ridge_predict(mapping, a_sealed), ridge_predict(mapping, b_sealed)
                correlations = torch.stack([torch.corrcoef(torch.stack((pred_a[:, index], pred_b[:, index])))[0, 1] for index in range(base.FACTORS)])
                scale = torch.cat((a_sealed, b_sealed)).std(0).clamp_min(1e-8)
                row.update({
                    "belief_state_cosine": float(torch.nn.functional.cosine_similarity(a_sealed, b_sealed).mean()),
                    "replicate_factor_prediction_correlation": float(correlations.mean()),
                    "replicate_paired_standardized_distance": float((((a_sealed - b_sealed) / scale).square().sum(1).sqrt()).mean()),
                })
                view_coordinates.append(result["coordinate_median_variance"])
                for rank, rank_summary in enumerate(result["amplitude_by_rank"]):
                    correlated.append({"condition": family, "view": view, "panel": panel, "rank": rank, "nll_minus_diagonalized": result["nll"] - result["diagonalized_nll"], "mean_correlated_energy": result["mean_correlated_energy"], "median_effective_rank": result["median_correlated_rank"], **{f"amplitude_{key}": value for key, value in rank_summary.items()}})
            coordinate_stacks[family].append(torch.stack(view_coordinates))
    summary = {}
    for family in structural.FAMILIES:
        monotonic = [float(((stack[1:] >= stack[:-1]).all(0)).float().mean()) for stack in coordinate_stacks[family]]
        summary[family] = {"monotonic_coordinate_fraction": float(np.median(monotonic)), "panels": {}}
        for panel in structural.PANEL_ORDER:
            selected = [row for row in rows if row["family"] == family and row["panel"] == panel]
            summary[family]["panels"][panel] = {key: float(np.median([row[key] for row in selected])) for key in selected[0] if key not in ("family", "view", "panel", "measured_genes")}
    return rows, correlated, summary


def fit_scalar_control(
    model: Any, fixture: Any, basis: Any, priors: dict[str, Any], panels: dict[str, Any], device: torch.device,
) -> tuple[float, list[dict[str, Any]], dict[str, Any]]:
    compact = []; validation_mahal = []
    for family in structural.FAMILIES:
        prior = priors["RANDOM_40" if family == "RANDOM_STRUCTURAL" else "COEXPRESSION_BLOCK_40"]
        for view, masks in enumerate(panels[family]):
            for panel in STRUCTURAL_FRACTIONS:
                print(f"scalar pre {family} view={view} panel={panel}", flush=True)
                result = structural.panel_forward(model, fixture, basis, prior, masks[panel], device, retain=True)
                arrays = result["arrays"]; half = len(arrays["belief"]) // 2
                validation = torch.cat((torch.arange(base.VALIDATION), torch.arange(half, half + base.VALIDATION)))
                sealed = torch.cat((torch.arange(base.VALIDATION, half), torch.arange(half + base.VALIDATION, 2 * half)))
                validation_mahal.append(arrays["mahal"][validation])
                compact.append({
                    "family": family, "view": view, "panel": panel,
                    "nll": arrays["full_nll"][sealed], "mahal": arrays["mahal"][sealed],
                    "residual": arrays["target"][sealed] - (arrays["belief"][sealed] - arrays["visible"][sealed]),
                    "marginal": arrays["marginal"][sealed], "trace": arrays["trace"][sealed],
                    "belief_factor_r2": result["factors"]["belief"]["mean"],
                })
    scale = float(torch.cat(validation_mahal).mean())
    if not np.isfinite(scale) or scale <= 0:
        raise RuntimeError("invalid scalar variance optimum")
    rows = []
    for item in compact:
        marginal = item["marginal"] * scale
        marginal_cal = base.marginal_calibration(item["residual"], marginal)
        scaled_nll = item["nll"] + .5 * (np.log(scale) + item["mahal"] * (1.0 / scale - 1.0))
        rows.append({
            "family": item["family"], "view": item["view"], "panel": item["panel"], "variance_temperature": scale,
            "sealed_nll": float(scaled_nll.mean()), "joint_scale": float((item["mahal"] / scale).mean()),
            "coverage_1sigma": marginal_cal["coverage_1sigma"], "coverage_1_96sigma": marginal_cal["coverage_1_96sigma"],
            "uncertainty_error_spearman": base.spearman(item["trace"] * scale, item["residual"].square().sum(1)),
            "belief_factor_r2": item["belief_factor_r2"], "median_trace": float((item["trace"] * scale).median()),
        })
    summary = {}
    for family in structural.FAMILIES:
        summary[family] = {}
        for panel in STRUCTURAL_FRACTIONS:
            selected = [row for row in rows if row["family"] == family and row["panel"] == panel]
            summary[family][panel] = {key: float(np.median([row[key] for row in selected])) for key in selected[0] if key not in ("family", "view", "panel")}
    return scale, rows, summary


def calibration_error(row: dict[str, float]) -> float:
    return abs(row["joint_scale"] - 1.0) + abs(row["coverage_1sigma"] - .6827) + abs(row["coverage_1_96sigma"] - .95)


def classify(
    ordinary: dict[str, Any], structural_post: dict[str, Any], structural_pre: dict[str, Any],
    scalar: dict[str, Any], semantics: dict[str, Any], cross: dict[str, Any],
) -> tuple[str, dict[str, bool], dict[str, str], dict[str, Any]]:
    ordinary_pass = all(
        row["nll"] < row["prior_nll"] and .8 <= row["joint_scale"] <= 1.25
        and row["uncertainty_error_spearman"] >= .75
        and row["belief_factor_r2"] >= row["visible_factor_r2"] - .01
        for row in ordinary.values()
    )
    p60_rows = [structural_post[family]["panels"]["P60"] for family in structural.FAMILIES]
    p60_proper = all(row["nll"] < row["prior_nll"] for row in p60_rows)
    p60_calibration = all(.8 <= row["joint_scale"] <= 1.25 and .58 <= row["coverage_1sigma"] <= .78 and .88 <= row["coverage_1_96sigma"] <= .99 for row in p60_rows)
    p60_localization = all(row["uncertainty_error_spearman"] > .5 for row in p60_rows)
    p60_no_harm = all(row["belief_factor_r2"] >= row["visible_factor_r2"] - .02 for row in p60_rows)
    general_rows = [structural_post[family]["panels"][panel] for family in structural.FAMILIES for panel in ("P80", "P40")]
    p80_p40 = all(row["belief_factor_r2"] >= row["visible_factor_r2"] - .02 for row in general_rows) and sum(row["nll"] < row["prior_nll"] for row in general_rows) >= 3
    monotonic = all(structural_post[family]["monotonic_coordinate_fraction"] >= .75 for family in structural.FAMILIES)
    semantic_pass = semantics["legacy_parity_pass"] and semantics["structural_firewall_pass"] and not semantics["training_vs_structural"]["structural_target_eligible"]
    scalar_sufficient = True
    meaningful = False
    comparisons = {}
    for family in structural.FAMILIES:
        pre = structural_pre[family]["panels"]["P60"]
        post = structural_post[family]["panels"]["P60"]
        scaled = scalar[family]["P60"]
        neural_localization_gain = post["uncertainty_error_spearman"] - scaled["uncertainty_error_spearman"]
        scalar_family_sufficient = (
            scaled["sealed_nll"] <= post["nll"]
            and calibration_error(scaled) <= calibration_error(post)
            and neural_localization_gain < .05
        )
        scalar_sufficient &= scalar_family_sufficient
        family_meaningful = (
            post["uncertainty_error_spearman"] >= pre["uncertainty_error_spearman"] + .05
            or calibration_error(post) <= calibration_error(pre) - .10
            or post["nll"] <= pre["nll"] - .01
        )
        meaningful |= family_meaningful
        comparisons[family] = {
            "pre": pre, "scalar": scaled, "post": post,
            "post_minus_pre_localization": post["uncertainty_error_spearman"] - pre["uncertainty_error_spearman"],
            "post_minus_scalar_localization": neural_localization_gain,
            "scalar_family_sufficient": scalar_family_sufficient,
            "meaningful_neural_change": family_meaningful,
        }
    gates = {
        "measurement_semantics": semantic_pass, "ordinary_no_forgetting": ordinary_pass,
        "p60_proper_score": p60_proper, "p60_calibration": p60_calibration,
        "p60_uncertainty_localization": p60_localization, "p60_no_harm": p60_no_harm,
        "p80_p40_generalization": p80_p40, "uncertainty_monotonic": monotonic,
        "cross_panel_identity": cross["same_cell_compatibility_pass"],
        "union_uncertainty_reduction": cross["union_uncertainty_reduction_pass"],
    }
    if not semantic_pass:
        classification = "MEASUREMENT-SEMANTICS REGRESSION"
    elif meaningful and not ordinary_pass:
        classification = "STRUCTURAL-PANEL EXPOSURE CREATES ORDINARY-MISSINGNESS TRADEOFF"
    elif scalar_sufficient:
        classification = "SCALAR RECALIBRATION IS SUFFICIENT; NEURAL PANEL EXPOSURE NOT EARNED"
    elif all(gates.values()):
        classification = "STRUCTURAL-PANEL BELIEF EXPOSURE QUALIFIED; CORE RBB BELIEF GENERALIZES ACROSS OBSERVATION REGIMES"
    elif meaningful:
        classification = "STRUCTURAL-PANEL EXPOSURE IMPROVES BELIEF BUT DOES NOT FULLY QUALIFY"
    else:
        classification = "STRUCTURAL-PANEL BELIEF EXPOSURE FAILS"
    correlated_delta = [structural_post[family]["panels"][panel]["nll"] - structural_post[family]["panels"][panel]["diagonalized_nll"] for family in structural.FAMILIES for panel in structural.PANEL_ORDER]
    correlated = "EARNED" if float(np.median(correlated_delta)) < -1e-4 else "NOT EARNED"
    point_changes = [row["belief_minus_visible_factor_r2"] for row in p60_rows]
    point = "HARMFUL" if min(point_changes) < -.02 else ("MEANINGFUL" if max(point_changes) >= .01 else "NEGLIGIBLE")
    p20 = [structural_post[family]["panels"]["P20"] for family in structural.FAMILIES]
    p20_cal = all(.8 <= row["joint_scale"] <= 1.25 and .58 <= row["coverage_1sigma"] <= .78 and .88 <= row["coverage_1_96sigma"] <= .99 for row in p20)
    p20_class = "GRACEFUL" if p20_cal else ("UNCERTAIN BUT CALIBRATION-DEGRADED" if monotonic else "FALSELY CONFIDENT")
    secondary = {
        "correlated_component": correlated, "point_state_recovery": point,
        "scalar_recalibration": "SUFFICIENT" if scalar_sufficient else "INSUFFICIENT",
        "p20": p20_class, "cross_panel_identity": "SUPPORTED" if cross["same_cell_compatibility_pass"] else "NOT SUPPORTED",
    }
    return classification, gates, secondary, comparisons


def append_readout(payload: dict[str, Any]) -> None:
    path = Path("docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md")
    marker = "## RBB Belief-Only Structural-Panel Exposure"
    existing = path.read_text(encoding="utf-8")
    if marker in existing:
        raise RuntimeError("panel-exposure readout already exists")
    section = f"""

{marker}

One seed-{SEED} synthetic model received exactly 150 belief-only updates. Every effective batch
contained eight fixed 32-example strata: ordinary random/block replay plus random/coherent P80,
P60, and P40 panel simulation. The molecular ledger remained detached and hash-stable with zero
optimizer overlap and zero molecular gradients. Panel-simulated values were removed from model
input while an independent paired full-support observation supplied only the existing latent-state
residual target. No gene reconstruction target was introduced.

A single positive global covariance temperature was fitted on VALIDATION only across both panel
families and P80/P60/P40, then compared on SEALED data against the unchanged pre-exposure belief
and the panel-exposed belief. Factor labels were evaluation-only and SEALED was never used for
panel construction, training, scalar fitting, or checkpoint selection.

Primary classification: **{payload['classification']}**.

Correlated component: **{payload['secondary_classifications']['correlated_component']}**.
Point-state recovery: **{payload['secondary_classifications']['point_state_recovery']}**.
Scalar recalibration: **{payload['secondary_classifications']['scalar_recalibration']}**.
P20 stress: **{payload['secondary_classifications']['p20']}**.
Cross-panel identity: **{payload['secondary_classifications']['cross_panel_identity']}**.

This is one bounded synthetic belief-training probe. It does not establish real biological
validity, disease biology, causality, spatial validity, perturbation dynamics, or Stage81A3
completion. The prior trainable-encoder failure, frozen-encoder engineering failure,
frozen-recovery success, and forward-only structural-panel classification remain separate evidence.
"""
    base.atomic_text(path, existing.rstrip() + section + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--project-dir", type=Path, default=ROOT)
    args = parser.parse_args(); os.chdir(args.project_dir.resolve())
    if any(path.exists() for path in OUTPUTS.values()):
        raise RuntimeError("panel-exposure artifact exists; continuation forbidden")
    prior_hashes = verify_prior_evidence(); device = torch.device("cuda")
    torch.set_float32_matmul_precision("high"); torch.backends.cuda.matmul.allow_tf32 = True
    total_started = time.perf_counter(); torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    basis = base.load_basis(device); fixture = base.build_fixture(device); priors = base.frozen_family_statistics(device)
    banks, bank_audit = build_banks(fixture); evaluation_panels, evaluation_panel_audit = structural.build_panels(fixture)
    model, molecular_hashes, initial_belief_hash = initialize_model(device, priors)
    step0 = frozen.retention_row(0, model, fixture, device)
    if abs(step0["retention_ratio"] - 1.0020574895396623) > .01:
        raise RuntimeError("initialization retention parity failure")
    optimizer = torch.optim.AdamW(list(model.belief_parameters()), lr=1e-4, weight_decay=.01)
    optimizer_report = optimizer_audit(model, optimizer)
    if optimizer_report["molecular_optimizer_overlap"] != 0:
        raise RuntimeError("GRADIENT FIREWALL FAILURE")
    payload: dict[str, Any] = {
        "stage": "stage81a3_rbb_panel_exposure", "anchor": base.ANCHOR, "seed": SEED,
        "status": "initialized", "classification": None,
        "prior_evidence_hashes": prior_hashes, "molecular_hashes_step0": molecular_hashes,
        "belief_initialization_sha256": initial_belief_hash, "initial_retention": step0,
        "optimizer_firewall": optimizer_report, "panel_banks": bank_audit,
        "evaluation_panel_construction": evaluation_panel_audit,
        "scientific_contract": {"single_change": "belief exposure to structural-panel simulation", "models": 1, "seed_sweep": False, "hyperparameter_sweep": False, "real_rna": False, "pathology": False},
    }
    base.atomic_json(OUTPUTS["json"], payload)
    telemetry, retention, hash_rows, training = train(model, fixture, basis, banks, priors, optimizer, molecular_hashes, device, payload)
    retention_pass = all(row["retention_ratio"] >= .95 for row in retention) and abs(retention[-1]["retention_ratio"] - retention[0]["retention_ratio"]) <= .005
    checkpoint_metadata = {
        "anchor": base.ANCHOR, "seed": SEED, "updates": UPDATES, "r_max": R_MAX,
        "panel_bank_sha256": bank_audit["hashes"], "molecular_sha256": molecular_hashes,
        "basis_sha256": base.BASIS_HASH, "optimizer": "AdamW", "learning_rate": 1e-4,
        "weight_decay": .01, "effective_batch": EFFECTIVE_BATCH, "microbatch": MICROBATCH,
        "strata": {name: STRATUM_SIZE for name in STRATA},
    }
    checkpoint_hash = save_checkpoint(model, checkpoint_metadata)
    payload.update({"status": "checkpoint_persisted", "training": training, "retention": retention, "retention_pass": retention_pass, "molecular_hash_trajectory": hash_rows, "belief_checkpoint": {"path": str(OUTPUTS["checkpoint"]), "sha256": checkpoint_hash, "metadata": checkpoint_metadata}})
    base.atomic_json(OUTPUTS["json"], payload)

    ordinary_rows, ordinary_correlated, ordinary_summary = ordinary_evaluation(model, fixture, basis, banks, priors, device)
    base.atomic_csv(OUTPUTS["ordinary"], ordinary_rows); payload.update({"status": "ordinary_persisted", "ordinary_summary": ordinary_summary}); base.atomic_json(OUTPUTS["json"], payload)
    structural_rows, structural_correlated, structural_summary = structural_evaluation(model, fixture, basis, priors, evaluation_panels, device)
    base.atomic_csv(OUTPUTS["structural"], structural_rows); payload.update({"status": "structural_persisted", "structural_summary": structural_summary}); base.atomic_json(OUTPUTS["json"], payload)
    cross_rows, cross_summary = structural.cross_panel_audit(model, fixture, basis, priors["RANDOM_40"], device)
    base.atomic_csv(OUTPUTS["cross"], cross_rows); payload.update({"status": "cross_panel_persisted", "cross_panel_summary": cross_summary}); base.atomic_json(OUTPUTS["json"], payload)
    correlated_rows = ordinary_correlated + structural_correlated; base.atomic_csv(OUTPUTS["correlated"], correlated_rows)

    pre_model = load_preexposure_model(device, priors)
    scalar_temperature, scalar_rows, scalar_summary = fit_scalar_control(pre_model, fixture, basis, priors, evaluation_panels, device)
    base.atomic_csv(OUTPUTS["scalar"], scalar_rows)
    pre_report = json.loads(Path("results/v4/stage81a3_rbb_structural_panel_audit.json").read_text(encoding="utf-8"))
    pre_summary = {family: {"panels": {row["panel"]: row for row in pre_report["panel_summary"] if row["family"] == family}} for family in structural.FAMILIES}
    semantics = structural.parity_and_firewalls(model, fixture, basis, priors["RANDOM_40"], device)
    classification, gates, secondary, comparisons = classify(ordinary_summary, structural_summary, pre_summary, scalar_summary, semantics, cross_summary)
    molecular_hashes_final = frozen.frozen_hashes(model)
    gradients_pass = all(row["maximum_absolute_molecular_gradient"] == 0 for row in training["gradient_firewall"])
    hashes_pass = all({key: row[key] for key in molecular_hashes} == molecular_hashes for row in hash_rows) and molecular_hashes_final == molecular_hashes
    if not gradients_pass or not hashes_pass:
        classification = "GRADIENT FIREWALL FAILURE"
    if not retention_pass:
        classification = "ENGINEERING / NUMERICAL FAILURE"
    severe = [row["gaussian_severe_fraction"] for row in structural_rows if row["panel"] in structural.PRIMARY]
    payload.update({
        "status": "complete", "classification": classification, "primary_gates": {**gates, "gradient_firewall": gradients_pass and hashes_pass, "token_retention": retention_pass},
        "secondary_classifications": secondary, "p60_three_way_comparison": comparisons,
        "scalar_recalibration": {"variance_temperature": scalar_temperature, "fit_split": "VALIDATION", "shared_across_families_and_p80_p60_p40": True, "sealed_used_for_fit": False, "posterior_mean_changed": False, "uncertainty_ranking_changed": False, "summary": scalar_summary},
        "measurement_semantics_reaudit": semantics, "gaussian_adequacy": {"maximum_primary_severe_fraction": max(severe), "family_concern": max(severe) >= .25},
        "counterfactual_sidecar": {"run": False, "reason": "optional compute omitted; prior NOT SUPPORTED evidence unchanged"},
        "complexity_decision": {"correlated_component": secondary["correlated_component"], "three_converging_negative_results": secondary["correlated_component"] == "NOT EARNED", "candidate_for_removal_before_final_a3_freeze": secondary["correlated_component"] == "NOT EARNED", "human_decision_required": True},
        "governance": {"stage81a3_complete": False, "stage81a3_frozen": False, "stage81b_started": False, "panel_exposure_models": 1, "belief_updates": UPDATES, "molecular_updates": 0, "real_rna_accessed": False, "pathology_opened": False, "factor_labels_used_for_training": False, "sealed_used_for_fitting": False},
        "total_wall_seconds": time.perf_counter() - total_started,
    })
    base.atomic_json(OUTPUTS["json"], payload); append_readout(payload)
    print(json.dumps({"classification": classification, "gates": payload["primary_gates"], "secondary": secondary, "checkpoint_sha256": checkpoint_hash, "scalar_temperature": scalar_temperature}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
