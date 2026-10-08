#!/usr/bin/env python3
"""Run bounded synthetic Stage81A3 policy calibration without RNA training."""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v4 import (  # noqa: E402
    LatentPredictor,
    construct_context_mask,
    covariance_calibration,
    ema_momentum_at_step,
    variance_floor_calibration,
)


TEST_SEEDS = (101, 211, 307, 401, 503)
BATCH_SIZES = (4, 8, 16, 32, 64, 256)
VARIANCE_FORMULATIONS = ("pooled_cell", "per_slot", "flattened_cell_slot", "combined")
COVARIANCE_FORMULATIONS = ("pooled_cell", "per_slot", "flattened_cell_slot")
TEST_GAMMAS = (0.05, 0.10, 0.25, 0.50, 1.00)
TEST_WEIGHTS = (0.001, 0.01, 0.1, 1.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/v4/stage81a3_remaining_mechanics_calibration.json"),
    )
    return parser.parse_args()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def trajectory_positions(kind: str, steps: int = 20) -> list[float]:
    if kind == "smooth_monotonic":
        return [0.1 * step for step in range(steps + 1)]
    if kind == "noisy_trend":
        noise = (0.0, 0.08, -0.06, 0.04, -0.03)
        return [0.1 * step + noise[step % len(noise)] for step in range(steps + 1)]
    if kind == "oscillatory":
        return [0.03 * step + (0.25 if step % 2 else -0.25) for step in range(steps + 1)]
    if kind == "abrupt_shift":
        return [0.0 if step < steps // 2 else 2.0 for step in range(steps + 1)]
    if kind == "very_small_updates":
        return [0.001 * step for step in range(steps + 1)]
    if kind == "occasional_large_update":
        values = [0.0]
        for step in range(1, steps + 1):
            values.append(values[-1] + (0.8 if step in {7, 14} else 0.02))
        return values
    raise ValueError(kind)


def ema_stress() -> dict[str, Any]:
    schedules = {
        "fixed_0.996_fixture": (0.996, 0.996, "fixed"),
        "historical_0.992_to_0.9995": (0.992, 0.9995, "linear"),
        "reference_0.996_to_1.0": (0.996, 1.0, "linear"),
        "proposal_0.996_to_0.9999": (0.996, 0.9999, "linear"),
    }
    rows = []
    steps = 20
    for trajectory_name in (
        "smooth_monotonic", "noisy_trend", "oscillatory", "abrupt_shift",
        "very_small_updates", "occasional_large_update",
    ):
        online = trajectory_positions(trajectory_name, steps)
        for schedule_name, (start, end, schedule_type) in schedules.items():
            target = online[0]
            target_values = [target]
            follow = []
            for update_index in range(steps):
                momentum = ema_momentum_at_step(
                    optimizer_step=update_index,
                    total_optimizer_steps=steps,
                    start_momentum=start,
                    end_momentum=end,
                    schedule_type=schedule_type,
                )
                pre_gap = abs(online[update_index + 1] - target)
                updated = momentum * target + (1 - momentum) * online[update_index + 1]
                follow.append(abs(updated - target) / max(pre_gap, 1e-12))
                target = updated
                target_values.append(target)
            target_steps = torch.diff(torch.tensor(target_values, dtype=torch.float64))
            online_steps = torch.diff(torch.tensor(online, dtype=torch.float64))
            response = None
            if trajectory_name == "abrupt_shift":
                shift_step = steps // 2
                for index in range(shift_step, len(target_values)):
                    if target_values[index] >= 1.0:
                        response = index - shift_step
                        break
            rows.append({
                "trajectory": trajectory_name,
                "schedule": schedule_name,
                "online_movement": float(online_steps.abs().sum()),
                "target_movement": float(target_steps.abs().sum()),
                "final_online_target_distance": abs(online[-1] - target_values[-1]),
                "normalized_final_distance": abs(online[-1] - target_values[-1]) / max(abs(online[-1]), 1e-12),
                "mean_target_follow_fraction": sum(follow) / len(follow),
                "target_movement_variance": float(target_steps.var(unbiased=False)),
                "final_target_lag": online[-1] - target_values[-1],
                "abrupt_shift_half_response_updates": response,
                "final_target": target_values[-1],
                "nearly_identical_to_online_fixture_flag": (
                    abs(online[-1] - target_values[-1])
                    / max(abs(online[-1]), 1e-12) < 0.01
                ),
                "extremely_stale_fixture_flag": (
                    abs(online[-1] - target_values[-1])
                    / max(abs(online[-1]), 1e-12) > 0.90
                ),
            })
    final_gap = 5.0
    return {
        "rows": rows,
        "last_step_endpoint_comparison": {
            "pre_update_gap": final_gap,
            "target_update_if_m_1": 0.0,
            "target_update_if_m_0_9999": (1 - 0.9999) * final_gap,
            "difference": (1 - 0.9999) * final_gap,
            "interpretation": "difference_exists_only_in_final_target_state_when_no_later_update_occurs",
        },
        "production_schedule_selected": False,
        "fixture_only_flag_thresholds": {
            "nearly_identical_normalized_distance_lt": 0.01,
            "extremely_stale_normalized_distance_gt": 0.90,
            "not_production_thresholds": True,
        },
    }


def synthetic_fixtures(seed: int, cells: int, slots: int = 8, width: int = 16) -> dict[str, torch.Tensor]:
    generator = torch.Generator().manual_seed(seed)
    healthy = torch.randn(cells, slots, width, generator=generator)
    cell_collapse = torch.randn(1, slots, width, generator=generator).repeat(cells, 1, 1)
    slot_collapse = torch.randn(cells, 1, width, generator=generator).repeat(1, slots, 1)
    both = torch.ones(cells, slots, width)
    coefficients = torch.randn(cells, 2, generator=generator)
    basis = torch.randn(2, slots * width, generator=generator)
    low_rank = (coefficients @ basis).reshape(cells, slots, width)
    direction = torch.randn(cells, slots * width, generator=generator)
    constant_norm = (10 * direction / direction.norm(dim=1, keepdim=True)).reshape(cells, slots, width)
    dominant = healthy + 4 * torch.randn(cells, 1, 1, generator=generator)
    near_collapse = cell_collapse + 0.01 * torch.randn(cells, slots, width, generator=generator)
    return {
        "healthy": healthy, "cell_collapse": cell_collapse,
        "slot_collapse": slot_collapse, "both": both, "low_rank": low_rank,
        "constant_norm": constant_norm, "rescaled_healthy": healthy * 0.05,
        "dominant_direction": dominant, "near_collapse": near_collapse,
    }


def variance_calibration() -> dict[str, Any]:
    registry = []
    base = synthetic_fixtures(101, 32)
    for fixture_name, tensor in base.items():
        if fixture_name == "near_collapse":
            continue
        for formulation in VARIANCE_FORMULATIONS:
            value = variance_floor_calibration(tensor, gamma=0.5, formulation=formulation)
            registry.append({"fixture": fixture_name, "formulation": formulation, "test_gamma": 0.5, "penalty": float(value)})
    batch_rows = []
    for cells in BATCH_SIZES:
        for formulation in VARIANCE_FORMULATIONS:
            penalties, gradients, collapse_penalties = [], [], []
            for seed in TEST_SEEDS:
                fixture = synthetic_fixtures(seed, cells, slots=4, width=8)
                healthy = fixture["healthy"].requires_grad_()
                value = variance_floor_calibration(healthy, gamma=0.5, formulation=formulation)
                gradient = torch.autograd.grad(value, healthy)[0]
                penalties.append(float(value)); gradients.append(float(gradient.norm()))
                collapse_penalties.append(float(variance_floor_calibration(fixture["cell_collapse"], gamma=0.5, formulation=formulation)))
            batch_rows.append({
                "batch_size": cells, "formulation": formulation,
                "penalty_mean": float(torch.tensor(penalties).mean()),
                "penalty_std": float(torch.tensor(penalties).std(unbiased=False)),
                "gradient_norm_mean": float(torch.tensor(gradients).mean()),
                "gradient_norm_std": float(torch.tensor(gradients).std(unbiased=False)),
                "nonzero_healthy_penalty_frequency": sum(value > 1e-8 for value in penalties) / len(penalties),
                "cell_collapse_penalty_mean": float(torch.tensor(collapse_penalties).mean()),
            })
    gamma_rows = []
    for formulation in VARIANCE_FORMULATIONS:
        for gamma in TEST_GAMMAS:
            for fixture_name in ("healthy", "low_rank", "near_collapse", "cell_collapse"):
                tensor = base[fixture_name].clone().requires_grad_()
                value = variance_floor_calibration(tensor, gamma=gamma, formulation=formulation)
                gradient = torch.autograd.grad(value, tensor)[0]
                gamma_rows.append({
                    "formulation": formulation, "test_gamma": gamma,
                    "fixture": fixture_name, "penalty": float(value),
                    "gradient_norm": float(gradient.norm()),
                })
    weight_rows = []
    generator = torch.Generator().manual_seed(701)
    target = torch.randn(16, 8, 16, generator=generator)
    for fixture_name, prediction_base in (
        ("healthy", torch.randn(16, 8, 16, generator=generator)),
        ("near_collapse", 0.02 * torch.randn(16, 8, 16, generator=generator)),
        ("recoverable_collapse", 0.001 * torch.randn(16, 8, 16, generator=generator)),
    ):
        prediction = prediction_base.requires_grad_()
        primary = (prediction - target).square().mean()
        primary_norm = float(torch.autograd.grad(primary, prediction, retain_graph=True)[0].norm())
        variance = variance_floor_calibration(prediction, gamma=0.5, formulation="per_slot")
        variance_norm = float(torch.autograd.grad(variance, prediction)[0].norm())
        for weight in TEST_WEIGHTS:
            weight_rows.append({
                "fixture": fixture_name, "test_weight": weight,
                "jepa_gradient_norm": primary_norm,
                "weighted_variance_gradient_norm": weight * variance_norm,
                "gradient_ratio": weight * variance_norm / max(primary_norm, 1e-12),
            })
    return {
        "failure_registry": registry,
        "batch_stability": batch_rows,
        "gamma_sensitivity": gamma_rows,
        "weight_sensitivity": weight_rows,
        "weight_sensitivity_formulation": "per_slot",
        "weight_sensitivity_gamma": 0.5,
        "production_gamma_selected": False,
        "production_weight_selected": False,
    }


def covariance_stability() -> dict[str, Any]:
    rows = []
    for formulation in COVARIANCE_FORMULATIONS:
        references = {}
        for seed in TEST_SEEDS:
            reference = synthetic_fixtures(seed, 256, slots=4, width=16)["healthy"]
            references[seed] = float(covariance_calibration(reference, formulation=formulation))
        for cells in BATCH_SIZES:
            values, gradients, deviations = [], [], []
            for seed in TEST_SEEDS:
                tensor = synthetic_fixtures(seed, cells, slots=4, width=16)["healthy"].requires_grad_()
                value = covariance_calibration(tensor, formulation=formulation)
                gradient = torch.autograd.grad(value, tensor)[0]
                values.append(float(value)); gradients.append(float(gradient.norm()))
                deviations.append(abs(float(value) - references[seed]))
            rows.append({
                "batch_size": cells, "formulation": formulation,
                "penalty_mean": float(torch.tensor(values).mean()),
                "penalty_std": float(torch.tensor(values).std(unbiased=False)),
                "gradient_norm_mean": float(torch.tensor(gradients).mean()),
                "gradient_norm_std": float(torch.tensor(gradients).std(unbiased=False)),
                "mean_abs_difference_from_b256": float(torch.tensor(deviations).mean()),
            })
    generator = torch.Generator().manual_seed(812)
    independent = torch.randn(64, 4, 16, generator=generator)
    correlated = independent.clone(); correlated[..., 1] = correlated[..., 0]
    correlation_check = {
        formulation: {
            "independent": float(covariance_calibration(independent, formulation=formulation)),
            "known_correlated": float(covariance_calibration(correlated, formulation=formulation)),
        }
        for formulation in COVARIANCE_FORMULATIONS
    }
    return {
        "batch_stability": rows,
        "known_correlation_check": correlation_check,
        "production_covariance_penalty_selected": False,
    }


def masking_calibration(project: Path) -> dict[str, Any]:
    summary_path = project / "results/v4/stage81a3_masking_calibration_summary.csv"
    summary = pd.read_csv(summary_path)
    fields = [
        "mask_fraction", "n_mask_evaluations", "n_unique_cells",
        "visible_detected_genes_p50", "visible_detected_genes_p05",
        "fraction_transformed_signal_retained_p50",
        "fraction_cells_below_500_visible_detected",
    ]
    classifications = {
        "0.15": "POSSIBLY_TOO_EASY", "0.25": "PLAUSIBLE",
        "0.4": "LEADING_CANDIDATE", "0.5": "AGGRESSIVE",
        "0.6": "AGGRESSIVE", "0.7": "REJECT_FOR_BASELINE",
    }
    synthetic = []
    for measured_genes in (20, 200):
        measurement = torch.ones(1000, measured_genes, dtype=torch.bool)
        cells = torch.arange(1000)
        for rule in ("exact_count", "bernoulli"):
            counts = construct_context_mask(
                measurement, mask_fraction=0.4, production_seed=9901,
                cell_indices=cells, sample_pass=0, view_index=0, rule=rule,
            ).sum(dim=1).float()
            synthetic.append({
                "measured_genes": measured_genes, "rule": rule,
                "masked_fraction_mean": float((counts / measured_genes).mean()),
                "masked_fraction_std": float((counts / measured_genes).std(unbiased=False)),
                "masked_count_min": int(counts.min()), "masked_count_max": int(counts.max()),
                "probability_masked_fraction_ge_0_50": float(
                    ((counts / measured_genes) >= 0.50).float().mean()
                ),
                "same_key_reproducible": bool(torch.equal(
                    counts.to(torch.int64),
                    construct_context_mask(
                        measurement, mask_fraction=0.4, production_seed=9901,
                        cell_indices=cells, sample_pass=0, view_index=0, rule=rule,
                    ).sum(dim=1),
                )),
            })
    return {
        "existing_exact_count_calibration": summary[fields].to_dict(orient="records"),
        "pathology_blind_information_classification": classifications,
        "synthetic_rule_comparison": synthetic,
        "calibration_rule": "exact_count_floor_fraction_of_measured_genes_after_sha256_seeded_permutation",
        "synthetic_severe_mask_definition": "realized_masked_fraction_ge_0.50",
        "computational_interpretation": (
            "exact_count requires a deterministic permutation; Bernoulli requires one "
            "deterministic draw per measured gene"
        ),
        "production_fraction_selected": False,
        "production_seed_selected": False,
        "production_view_count_selected": False,
    }


def slot_collapse_probe() -> dict[str, Any]:
    torch.manual_seed(5501)
    context = torch.randn(8, 24, 160)
    collapsed_target = context.mean(dim=1, keepdim=True).repeat(1, 24, 1)
    predictor = LatentPredictor()
    optimizer = torch.optim.AdamW(predictor.parameters(), lr=0.01, weight_decay=0.0)
    with torch.no_grad():
        initial_prediction = predictor(context)
        initial_loss = float((initial_prediction - collapsed_target).square().mean())
        initial_variance = float(initial_prediction.var(dim=1, unbiased=False).mean())
    loss = torch.tensor(float("nan"))
    for _ in range(100):
        optimizer.zero_grad(set_to_none=True)
        prediction = predictor(context)
        loss = (prediction - collapsed_target).square().mean()
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        final_prediction = predictor(context)
        final_loss = float((final_prediction - collapsed_target).square().mean())
        final_variance = float(final_prediction.var(dim=1, unbiased=False).mean())
    return {
        "probe_target": "same_within_cell_latent_repeated_across_24_slots",
        "optimized_component": "LatentPredictor",
        "optimizer_steps": 100,
        "initial_objective": initial_loss,
        "final_objective": final_loss,
        "initial_predicted_slot_variance": initial_variance,
        "final_predicted_slot_variance": final_variance,
        "objective_reduction_fraction": 1.0 - final_loss / initial_loss,
        "slot_variance_reduction_fraction": 1.0 - final_variance / initial_variance,
        "synthetic_predictor_can_express_slot_collapse": (
            final_loss < 0.25 * initial_loss
            and final_variance < 0.25 * initial_variance
        ),
        "biological_slot_collapse_demonstrated": False,
        "slot_repulsion_mechanically_required": False,
        "interpretation": (
            "predictor susceptibility under an explicitly collapse-seeking synthetic objective; "
            "this does not establish collapse under the proposed JEPA objective"
        ),
        "production_slot_repulsion_selected": False,
    }


def main() -> int:
    args = parse_args()
    project = args.project_dir.resolve()
    payload = {
        "stage": "Stage81A3_remaining_mechanics_calibration",
        "stage81a2_parent": "808ce4f170055c5568cc5c1e0e3a56415b52f908",
        "evidence_scope": "synthetic_and_existing_pathology_blind_masking_calibration_only",
        "ema_schedule_stress": ema_stress(),
        "variance": variance_calibration(),
        "covariance": covariance_stability(),
        "masking": masking_calibration(project),
        "slot_collapse_probe": slot_collapse_probe(),
        "safety": {
            "real_rna_training": False,
            "stage81b_started": False,
            "pathology_accessed": False,
            "production_seed_selected": False,
            "production_ema_selected": False,
            "production_variance_policy_selected": False,
            "production_covariance_penalty_selected": False,
            "production_masking_policy_selected": False,
        },
    }
    output = args.output if args.output.is_absolute() else project / args.output
    atomic_json(output, payload)
    print(json.dumps({
        "output": str(output),
        "ema_rows": len(payload["ema_schedule_stress"]["rows"]),
        "variance_batch_rows": len(payload["variance"]["batch_stability"]),
        "covariance_batch_rows": len(payload["covariance"]["batch_stability"]),
        "masking_rows": len(payload["masking"]["existing_exact_count_calibration"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
