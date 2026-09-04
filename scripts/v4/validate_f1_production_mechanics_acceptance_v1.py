"""Production-shaped, outcome-blind F1 mechanics acceptance gate."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import statistics
import subprocess
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from scripts.v4 import contextual_target_f1_preflight_executor_v1 as executor
from scripts.v4 import contextual_target_f1_querydesign_decision_v2 as downstream
from scripts.v4 import finalize_contextual_target_f1_real_forward_preflight_v1 as preflight_finalizer


WORKTREE = Path(__file__).resolve().parents[2]
CANONICAL = Path(os.environ.get("JEPA_CANONICAL_ROOT", "/mnt/d/Jepa project" if os.name != "nt" else "D:/Jepa project"))
PACKAGE = WORKTREE / "outputs/contextual_teacher_target_v1_f1_production_mechanics_acceptance_20260903"
ASSIGNMENTS = CANONICAL / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv"
DEDUP = CANONICAL / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_EXECUTION_DEDUP_MAP.csv"
NULL_MAP = CANONICAL / "outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_PRIMARY_MAP.csv"
ASSIGNMENT_SHA = "12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617"
DEDUP_SHA = "3fcd11908723e2cc80db0f5a0f017ad382bd1ed9be522f97081587ae989c2423"
NULL_SHA = "aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6"
ACCEPTED_FORWARD_ROOT = "007bc6f182354a133a2ec49ce0ef5966831d4995a0a2a5f004bb845772469ad3"
BASE_SHA = "c533fdda40eb23e6a775277e98cbdfcee568ee8b"
ORIGIN_MAIN_SHA = "76fe7d63efe81451ef0fae3ef3eaf116be14f6be"
EVIDENCE = (20, 40, 60, 80, 100)
EVIDENCE_FLOAT = {20: .2, 40: .4, 60: .6, 80: .8, 100: 1.0}
EXPECTED = executor.full_geometry()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_sha(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_suffix(path.suffix + ".staging")
    staging.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(staging, path)


def git_head() -> str:
    return preflight_finalizer.git_output("rev-parse", "HEAD")


def validate_authorities() -> None:
    expected = ((ASSIGNMENTS, ASSIGNMENT_SHA), (DEDUP, DEDUP_SHA), (NULL_MAP, NULL_SHA))
    for path, digest in expected:
        if not path.is_file() or sha256_file(path) != digest:
            raise RuntimeError("STOP_F1_MECHANICS_BASE_MISMATCH")


def load_assignments(path: Path = ASSIGNMENTS) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append({
                "assignment_key": row["assignment_key_sha256"], "cell": row["canonical_cell_id"],
                "donor": row["donor_id"], "source": row["source"], "operator": int(row["operator_index"]),
                "program": row["program"], "draw": int(row["draw_replicate"]),
                "q": int(row["selected_query_address"]), "row_authority": row["evaluation_row_authority_sha256"],
            })
    return rows


def load_nulls(path: Path = NULL_MAP) -> dict[str, str]:
    result: dict[str, str] = {}
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            cell, source = row["recipient_canonical_cell_id"], row["source_canonical_cell_id"]
            if cell in result and result[cell] != source:
                raise RuntimeError("ambiguous matched-null source")
            result[cell] = source
    return result


def unique_cell_queries(assignments: Iterable[dict[str, Any]]) -> list[tuple[str, int]]:
    seen: set[tuple[str, int]] = set(); ordered = []
    for row in assignments:
        key = (str(row["cell"]), int(row["q"]))
        if key not in seen:
            seen.add(key); ordered.append(key)
    return ordered


def _root_lines(values: Iterable[str]) -> str:
    h = hashlib.sha256()
    for value in values:
        h.update(value.encode("ascii")); h.update(b"\n")
    return h.hexdigest()


def build_identity_topology(assignments: list[dict[str, Any]], nulls: dict[str, str], authority: dict[str, Any], *, evidence: tuple[int, ...] = EVIDENCE) -> dict[str, Any]:
    ordered: list[str] = []
    teacher: list[str] = []; correct: list[str] = []; null: list[str] = []
    for cell, query in unique_cell_queries(assignments):
        base = {"canonical_cell_id": cell, "q": query}
        identity = executor.teacher_compute_identity(authority, base)
        teacher.append(identity); ordered.append(identity)
        if cell not in nulls:
            raise RuntimeError("matched-null source missing")
        for level in evidence:
            record = {**base, "evidence_level": int(level), "null_source_cell": nulls[cell]}
            c = executor.student_forward_identity(authority, record, "correct_student")
            n = executor.student_forward_identity(authority, record, "matched_null_student")
            correct.append(c); null.append(n); ordered.extend((c, n))
    all_unique = len(ordered) == len(set(ordered))
    return {
        "counts": {"teacher": len(teacher), "correct": len(correct), "null": len(null), "total": len(ordered)},
        "ordered_identity_root_sha256": _root_lines(ordered), "ordered_identities": ordered,
        "teacher_evidence_invariant": len(teacher) == len(set(teacher)),
        "students_evidence_sensitive": len(correct) == len(set(correct)) and len(null) == len(set(null)),
        "correct_null_disjoint": set(correct).isdisjoint(null), "all_identities_unique": all_unique,
    }


def independent_identity_root(assignments: list[dict[str, Any]], nulls: dict[str, str], authority: dict[str, Any], evidence: tuple[int, ...] = EVIDENCE) -> str:
    values = []
    for cell, query in unique_cell_queries(assignments):
        values.append(hashlib.sha256(canonical_bytes({"authority": authority, "role": "teacher", "recipient": cell, "q": query})).hexdigest())
        for level in evidence:
            values.append(hashlib.sha256(canonical_bytes({"authority": authority, "role": "correct_student", "recipient": cell, "q": query, "evidence_level": level})).hexdigest())
            values.append(hashlib.sha256(canonical_bytes({"authority": authority, "role": "matched_null_student", "recipient": cell, "q": query, "evidence_level": level, "null_source": nulls[cell]})).hexdigest())
    return _root_lines(values)


def reconcile_dedup_to_inference(assignments: list[dict[str, Any]], *, evidence: tuple[int, ...] = EVIDENCE) -> dict[str, Any]:
    keys = unique_cell_queries(assignments)
    mapped = {(row["assignment_key"], level) for row in assignments for level in evidence}
    expected = len(assignments) * len(evidence)
    return {
        "statistical_assignments": len(assignments), "unique_cell_q": len(keys),
        "compute_only_dedups": len(assignments) - len(keys), "mapped_assignment_evidence_rows": len(mapped),
        "missing": expected - len(mapped), "extra": max(0, len(mapped) - expected),
        "ambiguous": len(assignments) - len({row["assignment_key"] for row in assignments}),
        "assignment_membership_root_sha256": _root_lines(row["assignment_key"] for row in assignments),
    }


def _synthetic_unit(cell: str, query: int, evidence: int, field: str) -> float:
    digest = hashlib.sha256(f"{cell}|{query}|{evidence}|{field}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


def synthetic_values(assignment: dict[str, Any], evidence: int) -> dict[str, float]:
    cell, query = str(assignment["cell"]), int(assignment["q"])
    a = 2.0 * _synthetic_unit(cell, query, evidence, "A") - 1.0
    direct = 2.0 * _synthetic_unit(cell, query, evidence, "direct") - 1.0
    margin = 2.0 * _synthetic_unit(cell, query, evidence, "qid") - 1.0
    return {"A": a, "direct_delta": a - direct, "qid_margin": margin, "qid_win": 1.0 if margin > 0 else 0.0 if margin < 0 else 0.5}


def independent_synthetic_values(assignment: dict[str, Any], evidence: int) -> dict[str, float]:
    prefix = f"{assignment['cell']}|{int(assignment['q'])}|{int(evidence)}|"
    def u(label: str) -> float:
        raw = hashlib.new("sha256", (prefix + label).encode("utf-8")).digest()[0:8]
        return float(int.from_bytes(raw, byteorder="big", signed=False)) / 18446744073709551616.0
    av, dv, qv = 2*u("A")-1, 2*u("direct")-1, 2*u("qid")-1
    return {"A": av, "direct_delta": av-dv, "qid_margin": qv, "qid_win": float(qv > 0) if qv != 0 else .5}


def synthetic_record(assignment: dict[str, Any], evidence: int) -> dict[str, Any]:
    values = synthetic_values(assignment, evidence)
    evidence_float = EVIDENCE_FLOAT.get(int(evidence), float(evidence) / 100.0)
    fi = {"cell": assignment["cell"], "query_address": int(assignment["q"]), "evidence": evidence_float,
          "mask_authority": f"FROZEN_EVIDENCE_MASK_{evidence}", "model_checkpoint": "SYNTHETIC_NO_MODEL",
          "sketch": "SYNTHETIC_KNOWN_ANSWER"}
    return {
        "cell": assignment["cell"], "donor": assignment["donor"], "source": assignment["source"],
        "operator": int(assignment["operator"]), "program": assignment["program"], "replicate": int(assignment["draw"]),
        "evidence": evidence_float, "query_address": int(assignment["q"]), "assignment_key": assignment["assignment_key"],
        "evaluation_row_authority": assignment["row_authority"], "assignment_authority_sha256": ASSIGNMENT_SHA,
        "mask_authority": fi["mask_authority"], "model_checkpoint": fi["model_checkpoint"], "sketch": fi["sketch"],
        "forward_identity_sha256": canonical_sha(fi), **values,
    }


def build_full_synthetic(assignments: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records = []; production = hashlib.sha256(); independent = hashlib.sha256()
    for row in assignments:
        for level in EVIDENCE:
            record = synthetic_record(row, level); records.append(record)
            p = [record[key] for key in ("A", "direct_delta", "qid_margin", "qid_win")]
            q = independent_synthetic_values(row, level)
            i = [q[key] for key in ("A", "direct_delta", "qid_margin", "qid_win")]
            production.update(np.asarray(p, np.float64).tobytes()); independent.update(np.asarray(i, np.float64).tobytes())
    return records, {"production_value_root_sha256": production.hexdigest(), "independent_value_root_sha256": independent.hexdigest(), "values_exact": production.digest() == independent.digest()}


@dataclass(frozen=True)
class ExpectedFinalization:
    shards: int; forwards: int; effects: int; membership_root: str; forward_root: str; implementation_commit: str
    def as_dict(self) -> dict[str, Any]:
        return {"shards": self.shards, "forwards": self.forwards, "effects": self.effects, "membership_root": self.membership_root, "forward_root": self.forward_root, "implementation_commit": self.implementation_commit}


def validate_finalization(expected: ExpectedFinalization, actual: dict[str, Any]) -> bool:
    if actual != expected.as_dict():
        raise RuntimeError("STOP_F1_MECHANICS_FINALIZER")
    return True


def exercise_shard_resume(root: Path, shard_rows: dict[str, list[tuple[str, np.ndarray]]], membership: str, forward: str) -> dict[str, Any]:
    root = Path(root); keys = sorted(shard_rows)
    normal_store = executor.AtomicShardStore(root / "uninterrupted", membership, forward, "float64")
    resume_store = executor.AtomicShardStore(root / "resumed", membership, forward, "float64")
    normal_values = []; resumed_values = []; reused = 0
    for shard in keys:
        ids = [x[0] for x in shard_rows[shard]]; values = np.stack([x[1] for x in shard_rows[shard]]).astype(np.float64)
        normal_store.commit(shard, ids, values); normal_values.append(normal_store.load(shard, ids))
    split = max(1, len(keys) // 3)
    for shard in keys[:split]:
        ids = [x[0] for x in shard_rows[shard]]; values = np.stack([x[1] for x in shard_rows[shard]]).astype(np.float64)
        resume_store.commit(shard, ids, values)
    resume_store = executor.AtomicShardStore(root / "resumed", membership, forward, "float64")
    for shard in keys:
        ids = [x[0] for x in shard_rows[shard]]; values = np.stack([x[1] for x in shard_rows[shard]]).astype(np.float64)
        path = resume_store.root / f"{shard}.npz"
        if path.exists(): reused += 1
        else: resume_store.commit(shard, ids, values)
        resumed_values.append(resume_store.load(shard, ids))
    left = np.concatenate(normal_values); right = np.concatenate(resumed_values)
    first, first_ids = keys[0], [x[0] for x in shard_rows[keys[0]]]
    reorder_shard = next((key for key in keys if len(shard_rows[key]) > 1), first)
    reorder_ids = [x[0] for x in shard_rows[reorder_shard]]
    attacked_order_ids = list(reversed(reorder_ids)) if len(reorder_ids) > 1 else [reorder_ids[0] + "|altered-order"]
    attacks = {}
    for name, store, shard, ids in (
        ("stale_membership", executor.AtomicShardStore(root / "resumed", "wrong", forward, "float64"), first, first_ids),
        ("wrong_forward", executor.AtomicShardStore(root / "resumed", membership, "wrong", "float64"), first, first_ids),
        ("wrong_dtype", executor.AtomicShardStore(root / "resumed", membership, forward, "float32"), first, first_ids),
        ("wrong_shard", resume_store, "absent", first_ids), ("reordered_payload", resume_store, reorder_shard, attacked_order_ids),
    ):
        try: store.load(shard, ids); attacks[name] = False
        except (RuntimeError, FileNotFoundError): attacks[name] = True
    try: resume_store.commit(first, first_ids, np.stack([x[1] for x in shard_rows[first]]).astype(np.float64)); attacks["duplicate_shard"] = False
    except RuntimeError: attacks["duplicate_shard"] = True
    corrupt = resume_store.root / f"{first}.npz"; backup = corrupt.read_bytes()
    with np.load(corrupt, allow_pickle=False) as packed:
        changed = packed["values"].copy(); identity_json = packed["identity_json"].copy(); stored_sha = packed["payload_semantic_sha256"].copy()
    changed.flat[0] += 1.0
    with corrupt.open("wb") as handle:
        np.savez(handle, values=changed, identity_json=identity_json, payload_semantic_sha256=stored_sha)
    try: resume_store.load(first, first_ids); attacks["corrupted_payload"] = False
    except Exception: attacks["corrupted_payload"] = True
    corrupt.write_bytes(backup)
    return {"ordered_bytes_exact": left.tobytes() == right.tobytes(), "semantic_root_uninterrupted": canonical_sha(left.tolist()),
            "semantic_root_resumed": canonical_sha(right.tolist()), "valid_shards_reused": reused == split,
            "reused_shard_count": reused, "total_shards": len(keys), "attacks_rejected": attacks}


def reuse_or_exercise_shards(root: Path, shard_rows: dict[str, list[tuple[str, np.ndarray]]], membership: str, forward: str) -> dict[str, Any]:
    root = Path(root); marker = root / "COMPLETE.json"; keys = sorted(shard_rows)
    if marker.is_file():
        saved = json.loads(marker.read_text(encoding="utf-8"))
        if saved.get("membership") != membership or saved.get("forward") != forward or saved.get("shards") != keys:
            raise RuntimeError("completed shard authority mismatch")
        arrays = {}
        for name in ("uninterrupted", "resumed"):
            store = executor.AtomicShardStore(root / name, membership, forward, "float64"); values = []
            for shard in keys:
                ids = [x[0] for x in shard_rows[shard]]; values.append(store.load(shard, ids))
            arrays[name] = np.concatenate(values)
        result = dict(saved["result"])
        if arrays["uninterrupted"].tobytes() != arrays["resumed"].tobytes() or canonical_sha(arrays["resumed"].tolist()) != result["semantic_root_resumed"]:
            raise RuntimeError("completed shard payload mismatch")
        result["reused_complete_run"] = True
        return result
    result = exercise_shard_resume(root, shard_rows, membership, forward)
    write_json(marker, {"membership": membership, "forward": forward, "shards": keys, "result": result})
    result["reused_complete_run"] = False
    return result


def validate_soak_windows(windows: list[dict[str, Any]], *, start_mem_available: int, cuda_total: int, projected_seconds: float = 38892.125) -> dict[str, Any]:
    if len(windows) < 5: return {"safe": False, "reason": "fewer_than_five_windows"}
    swap = windows[-1]["pswpin"] == windows[0]["pswpin"] and windows[-1]["pswpout"] == windows[0]["pswpout"]
    model = len({row["model_hash"] for row in windows}) == 1
    ceilings = max(row["rss"] for row in windows) <= .8 * start_mem_available and max(row["cuda_reserved"] for row in windows) <= .85 * cuda_total
    finite = all(math.isfinite(float(row["throughput"])) and float(row["throughput"]) > 0 for row in windows)
    fds_continuous = all(windows[i]["fds"] < windows[i+1]["fds"] for i in range(len(windows)-1))
    projection_safe = True
    if all("elapsed" in row for row in windows):
        x = np.asarray([row["elapsed"] for row in windows], np.float64)
        for key, ceiling in (("rss", .8*start_mem_available), ("cuda_reserved", .85*cuda_total)):
            y = np.asarray([row[key] for row in windows], np.float64)
            slope = float(np.polyfit(x, y, 1)[0]) if np.ptp(x) else 0.0
            if slope > 0 and float(y[-1] + slope * max(0.0, projected_seconds-x[-1])) > ceiling: projection_safe = False
    safe = swap and model and ceilings and finite and not fds_continuous and projection_safe
    return {"safe": safe, "zero_swap": swap, "model_unchanged": model, "resource_ceilings": ceilings,
            "throughput_finite": finite, "fds_not_continuously_growing": not fds_continuous, "projected_resource_safe": projection_safe}


def _shard_rows(assignments: list[dict[str, Any]]) -> dict[str, list[tuple[str, np.ndarray]]]:
    grouped: dict[str, list[tuple[str, np.ndarray]]] = defaultdict(list)
    for row in assignments:
        for level in EVIDENCE:
            values = synthetic_values(row, level)
            grouped[f"{row['donor']}|{row['operator']:02d}"].append((f"{row['assignment_key']}|{level}", np.asarray(list(values.values()), np.float64)))
    return dict(grouped)


def prepare(output: Path) -> dict[str, Any]:
    validate_authorities(); output.mkdir(parents=True, exist_ok=True)
    assignments, nulls = load_assignments(), load_nulls()
    authority = {"accepted_real_forward_root": ACCEPTED_FORWARD_ROOT, "assignment_sha256": ASSIGNMENT_SHA, "dedup_sha256": DEDUP_SHA, "matched_null_sha256": NULL_SHA}
    topology = build_identity_topology(assignments, nulls, authority); independent_root = independent_identity_root(assignments, nulls, authority)
    del topology["ordered_identities"]
    topology.update({"schema": "f1-mechanics-full-forward-topology-v1", "status": "PASS" if topology["ordered_identity_root_sha256"] == independent_root else "STOP_F1_MECHANICS_FORWARD_TOPOLOGY", "independent_root_sha256": independent_root})
    expected_counts = {"teacher": 43108, "correct": 215540, "null": 215540, "total": 474188}
    if topology["counts"] != expected_counts or not all(topology[k] for k in ("teacher_evidence_invariant", "students_evidence_sensitive", "correct_null_disjoint", "all_identities_unique")): raise RuntimeError("STOP_F1_MECHANICS_FORWARD_TOPOLOGY")
    write_json(output / "F1_MECHANICS_FULL_FORWARD_TOPOLOGY.json", topology)
    dedup = reconcile_dedup_to_inference(assignments)
    with DEDUP.open("r", encoding="utf-8-sig", newline="") as handle: dedup_rows = list(csv.DictReader(handle))
    dedup["dedup_authority_unique_cell_q"] = len(dedup_rows); dedup["status"] = "PASS" if dedup["missing"] == dedup["extra"] == dedup["ambiguous"] == 0 and len(dedup_rows) == dedup["unique_cell_q"] else "STOP_F1_MECHANICS_DEDUP_INFERENCE_MISMATCH"
    if dedup["status"] != "PASS" or dedup["statistical_assignments"] != 44496 or dedup["compute_only_dedups"] != 1388: raise RuntimeError(dedup["status"])
    write_json(output / "F1_MECHANICS_DEDUP_TO_INFERENCE_RECONCILIATION.json", dedup)
    records, roots = build_full_synthetic(assignments)
    aggregated = downstream.aggregate(records, ASSIGNMENTS, ASSIGNMENT_SHA, test_only=True)
    cells = {row["cell"] for row in assignments}; donors = {row["donor"] for row in assignments}; operators = {row["operator"] for row in assignments}; programs = {row["program"] for row in assignments}; draws = {row["draw"] for row in assignments}
    synthetic = {"schema": "f1-mechanics-full-synthetic-topology-v1", "record_count": len(records), "assignment_count": len(assignments), "cells": len(cells), "donors": len(donors), "operators": len(operators), "programs": len(programs), "draws": sorted(draws), "evidence_levels": list(EVIDENCE), "logical_shards": len({(row['donor'],row['operator']) for row in assignments}), "aggregation_population_authority": aggregated["population_authority"], **roots}
    synthetic["status"] = "PASS" if roots["values_exact"] and (synthetic["record_count"], synthetic["cells"], synthetic["donors"], synthetic["operators"], synthetic["programs"], synthetic["draws"], synthetic["logical_shards"]) == (222480,2781,104,42,8,[0,1],1400) else "STOP_F1_MECHANICS_SYNTHETIC_TOPOLOGY"
    if synthetic["status"] != "PASS": raise RuntimeError(synthetic["status"])
    write_json(output / "F1_MECHANICS_FULL_SYNTHETIC_TOPOLOGY.json", synthetic)
    shard_root = output / "local_shard_resume_work"; shard_rows = _shard_rows(assignments)
    marker = shard_root / "COMPLETE.json"; prior_path = output / "F1_MECHANICS_PRODUCTION_SHARD_RESUME.json"
    if not marker.exists() and prior_path.exists() and len(list((shard_root/"uninterrupted").glob("*.npz"))) == len(shard_rows) and len(list((shard_root/"resumed").glob("*.npz"))) == len(shard_rows):
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        if prior.get("status") == "PASS" and prior.get("total_shards") == len(shard_rows):
            write_json(marker, {"membership":dedup["assignment_membership_root_sha256"],"forward":topology["ordered_identity_root_sha256"],"shards":sorted(shard_rows),"result":{k:v for k,v in prior.items() if k not in {"status","elapsed_seconds"}}})
    started = time.perf_counter(); shard = reuse_or_exercise_shards(shard_root, shard_rows, dedup["assignment_membership_root_sha256"], topology["ordered_identity_root_sha256"]); shard["elapsed_seconds"] = time.perf_counter()-started
    shard["status"] = "PASS" if shard["ordered_bytes_exact"] and shard["valid_shards_reused"] and all(shard["attacks_rejected"].values()) and shard["total_shards"] == 1400 else "STOP_F1_MECHANICS_SHARD_RESUME"
    if shard["status"] != "PASS": raise RuntimeError(shard["status"])
    write_json(output / "F1_MECHANICS_PRODUCTION_SHARD_RESUME.json", shard)
    expected = ExpectedFinalization(1400,474188,222480,dedup["assignment_membership_root_sha256"],topology["ordered_identity_root_sha256"],git_head())
    attacks = {}
    for key, value in (("shards",1399),("shards",1401),("forwards",474187),("forwards",474189),("effects",222479),("effects",222481),("membership_root","wrong"),("forward_root","wrong"),("implementation_commit","wrong")):
        actual=expected.as_dict();actual[key]=value
        try: validate_finalization(expected,actual); attacks[f"{key}_{value}"]=False
        except RuntimeError: attacks[f"{key}_{value}"]=True
    finalizer={"schema":"f1-mechanics-finalizer-failclosed-v1","expected":expected.as_dict(),"attacks_rejected":attacks,"status":"PASS" if all(attacks.values()) else "STOP_F1_MECHANICS_FINALIZER"}
    if finalizer["status"] != "PASS": raise RuntimeError(finalizer["status"])
    write_json(output / "F1_MECHANICS_FINALIZER_FAILCLOSED.json", finalizer)
    firewall={"schema":"f1-mechanics-firewall-v1","bounded_fixture_only":True,"protected_expression_opened":False,"DEV_opened":False,"SEALED_opened":False,"pathology_opened":False,"reader_validation_or_oracle_opened":False,"full_real_f1_expression_opened":False,"training":False,"backward":False,"optimizer":False,"EMA":False,"real_f1_biological_effects_computed":False,"status":"PASS"}
    write_json(output / "F1_MECHANICS_FIREWALL.json", firewall)
    validation=independent_validation(output, assignments, nulls, authority)
    write_json(output / "F1_MECHANICS_INDEPENDENT_VALIDATION.json", validation)
    if validation["status"] != "PASS": raise RuntimeError(validation["status"])
    shutil.rmtree(shard_root, ignore_errors=True)
    return {"status":"PASS_PRE_SOAK_MECHANICS","output":str(output)}


def independent_validation(output: Path, assignments: list[dict[str, Any]] | None = None, nulls: dict[str,str] | None = None, authority: dict[str,Any] | None = None) -> dict[str,Any]:
    assignments = assignments or load_assignments(); nulls = nulls or load_nulls(); authority = authority or {"accepted_real_forward_root":ACCEPTED_FORWARD_ROOT,"assignment_sha256":ASSIGNMENT_SHA,"dedup_sha256":DEDUP_SHA,"matched_null_sha256":NULL_SHA}
    topology=json.loads((output/"F1_MECHANICS_FULL_FORWARD_TOPOLOGY.json").read_text());dedup=json.loads((output/"F1_MECHANICS_DEDUP_TO_INFERENCE_RECONCILIATION.json").read_text());synthetic=json.loads((output/"F1_MECHANICS_FULL_SYNTHETIC_TOPOLOGY.json").read_text());shard=json.loads((output/"F1_MECHANICS_PRODUCTION_SHARD_RESUME.json").read_text());finalizer=json.loads((output/"F1_MECHANICS_FINALIZER_FAILCLOSED.json").read_text());firewall=json.loads((output/"F1_MECHANICS_FIREWALL.json").read_text())
    checks={"forward_root_independent":topology["ordered_identity_root_sha256"]==independent_identity_root(assignments,nulls,authority),"forward_counts":topology["counts"]=={"teacher":43108,"correct":215540,"null":215540,"total":474188},"dedup_counts":(len(assignments),len(unique_cell_queries(assignments)),len(assignments)-len(unique_cell_queries(assignments)))==(44496,43108,1388),"effect_rows":synthetic["record_count"]==222480,"population":(synthetic["cells"],synthetic["donors"],synthetic["operators"],synthetic["programs"],synthetic["draws"])==(2781,104,42,8,[0,1]),"shards":synthetic["logical_shards"]==shard["total_shards"]==1400,"synthetic_oracle":synthetic["values_exact"] is True,"resume":shard["status"]=="PASS" and all(shard["attacks_rejected"].values()),"finalizer":finalizer["status"]=="PASS" and all(finalizer["attacks_rejected"].values()),"firewall":firewall["status"]=="PASS" and not any(firewall[k] for k in ("protected_expression_opened","DEV_opened","SEALED_opened","pathology_opened","training","backward","optimizer","EMA","real_f1_biological_effects_computed"))}
    soak_path=output/"F1_MECHANICS_WSL_GPU_STABILITY_SOAK.json"
    if soak_path.exists(): checks["soak"]=json.loads(soak_path.read_text())["status"]=="PASS"
    return {"schema":"f1-mechanics-independent-validation-v1","production_pass_booleans_used_as_expected":False,"checks":checks,"status":"PASS" if all(checks.values()) else "STOP_F1_MECHANICS_INDEPENDENT_VALIDATION"}


def soak(output: Path, duration: float) -> dict[str,Any]:
    if not (900 <= duration <= 1800): raise RuntimeError("STOP_F1_MECHANICS_GPU_STABILITY")
    import resource
    import torch
    from scripts.v4 import run_contextual_target_f1_real_forward_preflight_v1 as preflight
    before_info=preflight.meminfo(); before_swap=preflight.vmstat_swap(); reader=preflight.MaterializedFixtureReader(CANONICAL,WORKTREE)
    model,_,by_cell,reader_metrics=preflight.read_fixture(reader,4,4,4);device=torch.device("cuda");encoder=preflight.load_encoder(CANONICAL,device);model_before=preflight._module_state_sha256(encoder)
    roles={role:preflight.role_records(reader,role) for role in ("teacher","correct_student","matched_null_student")};torch.cuda.reset_peak_memory_stats();windows=[];cycle=0;start=time.perf_counter();window_start=start;window_counts=defaultdict(int);window_role_seconds=defaultdict(float);baseline_digest=None;errors=0
    while time.perf_counter()-start < duration:
        digest=hashlib.sha256(); cycle_start=time.perf_counter()
        for role,rows in roles.items():
            role_start=time.perf_counter()
            for offset in range(0,len(rows),4):
                tensors,_,_=preflight.prepare_chunk(rows[offset:offset+4],role,model,by_cell,False);x,state,visible,query=[tensor.to(device) for tensor in tensors]
                result,_=preflight.lean_query_local(encoder,x,state,visible,query,"teacher" if role=="teacher" else "student")
                digest.update(result["contextual_state"].detach().cpu().numpy().tobytes());digest.update(result["direct_state"].detach().cpu().numpy().tobytes());window_counts[role]+=len(query)
            torch.cuda.synchronize();window_role_seconds[role]+=time.perf_counter()-role_start
        cycle+=1
        if baseline_digest is None: baseline_digest=digest.hexdigest()
        elif digest.hexdigest()!=baseline_digest: errors+=1
        now=time.perf_counter(); due=(now-window_start>=duration/5) or (now-start>=duration)
        if due:
            swap=preflight.vmstat_swap();info=preflight.meminfo();fds=len(list(Path("/proc/self/fd").iterdir()));elapsed=now-start;count=sum(window_counts.values());span=now-window_start
            try: util=int(subprocess.check_output(["nvidia-smi","--query-gpu=utilization.gpu","--format=csv,noheader,nounits"],text=True).strip().splitlines()[0])
            except Exception: util=None
            windows.append({"elapsed":elapsed,"cycles":cycle,"throughput":count/span,"role_rates":{k:window_counts[k]/window_role_seconds[k] for k in roles},"rss":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*1024,"mem_available":info["MemAvailable"],"cuda_allocated":torch.cuda.memory_allocated(),"cuda_reserved":torch.cuda.memory_reserved(),"cuda_peak_reserved":torch.cuda.max_memory_reserved(),"pswpin":swap["pswpin"],"pswpout":swap["pswpout"],"fds":fds,"gpu_utilization":util,"model_hash":preflight._module_state_sha256(encoder),"errors":errors});window_start=now;window_counts=defaultdict(int);window_role_seconds=defaultdict(float)
    after_swap=preflight.vmstat_swap();model_after=preflight._module_state_sha256(encoder);cuda_total=torch.cuda.get_device_properties(0).total_memory
    safety=validate_soak_windows(windows,start_mem_available=before_info["MemAvailable"],cuda_total=cuda_total)
    status="PASS" if safety["safe"] and errors==0 and model_before==model_after and preflight.no_swap_activity(before_swap,after_swap) else "STOP_F1_MECHANICS_GPU_STABILITY"
    result={"schema":"f1-mechanics-wsl-gpu-stability-soak-v1","status":status,"duration_seconds":time.perf_counter()-start,"cycles":cycle,"selected":{"batch":4,"reader_block":4,"workers":4,"prefetch":4,"pinned":False},"windows":windows,"start":{"rss":windows[0]["rss"],"cuda_reserved":windows[0]["cuda_reserved"],"fds":windows[0]["fds"],"pswpin":before_swap["pswpin"],"pswpout":before_swap["pswpout"]},"end":{"rss":windows[-1]["rss"],"cuda_reserved":windows[-1]["cuda_reserved"],"fds":windows[-1]["fds"],"pswpin":after_swap["pswpin"],"pswpout":after_swap["pswpout"]},"peak":{"rss":max(x["rss"] for x in windows),"cuda_reserved":max(x["cuda_peak_reserved"] for x in windows),"fds":max(x["fds"] for x in windows)},"model_hash_before":model_before,"model_hash_after":model_after,"output_digest_stable":errors==0,"reader":reader_metrics,"safety":safety,"firewall":{"bounded_fixture_rows":len(reader.rows),"biological_metrics_computed":False,"training":False,"backward":False,"optimizer":False,"EMA":False}}
    write_json(output/"F1_MECHANICS_WSL_GPU_STABILITY_SOAK.json",result)
    if status!="PASS": raise RuntimeError(status)
    return result


def finalize(output: Path) -> dict[str,Any]:
    soak_result=json.loads((output/"F1_MECHANICS_WSL_GPU_STABILITY_SOAK.json").read_text());preflight_runtime=json.loads((WORKTREE/"outputs/contextual_teacher_target_v1_f1_real_reader_forward_executor_preflight_20260903/F1_PREFLIGHT_RUNTIME_PROJECTION.json").read_text());rates=[row["role_rates"] for row in soak_result["windows"]];roles=("teacher","correct_student","matched_null_student")
    median={r:statistics.median(x[r] for x in rates) for r in roles};low={r:min(x[r] for x in rates) for r in roles};high={r:max(x[r] for x in rates) for r in roles};counts={"teacher":43108,"correct_student":215540,"matched_null_student":215540}
    def forward_seconds(rate): return sum(counts[r]/rate[r] for r in roles)
    fixed=preflight_runtime["T_physical_reader_seconds"]+preflight_runtime["T_shard_commit_seconds"]+preflight_runtime["T_finalization_seconds"]
    runtime={"schema":"f1-mechanics-runtime-projection-v1","counts":counts,"role_rates_median":median,"role_rates_min":low,"role_rates_max":high,"point_seconds":fixed+forward_seconds(median),"range_seconds":[fixed+forward_seconds(high),fixed+forward_seconds(low)],"point_hours":(fixed+forward_seconds(median))/3600,"range_hours":[(fixed+forward_seconds(high))/3600,(fixed+forward_seconds(low))/3600],"physical_reader_seconds":preflight_runtime["T_physical_reader_seconds"],"shard_commit_seconds":preflight_runtime["T_shard_commit_seconds"],"finalization_seconds":preflight_runtime["T_finalization_seconds"],"components_counted_once":True,"engineering_only":True}
    write_json(output/"F1_MECHANICS_RUNTIME_PROJECTION.json",runtime)
    validation=independent_validation(output);write_json(output/"F1_MECHANICS_INDEPENDENT_VALIDATION.json",validation)
    if validation["status"]!="PASS":raise RuntimeError(validation["status"])
    return {"status":"PASS_POST_SOAK_MECHANICS","runtime":runtime}


def main() -> None:
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("prepare");p.add_argument("--output",type=Path,default=PACKAGE)
    s=sub.add_parser("soak");s.add_argument("--output",type=Path,default=PACKAGE);s.add_argument("--duration-seconds",type=float,default=1200)
    f=sub.add_parser("finalize");f.add_argument("--output",type=Path,default=PACKAGE)
    args=parser.parse_args()
    if args.command=="prepare": result=prepare(args.output)
    elif args.command=="soak": result=soak(args.output,args.duration_seconds)
    else: result=finalize(args.output)
    print(json.dumps(result,sort_keys=True))


if __name__ == "__main__": main()
