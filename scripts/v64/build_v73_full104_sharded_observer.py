#!/usr/bin/env python3
"""Observe V73 master-truth shards through a FULL104-like RNA operator.

No global dense matrix is allocated. Counts are generated deterministically from global
cell identity and gene identity, so changing shard size or processing order cannot alter
the scientific bytes for a cell after shards are aligned by global index.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_v73_sharded_master_truth as T

N_GENES = 96
GENES = np.array([f"ENSG_SYN_{i:05d}" for i in range(N_GENES)])
GENE_NAMES = np.array([f"GENE{i:03d}" for i in range(N_GENES)])


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def poisson_from_uniform(lam, u, max_k=80):
    """Vectorized inverse-CDF Poisson draw using a stateless uniform matrix.

    lam is bounded to <= exp(3) ~20 by construction; tail mass beyond 80 is negligible.
    This avoids stateful RNG consumption that would make counts depend on shard boundaries.
    """
    lam = np.asarray(lam, dtype=np.float64)
    u = np.asarray(u, dtype=np.float64)
    pmf = np.exp(-lam)
    cdf = pmf.copy()
    out = np.zeros(lam.shape, dtype=np.int16)
    active = u > cdf
    for k in range(1, max_k + 1):
        if not active.any():
            break
        pmf = pmf * lam / float(k)
        cdf = cdf + pmf
        hit = active & (u <= cdf)
        out[hit] = k
        active &= ~hit
    if active.any():
        out[active] = max_k
    return out


def weights(seed):
    gid = np.arange(N_GENES, dtype=np.uint64)
    # 11 latent dimensions: global4, query2, shared3, source-embedding2
    return np.stack(
        [T.normal(seed + 100, gid, 200 + j) for j in range(11)], axis=0
    ).astype(np.float32) * np.float32(0.22)


def source_embeddings(seed):
    sid = np.arange(3, dtype=np.uint64)
    return np.stack(
        [T.normal(seed + 200, sid, 300 + j) for j in range(2)], axis=1
    ).astype(np.float32)


def observe(root: Path, seed: int = 7302) -> dict:
    truth_root = root / "hidden_truth"
    obs = root / "observable_raw" / "FULL104_like_sharded"
    obs.mkdir(parents=True, exist_ok=True)
    tm = json.loads((truth_root / "TRUTH_MANIFEST.json").read_text())
    if int(tm["seed"]) != int(seed):
        raise ValueError("observer seed must equal master-truth seed")

    W = weights(seed)
    src_embed = source_embeddings(seed)
    out_shards = []
    total_cells = 0

    for s in tm["shards"]:
        tp = truth_root / s["file"]
        if sha256_file(tp) != s["sha256"]:
            raise RuntimeError("truth shard digest mismatch: " + s["file"])
        z = np.load(tp, allow_pickle=False)
        ids = z["global_cell_index"].astype(np.int64)
        src = z["source_index"].astype(np.int8)
        latent = np.c_[
            z["z_global"], z["z_query"], z["z_reg_shared"], src_embed[src]
        ].astype(np.float32)
        eta = latent @ W
        technical_depth = np.exp(
            np.clip(7.4 + 0.35 * z["technical_latents"][:, 0], 5.0, 9.5)
        )
        eta = eta + (0.06 * np.log1p(technical_depth))[:, None]
        lam = np.exp(np.clip(eta, -3.0, 3.0))

        gid = np.arange(N_GENES, dtype=np.uint64)
        keys = (ids.astype(np.uint64)[:, None] * np.uint64(1315423911)
                + gid[None, :] * np.uint64(2654435761))
        u = T.u01(seed + 500, keys, 900)
        counts = poisson_from_uniform(lam, u).T.astype(np.int16)

        avail = np.ones((N_GENES, len(ids)), dtype=np.uint8)
        hvs = np.where(src == 2)[0]
        nph = np.where(src == 1)[0]
        if len(hvs):
            avail[-24:, hvs] = 0
        if len(nph):
            avail[-10:, nph] = 0
        counts[avail == 0] = 0

        op = z["operator_index"].astype(np.int16)
        donor = z["donor_index"].astype(np.int16)
        cell_ids = z["cell_id"]
        start, stop = int(ids[0]), int(ids[-1]) + 1
        opath = obs / f"RNA_{start:09d}_{stop:09d}.npz"
        np.savez(
            opath,
            counts=counts,
            availability=avail,
            genes=GENES,
            gene_names=GENE_NAMES,
            global_cell_index=ids,
            cell_id=cell_ids,
        )
        mpath = obs / f"META_{start:09d}_{stop:09d}.csv.gz"
        source_names = np.array(["SEA_AD", "NPH52", "HVS"])
        with gzip.open(mpath, "wt", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["global_cell_index","cell_id","donor","source","operator"])
            for i in range(len(ids)):
                w.writerow([
                    int(ids[i]), str(cell_ids[i]), f"D{int(donor[i]):03d}",
                    str(source_names[int(src[i])]), f"OP{int(op[i]):02d}"
                ])

        out_shards.append(dict(
            start=start, stop=stop, cells=len(ids),
            rna_file=opath.name, rna_sha256=sha256_file(opath),
            metadata_file=mpath.name, metadata_sha256=sha256_file(mpath),
        ))
        total_cells += len(ids)

    manifest = dict(
        schema="V73_FULL104_SHARDED_OBSERVER_MANIFEST_V1",
        seed=seed,
        n_cells=total_cells,
        n_genes=N_GENES,
        n_donors=104,
        n_operators=42,
        source_target="80/14/6 SEA_AD/NPH52/HVS by global-index rule",
        structural_missingness=True,
        hidden_truth_path_exposed=False,
        master_truth_digest_binding=[
            dict(file=s["file"], sha256=s["sha256"]) for s in tm["shards"]
        ],
        count_randomization=(
            "stateless inverse-CDF Poisson keyed by global_cell_index x gene identity; "
            "shard boundaries and worker order are non-scientific"
        ),
        shards=out_shards,
    )
    mp = obs / "FULL104_SHARDED_MANIFEST.json"
    mp.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--seed", type=int, default=7302)
    a = ap.parse_args()
    m = observe(Path(a.root), a.seed)
    print(json.dumps(dict(status="PASS", cells=m["n_cells"], shards=len(m["shards"])), indent=2))


if __name__ == "__main__":
    main()
