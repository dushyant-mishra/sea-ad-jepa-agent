#!/usr/bin/env python3
"""Freeze a deterministic nested Phase-2 metadata selection without opening expression."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import heapq
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
META = ROOT / "outputs/full104_v014_20260826/01_full104_metadata_adapter"
V8_ENV = ROOT / "outputs/full104_v014_20260826/full104_expression_interface_v8_verified"
V8 = V8_ENV / "FULL104_EXPRESSION_INTERFACE_V8"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--level", type=int, default=0)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    freeze_dir = Path(args.freeze).resolve()
    out = Path(args.out).resolve()
    if out.exists():
        raise RuntimeError("metadata-selection output already exists")
    out.mkdir(parents=True)

    freeze_manifest = freeze_dir / "PHASE2_PREEXPRESSION_MANIFEST.csv"
    freeze_anchor = freeze_dir.parent / "PHASE2_PREEXPRESSION_MANIFEST_SHA256.txt"
    if sha(freeze_manifest) != freeze_anchor.read_text(encoding="ascii").strip():
        raise RuntimeError("preexpression freeze anchor mismatch")
    for row in pd.read_csv(freeze_manifest).itertuples(index=False):
        path = freeze_dir / str(row.path)
        if not path.is_file() or path.stat().st_size != int(row.bytes) or sha(path) != str(row.sha256):
            raise RuntimeError("preexpression freeze artifact mismatch")
    freeze = json.loads((freeze_dir / "PHASE2_DERIVATION_FREEZE.json").read_text(encoding="utf-8"))
    if freeze.get("status") != "FROZEN_BEFORE_PHASE2_EXPRESSION" or not freeze.get("no_expression_opened"):
        raise RuntimeError("preexpression freeze unavailable")
    ladder = pd.read_csv(freeze_dir / "PHASE2_SAMPLE_LADDER.csv", dtype=str)
    level = ladder[ladder.level.astype(int).eq(args.level)]
    if len(level) != 1:
        raise RuntimeError("requested selection level is unavailable")
    full_level = level.iloc[0].per_donor_cap == "FULL"
    cap = "FULL" if full_level else int(level.iloc[0].per_donor_cap)
    expected_total = int(level.iloc[0].selected_cells)
    donors = pd.read_csv(freeze_dir / "PHASE2_DONOR_INVENTORY.csv", dtype={"donor_id": str})
    capacity = dict(zip(donors.donor_id, donors.cell_count.astype(int)))
    expected_by_donor = capacity.copy() if full_level else {donor: min(count, cap) for donor, count in capacity.items()}
    rng = json.loads((freeze_dir / "PHASE2_RNG_KEYS.json").read_text(encoding="utf-8"))["keys"]
    order_key = rng["cell_order"]

    meta_manifest_path = META / "FULL104_ADAPTER_SHA256_MANIFEST.csv"
    if sha(meta_manifest_path) != "54e4ba5b60e9c5d3ff23a307df03576f45ac725f3b71642888500a469ebdbc74":
        raise RuntimeError("metadata manifest external hash mismatch")
    meta_manifest = pd.read_csv(meta_manifest_path, dtype=str).set_index("path")
    index_path = META / "FULL104_ROW_LINEAGE.csv"
    index_row = meta_manifest.loc["FULL104_ROW_LINEAGE.csv"]
    if index_path.stat().st_size != int(index_row.bytes) or sha(index_path) != index_row.sha256:
        raise RuntimeError("lineage index authentication failed")
    index = pd.read_csv(index_path).sort_values("operator_index")
    if len(index) != 42 or index.row_count.sum() != 4_553_407:
        raise RuntimeError("lineage geometry mismatch")

    nph_manifest = pd.read_csv(V8 / "NPH_READER_FIT_DERIVATIVE_MANIFEST.csv", dtype=str)
    nph_assets = {
        row.matrix_id: (
            (V8 / row.derivative_relative_path).relative_to(ROOT).as_posix(),
            row.derivative_sha256,
        )
        for row in nph_manifest.itertuples(index=False)
    }
    nph_expected = pd.read_csv(gzip.open(V8 / "NPH_READER_FIT_EXPECTED_LINEAGE.csv.gz", "rt"), dtype=str)
    nph_expected["expression_row"] = nph_expected.groupby("operator_index", sort=False).cumcount()
    nph_columns = dict(zip(nph_expected.canonical_cell_id, nph_expected.expression_row.astype(int)))
    asset_pins = pd.read_csv(V8 / "interface_check_v8r1/FULL104_EXPRESSION_ASSET_PINS.csv", dtype=str)
    h5_assets = {row.matrix_id: (row.expression_path, row.registered_sha256) for row in asset_pins.itertuples(index=False) if row.source != "NPH52"}

    heaps: dict[str, list] = defaultdict(list)
    seen = 0
    columns = ["source", "operator_index", "matrix_id", "donor_id", "canonical_cell_id", "source_path", "source_row", "row_locator", "locator_kind", "eligibility_status", "reader_partition", "foundation_split", "operator_state_sha256"]
    for shard in index.itertuples(index=False):
        relative = str(shard.path).replace("\\", "/")
        manifest_row = meta_manifest.loc[relative]
        path = META / relative
        if path.stat().st_size != int(manifest_row.bytes) or sha(path) != manifest_row.sha256 or sha(path) != str(shard.sha256):
            raise RuntimeError(f"lineage shard authentication failed: {relative}")
        frame = pd.read_csv(path, usecols=columns, dtype={"donor_id": str, "canonical_cell_id": str, "row_locator": str})
        if len(frame) != int(shard.row_count) or set(frame.eligibility_status) != {"LAWFUL_READER_FIT"} or set(frame.reader_partition) != {"reader_fit"} or set(frame.foundation_split) != {"foundation/train"}:
            raise RuntimeError(f"lineage shard firewall mismatch: {relative}")
        for row in frame.itertuples(index=False, name=None):
            source, operator, matrix_id, donor, cell, source_path, source_row, locator, locator_kind, eligibility, partition, split, state_hash = row
            if donor not in expected_by_donor:
                raise RuntimeError("non-fit donor reached selection")
            digest_bytes = hashlib.sha256(f"{order_key}|{source}|{donor}|{operator}|{cell}|{locator}".encode("utf-8")).digest()
            digest_int = int.from_bytes(digest_bytes, "big")
            compact = (source, int(operator), matrix_id, donor, cell, source_path, int(source_row), locator, locator_kind, state_hash, digest_bytes.hex())
            item = (-digest_int, compact)
            heap = heaps[donor]
            target = expected_by_donor[donor]
            if len(heap) < target:
                heapq.heappush(heap, item)
            elif digest_int < -heap[0][0]:
                heapq.heapreplace(heap, item)
        seen += len(frame)
        print(f"metadata shard op{int(shard.operator_index):02d}: rows={len(frame)} cumulative={seen}", flush=True)
    if seen != 4_553_407 or set(heaps) != set(expected_by_donor):
        raise RuntimeError("full lineage was not traversed")

    output = []
    for donor in sorted(heaps):
        selected = sorted((item[1] for item in heaps[donor]), key=lambda x: (x[-1], x[4], x[7]))
        if len(selected) != expected_by_donor[donor]:
            raise RuntimeError("donor quota mismatch")
        for rank, row in enumerate(selected):
            source, operator, matrix_id, donor_id, cell, source_path, source_row, locator, locator_kind, state_hash, digest = row
            if source == "NPH52":
                expression_path, asset_hash = nph_assets[matrix_id]
                expression_row = nph_columns.get(cell)
                if expression_row is None:
                    raise RuntimeError("selected NPH cell absent from fit-only derivative lineage")
                expression_kind = "verified_fit_only_qs_column"
            else:
                expression_path, asset_hash = h5_assets[matrix_id]
                expression_row = source_row
                expression_kind = "authenticated_h5ad_obs_row"
            output.append({
                "selection_row": len(output), "sample_level": args.level, "donor_rank": rank,
                "source": source, "operator_index": operator, "matrix_id": matrix_id, "donor_id": donor_id,
                "canonical_cell_id": cell, "audit_source_path": source_path, "audit_source_row": source_row,
                "row_locator": locator, "locator_kind": locator_kind, "operator_state_sha256": state_hash,
                "selection_sha256": digest, "expression_asset_path": expression_path,
                "expression_asset_sha256": asset_hash, "expression_row": int(expression_row),
                "expression_asset_kind": expression_kind,
                "primary_row_weight": 1.0 / (104 * expected_by_donor[donor_id]),
                "authority_tag": "DERIVE_ON_104_FIT",
            })
    selected = pd.DataFrame(output)
    if len(selected) != expected_total or selected.canonical_cell_id.nunique() != len(selected) or selected.donor_id.nunique() != 104 or selected.operator_index.nunique() != 42:
        raise RuntimeError("selection global geometry mismatch")
    if abs(selected.primary_row_weight.sum() - 1.0) > 1e-12:
        raise RuntimeError("equal-donor primary weights do not sum to one")
    counts = selected.groupby("donor_id").size()
    if any(counts[donor] != count for donor, count in expected_by_donor.items()):
        raise RuntimeError("selection donor quota mismatch")

    selection_path = out / f"PHASE2_METADATA_SELECTION_LEVEL{args.level}.csv.gz"
    selected.to_csv(selection_path, index=False, compression={"method": "gzip", "compresslevel": 6, "mtime": 0}, lineterminator="\n")
    coverage = selected.groupby(["source", "operator_index"], as_index=False).agg(cells=("selection_row", "size"), donors=("donor_id", "nunique"), total_weight=("primary_row_weight", "sum"))
    coverage_path = out / f"PHASE2_METADATA_SELECTION_LEVEL{args.level}_COVERAGE.csv"
    coverage.to_csv(coverage_path, index=False, lineterminator="\n")
    audit = {
        "schema": "full104-phase2-metadata-selection-v1", "status": "PASS_PHASE2_METADATA_SELECTION_FROZEN",
        "level": args.level, "per_donor_cap": cap, "cells": len(selected), "donors": selected.donor_id.nunique(),
        "operators": selected.operator_index.nunique(), "sources": selected.source.nunique(),
        "source_cells": selected.groupby("source").size().astype(int).to_dict(),
        "source_primary_weight": selected.groupby("source").primary_row_weight.sum().to_dict(),
        "primary_weight_sum": float(selected.primary_row_weight.sum()),
        "selection_rule": freeze["sampling"]["selection_order"],
        "selection_sha256": sha(selection_path), "coverage_sha256": sha(coverage_path),
        "lineage_rows_traversed": seen, "expression_opened": False, "protected_expression_opened": False,
        "original_mixed_nph_assets_selected": False,
    }
    audit_path = out / "PHASE2_METADATA_SELECTION_AUDIT.json"
    write_json(audit_path, audit)
    code_copy = out / "build_full104_phase2_metadata_selection.py"
    code_copy.write_bytes(Path(__file__).read_bytes())
    manifest_path = out / "PHASE2_METADATA_SELECTION_MANIFEST.csv"
    files = [selection_path, coverage_path, audit_path, code_copy]
    pd.DataFrame([{"path": p.name, "bytes": p.stat().st_size, "sha256": sha(p)} for p in files]).to_csv(manifest_path, index=False, lineterminator="\n")
    anchor = out.parent / f"PHASE2_METADATA_SELECTION_LEVEL{args.level}_MANIFEST_SHA256.txt"
    anchor.write_text(sha(manifest_path) + "\n", encoding="ascii")
    print(json.dumps({**audit, "manifest_sha256": sha(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
