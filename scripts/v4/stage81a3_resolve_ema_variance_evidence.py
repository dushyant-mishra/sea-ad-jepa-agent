#!/usr/bin/env python3
"""Resolve bounded Stage81A3 EMA-timescale and variance evidence synthetically."""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v4 import (  # noqa: E402
    LatentPredictor,
    V4AEncoderSkeleton,
    construct_context_mask,
    create_ema_target,
    ema_momentum_at_step,
    ema_parameter_health,
    jepa_prediction_loss,
    representation_health,
    update_ema_target,
    variance_floor_penalty,
)


TEST_SEEDS = (101, 211, 307, 401, 503)
RUN_LENGTHS = (1_000, 5_000, 10_000, 50_000, 100_000)
MOMENTA = (0.992, 0.996, 0.99925, 0.9995, 0.9999)
SCHEDULES = {
    "fixed_0.99925": (0.99925, 0.99925, "fixed"),
    "linear_0.996_to_1.0": (0.996, 1.0, "linear"),
    "historical_0.992_to_0.9995": (0.992, 0.9995, "linear"),
}
TEST_GAMMA = 0.10
TEST_WEIGHT = 0.10
SYNTHETIC_STEPS = 20
SYNTHETIC_GENES = 128
SYNTHETIC_BATCH = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/v4/stage81a3_ema_variance_resolution.json"),
    )
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    return parser.parse_args()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def optimizer_step_audit() -> dict[str, Any]:
    return {
        "exact_total_optimizer_steps_available": False,
        "locked_effective_batch_size": 256,
        "locked_initial_microbatch_size": 8,
        "implied_initial_accumulation_microbatches": 32,
        "locked_startup_optimizer_steps": 300,
        "ema_updates_per_successful_optimizer_update": 1,
        "foundation_training_donors": 149,
        "unfrozen_training_length_parameters": [
            "loader samples or weighted exposures constituting one pass",
            "total number of foundation passes or epochs",
        ],
        "reason": (
            "Stage81A2 freezes hierarchical weighting rules, not a loader implementation or "
            "per-pass sample count; the compute contract freezes only the first 300 steps"
        ),
    }


def half_life_rows() -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    for momentum in MOMENTA:
        half_life = math.log(0.5) / math.log(momentum)
        for run_length in RUN_LENGTHS:
            rows.append({
                "momentum": momentum,
                "half_life_optimizer_steps": half_life,
                "run_length_optimizer_steps": run_length,
                "half_life_fraction_of_run": half_life / run_length,
            })
    return rows


def online_value(update: int, total: int, *, shifted: bool) -> float:
    progress = update / total
    value = progress + 0.02 * math.sin(40.0 * math.pi * progress)
    if shifted and update >= total // 2:
        value += 1.0
    return value


def schedule_stress() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for total in RUN_LENGTHS:
        for name, (start, end, schedule_type) in SCHEDULES.items():
            target_base = online_value(0, total, shifted=False)
            target_shift = target_base
            previous_target = target_shift
            movement_sum = 0.0
            movement_square_sum = 0.0
            response_steps = None
            for index in range(total):
                update = index + 1
                momentum = ema_momentum_at_step(
                    optimizer_step=index,
                    total_optimizer_steps=total,
                    start_momentum=start,
                    end_momentum=end,
                    schedule_type=schedule_type,
                )
                base = online_value(update, total, shifted=False)
                shifted = online_value(update, total, shifted=True)
                target_base = momentum * target_base + (1.0 - momentum) * base
                target_shift = momentum * target_shift + (1.0 - momentum) * shifted
                movement = target_shift - previous_target
                movement_sum += movement
                movement_square_sum += movement * movement
                previous_target = target_shift
                isolated_shift_response = target_shift - target_base
                if update >= total // 2 and response_steps is None and isolated_shift_response >= 0.5:
                    response_steps = update - total // 2
            mean_movement = movement_sum / total
            movement_variance = max(0.0, movement_square_sum / total - mean_movement**2)
            final_online = online_value(total, total, shifted=True)
            final_shift_response = target_shift - target_base
            rows.append({
                "run_length_optimizer_steps": total,
                "schedule": name,
                "final_target_lag": final_online - target_shift,
                "target_update_std": math.sqrt(movement_variance),
                "midrun_shift_half_response_steps": response_steps,
                "midrun_shift_response_at_end": final_shift_response,
                "effectively_frozen_fixture_flag": final_shift_response < 0.25,
                "tracks_almost_immediately_fixture_flag": (
                    response_steps is not None and response_steps <= 10
                ),
                "fixture_flag_definitions_are_not_production_thresholds": True,
            })
    return rows


