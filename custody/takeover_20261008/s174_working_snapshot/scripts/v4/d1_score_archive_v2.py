#!/usr/bin/env python3
"""Hash-bound D1 discovery-object score archive V2.

After D is frozen, project every canonical teacher state onto the prospectively
defined D1 discovery objects exactly once. The resulting score shards are the
single source for cell rankings and molecular association passes.

This archive is D-dependent and therefore binds both the teacher-state archive
root and the exact D-derivation root. It never re-forwards the model and never
recomputes D.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from d1_discovery_atlas_v2 import DiscoveryObject, build_discovery_objects, score_object
from d1_teacher_state_archive_v2 import ArchivedStrataSource

SCHEMA = "D1_DISCOVERY_SCORE_ARCHIVE_V2"
MANIFEST_NAME = "D1_DISCOVERY_SCORE_ARCHIVE_V2.json"
STOP_SCORE_ARCHIVE_INVALID = "STOP_D1_V2_SCORE_ARCHIVE_INVALID"
STOP_SCORE_ARCHIVE_DRIFT = "STOP_D1_V2_SCORE_ARCHIVE_DRIFT"


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


def materialize_score_archive(
    *,
    teacher_archive_dir: Path | str,
    teacher_archive_root_sha256: str,
    derivation: Mapping[str, Any],
    derivation_root_sha256: str,
    output_dir: Path | str,
) -> dict[str, Any]:
    source = ArchivedStrataSource(teacher_archive_dir)
    actual_teacher_root = str(source.manifest.get("archive_root_sha256") or "")
    if actual_teacher_root != str(teacher_archive_root_sha256):
        raise ValueError(
            f"{STOP_SCORE_ARCHIVE_DRIFT}: teacher archive root {actual_teacher_root} "
            f"!= {teacher_archive_root_sha256}")
    if len(str(derivation_root_sha256)) != 64:
        raise ValueError(f"{STOP_SCORE_ARCHIVE_INVALID}: derivation root")
    objects = build_discovery_objects(derivation)
    mean = np.asarray(derivation["mean"], dtype=np.float64)
    if mean.ndim != 1 or mean.size != source.dimension:
        raise ValueError(f"{STOP_SCORE_ARCHIVE_INVALID}: mean/readout dimension")
    destination = Path(output_dir)
    if destination.exists():
        raise FileExistsError(f"{STOP_SCORE_ARCHIVE_INVALID}: output exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(
        prefix=destination.name + ".tmp.", dir=destination.parent))
    entries = []
    total = 0
    try:
        for donor, operator in source.strata():
            states, _ = source.load(donor, operator)
            columns = [
                score_object(states, mean, obj)
                for obj in objects
            ]
            scores = np.stack(columns, axis=1).astype(np.float64, copy=False)
            if scores.shape != (states.shape[0], len(objects)):
                raise ValueError(f"{STOP_SCORE_ARCHIVE_INVALID}: score shape")
            if not np.all(np.isfinite(scores)):
                raise ValueError(f"{STOP_SCORE_ARCHIVE_INVALID}: nonfinite score")
            token = hashlib.sha256(
                f"{donor}|{operator}".encode("utf-8")).hexdigest()[:16]
            score_path = temporary / f"stratum_{token}.scores.npy"
            np.save(score_path, scores, allow_pickle=False)
            entries.append({
                "donor_id": str(donor),
                "operator_index": int(operator),
                "rows": int(scores.shape[0]),
                "score_file": score_path.name,
                "score_sha256": sha256_file(score_path),
                "shape": list(scores.shape),
                "dtype": str(scores.dtype),
            })
            total += int(scores.shape[0])
        manifest = {
            "schema": SCHEMA,
            "status": "FROZEN_DATA_ONLY_ARCHIVE",
            "teacher_archive_root_sha256": str(teacher_archive_root_sha256),
            "derivation_root_sha256": str(derivation_root_sha256),
            "teacher_checkpoint_sha256": source.manifest["teacher_checkpoint_sha256"],
            "readout_contract_sha256": source.manifest["readout_contract_sha256"],
            "program_ids": [obj.program_id for obj in objects],
            "program_objects": [obj.as_dict() for obj in objects],
            "rows": total,
            "strata": len(entries),
            "entries": entries,
        }
        manifest["score_archive_root_sha256"] = payload_root(manifest)
        (temporary / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        os.replace(temporary, destination)
        return manifest
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def verify_score_archive(
    score_archive_dir: Path | str,
    *,
    expected_teacher_archive_root: str | None = None,
    expected_derivation_root: str | None = None,
) -> dict[str, Any]:
    root = Path(score_archive_dir)
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        raise FileNotFoundError(f"{STOP_SCORE_ARCHIVE_INVALID}: missing manifest")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA:
        raise ValueError(f"{STOP_SCORE_ARCHIVE_INVALID}: schema")
    body = dict(payload)
    claimed = str(body.pop("score_archive_root_sha256", ""))
    if payload_root(body) != claimed:
        raise ValueError(f"{STOP_SCORE_ARCHIVE_DRIFT}: root")
    if expected_teacher_archive_root is not None and payload.get(
        "teacher_archive_root_sha256") != expected_teacher_archive_root:
        raise ValueError(f"{STOP_SCORE_ARCHIVE_DRIFT}: teacher archive root")
    if expected_derivation_root is not None and payload.get(
        "derivation_root_sha256") != expected_derivation_root:
        raise ValueError(f"{STOP_SCORE_ARCHIVE_DRIFT}: derivation root")
    seen = set()
    rows = 0
    for entry in payload.get("entries", []):
        key = (str(entry["donor_id"]), int(entry["operator_index"]))
        if key in seen:
            raise ValueError(f"{STOP_SCORE_ARCHIVE_INVALID}: duplicate stratum")
        seen.add(key)
        path = root / str(entry["score_file"])
        if sha256_file(path) != str(entry["score_sha256"]):
            raise ValueError(f"{STOP_SCORE_ARCHIVE_DRIFT}: score shard {key}")
        scores = np.load(path, mmap_mode="r", allow_pickle=False)
        if list(scores.shape) != list(entry["shape"]):
            raise ValueError(f"{STOP_SCORE_ARCHIVE_INVALID}: shape {key}")
        if str(scores.dtype) != str(entry["dtype"]):
            raise ValueError(f"{STOP_SCORE_ARCHIVE_INVALID}: dtype {key}")
        if scores.shape[1] != len(payload["program_ids"]):
            raise ValueError(f"{STOP_SCORE_ARCHIVE_INVALID}: program width")
        rows += int(scores.shape[0])
    if rows != int(payload.get("rows", -1)):
        raise ValueError(f"{STOP_SCORE_ARCHIVE_INVALID}: row total")
    if len(seen) != int(payload.get("strata", -1)):
        raise ValueError(f"{STOP_SCORE_ARCHIVE_INVALID}: stratum total")
    return {
        "terminal": "PASS_D1_V2_SCORE_ARCHIVE",
        "score_archive_root_sha256": claimed,
        "rows": rows,
        "strata": len(seen),
        "programs": len(payload["program_ids"]),
    }


class ArchivedScoreSource:
    def __init__(self, score_archive_dir: Path | str) -> None:
        self.root = Path(score_archive_dir)
        self.manifest = json.loads(
            (self.root / MANIFEST_NAME).read_text(encoding="utf-8"))
        if self.manifest.get("schema") != SCHEMA:
            raise ValueError(f"{STOP_SCORE_ARCHIVE_INVALID}: schema")
        self.program_ids = [str(x) for x in self.manifest["program_ids"]]
        self._entries = {
            (str(e["donor_id"]), int(e["operator_index"])): e
            for e in self.manifest["entries"]
        }

    def strata(self) -> list[tuple[str, int]]:
        return sorted(self._entries)

    def load(self, donor: str, operator: int) -> np.ndarray:
        key = (str(donor), int(operator))
        if key not in self._entries:
            raise KeyError(key)
        return np.load(
            self.root / self._entries[key]["score_file"],
            mmap_mode="r", allow_pickle=False)
