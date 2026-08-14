"""Close scalar observability after the frozen A2R collision audit."""

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


STATUS = "SCALAR_OBSERVABILITY_CLOSURE_HUMAN_REVIEW"
FROZEN_HASH = "5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff"
STATES = ("STRUCTURALLY_UNMEASURED", "MEASURED_SCALAR", "MEASURED_COLLISION_UNRESOLVED")


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


def family_of(matrix_id: str) -> str:
    if matrix_id.startswith("HVS::"):
        return "HVS"
    if matrix_id.startswith("NPH52::"):
        return "NPH52"
    if matrix_id.startswith("sea_ad_"):
        return "SEA_AD"
    raise RuntimeError(f"unknown foundation operator: {matrix_id}")


def train_donors(split: pd.DataFrame) -> dict[str, set[str]]:
    selected = split[(split.split_domain == "foundation") & (split.split == "train")]
    result = {
        str(study): {str(value).split("::", 1)[-1] for value in group.canonical_person_id}
        for study, group in selected.groupby("study_id")
    }
    expected = {"HVS": 62, "NPH52": 19, "SEA_AD": 68}
    if {key: len(result[key]) for key in expected} != expected:
        raise RuntimeError("frozen TRAIN donor contract changed")
    return result


def train_cell_counts(source: Path, config: dict[str, Any], matrix_ids: list[str]) -> dict[str, int]:
    split = pd.read_csv(source / config["inputs"]["split_registry"])
    allowed = train_donors(split)
    assets = pd.read_csv(source / config["inputs"]["assets"])
    result: dict[str, int] = {}
    for asset in assets[assets.dataset_id.astype(str).isin(matrix_ids)].itertuples(index=False):
        study = str(asset.study_id)
        donor_key = "donor_id" if study == "HVS" else "Donor ID"
        with h5py.File(source / str(asset.matrix_path_or_object), "r") as handle:
            donors = h5_vector(handle["obs"], donor_key)
        result[str(asset.dataset_id)] = int(np.isin(donors, sorted(allowed[study])).sum())
    manifest = pd.read_csv(
        source / "data/processed/v4/stage81a2r/nph52_physical_split/nph52_physical_split_exactness_manifest.csv"
    )
    for row in manifest[manifest.partition.eq("TRAIN")].itertuples(index=False):
        matrix_id = "NPH52::matrix::" + str(row.source_object_id)
        result[matrix_id] = int(row.cell_count)
    missing = sorted(set(matrix_ids) - set(result))
    if missing:
        raise RuntimeError(f"TRAIN cell counts missing for operators: {missing}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--source-project", type=Path, required=True)
    args = parser.parse_args()
    project, source = args.project_dir.resolve(), args.source_project.resolve()
    config = yaml.safe_load((project / "configs/v4/stage81a3r_real_train_global_state.yaml").read_text(encoding="utf-8"))
    outputs = {key: project / value for key, value in config["outputs"].items()}

    registry = pd.read_csv(source / config["inputs"]["address_registry"], dtype=str, keep_default_na=False)
    support = pd.read_csv(source / config["inputs"]["measurement_support"], dtype=str, keep_default_na=False)
    collision = pd.read_csv(outputs["collision_ledger"], dtype=str, keep_default_na=False, low_memory=False)
    impact = pd.read_csv(outputs["collision_impact"])
    weights = pd.read_csv(outputs["address_weights"])
    historical = set(pd.read_csv(source / config["inputs"]["nph_cache_vocabulary"]).canonical_ensembl_gene_id.astype(str))

    if len(registry) != 41_238 or registry.registry_semantic_hash.nunique() != 1 or registry.registry_semantic_hash.iloc[0] != FROZEN_HASH:
        raise RuntimeError("frozen 41,238-address registry changed")
    if support.matrix_id.nunique() != 42 or len(collision[["matrix_id", "molecular_address_id"]].drop_duplicates()) != 11_435:
        raise RuntimeError("frozen support/collision accounting changed")

    support["measured_address"] = support.measured_address.str.lower().eq("true")
    collision_keys = set(zip(collision.matrix_id, collision.molecular_address_id, strict=True))
    support["operator_family"] = support.matrix_id.map(family_of)
    support["observation_state"] = [
        "STRUCTURALLY_UNMEASURED" if not measured else
        "MEASURED_COLLISION_UNRESOLVED" if (matrix_id, address) in collision_keys else
        "MEASURED_SCALAR"
        for matrix_id, address, measured in zip(
            support.matrix_id, support.molecular_address_id, support.measured_address, strict=True
        )
    ]
    support["assay_measured"] = support.observation_state.ne("STRUCTURALLY_UNMEASURED")
    support["scalar_materializable"] = support.observation_state.eq("MEASURED_SCALAR")
    if set(support.observation_state) != set(STATES):
        raise RuntimeError("three-state observation contract not represented")

    support["collision_unresolved"] = support.observation_state.eq("MEASURED_COLLISION_UNRESOLVED")
    scalar_by_family = (
        support.pivot_table(
            index="molecular_address_id", columns="operator_family", values="scalar_materializable",
            aggfunc="sum", fill_value=0,
        )
        .rename(columns={
            "HVS": "collision_free_hvs_operators", "SEA_AD": "collision_free_sea_ad_operators",
            "NPH52": "collision_free_nph52_operators",
        })
        .reset_index()
    )
    address_counts = support.groupby("molecular_address_id", as_index=False).agg(
        measured_train_operators=("assay_measured", "sum"),
        collision_free_train_operators=("scalar_materializable", "sum"),
        collision_unresolved_train_operators=("collision_unresolved", "sum"),
    )
    measured_families = (
        support[support.assay_measured].groupby("molecular_address_id").operator_family.nunique()
        .rename("operator_families_measuring")
    )
    scalar_families = (
        support[support.scalar_materializable].groupby("molecular_address_id").operator_family.nunique()
        .rename("operator_families_scalar")
    )
    family_state = support.groupby(["molecular_address_id", "operator_family"], as_index=False).agg(
        family_measured=("assay_measured", "any"), family_scalar=("scalar_materializable", "any")
    )
    all_measuring_families_scalar = (
        family_state[family_state.family_measured].groupby("molecular_address_id").family_scalar.all()
        .rename("scalar_observable_in_all_measuring_families")
    )
    address = (
        registry[["molecular_address_index", "molecular_address_id", "identity_class"]]
        .merge(address_counts, on="molecular_address_id", how="left", validate="one_to_one")
        .merge(scalar_by_family, on="molecular_address_id", how="left", validate="one_to_one")
        .merge(measured_families, on="molecular_address_id", how="left", validate="one_to_one")
        .merge(scalar_families, on="molecular_address_id", how="left", validate="one_to_one")
        .merge(all_measuring_families_scalar, on="molecular_address_id", how="left", validate="one_to_one")
    )
    numeric = [
        "measured_train_operators", "collision_free_train_operators", "collision_unresolved_train_operators",
        "collision_free_hvs_operators", "collision_free_sea_ad_operators", "collision_free_nph52_operators",
        "operator_families_measuring", "operator_families_scalar",
    ]
    address[numeric] = address[numeric].fillna(0).astype(int)
    address["scalar_observable_in_all_measuring_families"] = address.scalar_observable_in_all_measuring_families.fillna(False).astype(bool)
    address["affected_by_collision"] = address.collision_unresolved_train_operators.gt(0)
    address["collision_unresolved_in_every_measuring_operator"] = address.measured_train_operators.gt(0) & address.collision_free_train_operators.eq(0)
    address["zero_scalar_materializable_train_observations"] = address.collision_free_train_operators.eq(0)
    address["historical_4096_address"] = address.molecular_address_id.isin(historical)
    address.insert(0, "status", STATUS)
    address = address.sort_values("molecular_address_index").reset_index(drop=True)

    operator = support.groupby(["operator_family", "matrix_id"], as_index=False).agg(
        frozen_assay_measured_addresses=("assay_measured", "sum"),
        scalar_materializable_addresses=("scalar_materializable", "sum"),
        collision_unresolved_addresses=("observation_state", lambda values: int((values == "MEASURED_COLLISION_UNRESOLVED").sum())),
        structurally_unmeasured_addresses=("observation_state", lambda values: int((values == "STRUCTURALLY_UNMEASURED").sum())),
    )
    operator["fraction_measured_support_scalar_materializable"] = (
        operator.scalar_materializable_addresses / operator.frozen_assay_measured_addresses
    )
    operator.insert(0, "status", STATUS)

    cells = train_cell_counts(source, config, operator.matrix_id.astype(str).tolist())
    operator["train_cells"] = operator.matrix_id.map(cells).astype(np.int64)
    train_rows: list[dict[str, Any]] = []
    for family, local in operator.groupby("operator_family", sort=True):
        total = int((local.train_cells * 41_238).sum())
        scalar_n = int((local.train_cells * local.scalar_materializable_addresses).sum())
        collision_n = int((local.train_cells * local.collision_unresolved_addresses).sum())
        unmeasured_n = int((local.train_cells * local.structurally_unmeasured_addresses).sum())
        mass_row = impact[impact.operator_family.eq(family)].iloc[0]
        train_rows.append({
            "status": STATUS, "operator_family": family,
            "train_cells_across_operators": int(local.train_cells.sum()),
            "cell_address_observations": total,
            "measured_scalar_cell_address_observations": scalar_n,
            "measured_collision_unresolved_cell_address_observations": collision_n,
            "structurally_unmeasured_cell_address_observations": unmeasured_n,
            "fraction_measured_scalar": scalar_n / total,
            "fraction_measured_collision_unresolved": collision_n / total,
            "fraction_structurally_unmeasured": unmeasured_n / total,
            "bounded_train_cells_for_count_mass": int(mass_row.bounded_train_cells_total),
            "bounded_collision_source_count_mass_fraction": float(mass_row.collision_source_count_mass_fraction),
            "count_mass_scope": "BOUNDED_TRAIN_DIAGNOSTIC_ONLY_DOES_NOT_SELECT_AGGREGATION",
        })
    train_impact = pd.DataFrame(train_rows)
    if not np.allclose(
        train_impact[["fraction_measured_scalar", "fraction_measured_collision_unresolved", "fraction_structurally_unmeasured"]].sum(axis=1),
        1.0,
    ):
        raise RuntimeError("cell/address state fractions do not close")

    weights = weights.merge(address[[
        "molecular_address_id", "zero_scalar_materializable_train_observations", "historical_4096_address",
        "collision_free_nph52_operators",
    ]], on="molecular_address_id", validate="one_to_one")
    consequence = []
    for identity_class, local in weights.groupby("identity_class", sort=True):
        consequence.append({
            "status": STATUS, "identity_class": identity_class, "addresses": len(local),
            "scalar_eligible_addresses": int((~local.zero_scalar_materializable_train_observations).sum()),
            "pilot_positive_weight_addresses": int((local.paired_view_reproducibility_weight > 0).sum()),
            "pilot_positive_weight_now_unavailable_due_collision": int(((local.paired_view_reproducibility_weight > 0) & local.zero_scalar_materializable_train_observations).sum()),
            "successor_non4096_scalar_materializable_addresses": int((~local.historical_4096_address & ~local.zero_scalar_materializable_train_observations).sum()),
            "successor_non4096_nph52_scalar_materializable_addresses": int((~local.historical_4096_address & local.collision_free_nph52_operators.gt(0)).sum()),
        })
    weight_consequence = pd.DataFrame(consequence)

    affected = address[address.affected_by_collision]
    identity_breakdown = {}
    for identity in ("current_exact", "legacy_exact", "source_native_anchored"):
        local = affected[affected.identity_class.eq(identity)]
        identity_breakdown[identity] = {
            "affected_addresses": int(len(local)),
            "with_collision_free_train_operator": int((local.collision_free_train_operators > 0).sum()),
            "with_collision_free_hvs_operator": int((local.collision_free_hvs_operators > 0).sum()),
            "with_collision_free_sea_ad_operator": int((local.collision_free_sea_ad_operators > 0).sum()),
            "with_collision_free_nph52_operator": int((local.collision_free_nph52_operators > 0).sum()),
            "collision_unresolved_in_every_measuring_operator": int(local.collision_unresolved_in_every_measuring_operator.sum()),
            "zero_scalar_materializable_train_observations": int(local.zero_scalar_materializable_train_observations.sum()),
        }
    zero_scalar = int(address.zero_scalar_materializable_train_observations.sum())
    report = {
        "status": STATUS,
        "frozen_molecular_addresses": 41_238,
        "frozen_semantic_hash": FROZEN_HASH,
        "observation_contract": {
            "states": list(STATES),
            "MEASURED_COLLISION_UNRESOLVED": {"assay_measured": True, "scalar_materializable": False},
            "scalar_matrix_input": "MEASURED_SCALAR_ONLY",
        },
        "affected_addresses": int(len(affected)),
        "affected_identity_breakdown": identity_breakdown,
        "global_support": {
            "scalar_observable_in_at_least_one_train_operator": int((address.collision_free_train_operators > 0).sum()),
            "scalar_observable_in_at_least_two_operator_families": int((address.operator_families_scalar >= 2).sum()),
            "scalar_observable_in_all_families_that_measure_it": int(address.scalar_observable_in_all_measuring_families.sum()),
            "scalar_unobservable_everywhere_due_only_to_unresolved_collisions": zero_scalar,
        },
        "reproducibility_weight_consequence": weight_consequence.set_index("identity_class").to_dict(orient="index"),
        "classification": "DATA / PROVENANCE LIMITATION - SCALAR MATERIALIZATION UNRESOLVED",
        "aggregation_rule_selected": False,
        "global_basis_fit_started": False,
        "corrected_real_train_rerun_started": False,
        "decision": "STOP_FOR_HUMAN_REVIEW_BEFORE_BASIS" if zero_scalar else "SUFFICIENT_SUPPORT_FOR_LATER_CORRECTED_RERUN",
    }
    atomic_csv(outputs["scalar_observability_address"], address, compress=True)
    atomic_csv(outputs["scalar_observability_operator"], operator.sort_values(["operator_family", "matrix_id"]))
    atomic_csv(outputs["scalar_observability_train_impact"], train_impact)
    atomic_csv(outputs["scalar_observability_weight_consequence"], weight_consequence)
    atomic_json(outputs["scalar_observability_report"], report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
