"""Evidence-earned RBB core with diagonal neural evidence uncertainty."""

from __future__ import annotations

from typing import NamedTuple

import torch
import torch.nn.functional as F
from torch import nn

from .measurement_state import MeasurementState
from .observation_calibration import apply_observation_calibration
from .rbb_adaptive import (
    R_MAX,
    MolecularEvidenceLedger,
    fuse_gaussian_beliefs,
)


class RBBCoreOutput(NamedTuple):
    molecular_evidence_tokens: torch.Tensor
    measurement_mask: torch.Tensor
    observed_mask: torch.Tensor
    structural_unmeasured_mask: torch.Tensor
    foundation_support_mask: torch.Tensor
    visible_state: torch.Tensor
    posterior_missing_mean: torch.Tensor
    belief_mean: torch.Tensor
    raw_conditional_diagonal: torch.Tensor
    raw_conditional_low_rank: torch.Tensor
    measurement_noise_diagonal: torch.Tensor
    raw_total_diagonal: torch.Tensor
    raw_total_low_rank: torch.Tensor
    calibration_regime: str
    calibration_scale: float
    calibrated_total_diagonal: torch.Tensor
    calibrated_total_low_rank: torch.Tensor
    evidence_mean: torch.Tensor
    evidence_diagonal: torch.Tensor
    minimum_attention_denominator: torch.Tensor


class RBBCore(nn.Module):
    """Frozen molecular ledger plus mean/diagonal-evidence Gaussian belief reasoner."""

    def __init__(
        self,
        *,
        vocabulary_size: int = 4096,
        width: int = 160,
        mask_context_dim: int = 512,
        gradient_checkpointing: bool = True,
    ) -> None:
        super().__init__()
        self.width = width
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
        self.evidence_output = nn.Linear(320, 2 * width)
        self.freeze_molecular_ledger()

    def freeze_molecular_ledger(self) -> None:
        for parameter in self.ledger.parameters():
            parameter.requires_grad_(False)

    def encode_molecular_ledger(
        self,
        gene_ids: torch.Tensor,
        expression: torch.Tensor,
        observed_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        with torch.no_grad():
            tokens, minimum = self.ledger(gene_ids, expression, observed_mask)
        return tokens.detach(), minimum.detach()

    def forward(
        self,
        gene_ids: torch.Tensor,
        expression: torch.Tensor,
        measurement_state: MeasurementState,
        visible_state: torch.Tensor,
        mask_context: torch.Tensor,
        prior_diagonal: torch.Tensor,
        prior_low_rank: torch.Tensor,
        noise_diagonal: torch.Tensor,
        *,
        calibration_regime: str = "ordinary_raw",
        calibration_scale: float = 1.0,
    ) -> RBBCoreOutput:
        measurement_state.assert_foundation_inference_supported()
        observed = measurement_state.observed_mask
        sanitized = measurement_state.sanitized_expression(expression)
        if not torch.all(observed.sum(1) == observed.sum(1)[0]):
            raise ValueError("RBB core requires one exact-count observation mask per microbatch")
        tokens, minimum = self.encode_molecular_ledger(gene_ids, sanitized, observed)
        context = self.mask_context(mask_context.float())
        count = int(observed.sum(1)[0])
        visible_tokens = tokens[observed].reshape(len(tokens), count, self.width)
        evidence = self.evidence_output(
            self.evidence_hidden(self.evidence_norm(visible_tokens + context[:, None, :]))
        ).float()
        proposed, precision_logits = torch.split(evidence, (self.width, self.width), dim=-1)
        precision = F.softplus(precision_logits)
        strength = precision.mean(-1)
        weights = strength / strength.sum(1, keepdim=True).clamp_min(1.0e-12)
        evidence_mean = torch.einsum("bg,bgd->bd", weights, proposed)
        evidence_diagonal = precision.sum(1).clamp_min(1.0e-6).reciprocal()
        zero_evidence_low_rank = torch.zeros(
            len(tokens), self.width, R_MAX,
            dtype=evidence_mean.dtype, device=evidence_mean.device,
        )
        posterior_mean, conditional_diagonal, conditional_low_rank = fuse_gaussian_beliefs(
            evidence_mean,
            prior_diagonal,
            prior_low_rank,
            evidence_diagonal,
            zero_evidence_low_rank,
        )
        noise = noise_diagonal.float().expand(len(tokens), -1)
        uncertainty = apply_observation_calibration(
            conditional_diagonal, conditional_low_rank, noise,
            regime=calibration_regime, scale=calibration_scale,
        )
        return RBBCoreOutput(
            tokens,
            measurement_state.measurement_mask,
            observed,
            measurement_state.structural_unmeasured_mask,
            measurement_state.foundation_support_mask,
            visible_state.float(),
            posterior_mean,
            visible_state.float() + posterior_mean,
            uncertainty.raw_conditional_diagonal,
            uncertainty.raw_conditional_low_rank,
            uncertainty.measurement_noise_diagonal,
            uncertainty.raw_total_diagonal,
            uncertainty.raw_total_low_rank,
            uncertainty.calibration_regime,
            uncertainty.calibration_scale,
            uncertainty.calibrated_total_diagonal,
            uncertainty.calibrated_total_low_rank,
            evidence_mean,
            evidence_diagonal,
            minimum,
        )


def migrate_adaptive_state(
    source_state: dict[str, torch.Tensor],
    core: RBBCore,
) -> tuple[dict[str, torch.Tensor], list[str], list[str]]:
    """Retain supported belief tensors and discard only adaptive-correlation slices."""
    destination = core.state_dict()
    retained: list[str] = []
    for name in (
        "mask_context.0.weight", "mask_context.0.bias",
        "mask_context.2.weight", "mask_context.2.bias",
        "evidence_norm.weight", "evidence_norm.bias",
        "evidence_hidden.0.weight", "evidence_hidden.0.bias",
    ):
        destination[name] = source_state[name].detach().clone(); retained.append(name)
    destination["evidence_output.weight"] = source_state["evidence_output.weight"][:2 * core.width].detach().clone()
    destination["evidence_output.bias"] = source_state["evidence_output.bias"][:2 * core.width].detach().clone()
    retained.extend(("evidence_output.weight[:320]", "evidence_output.bias[:320]"))
    discarded = (
        "evidence_output.weight[320:352]",
        "evidence_output.bias[320:352]",
        "correlated_directions",
    )
    return destination, retained, list(discarded)
