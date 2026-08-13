"""Auditable measured-gene masking mechanics without a production seed policy."""

from __future__ import annotations

import hashlib
import math
from typing import Literal

import torch


MaskingRule = Literal["exact_count", "bernoulli"]


def keyed_mask_seed(
    *,
    production_seed: int,
    cell_index: int,
    sample_pass: int,
    view_index: int,
) -> int:
    """Derive a stable seed without Python hash randomization or biological metadata."""
    if min(cell_index, sample_pass, view_index) < 0:
        raise ValueError("cell_index, sample_pass, and view_index must be non-negative")
    payload = f"{int(production_seed)}|{cell_index}|{sample_pass}|{view_index}".encode("ascii")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % (2**63 - 1)


def construct_context_mask(
    measurement_mask: torch.Tensor,
    *,
    mask_fraction: float,
    production_seed: int,
    cell_indices: torch.Tensor,
    sample_pass: int,
    view_index: int,
    rule: MaskingRule,
) -> torch.Tensor:
    """Hide only measured genes using exact-count or Bernoulli test mechanics."""
    if measurement_mask.dtype is not torch.bool or measurement_mask.ndim != 2:
        raise ValueError("measurement_mask must be boolean with shape [cells, genes]")
    if cell_indices.ndim != 1 or cell_indices.shape[0] != measurement_mask.shape[0]:
        raise ValueError("cell_indices must have one entry per cell")
    if not 0.0 <= mask_fraction <= 1.0:
        raise ValueError("mask_fraction must be in [0, 1]")
    if rule not in {"exact_count", "bernoulli"}:
        raise ValueError("rule must be exact_count or bernoulli")
    output = torch.zeros_like(measurement_mask)
    for row in range(measurement_mask.shape[0]):
        measured = torch.nonzero(measurement_mask[row], as_tuple=False).flatten()
        generator = torch.Generator(device="cpu").manual_seed(keyed_mask_seed(
            production_seed=production_seed,
            cell_index=int(cell_indices[row]),
            sample_pass=sample_pass,
            view_index=view_index,
        ))
        if rule == "exact_count":
            count = int(math.floor(mask_fraction * measured.numel()))
            if count:
                selected = measured[torch.randperm(measured.numel(), generator=generator)[:count]]
                output[row, selected.to(output.device)] = True
        else:
            selected = torch.rand(measured.numel(), generator=generator) < mask_fraction
            output[row, measured[selected].to(output.device)] = True
    if torch.any(output & ~measurement_mask):
        raise RuntimeError("constructed context mask includes an unmeasured gene")
    return output
