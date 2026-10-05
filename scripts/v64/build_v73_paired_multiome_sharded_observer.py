#!/usr/bin/env python3
"""Build a shard-invariant paired RNA+ATAC stress observer from the V73 master truth.

This is an observation-architecture fixture, not a claim that its feature counts reproduce
GSE214979. Every output row is tied to the SAME global synthetic cell used by the FULL104
observer. RNA observes global/query/shared state; ATAC observes global/shared plus private
regulatory state. The private truth is consumed only inside this generator and is never
serialized into observable output.

V75 separates the truth/operator-model seed from stochastic measurement realization.
Omitting measurement_seed preserves V73/V74 semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_v73_sharded_master_truth as T
import build_v73_full104_sharded_observer as F

N_RNA_GENES = 64
N_ATAC_REGIONS = 256
RNA_GENES = np.array([f"ENSG_MULTIOME_SYN_{i:05d}" for i in range(N_RNA_GENES)])
REGION_CHROM = np.array(["chr1"] * N_ATAC_REGIONS)
REGION_START = np.arange(N_ATAC_REGIONS, dtype=np.int64) * 5000 + 1_000_000
REGION_END = REGION_START + 5000


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _weights(seed: int, n_features: int, n_latent: int, stream0: int, scale: float):
    fid = np.arange(n_features, dtype=np.uint64)
    return np.stack(
        [T.normal(seed, fid, stream0 + j) for j in range(n_latent)], axis=0
    ).astype(np.float32) * np.float32(scale)


def _source_embeddings(seed: int):
    sid = np.arange(3, dtype=np.uint64)
    return np.stack(
        [T.normal(seed + 300, sid, 700 + j) for j in range(2)], axis=1
    ).astype(np.float32)


def observe(root: Path, seed: int = 7302, measurement_seed: int | None = None) -> dict:
    truth_root = root / "hidden_truth"
    obs = root / "observable_raw" / "PAIRED_MULTIOME_like_sharded"
    obs.mkdir(parents=True, exist_ok=True)
    tm = json.loads((truth_root / "TRUTH_MANIFEST.json").read_text())
    if int(tm["seed"]) != int(seed):
        raise ValueError("observer seed must equal master-truth seed")
    measurement_seed = int(seed if measurement_seed is None else measurement_seed)

    src_embed = _source_embeddings(seed)
    # Operator/model mappings stay tied to the truth seed; only stochastic count
    # realization changes with measurement_seed.
    Wr = _weights(seed + 1100, N_RNA_GENES, 11, 1000, 0.20)
    Wa = _weights(seed + 1200, N_ATAC_REGIONS, 12, 1200, 0.18)
    out_shards = []
    total = 0

    for s in tm["shards"]:
        tp = truth_root / s["file"]
        if sha256_file(tp) != s["sha256"]:
            raise RuntimeError("truth shard digest mismatch: " + s["file"])
        z = np.load(tp, allow_pickle=False)
        ids = z["global_cell_index"].astype(np.int64)
        src = z["source_index"].astype(np.int8)

        rlatent = np.c_[
            z["z_global"], z["z_query"], z["z_reg_shared"], src_embed[src]
        ].astype(np.float32)
        alatent = np.c_[
            z["z_global"], z["z_reg_shared"], z["z_reg_private"], src_embed[src],
            z["technical_latents"][:, :1]
        ].astype(np.float32)

        reta = rlatent @ Wr
        aeta = alatent @ Wa
        rlam = np.exp(np.clip(reta, -3.5, 2.7))
        alam = np.exp(np.clip(aeta, -4.0, 2.4))

        rgid = np.arange(N_RNA_GENES, dtype=np.uint64)
        rkeys = (ids.astype(np.uint64)[:, None] * np.uint64(1140071481932319849)
                 + rgid[None, :] * np.uint64(1402946736689701973))
        rcounts = F.poisson_from_uniform(
            rlam, T.u01(measurement_seed + 1300, rkeys, 1400), max_k=64
        ).T.astype(np.int16)

        rid = np.arange(N_ATAC_REGIONS, dtype=np.uint64)
        akeys = (ids.astype(np.uint64)[:, None] * np.uint64(6364136223846793005)
                 + rid[None, :] * np.uint64(1442695040888963407))
        acounts = F.poisson_from_uniform(
            alam, T.u01(measurement_seed + 1400, akeys, 1500), max_k=64
        ).T.astype(np.int16)

        start, stop = int(ids[0]), int(ids[-1]) + 1
        p = obs / f"MULTIOME_{start:09d}_{stop:09d}.npz"
        np.savez(
            p,
            global_cell_index=ids,
            cell_id=z["cell_id"],
            donor_index=z["donor_index"],
            source_index=src,
            operator_index=z["operator_index"],
            rna_counts=rcounts,
            rna_genes=RNA_GENES,
            atac_counts=acounts,
            atac_region_chrom=REGION_CHROM,
            atac_region_start=REGION_START,
            atac_region_end=REGION_END,
        )
        out_shards.append(dict(
            start=start, stop=stop, cells=len(ids), file=p.name, sha256=sha256_file(p)
        ))
        total += len(ids)

    manifest = dict(
        schema="V75_PAIRED_MULTIOME_SHARDED_OBSERVER_MANIFEST_V2_MEASUREMENT_SEED_SEPARATED",
        seed=seed,
        truth_seed=seed,
        measurement_seed=measurement_seed,
        n_cells=total,
        paired_same_cell_identity=True,
        n_rna_genes=N_RNA_GENES,
        n_atac_regions=N_ATAC_REGIONS,
        feature_scale_status="STRESS_ARCHITECTURE_ONLY__NOT_GSE214979_FEATURE_SCALE",
        source_counts=tm["source_counts"],
        private_regulatory_state=(
            "consumed only by the synthetic ATAC observation operator; not serialized into output"
        ),
        model_facing_output_contains_hidden_truth=False,
        master_truth_digest_binding=[
            dict(file=s["file"], sha256=s["sha256"]) for s in tm["shards"]
        ],
        observation_operator_seed=seed,
        measurement_realization_seed=measurement_seed,
        count_randomization=(
            "stateless feature-by-cell inverse-CDF Poisson keyed by measurement realization seed; invariant to shard boundaries"
        ),
        shards=out_shards,
    )
    mp = obs / "PAIRED_MULTIOME_SHARDED_MANIFEST.json"
    mp.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--seed", type=int, default=7302)
    ap.add_argument("--measurement-seed", type=int, default=None)
    a = ap.parse_args()
    m = observe(Path(a.root), a.seed, a.measurement_seed)
    print(json.dumps(dict(status="PASS", cells=m["n_cells"], shards=len(m["shards"]), truth_seed=m["truth_seed"], measurement_seed=m["measurement_seed"]), indent=2))


if __name__ == "__main__":
    main()
