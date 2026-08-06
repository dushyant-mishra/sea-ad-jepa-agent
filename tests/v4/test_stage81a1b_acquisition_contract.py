from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import h5py
import numpy as np
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
    assert config["schema_version"] == "2.0"
    assert config["contract_revision"] == "june_2026_complete_multiregion"
    required = [x for x in config["assets"] if x["required"]]
    assert len(required) == 17
    assert all("amazonaws.com" in x["remote_url"] for x in config["assets"] if x["decision"] == "download")
    local = next(x for x in config["assets"] if x["asset_id"] == "local_mtg_rna_final_2024")
    resolved = (PROJECT / config["policy"]["data_root"] / local["destination"]).resolve()
    assert resolved == (PROJECT / "data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad").resolve()


def test_governing_ancestry_and_region_inventory() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert {
        "16e287766be2981531d55f1b99404b85b61cf679",
        "7523399d639119071a0e3cc5873b2303d827fc5f",
    }.issubset(config["required_ancestor_commits"])
    regions = config["discovery"]["official_region_inventory"]
    assert len(regions) == 11
    assert set(regions) == {"MTG", "PFC_A9_DFC", "STG", "V1C", "MEC", "LEC", "HIP", "ITG", "AnG", "FI", "Caudate_Nucleus"}


def test_current_authorities_and_deprecated_source_preservation() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assets = {x["asset_id"]: x for x in config["assets"]}
    assert assets["sea_ad_mtg_rna_final_2026"]["release"] == "2026-06-22"
    assert assets["sea_ad_pfc_a9_rna_final_2026"]["region"] == "PFC_A9_DFC"
    assert assets["sea_ad_multiregion_immune_rna_final_2026"]["role"] == "microglia_specialization_candidate"
    assert assets["local_mtg_rna_final_2024"]["decision"] == "preserve_deprecated_official_source"
    rna = [x for x in config["assets"] if x["modality"] == "snRNA" and x["decision"] == "download"]
    by_region = {}
    for asset in rna:
        by_region.setdefault(asset["region"], []).append(asset)
    assert all(len(items) == 1 for region, items in by_region.items() if region != "MULTIREGION_10")
    assert next(x for x in rna if x["region"] == "Caudate_Nucleus")["object_scope"] == "all_nuclei_only_current_consolidated_release"


def test_modality_spatial_fragment_and_etag_contracts() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    allowed = {"processed_current", "processed_historical", "fragments_only", "announced_pending", "not_released", "access_blocked", "not_applicable"}
    for row in config["modality_availability"]:
        assert row["rna_status"] in allowed
        assert row["atac_status"] in allowed
        assert row["fragments_status"] in allowed
    assert sum(row["atac_status"] == "processed_current" for row in config["modality_availability"]) == 1
    modalities = {x["modality"] for x in config["assets"] if x["required"]}
    assert {"MERFISH", "MERSCOPE", "Xenium", "snATAC"}.issubset(modalities)
    assert all(row["fragments_status"] == "access_blocked" for row in config["modality_availability"])
    module = load_script()
    catalog = module.catalog_rows(config)
    multipart = [row for row in catalog if "-" in str(row["etag"])]
    assert multipart
    assert all(row["checksum_type"] == "s3_multipart_etag_not_a_checksum" for row in multipart)


def test_download_safety_and_compute_boundary_are_explicit() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["policy"]["minimum_free_bytes_after_acquisition"] == 805306368000
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"--continue-at", "-"' in source
    assert "part.stat().st_size != expected_size" in source
    assert "bounded_open_status(part)" in source
    assert "os.replace(part, target)" in source
    download_block = source[source.index("def download_asset("):source.index("def download_documentation(")]
    assert download_block.index("bounded_open_status(part)") < download_block.index("os.replace(part, target)")
    assert "import torch" not in source
    assert ".toarray(" not in source
    assert "stage81a1b_download_events.jsonl" in source
    assert "stage81a1b_download_ledger.json" in source
    assert "mtime_ns" in source
    assert "verification_schema_version" in source


def test_perturbation_next_stage_registry_is_planning_only() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    rows = config["perturbation_next_stage_candidates"]
    assert {x["accession"] for x in rows} == {
        "GSE178317", "GSE175721", "GSE301119", "GSE293118",
        "GSE311359", "GSE254205", "GSE241858", "GSE240609",
    }
    assert all(x["official_record_verified"] is True for x in rows)
    assert all(x["download_decision_for_stage81a1c"] == "acquire_processed" for x in rows)


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