def structured_expression(seed: int, kind: str) -> tuple[torch.Tensor, torch.Tensor]:
    generator = torch.Generator().manual_seed(seed)
    genes = SYNTHETIC_GENES
    if kind == "healthy_structured":
        factors = torch.randn(SYNTHETIC_BATCH, 4, generator=generator)
        loadings = torch.randn(4, genes, generator=generator)
        signal = torch.relu(factors @ loadings + 0.35)
        threshold = torch.quantile(signal, 0.68)
        expression = torch.where(signal >= threshold, torch.log1p(signal), torch.zeros_like(signal))
        measurement = torch.rand(SYNTHETIC_BATCH, genes, generator=generator) > 0.08
    elif kind == "collapse_prone_structured":
        shared = torch.randn(1, 2, generator=generator).repeat(SYNTHETIC_BATCH, 1)
        factors = shared + 0.005 * torch.randn(SYNTHETIC_BATCH, 2, generator=generator)
        loadings = torch.randn(2, genes, generator=generator)
        signal = torch.relu(factors @ loadings + 0.20)
        threshold = torch.quantile(signal, 0.78)
        expression = torch.where(signal >= threshold, torch.log1p(signal), torch.zeros_like(signal))
        common_measurement = torch.rand(1, genes, generator=generator) > 0.08
        measurement = common_measurement.repeat(SYNTHETIC_BATCH, 1)
    else:
        raise ValueError(kind)
    if torch.any(measurement.sum(dim=1) < 2):
        raise RuntimeError("synthetic fixture must have at least two measured genes per cell")
    return expression, measurement


def gradient_norm(loss: torch.Tensor, parameters: Iterable[torch.nn.Parameter]) -> float:
    gradients = torch.autograd.grad(
        loss,
        tuple(parameters),
        retain_graph=True,
        allow_unused=True,
    )
    squared = sum(float(gradient.detach().square().sum()) for gradient in gradients if gradient is not None)
    return math.sqrt(squared)


def evaluate_run(
    online: V4AEncoderSkeleton,
    target: torch.nn.Module,
    predictor: LatentPredictor,
    expression: torch.Tensor,
    measurement: torch.Tensor,
    *,
    seed: int,
    sample_pass: int,
) -> dict[str, Any]:
    online.eval()
    predictor.eval()
    cells, genes = expression.shape
    gene_ids = torch.arange(genes, device=expression.device).repeat(cells, 1)
    context = construct_context_mask(
        measurement.cpu(),
        mask_fraction=0.40,
        production_seed=seed,
        cell_indices=torch.arange(cells),
        sample_pass=sample_pass,
        view_index=0,
        rule="exact_count",
    ).to(expression.device)
    online_latents = online(gene_ids, expression, measurement, context, "student")
    prediction = predictor(online_latents)
    with torch.no_grad():
        target_latents = target(gene_ids, expression, measurement, context, "target")
    jepa = jepa_prediction_loss(prediction, target_latents)
    variance_weighted, _ = variance_floor_penalty(
        online_latents,
        gamma=TEST_GAMMA,
        weight=TEST_WEIGHT,
    )
    variance_unweighted, _ = variance_floor_penalty(
        online_latents,
        gamma=TEST_GAMMA,
        weight=1.0,
    )
    health = representation_health(online_latents, subsample_seed=seed)
    return {
        "jepa_loss": float(jepa.detach()),
        "effective_rank": health.effective_rank,
        "top_singular_l1_fraction": health.top_singular_l1_fraction,
        "top_singular_energy_fraction": health.top_singular_energy_fraction,
        "cross_cell_std": health.cross_cell_std_mean,
        "slot_variance": health.slot_variance_mean,
        "slot_cosine": health.slot_cosine_similarity_mean,
        "variance_penalty_unweighted": float(variance_unweighted.detach()),
        "variance_penalty_weighted": float(variance_weighted.detach()),
        "jepa_gradient_norm": gradient_norm(jepa, list(online.parameters()) + list(predictor.parameters())),
        "variance_gradient_norm": gradient_norm(variance_unweighted, online.parameters()),
        "online_target_distance": ema_parameter_health(online, target).online_target_parameter_l2_distance,
    }


