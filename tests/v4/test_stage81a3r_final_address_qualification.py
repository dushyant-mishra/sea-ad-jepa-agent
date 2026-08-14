"""Focused deterministic contracts for Stage81A3R synthetic qualification."""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml

from sea_ad_jepa.v4.a3r_qualification import anti_topk_fixture, contextual_distance
from sea_ad_jepa.v4.ipb_jepa import sample_uniform_target_blocks

ROOT = Path(__file__).resolve().parents[2]
CONFIG = yaml.safe_load((ROOT / "configs/v4/stage81a3r_final_address_qualification.yaml").read_text())
EXPECTED_HASH = "5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff"


def test_frozen_registry_hash_count_uniqueness_and_classes() -> None:
    registry = pd.read_csv(ROOT / CONFIG["inputs"]["registry"])
    audit = json.loads((ROOT / CONFIG["inputs"]["injectivity_audit"]).read_text())
    assert len(registry) == 41238
    assert registry.molecular_address_id.is_unique
    assert registry.molecular_address_index.is_unique
    assert registry.molecular_address_index.tolist() == list(range(41238))
    assert registry.identity_class.value_counts().to_dict() == {
        "current_exact": 40422, "legacy_exact": 773, "source_native_anchored": 43,
    }
    assert audit["registry_semantic_hash"] == EXPECTED_HASH
    assert audit["future_only_addresses"] == 0


def test_measurement_support_contract_and_zero_semantics() -> None:
    support = pd.read_csv(ROOT / CONFIG["inputs"]["measurement_support"])
    assert support.matrix_id.nunique() == 42
    assert len(support) == 1731996
    assert not support.duplicated(["matrix_id", "molecular_address_id"]).any()
    assert support.measured_zero_distinct_from_unmeasured.all()


def test_graph_free_masker_exact_measured_deterministic() -> None:
    measured = torch.tensor([
        [True, True, False, True, True, False, True, True, True, True],
        [True, False, True, True, False, True, True, True, True, True],
    ])
    kwargs = dict(
        production_seed=17, cell_indices=torch.tensor([3, 9]), sample_pass=2,
        view_index=1, mask_fraction=0.40, block_count=4,
    )
    first = sample_uniform_target_blocks(measured, **kwargs)
    second = sample_uniform_target_blocks(measured, **kwargs)
    assert torch.equal(first.hidden_mask, second.hidden_mask)
    assert torch.equal(first.indices, second.indices)
    assert first.hidden_mask.sum(1).tolist() == [3, 3]
    assert not torch.any(first.hidden_mask & ~measured)


def test_graph_free_masker_api_cannot_read_expression_or_identity() -> None:
    parameters = set(inspect.signature(sample_uniform_target_blocks).parameters)
    assert parameters == {
        "measurement_mask", "production_seed", "cell_indices", "sample_pass",
        "view_index", "mask_fraction", "block_count",
    }
    executable_names = {value.lower() for value in sample_uniform_target_blocks.__code__.co_names}
    executable_names.update(value.lower() for value in sample_uniform_target_blocks.__code__.co_varnames)
    for forbidden in ("expression", "correlation", "dataset_id", "matrix_id", "identity_class"):
        assert forbidden not in executable_names


def test_full_h_evaluation_is_not_mean_pool_or_raw_concatenation() -> None:
    source = (ROOT / "scripts/v4/stage81a3r_final_address_qualification.py").read_text()
    tree = ast.parse(source)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "evaluate_context")
    rendered = ast.unparse(function)
    assert "centered_normalized_linear_kernels(h_train, h_test)" in rendered
    assert ".mean(dim=1" not in rendered and ".mean(1" not in rendered
    assert "torch.cat((states" not in rendered and "concatenate((states" not in rendered


def test_width_256_is_guarded_by_capacity_gate() -> None:
    source = (ROOT / "scripts/v4/stage81a3r_final_address_qualification.py").read_text()
    assert 'if gate["width_160_gate_fired"]:' in source
    assert 'width=256' in source
    assert source.index('if gate["width_160_gate_fired"]:') < source.index('width=256')
    assert CONFIG["architecture"]["d_gene"] == 160


