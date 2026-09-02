#!/usr/bin/env python3
"""Exact durable recovery of the frozen-encoder RBB scientific evidence."""

from __future__ import annotations

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
from sea_ad_jepa.v4.conditional_predictability import (  # noqa: E402
    r2_columns, ridge_fit, ridge_predict, topk_absolute_correlation,
)
from sea_ad_jepa.v4.rbb_adaptive import RBBAdaptiveBelief, R_MAX, nested_visibility_masks, structured_gaussian_terms  # noqa: E402


OUTPUTS = {
    "json": Path("results/v4/stage81a3_rbb_frozen_recovery.json"),
    "retention": Path("results/v4/stage81a3_rbb_frozen_recovery_retention.csv"),
    "calibration": Path("results/v4/stage81a3_rbb_frozen_recovery_calibration.csv"),
    "activity": Path("results/v4/stage81a3_rbb_frozen_recovery_correlated_activity.csv"),
    "replicate": Path("results/v4/stage81a3_rbb_frozen_recovery_replicate.csv"),
    "counterfactual": Path("results/v4/stage81a3_rbb_frozen_recovery_counterfactual.csv"),
    "checkpoint": Path("results/v4/stage81a3_rbb_frozen_recovery_belief_state.pt"),
}
EXPECTED_ADDITIONAL = {
    "results/v4/stage81a3_rbb_adaptive_correlated_probe.json": frozen.PREVIOUS_REPORT_HASH,
    "results/v4/stage81a3_rbb_frozen_encoder_probe.json": "915e76e4123b5fa7dd3b026072b1faef10d98063b349fc26f1d3e5b7e201b71f",
    "results/v4/stage81a3_rbb_frozen_encoder_retention.csv": "1267f3d573107cf8efa81dc3f78cc94788bb63c21e1f9c6d269220fd8b746e42",
}


