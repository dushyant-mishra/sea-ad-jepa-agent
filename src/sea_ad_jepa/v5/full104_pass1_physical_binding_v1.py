"""Physical provenance verifier for the FULL104 census pass1 artifact.

The pass1 NPZ is a derived acceleration artifact, not an authority by itself.
This module binds it back to the authenticated Level-4 counts/metadata, canonical
registry, and operator x address observation-state bytes before any census,
split, or target-eligibility receipt may use it.

No masking-policy, protected, pathology, D_shared, or training outcome is read.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import scipy.sparse as sp

from .full104_masking_qualification_runner_v1 import (
    infer_strict_measured_scalar_common_core,
)
from .full104_physical_shakedown_v1 import (
    MANIFEST_COLUMNS,
    META_COLUMNS,
    _parse_source_library,
    sha256_file,
)

FULL104_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
CANONICAL_REGISTRY_SHA256 = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
OBSERVATION_STATE_SHA256 = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"

EXPECTED_BLOCKS = 8_915
EXPECTED_ROWS = 4_553_407
EXPECTED_DONORS = 104
EXPECTED_OPERATORS = 42
EXPECTED_ADDRESSES = 41_238
EXPECTED_CORE = 17_186
SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")
SCHEMA_ID = "V5_FULL104_PASS1_PHYSICAL_BINDING_RECEIPT_V1"


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _array_digest(value: np.ndarray) -> str:
    arr = np.ascontiguousarray(value)
    h = hashlib.sha256()
    h.update(str(arr.dtype).encode("ascii"))
    h.update(b"|")
    h.update(",".join(map(str, arr.shape)).encode("ascii"))
    h.update(b"|")
    h.update(memoryview(arr).cast("B"))
    return h.hexdigest()


def _string_vector_digest(values: np.ndarray) -> str:
    """Canonical, platform-independent digest for string identity vectors."""

    items = [str(item) for item in np.asarray(values).reshape(-1)]
    return _canonical_sha(
        {
            "schema": "V5_CANONICAL_STRING_VECTOR_V1",
            "shape": [len(items)],
            "values": items,
        }
    )


def _resolve_under(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute():
        raise ValueError("FULL104 manifest path must be relative")
    resolved_root = root.resolve()
    path = (resolved_root / rel).resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("FULL104 manifest path escapes Level-4 root") from exc
    return path


def _load_observation_matrix(path: Path) -> np.ndarray:
    if sha256_file(path) != OBSERVATION_STATE_SHA256:
        raise ValueError("observation-state root mismatch")
    loaded = np.load(path, allow_pickle=False)
    if isinstance(loaded, np.lib.npyio.NpzFile):
        try:
            candidates = []
            for key in loaded.files:
                value = np.asarray(loaded[key])
                if value.shape == (EXPECTED_OPERATORS, EXPECTED_ADDRESSES) and value.dtype == np.uint8:
                    candidates.append(value)
            if len(candidates) != 1:
                raise ValueError(
                    "observation-state NPZ must contain exactly one uint8 "
                    "operator x address matrix at current FULL104 geometry"
                )
            return np.asarray(candidates[0])
        finally:
            loaded.close()
    value = np.asarray(loaded)
    if value.shape != (EXPECTED_OPERATORS, EXPECTED_ADDRESSES) or value.dtype != np.uint8:
        raise ValueError("observation-state matrix geometry/dtype mismatch")
    return value


def _load_registry(path: Path) -> None:
    if sha256_file(path) != CANONICAL_REGISTRY_SHA256:
        raise ValueError("canonical registry root mismatch")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or ())
        if not {"molecular_address_index", "molecular_address_id"}.issubset(fields):
            raise ValueError("canonical registry lacks model-facing fields")
        indices = []
        ids = []
        for row in reader:
            indices.append(int(row["molecular_address_index"]))
            ids.append(str(row["molecular_address_id"]))
    if indices != list(range(EXPECTED_ADDRESSES)):
        raise ValueError("canonical registry ordering/cardinality mismatch")
    if len(set(ids)) != EXPECTED_ADDRESSES or any(not x for x in ids):
        raise ValueError("canonical registry ids must be unique and nonempty")


@dataclass(frozen=True)
class Full104Pass1PhysicalBindingReceiptV1:
    pass1_npz_sha256: str
    full104_block_manifest_sha256: str
    canonical_registry_sha256: str
    observation_state_sha256: str
    strict_core_state_code: int
    block_count: int
    row_count: int
    donor_count: int
    operator_count: int
    address_count: int
    source_names: tuple[str, ...]
    cell_donor_semantic_sha256: str
    cell_nnz_core_semantic_sha256: str
    donor_core_nnz_semantic_sha256: str
    donor_ids_semantic_sha256: str
    donor_source_semantic_sha256: str
    strict_core_cols_semantic_sha256: str
    terminal_masking_outcomes_inspected: bool = False
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        roots = (
            self.pass1_npz_sha256,
            self.full104_block_manifest_sha256,
            self.canonical_registry_sha256,
            self.observation_state_sha256,
            self.cell_donor_semantic_sha256,
            self.cell_nnz_core_semantic_sha256,
            self.donor_core_nnz_semantic_sha256,
            self.donor_ids_semantic_sha256,
            self.donor_source_semantic_sha256,
            self.strict_core_cols_semantic_sha256,
        )
        for root in roots:
            if not isinstance(root, str) or len(root) != 64 or root != root.lower():
                raise ValueError("physical binding roots must be lowercase SHA-256")
            try:
                int(root, 16)
            except ValueError as exc:
                raise ValueError("physical binding roots must be lowercase SHA-256") from exc
        if self.full104_block_manifest_sha256 != FULL104_BLOCK_MANIFEST_SHA256:
            raise ValueError("pass1 binding uses a different FULL104 manifest")
        if self.canonical_registry_sha256 != CANONICAL_REGISTRY_SHA256:
            raise ValueError("pass1 binding uses a different canonical registry")
        if self.observation_state_sha256 != OBSERVATION_STATE_SHA256:
            raise ValueError("pass1 binding uses a different observation state")
        if (
            self.block_count,
            self.row_count,
            self.donor_count,
            self.operator_count,
            self.address_count,
        ) != (
            EXPECTED_BLOCKS,
            EXPECTED_ROWS,
            EXPECTED_DONORS,
            EXPECTED_OPERATORS,
            EXPECTED_ADDRESSES,
        ):
            raise ValueError("pass1 physical geometry does not equal current FULL104")
        if tuple(self.source_names) != SOURCE_NAMES:
            raise ValueError("pass1 physical source identities mismatch")
        if isinstance(self.strict_core_state_code, bool) or not isinstance(
            self.strict_core_state_code, int
        ) or self.strict_core_state_code <= 0:
            raise ValueError("strict_core_state_code must be a positive integer")
        for name in (
            "terminal_masking_outcomes_inspected",
            "protected_outcomes_authorized",
            "training_authorized",
        ):
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain False")

    def canonical_digest(self) -> str:
        self.validate()
        payload = asdict(self)
        payload["source_names"] = list(self.source_names)
        return _canonical_sha({"schema": SCHEMA_ID, **payload})


def verify_pass1_against_physical_full104(
    *,
    pass1_path: Path,
    level4_root: Path,
    registry_path: Path,
    observation_state_path: Path,
) -> Full104Pass1PhysicalBindingReceiptV1:
    pass1_path = Path(pass1_path)
    level4_root = Path(level4_root)
    registry_path = Path(registry_path)
    observation_state_path = Path(observation_state_path)

    pass1_sha = sha256_file(pass1_path)
    _load_registry(registry_path)
    observation = _load_observation_matrix(observation_state_path)
    state_code, physical_core = infer_strict_measured_scalar_common_core(
        observation,
        expected_size=EXPECTED_CORE,
    )

    with np.load(pass1_path, allow_pickle=False) as data:
        required = {
            "cell_donor",
            "cell_nnz_core",
            "donor_addr_nnz",
            "donor_src",
            "duniq",
            "core",
        }
        missing = required - set(data.files)
        if missing:
            raise ValueError(f"pass1 is missing required arrays: {sorted(missing)}")
        cell_donor = np.asarray(data["cell_donor"], dtype=np.int64)
        cell_nnz_core = np.asarray(data["cell_nnz_core"], dtype=np.int64)
        donor_addr_nnz = np.asarray(data["donor_addr_nnz"], dtype=np.int64)
        donor_src = np.asarray(data["donor_src"], dtype=np.int64)
        donor_ids = np.asarray(data["duniq"]).astype(str)
        pass1_core = np.asarray(data["core"], dtype=np.int64)

    if cell_donor.shape != (EXPECTED_ROWS,) or cell_nnz_core.shape != (EXPECTED_ROWS,):
        raise ValueError("pass1 cell vectors do not equal current FULL104 row count")
    if donor_addr_nnz.shape != (EXPECTED_DONORS, EXPECTED_ADDRESSES):
        raise ValueError("pass1 donor/address support matrix geometry mismatch")
    if donor_src.shape != (EXPECTED_DONORS,) or donor_ids.shape != (EXPECTED_DONORS,):
        raise ValueError("pass1 donor registry geometry mismatch")
    if pass1_core.shape != (EXPECTED_CORE,) or not np.array_equal(pass1_core, physical_core):
        raise ValueError("pass1 strict core does not rederive from current observation state")
    if len(set(map(str, donor_ids))) != EXPECTED_DONORS or any(not x for x in donor_ids):
        raise ValueError("pass1 donor ids must be unique and nonempty")
    if np.any(cell_donor < 0) or np.any(cell_donor >= EXPECTED_DONORS):
        raise ValueError("pass1 cell_donor contains out-of-range donor codes")
    if np.any(donor_src < 0) or np.any(donor_src >= len(SOURCE_NAMES)):
        raise ValueError("pass1 donor_src contains out-of-range source codes")
    if np.any(cell_nnz_core < 0) or np.any(donor_addr_nnz < 0):
        raise ValueError("pass1 support counts must be nonnegative")

    manifest_path = level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if sha256_file(manifest_path) != FULL104_BLOCK_MANIFEST_SHA256:
        raise ValueError("FULL104 block manifest root mismatch")
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != MANIFEST_COLUMNS:
            raise ValueError("FULL104 block manifest schema mismatch")
        manifest = [dict(row) for row in reader]
    if len(manifest) != EXPECTED_BLOCKS:
        raise ValueError("FULL104 block manifest block count mismatch")
    if len({row["block_key"] for row in manifest}) != EXPECTED_BLOCKS:
        raise ValueError("FULL104 block manifest contains duplicate block keys")
    if len({int(row["operator_index"]) for row in manifest}) != EXPECTED_OPERATORS:
        raise ValueError("FULL104 operator count mismatch")
    if tuple(sorted({str(row["source"]) for row in manifest})) != tuple(sorted(SOURCE_NAMES)):
        raise ValueError("FULL104 source identities mismatch")

    donor_to_code = {str(donor): i for i, donor in enumerate(donor_ids)}
    source_to_code = {name: i for i, name in enumerate(SOURCE_NAMES)}
    seen_selection = np.zeros(EXPECTED_ROWS, dtype=np.bool_)
    physical_donor_core_nnz = np.zeros((EXPECTED_DONORS, EXPECTED_CORE), dtype=np.int64)
    core_mask = np.zeros(EXPECTED_ADDRESSES, dtype=np.bool_)
    core_mask[physical_core] = True
    total_rows = 0

    for row in manifest:
        counts_path = _resolve_under(level4_root, row["counts_path"])
        meta_path = _resolve_under(level4_root, row["meta_path"])
        if sha256_file(counts_path) != row["counts_sha256"]:
            raise ValueError(f"FULL104 counts hash mismatch: {row['block_key']}")
        if sha256_file(meta_path) != row["meta_sha256"]:
            raise ValueError(f"FULL104 metadata hash mismatch: {row['block_key']}")

        matrix = sp.load_npz(counts_path).tocsr()
        expected_rows = int(row["rows"])
        if matrix.shape != (expected_rows, EXPECTED_ADDRESSES):
            raise ValueError(f"FULL104 counts geometry mismatch: {row['block_key']}")
        if matrix.nnz != int(row["nnz"]):
            raise ValueError(f"FULL104 counts nnz mismatch: {row['block_key']}")

        with meta_path.open(newline="", encoding="utf-8") as handle:
            meta_reader = csv.DictReader(handle)
            if tuple(meta_reader.fieldnames or ()) != META_COLUMNS:
                raise ValueError(f"FULL104 metadata schema mismatch: {row['block_key']}")
            selection = []
            block_donor_codes = []
            block_libraries = []
            source = str(row["source"])
            expected_source_code = source_to_code[source]
            for meta in meta_reader:
                selection_row = int(meta["selection_row"])
                donor_id = str(meta["donor_id"])
                if donor_id not in donor_to_code:
                    raise ValueError("physical metadata contains donor absent from pass1 donor registry")
                donor_code = donor_to_code[donor_id]
                if int(donor_src[donor_code]) != expected_source_code:
                    raise ValueError("pass1 donor/source identity disagrees with physical metadata")
                library = _parse_source_library(meta["source_library"], row["block_key"])
                if library <= 0:
                    raise ValueError("physical metadata contains invalid source_library")
                selection.append(selection_row)
                block_donor_codes.append(donor_code)
                block_libraries.append(library)

        selection_arr = np.asarray(selection, dtype=np.int64)
        donor_codes = np.asarray(block_donor_codes, dtype=np.int64)
        libraries = np.asarray(block_libraries, dtype=np.int64)
        if (
            selection_arr.shape != (expected_rows,)
            or donor_codes.shape != (expected_rows,)
            or libraries.shape != (expected_rows,)
        ):
            raise ValueError(f"FULL104 metadata row count mismatch: {row['block_key']}")
        if np.any(selection_arr < 0) or np.any(selection_arr >= EXPECTED_ROWS):
            raise ValueError("physical selection_row is out of range")
        if np.unique(selection_arr).size != selection_arr.size or np.any(seen_selection[selection_arr]):
            raise ValueError("duplicate physical selection_row across FULL104 blocks")
        seen_selection[selection_arr] = True
        if not np.array_equal(cell_donor[selection_arr], donor_codes):
            raise ValueError("pass1 cell_donor does not rederive from physical metadata")

        mapped_row_sums = np.asarray(matrix.sum(axis=1), dtype=np.int64).reshape(-1)
        if (
            mapped_row_sums.shape != libraries.shape
            or np.any(mapped_row_sums > libraries)
        ):
            raise ValueError(
                f"source_library row-alignment invariant failed: {row['block_key']}"
            )

        # Slice the physical strict core once per block, then reuse it for
        # both per-cell and donor/address support checks.  This avoids repeating
        # a 41,238 -> 17,186 column projection for every donor in the block.
        core_block = matrix[:, physical_core].tocsr()
        physical_row_core_nnz = np.diff(core_block.indptr).astype(
            np.int64, copy=False
        )
        if not np.array_equal(cell_nnz_core[selection_arr], physical_row_core_nnz):
            raise ValueError("pass1 cell_nnz_core does not rederive from physical count blocks")

        for donor_code in np.unique(donor_codes):
            local_rows = np.flatnonzero(donor_codes == int(donor_code))
            physical_donor_core_nnz[int(donor_code)] += np.asarray(
                core_block[local_rows].getnnz(axis=0), dtype=np.int64
            ).reshape(-1)

        total_rows += expected_rows

    if total_rows != EXPECTED_ROWS or not np.all(seen_selection):
        raise ValueError("physical pass1 verification did not close over all FULL104 rows")
    if not np.array_equal(donor_addr_nnz[:, physical_core], physical_donor_core_nnz):
        raise ValueError("pass1 donor/core support does not rederive from physical count blocks")

    receipt = Full104Pass1PhysicalBindingReceiptV1(
        pass1_npz_sha256=pass1_sha,
        full104_block_manifest_sha256=FULL104_BLOCK_MANIFEST_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        observation_state_sha256=OBSERVATION_STATE_SHA256,
        strict_core_state_code=int(state_code),
        block_count=len(manifest),
        row_count=total_rows,
        donor_count=len(donor_ids),
        operator_count=EXPECTED_OPERATORS,
        address_count=EXPECTED_ADDRESSES,
        source_names=SOURCE_NAMES,
        cell_donor_semantic_sha256=_array_digest(cell_donor),
        cell_nnz_core_semantic_sha256=_array_digest(cell_nnz_core),
        donor_core_nnz_semantic_sha256=_array_digest(physical_donor_core_nnz),
        donor_ids_semantic_sha256=_string_vector_digest(donor_ids),
        donor_source_semantic_sha256=_array_digest(donor_src),
        strict_core_cols_semantic_sha256=_array_digest(physical_core),
    )
    receipt.validate()
    return receipt
