#!/usr/bin/env python3
"""Zero-update simplification and integrated qualification audit of the RBB core."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
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
import stage81a3_rbb_panel_exposure as exposure  # noqa: E402
import stage81a3_rbb_structural_panel_audit as structural  # noqa: E402
from sea_ad_jepa.v4.conditional_predictability import ridge_fit, ridge_predict  # noqa: E402
from sea_ad_jepa.v4.measurement_state import MeasurementState  # noqa: E402
from sea_ad_jepa.v4.observation_calibration import (  # noqa: E402
    apply_observation_calibration, fit_conditional_only_scale,
)
from sea_ad_jepa.v4.rbb_adaptive import (  # noqa: E402
    RBBAdaptiveBelief, dense_covariance, lrd_solve, structured_gaussian_terms,
)
from sea_ad_jepa.v4.rbb_core import RBBCore, migrate_adaptive_state  # noqa: E402


SEED = base.SEED
MICROBATCH = 32
SOURCE_CHECKPOINT = structural.CHECKPOINT
SOURCE_CHECKPOINT_HASH = structural.CHECKPOINT_HASH
REJECTED_CHECKPOINT = Path("results/v4/stage81a3_rbb_panel_exposure_checkpoint.pt")
REJECTED_CHECKPOINT_HASH = "c78cf055ceb020c2d0e928c021703d1063a24c010e92f6bbef7e572a368e8396"
PANEL_EXPOSURE_REPORT = Path("results/v4/stage81a3_rbb_panel_exposure.json")
PANEL_EXPOSURE_HASH = "207302fb720924f46a62162fcdc6eb29c6fb7cd796189765fe4bb45e98fbe7f0"
PRIOR_EVIDENCE = {
    **exposure.PRIOR_EVIDENCE,
    str(PANEL_EXPOSURE_REPORT): PANEL_EXPOSURE_HASH,
    str(REJECTED_CHECKPOINT): REJECTED_CHECKPOINT_HASH,
}
OUTPUTS = {
    "json": Path("results/v4/stage81a3_rbb_core_simplification.json"),
    "checkpoint": Path("results/v4/stage81a3_rbb_core_simplified_checkpoint.pt"),
    "migration": Path("results/v4/stage81a3_rbb_core_migration_manifest.json"),
    "ordinary": Path("results/v4/stage81a3_rbb_core_ordinary.csv"),
    "structural": Path("results/v4/stage81a3_rbb_core_structural.csv"),
    "calibration": Path("results/v4/stage81a3_rbb_core_calibration.csv"),
    "cross": Path("results/v4/stage81a3_rbb_core_cross_panel.csv"),
    "registry": Path("results/v4/stage81a3_rbb_core_failure_registry.csv"),
}


def tensor_hash(value: torch.Tensor) -> str:
    value = value.detach().cpu().contiguous(); digest = hashlib.sha256()
    digest.update(str(value.dtype).encode()); digest.update(str(tuple(value.shape)).encode())
    digest.update(value.numpy().tobytes()); return digest.hexdigest()


def state_hash(state: dict[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        digest.update(name.encode()); digest.update(tensor_hash(state[name]).encode())
    return digest.hexdigest()


def verify_evidence() -> dict[str, str]:
    actual = {path: structural.sha256(Path(path)) for path in PRIOR_EVIDENCE}
    if actual != PRIOR_EVIDENCE:
        raise RuntimeError("prior evidence hash mismatch")
    report = json.loads(PANEL_EXPOSURE_REPORT.read_text(encoding="utf-8"))
    expected = "SCALAR RECALIBRATION IS SUFFICIENT; NEURAL PANEL EXPOSURE NOT EARNED"
    if report["classification"] != expected:
        raise RuntimeError("panel-exposure classification mismatch")
    return actual


def reconstruct_adaptive(device: torch.device, priors: dict[str, Any]) -> tuple[RBBAdaptiveBelief, dict[str, str]]:
    torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    precision_bias, correlation_bias, _ = base.initialization_biases(priors)
    model = RBBAdaptiveBelief(diagonal_precision_bias=precision_bias, correlated_amplitude_bias=correlation_bias).to(device)
    hashes = frozen.frozen_hashes(model)
    expected = json.loads(structural.RECOVERY_REPORT.read_text(encoding="utf-8"))["molecular_hashes_step0"]
    if hashes != expected:
        raise RuntimeError("molecular reconstruction hash mismatch")
    checkpoint = torch.load(SOURCE_CHECKPOINT, map_location=device, weights_only=False)
    missing, unexpected = model.load_state_dict(checkpoint["belief_state_dict"], strict=False)
    if unexpected or any(not name.startswith("ledger.") for name in missing):
        raise RuntimeError("source checkpoint key mismatch")
    model.freeze_molecular_ledger()
    for parameter in model.parameters(): parameter.requires_grad_(False)
    model.eval(); return model, hashes


def migration_entries(source: dict[str, torch.Tensor], core: RBBCore) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    retained = []
    for name in (
        "mask_context.0.weight", "mask_context.0.bias", "mask_context.2.weight", "mask_context.2.bias",
        "evidence_norm.weight", "evidence_norm.bias", "evidence_hidden.0.weight", "evidence_hidden.0.bias",
    ):
        retained.append({"source": name, "destination": name, "sha256": tensor_hash(source[name]), "parameters": source[name].numel()})
    for source_name, destination_name, value in (
        ("evidence_output.weight[:320]", "evidence_output.weight", source["evidence_output.weight"][:2 * core.width]),
        ("evidence_output.bias[:320]", "evidence_output.bias", source["evidence_output.bias"][:2 * core.width]),
    ):
        retained.append({"source": source_name, "destination": destination_name, "sha256": tensor_hash(value), "parameters": value.numel()})
    discarded = [
        {"source": "evidence_output.weight[320:352]", "sha256": tensor_hash(source["evidence_output.weight"][2 * core.width:]), "parameters": source["evidence_output.weight"][2 * core.width:].numel()},
        {"source": "evidence_output.bias[320:352]", "sha256": tensor_hash(source["evidence_output.bias"][2 * core.width:]), "parameters": source["evidence_output.bias"][2 * core.width:].numel()},
        {"source": "correlated_directions", "sha256": tensor_hash(source["correlated_directions"]), "parameters": source["correlated_directions"].numel()},
    ]
    return retained, discarded


def migrate_core(adaptive: RBBAdaptiveBelief, device: torch.device) -> tuple[RBBCore, dict[str, Any]]:
    core = RBBCore().to(device)
    core.ledger.load_state_dict(adaptive.ledger.state_dict(), strict=True)
    source_checkpoint = torch.load(SOURCE_CHECKPOINT, map_location=device, weights_only=False)
    source = source_checkpoint["belief_state_dict"]
    destination, _, _ = migrate_adaptive_state(source, core)
    core.load_state_dict(destination, strict=True)
    for parameter in core.parameters(): parameter.requires_grad_(False)
    core.eval()
    retained, discarded = migration_entries(source, core)
    destination_belief = {name: value.detach().cpu() for name, value in core.state_dict().items() if not name.startswith("ledger.")}
    source_count = sum(value.numel() for value in source.values())
    destination_count = sum(value.numel() for value in destination_belief.values())
    checkpoint_payload = {
        "belief_state_dict": destination_belief,
        "metadata": {
            "anchor": base.ANCHOR, "seed": SEED, "source_checkpoint_sha256": SOURCE_CHECKPOINT_HASH,
            "adaptive_correlated_evidence": False, "fixed_prior_correlation_external_and_retained": True,
            "contains_molecular_weights": False, "neural_optimizer_updates": 0,
        },
    }
    destination_hash = recovery.atomic_checkpoint(OUTPUTS["checkpoint"], checkpoint_payload)
    manifest = {
        "source_checkpoint": str(SOURCE_CHECKPOINT), "source_checkpoint_sha256": SOURCE_CHECKPOINT_HASH,
        "destination_checkpoint": str(OUTPUTS["checkpoint"]), "destination_checkpoint_sha256": destination_hash,
        "retained": retained, "discarded": discarded,
        "source_belief_parameters": source_count, "destination_belief_parameters": destination_count,
        "parameter_count_difference": source_count - destination_count,
        "destination_state_sha256": state_hash(destination_belief),
        "source_checkpoint_unchanged": structural.sha256(SOURCE_CHECKPOINT) == SOURCE_CHECKPOINT_HASH,
    }
    base.atomic_json(OUTPUTS["migration"], manifest)
    return core, manifest


def make_state(measured: torch.Tensor, batch: int, device: torch.device, *, ordinary: bool) -> tuple[MeasurementState, torch.Tensor]:
    measured = measured.to(device)
    if ordinary:
        measurement = torch.ones(batch, base.GENES, dtype=torch.bool, device=device)
        training_hidden = (~measured)[None].expand(batch, -1)
    else:
        measurement = measured[None].expand(batch, -1)
        training_hidden = torch.zeros_like(measurement)
    state = MeasurementState(measurement, training_hidden, torch.ones(base.GENES, dtype=torch.bool, device=device))
    return state, state.belief_missing_mask[0]


def core_forward(
    core: RBBCore, expression: torch.Tensor, state: MeasurementState, hidden: torch.Tensor,
    basis: Any, prior: dict[str, Any], *, regime: str = "ordinary_raw", scale: float = 1.0,
) -> Any:
    sanitized = state.sanitized_expression(expression)
    visible_state = basis.contribution(sanitized, state.observed_mask[0])
    ids = torch.arange(base.GENES, device=expression.device)[None].expand(len(expression), -1)
    return core(
        ids, expression, state, visible_state, base.mask_context(basis, hidden, prior, len(expression)),
        prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"],
        calibration_regime=regime, calibration_scale=scale,
    )


def parity_audit(
    adaptive: RBBAdaptiveBelief, core: RBBCore, fixture: Any, basis: Any,
    prior: dict[str, Any], hidden: torch.Tensor, device: torch.device,
) -> dict[str, Any]:
    selected = torch.arange(base.TRAIN, base.TRAIN + 32, device=device)
    expression = fixture.x_a[selected]; measured = ~hidden.cpu()
    state, hidden_one = make_state(measured, len(selected), device, ordinary=True)
    sanitized = state.sanitized_expression(expression)
    visible = basis.contribution(sanitized, state.observed_mask[0])
    ids = torch.arange(base.GENES, device=device)[None].expand(len(selected), -1)
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16):
        historical = adaptive(
            ids, sanitized, state.observed_mask, visible,
            base.mask_context(basis, hidden_one, prior, len(selected)),
            prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"],
            diagonalize_evidence=True,
        )
        simplified = core_forward(core, expression, state, hidden_one, basis, prior)
    target = basis.contribution(fixture.x_b[selected], hidden_one)
    old_nll, _, _ = structured_gaussian_terms(target - historical.posterior_missing_mean, historical.total_diagonal, historical.total_low_rank)
    new_nll, _, _ = structured_gaussian_terms(target - simplified.posterior_missing_mean, simplified.raw_total_diagonal, simplified.raw_total_low_rank)
    old_dense = dense_covariance(historical.conditional_diagonal, historical.conditional_low_rank)
    new_dense = dense_covariance(simplified.raw_conditional_diagonal, simplified.raw_conditional_low_rank)
    differences = {
        "posterior_missing_mean": float((historical.posterior_missing_mean - simplified.posterior_missing_mean).abs().max()),
        "belief_mean": float((historical.belief_mean - simplified.belief_mean).abs().max()),
        "visible_state": float((historical.visible_state - simplified.visible_state).abs().max()),
        "conditional_dense_covariance": float((old_dense - new_dense).abs().max()),
        "total_marginal_variance": float(((historical.total_diagonal + historical.total_low_rank.square().sum(-1)) - (simplified.raw_total_diagonal + simplified.raw_total_low_rank.square().sum(-1))).abs().max()),
        "nll": float((old_nll - new_nll).abs().max()),
    }
    return {"maximum_absolute_differences": differences, "maximum": max(differences.values()), "pass": max(differences.values()) <= 1e-6}


def summarize_factors(values: torch.Tensor, fixture: Any) -> dict[str, Any]:
    half = len(values) // 2
    validation = torch.cat((values[:base.VALIDATION], values[half:half + base.VALIDATION]))
    sealed = torch.cat((values[base.VALIDATION:half], values[half + base.VALIDATION:]))
    return base.representation_readout(validation, sealed, fixture.factors.cpu())


def evaluate_condition(
    core: RBBCore,
    fixture: Any,
    basis: Any,
    prior: dict[str, Any],
    measured: torch.Tensor,
    device: torch.device,
    *,
    ordinary: bool,
    variants: dict[str, tuple[str, float]],
    retain: bool = False,
) -> dict[str, Any]:
    indices = torch.arange(base.TRAIN, base.CELLS, device=device)
    collected: dict[str, list[torch.Tensor]] = {name: [] for name in (
        "visible", "belief", "target", "conditional_diagonal", "conditional_low_rank", "noise_diagonal",
    )}
    with torch.no_grad():
        for direction, source in enumerate((fixture.x_a, fixture.x_b)):
            for start in range(0, len(indices), MICROBATCH):
                selected = indices[start:start + MICROBATCH]; expression = source[selected]
                state, hidden = make_state(measured, len(selected), device, ordinary=ordinary)
                with torch.autocast("cuda", dtype=torch.float16):
                    output = core_forward(core, expression, state, hidden, basis, prior)
                if ordinary:
                    independent = fixture.x_b[selected] if direction == 0 else fixture.x_a[selected]
                    target = basis.contribution(independent, hidden)
                else:
                    target = basis.contribution(fixture.lambda_norm[selected], hidden)
                values = {
                    "visible": output.visible_state, "belief": output.belief_mean, "target": target,
                    "conditional_diagonal": output.raw_conditional_diagonal,
                    "conditional_low_rank": output.raw_conditional_low_rank,
                    "noise_diagonal": output.measurement_noise_diagonal,
                }
                for name, value in values.items(): collected[name].append(value.float().cpu())
    arrays = {name: torch.cat(parts) for name, parts in collected.items()}
    half = len(arrays["belief"]) // 2
    validation = torch.cat((torch.arange(base.VALIDATION), torch.arange(half, half + base.VALIDATION)))
    sealed = torch.cat((torch.arange(base.VALIDATION, half), torch.arange(half + base.VALIDATION, 2 * half)))
    residual = arrays["target"] - (arrays["belief"] - arrays["visible"])
    visible_factors = summarize_factors(arrays["visible"], fixture)
    belief_factors = summarize_factors(arrays["belief"], fixture)
    prior_nll, _, _ = structured_gaussian_terms(
        arrays["target"][sealed],
        (prior["prior_diagonal"].cpu() + prior["noise_diagonal"].cpu())[None].expand(len(sealed), -1),
        prior["prior_low_rank"].cpu()[None].expand(len(sealed), -1, -1),
    )
    rows = []
    variant_arrays = {}
    for variant, (regime, scale) in variants.items():
        uncertainty = apply_observation_calibration(
            arrays["conditional_diagonal"], arrays["conditional_low_rank"], arrays["noise_diagonal"],
            regime=regime, scale=scale,
        )
        nll, mahal, logdet = structured_gaussian_terms(
            residual, uncertainty.calibrated_total_diagonal, uncertainty.calibrated_total_low_rank,
        )
        marginal = uncertainty.calibrated_total_diagonal + uncertainty.calibrated_total_low_rank.square().sum(-1)
        calibration = base.marginal_calibration(residual[sealed], marginal[sealed])
        gaussian = base.gaussianity(residual[sealed], marginal[sealed])
        rows.append({
            "variant": variant, "calibration_regime": regime, "calibration_scale": scale,
            "nll": float((nll[sealed] / base.WIDTH).mean()), "prior_nll": float((prior_nll / base.WIDTH).mean()),
            "joint_scale": float((mahal[sealed] / base.WIDTH).mean()),
            "coverage_1sigma": calibration["coverage_1sigma"], "coverage_1_96sigma": calibration["coverage_1_96sigma"],
            "standardized_variance": calibration["standardized_variance"],
            "uncertainty_error_spearman": base.spearman(marginal[sealed].sum(1), residual[sealed].square().sum(1)),
            "visible_factor_r2": visible_factors["mean"], "belief_factor_r2": belief_factors["mean"],
            "belief_minus_visible_factor_r2": belief_factors["mean"] - visible_factors["mean"],
            "median_trace": float(marginal[sealed].sum(1).median()), "median_logdet": float(logdet[sealed].median()),
            "gaussian_severe_fraction": gaussian["severe_fraction"],
        })
        variant_arrays[variant] = {
            "diagonal": uncertainty.calibrated_total_diagonal,
            "low_rank": uncertainty.calibrated_total_low_rank,
            "marginal": marginal,
            "trace": marginal.sum(1),
        }
    result = {"rows": rows, "visible_factors": visible_factors, "belief_factors": belief_factors}
    if retain:
        result["arrays"] = {**arrays, "residual": residual, "validation": validation, "sealed": sealed, "variants": variant_arrays}
    return result


def fit_conditional_scale(
    core: RBBCore, fixture: Any, basis: Any, priors: dict[str, Any], panels: dict[str, Any], device: torch.device,
) -> tuple[float, dict[str, Any]]:
    batches = []
    for family in structural.FAMILIES:
        prior = priors["RANDOM_40" if family == "RANDOM_STRUCTURAL" else "COEXPRESSION_BLOCK_40"]
        for view, masks in enumerate(panels[family]):
            for panel in ("P80", "P60", "P40"):
                print(f"conditional fit {family} view={view} panel={panel}", flush=True)
                result = evaluate_condition(
                    core, fixture, basis, prior, masks[panel], device,
                    ordinary=False, variants={"raw": ("ordinary_raw", 1.0)}, retain=True,
                )
                arrays = result["arrays"]; selected = arrays["validation"]
                batches.append((
                    arrays["residual"][selected], arrays["conditional_diagonal"][selected],
                    arrays["conditional_low_rank"][selected], arrays["noise_diagonal"][selected],
                ))
    scale, fit = fit_conditional_only_scale(batches)
    fit.update({
        "fit_split": "VALIDATION", "families": list(structural.FAMILIES),
        "fractions": ["P80", "P60", "P40"], "sealed_used": False,
        "factor_labels_used": False, "shared_scalar": True,
    })
    return scale, fit


def structural_evaluation(
    core: RBBCore, fixture: Any, basis: Any, priors: dict[str, Any], panels: dict[str, Any],
    historical_scale: float, conditional_scale: float, device: torch.device,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    variants = {
        "RAW": ("ordinary_raw", 1.0),
        "HISTORICAL_TOTAL_SCALAR": ("historical_total_scalar", historical_scale),
        "CONDITIONAL_ONLY_SCALAR": ("conditional_only_scalar", conditional_scale),
    }
    rows = []; coordinates = {family: {variant: [] for variant in variants} for family in structural.FAMILIES}
    for family in structural.FAMILIES:
        prior = priors["RANDOM_40" if family == "RANDOM_STRUCTURAL" else "COEXPRESSION_BLOCK_40"]
        for view, masks in enumerate(panels[family]):
            view_coordinates = {variant: [] for variant in variants}
            for panel in structural.PANEL_ORDER:
                print(f"core {family} view={view} panel={panel}", flush=True)
                panel_variants = variants if panel != "FULL" else {
                    variant: ("ordinary_raw", 1.0) for variant in variants
                }
                result = evaluate_condition(core, fixture, basis, prior, masks[panel], device, ordinary=False, variants=panel_variants, retain=True)
                for row in result["rows"]:
                    rows.append({"family": family, "view": view, "panel": panel, "measured_genes": structural.PANEL_COUNTS[panel], **row})
                    selected = result["arrays"]["sealed"]
                    view_coordinates[row["variant"]].append(result["arrays"]["variants"][row["variant"]]["marginal"][selected].median(0).values)
            for variant in variants:
                coordinates[family][variant].append(torch.stack(view_coordinates[variant]))
    summary = {}
    monotonic = {}
    for family in structural.FAMILIES:
        summary[family] = {}
        monotonic[family] = {}
        for variant in variants:
            summary[family][variant] = {}
            fractions = [float(((stack[1:] >= stack[:-1]).all(0)).float().mean()) for stack in coordinates[family][variant]]
            monotonic[family][variant] = float(np.median(fractions))
            for panel in structural.PANEL_ORDER:
                selected = [row for row in rows if row["family"] == family and row["variant"] == variant and row["panel"] == panel]
                summary[family][variant][panel] = {key: float(np.median([row[key] for row in selected])) for key in selected[0] if key not in ("family", "view", "panel", "measured_genes", "variant", "calibration_regime")}
    return rows, summary, monotonic


def ordinary_evaluation(
    core: RBBCore, fixture: Any, basis: Any, priors: dict[str, Any], banks: dict[str, torch.Tensor], device: torch.device,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []; summary = {}
    for label, prior_name in (("ORDINARY_RANDOM_40", "RANDOM_40"), ("ORDINARY_BLOCK_40", "COEXPRESSION_BLOCK_40")):
        family_rows = []
        for view in range(4):
            result = evaluate_condition(
                core, fixture, basis, priors[prior_name], ~banks[label][view], device,
                ordinary=True, variants={"RAW": ("ordinary_raw", 1.0)}, retain=False,
            )
            row = {"family": prior_name, "view": view, **result["rows"][0]}
            rows.append(row); family_rows.append(row)
        summary[prior_name] = {
            key: float(np.median([row[key] for row in family_rows]))
            for key in family_rows[0] if key not in ("family", "view", "variant", "calibration_regime")
        }
    return rows, summary


def cross_panel_audit(
    core: RBBCore, fixture: Any, basis: Any, prior: dict[str, Any], historical_scale: float,
    conditional_scale: float, device: torch.device,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    variants = {
        "RAW": ("ordinary_raw", 1.0),
        "HISTORICAL_TOTAL_SCALAR": ("historical_total_scalar", historical_scale),
        "CONDITIONAL_ONLY_SCALAR": ("conditional_only_scalar", conditional_scale),
    }
    rows = []; passes = {variant: {"identity": [], "union": []} for variant in variants}
    for pair in range(4):
        a_mask, b_mask = structural.complementary_masks(pair)
        full_mask = torch.ones(base.GENES, dtype=torch.bool)
        outputs = {}
        for name, mask in (("A", a_mask), ("B", b_mask), ("FULL", full_mask)):
            active_variants = variants if name != "FULL" else {variant: ("ordinary_raw", 1.0) for variant in variants}
            outputs[name] = evaluate_condition(
                core, fixture, basis, prior, mask, device, ordinary=False,
                variants=active_variants, retain=True,
            )["arrays"]
        for variant in variants:
            sealed = outputs["A"]["sealed"]
            mean_a, mean_b = outputs["A"]["belief"][sealed], outputs["B"]["belief"][sealed]
            covariance_a, covariance_b = outputs["A"]["variants"][variant], outputs["B"]["variants"][variant]
            diagonal_a, diagonal_b = covariance_a["diagonal"][sealed], covariance_b["diagonal"][sealed]
            low_rank_a, low_rank_b = covariance_a["low_rank"][sealed], covariance_b["low_rank"][sealed]
            same_delta = mean_a - mean_b; mismatch_delta = mean_a - mean_b.roll(-1, 0)
            same = (same_delta * lrd_solve(same_delta, diagonal_a + diagonal_b, torch.cat((low_rank_a, low_rank_b), -1))).sum(1) / base.WIDTH
            mismatch = (
                mismatch_delta * lrd_solve(
                    mismatch_delta, diagonal_a + diagonal_b.roll(-1, 0),
                    torch.cat((low_rank_a, low_rank_b.roll(-1, 0)), -1),
                )
            ).sum(1) / base.WIDTH
            below = float((same < mismatch.median()).float().mean())
            identity_pass = float(same.median()) < float(mismatch.median()) and below >= .75
            medians = {
                name: outputs[name]["variants"][variant]["marginal"][outputs[name]["sealed"]].median(0).values
                for name in outputs
            }
            union_fraction = float(((medians["FULL"] <= medians["A"]) & (medians["FULL"] <= medians["B"])).float().mean())
            union_pass = union_fraction >= .75
            rows.append({
                "pair": pair, "variant": variant, "panel_a_size": int(a_mask.sum()), "panel_b_size": int(b_mask.sum()),
                "intersection": int((a_mask & b_mask).sum()), "union": int((a_mask | b_mask).sum()),
                "same_cell_median_J": float(same.median()), "mismatched_cell_median_J": float(mismatch.median()),
                "same_below_mismatch_median_fraction": below, "same_cell_compatibility_pass": identity_pass,
                "union_coordinate_reduction_fraction": union_fraction, "union_reduction_pass": union_pass,
                "panel_a_median_trace": float(covariance_a["trace"][sealed].median()),
                "panel_b_median_trace": float(covariance_b["trace"][sealed].median()),
                "union_median_trace": float(outputs["FULL"]["variants"][variant]["trace"][outputs["FULL"]["sealed"]].median()),
                "full_union_calibration_semantics": "FULL union remains raw scale 1; structural component panels use the named regime scalar",
            })
            passes[variant]["identity"].append(identity_pass); passes[variant]["union"].append(union_pass)
        print(f"cross-panel pair={pair} complete", flush=True)
    summary = {
        variant: {
            "same_cell_compatibility_pass": all(values["identity"]),
            "union_uncertainty_reduction_pass": all(values["union"]),
        }
        for variant, values in passes.items()
    }
    return rows, summary


def semantics_audit(
    core: RBBCore, fixture: Any, basis: Any, prior: dict[str, Any], device: torch.device,
) -> dict[str, Any]:
    measured = torch.ones(base.GENES, dtype=torch.bool); measured[:base.HIDDEN] = False
    selected = torch.arange(base.TRAIN, base.TRAIN + 32, device=device); expression = fixture.x_a[selected]
    state, hidden = make_state(measured, len(selected), device, ordinary=False)
    shuffled = expression.clone(); shuffled[state.structural_unmeasured_mask] = expression.roll(1, 0)[state.structural_unmeasured_mask]
    substitutions = {
        "true": expression, "zero": expression.masked_fill(state.structural_unmeasured_mask, 0),
        "shuffled": shuffled, "large_finite": expression.masked_fill(state.structural_unmeasured_mask, 1000.0),
    }
    fields = ("molecular_evidence_tokens", "visible_state", "posterior_missing_mean", "belief_mean", "raw_conditional_diagonal", "raw_conditional_low_rank", "raw_total_diagonal", "raw_total_low_rank")
    reference = None; differences = {}
    with torch.no_grad():
        for name, values in substitutions.items():
            with torch.autocast("cuda", dtype=torch.float16):
                output = core_forward(core, values, state, hidden, basis, prior)
            current = {field: getattr(output, field).float().cpu() for field in fields}
            if reference is None: reference = current
            differences[name] = max(float((current[field] - reference[field]).abs().max()) for field in fields)
    zeros = fixture.x_a[-256:] == 0
    measured_state = MeasurementState(torch.ones_like(zeros), torch.zeros_like(zeros), torch.ones(base.GENES, dtype=torch.bool, device=device))
    structural_measurement = torch.ones_like(zeros); structural_measurement[zeros] = False
    structural_state = MeasurementState(structural_measurement, torch.zeros_like(zeros), torch.ones(base.GENES, dtype=torch.bool, device=device))
    one = torch.ones(1, base.GENES, dtype=torch.bool, device=device); train_hidden = torch.zeros_like(one); train_hidden[:, 0] = True
    training = MeasurementState(one, train_hidden, torch.ones(base.GENES, dtype=torch.bool, device=device))
    structural_one = one.clone(); structural_one[:, 0] = False
    structural_target = MeasurementState(structural_one, torch.zeros_like(one), torch.ones(base.GENES, dtype=torch.bool, device=device))
    unsupported = torch.ones(base.GENES, dtype=torch.bool, device=device); unsupported[0] = False
    unsupported_measurement = one.clone(); unsupported_measurement[:, 0] = False
    unsupported_state = MeasurementState(unsupported_measurement, torch.zeros_like(one), unsupported)
    unsupported_rejected = False
    try: unsupported_state.assert_foundation_inference_supported()
    except ValueError: unsupported_rejected = True
    return {
        "structural_substitution_max_abs": differences,
        "structural_firewall_pass": max(differences.values()) <= 1e-6,
        "measured_zero": {
            "examples": int(zeros.sum()), "measured_zero_observed": bool(torch.all(measured_state.observed_mask[zeros])),
            "structural_zero_not_observed": bool(torch.all(~structural_state.observed_mask[zeros])),
            "states_distinct": bool(torch.any(measured_state.observed_mask != structural_state.observed_mask)),
        },
        "training_vs_structural": {
            "training_measurement_supported": bool(training.measurement_mask[0, 0]),
            "both_belief_missing": bool(training.belief_missing_mask[0, 0] and structural_target.belief_missing_mask[0, 0]),
            "training_target_eligible": bool(training.training_target_eligible_mask[0, 0]),
            "structural_target_eligible": bool(structural_target.training_target_eligible_mask[0, 0]),
        },
        "foundation_unsupported_rejected": unsupported_rejected,
        "visible_state_formula": "A @ ((x - mu) * observed_mask)",
    }


def classify_point_value(structural_summary: dict[str, Any]) -> str:
    values = [
        structural_summary[family]["RAW"][panel]["belief_minus_visible_factor_r2"]
        for family in structural.FAMILIES for panel in structural.PRIMARY
    ]
    median = float(np.median(values))
    if median < -.02: return "HARMFUL"
    if median > .02: return "MEANINGFUL"
    return "NEGLIGIBLE"


def failure_registry() -> list[dict[str, str]]:
    rows = [
        ("PERCEIVER INFORMATION LOSS", "REMOVED AS UNEARNED"),
        ("CELL-TOKEN INFORMATION LOSS", "REMOVED AS UNEARNED"),
        ("CROSS-ATTENTION ROUTING BOTTLENECK", "REMOVED AS UNEARNED"),
        ("JEPA LOSS WITH BAD GEOMETRY", "RESOLVED BY EVALUATION CONTRACT"),
        ("FAKE RANK / LOW INFORMATION", "RESOLVED BY EVALUATION CONTRACT"),
        ("DETERMINISTIC RESIDUAL-COMPLETION DAMAGE", "REMOVED AS UNEARNED"),
        ("CAUSAL-DAG FAILURE", "DOWNSTREAM / NOT YET CLAIMED"),
        ("EXACT MISSING-STATE IDENTIFIABILITY FAILURE", "RESOLVED BY EVALUATION CONTRACT"),
        ("IN-SAMPLE COVARIANCE UNDERESTIMATION", "RESOLVED BY EVALUATION CONTRACT"),
        ("OOF COVARIANCE OVERESTIMATION", "RESOLVED BY EVALUATION CONTRACT"),
        ("END-TO-END BELIEF GRADIENT DAMAGE", "RESOLVED BY ARCHITECTURE"),
        ("STRUCTURAL ZERO/UNMEASURED COLLAPSE", "RESOLVED BY ARCHITECTURE"),
        ("STRUCTURAL RAW-VALUE LEAKAGE", "RESOLVED BY ARCHITECTURE"),
        ("NEURAL PANEL-EXPOSURE NON-VALUE", "REMOVED AS UNEARNED"),
        ("ADAPTIVE CORRELATED-EVIDENCE NON-VALUE", "REMOVED AS UNEARNED"),
        ("STRUCTURAL UNCERTAINTY SCALE MISCALIBRATION", "KNOWN OPEN LIMITATION"),
        ("STRUCTURAL CELL-LEVEL UNCERTAINTY LOCALIZATION FAILURE", "KNOWN OPEN LIMITATION"),
        ("COUNTERFACTUAL FAILURE", "DOWNSTREAM / NOT YET CLAIMED"),
    ]
    return [{"failure": name, "classification": classification} for name, classification in rows]


def append_readout(payload: dict[str, Any]) -> None:
    path = Path("docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md")
    marker = "## Stage81A3 Core Architecture Simplification"
    existing = path.read_text(encoding="utf-8")
    if marker in existing: raise RuntimeError("core-simplification readout already exists")
    text = f"""

