#!/usr/bin/env python3
"""V78 corrected-TRAIN marginal authority core.

This module intentionally separates two things:

1. governance/compact-authority mechanics, which are testable with synthetic fixtures; and
2. the canonical corrected-TRAIN build, which must fail closed unless the exact repaired
   cache bytes and an authenticated shard-to-operator bridge are physically available.

It must never reconstruct the canonical authority from calibration/envelope summaries.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

SCHEMA = "V78_MARGINAL_AUTHORITY_V1"
OPERATOR_BRIDGE_SCHEMA = "V78_S174_SHARD_OPERATOR_BRIDGE_V1"
EXPECTED_REGISTRY_SHA256 = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
EXPECTED_N_ADDRESSES = 41238
EXPECTED_N_SHARDS = 42
ABUNDANCE_PERMUTATION_STREAM = 14000
FALLBACK_MIN_CELLS = 50
FALLBACK_RULE = "operator_if_n>=50_else_source_if_n>=50_else_global"

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
    """Validate a custody bridge from corrected-cache shard stem to frozen operator index.

    The bridge is metadata-only and non-authorizing. It is allowed to carry matrix identity because
    it never enters synthetic biology or runtime model inputs; the compact F3 authority later stores
    only the derived stratum summaries and bridge digest.
    """
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
    """Fixture/general builder for already-authenticated, already-derived arrays.

    This is not the canonical cache reader. It exists so governance and compact-runtime
    contracts can be tested independently of possession of protected corrected TRAIN bytes.
    """
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


def build_from_corrected_cache(cache_root: Path, operator_mapping) -> dict:
    """Canonical entrypoint; deliberately fail closed until exact cache custody is present.

    The S174 rebuild's `source_library` metadata is the physical library total, not an operator
    identifier. Operator identity therefore comes only from the authenticated shard->matrix->operator
    bridge. Summary calibration JSON is not an acceptable substitute for corrected count bytes.
    """
    cache_root = Path(cache_root)
    if not cache_root.exists():
        raise FileNotFoundError(f"exact corrected TRAIN cache unavailable: {cache_root}")
    if operator_mapping is None:
        raise PermissionError(
            "authenticated corrected-shard -> observation-operator bridge is required; "
            "refusing to infer operator identity from source_library"
        )
    validate_operator_bridge(operator_mapping)
    raise RuntimeError(
        "canonical corrected-TRAIN authority build is not enabled until the exact 42 corrected "
        "count/meta shard bytes authenticate against the frozen S174 digest receipt"
    )
