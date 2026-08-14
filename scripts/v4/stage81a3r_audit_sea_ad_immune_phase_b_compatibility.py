"""Audit SEA-AD Immune compatibility without admitting it to Phase A."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import yaml

from sea_ad_jepa.v4.a3r_global_state import collision_evidence_class


STATUS = "SEA_AD_IMMUNE_PHASE_B_COMPATIBILITY_ONLY"
ROLE = "PHASE_B_IMMUNE_MICROGLIA_PVM_CONTINUATION"
FROZEN_HASH = "5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff"
IMMUNE_RELATIVE = "data/external/v4/sea_ad/multiregion/SEAAD_Immune_10-region_RNAseq_final-nuclei.2026-06-22.h5ad"


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_csv(path: Path, frame: pd.DataFrame, *, compress: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent, suffix=".csv.gz" if compress else ".csv")
    os.close(descriptor)
    temporary = Path(name)
    if compress:
        with temporary.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                    frame.to_csv(text, index=False, lineterminator="\n")
    else:
        frame.to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, path)


def h5_vector(group: h5py.Group, key: str) -> np.ndarray:
    node = group[key]
    if isinstance(node, h5py.Dataset):
        values = node[:]
    elif "categories" in node and "codes" in node:
        categories = node["categories"][:]
        values = categories[node["codes"][:]]
    else:
        raise RuntimeError(f"unsupported HDF5 vector: {group.name}/{key}")
    return np.asarray([value.decode() if isinstance(value, bytes) else str(value) for value in values])


def stable_hash(values: set[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(values)) + "\n").encode()).hexdigest()


def map_addresses(identity: pd.DataFrame, registry: pd.DataFrame) -> pd.DataFrame:
    current = set(registry.loc[registry.identity_class.eq("current_exact"), "molecular_address_id"])
    legacy = dict(zip(
        registry.loc[registry.identity_class.eq("legacy_exact"), "legacy_source_exact_id"],
        registry.loc[registry.identity_class.eq("legacy_exact"), "molecular_address_id"],
        strict=True,
    ))
    anchored = dict(zip(
        registry.loc[registry.identity_class.eq("source_native_anchored"), "source_native_anchor"],
        registry.loc[registry.identity_class.eq("source_native_anchored"), "molecular_address_id"],
        strict=True,
    ))
    addresses, classes = [], []
    for row in identity.itertuples(index=False):
        current_id = str(row.current_ensembl_gene_id)
        source_id = str(row.source_ensembl_stable_id)
        native_id = str(row.source_native_id)
        if current_id in current:
            addresses.append(current_id); classes.append("current_exact")
        elif source_id in legacy:
            addresses.append(legacy[source_id]); classes.append("legacy_exact")
        elif native_id in anchored:
            addresses.append(anchored[native_id]); classes.append("source_native_anchored")
        else:
            addresses.append(""); classes.append("nonuniversal_preserved_evidence")
    result = identity.copy()
    result["molecular_address_id"] = addresses
    result["identity_class_for_frozen_address"] = classes
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--source-project", type=Path, required=True)
    args = parser.parse_args()
    project, source = args.project_dir.resolve(), args.source_project.resolve()
    config = yaml.safe_load((project / "configs/v4/stage81a3r_real_train_global_state.yaml").read_text(encoding="utf-8"))
    outputs = {key: project / value for key, value in config["outputs"].items()}
    immune_path = source / IMMUNE_RELATIVE

    registry = pd.read_csv(source / config["inputs"]["address_registry"], dtype=str, keep_default_na=False)
    if len(registry) != 41_238 or registry.registry_semantic_hash.nunique() != 1 or registry.registry_semantic_hash.iloc[0] != FROZEN_HASH:
        raise RuntimeError("frozen molecular-address registry changed")
    assets = pd.read_csv(source / config["inputs"]["assets"], dtype=str, keep_default_na=False)
    if IMMUNE_RELATIVE in set(assets.matrix_path_or_object):
        raise RuntimeError("Immune object was incorrectly admitted to frozen Phase A assets")
    regional = assets[(assets.study_id == "SEA_AD") & assets.foundation_eligible.str.lower().eq("true")].copy()
    if len(regional) != 11:
        raise RuntimeError("frozen 11-operator SEA-AD contract changed")

    identity = pd.read_csv(
        source / "results/v4/stage81a2r_projectwide_source_feature_identity_candidate.csv.gz",
        dtype=str, keep_default_na=False, low_memory=False,
    )
    identity = identity[identity.matrix_id.eq(IMMUNE_RELATIVE)].copy()
    identity["source_feature_index"] = identity.source_feature_index.astype(int)
    identity = identity.sort_values("source_feature_index")
    if len(identity) != 36_601 or identity.source_feature_index.tolist() != list(range(36_601)):
        raise RuntimeError("Immune source-feature contract changed")
    mapped = map_addresses(identity, registry)
    universal = mapped[mapped.molecular_address_id.ne("")].copy()
    feature_summary = mapped.groupby("identity_class_for_frozen_address", as_index=False).agg(
        source_feature_rows=("source_feature_index", "size"),
        unique_universal_addresses=("molecular_address_id", lambda values: int(pd.Series(values)[pd.Series(values).ne("")].nunique())),
    )
    feature_summary.insert(0, "status", STATUS)
    feature_summary.insert(1, "role", ROLE)

    collisions = pd.read_csv(
        source / "results/v4/stage81a2r_projectwide_within_matrix_collisions_candidate.csv",
        dtype=str, keep_default_na=False,
    )
    collisions = collisions[collisions.matrix_id.eq(IMMUNE_RELATIVE)].copy()
    collision_rows: list[dict[str, Any]] = []
    for row in collisions.itertuples(index=False):
        for index, raw_id, symbol in zip(
            str(row.source_feature_indices).split("|"),
            str(row.raw_feature_ids).split("|"),
            str(row.raw_symbols).split("|"),
            strict=True,
        ):
            collision_rows.append({
                "status": STATUS, "role": ROLE,
                "molecular_address_id": str(row.canonical_ensembl_gene_id),
                "source_feature_index": int(index), "raw_feature_id": raw_id, "raw_symbol": symbol,
                "colliding_row_count": int(row.colliding_row_count), "resolution_tiers": str(row.resolution_tiers),
                "collision_evidence_class": collision_evidence_class("current_exact", str(row.resolution_tiers)),
                "assay_measured": True, "scalar_materializable": False,
                "observation_state": "MEASURED_COLLISION_UNRESOLVED",
                "aggregation_rule_applied": False,
            })
    collision_ledger = pd.DataFrame(collision_rows).sort_values(["molecular_address_id", "source_feature_index"])
    if len(collisions) != 710 or collisions.canonical_ensembl_gene_id.nunique() != 710:
        raise RuntimeError("Immune collision accounting changed")

    with h5py.File(immune_path, "r") as handle:
        immune_cells_array = h5_vector(handle["obs"], "exp_component_name")
        immune_donors_array = h5_vector(handle["obs"], "Donor ID")
        matrix_shape = [int(value) for value in handle["X"].attrs["shape"]]
    immune_cells = set(immune_cells_array)
    immune_donors = set(immune_donors_array)
    if len(immune_cells_array) != matrix_shape[0]:
        raise RuntimeError("Immune cell identity count does not match matrix")

    overlap_rows, overlap_ids = [], []
    regional_donor_union: set[str] = set()
    regional_cell_union: set[str] = set()
    for asset in regional.sort_values("dataset_id").itertuples(index=False):
        with h5py.File(source / str(asset.matrix_path_or_object), "r") as handle:
            cells = set(h5_vector(handle["obs"], "exp_component_name"))
            donors = set(h5_vector(handle["obs"], "Donor ID"))
        cell_overlap = immune_cells & cells
        donor_overlap = immune_donors & donors
        regional_cell_union.update(cells)
        regional_donor_union.update(donors)
        overlap_rows.append({
            "status": STATUS, "role": ROLE, "regional_operator": str(asset.dataset_id),
            "regional_cells": len(cells), "immune_cells": len(immune_cells),
            "exact_cell_id_overlap": len(cell_overlap), "donor_overlap": len(donor_overlap),
            "donor_overlap_is_duplicate_cell_evidence": False,
        })
        overlap_ids.extend({
            "status": STATUS, "role": ROLE, "regional_operator": str(asset.dataset_id), "exact_source_cell_id": cell
        } for cell in sorted(cell_overlap))
    union_cell_overlap = immune_cells & regional_cell_union
    union_donor_overlap = immune_donors & regional_donor_union
    cell_overlap = pd.DataFrame(overlap_rows)
    exact_overlap_ids = pd.DataFrame(overlap_ids, columns=["status", "role", "regional_operator", "exact_source_cell_id"])

    split = pd.read_csv(source / config["inputs"]["split_registry"], dtype=str, keep_default_na=False)
    sea_split = split[(split.split_domain == "foundation") & (split.study_id == "SEA_AD")].copy()
    split_map = {str(row.canonical_person_id).split("::", 1)[-1]: str(row.split) for row in sea_split.itertuples(index=False)}
    donor_membership = pd.DataFrame({"donor_id": sorted(immune_donors)})
    donor_membership.insert(0, "role", ROLE)
    donor_membership.insert(0, "status", STATUS)
    donor_membership["frozen_foundation_split"] = donor_membership.donor_id.map(split_map).fillna("NOT_IN_FROZEN_FOUNDATION_SPLIT")
    donor_membership["present_in_any_of_11_regional_objects"] = donor_membership.donor_id.isin(regional_donor_union)
    donor_membership["donor_overlap_is_duplicate_cell_evidence"] = False

    collision_classes = (
        collision_ledger[["molecular_address_id", "collision_evidence_class"]]
        .drop_duplicates().collision_evidence_class.value_counts().to_dict()
    )
    report = {
        "status": STATUS, "role": ROLE,
        "excluded_from_phase_a_whole_taxonomy_operators": True,
        "included_in_a3r_global_basis": False,
        "changes_k_bulk": False,
        "changes_frozen_address_registry": False,
        "frozen_address_semantic_hash": FROZEN_HASH,
        "source": {"relative_path": IMMUNE_RELATIVE, "matrix_shape": matrix_shape, "source_feature_count": len(mapped)},
        "feature_compatibility": {
            "measured_frozen_molecular_addresses": int(universal.molecular_address_id.nunique()),
            "current_exact_coverage": int(universal.loc[universal.identity_class_for_frozen_address.eq("current_exact"), "molecular_address_id"].nunique()),
            "legacy_exact_coverage": int(universal.loc[universal.identity_class_for_frozen_address.eq("legacy_exact"), "molecular_address_id"].nunique()),
            "source_native_anchored_coverage": int(universal.loc[universal.identity_class_for_frozen_address.eq("source_native_anchored"), "molecular_address_id"].nunique()),
            "unresolved_nonuniversal_source_rows": int(mapped.molecular_address_id.eq("").sum()),
            "within_matrix_collision_pairs": int(len(collisions)),
            "unique_universal_addresses_affected_by_collisions": int(collisions.canonical_ensembl_gene_id.nunique()),
            "collision_classes": collision_classes,
            "aggregation_rule_applied": False,
        },
        "cell_identity": {
            "source_cell_ids_available": True,
            "source_cell_id_rows": len(immune_cells_array),
            "unique_source_cell_ids": len(immune_cells),
            "duplicate_source_cell_id_rows": len(immune_cells_array) - len(immune_cells),
            "source_cell_id_set_sha256": stable_hash(immune_cells),
            "exact_cell_id_overlap_with_11_regional_union": len(union_cell_overlap),
        },
        "donors": {
            "immune_unique_donors": len(immune_donors),
            "donor_set_sha256": stable_hash(immune_donors),
            "donor_overlap_with_11_regional_union": len(union_donor_overlap),
            "split_membership_counts": donor_membership.frozen_foundation_split.value_counts().to_dict(),
            "donor_overlap_is_duplicate_cell_evidence": False,
        },
        "compatibility_conclusion": "CAN_BE_MATERIALIZED_LATER_AGAINST_SAME_FROZEN_ADDRESS_CONTRACT_PENDING_COLLISION_POLICY",
        "phase_b_sampling_must_handle_exact_cell_overlap": bool(union_cell_overlap),
    }
    atomic_csv(outputs["immune_phase_b_feature_summary"], feature_summary)
    atomic_csv(outputs["immune_phase_b_collision_ledger"], collision_ledger, compress=True)
    atomic_csv(outputs["immune_phase_b_cell_overlap"], cell_overlap)
    atomic_csv(outputs["immune_phase_b_exact_overlap_ids"], exact_overlap_ids, compress=True)
    atomic_csv(outputs["immune_phase_b_donor_membership"], donor_membership)
    atomic_json(outputs["immune_phase_b_report"], report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
