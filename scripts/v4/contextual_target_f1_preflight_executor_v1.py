"""Prospective pre-result F1 executor mechanics."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np


def power_ladder(capacity: int) -> list[int]:
    if capacity < 1:
        raise ValueError("capacity")
    values = []
    value = 1
    while value <= capacity:
        values.append(value)
        value *= 2
    return values


def select_smallest_near_best(rows: list[dict[str, Any]]) -> dict[str, Any]:
    safe = [row for row in rows if bool(row["safe"])]
    if not safe:
        raise RuntimeError("STOP_F1_PREFLIGHT_RESOURCE_SELECTION_UNRESOLVED")
    best = max(float(row["median_throughput"]) for row in safe)
    eligible = [row for row in safe if float(row["median_throughput"]) >= 0.95 * best]
    return min(eligible, key=lambda row: int(row["configuration"]))


def build_effect_row(*, teacher: float, correct: float, null: float, direct: float) -> dict[str, float]:
    contextual_advantage = float(teacher) - float(correct)
    null_advantage = float(teacher) - float(null)
    return {
        "teacher": float(teacher),
        "correct": float(correct),
        "null": float(null),
        "direct": float(direct),
        "contextual_advantage": contextual_advantage,
        "null_advantage": null_advantage,
        "qid_margin": null_advantage - contextual_advantage,
    }


def full_geometry() -> dict[str, int]:
    geometry = {
        "recipient_cells": 2781,
        "statistical_assignments": 44496,
        "unique_cell_q": 43108,
        "compute_only_dedups": 1388,
        "teacher_forwards": 43108,
        "correct_forwards": 215540,
        "null_forwards": 215540,
        "total_expensive_forwards": 474188,
        "assignment_evidence_effect_rows": 222480,
        "logical_donor_operator_shards": 1400,
    }
    if geometry["statistical_assignments"] - geometry["unique_cell_q"] != geometry["compute_only_dedups"]:
        raise AssertionError("dedup reconciliation")
    if geometry["teacher_forwards"] + geometry["correct_forwards"] + geometry["null_forwards"] != geometry["total_expensive_forwards"]:
        raise AssertionError("forward reconciliation")
    return geometry


def _payload_sha(ids: list[str], values: np.ndarray) -> str:
    array = np.asarray(values)
    h = hashlib.sha256()
    h.update(json.dumps(ids, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    h.update(str(array.dtype).encode("ascii"))
    h.update(np.asarray(array.shape, dtype=np.int64).tobytes())
    h.update(array.tobytes(order="C"))
    return h.hexdigest()


class AtomicShardStore:
    def __init__(self, root: Path, membership_root: str, forward_root: str, dtype: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.membership_root = str(membership_root)
        self.forward_root = str(forward_root)
        self.dtype = str(dtype)

    def _identity(self, shard_id: str, ordered_ids: list[str]) -> dict[str, object]:
        return {
            "shard_id": str(shard_id),
            "ordered_ids": list(ordered_ids),
            "membership_root": self.membership_root,
            "forward_root": self.forward_root,
            "dtype": self.dtype,
        }

    def commit(self, shard_id: str, ordered_ids: list[str], values: np.ndarray) -> Path:
        path = self.root / f"{shard_id}.npz"
        if path.exists():
            raise RuntimeError("duplicate shard write")
        array = np.asarray(values)
        identity = self._identity(shard_id, ordered_ids)
        staging = self.root / f"{shard_id}.staging.npz"
        with staging.open("wb") as handle:
            np.savez(
                handle,
                values=array,
                identity_json=np.asarray(json.dumps(identity, sort_keys=True, separators=(",", ":"))),
                payload_semantic_sha256=np.asarray(_payload_sha(ordered_ids, array)),
            )
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staging, path)
        return path

    def load(self, shard_id: str, ordered_ids: list[str]) -> np.ndarray:
        path = self.root / f"{shard_id}.npz"
        with np.load(path, allow_pickle=False) as packed:
            values = packed["values"].copy()
            identity_json = str(packed["identity_json"])
            stored_sha = str(packed["payload_semantic_sha256"])
        expected_identity = json.dumps(self._identity(shard_id, ordered_ids), sort_keys=True, separators=(",", ":"))
        if identity_json != expected_identity:
            raise RuntimeError("shard identity mismatch")
        if stored_sha != _payload_sha(ordered_ids, values):
            raise RuntimeError("shard scientific payload mismatch")
        return values
