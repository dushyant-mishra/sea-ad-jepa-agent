from __future__ import annotations

import copy

import torch
from torch import nn
import torch.nn.functional as F


class GraphGeneEncoder(nn.Module):
    """Gene-graph encoder for Graph-JEPA v2.

    Node input combines:

    - per-cell expression value and optional node annotations
    - learnable gene identity embedding

    The identity embedding is critical. Without it, every node only carries a
    scalar expression value plus generic flags, and message passing can collapse
    distinct genes into neighborhood averages.
    """

    def __init__(
        self,
        n_genes: int,
        node_feature_dim: int,
        gene_embed_dim: int = 32,
        hidden_dim: int = 128,
        latent_dim: int = 128,
        n_layers: int = 2,
        dropout: float = 0.1,
        conv: str = "sage",
    ):
        super().__init__()
        if n_layers < 1:
            raise ValueError("n_layers must be >= 1")

        self.n_genes = n_genes
        self.node_feature_dim = node_feature_dim
        self.gene_embedding = nn.Embedding(n_genes, gene_embed_dim)
        self.input_proj = nn.Sequential(
            nn.Linear(node_feature_dim + gene_embed_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
        )
        self.convs = nn.ModuleList([self._make_conv(conv, hidden_dim) for _ in range(n_layers)])
        self.norms = nn.ModuleList([nn.LayerNorm(hidden_dim) for _ in range(n_layers)])
        self.dropout = nn.Dropout(dropout)
        self.out = nn.Linear(hidden_dim, latent_dim)

    @staticmethod
    def _make_conv(conv: str, hidden_dim: int) -> nn.Module:
        try:
            from torch_geometric.nn import GCNConv, SAGEConv
        except ImportError as exc:
            raise ImportError("Install torch-geometric to use GraphGeneEncoder") from exc

        conv = conv.lower()
        if conv == "sage":
            return SAGEConv(hidden_dim, hidden_dim)
        if conv == "gcn":
            return GCNConv(hidden_dim, hidden_dim)
        raise ValueError("conv must be 'sage' or 'gcn'")

    def forward(self, data) -> torch.Tensor:
        x = data.x
        node_id = data.node_id
        edge_index = data.edge_index
        batch = getattr(data, "batch", None)
        if batch is None:
            batch = torch.zeros(x.shape[0], dtype=torch.long, device=x.device)

        gene_id = self.gene_embedding(node_id)
        h = self.input_proj(torch.cat([x, gene_id], dim=-1))
        for conv, norm in zip(self.convs, self.norms):
            residual = h
            h = conv(h, edge_index)
            h = norm(h)
            h = F.gelu(h)
            h = self.dropout(h)
            h = h + residual

        pooled = self._pool_mean(h, batch)
        return self.out(pooled)

    @staticmethod
    def _pool_mean(h: torch.Tensor, batch: torch.Tensor) -> torch.Tensor:
        try:
            from torch_geometric.nn import global_mean_pool
        except ImportError as exc:
            raise ImportError("Install torch-geometric to use GraphGeneEncoder") from exc
        return global_mean_pool(h, batch)


class GraphGeneJEPA(nn.Module):
    """EMA-target Graph-JEPA for gene-graph cell-state prediction."""

    def __init__(
        self,
        n_genes: int,
        node_feature_dim: int,
        gene_embed_dim: int = 32,
        hidden_dim: int = 128,
        latent_dim: int = 128,
        n_layers: int = 2,
        dropout: float = 0.1,
        conv: str = "sage",
        ema_decay: float = 0.996,
    ):
        super().__init__()
        self.ema_decay = ema_decay
        self.context_encoder = GraphGeneEncoder(
            n_genes=n_genes,
            node_feature_dim=node_feature_dim,
            gene_embed_dim=gene_embed_dim,
            hidden_dim=hidden_dim,
            latent_dim=latent_dim,
            n_layers=n_layers,
            dropout=dropout,
            conv=conv,
        )
        self.target_encoder = copy.deepcopy(self.context_encoder)
        for param in self.target_encoder.parameters():
            param.requires_grad = False
        self.predictor = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, latent_dim),
        )

    @torch.no_grad()
    def update_target_network(self) -> None:
        for context_param, target_param in zip(self.context_encoder.parameters(), self.target_encoder.parameters()):
            target_param.data.mul_(self.ema_decay).add_(context_param.data, alpha=1.0 - self.ema_decay)

    def reset_target_network(self) -> None:
        self.target_encoder.load_state_dict(self.context_encoder.state_dict())
        for param in self.target_encoder.parameters():
            param.requires_grad = False

    @torch.no_grad()
    def encode(self, data) -> torch.Tensor:
        return F.normalize(self.context_encoder(data), dim=-1)

    def forward(self, context_data, target_data) -> tuple[torch.Tensor, torch.Tensor]:
        context_z = self.context_encoder(context_data)
        pred_z = self.predictor(context_z)
        with torch.no_grad():
            target_z = self.target_encoder(target_data)
        return pred_z, target_z
