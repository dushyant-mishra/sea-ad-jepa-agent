"""Synthetic red-team of explicit Entrez mapping; NOT real annotation authentication."""
from dataclasses import replace
import numpy as np
import pytest

from sea_ad_jepa.perturbation.cross_study_feature_contract_v1 import (
    FeatureContractError, FeatureMapEntry, StudyFeatures, align,
    freeze_annotation, aligned_observation,
)


def annotation():
    # These IDs and crosswalks are SYNTHETIC, never a real annotation source.
    return freeze_annotation(
        release="SYNTHETIC_TEST_ONLY",
        annotation_file_sha256="e" * 64,
        entries=[
            FeatureMapEntry("ENTREZ_GENE_ID", "101", "ENSG00000000001",
                            "SYNTHETIC_ENTRY_1", "PRIMARY_ID"),
            FeatureMapEntry("ENTREZ_GENE_ID", "102", "ENSG00000000002",
                            "SYNTHETIC_ENTRY_2", "PRIMARY_ID"),
            FeatureMapEntry("HGNC_SYMBOL", "FAKE_ONE", "ENSG00000000001",
                            "SYNTHETIC_ENTRY_1", "PRIMARY_ID"),
        ],
    )


def study(name, namespace, ids, assayed, detected):
    return StudyFeatures(name, "SYNTHETIC_ASSAY", namespace, tuple(ids),
                         np.asarray([assayed], dtype=bool),
                         np.asarray([detected], dtype=bool))


def test_explicit_entrez_symbol_alignment_and_unmeasured_not_zero():
    ann = annotation()
    a = study("A", "ENTREZ_GENE_ID", ["101", "102"], [True, True], [True, False])
    b = study("B", "HGNC_SYMBOL", ["FAKE_ONE"], [True], [True])
    joint = align(a, b, ann)
    assert joint.canonical_ids == ("ENSG00000000001", "ENSG00000000002")
    assert joint.index_a == (0, 1)
    assert joint.index_b == (0, -1)
    output, measured, detected = aligned_observation(
        b, joint, np.array([[4.0]]), side="b", sample_index=0,
    )
    assert output[0] == 4.0 and np.isnan(output[1])
    assert measured.tolist() == [True, False]
    assert detected.tolist() == [True, False]


@pytest.mark.parametrize("bad", ["", "0", "-1", "00101", "101.0", " 101", "101 ", "ENSG00000000001"])
def test_entrez_rejects_noncanonical_source_keys(bad):
    with pytest.raises(FeatureContractError):
        freeze_annotation(release="SYNTHETIC_TEST_ONLY",
                          annotation_file_sha256="e"*64,
                          entries=[FeatureMapEntry("ENTREZ_GENE_ID", bad,
                              "ENSG00000000001", "SYNTHETIC", "PRIMARY_ID")])


def test_no_inference_for_entrez_absent_frozen_annotation():
    ann = annotation()
    a = study("A", "ENTREZ_GENE_ID", ["999"], [True], [True])
    b = study("B", "HGNC_SYMBOL", ["FAKE_ONE"], [True], [True])
    with pytest.raises(FeatureContractError, match="unmapped feature"):
        align(a, b, ann)


def test_entrez_symbol_canonical_collision_not_silently_deduplicated():
    ann = annotation()
    a = study("A", "ENTREZ_GENE_ID", ["101", "101"], [True, True], [True, True])
    b = study("B", "HGNC_SYMBOL", ["FAKE_ONE"], [True], [True])
    with pytest.raises(FeatureContractError, match="duplicate original feature"):
        align(a, b, ann)


def test_entrez_mapping_requires_source_evidence_and_frozen_digest():
    ann = annotation()
    with pytest.raises(FeatureContractError, match="annotation evidence"):
        freeze_annotation(release="SYNTHETIC_TEST_ONLY", annotation_file_sha256="e"*64,
            entries=[FeatureMapEntry("ENTREZ_GENE_ID", "101",
                    "ENSG00000000001", "", "PRIMARY_ID")])
    with pytest.raises(FeatureContractError, match="digest mismatch"):
        replace(ann, contract_sha256="f"*64).lookup("ENTREZ_GENE_ID", "101")


def test_entrez_alias_cannot_claim_primary_mapping_without_review():
    with pytest.raises(FeatureContractError, match="primary evidence"):
        freeze_annotation(release="SYNTHETIC_TEST_ONLY", annotation_file_sha256="e"*64,
            entries=[FeatureMapEntry("ENTREZ_GENE_ID", "101",
                    "ENSG00000000001", "SYNTHETIC", "REVIEWED_ALIAS")])
