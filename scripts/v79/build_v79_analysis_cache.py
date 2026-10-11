#!/usr/bin/env python3
"""V79 compact analysis cache for corrected TRAIN, with bounded shard residency.

Count shards are never globally concatenated. Pass 1 authenticates one shard at a time and accumulates only
per-address detection counts plus per-cell library/detected-feature summaries. The frozen identity-blind gene
sample is selected from that prevalence vector. Pass 2 reopens one authenticated count shard at a time and
copies only the selected columns into a compact dense panel. At most one count shard CSR is resident at once.

The historical full-matrix loader remains untouched for reproducibility. `verify_against_loader` now verifies the
same quantities by an independent bounded shard stream, so verification also cannot accidentally rebuild the full
41K matrix. Synthetic tests establish equality to the historical loader path.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v79_data as DA  # noqa: E402
import v79_firewall as FW  # noqa: E402


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_verified(path: Path, auth: dict) -> bytes:
    b = FW.check_path(path).read_bytes()
    rec = auth.get(path.name)
    if rec is None or sha(b) != rec["sha256"] or len(b) != rec["bytes"]:
        raise SystemExit(f"STOP: {path.name} does not match the shard authority")
    return b


def _count_matrix_from_bytes(b: bytes, name: str) -> sparse.csr_matrix:
    with np.load(io.BytesIO(b), allow_pickle=False) as z:
        shape = tuple(int(x) for x in z["shape"])
        if shape[1] != DA.N_ADDRESSES:
            raise SystemExit(f"STOP: {name} has {shape[1]} columns")
        return sparse.csr_matrix((z["data"], z["indices"], z["indptr"]), shape=shape)


def _authority(authority) -> dict:
    raw = json.loads(Path(authority).read_text(encoding="utf-8"))["files"]
    if isinstance(raw, list):
        return {r["file"]: r for r in raw}
    return raw


def _rows(bridge) -> list[dict]:
    return sorted(FW.load_bridge(bridge), key=lambda r: r["operator_index"])


def _first_pass(root: Path, rows: list[dict], auth: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[int], dict]:
    """Authenticate one shard at a time; return prevalence numerator and per-cell summaries."""
    det = np.zeros(DA.N_ADDRESSES, dtype=np.int64)
    libraries, detected, shard_sizes = [], [], []
    verified = {}
    for r in rows:
        # Authenticate metadata bytes here as part of the custody pass. Metadata are parsed later only through FW.
        meta_name = f"{r['stem']}.meta.npz"
        mb = read_verified(root / meta_name, auth)
        verified[meta_name] = sha(mb)

        count_name = f"{r['stem']}.counts.npz"
        cb = read_verified(root / count_name, auth)
        verified[count_name] = sha(cb)
        X = _count_matrix_from_bytes(cb, count_name)
        shard_sizes.append(int(X.shape[0]))
        det += np.bincount(X.indices[X.data > 0], minlength=DA.N_ADDRESSES)
        libraries.append(np.asarray(X.sum(1)).ravel())
        detected.append(np.asarray((X > 0).sum(1)).ravel())
        del X, cb, mb
    return det, np.concatenate(libraries), np.concatenate(detected), shard_sizes, verified


def _second_pass_selected(root: Path, rows: list[dict], auth: dict, genes: np.ndarray,
                          shard_sizes: list[int]) -> np.ndarray:
    n = int(sum(shard_sizes))
    counts = None
    start = 0
    for r, expected_n in zip(rows, shard_sizes):
        name = f"{r['stem']}.counts.npz"
        b = read_verified(root / name, auth)
        X = _count_matrix_from_bytes(b, name)
        if X.shape[0] != expected_n:
            raise SystemExit(f"STOP: {name} row count changed between streaming passes")
        panel = X[:, genes].toarray()
        if counts is None:
            counts = np.empty((n, len(genes)), dtype=panel.dtype)
        counts[start:start + expected_n] = panel
        start += expected_n
        del X, panel, b
    if counts is None or start != n:
        raise SystemExit("STOP: no count shards or incomplete second pass")
    return counts


def build(cache_root, bridge, authority, gene_count: int) -> tuple:
    root = Path(cache_root)
    auth = _authority(authority)
    rows = _rows(bridge)

    det, lib, n_det, shard_sizes, verified = _first_pass(root, rows, auth)
    n = int(sum(shard_sizes))
    if n <= 0:
        raise SystemExit("STOP: no cells in corrected TRAIN shards")
    prevalence = det / n
    genes = DA.stratified_gene_sample(None, gene_count, prevalence_all=prevalence)
    counts = _second_pass_selected(root, rows, auth, genes, shard_sizes)

    d = FW.load_cell_design(root, bridge)
    di = DA.design_indices(d)
    if len(d["donor_id"]) != n:
        raise SystemExit("STOP: design and counts disagree on the number of cells")
    if counts.shape[0] != n or len(lib) != n or len(n_det) != n:
        raise SystemExit("STOP: streamed arrays disagree on cell count")

    arrays = dict(counts_selected=counts, gene_address_index=genes, prevalence_selected=prevalence[genes],
                  library_cached=lib, n_detected=n_det, source_library=np.asarray(d["source_library"]),
                  cls=di["cls"], src=di["src"], op=di["op"], donor=di["donor"], dk=di["dk"],
                  log_lib_centered=di["log_lib_centered"])
    meta = dict(n_cells=n, gene_count=int(gene_count), sample_seed=DA.GENE_SAMPLE_SEED,
                prevalence_floor=DA.PREVALENCE_FLOOR, universe_size=int((prevalence > DA.PREVALENCE_FLOOR).sum()),
                prevalence_sha256=sha(prevalence.tobytes()), shard_files_verified=len(verified),
                shard_sha256=verified, streaming_passes=2, max_count_shards_resident=1,
                global_sparse_assembly=False,
                levels=dict(n_cls=di["n_cls"], n_src=di["n_src"], n_op=di["n_op"],
                            n_donor=di["n_donor"], n_dk=di["n_dk"]),
                class_levels=[str(x) for x in di["class_levels"]], source_levels=[str(x) for x in di["source_levels"]])
    return arrays, meta


def verify_against_loader(arrays: dict, cache_root, bridge, gene_count: int) -> dict:
    """Independent bounded-stream equivalence verification; deliberately never calls DA.load_counts/vstack."""
    root = Path(cache_root)
    rows = _rows(bridge)
    genes_expected = np.asarray(arrays["gene_address_index"])
    if len(genes_expected) != gene_count:
        return dict(gene_sample=False, counts=False, library=False, n_detected=False)

    det = np.zeros(DA.N_ADDRESSES, dtype=np.int64)
    lib_parts, ndet_parts, selected_parts = [], [], []
    for r in rows:
        p = FW.check_path(root / f"{r['stem']}.counts.npz")
        with np.load(p, allow_pickle=False) as z:
            X = sparse.csr_matrix((z["data"], z["indices"], z["indptr"]),
                                  shape=tuple(int(x) for x in z["shape"]))
        det += np.bincount(X.indices[X.data > 0], minlength=DA.N_ADDRESSES)
        lib_parts.append(np.asarray(X.sum(1)).ravel())
        ndet_parts.append(np.asarray((X > 0).sum(1)).ravel())
        selected_parts.append(X[:, genes_expected].toarray())
        del X
    n = int(sum(len(x) for x in lib_parts))
    prevalence = det / n
    genes = DA.stratified_gene_sample(None, gene_count, prevalence_all=prevalence)
    selected = np.concatenate(selected_parts, axis=0)
    lib = np.concatenate(lib_parts)
    n_det = np.concatenate(ndet_parts)
    return dict(gene_sample=np.array_equal(genes, genes_expected),
                counts=np.array_equal(selected, arrays["counts_selected"]),
                library=np.array_equal(lib, arrays["library_cached"]),
                n_detected=np.array_equal(n_det, arrays["n_detected"]))


def main() -> None:
    root, bridge, authority, g, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), Path(sys.argv[5])
    arrays, meta = build(root, bridge, authority, g)
    # Real execution stays two-pass. Exact equivalence to the historical loader is enforced by synthetic fixture
    # tests; authenticated shard hashes bind real execution to those same bytes without a third/fourth full read.
    meta["verified_against_loader"] = "SYNTHETIC_EQUIVALENCE_TEST_REQUIRED__REAL_RUN_NOT_REREAD"
    out.mkdir(parents=True, exist_ok=True)
    npz = out / f"V79_ANALYSIS_CACHE_G{g}.npz"
    np.savez_compressed(npz, **arrays)
    snap = HERE.parents[1] / "SNAPSHOT_COMMIT.txt"
    meta.update(schema="V79_ANALYSIS_CACHE_RECEIPT_V2", npz=npz.name, npz_sha256=sha(npz.read_bytes()),
                authority=Path(authority).name, authority_sha256=sha(Path(authority).read_bytes()),
                code_snapshot=snap.read_text(encoding="utf-8").strip() if snap.exists() else "LIVE_TREE_NOT_A_SNAPSHOT")
    with open(out / f"V79_ANALYSIS_CACHE_G{g}_RECEIPT.json", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(meta, indent=1) + "\n")
    print("cache written", npz.name, meta["npz_sha256"][:16], "streaming", meta["streaming_passes"], "passes")


if __name__ == "__main__":
    main()
