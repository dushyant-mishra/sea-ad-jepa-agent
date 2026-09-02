"""Deterministic real measurement-mask and overlap utilities."""

from __future__ import annotations

import hashlib
from collections import defaultdict

import numpy as np


def mask_hash(mask: np.ndarray) -> str:
    values = np.asarray(mask, dtype=np.bool_)
    digest = hashlib.sha256()
    digest.update(str(values.shape).encode("ascii"))
    digest.update(np.packbits(values, bitorder="little").tobytes())
    return digest.hexdigest()


def measured_mask(feature_ids: list[str], vocabulary_ids: list[str]) -> np.ndarray:
    features = set(feature_ids)
    return np.asarray([gene in features for gene in vocabulary_ids], dtype=np.bool_)


def deduplicate_masks(masks: dict[str, np.ndarray]) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    unique: dict[str, np.ndarray] = {}
    mapping: dict[str, str] = {}
    for name in sorted(masks):
        digest = mask_hash(masks[name])
        unique.setdefault(digest, np.asarray(masks[name], dtype=np.bool_).copy())
        mapping[name] = digest
    return unique, mapping


def overlap(first: np.ndarray, second: np.ndarray) -> dict[str, float | int]:
    a, b = np.asarray(first, bool), np.asarray(second, bool)
    shared = int(np.count_nonzero(a & b))
    union = int(np.count_nonzero(a | b))
    count_a, count_b = int(a.sum()), int(b.sum())
    return {
        "shared_genes": shared,
        "jaccard": shared / union if union else 1.0,
        "containment_a_in_b": shared / count_a if count_a else 1.0,
        "containment_b_in_a": shared / count_b if count_b else 1.0,
        "additional_a_over_b": int(np.count_nonzero(a & ~b)),
        "additional_b_over_a": int(np.count_nonzero(b & ~a)),
    }


def connected_components(names: list[str], masks: dict[str, np.ndarray], threshold: float) -> list[list[str]]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for index, first in enumerate(names):
        adjacency[first]
        for second in names[index + 1:]:
            metrics = overlap(masks[first], masks[second])
            if metrics["jaccard"] >= threshold:
                adjacency[first].add(second)
                adjacency[second].add(first)
    remaining, components = set(names), []
    while remaining:
        root = min(remaining)
        stack, component = [root], []
        remaining.remove(root)
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in sorted(adjacency[node]):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(sorted(component))
    return sorted(components, key=lambda values: (-len(values), values))


def support_counts(masks: dict[str, np.ndarray]) -> np.ndarray:
    return np.stack([np.asarray(masks[name], bool) for name in sorted(masks)]).sum(axis=0)
