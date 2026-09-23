"""Outcome-blind canonical-source derivative of the frozen FULL104 heavy NPZ.

NOT a replacement of the original, a requalified heavy result, or N1 authority.
Pin the original file and ALL authenticated Level-4 metadata using PR67 first;
change only source_names and src_of_cell. An independently reviewed successor
qualification must bind the new SHA before N1 can be opened.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
from typing import Any, Mapping

import numpy as np

from sea_ad_jepa.v5 import audit_b_n1_source_lineage_v1 as lineage

SCHEMA = "V5_FULL104_N1_CANONICAL_SOURCE_DERIVATIVE_V1"
STATE = "METADATA_REPAIRED_DERIVATIVE__UNQUALIFIED__N1_STOP"
ALLOWED_CHANGES = frozenset({"source_names", "src_of_cell"})


def _array_record(value: np.ndarray) -> dict[str, Any]:
    """Stable, typed array digest. Object arrays may contain strings only."""
    arr = np.asarray(value)
    if arr.dtype.hasobject:
        if not all(isinstance(x, str) for x in arr.flat):
            raise ValueError("non-string object array is not eligible for derivative")
        data = json.dumps(arr.tolist(), sort_keys=True, ensure_ascii=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    else:
        data = np.ascontiguousarray(arr).tobytes()
    return {
        "dtype": arr.dtype.str, "shape": list(arr.shape),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _array_inventory(arrays: Mapping[str, np.ndarray]) -> dict[str, dict[str, Any]]:
    return {k: _array_record(arrays[k]) for k in sorted(arrays)}


def prepare_corrected_arrays(
    *, original: Mapping[str, np.ndarray], diagnostic: Mapping[str, Any],
) -> tuple[dict[str, np.ndarray], dict[str, dict[str, Any]]]:
    """Pure fail-closed transformation; must not accept synthetic approvals."""
    if (diagnostic.get("schema") != lineage.SCHEMA
            or diagnostic.get("role") !=
            "PHYSICAL_METADATA_DIAGNOSTIC_ONLY__NEVER_EXECUTION_AUTHORITY"
            or diagnostic.get("original_heavy_artifact_sha256") !=
            lineage.ORIGINAL_HEAVY_SHA256
            or diagnostic.get("full104_manifest_sha256") != lineage.MANIFEST_SHA256
            or diagnostic.get("metadata_blocks_sha_verified") != lineage.N_BLOCKS
            or diagnostic.get("metadata_cells_accounted_exactly_once") != lineage.N_CELLS
            or diagnostic.get("state") != "QUARANTINED_SOURCE_ENCODING__N1_STOP"
            or diagnostic.get("training_authorized") is not False
            or diagnostic.get("burden_calculated") is not False
            or diagnostic.get("masks_executed") is not False):
        raise ValueError("requires full physical quarantine diagnostic for ORIGINAL NPZ")
    recorded = diagnostic.get("receipt_sha256")
    body = {k: v for k, v in diagnostic.items() if k != "receipt_sha256"}
    if recorded != lineage.canonical_digest(body):
        raise ValueError("physical source diagnostic self-digest mismatch")
    keys = set(original)
    if not {"donor_src", "duniq", "source_names", "src_of_cell"}.issubset(keys):
        raise ValueError("original heavy NPZ missing source identity arrays")
    old_names_array = np.asarray(original["source_names"])
    old_names = [str(x) for x in old_names_array.tolist()]
    if (len(old_names) != 3 or set(old_names) != set(lineage.SOURCES)
            or old_names != diagnostic.get("stored_source_names")):
        raise ValueError("wrong or unauthenticated original source_names")
    donor_src = np.asarray(original["donor_src"])
    original_src = np.asarray(original["src_of_cell"])
    if donor_src.dtype != np.int64 or donor_src.shape != (lineage.N_DONORS,):
        raise ValueError("donor_src geometry/dtype differs from frozen FULL104")
    if original_src.dtype != np.int64 or original_src.shape != (lineage.N_CELLS,):
        raise ValueError("src_of_cell geometry/dtype differs from frozen FULL104")
    if np.any((original_src < 0) | (original_src > 2)):
        raise ValueError("original per-cell source code outside stored source registry")
    if lineage.int64_digest(donor_src) != diagnostic.get(
        "canonical_donor_source_vector_sha256"
    ):
        raise ValueError("donor_src was changed after metadata diagnostic")
    if lineage.int64_digest(original_src) != diagnostic.get(
        "stored_per_cell_source_sha256"
    ):
        raise ValueError("src_of_cell was changed after metadata diagnostic")
    if diagnostic.get("source_name_order_matches") is not False:
        raise ValueError("original source-name ordering not quarantined")
    # Correct codes by SOURCE NAME (not guessed by counts or index swapping).
    remap = np.asarray([lineage.SOURCES.index(n) for n in old_names], dtype=np.int64)
    corrected = remap[original_src]
    if lineage.int64_digest(corrected) != diagnostic.get(
        "metadata_source_vector_sha256"
    ):
        raise ValueError(
            "corrected source vector differs from SHA-authenticated Level-4 metadata"
        )
    if diagnostic.get("src_of_cell_mismatch_count") != int(
        np.count_nonzero(corrected != original_src)
    ):
        raise ValueError("original mismatch count does not match physical diagnostic")
    updated = dict(original)
    updated["source_names"] = np.asarray(lineage.SOURCES, dtype=old_names_array.dtype)
    updated["src_of_cell"] = corrected
    old_records = _array_inventory(original)
    new_records = _array_inventory(updated)
    changes = {key for key in old_records if old_records[key] != new_records[key]}
    if changes != ALLOWED_CHANGES or set(new_records) != keys:
        raise ValueError("derivative did not change exactly the two approved source arrays")
    return updated, old_records


def materialize_canonical_source_derivative(
    *, heavy_artifact: Path, level4_root: Path, out: Path, out_receipt: Path,
) -> dict[str, Any]:
    """Create a separately named derivative + non-authoritative evidence receipt.

    Read ONLY the old heavy NPZ + Level-4 metadata (never raw count matrices).
    Never replace the original or overwrite an existing derivative/receipt.
    """
    original_path = Path(heavy_artifact).resolve()
    out = Path(out).resolve()
    out_receipt = Path(out_receipt).resolve()
    if len({original_path, out, out_receipt}) != 3:
        raise ValueError("original, derivative and receipt paths must be distinct")
    if (out.exists() or out_receipt.exists()
            or not out.name.endswith(".npz")):
        raise ValueError("derivative and receipt must be new files; out must be NPZ")
    if lineage.sha256_file(original_path) != lineage.ORIGINAL_HEAVY_SHA256:
        raise ValueError("original heavy NPZ bytes changed")
    diagnostic = lineage.audit_original_heavy_source_lineage(
        heavy_artifact=original_path, level4_root=level4_root,
    )
    if diagnostic.get("state") != "QUARANTINED_SOURCE_ENCODING__N1_STOP":
        raise ValueError("expected original source encoding discrepancy not reproduced")
    with np.load(original_path, allow_pickle=True) as z:
        original = {k: z[k] for k in z.files}
    updated, old_records = prepare_corrected_arrays(
        original=original, diagnostic=diagnostic,
    )
    expected_inventory = _array_inventory(updated)
    out.parent.mkdir(parents=True, exist_ok=True)
    out_receipt.parent.mkdir(parents=True, exist_ok=True)
    intent = out.with_name(out.name + ".repair.intent.json")
    fd = os.open(str(intent), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump({
            "schema": "V5_N1_SOURCE_DERIVATIVE_INTENT_V1",
            "original_heavy_sha256": lineage.ORIGINAL_HEAVY_SHA256,
            "diagnostic_receipt_sha256": diagnostic["receipt_sha256"],
            "result_path": str(out), "training_authorized": False,
        }, handle, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    staged = out.with_name("." + out.name + ".staged-" + secrets.token_hex(8))
    with staged.open("xb+") as handle:
        np.savez_compressed(handle, **updated)
        handle.flush()
        os.fsync(handle.fileno())
    with np.load(staged, allow_pickle=True) as z:
        if set(z.files) != set(updated):
            raise ValueError("staged derivative lost an array")
        observed_inventory = _array_inventory({k: z[k] for k in z.files})
    if observed_inventory != expected_inventory:
        raise ValueError("staged derivative changed array bytes, dtype, or shape")
    result_sha = lineage.sha256_file(staged)
    os.replace(staged, out)
    payload = {
        "schema": SCHEMA,
        "state": STATE,
        "original_heavy_sha256": lineage.ORIGINAL_HEAVY_SHA256,
        "derivative_file_sha256": result_sha,
        "derivative_file_bytes": out.stat().st_size,
        "full104_manifest_sha256": lineage.MANIFEST_SHA256,
        "original_diagnostic_receipt_sha256": diagnostic["receipt_sha256"],
        "old_array_inventory": old_records,
        "derivative_array_inventory": observed_inventory,
        "changed_arrays": sorted(ALLOWED_CHANGES),
        "independent_requalification_required": True,
        "n1_executed": False,
        "masks_executed": False,
        "burden_calculated": False,
        "precision_calculated": False,
        "rare_tail_molecular_opened": False,
        "training_authorized": False,
    }
    payload["receipt_sha256"] = lineage.canonical_digest(payload)
    receipt_stage = out_receipt.with_name("." + out_receipt.name + ".staged-" +
                                          secrets.token_hex(8))
    fd = os.open(str(receipt_stage), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(receipt_stage, out_receipt)
    return payload
