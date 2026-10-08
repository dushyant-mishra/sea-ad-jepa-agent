#!/usr/bin/env python3
"""Build deterministic four-view molecular sketches for FULL104 Phase-2."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
ADDRESS_N = 41_238


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json_atomic(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def write_csv_atomic(path: Path, frame: pd.DataFrame) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(tmp, index=False, lineterminator="\n")
    os.replace(tmp, path)


def digest_int(*parts: object) -> int:
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:8], "big")


def projection(seed_hex: str, width: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(int(seed_hex[:16], 16))
    return rng.integers(0, width, size=ADDRESS_N, dtype=np.int32), rng.choice(np.asarray([-1.0, 1.0], np.float32), size=ADDRESS_N)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--expression", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    started = time.time()
    freeze_dir = Path(args.freeze).resolve()
    expression_dir = Path(args.expression).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    feature_dir = out / "blocks"
    feature_dir.mkdir(exist_ok=True)

    freeze_manifest = freeze_dir / "PHASE2_PREEXPRESSION_MANIFEST.csv"
    if sha(freeze_manifest) != (freeze_dir.parent / "PHASE2_PREEXPRESSION_MANIFEST_SHA256.txt").read_text().strip():
        raise RuntimeError("freeze anchor mismatch")
    freeze = json.loads((freeze_dir / "PHASE2_DERIVATION_FREEZE.json").read_text())
    if freeze["status"] != "FROZEN_BEFORE_PHASE2_EXPRESSION":
        raise RuntimeError("freeze unavailable")
    expression_manifest = expression_dir / "PHASE2_EXPRESSION_MATERIALIZATION_MANIFEST.csv"
    expression_audit = json.loads((expression_dir / "PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json").read_text())
    level = int(expression_audit.get("sample_level", 0))
    anchor = expression_dir.parent / f"PHASE2_EXPRESSION_MATERIALIZATION_LEVEL{level}_MANIFEST_SHA256.txt"
    if level == 0 and not anchor.exists(): anchor = expression_dir.parent / "PHASE2_EXPRESSION_MATERIALIZATION_MANIFEST_SHA256.txt"
    if sha(expression_manifest) != anchor.read_text().strip():
        raise RuntimeError("expression materialization anchor mismatch")
    if expression_audit["status"] != "PASS_PHASE2_EXPRESSION_MATERIALIZED" or expression_audit["protected_expression_opened"]:
        raise RuntimeError("expression materialization gate unavailable")
    blocks = pd.read_csv(expression_dir / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv")
    if blocks.rows.sum() != int(expression_audit["cells"]) or blocks.operator_index.nunique() != 42:
        raise RuntimeError("expression block geometry mismatch")

    shared = freeze["shared"]
    views = int(shared["views"])
    feature_dim = int(shared["feature_sketch_dimension"])
    channel_dim = feature_dim // 2
    mask_blocks = int(shared["mask_blocks"])
    selected_blocks = int(shared["selected_blocks"])
    rng_keys = json.loads((freeze_dir / "PHASE2_RNG_KEYS.json").read_text())["keys"]
    maps = {}
    for label, seed_name in [("A", "feature_sketch_A"), ("B", "feature_sketch_B")]:
        base = rng_keys[seed_name]
        value_col, value_sign = projection(hashlib.sha256((base + "|value").encode()).hexdigest(), channel_dim)
        visibility_col, visibility_sign = projection(hashlib.sha256((base + "|visibility").encode()).hexdigest(), channel_dim)
        maps[label] = (value_col, value_sign, visibility_col, visibility_sign)
    projection_path = out / "PHASE2_SKETCH_PROJECTIONS.npz"
    if not projection_path.is_file():
        np.savez_compressed(projection_path, **{
            f"{label}_{name}": array
            for label, arrays in maps.items()
            for name, array in zip(["value_col", "value_sign", "visibility_col", "visibility_sign"], arrays)
        })

    states_file = ROOT / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
    state_data = np.load(states_file, allow_pickle=False)
    states = state_data["states"].astype(np.uint8)
    if states.shape != (42, ADDRESS_N):
        raise RuntimeError("operator-state geometry mismatch")
    op_cache = {}
    mask_seed = rng_keys["four_views"]
    for op in range(42):
        measured = np.flatnonzero(states[op] == 1).astype(np.int32)
        ordering = sorted(measured.tolist(), key=lambda address: (digest_int(mask_seed, "address-block", op, address), address))
        block_id = np.full(ADDRESS_N, -1, np.int16)
        block_addresses = [[] for _ in range(mask_blocks)]
        for rank, address in enumerate(ordering):
            block = rank % mask_blocks
            block_id[address] = block
            block_addresses[block].append(address)
        block_counts = np.asarray([len(values) for values in block_addresses], np.int32)
        target = int(np.floor(0.6 * len(measured)))
        visibility_sums = {}
        full_visibility = {}
        for label, (_, _, vcol, vsign) in maps.items():
            sums = np.zeros((mask_blocks, channel_dim), np.float32)
            for block, addresses in enumerate(block_addresses):
                np.add.at(sums[block], vcol[addresses], vsign[addresses])
            visibility_sums[label] = sums
            full = np.zeros(channel_dim, np.float32)
            np.add.at(full, vcol[measured], vsign[measured])
            full_visibility[label] = full
        op_cache[op] = (block_id, block_addresses, block_counts, target, visibility_sums, full_visibility)

    contract = {
        "schema": "full104-phase2-multiview-features-v1", "status": "IN_PROGRESS",
        "freeze_manifest_sha256": sha(freeze_manifest), "expression_manifest_sha256": sha(expression_manifest),
        "expression_block_manifest_sha256": sha(expression_dir / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"),
        "code_sha256": sha(Path(__file__)), "cells": int(blocks.rows.sum()), "sample_level": level, "blocks": len(blocks),
        "views": views, "feature_dim_per_view": feature_dim, "value_channels": channel_dim, "visibility_channels": channel_dim,
        "sketches": 2, "mask_blocks": mask_blocks, "selected_blocks": selected_blocks,
        "visible_count": "exact floor(0.60*MEASURED_SCALAR) through deterministic <=8-address block-boundary repair",
        "normalization": "log1p(raw_count*10000/full_source_library) exactly once",
        "labels_or_identity_as_features": False, "optimizer_ema_lambda_query_schedule_gpu_mechanics_or_training": False,
    }
    contract_path = out / "MULTIVIEW_FEATURE_CONTRACT.json"
    if contract_path.is_file():
        if json.loads(contract_path.read_text()) != contract:
            raise RuntimeError("feature resume contract mismatch")
    else:
        write_json_atomic(contract_path, contract)
    journal_path = out / "FEATURE_BLOCK_MANIFEST.partial.csv"
    journal = pd.read_csv(journal_path, dtype=str) if journal_path.is_file() else pd.DataFrame()

    for record in blocks.sort_values(["operator_index", "block_key"]).itertuples(index=False):
        key = str(record.block_key)
        old = journal[journal.block_key.eq(key)] if len(journal) else pd.DataFrame()
        output_path = feature_dir / (key.replace("/", "_") + ".features.npz")
        if len(old) == 1 and output_path.is_file() and sha(output_path) == old.iloc[0].feature_sha256:
            print(f"reuse features {key}", flush=True)
            continue
        counts_path = expression_dir / str(record.counts_path)
        meta_path = expression_dir / str(record.meta_path)
        if sha(counts_path) != str(record.counts_sha256) or sha(meta_path) != str(record.meta_sha256):
            raise RuntimeError(f"expression block hash mismatch: {key}")
        raw = sparse.load_npz(counts_path).tocsr().astype(np.float32)
        meta = pd.read_csv(meta_path, dtype={"donor_id": str, "canonical_cell_id": str})
        if raw.shape != (len(meta), ADDRESS_N):
            raise RuntimeError(f"expression/meta geometry mismatch: {key}")
        scale = (10_000 / np.maximum(meta.source_library.to_numpy(np.float64), 1)).astype(np.float32)
        values = raw.multiply(scale[:, None]).tocsr()
        values.data = np.log1p(values.data)
        values.sort_indices()
        coo = values.tocoo()
        op = int(record.operator_index)
        block_id, block_addresses, block_counts, target_visible, visibility_sums, full_visibility = op_cache[op]
        if len(coo.col) and np.any(block_id[coo.col] < 0):
            raise RuntimeError(f"numeric value outside MEASURED_SCALAR: {key}")
        result = {"selection_row": meta.selection_row.to_numpy(np.int64)}
        selected_by_view = []
        repairs_by_view = []
        for view in range(views):
            chosen = np.zeros((len(meta), mask_blocks), bool)
            repairs = []
            for row_index, cell in enumerate(meta.canonical_cell_id.astype(str)):
                ordered_blocks = sorted(range(mask_blocks), key=lambda block: (digest_int(mask_seed, "cell-view-block", cell, view, block), block))
                selected_set = ordered_blocks[:selected_blocks]
                chosen[row_index, selected_set] = True
                count = int(block_counts[selected_set].sum())
                if count > target_visible:
                    adjust_blocks = sorted(selected_set, key=lambda block: (digest_int(mask_seed, "repair-remove", cell, view, block), block))[:count - target_visible]
                    repairs.append(([(block_addresses[block][0]) for block in adjust_blocks], []))
                elif count < target_visible:
                    unselected = ordered_blocks[selected_blocks:]
                    adjust_blocks = sorted(unselected, key=lambda block: (digest_int(mask_seed, "repair-add", cell, view, block), block))[:target_visible - count]
                    repairs.append(([], [(block_addresses[block][0]) for block in adjust_blocks]))
                else:
                    repairs.append(([], []))
                removed, added = repairs[-1]
                if count - len(removed) + len(added) != target_visible:
                    raise RuntimeError("exact visible-address count repair failed")
            selected_by_view.append(chosen)
            repairs_by_view.append(repairs)
        for label, (vcol, vsign, viscol, vissign) in maps.items():
            full_value = sparse.csr_matrix((coo.data * vsign[coo.col], (coo.row, vcol[coo.col])), shape=(len(meta), channel_dim)).toarray().astype(np.float32)
            result[f"{label}_full"] = np.concatenate((full_value, np.repeat(full_visibility[label][None, :], len(meta), axis=0)), axis=1)
            for view in range(views):
                chosen = selected_by_view[view]
                baseline = chosen[coo.row, block_id[coo.col]]
                view_value = sparse.csr_matrix((coo.data[baseline] * vsign[coo.col[baseline]], (coo.row[baseline], vcol[coo.col[baseline]])), shape=(len(meta), channel_dim)).toarray().astype(np.float32)
                view_visibility = (chosen.astype(np.float32) @ visibility_sums[label]).astype(np.float32)
                for row_index, (removed, added) in enumerate(repairs_by_view[view]):
                    begin, end = values.indptr[row_index], values.indptr[row_index + 1]
                    indices = values.indices[begin:end]
                    data = values.data[begin:end]
                    for address, direction in [(x, -1.0) for x in removed] + [(x, 1.0) for x in added]:
                        view_visibility[row_index, viscol[address]] += direction * vissign[address]
                        position = int(np.searchsorted(indices, address))
                        if position < len(indices) and int(indices[position]) == address:
                            view_value[row_index, vcol[address]] += direction * data[position] * vsign[address]
                result[f"{label}_view{view}"] = np.concatenate((view_value, view_visibility), axis=1)
        scalar = int(np.count_nonzero(states[op] == 1))
        structural = int(np.count_nonzero(states[op] == 0))
        collision = int(np.count_nonzero(states[op] == 2))
        nonzero = np.diff(values.indptr).astype(np.float32)
        result["physical_descriptors"] = np.column_stack([
            np.log1p(meta.source_library.to_numpy(np.float64)),
            np.full(len(meta), scalar / ADDRESS_N), np.full(len(meta), structural / ADDRESS_N),
            np.full(len(meta), collision / ADDRESS_N), nonzero / max(scalar, 1), np.full(len(meta), 0.6),
        ]).astype(np.float32)
        tmp = output_path.with_name(output_path.stem + ".tmp.npz")
        np.savez_compressed(tmp, **result)
        os.replace(tmp, output_path)
        row = {"block_key": key, "operator_index": op, "rows": len(meta), "feature_path": output_path.relative_to(out).as_posix(), "feature_sha256": sha(output_path)}
        journal = pd.concat([journal, pd.DataFrame([row])], ignore_index=True)
        write_csv_atomic(journal_path, journal)
        print(f"features {key} rows={len(meta)}", flush=True)

    final = pd.read_csv(journal_path)
    if final.block_key.nunique() != len(blocks) or final.rows.sum() != blocks.rows.sum() or final.operator_index.nunique() != 42:
        raise RuntimeError("final feature geometry mismatch")
    for row in final.itertuples(index=False):
        if sha(out / row.feature_path) != row.feature_sha256:
            raise RuntimeError(f"final feature hash mismatch: {row.block_key}")
    manifest_path = out / "PHASE2_MULTIVIEW_FEATURE_BLOCK_MANIFEST.csv"
    write_csv_atomic(manifest_path, final.sort_values(["operator_index", "block_key"]))
    contract["status"] = "PASS_PHASE2_MULTIVIEW_FEATURES"
    write_json_atomic(contract_path, contract)
    audit = {
        "schema": "full104-phase2-multiview-features-v1", "status": "PASS_PHASE2_MULTIVIEW_FEATURES",
        "cells": int(final.rows.sum()), "sample_level": level, "blocks": len(final), "operators": int(final.operator_index.nunique()),
        "views": views, "sketches": 2, "feature_dim_per_view": feature_dim,
        "projection_sha256": sha(projection_path), "block_manifest_sha256": sha(manifest_path),
        "exact_visible_scalar_count_rule": True, "measured_zero_visibility_channel_retained": True,
        "identity_or_biology_labels_in_features": False, "protected_or_heldout_expression_opened": False,
        "optimizer_ema_lambda_query_schedule_gpu_mechanics_or_training": False,
        "wall_seconds": time.time() - started,
    }
    audit_path = out / "PHASE2_MULTIVIEW_FEATURE_AUDIT.json"
    write_json_atomic(audit_path, audit)
    package_manifest = out / "PHASE2_MULTIVIEW_FEATURE_MANIFEST.csv"
    files = [contract_path, projection_path, manifest_path, audit_path, Path(__file__)]
    pd.DataFrame([{"path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), "bytes": path.stat().st_size, "sha256": sha(path)} for path in files]).to_csv(package_manifest, index=False, lineterminator="\n")
    (out.parent / f"PHASE2_MULTIVIEW_FEATURE_LEVEL{level}_MANIFEST_SHA256.txt").write_text(sha(package_manifest) + "\n", encoding="ascii")
    print(json.dumps({**audit, "manifest_sha256": sha(package_manifest)}, indent=2))


if __name__ == "__main__":
    main()
