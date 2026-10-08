#!/usr/bin/env python3
"""Portable, hash-bound sparse expression reader for D1 V2.

The historical production loader froze the correct science but also froze local
Windows paths. This module separates those concerns:

- semantic authority remains the frozen loader manifest and observation-state
  authority;
- physical shard locations are supplied by a separate execution-binding
  manifest whose bytes/hashes must exactly match the frozen manifest;
- lawful cell locators come independently from the reader_fit SQLite authority;
- source_library is recovered from the exact meta shard and cross-checked
  against donor/cell identity before any expression row is used;
- expression stays sparse while preserving the historical
  log1p(raw_count * 10000 / max(source_library, 1)) transform exactly once.

No protected partition is ever queried and no missing/mismatched row is filtered
away.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import scipy.sparse as sp

from d1_real_data_derivation_core_v1 import (
    MEASURED_SCALAR,
    STRUCTURALLY_UNMEASURED,
    COLLISION_UNRESOLVED,
)

FROZEN_LOADER_MANIFEST_SHA256 = "2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328"
FROZEN_OBSERVATION_STATE_SHA256 = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
FROZEN_CELL_METADATA_SHA256 = "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"
ADDRESS_COUNT = 41_238
LAWFUL_PARTITION = "reader_fit"
LOCATION_SCHEMA = "D1_EXPRESSION_SHARD_LOCATION_MANIFEST_V2"
STOP_LOCATION_INVALID = "STOP_D1_V2_EXPRESSION_LOCATION_MANIFEST_INVALID"
STOP_SHARD_DRIFT = "STOP_D1_V2_EXPRESSION_SHARD_DRIFT"
STOP_ROW_ALIGNMENT = "STOP_D1_V2_EXPRESSION_ROW_ALIGNMENT_MISMATCH"
STOP_PROTECTED_QUERY = "STOP_D1_V2_PROTECTED_EXPRESSION_QUERY"
STOP_EXPRESSION_INVALID = "STOP_D1_V2_EXPRESSION_INVALID"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_sha256(text: Any) -> bool:
    value = str(text or "")
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{STOP_LOCATION_INVALID}: JSON root is not an object")
    return payload


def load_frozen_loader_manifest(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    actual = sha256_file(path)
    if actual != FROZEN_LOADER_MANIFEST_SHA256:
        raise ValueError(
            f"{STOP_SHARD_DRIFT}: loader manifest is {actual}, expected "
            f"{FROZEN_LOADER_MANIFEST_SHA256}")
    payload = _load_json(path)
    if payload.get("schema") != "foundation-train-loader-v1":
        raise ValueError(f"{STOP_LOCATION_INVALID}: loader manifest schema")
    shards = payload.get("shards")
    if not isinstance(shards, list) or len(shards) != 42:
        raise ValueError(f"{STOP_LOCATION_INVALID}: loader manifest must name 42 shards")
    return payload


def load_observation_state_authority(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    actual = sha256_file(path)
    if actual != FROZEN_OBSERVATION_STATE_SHA256:
        raise ValueError(
            f"{STOP_SHARD_DRIFT}: observation-state authority is {actual}, expected "
            f"{FROZEN_OBSERVATION_STATE_SHA256}")
    data = np.load(path, allow_pickle=False)
    required = {"states", "matrix_id", "operator_index", "molecular_address_index", "state_names"}
    if set(data.files) != required:
        raise ValueError(f"{STOP_EXPRESSION_INVALID}: observation-state surface")
    states = np.asarray(data["states"], dtype=np.uint8)
    matrix_id = [str(x) for x in data["matrix_id"]]
    operator_index = np.asarray(data["operator_index"], dtype=np.int64)
    address_index = np.asarray(data["molecular_address_index"], dtype=np.int64)
    state_names = tuple(str(x) for x in data["state_names"])
    if states.shape != (42, ADDRESS_COUNT):
        raise ValueError(f"{STOP_EXPRESSION_INVALID}: observation-state shape")
    if not np.array_equal(operator_index, np.arange(42)):
        raise ValueError(f"{STOP_EXPRESSION_INVALID}: operator index order")
    if not np.array_equal(address_index, np.arange(ADDRESS_COUNT)):
        raise ValueError(f"{STOP_EXPRESSION_INVALID}: address order")
    if state_names != (
        "STRUCTURALLY_UNMEASURED",
        "MEASURED_SCALAR",
        "MEASURED_COLLISION_UNRESOLVED",
    ):
        raise ValueError(f"{STOP_EXPRESSION_INVALID}: state names")
    if not set(np.unique(states)).issubset(
        {STRUCTURALLY_UNMEASURED, MEASURED_SCALAR, COLLISION_UNRESOLVED}
    ):
        raise ValueError(f"{STOP_EXPRESSION_INVALID}: state codes")
    return {
        "states": states,
        "matrix_id": matrix_id,
        "operator_index": operator_index,
        "state_names": state_names,
        "sha256": actual,
    }


@dataclass(frozen=True)
class ShardBinding:
    operator_index: int
    matrix_id: str
    counts_path: Path
    counts_sha256: str
    meta_path: Path
    meta_sha256: str
    source: str | None = None


def validate_location_manifest(
    location_path: Path | str,
    *,
    loader_manifest_path: Path | str,
    observation_state_path: Path | str,
    verify_bytes: bool = True,
) -> dict[str, Any]:
    """Bind physical files to the exact frozen 42-shard semantic inventory."""
    location_path = Path(location_path)
    location = _load_json(location_path)
    if location.get("schema") != LOCATION_SCHEMA:
        raise ValueError(f"{STOP_LOCATION_INVALID}: schema")
    if not str(location.get("status") or "").startswith("FROZEN_"):
        raise ValueError(f"{STOP_LOCATION_INVALID}: status")
    if str(location.get("production_loader_manifest_sha256") or "") != (
        FROZEN_LOADER_MANIFEST_SHA256
    ):
        raise ValueError(f"{STOP_LOCATION_INVALID}: loader-manifest binding")
    if str(location.get("observation_state_sha256") or "") != (
        FROZEN_OBSERVATION_STATE_SHA256
    ):
        raise ValueError(f"{STOP_LOCATION_INVALID}: observation-state binding")

    frozen = load_frozen_loader_manifest(loader_manifest_path)
    obs = load_observation_state_authority(observation_state_path)
    entries = location.get("shards")
    if not isinstance(entries, list) or len(entries) != 42:
        raise ValueError(f"{STOP_LOCATION_INVALID}: exactly 42 location entries required")

    bindings: list[ShardBinding] = []
    seen_matrix: set[str] = set()
    seen_operator: set[int] = set()
    for operator, (expected, entry) in enumerate(zip(frozen["shards"], entries)):
        if not isinstance(entry, Mapping):
            raise ValueError(f"{STOP_LOCATION_INVALID}: entry {operator}")
        op = int(entry.get("operator_index", -1))
        matrix = str(entry.get("matrix_id") or "")
        if op != operator:
            raise ValueError(f"{STOP_LOCATION_INVALID}: operator order at {operator}")
        if matrix != str(expected["matrix_id"]):
            raise ValueError(f"{STOP_LOCATION_INVALID}: matrix id at operator {operator}")
        if matrix != str(obs["matrix_id"][operator]):
            raise ValueError(
                f"{STOP_LOCATION_INVALID}: observation-state matrix mismatch at {operator}")
        expected_counts = str(expected["counts_sha256"])
        expected_meta = str(expected["meta_sha256"])
        if str(entry.get("counts_sha256") or "") != expected_counts:
            raise ValueError(f"{STOP_LOCATION_INVALID}: counts hash declaration {operator}")
        if str(entry.get("meta_sha256") or "") != expected_meta:
            raise ValueError(f"{STOP_LOCATION_INVALID}: meta hash declaration {operator}")
        counts_path = Path(str(entry.get("counts_path") or ""))
        meta_path = Path(str(entry.get("meta_path") or ""))
        if not counts_path.is_file() or not meta_path.is_file():
            raise FileNotFoundError(
                f"{STOP_SHARD_DRIFT}: missing physical shard for operator {operator}")
        if verify_bytes:
            actual_counts = sha256_file(counts_path)
            actual_meta = sha256_file(meta_path)
            if actual_counts != expected_counts:
                raise ValueError(
                    f"{STOP_SHARD_DRIFT}: counts operator {operator} is {actual_counts}, "
                    f"expected {expected_counts}")
            if actual_meta != expected_meta:
                raise ValueError(
                    f"{STOP_SHARD_DRIFT}: meta operator {operator} is {actual_meta}, "
                    f"expected {expected_meta}")
        if matrix in seen_matrix or op in seen_operator:
            raise ValueError(f"{STOP_LOCATION_INVALID}: duplicate matrix/operator")
        seen_matrix.add(matrix)
        seen_operator.add(op)
        bindings.append(ShardBinding(
            operator_index=op,
            matrix_id=matrix,
            counts_path=counts_path,
            counts_sha256=expected_counts,
            meta_path=meta_path,
            meta_sha256=expected_meta,
            source=str(entry.get("source")) if entry.get("source") is not None else None,
        ))
    return {
        "terminal": "PASS_D1_V2_EXPRESSION_LOCATION_BINDING",
        "location_manifest_sha256": sha256_file(location_path),
        "bindings": bindings,
        "loader_manifest_sha256": FROZEN_LOADER_MANIFEST_SHA256,
        "observation_state_sha256": FROZEN_OBSERVATION_STATE_SHA256,
    }


def open_cell_metadata(path: Path | str, *, verify_hash: bool = True) -> sqlite3.Connection:
    path = Path(path)
    if verify_hash:
        actual = sha256_file(path)
        if actual != FROZEN_CELL_METADATA_SHA256:
            raise ValueError(
                f"{STOP_SHARD_DRIFT}: cell metadata is {actual}, expected "
                f"{FROZEN_CELL_METADATA_SHA256}")
    connection = sqlite3.connect(
        f"file:{path}?mode=ro&immutable=1", uri=True)
    connection.execute("PRAGMA query_only=ON")
    connection.execute("PRAGMA temp_store=MEMORY")
    return connection


def lawful_stratum_locators(
    connection: sqlite3.Connection, *, donor_id: str, operator_index: int
) -> list[dict[str, Any]]:
    """Read only reader_fit rows for one donor x operator stratum."""
    rows = connection.execute(
        """
        SELECT source, matrix_id, operator_index, local_row, donor_id,
               partition, cell_id
        FROM cells
        WHERE partition=? AND donor_id=? AND operator_index=?
        ORDER BY local_row
        """,
        (LAWFUL_PARTITION, str(donor_id), int(operator_index)),
    ).fetchall()
    out = []
    seen_ids: set[str] = set()
    seen_local: set[int] = set()
    for source, matrix, operator, local_row, donor, partition, cell_id in rows:
        if str(partition) != LAWFUL_PARTITION:
            raise PermissionError(f"{STOP_PROTECTED_QUERY}: non-fit row delivered")
        if str(donor) != str(donor_id) or int(operator) != int(operator_index):
            raise ValueError(f"{STOP_ROW_ALIGNMENT}: stratum drift")
        cid = str(cell_id)
        lr = int(local_row)
        if cid in seen_ids or lr in seen_local:
            raise ValueError(f"{STOP_ROW_ALIGNMENT}: duplicate identity/local row")
        seen_ids.add(cid)
        seen_local.add(lr)
        out.append({
            "source": str(source),
            "matrix_id": str(matrix),
            "operator_index": int(operator),
            "local_row": lr,
            "donor_id": str(donor),
            "partition": LAWFUL_PARTITION,
            "canonical_cell_id": cid,
        })
    return out


def expected_cell_ids_from_metadata(
    connection: sqlite3.Connection,
    strata: Iterable[tuple[str, int]],
) -> dict[tuple[str, int], list[str]]:
    """Independent expected identity map for teacher-state materialization."""
    result = {}
    for donor, operator in strata:
        key = (str(donor), int(operator))
        rows = lawful_stratum_locators(
            connection, donor_id=key[0], operator_index=key[1])
        result[key] = [row["canonical_cell_id"] for row in rows]
    return result


class PortableExpressionReader:
    """Sparse, exact-semantics reader over the frozen physical shards."""

    def __init__(
        self,
        *,
        bindings: Sequence[ShardBinding],
        observation_state_path: Path | str,
        cell_metadata_connection: sqlite3.Connection,
    ) -> None:
        self.bindings = {int(b.operator_index): b for b in bindings}
        if set(self.bindings) != set(range(42)):
            raise ValueError(f"{STOP_LOCATION_INVALID}: operator closure")
        self.observation = load_observation_state_authority(observation_state_path)
        self.connection = cell_metadata_connection
        self._counts_cache: dict[int, sp.csr_matrix] = {}
        self._meta_cache: dict[int, dict[str, np.ndarray]] = {}
        self._operator_validated: set[int] = set()

    def _load_operator(self, operator: int) -> tuple[sp.csr_matrix, dict[str, np.ndarray]]:
        operator = int(operator)
        if operator in self._counts_cache:
            return self._counts_cache[operator], self._meta_cache[operator]
        binding = self.bindings[operator]
        counts = sp.load_npz(binding.counts_path).tocsr()
        meta_file = np.load(binding.meta_path, allow_pickle=False)
        if set(meta_file.files) != {
            "donor_id", "cell_id", "broad_cell_class", "source_library"
        }:
            raise ValueError(f"{STOP_EXPRESSION_INVALID}: meta surface operator {operator}")
        meta = {name: np.asarray(meta_file[name]) for name in meta_file.files}
        n = len(meta["cell_id"])
        if counts.shape != (n, ADDRESS_COUNT):
            raise ValueError(
                f"{STOP_EXPRESSION_INVALID}: counts/meta shape operator {operator}: "
                f"{counts.shape} vs {n}")
        state = self.observation["states"][operator]
        measured = state == MEASURED_SCALAR
        if counts[:, ~measured].nnz:
            raise ValueError(
                f"{STOP_EXPRESSION_INVALID}: numeric value outside MEASURED_SCALAR "
                f"operator {operator}")
        self._counts_cache[operator] = counts
        self._meta_cache[operator] = meta
        self._operator_validated.add(operator)
        return counts, meta

    def release_operator(self, operator: int) -> None:
        self._counts_cache.pop(int(operator), None)
        self._meta_cache.pop(int(operator), None)

    def aligned_locators(
        self, *, donor_id: str, operator_index: int,
        expected_cell_ids: Sequence[str] | None = None,
    ) -> list[dict[str, Any]]:
        operator = int(operator_index)
        binding = self.bindings[operator]
        rows = lawful_stratum_locators(
            self.connection, donor_id=str(donor_id), operator_index=operator)
        if not rows:
            raise ValueError(
                f"{STOP_ROW_ALIGNMENT}: empty lawful stratum {(donor_id, operator)}")
        matrices = {row["matrix_id"] for row in rows}
        sources = {row["source"] for row in rows}
        if matrices != {binding.matrix_id}:
            raise ValueError(
                f"{STOP_ROW_ALIGNMENT}: SQLite matrix {matrices} != {binding.matrix_id}")
        if binding.source is not None and sources != {binding.source}:
            raise ValueError(
                f"{STOP_ROW_ALIGNMENT}: source {sources} != {binding.source}")
        if expected_cell_ids is not None:
            observed = [row["canonical_cell_id"] for row in rows]
            expected = [str(x) for x in expected_cell_ids]
            if observed != expected:
                raise ValueError(
                    f"{STOP_ROW_ALIGNMENT}: teacher archive cell IDs/order disagree")
        counts, meta = self._load_operator(operator)
        for row in rows:
            local = int(row["local_row"])
            if local < 0 or local >= counts.shape[0]:
                raise ValueError(f"{STOP_ROW_ALIGNMENT}: local row out of bounds")
            if str(meta["cell_id"][local]) != row["canonical_cell_id"]:
                raise ValueError(
                    f"{STOP_ROW_ALIGNMENT}: meta cell_id differs at local row {local}")
            if str(meta["donor_id"][local]) != str(donor_id):
                raise ValueError(
                    f"{STOP_ROW_ALIGNMENT}: meta donor differs at local row {local}")
            row["source_library"] = int(meta["source_library"][local])
        return rows

    def load_sparse_stratum(
        self, *, donor_id: str, operator_index: int,
        expected_cell_ids: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Return exact normalized sparse expression and operator observation state."""
        operator = int(operator_index)
        rows = self.aligned_locators(
            donor_id=donor_id, operator_index=operator,
            expected_cell_ids=expected_cell_ids)
        counts, _ = self._load_operator(operator)
        local_rows = np.asarray([row["local_row"] for row in rows], dtype=np.int64)
        library = np.asarray([row["source_library"] for row in rows], dtype=np.float32)
        matrix = counts[local_rows].astype(np.float32)
        normalized = matrix.multiply(
            (10_000.0 / np.maximum(library, 1.0))[:, None]).tocsr()
        normalized.data = np.log1p(normalized.data)
        if not np.all(np.isfinite(normalized.data)):
            raise ValueError(f"{STOP_EXPRESSION_INVALID}: nonfinite normalized value")
        state = self.observation["states"][operator]
        return {
            "donor_id": str(donor_id),
            "operator_index": operator,
            "matrix_id": self.bindings[operator].matrix_id,
            "source": rows[0]["source"],
            "canonical_cell_id": [row["canonical_cell_id"] for row in rows],
            "local_row": local_rows,
            "source_library": library,
            "expression_csr": normalized,
            "observation_state": state,
            "normalization": "log1p(raw_count * 10000 / max(source_library, 1.0))",
        }
