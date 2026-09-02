"""Residual latent completion mechanics for the bounded Stage81A3 RLC-CD probe."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import NamedTuple

import torch
import torch.nn.functional as F
from torch import nn

from .gene_tokenizer import GeneExpressionTokenizer
from .ipb_jepa import TokenPreservingBlock
from .masking import keyed_mask_seed


class TokenEncoderOutput(NamedTuple):
    gene_states: torch.Tensor
    minimum_denominator: torch.Tensor


@dataclass(frozen=True)
class WhitenedPCABasis:
    mean: torch.Tensor
    components: torch.Tensor
    eigenvalues: torch.Tensor
    whitened: torch.Tensor
    epsilon: float

    def to(self, device: torch.device) -> "WhitenedPCABasis":
        return WhitenedPCABasis(
            self.mean.to(device), self.components.to(device), self.eigenvalues.to(device),
            self.whitened.to(device), self.epsilon,
        )

    def ordinary(self, values: torch.Tensor) -> torch.Tensor:
        return (values.float() - self.mean) @ self.components.T

    def transform(self, values: torch.Tensor) -> torch.Tensor:
        return (values.float() - self.mean) @ self.whitened.T

    def inverse_whitening(self, values: torch.Tensor) -> torch.Tensor:
        return values.float() * torch.sqrt(self.eigenvalues + self.epsilon)

    def reconstruct(self, ordinary_coordinates: torch.Tensor) -> torch.Tensor:
        return self.mean + ordinary_coordinates.float() @ self.components

    def contribution(self, centered_values: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        return (centered_values.float() * mask.float()) @ self.whitened.T


@dataclass(frozen=True)
class MaskBank:
    visible: torch.Tensor
    hidden: torch.Tensor
    block_masks: torch.Tensor
    block_indices: torch.Tensor
    block_members: torch.Tensor
    fallback_counts: torch.Tensor

    def to(self, device: torch.device) -> "MaskBank":
        return MaskBank(*(value.to(device) for value in (
            self.visible, self.hidden, self.block_masks, self.block_indices,
            self.block_members, self.fallback_counts,
        )))


def fit_whitened_pca_gram(
    training_values: torch.Tensor,
    *,
    components: int = 160,
    epsilon: float = 1.0e-6,
) -> WhitenedPCABasis:
    """Fit PCA through the sample Gram matrix without evaluation-cell access."""
    if training_values.ndim != 2 or components > min(training_values.shape):
        raise ValueError("invalid training matrix or component count")
    values = training_values.detach().float()
    mean = values.mean(0)
    centered = values - mean
    gram = centered @ centered.T
    eigenvalues, eigenvectors = torch.linalg.eigh(gram)
    order = torch.argsort(eigenvalues, descending=True)[:components]
    eigenvalues = eigenvalues[order].clamp_min(epsilon)
    left = eigenvectors[:, order]
    singular = torch.sqrt(eigenvalues)
    p = (left.T @ centered) / singular[:, None]
    p = F.normalize(p, dim=1)
    whitened = p / torch.sqrt(eigenvalues + epsilon)[:, None]
    return WhitenedPCABasis(mean, p, eigenvalues, whitened, epsilon)


def gpu_topk_absolute_correlation(
    training_values: torch.Tensor,
    *,
    top_k: int = 8,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return directed top-k absolute Pearson neighbors using one GPU GEMM."""
    values = training_values.detach().float()
    values = values - values.mean(0, keepdim=True)
    values = values / values.std(0, unbiased=True, keepdim=True).clamp_min(1.0e-6)
    correlation = ((values.T @ values) / (len(values) - 1)).abs()
    correlation.fill_diagonal_(-torch.inf)
    weights, indices = correlation.topk(top_k, dim=1, largest=True, sorted=True)
    return indices, weights


def _block_sizes(hidden: int, blocks: int) -> list[int]:
    quotient, remainder = divmod(hidden, blocks)
    return [quotient + (index < remainder) for index in range(blocks)]


