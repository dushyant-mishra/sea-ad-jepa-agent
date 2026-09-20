"""Build the FULL104 census pass1 artifact from authenticated physical bytes.

The September-17 pass1 was an ad-hoc scratch artifact whose per-cell vectors were
indexed by *block iteration order*. That is a storage property: repacking the
Level-4 store would silently change every array. The authoritative global cell
identity is ``selection_row`` from the physical block metadata, and this builder
uses it exclusively.

Two orderings are declared explicitly here, and neither depends on traversal:

``CELL_IDENTITY_RULE``
    ``cell_donor[selection_row]`` / ``cell_nnz_core[selection_row]``. Every one of
    the 4,553,407 selection rows must be written exactly once, which makes the
    result independent of block order and of row order within a block.

``DONOR_ORDER_RULE``
    ``duniq = sorted(unique physical donor_id)`` -- a lexicographic sort of the
    donor identity strings. This is storage-independent and reproducible from the
    metadata alone. It is preserved deliberately rather than re-invented: the
    source-stratified outer split assigns folds by donor index, so changing donor
    order would change the split.

This module only *builds*. Verification remains the sole responsibility of
``full104_pass1_physical_binding_v1.verify_pass1_against_physical_full104``,
which is not weakened or bypassed here.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import scipy.sparse as sp

from .full104_masking_qualification_runner_v1 import (
    infer_strict_measured_scalar_common_core,
)
from .full104_pass1_physical_binding_v1 import (
    CANONICAL_REGISTRY_SHA256,
    _load_observation_matrix,
    _load_registry,
    EXPECTED_ADDRESSES,
    EXPECTED_BLOCKS,
    EXPECTED_CORE,
    EXPECTED_DONORS,
    EXPECTED_OPERATORS,
    EXPECTED_ROWS,
    FULL104_BLOCK_MANIFEST_SHA256,
    OBSERVATION_STATE_SHA256,
    SOURCE_NAMES,
    _resolve_under,
)
from .full104_physical_shakedown_v1 import (
    MANIFEST_COLUMNS,
    META_COLUMNS,
    sha256_file,
)

CELL_IDENTITY_RULE = "GLOBAL_SELECTION_ROW_IDENTITY_V1"
DONOR_ORDER_RULE = "SORTED_UNIQUE_PHYSICAL_DONOR_ID_V1"
BUILDER_SCHEMA_ID = "V5_FULL104_PASS1_PHYSICAL_BUILDER_V1"

PASS1_ARRAYS = ("cell_donor", "cell_nnz_core", "donor_addr_nnz", "donor_src", "duniq", "core")


@dataclass(frozen=True)
class Full104Pass1BuildSummaryV1:
    builder_schema_id: str
    cell_identity_rule_id: str
    donor_order_rule_id: str
    block_count: int
    row_count: int
    donor_count: int
    operator_count: int
    address_count: int
    strict_core_count: int
    total_core_nnz: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "builder_schema_id": self.builder_schema_id,
            "cell_identity_rule_id": self.cell_identity_rule_id,
            "donor_order_rule_id": self.donor_order_rule_id,
            "block_count": self.block_count,
            "row_count": self.row_count,
            "donor_count": self.donor_count,
            "operator_count": self.operator_count,
            "address_count": self.address_count,
            "strict_core_count": self.strict_core_count,
            "total_core_nnz": self.total_core_nnz,
        }


def _read_manifest(level4_root: Path, *, expect_hashes: bool) -> list[dict[str, str]]:
    manifest_path = level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if expect_hashes and sha256_file(manifest_path) != FULL104_BLOCK_MANIFEST_SHA256:
        raise ValueError("FULL104 block manifest root mismatch")
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != MANIFEST_COLUMNS:
            raise ValueError("FULL104 block manifest schema mismatch")
        manifest = [dict(row) for row in reader]
    if expect_hashes:
        if len(manifest) != EXPECTED_BLOCKS:
            raise ValueError("FULL104 block manifest block count mismatch")
        if len({row["block_key"] for row in manifest}) != len(manifest):
            raise ValueError("FULL104 block manifest contains duplicate block keys")
        if len({int(row["operator_index"]) for row in manifest}) != EXPECTED_OPERATORS:
            raise ValueError("FULL104 operator count mismatch")
        if tuple(sorted({str(row["source"]) for row in manifest})) != tuple(sorted(SOURCE_NAMES)):
            raise ValueError("FULL104 source identities mismatch")
    return manifest


def derive_canonical_donor_registry(
    level4_root: Path, *, expect_hashes: bool = True
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(duniq, donor_src)`` under :data:`DONOR_ORDER_RULE`.

    Reads metadata only. Fails closed if any donor maps to more than one source.
    """
    manifest = _read_manifest(level4_root, expect_hashes=expect_hashes)
    source_to_code = {name: i for i, name in enumerate(SOURCE_NAMES)}
    donor_to_source: dict[str, int] = {}

    for row in manifest:
        meta_path = _resolve_under(level4_root, row["meta_path"])
        if expect_hashes and sha256_file(meta_path) != row["meta_sha256"]:
            raise ValueError(f"FULL104 metadata hash mismatch: {row['block_key']}")
        source = str(row["source"])
        if source not in source_to_code:
            raise ValueError(f"unknown FULL104 source identity: {source!r}")
        code = source_to_code[source]
        with meta_path.open(newline="", encoding="utf-8") as handle:
            meta_reader = csv.DictReader(handle)
            if tuple(meta_reader.fieldnames or ()) != META_COLUMNS:
                raise ValueError(f"FULL104 metadata schema mismatch: {row['block_key']}")
            for meta in meta_reader:
                donor_id = str(meta["donor_id"])
                if not donor_id:
                    raise ValueError("physical metadata contains an empty donor_id")
                previous = donor_to_source.get(donor_id)
                if previous is None:
                    donor_to_source[donor_id] = code
                elif previous != code:
                    raise ValueError(
                        f"donor {donor_id!r} maps to more than one physical source"
                    )

    duniq = np.array(sorted(donor_to_source), dtype=object)
    donor_src = np.array([donor_to_source[str(d)] for d in duniq], dtype=np.int64)
    return duniq, donor_src



