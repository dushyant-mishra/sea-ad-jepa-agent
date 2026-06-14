from __future__ import annotations

import torch
from torch import nn
import torch.nn.functional as F


class GatedAttentionMIL(nn.Module):
    """Interpretable gated-attention MIL head for donor bags of cell embeddings.

    This is the lean Ilse-style attention pooling layer we want for the 6e10
    problem: it predicts one donor-level target from a variable number of cell
    embeddings while returning a normalized attention weight for every cell.
    """

    def __init__(self, input_dim: int, hidden_dim: int = 64, dropout: float = 0.2):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.dropout = dropout
        self.attention_v = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Dropout(dropout),
        )
        self.attention_u = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Sigmoid(),
            nn.Dropout(dropout),
        )
        self.attention_weights = nn.Linear(hidden_dim, 1)
        self.regressor = nn.Sequential(
            nn.Linear(input_dim, max(1, hidden_dim // 2)),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(max(1, hidden_dim // 2), 1),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Predict one donor target from a single donor bag.

        Args:
            x: Tensor with shape [n_cells, input_dim].

        Returns:
            y_pred: Tensor with shape [1].
            attention: Tensor with shape [n_cells].
        """

        if x.ndim != 2:
            raise ValueError("MIL input must have shape [n_cells, input_dim]")
        if x.shape[0] == 0:
            raise ValueError("MIL bag must contain at least one cell")
        gated = self.attention_v(x) * self.attention_u(x)
        attention_logits = self.attention_weights(gated).transpose(1, 0)
        attention = F.softmax(attention_logits, dim=1)
        pooled = attention @ x
        prediction = self.regressor(pooled).squeeze(0).squeeze(-1)
        return prediction, attention.squeeze(0)
