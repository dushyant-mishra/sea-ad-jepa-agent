#!/usr/bin/env python3
"""Value-blind preflight for the corrected TD56->TD59 relational replay.

Reads only file bytes plus identity/support metadata from H5AD files (var/obs). It never opens
raw/X or X count arrays. The scientific question is deliberately narrow: do the exact 9,216
historical TD addresses and exact 25,000 Sample-A cells remain resolvable under the already-audited
S174 identifier join, with the physical H5AD bytes still matching the frozen S174 authority?
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

EXPECTED_REPLAY_MANIFEST_SHA = "4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660"
EXPECTED_SAMPLE_FREEZE_SHA = "79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6"
EXPECTED_PROVENANCE_SHA = "df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51"
EXPECTED_COLLISION_SHA = "f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722"
EXPECTED_MACHA_FREEZE_SHA = "240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c"
N_REPLAY = 9_216
N_SAMPLE_A = 25_000
SOURCE_COUNTS = {"HVS": 1_129, "NPH52": 1_310, "SEA_AD": 22_561}
VAR_ID_COLUMN = {"HVS": "_index", "SEA_AD": "gene_ids"}
FAMILY = {"HVS": "HVS_COMMON", "SEA_AD": "SEA_AD_COMMON"}


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def verify_source_file(path: Path, source_rec: dict) -> str:
    path = Path(path)
    if not path.is_file():
        raise RuntimeError(f"source file missing: {path}")
    expected_size = int(source_rec["bytes"])
    if path.stat().st_size != expected_size:
        raise RuntimeError(f"source size mismatch: {path.stat().st_size} != {expected_size}: {path}")
    actual = sha256_file(path)
    expected = str(source_rec["sha256"])
    if actual != expected:
        raise RuntimeError(f"source SHA mismatch: {actual} != {expected}: {path}")
    return actual


def h5_strings(group, name: str) -> np.ndarray:
    """Read an AnnData categorical/plain string vector without touching expression arrays."""
    import h5py

    if name == "_index":
        name = group.attrs.get("_index", "_index")
        name = name.decode() if isinstance(name, bytes) else str(name)
    obj = group[name]
    vals = obj["categories"][:][obj["codes"][:]] if isinstance(obj, h5py.Group) else obj[:]
    return np.asarray([v.decode() if isinstance(v, bytes) else str(v) for v in vals], dtype=object)


def identifier_map(var_ids, id_to_address: dict[str, int], ledger_ids: set[str]):
    """Same pure policy as S174: identifier join, collision exclusion, never summation."""
    reach: dict[int, list[int]] = {}
    excluded: dict[int, str] = {}
    for j, gid0 in enumerate(var_ids):
        gid = str(gid0)
        if gid in ledger_ids:
            excluded[j] = "LEDGER_COLLISION"
            continue
        address = id_to_address.get(gid)
        if address is None:
            excluded[j] = "UNMAPPED"
            continue
        reach.setdefault(int(address), []).append(j)
    col_to_address = {}
    for address, cols in reach.items():
        if len(cols) == 1:
            col_to_address[cols[0]] = address
        else:
            for j in cols:
                excluded[j] = "JOIN_COLLISION"
    return col_to_address, excluded


def replay_address_coverage(var_ids, id_to_address, ledger_ids, replay_addresses: set[int]):
    col_to_address, excluded = identifier_map(var_ids, id_to_address, ledger_ids)
    by_addr = Counter(col_to_address.values())
    missing = sorted(a for a in replay_addresses if by_addr[a] == 0)
    noninjective = sorted(a for a in replay_addresses if by_addr[a] > 1)
    resolved = len(replay_addresses) - len(missing) - len(noninjective)
    return {
        "resolved": resolved,
        "missing": missing,
        "noninjective": noninjective,
        "excluded_columns": dict(Counter(excluded.values())),
        "mapped_columns": len(col_to_address),
    }


def load_authorities(args):
    replay = Path(args.replay_manifest)
    sample = Path(args.sample_freeze)
    prov = Path(args.provenance)
    coll = Path(args.collision_ledger)
    mf = Path(args.macha_freeze)
    checks = {
        "replay_manifest_sha": sha256_file(replay) == EXPECTED_REPLAY_MANIFEST_SHA,
        "sample_freeze_sha": sha256_file(sample) == EXPECTED_SAMPLE_FREEZE_SHA,
        "provenance_sha": sha256_file(prov) == EXPECTED_PROVENANCE_SHA,
        "collision_ledger_sha": sha256_file(coll) == EXPECTED_COLLISION_SHA,
        "macha_freeze_sha": sha256_file(mf) == EXPECTED_MACHA_FREEZE_SHA,
    }
    if not all(checks.values()):
        raise RuntimeError(f"authority SHA mismatch: {checks}")
    r = pd.read_csv(replay)
    s = pd.read_csv(sample, dtype=str)
    p = pd.read_csv(prov, low_memory=False)
    c = pd.read_csv(coll, low_memory=False)
    freeze = json.loads(mf.read_text(encoding="utf-8"))
    if len(r) != N_REPLAY or r.molecular_address_index.nunique() != N_REPLAY:
        raise RuntimeError("replay manifest geometry mismatch")
    a = s[s["sample"].astype(str).eq("A")].copy()
    if len(a) != N_SAMPLE_A:
        raise RuntimeError("Sample-A geometry mismatch")
    got = a.source.value_counts().to_dict()
    if got != SOURCE_COUNTS:
        raise RuntimeError(f"Sample-A source counts mismatch: {got}")
    return checks, r, a, p, c, freeze


def audit(args) -> dict:
    import h5py

    checks, replay, sample_a, prov, collision, freeze = load_authorities(args)
    replay_addresses = set(replay.molecular_address_index.astype(int))
    matrices = {m["matrix_id"]: m for m in freeze["matrices"]}
    details = []
    root = Path(args.source_root)
    all_mapping = True
    all_cells = True
    all_sources = True

    for mid, rows in sample_a[~sample_a.source.eq("NPH52")].groupby("matrix_id", sort=True):
        study = str(rows.source.iloc[0])
        if mid not in matrices:
            details.append({"matrix_id": mid, "study": study, "status": "MISSING_FROM_MACHA_FREEZE"})
            all_sources = False
            continue
        m = matrices[mid]
        source_path = root / str(m["source"]["path"])
        try:
            verified_source_sha = verify_source_file(source_path, m["source"])
        except RuntimeError as e:
            details.append({"matrix_id": str(mid), "study": study, "status": "SOURCE_AUTHORITY_MISMATCH", "error": str(e)})
            all_sources = False
            continue

        family = FAMILY[study]
        fprov = prov[prov.source_dataset_id.astype(str).eq(family)]
        if fprov.source_exact_ensembl_id.astype(str).duplicated().any():
            raise RuntimeError(f"nonunique provenance identifier in {family}")
        id_to_address = dict(zip(fprov.source_exact_ensembl_id.astype(str), fprov.molecular_address_index.astype(int)))
        ledger_ids = set(collision.loc[collision.matrix_id.astype(str).eq(str(mid)), "source_exact_ensembl_id"].astype(str))

        with h5py.File(source_path, "r") as h:
            # VALUE-BLIND BOUNDARY: only var and obs are opened after byte-level source authentication.
            var_ids = h5_strings(h["var"], VAR_ID_COLUMN[study])
            obs_ids = h5_strings(h["obs"], "exp_component_name")
        cov = replay_address_coverage(var_ids, id_to_address, ledger_ids, replay_addresses)
        mapping_ok = cov["resolved"] == N_REPLAY and not cov["missing"] and not cov["noninjective"]
        all_mapping &= mapping_ok

        local_rows = rows.local_row.astype(int).to_numpy()
        cell_ids = rows.cell_id.astype(str).to_numpy()
        in_bounds = bool(np.all((local_rows >= 0) & (local_rows < len(obs_ids))))
        cell_exact = in_bounds and bool(np.array_equal(obs_ids[local_rows].astype(str), cell_ids))
        all_cells &= cell_exact
        details.append({
            "matrix_id": str(mid),
            "study": study,
            "status": "PASS" if mapping_ok and cell_exact else "FAIL",
            "sample_A_cells": int(len(rows)),
            "var_features": int(len(var_ids)),
            "replay_addresses_resolved": int(cov["resolved"]),
            "replay_addresses_missing_n": len(cov["missing"]),
            "replay_addresses_noninjective_n": len(cov["noninjective"]),
            "missing_preview": cov["missing"][:20],
            "noninjective_preview": cov["noninjective"][:20],
            "excluded_columns": cov["excluded_columns"],
            "sample_A_cell_local_row_exact": cell_exact,
            "source_path": str(m["source"]["path"]),
            "source_sha256_verified": verified_source_sha,
        })

    expected_h5 = set(sample_a.loc[~sample_a.source.eq("NPH52"), "matrix_id"].astype(str))
    authenticated_h5 = {d["matrix_id"] for d in details if d.get("source_sha256_verified")}
    checks.update({
        "all_sample_A_h5_matrices_present": authenticated_h5 == expected_h5,
        "all_35_h5_source_sha256_verified": authenticated_h5 == expected_h5 and len(authenticated_h5) == 35,
        "all_9216_addresses_one_to_one": bool(all_mapping),
        "all_sample_A_h5_cell_rows_exact": bool(all_cells),
        "source_files_exactly_hash_bound": bool(all_sources),
        "count_arrays_never_opened_by_design": True,
    })
    status = "PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND" if all(checks.values()) else "FAIL_TD_RELATIONAL_MAPPING_PREFLIGHT"
    return {
        "schema": "JEPA_TD_RELATIONAL_MAPPING_PREFLIGHT_V2",
        "status": status,
        "scope": "value-blind HVS/SEA-AD source-byte authentication, mapping and Sample-A row identity only; no count arrays read",
        "inherited_authority": {
            "macha_branch": "claude/s174-train-cache-rebuild-20261007",
            "macha_freeze_commit": "cf4d4708af68d32c8c1ec73b1a4b09294b2df6ef",
            "macha_g1b_pass_commit": "4ab8e2101f2e595d9a97df05517d6e672768ecec",
            "macha_ci_confirmed_code": "46d8eaa8fa23cd60762a8a90c55b84e8d86364b2",
        },
        "checks": checks,
        "matrices": details,
        "nph52": "not reread here; separate NPH identity path, retained as later consistency control",
        "training_authorized": False,
        "real_value_replay_authorized_by_this_receipt": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay-manifest", required=True)
    ap.add_argument("--sample-freeze", required=True)
    ap.add_argument("--provenance", required=True)
    ap.add_argument("--collision-ledger", required=True)
    ap.add_argument("--macha-freeze", required=True)
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rec = audit(args)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": rec["status"], "checks": rec["checks"]}, sort_keys=True))
    return 0 if rec["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
