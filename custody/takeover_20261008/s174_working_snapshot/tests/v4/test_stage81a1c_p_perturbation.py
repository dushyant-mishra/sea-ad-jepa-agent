from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import yaml


PROJECT = Path(__file__).resolve().parents[2]
CONFIG = PROJECT / "configs/v4/stage81a1c_p_perturbation.yaml"
SCRIPT = PROJECT / "scripts/v4/stage81a1c_p_acquire_perturbation.py"


def load_script():
    spec = importlib.util.spec_from_file_location("stage81a1c_p", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scope_and_accessions_are_bounded() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["policy"]["no_fixed_stage_download_cap"] is True
    assert config["policy"]["free_space_policy"] == "monitor_capacity_without_fixed_reserve"
    assert config["policy"]["processed_data_only"] is True
    assert config["policy"]["no_model_training"] is True
    assert config["policy"]["no_perturbation_controller"] is True
    assert {row["accession"] for row in config["studies"]} == {
        "GSE178317", "GSE175721", "GSE301119", "GSE293118",
        "GSE311359", "GSE254205", "GSE241858", "GSE240609",
    }


def test_roles_and_modalities_remain_distinct() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    by_id = {row["accession"]: row for row in config["studies"]}
    assert by_id["GSE178317"]["primary_role"] == "primary_microglial_perturbation_training"
    assert by_id["GSE301119"]["cell_model"] == "primary_human_macrophage"
    assert by_id["GSE293118"]["non_targeting_controls"] == "23_guides"
    assert by_id["GSE241858"]["single_cell_or_bulk"] == "bulk"
    assert sum(bool(row["guide_assignment_available"]) for row in config["studies"]) == 5
    assert config["seurat_audit"]["expected_object_count"] == 2


def test_raw_extensions_are_forbidden() -> None:
    module = load_script()
    assert ".fastq" in module.FORBIDDEN_RAW_EXTENSIONS
    assert ".bam" in module.FORBIDDEN_RAW_EXTENSIONS
    assert ".cram" in module.FORBIDDEN_RAW_EXTENSIONS
    source = SCRIPT.read_text(encoding="utf-8")
    assert "SRA" not in source[source.index("def acquire_asset"):source.index("def preflight")]


def test_protected_signatures_are_unchanged() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for path, expected in config["protected_worktree_signatures"].items():
        assert hashlib.sha256((PROJECT / path).read_bytes()).hexdigest() == expected


def test_frozen_outputs_when_present() -> None:
    path = PROJECT / "results/v4/stage81a1c_p_acquisition_report.json"
    if not path.exists():
        return
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["stage81a1c_p_pass"] is True
    assert report["study_count"] == 8
    assert report["all_processed_assets_verified"] is True
    assert report["rds_full_object_audit_pass"] is True
    assert report["raw_sequencing_downloaded"] is False
    assert report["model_trained"] is False
    assert report["perturbation_controller_trained"] is False
