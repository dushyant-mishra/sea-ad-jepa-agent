#!/usr/bin/env python3
"""Build a virtual, non-destructive harmonization layer for Stage81A2 review."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import h5py
import yaml


OUTPUTS = {
    "datasets": "pre_stage81a2_dataset_manifest.csv",
    "semantics": "pre_stage81a2_matrix_semantics_registry.csv",
    "features": "pre_stage81a2_feature_identifier_registry.csv",
    "mappings": "pre_stage81a2_gene_mapping_registry.csv",
    "identity": "pre_stage81a2_donor_study_specimen_registry.csv",
    "duplicates": "pre_stage81a2_duplicate_overlap_registry.csv",
    "roles": "pre_stage81a2_dataset_role_candidates.csv",
    "modalities": "pre_stage81a2_modality_integration_registry.csv",
    "perturbation": "pre_stage81a2_perturbation_readiness_registry.csv",
    "virtual": "pre_stage81a2_virtual_concat_manifest.json",
    "report": "pre_stage81a2_harmonization_report.json",
}
GENE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
ENSEMBL_RE = re.compile(r"^ENSG\d+(?:\.\d+)?$")
RAW_EXTENSIONS = (".fastq", ".fastq.gz", ".fq", ".fq.gz", ".bam", ".cram", ".sra")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/v4/pre_stage81a2_harmonization_contract.yaml")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output-dir", default="results/v4")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(rows[0]) if rows else []
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def sha256(path: Path, chunk: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while value := handle.read(chunk):
            digest.update(value)
    return digest.hexdigest()


def verify_governance(project: Path, config: dict[str, Any]) -> None:
    for commit in config["required_ancestor_commits"]:
        if subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=project).returncode:
            raise RuntimeError(f"Missing governing ancestor: {commit}")
    for name, expected in config["protected_worktree_signatures"].items():
        if sha256(project / name) != expected:
            raise RuntimeError(f"Protected worktree file changed: {name}")
    policy = config["policy"]
    required_false = (
        "physical_full_matrix_merge_performed", "final_vocabulary_frozen",
        "donor_split_frozen", "pathology_values_used", "model_trained",
        "fuzzy_gene_aliasing_allowed",
    )
    if any(policy[name] is not False for name in required_false):
        raise RuntimeError("Harmonization safety contract is not active")
    required_false = (
        "spatial_zero_fill_into_rna_vocabulary_allowed",
        "atac_features_allowed_in_rna_vocabulary",
        "holdout_may_influence_model_design",
        "pathology_context_allowed_in_foundation_supervision",
    )
    if any(policy[name] is not False for name in required_false):
        raise RuntimeError("Modality or leakage guardrail is not active")
    if policy["perturbation_training_requires_complete_asset_audit"] is not True:
        raise RuntimeError("Perturbation readiness gate is not active")


def integration_contract(asset: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    dataset_id = asset["dataset_id"]
    modality = asset["modality"].lower()
    path = config.get("dataset_contracts", {}).get(dataset_id, {}).get("integration_path", "")
    feature_space = "rna_expression_candidate"
    vocabulary = "pending_exact_gene_identity_and_stage81a2"
    missing = "not_applicable"
    leakage = "none_beyond_registered_role"
    mask_required = False
    equivalent_to_full_rna = True
    if any(token in modality for token in ("merfish", "merscope", "xenium")):
        feature_space = "targeted_spatial_panel"
        vocabulary = "excluded_from_direct_full_rna_vocabulary"
        missing = "shared_feature_projection_or_explicit_missing_modality_mask_required"
        equivalent_to_full_rna = False
    elif "atac" in modality:
        feature_space = "regulatory_peak_namespace"
        vocabulary = "excluded_from_rna_vocabulary"
        missing = "regulatory_prior_or_adapter_only"
        equivalent_to_full_rna = False
    elif dataset_id == "siletti_hbca_all_non_neuronal":
        vocabulary = "holdout_excluded_from_vocabulary_selection"
        leakage = "exclude_from_training_vocabulary_architecture_threshold_checkpoint_and_hyperparameter_decisions"
    elif dataset_id == "gse243292_full_dlpfc_h5ad":
        vocabulary = "validation_only_not_foundation_vocabulary_selection"
        leakage = "pathology_fields_prohibited_from_pathology_blind_foundation_supervision"
    elif asset["study_id"] == "GSE301119":
        feature_space = "perturbation_expression_unequal_feature_universe"
        vocabulary = "exact_stable_feature_intersection_or_projection_pending"
        missing = "explicit_measurement_mask_required"
        mask_required = True
        equivalent_to_full_rna = False
    return {
        "integration_path": path or "role_pending_stage81a2",
        "feature_space_class": feature_space,
        "rna_vocabulary_eligibility": vocabulary,
        "missing_modality_policy": missing,
        "measurement_mask_required": mask_required,
        "equivalent_to_full_rna_matrix": equivalent_to_full_rna,
        "leakage_guardrail": leakage,
    }


def decode(values: Iterable[Any]) -> list[str]:
    return [value.decode("utf-8") if isinstance(value, bytes) else str(value) for value in values]


def h5_column(group: h5py.Group, key: str) -> list[str]:
    if key not in group:
        return []
    value = group[key]
    if isinstance(value, h5py.Group) and {"categories", "codes"}.issubset(value):
        categories = decode(value["categories"][:])
        return [categories[int(code)] if int(code) >= 0 else "" for code in value["codes"][:]]
    return decode(value[:])


def h5_index(group: h5py.Group) -> list[str]:
    key = group.attrs.get("_index", "_index")
    if isinstance(key, bytes):
        key = key.decode("utf-8")
    return h5_column(group, str(key))


def inspect_h5_features(path: Path) -> tuple[list[tuple[str, str, str]], dict[str, Any]]:
    with h5py.File(path, "r") as handle:
        var = handle["var"]
        identifiers = h5_index(var)
        stable = h5_column(var, "gene_ids") or h5_column(var, "Gene")
        symbols = h5_column(var, "feature_name")
        if not symbols:
            symbols = ["" if ENSEMBL_RE.match(value) else value for value in identifiers]
        if not stable:
            stable = [value if ENSEMBL_RE.match(value) else "" for value in identifiers]
        records = [
            (identifiers[i], symbols[i] if i < len(symbols) else "", stable[i] if i < len(stable) else "")
            for i in range(len(identifiers))
        ]
        obs = handle["obs"]
        obs_columns = set(obs.keys())
        donor_field = next((name for name in ("Donor ID", "donor_id", "donor") if name in obs_columns), "")
        donor_values = sorted(set(h5_column(obs, donor_field))) if donor_field else []
        specimen_field = next((name for name in ("Specimen_ID", "Specimen Barcode", "sample_id") if name in obs_columns), "")
        section_field = next((name for name in ("Section", "section_id", "section") if name in obs_columns), "")
        region_field = next((name for name in ("Brain Region", "tissue", "Region", "region") if name in obs_columns), "")
        assay_field = next((name for name in ("method", "assay") if name in obs_columns), "")
        cell_field = handle["obs"].attrs.get("_index", "_index")
        if isinstance(cell_field, bytes):
            cell_field = cell_field.decode("utf-8")
        identity = {
            "donor_field": donor_field, "donor_count": len(donor_values),
            "specimen_field": specimen_field, "section_field": section_field,
            "region_field": region_field, "assay_field": assay_field,
            "cell_identifier_field": str(cell_field),
        }
    return records, identity


def inspect_compressed_h5(path: Path, temporary_root: Path) -> tuple[list[tuple[str, str, str]], dict[str, Any]]:
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".h5ad", dir=temporary_root, delete=False) as target:
        temporary = Path(target.name)
        with gzip.open(path, "rb") as source:
            shutil.copyfileobj(source, target, length=16 * 1024 * 1024)
    try:
        return inspect_h5_features(temporary)
    finally:
        temporary.unlink(missing_ok=True)


def text_features(path: Path) -> list[tuple[str, str, str]]:
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    records = []
    with opener(path, "rt", encoding="utf-8", errors="strict", newline="") as handle:
        for index, line in enumerate(handle):
            if not line.strip():
                continue
            first = re.split(r"[\t,]", line.rstrip("\r\n"), maxsplit=1)[0].strip().strip('"')
            if index == 0 and first.lower() in {"gene", "genes", "gene_id", "geneid", "ensembl_gene_id", ""}:
                continue
            if first.startswith("N_"):
                continue
            stable = first if ENSEMBL_RE.match(first) else ""
            symbol = "" if stable else first
            records.append((first, symbol, stable))
    return records


def tar_features(path: Path, temporary_root: Path) -> list[tuple[str, str, str]]:
    candidates: list[list[tuple[str, str, str]]] = []
    with tarfile.open(path, "r:*") as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        if any(member.name.lower().endswith(RAW_EXTENSIONS) for member in members):
            raise RuntimeError(f"Raw sequencing member in harmonization source: {path.name}")
        feature_members = [member for member in members if member.name.lower().endswith(("features.tsv.gz", "genes.tsv.gz"))]
        for member in feature_members:
            source = archive.extractfile(member)
            if source is None:
                continue
            records = []
            with gzip.GzipFile(fileobj=source) as compressed:
                for raw in compressed:
                    fields = raw.decode("utf-8").rstrip("\r\n").split("\t")
                    stable = fields[0] if fields and ENSEMBL_RE.match(fields[0]) else ""
                    symbol = fields[1] if len(fields) > 1 else ("" if stable else fields[0])
                    records.append((fields[0], symbol, stable))
            candidates.append(records)
        if not candidates:
            count_members = [member for member in members if "readspergene" in member.name.lower() or "gene_counts" in member.name.lower()]
            for member in count_members[:1]:
                source = archive.extractfile(member)
                if source is None:
                    continue
                if member.name.lower().endswith(".gz"):
                    source = gzip.GzipFile(fileobj=source)
                records = []
                for raw in source:
                    fields = raw.decode("utf-8").rstrip("\r\n").split("\t")
                    identifier = fields[0].strip('"')
                    if not identifier or identifier.startswith("N_"):
                        continue
                    stable = identifier if ENSEMBL_RE.match(identifier) else ""
                    records.append((identifier, "" if stable else identifier, stable))
                candidates.append(records)
        if not candidates:
            h5_members = [
                member for member in members
                if member.name.endswith("filtered_feature_bc_matrix.h5")
                and "sgrna" not in member.name.lower()
            ]
            if h5_members:
                temporary_root.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(h5_members[0])
                if source is not None:
                    with tempfile.NamedTemporaryFile(suffix=".h5", dir=temporary_root, delete=False) as target:
                        temporary = Path(target.name)
                        shutil.copyfileobj(source, target, length=16 * 1024 * 1024)
                    try:
                        with h5py.File(temporary, "r") as handle:
                            features = handle["matrix/features"]
                            ids = decode(features["id"][:])
                            names = decode(features["name"][:])
                            candidates.append([(ids[i], names[i], ids[i] if ENSEMBL_RE.match(ids[i]) else "") for i in range(len(ids))])
                    finally:
                        temporary.unlink(missing_ok=True)
    if not candidates:
        return []
    first_signature = hashlib.sha256("\n".join(row[0] for row in candidates[0]).encode()).hexdigest()
    matching = [candidate for candidate in candidates if hashlib.sha256("\n".join(row[0] for row in candidate).encode()).hexdigest() == first_signature]
    return candidates[0] if len(matching) == len(candidates) else []


def mapping_rows(records: list[tuple[str, str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    symbols = [symbol for _, symbol, _ in records if symbol]
    duplicates = {name for name, count in Counter(symbols).items() if count > 1}
    rows = []
    for index, (identifier, symbol, stable) in enumerate(records):
        valid_symbol = bool(symbol and GENE_RE.match(symbol) and symbol not in duplicates)
        valid_stable = bool(stable and ENSEMBL_RE.match(stable))
        status = "exact_symbol_and_stable_id" if valid_symbol and valid_stable else "exact_symbol_only" if valid_symbol else "exact_stable_id_only" if valid_stable else "unresolved"
        rows.append({
            "source_feature_index": index,
            "source_feature_id": identifier,
            "source_symbol": symbol,
            "source_stable_id": stable,
            "canonical_symbol": symbol if valid_symbol else "",
            "canonical_stable_id": stable if valid_stable else "",
            "mapping_method": "exact_source_identifier_no_alias_inference",
            "mapping_status": status,
        })
    summary = {
        "feature_count": len(records), "exact_symbol_count": sum(bool(row["canonical_symbol"]) for row in rows),
        "exact_stable_id_count": sum(bool(row["canonical_stable_id"]) for row in rows),
        "unresolved_count": sum(row["mapping_status"] == "unresolved" for row in rows),
        "duplicate_symbol_count": len(duplicates),
    }
    return rows, summary


def write_mapping(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as text:
                writer = csv.DictWriter(text, fieldnames=list(rows[0]), lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
    os.replace(temporary, path)


def build_assets(project: Path, config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    inputs = {name: project / value for name, value in config["inputs"].items()}
    assets = []
    semantics: dict[str, dict[str, str]] = {}
    identity: dict[str, dict[str, str]] = {}

    sea_semantics = {row["asset_id"]: row for row in read_csv(inputs["sea_ad_semantics"])}
    sea_identity = {row["dataset"]: row for row in read_csv(inputs["sea_ad_identity"])}
    for source in read_csv(inputs["sea_ad_assets"]):
        asset_id = source["asset_id"]
        assets.append({
            "dataset_id": asset_id, "cohort": "sea_ad", "study_id": "SEA_AD",
            "modality": source["modality"], "source_path": source["path"],
            "source_hash": source["sha256"], "size_bytes": source["size_bytes"],
            "shape": f"{source['n_obs']}x{source['n_vars']}", "file_type": "h5ad",
            "registered_role": source["intended_role"], "documentation_only": False,
        })
        semantics[asset_id] = sea_semantics[asset_id]
        identity[asset_id] = sea_identity[asset_id]

    normal_hashes = {row["asset_id"]: row for row in read_csv(inputs["normal_hashes"])}
    normal_semantics = {row["asset_id"]: row for row in read_csv(inputs["normal_semantics"])}
    normal_roles = {row["source_path"]: row for row in read_csv(inputs["normal_roles"]) if row["accepted"].lower() == "true"}
    for source in read_csv(inputs["normal_catalog"]):
        asset_id = source["asset_id"]
        record = normal_hashes[asset_id]
        role = normal_roles.get(record["path"], {})
        assets.append({
            "dataset_id": asset_id, "cohort": "normal_reference", "study_id": source["study_id"],
            "modality": "documentation" if source["file_type"] == "text" else "expression",
            "source_path": record["path"], "source_hash": record["sha256"],
            "size_bytes": record["size_bytes"],
            "shape": normal_semantics[asset_id]["shape_or_rows_columns"], "file_type": source["file_type"],
            "registered_role": role.get("primary_role", source["primary_role"]),
            "documentation_only": source["file_type"] == "text",
        })
        semantics[asset_id] = normal_semantics[asset_id]

    perturb_hashes = {row["asset_id"]: row for row in read_csv(inputs["perturbation_hashes"])}
    perturb_roles = {row["accession"]: row for row in read_csv(inputs["perturbation_identity"])}
    rds = {row["source_path"]: row for row in read_csv(inputs["perturbation_seurat"])}
    for source in read_csv(inputs["perturbation_catalog"]):
        asset_id = source["asset_id"]
        record = perturb_hashes[asset_id]
        role = perturb_roles[source["accession"]]
        lower = source["filename"].lower()
        documentation = lower.endswith((".fa.gz", "feature_reference.csv.gz"))
        shape = "unresolved_source_archive_or_table"
        if record["path"] in rds:
            shape = f"{rds[record['path']]['n_cells']}x{rds[record['path']]['n_features']}"
        assets.append({
            "dataset_id": asset_id, "cohort": "perturbation", "study_id": source["accession"],
            "modality": "documentation" if documentation else "perturbation_expression_or_assignment",
            "source_path": record["path"], "source_hash": record["sha256"],
            "size_bytes": record["size_bytes"], "shape": shape,
            "file_type": Path(source["filename"]).suffix.lower().lstrip("."),
            "registered_role": role["primary_role"], "documentation_only": documentation,
        })
    return sorted(assets, key=lambda row: row["dataset_id"]), semantics, identity


def main() -> int:
    args = parse_args()
    project = Path(args.project_dir).resolve()
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8"))
    output = (project / args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    verify_governance(project, config)
    assets, source_semantics, source_identity = build_assets(project, config)
    mapping_root = project / config["policy"]["mapping_root"]
    temporary_root = project / "outputs/v4/pre_stage81a2_temporary"

    dataset_rows = []
    semantics_rows = []
    feature_rows = []
    mapping_registry = []
    identity_rows = []
    role_rows = []
    modality_rows = []
    perturbation_rows = []
    mapping_cache: dict[str, str] = {}
    bounded_samples = []
    perturbation_identity = {
        row["accession"]: row
        for row in read_csv(project / config["inputs"]["perturbation_identity"])
    }

    for asset in assets:
        path = project / asset["source_path"]
        if not path.exists() or path.stat().st_size != int(asset["size_bytes"]):
            raise RuntimeError(f"Missing or size-drifted source: {asset['dataset_id']}")
        contract = config["role_contracts"][asset["cohort"]]
        integration = integration_contract(asset, config)
        semantics = source_semantics.get(asset["dataset_id"], {})
        identity = source_identity.get(asset["dataset_id"], {})
        records: list[tuple[str, str, str]] = []
        h5_identity: dict[str, Any] = {}
        mapping_status = "documentation_not_in_virtual_matrix" if asset["documentation_only"] else "unresolved_exact_feature_mapping_required"
        lower = path.name.lower()
        modality = asset["modality"].lower()
        if not asset["documentation_only"] and "atac" not in modality:
            try:
                if asset["file_type"] == "h5ad" or lower.endswith(".h5ad"):
                    records, h5_identity = inspect_h5_features(path)
                elif lower.endswith(".h5ad.gz"):
                    records, h5_identity = inspect_compressed_h5(path, temporary_root)
                elif lower.endswith((".txt.gz", ".csv.gz")):
                    records = text_features(path)
                elif lower.endswith((".tar", ".tar.gz", ".tgz")):
                    records = tar_features(path, temporary_root)
            except (OSError, KeyError, UnicodeError, tarfile.TarError) as exc:
                mapping_status = f"unresolved_exact_reader_error:{type(exc).__name__}"
        feature_hash = ""
        mapping_path = ""
        summary = {"feature_count": 0, "exact_symbol_count": 0, "exact_stable_id_count": 0, "unresolved_count": 0, "duplicate_symbol_count": 0}
        if records:
            feature_hash = hashlib.sha256("\n".join(row[0] for row in records).encode("utf-8")).hexdigest()
            mapped, summary = mapping_rows(records)
            if feature_hash in mapping_cache:
                mapping_path = mapping_cache[feature_hash]
            else:
                target = mapping_root / f"feature_universe_{feature_hash[:16]}.csv.gz"
                write_mapping(target, mapped)
                mapping_path = target.resolve().relative_to(project).as_posix()
                mapping_cache[feature_hash] = mapping_path
            mapping_status = "exact_sidecar_ready_with_unresolved_identifiers_recorded"
            bounded_samples.append({
                "dataset_id": asset["dataset_id"], "feature_order_sha256": feature_hash,
                "first_features": [row[0] for row in records[:3]],
                "last_features": [row[0] for row in records[-3:]],
            })
        elif not asset["documentation_only"] and "atac" in modality:
            mapping_status = "non_gene_peak_namespace_not_expression_vocabulary"

        donor_field = identity.get("donor_field", h5_identity.get("donor_field", ""))
        donor_count = identity.get("donor_count", h5_identity.get("donor_count", 0))
        specimen_field = identity.get("specimen_field", h5_identity.get("specimen_field", ""))
        section_field = identity.get("section_field", h5_identity.get("section_field", ""))
        region_field = identity.get("region_field", h5_identity.get("region_field", ""))
        assay_field = identity.get("method_field", h5_identity.get("assay_field", ""))
        cell_field = identity.get("cell_or_nucleus_id_field", h5_identity.get("cell_identifier_field", ""))
        audit: dict[str, str] = {}
        if asset["study_id"] == "GSE301119":
            audit = next((row for row in read_csv(project / config["inputs"]["perturbation_seurat"]) if row["source_path"] == asset["source_path"]), {})
            donor_field, donor_count = "donor", audit.get("donor_count", 0)
        unresolved_identity = [name for name, value in (("donor", donor_field), ("specimen", specimen_field), ("section", section_field)) if not value]
        split_keys = ";".join(value for value in ("study_id", donor_field, specimen_field, section_field) if value)

        dataset_rows.append({
            "dataset_id": asset["dataset_id"], "cohort": asset["cohort"], "study_id": asset["study_id"],
            "modality": asset["modality"], "source_path": asset["source_path"], "source_hash": asset["source_hash"],
            "size_bytes": asset["size_bytes"], "shape": asset["shape"], "registered_role": asset["registered_role"],
            "documentation_only": asset["documentation_only"], "source_exists": True,
        })
        semantics_rows.append({
            "dataset_id": asset["dataset_id"], "shape": asset["shape"],
            "matrix_semantics": semantics.get("x_encoding", semantics.get("file_type", "source_format_requires_harmonization")),
            "x_dtype": semantics.get("x_dtype", "source_defined"), "raw_present": semantics.get("raw_present", "unknown"),
            "layers": semantics.get("layer_names", semantics.get("layers", "")),
            "integer_count_layer_available": semantics.get("integer_count_layer_available", "unknown"),
            "normalization_evidence": semantics.get("log_transform_evidence", "not_resolved_from_compact_source"),
            "expression_matrix_loaded": False,
            "feature_space_class": integration["feature_space_class"],
            "equivalent_to_full_rna_matrix": integration["equivalent_to_full_rna_matrix"],
        })
        feature_rows.append({
            "dataset_id": asset["dataset_id"], "gene_namespace": "exact_source_feature_identifiers" if records else "unresolved_or_non_gene",
            "feature_count": summary["feature_count"], "feature_order_sha256": feature_hash or "unresolved",
            "exact_symbol_count": summary["exact_symbol_count"], "exact_stable_id_count": summary["exact_stable_id_count"],
            "duplicate_symbol_count": summary["duplicate_symbol_count"], "unresolved_identifier_count": summary["unresolved_count"],
            "source_values_preserved": True, "fuzzy_aliasing_used": False,
        })
        mapping_registry.append({
            "dataset_id": asset["dataset_id"], "canonical_mapping_file": mapping_path or "not_available",
            "mapping_status": mapping_status, "feature_order_sha256": feature_hash or "unresolved",
            "mapping_policy": config["policy"]["gene_mapping_policy"],
            "future_vocabulary_projection_status": "candidate_not_frozen" if mapping_path else "blocked_or_not_applicable",
        })
        identity_rows.append({
            "dataset_id": asset["dataset_id"], "study_id": asset["study_id"], "donor_field": donor_field or "unresolved",
            "donor_count": donor_count or 0, "specimen_field": specimen_field or "unresolved",
            "section_field": section_field or "unresolved", "region_field": region_field or "unresolved",
            "assay_field": assay_field or "unresolved", "cell_identifier_field": cell_field or "unresolved",
            "future_split_grouping_keys": split_keys, "unresolved_identity_fields": ";".join(unresolved_identity),
            "fuzzy_identity_inference_used": False, "split_frozen": False,
        })
        role_rows.append({
            "dataset_id": asset["dataset_id"], "registered_role": asset["registered_role"],
            "allowed_role": contract["allowed_role"], "forbidden_role": contract["forbidden_role"],
            "role_status": "candidate_not_frozen", "pathology_supervision_allowed": False,
            "integration_path": integration["integration_path"],
            "rna_vocabulary_eligibility": integration["rna_vocabulary_eligibility"],
            "leakage_guardrail": integration["leakage_guardrail"],
        })
        modality_rows.append({
            "dataset_id": asset["dataset_id"], "modality": asset["modality"],
            "shape": asset["shape"], "feature_space_class": integration["feature_space_class"],
            "integration_path": integration["integration_path"],
            "rna_vocabulary_eligibility": integration["rna_vocabulary_eligibility"],
            "missing_modality_policy": integration["missing_modality_policy"],
            "measurement_mask_required": integration["measurement_mask_required"],
            "equivalent_to_full_rna_matrix": integration["equivalent_to_full_rna_matrix"],
            "leakage_guardrail": integration["leakage_guardrail"],
        })
        if asset["cohort"] == "perturbation":
            is_rds = lower.endswith(".rds")
            is_documentation = asset["documentation_only"]
            shape_resolved = asset["shape"] != "unresolved_source_archive_or_table"
            study_identity = perturbation_identity[asset["study_id"]]
            rds_identity_verified = is_rds and audit.get("full_object_audit_pass", "").lower() == "true"
            blockers = []
            gates = {
                "archive_members_resolved": is_rds,
                "matrix_orientation_resolved": is_rds,
                "exact_feature_identifiers_resolved": bool(mapping_path),
                "guide_to_cell_assignments_resolved": rds_identity_verified and int(audit.get("n_guide_identities", 0)) > 0,
                "controls_resolved": rds_identity_verified and int(audit.get("n_non_targeting_control_cells", 0)) > 0,
                "samples_resolved": rds_identity_verified and int(audit.get("donor_count", 0)) > 0,
                "replicates_resolved": rds_identity_verified and "replicate" in study_identity["replicate_structure"].lower(),
                "perturbation_identities_resolved": rds_identity_verified and int(audit.get("n_target_genes", 0)) > 0,
            }
            if is_documentation:
                blockers.append("documentation_asset_not_training_matrix")
            if not shape_resolved:
                blockers.append("source_archive_or_table_shape_unresolved")
            blockers.extend(name for name, passed in gates.items() if not passed)
            if asset["study_id"] == "GSE301119":
                blockers.append("unequal_crispra_crispri_feature_universes_require_stable_alignment_and_measurement_masks")
            perturbation_rows.append({
                "dataset_id": asset["dataset_id"], "study_id": asset["study_id"],
                "source_path": asset["source_path"], "shape": asset["shape"],
                **gates, "measurement_mask_required": integration["measurement_mask_required"],
                "perturbation_training_ready": False,
                "readiness_blockers": ";".join(dict.fromkeys(blockers)),
            })

    duplicate_rows = []
    for source in read_csv(project / config["inputs"]["normal_duplicates"]):
        duplicate_rows.append({
            "duplicate_group": f"normal:{source['left_dataset']}:{source['right_dataset']}",
            "left_dataset": source["left_dataset"], "right_dataset": source["right_dataset"],
            "exact_overlap_evidence": source["exact_donor_overlap_count"], "action": source["action"],
            "fuzzy_matching_used": source["fuzzy_matching_used"],
        })
    for source in read_csv(project / config["inputs"]["sea_ad_release_lineage"]):
        duplicate_rows.append({
            "duplicate_group": f"sea_ad_release:{source['asset_id']}", "left_dataset": source["old_path"],
            "right_dataset": source["new_path"], "exact_overlap_evidence": source["supersession_type"],
            "action": "preserve_old_for_reproducibility_use_new_as_production_candidate",
            "fuzzy_matching_used": False,
        })
    duplicate_rows.append({
        "duplicate_group": "GSE178317_existing_and_new_processed_assets",
        "left_dataset": "data/raw/kampmann_gse178317", "right_dataset": "data/external/v4/perturbation/GSE178317",
        "exact_overlap_evidence": "same_official_GEO_accession_and_lane_filenames",
        "action": "single_study_group_never_cross_split_or_double_count", "fuzzy_matching_used": False,
    })

    matrix_assets = [row for row in dataset_rows if str(row["documentation_only"]).lower() == "false"]
    maps = {row["dataset_id"]: row for row in mapping_registry}
    ids = {row["dataset_id"]: row for row in identity_rows}
    sem = {row["dataset_id"]: row for row in semantics_rows}
    roles = {row["dataset_id"]: row for row in role_rows}
    virtual = {
        "stage_id": config["stage_id"], "schema_version": config["schema_version"],
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project, text=True).strip(),
        "physical_full_matrix_merge_performed": False,
        "datasets": [{
            "dataset_id": row["dataset_id"], "source_hash": row["source_hash"], "source_path": row["source_path"],
            "shape": row["shape"], "gene_namespace": next(item["gene_namespace"] for item in feature_rows if item["dataset_id"] == row["dataset_id"]),
            "canonical_mapping_file": maps[row["dataset_id"]]["canonical_mapping_file"],
            "cell_identifier_policy": ids[row["dataset_id"]]["cell_identifier_field"],
            "donor_field": ids[row["dataset_id"]]["donor_field"], "study_field": "study_id",
            "region_field": ids[row["dataset_id"]]["region_field"], "assay_field": ids[row["dataset_id"]]["assay_field"],
            "matrix_semantics": sem[row["dataset_id"]]["matrix_semantics"],
            "allowed_role": roles[row["dataset_id"]]["allowed_role"], "forbidden_role": roles[row["dataset_id"]]["forbidden_role"],
            "duplicate_group": ";".join(item["duplicate_group"] for item in duplicate_rows if row["dataset_id"] in {item["left_dataset"], item["right_dataset"]}) or "none_registered",
            "future_vocabulary_projection_status": maps[row["dataset_id"]]["future_vocabulary_projection_status"],
            "future_split_grouping_keys": ids[row["dataset_id"]]["future_split_grouping_keys"],
            "feature_space_class": next(item["feature_space_class"] for item in modality_rows if item["dataset_id"] == row["dataset_id"]),
            "integration_path": next(item["integration_path"] for item in modality_rows if item["dataset_id"] == row["dataset_id"]),
            "missing_modality_policy": next(item["missing_modality_policy"] for item in modality_rows if item["dataset_id"] == row["dataset_id"]),
            "measurement_mask_required": next(item["measurement_mask_required"] for item in modality_rows if item["dataset_id"] == row["dataset_id"]),
            "equivalent_to_full_rna_matrix": next(item["equivalent_to_full_rna_matrix"] for item in modality_rows if item["dataset_id"] == row["dataset_id"]),
        } for row in matrix_assets],
    }

    write_csv(output / OUTPUTS["datasets"], dataset_rows)
    write_csv(output / OUTPUTS["semantics"], semantics_rows)
    write_csv(output / OUTPUTS["features"], feature_rows)
    write_csv(output / OUTPUTS["mappings"], mapping_registry)
    write_csv(output / OUTPUTS["identity"], identity_rows)
    write_csv(output / OUTPUTS["duplicates"], sorted(duplicate_rows, key=lambda row: row["duplicate_group"]))
    write_csv(output / OUTPUTS["roles"], role_rows)
    write_csv(output / OUTPUTS["modalities"], modality_rows)
    write_csv(output / OUTPUTS["perturbation"], perturbation_rows)
    atomic_text(output / OUTPUTS["virtual"], json.dumps(virtual, indent=2, sort_keys=True) + "\n")
    atomic_text(project / config["policy"]["bounded_sample_path"], json.dumps(bounded_samples, indent=2, sort_keys=True) + "\n")

    unresolved_mapping = sum(row["future_vocabulary_projection_status"] == "blocked_or_not_applicable" and not next(asset["documentation_only"] for asset in assets if asset["dataset_id"] == row["dataset_id"]) for row in mapping_registry)
    unresolved_donor = sum(row["donor_field"] == "unresolved" for row in identity_rows if not next(asset["documentation_only"] for asset in assets if asset["dataset_id"] == row["dataset_id"]))
    unresolved_spatial_section = sum(
        row["section_field"] == "unresolved" and any(token in next(asset["modality"] for asset in assets if asset["dataset_id"] == row["dataset_id"]).lower() for token in ("merfish", "merscope", "xenium"))
        for row in identity_rows
    )
    unresolved_perturbation_shape = sum(row["shape"] == "unresolved_source_archive_or_table" for row in perturbation_rows)
    perturbation_training_ready = bool(perturbation_rows) and all(row["perturbation_training_ready"] for row in perturbation_rows if "documentation_asset_not_training_matrix" not in row["readiness_blockers"])
    readiness_blockers = []
    if unresolved_spatial_section:
        readiness_blockers.append("exact_spatial_section_identity_unresolved")
    if not perturbation_training_ready:
        readiness_blockers.append("perturbation_asset_content_harmonization_incomplete")
    report = {
        "stage_id": config["stage_id"], "schema_version": config["schema_version"],
        "source_commit": virtual["source_commit"], "dataset_count": len(dataset_rows),
        "virtual_matrix_dataset_count": len(matrix_assets), "mapping_sidecar_count": len(set(mapping_cache.values())),
        "unresolved_exact_feature_mapping_count": unresolved_mapping,
        "unresolved_donor_dataset_count": unresolved_donor,
        "unresolved_spatial_section_dataset_count": unresolved_spatial_section,
        "unresolved_perturbation_shape_asset_count": unresolved_perturbation_shape,
        "perturbation_asset_count": len(perturbation_rows),
        "perturbation_training_ready": perturbation_training_ready,
        "spatial_zero_fill_into_rna_vocabulary_allowed": False,
        "atac_features_allowed_in_rna_vocabulary": False,
        "holdout_may_influence_model_design": False,
        "pathology_context_allowed_in_foundation_supervision": False,
        "all_source_paths_exist_and_sizes_match": True, "all_source_hashes_registered": all(len(row["source_hash"]) == 64 for row in dataset_rows),
        "physical_full_matrix_merge_performed": False, "final_vocabulary_frozen": False,
        "donor_split_frozen": False, "pathology_values_used": False, "model_trained": False,
        "fuzzy_gene_aliasing_used": False, "fuzzy_donor_inference_used": False,
        "bounded_feature_samples_written": len(bounded_samples),
        "virtual_harmonization_layer_pass": True,
        "ready_for_stage81a2_review": not readiness_blockers,
        "readiness_blockers": readiness_blockers,
    }
    atomic_text(output / OUTPUTS["report"], json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
