from __future__ import annotations

import numpy as np
from scipy import sparse


class DenseExpressionDataset:
    """Small in-memory expression dataset for pilot JEPA training."""

    def __init__(self, matrix, mask_fraction: float = 0.35, seed: int = 7):
        if sparse.issparse(matrix):
            matrix = matrix.toarray()
        self.x = np.asarray(matrix, dtype=np.float32)
        self.mask_fraction = mask_fraction
        self.rng = np.random.default_rng(seed)

    def __len__(self) -> int:
        return self.x.shape[0]

    def __getitem__(self, index: int) -> tuple[np.ndarray, np.ndarray]:
        target = self.x[index].copy()
        context = target.copy()
        n_genes = context.shape[0]
        n_mask = max(1, int(n_genes * self.mask_fraction))
        mask_idx = self.rng.choice(n_genes, size=n_mask, replace=False)
        context[mask_idx] = 0.0
        return context, target

