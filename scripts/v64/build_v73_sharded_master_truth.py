#!/usr/bin/env python3
"""Build a sharded master hidden truth with cell-identity keyed randomness.

The same global cell index receives the same latent state regardless of shard size,
execution order or worker count. This is the scaling analogue of the Stage-4 isolation
rule: scheduling must not become scientific identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

MASK = np.uint64(0xFFFFFFFFFFFFFFFF)
C1 = np.uint64(0x9E3779B97F4A7C15)
C2 = np.uint64(0xBF58476D1CE4E5B9)
C3 = np.uint64(0x94D049BB133111EB)


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _mix64(x):
    x = (x + C1) & MASK
    x = ((x ^ (x >> np.uint64(30))) * C2) & MASK
    x = ((x ^ (x >> np.uint64(27))) * C3) & MASK
    return x ^ (x >> np.uint64(31))


def u01(seed: int, idx, stream: int):
    idx = np.asarray(idx, dtype=np.uint64)
    x = idx ^ np.uint64(seed) ^ (np.uint64(stream + 1) * C1)
    z = _mix64(x)
    # top 53 bits -> open interval (0,1)
    return ((z >> np.uint64(11)).astype(np.float64) + 0.5) / float(1 << 53)


def normal(seed: int, idx, stream: int):
    u1 = np.clip(u01(seed, idx, stream * 2), 1e-15, 1 - 1e-15)
    u2 = u01(seed, idx, stream * 2 + 1)
    return np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)


def latent_block(seed, ids, start_stream, width):
    return np.stack(
        [normal(seed, ids, start_stream + j) for j in range(width)], axis=1
    ).astype(np.float32)


def build(root: Path, n_cells: int, shard_size: int, seed: int) -> dict:
    truth = root / "hidden_truth"
    truth.mkdir(parents=True, exist_ok=True)
    shards = []
    for start in range(0, n_cells, shard_size):
        stop = min(start + shard_size, n_cells)
        ids = np.arange(start, stop, dtype=np.uint64)
        donor_idx = (ids % np.uint64(104)).astype(np.int16)
        src_bucket = (ids % np.uint64(100)).astype(np.int16)
        source_ix = np.where(src_bucket < 80, 0, np.where(src_bucket < 94, 1, 2)).astype(np.int8)
        operator = (_mix64(ids ^ np.uint64(seed + 991)) % np.uint64(42)).astype(np.int16)
        path = truth / f"TRUTH_{start:09d}_{stop:09d}.npz"
        np.savez(
            path,
            global_cell_index=ids.astype(np.int64),
            cell_id=np.array([f"MASTER_{int(i):09d}" for i in ids]),
            donor_index=donor_idx,
            source_index=source_ix,
            operator_index=operator,
            z_global=latent_block(seed, ids, 10, 4),
            z_query=latent_block(seed, ids, 20, 2),
            z_reg_shared=latent_block(seed, ids, 30, 3),
            z_reg_private=latent_block(seed, ids, 40, 2),
            technical_latents=latent_block(seed, ids, 50, 3),
        )
        shards.append(dict(
            start=start, stop=stop, cells=stop-start,
            file=path.name, sha256=sha256_file(path)
        ))
    manifest = dict(
        schema="V73_SHARDED_MASTER_TRUTH_MANIFEST_V1",
        seed=seed,
        n_cells=n_cells,
        n_donors=104,
        n_operators=42,
        source_rule="global_cell_index % 100 -> SEA_AD<80, NPH52<94, else HVS",
        randomization="stateless SplitMix64 keyed by (seed, global_cell_index, stream)",
        shard_size_requested=shard_size,
        shard_size_is_non_scientific=True,
        shards=shards,
        truth_firewall="hidden_truth only; observable manifests must never reference this path",
    )
    mp = truth / "TRUTH_MANIFEST.json"
    mp.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--cells", type=int, required=True)
    ap.add_argument("--shard-size", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=7302)
    a = ap.parse_args()
    m = build(Path(a.root), a.cells, a.shard_size, a.seed)
    print(json.dumps(dict(status="PASS", cells=m["n_cells"], shards=len(m["shards"])), indent=2))


if __name__ == "__main__":
    main()
