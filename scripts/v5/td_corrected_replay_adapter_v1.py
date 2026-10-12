#!/usr/bin/env python3
"""Corrected-replay adapter: present Sample-A values to the exact frozen TD56/TD57B/TD57C/TD59 executors in their
historical on-disk layout. This module defines no science.

The frozen executors read four inputs under /mnt/data:
  - the 50,000 x 41,238 log1p10k CSR (`td_matrix_npz/arrays/{data,indices,indptr,shape}.npy`);
  - the support observation-state NPZ;
  - `td50_<SOURCE>.npz`, from which they read only global_row, donor, operator, source_library and detected;
  - (TD56 only) a result path.
The adapter rebuilds exactly those inputs. Sample-A rows are placed at their historical global_row, values exist
only at the frozen 9,216 replay addresses, and each td50 file keeps the historical row order (global_row ascending).
There are two value sources:
  - HISTORICAL_FIXTURE: historical values restricted to the replay addresses. Used for equivalence qualification
    only; creates no corrected evidence.
  - CORRECTED: the accepted G6 V2 values and metadata.
Executors are run by td_corrected_replay_exec_bootstrap_v1.py from their exact bytes. Only their input paths, and
for TD57B/TD57C/TD59 their input-SHA constants, are redirected to these adapter-built, hash-recorded inputs.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np

N_GLOBAL = 50_000
N_ADDR = 41_238
SOURCES = ("HVS", "NPH52", "SEA_AD")
SAMPLE_A = "A_NATURAL_MIXTURE"
SAMPLE_A_COUNTS = {"HVS": 1_129, "NPH52": 1_310, "SEA_AD": 22_561}
ARCHIVE_SHA = "c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417"
SUPPORT_SHA = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
SUPPORT_BUNDLE_SHA = None  # the bundle is identified by the support member SHA it yields
SUPPORT_MEMBER = ("FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/support/"
                  "FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz")
SUPPORT_REL = ("td_support_extract/FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/"
               "support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz")
HIST_CSR_SHA = {"data.npy": "0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e",
                "indices.npy": "f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771",
                "indptr.npy": "58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1",
                "shape.npy": "5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb"}
HIST_TD50_SHA = {"HVS": "d6d30cb5ef791fdaaa6f751ee6d802f8e64e062ab641a48194dfc9b596609aeb",
                 "NPH52": "9de0c199414db0705d25cce18cb5007915bcf527c245ed039e2f966437c790fe",
                 "SEA_AD": "ab4fa37a2596de609b4245e82dec0ba7e4a43f95d03421acd46c5814eaaa57d4"}
SAMPLE_FREEZE_SHA = "79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6"
REPLAY_MANIFEST_SHA = "4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660"
G6_VALUES_SHA = "fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9"
G6_META_SHA = "bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74"
DETECTED_FIELDS = ("detected_historical", "detected_corrected")
BOOTSTRAP = Path(__file__).resolve().with_name("td_corrected_replay_exec_bootstrap_v1.py")


class AdapterError(RuntimeError):
    pass


def sha_file(path: Path, chunk: int = 1 << 24) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                return h.hexdigest()
            h.update(b)


def require_sha(path: Path, expected: str, label: str) -> None:
    actual = sha_file(path)
    if actual != expected:
        raise AdapterError(f"{label} SHA mismatch: {actual} != {expected} ({path})")


# ------------------------------------------------------------------------------------------------ authenticated reads
def archive_member(archive: Path, name: str, expected_sha: str | None = None) -> bytes:
    with zipfile.ZipFile(archive) as z:
        matches = [n for n in z.namelist() if n == name or n.endswith("/" + name)]
        if len(matches) != 1:
            raise AdapterError(f"archive member {name!r} is not unique: {matches}")
        raw = z.read(matches[0])
    if expected_sha is not None and hashlib.sha256(raw).hexdigest() != expected_sha:
        raise AdapterError(f"archive member {name} SHA mismatch")
    return raw


def historical_td50(archive: Path, source: str) -> dict[str, np.ndarray]:
    raw = archive_member(archive, f"td50_{source}.npz", HIST_TD50_SHA[source])
    with np.load(io.BytesIO(raw), allow_pickle=True) as t:  # historical file; donor is an object array
        out = {k: np.asarray(t[k]) for k in ("global_row", "donor", "operator", "source_library", "detected")}
    if len(out["global_row"]) != SAMPLE_A_COUNTS[source] or np.any(np.diff(out["global_row"]) <= 0):
        raise AdapterError(f"historical td50 {source} geometry/order unexpected")
    return out


def replay_addresses(manifest: Path) -> np.ndarray:
    require_sha(manifest, REPLAY_MANIFEST_SHA, "replay manifest")
    import pandas as pd
    addr = pd.read_csv(manifest, usecols=["molecular_address_index"]).molecular_address_index.to_numpy(np.int64)
    if len(addr) != 9_216 or len(np.unique(addr)) != 9_216 or addr.min() < 0 or addr.max() >= N_ADDR:
        raise AdapterError("replay manifest geometry mismatch")
    return np.sort(addr)


def sample_a_global_rows(freeze: Path) -> tuple[np.ndarray, np.ndarray]:
    """Sample-A rows in sample_row order: (global_row, source). global_row = original freeze-file row position."""
    require_sha(freeze, SAMPLE_FREEZE_SHA, "sample freeze")
    import pandas as pd
    f = pd.read_csv(freeze, dtype=str, usecols=["sample", "sample_row", "source"])
    f["global_row"] = np.arange(len(f), dtype=np.int64)
    a = f[f["sample"].eq(SAMPLE_A)].sort_values("sample_row", key=lambda s: s.astype(int), kind="stable")
    if a.sample_row.astype(int).tolist() != list(range(25_000)):
        raise AdapterError("Sample-A row order mismatch")
    return a.global_row.to_numpy(np.int64), a.source.to_numpy(str)


# -------------------------------------------------------------------------------------------- G6-shaped value caches
def historical_fixture(hist_csr: Path, freeze: Path, manifest: Path, archive: Path) -> dict:
    """G6-shaped cache (25,000 Sample-A rows, canonical columns, replay addresses only) from historical values.
    For adapter equivalence only; it is not corrected evidence."""
    for name, sha in HIST_CSR_SHA.items():
        require_sha(hist_csr / name, sha, f"historical CSR {name}")
    data = np.load(hist_csr / "data.npy", mmap_mode="r")
    indices = np.load(hist_csr / "indices.npy", mmap_mode="r")
    indptr = np.load(hist_csr / "indptr.npy", mmap_mode="r")
    keep = np.zeros(N_ADDR, dtype=bool)
    keep[replay_addresses(manifest)] = True
    rows, sources = sample_a_global_rows(freeze)
    out_ptr, out_idx, out_val = [0], [], []
    for r in rows:
        a, b = int(indptr[r]), int(indptr[r + 1])
        ix = np.asarray(indices[a:b])
        m = keep[ix]
        out_idx.append(ix[m].astype(np.int32))
        out_val.append(np.asarray(data[a:b])[m].astype(np.float64))
        out_ptr.append(out_ptr[-1] + int(m.sum()))
    meta = {"global_row": rows, "source": sources}
    lookup = {}
    for s in SOURCES:
        t = historical_td50(archive, s)
        for i, g in enumerate(t["global_row"].tolist()):
            lookup[int(g)] = (t["donor"][i], int(t["operator"][i]), int(t["source_library"][i]), int(t["detected"][i]))
    meta["donor"] = np.asarray([str(lookup[int(g)][0]) for g in rows])
    meta["operator"] = np.asarray([lookup[int(g)][1] for g in rows], dtype=np.int64)
    meta["source_library"] = np.asarray([lookup[int(g)][2] for g in rows], dtype=np.int64)
    meta["detected"] = np.asarray([lookup[int(g)][3] for g in rows], dtype=np.int64)
    return {"kind": "HISTORICAL_FIXTURE", "indptr": np.asarray(out_ptr, dtype=np.int64),
            "indices": np.concatenate(out_idx), "data": np.concatenate(out_val), "meta": meta}


def corrected_cache(g6_values: Path, g6_meta: Path, freeze: Path, *, detected_field: str) -> dict:
    """The accepted G6 V2 corrected cache, read for the replay. Opens corrected values: never call before the marker."""
    if detected_field not in DETECTED_FIELDS:
        raise AdapterError(f"detected field must be one of {DETECTED_FIELDS}")
    require_sha(g6_values, G6_VALUES_SHA, "G6 values")
    require_sha(g6_meta, G6_META_SHA, "G6 metadata")
    rows, sources = sample_a_global_rows(freeze)
    with np.load(g6_meta, allow_pickle=False) as m:
        meta = {"global_row": m["global_row"].astype(np.int64), "source": m["source"].astype(str),
                "donor": m["donor"].astype(str), "operator": m["operator"].astype(np.int64),
                "source_library": m["source_library"].astype(np.int64), "detected": m[detected_field].astype(np.int64)}
    if not (np.array_equal(meta["global_row"], rows) and np.array_equal(meta["source"], sources)):
        raise AdapterError("G6 metadata rows are not the frozen Sample-A rows in sample_row order")
    with np.load(g6_values, allow_pickle=False) as v:
        if tuple(int(x) for x in v["shape"]) != (25_000, N_ADDR):
            raise AdapterError("G6 values geometry mismatch")
        out = {"indptr": v["indptr"].astype(np.int64), "indices": v["indices"].astype(np.int32),
               "data": v["data"].astype(np.float64)}
    return {"kind": "CORRECTED", **out, "meta": meta}


def metadata_view(meta_npz: Path, freeze: Path) -> dict:
    """Structural metadata only (no detected/library-derived science) for outcome-blind QUALIFY checks."""
    rows, sources = sample_a_global_rows(freeze)
    require_sha(meta_npz, G6_META_SHA, "G6 metadata")
    with np.load(meta_npz, allow_pickle=False) as m:
        view = {"global_row": m["global_row"].astype(np.int64), "source": m["source"].astype(str),
                "donor": m["donor"].astype(str), "operator": m["operator"].astype(np.int64)}
    if not (np.array_equal(view["global_row"], rows) and np.array_equal(view["source"], sources)):
        raise AdapterError("G6 metadata rows are not the frozen Sample-A rows in sample_row order")
    return view


# ---------------------------------------------------------------------------------------- historical-layout writer
def write_inputs(cache: dict, archive: Path, support_bundle: Path, mnt: Path) -> dict:
    """Write the executors' /mnt/data inputs under `mnt`; return every written file's SHA-256."""
    mnt = Path(mnt)
    if mnt.exists() and any(mnt.iterdir()):
        raise AdapterError(f"adapter input directory must be fresh: {mnt}")
    arr = mnt / "td_matrix_npz" / "arrays"
    arr.mkdir(parents=True)
    rows = cache["meta"]["global_row"]
    order = np.argsort(rows, kind="stable")
    counts = np.zeros(N_GLOBAL, dtype=np.int64)
    counts[rows] = np.diff(cache["indptr"])
    indptr = np.zeros(N_GLOBAL + 1, dtype=np.int64)
    indptr[1:] = np.cumsum(counts)
    if indptr[-1] > np.iinfo(np.int32).max:
        raise AdapterError("nnz exceeds the historical int32 indptr")
    data = np.empty(int(indptr[-1]), dtype=np.float64)
    indices = np.empty(int(indptr[-1]), dtype=np.int32)
    for i in order:
        a, b = int(cache["indptr"][i]), int(cache["indptr"][i + 1])
        g = int(rows[i])
        data[indptr[g]:indptr[g + 1]] = cache["data"][a:b]
        indices[indptr[g]:indptr[g + 1]] = cache["indices"][a:b]
    np.save(arr / "data.npy", data)
    np.save(arr / "indices.npy", indices)
    np.save(arr / "indptr.npy", indptr.astype(np.int32))
    np.save(arr / "shape.npy", np.asarray([N_GLOBAL, N_ADDR], dtype=np.int32))
    support = mnt / SUPPORT_REL
    support.parent.mkdir(parents=True)
    with zipfile.ZipFile(support_bundle) as z:
        support.write_bytes(z.read(SUPPORT_MEMBER))
    require_sha(support, SUPPORT_SHA, "support NPZ")
    meta = cache["meta"]
    for s in SOURCES:
        hist_rows = historical_td50(archive, s)["global_row"]  # structural row order only
        idx = {int(g): i for i, g in enumerate(meta["global_row"].tolist())}
        take = np.asarray([idx[int(g)] for g in hist_rows])
        if not np.all(meta["source"][take] == s):
            raise AdapterError(f"source mismatch building td50 {s}")
        np.savez(mnt / f"td50_{s}.npz", global_row=meta["global_row"][take].astype(np.int64),
                 donor=np.asarray(meta["donor"][take], dtype=object), operator=meta["operator"][take].astype(np.int64),
                 source_library=meta["source_library"][take].astype(np.int64),
                 detected=meta["detected"][take].astype(np.int64))
    files = sorted(p for p in mnt.rglob("*") if p.is_file())
    return {p.relative_to(mnt).as_posix(): sha_file(p) for p in files}


# --------------------------------------------------------------------------------------------- exact-bytes running
def run_executor(*, kind: str, executor: Path, executor_sha: str, mnt: Path, input_sha: dict, python: str,
                 source: str | None = None, panel: int | None = None, output: Path | None = None,
                 stdout: Path, stderr: Path, timeout: int | None = None) -> int:
    """Run one exact executor in a subprocess through the bootstrap. Returns the executor's exit code."""
    cmd = [python, str(BOOTSTRAP), "--kind", kind, "--executor", str(executor), "--executor-sha256", executor_sha,
           "--mnt", str(mnt), "--input-sha-json", json.dumps(input_sha, sort_keys=True)]
    if kind == "module":
        cmd += ["--", "--source", str(source), "--panel", str(panel), "--output", str(output)]
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1", PYTHONHASHSEED="0")
    with open(stdout, "wb") as out, open(stderr, "wb") as err:
        proc = subprocess.run(cmd, stdout=out, stderr=err, env=env, timeout=timeout)
    return proc.returncode