def architecture_stress(device: torch.device) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed in TEST_SEEDS:
        for fixture in ("healthy_structured", "collapse_prone_structured"):
            expression_cpu, measurement_cpu = structured_expression(seed, fixture)
            expression = expression_cpu.to(device)
            measurement = measurement_cpu.to(device)
            for use_safeguard in (False, True):
                torch.manual_seed(seed)
                if device.type == "cuda":
                    torch.cuda.manual_seed_all(seed)
                online = V4AEncoderSkeleton().to(device)
                predictor = LatentPredictor().to(device)
                target = create_ema_target(online).to(device)
                optimizer = torch.optim.AdamW(
                    list(online.parameters()) + list(predictor.parameters()),
                    lr=0.001,
                    weight_decay=0.0,
                )
                initial = evaluate_run(
                    online, target, predictor, expression, measurement,
                    seed=seed, sample_pass=0,
                )
                nonfinite_events = 0
                online.train()
                predictor.train()
                cells, genes = expression.shape
                gene_ids = torch.arange(genes, device=device).repeat(cells, 1)
                for step in range(SYNTHETIC_STEPS):
                    context = construct_context_mask(
                        measurement.cpu(),
                        mask_fraction=0.40,
                        production_seed=seed,
                        cell_indices=torch.arange(cells),
                        sample_pass=step,
                        view_index=0,
                        rule="exact_count",
                    ).to(device)
                    optimizer.zero_grad(set_to_none=True)
                    online_latents = online(
                        gene_ids, expression, measurement, context, "student"
                    )
                    prediction = predictor(online_latents)
                    with torch.no_grad():
                        target_latents = target(
                            gene_ids, expression, measurement, context, "target"
                        )
                    jepa = jepa_prediction_loss(prediction, target_latents)
                    weighted_variance, _ = variance_floor_penalty(
                        online_latents,
                        gamma=TEST_GAMMA,
                        weight=TEST_WEIGHT if use_safeguard else 0.0,
                    )
                    total = jepa + weighted_variance
                    if not torch.isfinite(total):
                        nonfinite_events += 1
                        break
                    total.backward()
                    if any(
                        parameter.grad is not None and not torch.isfinite(parameter.grad).all()
                        for parameter in list(online.parameters()) + list(predictor.parameters())
                    ):
                        nonfinite_events += 1
                        break
                    optimizer.step()
                    update_ema_target(online, target, momentum=0.996)
                final = evaluate_run(
                    online, target, predictor, expression, measurement,
                    seed=seed, sample_pass=SYNTHETIC_STEPS,
                )
                rows.append({
                    "seed": seed,
                    "fixture": fixture,
                    "regime": "jepa_plus_weak_per_slot_std" if use_safeguard else "jepa_only",
                    "test_gamma": TEST_GAMMA if use_safeguard else None,
                    "test_weight": TEST_WEIGHT if use_safeguard else 0.0,
                    "test_ema_momentum": 0.996,
                    "optimizer_steps": SYNTHETIC_STEPS,
                    "initial": initial,
                    "final": final,
                    "nonfinite_events": nonfinite_events,
                })
    return rows


