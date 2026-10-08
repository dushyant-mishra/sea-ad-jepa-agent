from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import yaml


PROJECT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = PROJECT / "configs/v4/stage81a0_v4_design_contract.yaml"
SCRIPT_PATH = PROJECT / "scripts/v4/build_stage81a0_failure_registry.py"
REQUIRED_CONTRACT_KEYS = {
    "schema_version",
    "stage",
    "model_lineage",
    "foundation_training_mode",
    "pathology_firewall",
    "model_sequence",
    "required_baselines",
    "required_regulatory_controls",
    "required_spatial_controls",
    "split_policy",
    "checkpoint_selection_policy",
    "dataset_role_policy",
    "agent_boundary",
    "protected_artifacts",
    "unknowns_requiring_resolution",
    "stage81a0_pass",
}
REGISTRY_FIELDS = {
    "failure_id",
    "historical_lineage",
    "category",
    "description",
    "evidence_status",
    "evidence_source_path",
    "evidence_section_or_field",
    "observed_metric_or_result",
    "scientific_consequence",
    "v4_prevention",
    "blocking_for_v4",
    "requires_human_decision",
}


def load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def run_builder(output_dir: Path) -> None:
    subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--project-dir", str(PROJECT), "--output-dir", str(output_dir)],
        check=True,
        cwd=PROJECT,
    )


def test_contract_schema_and_sequence() -> None:
    contract = load_contract()
    assert REQUIRED_CONTRACT_KEYS <= set(contract)
    assert contract["stage"] == "stage81a0"
    assert contract["stage81a0_pass"] is True
    assert [item["stage"] for item in contract["model_sequence"]] == ["v4A", "v4B", "v4C", "v4D", "v4E"]
    assert contract["split_policy"]["biological_split_unit"] == "donor"
    assert contract["split_policy"]["spatial_split_unit"] == "tissue_section"


def test_pathology_firewall_and_agent_boundary() -> None:
    contract = load_contract()
    firewall = contract["pathology_firewall"]
    assert firewall["enabled"] is True
    assert contract["foundation_training_mode"] == "self_supervised_pathology_label_free"
    assert contract["checkpoint_selection_policy"]["pathology_or_diagnosis_labels_allowed"] is False
    assert {"diagnosis", "pathology_burden", "braak", "cerad", "gfap", "iba1", "neun"} <= set(firewall["forbidden_foundation_training_fields"])
    assert contract["agent_boundary"]["included_in_foundation_checkpoint_selection"] is False


def test_required_controls_and_protected_paths() -> None:
    contract = load_contract()
    assert {"no_prior", "prior_weight_zero", "tf_label_shuffle", "edge_shuffle", "expression_matched_random_targets"} <= set(contract["required_regulatory_controls"])
    assert {"no_spatial", "real_section_local_graph", "shuffled_section_local_graph", "distance_matched_random_neighbors", "coordinates_only", "zero_cross_section_edges"} <= set(contract["required_spatial_controls"])
    protected = set(contract["protected_artifacts"])
    assert "docs/stage_c_finetuning_analysis.md" in protected
    assert "data/" in protected
    assert "web/stage78_graph_explorer/.gitignore" in protected
    assert "existing_h5ad_files" in protected


def test_registry_sources_are_real_or_explicitly_unresolved(tmp_path: Path) -> None:
    run_builder(tmp_path)
    payload = json.loads((tmp_path / "stage81a0_v4_failure_registry.json").read_text(encoding="utf-8"))
    rows = payload["records"]
    assert len(rows) >= 50
    assert len({row["failure_id"] for row in rows}) == len(rows)
    assert {row["category"] for row in rows} == {
        "data_and_preprocessing",
        "split_and_leakage",
        "representation_learning",
        "graph_modeling",
        "external_pretraining",
        "perturbation_analysis",
        "spatial_modeling_risks",
        "engineering_and_provenance",
    }
    for row in rows:
        assert set(row) == REGISTRY_FIELDS
        if row["evidence_status"] == "unresolved_from_current_repository_evidence":
            assert row["evidence_source_path"] == ""
        else:
            assert (PROJECT / row["evidence_source_path"]).is_file()


def test_outputs_are_deterministic_consistent_and_portable(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    run_builder(first)
    run_builder(second)
    names = [
        "stage81a0_v4_failure_registry.json",
        "stage81a0_v4_failure_registry.csv",
        "stage81a0_v4_stage_report.json",
    ]
    for name in names:
        a = (first / name).read_bytes()
        b = (second / name).read_bytes()
        assert a == b
        text = a.decode("utf-8")
        assert not any(marker in text for marker in ["D:\\", "C:\\", "/mnt/d/", "/mnt/c/", "file://"])
    registry = json.loads((first / names[0]).read_text(encoding="utf-8"))["records"]
    with (first / names[1]).open(encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == len(registry)
    report = json.loads((first / names[2]).read_text(encoding="utf-8"))
    assert report["stage_id"] == "stage81a0"
    assert report["documented_issue_count"] == len(registry)
    assert report["stage81a0_pass"] is True
