"""Deterministic non-gradient PCA summary for distributed v4 slot states."""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class FrozenPCA:
    """A train-fitted PCA transform with no factor-label or evaluation-data API."""

    mean: torch.Tensor
    components: torch.Tensor

    @property
    def n_components(self) -> int:
        return int(self.components.shape[0])

    @classmethod
    def fit(cls, training_values: torch.Tensor, n_components: int = 160) -> "FrozenPCA":
        if training_values.ndim != 2:
            raise ValueError("training_values must have shape [train_cells, features]")
        if n_components <= 0 or n_components > min(training_values.shape):
            raise ValueError("n_components exceeds the deterministic PCA rank bound")
        values = training_values.detach().float()
        mean = values.mean(dim=0)
        _, _, vh = torch.linalg.svd(values - mean, full_matrices=False)
        return cls(mean=mean.cpu(), components=vh[:n_components].cpu())

    def transform(self, values: torch.Tensor) -> torch.Tensor:
        if values.ndim != 2 or values.shape[1] != self.mean.numel():
            raise ValueError("values do not match the fitted PCA feature contract")
        return (values.detach().float().cpu() - self.mean) @ self.components.T


def flatten_slots(slots: torch.Tensor) -> torch.Tensor:
    """Preserve the complete slot pattern before any compact projection."""
    if slots.ndim != 3:
        raise ValueError("slots must have shape [cells, slots, width]")
    return slots.detach().float().reshape(slots.shape[0], -1)
