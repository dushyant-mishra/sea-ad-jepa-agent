"""Synthetic-only adversarial feature contract tests.

All names/values below are invented fixtures, NOT a gene annotation database
or physical experiment. No real data, protected outcomes or JEPA training.
"""
from dataclasses import replace

import numpy as np
import pytest

from sea_ad_jepa.perturbation.cross_study_feature_contract_v1 import (
    FeatureContractError, FeatureMapEntry, ObservationStatus,
    StudyFeatures, align, aligned_observation, freeze_annotation,
)

G1 = "ENSG00000000001"
G2 = "ENSG00000000002"
G3 = "ENSG00000000003"
ROOT = "a" * 64


def annotation(entries=None):
    if entries is None:
        entries = [
            FeatureMapEntry("HGNC_SYMBOL", "TEST1", G1, "SYNTHETIC_MAP_A", "PRIMARY_ID"),
            FeatureMapEntry("HGNC_SYMBOL", "TEST2", G2, "SYNTHETIC_MAP_B", "PRIMARY_ID"),
            FeatureMapEntry("ENSEMBL_GENE_ID", G1 + ".4", G1, "SYNTHETIC_MAP_A", "VERSIONED_ID"),
            FeatureMapEntry("ENSEMBL_GENE_ID", G3, G3, "SYNTHETIC_MAP_C", "PRIMARY_ID"),
        ]
    return freeze_annotation(
        release="SYNTHETIC_ONLY_FAKE_ANNOTATION", annotation_file_sha256=ROOT,
        entries=entries,
    )


def study_a():
    return StudyFeatures(
        "SYNTHETIC_SYMBOL_STUDY", "FAKE_COUNTS", "HGNC_SYMBOL",
        ("TEST1", "TEST2"), np.array([[True, True]], dtype=bool),
        np.array([[True, False]], dtype=bool),
    )


def study_b():
    return StudyFeatures(
        "SYNTHETIC_ENSEMBL_STUDY", "FAKE_COUNTS", "ENSEMBL_GENE_ID",
        (G1 + ".4", G3), np.array([[True, True]], dtype=bool),
        np.array([[True, True]], dtype=bool),
    )


def test_full_outer_alignment_preserves_structural_absence_and_measured_zero():
    a, b = study_a(), study_b()
    cross = align(a, b, annotation())
    assert cross.canonical_ids == (G1, G2, G3)
    assert cross.index_a == (0, 1, -1)
    assert cross.index_b == (0, -1, 1)
    val_a, assayed_a, det_a = aligned_observation(
        a, cross.index_a, np.array([[10, 0.]], dtype=float), sample_index=0,
    )
    assert val_a[0] == 10
    assert val_a[1] == 0
    assert np.isnan(val_a[2])
    assert assayed_a.tolist() == [True, True, False]
    assert det_a.tolist() == [True, False, False]
    assert a.status(0, 1) == ObservationStatus.ASSAYED_UNDETECTED
    val_b, assayed_b, det_b = aligned_observation(
        b, cross.index_b, np.array([[4, 9.]], dtype=float), sample_index=0,
    )
    assert val_b[0] == 4 and np.isnan(val_b[1]) and val_b[2] == 9
    assert assayed_b.tolist() == [True, False, True]
    assert det_b.tolist() == [True, False, True]


def test_unreviewed_alias_or_unknown_namespace_cannot_resolve():
    a = annotation()
    assert a.lookup("HGNC_SYMBOL", "TEST1") == G1
    assert a.lookup("HGNC_SYMBOL", "AliasOfTEST1") is None
    with pytest.raises(FeatureContractError, match="namespace"):
        a.lookup("FREE_TEXT", "TEST1")
    with pytest.raises(FeatureContractError, match="unmapped feature"):
        align(
            replace(study_a(), original_ids=("AliasOfTEST1", "TEST2")),
            study_b(), a,
        )


