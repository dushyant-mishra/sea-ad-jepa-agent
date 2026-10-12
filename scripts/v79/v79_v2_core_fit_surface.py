#!/usr/bin/env python3
"""Hash-first blinded input loader for the V79 V2_CORE fitter.

The loader never parses the unblinded root world-set manifest. Fit-side authority is
a SHA-pinned blinded index plus exact-schema per-world manifests/arrays.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np

from v79_v2_core_fit_contract import SOURCE_CONTRACT_SHA256 as FINAL_CONTRACT_SHA256

ROOT_MANIFEST_NAME = "V79_V2_CORE_WORLD_SET_MANIFEST_V1.json"
FIT_INDEX_NAME = "V79_V2_CORE_BLINDED_FIT_INDEX_V1.json"
FIT_ROOT_NAME = "blinded_fit_inputs"
OPAQUE_RE = re.compile(r"^[0-9a-f]{12}$")
REPLICATES = ("train", "same_donor", "new_donor")
DESIGN_KEYS = ("src", "donor", "cls", "log_lib")
ALLOWED_MODES = ("QUALIFICATION_TRUTH_FREEZE", "ENGINEERING_TEST_ONLY")
QUALIFICATION_ROOT_MANIFEST_SHA256 = "84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de"
QUALIFICATION_INDEX_SHA256 = "8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40"
INDEX_KEYS = {"schema", "final_contract_sha256", "pairing_amendment_sha256", "generator_bundle_sha256",
              "world_count", "worlds", "benchmark_run", "qualification_fits_run", "training_authorized"}
WORLD_REC_KEYS = {"opaque_world_id", "manifest_path", "manifest_sha256"}
WORLD_MANIFEST_KEYS = {"schema", "opaque_world_id", "final_contract_sha256", "pairing_amendment_sha256",
                       "generator_bundle_sha256", "generated_outputs", "benchmark_run",
                       "qualification_fits_run", "training_authorized"}


class FitSurfaceRefused(RuntimeError):
    pass


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
        resolved_base = base.resolve(strict=True); resolved = lexical.resolve(strict=True); resolved.relative_to(resolved_base)
    except Exception:
        _refuse(f"path escapes blinded surface: {rel}")
    return lexical


def _load_npy_checked(base: Path, rel: str, expected_sha: str) -> np.ndarray:
    path = _safe_existing_file(base, rel); actual = _sha(path)
    if actual != expected_sha:
        _refuse(f"hash mismatch for {rel}: {actual} != {expected_sha}")
    try:
        with path.open("rb") as f: arr = np.load(f, allow_pickle=False)
    except Exception as exc:
        _refuse(f"unreadable/forbidden ndarray {rel}: {exc}")
    if arr.dtype.hasobject: _refuse(f"object dtype forbidden: {rel}")
    return np.asarray(arr)


def _expected_output_paths() -> set[str]:
    out = {f"design/{key}.npy" for key in DESIGN_KEYS}; out.add("support.npy")
    for rep in REPLICATES:
        out.add(f"observations/{rep}/observed.npy"); out.add(f"observations/{rep}/detected.npy")
    return out


@dataclass(frozen=True)
class BlindedIndex:
    fit_root: Path
    execution_mode: str
    root_manifest_sha256: str
    index_sha256: str
    index: Mapping
    opaque_world_ids: tuple[str, ...]


@dataclass(frozen=True)
class BlindedWorld:
    fit_root: Path
    execution_mode: str
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


def load_blinded_index(package_root: Path, *, expected_mode: str, expected_root_manifest_sha: str | None,
                       expected_index_sha: str | None) -> BlindedIndex:
    if expected_mode not in ALLOWED_MODES: _refuse(f"unsupported expected mode {expected_mode!r}")
    if not expected_root_manifest_sha or not expected_index_sha: _refuse("root and blinded-index SHA-256 pins are mandatory")
    package_root = Path(package_root); root_path = _safe_existing_file(package_root, ROOT_MANIFEST_NAME); root_sha = _sha(root_path)
    if root_sha != expected_root_manifest_sha: _refuse("root manifest hash differs from supplied authority")
    if expected_mode == "QUALIFICATION_TRUTH_FREEZE":
        if root_sha != QUALIFICATION_ROOT_MANIFEST_SHA256 or expected_index_sha != QUALIFICATION_INDEX_SHA256:
            _refuse("qualification mode requires the immutable realized root/index authority")
    elif root_sha == QUALIFICATION_ROOT_MANIFEST_SHA256 or expected_index_sha == QUALIFICATION_INDEX_SHA256:
        _refuse("engineering mode may not consume the frozen qualification package")
    fit_root = package_root / FIT_ROOT_NAME; index_path = _safe_existing_file(fit_root, FIT_INDEX_NAME); index_sha = _sha(index_path)
    if index_sha != expected_index_sha: _refuse("blinded index hash differs from supplied authority")
    index = _load_json(index_path)
    if set(index) != INDEX_KEYS: _refuse("blinded index key set differs")
    if index.get("schema") != "V79_V2_CORE_BLINDED_FIT_INDEX_V1" or index.get("final_contract_sha256") != FINAL_CONTRACT_SHA256:
        _refuse("wrong blinded index schema/contract")
    if index.get("benchmark_run") is not False or index.get("qualification_fits_run") != 0 or index.get("training_authorized") is not False:
        _refuse("blinded index already records downstream execution")
    worlds = index.get("worlds")
    if not isinstance(worlds, list) or index.get("world_count") != len(worlds): _refuse("blinded index world count mismatch")
    ids=[]
    for rec in worlds:
        if not isinstance(rec, Mapping) or set(rec) != WORLD_REC_KEYS: _refuse("blinded world record key set differs")
        oid=rec.get("opaque_world_id")
        if not isinstance(oid,str) or not OPAQUE_RE.fullmatch(oid): _refuse(f"non-opaque world identifier {oid!r}")
        if rec.get("manifest_path") != f"{oid}/manifest.json": _refuse(f"unexpected manifest path for {oid}")
        if not re.fullmatch(r"[0-9a-f]{64}",str(rec.get("manifest_sha256",""))): _refuse(f"invalid manifest hash for {oid}")
        ids.append(oid)
    if len(set(ids)) != len(ids): _refuse("duplicate opaque world ID")
    return BlindedIndex(fit_root, expected_mode, root_sha, index_sha, index, tuple(ids))


def load_blinded_world(index: BlindedIndex, opaque_world_id: str) -> BlindedWorld:
    if not isinstance(index, BlindedIndex): _refuse("validated BlindedIndex authority is required")
    if not isinstance(opaque_world_id,str) or not OPAQUE_RE.fullmatch(opaque_world_id): _refuse(f"opaque 12-hex world ID required, got {opaque_world_id!r}")
    recs={r["opaque_world_id"]:r for r in index.index["worlds"]}
    if opaque_world_id not in recs: _refuse(f"unknown opaque world ID {opaque_world_id}")
    world_dir=index.fit_root/opaque_world_id; manifest_path=_safe_existing_file(world_dir,"manifest.json"); manifest_sha=_sha(manifest_path)
    if manifest_sha != recs[opaque_world_id]["manifest_sha256"]: _refuse(f"world manifest hash mismatch for {opaque_world_id}")
    manifest=_load_json(manifest_path)
    if set(manifest) != WORLD_MANIFEST_KEYS: _refuse("world manifest key set differs")
    if manifest.get("schema") != "V79_V2_CORE_BLINDED_WORLD_DATA_MANIFEST_V1" or manifest.get("opaque_world_id") != opaque_world_id:
        _refuse("world manifest identity/schema mismatch")
    if manifest.get("final_contract_sha256") != FINAL_CONTRACT_SHA256: _refuse("world manifest contract hash differs")
    if manifest.get("benchmark_run") is not False or manifest.get("qualification_fits_run") != 0 or manifest.get("training_authorized") is not False:
        _refuse("world manifest already records downstream execution")
    outputs=manifest.get("generated_outputs"); expected=_expected_output_paths()
    if not isinstance(outputs,dict): _refuse("generated_outputs must be an object")
    if set(outputs) != expected: _refuse(f"forbidden/unexpected fit output paths; extra={sorted(set(outputs)-expected)}, missing={sorted(expected-set(outputs))}")
    physical={p.relative_to(world_dir).as_posix() for p in world_dir.rglob("*") if p.is_file()}
    if physical != expected|{"manifest.json"}: _refuse("physical blinded world contains unmanifested or missing files")
    design={key:_load_npy_checked(world_dir,f"design/{key}.npy",outputs[f"design/{key}.npy"]) for key in DESIGN_KEYS}
    support=_load_npy_checked(world_dir,"support.npy",outputs["support.npy"])
    observations={}
    for rep in REPLICATES:
        observations[rep]={kind:_load_npy_checked(world_dir,f"observations/{rep}/{kind}.npy",outputs[f"observations/{rep}/{kind}.npy"]) for kind in ("observed","detected")}
    n_cells=len(design["src"])
    if any(np.asarray(design[k]).ndim!=1 or len(design[k])!=n_cells for k in DESIGN_KEYS): _refuse("fit design arrays must be aligned 1-D cell vectors")
    if support.ndim!=2 or support.shape[0]!=n_cells: _refuse("support must be cell x gene")
    if support.dtype!=np.bool_: support=support.astype(bool,copy=False)
    for rep,obs in observations.items():
        if obs["observed"].shape!=support.shape or obs["detected"].shape!=support.shape: _refuse(f"observation shape mismatch for {rep}")
    return BlindedWorld(index.fit_root,index.execution_mode,opaque_world_id,manifest_sha,manifest,design,support,observations)


def load_gene_inputs(world: BlindedWorld, *, gene_index: int, replicate: str) -> GeneInputs:
    if replicate not in REPLICATES: _refuse(f"unknown replicate {replicate!r}")
    if not isinstance(gene_index,int) or gene_index<0 or gene_index>=world.support.shape[1]: _refuse(f"gene index out of range: {gene_index!r}")
    observed=np.asarray(world.observations[replicate]["observed"][:,gene_index]); detected=np.asarray(world.observations[replicate]["detected"][:,gene_index])
    measured=np.asarray(world.support[:,gene_index],dtype=bool); positive=measured&(observed>0)
    return GeneInputs(world.opaque_world_id,gene_index,replicate,world.design,observed,detected,measured,positive)
