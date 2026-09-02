#!/usr/bin/env python3
"""Resumable authenticated materialization of Phase-2 selection into sparse 41K blocks."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.io import mmread

ROOT = Path(__file__).resolve().parents[2]
V8_ENV = ROOT / "outputs/full104_v014_20260826/full104_expression_interface_v8_verified"
V8 = V8_ENV / "FULL104_EXPRESSION_INTERFACE_V8"
AUTH = Path(r"D:\Jepa project-stage81a3r-20260814")
ADDRESS_N = 41_238
BLOCK = 512


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json_atomic(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def write_csv_atomic(path: Path, frame: pd.DataFrame) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(tmp, index=False, lineterminator="\n")
    os.replace(tmp, path)


def decode(values):
    return np.asarray([x.decode() if isinstance(x, (bytes, np.bytes_)) else str(x) for x in values], object)


def hvec(group, key):
    node = group[key]
    if isinstance(node, h5py.Group) and "codes" in node:
        codes = np.asarray(node["codes"])
        categories = decode(np.asarray(node["categories"]))
        return np.asarray([categories[int(x)] if int(x) >= 0 else "" for x in codes], object)
    return decode(np.asarray(node))


def verify_manifest(directory: Path, manifest_name: str, anchor: Path) -> str:
    manifest = directory / manifest_name
    digest = sha(manifest)
    if digest != anchor.read_text(encoding="ascii").strip():
        raise RuntimeError(f"manifest anchor mismatch: {manifest}")
    for row in pd.read_csv(manifest).itertuples(index=False):
        path = directory / str(row.path)
        if not path.is_file() or path.stat().st_size != int(row.bytes) or sha(path) != str(row.sha256):
            raise RuntimeError(f"manifest artifact mismatch: {path}")
    return digest


def append_journal(path: Path, row: dict) -> None:
    current = pd.read_csv(path) if path.is_file() else pd.DataFrame()
    current = pd.concat([current, pd.DataFrame([row])], ignore_index=True)
    write_csv_atomic(path, current)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    started = time.time()
    freeze_dir = Path(args.freeze).resolve()
    selection_dir = Path(args.selection).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    blocks_dir = out / "blocks"
    blocks_dir.mkdir(exist_ok=True)

    freeze_sha = verify_manifest(freeze_dir, "PHASE2_PREEXPRESSION_MANIFEST.csv", freeze_dir.parent / "PHASE2_PREEXPRESSION_MANIFEST_SHA256.txt")
    selection_audit = json.loads((selection_dir / "PHASE2_METADATA_SELECTION_AUDIT.json").read_text())
    level = int(selection_audit["level"])
    selection_sha = verify_manifest(selection_dir, "PHASE2_METADATA_SELECTION_MANIFEST.csv", selection_dir.parent / f"PHASE2_METADATA_SELECTION_LEVEL{level}_MANIFEST_SHA256.txt")
    selection_path = selection_dir / f"PHASE2_METADATA_SELECTION_LEVEL{level}.csv.gz"
    selected = pd.read_csv(selection_path, dtype={"donor_id": str, "canonical_cell_id": str})
    if len(selected) != int(selection_audit["cells"]) or selected.donor_id.nunique() != 104 or selected.operator_index.nunique() != 42:
        raise RuntimeError("selection geometry mismatch")
    if selected.expression_asset_path.str.contains("stage81a1d/sealed/nph52_organized", case=False).any():
        raise RuntimeError("original mixed NPH path reached materializer")

    contract = {
        "schema": "full104-phase2-expression-materialization-v1",
        "status": "IN_PROGRESS",
        "freeze_manifest_sha256": freeze_sha,
        "selection_manifest_sha256": selection_sha,
        "selection_sha256": sha(selection_path),
        "code_sha256": sha(Path(__file__)),
        "cells": len(selected), "sample_level": level, "donors": 104, "operators": 42, "addresses": ADDRESS_N,
        "block_rows": BLOCK, "normalization_deferred": "raw integer counts plus full-source library; downstream applies log1p(raw*10000/library) exactly once",
        "identity_is_audit_metadata_not_model_input": True,
        "original_mixed_nph_denied": True,
        "no_validation_oracle_dev_sealed_pathology": True,
        "no_optimizer_ema_lambda_query_schedule_gpu_mechanics_or_training": True,
    }
    contract_path = out / "MATERIALIZATION_CONTRACT.json"
    if contract_path.is_file():
        previous = json.loads(contract_path.read_text(encoding="utf-8"))
        if previous != contract:
            previous_without_code = {k: v for k, v in previous.items() if k != "code_sha256"}
            contract_without_code = {k: v for k, v in contract.items() if k != "code_sha256"}
            authorized_predecessor = "ff9d5445cf10c5e63a01d782227591f5a26d545f2ad5f09fbfd13c3243f14a45"
            if previous_without_code != contract_without_code or previous.get("code_sha256") != authorized_predecessor:
                raise RuntimeError("resume contract mismatch")
            transition = {
                "schema": "phase2-expression-execution-code-transition-v1",
                "reason": "reuse complete authenticated NPH intermediates after worker lease expiry",
                "previous_code_sha256": authorized_predecessor,
                "current_code_sha256": contract["code_sha256"],
                "scientific_and_data_contract_fields_unchanged": True,
            }
            write_json_atomic(out / "EXECUTION_CODE_TRANSITION.json", transition)
            write_json_atomic(contract_path, contract)
    else:
        write_json_atomic(contract_path, contract)

    asset_journal = out / "ASSET_AUTHENTICATION.csv"
    authenticated = pd.read_csv(asset_journal, dtype=str) if asset_journal.is_file() else pd.DataFrame()
    unique_assets = selected[["matrix_id", "source", "expression_asset_path", "expression_asset_sha256"]].drop_duplicates()
    if len(unique_assets) != 42:
        raise RuntimeError("asset cardinality mismatch")
    for row in unique_assets.sort_values(["source", "matrix_id"]).itertuples(index=False):
        path = ROOT / str(row.expression_asset_path)
        if not path.is_file():
            raise RuntimeError(f"expression asset missing: {path}")
        stat = path.stat()
        old = authenticated[authenticated.matrix_id.eq(row.matrix_id)] if len(authenticated) else pd.DataFrame()
        if len(old) == 1 and int(old.iloc[0].bytes) == stat.st_size and int(old.iloc[0].mtime_ns) == stat.st_mtime_ns and old.iloc[0].sha256 == row.expression_asset_sha256:
            print(f"reuse asset authentication {row.matrix_id}", flush=True)
            continue
        digest = sha(path)
        if digest != row.expression_asset_sha256:
            raise RuntimeError(f"live expression asset hash mismatch: {row.matrix_id}")
        append_journal(asset_journal, {"matrix_id": row.matrix_id, "source": row.source, "path": row.expression_asset_path, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": digest})
        authenticated = pd.read_csv(asset_journal, dtype=str)
        print(f"authenticated asset {row.matrix_id} bytes={stat.st_size}", flush=True)

    assets = pd.read_csv(ROOT / "results/v4/stage81a2_canonical_asset_registry.csv", dtype=str).set_index("dataset_id")
    semantics = pd.read_csv(ROOT / "results/v4/stage81a2_matrix_semantics_contract.csv", dtype=str).set_index("dataset_id")
    provenance = pd.read_csv(ROOT / "results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz", low_memory=False)
    collision = pd.read_csv(AUTH / "results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz", low_memory=False)
    supplement = pd.read_csv(AUTH / "results/v4/stage81a3r_scalar_mapping_unregistered_collisions.csv")
    state_npz = np.load(ROOT / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz", allow_pickle=False)
    states = state_npz["states"].astype(np.uint8)
    if states.shape != (42, ADDRESS_N):
        raise RuntimeError("operator-state geometry mismatch")

    block_journal = out / "BLOCK_MANIFEST.partial.csv"
    completed = pd.read_csv(block_journal, dtype=str) if block_journal.is_file() else pd.DataFrame()
    h5_selection = selected[~selected.source.eq("NPH52")]
    for matrix_id, group in h5_selection.groupby("matrix_id", sort=True):
        group = group.sort_values("selection_row").reset_index(drop=True)
        source = str(group.source.iloc[0])
        op = int(group.operator_index.iloc[0])
        source_key = "HVS_COMMON" if source == "HVS" else "SEA_AD_COMMON"
        mapping = provenance[provenance.source_dataset_id.eq(source_key)][["source_feature_index", "molecular_address_index"]].copy()
        blocked = set(collision.loc[collision.matrix_id.astype(str).eq(matrix_id), "source_feature_index"].astype(int))
        for value in supplement.loc[supplement.matrix_id.astype(str).eq(matrix_id), "source_feature_indices"].astype(str):
            blocked.update(map(int, value.split("|")))
        mapping = mapping[~mapping.source_feature_index.astype(int).isin(blocked)]
        if mapping.source_feature_index.duplicated().any() or mapping.molecular_address_index.duplicated().any():
            raise RuntimeError(f"noninjective address mapping: {matrix_id}")
        if len(mapping) and not np.all(states[op, mapping.molecular_address_index.astype(int).to_numpy()] == 1):
            raise RuntimeError(f"mapping target is not MEASURED_SCALAR: {matrix_id}")
        asset = assets.loc[matrix_id]
        sem = semantics.loc[matrix_id]
        if sem.matrix_semantics != "raw_integer_counts" or str(sem.normalization_already_applied).lower() != "false" or str(sem.log_transform_already_applied).lower() != "false":
            raise RuntimeError(f"expression semantics mismatch: {matrix_id}")
        output_dir = blocks_dir / f"op{op:02d}"
        output_dir.mkdir(exist_ok=True)
        with h5py.File(ROOT / str(asset.matrix_path_or_object), "r") as handle:
            donor_key = "donor_id" if source == "HVS" else "Donor ID"
            donors = hvec(handle["obs"], donor_key)
            cells = hvec(handle["obs"], "exp_component_name")
            node = handle[str(sem.matrix_slot)]
            n_features = int(node.attrs.get("shape", [len(cells), max(mapping.source_feature_index.max() + 1, 1)])[1]) if "shape" in node.attrs else int(max(mapping.source_feature_index.max() + 1, 1))
            source_to_address = np.full(n_features, -1, dtype=np.int32)
            valid_source = mapping.source_feature_index.astype(int).to_numpy()
            if len(valid_source) and valid_source.max() >= n_features:
                n_features = int(valid_source.max() + 1)
                source_to_address = np.full(n_features, -1, dtype=np.int32)
            source_to_address[valid_source] = mapping.molecular_address_index.astype(int).to_numpy()
            for block_index, begin in enumerate(range(0, len(group), BLOCK)):
                take = group.iloc[begin:begin + BLOCK].copy()
                key = f"op{op:02d}/block-{block_index:05d}"
                old = completed[completed.block_key.eq(key)] if len(completed) else pd.DataFrame()
                counts_path = output_dir / f"block-{block_index:05d}.counts.npz"
                meta_path = output_dir / f"block-{block_index:05d}.meta.csv"
                if len(old) == 1 and counts_path.is_file() and meta_path.is_file() and sha(counts_path) == old.iloc[0].counts_sha256 and sha(meta_path) == old.iloc[0].meta_sha256:
                    print(f"reuse block {key}", flush=True)
                    continue
                row_parts, col_parts, value_parts, libraries = [], [], [], []
                for local, row in enumerate(take.itertuples(index=False)):
                    source_row = int(row.expression_row)
                    if str(cells[source_row]) != str(row.canonical_cell_id) or str(donors[source_row]) != str(row.donor_id):
                        raise RuntimeError(f"H5 row identity mismatch: {matrix_id}")
                    a, b = int(node["indptr"][source_row]), int(node["indptr"][source_row + 1])
                    indices = np.asarray(node["indices"][a:b], dtype=np.int64)
                    values = np.asarray(node["data"][a:b])
                    if np.any(values < 0) or not np.allclose(values, np.rint(values)):
                        raise RuntimeError(f"H5 payload is not raw integer counts: {matrix_id}")
                    libraries.append(int(np.rint(values).sum()))
                    in_range = indices < len(source_to_address)
                    targets = np.full(len(indices), -1, dtype=np.int32)
                    targets[in_range] = source_to_address[indices[in_range]]
                    keep = targets >= 0
                    if keep.any():
                        row_parts.append(np.full(int(keep.sum()), local, dtype=np.int32))
                        col_parts.append(targets[keep])
                        value_parts.append(np.rint(values[keep]).astype(np.int32))
                rows = np.concatenate(row_parts) if row_parts else np.empty(0, np.int32)
                cols = np.concatenate(col_parts) if col_parts else np.empty(0, np.int32)
                vals = np.concatenate(value_parts) if value_parts else np.empty(0, np.int32)
                matrix = sparse.csr_matrix((vals, (rows, cols)), shape=(len(take), ADDRESS_N), dtype=np.int32)
                tmp_counts = counts_path.with_name(counts_path.stem + ".tmp.npz")
                sparse.save_npz(tmp_counts, matrix, compressed=True)
                os.replace(tmp_counts, counts_path)
                meta = take[["selection_row", "canonical_cell_id", "donor_id", "expression_row", "primary_row_weight"]].copy()
                meta["source_library"] = libraries
                write_csv_atomic(meta_path, meta)
                append_journal(block_journal, {"block_key": key, "source": source, "operator_index": op, "matrix_id": matrix_id, "rows": len(take), "nnz": int(matrix.nnz), "counts_path": counts_path.relative_to(out).as_posix(), "counts_sha256": sha(counts_path), "meta_path": meta_path.relative_to(out).as_posix(), "meta_sha256": sha(meta_path)})
                completed = pd.read_csv(block_journal, dtype=str)
                print(f"materialized {key} rows={len(take)} nnz={matrix.nnz}", flush=True)

    nph_staging = out / "nph_matrix_market_intermediate"
    nph_staging.mkdir(exist_ok=True)
    rscript = Path(r"C:\Program Files\R\R-4.1.2\bin\Rscript.exe")
    # R materialization can exceed a single worker lease.  Reuse only a complete
    # intermediate set; the conversion below still validates every block's exact
    # selection-row and canonical-cell identity before it enters the journal.
    nph_selected = selected.loc[selected.source.eq("NPH52")]
    expected_nph_stems = {
        f"op{int(op):02d}/block-{block_index:05d}"
        for op, group in nph_selected.groupby("operator_index")
        for block_index in range((len(group) + BLOCK - 1) // BLOCK)
    }
    actual_mtx_stems = {
        path.relative_to(nph_staging).with_suffix("").as_posix()
        for path in nph_staging.glob("op*/block-*.mtx")
    }
    actual_meta_stems = {
        path.relative_to(nph_staging).as_posix().removesuffix(".meta.csv")
        for path in nph_staging.glob("op*/block-*.meta.csv")
    }
    nph_intermediates_complete = (
        actual_mtx_stems == expected_nph_stems
        and actual_meta_stems == expected_nph_stems
        and all(path.stat().st_size > 0 for path in nph_staging.glob("op*/block-*.mtx"))
        and all(path.stat().st_size > 0 for path in nph_staging.glob("op*/block-*.meta.csv"))
    )
    if nph_intermediates_complete:
        print(f"reuse complete NPH intermediate set blocks={len(expected_nph_stems)}", flush=True)
    else:
        subprocess.run([str(rscript), str(ROOT / "scripts/v4/materialize_full104_phase2_nph_blocks.R"), str(ROOT), str(V8), str(selection_path), str(ROOT / "results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz"), str(AUTH / "results/v4"), str(nph_staging)], check=True)
    for op in sorted(selected.loc[selected.source.eq("NPH52"), "operator_index"].unique().astype(int)):
        op_stage = nph_staging / f"op{op:02d}"
        op_out = blocks_dir / f"op{op:02d}"
        op_out.mkdir(exist_ok=True)
        for mtx_path in sorted(op_stage.glob("block-*.mtx")):
            block_index = int(mtx_path.stem.split("-")[-1])
            key = f"op{op:02d}/block-{block_index:05d}"
            counts_path = op_out / f"block-{block_index:05d}.counts.npz"
            meta_path = op_out / f"block-{block_index:05d}.meta.csv"
            source_meta = mtx_path.with_suffix(".meta.csv")
            old = completed[completed.block_key.eq(key)] if len(completed) else pd.DataFrame()
            if len(old) == 1 and counts_path.is_file() and meta_path.is_file() and sha(counts_path) == old.iloc[0].counts_sha256 and sha(meta_path) == old.iloc[0].meta_sha256:
                continue
            matrix = mmread(mtx_path).tocsr().astype(np.int32)
            meta = pd.read_csv(source_meta, dtype={"donor_id": str, "canonical_cell_id": str})
            expected = selected[selected.operator_index.eq(op)].sort_values("selection_row").iloc[block_index * BLOCK:block_index * BLOCK + len(meta)]
            if matrix.shape != (len(meta), ADDRESS_N) or meta.selection_row.astype(int).tolist() != expected.selection_row.astype(int).tolist() or meta.canonical_cell_id.tolist() != expected.canonical_cell_id.tolist():
                raise RuntimeError(f"NPH block identity mismatch: {key}")
            meta = meta.merge(expected[["selection_row", "primary_row_weight"]], on="selection_row", validate="one_to_one")
            tmp_counts = counts_path.with_name(counts_path.stem + ".tmp.npz")
            sparse.save_npz(tmp_counts, matrix, compressed=True)
            os.replace(tmp_counts, counts_path)
            write_csv_atomic(meta_path, meta[["selection_row", "canonical_cell_id", "donor_id", "expression_row", "primary_row_weight", "source_library"]])
            append_journal(block_journal, {"block_key": key, "source": "NPH52", "operator_index": op, "matrix_id": str(expected.matrix_id.iloc[0]), "rows": len(meta), "nnz": int(matrix.nnz), "counts_path": counts_path.relative_to(out).as_posix(), "counts_sha256": sha(counts_path), "meta_path": meta_path.relative_to(out).as_posix(), "meta_sha256": sha(meta_path)})
            completed = pd.read_csv(block_journal, dtype=str)
            print(f"converted NPH {key} rows={len(meta)} nnz={matrix.nnz}", flush=True)

    final_blocks = pd.read_csv(block_journal)
    if final_blocks.block_key.nunique() != len(final_blocks) or final_blocks.rows.sum() != len(selected) or final_blocks.operator_index.nunique() != 42:
        raise RuntimeError("final block geometry mismatch")
    for row in final_blocks.itertuples(index=False):
        cp, mp = out / row.counts_path, out / row.meta_path
        if sha(cp) != row.counts_sha256 or sha(mp) != row.meta_sha256:
            raise RuntimeError(f"final block hash mismatch: {row.block_key}")
    final_manifest = out / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    write_csv_atomic(final_manifest, final_blocks.sort_values(["operator_index", "block_key"]))
    audit = {
        "schema": "full104-phase2-expression-materialization-v1", "status": "PASS_PHASE2_EXPRESSION_MATERIALIZED",
        "cells": int(final_blocks.rows.sum()), "sample_level": level, "blocks": len(final_blocks), "operators": int(final_blocks.operator_index.nunique()),
        "nnz": int(final_blocks.nnz.sum()), "addresses": ADDRESS_N,
        "normalization": "raw integer counts retained; full-source library retained; downstream log1p10K exactly once",
        "measured_zero_semantics": "zero remains measured through separate authenticated operator-state authority",
        "asset_authentication_sha256": sha(asset_journal), "block_manifest_sha256": sha(final_manifest),
        "original_mixed_nph_opened": False, "protected_expression_opened": False,
        "reader_validation_oracle_dev_sealed_pathology_opened": False,
        "optimizer_ema_lambda_query_schedule_gpu_mechanics_or_training": False,
        "wall_seconds": time.time() - started,
    }
    audit_path = out / "PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json"
    write_json_atomic(audit_path, audit)
    contract["status"] = "PASS_PHASE2_EXPRESSION_MATERIALIZED"
    write_json_atomic(contract_path, contract)
    package_manifest = out / "PHASE2_EXPRESSION_MATERIALIZATION_MANIFEST.csv"
    package_files = [contract_path, asset_journal, final_manifest, audit_path, Path(__file__), ROOT / "scripts/v4/materialize_full104_phase2_nph_blocks.R"]
    pd.DataFrame([{"path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), "bytes": path.stat().st_size, "sha256": sha(path)} for path in package_files]).to_csv(package_manifest, index=False, lineterminator="\n")
    (out.parent / f"PHASE2_EXPRESSION_MATERIALIZATION_LEVEL{level}_MANIFEST_SHA256.txt").write_text(sha(package_manifest) + "\n", encoding="ascii")
    print(json.dumps({**audit, "manifest_sha256": sha(package_manifest)}, indent=2))


if __name__ == "__main__":
    main()
