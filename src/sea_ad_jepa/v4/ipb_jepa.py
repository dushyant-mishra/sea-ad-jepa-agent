"""Information-preserving block JEPA mechanics for the bounded v4.1 study."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import NamedTuple

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.checkpoint import checkpoint

from .gene_tokenizer import GeneExpressionTokenizer
from .contracts import MECHANICS_CONTRACT
from .masking import keyed_mask_seed


class EncoderOutput(NamedTuple):
    gene_states: torch.Tensor
    cell_state: torch.Tensor
    minimum_denominator: torch.Tensor


@dataclass(frozen=True)
class CorrelationGraph:
    """Sparse symmetric graph used only to sample hidden target blocks."""

    neighbors: tuple[torch.Tensor, ...]
    weights: tuple[torch.Tensor, ...]
    top_k: int
    genes: int


@dataclass(frozen=True)
class TargetBlocks:
    hidden_mask: torch.Tensor
    indices: torch.Tensor
    member_mask: torch.Tensor
    fallback_counts: torch.Tensor


def build_train_pearson_graph(
    training_expression: torch.Tensor,
    *,
    top_k: int = 8,
    chunk_genes: int = 256,
) -> CorrelationGraph:
    """Build an absolute-Pearson top-k union graph from training expression only."""
    if training_expression.ndim != 2 or training_expression.shape[0] < 2:
        raise ValueError("training_expression must have shape [train_cells, genes]")
    if top_k < 1 or top_k >= training_expression.shape[1]:
        raise ValueError("top_k must be positive and smaller than the gene count")
    if not training_expression.is_floating_point() or not torch.isfinite(training_expression).all():
        raise ValueError("training_expression must be finite floating point")
    values = training_expression.float()
    values = values - values.mean(dim=0, keepdim=True)
    values = values / values.square().mean(dim=0, keepdim=True).sqrt().clamp_min(1e-6)
    cells, genes = values.shape
    directed_indices = torch.empty((genes, top_k), dtype=torch.int64)
    directed_weights = torch.empty((genes, top_k), dtype=torch.float32)
    compute = values.device
    for start in range(0, genes, chunk_genes):
        end = min(start + chunk_genes, genes)
        correlations = (values[:, start:end].T @ values) / cells
        correlations = correlations.abs()
        local = torch.arange(end - start, device=compute)
        correlations[local, torch.arange(start, end, device=compute)] = -torch.inf
        weights, indices = correlations.topk(top_k, dim=1, largest=True, sorted=True)
        directed_indices[start:end] = indices.cpu()
        directed_weights[start:end] = weights.cpu()
    adjacency: list[dict[int, float]] = [dict() for _ in range(genes)]
    for source in range(genes):
        for target, weight in zip(directed_indices[source].tolist(), directed_weights[source].tolist()):
            adjacency[source][target] = max(adjacency[source].get(target, 0.0), weight)
            adjacency[target][source] = max(adjacency[target].get(source, 0.0), weight)
    neighbors = []
    weights = []
    for row in adjacency:
        ordered = sorted(row.items(), key=lambda item: (-item[1], item[0]))
        neighbors.append(torch.tensor([item[0] for item in ordered], dtype=torch.int64))
        weights.append(torch.tensor([item[1] for item in ordered], dtype=torch.float32))
    return CorrelationGraph(tuple(neighbors), tuple(weights), top_k, genes)


def _block_sizes(hidden_count: int, block_count: int) -> list[int]:
    quotient, remainder = divmod(hidden_count, block_count)
    return [quotient + (index < remainder) for index in range(block_count)]


def sample_target_blocks(
    measurement_mask: torch.Tensor,
    graph: CorrelationGraph,
    *,
    production_seed: int,
    cell_indices: torch.Tensor,
    sample_pass: int,
    view_index: int,
    mask_fraction: float = 0.40,
    block_count: int = 16,
) -> TargetBlocks:
    """Create deterministic disjoint graph-expanded blocks with exact hidden union."""
    if measurement_mask.dtype is not torch.bool or measurement_mask.ndim != 2:
        raise ValueError("measurement_mask must be boolean [cells, genes]")
    if measurement_mask.shape[1] != graph.genes:
        raise ValueError("measurement mask and graph gene counts differ")
    if cell_indices.ndim != 1 or len(cell_indices) != len(measurement_mask):
        raise ValueError("cell_indices must contain one index per cell")
    if block_count < 1 or not 0.0 <= mask_fraction <= 1.0:
        raise ValueError("invalid block_count or mask_fraction")
    device = measurement_mask.device
    measured_cpu = measurement_mask.cpu()
    hidden = torch.zeros_like(measured_cpu)
    all_blocks: list[list[list[int]]] = []
    fallbacks = []
    maximum_size = 0
    for row in range(len(measured_cpu)):
        measured = torch.nonzero(measured_cpu[row], as_tuple=False).flatten().tolist()
        hidden_count = int(math.floor(mask_fraction * len(measured)))
        sizes = _block_sizes(hidden_count, block_count)
        maximum_size = max(maximum_size, max(sizes, default=0))
        generator = torch.Generator(device="cpu").manual_seed(keyed_mask_seed(
            production_seed=production_seed,
            cell_index=int(cell_indices[row]),
            sample_pass=sample_pass,
            view_index=view_index,
        ))
        ranking = torch.tensor(measured)[torch.randperm(len(measured), generator=generator)].tolist()
        available = set(measured)
        cursor = 0
        row_blocks: list[list[int]] = []
        fallback_count = 0
        for size in sizes:
            block: list[int] = []
            frontier: list[tuple[float, int]] = []
            frontier_best: dict[int, float] = {}

            def add_gene(gene: int) -> None:
                block.append(gene)
                available.remove(gene)
                hidden[row, gene] = True
                for neighbor, weight in zip(
                    graph.neighbors[gene].tolist(), graph.weights[gene].tolist()
                ):
                    if neighbor in available and weight > frontier_best.get(neighbor, -1.0):
                        frontier_best[neighbor] = weight
                        heapq.heappush(frontier, (-weight, neighbor))

            while cursor < len(ranking) and ranking[cursor] not in available:
                cursor += 1
            if size and cursor < len(ranking):
                add_gene(ranking[cursor])
                cursor += 1
            while len(block) < size:
                while frontier:
                    negative_weight, candidate = heapq.heappop(frontier)
                    if candidate not in available:
                        continue
                    if -negative_weight < frontier_best.get(candidate, -1.0):
                        continue
                    frontier_best.pop(candidate, None)
                    add_gene(candidate)
                    break
                else:
                    while cursor < len(ranking) and ranking[cursor] not in available:
                        cursor += 1
                    if cursor >= len(ranking):
                        raise RuntimeError("target-block fallback exhausted measured genes")
                    add_gene(ranking[cursor])
                    cursor += 1
                    fallback_count += 1
                    continue
                continue
            row_blocks.append(block)
        if sum(len(block) for block in row_blocks) != hidden_count:
            raise RuntimeError("target blocks do not match exact hidden count")
        all_blocks.append(row_blocks)
        fallbacks.append(fallback_count)
    indices = torch.full((len(all_blocks), block_count, maximum_size), -1, dtype=torch.int64)
    members = torch.zeros_like(indices, dtype=torch.bool)
    for row, blocks in enumerate(all_blocks):
        for block_index, block in enumerate(blocks):
            if block:
                indices[row, block_index, : len(block)] = torch.tensor(block)
                members[row, block_index, : len(block)] = True
    return TargetBlocks(
        hidden.to(device), indices.to(device), members.to(device),
        torch.tensor(fallbacks, dtype=torch.int64, device=device),
    )


def sample_uniform_target_blocks(
    measurement_mask: torch.Tensor,
    *,
    production_seed: int,
    cell_indices: torch.Tensor,
    sample_pass: int,
    view_index: int,
    mask_fraction: float = 0.40,
    block_count: int = 16,
) -> TargetBlocks:
    """Create deterministic graph-free blocks from measured genes only.

    This additive sampler intentionally accepts no expression matrix, graph,
    source identity, or dataset identity. It preserves the historical target
    block shape and exact hidden-union semantics while providing a scalable
    graph-free masking control.
    """
    if measurement_mask.dtype is not torch.bool or measurement_mask.ndim != 2:
        raise ValueError("measurement_mask must be boolean [cells, genes]")
    if cell_indices.ndim != 1 or len(cell_indices) != len(measurement_mask):
        raise ValueError("cell_indices must contain one index per cell")
    if block_count < 1 or not 0.0 <= mask_fraction <= 1.0:
        raise ValueError("invalid block_count or mask_fraction")
    device = measurement_mask.device
    measured_cpu = measurement_mask.cpu()
    hidden = torch.zeros_like(measured_cpu)
    row_blocks: list[list[list[int]]] = []
    maximum_size = 0
    for row in range(len(measured_cpu)):
        measured = torch.nonzero(measured_cpu[row], as_tuple=False).flatten()
        hidden_count = int(math.floor(mask_fraction * len(measured)))
        sizes = _block_sizes(hidden_count, block_count)
        maximum_size = max(maximum_size, max(sizes, default=0))
        generator = torch.Generator(device="cpu").manual_seed(keyed_mask_seed(
            production_seed=production_seed,
            cell_index=int(cell_indices[row]),
            sample_pass=sample_pass,
            view_index=view_index,
        ))
        ranking = measured[torch.randperm(len(measured), generator=generator)]
        cursor = 0
        blocks = []
        for size in sizes:
            block = ranking[cursor:cursor + size].tolist()
            blocks.append(block)
            if block:
                hidden[row, block] = True
            cursor += size
        if cursor != hidden_count:
            raise RuntimeError("uniform target blocks do not match exact hidden count")
        row_blocks.append(blocks)
    indices = torch.full((len(row_blocks), block_count, maximum_size), -1, dtype=torch.int64)
    members = torch.zeros_like(indices, dtype=torch.bool)
    for row, blocks in enumerate(row_blocks):
        for block_index, block in enumerate(blocks):
            if block:
                indices[row, block_index, :len(block)] = torch.tensor(block)
                members[row, block_index, :len(block)] = True
    return TargetBlocks(
        hidden.to(device), indices.to(device), members.to(device),
        torch.zeros(len(row_blocks), dtype=torch.int64, device=device),
    )


class KernelLinearAttention(nn.Module):
    """Four-head ELU+1 linear attention without an N-by-N score tensor."""

    def __init__(self, width: int = 160, heads: int = 4, eps: float = 1e-6) -> None:
        super().__init__()
        if width % heads:
            raise ValueError("width must be divisible by heads")
        self.width = width
        self.heads = heads
        self.head_dim = width // heads
        self.eps = eps
        self.query = nn.Linear(width, width)
        self.key = nn.Linear(width, width)
        self.value = nn.Linear(width, width)
        self.output = nn.Linear(width, width)

    def forward(self, tokens: torch.Tensor, valid_mask: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        if tokens.ndim != 3 or valid_mask.shape != tokens.shape[:2] or valid_mask.dtype is not torch.bool:
            raise ValueError("tokens and valid_mask must be [batch,tokens,width] and boolean [batch,tokens]")
        batch, count, _ = tokens.shape
        shape = (batch, count, self.heads, self.head_dim)
        projected_q = self.query(tokens).reshape(shape)
        projected_k = self.key(tokens).reshape(shape)
        projected_v = self.value(tokens).reshape(shape)
        with torch.autocast(device_type=tokens.device.type, enabled=False):
            q = (F.elu(projected_q.float()) + 1.0).transpose(1, 2)
            k = (F.elu(projected_k.float()) + 1.0).transpose(1, 2)
            v = projected_v.float().transpose(1, 2)
            valid = valid_mask[:, None, :, None]
            k = k * valid
            v = v * valid
            kv = torch.einsum("bhnd,bhne->bhde", k, v)
            ksum = k.sum(dim=2)
            denominator = torch.einsum("bhnd,bhd->bhn", q, ksum).clamp_min(self.eps)
            numerator = torch.einsum("bhnd,bhde->bhne", q, kv)
            output = (numerator / denominator[..., None]).transpose(1, 2).reshape(
                batch, count, self.width
            )
        return self.output(output.to(tokens.dtype)), denominator.amin()


class TokenPreservingBlock(nn.Module):
    def __init__(self, width: int = 160, heads: int = 4, ffn_width: int = 320, dropout: float = 0.10) -> None:
        super().__init__()
        self.attention_norm = nn.LayerNorm(width)
        self.attention = KernelLinearAttention(width, heads)
        self.attention_dropout = nn.Dropout(dropout)
        self.ffn_norm = nn.LayerNorm(width)
        self.ffn = nn.Sequential(
            nn.Linear(width, ffn_width), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(ffn_width, width), nn.Dropout(dropout),
        )

    def forward(self, tokens: torch.Tensor, valid_mask: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        attended, minimum = self.attention(self.attention_norm(tokens), valid_mask)
        tokens = tokens + self.attention_dropout(attended)
        return tokens + self.ffn(self.ffn_norm(tokens)), minimum


class IPBEncoder(nn.Module):
    """Six-block token-preserving encoder with one explicit cell token."""

    def __init__(
        self,
        *,
        width: int = 160,
        heads: int = 4,
        blocks: int = 6,
        ffn_width: int = 320,
        dropout: float = 0.10,
        gradient_checkpointing: bool = False,
        vocabulary_size: int = MECHANICS_CONTRACT.vocabulary_size,
    ) -> None:
        super().__init__()
        self.tokenizer = GeneExpressionTokenizer(
            vocabulary_size=vocabulary_size,
            width=width,
        )
        self.cell_token = nn.Parameter(torch.empty(1, 1, width))
        nn.init.normal_(self.cell_token, mean=0.0, std=0.02)
        self.blocks = nn.ModuleList([
            TokenPreservingBlock(width, heads, ffn_width, dropout) for _ in range(blocks)
        ])
        self.final_norm = nn.LayerNorm(width)
        self.gradient_checkpointing = gradient_checkpointing

    def forward(
        self,
        gene_ids: torch.Tensor,
        expression: torch.Tensor,
        measurement_mask: torch.Tensor,
        hidden_target_mask: torch.Tensor,
        view: str,
    ) -> EncoderOutput:
        if view == "student":
            gene_valid = measurement_mask & ~hidden_target_mask
        elif view == "target":
            gene_valid = measurement_mask
        else:
            raise ValueError("view must be student or target")
        if torch.any(~gene_valid.any(dim=1)):
            raise ValueError("every cell must have at least one valid gene")
        safe_expression = expression.masked_fill(~gene_valid, 0.0)
        gene_tokens = self.tokenizer(gene_ids, safe_expression)
        cell = self.cell_token.expand(len(expression), -1, -1)
        tokens = torch.cat((cell, gene_tokens), dim=1)
        valid = torch.cat((torch.ones(len(expression), 1, dtype=torch.bool, device=expression.device), gene_valid), dim=1)
        minima = []
        for block in self.blocks:
            if self.gradient_checkpointing and self.training:
                tokens, minimum = checkpoint(block, tokens, valid, use_reentrant=False)
            else:
                tokens, minimum = block(tokens, valid)
            minima.append(minimum)
        tokens = self.final_norm(tokens)
        return EncoderOutput(tokens[:, 1:], tokens[:, 0], torch.stack(minima).amin())


def gather_block_states(
    gene_states: torch.Tensor,
    blocks: TargetBlocks,
) -> torch.Tensor:
    safe = blocks.indices.clamp_min(0)
    batch = torch.arange(len(gene_states), device=gene_states.device)[:, None, None]
    gathered = gene_states[batch, safe]
    gathered = gathered * blocks.member_mask[..., None]
    means = gathered.sum(dim=2) / blocks.member_mask.sum(dim=2, keepdim=True).clamp_min(1)
    return F.layer_norm(means, (means.shape[-1],))


class BlockPredictor(nn.Module):
    """Identity-only block queries attending to visible states plus z_cell."""

    def __init__(self, identity_dim: int = 48, width: int = 160, heads: int = 4) -> None:
        super().__init__()
        self.identity_projection = nn.Linear(identity_dim, width)
        self.block_mask = nn.Parameter(torch.empty(1, 1, width))
        nn.init.normal_(self.block_mask, mean=0.0, std=0.02)
        self.cross_attention = nn.MultiheadAttention(width, heads, batch_first=True)
        self.norm = nn.LayerNorm(width)
        self.ffn = nn.Sequential(nn.Linear(width, 320), nn.GELU(), nn.Linear(320, width))
        self.output_norm = nn.LayerNorm(width)

    def block_queries(self, identity_embedding: nn.Embedding, blocks: TargetBlocks) -> torch.Tensor:
        safe = blocks.indices.clamp_min(0)
        identities = identity_embedding(safe)
        identities = identities * blocks.member_mask[..., None]
        mean_identity = identities.sum(dim=2) / blocks.member_mask.sum(dim=2, keepdim=True).clamp_min(1)
        return self.identity_projection(mean_identity) + self.block_mask

    def forward(
        self,
        identity_embedding: nn.Embedding,
        blocks: TargetBlocks,
        student_gene_states: torch.Tensor,
        student_cell_state: torch.Tensor,
        student_valid_genes: torch.Tensor,
    ) -> torch.Tensor:
        queries = self.block_queries(identity_embedding, blocks)
        memory = torch.cat((student_cell_state[:, None], student_gene_states), dim=1)
        valid = torch.cat((torch.ones(len(memory), 1, dtype=torch.bool, device=memory.device), student_valid_genes), dim=1)
        attended, _ = self.cross_attention(
            queries, memory, memory, key_padding_mask=~valid, need_weights=False
        )
        state = queries + attended
        return self.output_norm(state + self.ffn(self.norm(state)))


class GeneAnchorDecoder(nn.Module):
    """Two bilinear heads that decode hidden genes only through z_cell."""

    def __init__(self, identity_dim: int = 48, width: int = 160) -> None:
        super().__init__()
        self.z_value = nn.Linear(width, width)
        self.gene_value = nn.Linear(identity_dim, width)
        self.z_detect = nn.Linear(width, width)
        self.gene_detect = nn.Linear(identity_dim, width)
        self.scale = math.sqrt(width)

    def forward(
        self,
        cell_state: torch.Tensor,
        identity_embedding: nn.Embedding,
        hidden_gene_ids: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        identities = identity_embedding(hidden_gene_ids)
        value = torch.einsum("bd,bhd->bh", self.z_value(cell_state), self.gene_value(identities)) / self.scale
        detection = torch.einsum("bd,bhd->bh", self.z_detect(cell_state), self.gene_detect(identities)) / self.scale
        return value, detection


def hidden_gene_indices(hidden_mask: torch.Tensor) -> torch.Tensor:
    counts = hidden_mask.sum(dim=1)
    if not torch.all(counts == counts[0]):
        raise ValueError("hidden_gene_indices requires equal hidden counts per batch")
    return torch.stack([torch.nonzero(row, as_tuple=False).flatten() for row in hidden_mask])


def gene_anchor_loss(
    predicted_standardized: torch.Tensor,
    detection_logits: torch.Tensor,
    target_standardized: torch.Tensor,
    detected: torch.Tensor,
) -> dict[str, torch.Tensor]:
    if not (
        predicted_standardized.shape == detection_logits.shape
        == target_standardized.shape == detected.shape
    ):
        raise ValueError("all hidden-gene anchor tensors must share shape")
    value = F.huber_loss(predicted_standardized, target_standardized, delta=1.0)
    detection = F.binary_cross_entropy_with_logits(detection_logits, detected.float())
    return {"value": value, "detection": detection, "gene": 0.5 * value + 0.5 * detection}


def block_jepa_loss(predicted: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    if predicted.shape != target.shape:
        raise ValueError("predicted and target block states must share shape")
    return F.mse_loss(predicted, target.detach())
