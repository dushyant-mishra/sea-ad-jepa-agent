#!/usr/bin/env python3
"""V79 compact analysis cache for the corrected-TRAIN phases (resource-efficiency requirements 3-6 and 8).

Reads each of the 42 count shards from disk exactly once, verifying every count and meta file's bytes against the
committed shard authority (results/v79/V79_S174_SHARD_AUTHORITY_V1.json, from the PR #244 custody verification).
In that one pass it computes per-address prevalence, each cell's library (sum over all cached addresses) and
detected-feature count; it then draws the frozen identity-blind gene sample from that prevalence and keeps only
those columns. Output: one npz (selected counts, gene address indices, library, detected features, source library,
design codes) and a receipt binding the cache to the shard hashes, the gene count, the sampling seed and the code.

The cache is numerically verified against the current loader before it is written (selected counts, library,
detected features and the gene sample identical), so speed never replaces equivalence. Real data: run only after
simulation recovery and the benchmark pass (contract order).

Usage: build_v79_analysis_cache.py <cache root> <bridge json> <authority json> <gene count> <out dir>
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


def build(cache_root, bridge, authority, gene_count: int) -> tuple:
    root = Path(cache_root)
    auth = json.loads(Path(authority).read_text(encoding="utf-8"))["files"]
    rows = sorted(FW.load_bridge(bridge), key=lambda r: r["operator_index"])
    blocks, verified = [], {}
    det = np.zeros(DA.N_ADDRESSES, dtype=np.int64)
    for r in rows:
        for suffix in ("counts", "meta"):
            name = f"{r['stem']}.{suffix}.npz"
            b = read_verified(root / name, auth)
            verified[name] = sha(b)
            if suffix == "counts":
                with np.load(io.BytesIO(b), allow_pickle=False) as z:
                    shape = tuple(int(x) for x in z["shape"])
                    if shape[1] != DA.N_ADDRESSES:
                        raise SystemExit(f"STOP: {name} has {shape[1]} columns")
                    X = sparse.csr_matrix((z["data"], z["indices"], z["indptr"]), shape=shape)
                det += np.bincount(X.indices[X.data > 0], minlength=DA.N_ADDRESSES)
                blocks.append(X)
    X = sparse.vstack(blocks, format="csr")
    n = X.shape[0]
    prevalence = det / n
    genes = DA.stratified_gene_sample(None, gene_count, prevalence_all=prevalence)
    lib = np.asarray(X.sum(1)).ravel()
    n_det = np.asarray((X > 0).sum(1)).ravel()
    counts = X[:, genes].toarray()
    d = FW.load_cell_design(root, bridge)
    di = DA.design_indices(d)
    if len(d["donor_id"]) != n:
        raise SystemExit("STOP: design and counts disagree on the number of cells")
    arrays = dict(counts_selected=counts, gene_address_index=genes, prevalence_selected=prevalence[genes],
                  library_cached=lib, n_detected=n_det, source_library=np.asarray(d["source_library"]),
                  cls=di["cls"], src=di["src"], op=di["op"], donor=di["donor"], dk=di["dk"],
                  log_lib_centered=di["log_lib_centered"])
    meta = dict(n_cells=int(n), gene_count=int(gene_count), sample_seed=DA.GENE_SAMPLE_SEED,
                prevalence_floor=DA.PREVALENCE_FLOOR, universe_size=int((prevalence > DA.PREVALENCE_FLOOR).sum()),
                prevalence_sha256=sha(prevalence.tobytes()), shard_files_verified=len(verified),
                shard_sha256=verified, levels=dict(n_cls=di["n_cls"], n_src=di["n_src"], n_op=di["n_op"],
                                                    n_donor=di["n_donor"], n_dk=di["n_dk"]),
                class_levels=[str(x) for x in di["class_levels"]], source_levels=[str(x) for x in di["source_levels"]])
    return arrays, meta


def verify_against_loader(arrays: dict, cache_root, bridge, gene_count: int) -> dict:
    """The current loader's path, end to end: full matrix, gene sample, the selected columns, library and
    detected features. Every check must be exactly equal."""
    X = DA.load_counts(cache_root, bridge)
    genes = DA.stratified_gene_sample(X, gene_count)
    checks = dict(gene_sample=np.array_equal(genes, arrays["gene_address_index"]),
                  counts=np.array_equal(X[:, genes].toarray(), arrays["counts_selected"]),
                  library=np.array_equal(np.asarray(X.sum(1)).ravel(), arrays["library_cached"]),
                  n_detected=np.array_equal(np.asarray((X > 0).sum(1)).ravel(), arrays["n_detected"]))
    if not all(checks.values()):
        raise SystemExit(f"STOP: compact cache differs from the current loader: {checks}")
    return checks


def main() -> None:
    root, bridge, authority, g, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), Path(sys.argv[5])
    arrays, meta = build(root, bridge, authority, g)
    meta["verified_against_loader"] = verify_against_loader(arrays, root, bridge, g)
    out.mkdir(parents=True, exist_ok=True)
    npz = out / f"V79_ANALYSIS_CACHE_G{g}.npz"
    np.savez_compressed(npz, **arrays)
    snap = HERE.parents[1] / "SNAPSHOT_COMMIT.txt"
    meta.update(schema="V79_ANALYSIS_CACHE_RECEIPT_V1", npz=npz.name, npz_sha256=sha(npz.read_bytes()),
                authority=Path(authority).name, authority_sha256=sha(Path(authority).read_bytes()),
                code_snapshot=snap.read_text(encoding="utf-8").strip() if snap.exists() else "LIVE_TREE_NOT_A_SNAPSHOT")
    with open(out / f"V79_ANALYSIS_CACHE_G{g}_RECEIPT.json", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(meta, indent=1) + "\n")
    print("cache written", npz.name, meta["npz_sha256"][:16], "verified", meta["verified_against_loader"])


if __name__ == "__main__":
    main()