def _load_unauthenticated_observation_matrix(path: Path) -> np.ndarray:
    """Load an operator x address uint8 state matrix WITHOUT root authentication.

    Only reachable when ``expect_reference_geometry`` is False, i.e. from
    synthetic regression fixtures. The authenticated path always goes through
    ``full104_pass1_physical_binding_v1._load_observation_matrix``.
    """
    loaded = np.load(path, allow_pickle=False)
    if isinstance(loaded, np.lib.npyio.NpzFile):
        try:
            candidates = [
                np.asarray(loaded[key])
                for key in loaded.files
                if np.asarray(loaded[key]).ndim == 2
                and np.asarray(loaded[key]).dtype == np.uint8
            ]
            if len(candidates) != 1:
                raise ValueError(
                    "fixture observation NPZ must contain exactly one uint8 matrix"
                )
            return candidates[0]
        finally:
            loaded.close()
    value = np.asarray(loaded)
    if value.ndim != 2 or value.dtype != np.uint8:
        raise ValueError("fixture observation matrix must be a uint8 2-D array")
    return value


def build_pass1_from_physical_full104(
    *,
    level4_root: Path,
    registry_path: Path,
    observation_state_path: Path,
    out_path: Path,
    expect_reference_geometry: bool = True,
) -> Full104Pass1BuildSummaryV1:
    """Build pass1 keyed to ``selection_row`` and write it, refusing overwrite.

    ``expect_reference_geometry`` enforces the exact current FULL104 constants and
    input hashes. Synthetic regression fixtures set it False to exercise ordering
    invariance on small substrates.
    """
    level4_root = Path(level4_root)
    out_path = Path(out_path)
    if out_path.exists():
        raise ValueError(f"refuse to overwrite an existing pass1 artifact: {out_path}")

    if expect_reference_geometry:
        # These helpers authenticate the canonical registry and observation-state
        # roots against the frozen current-FULL104 digests.
        _load_registry(Path(registry_path))
        observation = _load_observation_matrix(Path(observation_state_path))
    else:
        observation = _load_unauthenticated_observation_matrix(
            Path(observation_state_path)
        )
    n_addresses = int(np.asarray(observation).shape[1])
    expected_core = int(EXPECTED_CORE) if expect_reference_geometry else None
    if expected_core is None:
        # Synthetic fixtures declare their own core size; derive it from the
        # observation matrix using the same strict MEASURED_SCALAR rule.
        states = np.asarray(observation)
        expected_core = int((states == 1).all(axis=0).sum())
    _state_code, core = infer_strict_measured_scalar_common_core(
        observation,
        expected_size=expected_core,
    )
    core = np.asarray(core, dtype=np.int64)
    if expect_reference_geometry:
        if core.size != EXPECTED_CORE:
            raise ValueError("strict core does not equal the current FULL104 core size")
        if n_addresses != EXPECTED_ADDRESSES:
            raise ValueError("observation state address width mismatch")

    duniq, donor_src = derive_canonical_donor_registry(
        level4_root, expect_hashes=expect_reference_geometry
    )
    n_donors = int(duniq.size)
    if expect_reference_geometry and n_donors != EXPECTED_DONORS:
        raise ValueError("physical donor registry does not contain exactly 104 donors")
    donor_to_code = {str(d): i for i, d in enumerate(duniq)}

    manifest = _read_manifest(level4_root, expect_hashes=expect_reference_geometry)
    n_rows = int(EXPECTED_ROWS) if expect_reference_geometry else sum(
        int(row["rows"]) for row in manifest
    )

    cell_donor = np.full(n_rows, -1, dtype=np.int64)
    cell_nnz_core = np.full(n_rows, -1, dtype=np.int64)
    donor_addr_nnz = np.zeros((n_donors, n_addresses), dtype=np.int64)
    seen_selection = np.zeros(n_rows, dtype=np.bool_)
    total_rows = 0
    total_core_nnz = 0

    for row in manifest:
        counts_path = _resolve_under(level4_root, row["counts_path"])
        meta_path = _resolve_under(level4_root, row["meta_path"])
        if expect_reference_geometry:
            if sha256_file(counts_path) != row["counts_sha256"]:
                raise ValueError(f"FULL104 counts hash mismatch: {row['block_key']}")
            if sha256_file(meta_path) != row["meta_sha256"]:
                raise ValueError(f"FULL104 metadata hash mismatch: {row['block_key']}")

        matrix = sp.load_npz(counts_path).tocsr()
        expected_rows = int(row["rows"])
        if matrix.shape != (expected_rows, n_addresses):
            raise ValueError(f"FULL104 counts geometry mismatch: {row['block_key']}")
        if matrix.nnz != int(row["nnz"]):
            raise ValueError(f"FULL104 counts nnz mismatch: {row['block_key']}")

        with meta_path.open(newline="", encoding="utf-8") as handle:
            meta_reader = csv.DictReader(handle)
            if tuple(meta_reader.fieldnames or ()) != META_COLUMNS:
                raise ValueError(f"FULL104 metadata schema mismatch: {row['block_key']}")
            selection = []
            block_donor_codes = []
            for meta in meta_reader:
                donor_id = str(meta["donor_id"])
                if donor_id not in donor_to_code:
                    raise ValueError("physical metadata donor absent from derived registry")
                selection.append(int(meta["selection_row"]))
                block_donor_codes.append(donor_to_code[donor_id])

        selection_arr = np.asarray(selection, dtype=np.int64)
        donor_codes = np.asarray(block_donor_codes, dtype=np.int64)
        if selection_arr.shape != (expected_rows,) or donor_codes.shape != (expected_rows,):
            raise ValueError(f"FULL104 metadata row count mismatch: {row['block_key']}")
        if np.any(selection_arr < 0) or np.any(selection_arr >= n_rows):
            raise ValueError("physical selection_row is out of range")
        if np.unique(selection_arr).size != selection_arr.size:
            raise ValueError(f"duplicate selection_row within block {row['block_key']}")
        if np.any(seen_selection[selection_arr]):
            raise ValueError("duplicate physical selection_row across FULL104 blocks")
        seen_selection[selection_arr] = True

        # Write by global scientific identity, never by traversal position.
        cell_donor[selection_arr] = donor_codes

        core_block = matrix[:, core].tocsr()
        row_core_nnz = np.diff(core_block.indptr).astype(np.int64, copy=False)
        cell_nnz_core[selection_arr] = row_core_nnz
        total_core_nnz += int(row_core_nnz.sum())

        block_csc = matrix.tocsc()
        for donor_code in np.unique(donor_codes):
            local_rows = np.flatnonzero(donor_codes == int(donor_code))
            donor_addr_nnz[int(donor_code)] += np.asarray(
                block_csc[local_rows].getnnz(axis=0), dtype=np.int64
            ).reshape(-1)

        total_rows += expected_rows

    if total_rows != n_rows or not np.all(seen_selection):
        raise ValueError("pass1 build did not close over every FULL104 selection row")
    if np.any(cell_donor < 0) or np.any(cell_nnz_core < 0):
        raise ValueError("pass1 build left unfilled cell positions")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_path,
        cell_donor=cell_donor,
        cell_nnz_core=cell_nnz_core,
        donor_addr_nnz=donor_addr_nnz,
        donor_src=donor_src,
        duniq=np.asarray([str(d) for d in duniq]),
        core=core,
    )

    return Full104Pass1BuildSummaryV1(
        builder_schema_id=BUILDER_SCHEMA_ID,
        cell_identity_rule_id=CELL_IDENTITY_RULE,
        donor_order_rule_id=DONOR_ORDER_RULE,
        block_count=len(manifest),
        row_count=int(total_rows),
        donor_count=n_donors,
        operator_count=len({int(r["operator_index"]) for r in manifest}),
        address_count=n_addresses,
        strict_core_count=int(core.size),
        total_core_nnz=int(total_core_nnz),
    )
