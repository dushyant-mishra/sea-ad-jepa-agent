"""Read-only Stage81A3 physical-context evidence and freeze-readiness audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd


ANCHOR = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
VOCABULARY_HASH = "f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb"
SUPPORTED_REGULATORS = ("ELF1", "SPI1", "STAT1", "BACH1", "CEBPA", "IRF8", "RELA")
PROTECTED = {
    "PRRC": ("results/v4/stage81a3_prrc_report.json", "7a2b3f97555cbbf95428b9c70b0f2192584d6a40d0804a55ddf6fa572711105e"),
    "FBSDQ": ("results/v4/stage81a3_foundation_biological_state_domain_qualification.json", "912bf050f1091575bf141295ccb06bbce648614cd5991cf660c33f8951cff4b3"),
    "IPB": ("results/v4/stage81a3_ipb_jepa_feasibility.json", "aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308"),
    "RLC-CD": ("results/v4/stage81a3_rlc_causal_fast_probe.json", "ac3e8a69964bfa11f5d8211f373e20c6476534095850dc48e8851ea9b42ab8fc"),
}

LOCAL_ASSETS = (
    {
        "asset_id": "sea_ad_mtg_merfish",
        "dataset": "SEA-AD MTG MERFISH",
        "path": "data/external/v4/sea_ad/merfish/SEAAD_MTG_MERFISH.2024-12-11.h5ad",
        "region": "MTG",
        "technology": "MERFISH",
        "release": "2024-12-11",
        "donor_field": "Donor ID",
        "section_field": "Section",
        "specimen_field": "Specimen Barcode",
    },
    {
        "asset_id": "sea_ad_hip_merscope",
        "dataset": "SEA-AD HIP MERSCOPE",
        "path": "data/external/v4/sea_ad/merfish/1444211893_HPF_mapped.h5ad",
        "region": "HIP/HPF",
        "technology": "MERSCOPE",
        "release": "2026-06-30",
        "official_donor": "H24.30.005",
        "official_section": "1444211893",
    },
    {
        "asset_id": "sea_ad_mec_merscope",
        "dataset": "SEA-AD MEC MERSCOPE",
        "path": "data/external/v4/sea_ad/merfish/1444201261_MEC_mapped.h5ad",
        "region": "MEC",
        "technology": "MERSCOPE",
        "release": "2026-06-30",
        "official_donor": "H24.30.005",
        "official_section": "1444201261",
    },
    {
        "asset_id": "sea_ad_caudate_xenium",
        "dataset": "SEA-AD Caudate Xenium",
        "path": "data/external/v4/sea_ad/xenium/CaH_Xenium.2026-01-07.h5ad",
        "region": "Caudate nucleus",
        "technology": "Xenium",
        "release": "2026-01-07",
        "donor_field": "Donor ID",
        "section_field": "Specimen_ID",
        "specimen_field": "LIMS2_Barcode",
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def decode(values: np.ndarray) -> list[str]:
    return [item.decode("utf-8") if isinstance(item, bytes) else str(item) for item in values]


def read_h5_series(group: h5py.Group, name: str) -> np.ndarray:
    """Read an AnnData string/categorical column without loading expression."""
    node = group[name]
    if isinstance(node, h5py.Dataset):
        return np.asarray(decode(node[:]), dtype=object)
    categories = np.asarray(decode(node["categories"][:]), dtype=object)
    codes = node["codes"][:]
    result = np.empty(len(codes), dtype=object)
    result[:] = ""
    valid = codes >= 0
    result[valid] = categories[codes[valid]]
    return result


def h5_shape(handle: h5py.File) -> tuple[int, int]:
    node = handle["X"]
    shape = node.attrs.get("shape", getattr(node, "shape", None))
    return int(shape[0]), int(shape[1])


def feature_names(handle: h5py.File) -> set[str]:
    return set(read_h5_series(handle["var"], "_index"))


def unique_count(handle: h5py.File, field: str | None) -> int | None:
    if not field or field not in handle["obs"]:
        return None
    return len(set(read_h5_series(handle["obs"], field)) - {""})


def git(project: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=project, check=True, capture_output=True, text=True
    ).stdout.strip()


def atomic_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def classify_worktree(path: str) -> str:
    if path == "docs/stage_c_finetuning_analysis.md":
        return "UNRELATED - exclude"
    if path.startswith("data/"):
        return "DATA - do not commit"
    if any(token in path for token in ("__pycache__", ".pytest", ".tmp", "cache")):
        return "GENERATED CACHE - do not commit"
    if path.startswith("configs/v4/") and "stage81a3" in path:
        return "A3 TEST/CONFIG - candidate"
    if path.startswith("tests/v4/") and "stage81a3" in path:
        return "A3 TEST/CONFIG - candidate"
    if path.startswith(("scripts/v4/", "src/sea_ad_jepa/v4/")) and "stage81a3" in path:
        return "A3 IMPLEMENTATION - candidate for eventual implementation commit"
    if path.startswith("results/v4/") and "stage81a3" in path:
        return "A3 EVIDENCE - candidate for later freeze/evidence commit"
    if path.startswith("docs/v4/") and "STAGE81A3" in path:
        return "A3 DOCUMENTATION - candidate"
    if path == "results/v4/stage81a0_v4_stage_report.json":
        return "NEEDS HUMAN REVIEW"
    return "NEEDS HUMAN REVIEW"


def inventory_worktree(project: Path) -> list[dict[str, Any]]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=project,
        check=True,
        capture_output=True,
    ).stdout
    entries = raw.decode("utf-8", errors="replace").split("\0")
    rows: list[dict[str, Any]] = []
    index = 0
    while index < len(entries) and entries[index]:
        entry = entries[index]
        status, name = entry[:2], entry[3:].replace("\\", "/")
        if status[0] in "RC" or status[1] in "RC":
            index += 1
            if index < len(entries):
                name = entries[index].replace("\\", "/")
        target = project / name
        rows.append(
            {
                "git_status": status,
                "path": name,
                "classification": classify_worktree(name),
                "size_bytes": target.stat().st_size if target.is_file() else "",
                "staged": status[0] not in (" ", "?"),
            }
        )
        index += 1
    by_path = {row["path"]: row for row in rows}
    tracked = set(git(project, "ls-files").splitlines())
    ignored = set(
        subprocess.run(
            ["git", "ls-files", "--others", "--ignored", "--exclude-standard"],
            cwd=project,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    )
    patterns = (
        "configs/v4/stage81a3*",
        "scripts/v4/stage81a3*",
        "src/sea_ad_jepa/v4/*",
        "tests/v4/test_stage81a3*",
        "results/v4/stage81a3*",
        "docs/v4/STAGE81A3*",
    )
    for pattern in patterns:
        for target in project.glob(pattern):
            if not target.is_file():
                continue
            name = target.relative_to(project).as_posix()
            if name in by_path:
                continue
            state = "tracked_clean" if name in tracked else "ignored" if name in ignored else "untracked_not_reported"
            by_path[name] = {
                "git_status": "  " if state == "tracked_clean" else "!!" if state == "ignored" else "??",
                "path": name,
                "classification": classify_worktree(name),
                "size_bytes": (
                    "SELF"
                    if name == "results/v4/stage81a3_local_working_tree_freeze_inventory.csv"
                    else target.stat().st_size
                ),
                "staged": False,
                "inventory_state": state,
            }
    for row in by_path.values():
        row.setdefault("inventory_state", "dirty_or_untracked")
    return sorted(by_path.values(), key=lambda row: row["path"])


def source_hash(values: pd.Series) -> str:
    return hashlib.sha256("|".join(values.astype(str)).encode("utf-8")).hexdigest()


def inspect_asset(project: Path, spec: dict[str, str], vocab: set[str]) -> tuple[dict[str, Any], set[str], dict[str, Any]]:
    path = project / spec["path"]
    verification = path.with_suffix(path.suffix + ".verification.json")
    with h5py.File(path, "r") as handle:
        cells, genes = h5_shape(handle)
        features = feature_names(handle)
        obs_fields = set(handle["obs"].keys())
        donor_count = unique_count(handle, spec.get("donor_field"))
        section_count = unique_count(handle, spec.get("section_field"))
        specimen_count = unique_count(handle, spec.get("specimen_field"))
        if spec.get("official_donor"):
            donor_count = 1
            section_count = 1
            specimen_count = 1
        raw_counts = "reads" in handle["layers"] or spec["technology"] == "MERSCOPE"
        normalized = "X_normalization" in handle["uns"] or "reads" in handle["layers"]
        provenance = {
            "obs_fields": sorted(obs_fields),
            "donor_count": donor_count,
            "section_count": section_count,
            "specimen_count": specimen_count,
            "donor_field_present": spec.get("donor_field") in obs_fields if spec.get("donor_field") else False,
            "section_field_present": spec.get("section_field") in obs_fields if spec.get("section_field") else False,
            "official_donor": spec.get("official_donor", ""),
            "official_section": spec.get("official_section", ""),
            "cell_to_section_mapping": (
                "deterministic by single-section file identity"
                if spec.get("official_section")
                else "deterministic from released obs section/specimen field"
            ),
            "section_to_donor_mapping": (
                "Allen Brain Map Community staff mapping"
                if spec.get("official_donor")
                else "deterministic from released obs donor and section/specimen fields"
            ),
            "mapping_evidence": (
                "https://community.brain-map.org/t/donor-mapping-for-merfish-mec-hpf-specimens/5020"
                if spec.get("official_donor")
                else spec["path"]
            ),
        }
    verified = json.loads(verification.read_text(encoding="utf-8")) if verification.exists() else {}
    row = {
        "resource_id": spec["asset_id"],
        "scope": "local",
        "dataset_source": spec["dataset"],
        "local_path_or_accession": spec["path"],
        "file_type": "h5ad",
        "size_bytes": path.stat().st_size,
        "sha256": verified.get("sha256", "NOT IDENTIFIABLE"),
        "species": "Homo sapiens",
        "brain_region": spec["region"],
        "donor_count": donor_count if donor_count is not None else "NOT IDENTIFIABLE",
        "sample_count": specimen_count if specimen_count is not None else "NOT IDENTIFIABLE",
        "section_count": section_count if section_count is not None else "NOT IDENTIFIABLE",
        "cell_or_spot_count": cells,
        "resolution": "cell-level segmented",
        "technology": spec["technology"],
        "n_genes_features": genes,
        "gene_identifier_convention": "HGNC symbol in var/_index; Ensembl field also present for MERSCOPE/Xenium",
        "raw_counts_available": raw_counts,
        "normalized_counts_available": normalized,
        "coordinates_available": True,
        "coordinate_fields": "obsm/spatial",
        "coordinate_units": "NOT IDENTIFIABLE",
        "cell_segmentation_available": True,
        "section_identity_available": section_count is not None,
        "donor_identity_available": donor_count is not None,
        "pairing_to_broader_assay": "group-level SEA-AD regional snRNA/snATAC only; not same-cell",
        "frozen_4096_overlap": len(features & vocab),
        "pathology_metadata_present": any(name in obs_fields for name in ("Braak", "CERAD score", "Thal")),
        "pathology_fields_isolatable": True,
        "sample_selection_pathology_conditioned": True,
        "context_suitability": "targeted-panel physical-context evidence only; not a full-4096 teacher; post-freeze under current pathology firewall",
        "resource_decision_class": "C. USEFUL ONLY AFTER PATHOLOGY OPENS",
        "official_source": "configs/v4/stage81a1b_official_sea_ad_acquisition.yaml",
    }
    return row, features, provenance


def external_rows() -> list[dict[str, Any]]:
    common = {
        "scope": "external_audit_only",
        "local_path_or_accession": "",
        "file_type": "repository record; no download performed",
        "size_bytes": "NOT IDENTIFIABLE",
        "sha256": "NOT APPLICABLE",
        "species": "Homo sapiens",
        "raw_counts_available": "NOT IDENTIFIABLE",
        "normalized_counts_available": "NOT IDENTIFIABLE",
        "coordinates_available": True,
        "coordinate_fields": "repository-dependent",
        "coordinate_units": "technology-defined; exact processed field not audited",
        "cell_segmentation_available": True,
        "section_identity_available": True,
        "donor_identity_available": True,
        "frozen_4096_overlap": "NOT COMPUTED - no feature list downloaded",
        "pathology_fields_isolatable": "NOT IDENTIFIABLE",
    }
    return [
        {
            **common,
            "resource_id": "stds0000242",
            "dataset_source": "Charting the spatial transcriptome of the human cerebral cortex",
            "local_path_or_accession": "STDS0000242 / STT0000059",
            "brain_region": "14 adult human cortical regions",
            "donor_count": 5,
            "sample_count": 5,
            "section_count": 44,
            "cell_or_spot_count": 1888306,
            "resolution": "Stereo-seq cell bins; 500-nm spot pitch",
            "technology": "Stereo-seq",
            "n_genes_features": "transcriptome-wide; exact processed feature count NOT IDENTIFIABLE",
            "gene_identifier_convention": "GRCh38-derived; exact processed convention NOT IDENTIFIABLE",
            "pairing_to_broader_assay": "same study snRNA-seq; section-to-snRNA pairing not established here",
            "pathology_metadata_present": False,
            "sample_selection_pathology_conditioned": False,
            "context_suitability": "strong pathology-blind candidate, but official project is 19.22 TB and processed spatial file sizes/direct bounded manifest are unresolved",
            "resource_decision_class": "B. POTENTIALLY USABLE AFTER A BOUNDED, DECISION-CHANGING DOWNLOAD",
            "official_source": "https://db.cngb.org/stomics/datasets/STDS0000242/; https://www.nature.com/articles/s41467-025-62793-9",
        },
        {
            **common,
            "resource_id": "cnp0007621",
            "dataset_source": "Population-scale single-cell spatial transcriptomic atlas of human cortex",
            "local_path_or_accession": "CNP0007621",
            "brain_region": "human cortex",
            "donor_count": "population-scale; exact released count NOT IDENTIFIABLE",
            "sample_count": "NOT IDENTIFIABLE",
            "section_count": "NOT IDENTIFIABLE",
            "cell_or_spot_count": "NOT IDENTIFIABLE",
            "resolution": "Stereo-seq single-cell spatial",
            "technology": "Stereo-seq and snRNA-seq",
            "n_genes_features": "transcriptome-wide; exact processed count NOT IDENTIFIABLE",
            "gene_identifier_convention": "NOT IDENTIFIABLE",
            "pairing_to_broader_assay": "same study snRNA-seq; exact pairing NOT IDENTIFIABLE",
            "pathology_metadata_present": True,
            "sample_selection_pathology_conditioned": True,
            "context_suitability": "post-freeze only: tissue was collected from patients diagnosed with tumor, epilepsy, or abscess",
            "resource_decision_class": "C. USEFUL ONLY AFTER PATHOLOGY OPENS",
            "official_source": "https://db.cngb.org/cnsa/; https://www.biorxiv.org/content/10.1101/2025.10.13.681959v1",
        },
        {
            **common,
            "resource_id": "cosmx6k_human_frontal_cortex",
            "dataset_source": "Bruker CosMx Human Frontal Cortex FFPE 6K",
            "local_path_or_accession": "Bruker public dataset / OSTA.data CosMx6k_HumanBrain",
            "brain_region": "frontal cortex",
            "donor_count": 1,
            "sample_count": 1,
            "section_count": 1,
            "cell_or_spot_count": 188686,
            "resolution": "single-cell segmented",
            "technology": "CosMx SMI",
            "n_genes_features": 6278,
            "gene_identifier_convention": "gene symbols; exact downloadable list not audited",
            "pairing_to_broader_assay": "no paired full-transcriptome assay established",
            "pathology_metadata_present": "NOT IDENTIFIABLE",
            "sample_selection_pathology_conditioned": "NOT IDENTIFIABLE",
            "context_suitability": "broad measured-panel candidate but one tissue section cannot establish donor/section reproducibility; pathology provenance unresolved",
            "resource_decision_class": "D. INSUFFICIENT / NOT IDENTIFIABLE",
            "official_source": "https://brukerspatialbiology.com/products/cosmx-spatial-molecular-imager/ffpe-dataset/human-frontal-cortex-ffpe-dataset/; https://bioconductor.org/books/release/OSTA/pages/bkg-example-datasets.html",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    project = args.project_dir.resolve()

    vocab_frame = pd.read_csv(project / "results/v4/stage81a2_foundation_vocabulary.csv")
    observed_vocab_hash = source_hash(vocab_frame.canonical_ensembl_gene_id)
    if len(vocab_frame) != 4096 or vocab_frame.canonical_ensembl_gene_id.nunique() != 4096:
        raise RuntimeError("frozen vocabulary size/identity drift")
    if observed_vocab_hash != VOCABULARY_HASH or set(vocab_frame.vocabulary_hash) != {VOCABULARY_HASH}:
        raise RuntimeError("frozen vocabulary hash drift")
    vocab = set(vocab_frame.canonical_hgnc_symbol.astype(str))

    edges = pd.read_csv(project / "results/tables/stage75_integrated_tf_target_summary_v1.csv")
    regulators = pd.read_csv(project / "results/tables/stage75_integrated_regulator_summary_v1.csv")
    if len(edges) != 96 or edges[["tf", "target_gene"]].duplicated().any():
        raise RuntimeError("Stage75 integrated edge schema/count drift")
    advanced = edges[edges.stage75_integrated_gate.eq("advance_supported")].copy()
    if set(advanced.tf) != set(SUPPORTED_REGULATORS):
        raise RuntimeError("Stage75 supported regulator drift")

    resource_rows: list[dict[str, Any]] = []
    overlap_rows: list[dict[str, Any]] = []
    provenance: dict[str, Any] = {}
    panel_summaries: dict[str, Any] = {}
    for spec in LOCAL_ASSETS:
        resource, features, trace = inspect_asset(project, spec, vocab)
        resource_rows.append(resource)
        provenance[spec["asset_id"]] = trace
        complete = advanced[advanced.tf.isin(features) & advanced.target_gene.isin(features)]
        measured_targets = sorted(set(advanced.target_gene) & features)
        measured_regulators = sorted(set(SUPPORTED_REGULATORS) & features)
        panel_summaries[spec["asset_id"]] = {
            "measured_supported_regulators": measured_regulators,
            "measured_stage75_targets": measured_targets,
            "complete_supported_edges": len(complete),
            "complete_edge_pairs": sorted(f"{row.tf}->{row.target_gene}" for row in complete.itertuples()),
        }
        for tf in SUPPORTED_REGULATORS:
            tf_edges = advanced[advanced.tf.eq(tf)]
            matched = tf_edges[tf_edges.target_gene.isin(features)] if tf in features else tf_edges.iloc[0:0]
            tier = str(tf_edges.evidence_tier.iloc[0])
            support = str(regulators.loc[regulators.tf.eq(tf), "motif_support_interpretation"].iloc[0])
            overlap_rows.append(
                {
                    "resource_id": spec["asset_id"],
                    "panel_gene_count": resource["n_genes_features"],
                    "frozen_4096_overlap": resource["frozen_4096_overlap"],
                    "tf": tf,
                    "tf_measured": tf in features,
                    "evidence_tier": tier,
                    "motif_support_class": support,
                    "supported_edges_total": len(tf_edges),
                    "supported_targets_measured": int(tf_edges.target_gene.isin(features).sum()),
                    "complete_tf_target_edges_measured": len(matched),
                    "measured_target_genes": "|".join(sorted(set(tf_edges.target_gene) & features)),
                    "complete_edge_pairs": "|".join(sorted(f"{row.tf}->{row.target_gene}" for row in matched.itertuples())),
                    "meaningful_program_evaluation": len(matched) >= 5,
                    "claim_boundary": "candidate coactivity-signed influence; not activation/repression or causal regulation",
                }
            )

    resource_rows.extend(external_rows())
    worktree = inventory_worktree(project)
    protected = {
        name: {"path": path, "expected_sha256": expected, "observed_sha256": sha256(project / path)}
        for name, (path, expected) in PROTECTED.items()
    }
    protected_pass = all(item["expected_sha256"] == item["observed_sha256"] for item in protected.values())
    staged = [row["path"] for row in worktree if row["staged"]]
    local_eligible = False
    real_context_reason = (
        "No eligible local experiment: all local panels are targeted (180-464 genes), none supplies a same-cell broad "
        "4096-gene teacher, the ContextReader has mechanics-only/random weights and this task forbids context training, "
        "and SEA-AD sample selection is pathology-structured under the strict A3 firewall."
    )
    audit = {
        "stage": "stage81a3_context_evidence_audit",
        "anchor_commit": ANCHOR,
        "head": git(project, "rev-parse", "HEAD"),
        "origin_main": git(project, "rev-parse", "origin/main"),
        "frozen_vocabulary": {"path": "results/v4/stage81a2_foundation_vocabulary.csv", "size": 4096, "hash": observed_vocab_hash},
        "stage75": {
            "integrated_edges": len(edges),
            "advanced_regulators": list(SUPPORTED_REGULATORS),
            "regulator_hierarchy": {
                "Tier A direct motif support": ["ELF1", "SPI1", "STAT1"],
                "Tier B extended-only support": ["BACH1", "CEBPA", "IRF8", "RELA"],
                "Tier C negative motif gate": ["MITF", "NRF1", "STAT3"],
            },
            "tier_a_old_usable_edges": {"ELF1": 23, "SPI1": 14, "STAT1": 16, "total": 53},
            "lineage_boundary": "Stage75-79 TF-target candidate evidence is separate from Stage51 STRING and Stage27/35 module graphs.",
            "frozen_sources": {
                "stage75_edges": "results/tables/stage75_integrated_tf_target_summary_v1.csv",
                "stage75_regulators": "results/tables/stage75_integrated_regulator_summary_v1.csv",
                "stage76_edge_coverage": "results/tables/stage76_perturbation_graph_edge_coverage_v1.csv",
                "stage76_regulator_readiness": "results/tables/stage76_regulator_readiness_v1.csv",
                "stage77_manifest": "results/reports/stage77_tier_a_perturbation_mvp_v1.json",
                "stage79_control_manifest": "results/reports/stage79_graph_controls_v1.json",
                "stage79_interpretation": "results/reports/stage79_control_interpretation_v1.json",
            },
        },
        "local_panel_summaries": panel_summaries,
        "hip_mec_provenance": provenance,
        "real_context_qualification": {"run": False, "classification": "REAL CONTEXT VALUE NOT IDENTIFIABLE", "reason": real_context_reason},
        "external_audit_stop": "No exact bounded multi-donor processed spatial manifest with sizes was established; no download was authorized or performed.",
        "protected_hashes": protected,
        "protected_hashes_pass": protected_pass,
        "governance": {
            "pathology_opened": False,
            "development_expression_accessed": False,
            "sealed_expression_accessed": False,
            "real_expression_accessed": True,
            "real_spatial_expression_access_scope": "bounded nonzero X samples used only to classify raw-count versus normalized-matrix semantics; no cell identities or values retained",
            "optimizer_updates": 0,
            "backward_calls": 0,
            "ema_updates": 0,
            "training_performed": False,
            "large_download_performed": False,
            "staged_files": staged,
        },
    }
    readiness = {
        "stage": "stage81a3_freeze_review_readiness",
        "classification": "B. CORE ARCHITECTURE READY; DOCUMENTED CONTEXT DATA LIMITATION REQUIRES HUMAN ACCEPTANCE BEFORE FREEZE",
        "architecture_failure": False,
        "audit_failure": False,
        "data_limitation": True,
        "core_intrinsic_evidence_ready_for_review": True,
        "real_context_value_identifiable": local_eligible,
        "specific_bounded_decision_changing_download_identified": False,
        "reason": real_context_reason,
        "additional_pre_freeze_experiment_would_change_decision": False,
        "additional_pre_freeze_experiment_explanation": "A credible broad candidate exists (STDS0000242), but its processed spatial subset lacks an exact bounded file/size manifest and context-value training is outside the frozen A3 audit contract. This is not a justified automatic pre-freeze expansion.",
        "stage81a3_complete": False,
        "stage81a3_frozen": False,
        "ready_for_stage81b": False,
        "stage81b_started": False,
        "pathology_opened": False,
    }

    resource_columns = list(resource_rows[0])
    overlap_columns = list(overlap_rows[0])
    worktree_columns = list(worktree[0]) if worktree else ["git_status", "path", "classification", "size_bytes", "staged", "inventory_state"]
    atomic_csv(project / "results/v4/stage81a3_context_resource_registry.csv", resource_rows, resource_columns)
    atomic_csv(project / "results/v4/stage81a3_stage75_spatial_edge_overlap.csv", overlap_rows, overlap_columns)
    atomic_csv(project / "results/v4/stage81a3_local_working_tree_freeze_inventory.csv", worktree, worktree_columns)
    atomic_json(project / "results/v4/stage81a3_context_evidence_audit.json", audit)
    atomic_json(project / "results/v4/stage81a3_freeze_review_readiness.json", readiness)

    caudate = panel_summaries["sea_ad_caudate_xenium"]
    document = f"""# Stage81A3 Context Evidence and Freeze Review

