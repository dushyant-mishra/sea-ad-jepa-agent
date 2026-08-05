from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml


PROJECT = Path(__file__).resolve().parents[2]
CONFIG = PROJECT / "configs/v4/stage81a1b_official_sea_ad_acquisition.yaml"
SCRIPT = PROJECT / "scripts/v4/stage81a1b_acquire_official_sea_ad.py"


def load_script():
    spec = importlib.util.spec_from_file_location("stage81a1b", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scope_and_official_portfolio_are_locked() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["stage_id"] == "stage81a1b"
    assert config["policy"]["no_model_training"] is True
    assert config["policy"]["no_final_vocabulary_freeze"] is True
    assert config["policy"]["no_donor_split_freeze"] is True
    assert config["policy"]["no_graph_rebuild"] is True
    assert config["policy"]["pathology_values_used"] is False
    required = {x["asset_id"] for x in config["assets"] if x["required"]}
    assert required == {
        "sea_ad_mtg_rna_final_2026",
        "sea_ad_pfc_a9_rna_final_2026",
        "sea_ad_mtg_atac_final_2024",
        "sea_ad_mtg_merfish_combined_2024",
    }
    assert all("amazonaws.com" in x["remote_url"] for x in config["assets"] if x["decision"] == "download")


def test_regulatory_lineages_and_integration_schema_are_explicit() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    lineages = {x["lineage"] for x in config["graph_lineages"]}
    assert lineages == {
        "stage27c_35c_expression_module_graph",
        "stage51_string_graph",
        "stage75_79_tf_target_graph",
        "motif_enhancer_atac_cistarget_evidence",
    }
    module = load_script()
    assert module.INTEGRATION_COLUMNS == [
        "tf", "target_gene", "existing_stage75_edge", "stage75_evidence_tier",
        "motif_support", "direct_motif_support", "extended_motif_support",
        "gse174367_atac_support", "gse174367_coactivity", "coactivity_sign",
        "bootstrap_sign_stability", "peak_to_gene_support", "sea_ad_multiome_support",
        "sea_ad_snatac_support", "sea_ad_expression_support", "donors_expressing_tf",
        "donors_expressing_target", "tf_in_final_gene_universe",
        "target_in_final_gene_universe", "direction_evidence_type",
        "direction_confidence", "allowed_model_role", "prohibited_claim",
        "source_paths", "source_hashes",
    ]


def test_protected_signatures_are_unchanged() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for relative, expected in config["protected_worktree_signatures"].items():
        actual = hashlib.sha256((PROJECT / relative).read_bytes()).hexdigest()
        assert actual == expected


def test_catalog_mode_is_deterministic_and_portable(tmp_path: Path) -> None:
    outputs = []
    for name in ("first", "second"):
        destination = tmp_path / name
        subprocess.run(
            [
                sys.executable, str(SCRIPT), "--project-dir", str(PROJECT),
                "--output-dir", str(destination), "--mode", "catalog",
            ],
            cwd=PROJECT,
            check=True,
        )
        outputs.append(destination)
    for filename in (
        "stage81a1b_remote_asset_catalog.csv",
        "stage81a1b_download_decisions.csv",
        "stage81a1b_download_manifest.json",
    ):
        first = (outputs[0] / filename).read_bytes()
        second = (outputs[1] / filename).read_bytes()
        assert first == second
        text = first.decode("utf-8")
        assert not any(marker in text for marker in ("C:\\", "D:\\", "/mnt/d/", "/mnt/c/", "file://"))
    for destination in outputs:
        storage = json.loads((destination / "stage81a1b_storage_preflight.json").read_text(encoding="utf-8"))
        assert storage["data_root"] == "data/external/v4/sea_ad"
        assert storage["storage_preflight_pass"] is True


def test_frozen_outputs_when_present() -> None:
    report_path = PROJECT / "results/v4/stage81a1b_acquisition_report.json"
    if not report_path.exists():
        return
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["stage81a1b_pass"] is True
    assert report["pathology_values_used"] is False
    assert report["no_model_trained"] is True
    assert report["no_graph_rebuilt"] is True
    assert report["final_vocabulary_frozen"] is False
    integration = PROJECT / "results/v4/stage81a1b_existing_regulatory_evidence_integration.csv"
    with integration.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 96
    assert len({(row["tf"], row["target_gene"]) for row in rows}) == 96
    assert all(row["direction_evidence_type"] == "predicted_response_sign_from_coactivity" for row in rows)
    assert all(row["tf_in_final_gene_universe"] == "not_frozen_stage81a1b" for row in rows)
