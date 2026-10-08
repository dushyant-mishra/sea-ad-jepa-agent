"""Rotation-invariant uncertainty reporting for stable coordinate blocks."""

from __future__ import annotations

import numpy as np


EIGENGAP_THRESHOLD = 0.01


def stable_blocks(eigenvalues: np.ndarray, relative_gap_threshold: float = EIGENGAP_THRESHOLD) -> list[np.ndarray]:
    values = np.asarray(eigenvalues, dtype=float)
    if values.ndim != 1 or not len(values):
        raise ValueError("eigenvalues must be a nonempty vector")
    gaps = np.abs(values[:-1] - values[1:]) / np.maximum(np.abs(values[:-1]), 1e-12)
    blocks: list[list[int]] = [[0]]
    for coordinate, gap in enumerate(gaps, start=1):
        if gap < relative_gap_threshold:
            blocks[-1].append(coordinate)
        else:
            blocks.append([coordinate])
    return [np.asarray(block, dtype=int) for block in blocks]


def aggregate_block_variance(diagonal_variance: np.ndarray, blocks: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    variance = np.asarray(diagonal_variance, dtype=float)
    if variance.shape[-1] != sum(len(block) for block in blocks):
        raise ValueError("blocks must cover every variance coordinate exactly once")
    block_values = np.stack([variance[..., block].sum(-1) for block in blocks], axis=-1)
    return block_values, variance.sum(-1)
