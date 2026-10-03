#!/usr/bin/env python3
"""Build a sharded master hidden truth with cell-identity keyed randomness.

The same global cell index receives the same latent state regardless of shard size,
execution order or worker count. This is the scaling analogue of the Stage-4 isolation
rule: scheduling must not become scientific identity.

FULL104 source composition is reproduced by deterministic largest-remainder
apportionment from the authoritative cell counts. A bijective permutation of global cell
indices assigns those exact source totals without turning source into a contiguous cell
range or making it depend on shard boundaries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

MASK = np.uint64(0xFFFFFFFFFFFFFFFF)
MASK_INT = (1 << 64) - 1
C1 = np.uint64(0x9E3779B97F4A7C15)
C2 = np.uint64(0xBF58476D1CE4E5B9)
C3 = np.uint64(0x94D049BB133111EB)

FULL104_N_CELLS = 4_553_407
SOURCE_NAMES = ("SEA_AD", "NPH52", "HVS")
FULL104_SOURCE_COUNTS = np.array([4_118_213, 236_476, 198_718], dtype=np.int64)


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
    # Intentional 64-bit wrap is performed in Python integer arithmetic first so NumPy
    # does not emit an overflow warning for the scalar stream multiplier.
    stream_mix = np.uint64(((int(stream) + 1) * int(C1)) & MASK_INT)
    x = idx ^ np.uint64(seed) ^ stream_mix
    z = _mix64(x)
    return ((z >> np.uint64(11)).astype(np.float64) + 0.5) / float(1 << 53)


def normal(seed: int, idx, stream: int):
    u1 = np.clip(u01(seed, idx, stream * 2), 1e-15, 1 - 1e-15)
    u2 = u01(seed, idx, stream * 2 + 1)
    return np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)


def latent_block(seed, ids, start_stream, width):
    return np.stack(
        [normal(seed, ids, start_stream + j) for j in range(width)], axis=1
    ).astype(np.float32)


def source_counts_for_n(n_cells: int) -> np.ndarray:
    """Hamilton/largest-remainder apportionment of authoritative FULL104 source counts.

    At n=4,553,407 this returns the exact authoritative counts. At stress scale it gives
    the closest integer composition with totals summing exactly to n_cells.
    """
    if n_cells <= 0:
        raise ValueError("n_cells must be positive")
    raw = FULL104_SOURCE_COUNTS.astype(np.float64) * (float(n_cells) / FULL104_N_CELLS)
    base = np.floor(raw).astype(np.int64)
    remainder = int(n_cells - int(base.sum()))
    if remainder:
        frac = raw - base
        order = np.argsort(-frac, kind="stable")
        base[order[:remainder]] += 1
    if int(base.sum()) != int(n_cells):
        raise RuntimeError("source apportionment does not sum to n_cells")
    return base


def _coprime_multiplier(n_cells: int, seed: int) -> int:
    if n_cells == 1:
        return 1
    a = int((2 * (seed % 1_000_003) + 1) % n_cells)
    if a == 0:
        a = 1
    while math.gcd(a, n_cells) != 1:
        a += 1
        if a >= n_cells:
            a = 1
    return a


def source_index_for_ids(ids, n_cells: int, seed: int) -> np.ndarray:
    """Assign exact global source totals via a deterministic bijection of cell indices."""
    ids = np.asarray(ids, dtype=np.int64)
    if ids.size and (ids.min() < 0 or ids.max() >= n_cells):
        raise ValueError("global cell id outside declared population")
    counts = source_counts_for_n(n_cells)
    a = _coprime_multiplier(n_cells, seed + 1777)
    b = int((seed * 104729 + 17) % n_cells)
    rank = (a * ids + b) % n_cells
    t0 = int(counts[0])
    t1 = int(counts[0] + counts[1])
    return np.where(rank < t0, 0, np.where(rank < t1, 1, 2)).astype(np.int8)


def build(root: Path, n_cells: int, shard_size: int, seed: int) -> dict:
    truth = root / "hidden_truth"
    truth.mkdir(parents=True, exist_ok=True)
    source_counts = source_counts_for_n(n_cells)
    shards = []
    realised_sources = np.zeros(3, dtype=np.int64)
    for start in range(0, n_cells, shard_size):
        stop = min(start + shard_size, n_cells)
        ids = np.arange(start, stop, dtype=np.uint64)
        donor_idx = (ids % np.uint64(104)).astype(np.int16)
        source_ix = source_index_for_ids(ids.astype(np.int64), n_cells, seed)
        realised_sources += np.bincount(source_ix, minlength=3)
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
    if not np.array_equal(realised_sources, source_counts):
        raise RuntimeError(
            f"realised source counts {realised_sources.tolist()} != target {source_counts.tolist()}"
        )
    manifest = dict(
        schema="V73_SHARDED_MASTER_TRUTH_MANIFEST_V2_FULL104_SOURCE_APPORTIONED",
        seed=seed,
        n_cells=n_cells,
        n_donors=104,
        n_operators=42,
        source_names=list(SOURCE_NAMES),
        authoritative_full104_source_counts=dict(zip(SOURCE_NAMES, FULL104_SOURCE_COUNTS.tolist())),
        source_counts=dict(zip(SOURCE_NAMES, source_counts.tolist())),
        source_assignment=(
            "largest-remainder apportionment from authoritative FULL104 counts followed by "
            "a deterministic bijective permutation of global_cell_index"
        ),
        source_assignment_is_shard_invariant=True,
        donor_assignment_status="PLACEHOLDER_UNIFORM_MODULO__MUST_BE_AUDITED_BEFORE_100K_PROMOTION",
        operator_assignment_status="PLACEHOLDER_HASHED_42_LEVEL__MUST_BE_AUDITED_FOR_SOURCE_OPERATOR_NESTING_BEFORE_100K_PROMOTION",
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
    print(json.dumps(dict(status="PASS", cells=m["n_cells"], shards=len(m["shards"]), source_counts=m["source_counts"]), indent=2))


if __name__ == "__main__":
    main()
