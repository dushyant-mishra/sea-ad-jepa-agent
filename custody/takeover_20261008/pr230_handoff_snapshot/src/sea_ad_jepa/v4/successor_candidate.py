"""Provisional full-transcriptome candidate mechanics for Stage81A2R/A3R."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import torch

from .ipb_jepa import CorrelationGraph


FORBIDDEN_BIOLOGICAL_INPUTS = frozenset({
    "donor_id", "dataset_id", "matrix_id", "pathology", "diagnosis",
    "neuropathology", "cell_type", "subtype", "rare_state", "latent_factor",
})


@dataclass(frozen=True)
class SuccessorCandidateContract:
    """Revisioned candidate contract that decouples address and state capacity."""

    gene_count: int
    d_gene: int = 160
    global_audit_max_dim: int = 96
    encoder_blocks: int = 6
    attention_heads: int = 4
    status: str = "PROVISIONAL_NOT_FROZEN"

    def __post_init__(self) -> None:
        if self.gene_count < 1 or self.d_gene < 1 or self.global_audit_max_dim < 1:
            raise ValueError("candidate dimensions must be positive")
        if self.d_gene % self.attention_heads:
            raise ValueError("d_gene must be divisible by attention_heads")


@dataclass(frozen=True)
class CandidateMolecularLedger:
    """Complete molecular evidence; contextual states cannot stand in for it."""

    canonical_gene_ids: torch.Tensor
    normalized_expression: torch.Tensor
    measurement_support: torch.Tensor
    contextual_gene_states: torch.Tensor

    def __post_init__(self) -> None:
        shape = self.normalized_expression.shape
        if self.canonical_gene_ids.shape != shape or self.measurement_support.shape != shape:
            raise ValueError("gene identity, expression, and support must share [B,G]")
        if self.contextual_gene_states.shape[:2] != shape:
            raise ValueError("contextual states must share the Ledger [B,G] axes")
        if self.canonical_gene_ids.dtype != torch.long:
            raise TypeError("canonical_gene_ids must be torch.long")
        if self.measurement_support.dtype != torch.bool:
            raise TypeError("measurement_support must be boolean")
        if not torch.isfinite(self.normalized_expression).all():
            raise ValueError("normalized expression must be finite")

    def detached(self) -> "CandidateMolecularLedger":
        return CandidateMolecularLedger(
            self.canonical_gene_ids.detach(),
            self.normalized_expression.detach(),
            self.measurement_support.detach(),
            self.contextual_gene_states.detach(),
        )


def validate_encoder_inputs(inputs: Iterable[str]) -> None:
    prohibited = sorted(set(inputs) & FORBIDDEN_BIOLOGICAL_INPUTS)
    if prohibited:
        raise ValueError(f"forbidden unrestricted biological inputs: {prohibited}")


def oracle_module_graph(module_ids: np.ndarray, neighbors_per_gene: int = 2) -> CorrelationGraph:
    """Build a sparse synthetic masking graph without any pairwise correlations."""
    modules = np.asarray(module_ids, dtype=np.int64)
    if modules.ndim != 1 or len(modules) < 2:
        raise ValueError("module_ids must be a one-dimensional multi-gene array")
    grouped: dict[int, list[int]] = {}
    for gene, module in enumerate(modules.tolist()):
        grouped.setdefault(module, []).append(gene)
    positions = {gene: position for members in grouped.values() for position, gene in enumerate(members)}
    neighbors: list[torch.Tensor] = []
    weights: list[torch.Tensor] = []
    for gene, module in enumerate(modules.tolist()):
        members = grouped[module]
        position = positions[gene]
        candidates = []
        for offset in range(1, neighbors_per_gene + 1):
            if len(members) > 1:
                candidates.extend((members[(position - offset) % len(members)], members[(position + offset) % len(members)]))
        ordered = sorted(set(candidates) - {gene})[: 2 * neighbors_per_gene]
        neighbors.append(torch.tensor(ordered, dtype=torch.long))
        weights.append(torch.linspace(1.0, 0.8, max(1, len(ordered)))[:len(ordered)])
    return CorrelationGraph(tuple(neighbors), tuple(weights), neighbors_per_gene, len(modules))


@dataclass(frozen=True)
class LinearBasis:
    mean: np.ndarray
    scale: np.ndarray
    weights: np.ndarray
    components: np.ndarray
    fit_donors: tuple[str, ...]
    singular_values: np.ndarray


def fit_reproducibility_weighted_basis(
    expression: np.ndarray,
    measurement_support: np.ndarray,
    reproducibility: np.ndarray,
    donors: np.ndarray,
    max_dim: int,
) -> LinearBasis:
    """Fit a donor-balanced accountable linear basis with local preprocessing."""
    x = np.asarray(expression, dtype=np.float64)
    support = np.asarray(measurement_support, dtype=bool)
    r = np.asarray(reproducibility, dtype=np.float64)
    donor_values = np.asarray(donors).astype(str)
    if x.shape != support.shape or x.shape[1] != len(r) or x.shape[0] != len(donor_values):
        raise ValueError("basis inputs have incompatible dimensions")
    measured_count = support.sum(0).clip(min=1)
    mean = (x * support).sum(0) / measured_count
    centered = np.where(support, x - mean, 0.0)
    scale = np.sqrt(((centered ** 2) * support).sum(0) / measured_count).clip(min=1e-6)
    weights = np.sqrt(np.maximum(r, 0.0))
    standardized = centered / scale * weights
    unique, counts = np.unique(donor_values, return_counts=True)
    donor_weight = {donor: 1.0 / count for donor, count in zip(unique, counts)}
    row_weights = np.sqrt(np.asarray([donor_weight[value] for value in donor_values]))
    weighted = standardized * row_weights[:, None]
    gram = weighted @ weighted.T
    values, vectors = np.linalg.eigh(gram)
    order = np.argsort(values)[::-1][: min(max_dim, x.shape[0] - 1)]
    singular = np.sqrt(np.maximum(values[order], 1e-12))
    components = (weighted.T @ vectors[:, order]) / singular
    return LinearBasis(mean, scale, weights, components.astype(np.float32), tuple(sorted(unique.tolist())), singular.astype(np.float64))


def masked_project(
    expression: np.ndarray,
    support: np.ndarray,
    basis: LinearBasis,
    dimensions: int,
    ridge: float = 1e-4,
) -> np.ndarray:
    """Infer coordinates from measured genes only; structural zeros never enter."""
    x = np.asarray(expression, dtype=np.float64)
    mask = np.asarray(support, dtype=bool)
    w = basis.components[:, :dimensions].astype(np.float64)
    standardized = (x - basis.mean) / basis.scale * basis.weights
    output = np.empty((len(x), dimensions), dtype=np.float64)
    eye = np.eye(dimensions)
    for row in range(len(x)):
        measured = mask[row]
        local = w[measured]
        output[row] = np.linalg.solve(local.T @ local + ridge * eye, local.T @ standardized[row, measured])
    return output


def zero_fill_project(expression: np.ndarray, support: np.ndarray, basis: LinearBasis, dimensions: int) -> np.ndarray:
    standardized = np.where(
        support,
        (expression - basis.mean) / basis.scale * basis.weights,
        0.0,
    )
    return standardized @ basis.components[:, :dimensions]


def one_standard_error_dimension(dimensions: list[int], errors: np.ndarray) -> tuple[int, float]:
    """Select the smallest dimension within one SE of the best mean error."""
    values = np.asarray(errors, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != len(dimensions):
        raise ValueError("errors must be [evaluations, dimensions]")
    means = values.mean(0)
    se = values.std(0, ddof=1) / np.sqrt(values.shape[0]) if values.shape[0] > 1 else np.zeros(len(dimensions))
    best = int(np.argmin(means))
    threshold = means[best] + se[best]
    eligible = [dimension for dimension, mean in zip(dimensions, means) if mean <= threshold]
    return min(eligible), float(threshold)


def contiguous_supported_prefix(blocks: list[tuple[int, int, bool]]) -> tuple[int, str]:
    """Stop at the first unsupported residual and flag later apparent support."""
    if not blocks:
        raise ValueError("at least one block is required")
    prefix = blocks[0][0] - 1
    gap = False
    later = False
    for start, end, supported in blocks:
        if not gap and supported:
            prefix = end
        elif not supported:
            gap = True
        elif gap and supported:
            later = True
    return prefix, "ORDERING FAILURE / REPRESENTATION-DESIGN CONCERN" if later else "CONTIGUOUS"


def biological_evidence_curve(expression: np.ndarray, support: np.ndarray, basis: LinearBasis, fractions: list[float], seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    reference = masked_project(expression, support, basis, basis.components.shape[1])
    values = []
    for fraction in fractions:
        subsupport = support & (rng.random(support.shape) < fraction)
        for row in range(len(subsupport)):
            if not subsupport[row].any():
                first_measured = int(np.flatnonzero(support[row])[0])
                subsupport[row, first_measured] = True
        values.append(np.linalg.norm(masked_project(expression, subsupport, basis, basis.components.shape[1]) - reference, axis=1))
    return np.stack(values, axis=1)


def measurement_quality_curve(expression: np.ndarray, support: np.ndarray, basis: LinearBasis, noise_scales: list[float], seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    reference = masked_project(expression, support, basis, basis.components.shape[1])
    values = []
    for scale in noise_scales:
        noisy = expression + rng.normal(0.0, scale, expression.shape) * support
        values.append(np.linalg.norm(masked_project(noisy, support, basis, basis.components.shape[1]) - reference, axis=1))
    return np.stack(values, axis=1)
