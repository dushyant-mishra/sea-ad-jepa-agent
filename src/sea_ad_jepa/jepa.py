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
    """JEPA-style model for masked gene-expression latent prediction."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 512,
        latent_dim: int = 128,
        dropout: float = 0.1,
        ema_decay: float = 0.996,
    ):
        super().__init__()
        self.ema_decay = ema_decay
        self.context_encoder = MLPEncoder(input_dim, hidden_dim, latent_dim, dropout)
        self.target_encoder = MLPEncoder(input_dim, hidden_dim, latent_dim, dropout)
        self.target_encoder.load_state_dict(self.context_encoder.state_dict())
        for param in self.target_encoder.parameters():
            param.requires_grad = False
        self.predictor = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, latent_dim),
        )

    @torch.no_grad()
    def update_target_network(self) -> None:
        """Update target encoder weights from context encoder using exponential moving average."""
        for context_param, target_param in zip(self.context_encoder.parameters(), self.target_encoder.parameters()):
            target_param.data.mul_(self.ema_decay).add_(context_param.data, alpha=1.0 - self.ema_decay)

    def reset_target_network(self) -> None:
        """Re-initialize the target encoder from the current context encoder."""
        self.target_encoder.load_state_dict(self.context_encoder.state_dict())
        for param in self.target_encoder.parameters():
            param.requires_grad = False

    @torch.no_grad()
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return F.normalize(self.context_encoder(x), dim=-1)

    def forward(self, context_x: torch.Tensor, target_x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        context_z = self.context_encoder(context_x)
        pred_z = self.predictor(context_z)
        with torch.no_grad():
            target_z = self.target_encoder(target_x)
        return pred_z, target_z


def variance_loss(z: torch.Tensor, gamma: float = 1.0, eps: float = 1e-4) -> torch.Tensor:
    std = torch.sqrt(z.var(dim=0, unbiased=False) + eps)
    return torch.mean(F.relu(gamma - std))


def jepa_loss(
    pred_z: torch.Tensor,
    target_z: torch.Tensor,
    variance_weight: float = 0.0,
    variance_gamma: float = 1.0,
    eps: float = 1e-4,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    pred_raw = pred_z
    target_raw = target_z
    pred_norm = F.normalize(pred_raw, dim=-1)
    target_norm = F.normalize(target_raw, dim=-1)
    alignment = 2 - 2 * (pred_norm * target_norm).sum(dim=-1).mean()
    pred_variance = variance_loss(pred_raw, gamma=variance_gamma, eps=eps)
    target_variance = variance_loss(target_raw, gamma=variance_gamma, eps=eps)
    variance = 0.5 * (pred_variance + target_variance)
    total = alignment + variance_weight * variance
    parts = {
        "alignment": alignment.detach(),
        "variance": variance.detach(),
        "pred_variance": pred_variance.detach(),
        "target_variance": target_variance.detach(),
    }
    return total, parts
