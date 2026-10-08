"""Context-adaptive Gaussian belief mechanics for the bounded RBB-JEPA probe."""

from __future__ import annotations

import math
from typing import NamedTuple

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.checkpoint import checkpoint

from .gene_tokenizer import GeneExpressionTokenizer
from .ipb_jepa import TokenPreservingBlock


R_MAX = 32


def cross_replicate_targets(
    x_a: torch.Tensor,
    x_b: torch.Tensor,
    analysis: torch.Tensor,
    mean: torch.Tensor,
    hidden_mask: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return A-visible->B-hidden and B-visible->A-hidden residual targets."""
    hidden = hidden_mask.to(x_a.dtype)
    target_ab = ((x_b.float() - mean.float()) * hidden) @ analysis.float().T
    target_ba = ((x_a.float() - mean.float()) * hidden) @ analysis.float().T
    return target_ab, target_ba


def random_mask_bank(
    *, genes: int = 4096, hidden_count: int = 1638, views: int = 128, seed: int = 8114001
) -> torch.Tensor:
    rows = []
    for view in range(views):
        generator = torch.Generator().manual_seed(seed + 1009 * view + 17)
        hidden = torch.zeros(genes, dtype=torch.bool)
        hidden[torch.randperm(genes, generator=generator)[:hidden_count]] = True
        rows.append(hidden)
    result = torch.stack(rows)
    if not torch.all(result.sum(1) == hidden_count):
        raise RuntimeError("random mask bank violated exact hidden count")
    return result


def nested_visibility_masks(
    order: torch.Tensor,
    fractions: tuple[float, ...] = (1.0, 0.8, 0.6, 0.4),
) -> dict[float, torch.Tensor]:
    genes = len(order)
    result: dict[float, torch.Tensor] = {}
    for fraction in fractions:
        count = int(round(fraction * genes))
        mask = torch.zeros(genes, dtype=torch.bool, device=order.device)
        mask[order[:count]] = True
        result[fraction] = mask
    return result


def mask_context_features(
    analysis: torch.Tensor,
    hidden_mask: torch.Tensor,
    prior_diagonal: torch.Tensor,
    prior_low_rank: torch.Tensor,
) -> torch.Tensor:
    """Mask-only RepPCA and frozen-prior context; no expression values enter."""
    selected = analysis.float()[:, hidden_mask]
    signed = selected.sum(1) / math.sqrt(max(int(hidden_mask.sum()), 1))
    squared = selected.square().sum(1)
    log_variance = prior_diagonal.float().clamp_min(1.0e-8).log()
    correlated_energy = prior_low_rank.float().square().sum(0)
    return torch.cat((signed, squared, log_variance, correlated_energy))


class RBBOutput(NamedTuple):
    molecular_evidence_tokens: torch.Tensor
    visible_state: torch.Tensor
    posterior_missing_mean: torch.Tensor
    belief_mean: torch.Tensor
    conditional_diagonal: torch.Tensor
    conditional_low_rank: torch.Tensor
    measurement_noise_diagonal: torch.Tensor
    total_diagonal: torch.Tensor
    total_low_rank: torch.Tensor
    correlated_activation_amplitudes: torch.Tensor
    evidence_mean: torch.Tensor
    evidence_diagonal: torch.Tensor
    evidence_low_rank: torch.Tensor
    minimum_attention_denominator: torch.Tensor


class MolecularEvidenceLedger(nn.Module):
    """Six-block token ledger with no cell token, Perceiver, or pooling path."""

    def __init__(
        self,
        *,
        vocabulary_size: int = 4096,
        width: int = 160,
        heads: int = 4,
        blocks: int = 6,
        ffn_width: int = 320,
        dropout: float = 0.10,
        gradient_checkpointing: bool = True,
    ) -> None:
        super().__init__()
        self.vocabulary_size = vocabulary_size
        self.width = width
        self.tokenizer = GeneExpressionTokenizer(vocabulary_size=vocabulary_size, width=width)
        self.measurement_state = nn.Embedding(2, width)
        self.blocks = nn.ModuleList([
            TokenPreservingBlock(width, heads, ffn_width, dropout) for _ in range(blocks)
        ])
        self.final_norm = nn.LayerNorm(width)
        self.gradient_checkpointing = gradient_checkpointing

    def forward(
        self,
        gene_ids: torch.Tensor,
        expression: torch.Tensor,
        visible_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if visible_mask.dtype is not torch.bool or visible_mask.shape != expression.shape:
            raise ValueError("visible_mask must be boolean and match expression")
        if not torch.all(visible_mask.any(1)):
            raise ValueError("every cell requires visible molecular evidence")
        safe_expression = expression.masked_fill(~visible_mask, 0.0)
        states = self.tokenizer(gene_ids, safe_expression)
        states = states + self.measurement_state(visible_mask.long())
        minima: list[torch.Tensor] = []
        for block in self.blocks:
            if self.gradient_checkpointing and self.training:
                states, minimum = checkpoint(block, states, visible_mask, use_reentrant=False)
            else:
                states, minimum = block(states, visible_mask)
            minima.append(minimum)
        return self.final_norm(states), torch.stack(minima).amin()


def _inverse_correction(
    diagonal: torch.Tensor,
    low_rank: torch.Tensor,
    epsilon: float = 1.0e-6,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return D^-1 and W where (D+UU')^-1 = D^-1-WW'."""
    diagonal = diagonal.float().clamp_min(epsilon)
    low_rank = low_rank.float()
    inverse = diagonal.reciprocal()
    scaled = inverse[..., :, None] * low_rank
    rank = low_rank.shape[-1]
    eye = torch.eye(rank, device=low_rank.device, dtype=torch.float32)
    middle = eye + low_rank.transpose(-1, -2) @ scaled
    chol = torch.linalg.cholesky(middle)
    correction = torch.linalg.solve_triangular(
        chol, scaled.transpose(-1, -2), upper=False
    ).transpose(-1, -2)
    return inverse, correction


def lrd_solve(
    values: torch.Tensor,
    diagonal: torch.Tensor,
    low_rank: torch.Tensor,
) -> torch.Tensor:
    inverse, correction = _inverse_correction(diagonal, low_rank)
    scaled = values.float() * inverse
    return scaled - torch.einsum(
        "bdr,br->bd", correction, torch.einsum("bdr,bd->br", correction, values.float())
    )


def fuse_gaussian_beliefs(
    evidence_mean: torch.Tensor,
    prior_diagonal: torch.Tensor,
    prior_low_rank: torch.Tensor,
    evidence_diagonal: torch.Tensor,
    evidence_low_rank: torch.Tensor,
    epsilon: float = 1.0e-6,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Fuse zero-mean prior and neural evidence without dense 160x160 inverses."""
    with torch.autocast(device_type=evidence_mean.device.type, enabled=False):
        batch = len(evidence_mean)
        pd = prior_diagonal.float().expand(batch, -1)
        pu = prior_low_rank.float().expand(batch, -1, -1)
        ed = evidence_diagonal.float()
        eu = evidence_low_rank.float()
        prior_inverse, prior_correction = _inverse_correction(pd, pu, epsilon)
        evidence_inverse, evidence_correction = _inverse_correction(ed, eu, epsilon)
        base_precision = prior_inverse + evidence_inverse
        base_covariance = base_precision.reciprocal()
        correction = torch.cat((prior_correction, evidence_correction), dim=-1)
        rank = correction.shape[-1]
        eye = torch.eye(rank, device=correction.device, dtype=torch.float32)
        middle = eye - correction.transpose(-1, -2) @ (
            base_covariance[..., :, None] * correction
        )
        chol = torch.linalg.cholesky(middle)
        posterior_low_rank = torch.linalg.solve_triangular(
            chol,
            (base_covariance[..., :, None] * correction).transpose(-1, -2),
            upper=False,
        ).transpose(-1, -2)
        evidence_information = evidence_mean.float() * evidence_inverse
        evidence_information = evidence_information - torch.einsum(
            "bdr,br->bd",
            evidence_correction,
            torch.einsum("bdr,bd->br", evidence_correction, evidence_mean.float()),
        )
        posterior_mean = base_covariance * evidence_information
        posterior_mean = posterior_mean + torch.einsum(
            "bdr,br->bd",
            posterior_low_rank,
            torch.einsum("bdr,bd->br", posterior_low_rank, evidence_information),
        )
    return posterior_mean, base_covariance, posterior_low_rank


def structured_gaussian_terms(
    residual: torch.Tensor,
    diagonal: torch.Tensor,
    low_rank: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Per-example NLL, Mahalanobis distance, and log determinant."""
    with torch.autocast(device_type=residual.device.type, enabled=False):
        residual = residual.float()
        diagonal = diagonal.float().clamp_min(1.0e-6)
        low_rank = low_rank.float()
        inverse, correction = _inverse_correction(diagonal, low_rank)
        quadratic = (residual.square() * inverse).sum(-1)
        projection = torch.einsum("bdr,bd->br", correction, residual)
        quadratic = quadratic - projection.square().sum(-1)
        scaled = inverse[..., :, None] * low_rank
        rank = low_rank.shape[-1]
        eye = torch.eye(rank, device=low_rank.device, dtype=torch.float32)
        middle = eye + low_rank.transpose(-1, -2) @ scaled
        chol = torch.linalg.cholesky(middle)
        logdet = diagonal.log().sum(-1) + 2.0 * torch.log(
            torch.diagonal(chol, dim1=-2, dim2=-1)
        ).sum(-1)
        nll = 0.5 * (residual.shape[-1] * math.log(2.0 * math.pi) + logdet + quadratic)
    return nll, quadratic, logdet


class RBBAdaptiveBelief(nn.Module):
    """Token-preserving adaptive diagonal-plus-correlated Gaussian belief model."""

    def __init__(
        self,
        *,
        vocabulary_size: int = 4096,
        width: int = 160,
        rank: int = R_MAX,
        mask_context_dim: int = 512,
        diagonal_precision_bias: float = -9.0,
        correlated_amplitude_bias: float = -4.0,
        gradient_checkpointing: bool = True,
    ) -> None:
        super().__init__()
        if rank != R_MAX:
            raise ValueError(f"RBB correlated capacity is frozen at R_MAX={R_MAX}")
        self.width = width
        self.rank = rank
        self.ledger = MolecularEvidenceLedger(
            vocabulary_size=vocabulary_size,
            width=width,
            gradient_checkpointing=gradient_checkpointing,
        )
        self.mask_context = nn.Sequential(
            nn.Linear(mask_context_dim, 320), nn.GELU(), nn.Linear(320, width)
        )
        self.evidence_norm = nn.LayerNorm(width)
        self.evidence_hidden = nn.Sequential(nn.Linear(width, 320), nn.GELU())
        self.evidence_output = nn.Linear(320, 2 * width + rank)
        directions = torch.randn(width, rank, generator=torch.Generator().manual_seed(8114001 + 919))
        self.correlated_directions = nn.Parameter(torch.linalg.qr(directions, mode="reduced").Q)
        with torch.no_grad():
            self.evidence_output.bias.zero_()
            self.evidence_output.bias[width:2 * width].fill_(diagonal_precision_bias)
            self.evidence_output.bias[2 * width:].fill_(correlated_amplitude_bias)
            self.evidence_output.weight[width:].zero_()
        self.molecular_ledger_frozen = False

    def freeze_molecular_ledger(self) -> None:
        """Freeze and firewall every parameter upstream of the belief reasoner."""
        for parameter in self.ledger.parameters():
            parameter.requires_grad_(False)
        self.molecular_ledger_frozen = True

    def belief_parameters(self):
        """Yield only downstream belief parameters for explicit optimizer groups."""
        for name, parameter in self.named_parameters():
            if not name.startswith("ledger.") and parameter.requires_grad:
                yield parameter

    def encode_molecular_ledger(
        self,
        gene_ids: torch.Tensor,
        expression: torch.Tensor,
        visible_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if self.molecular_ledger_frozen:
            with torch.no_grad():
                tokens, minimum = self.ledger(gene_ids, expression, visible_mask)
            return tokens.detach(), minimum.detach()
        return self.ledger(gene_ids, expression, visible_mask)

    def normalized_directions(self) -> torch.Tensor:
        return F.normalize(self.correlated_directions.float(), dim=0)

    def forward(
        self,
        gene_ids: torch.Tensor,
        expression: torch.Tensor,
        visible_mask: torch.Tensor,
        visible_state: torch.Tensor,
        mask_context: torch.Tensor,
        prior_diagonal: torch.Tensor,
        prior_low_rank: torch.Tensor,
        noise_diagonal: torch.Tensor,
        *,
        diagonalize_evidence: bool = False,
    ) -> RBBOutput:
        tokens, minimum = self.encode_molecular_ledger(gene_ids, expression, visible_mask)
        context = self.mask_context(mask_context.float())
        counts = visible_mask.sum(1)
        if not torch.all(counts == counts[0]):
            raise ValueError("bounded probe requires one exact-count mask per microbatch")
        visible_tokens = tokens[visible_mask].reshape(len(tokens), int(counts[0]), self.width)
        evidence = self.evidence_output(
            self.evidence_hidden(self.evidence_norm(visible_tokens + context[:, None, :]))
        ).float()
        proposed, precision_logits, correlation_logits = torch.split(
            evidence, (self.width, self.width, self.rank), dim=-1
        )
        precision = F.softplus(precision_logits)
        strength = precision.mean(-1)
        weights = strength / strength.sum(1, keepdim=True).clamp_min(1.0e-12)
        evidence_mean = torch.einsum("bg,bgd->bd", weights, proposed)
        evidence_precision = precision.sum(1).clamp_min(1.0e-6)
        evidence_diagonal = evidence_precision.reciprocal()
        global_logits = torch.einsum("bg,bgr->br", weights, correlation_logits)
        amplitudes = F.softplus(global_logits)
        directions = self.normalized_directions()
        evidence_low_rank = directions[None, :, :] * amplitudes[:, None, :]
        if diagonalize_evidence:
            evidence_low_rank = torch.zeros_like(evidence_low_rank)
        posterior_mean, conditional_diagonal, conditional_low_rank = fuse_gaussian_beliefs(
            evidence_mean,
            prior_diagonal,
            prior_low_rank,
            evidence_diagonal,
            evidence_low_rank,
        )
        noise = noise_diagonal.float().expand(len(tokens), -1)
        total_diagonal = conditional_diagonal + noise
        return RBBOutput(
            tokens,
            visible_state.float(),
            posterior_mean,
            visible_state.float() + posterior_mean,
            conditional_diagonal,
            conditional_low_rank,
            noise,
            total_diagonal,
            conditional_low_rank,
            amplitudes,
            evidence_mean,
            evidence_diagonal,
            evidence_low_rank,
            minimum,
        )


def rbb_nll(output: RBBOutput, hidden_residual_target: torch.Tensor) -> torch.Tensor:
    residual = hidden_residual_target.float() - output.posterior_missing_mean.float()
    nll, _, _ = structured_gaussian_terms(
        residual, output.total_diagonal, output.total_low_rank
    )
    return nll.mean() / residual.shape[-1]


def dense_covariance(diagonal: torch.Tensor, low_rank: torch.Tensor) -> torch.Tensor:
    return torch.diag_embed(diagonal.float()) + low_rank.float() @ low_rank.float().transpose(-1, -2)
