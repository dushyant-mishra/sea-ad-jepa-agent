#!/usr/bin/env python3
"""V78 corrected-TRAIN marginal authority core.

The canonical builder reads only authenticated corrected S174 TRAIN count/meta shards,
uses the frozen shard->matrix->operator bridge, and emits a compact identity-scrubbed
runtime authority. It must never reconstruct the canonical authority from calibration
or envelope summaries.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

SCHEMA = "V78_MARGINAL_AUTHORITY_V1"
OPERATOR_BRIDGE_SCHEMA = "V78_S174_SHARD_OPERATOR_BRIDGE_V1"
EXPECTED_REGISTRY_SHA256 = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
EXPECTED_LOADER_MANIFEST_SHA256 = "2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328"
EXPECTED_N_ADDRESSES = 41238
EXPECTED_N_SHARDS = 42
ABUNDANCE_PERMUTATION_STREAM = 14000
FALLBACK_MIN_CELLS = 50
FALLBACK_RULE = "operator_if_n>=50_else_source_if_n>=50_else_global"
QUANTILE_PROBS = np.linspace(0.0, 1.0, 101, dtype=np.float64)

_DENY_FIELD_TOKENS = (
    "pathology", "diagnos", "braak", "cerad", "disease", "target", "query",
    "morbidity", "dement", "case_control", "case-control",
)
_RUNTIME_FORBIDDEN_KEYS = (
    "cache", "cache_path", "raw_cache", "address_to_abundance", "symbol_to_abundance",
    "ensembl_to_abundance", "gene_to_abundance", "marker_membership", "regulatory_membership",
)


def _canonical_json_sha256(obj: object) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _is_sha256(text: object) -> bool:
    if not isinstance(text, str) or len(text) != 64:
        return False
    try:
        int(text, 16)
    except ValueError:
        return False
    return True


def validate_source_contract(source: dict, canonical: bool = False) -> dict:
    if not isinstance(source, dict):
        raise TypeError("source contract must be a dict")
    for flag in ("pathology_blind", "train_only", "read_only"):
        if source.get(flag) is not True:
            raise PermissionError(f"source must declare {flag}=true")

    fields = [str(x) for x in source.get("fields_read", [])]
    for field in fields:
        low = field.lower()
        if any(token in low for token in _DENY_FIELD_TOKENS):
            raise PermissionError(f"forbidden corrected-TRAIN field in authority build: {field}")

    shards = source.get("shard_digests", [])
    if not isinstance(shards, list):
        raise RuntimeError("shard_digests must be a list")
    seen = set()
    for row in shards:
        if not isinstance(row, dict) or not row.get("file") or not _is_sha256(row.get("sha256")):
            raise RuntimeError("malformed shard digest receipt")
        if row["file"] in seen:
            raise RuntimeError("duplicate shard filename in source receipt")
        if "meta_sha256" in row and not _is_sha256(row.get("meta_sha256")):
            raise RuntimeError("malformed paired meta digest receipt")
        seen.add(row["file"])

    if canonical:
        if source.get("registry_sha256") != EXPECTED_REGISTRY_SHA256:
            raise RuntimeError("canonical registry sha256 mismatch")
        if int(source.get("n_addresses", -1)) != EXPECTED_N_ADDRESSES:
            raise RuntimeError("canonical address count mismatch")
        if len(shards) != EXPECTED_N_SHARDS:
            raise RuntimeError(f"canonical corrected TRAIN requires {EXPECTED_N_SHARDS} shards")

    return {
        "n_shards": len(shards),
        "fields_read": fields,
        "source_receipt_sha256": _canonical_json_sha256(source),
    }


def build_rank_scrubbed_abundance(per_address_positive_count_abundance: np.ndarray) -> dict:
    x = np.asarray(per_address_positive_count_abundance, dtype=np.float64)
    if x.ndim != 1 or len(x) == 0:
        raise ValueError("per-address abundance must be a nonempty 1-D array")
    if np.any(~np.isfinite(x)) or np.any(x < 0):
        raise ValueError("per-address abundance must be finite and nonnegative")
    pos = np.sort(x[x > 0])
    return {
        "identity_scrubbed": True,
        "rank_scrubbed": True,
        "n_addresses": int(len(x)),
        "n_zero": int((x == 0).sum()),
        "positive_abundance_sorted": [float(v) for v in pos],
        "assignment_stream": ABUNDANCE_PERMUTATION_STREAM,
        "content_policy": "EMPIRICAL_DISTRIBUTION_ONLY__IDENTITY_SCRUBBED",
    }


def _permutation(seed: int, n: int) -> np.ndarray:
    rng = np.random.default_rng(np.random.SeedSequence([int(seed), ABUNDANCE_PERMUTATION_STREAM]))
    return rng.permutation(int(n))


def assign_rank_scrubbed_abundance(authority: dict, seed: int, n_addresses: int) -> np.ndarray:
    n_addresses = int(n_addresses)
    if int(authority.get("n_addresses", -1)) != n_addresses:
        raise RuntimeError("abundance authority address count mismatch")
    if authority.get("identity_scrubbed") is not True or authority.get("rank_scrubbed") is not True:
        raise PermissionError("abundance authority is not identity/rank scrubbed")
    pos = np.asarray(authority.get("positive_abundance_sorted", []), dtype=np.float64)
    n_zero = int(authority.get("n_zero", n_addresses - len(pos)))
    if n_zero < 0 or n_zero + len(pos) != n_addresses:
        raise RuntimeError("abundance authority cardinality mismatch")
    values = np.concatenate([np.zeros(n_zero, dtype=np.float64), pos])
    order = _permutation(int(seed), n_addresses)
    out = np.empty(n_addresses, dtype=np.float64)
    out[order] = values
    return out


def choose_depth_stratum(operator_n: int, source_n: int) -> str:
    operator_n = int(operator_n)
    source_n = int(source_n)
    if operator_n < 0 or source_n < 0:
        raise ValueError("stratum counts must be nonnegative")
    if operator_n >= FALLBACK_MIN_CELLS:
        return "operator"
    if source_n >= FALLBACK_MIN_CELLS:
        return "source"
    return "global"


def validate_operator_bridge(bridge: dict) -> dict:
    if not isinstance(bridge, dict) or bridge.get("schema") != OPERATOR_BRIDGE_SCHEMA:
        raise RuntimeError("operator bridge schema mismatch")
    if bridge.get("claim_class") != "CUSTODY_DERIVATION__NON_AUTHORIZING":
        raise PermissionError("operator bridge must remain non-authorizing custody")
    source_bundle = bridge.get("source_bundle", {})
    source_member = bridge.get("source_member", {})
    if not _is_sha256(source_bundle.get("sha256")) or not _is_sha256(source_member.get("sha256")):
        raise RuntimeError("operator bridge lacks source digests")
    rows = bridge.get("rows", [])
    if not isinstance(rows, list) or len(rows) != EXPECTED_N_SHARDS:
        raise RuntimeError(f"operator bridge requires exactly {EXPECTED_N_SHARDS} rows")
    indices, matrices, stems = [], [], []
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("malformed operator bridge row")
        oi = int(row.get("operator_index", -1))
        matrix_id = str(row.get("matrix_id", ""))
        source = str(row.get("source", ""))
        stem = str(row.get("stem", ""))
        if source not in {"HVS", "SEA_AD", "NPH52"}:
            raise RuntimeError(f"unknown operator source {source!r}")
        if not matrix_id or not stem:
            raise RuntimeError("operator bridge row lacks matrix/stem")
        expected_stem = hashlib.sha256(("corrected|" + matrix_id).encode()).hexdigest()[:16]
        if stem != expected_stem:
            raise RuntimeError(f"operator bridge stem mismatch for {matrix_id}")
        indices.append(oi); matrices.append(matrix_id); stems.append(stem)
    if sorted(indices) != list(range(EXPECTED_N_SHARDS)):
        raise RuntimeError("operator bridge indices must be exactly 0..41")
    if len(set(matrices)) != EXPECTED_N_SHARDS or len(set(stems)) != EXPECTED_N_SHARDS:
        raise RuntimeError("operator bridge matrix IDs and stems must be one-to-one")
    return {
        "n_operators": EXPECTED_N_SHARDS,
        "operator_indices": sorted(indices),
        "bridge_sha256": _canonical_json_sha256(bridge),
        "source_bundle_sha256": source_bundle["sha256"],
        "source_member_sha256": source_member["sha256"],
    }


def _walk_keys(obj: object):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key).lower()
            yield from _walk_keys(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk_keys(value)


def validate_runtime_authority(authority: dict) -> dict:
    if not isinstance(authority, dict) or authority.get("schema") != SCHEMA:
        raise RuntimeError("V78 marginal authority schema mismatch")
    keys = set(_walk_keys(authority))
    bad = sorted(k for k in keys if k in _RUNTIME_FORBIDDEN_KEYS)
    if bad:
        raise PermissionError("runtime authority exposes forbidden raw/identity fields: " + ", ".join(bad))
    source = authority.get("source", {})
    if not _is_sha256(source.get("source_receipt_sha256")):
        raise RuntimeError("runtime authority lacks source receipt digest")
    abundance = authority.get("rank_scrubbed_abundance", {})
    if abundance.get("identity_scrubbed") is not True:
        raise PermissionError("runtime abundance is not identity scrubbed")
    depth = authority.get("depth_marginals", {})
    if depth.get("fallback_rule") != FALLBACK_RULE:
        raise RuntimeError("depth fallback rule mismatch")
    return authority


def build_from_arrays(source: dict, per_address_abundance: np.ndarray,
                      depth_marginals: dict, canonical: bool = False) -> dict:
    receipt = validate_source_contract(source, canonical=canonical)
    if depth_marginals.get("fallback_rule") != FALLBACK_RULE:
        raise RuntimeError("depth marginals do not use the preregistered fallback rule")
    out = {
        "schema": SCHEMA,
        "source": {
            "source_receipt_sha256": receipt["source_receipt_sha256"],
            "n_shards": receipt["n_shards"],
        },
        "rank_scrubbed_abundance": build_rank_scrubbed_abundance(per_address_abundance),
        "depth_marginals": dict(depth_marginals),
        "canonical_corrected_train": bool(canonical),
        "training_authorized": False,
    }
    validate_runtime_authority(out)
    return out


def _depth_entry(library: np.ndarray, detected: np.ndarray, source: str | None = None) -> dict:
    library = np.asarray(library, dtype=np.float64)
    detected = np.asarray(detected, dtype=np.float64)
    if library.ndim != 1 or detected.ndim != 1 or len(library) != len(detected) or len(library) == 0:
        raise RuntimeError("depth stratum must contain aligned nonempty vectors")
    if np.any(~np.isfinite(library)) or np.any(~np.isfinite(detected)) or np.any(library < 0) or np.any(detected < 0):
        raise RuntimeError("depth stratum contains invalid values")
    lx = np.log1p(library)
    dx = np.log1p(detected)
    if len(library) < 2 or float(np.std(lx)) == 0.0 or float(np.std(dx)) == 0.0:
        rho = 0.0
    else:
        rho = float(np.corrcoef(lx, dx)[0, 1])
        if not np.isfinite(rho):
            rho = 0.0
    rec = {
        "n_cells": int(len(library)),
        "library_quantiles": [float(x) for x in np.quantile(library, QUANTILE_PROBS)],
        "detected_quantiles": [float(x) for x in np.quantile(detected, QUANTILE_PROBS)],
        "log1p_library_vs_detected_pearson": rho,
    }
    if source is not None:
        rec["source"] = str(source)
    return rec


def _load_csr_counts(path: Path, n_addresses: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    with np.load(path, allow_pickle=False) as z:
        required = {"indices", "indptr", "shape", "data"}
        if not required.issubset(z.files):
            raise RuntimeError(f"corrected count shard lacks CSR arrays: {path.name}")
        indices = np.asarray(z["indices"], dtype=np.int64)
        indptr = np.asarray(z["indptr"], dtype=np.int64)
        shape = np.asarray(z["shape"], dtype=np.int64)
        data = np.asarray(z["data"], dtype=np.float64)
    if shape.shape != (2,) or int(shape[1]) != int(n_addresses):
        raise RuntimeError(f"corrected count shard address axis mismatch: {path.name}")
    n_cells = int(shape[0])
    if indptr.shape != (n_cells + 1,) or len(indices) != len(data):
        raise RuntimeError(f"corrected count shard CSR cardinality mismatch: {path.name}")
    if int(indptr[0]) != 0 or int(indptr[-1]) != len(indices) or np.any(np.diff(indptr) < 0):
        raise RuntimeError(f"corrected count shard CSR indptr invalid: {path.name}")
    if np.any(indices < 0) or np.any(indices >= n_addresses):
        raise RuntimeError(f"corrected count shard index outside registry: {path.name}")
    if np.any(~np.isfinite(data)) or np.any(data <= 0):
        raise RuntimeError(f"corrected count shard stored values must be finite positive counts: {path.name}")
    return indices, indptr, data, n_cells


def _load_source_library(path: Path, n_cells: int) -> np.ndarray:
    with np.load(path, allow_pickle=False) as z:
        if "source_library" not in z.files:
            raise RuntimeError(f"corrected meta shard lacks source_library: {path.name}")
        library = np.asarray(z["source_library"], dtype=np.float64)
    if library.shape != (n_cells,) or np.any(~np.isfinite(library)) or np.any(library <= 0):
        raise RuntimeError(f"corrected meta source_library invalid: {path.name}")
    return library


def build_from_corrected_cache(cache_root: Path, operator_mapping, loader_manifest_path: Path | None = None,
                               canonical: bool = True) -> dict:
    """Build F3 marginals from authenticated corrected TRAIN shard bytes only.

    Only sparse count arrays and the per-cell physical ``source_library`` field are read.
    Operator/source identity comes exclusively from the authenticated custody bridge.
    """
    cache_root = Path(cache_root)
    if not cache_root.is_dir():
        raise FileNotFoundError(f"exact corrected TRAIN cache unavailable: {cache_root}")
    if operator_mapping is None:
        raise PermissionError(
            "authenticated corrected-shard -> observation-operator bridge is required; "
            "refusing to infer operator identity from source_library"
        )
    bridge_rec = validate_operator_bridge(operator_mapping)
    if loader_manifest_path is None:
        raise FileNotFoundError("frozen production loader manifest is required")
    loader_manifest_path = Path(loader_manifest_path)
    if not loader_manifest_path.is_file():
        raise FileNotFoundError(f"production loader manifest unavailable: {loader_manifest_path}")
    manifest_sha = _sha256_file(loader_manifest_path)
    if canonical and manifest_sha != EXPECTED_LOADER_MANIFEST_SHA256:
        raise RuntimeError("frozen loader manifest SHA-256 mismatch")
    manifest = json.loads(loader_manifest_path.read_text())
    if manifest.get("schema") != "foundation-train-loader-v1":
        raise RuntimeError("production loader manifest schema mismatch")
    if int(manifest.get("address_count", -1)) != EXPECTED_N_ADDRESSES:
        raise RuntimeError("production loader manifest address count mismatch")
    if manifest.get("authority_hashes", {}).get("registry") != EXPECTED_REGISTRY_SHA256:
        raise RuntimeError("production loader manifest registry mismatch")
    mrows = manifest.get("shards", [])
    if not isinstance(mrows, list) or len(mrows) != EXPECTED_N_SHARDS:
        raise RuntimeError("production loader manifest must contain exactly 42 shards")
    by_matrix = {str(r.get("matrix_id")): r for r in mrows}
    if len(by_matrix) != EXPECTED_N_SHARDS:
        raise RuntimeError("production loader manifest matrix IDs are not unique")

    abundance_sum = np.zeros(EXPECTED_N_ADDRESSES, dtype=np.float64)
    abundance_n = np.zeros(EXPECTED_N_ADDRESSES, dtype=np.int64)
    operator_depth: dict[str, tuple[list[np.ndarray], list[np.ndarray], str]] = {}
    source_depth: dict[str, tuple[list[np.ndarray], list[np.ndarray]]] = {}
    global_lib: list[np.ndarray] = []
    global_det: list[np.ndarray] = []
    shard_receipts = []
    total_cells = 0

    for row in sorted(operator_mapping["rows"], key=lambda r: int(r["operator_index"])):
        oi = int(row["operator_index"])
        matrix_id = str(row["matrix_id"])
        source = str(row["source"])
        stem = str(row["stem"])
        expected = by_matrix.get(matrix_id)
        if expected is None:
            raise RuntimeError(f"loader manifest missing bridge matrix: {matrix_id}")
        cp = cache_root / f"{stem}.counts.npz"
        mp = cache_root / f"{stem}.meta.npz"
        if not cp.is_file() or not mp.is_file():
            raise FileNotFoundError(f"corrected shard pair unavailable for stem {stem}")
        count_sha = _sha256_file(cp)
        meta_sha = _sha256_file(mp)
        if count_sha != expected.get("counts_sha256"):
            raise RuntimeError(f"count digest mismatch for stem {stem}")
        if meta_sha != expected.get("meta_sha256"):
            raise RuntimeError(f"meta digest mismatch for stem {stem}")

        indices, indptr, data, n_cells = _load_csr_counts(cp, EXPECTED_N_ADDRESSES)
        library = _load_source_library(mp, n_cells)
        detected = np.diff(indptr).astype(np.float64)
        np.add.at(abundance_sum, indices, data)
        np.add.at(abundance_n, indices, 1)
        total_cells += n_cells
        global_lib.append(library)
        global_det.append(detected)
        operator_depth[str(oi)] = ([library], [detected], source)
        source_depth.setdefault(source, ([], []))[0].append(library)
        source_depth.setdefault(source, ([], []))[1].append(detected)
        shard_receipts.append({
            "file": cp.name,
            "sha256": count_sha,
            "meta_file": mp.name,
            "meta_sha256": meta_sha,
        })

    abundance = np.zeros(EXPECTED_N_ADDRESSES, dtype=np.float64)
    nz = abundance_n > 0
    abundance[nz] = abundance_sum[nz] / abundance_n[nz]

    depth = {
        "fallback_rule": FALLBACK_RULE,
        "quantile_probs": [float(x) for x in QUANTILE_PROBS],
        "global": _depth_entry(np.concatenate(global_lib), np.concatenate(global_det)),
        "sources": {},
        "operators": {},
    }
    for source, (libs, dets) in sorted(source_depth.items()):
        depth["sources"][source] = _depth_entry(np.concatenate(libs), np.concatenate(dets))
    for op_key, (libs, dets, source) in sorted(operator_depth.items(), key=lambda kv: int(kv[0])):
        depth["operators"][op_key] = _depth_entry(np.concatenate(libs), np.concatenate(dets), source=source)

    source = {
        "pathology_blind": True,
        "train_only": True,
        "read_only": True,
        "registry_sha256": EXPECTED_REGISTRY_SHA256,
        "n_addresses": EXPECTED_N_ADDRESSES,
        "loader_manifest_sha256": manifest_sha,
        "operator_bridge_sha256": bridge_rec["bridge_sha256"],
        "fields_read": ["counts.indices", "counts.indptr", "counts.data", "meta.source_library"],
        "shard_digests": shard_receipts,
    }
    receipt = validate_source_contract(source, canonical=True)
    out = {
        "schema": SCHEMA,
        "source": {
            "source_receipt_sha256": receipt["source_receipt_sha256"],
            "n_shards": receipt["n_shards"],
            "n_cells": int(total_cells),
            "registry_sha256": EXPECTED_REGISTRY_SHA256,
            "loader_manifest_sha256": manifest_sha,
            "operator_bridge_sha256": bridge_rec["bridge_sha256"],
            "paired_meta_manifest_verified": True,
            "fields_read": list(source["fields_read"]),
        },
        "rank_scrubbed_abundance": build_rank_scrubbed_abundance(abundance),
        "depth_marginals": depth,
        "canonical_corrected_train": bool(canonical),
        "training_authorized": False,
    }
    validate_runtime_authority(out)
    return out
