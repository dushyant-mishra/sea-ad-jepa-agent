from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml


PROJECT = Path(__file__).resolve().parents[2]
CONFIG = PROJECT / "configs/v4/stage81a1c_n_normal_references.yaml"
SCRIPT = PROJECT / "scripts/v4/stage81a1c_n_acquire_normal_references.py"


def load_script():
    spec = importlib.util.spec_from_file_location("stage81a1c_n", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scope_roles_and_no_fixed_cap() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["stage_id"] == "stage81a1c_n"
    assert config["policy"]["no_fixed_stage_download_cap"] is True
    assert config["policy"]["free_space_policy"] == "monitor_capacity_without_fixed_reserve"
    assert config["policy"]["no_model_training"] is True
    assert config["policy"]["no_final_vocabulary_freeze"] is True
    assert config["policy"]["no_donor_split_freeze"] is True
    assert config["policy"]["pathology_values_used"] is False
    assert {asset["primary_role"] for asset in config["assets"]} <= {
        "normal_training_reference", "clean_normal_holdout", "technical_compatibility_only"
    }


def test_clean_holdout_is_study_isolated_and_not_duplicated() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    holdout = config["holdout_contract"]
    assert holdout["whole_study_isolation_required"] is True
    assert holdout["adult_only_required"] is True
    assert holdout["disease_label_required"] == "normal"
    microglia = next(x for x in config["catalog_only_candidates"] if x["dataset_id"].startswith("700aed"))
    assert microglia["primary_role"] == "excluded_duplicate"


def test_only_processed_compact_files_are_selected() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert len(config["assets"]) == 5
    assert {asset["file_type"] for asset in config["assets"]} == {"h5ad", "gzipped_text_matrix", "text"}
    forbidden = ("fastq", "bam", "cram", ".sra", "raw image")
    assert not any(token in asset["remote_url"].lower() for asset in config["assets"] for token in forbidden)


def test_adult_stage_parser_is_explicit() -> None:
    module = load_script()
    assert module.is_adult_stage("18-year-old stage") is True
    assert module.is_adult_stage("80 year-old and over stage") is True
    assert module.is_adult_stage("adult stage") is True
    assert module.is_adult_stage("17-year-old stage") is False
    assert module.is_adult_stage("12th week post-fertilization stage") is False


def test_protected_signatures_are_unchanged() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for path, expected in config["protected_worktree_signatures"].items():
        assert hashlib.sha256((PROJECT / path).read_bytes()).hexdigest() == expected


def test_catalog_is_deterministic_and_portable(tmp_path: Path) -> None:
    outputs = []
    for name in ("one", "two"):
        target = tmp_path / name
        subprocess.run([
            sys.executable, str(SCRIPT), "--project-dir", str(PROJECT),
            "--output-dir", str(target), "--mode", "catalog",
        ], cwd=PROJECT, check=True)
        outputs.append(target)
    module = load_script()
    for filename in (module.OUTPUTS["catalog"], module.OUTPUTS["decisions"]):
        first = (outputs[0] / filename).read_bytes()
        assert first == (outputs[1] / filename).read_bytes()
        text = first.decode("utf-8")
        assert not any(marker in text for marker in ("C:\\", "D:\\", "/mnt/", "file://"))


def test_frozen_outputs_when_present() -> None:
    path = PROJECT / "results/v4/stage81a1c_n_acquisition_report.json"
    if not path.exists():
        return
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["stage81a1c_n_pass"] is True
    assert report["clean_normal_holdout_resolved"] is True
    assert report["normal_training_reference_candidate_resolved"] is True
    assert report["normal_adult_microglia_coverage_assessed"] is True
    assert report["microglia_partition_counts_assumed_equivalent"] is False
    assert report["pathology_values_used"] is False
    assert report["model_trained"] is False
    assert report["final_vocabulary_frozen"] is False
    assert report["donor_split_frozen"] is False