def test_repair_contract_uses_exact_safe_identity_fields() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["policy"]["metadata_csv_data_rows_must_not_be_read"] is True
    assert config["identity_fields"]["snRNA"]["method"][0] == "method"
    assert "Section" in config["identity_fields"]["MERFISH"]["section"]
    assert "Total microinfarcts in screening sections" not in config["identity_fields"]["MERFISH"]["section"]
    assert config["commit_provenance"]["original_stage81a1b_commit"] == "e70be4f69d9cd06ddbbaa30952ffd58fbf4b25b4"
    assert config["commit_provenance"]["june2026_expansion_commit"] == "94137398df48677c96602ee7d1c6260a7a071230"
    assert config["commit_provenance"]["transport_update_commit"] == "9bccfc0e5760091554801e9a7a4044dd7c441e1c"


def test_append_only_event_chain_and_ledger_are_deterministic(tmp_path: Path) -> None:
    module = load_script()
    path = tmp_path / "events.jsonl"
    kwargs = dict(
        asset_id="asset", event_type="discovered", relative_path="data/asset.h5ad",
        expected_size=10, observed_size=0, status="known", source_commit="abc",
        tool_version="test",
    )
    first = module.append_event(path, **kwargs)
    original = path.read_bytes()
    duplicate = module.append_event(path, **kwargs)
    assert first == duplicate
    assert path.read_bytes() == original
    module.append_event(path, **{**kwargs, "event_type": "size_verified", "observed_size": 10})
    events = module.read_event_log(path)
    assert len(events) == 2
    assert events[1]["previous_event_hash"] == events[0]["event_hash"]
    ledger = module.build_download_ledger(events)
    assert ledger["event_count"] == 2
    assert ledger["assets"][0]["event_types"] == ["discovered", "size_verified"]


def test_bound_verification_reuse_requires_size_mtime_and_schema(tmp_path: Path) -> None:
    module = load_script()
    project = tmp_path
    path = project / "data" / "small.h5ad"
    path.parent.mkdir(parents=True)
    with h5py.File(path, "w") as handle:
        handle.create_dataset("X", data=np.zeros((2, 3), dtype=np.float32))
        obs = handle.create_group("obs")
        obs.attrs["_index"] = "index"
        obs.create_dataset("index", data=np.asarray([b"a", b"b"]))
        var = handle.create_group("var")
        var.attrs["_index"] = "index"
        var.create_dataset("index", data=np.asarray([b"g1", b"g2", b"g3"]))
    config = {"policy": {"verification_schema_version": "1.0", "verification_tool_version": "test"}}
    first = module.verify_bound_asset(project, config, path, "commit-a", {})
    assert first["hash_computed_this_run"] is True
    second = module.verify_bound_asset(project, config, path, "commit-b", {})
    assert second["hash_computed_this_run"] is False
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 2_000_000_000))
    third = module.verify_bound_asset(project, config, path, "commit-c", {})
    assert third["hash_computed_this_run"] is True


def test_metadata_audit_is_header_only_and_outputs_are_registered() -> None:
    module = load_script()
    source = SCRIPT.read_text(encoding="utf-8")
    block = source[source.index("def remote_csv_header("):source.index("def regional_metadata_audit(")]
    assert ".readline(" in block
    assert ".read(" not in block
    assert module.metadata_url_for_asset({
        "asset_id": "x",
        "remote_url": "https://example.org/SEAAD_MTG_RNAseq_final-nuclei.2026-06-22.h5ad",
    }).endswith("SEAAD_MTG_RNAseq_final-nuclei_metadata.2026-06-22.csv")
    for key in ("events", "ledger", "identity_crosswalk", "matrix_semantics", "metadata_catalog", "metadata_schema", "metadata_decisions", "library_swap"):
        assert key in module.OUTPUT_NAMES


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
    assert report["regional_metadata_audit_complete"] is True
    assert report["matrix_semantics_registry_ready"] is True
    assert report["donor_library_specimen_crosswalk_ready"] is True
    assert "processed_multiome_ready" not in report
    assert report["paired_multiome_contract_ready"] == report["exact_rna_atac_barcode_linkage_verified"]
    integration = PROJECT / "results/v4/stage81a1b_existing_regulatory_evidence_integration.csv"
    with integration.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 96
    assert len({(row["tf"], row["target_gene"]) for row in rows}) == 96
    assert all(row["direction_evidence_type"] == "predicted_response_sign_from_coactivity" for row in rows)
    assert all(row["tf_in_final_gene_universe"] == "not_frozen_stage81a1b" for row in rows)
