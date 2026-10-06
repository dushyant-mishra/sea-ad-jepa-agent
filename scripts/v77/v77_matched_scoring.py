#!/usr/bin/env python3
"""Score a synthetic count matrix with EXACTLY the rules that produced the frozen real envelopes.

WHY THIS EXISTS (defects S139, S140). Every synthetic-versus-real comparison of detection
topology made before this module chose its 3,000 genes by the variance of the BINARY detection
matrix. The frozen real detection envelope chooses them by the variance of CPM-log1p EXPRESSION
and only then binarises, and its builder says so in a comment: the binary rule "would select a
different gene set and the two calibrations would not be comparable". The synthetic T5 guard
was likewise computed on the binary layer with a 150-cell class floor, while the real T5 of
1.012 is computed on the CPM-log1p expression layer with a 200-cell floor.

NOTHING HERE IS RE-IMPLEMENTED. Each statistic is computed by the real builder's own function:

    gene selection, expression correlation   build_v77_topology_calibration.hvg_correlation
    dependence statistics, either layer      build_v77_calibration_envelope.stats_from_logmatrix
    class-conditional T5                     build_v77_topology_calibration.class_conditional_t5
    abundance marginals                      build_v77_calibration_envelope.abundance_stats

on the FROZEN evaluation universe TRAIN_PREVALENCE05_19569, where a universe gene the candidate
fails to detect stays as a zero column so the loss counts against the candidate.

KNOWN LIMITATION, NOT FIXED HERE (S130). abundance max/median divides by the median of the
NONZERO per-gene means, so a candidate that detects many universe genes only rarely gets a small
denominator and a large ratio. On the frozen universe this statistic therefore also penalises
detection coverage, and must be read that way wherever it is quoted.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v77_calibration_envelope as ENV  # noqa: E402
import build_v77_topology_calibration as TC  # noqa: E402

N_HVG = 3000
RULE = ("genes chosen by CPM-log1p expression variance on the frozen universe, then each layer "
        "scored on that same gene set; T5 on the expression layer with the real 200-cell floor")


def score_matched(counts: np.ndarray, universe: np.ndarray, cls: np.ndarray,
                  n_hvg: int = N_HVG) -> dict:
    """counts: (cells, all addresses) raw counts. universe: frozen evaluation universe."""
    X = sparse.csr_matrix(np.asarray(counts, dtype=np.float64))
    lib = np.asarray(X.sum(1)).ravel()
    C, _hvg_idx, Ld, sel = TC.hvg_correlation(X, lib, np.asarray(universe), n_hvg)
    sub = np.asarray(X[:, universe].todense())
    det = (sub > 0).astype(np.float64)
    det_stats = ENV.stats_from_logmatrix(det, sel, n_hvg)
    expr_stats = ENV.stats_from_logmatrix(Ld, sel, n_hvg)
    per_class, pooled, within = TC.class_conditional_t5(Ld, sel, C, np.asarray(cls))
    ab = ENV.abundance_stats(sub, lib[:, None])
    # genes in the selected set whose detection never varies contribute zero correlation, exactly
    # as they do in the real envelope; report how many so a reader can see it
    det_constant = int((det[:, sel].std(0) == 0).sum())
    return dict(
        rule=RULE,
        detection=dict(det_stats, selected_genes_with_constant_detection=det_constant),
        expression=expr_stats,
        t5=dict(within_over_pooled=(float(within / pooled) if pooled > 0 else float("nan")),
                pooled_median_abs_corr=pooled, mean_within_class_median_abs_corr=within,
                classes_used=list(per_class), min_class_cells=TC.MIN_CLASS_CELLS),
        abundance=ab,
        canonical_genes_detected=int((sub.sum(0) > 0).sum()),
        canonical_genes_lost=int(len(universe) - (sub.sum(0) > 0).sum()),
        median_detected_per_cell=float(np.median((sub > 0).sum(1))))
