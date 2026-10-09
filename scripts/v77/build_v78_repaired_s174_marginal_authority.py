#!/usr/bin/env python3
"""Canonical V78 F3 authority builder for the repaired S174 TRAIN cache.

This adapter changes custody/authentication only. Marginal derivation, rank scrubbing,
quantile compression, and runtime validation are delegated to the already-tested V78 core.
The historical production-loader manifest is not a valid identity root for the repaired
S174 cache; counts bind to the corrected calibration receipt and metadata binds to the
repaired-RAR digest receipt.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v78_marginal_authority as CORE  # noqa: E402

SCHEMA = CORE.SCHEMA
FALLBACK_RULE = CORE.FALLBACK_RULE
EXPECTED_REGISTRY_SHA256 = CORE.EXPECTED_REGISTRY_SHA256
EXPECTED_N_ADDRESSES = CORE.EXPECTED_N_ADDRESSES
EXPECTED_N_SHARDS = CORE.EXPECTED_N_SHARDS
EXPECTED_CORRECTED_CALIBRATION_SHA256 = "f6ba2c725a5437cc8455fff418027d36efe9ea9430fbd0a5765df62dedca6068"
EXPECTED_META_DIGEST_SEMANTIC_SHA256 = "b876e13526f51d5a4199ca750ad09065c5ab8a20aeca39dff3d8c385f2241f46"
EXPECTED_REPAIRED_ARCHIVE_SHA256 = "88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f"

assign_rank_scrubbed_abundance = CORE.assign_rank_scrubbed_abundance


def _count_receipt(path: Path, canonical: bool) -> tuple[str, dict[str, str]]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"corrected S174 calibration unavailable: {path}")
    sha = CORE._sha256_file(path)
    if canonical and sha != EXPECTED_CORRECTED_CALIBRATION_SHA256:
        raise RuntimeError("corrected S174 calibration SHA-256 mismatch")
    rec = json.loads(path.read_text())
    if rec.get("schema") != "V77_REAL_TRAIN_EXPRESSION_CALIBRATION_V1":
        raise RuntimeError("corrected S174 calibration schema mismatch")
    source = rec.get("source", {})
    for flag in ("pathology_blind", "train_only", "read_only"):
        if source.get(flag) is not True:
            raise PermissionError(f"corrected S174 calibration must declare {flag}=true")
    rows = source.get("shard_digests", [])
    if not isinstance(rows, list) or len(rows) != EXPECTED_N_SHARDS:
        raise RuntimeError("corrected S174 calibration must contain exactly 42 count digests")
    out: dict[str, str] = {}
    for row in rows:
        name = Path(str(row.get("file", ""))).name
        digest = str(row.get("sha256", ""))
        if not name.endswith(".counts.npz") or not CORE._is_sha256(digest):
            raise RuntimeError("malformed corrected S174 count digest row")
        stem = name.removesuffix(".counts.npz")
        if stem in out:
            raise RuntimeError("duplicate corrected S174 count stem")
        out[stem] = digest
    return sha, out


def _meta_receipt(path: Path, calibration_sha: str, canonical: bool) -> tuple[dict, str, dict[str, str]]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"repaired S174 meta digest unavailable: {path}")
    rec = json.loads(path.read_text())
    if rec.get("schema") != "V78_S174_SHARD_META_DIGEST_V1":
        raise RuntimeError("repaired S174 meta digest schema mismatch")
    if rec.get("claim_class") != "CUSTODY_DERIVATION__NON_AUTHORIZING":
        raise PermissionError("repaired S174 meta digest must remain non-authorizing custody")
    if rec.get("corrected_calibration", {}).get("sha256") != calibration_sha:
        raise RuntimeError("repaired S174 meta digest calibration binding mismatch")
    semantic = CORE._canonical_json_sha256(rec)
    if canonical:
        if semantic != EXPECTED_META_DIGEST_SEMANTIC_SHA256:
            raise RuntimeError("repaired S174 meta digest semantic SHA-256 mismatch")
        if rec.get("source_archive", {}).get("sha256") != EXPECTED_REPAIRED_ARCHIVE_SHA256:
            raise RuntimeError("repaired S174 archive SHA-256 mismatch")
    rows = rec.get("rows", [])
    if not isinstance(rows, list) or len(rows) != EXPECTED_N_SHARDS:
        raise RuntimeError("repaired S174 meta digest must contain exactly 42 rows")
    out: dict[str, str] = {}
    for row in rows:
        name = Path(str(row.get("file", ""))).name
        digest = str(row.get("sha256", ""))
        if not name.endswith(".meta.npz") or not CORE._is_sha256(digest):
            raise RuntimeError("malformed repaired S174 meta digest row")
        stem = name.removesuffix(".meta.npz")
        if stem in out:
            raise RuntimeError("duplicate repaired S174 meta stem")
        out[stem] = digest
    return rec, semantic, out


def build_from_corrected_cache(cache_root: Path, operator_mapping, corrected_calibration_path: Path,
                               meta_digest_path: Path, canonical: bool = True) -> dict:
    cache_root = Path(cache_root)
    if not cache_root.is_dir():
        raise FileNotFoundError(f"exact corrected TRAIN cache unavailable: {cache_root}")
    bridge_rec = CORE.validate_operator_bridge(operator_mapping)
    calibration_sha, count_by_stem = _count_receipt(corrected_calibration_path, canonical)
    meta_rec, meta_semantic, meta_by_stem = _meta_receipt(meta_digest_path, calibration_sha, canonical)
    bridge_stems = {str(row["stem"]) for row in operator_mapping["rows"]}
    if set(count_by_stem) != bridge_stems or set(meta_by_stem) != bridge_stems:
        raise RuntimeError("repaired S174 count/meta stems do not exactly match operator bridge")

    abundance_sum = np.zeros(EXPECTED_N_ADDRESSES, dtype=np.float64)
    abundance_n = np.zeros(EXPECTED_N_ADDRESSES, dtype=np.int64)
    operator_depth: dict[str, tuple[list[np.ndarray], list[np.ndarray], str]] = {}
    source_depth: dict[str, tuple[list[np.ndarray], list[np.ndarray]]] = {}
    global_lib: list[np.ndarray] = []
    global_det: list[np.ndarray] = []
    shard_receipts = []
    total_cells = 0

    for row in sorted(operator_mapping["rows"], key=lambda r: int(r["operator_index"])):
        oi, source, stem = int(row["operator_index"]), str(row["source"]), str(row["stem"])
        cp, mp = cache_root / f"{stem}.counts.npz", cache_root / f"{stem}.meta.npz"
        if not cp.is_file() or not mp.is_file():
            raise FileNotFoundError(f"corrected shard pair unavailable for stem {stem}")
        count_sha, meta_sha = CORE._sha256_file(cp), CORE._sha256_file(mp)
        if count_sha != count_by_stem[stem]:
            raise RuntimeError(f"count digest mismatch for stem {stem}")
        if meta_sha != meta_by_stem[stem]:
            raise RuntimeError(f"meta digest mismatch for stem {stem}")
        indices, indptr, data, n_cells = CORE._load_csr_counts(cp, EXPECTED_N_ADDRESSES)
        library = CORE._load_source_library(mp, n_cells)
        detected = np.diff(indptr).astype(np.float64)
        np.add.at(abundance_sum, indices, data)
        np.add.at(abundance_n, indices, 1)
        total_cells += n_cells
        global_lib.append(library)
        global_det.append(detected)
        operator_depth[str(oi)] = ([library], [detected], source)
        source_depth.setdefault(source, ([], []))[0].append(library)
        source_depth.setdefault(source, ([], []))[1].append(detected)
        shard_receipts.append({"file": cp.name, "sha256": count_sha,
                               "meta_file": mp.name, "meta_sha256": meta_sha})

    abundance = np.zeros(EXPECTED_N_ADDRESSES, dtype=np.float64)
    nz = abundance_n > 0
    abundance[nz] = abundance_sum[nz] / abundance_n[nz]
    depth = {
        "fallback_rule": FALLBACK_RULE,
        "quantile_probs": [float(x) for x in CORE.DEPTH_QUANTILE_PROBS],
        "global": CORE._depth_entry(np.concatenate(global_lib), np.concatenate(global_det)),
        "sources": {}, "operators": {},
    }
    for source, (libs, dets) in sorted(source_depth.items()):
        depth["sources"][source] = CORE._depth_entry(np.concatenate(libs), np.concatenate(dets))
    for op_key, (libs, dets, source) in sorted(operator_depth.items(), key=lambda kv: int(kv[0])):
        depth["operators"][op_key] = CORE._depth_entry(np.concatenate(libs), np.concatenate(dets), source=source)

    source_contract = {
        "pathology_blind": True, "train_only": True, "read_only": True,
        "registry_sha256": EXPECTED_REGISTRY_SHA256, "n_addresses": EXPECTED_N_ADDRESSES,
        "corrected_calibration_sha256": calibration_sha,
        "meta_digest_semantic_sha256": meta_semantic,
        "repaired_archive_sha256": meta_rec.get("source_archive", {}).get("sha256"),
        "operator_bridge_sha256": bridge_rec["bridge_sha256"],
        "fields_read": ["counts.indices", "counts.indptr", "counts.data", "meta.source_library"],
        "shard_digests": shard_receipts,
    }
    receipt = CORE.validate_source_contract(source_contract, canonical=True)
    out = {
        "schema": SCHEMA,
        "source": {
            "source_receipt_sha256": receipt["source_receipt_sha256"], "n_shards": 42,
            "n_cells": int(total_cells), "registry_sha256": EXPECTED_REGISTRY_SHA256,
            "corrected_calibration_sha256": calibration_sha,
            "meta_digest_manifest_sha256": CORE._sha256_file(meta_digest_path),
            "meta_digest_semantic_sha256": meta_semantic,
            "repaired_archive_sha256": meta_rec.get("source_archive", {}).get("sha256"),
            "operator_bridge_sha256": bridge_rec["bridge_sha256"],
            "paired_meta_manifest_verified": True,
            "fields_read": list(source_contract["fields_read"]),
        },
        "rank_scrubbed_abundance": CORE.build_rank_scrubbed_abundance_quantiles(abundance),
        "depth_marginals": depth,
        "canonical_corrected_train": bool(canonical), "training_authorized": False,
    }
    CORE.validate_runtime_authority(out)
    return out
