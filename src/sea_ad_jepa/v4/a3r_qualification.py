"""Deterministic synthetic-only utilities for Stage81A3R qualification."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from sklearn.linear_model import Ridge
from sklearn.metrics import average_precision_score, r2_score, roc_auc_score


@dataclass(frozen=True)
class CapacityFixture:
    name: str
    counts: np.ndarray
    normalized: np.ndarray
    factors: np.ndarray
    factor_names: tuple[str, ...]
    factor_families: tuple[str, ...]
    factor_gene_mask: np.ndarray
    donors: np.ndarray
    rare_mask: np.ndarray
    module_ids: np.ndarray
    rates: np.ndarray


def normalize_counts(counts: np.ndarray, support: np.ndarray) -> np.ndarray:
    """Library-size normalize measured counts to 10,000, then apply log1p."""
    observed = np.where(support, counts, 0.0)
    totals = observed.sum(axis=1, keepdims=True).clip(min=1.0)
    return np.log1p(10000.0 * observed / totals).astype(np.float32)


def generate_capacity_fixture(
    *,
    genes: int,
    cells: int,
    donors: int,
    seed: int,
    name: str,
) -> CapacityFixture:
    """Generate a rich overlapping count fixture with recurrent 5% rare state."""
    if genes < 1024 or cells < 256 or donors < 16 or cells % donors:
        raise ValueError("capacity fixture requires genes>=1024, cells>=256, donors>=16, cells divisible by donors")
    rng = np.random.default_rng(seed)
    families = (
        "broad", "broad", "broad", "broad",
        "subtype", "subtype", "subtype", "subtype",
        "state", "state", "state", "state",
        "fine", "fine", "fine", "fine",
        "rare", "rare", "antagonistic", "antagonistic",
        "distributed", "distributed", "compact", "compact", "donor", "donor",
    )
    names = tuple(f"{family}_{index:02d}" for index, family in enumerate(families))
    factor_count = len(families)
    donor_ids = np.repeat(np.arange(donors), cells // donors)
    rng.shuffle(donor_ids)
    factors = rng.normal(0.0, 1.0, (cells, factor_count)).astype(np.float32)
    factors[:, 1] = 0.55 * factors[:, 0] + 0.84 * factors[:, 1]
    factors[:, 5] = -0.45 * factors[:, 4] + 0.89 * factors[:, 5]
    factors[:, 9] = 0.40 * factors[:, 8] + 0.92 * factors[:, 9]
    rare_count = max(16, int(round(0.05 * cells)))
    rare_indices = np.linspace(0, cells - 1, rare_count, dtype=int)
    rare = np.zeros(cells, dtype=bool)
    rare[rare_indices] = True
    factors[:, 16] = rare.astype(np.float32) * 3.0 + rng.normal(0, 0.20, cells)
    factors[:, 17] = rare.astype(np.float32) * -2.2 + rng.normal(0, 0.25, cells)
    donor_values = rng.normal(0, 1, (donors, 2)).astype(np.float32)
    factors[:, 24:26] = donor_values[donor_ids]

    loadings = np.zeros((factor_count, genes), dtype=np.float32)
    module_ids = np.arange(genes, dtype=np.int64) // 32
    widths = (
        genes // 3, genes // 4, genes // 5, genes // 6,
        700, 620, 560, 500, 420, 360, 320, 280,
        180, 150, 120, 100, 72, 64, 240, 220,
        genes // 2, genes // 2, 48, 40, 500, 450,
    )
    for factor, requested in enumerate(widths):
        width = max(24, min(int(requested), genes))
        stride = 131 if name == "overlap_dense" else 197
        start = (factor * stride) % genes
        indices = (start + np.arange(width) * (1 + factor % 5)) % genes
        amplitude = 0.22 if families[factor] in {"distributed", "broad"} else 0.38
        if families[factor] in {"fine", "rare", "compact"}:
            amplitude = 0.55
        signs = np.ones(width, dtype=np.float32)
        if families[factor] == "antagonistic":
            signs[1::2] = -1.0
        if name == "partial_correlation" and factor % 3 == 0:
            signs[::3] *= -1.0
        loadings[factor, indices] += signs * rng.normal(amplitude, 0.05, width)
        module_ids[indices] = factor
    # Overlap modules deliberately without making the latent problem tiny.
    shared = rng.choice(genes, size=min(900, genes // 3), replace=False)
    loadings[2, shared] += 0.15
    loadings[10, shared] -= 0.12
    loadings[20, shared] += 0.10
    baseline = rng.normal(-2.8, 0.65, genes).astype(np.float32)
    log_rate = np.clip(baseline[None, :] + factors @ loadings, -9.0, 3.5)
    rate = np.exp(log_rate)
    depth = rng.lognormal(9.0, 0.35, cells)
    rate = rate / rate.sum(axis=1, keepdims=True) * depth[:, None]
    counts = rng.poisson(rate).astype(np.float32)
    support = np.ones_like(counts, dtype=bool)
    return CapacityFixture(
        name=name,
        counts=counts,
        normalized=normalize_counts(counts, support),
        factors=factors,
        factor_names=names,
        factor_families=families,
        factor_gene_mask=loadings != 0,
        donors=donor_ids,
        rare_mask=rare,
        module_ids=module_ids,
        rates=rate.astype(np.float32),
    )


def donor_split(donors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Use the final quarter of sorted donors as a deterministic held-out set."""
    unique = np.unique(donors)
    boundary = int(np.floor(0.75 * len(unique)))
    train = np.flatnonzero(np.isin(donors, unique[:boundary]))
    test = np.flatnonzero(np.isin(donors, unique[boundary:]))
    return train, test


