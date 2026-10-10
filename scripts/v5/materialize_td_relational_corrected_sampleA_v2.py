#!/usr/bin/env python3
"""Standalone G6 V2 corrected Sample-A materializer candidate.

THIS FILE DOES NOT AUTHORIZE A VALUE READ.

Execution requires a separately created, exact V2 runtime authorization after a reviewed V3 G4/G5
PASS. Historical V1 G6 is not imported or delegated to. This entrypoint owns its authorization gate,
input custody, immediate H5AD source authentication, strict raw-count semantics and V2 receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


def _load_common():
    path = Path(__file__).resolve().with_name("td_relational_value_read_v2_common.py")
    spec = importlib.util.spec_from_file_location("td_value_v2_common", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


common = _load_common()

G6_RECEIPT_SCHEMA = "JEPA_TD_RELATIONAL_G6_RECEIPT_V2"
CACHE_SCHEMA = "JEPA_TD_RELATIONAL_CORRECTED_SAMPLE_A_CACHE_V2"
G6_PASS = "PASS_TD_G6_SOURCE_LIBRARY_EXACT"
G6_MISMATCH = "STOP_TD_G6_SOURCE_LIBRARY_MISMATCH"

EXPECTED_REPLAY_MANIFEST_SHA = common.EXPECTED_INPUT_HASHES["replay_manifest_sha256"]
EXPECTED_SAMPLE_FREEZE_SHA = common.EXPECTED_INPUT_HASHES["sample_freeze_sha256"]
EXPECTED_PROVENANCE_SHA = common.EXPECTED_INPUT_HASHES["provenance_sha256"]
EXPECTED_COLLISION_SHA = common.EXPECTED_INPUT_HASHES["collision_ledger_sha256"]
EXPECTED_MACHA_FREEZE_SHA = common.EXPECTED_INPUT_HASHES["macha_freeze_sha256"]
EXPECTED_TD_ARTIFACTS_SHA = common.EXPECTED_INPUT_HASHES["td_artifacts_zip_sha256"]

N_ADDR = 41_238
N_SAMPLE_A = 25_000
N_REPLAY = 9_216
SAMPLE_A_LABEL = "A_NATURAL_MIXTURE"
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
INPUT_AUTHORITY_HASHES = {
    **common.EXPECTED_INPUT_HASHES,
    "historical_csr_sha256": dict(HIST_CSR_SHA),
    "td50_member_sha256": dict(TD50_SHA),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assert_empty_output(out: Path) -> None:
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"immutable output namespace is not empty; refusing overwrite: {out}")


def begin_namespace(out: Path, authority_trace: dict) -> Path:
    """Spend the namespace immediately so every later failure leaves durable evidence."""
    out = Path(out)
    assert_empty_output(out)
    if not out.exists():
        out.mkdir(parents=True, exist_ok=False)
    marker = out / "G6_EXECUTION_START.json"
    if marker.exists():
        raise RuntimeError(f"G6 execution-start marker already exists: {marker}")
    marker.write_text(
        json.dumps(
            {
                "schema": "JEPA_TD_RELATIONAL_G6_EXECUTION_START_V1",
                "status": "STARTED_NOT_A_PASS",
                "authority_trace": authority_trace,
                "biological_replay_authorized": False,
                "target_selection_authorized": False,
                "td60_authorized": False,
                "training_authorized": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return marker


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
    """Strict raw-count decoder; whole physical row contributes to library total before filtering."""
    row: dict[int, int] = {}
    total = 0
    for j0, v0 in zip(indices, values):
        column = int(j0)
        value = common.strict_raw_integer(v0)
        total += value
        address = col_to_address.get(column)
        if address is not None and address in replay_addresses and value:
            if address in row:
                raise RuntimeError(f"noninjective mapped replay address encountered at value read: {address}")
            row[address] = value
    return row, total


def select_sample_a(frame: pd.DataFrame, *, enforce_geometry: bool = True) -> pd.DataFrame:
    selected = frame[frame["sample"].astype(str).eq(SAMPLE_A_LABEL)].copy().sort_values("sample_row")
    if enforce_geometry:
        if len(selected) != N_SAMPLE_A:
            raise RuntimeError(f"Sample-A geometry mismatch: {len(selected)} != {N_SAMPLE_A}")
        if selected.source.value_counts().to_dict() != SOURCE_COUNTS:
            raise RuntimeError("Sample-A source counts mismatch")
        if selected.sample_row.astype(int).tolist() != list(range(N_SAMPLE_A)):
            raise RuntimeError("Sample-A row order mismatch")
    return selected


def read_td50(zip_path: Path) -> dict[str, dict[str, np.ndarray]]:
    zip_path = Path(zip_path)
    if common.sha256_file(zip_path) != EXPECTED_TD_ARTIFACTS_SHA:
        raise RuntimeError("TD41-TD58 historical archive SHA mismatch")
    out: dict[str, dict[str, np.ndarray]] = {}
    with zipfile.ZipFile(zip_path) as archive:
        for source in SOURCE_COUNTS:
            name = next((n for n in archive.namelist() if n.endswith(f"td50_{source}.npz")), None)
            if name is None:
                raise RuntimeError(f"missing td50_{source}.npz in {zip_path}")
            raw = archive.read(name)
            if sha256_bytes(raw) != TD50_SHA[source]:
                raise RuntimeError(f"td50 {source} SHA mismatch")
            with np.load(io.BytesIO(raw), allow_pickle=False) as data:
                out[source] = {key: data[key].copy() for key in ("global_row", "source_library", "detected")}
    return out


def sentinel_maps(td50):
    library, detected = {}, {}
    for source, payload in td50.items():
        for grow, source_library, det in zip(
            payload["global_row"].astype(int),
            payload["source_library"].astype(np.int64),
            payload["detected"].astype(np.int64),
        ):
            library[int(grow)] = int(source_library)
            detected[int(grow)] = int(det)
    if len(library) != N_SAMPLE_A or len(detected) != N_SAMPLE_A:
        raise RuntimeError("TD50 sentinel geometry mismatch")
    return library, detected


def verify_historical_csr(root: Path):
    root = Path(root)
    for name, expected in HIST_CSR_SHA.items():
        path = root / name
        if not path.is_file() or common.sha256_file(path) != expected:
            raise RuntimeError(f"historical CSR authority mismatch: {path}")
    data = np.load(root / "data.npy", mmap_mode="r")
    indices = np.load(root / "indices.npy", mmap_mode="r")
    indptr = np.load(root / "indptr.npy", mmap_mode="r")
    shape = tuple(np.load(root / "shape.npy"))
    if shape != (50_000, N_ADDR):
        raise RuntimeError(f"historical CSR shape mismatch: {shape}")
    return data, indices, indptr, shape


def nph_historical_row(global_row: int, data, indices, indptr, replay_addresses: set[int]):
    lo, hi = int(indptr[global_row]), int(indptr[global_row + 1])
    row: dict[int, float] = {}
    for a0, v0 in zip(indices[lo:hi], data[lo:hi]):
        address = int(a0)
        value = float(v0)
        if not np.isfinite(value):
            raise RuntimeError("non-finite historical NPH normalized value")
        if address in replay_addresses and value != 0.0:
            row[address] = value
    return row


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
    sample_a = select_sample_a(sample, enforce_geometry=True)
    provenance = pd.read_csv(require["provenance"][0], low_memory=False)
    collision = pd.read_csv(require["collision_ledger"][0], low_memory=False)
    freeze = json.loads(require["macha_freeze"][0].read_text(encoding="utf-8"))
    return replay, sample_a, provenance, collision, freeze


def bind_execution(args):
    g6_path = Path(__file__).resolve()
    g7_path = g6_path.with_name("audit_td_relational_g7_s174_overlap_v2.py")
    auth = common.load_runtime_authorization(
        Path(args.value_authorization),
        preflight_path=Path(args.preflight_result),
        mapping_path=Path(args.mapping_receipt),
        g6_path=g6_path,
        g7_path=g7_path,
    )
    preflight, mapping = common.load_bound_preflight(
        Path(args.preflight_result),
        Path(args.mapping_receipt),
        expected_preflight_sha=auth["preflight_result_sha256"],
        expected_mapping_sha=auth["mapping_receipt_sha256"],
    )
    return auth, preflight, mapping, g6_path, g7_path


def _authority_trace(args, auth: dict, g6_path: Path, g7_path: Path) -> dict:
    return {
        "preflight_result_sha256": common.sha256_file(Path(args.preflight_result)),
        "mapping_receipt_sha256": common.sha256_file(Path(args.mapping_receipt)),
        "authorization_sha256": common.sha256_file(Path(args.value_authorization)),
        **common.code_identity(g6_path, g7_path),
        "authorization_schema": auth["schema"],
        "authorization_token": auth["authorization"],
    }


def _write_g6_stop(out: Path, status: str, *, authority_trace: dict, mismatches: list[dict]) -> None:
    receipt = {
        "schema": G6_RECEIPT_SCHEMA,
        "status": status,
        "mismatch_count": len(mismatches),
        "preview": mismatches[:50],
        "authority_trace": authority_trace,
        "input_authority_hashes": INPUT_AUTHORITY_HASHES,
        "biological_replay_authorized": False,
        "target_selection_authorized": False,
        "td60_authorized": False,
        "training_authorized": False,
    }
    (out / "G6_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-result", required=True)
    parser.add_argument("--mapping-receipt", required=True)
    parser.add_argument("--value-authorization", required=True)
    parser.add_argument("--replay-manifest", required=True)
    parser.add_argument("--sample-freeze", required=True)
    parser.add_argument("--provenance", required=True)
    parser.add_argument("--collision-ledger", required=True)
    parser.add_argument("--macha-freeze", required=True)
    parser.add_argument("--td-artifacts-zip", required=True)
    parser.add_argument("--historical-csr-root", required=True,
                        help="Authenticated old 50K CSR arrays; NPH52 pass-through only")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    auth, _, _, g6_path, g7_path = bind_execution(args)
    authority_trace = _authority_trace(args, auth, g6_path, g7_path)

    out = Path(args.output_dir)
    begin_namespace(out, authority_trace)

    replay, sample_a, provenance, collision, freeze = load_inputs(args)
    replay_addresses = set(replay.molecular_address_index.astype(int))
    td50 = read_td50(Path(args.td_artifacts_zip))
    historical_library, historical_detected = sentinel_maps(td50)
    hdata, hindices, hindptr, _ = verify_historical_csr(Path(args.historical_csr_root))

    matrices = {str(item["matrix_id"]): item for item in freeze["matrices"]}
    rows_out: list[int] = []
    cols_out: list[int] = []
    vals_out: list[float] = []
    source_library_corrected = np.zeros(N_SAMPLE_A, dtype=np.int64)
    detected_corrected = np.full(N_SAMPLE_A, -1, dtype=np.int64)
    detected_historical = np.zeros(N_SAMPLE_A, dtype=np.int64)
    source = sample_a.source.astype(str).to_numpy()
    donor = sample_a.donor_id.astype(str).to_numpy()
    operator = sample_a.operator_index.astype(int).to_numpy()
    global_row = sample_a.global_row.astype(int).to_numpy()
    cell_id = sample_a.cell_id.astype(str).to_numpy()
    g6_mismatches: list[dict] = []
    mapping_diagnostics: list[dict] = []
    verified_source_shas: dict[str, str] = {}
    source_root = Path(args.source_root)

    import h5py

    for mid0, group in sample_a[~sample_a.source.eq("NPH52")].groupby("matrix_id", sort=True):
        mid = str(mid0)
        study = str(group.source.iloc[0])
        matrix = matrices.get(mid)
        if matrix is None:
            raise RuntimeError(f"matrix absent from Macha freeze: {mid}")
        fprov = provenance[provenance.source_dataset_id.astype(str).eq(FAMILY[study])]
        if fprov.source_exact_ensembl_id.astype(str).duplicated().any():
            raise RuntimeError(f"nonunique provenance identifier: {study}")
        id_to_address = dict(zip(
            fprov.source_exact_ensembl_id.astype(str),
            fprov.molecular_address_index.astype(int),
        ))
        ledger_ids = set(collision.loc[
            collision.matrix_id.astype(str).eq(mid), "source_exact_ensembl_id"
        ].astype(str))
        src = source_root / str(matrix["source"]["path"])

        verified_source_shas[mid] = common.verify_source_file(src, matrix["source"])
        with h5py.File(src, "r") as handle:
            var_ids = h5_strings(handle["var"], VAR_ID_COLUMN[study])
            col_to_address, excluded = identifier_map(var_ids, id_to_address, ledger_ids)
            obs = h5_strings(handle["obs"], "exp_component_name")
            node = handle[str(matrix["slot"])]
            indptr = node["indptr"]
            for row in group.itertuples(index=False):
                sample_row = int(row.sample_row)
                local_row = int(row.local_row)
                if local_row < 0 or local_row >= len(obs) or str(obs[local_row]) != str(row.cell_id):
                    raise RuntimeError(f"cell row drift after preflight: {mid} row {local_row}")
                lo, hi = int(indptr[local_row]), int(indptr[local_row + 1])
                physical_indices = node["indices"][lo:hi]
                physical_values = node["data"][lo:hi]
                raw_replay, total = corrected_row(
                    physical_indices, physical_values, col_to_address, replay_addresses
                )
                if total != historical_library[int(row.global_row)]:
                    g6_mismatches.append({
                        "sample_row": sample_row,
                        "global_row": int(row.global_row),
                        "matrix_id": mid,
                        "historical": historical_library[int(row.global_row)],
                        "corrected": total,
                    })
                source_library_corrected[sample_row] = total
                detected_corrected[sample_row] = sum(
                    common.strict_raw_integer(value) != 0 and int(column) in col_to_address
                    for column, value in zip(physical_indices, physical_values)
                )
                detected_historical[sample_row] = historical_detected[int(row.global_row)]
                for address, raw in raw_replay.items():
                    normalized = float(np.log1p(raw * 10000.0 / total)) if total > 0 else 0.0
                    if normalized:
                        rows_out.append(sample_row)
                        cols_out.append(address)
                        vals_out.append(normalized)
        mapping_diagnostics.append({
            "matrix_id": mid,
            "study": study,
            "excluded": dict(Counter(excluded.values())),
            "source_sha256_verified": verified_source_shas[mid],
        })

    if g6_mismatches:
        _write_g6_stop(out, G6_MISMATCH, authority_trace=authority_trace, mismatches=g6_mismatches)
        raise RuntimeError(f"G6 source-library mismatch in {len(g6_mismatches)} rows")

    for row in sample_a[sample_a.source.eq("NPH52")].itertuples(index=False):
        sample_row = int(row.sample_row)
        grow = int(row.global_row)
        old = nph_historical_row(grow, hdata, hindices, hindptr, replay_addresses)
        source_library_corrected[sample_row] = historical_library[grow]
        detected_historical[sample_row] = historical_detected[grow]
        detected_corrected[sample_row] = historical_detected[grow]
        for address, value in old.items():
            rows_out.append(sample_row)
            cols_out.append(address)
            vals_out.append(value)

    if np.any(source_library_corrected <= 0) or np.any(detected_corrected < 0):
        raise RuntimeError("incomplete Sample-A materialization metadata")

    from scipy import sparse

    matrix = sparse.csr_matrix(
        (np.asarray(vals_out, np.float32), (np.asarray(rows_out), np.asarray(cols_out))),
        shape=(N_SAMPLE_A, N_ADDR),
        dtype=np.float32,
    )
    matrix.sort_indices()
    values_path = out / "TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz"
    sparse.save_npz(values_path, matrix, compressed=True)
    meta_path = out / "TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz"
    np.savez_compressed(
        meta_path,
        source=source,
        donor=donor,
        operator=operator,
        global_row=global_row,
        cell_id=cell_id,
        source_library=source_library_corrected,
        detected_historical=detected_historical,
        detected_corrected=detected_corrected,
    )

    receipt = {
        "schema": G6_RECEIPT_SCHEMA,
        "status": G6_PASS,
        "rows": N_SAMPLE_A,
        "source_library_exact_rows": N_SAMPLE_A,
        "verified_source_h5ad_sha256": verified_source_shas,
        "authority_trace": authority_trace,
        "input_authority_hashes": INPUT_AUTHORITY_HASHES,
        "historical_detected_is_diagnostic_only": True,
        "detected_changed_rows": int(np.sum(detected_historical != detected_corrected)),
        "values_sha256": common.sha256_file(values_path),
        "meta_sha256": common.sha256_file(meta_path),
        "biological_replay_authorized": False,
        "target_selection_authorized": False,
        "td60_authorized": False,
        "training_authorized": False,
    }
    (out / "G6_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "schema": CACHE_SCHEMA,
        "status": "MATERIALIZED_G6_V2_PASS__G7_PENDING",
        "shape": [N_SAMPLE_A, N_ADDR],
        "stored_replay_addresses": N_REPLAY,
        "nnz": int(matrix.nnz),
        "values_path": values_path.name,
        "values_sha256": receipt["values_sha256"],
        "meta_path": meta_path.name,
        "meta_sha256": receipt["meta_sha256"],
        "verified_source_h5ad_sha256": verified_source_shas,
        "mapping_diagnostics": mapping_diagnostics,
        "authority_trace": authority_trace,
        "input_authority_hashes": INPUT_AUTHORITY_HASHES,
        "g6_receipt": "G6_RECEIPT.json",
        "g7_status": "PENDING_SEPARATE_INDEPENDENT_CROSSCHECK",
        "biological_replay_authorized": False,
        "target_selection_authorized": False,
        "td60_authorized": False,
        "training_authorized": False,
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "nnz": int(matrix.nnz), "output": str(out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
