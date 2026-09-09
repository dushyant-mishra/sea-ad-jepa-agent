"""Prospective z_bio / z_obs adapter for Teacher/Student V5.

A same-cell common-core state defines the biology anchor. Student/native evidence
predicts that anchor through a biology-only path. Observation descriptors have
their own route into z_obs and are structurally excluded from z_bio.

No training authority, thresholds, or loss coefficients are selected here.
"""
from __future__ import annotations
from typing import NamedTuple
import torch
from torch import nn
import torch.nn.functional as F

class BiologyObservationOutput(NamedTuple):
    z_bio_prediction: torch.Tensor
    z_bio_anchor: torch.Tensor
    z_obs: torch.Tensor

class BiologyObservationAdapterV1(nn.Module):
    def __init__(self, *, state_width:int, observation_feature_width:int, observation_width:int)->None:
        super().__init__()
        if min(state_width,observation_feature_width,observation_width)<1:
            raise ValueError("all adapter widths must be explicit positive integers")
        self.state_width=int(state_width)
        self.observation_feature_width=int(observation_feature_width)
        self.observation_width=int(observation_width)
        self.bio_predictor=nn.Sequential(
            nn.LayerNorm(self.state_width),
            nn.Linear(self.state_width,self.state_width),
            nn.GELU(),
            nn.Linear(self.state_width,self.state_width),
        )
        self.anchor_norm=nn.LayerNorm(self.state_width,elementwise_affine=False)
        self.obs_head=nn.Sequential(
            nn.LayerNorm(self.state_width+self.observation_feature_width),
            nn.Linear(self.state_width+self.observation_feature_width,self.observation_width),
            nn.GELU(),
            nn.Linear(self.observation_width,self.observation_width),
        )

    def forward(self, *, student_native_state:torch.Tensor,
                teacher_common_core_state:torch.Tensor,
                observation_features:torch.Tensor)->BiologyObservationOutput:
        if student_native_state.ndim!=2:
            raise ValueError("student_native_state must be [cells,state_width]")
        if teacher_common_core_state.shape!=student_native_state.shape:
            raise ValueError("teacher_common_core_state must match student_native_state")
        if student_native_state.shape[1]!=self.state_width:
            raise ValueError("student state width disagrees with adapter authority")
        if observation_features.ndim!=2 or len(observation_features)!=len(student_native_state):
            raise ValueError("observation_features must be [cells,observation_feature_width]")
        if observation_features.shape[1]!=self.observation_feature_width:
            raise ValueError("observation feature width disagrees with adapter authority")
        tensors=(student_native_state,teacher_common_core_state,observation_features)
        if any(not x.is_floating_point() or not bool(torch.isfinite(x).all()) for x in tensors):
            raise ValueError("adapter inputs must be finite floating point")
        z_bio_prediction=F.layer_norm(self.bio_predictor(student_native_state),(self.state_width,))
        z_bio_anchor=self.anchor_norm(teacher_common_core_state).detach()
        z_obs=self.obs_head(torch.cat((student_native_state,observation_features),dim=1))
        return BiologyObservationOutput(z_bio_prediction,z_bio_anchor,z_obs)

def biology_anchor_alignment_loss(output:BiologyObservationOutput)->torch.Tensor:
    pred=F.normalize(output.z_bio_prediction,dim=-1)
    tgt=F.normalize(output.z_bio_anchor.detach(),dim=-1)
    return (1.0-(pred*tgt).sum(dim=-1)).mean()
