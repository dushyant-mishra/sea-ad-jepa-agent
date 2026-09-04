"""Fail-closed contextual-target F1 production executor.

Real production execution is launch-authority guarded.  Synthetic and bounded
technical-fixture modes exist only for mechanics verification and cannot open
the full F1 population.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


STOP_UNAUTHORIZED = "STOP_F1_REAL_RUN_NOT_EXTERNALLY_AUTHORIZED"
LAUNCH_SCHEMA = "f1-real-production-execution-external-authority-v1"
EXTERNAL_REVIEW_REPOSITORY = "dushyant-mishra/sea-ad-jepa-agent"
EXTERNAL_REVIEW_OWNER = "dushyant-mishra"
CONTRACT_RELATIVE = Path("docs/agent/F1_REAL_PRODUCTION_EXECUTOR_CONTRACT_20260904.md")
EVIDENCE_LEVELS = (20, 40, 60, 80, 100)
PROGRESS_FIELDS = frozenset({"schema", "completed_shards", "completed_forwards", "elapsed_seconds"})

FROZEN_ROOTS = {
    "assignment_sha256": "12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617",
    "dedup_sha256": "3fcd11908723e2cc80db0f5a0f017ad382bd1ed9be522f97081587ae989c2423",
    "matched_null_sha256": "aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6",
    "evidence_mask_sha256": "d1eefdab177501a00370d71521ae86932e60540fb9f769dfe2b56c7994ca5c5a",
    "namespace_sha256": "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd",
    "namespace_semantic_root": "595fd8bc860b13ce9ec2a957b0f3d92f850effcb51ae6e2f06b8c5d25d7bd53f",
    "reader_split_sha256": "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511",
    "row_lineage_sha256": "a6065751667b35a38c5990107c6b3f0177e262f7d145addb24bea24206eeb61b",
    "observation_state_sha256": "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537",
    "program_weights_sha256": "001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70",
    "checkpoint_sha256": "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4",
    "constructor_sha256": "6bd641cd22c160dfbec4e1ae4a0cc31929af436526487383f290397f4f55eeaa",
    "encoder_sha256": "732ea46f72384f29d503de1e0cc9d853315e2493cace054cced74849aa77485a",
    "tokenizer_sha256": "2a2ba7f4c2e52364cce471466ebacceefc2a1fccb29f4959860c885f281a89f4",
    "accepted_preflight_root": "52691e1397e91eaedc8417f72623cd176108d8b57d84cd1d2d0b9fe7064b959e",
    "repaired_mechanics_root": "37c6e70b982dd300082a2b53a8fe0074c4426b9f571d1f825b8f6ad0d4d5f534",
}

FULL_TOPOLOGY = {
    "recipient_cells": 2_781,
    "statistical_assignments": 44_496,
    "unique_cell_q": 43_108,
    "compute_only_dedups": 1_388,
    "teacher_forwards": 43_108,
    "correct_forwards": 215_540,
    "matched_null_forwards": 215_540,
    "total_expensive_forwards": 474_188,
    "effect_rows": 222_480,
    "logical_shards": 1_400,
}

AUTHORITY_PATHS = {
    "assignment_sha256": Path("outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv"),
    "dedup_sha256": Path("outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_EXECUTION_DEDUP_MAP.csv"),
    "matched_null_sha256": Path("outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_PRIMARY_MAP.csv"),
    "evidence_mask_sha256": Path("outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_EVIDENCE_MASK_CONTRACT.md"),
    "namespace_sha256": Path("exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv"),
    "reader_split_sha256": Path("exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv"),
    "row_lineage_sha256": Path("outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_ROW_LINEAGE.csv"),
    "observation_state_sha256": Path("exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"),
    "program_weights_sha256": Path("exports/contextual_biology_v6r5a_20260822/program_weights.npz"),
    "checkpoint_sha256": Path("exports/prod41k_teacher_t1_20260823/t1_run/t1_checkpoint_u0000.pt"),
    "constructor_sha256": Path("src/sea_ad_jepa/v4/contextual_query_local.py"),
    "encoder_sha256": Path("src/sea_ad_jepa/v4/ipb_jepa.py"),
    "tokenizer_sha256": Path("src/sea_ad_jepa/v4/gene_tokenizer.py"),
}


class InjectedInterruption(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def validate_topology(value: dict[str, int]) -> bool:
    required = set(FULL_TOPOLOGY)
    if set(value) != required or any(type(value[key]) is not int or value[key] < 0 for key in required):
        raise RuntimeError("STOP_F1_TOPOLOGY_SCHEMA_MISMATCH")
    if value["statistical_assignments"] - value["unique_cell_q"] != value["compute_only_dedups"]:
        raise RuntimeError("STOP_F1_DEDUP_RECONCILIATION")
    if value["teacher_forwards"] != value["unique_cell_q"]:
        raise RuntimeError("STOP_F1_TEACHER_MULTIPLICITY")
    if value["correct_forwards"] != value["unique_cell_q"] * len(EVIDENCE_LEVELS):
        raise RuntimeError("STOP_F1_CORRECT_MULTIPLICITY")
    if value["matched_null_forwards"] != value["correct_forwards"]:
        raise RuntimeError("STOP_F1_NULL_MULTIPLICITY")
    if value["total_expensive_forwards"] != value["teacher_forwards"] + value["correct_forwards"] + value["matched_null_forwards"]:
        raise RuntimeError("STOP_F1_FORWARD_RECONCILIATION")
    if value["effect_rows"] != value["statistical_assignments"] * len(EVIDENCE_LEVELS):
        raise RuntimeError("STOP_F1_EFFECT_MULTIPLICITY")
    return True


validate_topology(FULL_TOPOLOGY)


def validate_private_output(path: Path) -> Path:
    resolved = Path(path).resolve()
    lowered = {part.lower() for part in resolved.parts}
    private_component = any(re.fullmatch(r"_?private(?:[-_].*)?", part.lower()) for part in resolved.parts)
    if not private_component or lowered & {"public", "docs"}:
        raise RuntimeError("STOP_F1_PRIVATE_OUTPUT_REQUIRED")
    return resolved


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip())
    return completed.stdout.strip()


def validate_launch_authority(path: Path | None, output_root: Path, expected: dict[str, str], repository_root: Path | None = None) -> dict[str, Any]:
    try:
        if path is None:
            raise ValueError("missing")
        authority_bytes = Path(path).read_bytes()
        payload = json.loads(authority_bytes.decode("utf-8"))
        if payload.get("schema") != LAUNCH_SCHEMA or type(payload.get("real_f1_execution_authorized")) is not bool or payload["real_f1_execution_authorized"] is not True:
            raise ValueError("schema/boolean")
        if Path(payload["output_root"]).resolve() != validate_private_output(output_root):
            raise ValueError("output")
        for field, value in expected.items():
            if payload.get(field) != value:
                raise ValueError(field)
        # The approval subject excludes only the external receipt fields, so a
        # repository-owner GitHub comment can bind already-final authority bytes
        # without a file/commit self-reference.
        subject = {key: value for key, value in payload.items() if key not in {"external_review_comment_api_url", "external_review_subject_sha256"}}
        subject_sha = canonical_sha(subject)
        if payload.get("external_review_subject_sha256") != subject_sha:
            raise ValueError("external review subject")
        api_url = str(payload.get("external_review_comment_api_url", ""))
        pattern = rf"^/repos/{re.escape(EXTERNAL_REVIEW_REPOSITORY)}/issues/comments/[1-9][0-9]*$"
        if not re.fullmatch(pattern, api_url):
            raise ValueError("external review URL")
        review = json.loads(subprocess.check_output(["gh", "api", api_url], text=True))
        expected_body = f"JEPA_F1_REAL_PRODUCTION_AUTHORITY_SHA256={subject_sha}"
        if review.get("user", {}).get("login") != EXTERNAL_REVIEW_OWNER or review.get("author_association") != "OWNER" or review.get("body", "").strip() != expected_body:
            raise ValueError("external owner review receipt")
        return payload
    except Exception as error:
        raise RuntimeError(f"{STOP_UNAUTHORIZED}: {type(error).__name__}") from error


def validate_reader_partition(partition: str) -> None:
    if partition != "reader_fit":
        raise RuntimeError("STOP_F1_READER_FIREWALL")


def authenticate_inputs(canonical_root: Path) -> dict[str, str]:
    root = Path(canonical_root).resolve()
    actual = {}
    for field, relative in AUTHORITY_PATHS.items():
        path = root / relative
        if field in {"constructor_sha256", "encoder_sha256", "tokenizer_sha256"}:
            actual[field] = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        else:
            actual[field] = sha256_file(path)
        if actual[field] != FROZEN_ROOTS[field]:
            raise RuntimeError(f"STOP_F1_AUTHORITY_MISMATCH:{field}")
    return actual


def read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_frozen_population(canonical_root: Path) -> dict[str, Any]:
    """Load and reconcile metadata-only schedules after hash authentication."""
    root = Path(canonical_root).resolve()
    authenticate_inputs(root)
    assignments = read_csv(root / AUTHORITY_PATHS["assignment_sha256"])
    dedup = read_csv(root / AUTHORITY_PATHS["dedup_sha256"])
    null_rows = read_csv(root / AUTHORITY_PATHS["matched_null_sha256"])
    if len(assignments) != FULL_TOPOLOGY["statistical_assignments"] or len(dedup) != FULL_TOPOLOGY["unique_cell_q"]:
        raise RuntimeError("STOP_F1_POPULATION_MULTIPLICITY")
    assignment_cells = {row["canonical_cell_id"] for row in assignments}
    if len(assignment_cells) != FULL_TOPOLOGY["recipient_cells"]:
        raise RuntimeError("STOP_F1_RECIPIENT_MULTIPLICITY")
    null_by_recipient: dict[str, dict[str, str]] = {}
    for row in null_rows:
        recipient = row["recipient_canonical_cell_id"]
        if recipient in null_by_recipient:
            raise RuntimeError("STOP_F1_NULL_MAP_DUPLICATE")
        if row["recipient_source"] != row["source_source"] or row["recipient_canonical_donor_id"] == row["source_canonical_donor_id"]:
            raise RuntimeError("STOP_F1_NULL_MAP_SEMANTICS")
        null_by_recipient[recipient] = row
    if set(null_by_recipient) != assignment_cells:
        raise RuntimeError("STOP_F1_NULL_MAP_MEMBERSHIP")
    assignment_pairs = {(row["canonical_cell_id"], int(row["selected_query_address"])) for row in assignments}
    dedup_pairs = {(row["canonical_cell_id"], int(row["selected_query_address"])) for row in dedup}
    if len(dedup_pairs) != len(dedup) or assignment_pairs != dedup_pairs:
        raise RuntimeError("STOP_F1_DEDUP_MEMBERSHIP")
    cell_geometry: dict[str, tuple[str, int, str]] = {}
    for row in assignments:
        value = (row["donor_id"], int(row["operator_index"]), row["source"])
        previous = cell_geometry.setdefault(row["canonical_cell_id"], value)
        if previous != value:
            raise RuntimeError("STOP_F1_CELL_GEOMETRY")
        validate_reader_partition("reader_fit")
    shards = {(donor, operator) for donor, operator, _ in cell_geometry.values()}
    if len(shards) != FULL_TOPOLOGY["logical_shards"]:
        raise RuntimeError("STOP_F1_SHARD_MULTIPLICITY")
    return {"assignments": assignments, "dedup": dedup, "null_by_recipient": null_by_recipient, "cell_geometry": cell_geometry}


@dataclass(frozen=True)
class MaterializedRow:
    canonical_cell_id: str
    row_locator: str
    operator: int
    counts_path: str
    counts_sha256: str
    row_index: int
    source_library: float


class ProductionMaterializedReader:
    """Selected-row, block-major reader over authenticated FULL104 CSR blocks."""
    BLOCK_MANIFEST_SHA = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"

    def __init__(self, canonical_root: Path, wanted: dict[str, tuple[int, str]]):
        from scipy.sparse import csr_matrix
        self._csr_matrix = csr_matrix
        self.root = Path(canonical_root).resolve()
        self.expression_root = self.root / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4"
        manifest_path = self.expression_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
        if sha256_file(manifest_path) != self.BLOCK_MANIFEST_SHA:
            raise RuntimeError("STOP_F1_BLOCK_MANIFEST_AUTHORITY")
        manifest = read_csv(manifest_path)
        if len(manifest) != 8_915 or {int(row["operator_index"]) for row in manifest} != set(range(42)):
            raise RuntimeError("STOP_F1_BLOCK_MANIFEST_GEOMETRY")
        by_operator: dict[int, list[dict[str, str]]] = defaultdict(list)
        for row in manifest:
            by_operator[int(row["operator_index"])].append(row)
        targets_by_operator: dict[int, set[str]] = defaultdict(set)
        for cell, (operator, _) in wanted.items():
            targets_by_operator[int(operator)].add(cell)
        found: dict[str, MaterializedRow] = {}
        for operator in sorted(targets_by_operator):
            targets = targets_by_operator[operator]
            for block in by_operator[operator]:
                meta_path = self.expression_root / block["meta_path"]
                if sha256_file(meta_path) != block["meta_sha256"]:
                    raise RuntimeError("STOP_F1_META_BLOCK_HASH")
                with meta_path.open("r", encoding="utf-8-sig", newline="") as handle:
                    for index, meta in enumerate(csv.DictReader(handle)):
                        cell = meta["canonical_cell_id"]
                        if cell not in targets:
                            continue
                        if cell in found or meta.get("reader_partition", "reader_fit") != "reader_fit":
                            raise RuntimeError("STOP_F1_SELECTED_ROW_FIREWALL")
                        expected_locator = wanted[cell][1]
                        if meta.get("row_locator") != expected_locator:
                            raise RuntimeError("STOP_F1_ROW_LOCATOR_MISMATCH")
                        found[cell] = MaterializedRow(cell, expected_locator, operator, block["counts_path"].replace("\\", "/"), block["counts_sha256"], index, float(meta["source_library"]))
            if not targets.issubset(found):
                raise RuntimeError("STOP_F1_SELECTED_ROW_MISSING")
        if set(found) != set(wanted):
            raise RuntimeError("STOP_F1_SELECTED_ROW_MEMBERSHIP")
        self.rows = found
        states_path = self.root / AUTHORITY_PATHS["observation_state_sha256"]
        with np.load(states_path, allow_pickle=False) as packed:
            self.states = {int(operator): state.astype(np.uint8) for operator, state in zip(packed["operator_index"], packed["states"])}

    def grouped_cells(self) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = defaultdict(list)
        for cell, row in self.rows.items():
            groups[row.counts_path].append(cell)
        return {path: sorted(cells) for path, cells in sorted(groups.items())}

    def read_block_cells(self, path_key: str, cells: list[str]) -> dict[str, np.ndarray]:
        requests = [self.rows[cell] for cell in cells]
        if any(row.counts_path != path_key for row in requests):
            raise RuntimeError("STOP_F1_PHYSICAL_BLOCK_REQUEST")
        expected = {row.counts_sha256 for row in requests}
        path = self.expression_root / path_key
        if len(expected) != 1 or sha256_file(path) != next(iter(expected)):
            raise RuntimeError("STOP_F1_COUNTS_BLOCK_HASH")
        with np.load(path, allow_pickle=False) as packed:
            matrix = self._csr_matrix((packed["data"], packed["indices"], packed["indptr"]), shape=tuple(packed["shape"]))
        result = {}
        for row in requests:
            raw = matrix.getrow(row.row_index).toarray().ravel().astype(np.float32)
            result[row.canonical_cell_id] = np.log1p(raw * np.float32(10_000.0 / row.source_library)).astype(np.float32)
        return result


def _identity(body: dict[str, Any]) -> str:
    return canonical_sha(body)


def forward_cache_identity(authority: dict[str, Any], *, role: str, recipient: str, input_cell: str,
                           q: int, evidence_level: int | None, physical_mask_sha256: str,
                           evidence_mask_sha256: str) -> str:
    if role not in {"teacher", "correct", "matched_null"}:
        raise ValueError("role")
    body = {
        "authority": authority,
        "role": role,
        "recipient": str(recipient),
        "input_cell": str(input_cell),
        "q": int(q),
        "physical_mask_sha256": str(physical_mask_sha256),
        "dtype": "float32",
        "autocast": False,
    }
    if role == "teacher":
        if input_cell != recipient:
            raise ValueError("teacher input")
        body["mask_semantics"] = "RICH_QUERY_SELF_ABLATED"
    else:
        if evidence_level not in EVIDENCE_LEVELS:
            raise ValueError("evidence level")
        if role == "correct" and input_cell != recipient:
            raise ValueError("correct input")
        body.update(evidence_level=int(evidence_level), evidence_mask_sha256=str(evidence_mask_sha256))
        if role == "matched_null":
            body["matched_null_source"] = str(input_cell)
            body["matched_null_authority"] = authority.get("matched_null_sha256")
    return _identity(body)


def qid_wrong_query_map(cell_id: str, queries: Iterable[int], root_key: str) -> dict[int, int]:
    unique = sorted({int(q) for q in queries})
    if len(unique) < 2:
        raise RuntimeError("STOP_F1_QID_UNESTIMABLE")
    ranked = sorted(unique, key=lambda q: hashlib.sha256(b"F1_QID_V2\0" + str(root_key).encode() + b"\0" + str(cell_id).encode() + b"\0" + int(q).to_bytes(4, "little", signed=False)).digest())
    return {query: ranked[(index + 1) % len(ranked)] for index, query in enumerate(ranked)}


def physical_shard_name(donor_id: str, operator: int) -> str:
    donor = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(donor_id)).strip("_.")
    if not donor:
        raise ValueError("empty donor")
    return f"{donor}__op{int(operator):03d}"


def _payload_sha(ordered_ids: list[str], values: np.ndarray) -> str:
    array = np.asarray(values)
    digest = hashlib.sha256()
    digest.update(json.dumps(ordered_ids, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    digest.update(array.dtype.str.encode("ascii"))
    digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


class AtomicEffectStore:
    def __init__(self, root: Path, implementation_fingerprint: str):
        self.root = Path(root).resolve(); self.root.mkdir(parents=True, exist_ok=True)
        self.fingerprint = str(implementation_fingerprint)

    def _path(self, shard_id: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+(?:__op[0-9]{3})?", shard_id):
            raise ValueError("unsafe shard id")
        return self.root / f"{shard_id}.npz"

    def _identity(self, shard_id: str, ids: list[str]) -> str:
        return canonical_sha({"shard_id": shard_id, "ordered_ids": ids, "implementation_fingerprint": self.fingerprint, "dtype": "float64", "columns": ["A", "direct_delta", "qid_margin", "qid_win"]})

    def commit(self, shard_id: str, ordered_ids: list[str], values: np.ndarray) -> Path:
        array = np.asarray(values)
        if array.dtype != np.float64 or array.shape != (len(ordered_ids), 4):
            raise TypeError("effect shard dtype/shape")
        path = self._path(shard_id)
        if path.exists():
            self.load(shard_id, ordered_ids)
            return path
        staging = path.with_suffix(".staging.npz")
        with staging.open("wb") as handle:
            np.savez(handle, values=array, identity_sha256=np.asarray(self._identity(shard_id, ordered_ids)), payload_semantic_sha256=np.asarray(_payload_sha(ordered_ids, array)))
            handle.flush(); os.fsync(handle.fileno())
        os.replace(staging, path)
        return path

    def load(self, shard_id: str, ordered_ids: list[str]) -> np.ndarray:
        path = self._path(shard_id)
        with np.load(path, allow_pickle=False) as packed:
            values = packed["values"].copy()
            identity = str(packed["identity_sha256"])
            payload = str(packed["payload_semantic_sha256"])
        if values.dtype != np.float64:
            raise RuntimeError("shard dtype mismatch")
        if identity != self._identity(shard_id, ordered_ids):
            raise RuntimeError("shard identity mismatch")
        if payload != _payload_sha(ordered_ids, values):
            raise RuntimeError("shard payload mismatch")
        return values


class AtomicForwardStore:
    """Atomic, semantic-hash-bound storage for contextual/direct states."""
    def __init__(self, root: Path, implementation_fingerprint: str):
        self.root = Path(root).resolve(); self.root.mkdir(parents=True, exist_ok=True)
        self.fingerprint = implementation_fingerprint

    def path(self, block_index: int) -> Path:
        return self.root / f"forward_block_{block_index:05d}.npz"

    def _identity(self, block_index: int, task_ids: list[str]) -> str:
        return canonical_sha({"block_index": block_index, "task_ids": task_ids, "implementation_fingerprint": self.fingerprint, "dtype": "float32", "shape_tail": [2, 160]})

    def commit(self, block_index: int, task_ids: list[str], values: np.ndarray) -> Path:
        array = np.asarray(values)
        if array.dtype != np.float32 or array.shape != (len(task_ids), 2, 160):
            raise TypeError("forward payload dtype/shape")
        path = self.path(block_index)
        if path.exists():
            self.load(block_index, task_ids)
            return path
        staging = path.with_suffix(".staging.npz")
        with staging.open("wb") as handle:
            np.savez(handle, values=array, task_ids=np.asarray(task_ids), identity_sha256=np.asarray(self._identity(block_index, task_ids)), payload_semantic_sha256=np.asarray(_payload_sha(task_ids, array)))
            handle.flush(); os.fsync(handle.fileno())
        os.replace(staging, path)
        return path

    def load(self, block_index: int, expected_task_ids: list[str]) -> np.ndarray:
        with np.load(self.path(block_index), allow_pickle=False) as packed:
            values = packed["values"].copy(); task_ids = packed["task_ids"].astype(str).tolist()
            identity = str(packed["identity_sha256"]); payload = str(packed["payload_semantic_sha256"])
        if task_ids != expected_task_ids or identity != self._identity(block_index, expected_task_ids):
            raise RuntimeError("forward shard identity mismatch")
        if values.dtype != np.float32 or payload != _payload_sha(task_ids, values):
            raise RuntimeError("forward shard payload mismatch")
        return values


def build_forward_tasks(population: dict[str, Any], reader: ProductionMaterializedReader, authority: dict[str, str]) -> list[dict[str, Any]]:
    from contextual_target_f1_preflight_core_v1 import evidence_mask
    tasks = []
    for row in population["dedup"]:
        cell = row["canonical_cell_id"]; q = int(row["selected_query_address"])
        operator = population["cell_geometry"][cell][1]
        state = reader.states[operator]
        physical_sha = hashlib.sha256(state.tobytes()).hexdigest()
        base = {"recipient": cell, "input_cell": cell, "q": q, "operator": operator, "recipient_row_locator": reader.rows[cell].row_locator}
        teacher_id = forward_cache_identity(authority, role="teacher", recipient=cell, input_cell=cell, q=q, evidence_level=None, physical_mask_sha256=physical_sha, evidence_mask_sha256="")
        tasks.append({**base, "role": "teacher", "evidence_level": None, "task_id": teacher_id})
        null_cell = population["null_by_recipient"][cell]["source_canonical_cell_id"]
        for level in EVIDENCE_LEVELS:
            visible = evidence_mask(state, reader.rows[cell].row_locator, q, level)
            mask_sha = hashlib.sha256(visible.astype(np.uint8).tobytes()).hexdigest()
            for role, input_cell in (("correct", cell), ("matched_null", null_cell)):
                task_id = forward_cache_identity(authority, role=role, recipient=cell, input_cell=input_cell, q=q, evidence_level=level, physical_mask_sha256=physical_sha, evidence_mask_sha256=mask_sha)
                tasks.append({**base, "role": role, "input_cell": input_cell, "evidence_level": level, "task_id": task_id})
    if len(tasks) != FULL_TOPOLOGY["total_expensive_forwards"] or len({row["task_id"] for row in tasks}) != len(tasks):
        raise RuntimeError("STOP_F1_FORWARD_TASK_TOPOLOGY")
    return tasks


def _execute_task_chunk(encoder: Any, tasks: list[dict[str, Any]], values_by_cell: dict[str, np.ndarray], reader: ProductionMaterializedReader, device: Any) -> np.ndarray:
    import torch
    from contextual_target_f1_preflight_core_v1 import evidence_mask, lean_query_local
    values, states, visible, queries = [], [], [], []
    for task in tasks:
        state = reader.states[int(task["operator"])]
        q = int(task["q"])
        if task["role"] == "teacher":
            mask = state == 1; mask = mask.copy(); mask[q] = False
        else:
            mask = evidence_mask(state, str(task["recipient_row_locator"]), q, int(task["evidence_level"]))
        if state[q] != 1 or mask[q]:
            raise RuntimeError("STOP_F1_QUERY_MASK_SEMANTICS")
        values.append(values_by_cell[str(task["input_cell"])]); states.append(state); visible.append(mask); queries.append(q)
    tensors = [torch.from_numpy(np.stack(array)) for array in (values, states, visible)]
    query_tensor = torch.tensor(queries, dtype=torch.long)
    x, physical, masks = [tensor.to(device) for tensor in tensors]; query_tensor = query_tensor.to(device)
    role = "teacher" if all(task["role"] == "teacher" for task in tasks) else "student"
    result, _ = lean_query_local(encoder, x, physical, masks, query_tensor, role)
    return torch.stack((result["contextual_state"], result["direct_state"]), dim=1).detach().float().cpu().numpy().astype(np.float32, copy=False)


def execute_forward_blocks(tasks: list[dict[str, Any]], reader: ProductionMaterializedReader, encoder: Any,
                           device: Any, store: AtomicForwardStore, batch_size: int = 4) -> list[dict[str, Any]]:
    by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        by_path[reader.rows[str(task["input_cell"])].counts_path].append(task)
    index = []
    for block_index, (path_key, block_tasks) in enumerate(sorted(by_path.items())):
        block_tasks.sort(key=lambda row: row["task_id"])
        task_ids = [row["task_id"] for row in block_tasks]
        try:
            stored = store.load(block_index, task_ids)
        except FileNotFoundError:
            cells = sorted({str(row["input_cell"]) for row in block_tasks})
            block_values = reader.read_block_cells(path_key, cells)
            chunks = []
            # Teacher and student roles cannot share a constructor call.
            ordered = sorted(block_tasks, key=lambda row: (row["role"] != "teacher", row["task_id"]))
            for role_class in ("teacher", "student"):
                subset = [row for row in ordered if (row["role"] == "teacher") == (role_class == "teacher")]
                for start in range(0, len(subset), batch_size):
                    chunk = subset[start:start + batch_size]
                    chunks.extend(zip((row["task_id"] for row in chunk), _execute_task_chunk(encoder, chunk, block_values, reader, device)))
            result_by_id = dict(chunks)
            stored = np.stack([result_by_id[task_id] for task_id in task_ids]).astype(np.float32, copy=False)
            store.commit(block_index, task_ids, stored)
        index.extend({"task_id": task_id, "block_index": block_index, "row_index": row_index} for row_index, task_id in enumerate(task_ids))
    if len(index) != len(tasks) or len({row["task_id"] for row in index}) != len(tasks):
        raise RuntimeError("STOP_F1_FORWARD_INDEX_RECONCILIATION")
    return index


def _cosine(left: np.ndarray, right: np.ndarray) -> float:
    a = np.asarray(left, np.float64); b = np.asarray(right, np.float64)
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denominator == 0 or not np.isfinite(denominator):
        raise RuntimeError("STOP_F1_COSINE_NUMERICAL")
    return float(np.dot(a, b) / denominator)


def load_forward_results(store: AtomicForwardStore, index: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    task_ids_all = [str(row["task_id"]) for row in index]
    if len(task_ids_all) != len(set(task_ids_all)):
        raise RuntimeError("STOP_F1_DUPLICATE_FORWARD_ID")
    by_block: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in index: by_block[int(row["block_index"])].append(row)
    result = {}
    for block_index, rows in sorted(by_block.items()):
        rows.sort(key=lambda row: int(row["row_index"]))
        if [int(row["row_index"]) for row in rows] != list(range(len(rows))):
            raise RuntimeError("STOP_F1_FORWARD_INDEX_ORDER")
        task_ids = [row["task_id"] for row in rows]
        values = store.load(block_index, task_ids)
        for task_id, value in zip(task_ids, values):
            if task_id in result:
                raise RuntimeError("STOP_F1_DUPLICATE_FORWARD_ID")
            result[task_id] = value
    if set(result) != set(task_ids_all) or len(result) != len(index):
        raise RuntimeError("STOP_F1_FORWARD_INDEX_RECONCILIATION")
    return result


def progress_record(*, completed_shards: int, completed_forwards: int, elapsed_seconds: float) -> dict[str, Any]:
    return {"schema": "f1-outcome-blind-progress-v1", "completed_shards": int(completed_shards), "completed_forwards": int(completed_forwards), "elapsed_seconds": float(elapsed_seconds)}


def reconcile_counts(observed: dict[str, int], expected: dict[str, int]) -> bool:
    validate_topology(expected)
    if observed != expected:
        raise RuntimeError("STOP_F1_FINAL_RECONCILIATION")
    return True


def validate_effect_ids(observed: list[str], expected: list[str]) -> bool:
    if len(observed) != len(set(observed)) or observed != expected:
        raise RuntimeError("STOP_F1_EFFECT_MEMBERSHIP")
    return True


def synthetic_schedule() -> list[dict[str, Any]]:
    rows = [{"kind": "teacher", "index": index} for index in range(2)]
    rows += [{"kind": role, "index": index} for role in ("correct", "matched_null") for index in range(14)]
    return rows


def count_schedule(schedule: list[dict[str, Any]]) -> dict[str, int]:
    return {"neural_forwards": sum(row.get("kind") in {"teacher", "correct", "matched_null"} for row in schedule)}


def run_synthetic(output_root: Path, interrupt_after_shards: int | None = None) -> dict[str, Any]:
    root = Path(output_root).resolve(); root.mkdir(parents=True, exist_ok=True)
    fingerprint = canonical_sha({"mode": "synthetic", "contract": "v1"})
    store = AtomicEffectStore(root / "shards", fingerprint)
    definitions = {
        "donor_a__op000": ["a0", "a1"],
        "donor_b__op001": ["b0", "b1"],
    }
    completed = 0
    for shard_id, ids in definitions.items():
        try:
            store.load(shard_id, ids)
        except FileNotFoundError:
            values = np.asarray([[index + 0.1, index + 0.2, index + 0.3, 1.0] for index in range(len(ids))], dtype=np.float64)
            store.commit(shard_id, ids, values)
        completed += 1
        if interrupt_after_shards is not None and completed >= interrupt_after_shards:
            raise InjectedInterruption("synthetic interruption")
    payloads = []
    for shard_id, ids in definitions.items():
        values = store.load(shard_id, ids)
        payloads.append({"shard_id": shard_id, "ordered_ids": ids, "payload_semantic_sha256": _payload_sha(ids, values)})
    result = {"status": "PASS_F1_SYNTHETIC_DRY_RUN", "shards": len(payloads), "scientific_root_sha256": canonical_sha(payloads), "real_f1_run": False}
    (root / "FINAL.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _actual_git_head(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def runtime_authority(worktree_root: Path) -> dict[str, str]:
    root = Path(worktree_root).resolve()
    source_relative = Path(__file__).resolve().relative_to(root).as_posix()
    contract_relative = CONTRACT_RELATIVE.as_posix()
    if subprocess.run(["git", "-C", str(root), "diff", "--quiet", "--", source_relative, contract_relative]).returncode:
        raise RuntimeError("STOP_F1_DIRTY_IMPLEMENTATION_BYTES")
    implementation_commit = _git(root, "log", "-1", "--format=%H", "--", source_relative)
    return {
        "repository_commit": implementation_commit,
        "executor_contract_sha256": sha256_file(root / CONTRACT_RELATIVE),
        "executor_source_sha256": sha256_file(Path(__file__)),
        **FROZEN_ROOTS,
    }


def run_technical_fixture(output_root: Path, canonical_root: Path, worktree_root: Path) -> dict[str, Any]:
    """Bounded real-reader/forward dry path; never loads full F1 assignments."""
    import torch
    from contextual_target_f1_preflight_core_v1 import MaterializedFixtureReader, lean_query_local, load_encoder
    from contextual_target_f1_preflight_executor_v1 import build_effect_row
    from run_contextual_target_f1_real_forward_preflight_v1 import prepare_chunk, read_fixture
    reader = MaterializedFixtureReader(Path(canonical_root), Path(worktree_root))
    ids = list(reader.rows)
    payload, sidecar, by_cell, timing = read_fixture(reader, 0, len(ids), 1)
    if set(payload) != {"normalized_values", "observation_states"} or len(sidecar) != len(ids):
        raise RuntimeError("STOP_F1_TECHNICAL_FIXTURE_READER")
    if not torch.cuda.is_available():
        raise RuntimeError("STOP_F1_TECHNICAL_FIXTURE_CUDA_REQUIRED")
    device = torch.device("cuda"); encoder = load_encoder(Path(canonical_root), device)
    outputs: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    cache_ids = []
    for role in ("teacher", "correct_student", "matched_null_student"):
        records = [row for row in reader.fixture["selected"] if row["role"] == role]
        for start in range(0, len(records), 4):
            chunk = records[start:start + 4]
            tensors, _, _ = prepare_chunk(chunk, role, payload, by_cell, False)
            x, state, visible, query = [tensor.to(device) for tensor in tensors]
            encoded, _ = lean_query_local(encoder, x, state, visible, query, "teacher" if role == "teacher" else "student")
            for position, record in enumerate(chunk):
                record_key = record["selection_sha256"]
                outputs[record_key] = (encoded["contextual_state"][position].detach().cpu().numpy(), encoded["direct_state"][position].detach().cpu().numpy())
                role_name = "correct" if role == "correct_student" else "matched_null" if role == "matched_null_student" else "teacher"
                cache_ids.append(canonical_sha({"bounded_record": record_key, "role": role_name, "cell": record["canonical_cell_id"], "q": int(record["q"]), "evidence": None if role_name == "teacher" else int(record["evidence_level"]), "input": record.get("null_source_cell") if role_name == "matched_null" else record["canonical_cell_id"]}))
    exemplars = {role: next(row for row in reader.fixture["selected"] if row["role"] == role) for role in ("teacher", "correct_student", "matched_null_student")}
    teacher = outputs[exemplars["teacher"]["selection_sha256"]]; correct = outputs[exemplars["correct_student"]["selection_sha256"]]; null = outputs[exemplars["matched_null_student"]["selection_sha256"]]
    # The accepted 51-record reader fixture has only one query per recipient,
    # so it cannot lawfully instantiate QID-v2.  Exercise QID separately with a
    # bounded synthetic same-recipient, distinct-query, 60%-evidence pair.  No
    # cross-cell relabelling and no additional neural forward are permitted.
    qid_queries = (7, 11)
    cyclic = qid_wrong_query_map("BOUNDED_SYNTHETIC_QID_RECIPIENT", qid_queries, "TECHNICAL_FIXTURE_ONLY")
    qid_states = {7: np.asarray([1.0, 0.0], np.float32), 11: np.asarray([-1.0, 0.0], np.float32)}
    qid_teacher = np.asarray([1.0, 0.0], np.float32)
    own_q = qid_queries[0]; wrong_q = cyclic[own_q]
    if wrong_q == own_q or wrong_q not in qid_states:
        raise RuntimeError("STOP_F1_TECHNICAL_FIXTURE_QID")
    mechanical_effect = build_effect_row(s_correct_contextual=correct[0], t_true_contextual=teacher[0], s_null_contextual=null[0], s_correct_direct=correct[1], t_true_direct=teacher[1], s_null_direct=null[1], own_similarity=_cosine(qid_states[own_q], qid_teacher), paired_wrong_similarity=_cosine(qid_states[wrong_q], qid_teacher))
    effect_values = np.asarray([[mechanical_effect[name] for name in ("A", "direct_delta", "qid_margin", "qid_win")]], dtype=np.float64)
    fingerprint = canonical_sha({"mode": "technical-fixture", "source": sha256_file(Path(__file__))})
    store = AtomicEffectStore(Path(output_root) / "bounded_shards", fingerprint)
    store.commit("bounded_fixture__op000", ["mechanical-effect-0"], effect_values)
    reloaded = store.load("bounded_fixture__op000", ["mechanical-effect-0"])
    if not np.array_equal(effect_values, reloaded):
        raise RuntimeError("STOP_F1_TECHNICAL_FIXTURE_RESUME")
    # Exercise the interruption/resume implementation independently as well.
    clean_root = Path(output_root) / "clean_mechanics"
    clean = run_synthetic(clean_root)
    mechanics_root = Path(output_root) / "resume_mechanics"
    try:
        run_synthetic(mechanics_root, interrupt_after_shards=1)
    except InjectedInterruption:
        pass
    resumed = run_synthetic(mechanics_root)
    clean_final_sha = sha256_file(clean_root / "FINAL.json"); resumed_final_sha = sha256_file(mechanics_root / "FINAL.json")
    if clean["scientific_root_sha256"] != resumed["scientific_root_sha256"] or clean_final_sha != resumed_final_sha:
        raise RuntimeError("STOP_F1_TECHNICAL_FIXTURE_RESUME_PARITY")
    result = {"status": "PASS_F1_REAL_PRODUCTION_EXECUTOR_BOUNDED_DRY_RUN", "reader_rows": len(ids), "forward_records": len(outputs), "role_counts": {role: sum(row["role"] == role for row in reader.fixture["selected"]) for role in ("teacher", "correct_student", "matched_null_student")}, "reader_timing": timing, "cache_identity_count": len(cache_ids), "cache_identity_unique": len(set(cache_ids)) == len(cache_ids), "sufficient_statistic_formed": True, "sufficient_statistic_payload_sha256": _payload_sha(["mechanical-effect-0"], effect_values), "shard_reload_exact": True, "uninterrupted_root_sha256": clean["scientific_root_sha256"], "resume_root_sha256": resumed["scientific_root_sha256"], "resume_final_bytes_sha256": resumed_final_sha, "uninterrupted_final_bytes_sha256": clean_final_sha, "resume_byte_and_root_parity": True, "real_f1_run": False, "biological_values_published": False}
    Path(output_root).mkdir(parents=True, exist_ok=True)
    (Path(output_root) / "DRY_RUN.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def run_production(output_root: Path, canonical_root: Path, worktree_root: Path) -> dict[str, Any]:
    """Production path reached only after external authority authentication."""
    authenticate_inputs(canonical_root)
    # A real launch consumes the frozen schedules without partial-population
    # options.  The separately reviewed launch packet supplies operational
    # batch/cadence values and invokes this complete scheduler.
    return execute_complete_population(output_root, canonical_root, worktree_root)


def execute_complete_population(output_root: Path, canonical_root: Path, worktree_root: Path) -> dict[str, Any]:
    import torch
    from contextual_target_f1_preflight_core_v1 import load_encoder
    root = validate_private_output(output_root); root.mkdir(parents=True, exist_ok=True)
    canonical = Path(canonical_root).resolve(); worktree = Path(worktree_root).resolve()
    authority = runtime_authority(worktree)
    population = load_frozen_population(canonical)
    wanted: dict[str, tuple[int, str]] = {}
    for cell, (_, operator, _) in population["cell_geometry"].items():
        null = population["null_by_recipient"][cell]
        wanted[cell] = (operator, null["recipient_row_locator"])
        source_cell = null["source_canonical_cell_id"]
        candidate = (operator, null["source_row_locator"])
        if source_cell in wanted and wanted[source_cell] != candidate:
            raise RuntimeError("STOP_F1_SOURCE_LOCATOR_CONFLICT")
        wanted[source_cell] = candidate
    reader = ProductionMaterializedReader(canonical, wanted)
    tasks = build_forward_tasks(population, reader, authority)
    fingerprint = canonical_sha({"authority": authority, "contract": sha256_file(worktree / CONTRACT_RELATIVE), "source": sha256_file(Path(__file__))})
    device = torch.device("cuda")
    if not torch.cuda.is_available():
        raise RuntimeError("STOP_F1_CUDA_REQUIRED")
    encoder = load_encoder(canonical, device)
    forward_store = AtomicForwardStore(root / "forward_shards", fingerprint)
    started = time.perf_counter()
    forward_index = execute_forward_blocks(tasks, reader, encoder, device, forward_store, batch_size=4)
    forward_values = load_forward_results(forward_store, forward_index)
    task_lookup = {(row["recipient"], int(row["q"]), row["role"], row["evidence_level"]): row["task_id"] for row in tasks}
    dedup_wrong = {(row["canonical_cell_id"], int(row["selected_query_address"])): int(row["wrong_query_address"]) for row in population["dedup"]}
    shard_assignments: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in population["assignments"]:
        shard_assignments[(row["donor_id"], int(row["operator_index"]))].append(row)
    effect_store = AtomicEffectStore(root / "effect_shards", fingerprint)
    all_effect_ids = []
    for donor_operator, rows in sorted(shard_assignments.items()):
        donor, operator = donor_operator
        rows.sort(key=lambda row: (row["canonical_cell_id"], row["program"], int(row["draw_replicate"]), int(row["selected_query_address"])))
        ids, values = [], []
        for assignment in rows:
            cell = assignment["canonical_cell_id"]; q = int(assignment["selected_query_address"]); wrong = dedup_wrong[(cell, q)]
            teacher = forward_values[task_lookup[(cell, q, "teacher", None)]]
            for level in EVIDENCE_LEVELS:
                correct = forward_values[task_lookup[(cell, q, "correct", level)]]
                null = forward_values[task_lookup[(cell, q, "matched_null", level)]]
                contextual = _cosine(correct[0], teacher[0]) - _cosine(null[0], teacher[0])
                direct = _cosine(correct[1], teacher[1]) - _cosine(null[1], teacher[1])
                if level == 60:
                    wrong_correct = forward_values[task_lookup[(cell, wrong, "correct", 60)]]
                    own_similarity = _cosine(correct[0], teacher[0]); wrong_similarity = _cosine(wrong_correct[0], teacher[0])
                    margin = own_similarity - wrong_similarity; win = 1.0 if margin > 0 else 0.0 if margin < 0 else 0.5
                else:
                    margin = np.nan; win = np.nan
                effect_id = canonical_sha({"evaluation_row_authority_sha256": assignment["evaluation_row_authority_sha256"], "evidence_level": level})
                ids.append(effect_id); values.append((contextual, contextual - direct, margin, win))
        shard_id = physical_shard_name(donor, operator)
        effect_store.commit(shard_id, ids, np.asarray(values, dtype=np.float64))
        all_effect_ids.extend(ids)
    expected_effect_ids = []
    for row in sorted(population["assignments"], key=lambda item: (item["donor_id"], int(item["operator_index"]), item["canonical_cell_id"], item["program"], int(item["draw_replicate"]), int(item["selected_query_address"]))):
        expected_effect_ids.extend(canonical_sha({"evaluation_row_authority_sha256": row["evaluation_row_authority_sha256"], "evidence_level": level}) for level in EVIDENCE_LEVELS)
    validate_effect_ids(all_effect_ids, expected_effect_ids)
    role_counts = {role: sum(task["role"] == role for task in tasks) for role in ("teacher", "correct", "matched_null")}
    observed = {
        "recipient_cells": len(population["cell_geometry"]),
        "statistical_assignments": len(population["assignments"]),
        "unique_cell_q": len(population["dedup"]),
        "compute_only_dedups": len(population["assignments"]) - len(population["dedup"]),
        "teacher_forwards": role_counts["teacher"],
        "correct_forwards": role_counts["correct"],
        "matched_null_forwards": role_counts["matched_null"],
        "total_expensive_forwards": len(forward_index),
        "effect_rows": len(all_effect_ids),
        "logical_shards": len(shard_assignments),
    }
    reconcile_counts(observed, FULL_TOPOLOGY)
    final = {
        "schema": "f1-real-production-executor-final-v1",
        "status": "COMPLETE_AWAITING_SEPARATE_SCIENTIFIC_ADJUDICATION",
        "implementation_fingerprint": fingerprint,
        "topology": observed,
        "forward_index_root_sha256": canonical_sha(forward_index),
        "effect_membership_root_sha256": canonical_sha(all_effect_ids),
        "elapsed_seconds": time.perf_counter() - started,
        "real_f1_run": True,
    }
    (root / "FINAL.json").write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return final


def dispatch(mode: str, output_root: Path, launch_authority: Path | None, expected: dict[str, str] | None = None,
             canonical_root: Path | None = None, worktree_root: Path | None = None) -> dict[str, Any]:
    if mode == "synthetic":
        return run_synthetic(output_root)
    if mode == "technical-fixture":
        if canonical_root is None or worktree_root is None:
            raise ValueError("technical fixture roots required")
        return run_technical_fixture(output_root, canonical_root, worktree_root)
    if mode != "production":
        raise ValueError("mode")
    expected = expected or runtime_authority(worktree_root or Path(__file__).resolve().parents[2])
    validate_launch_authority(launch_authority, output_root, expected, worktree_root or Path(__file__).resolve().parents[2])
    return run_production(output_root, canonical_root or Path("D:/Jepa project"), worktree_root or Path(__file__).resolve().parents[2])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--synthetic", action="store_true")
    modes.add_argument("--technical-fixture", action="store_true")
    modes.add_argument("--production", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--launch-authority", type=Path)
    parser.add_argument("--canonical-root", type=Path, default=Path(os.environ.get("JEPA_CANONICAL_ROOT", "D:/Jepa project")))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mode = "production" if args.production else "technical-fixture" if args.technical_fixture else "synthetic"
    result = dispatch(mode, args.output_root, args.launch_authority, canonical_root=args.canonical_root, worktree_root=Path(__file__).resolve().parents[2])
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
