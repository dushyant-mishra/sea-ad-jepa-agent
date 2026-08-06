from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import yaml


PROJECT = Path(__file__).resolve().parents[2]
CONFIG = PROJECT / "configs/v4/stage81a1d_living_human.yaml"
SCRIPT = PROJECT / "scripts/v4/stage81a1d_acquire_living_human.py"


def load_script():
    spec = importlib.util.spec_from_file_location("stage81a1d", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_required_source_inventory_and_roles() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["stage_id"] == "stage81a1d"
    assert config["hvs"]["collection_id"] == "35928d1c-36fc-4f93-9a8d-0b921ab41745"
    assert config["nph52"]["record_id"] == 8319719
    assert set(config["nph52"]["required_files"]) == {"organized_data.zip", "annotations.zip"}
    required_geo = {x["study_id"] for x in config["geo"] if x["required"]}
    assert required_geo == {"GSE302937", "GSE200164", "GSE226602", "GSE226267", "GSE181279", "GSE134577", "GSE292141"}


def test_governance_and_no_fixed_storage_cap() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    policy = config["policy"]
    assert policy["no_fixed_stage_download_cap"] is True
    assert policy["pathology_firewall_active"] is True
    assert policy["no_model_training"] is True
    assert policy["no_final_vocabulary_freeze"] is True
    assert policy["no_donor_split_freeze"] is True
    assert policy["no_physical_matrix_merge"] is True


def test_hvs_live_payload_enumeration_uses_current_assets() -> None:
    module = load_script()
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    payload = {
        "datasets": [{"dataset_id": "dataset", "dataset_version_id": "version", "title": "MicroPVM",
                      "cell_count": 4, "revised_at": "now",
                      "assets": [{"filetype": "H5AD", "filesize": 12, "url": "https://example.org/version.h5ad"}]}]
    }
    rows = module.hvs_catalog(config, payload)
    assert rows[0]["source_accession"] == "dataset"
    assert rows[0]["source_version"] == "version"
    assert rows[0]["remote_url"].endswith("version.h5ad")


def test_zenodo_md5_contract_rejects_drift() -> None:
    module = load_script()
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    payload = {"revision": 1, "metadata": {"title": "NPH"}, "files": [
        {"key": name, "size": 1, "checksum": f"md5:{checksum}", "links": {"self": "https://example.org/" + name}}
        for name, checksum in (config["nph52"]["required_files"] | config["nph52"]["catalog_only_files"]).items()
    ]}
    assert len(module.zenodo_catalog(config, payload)) == 3
    payload["files"][0]["checksum"] = "md5:bad"
    try:
        module.zenodo_catalog(config, payload)
    except RuntimeError as exc:
        assert "checksum drift" in str(exc)
    else:
        raise AssertionError("checksum drift was accepted")


def test_safe_archive_member_handling(tmp_path: Path) -> None:
    module = load_script()
    safe = tmp_path / "safe.zip"
    with zipfile.ZipFile(safe, "w") as handle:
        handle.writestr("study/matrix.mtx", "x")
    assert module.archive_members(safe)[0] == ["study/matrix.mtx"]
    unsafe = tmp_path / "unsafe.tar"
    with tarfile.open(unsafe, "w") as handle:
        path = tmp_path / "value"
        path.write_text("x", encoding="utf-8")
        handle.add(path, arcname="../escape")
    try:
        module.archive_members(unsafe)
    except RuntimeError as exc:
        assert "Unsafe" in str(exc)
    else:
        raise AssertionError("unsafe member was accepted")


def test_tissue_state_and_modality_boundaries() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    geo = {x["study_id"]: x for x in config["geo"]}
    assert geo["GSE226267"]["modality"] == "scATAC-seq"
    assert geo["GSE270454"]["modality"] == "bulk_RNA-seq"
    assert geo["GSE305625"]["modality"] == "miRNA_RT_qPCR"
    assert geo["GSE200164"]["tissue_state"] == "living_csf"
    correction = config["existing_dataset_corrections"][0]
    assert correction["study_id"] == "GSE146639"
    assert correction["tissue_state"] == "postmortem_brain"
    assert correction["redownload"] is False


def test_no_raw_sequence_or_imaging_selected() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    selected = [name.lower() for study in config["geo"] for name in study["selected_patterns"]]
    assert not any(name.endswith((".fastq", ".fastq.gz", ".bam", ".cram", ".sra")) for name in selected)
    assert not any("image" in name or "genotype" in name for name in selected)


def test_pathology_sidecar_is_outside_committed_evidence() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["policy"]["sealed_root"].startswith("data/processed/")
    assert not config["policy"]["sealed_root"].startswith("results/")
    helper = PROJECT / "scripts/v4/stage81a1d_audit_nph_annotations.R"
    text = helper.read_text(encoding="utf-8")
    assert 'frame$ds_batch == "human_NPH"' in text
    assert "anno_batch" in text
    assert "anno_condition" in text


def test_synapse_policy_never_accepts_terms() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["synapse"]["accept_terms_automatically"] is False
    text = SCRIPT.read_text(encoding="utf-8")
    assert "acceptAccessRequirement" not in text
    assert "submitAccess" not in text
    assert "getChildren" in text
    assert "exceeded 5000 objects" in text


def test_protected_signatures_are_unchanged() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for name, expected in config["protected_worktree_signatures"].items():
        assert hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() == expected


def test_catalog_output_is_deterministic_and_portable(tmp_path: Path, monkeypatch) -> None:
    module = load_script()
    rows = [{"study_id": "HVS", "asset_id": "a", "remote_url": "https://example.org/a",
             "supplementary_directory": "https://example.org/", "destination": "hvs/a.h5ad"}]
    metadata = {"hvs_collection_id": "id"}
    one, two = tmp_path / "one", tmp_path / "two"
    module.write_catalog_outputs(one, rows, metadata)
    module.write_catalog_outputs(two, rows, metadata)
    assert (one / module.OUTPUTS["catalog"]).read_bytes() == (two / module.OUTPUTS["catalog"]).read_bytes()
    text = (one / module.OUTPUTS["catalog"]).read_text(encoding="utf-8")
    assert not any(marker in text for marker in ("C:\\", "D:\\", "/mnt/", "file://"))


def test_frozen_report_boundaries_when_present() -> None:
    path = PROJECT / "results/v4/stage81a1d_living_human_acquisition_report.json"
    if not path.exists():
        return
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["physical_full_matrix_merge_performed"] is False
    assert report["final_vocabulary_frozen"] is False
    assert report["donor_split_frozen"] is False
    assert report["model_trained"] is False
    assert report["postmortem_dataset_mislabeled_as_living_count"] == 0