def test_structural_unmeasurement_excluded_from_contextual_distance() -> None:
    reference = torch.zeros((1, 3, 2))
    candidate = reference.clone()
    candidate[:, 2] = 1000.0
    support = torch.tensor([[True, True, False]])
    assert contextual_distance(candidate, reference, support).tolist() == [0.0]


def test_u_bio_and_u_meas_perturbations_are_distinct() -> None:
    assert CONFIG["uncertainty"]["biology_fractions"] == [0.20, 0.40, 0.60, 0.80, 1.00]
    assert CONFIG["uncertainty"]["measurement_quality"] == [0.25, 0.50, 0.75, 1.00]
    source = (ROOT / "scripts/v4/stage81a3r_final_address_qualification.py").read_text()
    assert '"U_BIO"' in source and '"U_MEAS"' in source
    assert '"combined_score_created": False' in source


def test_u_meas_level_one_is_independent_remeasurement_not_self_comparison() -> None:
    summary = json.loads((ROOT / CONFIG["outputs"]["uncertainty_summary"]).read_text())
    assert "independent Poisson remeasurement" in summary["u_meas_reference_definition"]
    assert "not an observation compared with itself" in summary["u_meas_reference_definition"]
    assert "zero is not expected" in summary["u_meas_level_1_interpretation"]
    assert "not a calibrated U_MEAS" in summary["u_meas_level_1_interpretation"]


def test_clean_worktree_portability_ledger_is_complete_and_not_a3r_regression() -> None:
    ledger = pd.read_csv(ROOT / CONFIG["outputs"]["portability_ledger"])
    summary = json.loads((ROOT / CONFIG["outputs"]["portability_summary"]).read_text())
    assert len(ledger) == 28
    assert ledger.test_node_id.is_unique
    assert set(ledger.classification) <= {
        "MISSING_IGNORED_HISTORICAL_ARTIFACT",
        "STALE_HISTORICAL_UCDQ_MANIFEST",
        "A3R_REGRESSION",
        "OTHER",
    }
    assert not ledger.exercised_new_a3r_code.any()
    assert "A3R_REGRESSION" not in set(ledger.classification)
    assert summary["clean_worktree_passed"] == 845
    assert summary["clean_worktree_failed"] == 28
    assert summary["a3r_regressions"] == 0


def test_anti_topk_selector_is_label_blind_and_loses_rare_signal() -> None:
    result = anti_topk_fixture(genes=8192, cells=512, seed=813901)
    assert result["selector_inputs"] == ["detection", "variance"]
    assert result["selector_accessed_latent_labels"] is False
    assert result["broad_genes_selected"] > 800
    assert result["rare_genes_selected"] == 0
    assert result["full_broad_r2"] >= 0.20 and result["topk_broad_r2"] >= 0.20
    assert result["full_rare_auroc"] >= 0.75
    assert result["topk_rare_auroc"] < result["full_rare_auroc"] - 0.10


def test_no_real_rna_dev_sealed_or_pathology_paths() -> None:
    serialized = json.dumps(CONFIG).lower()
    assert "pathology" not in serialized
    assert "dev_rna" not in serialized and "sealed_rna" not in serialized
    allowed = set(CONFIG["inputs"])
    assert allowed == {"registry", "measurement_support", "injectivity_audit"}
    for path in CONFIG["inputs"].values():
        lowered = path.lower()
        assert all(term not in lowered for term in ("h5ad", "expression", "counts", "pathology", "dev", "sealed"))


def test_model_inputs_do_not_include_source_or_identity_class() -> None:
    source = (ROOT / "scripts/v4/stage81a3r_final_address_qualification.py").read_text()
    for call in ("online(", "target(", "model("):
        assert call in source
    assert "dataset_or_matrix_id_supplied_to_encoder\": False" in source
    signature = set(inspect.signature(__import__("sea_ad_jepa.v4.ipb_jepa", fromlist=["IPBEncoder"]).IPBEncoder.forward).parameters)
    assert signature == {"self", "gene_ids", "expression", "measurement_mask", "hidden_target_mask", "view"}
