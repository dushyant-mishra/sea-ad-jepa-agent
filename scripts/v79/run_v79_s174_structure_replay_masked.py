#!/usr/bin/env python3
"""Structural-support-corrected exact-S174 development replay (V4).

This module deliberately preserves the V3 replay's model structures, folds, panel-selection rule, operator penalty
set and residual-support definitions. The only scientific correction is observation eligibility: structurally
unmeasured cell-gene entries never enter a likelihood, score, prevalence summary, or residual diagnostic.

The historical V3 runner remains unchanged for provenance. This V4 runner requires a separately authenticated
operator-by-gene structural-support mask derived from the Stage81A2R measurement-support authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import run_v79_s174_structure_replay as L

SEED = L.SEED
RIDGE = L.RIDGE
MODELS = L.MODELS
OPERATOR_MODEL = L.OPERATOR_MODEL
OPERATOR_LAMBDA_PRIMARY = L.OPERATOR_LAMBDA_PRIMARY
OPERATOR_LAMBDA_SET = L.OPERATOR_LAMBDA_SET
OPERATOR_RULING_CONVENTION = L.OPERATOR_RULING_CONVENTION

sha256 = L.sha256
select_panel_positions = L.select_panel_positions
donor_folds = L.donor_folds
design_matrix = L.design_matrix
operator_column_mask = L.operator_column_mask
operator_penalty_vector = L.operator_penalty_vector
permutation_group_support = L.permutation_group_support
operator_support_after_donor_centering = L.operator_support_after_donor_centering
operator_increment_ruling = L.operator_increment_ruling
summarize = L.summarize
summarize_support = L.summarize_support


def _raw_bool_sha256(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a, dtype=bool).tobytes()).hexdigest()


def load_structural_support(mask_path, record_path, data: dict, expected_cache_sha256: str) -> np.ndarray:
    """Authenticate an operator×gene support matrix and expand it to cell×gene support.

    The record row order is explicit through `operators`; no assumption is made that operator IDs are dense or
    start at zero. This is required for partial measurement support inside a source.
    """
    mask_path, record_path = Path(mask_path), Path(record_path)
    rec = json.loads(record_path.read_text(encoding="utf-8"))
    if rec.get("schema") != "V79_G500_STRUCTURAL_SUPPORT_DEV_V1":
        raise SystemExit("STOP: structural-support record has unexpected schema")
    if rec.get("cache_sha256") != expected_cache_sha256:
        raise SystemExit("STOP: structural-support record is bound to a different compact cache")

    op_gene = np.asarray(np.load(mask_path, allow_pickle=False), dtype=bool)
    operators = np.asarray(rec.get("operators", []), dtype=np.int64)
    if op_gene.ndim != 2 or len(operators) != op_gene.shape[0]:
        raise SystemExit("STOP: structural-support operator rows disagree with record")
    if op_gene.shape[1] != data["counts_selected"].shape[1]:
        raise SystemExit("STOP: structural-support gene dimension disagrees with compact cache")
    if len(np.unique(operators)) != len(operators):
        raise SystemExit("STOP: structural-support record contains duplicate operator IDs")
    if rec.get("op_x_gene_sha256") != _raw_bool_sha256(op_gene):
        raise SystemExit("STOP: structural-support mask content hash mismatch")

    op_to_row = {int(op): i for i, op in enumerate(operators.tolist())}
    missing = sorted(set(map(int, np.unique(data["op"]))) - set(op_to_row))
    if missing:
        raise SystemExit(f"STOP: structural-support mask lacks operators {missing[:5]}")
    rows = np.asarray([op_to_row[int(op)] for op in data["op"]], dtype=np.int64)
    cell_gene = op_gene[rows]
    if cell_gene.shape != data["counts_selected"].shape:
        raise SystemExit("STOP: expanded structural-support mask has wrong shape")
    return np.asarray(cell_gene, dtype=bool)


def gene_observation_masks(data: dict, gene: int) -> dict[str, np.ndarray]:
    counts = np.asarray(data["counts_selected"])[:, gene]
    support = data.get("measured_selected")
    if support is None:
        measured = np.ones(len(counts), dtype=bool)
    else:
        support = np.asarray(support, dtype=bool)
        if support.shape != np.asarray(data["counts_selected"]).shape:
            raise ValueError("measured_selected must match counts_selected shape")
        measured = support[:, gene]
    detected = measured & (counts > 0)
    return {
        "measured": measured,
        "eligible_detection": measured.copy(),
        "detected": detected,
        "positive": detected.copy(),
    }


def evaluate_detection_gene(data: dict, gene: int, k: int = 3, seed: int = SEED) -> dict:
    counts = np.asarray(data["counts_selected"])[:, gene]
    obs = gene_observation_masks(data, gene)
    measured = obs["measured"]
    y = (counts > 0).astype(np.float64)
    folds = donor_folds(data["donor"], data["src"], k, seed)
    out = {}

    for model in MODELS[:-1]:
        X = design_matrix(data, model)
        losses = []
        for test_fold in folds:
            train = (~test_fold) & measured
            test = test_fold & measured
            if not test.any() or not train.any():
                continue
            beta = L._logistic_fit(X[train], y[train])
            losses.append(L._bernoulli_logloss(y[test], X[test] @ beta))
        if not losses:
            out[model] = {"mean_logloss": None, "n_test_predictions": 0}
        else:
            loss = np.concatenate(losses)
            out[model] = {"mean_logloss": float(loss.mean()), "n_test_predictions": int(len(loss))}

    X = design_matrix(data, OPERATOR_MODEL)
    sens = {}
    for lam in OPERATOR_LAMBDA_SET:
        pen = operator_penalty_vector(data, OPERATOR_MODEL, lam)
        losses, failed = [], 0
        for test_fold in folds:
            train = (~test_fold) & measured
            test = test_fold & measured
            if not test.any() or not train.any():
                continue
            try:
                beta = L._logistic_fit(X[train], y[train], penalty=pen)
            except RuntimeError:
                if lam == OPERATOR_LAMBDA_PRIMARY:
                    raise
                failed += 1
                continue
            losses.append(L._bernoulli_logloss(y[test], X[test] @ beta))
        if failed:
            sens[str(lam)] = {"mean_logloss": None, "n_test_predictions": 0,
                              "converged": False, "failed_folds": int(failed)}
        elif not losses:
            sens[str(lam)] = {"mean_logloss": None, "n_test_predictions": 0,
                              "converged": True, "failed_folds": 0}
        else:
            loss = np.concatenate(losses)
            sens[str(lam)] = {"mean_logloss": float(loss.mean()), "n_test_predictions": int(len(loss)),
                              "converged": True, "failed_folds": 0}
    out[OPERATOR_MODEL] = sens[str(OPERATOR_LAMBDA_PRIMARY)]
    prevalence = float(y[measured].mean()) if measured.any() else None
    return {"gene_position": int(gene), "prevalence": prevalence, "n_measured": int(measured.sum()),
            "models": out, "operator_penalty_sensitivity": sens}


def evaluate_positive_gene(data: dict, gene: int, k: int = 3, seed: int = SEED) -> dict:
    counts = np.asarray(data["counts_selected"])[:, gene].astype(np.float64)
    obs = gene_observation_masks(data, gene)
    pos = obs["positive"]
    folds = donor_folds(data["donor"], data["src"], k, seed)

    def run(X, penalty=None):
        lpds = []
        for test_donor in folds:
            train = (~test_donor) & pos
            test = test_donor & pos
            if train.sum() <= X.shape[1] or not test.any():
                continue
            beta, sigma = L._ridge_linear_fit(X[train], np.log(counts[train]), penalty=penalty)
            lpds.append(L._normal_lpd(np.log(counts[test]), X[test] @ beta, sigma))
        if not lpds:
            return {"mean_lpd": None, "n_positive_test_predictions": 0}
        lpd = np.concatenate(lpds)
        return {"mean_lpd": float(lpd.mean()), "n_positive_test_predictions": int(len(lpd))}

    out = {model: run(design_matrix(data, model)) for model in MODELS[:-1]}
    X = design_matrix(data, OPERATOR_MODEL)
    sens = {str(lam): run(X, operator_penalty_vector(data, OPERATOR_MODEL, lam)) for lam in OPERATOR_LAMBDA_SET}
    out[OPERATOR_MODEL] = sens[str(OPERATOR_LAMBDA_PRIMARY)]
    return {"gene_position": int(gene), "n_measured": int(obs["measured"].sum()),
            "n_positive": int(pos.sum()), "models": out, "operator_penalty_sensitivity": sens}


def residual_support_for_gene(data: dict, gene: int, seed: int = SEED, n_perm: int = 99) -> dict:
    counts = np.asarray(data["counts_selected"])[:, gene].astype(np.float64)
    obs = gene_observation_masks(data, gene)
    measured = obs["measured"]
    y_all = (counts > 0).astype(np.float64)

    X_full_all = design_matrix(data, OPERATOR_MODEL)
    X_noop_all = design_matrix(data, "depth_class_source")
    X_full = X_full_all[measured]
    X_noop = X_noop_all[measured]
    y = y_all[measured]
    donor = np.asarray(data["donor"])[measured]
    src = np.asarray(data["src"])[measured]
    op = np.asarray(data["op"])[measured]
    dk = np.asarray(data["dk"])[measured]

    pen_full = operator_penalty_vector(data, OPERATOR_MODEL, OPERATOR_LAMBDA_PRIMARY)
    b_full = L._logistic_fit(X_full, y, penalty=pen_full)
    det_full_resid = y - L.expit(X_full @ b_full)
    b_noop = L._logistic_fit(X_noop, y)
    det_noop_resid = y - L.expit(X_noop @ b_noop)
    det_dc_resid = L._center_within(det_full_resid, donor)

    det = {
        "donor": permutation_group_support(det_full_resid, donor, src, seed + 1, n_perm),
        "operator": operator_support_after_donor_centering(det_noop_resid, op, donor, src, seed + 2, n_perm),
        "donor_class_increment": permutation_group_support(det_dc_resid, dk, donor, seed + 3, n_perm),
    }

    pos = obs["positive"]
    positive = None
    if int(pos.sum()) > X_full_all.shape[1] + 5:
        z = np.log(counts[pos])
        Xf = X_full_all[pos]
        Xn = X_noop_all[pos]
        bf, _ = L._ridge_linear_fit(Xf, z, penalty=pen_full)
        pos_full_resid = z - Xf @ bf
        bn, _ = L._ridge_linear_fit(Xn, z)
        pos_noop_resid = z - Xn @ bn
        donor_pos = np.asarray(data["donor"])[pos]
        src_pos = np.asarray(data["src"])[pos]
        op_pos = np.asarray(data["op"])[pos]
        dk_pos = np.asarray(data["dk"])[pos]
        pos_dc_resid = L._center_within(pos_full_resid, donor_pos)
        positive = {
            "donor": permutation_group_support(pos_full_resid, donor_pos, src_pos, seed + 11, n_perm),
            "operator": operator_support_after_donor_centering(pos_noop_resid, op_pos, donor_pos, src_pos,
                                                               seed + 12, n_perm),
            "donor_class_increment": permutation_group_support(pos_dc_resid, dk_pos, donor_pos,
                                                               seed + 13, n_perm),
        }
    return {"gene_position": int(gene), "n_measured": int(measured.sum()),
            "detection": det, "positive": positive}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("cache")
    ap.add_argument("receipt")
    ap.add_argument("out")
    ap.add_argument("--support-mask", required=True)
    ap.add_argument("--support-record", required=True)
    ap.add_argument("--genes", type=int, default=200)
    ap.add_argument("--support-genes", type=int, default=50)
    ap.add_argument("--permutations", type=int, default=99)
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--seed", type=int, default=SEED)
    return ap


def main() -> None:
    a = build_parser().parse_args()
    cache_path = Path(a.cache)
    data = L.load_compact_cache(cache_path, a.receipt)
    measured = load_structural_support(a.support_mask, a.support_record, data, sha256(cache_path))
    data["measured_selected"] = measured

    panel = select_panel_positions(data["prevalence_selected"], min(a.genes, data["counts_selected"].shape[1]), a.seed)
    support_panel_local = select_panel_positions(data["prevalence_selected"][panel],
                                                 min(a.support_genes, len(panel)), a.seed + 101)
    support_panel = panel[support_panel_local]

    det = [evaluate_detection_gene(data, int(g), a.folds, a.seed) for g in panel.tolist()]
    pos = [evaluate_positive_gene(data, int(g), a.folds, a.seed) for g in panel.tolist()]
    support = [residual_support_for_gene(data, int(g), a.seed + int(i) * 100, a.permutations)
               for i, g in enumerate(support_panel.tolist())]

    operator_robustness = {
        "detection": operator_increment_ruling(det, "mean_logloss", higher_is_better=False, seed=a.seed),
        "positive_lognormal": operator_increment_ruling(pos, "mean_lpd", higher_is_better=True, seed=a.seed + 1),
    }
    support_rec = json.loads(Path(a.support_record).read_text(encoding="utf-8"))
    affected = np.any(~measured, axis=0)
    rec = {
        "schema": "V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V4_MASKED",
        "status": "DEVELOPMENT_ONLY__MASK_CORRECTED__NOT_CONFIRMATORY__NOT_SYNTHETIC_CONSUMABLE",
        "structural_support": {
            "invariant": "MEASURED_SCALAR != STRUCTURALLY_UNMEASURED",
            "mask_path_name": Path(a.support_mask).name,
            "mask_file_sha256": sha256(Path(a.support_mask)),
            "record_path_name": Path(a.support_record).name,
            "record_sha256": sha256(Path(a.support_record)),
            "op_x_gene_sha256": support_rec.get("op_x_gene_sha256"),
            "n_unmeasured_entries": int((~measured).sum()),
            "unmeasured_fraction": float((~measured).mean()),
            "affected_cache_genes": int(affected.sum()),
        },
        "operator_penalty": {
            "primary_lambda": OPERATOR_LAMBDA_PRIMARY,
            "sensitivity_set": list(OPERATOR_LAMBDA_SET),
            "primary_fits_must_converge": True,
            "sensitivity_failures_recorded_not_rescued": True,
        },
        "operator_increment_robustness": operator_robustness,
        "operator_support_null": "DONOR_CENTERED_RESIDUALS__PERMUTED_WITHIN_DONOR",
        "cache_sha256": sha256(cache_path),
        "receipt_sha256": sha256(Path(a.receipt)),
        "n_cells": int(len(data["donor"])),
        "n_donors": int(len(np.unique(data["donor"]))),
        "n_cache_genes": int(data["counts_selected"].shape[1]),
        "n_replay_genes": int(len(panel)),
        "n_support_genes": int(len(support_panel)),
        "folds": int(a.folds),
        "seed": int(a.seed),
        "permutations": int(a.permutations),
        "models": list(MODELS),
        "ridge": RIDGE,
        "panel_positions_internal": panel.tolist(),
        "support_panel_positions_internal": support_panel.tolist(),
        "panel_prevalence_range_legacy_selection": [float(data["prevalence_selected"][panel].min()),
                                                    float(data["prevalence_selected"][panel].max())],
        "detection_summary": summarize(det, "mean_logloss"),
        "positive_lognormal_summary": summarize(pos, "mean_lpd"),
        "random_effect_support": {"detection": summarize_support(support, "detection"),
                                  "positive": summarize_support(support, "positive")},
        "per_gene_detection": det,
        "per_gene_positive": pos,
        "per_gene_random_effect_support": support,
        "boundaries": {"bayesian_posterior_inference": False, "confirmatory_qualification": False,
                       "qualification_world_generation": False, "factorial_execution": False,
                       "training_authorized": False},
        "terminal": ("MASK_CORRECTED_EXACT_S174_REPLAY_COMPLETE__DEVELOPMENT_ONLY__CONTROLLER_REVIEW_REQUIRED__"
                     "QUALIFICATION_WORLDS_NOT_GENERATED__TRAINING_OFF"),
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "schema": rec["schema"], "n_replay_genes": len(panel),
                      "n_unmeasured_entries": rec["structural_support"]["n_unmeasured_entries"]}))


if __name__ == "__main__":
    main()
