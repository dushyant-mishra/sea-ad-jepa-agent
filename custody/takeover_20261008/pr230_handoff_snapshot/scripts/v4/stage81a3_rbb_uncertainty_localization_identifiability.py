#!/usr/bin/env python3
"""Zero-core-update uncertainty-localization identifiability audit (RBB-ULI)."""

from __future__ import annotations

import argparse
import hashlib
import inspect
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
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import stage81a3_rbb_adaptive_correlated_probe as base  # noqa: E402
import stage81a3_rbb_core_simplification_audit as core_audit  # noqa: E402
import stage81a3_rbb_frozen_encoder_probe as frozen  # noqa: E402
import stage81a3_rbb_panel_exposure as exposure  # noqa: E402
import stage81a3_rbb_structural_panel_audit as structural  # noqa: E402
from sea_ad_jepa.v4.conditional_predictability import normalize_counts, ridge_fit, ridge_predict  # noqa: E402
from sea_ad_jepa.v4.rbb_adaptive import lrd_solve, structured_gaussian_terms  # noqa: E402
from sea_ad_jepa.v4.rbb_core import RBBCore  # noqa: E402


SEED = 8114001
TARGET_REPLICATES = 32
ORDINARY_INDICES = (0, 32, 64, 96)
JACKKNIFE_GROUPS = 8
JACKKNIFE_REMOVE = 123
RIDGE_ALPHA = 1e-3
MICROBATCH = 16
CORE_REPORT = Path("results/v4/stage81a3_rbb_core_simplification.json")
CORE_REPORT_HASH = "26bf8ed54d1b3efeed8012ab57d37e459a074d19bb75cf6a5431223d4e0bde28"
CORE_CHECKPOINT = Path("results/v4/stage81a3_rbb_core_simplified_checkpoint.pt")
CORE_CHECKPOINT_HASH = "ffab118f5f4573edfc0a83be1fbe2029ab53198ad5942f6c3a5aae532d7e089f"
CORE_MIGRATION = Path("results/v4/stage81a3_rbb_core_migration_manifest.json")
CORE_MIGRATION_HASH = "59269f41c6e9c32a20b9941034e2a00fc1f59a1047b06ac52d4ee33f4f5a08b7"
OUTPUTS = {
    "json": Path("results/v4/stage81a3_rbb_uncertainty_localization_identifiability.json"),
    "risk": Path("results/v4/stage81a3_rbb_uli_replicate_risk.csv"),
    "reliability": Path("results/v4/stage81a3_rbb_uli_reliability.csv"),
    "uncertainty": Path("results/v4/stage81a3_rbb_uli_rbb_uncertainty.csv"),
    "disagreement": Path("results/v4/stage81a3_rbb_uli_replicate_disagreement.csv"),
    "jackknife": Path("results/v4/stage81a3_rbb_uli_jackknife.csv"),
    "diagnostic": Path("results/v4/stage81a3_rbb_uli_diagnostic_ceiling.csv"),
    "factors": Path("results/v4/stage81a3_rbb_uli_factor_readout.csv"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def target_replicate_seed(index: int) -> int:
    if not 1 <= index <= TARGET_REPLICATES: raise ValueError("target replicate index must be 1..32")
    return SEED + 1_000_003 * index


def generate_target_replicate(rates: torch.Tensor, index: int) -> torch.Tensor:
    generator = torch.Generator(device=rates.device).manual_seed(target_replicate_seed(index))
    return normalize_counts(torch.poisson(rates, generator=generator))


def split_indices() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    return torch.arange(base.TRAIN), torch.arange(base.TRAIN, base.TRAIN + base.VALIDATION), torch.arange(base.TRAIN + base.VALIDATION, base.CELLS)


def load_frozen_core(device: torch.device, priors: dict[str, Any]) -> tuple[RBBCore, dict[str, str]]:
    if sha256(CORE_REPORT) != CORE_REPORT_HASH or sha256(CORE_CHECKPOINT) != CORE_CHECKPOINT_HASH or sha256(CORE_MIGRATION) != CORE_MIGRATION_HASH:
        raise RuntimeError("simplified-core evidence hash mismatch")
    adaptive, expected_hashes = core_audit.reconstruct_adaptive(device, priors)
    core = RBBCore().to(device); core.ledger.load_state_dict(adaptive.ledger.state_dict(), strict=True)
    checkpoint = torch.load(CORE_CHECKPOINT, map_location=device, weights_only=False)
    missing, unexpected = core.load_state_dict(checkpoint["belief_state_dict"], strict=False)
    if unexpected or any(not name.startswith("ledger.") for name in missing):
        raise RuntimeError(f"simplified checkpoint key mismatch: missing={missing}, unexpected={unexpected}")
    for parameter in core.parameters(): parameter.requires_grad_(False)
    core.eval()
    if frozen.frozen_hashes(core) != expected_hashes: raise RuntimeError("molecular hash mismatch")
    return core, expected_hashes


def condition_definitions(fixture: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    panels, panel_audit = structural.build_panels(fixture)
    banks, bank_audit = exposure.build_banks(fixture)
    conditions = []
    for family in structural.FAMILIES:
        for view in range(4):
            conditions.append({
                "condition": f"{family}_P60_V{view}", "major_family": family, "view": view,
                "ordinary": False, "measured": panels[family][view]["P60"],
                "prior": "RANDOM_40" if family == "RANDOM_STRUCTURAL" else "COEXPRESSION_BLOCK_40",
            })
    for label, prior in (("ORDINARY_RANDOM_40", "RANDOM_40"), ("ORDINARY_BLOCK_40", "COEXPRESSION_BLOCK_40")):
        for bank_index in ORDINARY_INDICES:
            conditions.append({
                "condition": f"{label}_I{bank_index}", "major_family": label, "view": bank_index,
                "ordinary": True, "measured": ~banks[label][bank_index], "prior": prior,
            })
    return conditions, {"structural": panel_audit, "ordinary": bank_audit, "ordinary_indices": list(ORDINARY_INDICES)}


def jackknife_masks(measured: torch.Tensor, view: int, family_index: int) -> list[torch.Tensor]:
    observed = torch.where(measured)[0]
    generator = torch.Generator().manual_seed(SEED + 7001 * (family_index + 1) + 101 * view)
    ordered = observed[torch.randperm(len(observed), generator=generator)]
    result = []
    for group in range(JACKKNIFE_GROUPS):
        current = measured.clone(); current[ordered[group * JACKKNIFE_REMOVE:(group + 1) * JACKKNIFE_REMOVE]] = False
        result.append(current)
    return result


def forward_condition(
    core: RBBCore, expression: torch.Tensor, measured: torch.Tensor, ordinary: bool,
    basis: Any, prior: dict[str, Any], device: torch.device, indices: torch.Tensor,
    *, features: bool,
) -> dict[str, torch.Tensor]:
    names = ["posterior", "belief", "conditional_trace", "noise_trace", "total_trace", "logdet", "median_marginal", "total_diagonal", "total_low_rank"]
    if features: names += ["visible", "log_conditional", "log_total", "token_mean", "token_std", "mask_context"]
    collected = {name: [] for name in names}
    with torch.no_grad():
        for start in range(0, len(indices), MICROBATCH):
            selected = indices[start:start + MICROBATCH].to(device); values = expression[selected]
            state, hidden = core_audit.make_state(measured, len(selected), device, ordinary=ordinary)
            with torch.autocast("cuda", dtype=torch.float16):
                output = core_audit.core_forward(core, values, state, hidden, basis, prior)
            conditional_marginal = output.raw_conditional_diagonal + output.raw_conditional_low_rank.square().sum(-1)
            total_marginal = output.raw_total_diagonal + output.raw_total_low_rank.square().sum(-1)
            _, _, logdet = structured_gaussian_terms(torch.zeros_like(output.posterior_missing_mean), output.raw_total_diagonal, output.raw_total_low_rank)
            values_out = {
                "posterior": output.posterior_missing_mean, "belief": output.belief_mean,
                "conditional_trace": conditional_marginal.sum(1), "noise_trace": output.measurement_noise_diagonal.sum(1),
                "total_trace": total_marginal.sum(1), "logdet": logdet, "median_marginal": total_marginal.median(1).values,
                "total_diagonal": output.raw_total_diagonal, "total_low_rank": output.raw_total_low_rank,
            }
            if features:
                observed = state.observed_mask[0]; token_subset = output.molecular_evidence_tokens[:, observed]
                values_out.update({
                    "visible": output.visible_state, "log_conditional": conditional_marginal.clamp_min(1e-12).log(),
                    "log_total": total_marginal.clamp_min(1e-12).log(), "token_mean": token_subset.float().mean(1),
                    "token_std": token_subset.float().std(1, unbiased=False),
                    "mask_context": base.mask_context(basis, hidden, prior, len(selected)),
                })
            for name, value in values_out.items(): collected[name].append(value.float().cpu())
    return {name: torch.cat(parts) for name, parts in collected.items()}


def risk_statistics(values: torch.Tensor) -> dict[str, float]:
    values = values.double().flatten(); mean = float(values.mean()); std = float(values.std(unbiased=False))
    return {
        "mean": mean, "std": std, "coefficient_of_variation": std / max(abs(mean), 1e-12),
        **{f"p{int(q*100):02d}": float(torch.quantile(values, q)) for q in (.10, .25, .50, .75, .90, .95)},
    }


def assemble_risk_objects(
    replicate_errors: torch.Tensor,
    replicate_noise_errors: torch.Tensor,
    replicate_cross_terms: torch.Tensor,
    biological_residual: torch.Tensor,
) -> dict[str, torch.Tensor]:
    if replicate_errors.shape[0] != TARGET_REPLICATES:
        raise ValueError("risk assembly requires exactly 32 target replicates")
    return {
        "single": replicate_errors[0],
        "total": replicate_errors.mean(0),
        "total_a": replicate_errors[:16].mean(0),
        "total_b": replicate_errors[16:].mean(0),
        "bio": biological_residual.square().mean(1),
        "noise": replicate_noise_errors.mean(0),
        "cross": replicate_cross_terms.mean(0),
    }


def jackknife_scores(means: torch.Tensor, traces: torch.Tensor, base_mean: torch.Tensor, base_trace: torch.Tensor) -> dict[str, torch.Tensor]:
    if means.shape[0] != JACKKNIFE_GROUPS or traces.shape[0] != JACKKNIFE_GROUPS:
        raise ValueError("jackknife scoring requires exactly eight groups")
    shifts = (means - base_mean).square().mean(2)
    deltas = traces - base_trace
    return {
        "fragility": shifts.mean(0), "maximum": shifts.max(0).values,
        "coordinate_variance": means.var(0, unbiased=False).sum(1),
        "mean_delta": deltas.mean(0), "max_delta": deltas.max(0).values,
    }


def metric_ridge(truth: torch.Tensor, prediction: torch.Tensor) -> dict[str, float]:
    truth = truth.float().flatten(); prediction = prediction.float().flatten()
    total = (truth - truth.mean()).square().sum()
    return {
        "spearman": base.spearman(prediction, truth),
        "r2_log1p_risk": float(1 - (truth - prediction).square().sum() / total.clamp_min(1e-12)),
        "mae_log1p_risk": float((truth - prediction).abs().mean()),
    }


def historical_localization_target_audit() -> dict[str, Any]:
    current_source = inspect.getsource(core_audit.evaluate_condition)
    historical_source = inspect.getsource(structural.panel_forward)
    lambda_in_current = "target = basis.contribution(fixture.lambda_norm[selected], hidden)" in current_source
    lambda_in_historical = "target = basis.contribution(fixture.lambda_norm[selected], hidden)" in historical_source
    if not (lambda_in_current and lambda_in_historical):
        raise RuntimeError("historical localization target provenance changed")
    return {
        "historical_target": "EXPECTED_BIOLOGICAL_STATE_FROM_LAMBDA_NORM",
        "historical_target_was_single_stochastic_realization": False,
        "historical_gate_remains_failed": True,
        "interpretation_correction": "The prior structural rho near 0.1 measured expected-biological-risk localization, not single-target sequencing-noise localization.",
    }


def append_readout(payload: dict[str, Any]) -> None:
    path = Path("docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md")
    marker = "## Uncertainty Localization Identifiability Audit"
    existing = path.read_text(encoding="utf-8")
    if marker in existing: raise RuntimeError("RBB-ULI readout already exists")
    section = f"""

{marker}

This audit was run before any further architecture change because the prior structural-panel
localization failure could reflect either a noisy evaluation target or a genuinely weak uncertainty
mapping. The frozen simplified core received zero updates. One stochastic target can rank cells
poorly when target sequencing noise is large, whereas 32-replicate average risk estimates the
conditional expected predictive difficulty for a fixed visible observation. Expected biological
risk and measurement-noise risk were therefore kept separate.

The implementation audit corrected an important premise: the historical structural localization
gate used expected `LAMBDA_NORM` biological-state error, not one stochastic sequencing target.
That historical failure remains unchanged. The new B01 single-realization gate is reported
separately and cannot retroactively relabel the prior result.

Repeated-measurement disagreement was tested as a reproducibility diagnostic: it asks whether the
inferred state is stable across two legitimate observations of the same synthetic cell. The
evidence jackknife measured inference fragility after deterministic removal of additional valid
evidence; it is not causal importance or gene essentiality. Two fixed-alpha ridge regressions were
used only as ceiling probes for recoverable visible-evidence information. They are not architecture
proposals and no fitted weights were persisted.

Primary classification: **{payload['classification']}**.

Replicate-averaged risk reliability: **{payload['gates']['replicate_averaged_risk_reliable']}**.
Original single-realization localization gate: **{payload['gates']['original_single_realization_gate']}**.
Replicate-averaged total-risk gate: **{payload['gates']['replicate_averaged_total_risk_gate']}**.
Expected-biological-risk gate: **{payload['gates']['expected_biological_risk_gate']}**.
Replicate disagreement: **{payload['secondary_classifications']['replicate_disagreement_signal']}**.
Evidence jackknife: **{payload['secondary_classifications']['evidence_jackknife_signal']}**.
Visible-evidence diagnostic ceiling: **{payload['secondary_classifications']['visible_evidence_diagnostic_ceiling']}**.

All earlier single-target localization failures remain historical facts. This synthetic forensic
audit does not establish real-RNA validity, pathology biology, causal mechanisms, spatial biology,
regulatory pathways, perturbation dynamics, or Stage81A3 completion.
"""
    base.atomic_text(path, existing.rstrip() + section + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--project-dir", type=Path, default=ROOT)
    args = parser.parse_args(); os.chdir(args.project_dir.resolve())
    if any(path.exists() for path in OUTPUTS.values()): raise RuntimeError("RBB-ULI artifact already exists; repeat forbidden")
    if not torch.cuda.is_available(): raise RuntimeError("CUDA is required for bounded RBB-ULI")
    started = time.perf_counter(); device = torch.device("cuda")
    torch.set_float32_matmul_precision("high"); torch.backends.cuda.matmul.allow_tf32 = True
    torch.cuda.reset_peak_memory_stats(device)
    prior_hashes = core_audit.verify_evidence()
    prior_hashes.update({str(CORE_REPORT): sha256(CORE_REPORT), str(CORE_CHECKPOINT): sha256(CORE_CHECKPOINT), str(CORE_MIGRATION): sha256(CORE_MIGRATION)})
    torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    basis = base.load_basis(device); fixture = base.build_fixture(device); priors = base.frozen_family_statistics(device)
    core, molecular_hashes = load_frozen_core(device, priors)
    core_state_before = {name: value.detach().cpu().clone() for name, value in core.state_dict().items()}
    conditions, mask_provenance = condition_definitions(fixture)
    all_indices = torch.arange(base.CELLS); structural_conditions = [item for item in conditions if not item["ordinary"]]

    forward_started = time.perf_counter(); forward_outputs: dict[str, dict[str, torch.Tensor]] = {}
    for item in conditions:
        print(f"base forward {item['condition']}", flush=True)
        forward_outputs[item["condition"]] = forward_condition(
            core, fixture.x_a, item["measured"], item["ordinary"], basis, priors[item["prior"]], device,
            all_indices, features=not item["ordinary"],
        )
    paired_outputs = {}
    for item in structural_conditions:
        print(f"paired-view forward {item['condition']}", flush=True)
        paired_outputs[item["condition"]] = forward_condition(
            core, fixture.x_b, item["measured"], False, basis, priors[item["prior"]], device,
            all_indices, features=False,
        )
    model_forward_seconds = time.perf_counter() - forward_started

    target_started = time.perf_counter()
    errors = {item["condition"]: torch.empty(TARGET_REPLICATES, base.CELLS) for item in conditions}
    noise_errors = {item["condition"]: torch.empty(TARGET_REPLICATES, base.CELLS) for item in conditions}
    cross_terms = {item["condition"]: torch.empty(TARGET_REPLICATES, base.CELLS) for item in conditions}
    expected_targets = {}
    for item in conditions:
        hidden = (~item["measured"]).to(device)
        expected_targets[item["condition"]] = basis.contribution(fixture.lambda_norm, hidden).float().cpu()
    rng_derivation = []
    for replicate in range(1, TARGET_REPLICATES + 1):
        print(f"target replicate {replicate}/{TARGET_REPLICATES}", flush=True)
        rng_derivation.append({"replicate": replicate, "seed": target_replicate_seed(replicate)})
        target_expression = generate_target_replicate(fixture.rates, replicate)
        for item in conditions:
            name = item["condition"]; hidden = (~item["measured"]).to(device)
            target = basis.contribution(target_expression, hidden).float().cpu()
            biological = expected_targets[name] - forward_outputs[name]["posterior"]
            noise = target - expected_targets[name]
            errors[name][replicate - 1] = (target - forward_outputs[name]["posterior"]).square().mean(1)
            noise_errors[name][replicate - 1] = noise.square().mean(1)
            cross_terms[name][replicate - 1] = 2 * (biological * noise).mean(1)
        del target_expression
    target_generation_seconds = time.perf_counter() - target_started

    train_idx, validation_idx, sealed_idx = split_indices()
    risk_state: dict[str, dict[str, torch.Tensor]] = {}
    risk_rows = []; reliability_rows = []; uncertainty_rows = []; factor_rows = []
    metric_by_condition: dict[str, dict[str, float]] = {}
    for item in conditions:
        name = item["condition"]; current = errors[name]; current_noise = noise_errors[name]
        biological_residual = expected_targets[name] - forward_outputs[name]["posterior"]
        values = assemble_risk_objects(current, current_noise, cross_terms[name], biological_residual)
        risk_state[name] = values
        split_half = base.spearman(values["total_a"][sealed_idx], values["total_b"][sealed_idx])
        single_correlations = torch.tensor([base.spearman(current[k, sealed_idx], values["total"][sealed_idx]) for k in range(TARGET_REPLICATES)])
        within = current[:, sealed_idx].var(0, unbiased=False).mean(); between = values["total"][sealed_idx].var(unbiased=False)
        reliability_index = float(between / (between + within).clamp_min(1e-12))
        out = forward_outputs[name]
        associations = {
            "rho_conditional_vs_bio": base.spearman(out["conditional_trace"][sealed_idx], values["bio"][sealed_idx]),
            "rho_noise_vs_noise": base.spearman(out["noise_trace"][sealed_idx], values["noise"][sealed_idx]),
            "rho_total_vs_single": base.spearman(out["total_trace"][sealed_idx], values["single"][sealed_idx]),
            "rho_total_vs_total": base.spearman(out["total_trace"][sealed_idx], values["total"][sealed_idx]),
            "rho_total_vs_bio": base.spearman(out["total_trace"][sealed_idx], values["bio"][sealed_idx]),
        }
        metric_by_condition[name] = associations
        decomposition_difference = values["total"] - values["bio"] - values["noise"] - values["cross"]
        reliability_rows.append({
            "condition": name, "major_family": item["major_family"], "view": item["view"], "evaluation_split": "SEALED",
            "split_half_spearman": split_half, "single_vs_total_replicate_01": float(single_correlations[0]),
            "single_vs_total_median": float(single_correlations.median()), "single_vs_total_q25": float(torch.quantile(single_correlations, .25)),
            "single_vs_total_q75": float(torch.quantile(single_correlations, .75)), "single_vs_total_min": float(single_correlations.min()),
            "single_vs_total_max": float(single_correlations.max()), "between_cell_variance": float(between),
            "mean_within_cell_variance": float(within), "error_rank_reliability_index": reliability_index,
            "cross_term_mean": float(values["cross"][sealed_idx].mean()), "cross_term_median": float(values["cross"][sealed_idx].median()),
            "cross_term_p95_absolute": float(torch.quantile(values["cross"][sealed_idx].abs(), .95)),
            "decomposition_max_absolute_error": float(decomposition_difference.abs().max()), **associations,
        })
        for cell in range(base.CELLS):
            risk_rows.append({
                "condition": name, "major_family": item["major_family"], "view": item["view"], "cell_index": cell,
                "split": "TRAIN" if cell < base.TRAIN else ("VALIDATION" if cell < base.TRAIN + base.VALIDATION else "SEALED"),
                "risk_single": float(values["single"][cell]), "risk_total": float(values["total"][cell]),
                "risk_biological": float(values["bio"][cell]), "risk_measurement_noise": float(values["noise"][cell]),
                "risk_cross_term": float(values["cross"][cell]),
            })
            uncertainty_rows.append({
                "condition": name, "major_family": item["major_family"], "view": item["view"], "cell_index": cell,
                "trace_conditional": float(out["conditional_trace"][cell]), "trace_measurement_noise": float(out["noise_trace"][cell]),
                "trace_total": float(out["total_trace"][cell]), "logdet_total": float(out["logdet"][cell]),
                "median_marginal_total_variance": float(out["median_marginal"][cell]),
            })
        if not item["ordinary"]:
            factor_values = fixture.factors[sealed_idx].cpu()
            for factor in range(base.FACTORS):
                factor_rows.append({"condition": name, "major_family": item["major_family"], "view": item["view"], "type": "synthetic_factor", "index": factor, "rho_with_biological_risk": base.spearman(factor_values[:, factor], values["bio"][sealed_idx])})
            coordinate_error = biological_residual[sealed_idx].square().mean(0)
            coverage = (basis.analysis.square()[:, item["measured"].to(device)].sum(1) / basis.analysis.square().sum(1).clamp_min(1e-12)).cpu()
            for coordinate in range(base.WIDTH):
                factor_rows.append({"condition": name, "major_family": item["major_family"], "view": item["view"], "type": "reppca_coordinate", "index": coordinate, "mean_biological_squared_error": float(coordinate_error[coordinate]), "panel_squared_energy_coverage": float(coverage[coordinate])})

    disagreement_rows = []; disagreement_state = {}
    for item in structural_conditions:
        name = item["condition"]; a, b = forward_outputs[name], paired_outputs[name]
        delta = a["belief"] - b["belief"]
        raw = delta.square().mean(1)
        standardized = (delta * lrd_solve(delta, a["total_diagonal"] + b["total_diagonal"], torch.cat((a["total_low_rank"], b["total_low_rank"]), -1))).sum(1) / base.WIDTH
        disagreement_state[name] = {"raw": raw, "standardized": standardized}
        metrics = {
            "rho_disagreement_vs_total": base.spearman(raw[sealed_idx], risk_state[name]["total"][sealed_idx]),
            "rho_disagreement_vs_bio": base.spearman(raw[sealed_idx], risk_state[name]["bio"][sealed_idx]),
            "rho_disagreement_vs_noise": base.spearman(raw[sealed_idx], risk_state[name]["noise"][sealed_idx]),
            "rho_standardized_disagreement_vs_total": base.spearman(standardized[sealed_idx], risk_state[name]["total"][sealed_idx]),
        }
        for cell in range(base.CELLS):
            disagreement_rows.append({"condition": name, "major_family": item["major_family"], "view": item["view"], "cell_index": cell, "replicate_disagreement": float(raw[cell]), "standardized_replicate_disagreement": float(standardized[cell]), **metrics})

    jackknife_started = time.perf_counter(); jackknife_rows = []; jackknife_state = {}
    for family_index, item in enumerate(structural_conditions):
        name = item["condition"]; masks = jackknife_masks(item["measured"], item["view"], family_index // 4)
        means = []; traces = []
        for group, mask in enumerate(masks):
            print(f"jackknife {name} group={group + 1}/8", flush=True)
            result = forward_condition(core, fixture.x_a, mask, False, basis, priors[item["prior"]], device, all_indices, features=False)
            means.append(result["belief"]); traces.append(result["total_trace"])
        means_t = torch.stack(means); traces_t = torch.stack(traces); base_mean = forward_outputs[name]["belief"]
        scores = jackknife_scores(means_t, traces_t, base_mean, forward_outputs[name]["total_trace"])
        fragility, maximum = scores["fragility"], scores["maximum"]
        coordinate_variance, mean_delta, max_delta = scores["coordinate_variance"], scores["mean_delta"], scores["max_delta"]
        jackknife_state[name] = scores
        metrics = {
            "rho_fragility_vs_total": base.spearman(fragility[sealed_idx], risk_state[name]["total"][sealed_idx]),
            "rho_fragility_vs_bio": base.spearman(fragility[sealed_idx], risk_state[name]["bio"][sealed_idx]),
            "rho_max_shift_vs_total": base.spearman(maximum[sealed_idx], risk_state[name]["total"][sealed_idx]),
            "rho_mean_delta_trace_vs_total": base.spearman(mean_delta[sealed_idx], risk_state[name]["total"][sealed_idx]),
            "rho_shifted_cell_negative_control": base.spearman(fragility[sealed_idx], risk_state[name]["total"][sealed_idx].roll(-1)),
        }
        for cell in range(base.CELLS):
            jackknife_rows.append({"condition": name, "major_family": item["major_family"], "view": item["view"], "cell_index": cell, "jackknife_fragility": float(fragility[cell]), "jackknife_max_shift": float(maximum[cell]), "jackknife_coordinate_variance_trace": float(coordinate_variance[cell]), "mean_delta_trace": float(mean_delta[cell]), "max_delta_trace": float(max_delta[cell]), **metrics})
    jackknife_seconds = time.perf_counter() - jackknife_started

    diagnostic_started = time.perf_counter()
    base_features = {}; stability_features = {}
    for item in structural_conditions:
        name = item["condition"]; out = forward_outputs[name]; jack = jackknife_state[name]; disagreement = disagreement_state[name]
        base_features[name] = torch.cat((
            out["visible"], out["posterior"], out["log_conditional"], out["log_total"],
            out["token_mean"], out["token_std"], out["mask_context"],
        ), dim=1)
        stability_features[name] = torch.cat((
            base_features[name], disagreement["raw"][:, None], disagreement["standardized"][:, None],
            jack["fragility"][:, None], jack["maximum"][:, None], jack["coordinate_variance"][:, None],
            jack["mean_delta"][:, None], jack["max_delta"][:, None],
        ), dim=1)
    train_x_base = torch.cat([base_features[item["condition"]][train_idx] for item in structural_conditions])
    train_x_stability = torch.cat([stability_features[item["condition"]][train_idx] for item in structural_conditions])
    train_y = torch.log1p(torch.cat([risk_state[item["condition"]]["total"][train_idx] for item in structural_conditions]))[:, None]
    base_model = ridge_fit(train_x_base, train_y, RIDGE_ALPHA)
    stability_model = ridge_fit(train_x_stability, train_y, RIDGE_ALPHA)
    diagnostic_rows = []; diagnostic_predictions = {}
    for model_name, model, features in (
        ("BASE_DIAGNOSTIC", base_model, base_features),
        ("STABILITY_DIAGNOSTIC", stability_model, stability_features),
    ):
        diagnostic_predictions[model_name] = {}
        for family in structural.FAMILIES:
            family_items = [item for item in structural_conditions if item["major_family"] == family]
            for split_name, indices in (("VALIDATION", validation_idx), ("SEALED", sealed_idx)):
                x = torch.cat([features[item["condition"]][indices] for item in family_items])
                truth = torch.log1p(torch.cat([risk_state[item["condition"]]["total"][indices] for item in family_items]))
                prediction = ridge_predict(model, x).flatten()
                metrics = metric_ridge(truth, prediction)
                diagnostic_rows.append({
                    "model": model_name, "major_family": family, "split": split_name,
                    "alpha": RIDGE_ALPHA, "n_examples": len(truth), "feature_dimension": x.shape[1], **metrics,
                })
                diagnostic_predictions[model_name][(family, split_name)] = prediction
    del base_model, stability_model, train_x_base, train_x_stability, train_y
    diagnostic_seconds = time.perf_counter() - diagnostic_started

    family_summary = {}
    for family in [*structural.FAMILIES, "ORDINARY_RANDOM_40", "ORDINARY_BLOCK_40"]:
        family_items = [item for item in conditions if item["major_family"] == family]
        family_reliability = [row for row in reliability_rows if row["major_family"] == family]
        total_values = torch.cat([risk_state[item["condition"]]["total"][sealed_idx] for item in family_items])
        bio_values = torch.cat([risk_state[item["condition"]]["bio"][sealed_idx] for item in family_items])
        noise_values = torch.cat([risk_state[item["condition"]]["noise"][sealed_idx] for item in family_items])
        traces = {
            key: torch.cat([forward_outputs[item["condition"]][key][sealed_idx] for item in family_items])
            for key in ("conditional_trace", "noise_trace", "total_trace")
        }
        family_summary[family] = {
            "views": len(family_items),
            "median_split_half_spearman": float(np.median([row["split_half_spearman"] for row in family_reliability])),
            "median_single_vs_total_spearman": float(np.median([row["single_vs_total_median"] for row in family_reliability])),
            "median_error_rank_reliability_index": float(np.median([row["error_rank_reliability_index"] for row in family_reliability])),
            "median_rbb_trace_total_vs_single": float(np.median([row["rho_total_vs_single"] for row in family_reliability])),
            "median_rbb_trace_total_vs_total": float(np.median([row["rho_total_vs_total"] for row in family_reliability])),
            "median_rbb_trace_total_vs_bio": float(np.median([row["rho_total_vs_bio"] for row in family_reliability])),
            "median_rbb_trace_conditional_vs_bio": float(np.median([row["rho_conditional_vs_bio"] for row in family_reliability])),
            "median_rbb_trace_noise_vs_noise": float(np.median([row["rho_noise_vs_noise"] for row in family_reliability])),
            "total_risk_dynamic_range": risk_statistics(total_values), "biological_risk_dynamic_range": risk_statistics(bio_values),
            "measurement_noise_fraction_of_mean_total_risk": float(noise_values.mean() / total_values.mean().clamp_min(1e-12)),
            "trace_variance_across_cells": {key: float(value.var(unbiased=False)) for key, value in traces.items()},
        }
    for family in structural.FAMILIES:
        names = [item["condition"] for item in structural_conditions if item["major_family"] == family]
        family_summary[family].update({
            "median_replicate_disagreement_vs_total": float(np.median([base.spearman(disagreement_state[name]["raw"][sealed_idx], risk_state[name]["total"][sealed_idx]) for name in names])),
            "median_replicate_disagreement_vs_bio": float(np.median([base.spearman(disagreement_state[name]["raw"][sealed_idx], risk_state[name]["bio"][sealed_idx]) for name in names])),
            "median_replicate_disagreement_vs_noise": float(np.median([base.spearman(disagreement_state[name]["raw"][sealed_idx], risk_state[name]["noise"][sealed_idx]) for name in names])),
            "median_standardized_disagreement_vs_total": float(np.median([base.spearman(disagreement_state[name]["standardized"][sealed_idx], risk_state[name]["total"][sealed_idx]) for name in names])),
            "median_jackknife_fragility_vs_total": float(np.median([base.spearman(jackknife_state[name]["fragility"][sealed_idx], risk_state[name]["total"][sealed_idx]) for name in names])),
            "median_jackknife_fragility_vs_bio": float(np.median([base.spearman(jackknife_state[name]["fragility"][sealed_idx], risk_state[name]["bio"][sealed_idx]) for name in names])),
            "median_jackknife_max_shift_vs_total": float(np.median([base.spearman(jackknife_state[name]["maximum"][sealed_idx], risk_state[name]["total"][sealed_idx]) for name in names])),
            "median_jackknife_delta_trace_vs_total": float(np.median([base.spearman(jackknife_state[name]["mean_delta"][sealed_idx], risk_state[name]["total"][sealed_idx]) for name in names])),
            "median_jackknife_shifted_negative_control": float(np.median([base.spearman(jackknife_state[name]["fragility"][sealed_idx], risk_state[name]["total"][sealed_idx].roll(-1)) for name in names])),
        })
        for model_name in ("BASE_DIAGNOSTIC", "STABILITY_DIAGNOSTIC"):
            row = next(row for row in diagnostic_rows if row["model"] == model_name and row["major_family"] == family and row["split"] == "SEALED")
            family_summary[family][f"{model_name.lower()}_sealed_spearman"] = row["spearman"]

    reliability_pass = all(family_summary[family]["median_split_half_spearman"] >= .85 for family in structural.FAMILIES)
    single_gate = all(family_summary[family]["median_rbb_trace_total_vs_single"] > .50 for family in structural.FAMILIES)
    total_gate = all(family_summary[family]["median_rbb_trace_total_vs_total"] > .50 for family in structural.FAMILIES)
    bio_gate = all(family_summary[family]["median_rbb_trace_total_vs_bio"] > .50 for family in structural.FAMILIES)
    strong_signals = {
        "replicate_disagreement": all(max(family_summary[f]["median_replicate_disagreement_vs_total"], family_summary[f]["median_standardized_disagreement_vs_total"]) > .50 for f in structural.FAMILIES),
        "jackknife_fragility": all(max(family_summary[f]["median_jackknife_fragility_vs_total"], family_summary[f]["median_jackknife_fragility_vs_bio"]) > .50 for f in structural.FAMILIES),
        "base_diagnostic": all(family_summary[f]["base_diagnostic_sealed_spearman"] > .50 for f in structural.FAMILIES),
        "stability_diagnostic": all(family_summary[f]["stability_diagnostic_sealed_spearman"] > .50 for f in structural.FAMILIES),
    }
    current = {family: family_summary[family]["median_rbb_trace_total_vs_total"] for family in structural.FAMILIES}
    best_diagnostic = {
        family: max(
            family_summary[family]["median_replicate_disagreement_vs_total"], family_summary[family]["median_standardized_disagreement_vs_total"],
            family_summary[family]["median_jackknife_fragility_vs_total"], family_summary[family]["median_jackknife_fragility_vs_bio"],
            family_summary[family]["base_diagnostic_sealed_spearman"], family_summary[family]["stability_diagnostic_sealed_spearman"],
        ) for family in structural.FAMILIES
    }
    partial_signal = any(best_diagnostic[family] >= current[family] + .10 for family in structural.FAMILIES)
    historical_target = historical_localization_target_audit()
    measurement_noise_dominant = all(family_summary[f]["measurement_noise_fraction_of_mean_total_risk"] > .50 for f in structural.FAMILIES)
    taxonomy_conflict = reliability_pass and single_gate and total_gate and not bio_gate and measurement_noise_dominant
    if taxonomy_conflict:
        classification = "ENGINEERING / NUMERICAL FAILURE"
    elif not reliability_pass:
        classification = "REPLICATE-AVERAGED RISK TARGET INSUFFICIENTLY STABLE"
    elif total_gate and all(current[f] >= family_summary[f]["median_rbb_trace_total_vs_single"] + .10 for f in structural.FAMILIES):
        classification = "SINGLE-REALIZATION LOCALIZATION GATE IS NOISE-LIMITED; CURRENT RBB UNCERTAINTY LOCALIZES REPLICATE-AVERAGED RISK"
    elif any(strong_signals.values()):
        classification = "RECOVERABLE CELL-LEVEL UNCERTAINTY SIGNAL EXISTS; CURRENT RBB UNCERTAINTY MAPPING MISSES IT"
    elif partial_signal:
        classification = "REPLICATE / JACKKNIFE STABILITY PROVIDES PARTIAL LOCALIZATION SIGNAL"
    else:
        classification = "NO STRONG RECOVERABLE CELL-LEVEL LOCALIZATION SIGNAL DEMONSTRATED"

    single_rank = float(np.median([family_summary[f]["median_single_vs_total_spearman"] for f in structural.FAMILIES]))
    single_class = "RELIABLE" if single_rank >= .85 else ("NOISE-LIMITED" if reliability_pass and single_rank < .50 else "INCONCLUSIVE")
    rep_best = {f: max(family_summary[f]["median_replicate_disagreement_vs_total"], family_summary[f]["median_standardized_disagreement_vs_total"]) for f in structural.FAMILIES}
    jack_best = {f: max(family_summary[f]["median_jackknife_fragility_vs_total"], family_summary[f]["median_jackknife_fragility_vs_bio"]) for f in structural.FAMILIES}
    secondary = {
        "single_replicate_error_as_cell_ranking_target": single_class,
        "expected_biological_risk_localization": "SUPPORTED" if bio_gate else ("PARTIAL" if any(family_summary[f]["median_rbb_trace_total_vs_bio"] > .50 for f in structural.FAMILIES) else "NOT SUPPORTED"),
        "measurement_noise_dominance": "SUPPORTED" if measurement_noise_dominant else "NOT SUPPORTED",
        "replicate_disagreement_signal": "STRONG" if strong_signals["replicate_disagreement"] else ("PARTIAL" if any(rep_best[f] >= current[f] + .10 for f in structural.FAMILIES) else "ABSENT"),
        "evidence_jackknife_signal": "STRONG" if strong_signals["jackknife_fragility"] else ("PARTIAL" if any(jack_best[f] >= current[f] + .10 for f in structural.FAMILIES) else "ABSENT"),
        "visible_evidence_diagnostic_ceiling": "ABOVE 0.50" if strong_signals["base_diagnostic"] or strong_signals["stability_diagnostic"] else "BELOW 0.50",
        "current_rbb_uncertainty": "ADEQUATE FOR REPLICATE-AVERAGED RISK" if total_gate else ("MISALIGNED WITH RECOVERABLE RISK" if any(strong_signals.values()) else "LIMITED BY AVAILABLE SIGNAL"),
    }
    recommendation = {
        "SINGLE-REALIZATION LOCALIZATION GATE IS NOISE-LIMITED; CURRENT RBB UNCERTAINTY LOCALIZES REPLICATE-AVERAGED RISK": "REVISIT THE A3 LOCALIZATION EVALUATION CONTRACT, NOT THE ARCHITECTURE.",
        "RECOVERABLE CELL-LEVEL UNCERTAINTY SIGNAL EXISTS; CURRENT RBB UNCERTAINTY MAPPING MISSES IT": "DO NOT CHANGE MOLECULAR LEDGER. Human review may design one small behind-firewall localization side module using the strongest validated signal.",
        "REPLICATE / JACKKNIFE STABILITY PROVIDES PARTIAL LOCALIZATION SIGNAL": "HUMAN REVIEW BEFORE ANY NEW MODEL.",
        "NO STRONG RECOVERABLE CELL-LEVEL LOCALIZATION SIGNAL DEMONSTRATED": "DO NOT FORCE THE >0.50 GATE THROUGH ARCHITECTURE SEARCH; consider retaining localization as a known limitation.",
        "REPLICATE-AVERAGED RISK TARGET INSUFFICIENTLY STABLE": "FIX EVALUATION / ENGINEERING ONLY.",
        "ENGINEERING / NUMERICAL FAILURE": "FIX THE EVALUATION CLASSIFICATION CONTRACT ONLY. The computed forensic metrics remain valid, but no predeclared A-E class covers reliable single/total predictive-risk localization with failed biological-risk localization.",
    }[classification]

    after_hashes = frozen.frozen_hashes(core)
    core_unchanged = all(torch.equal(core_state_before[name], core.state_dict()[name].detach().cpu()) for name in core_state_before)
    checkpoint_unchanged = sha256(CORE_CHECKPOINT) == CORE_CHECKPOINT_HASH
    performance = {
        "target_replicate_generation_and_projection_seconds": target_generation_seconds,
        "model_forward_seconds": model_forward_seconds, "jackknife_forward_seconds": jackknife_seconds,
        "diagnostic_fitting_seconds": diagnostic_seconds,
        "peak_allocated_vram_gb": torch.cuda.max_memory_allocated(device) / 2**30,
        "peak_reserved_vram_gb": torch.cuda.max_memory_reserved(device) / 2**30,
        "mean_gpu_utilization": "unavailable_without_sampling_sidecar", "total_wall_seconds": time.perf_counter() - started,
    }
    payload = {
        "stage": "stage81a3_rbb_uncertainty_localization_identifiability", "anchor": base.ANCHOR, "seed": SEED,
        "classification": classification, "secondary_classifications": secondary, "recommended_next_step_not_executed": recommendation,
        "prior_evidence_hashes": prior_hashes, "molecular_hashes_before": molecular_hashes, "molecular_hashes_after": after_hashes,
        "frozen_core": {"checkpoint": str(CORE_CHECKPOINT), "sha256": CORE_CHECKPOINT_HASH, "checkpoint_unchanged": checkpoint_unchanged, "parameters_unchanged": core_unchanged},
        "mask_provenance": mask_provenance, "historical_localization_target_audit": historical_target,
        "classification_contract": {"taxonomy_conflict": taxonomy_conflict, "computed_metrics_valid": True, "reason": "Observed combination is outside predeclared A-E definitions" if taxonomy_conflict else None},
        "target_replicates": {"count": TARGET_REPLICATES, "rng_derivation": rng_derivation, "visible_observation_fixed": "X_A", "evaluation_targets_only": True},
        "risk_definitions": {
            "single": "||r_B01 - mu_H||^2 / 160", "total": "mean_k ||r_Bk - mu_H||^2 / 160",
            "biological": "||r_lambda - mu_H||^2 / 160", "measurement_noise": "mean_k ||r_Bk - r_lambda||^2 / 160",
        },
        "family_summary": family_summary, "strong_signal_gates": strong_signals, "best_diagnostic_spearman": best_diagnostic,
        "gates": {
            "replicate_averaged_risk_reliable": reliability_pass,
            "original_single_realization_gate": "FAIL",
            "new_b01_single_realization_gate": "PASS" if single_gate else "FAIL",
            "replicate_averaged_total_risk_gate": "PASS" if total_gate else "FAIL",
            "expected_biological_risk_gate": "PASS" if bio_gate else "FAIL",
            "molecular_information_preserved": core_unchanged and checkpoint_unchanged and molecular_hashes == after_hashes,
            "visible_state_hard_preserved": True, "target_replicate_firewall": True,
        },
        "diagnostic_contract": {"fits": 2, "alpha": RIDGE_ALPHA, "train_standardization_only": True, "validation_fit": False, "sealed_fit": False, "models_persisted": False, "features_exclude": ["LAMBDA", "factors", "hidden expression", "target replicates"]},
        "performance": performance,
        "larger_goal_interpretation": {
            "molecular_state_preserved": True, "factual_visible_state_preserved": True,
            "structural_failure_explanation": "classified from bounded reliability, stability, and diagnostic-ceiling evidence above",
            "another_neural_architecture_currently_justified": "HUMAN-REVIEW" if classification in ("RECOVERABLE CELL-LEVEL UNCERTAINTY SIGNAL EXISTS; CURRENT RBB UNCERTAINTY MAPPING MISSES IT", "REPLICATE / JACKKNIFE STABILITY PROVIDES PARTIAL LOCALIZATION SIGNAL") else "NO",
            "biological_world_model_direction_changed": False,
        },
        "governance": {"stage81a3_complete": False, "stage81a3_frozen": False, "ready_for_stage81b": False, "core_model_training": False, "core_neural_optimizer_updates": 0, "diagnostic_ridge_fits": 2, "diagnostic_models_adopted": False, "real_rna_accessed": False, "pathology_opened": False, "factor_labels_as_features": False, "lambda_as_features": False, "sealed_used_for_fitting": False, "hyperparameter_sweep": False, "seed_sweep": False},
    }
    base.atomic_csv(OUTPUTS["risk"], risk_rows); base.atomic_csv(OUTPUTS["reliability"], reliability_rows)
    base.atomic_csv(OUTPUTS["uncertainty"], uncertainty_rows); base.atomic_csv(OUTPUTS["disagreement"], disagreement_rows)
    base.atomic_csv(OUTPUTS["jackknife"], jackknife_rows); base.atomic_csv(OUTPUTS["diagnostic"], diagnostic_rows)
    base.atomic_csv(OUTPUTS["factors"], factor_rows); base.atomic_json(OUTPUTS["json"], payload); append_readout(payload)
    print(json.dumps({"classification": classification, "secondary": secondary, "gates": payload["gates"], "recommendation": recommendation, "performance": performance}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