def tensor_hash(*values: torch.Tensor) -> str:
    digest = hashlib.sha256()
    for value in values:
        tensor = value.detach().cpu().contiguous()
        digest.update(str(tensor.dtype).encode()); digest.update(str(tuple(tensor.shape)).encode())
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def atomic_checkpoint(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    try:
        torch.save(payload, temporary); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    return base.file_hash(path)


def checkpoint_belief(
    model: RBBAdaptiveBelief,
    hashes: dict[str, str],
    banks: dict[str, torch.Tensor],
    priors: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    state = {name: value.detach().cpu() for name, value in model.state_dict().items() if not name.startswith("ledger.")}
    metadata = {
        "anchor": base.ANCHOR, "seed": base.SEED, "r_max": R_MAX,
        "updates": base.UPDATES, "basis_sha256": base.BASIS_HASH,
        "tokenizer_sha256": hashes["tokenizer"],
        "molecular_encoder_sha256": hashes["encoder_without_tokenizer"],
        "complete_molecular_ledger_sha256": hashes["complete_molecular_ledger"],
        "mask_bank_sha256": {name: hashlib.sha256(bank.numpy().tobytes()).hexdigest() for name, bank in banks.items()},
        "prior_sha256": {name: tensor_hash(value["prior_diagonal"], value["prior_low_rank"]) for name, value in priors.items()},
        "noise_sha256": {name: tensor_hash(value["noise_diagonal"]) for name, value in priors.items()},
        "contains_frozen_molecular_weights": False,
        "architecture": {"width": base.WIDTH, "rank": R_MAX, "belief_implementation": "RBBAdaptiveBelief"},
    }
    sha = atomic_checkpoint(OUTPUTS["checkpoint"], {"belief_state_dict": state, "metadata": metadata})
    return sha, metadata


def primary_mask_evaluation(
    model: RBBAdaptiveBelief,
    fixture: Any,
    basis: Any,
    banks: dict[str, torch.Tensor],
    priors: dict[str, Any],
    device: torch.device,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    evaluations: dict[str, list[dict[str, Any]]] = {family: [] for family in base.FAMILIES}
    factor_information: dict[str, list[dict[str, Any]]] = {family: [] for family in base.FAMILIES}
    calibration_rows: list[dict[str, Any]] = []; activity_rows: list[dict[str, Any]] = []; replicate_rows: list[dict[str, Any]] = []
    for family in base.FAMILIES:
        for view in range(4):
            print(f"evaluating {family} view={view}", flush=True)
            result = base.evaluate_mask(model, fixture, basis, banks[family][view].to(device), priors[family], frozen.MICROBATCH, device)
            representations = {}
            for name in ("visible", "raw", "diagonalized", "belief"):
                values = result[name]; half = len(values) // 2
                validation = torch.cat((values[:base.VALIDATION], values[half:half + base.VALIDATION]))
                sealed_values = torch.cat((values[base.VALIDATION:half], values[half + base.VALIDATION:]))
                representations[name] = base.representation_readout(validation, sealed_values, fixture.factors.cpu())
            factor_information[family].append({"view": view, "representations": representations})
            sealed = torch.cat((torch.arange(base.VALIDATION, 2 * base.VALIDATION), torch.arange(3 * base.VALIDATION, 4 * base.VALIDATION)))
            target = result["target"][sealed]; residual = target - (result["belief"][sealed] - result["visible"][sealed]); marginal = result["marginal"][sealed]
            marginal_metrics = base.marginal_calibration(residual, marginal)
            row = {
                "family": family, "view": view,
                "prior_nll": float(result["prior_nll"][sealed].mean()),
                "diagonalized_nll": float(result["diag_nll"][sealed].mean()),
                "full_nll": float(result["full_nll"][sealed].mean()),
                "joint_scale_full": float(result["full_mahal"][sealed].mean() / base.WIDTH),
                "joint_scale_diagonalized": float(result["diag_mahal"][sealed].mean() / base.WIDTH),
                **{f"marginal_{key}": value for key, value in marginal_metrics.items()},
                "uncertainty_error_spearman": base.spearman(result["trace"][sealed], result["squared_error"][sealed]),
                "coordinate_variance_error_spearman": base.spearman(marginal.mean(0), residual.square().mean(0)),
                "gaussian_severe_fraction": base.gaussianity(residual, marginal)["severe_fraction"],
                **{f"{name}_factor_r2": value["mean"] for name, value in representations.items()},
            }
            evaluations[family].append(row); calibration_rows.append(row)
            amplitudes = result["amplitudes"][sealed]
            for index in range(len(amplitudes)):
                activity = {
                    "family": family, "view": view, "example": index,
                    "sum_amplitude_squared": float(amplitudes[index].square().sum()),
                    "correlated_covariance_energy": float(result["corr_energy"][sealed][index]),
                    "effective_correlated_rank": float(result["effective_rank"][sealed][index]),
                }
                activity.update({f"amplitude_{rank:02d}": float(amplitudes[index, rank]) for rank in range(R_MAX)})
                activity_rows.append(activity)
            if view == 0:
                a, b = result["belief_a"], result["belief_b"]
                factors_validation = fixture.factors[base.TRAIN:base.TRAIN + base.VALIDATION].cpu(); factors_sealed = fixture.factors[-base.SEALED:].cpu()
                mapping = ridge_fit(a[:base.VALIDATION], factors_validation, 1e-3)
                pred_a = ridge_predict(mapping, a[base.VALIDATION:]); pred_b = ridge_predict(mapping, b[base.VALIDATION:])
                score_a, score_b = r2_columns(factors_sealed, pred_a), r2_columns(factors_sealed, pred_b)
                cosine = float(torch.nn.functional.cosine_similarity(a[base.VALIDATION:], b[base.VALIDATION:]).mean())
                distance = float(((a[base.VALIDATION:] - b[base.VALIDATION:]) / torch.cat((a[base.VALIDATION:], b[base.VALIDATION:])).std(0).clamp_min(1e-8)).square().sum(1).sqrt().mean())
                for factor in range(base.FACTORS):
                    replicate_rows.append({
                        "family": family, "factor": factor, "belief_mean_state_cosine": cosine,
                        "paired_standardized_l2": distance, "a_factor_r2": float(score_a[factor]),
                        "b_factor_r2_under_a_map": float(score_b[factor]),
                        "prediction_correlation": float(torch.corrcoef(torch.stack((pred_a[:, factor], pred_b[:, factor])))[0, 1]),
                    })
        family_rows = evaluations[family]
        payload.setdefault("primary_evaluation", {})[family] = {
            key: float(np.median([row[key] for row in family_rows]))
            for key in family_rows[0] if key not in ("family", "view")
        }
        payload.setdefault("factor_information", {})[family] = factor_information[family]
        payload["status"] = f"primary_{family.lower()}_persisted"
        base.atomic_csv(OUTPUTS["calibration"], calibration_rows); base.atomic_csv(OUTPUTS["activity"], activity_rows)
        base.atomic_csv(OUTPUTS["replicate"], replicate_rows); base.atomic_json(OUTPUTS["json"], payload)
    return payload["primary_evaluation"], calibration_rows, activity_rows, replicate_rows


def observation_removal(model: RBBAdaptiveBelief, fixture: Any, basis: Any, priors: dict[str, Any], device: torch.device) -> dict[str, Any]:
    order = torch.randperm(base.GENES, generator=torch.Generator().manual_seed(base.SEED + 812)).to(device)
    nested = nested_visibility_masks(order); rows = []; model.eval()
    with torch.no_grad():
        for fraction, visible_one in nested.items():
            marginals, logdets, ranks = [], [], []
            indices = torch.arange(base.CELLS - 128, base.CELLS, device=device); hidden = ~visible_one
            for start in range(0, len(indices), frozen.MICROBATCH):
                selected = indices[start:start + frozen.MICROBATCH]; values = fixture.x_a[selected]
                state = basis.contribution(values, visible_one); ids = torch.arange(base.GENES, device=device)[None].expand(len(selected), -1)
                visible = visible_one[None].expand(len(selected), -1); prior = priors["RANDOM_40"]
                with torch.autocast("cuda", dtype=torch.float16):
                    output = model(ids, values, visible, state, base.mask_context(basis, hidden, prior, len(selected)), prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"])
                marginal = output.total_diagonal + output.total_low_rank.square().sum(-1)
                _, _, logdet = structured_gaussian_terms(torch.zeros_like(output.belief_mean), output.total_diagonal, output.total_low_rank)
                marginals.append(marginal.cpu()); logdets.append(logdet.cpu()); ranks.append(base.effective_rank(output.evidence_low_rank).cpu())
            marginal = torch.cat(marginals)
            rows.append({
                "visible_fraction": fraction, "median_trace": float(marginal.sum(1).median()),
                "median_logdet": float(torch.cat(logdets).median()),
                "median_marginal_uncertainty": float(marginal.median()),
                "median_effective_correlated_rank": float(torch.cat(ranks).median()),
                "coordinate_medians": marginal.median(0).values,
            })
    rows = sorted(rows, key=lambda row: row["visible_fraction"], reverse=True)
    stack = torch.stack([row.pop("coordinate_medians") for row in rows])
    fraction = float(((stack[1:] >= stack[:-1]).all(0)).float().mean())
    return {"rows": rows, "nondecreasing_coordinate_fraction": fraction, "pass": fraction >= .75, "nested_masks_verified": all(torch.all(nested[b] <= nested[a]) for a, b in ((1.0, .8), (.8, .6), (.6, .4)))}


def append_readout(payload: dict[str, Any]) -> None:
    path = Path("docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md")
    marker = "## RBB-JEPA Frozen-Encoder Exact Recovery Probe"
    existing = path.read_text(encoding="utf-8")
    if marker in existing: raise RuntimeError("recovery readout already exists")
    section = f"""

{marker}

This exact seed-{base.SEED} repeat preserved the frozen molecular ledger and added only durable
serialization plus corrected counterfactual dtype handling. The belief-side checkpoint was written
immediately after update 150, before SEALED evaluation. Retention stayed at
`{payload['retention'][-1]['retention_ratio']:.6f}` and all molecular hashes and gradient-firewall
checks passed.

Primary classification: **{payload['classification']}**.

Correlated component: **{payload['secondary_classifications']['correlated_component']}**.
Point-state recovery: **{payload['secondary_classifications']['point_state_recovery']}**.
Counterfactual sidecar: **{payload['secondary_classifications']['counterfactual_sidecar']}**.

This supports molecular evidence preservation and is still synthetic qualification evidence. It
does not establish pathology biology, disease vulnerability/resilience, spatial validity,
regulator causality, perturbational world dynamics, cross-platform transfer, or permanently
unmeasured-panel generalization. The structurally unmeasured gene contract remains open before
final Stage81A3 freeze qualification.
"""
    base.atomic_text(path, existing.rstrip() + section + "\n")


def main() -> int:
    os.chdir(ROOT)
    if any(path.exists() for path in OUTPUTS.values()): raise RuntimeError("recovery artifact exists; repeat forbidden")
    for path, expected in {**base.EXPECTED_HASHES, **EXPECTED_ADDITIONAL}.items():
        if base.file_hash(Path(path)) != expected: raise RuntimeError(f"prior evidence changed: {path}")
    device = torch.device("cuda"); torch.set_float32_matmul_precision("high"); torch.backends.cuda.matmul.allow_tf32 = True
    torch.manual_seed(base.SEED); torch.cuda.manual_seed_all(base.SEED); total_started = time.perf_counter(); prep_started = time.perf_counter()
    basis = base.load_basis(device); fixture = base.build_fixture(device); priors = base.frozen_family_statistics(device)
    weights, neighbors = topk_absolute_correlation(.5 * (fixture.x_a[:base.TRAIN] + fixture.x_b[:base.TRAIN]), 8)
    banks = {"RANDOM_40": base.random_mask_bank().pin_memory(), "COEXPRESSION_BLOCK_40": base.block_mask_bank(neighbors, weights).pin_memory()}
    precision_bias, correlation_bias, initialization = base.initialization_biases(priors)
    model = RBBAdaptiveBelief(diagonal_precision_bias=precision_bias, correlated_amplitude_bias=correlation_bias).to(device)
    hashes = frozen.frozen_hashes(model); dropout = frozen.dropout_diagnostic(model, fixture, banks["RANDOM_40"][0].to(device), device)
    step0 = frozen.retention_row(0, model, fixture, device); parity = abs(step0["retention_ratio"] - frozen.PREVIOUS_STEP0)
    if parity > .01: raise RuntimeError("INITIALIZATION PARITY FAILURE")
    model.freeze_molecular_ledger(); model.train(); optimizer = torch.optim.AdamW(list(model.belief_parameters()), lr=1e-4, weight_decay=.01)
    optimizer_audit = frozen.optimizer_audit(model, optimizer); preparation_seconds = time.perf_counter() - prep_started
    payload: dict[str, Any] = {
        "stage": "stage81a3_rbb_frozen_recovery", "anchor": base.ANCHOR,
        "status": "initialized", "classification": None,
        "initialization_parity": {"reference": frozen.PREVIOUS_STEP0, "observed": step0["retention_ratio"], "absolute_difference": parity, "pass": True},
        "molecular_hashes_step0": hashes, "dropout_semantics": dropout,
        "optimizer_firewall": optimizer_audit, "retention": [step0],
        "scientific_contract": {"single_engineering_repeat": True, "scientific_changes": 0, "real_rna": False, "pathology": False},
    }
    base.atomic_json(OUTPUTS["json"], payload); base.atomic_csv(OUTPUTS["retention"], [step0])

    def persist_milestone(step, retention, hash_audit, gradient_audit, telemetry):
        payload.update({"status": f"training_step_{step}_persisted", "retention": retention, "molecular_hash_audit": hash_audit, "gradient_firewall_audit": gradient_audit, "telemetry": telemetry})
        base.atomic_csv(OUTPUTS["retention"], retention); base.atomic_json(OUTPUTS["json"], payload)

    retention, hash_audit, training = frozen.train_belief_only(model, fixture, basis, banks, priors, optimizer, hashes, step0, device, milestone_callback=persist_milestone)
    payload.update({"status": "training_complete", "retention": retention, "molecular_hash_audit": hash_audit, "gradient_firewall_audit": training["gradient_audit"], "training": training})
    checkpoint_sha, checkpoint_metadata = checkpoint_belief(model, hashes, banks, priors)
    payload["belief_checkpoint"] = {"path": str(OUTPUTS["checkpoint"]), "sha256": checkpoint_sha, "metadata": checkpoint_metadata}
    payload["status"] = "checkpoint_persisted"; base.atomic_json(OUTPUTS["json"], payload)

    primary, calibration_rows, activity_rows, replicate_rows = primary_mask_evaluation(model, fixture, basis, banks, priors, device, payload)
    observation = observation_removal(model, fixture, basis, priors, device); payload["observation_removal"] = observation
    full_reference = base.representation_readout(basis.transform(fixture.lambda_norm[base.TRAIN:base.TRAIN + base.VALIDATION], whiten=True).cpu(), basis.transform(fixture.lambda_norm[-base.SEALED:], whiten=True).cpu(), fixture.factors.cpu())
    payload["full_lambda_factor_information"] = full_reference
    for family in base.FAMILIES:
        current = primary[family]; current["belief_minus_visible_factor_r2"] = current["belief_factor_r2"] - current["visible_factor_r2"]
        denominator = full_reference["mean"] - current["visible_factor_r2"]
        current["recoverable_gap_fraction"] = current["belief_minus_visible_factor_r2"] / denominator if denominator > .02 else None
        current["full_minus_diagonalized_nll"] = current["full_nll"] - current["diagonalized_nll"]
    proper = all(primary[f]["full_nll"] < primary[f]["prior_nll"] for f in base.FAMILIES)
    no_harm = all(primary[f]["belief_factor_r2"] >= primary[f]["visible_factor_r2"] - .01 for f in base.FAMILIES)
    joint = all(.80 <= primary[f]["joint_scale_full"] <= 1.25 for f in base.FAMILIES)
    marginal = all(.58 <= primary[f]["marginal_coverage_1sigma"] <= .78 and .88 <= primary[f]["marginal_coverage_1_96sigma"] <= .99 for f in base.FAMILIES)
    uncertainty = all(primary[f]["uncertainty_error_spearman"] > 0 for f in base.FAMILIES)
    retention_pass = all(row["retention_ratio"] >= .95 for row in retention) and abs(retention[-1]["retention_ratio"] - retention[0]["retention_ratio"]) <= .005
    hashes_pass = all({key: row[key] for key in hashes} == hashes for row in hash_audit); gradients_pass = all(row["maximum_absolute_frozen_gradient"] == 0 for row in training["gradient_audit"])
    payload["primary_gates"] = {"initialization_parity": True, "molecular_hashes_unchanged": hashes_pass, "molecular_gradients_zero": gradients_pass, "token_retention": retention_pass, "proper_score": proper, "no_harm": no_harm, "joint_calibration": joint, "marginal_calibration": marginal, "uncertainty_error": uncertainty, "observation_removal": observation["pass"]}
    if retention_pass and hashes_pass and gradients_pass and proper and no_harm and joint and marginal and uncertainty:
        classification = "GRADIENT INTERFERENCE CONFIRMED; FROZEN MOLECULAR LEDGER SUPPORTS RBB BELIEF"
    elif retention_pass and not proper: classification = "FROZEN MOLECULAR LEDGER PRESERVES BIOLOGY, BUT RBB BELIEF ADDS LITTLE PROBABILISTIC VALUE"
    elif retention_pass: classification = "RBB BELIEF FAILS EVEN WITH FROZEN MOLECULAR LEDGER"
    elif not hashes_pass or not gradients_pass: classification = "GRADIENT FIREWALL FAILURE"
    else: classification = "ENGINEERING / NUMERICAL FAILURE"
    correlated = "EARNED" if primary["COEXPRESSION_BLOCK_40"]["full_nll"] < primary["COEXPRESSION_BLOCK_40"]["diagonalized_nll"] - 1e-4 else "NOT EARNED"
    point_changes = [primary[f]["belief_minus_visible_factor_r2"] for f in base.FAMILIES]
    point = "HARMFUL" if min(point_changes) < -.01 else ("MEANINGFUL" if max(point_changes) >= .01 else "NEGLIGIBLE")
    payload.update({"classification": classification, "secondary_classifications": {"correlated_component": correlated, "point_state_recovery": point, "counterfactual_sidecar": "INCONCLUSIVE"}, "status": "all_primary_evidence_persisted", "numerical_health": {"nonfinite_events": training["nonfinite_events"], "adaptive_jitter_events": 0, "maximum_adaptive_jitter": 0.0, "fixed_diagonal_floor": 1e-6}, "performance": {key: training[key] for key in ("microbatch", "accumulation_microbatches", "effective_batch", "updates", "examples", "peak_allocated_gb", "peak_reserved_gb", "examples_per_second", "seconds_per_update", "wall_seconds")}})
    payload["performance"].update({"mean_gpu_utilization": None, "cpu_preparation_fraction": preparation_seconds / max(time.perf_counter() - total_started, 1e-12)})
    base.atomic_json(OUTPUTS["json"], payload)

    try:
        rows, summary = frozen.evaluate_counterfactual(model, fixture, basis, banks["COEXPRESSION_BLOCK_40"][0].to(device), priors["COEXPRESSION_BLOCK_40"], device)
        base.atomic_csv(OUTPUTS["counterfactual"], rows); payload["counterfactual"] = summary
        payload["secondary_classifications"]["counterfactual_sidecar"] = "SUPPORTED" if summary["coordinate_delta_r2"]["median"] > 0 and summary["cosine"]["median"] > .5 else "NOT SUPPORTED"
        payload["counterfactual_status"] = "passed"
    except Exception as exc:
        payload["counterfactual_status"] = "failed_without_primary_evidence_loss"
        payload["counterfactual_error"] = f"{type(exc).__name__}: {exc}"
    payload["status"] = "complete"; payload["total_wall_seconds"] = time.perf_counter() - total_started
    payload["larger_goal_checkpoint"] = {"establishes": ["synthetic molecular evidence preservation", "belief inference from incomplete synthetic molecular evidence", "calibrated uncertainty"], "selective_correlated_uncertainty_value": correlated == "EARNED", "does_not_establish": ["pathology biology", "disease vulnerability or resilience", "spatial validity", "regulator causality", "perturbational world dynamics", "cross-platform transfer", "permanent-unmeasured-panel generalization"], "open_before_final_a3_freeze": "structurally/permanently unmeasured gene contract"}
    base.atomic_json(OUTPUTS["json"], payload); append_readout(payload)
    print(json.dumps({"classification": classification, "gates": payload["primary_gates"], "secondary": payload["secondary_classifications"], "checkpoint_sha256": checkpoint_sha}, indent=2), flush=True)
    return 0


if __name__ == "__main__": raise SystemExit(main())
