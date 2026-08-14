"""Audit within-operator expression collisions without materializing them."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import tempfile
from itertools import combinations
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import yaml

from sea_ad_jepa.v4.a3r_global_state import collision_evidence_class


STATUS = "EXPRESSION_MATERIALIZATION_COLLISION_AUDIT_HUMAN_REVIEW_REQUIRED"
FROZEN_HASH = "5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff"


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


def balanced_rows(donors: np.ndarray, cells: np.ndarray, cap: int, seed: int) -> np.ndarray:
    groups: dict[str, list[tuple[str, int]]] = {}
    for index, (donor, cell) in enumerate(zip(donors, cells, strict=True)):
        key = hashlib.sha256(f"{seed}|{donor}|{cell}".encode()).hexdigest()
        groups.setdefault(str(donor), []).append((key, index))
    for values in groups.values():
        values.sort()
    chosen: list[int] = []
    depth = 0
    while len(chosen) < min(cap, len(donors)):
        added = False
        for donor in sorted(groups):
            if depth < len(groups[donor]):
                chosen.append(groups[donor][depth][1])
                added = True
                if len(chosen) == min(cap, len(donors)):
                    break
        if not added:
            break
        depth += 1
    return np.asarray(chosen, dtype=np.int64)


def pair_metrics(left: np.ndarray, right: np.ndarray) -> dict[str, Any]:
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    correlation = float(np.corrcoef(left, right)[0, 1]) if left.std() > 0 and right.std() > 0 else float("nan")
    return {
        "exact_count_vector_equality": bool(np.array_equal(left, right)),
        "fraction_cells_both_nonzero": float(np.mean((left > 0) & (right > 0))),
        "row_total_count_a": float(left.sum()),
        "row_total_count_b": float(right.sum()),
        "pearson_correlation": correlation,
    }


def source_key_from_identity(row: Any) -> str:
    if str(row.dataset_id) == "NPH52":
        return "NPH52::" + Path(str(row.matrix_id)).name
    if str(row.dataset_id) == "SEA_AD":
        return "SEA_AD_COMMON"
    if str(row.dataset_id) == "HVS":
        return "HVS_COMMON"
    return ""


def build_ledger(source: Path, collisions: pd.DataFrame, registry: pd.DataFrame) -> pd.DataFrame:
    provenance = pd.read_csv(
        source / "results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz",
        low_memory=False,
    )
    identity_columns = [
        "dataset_id", "matrix_id", "source_feature_index", "raw_feature_id", "raw_gene_symbol",
        "source_ensembl_id", "source_refseq_id", "source_ncbi_gene_id", "source_transcript_id",
        "source_chromosome", "source_start", "source_end", "source_strand", "source_biotype",
        "terminal_disposition", "mapping_evidence_class", "mapping_authority", "mapping_evidence_file",
        "foundation_eligible",
    ]
    identity = pd.read_csv(
        source / "results/v4/stage81a2r_projectwide_source_feature_identity_candidate.csv.gz",
        usecols=identity_columns,
        low_memory=False,
    )
    identity = identity[identity.foundation_eligible.astype(bool)].copy()
    identity["source_dataset_id"] = [source_key_from_identity(row) for row in identity.itertuples(index=False)]
    assets = pd.read_csv(source / "results/v4/stage81a2_canonical_asset_registry.csv")
    path_to_operator = dict(zip(assets.matrix_path_or_object.astype(str), assets.dataset_id.astype(str)))
    identity = identity[
        identity.dataset_id.astype(str).eq("NPH52")
        | identity.matrix_id.astype(str).isin(path_to_operator)
    ].copy()
    identity["audit_matrix_id"] = [
        "NPH52::matrix::" + Path(str(matrix_id)).name
        if str(dataset_id) == "NPH52"
        else path_to_operator.get(str(matrix_id), "")
        for dataset_id, matrix_id in zip(identity.dataset_id, identity.matrix_id, strict=True)
    ]
    if (identity.audit_matrix_id == "").any():
        raise RuntimeError("foundation identity row lacks operator mapping")
    metadata_columns = [column for column in identity_columns if column not in {"dataset_id", "matrix_id", "foundation_eligible"}]
    identity = identity[["audit_matrix_id", "source_dataset_id", *metadata_columns]].drop_duplicates()
    conflict = identity.groupby(["audit_matrix_id", "source_feature_index"]).size()
    if (conflict > 1).any():
        raise RuntimeError("conflicting source-feature metadata in identity ledger")

    rows: list[dict[str, Any]] = []
    class_map = registry.set_index("molecular_address_id").identity_class.to_dict()
    for collision in collisions.itertuples(index=False):
        indices = [int(value) for value in str(collision.source_feature_indices).split("|")]
        symbols = str(collision.raw_symbols).split("|")
        raw_ids = str(collision.raw_ids).split("|")
        for offset, index in enumerate(indices):
            rows.append({
                "operator_family": "NPH52" if str(collision.matrix_id).startswith("NPH52::") else "SEA_AD",
                "matrix_id": str(collision.matrix_id),
                "source_dataset_id": str(collision.source_object),
                "molecular_address_id": str(collision.canonical_ensembl_gene_id),
                "identity_class": class_map[str(collision.canonical_ensembl_gene_id)],
                "source_feature_index": index,
                "collision_source_row_offset": offset,
                "raw_symbol_from_collision_ledger": symbols[offset],
                "raw_id_from_collision_ledger": raw_ids[offset],
                "resolution_tiers": str(collision.resolution_tiers),
                "already_duplicate_before_remapping": bool(collision.already_duplicate_before_remapping),
                "colliding_row_count": int(collision.colliding_row_count),
            })
    ledger = pd.DataFrame(rows)
    provenance_columns = [
        "source_dataset_id", "source_feature_index", "molecular_address_id", "raw_source_feature_id",
        "raw_source_feature_symbol", "source_exact_ensembl_id", "source_native_anchor",
        "mapping_evidence_class", "mapping_authority", "mapping_evidence_file", "measurement_provenance_key",
    ]
    ledger = ledger.merge(provenance[provenance_columns], on=["source_dataset_id", "source_feature_index", "molecular_address_id"], how="left", validate="many_to_one")
    ledger = ledger.merge(
        identity,
        left_on=["matrix_id", "source_dataset_id", "source_feature_index"],
        right_on=["audit_matrix_id", "source_dataset_id", "source_feature_index"],
        how="left",
        validate="many_to_one",
        suffixes=("_frozen", "_source"),
    ).drop(columns="audit_matrix_id")
    if ledger.raw_source_feature_id.isna().any():
        raise RuntimeError("collision row lacks frozen source provenance")
    ledger["collision_evidence_class"] = [
        collision_evidence_class(identity_class, tiers)
        for identity_class, tiers in zip(ledger.identity_class, ledger.resolution_tiers, strict=True)
    ]
    ledger["scalar_materialization_status"] = "MEASURED_COLLISION_UNRESOLVED"
    ledger["assay_measured"] = True
    ledger["scalar_materializable"] = False
    return ledger.sort_values(["matrix_id", "molecular_address_id", "source_feature_index"]).reset_index(drop=True)


def sea_ad_diagnostics(source: Path, config: dict[str, Any], collisions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    assets = pd.read_csv(source / config["inputs"]["assets"])
    semantics = pd.read_csv(source / config["inputs"]["matrix_semantics"])
    split = pd.read_csv(source / config["inputs"]["split_registry"])
    train = {
        str(value).split("::", 1)[-1]
        for value in split.loc[
            (split.split_domain == "foundation") & (split.split == "train") & (split.study_id == "SEA_AD"),
            "canonical_person_id",
        ]
    }
    pair_rows: list[dict[str, Any]] = []
    mass_rows: list[dict[str, Any]] = []
    for matrix_id, local in collisions[~collisions.matrix_id.astype(str).str.startswith("NPH52::")].groupby("matrix_id", sort=True):
        asset = assets[assets.dataset_id.eq(matrix_id)].iloc[0]
        contract = semantics[semantics.dataset_id.eq(matrix_id)].iloc[0]
        feature_indices = sorted({int(value) for values in local.source_feature_indices for value in str(values).split("|")})
        feature_map = {value: offset for offset, value in enumerate(feature_indices)}
        with h5py.File(source / str(asset.matrix_path_or_object), "r") as handle:
            donors = h5_vector(handle["obs"], "Donor ID")
            cells = h5_vector(handle["obs"], "exp_component_name")
            eligible = np.where(np.isin(donors, sorted(train)))[0]
            selected = eligible[balanced_rows(donors[eligible], cells[eligible], int(config["sampling"]["cells_per_h5_matrix"]), int(config["sampling"]["seed"]))]
            node = handle[str(contract.matrix_slot)]
            matrix = np.zeros((len(selected), len(feature_indices)), dtype=np.int64)
            total_mass = 0
            for output_row, source_row in enumerate(selected):
                start, end = int(node["indptr"][source_row]), int(node["indptr"][source_row + 1])
                columns = np.asarray(node["indices"][start:end], dtype=np.int64)
                values = np.asarray(node["data"][start:end], dtype=np.int64)
                total_mass += int(values.sum())
                for column, value in zip(columns, values, strict=True):
                    local_column = feature_map.get(int(column))
                    if local_column is not None:
                        matrix[output_row, local_column] = int(value)
        collision_mass = int(matrix.sum())
        mass_rows.append({
            "operator_family": "SEA_AD", "matrix_id": matrix_id, "bounded_train_cells": len(selected),
            "source_feature_rows": int(asset.n_vars), "collision_source_rows": len(feature_indices),
            "total_source_count_mass": total_mass, "collision_source_count_mass": collision_mass,
            "collision_source_count_mass_fraction": collision_mass / total_mass if total_mass else float("nan"),
        })
        for record in local.itertuples(index=False):
            indices = [int(value) for value in str(record.source_feature_indices).split("|")]
            symbols = str(record.raw_symbols).split("|")
            raw_ids = str(record.raw_ids).split("|")
            for left_offset, right_offset in combinations(range(len(indices)), 2):
                left_index, right_index = indices[left_offset], indices[right_offset]
                pair_rows.append({
                    "operator_family": "SEA_AD", "matrix_id": matrix_id,
                    "molecular_address_id": str(record.canonical_ensembl_gene_id),
                    "source_feature_index_a": left_index, "source_feature_index_b": right_index,
                    "raw_source_feature_id_a": raw_ids[left_offset], "raw_source_feature_id_b": raw_ids[right_offset],
                    "raw_symbol_a": symbols[left_offset], "raw_symbol_b": symbols[right_offset],
                    "bounded_train_cells": len(selected),
                    **pair_metrics(matrix[:, feature_map[left_index]], matrix[:, feature_map[right_index]]),
                })
    return pd.DataFrame(pair_rows), pd.DataFrame(mass_rows)


def genomic_overlap_status(row: Any, lookup: dict[tuple[str, str, int], dict[str, Any]]) -> str:
    left = lookup.get((str(row.matrix_id), str(row.molecular_address_id), int(row.source_feature_index_a)), {})
    right = lookup.get((str(row.matrix_id), str(row.molecular_address_id), int(row.source_feature_index_b)), {})
    required = (left.get("source_chromosome"), left.get("source_start"), left.get("source_end"), right.get("source_chromosome"), right.get("source_start"), right.get("source_end"))
    if any(pd.isna(value) for value in required):
        return "COORDINATES_UNAVAILABLE"
    if str(required[0]) != str(required[3]):
        return "EXACT_COORDINATES_DISJOINT"
    return "EXACT_COORDINATES_OVERLAP" if max(float(required[1]), float(required[4])) <= min(float(required[2]), float(required[5])) else "EXACT_COORDINATES_DISJOINT"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--source-project", type=Path, required=True)
    parser.add_argument("--nph-pairs", type=Path, required=True)
    parser.add_argument("--nph-mass", type=Path, required=True)
    args = parser.parse_args()
    project = args.project_dir.resolve()
    source = args.source_project.resolve()
    config = yaml.safe_load((project / "configs/v4/stage81a3r_real_train_global_state.yaml").read_text(encoding="utf-8"))
    registry = pd.read_csv(source / config["inputs"]["address_registry"])
    if len(registry) != 41_238 or registry.registry_semantic_hash.nunique() != 1 or registry.registry_semantic_hash.iloc[0] != FROZEN_HASH:
        raise RuntimeError("frozen A2R molecular-address contract changed")
    collisions = pd.read_csv(source / "results/v4/stage81a2r_within_matrix_mapping_collisions_candidate.csv")
    if len(collisions) != 11_435 or collisions.matrix_id.nunique() != 18:
        raise RuntimeError("frozen collision ledger contract changed")
    ledger = build_ledger(source, collisions, registry)
    sea_pairs, sea_mass = sea_ad_diagnostics(source, config, collisions)
    def read_one_or_directory(path: Path, pattern: str) -> pd.DataFrame:
        files = sorted(path.glob(pattern)) if path.is_dir() else [path]
        if len(files) != 7:
            raise RuntimeError(f"expected seven isolated NPH diagnostic files for {pattern}, found {len(files)}")
        return pd.concat([pd.read_csv(file) for file in files], ignore_index=True)

    nph_pairs = read_one_or_directory(args.nph_pairs, "*.pairs.csv")
    nph_mass = read_one_or_directory(args.nph_mass, "*.mass.csv")
    diagnostics = pd.concat([sea_pairs, nph_pairs], ignore_index=True)
    mass = pd.concat([sea_mass, nph_mass], ignore_index=True)

    lookup = {
        (str(row.matrix_id), str(row.molecular_address_id), int(row.source_feature_index)): row._asdict()
        for row in ledger.itertuples(index=False)
    }
    diagnostics["genomic_overlap_status"] = [genomic_overlap_status(row, lookup) for row in diagnostics.itertuples(index=False)]
    diagnostics["diagnostic_authorizes_aggregation"] = False
    diagnostics = diagnostics.sort_values(["matrix_id", "molecular_address_id", "source_feature_index_a", "source_feature_index_b"]).reset_index(drop=True)

    pair_classes = ledger.groupby(["matrix_id", "molecular_address_id"], as_index=False).agg(
        operator_family=("operator_family", "first"), identity_class=("identity_class", "first"),
        contributing_source_rows=("source_feature_index", "size"),
        collision_evidence_class=("collision_evidence_class", "first"),
        scalar_materialization_status=("scalar_materialization_status", "first"),
    )
    address_summary = pair_classes.groupby(["molecular_address_id", "identity_class"], as_index=False).agg(
        operators_affected=("matrix_id", "nunique"), matrix_address_collision_pairs=("matrix_id", "size"),
        collision_evidence_classes=("collision_evidence_class", lambda values: "|".join(sorted(set(values)))),
    ).sort_values(["identity_class", "molecular_address_id"])
    class_summary = pair_classes.groupby("collision_evidence_class", as_index=False).agg(
        matrix_address_collision_pairs=("matrix_id", "size"),
        unique_universal_addresses=("molecular_address_id", "nunique"),
        operators_affected=("matrix_id", "nunique"),
        contributing_source_rows=("contributing_source_rows", "sum"),
    )
    class_summary["candidate_policy_if_human_approved"] = class_summary.collision_evidence_class.map({
        "EXACT_TECHNICAL_DUPLICATE": "ONE_SCALAR_DO_NOT_SUM",
        "PRIMARY_PLUS_ANNOTATION_REDUNDANCY": "USE_PROVEN_PRIMARY_ONLY",
        "PROVEN_ADDITIVE_NONOVERLAPPING_COMPONENTS": "SUM",
    }).fillna("MEASURED_COLLISION_UNRESOLVED")
    class_summary["policy_applied"] = False

    support = pd.read_csv(source / config["inputs"]["measurement_support"])
    measured = support[support.measured_address.astype(bool)]
    impact_rows: list[dict[str, Any]] = []
    for family, operators in (("HVS", 24), ("SEA_AD", 11), ("NPH52", 7)):
        prefix = "HVS::" if family == "HVS" else "NPH52::" if family == "NPH52" else "sea_ad_"
        local_pairs = pair_classes[pair_classes.operator_family.eq(family)]
        local_measured = measured[measured.matrix_id.astype(str).str.startswith(prefix)]
        local_mass = mass[mass.operator_family.eq(family)]
        impact_rows.append({
            "operator_family": family,
            "operators": operators,
            "operators_affected": int(local_pairs.matrix_id.nunique()),
            "source_rows_participating_in_collisions": int(local_pairs.contributing_source_rows.sum()),
            "matrix_address_collision_pairs": len(local_pairs),
            "unique_universal_addresses_affected": int(local_pairs.molecular_address_id.nunique()),
            "measured_operator_address_pairs": len(local_measured),
            "fraction_measured_operator_addresses_affected": len(local_pairs) / len(local_measured) if len(local_measured) else 0.0,
            "bounded_train_cells_total": int(local_mass.bounded_train_cells.sum()) if len(local_mass) else 0,
            "collision_source_count_mass": float(local_mass.collision_source_count_mass.sum()) if len(local_mass) else 0.0,
            "total_source_count_mass": float(local_mass.total_source_count_mass.sum()) if len(local_mass) else float("nan"),
            "collision_source_count_mass_fraction": float(local_mass.collision_source_count_mass.sum() / local_mass.total_source_count_mass.sum()) if len(local_mass) and local_mass.total_source_count_mass.sum() else 0.0,
        })
    impact = pd.DataFrame(impact_rows)

    outputs = {key: project / value for key, value in config["outputs"].items()}
    atomic_csv(outputs["collision_ledger"], ledger, compress=True)
    atomic_csv(outputs["collision_address_summary"], address_summary)
    atomic_csv(outputs["collision_class_summary"], class_summary)
    atomic_csv(outputs["collision_diagnostics"], diagnostics, compress=True)
    atomic_csv(outputs["collision_impact"], impact)
    report = {
        "status": STATUS,
        "frozen_molecular_addresses": 41_238,
        "frozen_semantic_hash": FROZEN_HASH,
        "total_contributing_source_rows": int(len(ledger)),
        "matrix_address_collision_pairs": int(len(pair_classes)),
        "unique_universal_addresses_affected": int(address_summary.molecular_address_id.nunique()),
        "fraction_of_universal_addresses_affected": float(address_summary.molecular_address_id.nunique() / 41_238),
        "operators_affected": int(pair_classes.matrix_id.nunique()),
        "families": impact.set_index("operator_family").to_dict(orient="index"),
        "identity_classes_affected": address_summary.groupby("identity_class").molecular_address_id.nunique().to_dict(),
        "collision_classes": class_summary.set_index("collision_evidence_class").to_dict(orient="index"),
        "exact_count_vector_equal_pairs": int(diagnostics.exact_count_vector_equality.sum()),
        "exact_technical_duplicate_cases": int((pair_classes.collision_evidence_class == "EXACT_TECHNICAL_DUPLICATE").sum()),
        "primary_plus_redundancy_cases": int((pair_classes.collision_evidence_class == "PRIMARY_PLUS_ANNOTATION_REDUNDANCY").sum()),
        "proven_additive_cases": int((pair_classes.collision_evidence_class == "PROVEN_ADDITIVE_NONOVERLAPPING_COMPONENTS").sum()),
        "unresolved_collision_cases": int((~pair_classes.collision_evidence_class.isin({"EXACT_TECHNICAL_DUPLICATE", "PRIMARY_PLUS_ANNOTATION_REDUNDANCY", "PROVEN_ADDITIVE_NONOVERLAPPING_COMPONENTS"})).sum()),
        "recommended_support_state": {"assay_measured": True, "scalar_materializable": False, "state": "MEASURED_COLLISION_UNRESOLVED"},
        "aggregation_rule_selected": False,
        "corrected_global_basis_constructed": False,
        "real_train_global_state_rerun_started": False,
        "human_review_required": True,
    }
    atomic_json(outputs["collision_report"], report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
