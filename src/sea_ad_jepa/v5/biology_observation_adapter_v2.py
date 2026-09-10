"""Observation-gradient-firewalled z_bio / z_obs adapter for prospective V5.

The same native student state may contain measurement information because it is
computed from observed RNA.  V1 allowed the observation head to backpropagate
through that shared state, so an observation/reconstruction loss could actively
write technical identity into the representation that also feeds z_bio.  V2
cuts that gradient path: z_obs may *condition on* a detached copy of the biology
state plus approved fixed observation descriptors, but observation-route
gradients cannot modify either upstream biology state or descriptor producers.
The observation head itself is the trainable observation encoder in this adapter.

This module does not claim that indirect measurement leakage is impossible.
Same-cell interventions and held-out biology remain mandatory qualification.
No dimensions, thresholds, losses, schedules, or training authority are set.
"""
from __future__ import annotations

from typing import NamedTuple

import torch
from torch import nn
import torch.nn.functional as F


class BiologyObservationOutputV2(NamedTuple):
    z_bio_prediction: torch.Tensor
    z_bio_anchor: torch.Tensor
    z_obs: torch.Tensor


class BiologyObservationAdapterV2(nn.Module):
    def __init__(
        self,
        *,
        state_width: int,
        observation_feature_width: int,
        observation_width: int,
    ) -> None:
        super().__init__()
        if min(state_width, observation_feature_width, observation_width) < 1:
            raise ValueError("all adapter widths must be explicit positive integers")
        self.state_width = int(state_width)
        self.observation_feature_width = int(observation_feature_width)
        self.observation_width = int(observation_width)
        self.bio_predictor = nn.Sequential(
            nn.LayerNorm(self.state_width),
            nn.Linear(self.state_width, self.state_width),
            nn.GELU(),
            nn.Linear(self.state_width, self.state_width),
        )
        self.anchor_norm = nn.LayerNorm(self.state_width, elementwise_affine=False)
        self.obs_head = nn.Sequential(
            nn.LayerNorm(self.state_width + self.observation_feature_width),
            nn.Linear(
                self.state_width + self.observation_feature_width,
                self.observation_width,
            ),
            nn.GELU(),
            nn.Linear(self.observation_width, self.observation_width),
        )

    def forward(
        self,
        *,
        student_biology_state: torch.Tensor,
        teacher_common_core_state: torch.Tensor,
        observation_features: torch.Tensor,
    ) -> BiologyObservationOutputV2:
        if student_biology_state.ndim != 2:
            raise ValueError("student_biology_state must be [cells,state_width]")
        if teacher_common_core_state.shape != student_biology_state.shape:
            raise ValueError("teacher_common_core_state must match student_biology_state")
        if student_biology_state.shape[1] != self.state_width:
            raise ValueError("student biology-state width disagrees with adapter authority")
        if observation_features.ndim != 2 or len(observation_features) != len(
            student_biology_state
        ):
            raise ValueError(
                "observation_features must be [cells,observation_feature_width]"
            )
        if observation_features.shape[1] != self.observation_feature_width:
            raise ValueError("observation feature width disagrees with adapter authority")
        tensors = (
            student_biology_state,
            teacher_common_core_state,
            observation_features,
        )
        if any(
            not x.is_floating_point() or not bool(torch.isfinite(x).all())
            for x in tensors
        ):
            raise ValueError("adapter inputs must be finite floating point")

        z_bio_prediction = F.layer_norm(
            self.bio_predictor(student_biology_state), (self.state_width,)
        )
        z_bio_anchor = self.anchor_norm(teacher_common_core_state).detach()

        # Critical V2 boundary: observation objectives can use biological context
        # as conditioning information, but cannot write gradients back into it.
        z_obs = self.obs_head(
            torch.cat(
                (student_biology_state.detach(), observation_features.detach()), dim=1
            )
        )
        return BiologyObservationOutputV2(z_bio_prediction, z_bio_anchor, z_obs)


def biology_anchor_alignment_loss_v2(
    output: BiologyObservationOutputV2,
) -> torch.Tensor:
    pred = F.normalize(output.z_bio_prediction, dim=-1)
    tgt = F.normalize(output.z_bio_anchor.detach(), dim=-1)
    return (1.0 - (pred * tgt).sum(dim=-1)).mean()


def gene_ledger_reconstruction_inputs_v2(
    output: BiologyObservationOutputV2,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return the only lawful V2 state inputs for ledger reconstruction.

    Reconstruction is allowed to *condition on* biology, but its target is also
    measurement-bearing.  The biological context is therefore detached here so
    a reconstruction loss cannot train z_bio into a technology/source shortcut.
    The observation state remains trainable.
    """
    return output.z_bio_prediction.detach(), output.z_obs
