from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


PROJECT = Path(__file__).resolve().parents[2]
CONFIG = PROJECT / "configs/v4/pre_stage81a2_harmonization_contract.yaml"


def test_contract_is_virtual_and_non_destructive() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    policy = config["policy"]
    assert policy["physical_full_matrix_merge_performed"] is False
    assert policy["final_vocabulary_frozen"] is False
    assert policy["donor_split_frozen"] is False
    assert policy["pathology_values_used"] is False
    assert policy["model_trained"] is False
    assert policy["fuzzy_gene_aliasing_allowed"] is False
    assert policy["no_fixed_storage_cap"] is True


def test_protected_files_are_unchanged() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for name, expected in config["protected_worktree_signatures"].items():
        assert hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() == expected


def test_frozen_outputs_when_present() -> None:
    report_path = PROJECT / "results/v4/pre_stage81a2_harmonization_report.json"
    if not report_path.exists():
        return
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["virtual_harmonization_layer_pass"] is True
    assert report["physical_full_matrix_merge_performed"] is False
    assert report["final_vocabulary_frozen"] is False
    assert report["donor_split_frozen"] is False
    assert report["pathology_values_used"] is False
    assert report["model_trained"] is False
    assert report["fuzzy_gene_aliasing_used"] is False


def test_virtual_manifest_has_required_fields_when_present() -> None:
    path = PROJECT / "results/v4/pre_stage81a2_virtual_concat_manifest.json"
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "dataset_id", "source_hash", "source_path", "shape", "gene_namespace",
        "canonical_mapping_file", "cell_identifier_policy", "donor_field",
        "study_field", "region_field", "assay_field", "matrix_semantics",
        "allowed_role", "forbidden_role", "duplicate_group",
        "future_vocabulary_projection_status", "future_split_grouping_keys",
    }
    assert manifest["physical_full_matrix_merge_performed"] is False
    assert manifest["datasets"]
    assert all(required <= set(row) for row in manifest["datasets"])
