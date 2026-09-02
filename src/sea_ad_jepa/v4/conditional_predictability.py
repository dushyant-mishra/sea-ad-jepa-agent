"""Mechanics for the bounded Stage81A3 conditional-predictability audit."""

from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass

import torch
import torch.nn.functional as F
from torch import nn

from .masking import keyed_mask_seed


@dataclass(frozen=True)
class CPFixture:
    factors: torch.Tensor
    factors_cf: torch.Tensor
    rates: torch.Tensor
    rates_cf: torch.Tensor
    lambda_norm: torch.Tensor
    lambda_norm_cf: torch.Tensor
    count_a: torch.Tensor
    count_b: torch.Tensor
    x_a: torch.Tensor
    x_b: torch.Tensor
    x_a_cf: torch.Tensor
    loadings: torch.Tensor
    library: torch.Tensor
    intervention_node: torch.Tensor
    true_adjacency: torch.Tensor
    timings: dict[str, float]


@dataclass(frozen=True)
class CPBasis:
    mean: torch.Tensor
    components: torch.Tensor
    eigenvalues: torch.Tensor
    analysis: torch.Tensor
    epsilon: float

    def transform(self, values: torch.Tensor) -> torch.Tensor:
        return (values.float() - self.mean) @ self.analysis.T

    def contribution(self, values: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        return ((values.float() - self.mean) * mask.float()) @ self.analysis.T

    def reconstruct_contribution(self, coordinates: torch.Tensor) -> torch.Tensor:
        ordinary = coordinates.float() * torch.sqrt(self.eigenvalues + self.epsilon)
        return ordinary @ self.components


@dataclass(frozen=True)
class CPMaskBank:
    families: tuple[str, ...]
    visible: torch.Tensor
    hidden: torch.Tensor
    block_ids: torch.Tensor


TRUE_EDGES = (
    (0, 3, .65), (0, 4, -.55), (1, 4, .70), (1, 5, -.60),
    (2, 5, .75), (2, 6, .55), (3, 7, .60), (4, 7, -.65),
    (4, 8, .50), (5, 8, .70), (5, 9, -.55), (6, 9, .65),
    (7, 10, .70), (8, 10, -.50), (8, 11, .60), (9, 11, .75),
)


def normalize_counts(values: torch.Tensor) -> torch.Tensor:
    return torch.log1p(values * (10_000.0 / values.sum(1, keepdim=True).clamp_min(1.0)))


def true_adjacency(device: torch.device, mechanisms: int = 12) -> torch.Tensor:
    adjacency = torch.zeros(mechanisms, mechanisms, device=device)
    for source, target, weight in TRUE_EDGES:
        adjacency[source, target] = weight
    return adjacency


def causal_values(
    exogenous: torch.Tensor,
    adjacency: torch.Tensor,
    intervention_node: torch.Tensor | None = None,
    intervention_delta: torch.Tensor | None = None,
) -> torch.Tensor:
    values = torch.zeros_like(exogenous)
    for node in range(adjacency.shape[0]):
        values[:, node] = 0.70 * exogenous[:, node] + values @ adjacency[:, node]
        if intervention_node is not None:
            selected = intervention_node == node
            values[selected, node] += intervention_delta[selected]
    return values


def build_fixture(
    device: torch.device,
    *,
    cells: int = 4096,
    genes: int = 4096,
    factors: int = 32,
    train: int = 3072,
    seed: int = 8114001,
) -> CPFixture:
    """Create expected state and independent paired sequencing observations."""
    generation_started = time.perf_counter()
    generator = torch.Generator(device=device).manual_seed(seed + 101)
    exogenous = torch.randn(cells, 12, generator=generator, device=device)
    independent = torch.randn(cells, factors - 12, generator=generator, device=device)
    adjacency = true_adjacency(device)
    raw = causal_values(exogenous, adjacency)
    mean = raw[:train].mean(0)
    std = raw[:train].std(0, unbiased=False).clamp_min(1e-6)
    nodes = torch.arange(cells, device=device) % 12
    signs = torch.where((torch.arange(cells, device=device) // 12) % 2 == 0, 1.0, -1.0)
    raw_cf = causal_values(exogenous, adjacency, nodes, signs * std[nodes])
    state = torch.cat(((raw - mean) / std, independent), dim=1)
    state_cf = torch.cat(((raw_cf - mean) / std, independent), dim=1)
    loadings = torch.zeros(factors, genes, device=device)
    module_size = 224
    for factor in range(factors):
        start = (factor * 257 + 31) % genes
        index = (start + torch.arange(module_size, device=device) * 17) % genes
        direction = torch.where(torch.arange(module_size, device=device) % 2 == 0, 1.0, -1.0)
        amplitude = 0.34 + 0.08 * torch.rand(module_size, generator=generator, device=device)
        loadings[factor, index] += direction * amplitude
    baseline = -1.8 + .45 * torch.randn(genes, generator=generator, device=device)
    library = torch.exp(math.log(5500.0) + .55 * torch.randn(cells, generator=generator, device=device)).clamp(1200, 25000)

    def rates_for(latent: torch.Tensor) -> torch.Tensor:
        return torch.softmax(baseline + latent @ loadings, dim=1) * library[:, None]

    rates = rates_for(state)
    rates_cf = rates_for(state_cf)
    lambda_norm = normalize_counts(rates)
    lambda_norm_cf = normalize_counts(rates_cf)
    generation_seconds = time.perf_counter() - generation_started
    replicate_started = time.perf_counter()
    state_before_a = torch.cuda.get_rng_state(device) if device.type == "cuda" else torch.random.get_rng_state()
    count_a = torch.poisson(rates)
    state_before_b = torch.cuda.get_rng_state(device) if device.type == "cuda" else torch.random.get_rng_state()
    count_b = torch.poisson(rates)
    if device.type == "cuda":
        torch.cuda.set_rng_state(state_before_a, device)
    else:
        torch.random.set_rng_state(state_before_a)
    count_a_cf = torch.poisson(rates_cf)
    if device.type == "cuda":
        torch.cuda.set_rng_state(state_before_b, device)
    else:
        torch.random.set_rng_state(state_before_b)
    return CPFixture(
        state, state_cf, rates, rates_cf, lambda_norm, lambda_norm_cf,
        count_a, count_b, normalize_counts(count_a), normalize_counts(count_b),
        normalize_counts(count_a_cf), loadings, library, nodes, adjacency,
        {"synthetic_generation_seconds": generation_seconds,
         "paired_replicate_seconds": time.perf_counter() - replicate_started},
    )


def fit_pca_gram(training_lambda: torch.Tensor, components: int = 160, epsilon: float = 1e-6) -> CPBasis:
    values = training_lambda.detach().float()
    mean = values.mean(0)
    centered = values - mean
    gram = centered @ centered.T
    eigenvalues, left = torch.linalg.eigh(gram)
    order = torch.argsort(eigenvalues, descending=True)[:components]
    eigenvalues = eigenvalues[order].clamp_min(epsilon)
    left = left[:, order]
    component_matrix = (left.T @ centered) / torch.sqrt(eigenvalues)[:, None]
    component_matrix = F.normalize(component_matrix, dim=1)
    analysis = component_matrix / torch.sqrt(eigenvalues + epsilon)[:, None]
    return CPBasis(mean, component_matrix, eigenvalues, analysis, epsilon)


def topk_absolute_correlation(values: torch.Tensor, top_k: int = 8) -> tuple[torch.Tensor, torch.Tensor]:
    standardized = values.float() - values.float().mean(0, keepdim=True)
    standardized /= standardized.std(0, unbiased=True, keepdim=True).clamp_min(1e-6)
    correlation = (standardized.T @ standardized / (len(values) - 1)).abs()
    correlation.fill_diagonal_(-torch.inf)
    return correlation.topk(top_k, dim=1)


def _graph_hidden(neighbors: torch.Tensor, weights: torch.Tensor, genes: int, hidden: int, seed: int) -> tuple[torch.Tensor, torch.Tensor]:
    neighbors, weights = neighbors.cpu(), weights.cpu()
    sizes = [hidden // 4 + (block < hidden % 4) for block in range(4)]
    mask = torch.zeros(genes, dtype=torch.bool)
    block_ids = torch.full((genes,), -1, dtype=torch.int16)
    order = torch.randperm(genes, generator=torch.Generator().manual_seed(seed)).tolist()
    available, cursor = set(range(genes)), 0
    for block, size in enumerate(sizes):
        chosen, frontier, best = [], [], {}
        def add(gene: int) -> None:
            chosen.append(gene); available.remove(gene); mask[gene] = True; block_ids[gene] = block
            for neighbor, weight in zip(neighbors[gene].tolist(), weights[gene].tolist()):
                if neighbor in available and weight > best.get(neighbor, -1.0):
                    best[neighbor] = weight; heapq.heappush(frontier, (-weight, neighbor))
        while order[cursor] not in available: cursor += 1
        add(order[cursor]); cursor += 1
        while len(chosen) < size:
            while frontier:
                negative, candidate = heapq.heappop(frontier)
                if candidate in available and -negative >= best.get(candidate, -1.0):
                    add(candidate); break
            else:
                while order[cursor] not in available: cursor += 1
                add(order[cursor]); cursor += 1
    return mask, block_ids


def build_masks(
    loadings: torch.Tensor,
    neighbors: torch.Tensor,
    weights: torch.Tensor,
    *,
    genes: int = 4096,
    hidden: int = 1638,
    views: int = 4,
    seed: int = 8114001,
) -> CPMaskBank:
    families = ("RANDOM_40", "COEXPRESSION_BLOCK_40", "ORACLE_COVERAGE_40")
    hidden_bank, blocks = [], []
    reporter_reserve = torch.zeros(genes, dtype=torch.bool)
    reserve_per_factor = min(32, max(1, (genes - hidden) // loadings.shape[0]))
    strongest = loadings.abs().topk(reserve_per_factor, dim=1).indices.cpu()
    reporter_reserve[strongest.flatten()] = True
    eligible_oracle = torch.where(~reporter_reserve)[0]
    if len(eligible_oracle) < hidden:
        raise RuntimeError("oracle reporter reserve leaves too few hidden candidates")
    for family_index, family in enumerate(families):
        for view in range(views):
            view_seed = keyed_mask_seed(production_seed=seed, cell_index=family_index, sample_pass=0, view_index=view)
            if family == "RANDOM_40":
                permutation = torch.randperm(genes, generator=torch.Generator().manual_seed(view_seed))
                current = torch.zeros(genes, dtype=torch.bool); current[permutation[:hidden]] = True
                block = torch.full((genes,), -1, dtype=torch.int16)
            elif family == "COEXPRESSION_BLOCK_40":
                current, block = _graph_hidden(neighbors, weights, genes, hidden, view_seed)
            else:
                permutation = eligible_oracle[torch.randperm(len(eligible_oracle), generator=torch.Generator().manual_seed(view_seed))]
                current = torch.zeros(genes, dtype=torch.bool); current[permutation[:hidden]] = True
                block = torch.full((genes,), -1, dtype=torch.int16)
            hidden_bank.append(current); blocks.append(block)
    hidden_tensor = torch.stack(hidden_bank)
    if not torch.all(hidden_tensor.sum(1) == hidden):
        raise RuntimeError("exact hidden-count contract failed")
    return CPMaskBank(families, ~hidden_tensor, hidden_tensor, torch.stack(blocks))


def ridge_fit(x: torch.Tensor, y: torch.Tensor, alpha: float = 1e-3) -> dict[str, torch.Tensor]:
    # The expected-expression fixture is intentionally low rank.  The declared
    # alpha is below the resolvable tail of its float32 Gram spectrum, so solve
    # the same fixed ridge equation in float64 and return compact float32 state.
    x, y = x.double(), y.double()
    x_mean = x.mean(0, keepdim=True); x_std = x.std(0, unbiased=False, keepdim=True).clamp_min(1e-8)
    y_mean = y.mean(0, keepdim=True)
    z = (x - x_mean) / x_std
    if z.shape[1] <= z.shape[0]:
        weights = torch.linalg.solve(z.T @ z + alpha * torch.eye(z.shape[1], device=z.device), z.T @ (y - y_mean))
    else:
        dual = torch.linalg.solve(z @ z.T + alpha * torch.eye(z.shape[0], device=z.device), y - y_mean)
        weights = z.T @ dual
    return {key: value.float() for key, value in {
        "x_mean": x_mean, "x_std": x_std, "y_mean": y_mean, "weights": weights,
    }.items()}


def ridge_predict(model: dict[str, torch.Tensor], x: torch.Tensor) -> torch.Tensor:
    return ((x.float() - model["x_mean"]) / model["x_std"]) @ model["weights"] + model["y_mean"]


class DiagnosticMLP(nn.Module):
    """Fixed value-plus-mask estimator; no factor or hidden-value input surface."""
    def __init__(self, genes: int = 4096, output: int = 160) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(genes * 2, 512), nn.GELU(),
            nn.Linear(512, 256), nn.GELU(), nn.Linear(256, output),
        )

    def forward(self, masked_values: torch.Tensor, visible_mask: torch.Tensor) -> torch.Tensor:
        values = masked_values.masked_fill(~visible_mask, 0.0)
        return self.network(torch.cat((values, visible_mask.float()), dim=1))


def r2_columns(truth: torch.Tensor, prediction: torch.Tensor) -> torch.Tensor:
    residual = (truth.float() - prediction.float()).square().sum(0)
    total = (truth.float() - truth.float().mean(0, keepdim=True)).square().sum(0)
    return torch.where(total > 0, 1.0 - residual / total, torch.nan)


def correlation_columns(first: torch.Tensor, second: torch.Tensor) -> torch.Tensor:
    first = first.float() - first.float().mean(0, keepdim=True)
    second = second.float() - second.float().mean(0, keepdim=True)
    numerator = (first * second).sum(0)
    denominator = torch.sqrt(first.square().sum(0) * second.square().sum(0))
    return torch.where(denominator > 0, numerator / denominator, torch.nan)
