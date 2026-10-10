#!/usr/bin/env python3
"""Standalone G7 V2 exact cross-check against the G1b-authorized S174 cache.

THIS FILE DOES NOT AUTHORIZE A VALUE READ.

It requires the same separately created V2 runtime authorization and repaired V3 G4/G5 evidence as
standalone G6 V2, plus a genuine G6 V2 PASS receipt bound to those same evidence/code bytes. It
independently authenticates the exact G1b PASS result/freeze pair, S174 shards and physical H5AD
bytes, rereads only natural Sample-A HVS/SEA overlaps, and compares all exact 9,216 replay addresses.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


def _load_common():
    path = Path(__file__).resolve().with_name("td_relational_value_read_v2_common.py")
    spec = importlib.util.spec_from_file_location("td_value_v2_common_g7", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


common = _load_common()

G7_SCHEMA = "JEPA_TD_RELATIONAL_G7_S174_OVERLAP_V2"
G6_RECEIPT_SCHEMA = "JEPA_TD_RELATIONAL_G6_RECEIPT_V2"
G6_PASS = "PASS_TD_G6_SOURCE_LIBRARY_EXACT"
G7_PASS = "PASS_TD_G7_S174_EXACT_OVERLAP"
G7_MISMATCH = "STOP_TD_G7_S174_CROSSCHECK_MISMATCH"
G7_NOT_ESTIMABLE = "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP"
G1B_FREEZE_SHA256 = "0513421e45865f290bddf8b0be56d64c7d9c5297bf0150ea6b9df286514b5f8f"
G1B_PASS_COMMIT = "4ab8e2101f2e595d9a97df05517d6e672768ecec"
G1B_FREEZE_REPO_PATH = "results/v77/S174_REBUILD_G1B_FREEZE_V1.json"
G1B_RESULT_REPO_PATH = "results/v77/S174_REBUILD_G1B_RESULT_V1.json"

N_ADDR = 41_238
N_SAMPLE_A = 25_000
N_REPLAY = 9_216
SAMPLE_A_LABEL = "A_NATURAL_MIXTURE"
SOURCE_COUNTS = {"HVS": 1_129, "NPH52": 1_310, "SEA_AD": 22_561}
FAMILY = {"HVS": "HVS_COMMON", "SEA_AD": "SEA_AD_COMMON"}
VAR_ID_COLUMN = {"HVS": "_index", "SEA_AD": "gene_ids"}

EXPECTED_REPLAY_MANIFEST_SHA = common.EXPECTED_INPUT_HASHES["replay_manifest_sha256"]
EXPECTED_SAMPLE_FREEZE_SHA = common.EXPECTED_INPUT_HASHES["sample_freeze_sha256"]
EXPECTED_PROVENANCE_SHA = common.EXPECTED_INPUT_HASHES["provenance_sha256"]
EXPECTED_COLLISION_SHA = common.EXPECTED_INPUT_HASHES["collision_ledger_sha256"]
EXPECTED_MACHA_FREEZE_SHA = common.EXPECTED_INPUT_HASHES["macha_freeze_sha256"]


def h5_strings(group, name: str) -> np.ndarray:
    import h5py
    if name == "_index":
        name = group.attrs.get("_index", "_index")
        name = name.decode() if isinstance(name, bytes) else str(name)
    obj = group[name]
    values = obj["categories"][:][obj["codes"][:]] if isinstance(obj, h5py.Group) else obj[:]
    return np.asarray([v.decode() if isinstance(v, bytes) else str(v) for v in values], dtype=object)


def identifier_map(var_ids, id_to_address: dict[str, int], ledger_ids: set[str]):
    reach: dict[int, list[int]] = {}
    excluded: dict[int, str] = {}
    for column, gid0 in enumerate(var_ids):
        gid = str(gid0)
        if gid in ledger_ids:
            excluded[column] = "LEDGER_COLLISION"
            continue
        address = id_to_address.get(gid)
        if address is None:
            excluded[column] = "UNMAPPED"
            continue
        reach.setdefault(int(address), []).append(column)
    col_to_address: dict[int, int] = {}
    for address, columns in reach.items():
        if len(columns) == 1:
            col_to_address[columns[0]] = address
        else:
            for column in columns:
                excluded[column] = "JOIN_COLLISION"
    return col_to_address, excluded


def corrected_row(indices, values, col_to_address: dict[int, int], replay_addresses: set[int]):
    row: dict[int, int] = {}
    total = 0
    for j0, v0 in zip(indices, values):
        column = int(j0)
        value = common.strict_raw_integer(v0)
        total += value
        address = col_to_address.get(column)
        if address is not None and address in replay_addresses and value:
            if address in row:
                raise RuntimeError(f"noninjective mapped replay address encountered at G7 reread: {address}")
            row[address] = value
    return row, total


def compare_rows(current: dict[int, int], reference: dict[int, int], addresses: set[int]) -> dict[str, int]:
    mismatches = sum(int(current.get(a, 0)) != int(reference.get(a, 0)) for a in addresses)
    return {"checked": len(addresses), "mismatches": int(mismatches)}


def overlap_status(overlap_cells: int, mismatches: int) -> str:
    if overlap_cells == 0:
        return G7_NOT_ESTIMABLE
    if mismatches:
        return G7_MISMATCH
    return G7_PASS


def exit_code_for_status(status: str) -> int:
    if status == G7_PASS:
        return 0
    if status == G7_NOT_ESTIMABLE:
        return 3
    return 2


def validate_g1b_result(result: dict) -> None:
    if result.get("schema") != "S174_REBUILD_G1B_RESULT_V1":
        raise RuntimeError("unexpected G1b result schema")
    if result.get("G1b_pass") is not True:
        raise RuntimeError("G1b result is not PASS")
    freeze = result.get("freeze") or {}
    if freeze.get("path") != G1B_FREEZE_REPO_PATH or freeze.get("sha256") != G1B_FREEZE_SHA256:
        raise RuntimeError("G1b result freeze authority mismatch")
    requirements = result.get("requirements") or {}
    failed = [f"R{i}" for i in range(1, 8) if requirements.get(f"R{i}") is not True]
    if failed:
        raise RuntimeError(f"G1b result requirement(s) not PASS: {failed}")


def validate_g1b_freeze(freeze: dict) -> None:
    if freeze.get("schema") != "S174_REBUILD_G1B_FREEZE_V1":
        raise RuntimeError("unexpected G1b freeze schema")
    if freeze.get("status") != "FROZEN__NO_COUNT_READ":
        raise RuntimeError("unexpected G1b freeze status")
    if not (freeze.get("rebuilt_cache") or {}).get("shards"):
        raise RuntimeError("G1b freeze contains no rebuilt-cache shard authority")


def _git_show_bytes(anchor_path: Path, commit: str, repo_path: str) -> bytes:
    root = common._git_root(Path(anchor_path))
    spec = f"{commit}:{repo_path}"
    try:
        return subprocess.check_output(["git", "-C", str(root), "show", spec], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"cannot resolve exact git authority {spec}: {exc.output.decode(errors='replace')}") from exc


def load_g1b_authority_from_pass_commit(anchor_path: Path) -> tuple[dict, dict, str, str]:
    result_raw = _git_show_bytes(anchor_path, G1B_PASS_COMMIT, G1B_RESULT_REPO_PATH)
    freeze_raw = _git_show_bytes(anchor_path, G1B_PASS_COMMIT, G1B_FREEZE_REPO_PATH)
    freeze_sha = hashlib.sha256(freeze_raw).hexdigest()
    if freeze_sha != G1B_FREEZE_SHA256:
        raise RuntimeError(f"exact G1b freeze bytes at pass commit do not match frozen SHA: {freeze_sha}")
    try:
        result = json.loads(result_raw.decode("utf-8"))
        freeze = json.loads(freeze_raw.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError("G1b pass-commit authority is not valid UTF-8 JSON") from exc
    validate_g1b_result(result)
    validate_g1b_freeze(freeze)
    return result, freeze, hashlib.sha256(result_raw).hexdigest(), freeze_sha


def validate_s174_payload(data, indices, indptr, shape) -> None:
    shape = tuple(int(x) for x in shape)
    if len(shape) != 2 or shape[1] != N_ADDR:
        raise RuntimeError(f"S174 cache geometry must have exactly 41238 columns: {shape}")
    data = np.asarray(data)
    indices = np.asarray(indices)
    indptr = np.asarray(indptr)
    if len(data) != len(indices):
        raise RuntimeError("S174 CSR data/indices length mismatch")
    if len(indptr) != shape[0] + 1 or int(indptr[0]) != 0 or int(indptr[-1]) != len(data):
        raise RuntimeError("S174 CSR indptr geometry mismatch")
    if np.any(np.diff(indptr.astype(np.int64, copy=False)) < 0):
        raise RuntimeError("S174 CSR indptr is not monotone")
    if len(indices) and (np.any(indices < 0) or np.any(indices >= N_ADDR)):
        raise RuntimeError("S174 CSR address index out of 41238-column bounds")
    numeric = data.astype(np.float64, copy=False)
    if not np.isfinite(numeric).all() or np.any(numeric < 0) or not np.equal(numeric, np.floor(numeric)).all():
        raise RuntimeError("S174 raw counts must be finite, nonnegative and exactly integer-valued")


def sparse_row_dict(matrix, row_index: int, addresses: set[int]) -> dict[int, int]:
    row = matrix.getrow(row_index)
    output: dict[int, int] = {}
    for address0, value0 in zip(row.indices, row.data):
        address = int(address0)
        value = common.strict_raw_integer(value0)
        if address in addresses and value:
            output[address] = value
    return output


def verify_cache_hashes(cache_root: Path, g1b_freeze: dict) -> tuple[int, dict[str, dict[str, str]]]:
    shards = g1b_freeze.get("rebuilt_cache", {}).get("shards", {})
    if not shards:
        raise RuntimeError("G1b freeze contains no rebuilt cache shard authority")
    verified: dict[str, dict[str, str]] = {}
    for stem, rec in shards.items():
        counts_path = Path(cache_root) / f"{stem}.counts.npz"
        meta_path = Path(cache_root) / f"{stem}.meta.npz"
        if not counts_path.is_file() or not meta_path.is_file():
            raise RuntimeError(f"S174 cache shard missing: {stem}")
        counts_sha = common.sha256_file(counts_path)
        meta_sha = common.sha256_file(meta_path)
        if counts_sha != rec["counts"] or meta_sha != rec["meta"]:
            raise RuntimeError(f"S174 G1b-authorized cache hash mismatch: {stem}")
        with np.load(counts_path, allow_pickle=False) as payload:
            shape = tuple(int(x) for x in payload["shape"])
            if len(shape) != 2 or shape[1] != N_ADDR:
                raise RuntimeError(f"S174 cache geometry must have exactly 41238 columns: {stem}: {shape}")
            n_rows = int(shape[0])
        with np.load(meta_path, allow_pickle=False) as meta:
            if "cell_id" not in meta.files or len(meta["cell_id"]) != n_rows:
                raise RuntimeError(f"S174 meta/count row geometry mismatch: {stem}")
        verified[str(stem)] = {"counts_sha256": counts_sha, "meta_sha256": meta_sha}
    return len(shards), verified


def select_sample_a(frame: pd.DataFrame) -> pd.DataFrame:
    selected = frame[frame["sample"].astype(str).eq(SAMPLE_A_LABEL)].copy().sort_values("sample_row")
    if len(selected) != N_SAMPLE_A:
        raise RuntimeError("Sample-A geometry mismatch")
    if selected.source.value_counts().to_dict() != SOURCE_COUNTS:
        raise RuntimeError("Sample-A source counts mismatch")
    if selected.sample_row.astype(int).tolist() != list(range(N_SAMPLE_A)):
        raise RuntimeError("Sample-A row order mismatch")
    return selected


def _require_file_hash(path: Path, expected: str, label: str) -> None:
    path = Path(path)
    if not path.is_file() or common.sha256_file(path) != expected:
        raise RuntimeError(f"authority mismatch: {label}: {path}")


def load_inputs(args):
    require = {
        "replay_manifest": (Path(args.replay_manifest), EXPECTED_REPLAY_MANIFEST_SHA),
        "sample_freeze": (Path(args.sample_freeze), EXPECTED_SAMPLE_FREEZE_SHA),
        "provenance": (Path(args.provenance), EXPECTED_PROVENANCE_SHA),
        "collision_ledger": (Path(args.collision_ledger), EXPECTED_COLLISION_SHA),
        "macha_freeze": (Path(args.macha_freeze), EXPECTED_MACHA_FREEZE_SHA),
    }
    for label, (path, expected) in require.items():
        _require_file_hash(path, expected, label)
    replay = pd.read_csv(require["replay_manifest"][0])
    if len(replay) != N_REPLAY or replay.molecular_address_index.nunique() != N_REPLAY:
        raise RuntimeError("replay manifest geometry mismatch")
    sample = pd.read_csv(require["sample_freeze"][0], dtype=str)
    sample_a = select_sample_a(sample)
    provenance = pd.read_csv(require["provenance"][0], low_memory=False)
    collision = pd.read_csv(require["collision_ledger"][0], low_memory=False)
    freeze = json.loads(require["macha_freeze"][0].read_text(encoding="utf-8"))
    return replay, sample_a, provenance, collision, freeze


def bind_execution(args):
    g7_path = Path(__file__).resolve()
    g6_path = g7_path.with_name("materialize_td_relational_corrected_sampleA_v2.py")
    auth = common.load_runtime_authorization(
        Path(args.value_authorization), preflight_path=Path(args.preflight_result),
        mapping_path=Path(args.mapping_receipt), g6_path=g6_path, g7_path=g7_path,
    )
    preflight, mapping = common.load_bound_preflight(
        Path(args.preflight_result), Path(args.mapping_receipt),
        expected_preflight_sha=auth["preflight_result_sha256"],
        expected_mapping_sha=auth["mapping_receipt_sha256"],
    )
    return auth, preflight, mapping, g6_path, g7_path


def expected_authority_trace(args, auth: dict, g6_path: Path, g7_path: Path) -> dict:
    return {
        "preflight_result_sha256": common.sha256_file(Path(args.preflight_result)),
        "mapping_receipt_sha256": common.sha256_file(Path(args.mapping_receipt)),
        "authorization_sha256": common.sha256_file(Path(args.value_authorization)),
        **common.code_identity(g6_path, g7_path),
        "authorization_schema": auth["schema"],
        "authorization_token": auth["authorization"],
    }


def load_g6_pass_receipt(path: Path, expected_trace: dict) -> dict:
    path = Path(path)
    if not path.is_file():
        raise RuntimeError(f"missing required G6 PASS receipt: {path}")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if receipt.get("schema") != G6_RECEIPT_SCHEMA or receipt.get("status") != G6_PASS:
        raise RuntimeError(f"G7 requires G6 V2 PASS before execution: {receipt.get('schema')} / {receipt.get('status')}")
    if receipt.get("authority_trace") != expected_trace:
        raise RuntimeError("G6 PASS receipt is not bound to the same preflight/authorization/code bytes")
    for key in ("biological_replay_authorized", "target_selection_authorized", "td60_authorized", "training_authorized"):
        if receipt.get(key) is not False:
            raise RuntimeError(f"G6 PASS receipt must keep {key}=false")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-result", required=True)
    parser.add_argument("--mapping-receipt", required=True)
    parser.add_argument("--value-authorization", required=True)
    parser.add_argument("--g6-receipt", required=True)
    parser.add_argument("--replay-manifest", required=True)
    parser.add_argument("--sample-freeze", required=True)
    parser.add_argument("--provenance", required=True)
    parser.add_argument("--collision-ledger", required=True)
    parser.add_argument("--macha-freeze", required=True)
    parser.add_argument("--s174-cache-root", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        raise RuntimeError(f"immutable G7 receipt already exists: {out}")

    auth, _, _, g6_path, g7_path = bind_execution(args)
    authority_trace = expected_authority_trace(args, auth, g6_path, g7_path)
    load_g6_pass_receipt(Path(args.g6_receipt), authority_trace)

    g1b_result, g1b_freeze, g1b_result_sha256, g1b_freeze_sha256 = load_g1b_authority_from_pass_commit(g7_path)
    verified_shards, shard_hashes = verify_cache_hashes(Path(args.s174_cache_root), g1b_freeze)

    replay, sample_a, provenance, collision, freeze = load_inputs(args)
    replay_addresses = set(replay.molecular_address_index.astype(int))
    matrices = {str(item["matrix_id"]): item for item in freeze["matrices"]}
    source_root = Path(args.source_root)

    from scipy import sparse
    import h5py

    total_overlap = total_checked = total_mismatches = 0
    per_matrix: list[dict] = []
    verified_physical_sources: dict[str, str] = {}

    for mid0, group in sample_a[~sample_a.source.eq("NPH52")].groupby("matrix_id", sort=True):
        mid = str(mid0)
        matrix_rec = matrices.get(mid)
        if matrix_rec is None:
            raise RuntimeError(f"matrix absent from Macha freeze: {mid}")
        study = str(group.source.iloc[0])
        stem = str(matrix_rec["stem"])
        meta_path = Path(args.s174_cache_root) / f"{stem}.meta.npz"
        counts_path = Path(args.s174_cache_root) / f"{stem}.counts.npz"

        with np.load(meta_path, allow_pickle=False) as meta:
            s174_cells = meta["cell_id"].astype(str)
        where_s174 = {cell: index for index, cell in enumerate(s174_cells)}
        overlap = group[group.cell_id.astype(str).isin(where_s174)].copy()
        if overlap.empty:
            per_matrix.append({"matrix_id": mid, "study": study, "overlap_cells": 0,
                               "checked_entries": 0, "mismatches": 0,
                               "s174_count_values_opened": False, "physical_h5ad_values_opened": False})
            continue

        with np.load(counts_path, allow_pickle=False) as payload:
            validate_s174_payload(payload["data"], payload["indices"], payload["indptr"], payload["shape"])
            s174_matrix = sparse.csr_matrix((payload["data"], payload["indices"], payload["indptr"]),
                                            shape=tuple(payload["shape"]))

        fprov = provenance[provenance.source_dataset_id.astype(str).eq(FAMILY[study])]
        if fprov.source_exact_ensembl_id.astype(str).duplicated().any():
            raise RuntimeError(f"nonunique provenance identifier: {study}")
        id_to_address = dict(zip(fprov.source_exact_ensembl_id.astype(str), fprov.molecular_address_index.astype(int)))
        ledger_ids = set(collision.loc[collision.matrix_id.astype(str).eq(mid), "source_exact_ensembl_id"].astype(str))
        physical_path = source_root / str(matrix_rec["source"]["path"])

        verified_physical_sources[mid] = common.verify_source_file(physical_path, matrix_rec["source"])
        with h5py.File(physical_path, "r") as handle:
            var_ids = h5_strings(handle["var"], VAR_ID_COLUMN[study])
            col_to_address, _ = identifier_map(var_ids, id_to_address, ledger_ids)
            obs = h5_strings(handle["obs"], "exp_component_name")
            node = handle[str(matrix_rec["slot"])]
            indptr = node["indptr"]
            mismatches = checked = 0
            for row in overlap.itertuples(index=False):
                local_row = int(row.local_row)
                if local_row < 0 or local_row >= len(obs) or str(obs[local_row]) != str(row.cell_id):
                    raise RuntimeError(f"G7 raw row identity drift: {mid} {row.cell_id}")
                lo, hi = int(indptr[local_row]), int(indptr[local_row + 1])
                current, _ = corrected_row(node["indices"][lo:hi], node["data"][lo:hi], col_to_address, replay_addresses)
                reference = sparse_row_dict(s174_matrix, where_s174[str(row.cell_id)], replay_addresses)
                comparison = compare_rows(current, reference, replay_addresses)
                checked += comparison["checked"]
                mismatches += comparison["mismatches"]

        total_overlap += len(overlap)
        total_checked += checked
        total_mismatches += mismatches
        per_matrix.append({"matrix_id": mid, "study": study, "overlap_cells": int(len(overlap)),
                           "checked_entries": int(checked), "mismatches": int(mismatches),
                           "physical_source_sha256_verified": verified_physical_sources[mid],
                           "s174_count_values_opened": True, "physical_h5ad_values_opened": True})

    status = overlap_status(total_overlap, total_mismatches)
    receipt = {
        "schema": G7_SCHEMA,
        "status": status,
        "scope": "all natural HVS/SEA Sample-A x S174 cell overlaps; all exact 9216 replay addresses; raw integer counts; zero tolerance",
        "macha_g1b_pass_commit": G1B_PASS_COMMIT,
        "macha_g1b_result_git_content_sha256": g1b_result_sha256,
        "macha_g1b_result_schema": g1b_result["schema"],
        "macha_g1b_requirements_all_pass": True,
        "macha_g1b_freeze_git_content_sha256": g1b_freeze_sha256,
        "macha_g1b_freeze_sha256": G1B_FREEZE_SHA256,
        "s174_verified_shards": int(verified_shards),
        "s174_verified_shard_sha256": shard_hashes,
        "verified_physical_h5ad_sha256": verified_physical_sources,
        "natural_overlap_cells": int(total_overlap),
        "checked_cell_address_entries": int(total_checked),
        "mismatches": int(total_mismatches),
        "per_matrix": per_matrix,
        "authority_trace": {**authority_trace, "g6_receipt_sha256": common.sha256_file(Path(args.g6_receipt))},
        "no_overlap_is_not_pass": total_overlap == 0,
        "biological_replay_authorized": False,
        "target_selection_authorized": False,
        "td60_authorized": False,
        "training_authorized": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "overlap_cells": int(total_overlap), "mismatches": int(total_mismatches)}, sort_keys=True))
    return exit_code_for_status(status)


if __name__ == "__main__":
    raise SystemExit(main())
