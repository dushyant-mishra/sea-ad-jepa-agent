"""Deterministic structured full-transcriptome fixtures for bounded audits."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SyntheticTranscriptome:
    name: str
    counts_view1: np.ndarray
    counts_view2: np.ndarray
    normalized_view1: np.ndarray
    normalized_view2: np.ndarray
    support_view1: np.ndarray
    support_view2: np.ndarray
    heldout_support: np.ndarray
    factors: np.ndarray
    factor_families: tuple[str, ...]
    donor_ids: np.ndarray
    operator_ids: np.ndarray
    module_ids: np.ndarray
    rare_mask: np.ndarray
    confounded_operator_ids: np.ndarray
    factor_gene_mask: np.ndarray


def normalize_counts(counts: np.ndarray, support: np.ndarray) -> np.ndarray:
    measured = np.where(support, counts, 0.0)
    totals = measured.sum(1, keepdims=True).clip(min=1.0)
    return np.log1p(10000.0 * measured / totals).astype(np.float32)


def _operator_support(cells: int, genes: int, fractions: tuple[float, ...], assignments: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    support = np.zeros((cells, genes), dtype=bool)
    for operator, fraction in enumerate(fractions):
        panel = rng.choice(genes, size=max(1, int(round(fraction * genes))), replace=False)
        support[np.ix_(assignments == operator, panel)] = True
    return support


def generate_full_transcriptome_fixture(
    gene_count: int,
    *,
    cells: int = 192,
    seed: int = 812301,
    name: str = "overlapping_programs",
) -> SyntheticTranscriptome:
    """Generate two-view count data with broad through recurrent-rare programs."""
    if gene_count < 256 or cells < 64:
        raise ValueError("scaled fixture requires at least 256 genes and 64 cells")
    rng = np.random.default_rng(seed)
    families = ("broad", "broad", "subtype", "subtype", "state", "state", "fine", "rare", "donor")
    factor_count = len(families)
    donors = np.asarray([f"D{index % 12:02d}" for index in rng.permutation(cells)])
    factors = rng.normal(size=(cells, factor_count)).astype(np.float32)
    factors[:, 1] = 0.65 * factors[:, 0] + 0.76 * factors[:, 1]
    factors[:, 3] = 0.45 * factors[:, 2] + 0.89 * factors[:, 3]
    rare_count = max(3, int(round(cells * (0.01 if name == "overlapping_programs" else 0.02))))
    rare_indices = np.linspace(0, cells - 1, rare_count, dtype=int)
    rare = np.zeros(cells, dtype=bool); rare[rare_indices] = True
    factors[:, 7] = rare.astype(np.float32) * 4.0 + rng.normal(0, 0.15, cells)
    donor_lookup = {donor: value for donor, value in zip(sorted(set(donors)), rng.normal(0, 1, len(set(donors))))}
    factors[:, 8] = np.asarray([donor_lookup[value] for value in donors])

    loadings = np.zeros((factor_count, gene_count), dtype=np.float32)
    widths = [max(500, gene_count // 5), max(400, gene_count // 6), 600, 450, 240, 180, 80, 32, 300]
    module_ids = np.arange(gene_count, dtype=np.int64) // 64
    for factor, width in enumerate(widths):
        width = min(width, gene_count)
        start = (factor * 977) % max(1, gene_count - width + 1)
        genes = np.arange(start, start + width)
        loadings[factor, genes] += rng.normal(0.65 if factor < 2 else 0.45, 0.10, width)
        module_ids[genes] = factor
    if name == "rare_tail_difficult":
        loadings[7] *= 0.55
        loadings[:2] *= 1.35
    baseline = rng.normal(-2.4, 0.55, gene_count)
    log_rate = baseline[None] + factors @ loadings
    depth = rng.lognormal(mean=9.2, sigma=0.35, size=cells)
    rate = np.exp(np.clip(log_rate, -8, 4))
    rate = rate / rate.sum(1, keepdims=True) * depth[:, None]
    counts1 = rng.poisson(rate).astype(np.float32)
    counts2 = np.random.default_rng(seed + 1).poisson(rate).astype(np.float32)
    operator = np.arange(cells) % 3
    support1 = _operator_support(cells, gene_count, (0.97, 0.83, 0.68), operator, seed + 2)
    support2 = _operator_support(cells, gene_count, (0.97, 0.83, 0.68), operator, seed + 3)
    counts1[~support1] = 0.0; counts2[~support2] = 0.0
    heldout = _operator_support(cells, gene_count, (0.74,), np.zeros(cells, dtype=int), seed + 4)
    confounded = operator.copy()
    confounded[factors[:, 0] > np.median(factors[:, 0])] = 2
    return SyntheticTranscriptome(
        name, counts1, counts2, normalize_counts(counts1, support1),
        normalize_counts(counts2, support2), support1, support2, heldout,
        factors, families, donors, operator, module_ids, rare, confounded,
        loadings != 0,
    )
