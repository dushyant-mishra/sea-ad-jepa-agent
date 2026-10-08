from __future__ import annotations

import torch
from torch import nn


class NonGraphV3MLP(nn.Module):
    """Small non-graph neural fusion model for Stage 27.

    This module has no graph topology, no message passing, and no node/edge
    operations. It is a compact donor-level MLP used to benchmark non-graph v3
    training regimes before any graph-specific claims are considered.
    """

    def __init__(
        self,
        condition: str,
        n_module_features: int,
        n_residual_features: int,
        hidden_dim: int = 32,
        dropout: float = 0.1,
        shared_trunk: bool = True,
    ) -> None:
        super().__init__()
        self.condition = condition
        self.n_module_features = n_module_features
        self.n_residual_features = n_residual_features

        def branch(in_dim: int) -> nn.Sequential:
            return nn.Sequential(
                nn.Linear(in_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
            )

        if condition == "module_only_mlp":
            self.module_branch = branch(n_module_features)
            fusion_dim = hidden_dim
        elif condition == "expression_residual_only_mlp":
            self.residual_branch = branch(n_residual_features)
            fusion_dim = hidden_dim
        elif condition in {"late_fusion_module_residual_mlp", "gated_fusion_module_residual_mlp"}:
            self.module_branch = branch(n_module_features)
            self.residual_branch = branch(n_residual_features)
            fusion_dim = hidden_dim * 2
            if condition == "gated_fusion_module_residual_mlp":
                self.gate = nn.Sequential(nn.Linear(fusion_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, 2), nn.Sigmoid())
        else:
            raise ValueError(f"Unknown non-graph v3 condition: {condition}")

        if shared_trunk:
            self.trunk = nn.Sequential(
                nn.Linear(fusion_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
            )
            head_dim = hidden_dim
        else:
            self.trunk = nn.Identity()
            head_dim = fusion_dim
        self.head = nn.Linear(head_dim, 1)

    def forward(self, module_x: torch.Tensor, residual_x: torch.Tensor) -> torch.Tensor:
        if self.condition == "module_only_mlp":
            z = self.module_branch(module_x)
        elif self.condition == "expression_residual_only_mlp":
            z = self.residual_branch(residual_x)
        else:
            module_z = self.module_branch(module_x)
            residual_z = self.residual_branch(residual_x)
            if self.condition == "gated_fusion_module_residual_mlp":
                gates = self.gate(torch.cat([module_z, residual_z], dim=1))
                module_z = module_z * gates[:, 0:1]
                residual_z = residual_z * gates[:, 1:2]
            z = torch.cat([module_z, residual_z], dim=1)
        return self.head(self.trunk(z)).squeeze(-1)