def build_mask_bank(
    neighbors: torch.Tensor,
    weights: torch.Tensor,
    *,
    views: int = 256,
    genes: int = 4096,
    hidden_count: int = 1638,
    blocks: int = 4,
    seed: int = 8114001,
) -> MaskBank:
    """Build all graph-expanded masks once; no traversal is needed during training."""
    neighbors = neighbors.detach().cpu()
    weights = weights.detach().cpu()
    sizes = _block_sizes(hidden_count, blocks)
    maximum = max(sizes)
    hidden_bank = torch.zeros(views, genes, dtype=torch.bool)
    block_masks = torch.zeros(views, blocks, genes, dtype=torch.bool)
    indices = torch.full((views, blocks, maximum), -1, dtype=torch.long)
    members = torch.zeros_like(indices, dtype=torch.bool)
    fallbacks = torch.zeros(views, dtype=torch.long)
    all_genes = torch.arange(genes)
    for view in range(views):
        generator = torch.Generator().manual_seed(keyed_mask_seed(
            production_seed=seed, cell_index=view, sample_pass=0, view_index=view,
        ))
        ranking = all_genes[torch.randperm(genes, generator=generator)].tolist()
        available = set(range(genes))
        cursor = 0
        for block, size in enumerate(sizes):
            selected: list[int] = []
            frontier: list[tuple[float, int]] = []
            best: dict[int, float] = {}

            def add_gene(gene: int) -> None:
                selected.append(gene)
                available.remove(gene)
                hidden_bank[view, gene] = True
                block_masks[view, block, gene] = True
                for neighbor, weight in zip(neighbors[gene].tolist(), weights[gene].tolist()):
                    if neighbor in available and weight > best.get(neighbor, -1.0):
                        best[neighbor] = weight
                        heapq.heappush(frontier, (-weight, neighbor))

            while ranking[cursor] not in available:
                cursor += 1
            add_gene(ranking[cursor]); cursor += 1
            while len(selected) < size:
                while frontier:
                    negative, candidate = heapq.heappop(frontier)
                    if candidate in available and -negative >= best.get(candidate, -1.0):
                        best.pop(candidate, None)
                        add_gene(candidate)
                        break
                else:
                    while ranking[cursor] not in available:
                        cursor += 1
                    add_gene(ranking[cursor]); cursor += 1
                    fallbacks[view] += 1
            indices[view, block, :size] = torch.tensor(selected)
            members[view, block, :size] = True
    visible = ~hidden_bank
    if not torch.all(hidden_bank.sum(1) == hidden_count):
        raise RuntimeError("mask bank hidden-count contract failed")
    if not torch.equal(block_masks.sum(1).bool(), hidden_bank):
        raise RuntimeError("mask bank block-union contract failed")
    if torch.any(block_masks.sum(1) > 1):
        raise RuntimeError("mask bank blocks overlap")
    return MaskBank(visible, hidden_bank, block_masks, indices, members, fallbacks)


class RLCGeneEncoder(nn.Module):
    """Token-preserving encoder with no cell token and no pooling path."""

    def __init__(
        self, *, width: int = 160, heads: int = 4, blocks: int = 6,
        ffn_width: int = 320, dropout: float = 0.10,
    ) -> None:
        super().__init__()
        self.tokenizer = GeneExpressionTokenizer(width=width)
        self.blocks = nn.ModuleList([
            TokenPreservingBlock(width, heads, ffn_width, dropout) for _ in range(blocks)
        ])
        self.final_norm = nn.LayerNorm(width)

    def forward(
        self,
        gene_ids: torch.Tensor,
        expression: torch.Tensor,
        visible_mask: torch.Tensor,
    ) -> TokenEncoderOutput:
        safe_expression = expression.masked_fill(~visible_mask, 0.0)
        states = self.tokenizer(gene_ids, safe_expression)
        minima = []
        for block in self.blocks:
            states, minimum = block(states, visible_mask)
            minima.append(minimum)
        states = self.final_norm(states).masked_fill(~visible_mask[..., None], 0.0)
        return TokenEncoderOutput(states, torch.stack(minima).amin())


