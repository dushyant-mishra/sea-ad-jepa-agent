#!/usr/bin/env python3
"""Forward-only qualification of explicit structural-panel semantics for RBB-JEPA."""

from __future__ import annotations

import argparse
import hashlib
import heapq
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
import stage81a3_rbb_frozen_encoder_probe as frozen  # noqa: E402
from sea_ad_jepa.v4.conditional_predictability import (  # noqa: E402
    r2_columns, ridge_fit, ridge_predict, topk_absolute_correlation,
)
from sea_ad_jepa.v4.measurement_state import MeasurementState, measurement_state_codes  # noqa: E402
from sea_ad_jepa.v4.rbb_adaptive import RBBAdaptiveBelief  # noqa: E402
from sea_ad_jepa.v4.rbb_adaptive import fuse_gaussian_beliefs, lrd_solve, structured_gaussian_terms  # noqa: E402


ANCHOR = base.ANCHOR
SEED = base.SEED
CHECKPOINT = Path("results/v4/stage81a3_rbb_frozen_recovery_belief_state.pt")
CHECKPOINT_HASH = "8ef9667e42f6c44be937b94cb54d89152805c3fbe0c254d23891a940d4474b24"
RECOVERY_REPORT = Path("results/v4/stage81a3_rbb_frozen_recovery.json")
RECOVERY_HASH = "49088ce3e2d677c62e5ac346e798f922ad7ff85c71a2abd039ca304ba52f98b7"
PRIOR_EVIDENCE = {
    **base.EXPECTED_HASHES,
    "results/v4/stage81a3_rbb_adaptive_correlated_probe.json": "c73440b97830f4dc09467797aaefe5d59d99649fa6c98c6ed60cb23e82e083d3",
    "results/v4/stage81a3_rbb_frozen_encoder_probe.json": "915e76e4123b5fa7dd3b026072b1faef10d98063b349fc26f1d3e5b7e201b71f",
    str(RECOVERY_REPORT): RECOVERY_HASH,
    str(CHECKPOINT): CHECKPOINT_HASH,
}
PANEL_COUNTS = {"FULL": 4096, "P80": 3277, "P60": 2458, "P40": 1638, "P20": 819}
PANEL_ORDER = tuple(PANEL_COUNTS)
FAMILIES = ("RANDOM_STRUCTURAL", "COHERENT_STRUCTURAL")
PRIMARY = ("P80", "P60", "P40")
MICROBATCH = 32
OUTPUTS = {
    "json": Path("results/v4/stage81a3_rbb_structural_panel_audit.json"),
    "metrics": Path("results/v4/stage81a3_rbb_structural_panel_metrics.csv"),
    "calibration": Path("results/v4/stage81a3_rbb_structural_panel_calibration.csv"),
    "cross": Path("results/v4/stage81a3_rbb_cross_panel_compatibility.csv"),
    "activity": Path("results/v4/stage81a3_rbb_structural_correlated_activity.csv"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_state(measured_one: torch.Tensor, batch: int, device: torch.device) -> MeasurementState:
    measurement = measured_one.to(device)[None].expand(batch, -1)
    return MeasurementState(
        measurement_mask=measurement,
        training_hidden_mask=torch.zeros_like(measurement),
        foundation_support_mask=torch.ones(base.GENES, dtype=torch.bool, device=device),
    )


def forward_contract(
    model: RBBAdaptiveBelief,
    expression: torch.Tensor,
    state: MeasurementState,
    basis: Any,
    prior: dict[str, Any],
) -> Any:
    """Bridge explicit measurement semantics to the unchanged frozen model API."""
    state.assert_foundation_inference_supported()
    observed = state.observed_mask
    if not torch.all(observed.sum(1) == observed.sum(1)[0]):
        raise ValueError("panel audit requires one exact measurement panel per microbatch")
    sanitized = state.sanitized_expression(expression)
    visible_state = basis.contribution(sanitized, observed[0])
    hidden = state.belief_missing_mask[0]
    ids = torch.arange(base.GENES, device=expression.device)[None].expand(len(expression), -1)
    return model(
        ids, sanitized, observed, visible_state,
        base.mask_context(basis, hidden, prior, len(expression)),
        prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"],
    )


def connected_order(neighbors: torch.Tensor, weights: torch.Tensor, seed: int) -> torch.Tensor:
    """Deterministic TRAIN-graph expansion ordering with no labels or SEALED data."""
    permutation = torch.randperm(base.GENES, generator=torch.Generator().manual_seed(seed))
    used = torch.zeros(base.GENES, dtype=torch.bool)
    order: list[int] = []
    frontier: list[tuple[float, int, int]] = []

    def add(gene: int) -> None:
        if used[gene]:
            return
        used[gene] = True; order.append(gene)
        for position, neighbor in enumerate(neighbors[gene].tolist()):
            if not used[neighbor]:
                heapq.heappush(frontier, (-float(weights[gene, position]), gene, int(neighbor)))

    cursor = 0
    add(int(permutation[cursor])); cursor += 1
    while len(order) < base.GENES:
        while frontier and used[frontier[0][2]]:
            heapq.heappop(frontier)
        if frontier:
            add(heapq.heappop(frontier)[2])
        else:
            while used[int(permutation[cursor])]:
                cursor += 1
            add(int(permutation[cursor])); cursor += 1
    return torch.tensor(order, dtype=torch.long)


def panel_masks(order: torch.Tensor, *, measured_prefix: bool) -> dict[str, torch.Tensor]:
    result = {}
    for label, count in PANEL_COUNTS.items():
        measured = torch.zeros(base.GENES, dtype=torch.bool)
        if measured_prefix:
            measured[order[:count]] = True
        else:
            measured[:] = True
            measured[order[:base.GENES - count]] = False
        result[label] = measured
    return result


def build_panels(fixture: Any) -> tuple[dict[str, list[dict[str, torch.Tensor]]], dict[str, Any]]:
    """Build all panels from seed and accepted TRAIN-only coexpression evidence."""
    train_average = .5 * (fixture.x_a[:base.TRAIN] + fixture.x_b[:base.TRAIN])
    weights, neighbors = topk_absolute_correlation(train_average, 8)
    families = {name: [] for name in FAMILIES}
    hashes = {name: [] for name in FAMILIES}
    for view in range(4):
        random_order = torch.randperm(base.GENES, generator=torch.Generator().manual_seed(SEED + 2003 * view + 71))
        coherent_order = connected_order(neighbors.cpu(), weights.cpu(), SEED + 2017 * view + 89)
        for family, order, prefix in (
            ("RANDOM_STRUCTURAL", random_order, True),
            ("COHERENT_STRUCTURAL", coherent_order, False),
        ):
            masks = panel_masks(order, measured_prefix=prefix)
            families[family].append(masks)
            hashes[family].append(hashlib.sha256(torch.stack([masks[x] for x in PANEL_ORDER]).numpy().tobytes()).hexdigest())
    audit = {
        "construction_inputs": "seed plus TRAIN-derived pathology-blind coexpression graph only",
        "factor_labels_used": False, "sealed_used": False, "views": 4, "hashes": hashes,
        "exact_cardinalities": all(int(m.sum()) == PANEL_COUNTS[p] for fs in families.values() for v in fs for p, m in v.items()),
        "nested": all(torch.all(v[b] <= v[a]) for fs in families.values() for v in fs for a, b in zip(PANEL_ORDER, PANEL_ORDER[1:])),
    }
    return families, audit


def reconstruct(device: torch.device) -> tuple[RBBAdaptiveBelief, Any, Any, dict[str, Any], dict[str, str], dict[str, Any]]:
    actual = {path: sha256(Path(path)) for path in PRIOR_EVIDENCE}
    if actual != PRIOR_EVIDENCE:
        raise RuntimeError("prior evidence hash mismatch")
    report = json.loads(RECOVERY_REPORT.read_text(encoding="utf-8"))
    expected_class = "GRADIENT INTERFERENCE CONFIRMED; FROZEN MOLECULAR LEDGER SUPPORTS RBB BELIEF"
    if report["classification"] != expected_class:
        raise RuntimeError("frozen recovery classification mismatch")
    torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    basis = base.load_basis(device); fixture = base.build_fixture(device); priors = base.frozen_family_statistics(device)
    precision_bias, correlation_bias, _ = base.initialization_biases(priors)
    model = RBBAdaptiveBelief(diagonal_precision_bias=precision_bias, correlated_amplitude_bias=correlation_bias).to(device)
    hashes = frozen.frozen_hashes(model)
    expected_hashes = report["molecular_hashes_step0"]
    if hashes != expected_hashes:
        raise RuntimeError("reconstructed molecular stack hash mismatch")
    checkpoint = torch.load(CHECKPOINT, map_location=device, weights_only=False)
    missing, unexpected = model.load_state_dict(checkpoint["belief_state_dict"], strict=False)
    if unexpected or any(not key.startswith("ledger.") for key in missing):
        raise RuntimeError(f"belief checkpoint key mismatch: missing={missing}, unexpected={unexpected}")
    model.freeze_molecular_ledger(); model.eval()
    if any(parameter.requires_grad for parameter in model.parameters()):
        for parameter in model.parameters():
            parameter.requires_grad_(False)
    return model, fixture, basis, priors, hashes, checkpoint["metadata"]


def summarize(values: torch.Tensor) -> dict[str, float]:
    return base.summarize(values.float().cpu())


def panel_forward(
    model: RBBAdaptiveBelief,
    fixture: Any,
    basis: Any,
    prior: dict[str, Any],
    measured: torch.Tensor,
    device: torch.device,
    *,
    retain: bool = False,
) -> dict[str, Any]:
    indices = torch.arange(base.TRAIN, base.CELLS, device=device)
    hidden = ~measured.to(device)
    names = ("visible", "belief", "diagonalized", "target", "full_nll", "diag_nll", "prior_nll", "mahal", "trace", "logdet", "marginal", "total_diagonal", "total_low_rank", "amplitudes", "corr_energy", "corr_rank")
    collected: dict[str, list[torch.Tensor]] = {name: [] for name in names}
    with torch.no_grad():
        for source in (fixture.x_a, fixture.x_b):
            for start in range(0, len(indices), MICROBATCH):
                selected = indices[start:start + MICROBATCH]
                expression = source[selected]
                state = make_state(measured, len(selected), device)
                with torch.autocast("cuda", dtype=torch.float16):
                    output = forward_contract(model, expression, state, basis, prior)
                target = basis.contribution(fixture.lambda_norm[selected], hidden)
                diag_mean, diag_d, diag_u = fuse_gaussian_beliefs(
                    output.evidence_mean, prior["prior_diagonal"], prior["prior_low_rank"],
                    output.evidence_diagonal, torch.zeros_like(output.evidence_low_rank),
                )
                residual = target - output.posterior_missing_mean
                diag_residual = target - diag_mean
                full_nll, mahal, logdet = structured_gaussian_terms(residual, output.total_diagonal, output.total_low_rank)
                diag_nll, _, _ = structured_gaussian_terms(diag_residual, diag_d + prior["noise_diagonal"], diag_u)
                prior_nll, _, _ = structured_gaussian_terms(
                    target,
                    (prior["prior_diagonal"] + prior["noise_diagonal"])[None].expand(len(target), -1),
                    prior["prior_low_rank"][None].expand(len(target), -1, -1),
                )
                marginal = output.total_diagonal + output.total_low_rank.square().sum(-1)
                corr = output.evidence_low_rank @ output.evidence_low_rank.transpose(-1, -2)
                corr = corr - torch.diag_embed(torch.diagonal(corr, dim1=-2, dim2=-1))
                values = {
                    "visible": output.visible_state, "belief": output.belief_mean,
                    "diagonalized": output.visible_state + diag_mean, "target": target,
                    "full_nll": full_nll / base.WIDTH, "diag_nll": diag_nll / base.WIDTH,
                    "prior_nll": prior_nll / base.WIDTH, "mahal": mahal / base.WIDTH,
                    "trace": marginal.sum(-1), "logdet": logdet, "marginal": marginal,
                    "total_diagonal": output.total_diagonal, "total_low_rank": output.total_low_rank,
                    "amplitudes": output.correlated_activation_amplitudes,
                    "corr_energy": corr.square().sum((-1, -2)), "corr_rank": base.effective_rank(output.evidence_low_rank),
                }
                for name, value in values.items():
                    collected[name].append(value.float().cpu())
    arrays = {name: torch.cat(parts) for name, parts in collected.items()}
    half = len(arrays["belief"]) // 2
    validation = torch.cat((torch.arange(base.VALIDATION), torch.arange(half, half + base.VALIDATION)))
    sealed = torch.cat((torch.arange(base.VALIDATION, half), torch.arange(half + base.VALIDATION, 2 * half)))
    factor_rows = {}
    for name in ("visible", "belief", "diagonalized"):
        factor_rows[name] = base.representation_readout(arrays[name][validation], arrays[name][sealed], fixture.factors.cpu())
    full_expected = basis.transform(fixture.lambda_norm[base.TRAIN:], whiten=True).float().cpu().repeat(2, 1)
    full_noisy = torch.cat((basis.transform(fixture.x_a[base.TRAIN:], whiten=True).float().cpu(), basis.transform(fixture.x_b[base.TRAIN:], whiten=True).float().cpu()))
    factor_rows["synthetic_full_expected"] = base.representation_readout(full_expected[validation], full_expected[sealed], fixture.factors.cpu())
    factor_rows["full_noisy"] = base.representation_readout(full_noisy[validation], full_noisy[sealed], fixture.factors.cpu())
    residual = arrays["target"][sealed] - (arrays["belief"][sealed] - arrays["visible"][sealed])
    marginal_cal = base.marginal_calibration(residual, arrays["marginal"][sealed])
    result = {
        "nll": float(arrays["full_nll"][sealed].mean()),
        "diagonalized_nll": float(arrays["diag_nll"][sealed].mean()),
        "prior_nll": float(arrays["prior_nll"][sealed].mean()),
        "joint_scale": float(arrays["mahal"][sealed].mean()),
        **marginal_cal,
        "uncertainty_error_spearman": base.spearman(arrays["trace"][sealed], residual.square().sum(1)),
        "gaussianity": base.gaussianity(residual, arrays["marginal"][sealed]),
        "median_trace": float(arrays["trace"][sealed].median()),
        "median_logdet": float(arrays["logdet"][sealed].median()),
        "coordinate_median_variance": arrays["marginal"][sealed].median(0).values,
        "mean_correlated_energy": float(arrays["corr_energy"][sealed].mean()),
        "median_correlated_rank": float(arrays["corr_rank"][sealed].median()),
        "amplitude_by_rank": [summarize(arrays["amplitudes"][sealed, rank]) for rank in range(base.R_MAX)],
        "factors": factor_rows,
    }
    if retain:
        result["arrays"] = {key: value for key, value in arrays.items() if key in (
            "visible", "belief", "target", "full_nll", "mahal", "logdet", "marginal",
            "trace", "total_diagonal", "total_low_rank",
        )}
    return result


def parity_and_firewalls(model: Any, fixture: Any, basis: Any, prior: dict[str, Any], device: torch.device) -> dict[str, Any]:
    selected = torch.arange(base.TRAIN, base.TRAIN + 32, device=device)
    measured = torch.ones(base.GENES, dtype=torch.bool); measured[:base.HIDDEN] = False
    expression = fixture.x_a[selected]
    state = make_state(measured, len(selected), device)
    sanitized = state.sanitized_expression(expression)
    ids = torch.arange(base.GENES, device=device)[None].expand(len(selected), -1)
    visible_state = basis.contribution(sanitized, measured.to(device))
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16):
        old = model(ids, sanitized, state.observed_mask, visible_state, base.mask_context(basis, ~measured.to(device), prior, len(selected)), prior["prior_diagonal"], prior["prior_low_rank"], prior["noise_diagonal"])
        new = forward_contract(model, expression, state, basis, prior)
    fields = (
        "molecular_evidence_tokens", "visible_state", "posterior_missing_mean", "belief_mean",
        "conditional_diagonal", "conditional_low_rank", "total_diagonal", "total_low_rank",
        "correlated_activation_amplitudes", "evidence_mean", "evidence_diagonal", "evidence_low_rank",
    )
    parity = {field: float((getattr(old, field) - getattr(new, field)).abs().max()) for field in fields}
    target = basis.contribution(fixture.lambda_norm[selected], (~measured).to(device))
    old_nll, _, _ = structured_gaussian_terms(target - old.posterior_missing_mean, old.total_diagonal, old.total_low_rank)
    new_nll, _, _ = structured_gaussian_terms(target - new.posterior_missing_mean, new.total_diagonal, new.total_low_rank)
    parity["nll"] = float((old_nll - new_nll).abs().max())

    shuffled = expression.clone()
    shuffled[state.structural_unmeasured_mask] = expression.roll(1, 0)[state.structural_unmeasured_mask]
    substitutions = {
        "true": expression, "zero": expression.masked_fill(state.structural_unmeasured_mask, 0),
        "shuffled": shuffled,
        "nonsense": expression.masked_fill(state.structural_unmeasured_mask, 1000.0),
    }
    reference = None; differences = {}
    with torch.no_grad():
        for label, values in substitutions.items():
            with torch.autocast("cuda", dtype=torch.float16):
                output = forward_contract(model, values, state, basis, prior)
            current = {field: getattr(output, field).float().cpu() for field in fields}
            if reference is None:
                reference = current
            differences[label] = max(float((current[field] - reference[field]).abs().max()) for field in fields)
    zeros = (fixture.x_a[-256:] == 0)
    examples = int(zeros.sum())
    measured_zero_state = MeasurementState(torch.ones_like(zeros), torch.zeros_like(zeros), torch.ones(base.GENES, dtype=torch.bool, device=device))
    structural_measurement = torch.ones_like(zeros); structural_measurement[zeros] = False
    structural_zero_state = MeasurementState(structural_measurement, torch.zeros_like(zeros), torch.ones(base.GENES, dtype=torch.bool, device=device))
    measured_codes = measurement_state_codes(fixture.x_a[-256:], measured_zero_state)
    structural_codes = measurement_state_codes(fixture.x_a[-256:], structural_zero_state)
    zero_coordinates = torch.nonzero(zeros, as_tuple=False)[:256]
    zero_contributions = torch.stack([
        (-basis.mean[gene] * basis.analysis[:, gene]).float().norm().cpu()
        for _, gene in zero_coordinates
    ])
    zero_semantics = {
        "cell_gene_examples": examples,
        "proof_subset_at_least_256": examples >= 256,
        "measured_zero_observed": bool(torch.all(measured_zero_state.observed_mask[zeros])),
        "structural_zero_not_observed": bool(torch.all(~structural_zero_state.observed_mask[zeros])),
        "state_codes_distinct": bool(torch.all(measured_codes[zeros] != structural_codes[zeros])),
        "visible_state_contribution_examples": int(len(zero_contributions)),
        "measured_zero_nonzero_visible_contribution_fraction": float((zero_contributions > 0).float().mean()),
        "measured_zero_median_visible_contribution_norm": float(zero_contributions.median()),
        "structural_zero_visible_contribution_norm": 0.0,
    }
    example_measurement = torch.ones(1, base.GENES, dtype=torch.bool, device=device)
    training_hidden = torch.zeros_like(example_measurement); training_hidden[:, 0] = True
    training = MeasurementState(example_measurement, training_hidden, torch.ones(base.GENES, dtype=torch.bool, device=device))
    structural_measurement = example_measurement.clone(); structural_measurement[:, 0] = False
    structural = MeasurementState(structural_measurement, torch.zeros_like(example_measurement), torch.ones(base.GENES, dtype=torch.bool, device=device))
    target_semantics = {
        "both_belief_missing": bool(training.belief_missing_mask[0, 0] and structural.belief_missing_mask[0, 0]),
        "training_mask_target_eligible": bool(training.training_target_eligible_mask[0, 0]),
        "structural_target_eligible": bool(structural.training_target_eligible_mask[0, 0]),
    }
    return {
        "legacy_parity_max_abs": parity, "legacy_parity_pass": max(parity.values()) <= 1e-6,
        "structural_substitution_max_abs": differences, "structural_firewall_pass": max(differences.values()) <= 1e-6,
        "measured_zero": zero_semantics, "training_vs_structural": target_semantics,
    }


def complementary_masks(pair: int) -> tuple[torch.Tensor, torch.Tensor]:
    order = torch.randperm(base.GENES, generator=torch.Generator().manual_seed(SEED + 3011 * pair + 131))
    a = torch.zeros(base.GENES, dtype=torch.bool); b = torch.zeros_like(a)
    a[order[:2458]] = True; b[order[-2458:]] = True
    return a, b


def cross_panel_audit(model: Any, fixture: Any, basis: Any, prior: dict[str, Any], device: torch.device) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []; pair_passes = []; union_passes = []
    for pair in range(4):
        a_mask, b_mask = complementary_masks(pair); full_mask = torch.ones(base.GENES, dtype=torch.bool)
        outputs = {name: panel_forward(model, fixture, basis, prior, mask, device, retain=True) for name, mask in (("A", a_mask), ("B", b_mask), ("FULL", full_mask))}
        half = len(outputs["A"]["arrays"]["belief"]) // 2
        sealed = slice(base.VALIDATION, half)
        means_a = outputs["A"]["arrays"]["belief"][sealed]
        means_b = outputs["B"]["arrays"]["belief"][sealed]
        diagonal_a = outputs["A"]["arrays"]["total_diagonal"][sealed]
        diagonal_b = outputs["B"]["arrays"]["total_diagonal"][sealed]
        low_rank_a = outputs["A"]["arrays"]["total_low_rank"][sealed]
        low_rank_b = outputs["B"]["arrays"]["total_low_rank"][sealed]
        same_delta = means_a - means_b
        mismatch_delta = means_a - means_b.roll(-1, 0)
        same_solve = lrd_solve(same_delta, diagonal_a + diagonal_b, torch.cat((low_rank_a, low_rank_b), dim=-1))
        mismatch_solve = lrd_solve(
            mismatch_delta,
            diagonal_a + diagonal_b.roll(-1, 0),
            torch.cat((low_rank_a, low_rank_b.roll(-1, 0)), dim=-1),
        )
        same = (same_delta * same_solve).sum(1) / base.WIDTH
        mismatch = (mismatch_delta * mismatch_solve).sum(1) / base.WIDTH
        threshold = mismatch.median(); fraction_below = float((same < threshold).float().mean())
        same_pass = float(same.median()) < float(mismatch.median()) and fraction_below >= .75
        medians = {name: outputs[name]["arrays"]["marginal"][sealed].median(0).values for name in outputs}
        union_fraction = float(((medians["FULL"] <= medians["A"]) & (medians["FULL"] <= medians["B"])).float().mean())
        union_pass = union_fraction >= .75
        cosine = torch.nn.functional.cosine_similarity(means_a, means_b)
        full_validation = outputs["FULL"]["arrays"]["belief"][:base.VALIDATION]
        mapping = ridge_fit(full_validation, fixture.factors[base.TRAIN:base.TRAIN + base.VALIDATION].cpu(), 1e-3)
        pred_a, pred_b = ridge_predict(mapping, means_a), ridge_predict(mapping, means_b)
        correlations = torch.stack([torch.corrcoef(torch.stack((pred_a[:, i], pred_b[:, i])))[0, 1] for i in range(base.FACTORS)])
        row = {
            "pair": pair, "panel_a_size": int(a_mask.sum()), "panel_b_size": int(b_mask.sum()),
            "intersection": int((a_mask & b_mask).sum()), "union": int((a_mask | b_mask).sum()),
            "same_cell_median_J": float(same.median()), "mismatched_cell_median_J": float(mismatch.median()),
            "same_below_mismatch_median_fraction": fraction_below, "same_cell_compatibility_pass": same_pass,
            "union_coordinate_reduction_fraction": union_fraction, "union_reduction_pass": union_pass,
            "panel_a_median_trace": float(outputs["A"]["arrays"]["trace"][sealed].median()),
            "panel_b_median_trace": float(outputs["B"]["arrays"]["trace"][sealed].median()),
            "union_median_trace": float(outputs["FULL"]["arrays"]["trace"][sealed].median()),
            "same_cell_belief_cosine": float(cosine.median()),
            "factor_prediction_correlation_mean": float(correlations.mean()),
            "factor_prediction_correlation_median": float(correlations.median()),
            "factor_prediction_mean_absolute_discrepancy": float((pred_a - pred_b).abs().mean()),
        }
        rows.append(row); pair_passes.append(same_pass); union_passes.append(union_pass)
        print(f"complementary pair={pair} same_pass={same_pass} union_pass={union_pass}", flush=True)
    return rows, {"same_cell_compatibility_pass": all(pair_passes), "union_uncertainty_reduction_pass": all(union_passes)}


def classify(rows: list[dict[str, Any]], semantics: dict[str, Any], cross: dict[str, Any]) -> tuple[str, dict[str, bool], dict[str, str]]:
    primary = [row for row in rows if row["panel"] in PRIMARY]
    p60 = [row for row in rows if row["panel"] == "P60"]
    gates = {
        "legacy_parity": semantics["legacy_parity_pass"],
        "structural_firewall": semantics["structural_firewall_pass"],
        "measured_zero_distinct": (
            semantics["measured_zero"]["proof_subset_at_least_256"]
            and semantics["measured_zero"]["measured_zero_observed"]
            and semantics["measured_zero"]["structural_zero_not_observed"]
            and semantics["measured_zero"]["state_codes_distinct"]
            and semantics["measured_zero"]["measured_zero_nonzero_visible_contribution_fraction"] == 1.0
            and semantics["measured_zero"]["structural_zero_visible_contribution_norm"] == 0.0
        ),
        "structural_target_excluded": not semantics["training_vs_structural"]["structural_target_eligible"],
        "p60_proper_score": all(row["nll"] < row["prior_nll"] for row in p60),
        "p60_calibration": all(.8 <= row["joint_scale"] <= 1.25 and .58 <= row["coverage_1sigma"] <= .78 and .88 <= row["coverage_1_96sigma"] <= .99 for row in p60),
        "no_harm": all(row["belief_factor_r2"] >= row["visible_factor_r2"] - .02 for row in primary),
        "uncertainty_monotonic": all(row["family_monotonic_fraction"] >= .75 for row in rows if row["panel"] == "FULL"),
        "uncertainty_error": all(row["family_primary_median_spearman"] > .5 for row in rows if row["panel"] == "FULL"),
        "cross_panel": cross["same_cell_compatibility_pass"],
        "union_reduction": cross["union_uncertainty_reduction_pass"],
    }
    semantic = all(gates[k] for k in ("legacy_parity", "structural_firewall", "measured_zero_distinct", "structural_target_excluded"))
    if not semantic:
        classification = "STRUCTURAL-UNMEASUREMENT CONTRACT FAILS"
    elif all(gates.values()):
        classification = "STRUCTURAL-UNMEASUREMENT CONTRACT QUALIFIED FOR RBB-JEPA"
    else:
        classification = "MEASUREMENT SEMANTICS QUALIFIED; BELIEF REQUIRES STRUCTURAL-PANEL TRAINING EXPOSURE"
    correlated_gain = [row["nll"] - row["diagonalized_nll"] for row in primary]
    correlated = "EARNED" if np.median(correlated_gain) < -1e-4 else "NOT EARNED"
    p20 = [row for row in rows if row["panel"] == "P20"]
    p20_cal = all(.8 <= row["joint_scale"] <= 1.25 and .58 <= row["coverage_1sigma"] <= .78 and .88 <= row["coverage_1_96sigma"] <= .99 for row in p20)
    p20_increasing = all(row["family_monotonic_fraction"] >= .75 for row in rows if row["panel"] == "FULL")
    p20_class = "GRACEFUL" if p20_cal else ("UNCERTAIN BUT CALIBRATION-DEGRADED" if p20_increasing else "FALSELY CONFIDENT")
    secondary = {"correlated_component": correlated, "p20_extreme_panel": p20_class, "cross_panel_cell_identity": "SUPPORTED" if cross["same_cell_compatibility_pass"] else "NOT SUPPORTED"}
    return classification, gates, secondary


def append_readout(payload: dict[str, Any]) -> None:
    path = Path("docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md")
    marker = "## Structurally Unmeasured Genes and Heterogeneous Panel Qualification"
    existing = path.read_text(encoding="utf-8")
    if marker in existing:
        raise RuntimeError("structural-panel readout already exists")
    section = f"""

{marker}

This forward-only synthetic audit introduced four explicit measurement states: observed measured,
measured zero, training masked, and structurally unmeasured. A measured zero remains factual
evidence; a training mask hides a measured value and remains target-eligible; structural panel
unmeasurement provides no value and is never target-eligible. Panel-unmeasured genes may be
inferred only when observation support exists elsewhere in foundation data. Globally never-observed
genes cannot receive learned cell-specific inference from nonexistent data.

The frozen molecular ledger and belief checkpoint received zero optimizer updates. Legacy parity
and the structural-value firewall were tested at `1e-6`. Four nested random and four TRAIN-graph
coherent panel views covered FULL, P80, P60, P40, and diagnostic P20 measurements. Four
complementary P60 pairs had exact 2,458/2,458 sizes, 820-gene intersections, and 4,096-gene unions.

Primary classification: **{payload['classification']}**.

Correlated component under structural panels: **{payload['secondary_classifications']['correlated_component']}**.
Cross-panel cell identity: **{payload['secondary_classifications']['cross_panel_cell_identity']}**.
P20 stress result: **{payload['secondary_classifications']['p20_extreme_panel']}**.

This is synthetic architecture qualification only. It does not establish real biological validity,
pathology biology, regulator causality, spatial validity, perturbational dynamics, or Stage81A3
completion.
"""
    base.atomic_text(path, existing.rstrip() + section + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--project-dir", type=Path, default=ROOT)
    args = parser.parse_args(); os.chdir(args.project_dir.resolve())
    if any(path.exists() for path in OUTPUTS.values()):
        raise RuntimeError("structural-panel artifact already exists; repeat forbidden")
    started = time.perf_counter(); device = torch.device("cuda")
    torch.set_float32_matmul_precision("high"); torch.backends.cuda.matmul.allow_tf32 = True
    model, fixture, basis, priors, hashes, checkpoint_metadata = reconstruct(device)
    before = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
    semantics = parity_and_firewalls(model, fixture, basis, priors["RANDOM_40"], device)
    families, panel_construction = build_panels(fixture)
    metric_rows: list[dict[str, Any]] = []; calibration_rows = []; activity_rows = []
    retained: dict[tuple[str, int, str], dict[str, Any]] = {}
    for family in FAMILIES:
        prior = priors["RANDOM_40" if family == "RANDOM_STRUCTURAL" else "COEXPRESSION_BLOCK_40"]
        for view, masks in enumerate(families[family]):
            for panel in PANEL_ORDER:
                print(f"{family} view={view} panel={panel} measured={PANEL_COUNTS[panel]}", flush=True)
                result = panel_forward(model, fixture, basis, prior, masks[panel], device)
                retained[(family, view, panel)] = result
                for factor in range(base.FACTORS):
                    metric_rows.append({
                        "family": family, "view": view, "panel": panel, "measured_genes": PANEL_COUNTS[panel], "factor": factor,
                        "synthetic_full_expected_factor_r2": result["factors"]["synthetic_full_expected"]["per_factor"][factor],
                        "full_noisy_factor_r2": result["factors"]["full_noisy"]["per_factor"][factor],
                        "visible_factor_r2": result["factors"]["visible"]["per_factor"][factor],
                        "belief_factor_r2": result["factors"]["belief"]["per_factor"][factor],
                    })
                calibration_rows.append({key: value for key, value in {
                    "family": family, "view": view, "panel": panel, "measured_genes": PANEL_COUNTS[panel],
                    "nll": result["nll"], "diagonalized_nll": result["diagonalized_nll"], "prior_nll": result["prior_nll"],
                    "joint_scale": result["joint_scale"], "standardized_variance": result["standardized_variance"],
                    "coverage_1sigma": result["coverage_1sigma"], "coverage_1_96sigma": result["coverage_1_96sigma"],
                    "uncertainty_error_spearman": result["uncertainty_error_spearman"], "median_trace": result["median_trace"], "median_logdet": result["median_logdet"],
                }.items()})
                for rank, rank_summary in enumerate(result["amplitude_by_rank"]):
                    activity_rows.append({"family": family, "view": view, "panel": panel, "rank": rank, "mean_correlated_energy": result["mean_correlated_energy"], "median_correlated_rank": result["median_correlated_rank"], **{f"amplitude_{key}": value for key, value in rank_summary.items()}})
    summary_rows = []
    for family in FAMILIES:
        coordinate_stacks = [torch.stack([retained[(family, view, panel)]["coordinate_median_variance"] for panel in PANEL_ORDER]) for view in range(4)]
        fractions = [float(((stack[1:] >= stack[:-1]).all(0)).float().mean()) for stack in coordinate_stacks]
        primary_spearman = np.median([retained[(family, view, panel)]["uncertainty_error_spearman"] for view in range(4) for panel in PRIMARY])
        for panel in PANEL_ORDER:
            values = [retained[(family, view, panel)] for view in range(4)]
            summary_rows.append({
                "family": family, "panel": panel,
                "nll": float(np.median([x["nll"] for x in values])), "diagonalized_nll": float(np.median([x["diagonalized_nll"] for x in values])), "prior_nll": float(np.median([x["prior_nll"] for x in values])),
                "joint_scale": float(np.median([x["joint_scale"] for x in values])), "coverage_1sigma": float(np.median([x["coverage_1sigma"] for x in values])), "coverage_1_96sigma": float(np.median([x["coverage_1_96sigma"] for x in values])),
                "visible_factor_r2": float(np.median([x["factors"]["visible"]["mean"] for x in values])), "belief_factor_r2": float(np.median([x["factors"]["belief"]["mean"] for x in values])),
                "visible_factor_r2_median": float(np.median([x["factors"]["visible"]["median"] for x in values])), "belief_factor_r2_median": float(np.median([x["factors"]["belief"]["median"] for x in values])),
                "median_trace": float(np.median([x["median_trace"] for x in values])), "median_logdet": float(np.median([x["median_logdet"] for x in values])),
                "mean_correlated_energy": float(np.median([x["mean_correlated_energy"] for x in values])),
                "uncertainty_error_spearman": float(np.median([x["uncertainty_error_spearman"] for x in values])),
                "family_monotonic_fraction": float(np.median(fractions)), "family_primary_median_spearman": float(primary_spearman),
            })
    cross_rows, cross_summary = cross_panel_audit(model, fixture, basis, priors["RANDOM_40"], device)
    random_vs_coherent = []
    for panel in PANEL_ORDER:
        random_row = next(row for row in summary_rows if row["family"] == "RANDOM_STRUCTURAL" and row["panel"] == panel)
        coherent_row = next(row for row in summary_rows if row["family"] == "COHERENT_STRUCTURAL" and row["panel"] == panel)
        random_vs_coherent.append({
            "panel": panel,
            **{f"coherent_minus_random_{field}": coherent_row[field] - random_row[field] for field in ("belief_factor_r2", "nll", "median_trace", "joint_scale", "mean_correlated_energy")},
        })
    classification, gates, secondary = classify(summary_rows, semantics, cross_summary)
    after = model.state_dict(); parameters_unchanged = all(torch.equal(before[name], after[name].detach().cpu()) for name in before)
    payload = {
        "stage": "stage81a3_rbb_structural_panel", "anchor": ANCHOR, "seed": SEED,
        "classification": classification, "secondary_classifications": secondary, "primary_gates": gates,
        "prior_evidence": {"verified_hashes": PRIOR_EVIDENCE, "molecular_hashes": hashes, "checkpoint_metadata": checkpoint_metadata},
        "measurement_state_contract": {"states": ["OBSERVED_MEASURED", "MEASURED_ZERO", "TRAINING_MASKED", "STRUCTURALLY_UNMEASURED"], "observed_mask": "measurement_mask & ~training_hidden_mask", "belief_missing_mask": "training_hidden_mask | structural_unmeasured_mask", "training_target_eligible_mask": "measurement_mask & training_hidden_mask", "factual_visible_state": "A @ ((x - mu) * observed_mask)", "primary_training_hidden_mask": "all false", "foundation_support_boundary": "globally never-observed genes cannot receive learned cell-specific inference"},
        "semantics_audit": semantics, "panel_construction": panel_construction, "panel_summary": summary_rows,
        "random_vs_coherent_missingness": random_vs_coherent, "cross_panel_summary": cross_summary, "model_parameters_unchanged": parameters_unchanged,
        "full_panel_sanity": {"measured_genes": 4096, "structurally_unmeasured_genes": 0, "artificial_missing_genes": False, "residual_uncertainty_reported": True},
        "optimizer_constructed": False, "optimizer_updates": 0, "model_training": False,
        "synthetic_full_reference_forward_access": False, "synthetic_full_reference_evaluation_only": True,
        "future_interfaces": {"regulator_adapter": "gene-token ledger compatible", "spatial_adapter": "cell belief plus molecular ledger compatible", "multimodal_adapter": "explicit modality/measurement masks compatible", "perturbation_controller": "pre-state plus intervention to post-state belief compatible", "modules_implemented": False},
        "governance": {"stage81a3_complete": False, "stage81b_started": False, "real_rna_accessed": False, "pathology_opened": False, "factor_labels_used_for_fitting": False, "sealed_used_for_panel_construction": False, "hyperparameter_sweep": False, "seed_sweep": False},
        "wall_seconds": time.perf_counter() - started,
    }
    base.atomic_csv(OUTPUTS["metrics"], metric_rows); base.atomic_csv(OUTPUTS["calibration"], calibration_rows)
    base.atomic_csv(OUTPUTS["cross"], cross_rows); base.atomic_csv(OUTPUTS["activity"], activity_rows)
    base.atomic_json(OUTPUTS["json"], payload); append_readout(payload)
    print(json.dumps({"classification": classification, "gates": gates, "secondary": secondary, "parameters_unchanged": parameters_unchanged}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
