from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.rare_state_audit import (
    ANNOTATION_RARE_MAX_FREQUENCY,
    ANNOTATION_RARE_MIN_CELLS,
    KNN_K,
    LOCAL_DENSITY_K,
    critical_compression_flag,
    ledger_cosine,
    rarity_flags,
    stable_hash_sample,
)


def test_fixed_neighbor_contracts() -> None:
    assert KNN_K == 15
    assert LOCAL_DENSITY_K == 30
    assert ANNOTATION_RARE_MAX_FREQUENCY == 0.01
    assert ANNOTATION_RARE_MIN_CELLS == 100


def test_annotation_rare_boundaries_are_exact() -> None:
    assert rarity_flags(100, 10_000, [100])[0]
    assert not rarity_flags(99, 10_000, [99])[0]
    assert not rarity_flags(101, 10_000, [101])[0]


def test_donor_recurring_requires_three_cells_in_five_donors() -> None:
    assert rarity_flags(100, 10_000, [3, 3, 3, 3, 3])[1]
    assert not rarity_flags(100, 10_000, [25, 25, 25, 25])[1]


def test_sampling_is_deterministic_and_donor_balanced() -> None:
    ids = [f"c{i}" for i in range(100)]
    donors = ["a"] * 50 + ["b"] * 50
    first = stable_hash_sample(ids, donors, 20)
    second = stable_hash_sample(ids, donors, 20)
    assert np.array_equal(first, second)
    assert np.sum(np.asarray(donors)[first] == "a") == 10


def test_ledger_similarity_uses_every_gene_token() -> None:
    left = np.zeros((1, 4096, 2), dtype=np.float32)
    right = np.zeros((2, 4096, 2), dtype=np.float32)
    left[0, :, 0] = 1
    right[0, :, 0] = 1
    right[1, :, 0] = 1
    right[1, -1, 0] = -1
    similarity = ledger_cosine(left, right, block_genes=127)
    assert similarity[0, 0] == 1.0
    assert similarity[0, 1] < 1.0


def test_critical_compression_flag_is_exact() -> None:
    assert critical_compression_flag(0.75, 0.49, 0.1, 0.1)
    assert not critical_compression_flag(0.75, 0.50, 0.1, 0.1)
    assert critical_compression_flag(0.1, 0.1, 0.70, 0.44)