class ResidualBlockPredictor(nn.Module):
    def __init__(self, *, identity_dim: int = 48, width: int = 160, heads: int = 4) -> None:
        super().__init__()
        self.identity_projection = nn.Linear(identity_dim, width)
        self.basis_projection = nn.Linear(width, width)
        self.block_mask = nn.Parameter(torch.empty(1, 1, width))
        nn.init.normal_(self.block_mask, std=0.02)
        self.query_norm = nn.LayerNorm(width)
        self.cross_attention = nn.MultiheadAttention(width, heads, batch_first=True)
        self.ffn_norm = nn.LayerNorm(width)
        self.ffn = nn.Sequential(nn.Linear(width, 320), nn.GELU(), nn.Linear(320, width))
        self.output_norm = nn.LayerNorm(width)

    def block_queries(
        self,
        identity_embedding: nn.Embedding,
        block_indices: torch.Tensor,
        block_members: torch.Tensor,
        basis_signatures: torch.Tensor,
        causal_context: torch.Tensor | None = None,
    ) -> torch.Tensor:
        safe = block_indices.clamp_min(0)
        identities = identity_embedding(safe) * block_members[..., None]
        means = identities.sum(2) / block_members.sum(2, keepdim=True).clamp_min(1)
        queries = self.identity_projection(means) + self.basis_projection(basis_signatures)
        queries = queries + self.block_mask
        if causal_context is not None:
            queries = queries + causal_context[:, None]
        return self.query_norm(queries)

    def forward(
        self,
        identity_embedding: nn.Embedding,
        block_indices: torch.Tensor,
        block_members: torch.Tensor,
        basis_signatures: torch.Tensor,
        visible_states: torch.Tensor,
        visible_mask: torch.Tensor,
        causal_context: torch.Tensor | None = None,
    ) -> torch.Tensor:
        queries = self.block_queries(
            identity_embedding, block_indices, block_members, basis_signatures,
            causal_context,
        )
        attended, _ = self.cross_attention(
            queries, visible_states, visible_states,
            key_padding_mask=~visible_mask, need_weights=False,
        )
        states = queries + attended
        return self.output_norm(states + self.ffn(self.ffn_norm(states)))


class RLCModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoder = RLCGeneEncoder()
        self.predictor = ResidualBlockPredictor()

    def forward(
        self,
        gene_ids: torch.Tensor,
        expression: torch.Tensor,
        visible_mask: torch.Tensor,
        block_indices: torch.Tensor,
        block_members: torch.Tensor,
        basis_signatures: torch.Tensor,
        u_visible: torch.Tensor,
        causal_context: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        encoded = self.encoder(gene_ids, expression, visible_mask)
        predicted = self.predictor(
            self.encoder.tokenizer.gene_identity, block_indices, block_members,
            basis_signatures, encoded.gene_states, visible_mask, causal_context,
        )
        return u_visible + predicted.sum(1), predicted, encoded.minimum_denominator


class CausalAuxiliary(nn.Module):
    """Learned latent mechanism graph with no true-DAG input surface."""

    def __init__(self, width: int = 160, mechanisms: int = 12) -> None:
        super().__init__()
        self.mechanisms = mechanisms
        self.mechanism = nn.Linear(width, mechanisms)
        self.response = nn.Linear(mechanisms, width)
        self.structural_context = nn.Linear(mechanisms, width)
        self.adjacency_raw = nn.Parameter(torch.empty(mechanisms, mechanisms))
        nn.init.normal_(self.adjacency_raw, std=0.01)
        self.register_buffer("off_diagonal", ~torch.eye(mechanisms, dtype=torch.bool))

    def adjacency(self) -> torch.Tensor:
        return self.off_diagonal * (0.5 * torch.tanh(self.adjacency_raw))

    def propagate(self, intervention: torch.Tensor) -> torch.Tensor:
        adjacency = self.adjacency()
        total = intervention
        term = intervention
        for _ in range(11):
            term = term @ adjacency
            total = total + term
        return total

    def context(self, u_visible: torch.Tensor) -> torch.Tensor:
        mechanisms = self.mechanism(u_visible)
        return self.structural_context(self.propagate(mechanisms))

    def acyclicity(self) -> torch.Tensor:
        adjacency = self.adjacency().float()
        return torch.trace(torch.matrix_exp(adjacency * adjacency)) - self.mechanisms


def rlc_loss(
    completed: torch.Tensor,
    predicted_blocks: torch.Tensor,
    full: torch.Tensor,
    true_blocks: torch.Tensor,
) -> dict[str, torch.Tensor]:
    state = F.smooth_l1_loss(completed, full, beta=1.0)
    block = F.smooth_l1_loss(predicted_blocks, true_blocks, beta=1.0)
    return {"state": state, "block": block, "rlc": state + block}


def finite_causal_response(
    adjacency: torch.Tensor,
    intervention_node: torch.Tensor,
    intervention_delta: torch.Tensor,
) -> torch.Tensor:
    intervention = F.one_hot(intervention_node, adjacency.shape[0]).float()
    intervention = intervention * intervention_delta[:, None]
    total = intervention
    term = intervention
    for _ in range(11):
        term = term @ adjacency
        total = total + term
    return total
