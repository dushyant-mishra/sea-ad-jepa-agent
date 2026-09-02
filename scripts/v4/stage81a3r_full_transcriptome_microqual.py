"""Run bounded provisional Stage81A3R full-transcriptome microqualification."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import yaml
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import average_precision_score, balanced_accuracy_score, r2_score, roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from scipy.stats import hypergeom, rankdata, spearmanr

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sea_ad_jepa.v4.ema import create_ema_target, update_ema_target
from sea_ad_jepa.v4.full_transcriptome_synthetic import generate_full_transcriptome_fixture, normalize_counts
from sea_ad_jepa.v4.ipb_jepa import (
    BlockPredictor, GeneAnchorDecoder, IPBEncoder, block_jepa_loss,
    gather_block_states, gene_anchor_loss, hidden_gene_indices, sample_target_blocks,
)
from sea_ad_jepa.v4.successor_candidate import (
    CandidateMolecularLedger, SuccessorCandidateContract, biological_evidence_curve,
    contiguous_supported_prefix, fit_reproducibility_weighted_basis, masked_project,
    measurement_quality_curve, one_standard_error_dimension, oracle_module_graph,
    zero_fill_project,
)


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk): digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True); handle.write("\n"); temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="") as handle:
        temporary = Path(handle.name)
    pd.DataFrame(rows).to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, path)


def reproducibility(view1: np.ndarray, view2: np.ndarray, support: np.ndarray) -> np.ndarray:
    both = support.astype(np.float64)
    count = both.sum(0).clip(min=2)
    mean1 = (view1 * both).sum(0) / count; mean2 = (view2 * both).sum(0) / count
    first = (view1 - mean1) * both; second = (view2 - mean2) * both
    covariance = (first * second).sum(0)
    denominator = np.sqrt((first ** 2).sum(0) * (second ** 2).sum(0)).clip(min=1e-12)
    return np.clip(covariance / denominator, -1.0, 1.0)


def regression_scores(features: np.ndarray, factors: np.ndarray, train: np.ndarray, test: np.ndarray) -> np.ndarray:
    scores = []
    for column in range(factors.shape[1]):
        model = Ridge(alpha=1.0).fit(features[train], factors[train, column])
        scores.append(r2_score(factors[test, column], model.predict(features[test])))
    return np.asarray(scores)


def standardized_target(expression: np.ndarray, basis) -> np.ndarray:
    return (expression - basis.mean) / basis.scale * basis.weights


def reconstruction_errors(coordinates: np.ndarray, target: np.ndarray, support: np.ndarray, components: np.ndarray) -> np.ndarray:
    prediction = coordinates @ components.T
    squared = (prediction - target) ** 2
    return (squared * support).sum(1) / support.sum(1).clip(min=1)


def top1_retrieval(first: np.ndarray, second: np.ndarray) -> float:
    a = first / np.linalg.norm(first, axis=1, keepdims=True).clip(min=1e-12)
    b = second / np.linalg.norm(second, axis=1, keepdims=True).clip(min=1e-12)
    return float(np.mean(np.argmax(a @ b.T, axis=1) == np.arange(len(a))))


def coordinate_subspace_similarity(first: np.ndarray, second: np.ndarray) -> float:
    """Median canonical correlation between centered coordinate subspaces."""
    left, _ = np.linalg.qr(first - first.mean(0, keepdims=True))
    right, _ = np.linalg.qr(second - second.mean(0, keepdims=True))
    singular = np.linalg.svd(left.T @ right, compute_uv=False)
    return float(np.median(singular))


def _single_full_g_mechanics(gene_count: int, config: dict, module_ids: np.ndarray, microbatch: int) -> dict[str, Any]:
    candidate = config["candidate"]
    contract = SuccessorCandidateContract(gene_count, candidate["d_gene"], config["synthetic"]["global_audit_max_dim"])
    result: dict[str, Any] = {
        "status": "PROVISIONAL_NOT_FROZEN", "G": gene_count, "d_gene": contract.d_gene,
        "blocks": contract.encoder_blocks, "heads": contract.attention_heads,
        "microbatch": microbatch, "gradient_checkpointing": True,
        "torch_version": torch.__version__, "cuda_version": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(), "optimizer_steps_requested": candidate["optimizer_steps"],
    }
    if not torch.cuda.is_available():
        result.update(classification="EXECUTION BLOCKED", reason="CUDA unavailable", optimizer_steps_completed=0)
        return result
    device = torch.device("cuda")
    result.update(gpu=torch.cuda.get_device_name(0), total_vram_bytes=torch.cuda.get_device_properties(0).total_memory, dtype="float16_autocast")
    torch.manual_seed(812401); torch.cuda.manual_seed_all(812401); torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    try:
        online = IPBEncoder(
            vocabulary_size=gene_count, width=contract.d_gene, heads=contract.attention_heads,
            blocks=contract.encoder_blocks, ffn_width=candidate["ffn_width"], dropout=0.0,
            gradient_checkpointing=True,
        ).to(device).train()
        target = create_ema_target(online).to(device)
        predictor = BlockPredictor(width=contract.d_gene, heads=contract.attention_heads).to(device).train()
        decoder = GeneAnchorDecoder(width=contract.d_gene).to(device).train()
        optimizer = torch.optim.AdamW(list(online.parameters()) + list(predictor.parameters()) + list(decoder.parameters()), lr=1e-4)
        graph = oracle_module_graph(module_ids)
        ids = torch.arange(gene_count, device=device).unsqueeze(0).repeat(microbatch, 1)
        measured = torch.ones((microbatch, gene_count), dtype=torch.bool, device=device)
        blocks = sample_target_blocks(measured, graph, production_seed=812401, cell_indices=torch.arange(microbatch, device=device), sample_pass=0, view_index=0, mask_fraction=candidate["mask_fraction"], block_count=candidate["target_blocks"])
        generator = torch.Generator(device=device).manual_seed(812402)
        expression = torch.rand((microbatch, gene_count), generator=generator, device=device)
        times = []; losses = []; minima = []; gradient_norms = []
        for step in range(candidate["optimizer_steps"]):
            optimizer.zero_grad(set_to_none=True); torch.cuda.synchronize(); step_start = time.perf_counter()
            forward_start = time.perf_counter()
            with torch.autocast("cuda", dtype=torch.float16):
                student = online(ids, expression, measured, blocks.hidden_mask, "student")
                with torch.no_grad(): teacher = target(ids, expression, measured, torch.zeros_like(measured), "target")
                teacher_blocks = gather_block_states(teacher.gene_states, blocks)
                predicted = predictor(online.tokenizer.gene_identity, blocks, student.gene_states, student.cell_state, measured & ~blocks.hidden_mask)
                hidden_ids = hidden_gene_indices(blocks.hidden_mask)
                value_hat, detection_hat = decoder(student.cell_state, online.tokenizer.gene_identity, hidden_ids)
                rows = torch.arange(microbatch, device=device)[:, None]
                anchor = gene_anchor_loss(value_hat, detection_hat, expression[rows, hidden_ids], expression[rows, hidden_ids] > 0)
                jepa = block_jepa_loss(predicted, teacher_blocks)
                loss = jepa + anchor["gene"]
            torch.cuda.synchronize(); forward_seconds = time.perf_counter() - forward_start
            backward_start = time.perf_counter(); loss.backward(); torch.cuda.synchronize(); backward_seconds = time.perf_counter() - backward_start
            norm = torch.sqrt(sum((parameter.grad.float().square().sum() for parameter in online.parameters() if parameter.grad is not None), torch.tensor(0.0, device=device)))
            optimizer_start = time.perf_counter(); optimizer.step(); update = update_ema_target(online, target, momentum=candidate["ema_momentum"]); torch.cuda.synchronize(); optimizer_seconds = time.perf_counter() - optimizer_start
            times.append({"step": step, "forward_seconds": forward_seconds, "backward_seconds": backward_seconds, "optimizer_ema_seconds": optimizer_seconds, "total_seconds": time.perf_counter() - step_start})
            losses.append({"step": step, "total": float(loss), "jepa": float(jepa), "gene_anchor": float(anchor["gene"])})
            minima.append(float(student.minimum_denominator)); gradient_norms.append(float(norm))
        ledger = CandidateMolecularLedger(ids, expression, measured, student.gene_states)
        result.update(
            optimizer_steps_completed=len(times), timing=times, losses=losses,
            gradient_norms=gradient_norms, minimum_linear_attention_denominator=min(minima),
            finite=all(np.isfinite([item["total"] for item in losses])) and torch.isfinite(ledger.contextual_gene_states).all().item(),
            optimizer_state_created=bool(optimizer.state), ema_update_success=update.parameter_count > 0,
            peak_allocated_cuda_bytes=torch.cuda.max_memory_allocated(), peak_reserved_cuda_bytes=torch.cuda.max_memory_reserved(),
            wall_seconds=time.perf_counter() - started, classification="MECHANICALLY FEASIBLE",
            pearson_graph_invoked=False, full_molecular_evidence_packaged=True,
        )
    except torch.cuda.OutOfMemoryError as exc:
        result.update(classification="ENGINEERING LIMITATION", reason=f"{type(exc).__name__}: {exc}", optimizer_steps_completed=0, peak_allocated_cuda_bytes=torch.cuda.max_memory_allocated(), peak_reserved_cuda_bytes=torch.cuda.max_memory_reserved())
    finally:
        torch.cuda.empty_cache()
    return result


def full_g_mechanics(gene_count: int, config: dict, module_ids: np.ndarray) -> dict[str, Any]:
    """Run at most three predeclared memory probes and select the largest safe one."""
    probes = []
    for microbatch in config["candidate"].get("memory_probe_microbatches", [1])[:3]:
        result = _single_full_g_mechanics(gene_count, config, module_ids, int(microbatch))
        probes.append(result)
        if result["classification"] in {"ENGINEERING LIMITATION", "MECHANICS FAILURE"}:
            break
        if result.get("peak_reserved_cuda_bytes", 0) >= 14 * 1024 ** 3:
            break
    feasible = [item for item in probes if item["classification"] == "MECHANICALLY FEASIBLE" and item.get("finite")]
    selected = dict(feasible[-1] if feasible else probes[0])
    selected["memory_probes"] = [{
        "microbatch": item["microbatch"], "classification": item["classification"],
        "peak_allocated_cuda_bytes": item.get("peak_allocated_cuda_bytes"),
        "peak_reserved_cuda_bytes": item.get("peak_reserved_cuda_bytes"),
        "optimizer_steps_completed": item.get("optimizer_steps_completed", 0),
    } for item in probes]
    selected["memory_probe_count"] = len(probes)
    selected["practical_microbatch_selected"] = selected["microbatch"]
    return selected


def audit_fixture(fixture, config: dict) -> tuple[list[dict], list[dict], list[dict], list[dict], dict]:
    n = len(fixture.factors); train = np.arange(0, int(n * 2 / 3)); test = np.arange(int(n * 2 / 3), n)
    both = fixture.support_view1 & fixture.support_view2
    repro = reproducibility(fixture.normalized_view1[train], fixture.normalized_view2[train], both[train])
    max_dim = min(config["synthetic"]["global_audit_max_dim"], len(train) - 1)
    basis = fit_reproducibility_weighted_basis(fixture.normalized_view1[train], fixture.support_view1[train], repro, fixture.donor_ids[train], max_dim)
    dimensions = [value for value in config["synthetic"]["dimension_checkpoints"] if value <= max_dim]
    target = standardized_target(fixture.normalized_view2[test], basis)
    error_columns = []; hierarchy = []
    for dimension in dimensions:
        coordinates = masked_project(fixture.normalized_view1[test], fixture.support_view1[test], basis, dimension)
        errors = reconstruction_errors(coordinates, target, fixture.support_view2[test], basis.components[:, :dimension])
        error_columns.append(errors)
        hierarchy.append({"fixture": fixture.name, "dimension": dimension, "mean_cross_view_error": float(errors.mean()), "standard_error": float(errors.std(ddof=1) / np.sqrt(len(errors))), "audit_channel": "bulk"})
    error_matrix = np.stack(error_columns, axis=1)
    k_bulk, threshold = one_standard_error_dimension(dimensions, error_matrix)
    selected = masked_project(fixture.normalized_view1, fixture.support_view1, basis, k_bulk)
    maximum = masked_project(fixture.normalized_view1, fixture.support_view1, basis, max_dim)
    raw_features = np.stack([
        fixture.normalized_view1[:, mask].mean(1) for mask in fixture.factor_gene_mask
    ], axis=1)
    raw_scores = regression_scores(raw_features, fixture.factors, train, test)
    global_scores = regression_scores(selected, fixture.factors, train, test)
    biology = []
    for index, family in enumerate(fixture.factor_families):
        classification = "RAW RNA NOT RECOVERABLE - DATA / EVIDENCE LIMITATION" if raw_scores[index] < 0.20 else ("RAW/LEDGER PRESERVED; GLOBAL-RESOLUTION LIMITATION" if global_scores[index] < raw_scores[index] - 0.10 else "RAW/LEDGER/GLOBAL PRESERVED IN BOUNDED FIXTURE")
        biology.append({"fixture": fixture.name, "factor_index": index, "factor_family": family, "raw_r2": raw_scores[index], "complete_ledger_r2": raw_scores[index], "global_r2": global_scores[index], "classification": classification})
    rare_train = fixture.rare_mask[train].astype(int); rare_test = fixture.rare_mask[test].astype(int)
    if rare_train.sum() and rare_test.sum():
        raw_prob = LogisticRegression(max_iter=1000).fit(raw_features[train], rare_train).predict_proba(raw_features[test])[:, 1]
        global_prob = LogisticRegression(max_iter=1000).fit(selected[train], rare_train).predict_proba(selected[test])[:, 1]
        biology.append({"fixture": fixture.name, "factor_index": 7, "factor_family": "rare_classification", "raw_r2": np.nan, "complete_ledger_r2": np.nan, "global_r2": np.nan, "raw_auroc": roc_auc_score(rare_test, raw_prob), "raw_ap": average_precision_score(rare_test, raw_prob), "global_auroc": roc_auc_score(rare_test, global_prob), "global_ap": average_precision_score(rare_test, global_prob), "classification": "RARE EVALUATION ONLY"})

    # Independently refit all preprocessing and bases on disjoint donor subsets.
    donor_set = sorted(set(fixture.donor_ids[train])); half = len(donor_set) // 2
    fits = []
    ordinary_fits = []
    for subset in (set(donor_set[:half]), set(donor_set[half:])):
        rows = np.asarray([value in subset for value in fixture.donor_ids[train]])
        local_repro = reproducibility(fixture.normalized_view1[train][rows], fixture.normalized_view2[train][rows], both[train][rows])
        fits.append(fit_reproducibility_weighted_basis(fixture.normalized_view1[train][rows], fixture.support_view1[train][rows], local_repro, fixture.donor_ids[train][rows], min(max_dim, rows.sum() - 1)))
        ordinary_fits.append(fit_reproducibility_weighted_basis(fixture.normalized_view1[train][rows], fixture.support_view1[train][rows], np.ones_like(local_repro), fixture.donor_ids[train][rows], min(max_dim, rows.sum() - 1)))
    common_dim = min(fit.components.shape[1] for fit in fits)
    bulk_singular = np.linalg.svd(fits[0].components[:, :k_bulk].T @ fits[1].components[:, :k_bulk], compute_uv=False)
    donor_stability = float(np.median(bulk_singular))
    ordinary_singular = np.linalg.svd(ordinary_fits[0].components[:, :k_bulk].T @ ordinary_fits[1].components[:, :k_bulk], compute_uv=False)
    ordinary_donor_stability = float(np.median(ordinary_singular))
    weighted_coordinates = [masked_project(fixture.normalized_view1[test], fixture.support_view1[test], item, k_bulk) for item in fits]
    ordinary_coordinates = [masked_project(fixture.normalized_view1[test], fixture.support_view1[test], item, k_bulk) for item in ordinary_fits]
    weighted_projected_stability = coordinate_subspace_similarity(*weighted_coordinates)
    ordinary_projected_stability = coordinate_subspace_similarity(*ordinary_coordinates)
    stability_threshold = config["synthetic"]["donor_subspace_min_canonical_correlation"]
    if ordinary_donor_stability < stability_threshold:
        localization = "AUDIT / FIXTURE LIMITATION - ordinary PCA and weighted basis both donor-unstable"
    elif donor_stability < stability_threshold:
        localization = "GLOBAL REPRESENTATION-DESIGN CONCERN - ordinary PCA stable, weighted basis unstable"
    elif weighted_projected_stability < stability_threshold:
        localization = "IMPLEMENTATION / PROJECTION CONCERN - bases stable, weighted projected state unstable"
    else:
        localization = "DONOR-STABLE IN BOUNDED FIXTURE"

    blocks = []; previous = k_bulk
    mean_by_dim = {row["dimension"]: row["mean_cross_view_error"] for row in hierarchy}
    se_by_dim = {row["dimension"]: row["standard_error"] for row in hierarchy}
    for start, end in config["synthetic"]["residual_blocks"]:
        if start <= k_bulk or end not in mean_by_dim or previous not in mean_by_dim:
            continue
        improvement = mean_by_dim[previous] - mean_by_dim[end]
        bulk_supported = improvement > np.sqrt(se_by_dim[previous] ** 2 + se_by_dim[end] ** 2)
        first = masked_project(fixture.normalized_view1[test], fixture.support_view1[test], basis, end)[:, start - 1:end]
        second = masked_project(fixture.normalized_view2[test], fixture.support_view2[test], basis, end)[:, start - 1:end]
        energy1 = np.linalg.norm(first, axis=1); energy2 = np.linalg.norm(second, axis=1)
        tail_spearman = float(spearmanr(energy1, energy2).statistic)
        tail_count = max(1, int(np.ceil(0.10 * len(test))))
        top1 = set(np.argsort(energy1)[-tail_count:]); top2 = set(np.argsort(energy2)[-tail_count:])
        overlap = len(top1 & top2)
        tail_p = float(hypergeom.sf(overlap - 1, len(test), tail_count, tail_count))
        if end <= common_dim:
            singular = np.linalg.svd(fits[0].components[:, start - 1:end].T @ fits[1].components[:, start - 1:end], compute_uv=False)
            block_stability = float(np.median(singular))
        else:
            block_stability = np.nan
        tail_supported = bool(
            tail_spearman >= config["synthetic"]["tail_split_view_min_spearman"]
            and tail_p * len(config["synthetic"]["residual_blocks"]) < config["synthetic"]["tail_familywise_alpha"]
            and np.isfinite(block_stability)
            and block_stability >= config["synthetic"]["tail_donor_subspace_min_canonical_correlation"]
        )
        supported = bulk_supported or tail_supported
        blocks.append((start, end, bool(supported))); previous = end
        hierarchy.append({"fixture": fixture.name, "dimension": end, "mean_cross_view_error": mean_by_dim[end], "standard_error": se_by_dim[end], "audit_channel": "residual_bulk_or_tail", "block_start": start, "block_end": end, "supported": supported, "bulk_supported": bulk_supported, "tail_supported": tail_supported, "improvement": improvement, "tail_split_view_spearman": tail_spearman, "tail_top_decile_overlap": overlap, "tail_hypergeom_p": tail_p, "tail_donor_subspace_median_canonical_correlation": block_stability})
    prefix, ordering = contiguous_supported_prefix([(1, k_bulk, True)] + blocks)
    if localization != "DONOR-STABLE IN BOUNDED FIXTURE":
        prefix = 0
        ordering = localization
    hierarchy.extend([
        {"fixture": fixture.name, "dimension": k_bulk, "audit_channel": "donor_localization_ordinary_pca", "supported": ordinary_donor_stability >= stability_threshold, "tail_donor_subspace_median_canonical_correlation": ordinary_donor_stability, "projected_state_subspace_similarity": ordinary_projected_stability},
        {"fixture": fixture.name, "dimension": k_bulk, "audit_channel": "donor_localization_reproducibility_weighted", "supported": donor_stability >= stability_threshold, "tail_donor_subspace_median_canonical_correlation": donor_stability, "projected_state_subspace_similarity": weighted_projected_stability},
    ])

    masked1 = masked_project(fixture.normalized_view1[test], fixture.support_view1[test], basis, k_bulk)
    masked2 = masked_project(fixture.normalized_view2[test], fixture.support_view2[test], basis, k_bulk)
    zero1 = zero_fill_project(fixture.normalized_view1[test], fixture.support_view1[test], basis, k_bulk)
    zero2 = zero_fill_project(fixture.normalized_view2[test], fixture.support_view2[test], basis, k_bulk)
    observation = [{
        "fixture": fixture.name, "masked_same_cell_distance": float(np.linalg.norm(masked1 - masked2, axis=1).mean()),
        "zero_fill_same_cell_distance": float(np.linalg.norm(zero1 - zero2, axis=1).mean()),
        "masked_top1_retrieval": top1_retrieval(masked1, masked2), "zero_fill_top1_retrieval": top1_retrieval(zero1, zero2),
        "heldout_operator_described_by_support_only": True,
    }]
    heldout = masked_project(fixture.normalized_view2[test], fixture.heldout_support[test], basis, k_bulk)
    heldout_scores = regression_scores(np.vstack((selected[train], heldout)), fixture.factors, np.arange(len(train)), np.arange(len(train), n))
    observation[0]["heldout_operator_mean_factor_r2"] = float(heldout_scores.mean())
    heldout_raw_features = np.stack([
        np.where(fixture.heldout_support, fixture.normalized_view2, 0.0)[:, mask].sum(1)
        / (fixture.heldout_support[:, mask].sum(1).clip(min=1))
        for mask in fixture.factor_gene_mask
    ], axis=1)
    heldout_raw_scores = regression_scores(heldout_raw_features, fixture.factors, train, test)
    observation[0]["heldout_panel_raw_informative_mean_factor_r2"] = float(heldout_raw_scores.mean())
    observation[0]["heldout_panel_attainable_upper_bound_by_family"] = json.dumps({family: float(np.mean(heldout_raw_scores[[index for index, value in enumerate(fixture.factor_families) if value == family]])) for family in sorted(set(fixture.factor_families))}, sort_keys=True)

    # Negative control: unconditional operator mean removal can erase confounded biology.
    confounded = fixture.confounded_operator_ids
    corrected = selected.copy()
    for operator in np.unique(confounded[train]):
        corrected[confounded == operator] -= selected[train][confounded[train] == operator].mean(0)
    factor0_before = regression_scores(selected, fixture.factors[:, :1], train, test)[0]
    factor0_after = regression_scores(corrected, fixture.factors[:, :1], train, test)[0]
    observation[0].update(confounded_biology_r2_before_mean_removal=float(factor0_before), confounded_biology_r2_after_mean_removal=float(factor0_after), unconditional_erasure_is_unsafe=bool(factor0_after < factor0_before))
    folds = GroupKFold(n_splits=3)
    unconditional_prediction = cross_val_predict(LogisticRegression(max_iter=1000), selected, fixture.operator_ids, cv=folds, groups=fixture.donor_ids)
    biology_fit = Ridge(alpha=1.0).fit(fixture.factors[train], selected[train])
    conditional_residual = selected - biology_fit.predict(fixture.factors)
    conditional_prediction = cross_val_predict(LogisticRegression(max_iter=1000), conditional_residual, fixture.operator_ids, cv=folds, groups=fixture.donor_ids)
    own_target = standardized_target(fixture.normalized_view1, basis)
    own_error = reconstruction_errors(selected, own_target, fixture.support_view1, basis.components[:, :k_bulk])
    observation[0].update(
        unconditional_operator_balanced_accuracy=float(balanced_accuracy_score(fixture.operator_ids, unconditional_prediction)),
        biology_conditioned_operator_balanced_accuracy=float(balanced_accuracy_score(fixture.operator_ids, conditional_prediction)),
        generic_residual_rare_mean=float(own_error[fixture.rare_mask].mean()),
        generic_residual_common_mean=float(own_error[~fixture.rare_mask].mean()),
        generic_residual_ood_shortcut_assessment="AUDIT FAILURE - rare sample underpowered; production shortcut not adopted",
        generic_residual_ood_shortcut_adopted=False,
    )

    u_bio = biological_evidence_curve(fixture.normalized_view1[test], fixture.support_view1[test], basis, config["synthetic"]["support_fractions"], 812501)
    u_meas = measurement_quality_curve(fixture.normalized_view1[test], fixture.support_view1[test], basis, config["synthetic"]["noise_scales"], 812502)
    uncertainty = []
    for column, fraction in enumerate(config["synthetic"]["support_fractions"]):
        uncertainty.append({"fixture": fixture.name, "uncertainty_type": "U_BIO", "level": fraction, "mean_distance_to_reference": float(u_bio[:, column].mean()), "rare_mean": float(u_bio[fixture.rare_mask[test], column].mean()) if fixture.rare_mask[test].any() else np.nan, "common_mean": float(u_bio[~fixture.rare_mask[test], column].mean())})
    for column, scale in enumerate(config["synthetic"]["noise_scales"]):
        uncertainty.append({"fixture": fixture.name, "uncertainty_type": "U_MEAS", "level": scale, "mean_distance_to_reference": float(u_meas[:, column].mean()), "rare_mean": float(u_meas[fixture.rare_mask[test], column].mean()) if fixture.rare_mask[test].any() else np.nan, "common_mean": float(u_meas[~fixture.rare_mask[test], column].mean())})
    corr = float(np.corrcoef(u_bio[:, 0], u_meas[:, 0])[0, 1])

    summary = {"fixture": fixture.name, "k_bulk_cross_view_candidate": k_bulk, "one_se_threshold": threshold, "final_contiguous_supported_prefix": prefix, "ordering_status": ordering, "ordinary_pca_donor_subspace_median_canonical_correlation": ordinary_donor_stability, "weighted_basis_donor_subspace_median_canonical_correlation": donor_stability, "ordinary_pca_projected_state_similarity": ordinary_projected_stability, "weighted_basis_projected_state_similarity": weighted_projected_stability, "u_bio_u_meas_correlation": corr, "basis_fit_labels_used": False}
    return biology, hierarchy, observation, uncertainty, summary


def real_train_microaudit(project: Path, config: dict, registry_count: int) -> dict[str, Any]:
    inputs = config["inputs"]
    h5 = pd.read_csv(project / inputs["frozen_h5_gene_stats"])
    nph = pd.read_csv(project / inputs["frozen_nph_gene_stats"])
    countsplit = pd.read_csv(project / inputs["historical_countsplit"])
    return {
        "status": "PARTIAL - DATA / PROVENANCE LIMITATION",
        "new_real_rna_values_opened": False,
        "authorized_train_only_cached_statistics_read": True,
        "candidate_gene_count": registry_count,
        "h5_cached_gene_stat_rows": len(h5), "nph_cached_gene_stat_rows": len(nph),
        "historical_countsplit_rows": len(countsplit),
        "countsplit_coverage_note": "historical count-split evidence covers the frozen 4096 vocabulary, not the complete A2R address space",
        "full_g_real_basis_run": False,
        "reason": "Existing bounded TRAIN caches do not contain a paired full-G cell-by-gene view; creating one would exceed this micro-audit and approach representation materialization.",
        "classification": "DATA / PROVENANCE LIMITATION, not architecture failure",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a2r_a3r_microqual.yaml"))
    args = parser.parse_args(); project = args.project_dir.resolve()
    with (project / args.config).open(encoding="utf-8") as handle: config = yaml.safe_load(handle)
    outputs = {key: project / value for key, value in config["outputs"].items()}
    registry = pd.read_csv(outputs["exact_registry"]); gene_count = len(registry)

    accessed = []
    for role in ("frozen_gene_registry", "frozen_asset_registry", "frozen_split_registry", "frozen_h5_gene_stats", "frozen_nph_gene_stats", "frozen_nph_feature_registry", "historical_countsplit", "historical_fbsdq_report"):
        path = project / config["inputs"][role]
        accessed.append({"role": role, "path": str(path.relative_to(project)).replace("\\", "/"), "sha256": sha256_file(path), "expression_values_accessed": False, "authorized_scope": "frozen metadata or bounded pathology-blind TRAIN statistic"})
    manifest = {"stage": config["stage_id"], "inputs": accessed, "dev_rna_accessed": False, "sealed_rna_accessed": False, "pathology_accessed": False, "real_train_rna_accessed": False}
    atomic_json(outputs["input_manifest"], manifest)

    fixtures = [generate_full_transcriptome_fixture(gene_count, cells=config["synthetic"]["cells"], seed=item["seed"], name=item["name"]) for item in config["synthetic"]["fixtures"]]
    mechanics = full_g_mechanics(gene_count, config, fixtures[0].module_ids)
    atomic_json(outputs["mechanics"], mechanics)
    biology_rows: list[dict] = []; hierarchy_rows: list[dict] = []; observation_rows: list[dict] = []; uncertainty_rows: list[dict] = []; summaries = []
    for fixture in fixtures:
        biology, hierarchy, observation, uncertainty, summary = audit_fixture(fixture, config)
        biology_rows.extend(biology); hierarchy_rows.extend(hierarchy); observation_rows.extend(observation); uncertainty_rows.extend(uncertainty); summaries.append(summary)
    atomic_csv(outputs["biology"], biology_rows); atomic_csv(outputs["hierarchy"], hierarchy_rows); atomic_csv(outputs["observation"], observation_rows); atomic_csv(outputs["uncertainty"], uncertainty_rows)
    real = real_train_microaudit(project, config, gene_count); real["synthetic_fixture_summaries"] = summaries
    atomic_json(outputs["real_train"], real)
    print(json.dumps({"mechanics": mechanics, "fixture_summaries": summaries, "real_train": real}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
