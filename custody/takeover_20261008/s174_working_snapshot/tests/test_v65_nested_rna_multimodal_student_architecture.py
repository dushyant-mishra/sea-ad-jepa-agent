from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/"results/v64/V65_NESTED_RNA_MULTIMODAL_STUDENT_ARCHITECTURE_V1.json"
DOC=ROOT/"docs/agent/V65_NESTED_RNA_MULTIMODAL_STUDENT_ARCHITECTURE_CONTRACT_20260930.md"


def _state():
    return json.loads(STATE.read_text())


def test_multimodal_student_extends_but_does_not_replace_universal_rna():
    p=_state()
    assert p["universal"]["student_input"]=="LAWFUL_RNA_ONLY"
    assert p["universal"]["teacher"]=="RNA_EMA_TEACHER"
    assert p["universal"]["paired_subset_sets_universal_mass"] is False
    assert p["multimodal"]["strict_information_extension"] is True
    assert p["multimodal"]["replacement_for_universal_rna"] is False


def test_private_state_cannot_be_compulsory_rna_target():
    p=_state()
    x=p["shared_private"]
    assert x["shared_requires_recoverability_authority"] is True
    assert x["partial_shared_projection_only"] is True
    assert x["private_compulsory_rna_loss"] is False
    assert x["poor_rna_prediction_assigns_private"] is False
    assert x["private_residual_preserved"] is True


def test_missing_modality_is_not_zero_and_inference_is_labeled():
    p=_state()
    x=p["missing_modality"]
    assert x["not_measured_is_zero"] is False
    assert x["rna_only_private_state"]=="NOT_OBSERVED_OR_NOT_IDENTIFIABLE_FROM_CURRENT_EVIDENCE"
    assert x["probabilistic_private_inference_must_be_labeled_inferred"] is True
    assert x["availability_mask_is_biology_feature_by_default"] is False


def test_shared_alignment_is_rotation_aware_not_raw_coordinate_identity():
    p=_state()
    x=p["alignment"]
    assert x["raw_coordinate_equality_required"] is False
    assert x["rotation_aware"] is True
    assert x["test_may_select_rotation"] is False
    assert "LOCKED_RECOVERABLE_SUBSPACE" in x["qualified_object"]


def test_real_shared_rank_is_not_predeclared_before_recoverability():
    p=_state()
    r=p["relation_to_recoverability"]
    assert r["current_factor"]=="Z_priv_ATAC_V1"
    assert r["real_shared_rank"]=="UNRESOLVED"
    assert r["real_paired_execution_authorized"] is False
    assert r["test_opened"] is False


def test_multimodal_training_remains_off():
    p=_state()
    g=p["governance"]
    assert p["multimodal"]["training_authorized"] is False
    assert g["training"]=="OFF"
    assert g["multimodal_training"]=="NOT_AUTHORIZED"
    assert g["current_runtime_modified"] is False
    assert g["stage4"]=="NOT_AUTHORIZED"


def test_contract_forbids_literal_latent_subtraction_as_default_science():
    t=DOC.read_text()
    assert "Literal coordinate subtraction" in t
    assert "is not authorized as the scientific definition" in t
    assert "What biological state becomes identifiable" in t


def test_contract_requires_missing_private_uncertainty_and_comparability():
    t=DOC.read_text()
    assert "private-state uncertainty rises" in t
    assert "RNA-only and paired cells remain comparable" in t
    assert "must not be moved into a wholly separate latent universe" in t