def centered_normalized_linear_kernels(
    train_values: torch.Tensor,
    test_values: torch.Tensor,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute the full centered/normalized linear kernel without pooling tokens."""
    if train_values.ndim < 2 or test_values.shape[1:] != train_values.shape[1:]:
        raise ValueError("train/test contextual tensors must share non-cell dimensions")
    device = train_values.device
    train = train_values.float().flatten(1)
    test = test_values.float().flatten(1)
    mean = train.mean(dim=0, keepdim=True)
    train = train - mean
    test = test - mean
    train = train / train.square().sum(1, keepdim=True).sqrt().clamp_min(1e-12)
    test = test / test.square().sum(1, keepdim=True).sqrt().clamp_min(1e-12)
    with torch.autocast(device_type=device.type, enabled=False):
        k_train = train @ train.T
        k_test = test @ train.T
    return k_train.cpu().numpy(), k_test.cpu().numpy()


def kernel_factor_scores(
    k_train: np.ndarray,
    k_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    *,
    alpha: float = 1.0,
) -> np.ndarray:
    """Evaluate donor-held-out kernel ridge R2 one synthetic factor at a time."""
    regularized = k_train.astype(np.float64) + alpha * np.eye(len(k_train), dtype=np.float64)
    coefficients = np.linalg.solve(regularized, y_train.astype(np.float64))
    prediction = k_test.astype(np.float64) @ coefficients
    scores = [r2_score(y_test[:, column], prediction[:, column]) for column in range(y_train.shape[1])]
    return np.asarray(scores, dtype=np.float64)


def rare_scores(
    k_train: np.ndarray,
    k_test: np.ndarray,
    rare_train: np.ndarray,
    rare_test: np.ndarray,
) -> tuple[float, float]:
    """Evaluate the recurrent rare state with a deterministic kernel ridge score."""
    regularized = k_train.astype(np.float64) + np.eye(len(k_train), dtype=np.float64)
    coefficients = np.linalg.solve(regularized, rare_train.astype(np.float64))
    prediction = k_test.astype(np.float64) @ coefficients
    return float(roc_auc_score(rare_test, prediction)), float(average_precision_score(rare_test, prediction))


def contextual_distance(
    candidate: torch.Tensor,
    reference: torch.Tensor,
    joint_support: torch.Tensor,
) -> np.ndarray:
    """Per-cell normalized Frobenius distance over jointly measured genes."""
    if candidate.shape != reference.shape or joint_support.shape != candidate.shape[:2]:
        raise ValueError("contextual tensors/support shapes differ")
    diff = (candidate.float() - reference.float()).square().sum(-1)
    ref = reference.float().square().sum(-1)
    mask = joint_support.float()
    numerator = (diff * mask).sum(1)
    denominator = (ref * mask).sum(1).clamp_min(1e-12)
    return torch.sqrt(numerator / denominator).cpu().numpy()


def anti_topk_fixture(*, genes: int = 8192, cells: int = 512, seed: int = 813901) -> dict:
    """Show that generic top-K ranking can retain broad and discard rare biology."""
    if genes <= 4096:
        raise ValueError("anti-top-K fixture requires a universe larger than 4096")
    rng = np.random.default_rng(seed)
    broad = rng.normal(size=cells)
    rare = np.zeros(cells, dtype=np.float32)
    rare[np.linspace(0, cells - 1, max(20, int(0.05 * cells)), dtype=int)] = 1.0
    base = np.concatenate((np.full(4096, 2.0), np.full(genes - 4096, 0.02)))
    rate = np.broadcast_to(base, (cells, genes)).copy()
    broad_genes = np.arange(0, 900)
    rare_genes = np.arange(genes - 96, genes)
    rate[:, broad_genes] *= np.exp(0.35 * broad[:, None])
    rate[:, rare_genes] *= np.exp(3.0 * rare[:, None])
    counts = rng.poisson(rate).astype(np.float32)
    detection = (counts > 0).mean(0)
    variance = np.log1p(counts).var(0)
    ranking_score = detection + 0.01 * variance
    selected = np.argsort(-ranking_score, kind="stable")[:4096]
    train = np.arange(0, int(0.75 * cells))
    test = np.arange(int(0.75 * cells), cells)

    def features(columns: np.ndarray) -> np.ndarray:
        broad_present = np.intersect1d(columns, broad_genes)
        rare_present = np.intersect1d(columns, rare_genes)
        return np.column_stack((
            np.log1p(counts[:, broad_present]).mean(1) if len(broad_present) else np.zeros(cells),
            np.log1p(counts[:, rare_present]).mean(1) if len(rare_present) else np.zeros(cells),
        ))

    full = features(np.arange(genes))
    top = features(selected)
    full_broad = Ridge(alpha=1.0).fit(full[train], broad[train]).predict(full[test])
    top_broad = Ridge(alpha=1.0).fit(top[train], broad[train]).predict(top[test])
    full_rare = Ridge(alpha=1.0).fit(full[train], rare[train]).predict(full[test])
    top_rare = Ridge(alpha=1.0).fit(top[train], rare[train]).predict(top[test])
    return {
        "status": "PROVISIONAL_SYNTHETIC_ONLY_NOT_FROZEN",
        "selector_inputs": ["detection", "variance"],
        "selector_accessed_latent_labels": False,
        "genes": genes,
        "top_k": 4096,
        "broad_genes_selected": int(np.isin(broad_genes, selected).sum()),
        "rare_genes_selected": int(np.isin(rare_genes, selected).sum()),
        "full_broad_r2": float(r2_score(broad[test], full_broad)),
        "topk_broad_r2": float(r2_score(broad[test], top_broad)),
        "full_rare_auroc": float(roc_auc_score(rare[test], full_rare)),
        "full_rare_ap": float(average_precision_score(rare[test], full_rare)),
        "topk_rare_auroc": float(roc_auc_score(rare[test], top_rare)),
        "topk_rare_ap": float(average_precision_score(rare[test], top_rare)),
    }
