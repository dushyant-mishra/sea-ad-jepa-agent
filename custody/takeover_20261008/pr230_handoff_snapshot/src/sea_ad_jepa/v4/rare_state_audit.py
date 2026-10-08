"""Fixed Stage81A3 rare-state and transfer qualification mechanics."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

import numpy as np


KNN_K = 15
LOCAL_DENSITY_K = 30
ANNOTATION_RARE_MAX_FREQUENCY = 0.01
ANNOTATION_RARE_MIN_CELLS = 100
RECURRING_MIN_DONORS = 5
RECURRING_MIN_CELLS_PER_DONOR = 3


def transfer_performance(balanced_accuracy: Iterable[float], neighbor_purity: Iterable[float]) -> str:
    accuracy = np.asarray(list(balanced_accuracy), dtype=float)
    purity = np.asarray(list(neighbor_purity), dtype=float)
    valid = np.isfinite(accuracy) & np.isfinite(purity)
    if not valid.any():
        return "NOT-IDENTIFIABLE"
    median_accuracy = float(np.median(accuracy[valid]))
    median_purity = float(np.median(purity[valid]))
    if median_accuracy >= 0.80 and median_purity >= 0.80:
        return "STRONG"
    if median_accuracy >= 0.60:
        return "MODERATE"
    return "WEAK"


def transfer_coverage(identifiable: int, total: int) -> str:
    fraction = identifiable / total if total else 0.0
    if fraction >= 0.75:
        return "BROAD"
    if fraction >= 0.25:
        return "PARTIAL"
    return "SPARSE"


def qc_earning(
    relative_mae_improvement: Iterable[float],
    quality_spearman: Iterable[float],
    technology_median_improvement: Iterable[float],
) -> str:
    improvement = np.asarray(list(relative_mae_improvement), dtype=float)
    spearman = np.asarray(list(quality_spearman), dtype=float)
    technology = np.asarray(list(technology_median_improvement), dtype=float)
    improvement = improvement[np.isfinite(improvement)]
    spearman = spearman[np.isfinite(spearman)]
    technology = technology[np.isfinite(technology)]
    if not len(improvement) or not len(spearman) or not len(technology):
        return "NOT EARNED"
    gates = (
        np.median(improvement) >= 0.10,
        np.mean(improvement > 0) >= 0.70,
        np.median(spearman) >= 0.50,
        np.min(technology) >= -0.10,
    )
    if all(gates):
        return "EARNED"
    return "PARTIAL" if any(gates) else "NOT EARNED"


def rarity_flags(class_count: int, total_count: int, donor_counts: Iterable[int]) -> tuple[bool, bool]:
    donor_counts = np.asarray(list(donor_counts), dtype=int)
    annotation_rare = (
        total_count > 0
        and class_count >= ANNOTATION_RARE_MIN_CELLS
        and class_count / total_count <= ANNOTATION_RARE_MAX_FREQUENCY
    )
    recurring = annotation_rare and int(np.sum(donor_counts >= RECURRING_MIN_CELLS_PER_DONOR)) >= RECURRING_MIN_DONORS
    return bool(annotation_rare), bool(recurring)


def stable_hash_sample(ids: Iterable[str], donors: Iterable[str], cap: int = 512) -> np.ndarray:
    ids = np.asarray(list(ids), dtype=str)
    donors = np.asarray(list(donors), dtype=str)
    if len(ids) != len(donors):
        raise ValueError("ids and donors must align")
    if len(ids) <= cap:
        return np.arange(len(ids), dtype=int)
    groups = sorted(np.unique(donors))
    base, remainder = divmod(cap, len(groups))
    selected: list[int] = []
    for position, donor in enumerate(groups):
        indices = np.flatnonzero(donors == donor)
        quota = base + (position < remainder)
        order = sorted(indices, key=lambda i: hashlib.sha256(f"{donor}|{ids[i]}".encode()).digest())
        selected.extend(order[:quota])
    if len(selected) < cap:
        remaining = sorted(set(range(len(ids))) - set(selected), key=lambda i: hashlib.sha256(ids[i].encode()).digest())
        selected.extend(remaining[: cap - len(selected)])
    return np.asarray(sorted(selected[:cap]), dtype=int)


def ledger_cosine(left: np.ndarray, right: np.ndarray, block_genes: int = 128) -> np.ndarray:
    """Cosine similarity over every gene-token entry, blockwise over genes."""
    if left.ndim != 3 or right.ndim != 3 or left.shape[1:] != right.shape[1:]:
        raise ValueError("ledger arrays must be [cells, genes, width] with matching gene/width shape")
    genes = left.shape[1]
    numerator = np.zeros((len(left), len(right)), dtype=np.float64)
    left_norm = np.zeros(len(left), dtype=np.float64)
    right_norm = np.zeros(len(right), dtype=np.float64)
    for start in range(0, genes, block_genes):
        stop = min(start + block_genes, genes)
        a = np.asarray(left[:, start:stop], dtype=np.float64).reshape(len(left), -1)
        b = np.asarray(right[:, start:stop], dtype=np.float64).reshape(len(right), -1)
        numerator += a @ b.T
        left_norm += np.square(a).sum(1)
        right_norm += np.square(b).sum(1)
    return numerator / np.maximum(np.sqrt(left_norm[:, None] * right_norm[None, :]), 1e-12)


def critical_compression_flag(ledger_purity: float, pca_purity: float, ledger_recall: float, pca_recall: float) -> bool:
    return bool(
        (ledger_purity >= 0.75 and ledger_purity - pca_purity > 0.25)
        or (ledger_recall >= 0.70 and ledger_recall - pca_recall > 0.25)
    )