def test_one_to_many_mapping_key_and_many_to_one_collision_fail():
    base = list(annotation().entries)
    conflict = base + [
        FeatureMapEntry("HGNC_SYMBOL", "TEST1", G2, "SECOND_SYNTHETIC", "REVIEWED_ALIAS"),
    ]
    with pytest.raises(FeatureContractError, match="unique"):
        annotation(conflict)
    # Different source IDs can map to the same canonical gene; this is legal
    # for a full annotation but forbidden inside one study without a policy.
    other = base + [
        FeatureMapEntry("HGNC_SYMBOL", "OLDTEST1", G1, "ALIAS_SYNTHETIC", "REVIEWED_ALIAS"),
    ]
    a = StudyFeatures(
        "SYNTHETIC_COLLISION", "COUNTS", "HGNC_SYMBOL",
        ("TEST1", "OLDTEST1"), np.array([[True, True]], dtype=bool),
        np.array([[True, True]], dtype=bool),
    )
    with pytest.raises(FeatureContractError, match="collision"):
        align(a, study_b(), annotation(other))


def test_duplicate_feature_id_and_detected_when_unassayed_fail_closed():
    a = study_a()
    with pytest.raises(FeatureContractError, match="duplicate original"):
        replace(a, original_ids=("TEST1", "TEST1")).validate()
    with pytest.raises(FeatureContractError, match="cannot be structurally"):
        replace(a, assayed=np.array([[False, True]]),
                detected=np.array([[True, False]])).validate()


def test_assayed_undetected_must_retain_observed_zero_only():
    a = study_a()
    cross = align(a, study_b(), annotation())
    with pytest.raises(FeatureContractError, match="contradicts"):
        aligned_observation(
            a, cross.index_a, np.array([[10, 2.]]), sample_index=0,
        )
    with pytest.raises(FeatureContractError, match="nonnegative"):
        aligned_observation(
            a, cross.index_a, np.array([[10, -1.]]), sample_index=0,
        )


def test_frozen_annotation_and_alignment_cannot_drift():
    frozen = annotation()
    with pytest.raises(FeatureContractError, match="digest mismatch"):
        replace(frozen, release="SYNTHETIC_CHANGED").validate()
    cross = align(study_a(), study_b(), frozen)
    with pytest.raises(FeatureContractError, match="changed after freeze"):
        replace(cross, index_a=(1, 0, -1)).validate()


def test_versioned_gene_must_have_explicit_exact_mapping():
    with pytest.raises(FeatureContractError, match="wrong base"):
        annotation([
            FeatureMapEntry("ENSEMBL_GENE_ID", G1 + ".4", G2, "TEST", "VERSIONED_ID"),
        ])
    with pytest.raises(FeatureContractError, match="wrong base"):
        annotation([
            FeatureMapEntry("ENSEMBL_GENE_ID", G1 + ".4", G1, "TEST", "PRIMARY_ID"),
        ])
    assert annotation().lookup("ENSEMBL_GENE_ID", G1 + ".5") is None


def test_source_feature_permutation_cannot_reuse_frozen_indices():
    a, b = study_a(), study_b()
    cross = align(a, b, annotation())
    swapped = replace(a, original_ids=("TEST2", "TEST1"))
    fresh = align(swapped, b, annotation())
    assert fresh.index_a == (1, 0, -1)
    assert fresh.alignment_sha256 != cross.alignment_sha256


def test_detection_is_sample_specific_not_global():
    multi = StudyFeatures(
        "SYNTHETIC_MULTI", "COUNTS", "HGNC_SYMBOL", ("TEST1",),
        np.array([[True], [True], [False]], dtype=bool),
        np.array([[False], [True], [False]], dtype=bool),
    )
    multi.validate()
    assert multi.status(0, 0) == ObservationStatus.ASSAYED_UNDETECTED
    assert multi.status(1, 0) == ObservationStatus.ASSAYED_DETECTED
    assert multi.status(2, 0) == ObservationStatus.STRUCTURALLY_UNMEASURED


def test_mapping_release_and_hash_are_required_but_not_producer_authority():
    with pytest.raises(FeatureContractError, match="source-file SHA"):
        freeze_annotation(
            release="UNVERIFIED", annotation_file_sha256="fake",
            entries=list(annotation().entries),
        )