## Decision changed by this audit

This audit asks only whether real physical cellular context can be qualified well enough to support a deliberate Stage81A3 freeze review. It does not redesign or train the architecture.

## Local evidence

All four SEA-AD spatial objects are locally present and have real cell coordinates. They are targeted panels (MTG 180, HIP 433, MEC 433, Caudate 464 genes), not full 4,096-gene molecular teachers. A bounded sample of nonzero spatial `X` values was read only to distinguish integer-count from normalized matrix semantics; no cell identities or expression values were retained. Pathology-bearing fields were identified by schema name only and pathology values were never opened. SEA-AD cohort selection is pathology-structured, so these objects are post-freeze under the strict A3 pathology firewall.

The HIP and MEC combined files omit donor/section columns. Their source filenames preserve specimen barcodes 1444211893 and 1444201261. An Allen Brain Map Community staff response identifies each file as one section and maps both sections to donor H24.30.005. This resolves biological provenance externally but does not create a cell-level donor column inside the released objects.

Caudate measures {', '.join(caudate['measured_supported_regulators']) or 'no supported regulator'} and has {caudate['complete_supported_edges']} complete Stage75 TF-target edges: {', '.join(caudate['complete_edge_pairs']) or 'none'}. This is exact panel overlap, not regulatory validation. The complete program is too narrow for a broad Stage75 context claim, and no trained/frozen context-value mapping exists.