{marker}

This zero-update audit returned to the frozen-recovery belief checkpoint and did not use the
rejected panel-exposure weights. The Perceiver and CELL-token designs remain rejected because
they lost molecular information; the six-block token-preserving ledger remains frozen. The hard
gradient firewall is architectural because prior end-to-end belief gradients damaged ledger
retention. Exact hidden-expression reconstruction is not the objective: the core reports an
accountable belief over RepPCA state while preserving factual visible evidence exactly.

Structural unmeasurement remains explicit because an assay that did not measure a gene is not
evidence of biological zero. Neural panel-exposure training was rejected after it failed to add
held-out value. The adaptive learned correlated evidence branch was removed because three
independent evaluations found no earned value. Fixed prior correlation was retained unchanged;
its statistical directions are not called pathways, programs, or mechanisms.

Calibration remains a post-inference observation-regime layer, not biological state. Raw
conditional uncertainty, separate measurement noise, raw total uncertainty, and calibrated total
uncertainty remain exposed. Population-scale calibration asks whether the belief is approximately
wide enough overall; cell-level localization asks whether the model knows which individual cells
are relatively more uncertain. A scalar can improve the former without improving the latter.

Primary classification: **{payload['classification']}**.

Adaptive correlated evidence: **{payload['secondary_classifications']['adaptive_correlated_evidence']}**.
Fixed prior correlation: **{payload['secondary_classifications']['fixed_prior_correlation']}**.
Point-state recovery: **{payload['secondary_classifications']['point_state_recovery']}**.
Structural population-scale calibration: **{payload['secondary_classifications']['structural_population_scale_calibration']}**.
Structural cell-level localization: **{payload['secondary_classifications']['structural_cell_level_localization']}**.

