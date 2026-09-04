"""Prospective pre-result F1 executor mechanics."""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    if a.shape != b.shape or a.ndim != 1 or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("cosine input")
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denominator == 0.0:
        raise ValueError("zero-norm cosine")
    return float(np.dot(a, b) / denominator)


def qid_v2(own_similarity: float, paired_wrong_similarity: float) -> dict[str, float]:
    own = float(own_similarity); wrong = float(paired_wrong_similarity)
    if not np.isfinite([own, wrong]).all():
        raise ValueError("nonfinite QID")
    margin = own - wrong
    return {"qid_margin": margin, "qid_win": 1.0 if margin > 0 else 0.0 if margin < 0 else 0.5}


def _identity_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def teacher_compute_identity(authority: dict[str, Any], record: dict[str, Any]) -> str:
    body = {"authority": authority, "role": "teacher", "recipient": record["canonical_cell_id"], "q": int(record["q"])}
    return _identity_sha(body)


def student_forward_identity(authority: dict[str, Any], record: dict[str, Any], role: str) -> str:
    if role not in {"correct_student", "matched_null_student"}:
        raise ValueError("student role")
    body = {"authority": authority, "role": role, "recipient": record["canonical_cell_id"], "q": int(record["q"]), "evidence_level": int(record["evidence_level"])}
    if role == "matched_null_student":
        body["null_source"] = record.get("null_source_cell", authority.get("null_source"))
    return _identity_sha(body)


def vmstat_swap(path: Path = Path("/proc/vmstat")) -> dict[str, int]:
    values = {}
    for line in path.read_text(encoding="ascii").splitlines():
        fields = line.split()
        if fields and fields[0] in {"pswpin", "pswpout"}:
            values[fields[0]] = int(fields[1])
    if set(values) != {"pswpin", "pswpout"}:
        raise RuntimeError("swap counters unavailable")
    return values


def no_swap_activity(before: dict[str, int], after: dict[str, int]) -> bool:
    return after["pswpin"] == before["pswpin"] and after["pswpout"] == before["pswpout"]


def evaluate_until_unsafe(candidates: list[int], evaluate: Callable[[int], dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for candidate in candidates:
        row = evaluate(candidate); rows.append(row)
        if row.get("safe") is not True:
            break
    return rows


def nonoverlapping_runtime(*, physical_reader: float, forward_pipeline: float, shard_commit: float, finalization: float) -> dict[str, Any]:
    components = {"physical_reader": float(physical_reader), "forward_pipeline": float(forward_pipeline), "shard_commit": float(shard_commit), "finalization": float(finalization)}
    if any(not np.isfinite(value) or value < 0 for value in components.values()):
        raise ValueError("runtime component")
    return {"components": components, "component_count": len(components), "total": sum(components.values())}


def benchmark_repetitions(operation: Callable[[], Any], units: int) -> dict[str, Any]:
    """Run the frozen one-warmup/three-timed-candidate protocol."""
    if units < 1:
        raise ValueError("units")
    operation()
    repetitions = []
    for _ in range(3):
        started = time.perf_counter()
        operation()
        elapsed = time.perf_counter() - started
        repetitions.append({
            "elapsed_seconds": elapsed,
            "throughput": units / elapsed,
        })
    return {
        "warmups": 1,
        "timed_repetitions": 3,
        "repetitions": repetitions,
        "median_throughput": statistics.median(row["throughput"] for row in repetitions),
    }


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


def build_effect_row(*, s_correct_contextual: np.ndarray, t_true_contextual: np.ndarray,
                     s_null_contextual: np.ndarray, s_correct_direct: np.ndarray,
                     t_true_direct: np.ndarray, s_null_direct: np.ndarray,
                     own_similarity: float, paired_wrong_similarity: float) -> dict[str, float]:
    contextual = cosine(s_correct_contextual, t_true_contextual) - cosine(s_null_contextual, t_true_contextual)
    direct = cosine(s_correct_direct, t_true_direct) - cosine(s_null_direct, t_true_direct)
    return {"A": contextual, "direct_delta": contextual - direct, **qid_v2(own_similarity, paired_wrong_similarity)}


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
        if array.dtype != np.dtype(self.dtype):
            raise TypeError("shard dtype does not match declared dtype")
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
        if values.dtype != np.dtype(self.dtype):
            raise RuntimeError("persisted shard dtype mismatch")
        if identity_json != expected_identity:
            raise RuntimeError("shard identity mismatch")
        if stored_sha != _payload_sha(ordered_ids, values):
            raise RuntimeError("shard scientific payload mismatch")
        return values
