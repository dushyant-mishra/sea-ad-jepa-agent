from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml


PROJECT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT / "scripts/v4/stage81a1_audit_local_multimodal_assets.py"
CONFIG = PROJECT / "configs/v4/stage81a1_multimodal_inventory.yaml"
OUTPUT_NAMES = [
    "stage81a1_local_asset_manifest.csv",
    "stage81a1_rna_matrix_audit.csv",
    "stage81a1_gene_identifier_audit.csv",
    "stage81a1_regulatory_evidence_audit.csv",
    "stage81a1_graph_lineage_registry.csv",
    "stage81a1_spatial_asset_audit.csv",
    "stage81a1_perturbation_asset_audit.csv",
    "stage81a1_donor_modality_section_crosswalk.csv",
    "stage81a1_dataset_role_registry.csv",
    "stage81a1_priority_missing_assets.csv",
    "stage81a1_multimodal_inventory_report.json",
]


def run_audit(output_dir: Path) -> None:
    subprocess.run(
        [sys.executable, str(SCRIPT), "--project-dir", str(PROJECT), "--output-dir", str(output_dir)],
        cwd=PROJECT,
        check=True,
    )


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_config_respects_stage81a0_contract() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    contract = yaml.safe_load((PROJECT / config["governing_contract"]).read_text(encoding="utf-8"))
    assert config["stage_id"] == "stage81a1"
    assert config["audit_policy"]["read_only_source_access"] is True
    assert config["audit_policy"]["no_downloads"] is True
    assert config["audit_policy"]["no_model_training"] is True
    assert config["audit_policy"]["pathology_values_used"] is False
    assert contract["pathology_firewall"]["enabled"] is True
    assert contract["foundation_training_mode"] == "self_supervised_pathology_label_free"
    assert contract["split_policy"]["biological_split_unit"] == "donor"
    assert contract["split_policy"]["spatial_split_unit"] == "tissue_section"


def test_audit_outputs_are_deterministic_and_portable(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    run_audit(first)
    run_audit(second)
    forbidden = ["D:\\", "C:\\", "/mnt/d/", "/mnt/c/", "file://"]
    for name in OUTPUT_NAMES:
        a = (first / name).read_bytes()
        b = (second / name).read_bytes()
        assert a == b, name
        text = a.decode("utf-8")
        assert not any(marker in text for marker in forbidden), name


def test_expression_and_gene_contract(tmp_path: Path) -> None:
    run_audit(tmp_path)
    report = json.loads((tmp_path / OUTPUT_NAMES[-1]).read_text(encoding="utf-8"))
    assert report["stage81a1_pass"] is True
    assert report["audit_integrity_pass"] is True
    assert report["expression_v4_ready"] is True
    assert report["primary_expression_candidate_hash_verified_this_run"] is True
    assert report["candidate_cell_count"] == 40000
    assert report["candidate_donor_count"] == 89
    assert report["canonical_donor_field"] == "Donor ID"
    assert report["canonical_cell_id_field"] == "obs_names"
    assert report["v3_feature_order_recoverable"] is True
    assert report["v3_feature_overlap"] == 2957
    assert report["pathology_values_used"] is False
    assert report["no_data_downloaded"] is True
    assert report["no_data_changed"] is True
    assert report["no_model_trained"] is True
    status = report["ten_regulator_status"]
    assert set(status) == {"STAT1", "ELF1", "SPI1", "IRF8", "BACH1", "CEBPA", "RELA", "MITF", "NRF1", "STAT3"}
    assert status["CEBPA"]["present_in_primary"] is False
    assert status["RELA"]["present_in_primary"] is False
    assert all(item["present_in_full_source"] for item in status.values())


def test_graph_spatial_perturbation_and_roles(tmp_path: Path) -> None:
    run_audit(tmp_path)
    report = json.loads((tmp_path / OUTPUT_NAMES[-1]).read_text(encoding="utf-8"))
    assert report["tf_prior_ready"] is True
    assert report["graph_lineages_separated"] is True
    assert report["spatial_assets_found"] is False
    assert report["spatial_panel_ready"] is False
    assert report["spatial_coordinates_ready"] is False
    assert report["spatial_section_identity_ready"] is False
    assert report["spatial_donor_linkage_ready"] is False
    assert report["experimental_perturbation_assets_found"] is True
    assert report["external_perturbation_ready"] is False
    graph_rows = csv_rows(tmp_path / "stage81a1_graph_lineage_registry.csv")
    assert len(graph_rows) == 4
    assert len({row["lineage"] for row in graph_rows}) == 4
    stage75 = next(row for row in graph_rows if row["graph_or_evidence_id"] == "stage75_79_tf_target_graph")
    assert stage75["edge_count"] == "96"
    assert stage75["directed"] == "True"
    assert "not_activation_or_repression" in stage75["sign_semantics"]
    roles = csv_rows(tmp_path / "stage81a1_dataset_role_registry.csv")
    assert any(row["primary_role"] == "foundation_training_candidate" for row in roles)
    assert any(row["primary_role"] == "experimental_perturbation_calibration" for row in roles)


def test_protected_signatures_and_source_hashes_are_frozen() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for relative, expected in config["protected_worktree_signatures"].items():
        assert hashlib.sha256((PROJECT / relative).read_bytes()).hexdigest() == expected
    expected = {row["asset_id"]: row["expected_sha256"] for row in config["rna_candidates"]}
    assert expected == {
        "sea_ad_mtg_full_source": "9c1b48266d0a9aef76ad20fb8487d604158b10fad18dc0de85d5261ef06cb7c8",
        "sea_ad_mtg_microglia_pvm_expanded": "d0385e86da482b2f0048e2d0d83116056b889b8449cc8778828b3eae1d1eed93",
        "sea_ad_mtg_microglia_pvm_module_preserved": "fc40b7c64b8bacd42e19b28227e4b6f02c3a9a3f09aefc8cddc9ea0bde09ca5d",
    }