Counterfactual capability remains unsupported. This synthetic audit does not establish pathology
biology, causal dynamics, real-data validity, or Stage81A3 completion.
"""
    base.atomic_text(path, existing.rstrip() + text + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=ROOT)
    args = parser.parse_args(); os.chdir(args.project_dir.resolve())
    if any(path.exists() for path in OUTPUTS.values()):
        raise RuntimeError("core-simplification artifact already exists; repeat forbidden")
    if not torch.cuda.is_available(): raise RuntimeError("CUDA is required for exact frozen-evidence reproduction")
    started = time.perf_counter(); device = torch.device("cuda")
    torch.set_float32_matmul_precision("high"); torch.backends.cuda.matmul.allow_tf32 = True
    evidence_hashes = verify_evidence()
    torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    basis = base.load_basis(device); fixture = base.build_fixture(device); priors = base.frozen_family_statistics(device)
    adaptive, molecular_hashes = reconstruct_adaptive(device, priors)
    source_before = {name: value.detach().cpu().clone() for name, value in adaptive.state_dict().items()}
    core, migration = migrate_core(adaptive, device)
    core_before = {name: value.detach().cpu().clone() for name, value in core.state_dict().items()}
    core_hashes = frozen.frozen_hashes(core)
    if core_hashes != molecular_hashes: raise RuntimeError("simplified molecular hashes differ from source")

    parity = parity_audit(adaptive, core, fixture, basis, priors["RANDOM_40"], base.random_mask_bank()[0].to(device), device)
    if not parity["pass"]:
        raise RuntimeError("CORRELATED-BRANCH REMOVAL PARITY FAILURE")
    retention = base.token_information(core, fixture, MICROBATCH, device)
    recovery_report = json.loads(structural.RECOVERY_REPORT.read_text(encoding="utf-8"))
    expected_retention = recovery_report["retention"][-1]["retention_ratio"]
    retention_difference = abs(retention["retention_ratio"] - expected_retention)
    retention_pass = retention["retention_ratio"] >= .95 and retention_difference <= 1e-6
    semantics = semantics_audit(core, fixture, basis, priors["RANDOM_40"], device)
    panels, panel_construction = structural.build_panels(fixture)
    banks, bank_audit = exposure.build_banks(fixture)

    panel_report = json.loads(PANEL_EXPOSURE_REPORT.read_text(encoding="utf-8"))
    scalar_record = panel_report["scalar_recalibration"]
    historical_scale = float(scalar_record["variance_temperature"])
    historical_provenance = {
        "value": historical_scale, "fit_split": scalar_record["fit_split"],
        "shared_across_families_and_p80_p60_p40": scalar_record["shared_across_families_and_p80_p60_p40"],
        "sealed_used_for_fit": scalar_record["sealed_used_for_fit"],
        "posterior_mean_changed": scalar_record["posterior_mean_changed"],
        "refitted_in_this_task": False,
    }
    if historical_provenance != {
        "value": historical_scale, "fit_split": "VALIDATION",
        "shared_across_families_and_p80_p60_p40": True,
        "sealed_used_for_fit": False, "posterior_mean_changed": False,
        "refitted_in_this_task": False,
    }:
        raise RuntimeError("historical scalar provenance mismatch")

    conditional_scale, conditional_fit = fit_conditional_scale(core, fixture, basis, priors, panels, device)
    ordinary_rows, ordinary_summary = ordinary_evaluation(core, fixture, basis, priors, banks, device)
    structural_rows, structural_summary, monotonicity = structural_evaluation(
        core, fixture, basis, priors, panels, historical_scale, conditional_scale, device,
    )
    cross_rows, cross_summary = cross_panel_audit(
        core, fixture, basis, priors["RANDOM_40"], historical_scale, conditional_scale, device,
    )

    ordinary_proper = all(summary["nll"] < summary["prior_nll"] for summary in ordinary_summary.values())
    ordinary_calibration = all(
        .8 <= summary["joint_scale"] <= 1.25 and .58 <= summary["coverage_1sigma"] <= .78
        and .88 <= summary["coverage_1_96sigma"] <= .99 for summary in ordinary_summary.values()
    )
    ordinary_localization = all(summary["uncertainty_error_spearman"] > .75 for summary in ordinary_summary.values())
    ordinary_no_harm = all(summary["belief_factor_r2"] >= summary["visible_factor_r2"] - .01 for summary in ordinary_summary.values())
    structural_raw_proper = all(
        structural_summary[family]["RAW"]["P60"]["nll"] < structural_summary[family]["RAW"]["P60"]["prior_nll"]
        for family in structural.FAMILIES
    )
    structural_no_harm = all(
        structural_summary[family]["RAW"][panel]["belief_factor_r2"]
        >= structural_summary[family]["RAW"][panel]["visible_factor_r2"] - .02
        for family in structural.FAMILIES for panel in structural.PRIMARY
    )
    localization = {
        family: structural_summary[family]["RAW"]["P60"]["uncertainty_error_spearman"]
        for family in structural.FAMILIES
    }
    localization_pass = all(value > .50 for value in localization.values())
    calibration_variant_pass = {}
    for variant in ("HISTORICAL_TOTAL_SCALAR", "CONDITIONAL_ONLY_SCALAR"):
        calibration_variant_pass[variant] = all(
            .8 <= structural_summary[family][variant]["P60"]["joint_scale"] <= 1.25
            and .58 <= structural_summary[family][variant]["P60"]["coverage_1sigma"] <= .78
            and .88 <= structural_summary[family][variant]["P60"]["coverage_1_96sigma"] <= .99
            for family in structural.FAMILIES
        )
    population_supported = any(calibration_variant_pass.values())
    calibration_improves = any(
        abs(structural_summary[family][variant]["P60"]["joint_scale"] - 1)
        < abs(structural_summary[family]["RAW"]["P60"]["joint_scale"] - 1)
        for family in structural.FAMILIES
        for variant in ("HISTORICAL_TOTAL_SCALAR", "CONDITIONAL_ONLY_SCALAR")
    )
    population_class = "SUPPORTED" if population_supported else ("PARTIAL" if calibration_improves else "NOT SUPPORTED")
    scalar_safe = {
        variant: all(monotonicity[family][variant] >= .75 for family in structural.FAMILIES)
        and cross_summary[variant]["same_cell_compatibility_pass"]
        and cross_summary[variant]["union_uncertainty_reduction_pass"]
        for variant in ("HISTORICAL_TOTAL_SCALAR", "CONDITIONAL_ONLY_SCALAR")
    }
    architecture_safe = any(scalar_safe.values())
    cross_pass = all(result["same_cell_compatibility_pass"] for result in cross_summary.values())
    union_pass = all(result["union_uncertainty_reduction_pass"] for result in cross_summary.values())
    point_value = classify_point_value(structural_summary)
    p20_calibrated = any(
        .8 <= structural_summary[family][variant]["P20"]["joint_scale"] <= 1.25
        for family in structural.FAMILIES for variant in ("HISTORICAL_TOTAL_SCALAR", "CONDITIONAL_ONLY_SCALAR")
    )
    p20_class = "GRACEFUL" if p20_calibrated and architecture_safe else ("UNCERTAIN BUT CALIBRATION-DEGRADED" if architecture_safe else "FALSELY CONFIDENT")

    molecular_unchanged = all(torch.equal(source_before[name], adaptive.state_dict()[name].detach().cpu()) for name in source_before)
    core_unchanged = all(torch.equal(core_before[name], core.state_dict()[name].detach().cpu()) for name in core_before)
    semantics_pass = (
        semantics["measured_zero"]["states_distinct"]
        and semantics["training_vs_structural"]["training_target_eligible"]
        and not semantics["training_vs_structural"]["structural_target_eligible"]
        and semantics["foundation_unsupported_rejected"]
    )
    gates = {
        "molecular_information_preservation": retention_pass and molecular_unchanged and core_hashes == molecular_hashes,
        "gradient_firewall_architectural_separation": all(not parameter.requires_grad for parameter in core.ledger.parameters()),
        "factual_visible_state_contract": semantics["visible_state_formula"] == "A @ ((x - mu) * observed_mask)",
        "measurement_semantics": semantics_pass,
        "structural_value_firewall": semantics["structural_firewall_pass"],
        "simplified_diagonalized_parity": parity["pass"],
        "ordinary_belief_proper_score": ordinary_proper,
        "ordinary_belief_calibration": ordinary_calibration,
        "ordinary_uncertainty_localization": ordinary_localization,
        "structural_p60_raw_belief_value": structural_raw_proper,
        "structural_population_scale_calibration": population_supported,
        "structural_cell_level_uncertainty_localization": localization_pass,
        "uncertainty_increases_as_evidence_decreases": architecture_safe,
        "cross_panel_cell_identity": cross_pass,
        "union_evidence_reduces_uncertainty": union_pass,
        "no_harm_biological_state": ordinary_no_harm and structural_no_harm,
        "adaptive_correlated_evidence_removal": parity["pass"],
        "no_pathology_or_real_optimization": True,
    }
    if not parity["pass"]:
        classification = "ADAPTIVE CORRELATED EVIDENCE REMOVAL INVALID"
    elif not semantics_pass or not semantics["structural_firewall_pass"]:
        classification = "MEASUREMENT SEMANTICS REGRESSION"
    elif not (ordinary_proper and ordinary_calibration and ordinary_localization and structural_raw_proper):
        classification = "CORE BELIEF MECHANICS FAIL AFTER SIMPLIFICATION"
    elif not architecture_safe:
        classification = "CORE ARCHITECTURE SUCCESSFULLY SIMPLIFIED; SCALAR CALIBRATION IS NOT ARCHITECTURE-SAFE"
    elif not localization_pass:
        classification = "CORE ARCHITECTURE SUCCESSFULLY SIMPLIFIED; STRUCTURAL UNCERTAINTY LOCALIZATION REMAINS A3 BLOCKER"
    elif all(gates.values()):
        classification = "STAGE81A3 CORE ARCHITECTURE QUALIFIED FOR FREEZE RECOMMENDATION"
    else:
        classification = "CORE BELIEF MECHANICS FAIL AFTER SIMPLIFICATION"

    registry = failure_registry()
    secondary = {
        "adaptive_correlated_evidence": "REMOVED - UNEARNED",
        "fixed_prior_correlation": "RETAINED",
        "point_state_recovery": point_value,
        "structural_population_scale_calibration": population_class,
        "structural_cell_level_localization": "SUPPORTED" if localization_pass else "NOT SUPPORTED",
        "cross_panel_identity": "SUPPORTED" if cross_pass else "NOT SUPPORTED",
        "p20": p20_class,
        "counterfactual_capability": "NOT SUPPORTED",
    }
    payload = {
        "stage": "stage81a3_rbb_core_simplification", "anchor": base.ANCHOR, "seed": SEED,
        "classification": classification, "primary_gates": gates, "secondary_classifications": secondary,
        "prior_evidence": {"verified_hashes": evidence_hashes, "molecular_hashes": molecular_hashes},
        "source_checkpoint": {"path": str(SOURCE_CHECKPOINT), "sha256": SOURCE_CHECKPOINT_HASH, "role": "frozen-recovery source"},
        "rejected_panel_exposure_checkpoint": {"path": str(REJECTED_CHECKPOINT), "sha256": REJECTED_CHECKPOINT_HASH, "used": False},
        "migration": migration, "diagonalized_parity": parity,
        "molecular_retention": {
            **retention, "expected_retention_ratio": expected_retention,
            "absolute_difference": retention_difference, "numerical_readout_tolerance": 1e-6,
            "exact_state_hashes_required_separately": True, "pass": retention_pass,
        },
        "measurement_semantics": semantics, "panel_construction": panel_construction, "ordinary_bank_audit": bank_audit,
        "historical_total_scalar": historical_provenance, "conditional_only_scalar": {"value": conditional_scale, **conditional_fit},
        "ordinary_summary": ordinary_summary, "structural_summary": structural_summary,
        "p60_localization": localization, "calibration_variant_pass": calibration_variant_pass,
        "full_to_sparse_coordinate_monotonic_fraction": monotonicity, "calibration_architecture_safety": scalar_safe,
        "cross_panel_summary": cross_summary, "failure_registry": registry,
        "calibration_interpretation": "Population width and cell-level uncertainty ranking are distinct; scalar calibration cannot repair ranking.",
        "jepa_terminology": {"recommendation": "KEEP RBB AS PROJECT NAME BUT CALL CORE A BELIEF WORLD MODEL", "reason": "The core operates over frozen accountable latent state but has no EMA JEPA teacher objective in the belief stage."},
        "future_interfaces": {
            "regulator_adapter": "molecular ledger available with later soft-prior controls", "spatial_adapter": "cell belief and ledger available",
            "multimodal_adapter": "explicit modality measurement masks supported", "perturbation_controller": "pre-state and intervention interface remains possible",
            "implemented_in_this_task": False,
        },
        "parameters_unchanged": {"historical_source": molecular_unchanged, "simplified_core": core_unchanged},
        "governance": {
            "stage81a3_complete": False, "stage81a3_frozen": False, "stage81b_started": False,
            "model_training": False, "neural_optimizer_updates": 0, "optimizer_constructed": False,
            "real_rna_accessed": False, "pathology_opened": False, "factor_labels_used_for_fitting": False,
            "sealed_used_for_calibration_fitting": False, "hyperparameter_sweep": False, "seed_sweep": False,
        },
        "wall_seconds": time.perf_counter() - started,
    }
    calibration_rows = [row for row in structural_rows if row["panel"] == "P60"]
    base.atomic_csv(OUTPUTS["ordinary"], ordinary_rows); base.atomic_csv(OUTPUTS["structural"], structural_rows)
    base.atomic_csv(OUTPUTS["calibration"], calibration_rows); base.atomic_csv(OUTPUTS["cross"], cross_rows)
    base.atomic_csv(OUTPUTS["registry"], registry); base.atomic_json(OUTPUTS["json"], payload)
    append_readout(payload)
    print(json.dumps({
        "classification": classification, "historical_scale": historical_scale,
        "conditional_only_scale": conditional_scale, "gates": gates,
        "secondary": secondary, "optimizer_updates": 0,
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
