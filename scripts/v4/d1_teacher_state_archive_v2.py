#!/usr/bin/env python3
"""Hash-bound D1 canonical teacher-state archive.

A healthy teacher is expensive to forward over 4.55M cells. D1 resampling must
not call the model again for every null/bootstrap replicate. This module
materializes the exact canonical readout once, binds every stratum and cell
identity, and exposes a read-only mmap source for downstream resampling.

It creates no execution authority. The caller must supply an already-open
D1ExecutionBinding and the exact lawful stratum/cell identities.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from d1_execution_contract_v2 import D1ExecutionBinding, build_state_batch_iterator
from d1_real_data_derivation_core_v1 import (
    PRODUCTION_FULL_FIT,
    assert_donor_primary_masses,
    derive_donor_operator_weights,
)

SCHEMA = "D1_TEACHER_STATE_ARCHIVE_V2"
MANIFEST_NAME = "D1_TEACHER_STATE_ARCHIVE_V2.json"
STOP_ARCHIVE_INVALID = "STOP_D1_V2_TEACHER_STATE_ARCHIVE_INVALID"
STOP_ARCHIVE_DRIFT = "STOP_D1_V2_TEACHER_STATE_ARCHIVE_DRIFT"
STOP_IDENTITY_MISMATCH = "STOP_D1_V2_TEACHER_STATE_IDENTITY_MISMATCH"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def payload_root(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def _slug(donor: str, operator: int) -> str:
    token = hashlib.sha256(f"{donor}|{int(operator)}".encode("utf-8")).hexdigest()[:16]
    return f"stratum_{token}"


def _write_ids(path: Path, ids: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["canonical_cell_id"])
        for value in ids:
            writer.writerow([str(value)])


def _read_ids(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [str(row["canonical_cell_id"]) for row in rows]


def _normalize_expected_ids(provider: Any, donor: str, operator: int) -> list[str]:
    values = provider(donor, operator) if callable(provider) else provider[(donor, operator)]
    out = [str(x) for x in values]
    if len(out) != len(set(out)):
        raise ValueError(f"{STOP_IDENTITY_MISMATCH}: duplicate expected ids in {(donor, operator)}")
    return out


def materialize_teacher_state_archive(
    *,
    binding: D1ExecutionBinding,
    donor_operator_counts: Mapping[tuple[str, int], int],
    expected_cell_ids: Any,
    output_dir: Path | str,
    population_audit_root: str,
    adapter_kwargs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Forward every lawful cell exactly once and freeze one shard per stratum."""
    if not donor_operator_counts:
        raise ValueError(f"{STOP_ARCHIVE_INVALID}: empty stratum map")
    destination = Path(output_dir)
    if destination.exists():
        raise FileExistsError(f"{STOP_ARCHIVE_INVALID}: output already exists: {destination}")
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=destination.name + ".tmp.", dir=parent))
    entries: list[dict[str, Any]] = []
    total_rows = 0
    seen_global: set[str] = set()
    try:
        for donor, operator in sorted((str(d), int(o)) for d, o in donor_operator_counts):
            expected_n = int(donor_operator_counts[(donor, operator)])
            expected_ids = _normalize_expected_ids(expected_cell_ids, donor, operator)
            if len(expected_ids) != expected_n:
                raise ValueError(
                    f"{STOP_IDENTITY_MISMATCH}: {(donor, operator)} expected "
                    f"{expected_n} ids, got {len(expected_ids)}")
            slug = _slug(donor, operator)
            state_path = temporary / f"{slug}.states.npy"
            ids_path = temporary / f"{slug}.cell_ids.csv"

            chunks: list[np.ndarray] = []
            observed_ids: list[str] = []
            kwargs = dict(adapter_kwargs or {})
            kwargs.update({
                "donor_id": donor,
                "operator_index": operator,
                "expected_rows": expected_n,
            })
            for batch in build_state_batch_iterator(binding, **kwargs):
                if not isinstance(batch, Mapping):
                    raise ValueError(f"{STOP_ARCHIVE_INVALID}: adapter batch is not a mapping")
                if set(batch) != {"canonical_cell_id", "states"}:
                    raise ValueError(
                        f"{STOP_ARCHIVE_INVALID}: adapter batch keys are {sorted(batch)}")
                ids = [str(x) for x in batch["canonical_cell_id"]]
                states = np.asarray(batch["states"])
                if states.ndim != 2 or states.shape[1] != binding.output_dimension:
                    raise ValueError(
                        f"{STOP_ARCHIVE_INVALID}: state shape {states.shape}, expected "
                        f"(*,{binding.output_dimension})")
                if states.shape[0] != len(ids):
                    raise ValueError(f"{STOP_ARCHIVE_INVALID}: ids/states length mismatch")
                if not np.all(np.isfinite(states)):
                    raise ValueError(f"{STOP_ARCHIVE_INVALID}: non-finite teacher state")
                chunks.append(states.astype(binding.output_dtype, copy=False))
                observed_ids.extend(ids)

            if observed_ids != expected_ids:
                raise ValueError(
                    f"{STOP_IDENTITY_MISMATCH}: adapter identities/order differ for "
                    f"{(donor, operator)}")
            if len(observed_ids) != expected_n:
                raise ValueError(
                    f"{STOP_IDENTITY_MISMATCH}: row count {len(observed_ids)} != {expected_n}")
            overlap = seen_global.intersection(observed_ids)
            if overlap:
                raise ValueError(
                    f"{STOP_IDENTITY_MISMATCH}: global duplicate cell id {next(iter(overlap))}")
            seen_global.update(observed_ids)

            states_all = (
                np.concatenate(chunks, axis=0)
                if chunks
                else np.empty((0, binding.output_dimension), dtype=binding.output_dtype)
            )
            if states_all.shape != (expected_n, binding.output_dimension):
                raise ValueError(f"{STOP_ARCHIVE_INVALID}: final shard shape {states_all.shape}")
            np.save(state_path, states_all, allow_pickle=False)
            _write_ids(ids_path, observed_ids)
            entry = {
                "donor_id": donor,
                "operator_index": operator,
                "rows": expected_n,
                "state_file": state_path.name,
                "state_sha256": sha256_file(state_path),
                "cell_id_file": ids_path.name,
                "cell_id_sha256": sha256_file(ids_path),
                "shape": [expected_n, binding.output_dimension],
                "dtype": str(states_all.dtype),
            }
            entries.append(entry)
            total_rows += expected_n

        manifest_body = {
            "schema": SCHEMA,
            "status": "FROZEN_DATA_ONLY_ARCHIVE",
            "population_class": PRODUCTION_FULL_FIT,
            "population_audit_root": str(population_audit_root),
            "readout_contract_sha256": binding.readout_contract_sha256,
            "qualification_authority_sha256": binding.qualification_authority_sha256,
            "teacher_checkpoint_sha256": binding.checkpoint_sha256,
            "adapter_sha256": binding.adapter_sha256,
            "teacher_role": binding.teacher_role,
            "output_dimension": binding.output_dimension,
            "output_dtype": binding.output_dtype,
            "strata": len(entries),
            "rows": total_rows,
            "entries": entries,
        }
        manifest_body["archive_root_sha256"] = payload_root(manifest_body)
        (temporary / MANIFEST_NAME).write_text(
            json.dumps(manifest_body, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        os.replace(temporary, destination)
        return manifest_body
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def verify_teacher_state_archive(
    archive_dir: Path | str,
    *,
    expected_binding: D1ExecutionBinding | None = None,
    expected_population_audit_root: str | None = None,
    expected_counts: Mapping[tuple[str, int], int] | None = None,
    expected_cell_ids: Any | None = None,
) -> dict[str, Any]:
    root = Path(archive_dir)
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        raise FileNotFoundError(f"{STOP_ARCHIVE_INVALID}: missing {MANIFEST_NAME}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA:
        raise ValueError(f"{STOP_ARCHIVE_INVALID}: schema")
    claimed_root = str(payload.get("archive_root_sha256") or "")
    body = dict(payload)
    body.pop("archive_root_sha256", None)
    if payload_root(body) != claimed_root:
        raise ValueError(f"{STOP_ARCHIVE_DRIFT}: archive root")
    if expected_binding is not None:
        exact = {
            "readout_contract_sha256": expected_binding.readout_contract_sha256,
            "qualification_authority_sha256": expected_binding.qualification_authority_sha256,
            "teacher_checkpoint_sha256": expected_binding.checkpoint_sha256,
            "adapter_sha256": expected_binding.adapter_sha256,
            "teacher_role": expected_binding.teacher_role,
            "output_dimension": expected_binding.output_dimension,
            "output_dtype": expected_binding.output_dtype,
        }
        for key, value in exact.items():
            if payload.get(key) != value:
                raise ValueError(f"{STOP_ARCHIVE_DRIFT}: {key}")
    if expected_population_audit_root is not None and payload.get(
        "population_audit_root") != expected_population_audit_root:
        raise ValueError(f"{STOP_ARCHIVE_DRIFT}: population_audit_root")

    rows = 0
    seen: set[tuple[str, int]] = set()
    global_ids: set[str] = set()
    for entry in payload.get("entries", []):
        key = (str(entry["donor_id"]), int(entry["operator_index"]))
        if key in seen:
            raise ValueError(f"{STOP_ARCHIVE_INVALID}: duplicate stratum {key}")
        seen.add(key)
        state_path = root / str(entry["state_file"])
        ids_path = root / str(entry["cell_id_file"])
        if sha256_file(state_path) != str(entry["state_sha256"]):
            raise ValueError(f"{STOP_ARCHIVE_DRIFT}: state shard {key}")
        if sha256_file(ids_path) != str(entry["cell_id_sha256"]):
            raise ValueError(f"{STOP_ARCHIVE_DRIFT}: identity shard {key}")
        states = np.load(state_path, mmap_mode="r", allow_pickle=False)
        ids = _read_ids(ids_path)
        expected_shape = tuple(int(x) for x in entry["shape"])
        if states.shape != expected_shape or states.shape[0] != len(ids):
            raise ValueError(f"{STOP_ARCHIVE_INVALID}: shard shape/ids {key}")
        if str(states.dtype) != str(entry["dtype"]):
            raise ValueError(f"{STOP_ARCHIVE_INVALID}: shard dtype {key}")
        if len(ids) != len(set(ids)):
            raise ValueError(f"{STOP_IDENTITY_MISMATCH}: duplicate id in shard {key}")
        overlap = global_ids.intersection(ids)
        if overlap:
            raise ValueError(
                f"{STOP_IDENTITY_MISMATCH}: duplicate id across shards {next(iter(overlap))}")
        global_ids.update(ids)
        if expected_counts is not None and int(expected_counts.get(key, -1)) != len(ids):
            raise ValueError(f"{STOP_IDENTITY_MISMATCH}: expected count {key}")
        if expected_cell_ids is not None:
            if ids != _normalize_expected_ids(expected_cell_ids, *key):
                raise ValueError(f"{STOP_IDENTITY_MISMATCH}: exact ids/order {key}")
        rows += len(ids)

    if int(payload.get("strata", -1)) != len(seen):
        raise ValueError(f"{STOP_ARCHIVE_INVALID}: stratum total")
    if int(payload.get("rows", -1)) != rows:
        raise ValueError(f"{STOP_ARCHIVE_INVALID}: row total")
    if expected_counts is not None:
        expected_keys = {(str(d), int(o)) for d, o in expected_counts}
        if seen != expected_keys:
            raise ValueError(f"{STOP_IDENTITY_MISMATCH}: stratum set")
        if rows != sum(int(v) for v in expected_counts.values()):
            raise ValueError(f"{STOP_IDENTITY_MISMATCH}: total rows")
    return {
        "terminal": "PASS_D1_V2_TEACHER_STATE_ARCHIVE",
        "archive_root_sha256": claimed_root,
        "rows": rows,
        "strata": len(seen),
        "teacher_checkpoint_sha256": payload["teacher_checkpoint_sha256"],
        "readout_contract_sha256": payload["readout_contract_sha256"],
    }


class ArchivedStrataSource:
    """Read-only mmap source for D1 statistics; never performs a model forward."""

    population_class = PRODUCTION_FULL_FIT

    def __init__(self, archive_dir: Path | str) -> None:
        self.root = Path(archive_dir)
        self.manifest = json.loads(
            (self.root / MANIFEST_NAME).read_text(encoding="utf-8"))
        if self.manifest.get("schema") != SCHEMA:
            raise ValueError(f"{STOP_ARCHIVE_INVALID}: schema")
        self.dimension = int(self.manifest["output_dimension"])
        self._entries = {
            (str(e["donor_id"]), int(e["operator_index"])): e
            for e in self.manifest["entries"]
        }
        counts = {key: int(entry["rows"]) for key, entry in self._entries.items()}
        self._weights = derive_donor_operator_weights(counts)
        assert_donor_primary_masses(self._weights)

    def strata(self) -> list[tuple[str, int]]:
        return sorted(self._entries)

    def donors(self) -> list[str]:
        return sorted({d for d, _ in self._entries})

    def total_cells(self) -> int:
        return int(sum(int(e["rows"]) for e in self._entries.values()))

    def load(self, donor: str, operator: int) -> tuple[np.ndarray, np.ndarray]:
        key = (str(donor), int(operator))
        if key not in self._entries:
            raise PermissionError(f"{STOP_ARCHIVE_INVALID}: unlawful stratum {key}")
        entry = self._entries[key]
        states = np.load(
            self.root / str(entry["state_file"]), mmap_mode="r", allow_pickle=False)
        weight = float(self._weights["cell_weight_a_dc"][key])
        return states, np.full(states.shape[0], weight, dtype=np.float64)

    def cell_ids(self, donor: str, operator: int) -> list[str]:
        entry = self._entries[(str(donor), int(operator))]
        return _read_ids(self.root / str(entry["cell_id_file"]))
