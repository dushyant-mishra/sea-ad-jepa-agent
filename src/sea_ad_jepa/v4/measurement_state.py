"""Explicit measurement semantics for heterogeneous molecular assays."""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class MeasurementState:
    """Cell-gene masks that keep measurement absence distinct from SSL hiding."""

    measurement_mask: torch.Tensor
    training_hidden_mask: torch.Tensor
    foundation_support_mask: torch.Tensor

    def __post_init__(self) -> None:
        measurement = self.measurement_mask
        hidden = self.training_hidden_mask
        support = self.foundation_support_mask
        if measurement.dtype is not torch.bool or hidden.dtype is not torch.bool:
            raise TypeError("measurement and training-hidden masks must be boolean")
        if measurement.shape != hidden.shape or measurement.ndim != 2:
            raise ValueError("measurement masks must share [cell, gene] shape")
        if support.dtype is not torch.bool or support.ndim != 1:
            raise TypeError("foundation support must be a boolean [gene] mask")
        if support.shape[0] != measurement.shape[1]:
            raise ValueError("foundation support must match the gene dimension")
        if torch.any(hidden & ~measurement):
            raise ValueError("training-hidden genes must have been measured")

    @property
    def structural_unmeasured_mask(self) -> torch.Tensor:
        return ~self.measurement_mask

    @property
    def observed_mask(self) -> torch.Tensor:
        return self.measurement_mask & ~self.training_hidden_mask

    @property
    def belief_missing_mask(self) -> torch.Tensor:
        return self.training_hidden_mask | self.structural_unmeasured_mask

    @property
    def training_target_eligible_mask(self) -> torch.Tensor:
        return self.measurement_mask & self.training_hidden_mask

    def sanitized_expression(self, expression: torch.Tensor) -> torch.Tensor:
        """Remove values unavailable to the model without interpreting them as zero."""
        if expression.shape != self.measurement_mask.shape:
            raise ValueError("expression must match measurement-state shape")
        return expression.masked_fill(~self.observed_mask, 0.0)

    def assert_foundation_inference_supported(self) -> None:
        """Reject cell-specific claims for genes never observed in foundation data."""
        unsupported_missing = self.belief_missing_mask & ~self.foundation_support_mask[None]
        if torch.any(unsupported_missing):
            raise ValueError(
                "globally never-observed genes cannot receive learned cell-specific inference"
            )


def measurement_state_codes(
    expression: torch.Tensor,
    state: MeasurementState,
) -> torch.Tensor:
    """Return 0 observed, 1 measured-zero, 2 training-masked, 3 structural."""
    codes = torch.zeros_like(expression, dtype=torch.int8)
    measured_zero = state.observed_mask & (expression == 0)
    codes[measured_zero] = 1
    codes[state.training_hidden_mask] = 2
    codes[state.structural_unmeasured_mask] = 3
    return codes
