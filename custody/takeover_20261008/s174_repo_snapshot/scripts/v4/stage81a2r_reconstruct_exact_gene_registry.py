"""Reconstruct a provisional maximal exact gene address space from frozen A2 metadata."""

from __future__ import annotations

import argparse
import hashlib
import gzip
import json
import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import yaml


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def atomic_csv(path: Path, frame: pd.DataFrame, compression: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, suffix=".csv", encoding="utf-8", newline="") as handle:
        raw = Path(handle.name)
    temporary = raw
    try:
        frame.to_csv(raw, index=False, lineterminator="\n")
        if compression == "gzip":
            with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent, suffix=".csv.gz") as handle:
                temporary = Path(handle.name)
                with raw.open("rb") as source, gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0) as target:
                    shutil.copyfileobj(source, target)
        else:
            temporary = raw
        os.replace(temporary, path)
    finally:
        raw.unlink(missing_ok=True)
        temporary.unlink(missing_ok=True)


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        handle.write(text); temporary = Path(handle.name)
    os.replace(temporary, path)


def source_family(source: str) -> str:
    return "NPH52" if source.startswith("NPH52::") else "SEA_AD" if source == "SEA_AD_COMMON" else "HVS"


def build(project: Path, config: dict) -> dict:
    paths = {key: project / value for key, value in config["outputs"].items()}
    source_path = project / config["inputs"]["frozen_gene_registry"]
    assets_path = project / config["inputs"]["frozen_asset_registry"]
    source = pd.read_csv(source_path, dtype=str, keep_default_na=False)
    exact = source[(source.mapping_status == "exact") & (source.rna_vocabulary_eligible.str.lower() == "true")].copy()
    exact["source_family"] = exact.source_dataset_id.map(source_family)

    preferred = exact.assign(priority=exact.source_dataset_id.map({"HVS_COMMON": 0, "SEA_AD_COMMON": 1}).fillna(2))
    preferred = preferred.sort_values(["canonical_ensembl_gene_id", "priority", "canonical_hgnc_symbol"])
    display = preferred.drop_duplicates("canonical_ensembl_gene_id").set_index("canonical_ensembl_gene_id").canonical_hgnc_symbol
    support = exact.groupby("canonical_ensembl_gene_id").agg(
        source_support_count=("source_dataset_id", "nunique"),
        source_family_support=("source_family", lambda x: "|".join(sorted(set(x)))),
        source_symbol_count=("canonical_hgnc_symbol", "nunique"),
    )
    registry = support.reset_index().sort_values("canonical_ensembl_gene_id").reset_index(drop=True)
    registry.insert(0, "successor_gene_index", range(len(registry)))
    registry.insert(2, "canonical_symbol", registry.canonical_ensembl_gene_id.map(display))
    registry["stable_canonical_identifier"] = registry.canonical_ensembl_gene_id
    registry["mapping_authority"] = "frozen_A2_source_provided_Ensembl_identity"
    registry["mapping_release_version"] = "source_specific_annotation_release_preserved_in_frozen_A2"
    registry["mapping_method"] = "exact_stable_Ensembl_identity; HVS_display_symbol_preferred_then_SEA_AD_then_NPH"
    registry["exactness_class"] = registry.source_symbol_count.map(lambda value: "EXACT_STABLE_ID_SYMBOL_RELEASE_CONFLICT" if int(value) > 1 else "EXACT_STABLE_ID_AND_SYMBOL")
    registry["ambiguity_status"] = registry.source_symbol_count.map(lambda value: "symbol_release_conflict_identity_unambiguous" if int(value) > 1 else "none")
    semantic = "".join(f"{row.canonical_ensembl_gene_id}\t{row.canonical_symbol}\n" for row in registry.itertuples())
    semantic_hash = hashlib.sha256(semantic.encode("utf-8")).hexdigest()
    registry["registry_semantic_hash"] = semantic_hash

    retained_ids = set(registry.canonical_ensembl_gene_id)
    decisions = source.copy()
    decisions["mapping_decision"] = "OTHER_EXPLICIT_REASON"
    decisions.loc[decisions.canonical_ensembl_gene_id.isin(retained_ids) & (decisions.mapping_status == "exact"), "mapping_decision"] = "EXACT_RETAINED"
    decisions.loc[(decisions.mapping_status == "unresolved") & (decisions.mapping_ambiguity.str.lower() == "true"), "mapping_decision"] = "AMBIGUOUS_UNRESOLVED"
    decisions.loc[decisions.source_feature_type.ne("Gene Expression"), "mapping_decision"] = "NON_GENE_OR_UNSUPPORTED"
    decisions["decision_reason"] = decisions.apply(lambda row: "stable exact Ensembl identity retained" if row.mapping_decision == "EXACT_RETAINED" else (row.exclusion_reason or row.mapping_method), axis=1)

    measured_by_source = exact.groupby("source_dataset_id").canonical_ensembl_gene_id.apply(set).to_dict()
    assets = pd.read_csv(assets_path, dtype=str, keep_default_na=False)
    units = []
    for row in assets.itertuples(index=False):
        if row.study_id == "HVS":
            units.append((row.dataset_id, "HVS_COMMON"))
        elif row.study_id == "SEA_AD":
            units.append((row.dataset_id, "SEA_AD_COMMON"))
    units.extend((source_id.replace("NPH52::", "NPH52::matrix::"), source_id) for source_id in sorted(measured_by_source) if source_id.startswith("NPH52::"))
    support_rows = []
    for matrix_id, source_id in units:
        measured = measured_by_source.get(source_id, set())
        universe_hash = hashlib.sha256("\n".join(sorted(measured)).encode()).hexdigest()
        for item in registry.itertuples(index=False):
            present = item.canonical_ensembl_gene_id in measured
            support_rows.append({
                "matrix_id": matrix_id, "source_dataset_id": source_id,
                "successor_gene_index": item.successor_gene_index,
                "canonical_ensembl_gene_id": item.canonical_ensembl_gene_id,
                "canonical_symbol": item.canonical_symbol,
                "measured_gene": present,
                "measurement_status": "addressable_measured_zero_or_nonzero_at_runtime" if present else "structurally_unmeasured",
                "measured_zero_distinct_from_unmeasured": True,
                "source_feature_universe_hash": universe_hash,
            })
    measurement = pd.DataFrame(support_rows)

    atomic_csv(paths["exact_registry"], registry)
    atomic_csv(paths["mapping_decisions"], decisions, "gzip")
    atomic_csv(paths["measurement_support"], measurement, "gzip")
    artifact_hashes = {str(path.relative_to(project)).replace("\\", "/"): sha256_file(path) for path in (paths["exact_registry"], paths["mapping_decisions"], paths["measurement_support"])}
    provenance = {
        "stage": config["stage_id"], "status": config["status"],
        "candidate_gene_count": len(registry), "source_mapping_records": len(decisions),
        "exact_retained_source_records": int((decisions.mapping_decision == "EXACT_RETAINED").sum()),
        "ambiguous_unresolved_source_records": int((decisions.mapping_decision == "AMBIGUOUS_UNRESOLVED").sum()),
        "stable_ids_with_symbol_release_conflict": int((registry.source_symbol_count > 1).sum()),
        "semantic_hash": semantic_hash, "artifact_hashes": artifact_hashes,
        "mapping_authority": "frozen Stage81A2 exact source-provided Ensembl/symbol evidence",
        "external_mapping_downloaded": False, "fuzzy_mapping_used": False,
        "historical_stage81a2_modified": False, "biological_top_k_used": False,
        "claim_boundary": "PROVISIONAL DEVELOPMENT EVIDENCE; NOT FROZEN",
    }
    atomic_json(paths["mapping_provenance"], provenance)
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a2r_a3r_microqual.yaml"))
    args = parser.parse_args()
    project = args.project_dir.resolve()
    with (project / args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    result = build(project, config)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
