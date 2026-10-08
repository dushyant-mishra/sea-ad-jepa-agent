"""Evidence and measurement response mechanics for Stage81A3 FBSDQ."""

from __future__ import annotations

import hashlib

import numpy as np


def keyed_seed(root: int, *parts: object) -> int:
    text = "|".join([str(root), *map(str, parts)])
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def nested_random_masks(genes: int, fractions: tuple[float, ...], sequences: int, root: int) -> np.ndarray:
    masks = np.zeros((sequences, len(fractions), genes), dtype=bool)
    for sequence in range(sequences):
        order = np.random.default_rng(keyed_seed(root, sequence)).permutation(genes)
        for level, fraction in enumerate(fractions):
            masks[sequence, level, order[: int(round(genes * fraction))]] = True
    return masks


def factual_visible_state(expression: np.ndarray, mask: np.ndarray, mean: np.ndarray, components: np.ndarray) -> np.ndarray:
    return ((np.asarray(expression) - mean) * np.asarray(mask)) @ np.asarray(components)


def state_deficit(reference: np.ndarray, candidate: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    delta = np.asarray(reference) - np.asarray(candidate)
    squared = np.square(delta).sum(axis=-1)
    return squared / reference.shape[-1], squared / np.maximum(np.square(reference).sum(axis=-1), 1e-12)


def trapezoid_auc(levels: np.ndarray, values: np.ndarray) -> np.ndarray:
    return np.trapezoid(np.asarray(values), np.asarray(levels), axis=-1)


def binomial_thin(counts: np.ndarray, fraction: float, seed: int) -> np.ndarray:
    values = np.asarray(counts, dtype=np.int64)
    return np.random.default_rng(seed).binomial(values, fraction).astype(np.int32)
