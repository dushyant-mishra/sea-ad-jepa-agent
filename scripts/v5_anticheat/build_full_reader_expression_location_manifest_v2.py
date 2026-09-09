#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def shard_stem(matrix_id: str) -> str:
    return hashlib.sha256(f"corrected|{matrix_id}".encode()).hexdigest()[:16]


def infer_source(matrix_id: str) -> str:
    if matrix_id.startswith("HVS::"):
        return "HVS"
    if matrix_id.startswith("NPH52::"):
        return "NPH52"
    if matrix_id.startswith("sea_ad_"):
        return "SEA_AD"
    raise ValueError(f"unknown frozen matrix source: {matrix_id}")


def build(
    *,
    loader_manifest: Path,
    expected_loader_sha256: str,
    observation_state: Path,
    expected_observation_sha256: str,
    cache_root: Path,
) -> dict:
    if sha256_file(loader_manifest) != expected_loader_sha256:
        raise RuntimeError("frozen loader manifest SHA mismatch")
    if sha256_file(observation_state) != expected_observation_sha256:
        raise RuntimeError("observation-state SHA mismatch")
    loader = json.loads(loader_manifest.read_text())
    if (
        loader.get("schema") != "foundation-train-loader-v1"
        or loader.get("address_count") != 41238
        or len(loader.get("shards", [])) != 42
    ):
        raise RuntimeError("frozen loader semantic surface mismatch")

    out = []
    for op, shard in enumerate(loader["shards"]):
        matrix = str(shard["matrix_id"])
        stem = shard_stem(matrix)
        counts_path = cache_root / f"{stem}.counts.npz"
        meta_path = cache_root / f"{stem}.meta.npz"
        if not counts_path.is_file() or not meta_path.is_file():
            raise FileNotFoundError(f"missing physical shard operator {op}: {matrix}")
        counts_sha = sha256_file(counts_path)
        meta_sha = sha256_file(meta_path)
        if counts_sha != shard["counts_sha256"]:
            raise RuntimeError(f"counts SHA mismatch operator {op}: {matrix}")
        if meta_sha != shard["meta_sha256"]:
            raise RuntimeError(f"meta SHA mismatch operator {op}: {matrix}")
        out.append(
            {
                "operator_index": op,
                "matrix_id": matrix,
                "source": infer_source(matrix),
                "counts_path": str(counts_path.resolve()),
                "counts_sha256": counts_sha,
                "meta_path": str(meta_path.resolve()),
                "meta_sha256": meta_sha,
            }
        )

    return {
        "schema": "D1_EXPRESSION_SHARD_LOCATION_MANIFEST_V2",
        "status": "FROZEN_42_OF_42_EXACT_SHARDS_BOUND",
        "production_loader_manifest_sha256": expected_loader_sha256,
        "observation_state_sha256": expected_observation_sha256,
        "cache_root": str(cache_root.resolve()),
        "shards": out,
        "synthetic_data_used": False,
        "pathology_used": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--loader-manifest", required=True, type=Path)
    p.add_argument("--expected-loader-sha256", required=True)
    p.add_argument("--observation-state", required=True, type=Path)
    p.add_argument("--expected-observation-sha256", required=True)
    p.add_argument("--cache-root", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    result = build(
        loader_manifest=a.loader_manifest,
        expected_loader_sha256=a.expected_loader_sha256,
        observation_state=a.observation_state,
        expected_observation_sha256=a.expected_observation_sha256,
        cache_root=a.cache_root,
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
