from __future__ import annotations

import numpy as np
from scipy import sparse


class DenseExpressionDataset:
    """Small in-memory expression dataset for pilot JEPA training."""

    def __init__(
        self,
        matrix,
        mask_fraction: float = 0.35,
        seed: int = 7,
        mask_mode: str = "random",
        gene_modules: dict[str, list[int]] | None = None,
    ):
        if sparse.issparse(matrix):
            matrix = matrix.toarray()
        self.x = np.asarray(matrix, dtype=np.float32)
        self.mask_fraction = mask_fraction
        self.rng = np.random.default_rng(seed)
        self.mask_mode = mask_mode
        self.gene_modules = gene_modules or {}
        self.module_names = sorted(self.gene_modules)

    def __len__(self) -> int:
        return self.x.shape[0]

    def __getitem__(self, index: int) -> tuple[np.ndarray, np.ndarray]:
        target = self.x[index].copy()
        context = target.copy()
        n_genes = context.shape[0]
        mask_idx = self._choose_mask(n_genes)
        context[mask_idx] = 0.0
        return context, target

    def _choose_mask(self, n_genes: int) -> np.ndarray:
        if self.mask_mode == "module" and self.module_names:
            module_name = self.rng.choice(self.module_names)
            return np.asarray(self.gene_modules[module_name], dtype=np.int64)

        if self.mask_mode == "mixed" and self.module_names and self.rng.random() < 0.5:
            module_name = self.rng.choice(self.module_names)
            return np.asarray(self.gene_modules[module_name], dtype=np.int64)

        n_mask = max(1, int(n_genes * self.mask_fraction))
        return self.rng.choice(n_genes, size=n_mask, replace=False)