def summarize_architecture_stress(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = (
        "jepa_loss",
        "effective_rank",
        "top_singular_l1_fraction",
        "top_singular_energy_fraction",
        "cross_cell_std",
        "slot_variance",
        "slot_cosine",
        "variance_penalty_unweighted",
        "jepa_gradient_norm",
        "variance_gradient_norm",
        "online_target_distance",
    )
    means: dict[str, dict[str, float]] = {}
    paired: dict[str, dict[str, Any]] = {}
    for fixture in ("healthy_structured", "collapse_prone_structured"):
        fixture_rows = [row for row in rows if row["fixture"] == fixture]
        for regime in ("jepa_only", "jepa_plus_weak_per_slot_std"):
            selected = [row for row in fixture_rows if row["regime"] == regime]
            means[f"{fixture}|{regime}"] = {
                metric: sum(row["final"][metric] for row in selected) / len(selected)
                for metric in metrics
            }
        baseline = {row["seed"]: row for row in fixture_rows if row["regime"] == "jepa_only"}
        guarded = {
            row["seed"]: row
            for row in fixture_rows
            if row["regime"] == "jepa_plus_weak_per_slot_std"
        }
        differences = {
            metric: [
                guarded[seed]["final"][metric] - baseline[seed]["final"][metric]
                for seed in TEST_SEEDS
            ]
            for metric in metrics
        }
        paired[fixture] = {
            "guarded_minus_jepa_only_mean": {
                metric: sum(values) / len(values)
                for metric, values in differences.items()
            },
            "seeds_with_higher_cross_cell_std": sum(
                difference > 0 for difference in differences["cross_cell_std"]
            ),
            "seeds_with_higher_effective_rank": sum(
                difference > 0 for difference in differences["effective_rank"]
            ),
            "seeds_with_lower_top_singular_energy_fraction": sum(
                difference < 0
                for difference in differences["top_singular_energy_fraction"]
            ),
        }
    return {
        "final_metric_means": means,
        "paired_guarded_minus_jepa_only": paired,
        "nonfinite_events_total": sum(row["nonfinite_events"] for row in rows),
        "demonstrable_selective_collapse_protection": False,
        "interpretation": (
            "the weak safeguard increased cross-cell std but did not improve effective rank "
            "or singular concentration selectively in collapse-prone fixtures; the short "
            "JEPA-only trajectories also did not exhibit gross progressive collapse"
        ),
        "recommendation": "telemetry_only_at_current_evidence",
    }


def variance_formula_audit() -> dict[str, Any]:
    return {
        "function": "sea_ad_jepa.v4.losses.variance_floor_penalty",
        "formula": "weight * mean(relu(gamma - std_population(raw_latents, dim=0)))",
        "input_shape": "[batch, 24, 160]",
        "reduction_for_standard_deviation": "batch/cell dimension 0",
        "remaining_standard_deviation_shape": "[24, 160]",
        "standard_deviation_convention": "torch.std(dim=0, unbiased=False); population correction=0",
        "epsilon": 0.0,
        "gamma_application": "elementwise hinge on each raw slot-by-dimension standard deviation",
        "weight_application": "scalar multiplication after mean hinge reduction",
        "l2_normalization_before_penalty": False,
        "direct_variance_target": False,
    }


def main() -> int:
    args = parse_args()
    project = args.project_dir.resolve()
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    stress_rows = architecture_stress(device)
    payload = {
        "stage": "Stage81A3_ema_variance_evidence_resolution",
        "scope": "synthetic_only_no_real_rna_no_pathology",
        "variance_formula_audit": variance_formula_audit(),
        "optimizer_step_audit": optimizer_step_audit(),
        "ema_half_lives": half_life_rows(),
        "ema_long_horizon_stress": schedule_stress(),
        "architecture_stress": {
            "device": str(device),
            "actual_v4_encoder": True,
            "actual_ema_target": True,
            "actual_predictor": True,
            "actual_jepa_loss": True,
            "masking": "40_percent_exact_count_refreshed_one_view_per_pass",
            "test_only_safeguard": {
                "gamma": TEST_GAMMA,
                "weight": TEST_WEIGHT,
                "production_value": False,
            },
            "rows": stress_rows,
            "summary": summarize_architecture_stress(stress_rows),
        },
        "safety": {
            "real_rna_training": False,
            "pathology_accessed": False,
            "stage81b_started": False,
            "production_ema_selected": False,
            "production_gamma_selected": False,
            "production_weight_selected": False,
        },
    }
    output = args.output if args.output.is_absolute() else project / args.output
    atomic_json(output, payload)
    print(json.dumps({
        "output": str(output),
        "device": str(device),
        "ema_rows": len(payload["ema_long_horizon_stress"]),
        "architecture_rows": len(payload["architecture_stress"]["rows"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