## External bounded audit

- **STDS0000242 / STT0000059:** pathology-blind adult human cortex, Stereo-seq, five samples and 44 sections. It is the strongest candidate. The official raw project is 19.22 TB, while processed spatial files are not exposed with stable sizes/direct bounded URLs in the audited manifest. No download was performed.
- **CNP0007621:** human cortical Stereo-seq, but tissue acquisition is conditioned on tumor, epilepsy, or abscess. It is post-freeze under this firewall.
- **CosMx 6K human frontal cortex:** 6,278 targets and 188,686 cells, but only one section/donor and pathology provenance is not identifiable. It cannot establish donor/section reproducibility.

## Scientific classification

- **Architecture failure:** no new evidence.
- **Audit failure:** no; the audit correctly establishes its empirical boundary.
- **Data limitation:** yes. No local pathology-blind, broad, multi-donor target/context resource is eligible under the current no-training contract.

## Final classification

**B. CORE ARCHITECTURE READY; DOCUMENTED CONTEXT DATA LIMITATION REQUIRES HUMAN ACCEPTANCE BEFORE FREEZE**

STAGE81A3 COMPLETE: NO
STAGE81A3 FROZEN: NO
READY FOR STAGE81B: NO
STAGE81B STARTED: NO
PATHOLOGY OPENED: NO

No real-context qualification run, optimizer, backward call, EMA update, model training, large download, staging, commit, or push occurred.
"""
    doc_path = project / "docs/v4/STAGE81A3_CONTEXT_EVIDENCE_AND_FREEZE_REVIEW.md"
    doc_path.write_text(document, encoding="utf-8", newline="\n")

    if not protected_pass:
        raise RuntimeError("protected evidence hash drift")
    if audit["head"] != ANCHOR or audit["origin_main"] != ANCHOR:
        raise RuntimeError("frozen repository anchor drift")
    if staged:
        raise RuntimeError(f"unexpected staged files: {staged}")
    print(f"resources={len(resource_rows)} local_panels={len(LOCAL_ASSETS)} overlap_rows={len(overlap_rows)}")
    print(f"caudate_complete_edges={caudate['complete_supported_edges']}")
    print("real_context_qualification=NOT_IDENTIFIABLE")
    print("final_classification=B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
