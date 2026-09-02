#!/usr/bin/env python3
"""Metadata-only audit of lawful inventory available beyond the bounded T1 cache."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import h5py
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports" / "prod41k_teacher_t1_20260823"
V5A = ROOT / "exports" / "contextual_biology_v6r5a_20260822"
sys.path.insert(0, str(ROOT / "scripts" / "v4"))
import stage81a3_real_rna_forward_smoke as prior_smoke  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    config_path = ROOT / "configs" / "v4" / "stage81a3_foundation_heterogeneity_reality_audit.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assets_path = ROOT / config["inputs"]["assets"]
    split_path = V5A / "reader_donor_split.csv"
    current_path = OUT / "t1_encoder_fit_inventory.csv"
    disposition_path = ROOT / config["inputs"]["nph_disposition"]
    authority_inventory_path = ROOT / "results" / "v4" / "stage81a3_foundation_matrix_inventory.csv"

    split = pd.read_csv(split_path)
    fit_donors = set(split.loc[split["reader_partition"].eq("reader_fit"), "donor_id"].astype(str))
    if len(fit_donors) != 104:
        raise RuntimeError("T1 fit donor count changed")
    current = pd.read_csv(current_path)
    current_counts = current.groupby("matrix_id").size().to_dict()
    assets = pd.read_csv(assets_path)
    eligible_assets = assets[
        assets["foundation_eligible"].astype(str).str.lower().eq("true")
        & assets["study_id"].isin(["HVS", "SEA_AD"])
    ].sort_values("dataset_id")

    rows: list[dict[str, object]] = []
    donor_sets: dict[str, set[str]] = {"HVS": set(), "SEA_AD": set(), "NPH52": set()}
    for asset in eligible_assets.itertuples(index=False):
        study = str(asset.study_id)
        matrix_id = str(asset.dataset_id)
        matrix_path = ROOT / str(asset.matrix_path_or_object)
        donor_field = config["allowed_metadata"][study]["donor"]
        with h5py.File(matrix_path, "r") as handle:
            donors = pd.Series(prior_smoke.read_h5_vector(handle["obs"], donor_field), dtype="string")
        selected = donors.isin(fit_donors)
        selected_donors = set(donors[selected].astype(str))
        donor_sets[study].update(selected_donors)
        available = int(selected.sum())
        cached = int(current_counts.get(matrix_id, 0))
        if cached > available:
            raise RuntimeError(f"cached count exceeds lawful fit inventory: {matrix_id}")
        rows.append({
            "study_id": study,
            "matrix_id": matrix_id,
            "lawful_fit_donors": len(selected_donors),
            "lawful_fit_cells_metadata_only": available,
            "current_t1_cached_fit_cells": cached,
            "additional_fit_cells_available": available - cached,
            "expression_values_read": False,
            "pathology_values_read": False,
        })

    disposition = pd.read_csv(
        disposition_path,
        usecols=["source_object", "donor_id", "foundation_eligibility"],
    )
    eligible = (
        disposition["foundation_eligibility"].astype(str).str.lower().eq("true")
        & disposition["donor_id"].astype(str).isin(fit_donors)
    )
    nph = disposition.loc[eligible].copy()
    donor_sets["NPH52"].update(nph["donor_id"].astype(str))
    for source_object, group in nph.groupby("source_object", sort=True):
        matrix_id = f"NPH52::matrix::{source_object}"
        available = len(group)
        cached = int(current_counts.get(matrix_id, 0))
        if cached > available:
            raise RuntimeError(f"cached count exceeds lawful NPH fit inventory: {matrix_id}")
        rows.append({
            "study_id": "NPH52",
            "matrix_id": matrix_id,
            "lawful_fit_donors": group["donor_id"].astype(str).nunique(),
            "lawful_fit_cells_metadata_only": available,
            "current_t1_cached_fit_cells": cached,
            "additional_fit_cells_available": available - cached,
            "expression_values_read": False,
            "pathology_values_read": False,
        })

    frame = pd.DataFrame(rows).sort_values(["study_id", "matrix_id"]).reset_index(drop=True)
    if int(frame["current_t1_cached_fit_cells"].sum()) != 3_292:
        raise RuntimeError("current T1 fit inventory was not reconstructed")
    if set().union(*donor_sets.values()) != fit_donors:
        missing = sorted(fit_donors - set().union(*donor_sets.values()))
        raise RuntimeError(f"fit donors missing from lawful full metadata: {missing}")
    frame.to_csv(OUT / "T1_INVENTORY_EXPANSION_FEASIBILITY.csv", index=False, lineterminator="\n")

    study = frame.groupby("study_id", as_index=False).agg(
        matrices=("matrix_id", "count"),
        lawful_fit_cells_metadata_only=("lawful_fit_cells_metadata_only", "sum"),
        current_t1_cached_fit_cells=("current_t1_cached_fit_cells", "sum"),
        additional_fit_cells_available=("additional_fit_cells_available", "sum"),
    )
    study["fit_donors"] = study["study_id"].map({key: len(value) for key, value in donor_sets.items()})
    study.to_csv(OUT / "T1_INVENTORY_EXPANSION_BY_STUDY.csv", index=False, lineterminator="\n")

    total = int(frame["lawful_fit_cells_metadata_only"].sum())
    current_total = int(frame["current_t1_cached_fit_cells"].sum())
    report = {
        "schema": "prod41k-t1-inventory-expansion-feasibility-v1",
        "status": "EXPANSION_FEASIBLE_REQUIRES_PROSPECTIVE_MATERIALIZATION_FREEZE",
        "fit_donors": len(fit_donors),
        "lawful_full_fit_cells_metadata_only": total,
        "current_t1_cached_fit_cells": current_total,
        "additional_fit_cells_available": total - current_total,
        "current_cache_fraction_of_lawful_fit_inventory": current_total / total,
        "full_fit_inventory_cap8_presentations": 8 * total,
        "full_fit_inventory_cap8_complete_updates_at_batch128": (8 * total) // 128,
        "expression_values_read": False,
        "development_expression_accessed": False,
        "sealed_expression_accessed": False,
        "pathology_values_read": False,
        "authority": {
            "prior_full_train_matrix_inventory": str(authority_inventory_path.relative_to(ROOT)),
            "prior_full_train_matrix_inventory_sha256": sha256(authority_inventory_path),
            "asset_registry_sha256": sha256(assets_path),
            "foundation_split_sha256": sha256(ROOT / config["inputs"]["split_registry"]),
            "t1_fit_split_sha256": sha256(split_path),
            "nph_disposition_sha256": sha256(disposition_path),
            "current_t1_inventory_sha256": sha256(current_path),
        },
        "decision": "Do not replay the old cache. Freeze a deterministic metadata-only selection/materialization plan from these fit-donor cells before reading expression rows or scheduling training.",
    }
    (OUT / "T1_INVENTORY_EXPANSION_FEASIBILITY.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
