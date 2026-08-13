"""Frozen dimensions and visibility semantics for synthetic Stage81A3 tests."""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class MechanicsContract:
    stage81a2_evidence_commit: str = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
    vocabulary_size: int = 4096
    vocabulary_semantic_hash: str = (
        "f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb"
    )
    gene_identity_dim: int = 48
    model_width: int = 160
    latent_slots: int = 24
    attention_heads: int = 4


MECHANICS_CONTRACT = MechanicsContract()

# Historical short/microbatch geometry overstated full-dataset health. This is
# a mechanics rule only; Stage81A3 does not freeze an audit size or threshold.
MICROBATCH_COLLAPSE_TELEMETRY_POLICY = (
    "diagnostic_only_checkpoint_acceptance_requires_large_pathology_blind_audit"
)


@dataclass(frozen=True)
class VisibilityMasks:
    student_valid: torch.Tensor
    target_valid: torch.Tensor


def derive_visibility_masks(
    measurement_mask: torch.Tensor,
    context_mask: torch.Tensor,
) -> VisibilityMasks:
    """Derive student and target validity without placeholder-token semantics."""
    if measurement_mask.dtype is not torch.bool or context_mask.dtype is not torch.bool:
        raise TypeError("measurement_mask and context_mask must be boolean tensors")
    if measurement_mask.shape != context_mask.shape:
        raise ValueError("measurement_mask and context_mask must have identical shapes")
    if measurement_mask.ndim != 2:
        raise ValueError("visibility masks must have shape [batch, genes]")
    if torch.any(context_mask & ~measurement_mask):
        raise ValueError("only genuinely measured genes may be context-hidden")
    return VisibilityMasks(
        student_valid=measurement_mask & ~context_mask,
        target_valid=measurement_mask,
    )
