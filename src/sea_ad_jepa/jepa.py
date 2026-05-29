from __future__ import annotations

import torch
from torch import nn
import torch.nn.functional as F


class MLPEncoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 512, latent_dim: int = 128, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, latent_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class GeneJEPA(nn.Module):
    """Minimal JEPA-style model for masked gene-expression latent prediction."""

    def __init__(self, input_dim: int, hidden_dim: int = 512, latent_dim: int = 128, dropout: float = 0.1):
        super().__init__()
        self.context_encoder = MLPEncoder(input_dim, hidden_dim, latent_dim, dropout)
        self.target_encoder = MLPEncoder(input_dim, hidden_dim, latent_dim, dropout)
        self.predictor = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, latent_dim),
        )

    @torch.no_grad()
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return F.normalize(self.context_encoder(x), dim=-1)

    def forward(self, context_x: torch.Tensor, target_x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        context_z = self.context_encoder(context_x)
        pred_z = self.predictor(context_z)
        with torch.no_grad():
            target_z = self.target_encoder(target_x)
        return pred_z, target_z


def jepa_loss(pred_z: torch.Tensor, target_z: torch.Tensor) -> torch.Tensor:
    pred_z = F.normalize(pred_z, dim=-1)
    target_z = F.normalize(target_z, dim=-1)
    return 2 - 2 * (pred_z * target_z).sum(dim=-1).mean()

