#!/usr/bin/env python3
"""Bounded direct-read proof for the current 41,238-address FOUNDATION loader."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports" / "foundation_corpus_discovery_v1"
V5A = ROOT / "exports" / "contextual_biology_v6r5a_20260822"
sys.path.insert(0, str(ROOT / "exports" / "static_context_decomposition_v4_20260821"))
from production_train_loader import (  # noqa: E402
    MEASURED_COLLISION_UNRESOLVED,
    MEASURED_SCALAR,
    STRUCTURALLY_UNMEASURED,
    PINNED_MANIFEST_SHA256,
    ProductionTrainLoader,
)


SEED = 20_260_824_01
CELLS_PER_OPERATOR = 8
RANDOM_ADDRESSES_PER_CELL = 20


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def score(*parts: object) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()


def source_family(matrix_id: str) -> str:
    if matrix_id.startswith("HVS::"):
        return "HVS"
    if matrix_id.startswith("NPH52::"):
        return "NPH52"
    return "SEA_AD"


def payload_hash(states: np.ndarray, values: np.ndarray) -> str:
    nonzero = np.flatnonzero(values).astype("<i4")
    digest = hashlib.sha256()
    digest.update(np.asarray(states, dtype=np.uint8).tobytes())
    digest.update(nonzero.tobytes())
    digest.update(np.asarray(values[nonzero], dtype="<f4").tobytes())
    return digest.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    loader = ProductionTrainLoader()
    split_path = V5A / "reader_donor_split.csv"
    split = pd.read_csv(split_path)
    fit_donors = set(split.loc[split["reader_partition"].eq("reader_fit"), "donor_id"].astype(str))
    if len(fit_donors) != 104:
        raise RuntimeError("104-donor T1 firewall changed")
    cells = loader.cell_table().reset_index().rename(columns={"index": "accepted_inventory_row"})
    if len(cells) != 4_726 or cells["operator_index"].nunique() != 42:
        raise RuntimeError("current production-loader inventory changed")
    eligible = cells[cells["donor_id"].astype(str).isin(fit_donors)].copy()
    if eligible["donor_id"].astype(str).nunique() != 104:
        raise RuntimeError("current loader does not reconstruct all fit donors")

    selected_parts = []
    operator_status = []
    for operator_index, operator_cells in eligible.groupby("operator_index", sort=True):
        matrix_id = str(operator_cells["matrix_id"].iloc[0])
        ranked = operator_cells.assign(
            selection_score=[score(SEED, matrix_id, donor, cell) for donor, cell in zip(
                operator_cells["donor_id"].astype(str), operator_cells["cell_id"].astype(str), strict=True
            )]
        ).sort_values(["selection_score", "donor_id", "cell_id"])
        take = ranked.head(CELLS_PER_OPERATOR).drop(columns="selection_score").copy()
        selected_parts.append(take)
        operator_status.append({
            "operator_index": int(operator_index), "matrix_id": matrix_id,
            "eligible_fit_cells": len(operator_cells), "selected_cells": len(take),
            "status": "SELECTED" if len(take) == CELLS_PER_OPERATOR else "SELECTED_ALL_FEWER_THAN_8",
        })
    selected = pd.concat(selected_parts, ignore_index=True)
    selected["loader_row"] = np.arange(len(selected), dtype=np.int64)

    summary_rows: list[dict[str, object]] = []
    top_rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    registry = loader.registry.set_index("molecular_address_index", drop=False)
    for operator_index, group in selected.groupby("operator_index", sort=True):
        matrix_id = str(group["matrix_id"].iloc[0])
        request = group.copy().reset_index(drop=True)
        request["loader_row"] = np.arange(len(request), dtype=np.int64)
        try:
            values, states = loader.load(request)
        except Exception as error:
            failures.append({"operator_index": int(operator_index), "matrix_id": matrix_id, "error": repr(error)})
            continue
        for local, cell in request.iterrows():
            x = values[local]
            state = states[local]
            measured = state == MEASURED_SCALAR
            structural = state == STRUCTURALLY_UNMEASURED
            collision = state == MEASURED_COLLISION_UNRESOLVED
            if np.any(x[~measured] != 0) or not np.isfinite(x).all():
                raise RuntimeError(f"observation/value semantic violation: {matrix_id} row {local}")
            measured_indices = np.flatnonzero(measured)
            measured_values = x[measured]
            nonzero_measured = measured_indices[measured_values != 0]
            random_ranked = sorted(measured_indices.tolist(), key=lambda address: score(
                SEED, matrix_id, cell["cell_id"], "random_address", address
            ))[:RANDOM_ADDRESSES_PER_CELL]
            random_payload = [{
                "address_index": int(address),
                "molecular_address_id": str(registry.loc[address, "molecular_address_id"]),
                "symbol": str(registry.loc[address, "symbol"]),
                "value": float(x[address]),
            } for address in random_ranked]
            summary_rows.append({
                "source": source_family(matrix_id),
                "operator_index": int(operator_index), "matrix_id": matrix_id,
                "accepted_inventory_row": int(cell["accepted_inventory_row"]),
                "donor_id": str(cell["donor_id"]), "cell_id": str(cell["cell_id"]),
                "native_class": "UNAVAILABLE_IN_CURRENT_LOADER_AUTHORITY",
                "broad_cell_class": str(cell["broad_cell_class"]),
                "measured_scalar_count": int(measured.sum()),
                "structurally_unmeasured_count": int(structural.sum()),
                "collision_unresolved_count": int(collision.sum()),
                "nonzero_measured_scalar_count": int(len(nonzero_measured)),
                "finite_value_count": int(np.isfinite(x).sum()),
                "measured_zero_count": int(np.count_nonzero(measured_values == 0)),
                "measured_value_min": float(measured_values.min()),
                "measured_value_q25": float(np.quantile(measured_values, 0.25)),
                "measured_value_median": float(np.median(measured_values)),
                "measured_value_mean": float(measured_values.mean()),
                "measured_value_q75": float(np.quantile(measured_values, 0.75)),
                "measured_value_max": float(measured_values.max()),
                "measured_value_std": float(measured_values.std()),
                "random_measured_address_sample_json": json.dumps(random_payload, separators=(",", ":")),
                "sparse_materialized_payload_sha256": payload_hash(state, x),
            })
            ranked_nonzero = nonzero_measured[np.argsort(-np.abs(x[nonzero_measured]), kind="stable")[:20]]
            for rank, address in enumerate(ranked_nonzero, start=1):
                row = registry.loc[int(address)]
                top_rows.append({
                    "source": source_family(matrix_id), "operator_index": int(operator_index),
                    "matrix_id": matrix_id, "donor_id": str(cell["donor_id"]),
                    "cell_id": str(cell["cell_id"]), "rank": rank,
                    "molecular_address_index": int(address),
                    "molecular_address_id": str(row["molecular_address_id"]),
                    "symbol": str(row["symbol"]), "identity_class": str(row["identity_class"]),
                    "source_native_anchor": str(row["source_native_anchor"]),
                    "contributing_source_families": str(row["contributing_source_families"]),
                    "contributing_source_dataset_ids": str(row["contributing_source_dataset_ids"]),
                    "value": float(x[address]), "absolute_value": float(abs(x[address])),
                })

    summary = pd.DataFrame(summary_rows)
    tops = pd.DataFrame(top_rows)
    summary_path = OUT / "FOUNDATION_ACTUAL_EXPRESSION_SPOTCHECK.csv"
    top_path = OUT / "FOUNDATION_ACTUAL_EXPRESSION_TOP_ADDRESSES.csv"
    summary.to_csv(summary_path, index=False, lineterminator="\n")
    tops.to_csv(top_path, index=False, lineterminator="\n")
    direct = len(summary) > 0
    report = {
        "schema": "foundation-actual-expression-spotcheck-v1",
        "current_authoritative_real_expression_directly_read": direct,
        "explicit_answer": "YES" if direct else "NO",
        "loader": "exports/static_context_decomposition_v4_20260821/production_train_loader.py",
        "loader_python_sha256": sha256(ROOT / "exports" / "static_context_decomposition_v4_20260821" / "production_train_loader.py"),
        "loader_manifest_sha256": sha256(ROOT / "exports" / "static_context_decomposition_v4_20260821" / "production_loader_manifest.json"),
        "loader_pinned_manifest_expected_sha256": PINNED_MANIFEST_SHA256,
        "fit_donor_count": len(fit_donors),
        "operators_in_authority": 42,
        "operators_successfully_read": int(summary["operator_index"].nunique()) if direct else 0,
        "cells_directly_read": len(summary),
        "operator_selection": operator_status,
        "operator_failures": failures,
        "firewalls": {"development_expression": False, "sealed_expression": False, "pathology": False},
        "outputs": {
            summary_path.name: {"bytes": summary_path.stat().st_size, "sha256": sha256(summary_path)},
            top_path.name: {"bytes": top_path.stat().st_size, "sha256": sha256(top_path)},
        },
    }
    json_path = OUT / "FOUNDATION_ACTUAL_EXPRESSION_SPOTCHECK.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md = f"""# Foundation actual-expression spot check

## Direct answer

**{'YES' if direct else 'NO'}: current authoritative real expression data were directly read.**

The hash-pinned current 41,238-address production loader directly materialized
{len(summary):,} cells across {report['operators_successfully_read']}/42 operators from the frozen 104 T1 fit donors.
No DEV expression, SEALED expression, pathology, or old 4K compatibility cache was read.

Each row records the three observation states separately, measured zeros separately,
nonzero measured values, finite/value summaries, a deterministic measured-address
sample, and a hash of the sparse value payload plus full observation-state vector.
The top-address table contains canonical molecular-address and source provenance.

Operator failures: {len(failures)}. See the JSON for exact per-operator status.
"""
    (OUT / "FOUNDATION_ACTUAL_EXPRESSION_SPOTCHECK.md").write_text(md, encoding="utf-8")
    print(json.dumps({"explicit_answer": report["explicit_answer"], "operators": report["operators_successfully_read"], "cells": len(summary), "failures": len(failures)}, indent=2))


if __name__ == "__main__":
    main()
