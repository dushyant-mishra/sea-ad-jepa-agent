#!/usr/bin/env python3
"""Guarded corrected-value materializer for the historical TD56->TD59 Sample-A replay.

THIS FILE DOES NOT AUTHORIZE A VALUE READ.
It refuses to run unless both are present:
  1. the exact PASS value-blind preflight receipt; and
  2. a separately created value-read authorization with the exact frozen scope.

When authorized, it creates one immutable 25,000 x 41,238 sparse CSR cache with values stored only
for the exact 9,216 historical replay addresses. HVS and SEA-AD are re-read from physical H5AD rows
through the corrected identifier join. NPH52 values are copied only from the authenticated historical
50K CSR because NPH52 did not share the HVS/SEA positional-axis defect. No target/replay verdict is
computed here.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

VALUE_AUTH_SCHEMA = "JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V1"
VALUE_AUTHORIZATION = "AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_ONLY"
VALUE_SCOPE = (
    "TRAIN-only historical A_NATURAL_MIXTURE 25000 cells; exact frozen 9216 TD56-TD59 addresses; "
    "HVS/SEA corrected physical-ID reads; NPH52 historical clean-path pass-through; G6/G7 only; "
    "no target selection, TD60, model fitting, EMA, training, TEST, DEV/SEALED, pathology, or external biology"
)
PREFLIGHT_PASS = "PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND"
EXPECTED_REPLAY_MANIFEST_SHA = "4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660"
EXPECTED_SAMPLE_FREEZE_SHA = "79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6"
EXPECTED_PROVENANCE_SHA = "df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51"
EXPECTED_COLLISION_SHA = "f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722"
EXPECTED_MACHA_FREEZE_SHA = "240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c"
N_ADDR = 41_238
N_SAMPLE_A = 25_000
N_REPLAY = 9_216
SOURCE_COUNTS = {"HVS": 1_129, "NPH52": 1_310, "SEA_AD": 22_561}
FAMILY = {"HVS": "HVS_COMMON", "SEA_AD": "SEA_AD_COMMON"}
VAR_ID_COLUMN = {"HVS": "_index", "SEA_AD": "gene_ids"}
HIST_CSR_SHA = {
    "data.npy": "0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e",
    "indices.npy": "f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771",
    "indptr.npy": "58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1",
    "shape.npy": "5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb",
}
TD50_SHA = {
    "HVS": "d6d30cb5ef791fdaaa6f751ee6d802f8e64e062ab641a48194dfc9b596609aeb",
    "NPH52": "9de0c199414db0705d25cce18cb5007915bcf527c245ed039e2f966437c790fe",
    "SEA_AD": "ab4fa37a2596de609b4245e82dec0ba7e4a43f95d03421acd46c5814eaaa57d4",
}


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_value_authority(path: Path) -> dict:
    rec = json.loads(Path(path).read_text(encoding="utf-8"))
    if rec.get("schema") != VALUE_AUTH_SCHEMA:
        raise RuntimeError("value authorization schema mismatch")
    if rec.get("authorization") != VALUE_AUTHORIZATION:
        raise RuntimeError("value authorization token mismatch")
    if rec.get("scope") != VALUE_SCOPE:
        raise RuntimeError("value authorization scope mismatch")
    if rec.get("training_authorized") is not False:
        raise RuntimeError("value authorization must explicitly keep training OFF")
    return rec


def load_preflight_pass(path: Path) -> dict:
    rec = json.loads(Path(path).read_text(encoding="utf-8"))
    if rec.get("status") != PREFLIGHT_PASS:
        raise RuntimeError(f"value-blind preflight is not PASS: {rec.get('status')}")
    return rec


def assert_empty_output(out: Path) -> None:
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"immutable output namespace is not empty; refusing overwrite: {out}")


def h5_strings(group, name: str) -> np.ndarray:
    import h5py
    if name == "_index":
        name = group.attrs.get("_index", "_index")
        name = name.decode() if isinstance(name, bytes) else str(name)
    obj = group[name]
    vals = obj["categories"][:][obj["codes"][:]] if isinstance(obj, h5py.Group) else obj[:]
    return np.asarray([v.decode() if isinstance(v, bytes) else str(v) for v in vals], dtype=object)


def identifier_map(var_ids, id_to_address: dict[str, int], ledger_ids: set[str]):
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


def corrected_row(indices, values, col_to_address: dict[int, int], replay_addresses: set[int]):
    """Return replay-address raw counts and whole-physical-row library total.

    Library total is intentionally accumulated before mapping/filtering.
    """
    row: dict[int, int] = {}
    total = 0
    for j0, v0 in zip(indices, values):
        j, v = int(j0), int(round(float(v0)))
        if v < 0:
            raise RuntimeError("negative raw count")
        total += v
        a = col_to_address.get(j)
        if a is not None and a in replay_addresses and v:
            if a in row:
                raise RuntimeError(f"noninjective mapped replay address encountered at value read: {a}")
            row[a] = v
    return row, total


def read_td50(zip_path: Path) -> dict[str, dict[str, np.ndarray]]:
    out = {}
    with zipfile.ZipFile(zip_path) as z:
        for source in SOURCE_COUNTS:
            name = next((n for n in z.namelist() if n.endswith(f"td50_{source}.npz")), None)
            if name is None:
                raise RuntimeError(f"missing td50_{source}.npz in {zip_path}")
            raw = z.read(name)
            if sha256_bytes(raw) != TD50_SHA[source]:
                raise RuntimeError(f"td50 {source} SHA mismatch")
            with np.load(io.BytesIO(raw), allow_pickle=False) as a:
                out[source] = {k: a[k].copy() for k in ("global_row", "source_library", "detected")}
    return out


def sentinel_maps(td50):
    lib, det = {}, {}
    for source, z in td50.items():
        for g, x, d in zip(z["global_row"].astype(int), z["source_library"].astype(np.int64), z["detected"].astype(np.int64)):
            lib[int(g)] = int(x)
            det[int(g)] = int(d)
    if len(lib) != N_SAMPLE_A or len(det) != N_SAMPLE_A:
        raise RuntimeError("TD50 sentinel geometry mismatch")
    return lib, det


def verify_historical_csr(root: Path):
    root = Path(root)
    for name, expected in HIST_CSR_SHA.items():
        p = root / name
        if not p.is_file() or sha256_file(p) != expected:
            raise RuntimeError(f"historical CSR authority mismatch: {p}")
    data = np.load(root / "data.npy", mmap_mode="r")
    indices = np.load(root / "indices.npy", mmap_mode="r")
    indptr = np.load(root / "indptr.npy", mmap_mode="r")
    shape = tuple(np.load(root / "shape.npy"))
    if shape != (50_000, N_ADDR):
        raise RuntimeError(f"historical CSR shape mismatch: {shape}")
    return data, indices, indptr, shape


def nph_historical_row(global_row: int, data, indices, indptr, replay_addresses: set[int]):
    lo, hi = int(indptr[global_row]), int(indptr[global_row + 1])
    row = {}
    for a0, v0 in zip(indices[lo:hi], data[lo:hi]):
        a = int(a0)
        if a in replay_addresses and float(v0) != 0.0:
            # Historical NPH values are already normalized values, not raw counts.
            row[a] = float(v0)
    return row


def load_inputs(args):
    require = {
        "replay_manifest": (Path(args.replay_manifest), EXPECTED_REPLAY_MANIFEST_SHA),
        "sample_freeze": (Path(args.sample_freeze), EXPECTED_SAMPLE_FREEZE_SHA),
        "provenance": (Path(args.provenance), EXPECTED_PROVENANCE_SHA),
        "collision_ledger": (Path(args.collision_ledger), EXPECTED_COLLISION_SHA),
        "macha_freeze": (Path(args.macha_freeze), EXPECTED_MACHA_FREEZE_SHA),
    }
    for label, (p, expected) in require.items():
        if not p.is_file() or sha256_file(p) != expected:
            raise RuntimeError(f"authority mismatch: {label}: {p}")
    replay = pd.read_csv(require["replay_manifest"][0])
    if len(replay) != N_REPLAY or replay.molecular_address_index.nunique() != N_REPLAY:
        raise RuntimeError("replay manifest geometry mismatch")
    sample = pd.read_csv(require["sample_freeze"][0], dtype=str)
    sample_a = sample[sample["sample"].astype(str).eq("A")].copy().sort_values("sample_row")
    if len(sample_a) != N_SAMPLE_A or sample_a.source.value_counts().to_dict() != SOURCE_COUNTS:
        raise RuntimeError("Sample-A geometry mismatch")
    if sample_a.sample_row.astype(int).tolist() != list(range(N_SAMPLE_A)):
        raise RuntimeError("Sample-A row order mismatch")
    prov = pd.read_csv(require["provenance"][0], low_memory=False)
    collision = pd.read_csv(require["collision_ledger"][0], low_memory=False)
    freeze = json.loads(require["macha_freeze"][0].read_text(encoding="utf-8"))
    return replay, sample_a, prov, collision, freeze


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight-result", required=True)
    ap.add_argument("--value-authorization", required=True)
    ap.add_argument("--replay-manifest", required=True)
    ap.add_argument("--sample-freeze", required=True)
    ap.add_argument("--provenance", required=True)
    ap.add_argument("--collision-ledger", required=True)
    ap.add_argument("--macha-freeze", required=True)
    ap.add_argument("--td-artifacts-zip", required=True)
    ap.add_argument("--historical-csr-root", required=True,
                    help="Authenticated old 50K CSR arrays; used only for NPH52 pass-through")
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    load_preflight_pass(Path(args.preflight_result))
    auth = load_value_authority(Path(args.value_authorization))
    out = Path(args.output_dir)
    assert_empty_output(out)
    out.mkdir(parents=True, exist_ok=False) if not out.exists() else None

    replay, sample_a, prov, collision, freeze = load_inputs(args)
    replay_addresses = set(replay.molecular_address_index.astype(int))
    source_root = Path(args.source_root)
    td50 = read_td50(Path(args.td_artifacts_zip))
    historical_library, historical_detected = sentinel_maps(td50)
    hdata, hindices, hindptr, _ = verify_historical_csr(Path(args.historical_csr_root))

    matrices = {str(m["matrix_id"]): m for m in freeze["matrices"]}
    rows_out, cols_out, vals_out = [], [], []
    source_library_corrected = np.zeros(N_SAMPLE_A, dtype=np.int64)
    detected_corrected = np.full(N_SAMPLE_A, -1, dtype=np.int64)
    detected_historical = np.zeros(N_SAMPLE_A, dtype=np.int64)
    source = sample_a.source.astype(str).to_numpy()
    donor = sample_a.donor_id.astype(str).to_numpy()
    operator = sample_a.operator_index.astype(int).to_numpy()
    global_row = sample_a.global_row.astype(int).to_numpy()
    cell_id = sample_a.cell_id.astype(str).to_numpy()
    g6_mismatches = []
    mapping_diag = []

    # HVS/SEA corrected physical reads.
    import h5py
    for mid, grp in sample_a[~sample_a.source.eq("NPH52")].groupby("matrix_id", sort=True):
        study = str(grp.source.iloc[0])
        m = matrices.get(str(mid))
        if m is None:
            raise RuntimeError(f"matrix absent from Macha freeze: {mid}")
        fprov = prov[prov.source_dataset_id.astype(str).eq(FAMILY[study])]
        if fprov.source_exact_ensembl_id.astype(str).duplicated().any():
            raise RuntimeError(f"nonunique provenance identifier: {study}")
        id_to_address = dict(zip(fprov.source_exact_ensembl_id.astype(str), fprov.molecular_address_index.astype(int)))
        ledger_ids = set(collision.loc[collision.matrix_id.astype(str).eq(str(mid)), "source_exact_ensembl_id"].astype(str))
        src = source_root / str(m["source"]["path"])
        if not src.is_file() or src.stat().st_size != int(m["source"]["bytes"]):
            raise RuntimeError(f"source file missing/size mismatch: {src}")
        with h5py.File(src, "r") as h:
            var_ids = h5_strings(h["var"], VAR_ID_COLUMN[study])
            col_to_address, excluded = identifier_map(var_ids, id_to_address, ledger_ids)
            obs = h5_strings(h["obs"], "exp_component_name")
            node = h[str(m["slot"])]
            ip = node["indptr"]
            for row in grp.itertuples(index=False):
                srow = int(row.sample_row); er = int(row.local_row)
                if er < 0 or er >= len(obs) or str(obs[er]) != str(row.cell_id):
                    raise RuntimeError(f"cell row drift after preflight: {mid} row {er}")
                lo, hi = int(ip[er]), int(ip[er + 1])
                phys_idx = node["indices"][lo:hi]
                phys_val = node["data"][lo:hi]
                raw_replay, total = corrected_row(phys_idx, phys_val, col_to_address, replay_addresses)
                if total != historical_library[int(row.global_row)]:
                    g6_mismatches.append({"sample_row": srow, "global_row": int(row.global_row), "matrix_id": str(mid),
                                          "historical": historical_library[int(row.global_row)], "corrected": total})
                source_library_corrected[srow] = total
                # Diagnostic only: number of nonzero mapped canonical addresses under corrected collision policy.
                det = 0
                for j0, v0 in zip(phys_idx, phys_val):
                    if float(v0) != 0.0 and int(j0) in col_to_address:
                        det += 1
                detected_corrected[srow] = det
                detected_historical[srow] = historical_detected[int(row.global_row)]
                for a, raw in raw_replay.items():
                    norm = float(np.log1p(raw * 10000.0 / total)) if total > 0 else 0.0
                    if norm:
                        rows_out.append(srow); cols_out.append(a); vals_out.append(norm)
        mapping_diag.append({"matrix_id": str(mid), "study": study, "excluded": dict(Counter(excluded.values()))})

    if g6_mismatches:
        receipt = {"schema": "JEPA_TD_RELATIONAL_G6_RECEIPT_V1", "status": "STOP_TD_G6_SOURCE_LIBRARY_MISMATCH",
                   "mismatch_count": len(g6_mismatches), "preview": g6_mismatches[:50], "training_authorized": False}
        (out / "G6_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise RuntimeError(f"G6 source-library mismatch in {len(g6_mismatches)} rows")

    # NPH52: preserve authenticated historical 50K normalized values for the unaffected source.
    for row in sample_a[sample_a.source.eq("NPH52")].itertuples(index=False):
        srow = int(row.sample_row); grow = int(row.global_row)
        old = nph_historical_row(grow, hdata, hindices, hindptr, replay_addresses)
        source_library_corrected[srow] = historical_library[grow]
        detected_historical[srow] = historical_detected[grow]
        detected_corrected[srow] = historical_detected[grow]  # pass-through diagnostic, not a gate
        for a, v in old.items():
            rows_out.append(srow); cols_out.append(a); vals_out.append(v)

    if np.any(source_library_corrected <= 0) or np.any(detected_corrected < 0):
        raise RuntimeError("incomplete Sample-A materialization metadata")

    from scipy import sparse
    X = sparse.csr_matrix((np.asarray(vals_out, np.float32), (np.asarray(rows_out), np.asarray(cols_out))),
                          shape=(N_SAMPLE_A, N_ADDR), dtype=np.float32)
    X.sort_indices()
    counts_path = out / "TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES.npz"
    sparse.save_npz(counts_path, X, compressed=True)
    meta_path = out / "TD_RELATIONAL_CORRECTED_SAMPLE_A_META.npz"
    np.savez_compressed(meta_path, source=source, donor=donor, operator=operator, global_row=global_row, cell_id=cell_id,
                        source_library=source_library_corrected, detected_historical=detected_historical,
                        detected_corrected=detected_corrected)

    g6 = {
        "schema": "JEPA_TD_RELATIONAL_G6_RECEIPT_V1",
        "status": "PASS_TD_G6_SOURCE_LIBRARY_EXACT",
        "rows": N_SAMPLE_A,
        "source_library_exact_rows": N_SAMPLE_A,
        "historical_detected_is_diagnostic_only": True,
        "detected_changed_rows": int(np.sum(detected_historical != detected_corrected)),
        "training_authorized": False,
    }
    (out / "G6_RECEIPT.json").write_text(json.dumps(g6, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "schema": "JEPA_TD_RELATIONAL_CORRECTED_SAMPLE_A_CACHE_V1",
        "status": "MATERIALIZED_G6_PASS__G7_PENDING",
        "authorization": auth,
        "shape": [N_SAMPLE_A, N_ADDR],
        "stored_replay_addresses": N_REPLAY,
        "nnz": int(X.nnz),
        "values_sha256": sha256_file(counts_path),
        "meta_sha256": sha256_file(meta_path),
        "mapping_diagnostics": mapping_diag,
        "g6_receipt": "G6_RECEIPT.json",
        "g7_status": "PENDING_SEPARATE_CROSSCHECK",
        "replay_authorized": False,
        "training_authorized": False,
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "nnz": manifest["nnz"], "output": str(out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
