"""Read-only FULL104 N1 source-lineage diagnostic for the ORIGINAL heavy NPZ.

This successor independently checks canonical source identity against every
SHA-verified Level-4 *metadata* block. It deliberately opens NO count matrices,
repairs NO frozen input, computes NO burden, and grants NO N1 authority.

The original heavy artifact has an already documented source-label disagreement.
For that artifact, a completed diagnostic is expected to be QUARANTINED, not PASS.
Do not turn this into a bypass or use a caller-supplied replacement source_names.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

import numpy as np

ORIGINAL_HEAVY_SHA256 = (
    "f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae"
)
MANIFEST_SHA256 = (
    "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
)
SOURCES = ("HVS", "NPH52", "SEA_AD")
SOURCE_DONORS = (41, 17, 46)
SOURCE_CELLS = (198_718, 236_476, 4_118_213)
N_DONORS = 104
N_CELLS = 4_553_407
N_BLOCKS = 8_915
SCHEMA = "V5_FULL104_N1_SOURCE_LINEAGE_DIAGNOSTIC_V1"
META_COLUMNS = (
    "selection_row", "canonical_cell_id", "donor_id",
    "expression_row", "primary_row_weight", "source_library",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def int64_digest(value: np.ndarray) -> str:
    arr = np.asarray(value)
    if arr.dtype != np.int64:
        raise ValueError("source-lineage array must be exact int64")
    return hashlib.sha256(
        np.ascontiguousarray(arr, dtype="<i8").tobytes()
    ).hexdigest()


def canonical_digest(data: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"),
                   allow_nan=False, ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def assess_source_vectors(
    *,
    donor_names: list[str],
    donor_source_code: np.ndarray,
    stored_source_names: list[str],
    stored_per_cell_source: np.ndarray,
    metadata_cell_donor: np.ndarray,
    metadata_cell_source: np.ndarray,
    expected_cells: int = N_CELLS,
    expected_source_cells: tuple[int, int, int] = SOURCE_CELLS,
) -> dict[str, Any]:
    """Pure fail-closed role check; wrong stored labels yield quarantine.

    The independent metadata source and donor mappings MUST agree first.
    A mismatch there is more serious than the known NPZ label permutation.
    """
    donor_src = np.asarray(donor_source_code)
    src_of_cell = np.asarray(stored_per_cell_source)
    cell_donor = np.asarray(metadata_cell_donor)
    meta_src = np.asarray(metadata_cell_source)
    if len(donor_names) != N_DONORS or donor_names != sorted(set(donor_names)):
        raise ValueError("donor registry is not the canonical sorted FULL104 registry")
    for name, arr, shape in (
        ("donor_source_code", donor_src, (N_DONORS,)),
        ("stored_per_cell_source", src_of_cell, (expected_cells,)),
        ("metadata_cell_donor", cell_donor, (expected_cells,)),
        ("metadata_cell_source", meta_src, (expected_cells,)),
    ):
        if not isinstance(arr, np.ndarray) or arr.dtype != np.int64 or arr.shape != shape:
            raise ValueError(f"{name} must be exact int64 geometry {shape}")
    if np.any(donor_src < 0) or np.any(donor_src >= len(SOURCES)):
        raise ValueError("donor source code outside canonical source registry")
    if not np.array_equal(np.bincount(donor_src, minlength=3), SOURCE_DONORS):
        raise ValueError("donor source count drift")
    if np.any(cell_donor < 0) or np.any(cell_donor >= N_DONORS):
        raise ValueError("metadata cell donor outside canonical donor registry")
    if np.any(meta_src < 0) or np.any(meta_src >= len(SOURCES)):
        raise ValueError("metadata cell source outside canonical source registry")
    if not np.array_equal(np.bincount(meta_src, minlength=3), expected_source_cells):
        raise ValueError("metadata source cell census drift")
    expected = donor_src[cell_donor]
    if not np.array_equal(meta_src, expected):
        raise ValueError(
            "authenticated Level-4 donor/source rows disagree with donor_src; "
            "this is NOT the known first-appearance label permutation"
        )
    name_ok = tuple(stored_source_names) == SOURCES
    cell_ok = bool(np.array_equal(src_of_cell, expected))
    bad = int(np.count_nonzero(src_of_cell != expected))
    return {
        "state": (
            "CANONICAL_SOURCE_ALIGNMENT_OBSERVED__DIAGNOSTIC_ONLY"
            if name_ok and cell_ok else "QUARANTINED_SOURCE_ENCODING__N1_STOP"
        ),
        "stored_source_names": list(stored_source_names),
        "canonical_source_names": list(SOURCES),
        "source_name_order_matches": name_ok,
        "src_of_cell_equals_donor_src_at_metadata_donor": cell_ok,
        "src_of_cell_mismatch_count": bad,
        "donor_source_counts": list(SOURCE_DONORS),
        "metadata_cell_source_counts": list(expected_source_cells),
        "canonical_donor_source_vector_sha256": int64_digest(donor_src),
        "stored_per_cell_source_sha256": int64_digest(src_of_cell),
        "metadata_donor_vector_sha256": int64_digest(cell_donor),
        "metadata_source_vector_sha256": int64_digest(meta_src),
    }


def audit_original_heavy_source_lineage(
    *, heavy_artifact: Path, level4_root: Path,
) -> dict[str, Any]:
    """Authenticate original NPZ and all 8,915 metadata blocks; no RNA access."""
    heavy = Path(heavy_artifact)
    root = Path(level4_root).resolve()
    manifest = root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if sha256_file(heavy) != ORIGINAL_HEAVY_SHA256:
        raise ValueError("original heavy NPZ physical SHA mismatch")
    if sha256_file(manifest) != MANIFEST_SHA256:
        raise ValueError("FULL104 manifest physical SHA mismatch")

    with np.load(heavy, allow_pickle=True) as artifact:
        mandatory = {"duniq", "donor_src", "source_names", "src_of_cell"}
        if not mandatory.issubset(artifact.files):
            raise ValueError("heavy NPZ missing source-lineage fields")
        donor_names = [str(x) for x in artifact["duniq"]]
        donor_src = artifact["donor_src"]
        names = [str(x) for x in artifact["source_names"]]
        src_of_cell = artifact["src_of_cell"]

    with manifest.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != N_BLOCKS or len({r["block_key"] for r in rows}) != N_BLOCKS:
        raise ValueError("FULL104 metadata manifest must contain 8,915 unique blocks")
    if donor_names != sorted(set(donor_names)) or len(donor_names) != N_DONORS:
        raise ValueError("heavy donor registry is not sorted unique FULL104")
    codes = {name: i for i, name in enumerate(donor_names)}
    code_by_source = {name: i for i, name in enumerate(SOURCES)}
    seen = np.zeros(N_CELLS, dtype=np.bool_)
    cell_donor = np.full(N_CELLS, -1, dtype=np.int64)
    cell_source = np.full(N_CELLS, -1, dtype=np.int64)
    count = 0
    for row in rows:
        source = row.get("source")
        if source not in code_by_source:
            raise ValueError("unrecognized manifest source")
        relative = Path(row["meta_path"])
        if relative.is_absolute():
            raise ValueError("absolute metadata path forbidden")
        metadata_path = (root / relative).resolve()
        metadata_path.relative_to(root)
        if sha256_file(metadata_path) != row["meta_sha256"]:
            raise ValueError("Level-4 metadata physical SHA mismatch")
        with metadata_path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if tuple(reader.fieldnames or ()) != META_COLUMNS:
                raise ValueError("Level-4 metadata schema mismatch")
            records = list(reader)
        if len(records) != int(row["rows"]):
            raise ValueError("Level-4 block metadata row count drift")
        sel = np.asarray([int(r["selection_row"]) for r in records], dtype=np.int64)
        if np.any(sel < 0) or np.any(sel >= N_CELLS):
            raise ValueError("out-of-range cell selection_row")
        if np.unique(sel).size != sel.size or np.any(seen[sel]):
            raise ValueError("duplicate cell selection_row within/across blocks")
        try:
            donor = np.asarray([codes[r["donor_id"]] for r in records], dtype=np.int64)
        except KeyError as exc:
            raise ValueError("metadata contains donor absent from frozen NPZ") from exc
        seen[sel] = True
        cell_donor[sel] = donor
        cell_source[sel] = code_by_source[source]
        count += sel.size
    if count != N_CELLS or not np.all(seen):
        raise ValueError("FULL104 Level-4 metadata does not close exactly once")

    result = assess_source_vectors(
        donor_names=donor_names,
        donor_source_code=donor_src,
        stored_source_names=names,
        stored_per_cell_source=src_of_cell,
        metadata_cell_donor=cell_donor,
        metadata_cell_source=cell_source,
    )
    body = {
        "schema": SCHEMA,
        "role": "PHYSICAL_METADATA_DIAGNOSTIC_ONLY__NEVER_EXECUTION_AUTHORITY",
        "original_heavy_artifact_sha256": ORIGINAL_HEAVY_SHA256,
        "full104_manifest_sha256": MANIFEST_SHA256,
        "metadata_blocks_sha_verified": N_BLOCKS,
        "metadata_cells_accounted_exactly_once": N_CELLS,
        **result,
        "n1_targets_selected": False,
        "masks_executed": False,
        "burden_calculated": False,
        "precision_calculated": False,
        "training_authorized": False,
    }
    return {**body, "receipt_sha256": canonical_digest(body)}
