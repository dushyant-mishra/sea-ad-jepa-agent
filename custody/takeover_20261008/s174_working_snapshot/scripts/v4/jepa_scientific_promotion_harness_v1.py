#!/usr/bin/env python3
"""Hash-bound scientific promotion state machine with recursive tainting."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


STATES = ("EXPLORATORY", "PROVISIONAL", "QUALIFIED", "FROZEN")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def validate_graph(graph: dict) -> None:
    nodes = set(graph)
    for node, record in graph.items():
        if record["state"] not in STATES:
            raise ValueError(f"invalid state for {node}")
        missing = set(record.get("depends_on", [])) - nodes
        if missing:
            raise ValueError(f"missing dependencies for {node}: {missing}")
    visiting, visited = set(), set()
    def walk(node):
        if node in visiting:
            raise ValueError("dependency cycle")
        if node in visited:
            return
        visiting.add(node)
        for parent in graph[node].get("depends_on", []):
            walk(parent)
        visiting.remove(node)
        visited.add(node)
    for node in nodes:
        walk(node)


def downstream(graph: dict, start: str) -> set[str]:
    found, frontier = set(), [start]
    while frontier:
        parent = frontier.pop()
        for node, record in graph.items():
            if parent in record.get("depends_on", []) and node not in found:
                found.add(node)
                frontier.append(node)
    return found


def invalidate(graph: dict, node: str, reason: str, evidence_sha256: str) -> dict:
    if node not in graph:
        raise KeyError(node)
    affected = {node} | downstream(graph, node)
    for item in affected:
        graph[item]["state"] = "EXPLORATORY"
        graph[item]["tainted"] = True
        graph[item]["taint_reason"] = reason
        graph[item]["taint_evidence_sha256"] = evidence_sha256
    return graph


def promote(graph: dict, node: str, target: str, validators: dict, reviewers: dict | None = None) -> dict:
    if target not in STATES:
        raise ValueError(target)
    record = graph[node]
    if STATES.index(target) != STATES.index(record["state"]) + 1:
        raise RuntimeError("promotion must advance exactly one state")
    if record.get("tainted"):
        raise RuntimeError("tainted artifact cannot promote")
    if target in {"QUALIFIED", "FROZEN"} and not validators:
        raise RuntimeError("executable validators required")
    if target in {"QUALIFIED", "FROZEN"} and not all(bool(v) for v in validators.values()):
        raise RuntimeError("validator failure blocks promotion")
    if target == "FROZEN":
        if not reviewers or not all(reviewers.get(name) == "PASS" for name in ("Representation-Geometry", "Statistics-Leakage", "Red-Team")):
            raise RuntimeError("ordered council PASS required for FROZEN")
        for parent in record.get("depends_on", []):
            if graph[parent]["state"] != "FROZEN" or graph[parent].get("tainted"):
                raise RuntimeError(f"dependency not frozen: {parent}")
    record["state"] = target
    record["validators"] = validators
    if reviewers:
        record["reviewers"] = reviewers
    return graph


def assert_frozen_consumable(graph: dict, node: str) -> None:
    record = graph[node]
    if record["state"] != "FROZEN" or record.get("tainted"):
        raise RuntimeError(f"artifact is not consumable: {node}")


def save_registry(path: Path, graph: dict) -> None:
    validate_graph(graph)
    atomic_json(path, {"schema": "jepa-scientific-promotion-registry-v1", "states": list(STATES), "artifacts": graph})
