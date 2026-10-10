#!/usr/bin/env python3
"""G7 exact cross-check for corrected TD Sample-A reads against Macha's G1b-authorized S174 cache.

THIS SCRIPT DOES NOT AUTHORIZE A VALUE READ. It requires the same exact-scope value authorization
as the corrected Sample-A materializer and an exact PASS value-blind preflight receipt.

It uses every natural HVS/SEA-AD cell-ID overlap between historical Sample-A and the frozen S174
cache. It never selects extra cells to create overlap. Raw integer counts on every frozen 9,216
address are compared with zero tolerance. If there is no natural overlap, the result is explicitly
NOT_ESTIMABLE and returns a non-success process exit.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

G1B_FREEZE_SHA256 = "0513421e45865f290bddf8b0be56d64c7d9c5297bf0150ea6b9df286514b5f8f"
G1B_PASS_COMMIT = "4ab8e2101f2e595d9a97df05517d6e672768ecec"


def _load_materializer():
    p = Path(__file__).resolve().with_name("materialize_td_relational_corrected_sampleA_v2.py")
    spec = importlib.util.spec_from_file_location("td_materializer_v2", p)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def raw_integer(v0) -> int:
    x = float(v0)
    if not (x >= 0.0):
        raise RuntimeError("negative or non-finite raw reference count")
    v = int(x)
    if float(v) != x:
        raise RuntimeError(f"non-integer value encountered in raw S174 reference count: {x!r}")
    return v


def compare_rows(current: dict[int, int], reference: dict[int, int], addresses: set[int]) -> dict[str, int]:
    mismatches = sum(current.get(a, 0) != reference.get(a, 0) for a in addresses)
    return {"checked": len(addresses), "mismatches": int(mismatches)}


def verify_cache_hashes(cache_root: Path, g1b_freeze: dict) -> int:
    shards = g1b_freeze.get("rebuilt_cache", {}).get("shards", {})
    if not shards:
        raise RuntimeError("G1b freeze contains no rebuilt cache shard authority")
    for stem, rec in shards.items():
        cp = Path(cache_root) / f"{stem}.counts.npz"
        mp = Path(cache_root) / f"{stem}.meta.npz"
        if not cp.is_file() or not mp.is_file():
            raise RuntimeError(f"S174 cache shard missing: {stem}")
        if sha256_file(cp) != rec["counts"] or sha256_file(mp) != rec["meta"]:
            raise RuntimeError(f"S174 G1b-authorized cache hash mismatch: {stem}")
    return len(shards)


def overlap_status(overlap_cells: int, mismatches: int) -> str:
    if overlap_cells == 0:
        return "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP"
    if mismatches:
        return "STOP_TD_G7_S174_CROSSCHECK_MISMATCH"
    return "PASS_TD_G7_S174_EXACT_OVERLAP"


def exit_code_for_status(status: str) -> int:
    return 0 if status == "PASS_TD_G7_S174_EXACT_OVERLAP" else 2


def sparse_row_dict(X, r: int, addresses: set[int]) -> dict[int, int]:
    row = X.getrow(r)
    out: dict[int, int] = {}
    for a0, v0 in zip(row.indices, row.data):
        a = int(a0)
        if a in addresses and float(v0) != 0.0:
            out[a] = raw_integer(v0)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight-result", required=True)
    ap.add_argument("--value-authorization", required=True)
    ap.add_argument("--replay-manifest", required=True)
    ap.add_argument("--sample-freeze", required=True)
    ap.add_argument("--provenance", required=True)
    ap.add_argument("--collision-ledger", required=True)
    ap.add_argument("--macha-freeze", required=True)
    ap.add_argument("--macha-g1b-freeze", required=True)
    ap.add_argument("--s174-cache-root", required=True)
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    M = _load_materializer()
    M.load_preflight_pass(Path(args.preflight_result))
    auth = M.load_value_authority(Path(args.value_authorization))
    if sha256_file(Path(args.macha_g1b_freeze)) != G1B_FREEZE_SHA256:
        raise RuntimeError("Macha G1b freeze SHA mismatch")
    g1b = json.loads(Path(args.macha_g1b_freeze).read_text(encoding="utf-8"))
    verified_shards = verify_cache_hashes(Path(args.s174_cache_root), g1b)

    class A:
        pass

    a = A()
    a.replay_manifest = args.replay_manifest
    a.sample_freeze = args.sample_freeze
    a.provenance = args.provenance
    a.collision_ledger = args.collision_ledger
    a.macha_freeze = args.macha_freeze
    replay, sample_a, prov, collision, freeze = M.load_inputs(a)
    replay_addresses = set(replay.molecular_address_index.astype(int))
    matrices = {str(m["matrix_id"]): m for m in freeze["matrices"]}
    source_root = Path(args.source_root)

    from scipy import sparse
    import h5py

    total_overlap = 0
    total_checked = 0
    total_mismatches = 0
    per_matrix = []

    for mid, grp in sample_a[~sample_a.source.eq("NPH52")].groupby("matrix_id", sort=True):
        m = matrices.get(str(mid))
        if m is None:
            raise RuntimeError(f"matrix absent from Macha freeze: {mid}")
        study, stem = str(grp.source.iloc[0]), str(m["stem"])
        meta_path = Path(args.s174_cache_root) / f"{stem}.meta.npz"
        counts_path = Path(args.s174_cache_root) / f"{stem}.counts.npz"
        meta = np.load(meta_path, allow_pickle=False)
        s174_cells = meta["cell_id"].astype(str)
        where_s174 = {c: i for i, c in enumerate(s174_cells)}
        overlap = grp[grp.cell_id.astype(str).isin(where_s174)].copy()
        if overlap.empty:
            per_matrix.append({"matrix_id": str(mid), "study": study, "overlap_cells": 0,
                               "checked_entries": 0, "mismatches": 0})
            continue

        z = np.load(counts_path, allow_pickle=False)
        Xs = sparse.csr_matrix((z["data"], z["indices"], z["indptr"]), shape=tuple(z["shape"]))
        fprov = prov[prov.source_dataset_id.astype(str).eq(M.FAMILY[study])]
        id_to_address = dict(zip(fprov.source_exact_ensembl_id.astype(str), fprov.molecular_address_index.astype(int)))
        ledger_ids = set(collision.loc[collision.matrix_id.astype(str).eq(str(mid)), "source_exact_ensembl_id"].astype(str))
        src = source_root / str(m["source"]["path"])
        with h5py.File(src, "r") as h:
            var_ids = M.h5_strings(h["var"], M.VAR_ID_COLUMN[study])
            col_to_address, _ = M.identifier_map(var_ids, id_to_address, ledger_ids)
            obs = M.h5_strings(h["obs"], "exp_component_name")
            node = h[str(m["slot"])]
            ip = node["indptr"]
            mm = 0
            checked = 0
            for row in overlap.itertuples(index=False):
                er = int(row.local_row)
                if str(obs[er]) != str(row.cell_id):
                    raise RuntimeError(f"G7 raw row identity drift: {mid} {row.cell_id}")
                lo, hi = int(ip[er]), int(ip[er + 1])
                current, _ = M.corrected_row(node["indices"][lo:hi], node["data"][lo:hi], col_to_address, replay_addresses)
                reference = sparse_row_dict(Xs, where_s174[str(row.cell_id)], replay_addresses)
                c = compare_rows(current, reference, replay_addresses)
                checked += c["checked"]
                mm += c["mismatches"]
            total_overlap += len(overlap)
            total_checked += checked
            total_mismatches += mm
            per_matrix.append({"matrix_id": str(mid), "study": study, "overlap_cells": int(len(overlap)),
                               "checked_entries": int(checked), "mismatches": int(mm)})

    status = overlap_status(total_overlap, total_mismatches)
    rec = {
        "schema": "JEPA_TD_RELATIONAL_G7_S174_OVERLAP_V2",
        "status": status,
        "scope": "all natural HVS/SEA Sample-A x S174 cell overlaps; all exact 9216 replay addresses; raw integer counts; zero tolerance",
        "materializer_entrypoint": "materialize_td_relational_corrected_sampleA_v2.py",
        "macha_g1b_pass_commit": G1B_PASS_COMMIT,
        "macha_g1b_freeze_sha256": G1B_FREEZE_SHA256,
        "s174_verified_shards": verified_shards,
        "natural_overlap_cells": int(total_overlap),
        "checked_cell_address_entries": int(total_checked),
        "mismatches": int(total_mismatches),
        "per_matrix": per_matrix,
        "authorization": auth,
        "no_overlap_is_not_pass": total_overlap == 0,
        "replay_authorized_by_this_receipt": False,
        "training_authorized": False,
    }
    out = Path(args.out)
    if out.exists():
        raise RuntimeError(f"immutable G7 receipt already exists: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "overlap_cells": total_overlap, "mismatches": total_mismatches}, sort_keys=True))
    return exit_code_for_status(status)


if __name__ == "__main__":
    raise SystemExit(main())
