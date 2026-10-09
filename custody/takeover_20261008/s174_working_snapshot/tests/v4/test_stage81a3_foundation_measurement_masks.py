from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v4.foundation_measurement_masks import (
    connected_components,
    deduplicate_masks,
    mask_hash,
    measured_mask,
    overlap,
    support_counts,
)


def test_measurement_mask_uses_feature_availability_not_expression() -> None:
    assert measured_mask(["a", "c"], ["a", "b", "c"]).tolist() == [True, False, True]


def test_mask_hash_is_deterministic() -> None:
    mask = np.asarray([True, False, True])
    assert mask_hash(mask) == mask_hash(mask.copy())


def test_mask_hash_changes_with_semantics() -> None:
    assert mask_hash(np.asarray([True, False])) != mask_hash(np.asarray([False, True]))


def test_unique_mask_deduplication_is_deterministic() -> None:
    masks = {"b": np.asarray([True, False]), "a": np.asarray([True, False]), "c": np.asarray([False, True])}
    unique, mapping = deduplicate_masks(masks)
    assert len(unique) == 2
    assert mapping["a"] == mapping["b"]


def test_overlap_calculation() -> None:
    result = overlap(np.asarray([1, 1, 0], bool), np.asarray([0, 1, 1], bool))
    assert result["shared_genes"] == 1
    assert result["jaccard"] == 1 / 3
    assert result["containment_a_in_b"] == 0.5


def test_zero_overlap_components_detected() -> None:
    masks = {"a": np.asarray([1, 0], bool), "b": np.asarray([0, 1], bool)}
    assert connected_components(["a", "b"], masks, 0.25) == [["a"], ["b"]]


def test_complete_overlap_is_connected() -> None:
    masks = {"a": np.ones(3, bool), "b": np.ones(3, bool)}
    assert connected_components(["a", "b"], masks, 0.90) == [["a", "b"]]


def test_foundation_support_counts() -> None:
    counts = support_counts({"a": np.asarray([1, 0], bool), "b": np.asarray([1, 1], bool)})
    assert counts.tolist() == [2, 1]


def test_frozen_registry_support_checks_all_4096_genes() -> None:
    frame = pd.read_csv(ROOT / "results/v4/stage81a2_gene_measurement_registry.csv")
    assert frame.canonical_ensembl_gene_id.nunique() == 4096
    assert frame.groupby("source_dataset_id").size().eq(4096).all()


def test_all_frozen_vocabulary_sources_measure_all_genes() -> None:
    frame = pd.read_csv(ROOT / "results/v4/stage81a2_gene_measurement_registry.csv")
    measured = frame.measured_gene.astype(str).str.lower().eq("true")
    assert measured.all()
