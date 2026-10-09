"""Independent workload-scale and integrity attacks on feature lookup V1.

All identifiers in this suite are synthetic and are NOT an annotation release.
The objective is to verify that joining large assay universes does not perform
quadratically many independent annotation validations, without relaxing the
frozen digest, namespace or collision guards.
"""
from dataclasses import replace
from unittest.mock import patch

import numpy as np
import pytest

from sea_ad_jepa.perturbation.cross_study_feature_contract_v1 import (
    FeatureContractError, FeatureMapEntry, FrozenAnnotation,
    StudyFeatures, align, freeze_annotation,
)


def fixture(n=2500):
    entries = []
    symbols = []
    ensembl_ids = []
    for i in range(n):
        ens = f"ENSG{i+1:011d}"
        symbol = f"SYNTHETIC_ID_{i}"
        symbols.append(symbol)
        ensembl_ids.append(ens + ".1")
        entries.append(FeatureMapEntry(
            "ENSEMBL_GENE_ID", ens + ".1", ens,
            "SYNTHETIC_FIXTURE_NOT_ANNOTATION", "VERSIONED_ID",
        ))
        entries.append(FeatureMapEntry(
            "HGNC_SYMBOL", symbol, ens,
            "SYNTHETIC_FIXTURE_NOT_ANNOTATION", "PRIMARY_ID",
        ))
    frozen = freeze_annotation(
        release="TEST_ONLY_FAKE_ANNOTATION",
        annotation_file_sha256="e" * 64,
        entries=entries,
    )
    a = StudyFeatures(
        "SYNTHETIC_A", "SYNTHETIC_ASSAY_A", "HGNC_SYMBOL",
        tuple(symbols),
        np.ones((1, n), dtype=bool),
        np.zeros((1, n), dtype=bool),
    )
    b = StudyFeatures(
        "SYNTHETIC_B", "SYNTHETIC_ASSAY_B", "ENSEMBL_GENE_ID",
        tuple(ensembl_ids),
        np.ones((1, n), dtype=bool),
        np.zeros((1, n), dtype=bool),
    )
    return frozen, a, b


def test_large_join_validates_frozen_annotation_once_not_once_per_gene():
    annotation, a, b = fixture()
    original = FrozenAnnotation.validate
    with patch.object(FrozenAnnotation, "validate", autospec=True) as wrapped:
        # Capture the original BEFORE patching: otherwise this test recurses
        # through the mock instead of actually validating the source digest.
        wrapped.side_effect = lambda self: original(self)
        result = align(a, b, annotation)
    assert wrapped.call_count == 1
    assert len(result.canonical_ids) == 2500
    assert result.index_a == tuple(range(2500))
    assert result.index_b == tuple(range(2500))


def test_direct_lookup_revalidates_changed_digest():
    annotation, _, _ = fixture(4)
    first = annotation.lookup("HGNC_SYMBOL", "SYNTHETIC_ID_1")
    assert first == "ENSG00000000002"
    wrong = replace(annotation, contract_sha256="f" * 64)
    with pytest.raises(FeatureContractError, match="digest mismatch"):
        wrong.lookup("HGNC_SYMBOL", "SYNTHETIC_ID_1")


def test_large_join_fails_closed_for_alias_missing_from_frozen_release():
    annotation, a, b = fixture(200)
    altered = list(a.original_ids)
    altered[-1] = "UNREVIEWED_SYNTHETIC_ALIAS"
    with pytest.raises(FeatureContractError, match="unmapped feature"):
        align(replace(a, original_ids=tuple(altered)), b, annotation)


def test_large_join_rejects_same_canonical_gene_twice():
    annotation, a, b = fixture(200)
    entries = list(annotation.entries)
    entries.append(FeatureMapEntry(
        "HGNC_SYMBOL", "DIFFERENT_ALIAS_0", "ENSG00000000001",
        "SYNTHETIC_FIXTURE_NOT_ANNOTATION", "REVIEWED_ALIAS",
    ))
    extended = freeze_annotation(
        release=annotation.release,
        annotation_file_sha256=annotation.annotation_file_sha256,
        entries=entries,
    )
    ids = list(a.original_ids)
    ids[-1] = "DIFFERENT_ALIAS_0"
    with pytest.raises(FeatureContractError, match="collision"):
        align(replace(a, original_ids=tuple(ids)), b, extended)
