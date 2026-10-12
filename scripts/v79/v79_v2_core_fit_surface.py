#!/usr/bin/env python3
"""Hash-first blinded input loader for the V79 V2_CORE fitter.

This module is intentionally ignorant of controller truth. It accepts only opaque
world IDs and the physical ``blinded_fit_inputs`` surface written by the frozen
world writer. It never maps opaque IDs to Q labels and never reads operator/matrix
identity, seeds, planted truth or scoring data.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np

from v79_v2_core_launch import FINAL_CONTRACT_SHA256

ROOT_MANIFEST_NAME = "V79_V2_CORE_WORLD_SET_MANIFEST_V1.json"
FIT_INDEX_NAME = "V79_V2_CORE_BLINDED_FIT_INDEX_V1.json"
FIT_ROOT_NAME = "blinded_fit_inputs"
OPAQUE_RE = re.compile(r"^[0-9a-f]{12}$")
REPLICATES = ("train", "same_donor", "new_donor")
DESIGN_KEYS = ("src", "donor", "cls", "log_lib")


class FitSurfaceRefused(RuntimeError):
    """The offered physical input is not the frozen blinded fit surface."""


def _refuse(message: str):
    raise FitSurfaceRefused(f"REFUSED blinded fit surface: {message}")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(Path(path).read_bytes().decode("utf-8"))
    except Exception as exc:
        _refuse(f"invalid JSON {path.name}: {exc}")
    if not isinstance(value, dict):
        _refuse(f"JSON object required: {path.name}")
    return value


def _safe_existing_file(base: Path, rel: str) -> Path:
    rel_path = Path(rel)
    if rel_path.is_absolute() or not rel_path.parts or ".." in rel_path.parts:
        _refuse(f"unsafe path {rel!r}")
    lexical = base / rel_path
    if not lexical.is_file():
        _refuse(f"missing file {rel}")
    try:
        resolved_base = base.resolve(strict=True)
        resolved = lexical.resolve(strict=True)
        resolved.relative_to(resolved_base)
    except Exception:
        _refuse(f"path escapes blinded surface: {rel}")
    return lexical


def _load_npy_checked(base: Path, rel: str, expected_sha: str) -> np.ndarray:
    path = _safe_existing_file(base, rel)
    actual = _sha(path)
    if actual != expected_sha:
        _refuse(f"hash mismatch for {rel}: {actual} != {expected_sha}")
    try:
        with path.open("rb") as f:
            arr = np.load(f, allow_pickle=False)
    except Exception as exc:
        _refuse(f"unreadable/forbidden ndarray {rel}: {exc}")
    if arr.dtype.hasobject:
        _refuse(f"object dtype forbidden: {rel}")
    return np.asarray(arr)


def _expected_output_paths() -> set[str]:
    out = {f"design/{key}.npy" for key in DESIGN_KEYS}
    out.add("support.npy")
    for rep in REPLICATES:
        out.add(f"observations/{rep}/observed.npy")
        out.add(f"observations/{rep}/detected.npy")
    return out


@dataclass(frozen=True)
class BlindedIndex:
    package_root: Path
    root_manifest: Mapping
    index: Mapping
    opaque_world_ids: tuple[str, ...]


@dataclass(frozen=True)
class BlindedWorld:
    package_root: Path
    opaque_world_id: str
    manifest_sha256: str
    manifest: Mapping
    design: Mapping[str, np.ndarray]
    support: np.ndarray
    observations: Mapping[str, Mapping[str, np.ndarray]]


@dataclass(frozen=True)
class GeneInputs:
    opaque_world_id: str
    gene_index: int
    replicate: str
    design: Mapping[str, np.ndarray]
    observed: np.ndarray
    detected: np.ndarray
    detection_mask: np.ndarray
    positive_mask: np.ndarray


def load_blinded_index(package_root: Path, *, expected_root_manifest_sha: str | None,
                       expected_index_sha: str | None) -> BlindedIndex:
    package_root = Path(package_root)
    root_path = _safe_existing_file(package_root, ROOT_MANIFEST_NAME)
    if expected_root_manifest_sha is not None and _sha(root_path) != expected_root_manifest_sha:
        _refuse("root manifest hash differs from accepted realization")
    root = _load_json(root_path)
    if root.get("schema") != "V79_V2_CORE_WORLD_SET_MANIFEST_V1":
        _refuse("wrong root manifest schema")
    if root.get("mode") != "QUALIFICATION_TRUTH_FREEZE":
        _refuse("wrong realization mode")
    if root.get("final_contract_sha256") != FINAL_CONTRACT_SHA256:
        _refuse("root manifest contract hash differs")
    if root.get("blinded_fit_root") != FIT_ROOT_NAME:
        _refuse("unexpected blinded fit root")
    if root.get("controller_truth_root") != "controller_truth":
        _refuse("unexpected controller truth root declaration")
    if root.get("benchmark_run") is not False or root.get("qualification_fits_run") != 0 or \
            root.get("training_authorized") is not False:
        _refuse("realization root already records downstream execution")
    index_rel = root.get("blinded_fit_index_path")
    if index_rel != f"{FIT_ROOT_NAME}/{FIT_INDEX_NAME}":
        _refuse("unexpected blinded index path")
    index_path = _safe_existing_file(package_root, index_rel)
    index_sha = _sha(index_path)
    if index_sha != root.get("blinded_fit_index_sha256"):
        _refuse("blinded index hash does not match root manifest")
    if expected_index_sha is not None and index_sha != expected_index_sha:
        _refuse("blinded index hash differs from accepted realization")
    index = _load_json(index_path)
    if index.get("schema") != "V79_V2_CORE_BLINDED_FIT_INDEX_V1":
        _refuse("wrong blinded index schema")
    if index.get("final_contract_sha256") != FINAL_CONTRACT_SHA256:
        _refuse("blinded index contract hash differs")
    worlds = index.get("worlds")
    if not isinstance(worlds, list) or index.get("world_count") != len(worlds):
        _refuse("blinded index world count mismatch")
    ids = []
    for rec in worlds:
        oid = rec.get("opaque_world_id") if isinstance(rec, dict) else None
        if not isinstance(oid, str) or not OPAQUE_RE.fullmatch(oid):
            _refuse(f"non-opaque world identifier {oid!r}")
        if rec.get("manifest_path") != f"{oid}/manifest.json":
            _refuse(f"unexpected manifest path for {oid}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(rec.get("manifest_sha256", ""))):
            _refuse(f"invalid manifest hash for {oid}")
        ids.append(oid)
    if len(set(ids)) != len(ids):
        _refuse("duplicate opaque world ID")
    return BlindedIndex(package_root, root, index, tuple(ids))


def load_blinded_world(package_root: Path, opaque_world_id: str) -> BlindedWorld:
    if not isinstance(opaque_world_id, str) or not OPAQUE_RE.fullmatch(opaque_world_id):
        _refuse(f"opaque 12-hex world ID required, got {opaque_world_id!r}")
    idx = load_blinded_index(package_root, expected_root_manifest_sha=None, expected_index_sha=None)
    recs = {r["opaque_world_id"]: r for r in idx.index["worlds"]}
    if opaque_world_id not in recs:
        _refuse(f"unknown opaque world ID {opaque_world_id}")
    fit_root = Path(package_root) / FIT_ROOT_NAME
    world_dir = fit_root / opaque_world_id
    manifest_path = _safe_existing_file(world_dir, "manifest.json")
    manifest_sha = _sha(manifest_path)
    if manifest_sha != recs[opaque_world_id]["manifest_sha256"]:
        _refuse(f"world manifest hash mismatch for {opaque_world_id}")
    manifest = _load_json(manifest_path)
    if manifest.get("schema") != "V79_V2_CORE_BLINDED_WORLD_DATA_MANIFEST_V1" or \
            manifest.get("opaque_world_id") != opaque_world_id:
        _refuse("world manifest identity/schema mismatch")
    if manifest.get("final_contract_sha256") != FINAL_CONTRACT_SHA256:
        _refuse("world manifest contract hash differs")
    outputs = manifest.get("generated_outputs")
    if not isinstance(outputs, dict):
        _refuse("generated_outputs must be an object")
    expected = _expected_output_paths()
    if set(outputs) != expected:
        extra = sorted(set(outputs) - expected)
        missing = sorted(expected - set(outputs))
        _refuse(f"forbidden/unexpected fit output paths; extra={extra}, missing={missing}")
    physical = {p.relative_to(world_dir).as_posix() for p in world_dir.rglob("*") if p.is_file()}
    if physical != expected | {"manifest.json"}:
        _refuse("physical blinded world contains unmanifested or missing files")
    design = {key: _load_npy_checked(world_dir, f"design/{key}.npy", outputs[f"design/{key}.npy"])
              for key in DESIGN_KEYS}
    support = _load_npy_checked(world_dir, "support.npy", outputs["support.npy"])
    observations = {}
    for rep in REPLICATES:
        observations[rep] = {
            kind: _load_npy_checked(world_dir, f"observations/{rep}/{kind}.npy",
                                    outputs[f"observations/{rep}/{kind}.npy"])
            for kind in ("observed", "detected")
        }
    n_cells = len(design["src"])
    if any(np.asarray(design[k]).ndim != 1 or len(design[k]) != n_cells for k in DESIGN_KEYS):
        _refuse("fit design arrays must be aligned 1-D cell vectors")
    if support.ndim != 2 or support.shape[0] != n_cells:
        _refuse("support must be cell x gene")
    if support.dtype != np.bool_:
        support = support.astype(bool, copy=False)
    for rep, obs in observations.items():
        if obs["observed"].shape != support.shape or obs["detected"].shape != support.shape:
            _refuse(f"observation shape mismatch for {rep}")
    return BlindedWorld(Path(package_root), opaque_world_id, manifest_sha, manifest,
                        design, support, observations)


def load_gene_inputs(world: BlindedWorld, *, gene_index: int, replicate: str) -> GeneInputs:
    if replicate not in REPLICATES:
        _refuse(f"unknown replicate {replicate!r}")
    if not isinstance(gene_index, int) or gene_index < 0 or gene_index >= world.support.shape[1]:
        _refuse(f"gene index out of range: {gene_index!r}")
    observed = np.asarray(world.observations[replicate]["observed"][:, gene_index])
    detected = np.asarray(world.observations[replicate]["detected"][:, gene_index])
    measured = np.asarray(world.support[:, gene_index], dtype=bool)
    positive = measured & (observed > 0)
    return GeneInputs(world.opaque_world_id, gene_index, replicate, world.design,
                      observed, detected, measured, positive)
