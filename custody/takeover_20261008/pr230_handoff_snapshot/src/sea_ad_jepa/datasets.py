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
        module_fill_random: bool = True,
    ):
        if sparse.issparse(matrix):
            matrix = matrix.toarray()
        self.x = np.asarray(matrix, dtype=np.float32)
        self.mask_fraction = mask_fraction
        self.rng = np.random.default_rng(seed)
        self.mask_mode = mask_mode
        self.gene_modules = gene_modules or {}
        self.module_names = sorted(self.gene_modules)
        self.module_fill_random = module_fill_random

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
            return self._module_mask(module_name, n_genes)

        if self.mask_mode == "mixed" and self.module_names and self.rng.random() < 0.5:
            module_name = self.rng.choice(self.module_names)
            return self._module_mask(module_name, n_genes)

        n_mask = max(1, int(n_genes * self.mask_fraction))
        return self.rng.choice(n_genes, size=n_mask, replace=False)

    def _module_mask(self, module_name: str, n_genes: int) -> np.ndarray:
        module_idx = set(self.gene_modules[module_name])
        if not self.module_fill_random:
            return np.asarray(sorted(module_idx), dtype=np.int64)

        n_mask = max(len(module_idx), int(n_genes * self.mask_fraction))
        if n_mask > len(module_idx):
            remaining = np.asarray([idx for idx in range(n_genes) if idx not in module_idx], dtype=np.int64)
            extra = self.rng.choice(remaining, size=n_mask - len(module_idx), replace=False)
            module_idx.update(int(idx) for idx in extra)
        return np.asarray(sorted(module_idx), dtype=np.int64)
