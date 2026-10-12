#!/usr/bin/env python3
"""Deterministic physical package writer for V79 V2_CORE worlds.

The successful engineering path is explicitly barred from the frozen qualification
seed. Qualification realization requires a separate controller authorization whose
generator-bundle SHA matches the exact bytes executing this writer. This module
writes data/truth packages only; it never benchmarks or fits a model.
"""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from typing import Any

import numpy as np

import generate_v79_v2_core_worlds as G
import v79_v2_core_world_assembly as A

QUALIFICATION_SEED_ROOT = 31_000_000
ROOT_MANIFEST_NAME = "V79_V2_CORE_WORLD_SET_MANIFEST_V1.json"
ENV_LOCK_SHA256 = "5253ddca79c5f1b11eff2432b39679f16a68a885486a333d244357452261c782"
WINDOWS_EXECUTION_PLATFORM = "WINDOWS_LOCKED_QUALIFICATION_ENVIRONMENT"

_BUNDLE_PATHS = (
    "scripts/v79/v79_v2_core_launch.py",
    "scripts/v79/generate_v79_v2_core_worlds.py",
    "scripts/v79/v79_v2_core_planting.py",
    "scripts/v79/v79_v2_core_observation.py",
    "scripts/v79/v79_v2_core_world_assembly.py",
    "scripts/v79/v79_v2_core_world_writer.py",
    "results/v79/v2_core_qualification_amendments/V79_V2_CORE_Q10_Q11_PAIRING_AMENDMENT_V1.json",
)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(Path(path).read_bytes())


def _json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _safe_rel(rel: str) -> Path:
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts or not p.parts:
        raise SystemExit(f"STOP: unsafe package path {rel!r}")
    return p


def _portable_rel(path: Path) -> str:
    return path.as_posix()


def generator_bundle_sha256(root: Path) -> str:
    root = Path(root)
    h = hashlib.sha256()
    for rel in sorted(_BUNDLE_PATHS):
        path = root / rel
        if not path.is_file():
            raise SystemExit(f"STOP: generator bundle file missing: {rel}")
        raw = path.read_bytes()
        h.update(rel.encode("utf-8")); h.update(b"\0")
        h.update(hashlib.sha256(raw).digest()); h.update(b"\0")
    return h.hexdigest()


def _write_json(path: Path, obj: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = _json_bytes(obj)
    path.write_bytes(raw)
    return _sha256_bytes(raw)


def _write_npy(path: Path, value: Any) -> str:
    arr = np.asarray(value)
    if arr.dtype.hasobject:
        raise SystemExit(f"STOP: object dtype forbidden in authority array {path.name}")
    arr = np.ascontiguousarray(arr)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        np.save(f, arr, allow_pickle=False)
    return _sha256_file(path)


def _record_array(outputs: dict[str, str], world_dir: Path, rel: str, value: Any) -> None:
    safe = _safe_rel(rel)
    outputs[_portable_rel(safe)] = _write_npy(world_dir / safe, value)


def _write_world_bundle(*, root: Path, payload: dict, design: dict[str, np.ndarray], bundle: dict,
                        out_dir: Path, mode: str, bundle_sha: str) -> dict:
    name = str(bundle["world"])
    wi = int(bundle["world_index"])
    world_dir = Path(out_dir) / name
    if world_dir.exists():
        raise SystemExit(f"STOP: world output already exists: {world_dir}")
    world_dir.mkdir(parents=True, exist_ok=False)
    outputs: dict[str, str] = {}

    for key in ("src", "donor", "cls", "op", "log_lib"):
        _record_array(outputs, world_dir, f"design/{key}.npy", design[key])
    _record_array(outputs, world_dir, "support.npy", bundle["support"])

    for part in ("detection", "positive"):
        for key, value in sorted(bundle["truth"][part].items()):
            _record_array(outputs, world_dir, f"truth/{part}/{key}.npy", value)

    for part in ("detection", "positive"):
        for key in ("donor_raw_centered", "donor_effects", "factor_loading"):
            _record_array(outputs, world_dir, f"truth/new_donor/{part}/{key}.npy",
                          bundle["new_donor_truth"][part][key])

    offsets = bundle.get("operator_offsets")
    if offsets is not None:
        for part in ("detection", "positive"):
            _record_array(outputs, world_dir, f"truth/operator_offsets/{part}.npy", offsets[part])

    for rep in ("train", "same_donor", "new_donor"):
        obs = bundle["observations"][rep]
        _record_array(outputs, world_dir, f"observations/{rep}/observed.npy", obs["observed"])
        _record_array(outputs, world_dir, f"observations/{rep}/detected.npy", obs["detected"])

    truth_for_hash = {
        "detection": bundle["truth"]["detection"],
        "positive": bundle["truth"]["positive"],
        "new_donor_truth": bundle["new_donor_truth"],
        "support": bundle["support"],
        "operator_offsets": offsets,
    }
    record = {
        "schema": "V79_V2_CORE_WORLD_RECORD_V1",
        "world_name": name,
        "world_index": wi,
        "seed_parent_world_index": int(bundle["seed_parent_world_index"]),
        "seed_root": int(payload["seeds"]["root"]),
        "mode": mode,
        "design_sha256": bundle["design_sha256"],
        "scientific_truth_sha256": G.scientific_truth_sha(truth_for_hash),
        "final_contract_sha256": G.FINAL_CONTRACT_SHA256,
        "pairing_amendment_sha256": G.PAIRING_AMENDMENT_SHA256,
        "generator_bundle_sha256": bundle_sha,
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "training_authorized": False,
    }
    outputs["world_record.json"] = _write_json(world_dir / "world_record.json", record)

    manifest = G.build_manifest(
        world_name=name, world_index=wi, truth=truth_for_hash,
        final_contract_sha=G.FINAL_CONTRACT_SHA256,
        payload_sha=G.QUALIFICATION_PAYLOAD_SHA256,
        generated_files=outputs,
    )
    manifest.update({
        "mode": mode,
        "seed_root": int(payload["seeds"]["root"]),
        "generator_bundle_sha256": bundle_sha,
    })
    manifest_sha = _write_json(world_dir / "manifest.json", manifest)
    return {
        "world_name": name,
        "world_index": wi,
        "relative_dir": name,
        "manifest_path": f"{name}/manifest.json",
        "manifest_sha256": manifest_sha,
    }


def _ensure_empty_destination(out_dir: Path) -> None:
    out_dir = Path(out_dir)
    if out_dir.exists():
        try:
            next(out_dir.iterdir())
        except StopIteration:
            return
        raise SystemExit(f"STOP: world-set destination is not empty: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)


def _write_world_set(*, root: Path, payload: dict, cal: dict, designs: dict[str, dict[str, np.ndarray]],
                     amendment: dict, out_dir: Path, mode: str,
                     authorization: dict | None = None) -> dict:
    root = Path(root)
    out_dir = Path(out_dir)
    _ensure_empty_destination(out_dir)
    bundle_sha = generator_bundle_sha256(root)
    worlds: list[dict] = []
    for world_def in payload["worlds"]["world_list"]:
        bundle = A.assemble_world_in_memory(payload, cal, designs, world_def, amendment)
        worlds.append(_write_world_bundle(
            root=root, payload=payload, design=designs[str(world_def["name"])], bundle=bundle,
            out_dir=out_dir, mode=mode, bundle_sha=bundle_sha))
    worlds.sort(key=lambda r: r["world_index"])

    root_manifest: dict[str, Any] = {
        "schema": "V79_V2_CORE_WORLD_SET_MANIFEST_V1",
        "mode": mode,
        "seed_root": int(payload["seeds"]["root"]),
        "world_count": len(worlds),
        "worlds": worlds,
        "final_contract_sha256": G.FINAL_CONTRACT_SHA256,
        "qualification_payload_sha256": G.QUALIFICATION_PAYLOAD_SHA256,
        "pairing_amendment_sha256": G.PAIRING_AMENDMENT_SHA256,
        "generator_bundle_sha256": bundle_sha,
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "training_authorized": False,
    }
    if authorization is not None:
        auth_raw = _json_bytes(authorization)
        (out_dir / "realization_authorization.json").write_bytes(auth_raw)
        root_manifest["realization_authorization_sha256"] = _sha256_bytes(auth_raw)
        root_manifest["execution_platform"] = authorization["execution_platform"]
        root_manifest["environment_lock_sha256"] = authorization["environment_lock_sha256"]
    _write_json(out_dir / ROOT_MANIFEST_NAME, root_manifest)
    verified = verify_world_set(out_dir)
    if verified != root_manifest:
        raise SystemExit("STOP: post-write verification did not reproduce root manifest")
    return root_manifest


def write_engineering_world_set(*, root: Path, payload: dict, cal: dict,
                                designs: dict[str, dict[str, np.ndarray]], amendment: dict,
                                out_dir: Path) -> dict:
    if int(payload["seeds"]["root"]) == QUALIFICATION_SEED_ROOT:
        raise SystemExit("STOP: engineering writer refuses the frozen qualification seed")
    return _write_world_set(
        root=root, payload=payload, cal=cal, designs=designs, amendment=amendment,
        out_dir=out_dir, mode="ENGINEERING_TEST_ONLY")


def validate_qualification_authorization(authorization: dict | None, *, root: Path,
                                         runtime_platform: str | None = None) -> dict:
    auth = G.validate_realization_authorization(authorization)
    actual_bundle = generator_bundle_sha256(root)
    if auth.get("generator_bundle_sha256") != actual_bundle:
        raise SystemExit("STOP: realization authorization does not bind the executing generator bundle")
    if auth.get("environment_lock_sha256") != ENV_LOCK_SHA256:
        raise SystemExit("STOP: realization authorization does not bind the frozen environment lock")
    if auth.get("execution_platform") != WINDOWS_EXECUTION_PLATFORM:
        raise SystemExit("STOP: realization authorization does not bind the locked Windows qualification environment")
    host = str(runtime_platform if runtime_platform is not None else platform.system())
    if host.lower() != "windows":
        raise SystemExit(f"STOP: qualification world realization is Windows-only for this frozen generation; host={host}")
    return auth


def realize_qualification_worlds(*, root: Path, payload: dict, cal: dict,
                                 designs: dict[str, dict[str, np.ndarray]], amendment: dict,
                                 out_dir: Path, authorization: dict | None) -> dict:
    if int(payload["seeds"]["root"]) != QUALIFICATION_SEED_ROOT:
        raise SystemExit("STOP: qualification realization requires the frozen qualification seed")
    auth = validate_qualification_authorization(authorization, root=root)
    return _write_world_set(
        root=root, payload=payload, cal=cal, designs=designs, amendment=amendment,
        out_dir=out_dir, mode="QUALIFICATION_TRUTH_FREEZE", authorization=auth)


def verify_world_set(out_dir: Path) -> dict:
    out_dir = Path(out_dir)
    root_path = out_dir / ROOT_MANIFEST_NAME
    if not root_path.is_file():
        raise SystemExit("STOP: root world-set manifest missing")
    root_manifest = json.loads(root_path.read_text(encoding="utf-8"))
    if root_manifest.get("schema") != "V79_V2_CORE_WORLD_SET_MANIFEST_V1":
        raise SystemExit("STOP: wrong world-set manifest schema")
    if root_manifest.get("final_contract_sha256") != G.FINAL_CONTRACT_SHA256:
        raise SystemExit("STOP: world set binds the wrong final contract")
    if root_manifest.get("pairing_amendment_sha256") != G.PAIRING_AMENDMENT_SHA256:
        raise SystemExit("STOP: world set binds the wrong pairing amendment")
    if root_manifest.get("qualification_fits_run") != 0 or root_manifest.get("benchmark_run") is not False:
        raise SystemExit("STOP: world set claims benchmark or qualification fitting")

    expected_files = {ROOT_MANIFEST_NAME}
    if "realization_authorization_sha256" in root_manifest:
        ap = out_dir / "realization_authorization.json"
        if not ap.is_file() or _sha256_file(ap) != root_manifest["realization_authorization_sha256"]:
            raise SystemExit("STOP: realization authorization file/hash mismatch")
        expected_files.add("realization_authorization.json")
        auth = json.loads(ap.read_text(encoding="utf-8"))
        if root_manifest.get("execution_platform") != auth.get("execution_platform") or \
                root_manifest.get("environment_lock_sha256") != auth.get("environment_lock_sha256"):
            raise SystemExit("STOP: root manifest authorization provenance mismatch")

    worlds = root_manifest.get("worlds")
    if not isinstance(worlds, list) or len(worlds) != int(root_manifest.get("world_count", -1)):
        raise SystemExit("STOP: world-set count/list mismatch")
    for rec in worlds:
        safe_manifest = _safe_rel(rec["manifest_path"])
        mrel = _portable_rel(safe_manifest)
        mp = out_dir / safe_manifest
        if not mp.is_file() or _sha256_file(mp) != rec["manifest_sha256"]:
            raise SystemExit(f"STOP: world manifest hash mismatch: {mrel}")
        expected_files.add(mrel)
        wm = json.loads(mp.read_text(encoding="utf-8"))
        if wm.get("world_name") != rec["world_name"] or int(wm.get("world_index", -1)) != int(rec["world_index"]):
            raise SystemExit("STOP: root/world manifest identity mismatch")
        if wm.get("generator_bundle_sha256") != root_manifest.get("generator_bundle_sha256"):
            raise SystemExit("STOP: generator bundle mismatch within world set")
        world_dir = mp.parent
        outputs = wm.get("generated_outputs")
        if not isinstance(outputs, dict) or not outputs:
            raise SystemExit("STOP: world generated-output ledger missing")
        for rel, digest in outputs.items():
            safe = _safe_rel(str(rel))
            fp = world_dir / safe
            if not fp.is_file() or _sha256_file(fp) != digest:
                raise SystemExit(f"STOP: world file hash mismatch: {wm['world_name']}/{rel}")
            expected_files.add(_portable_rel(Path(rec["relative_dir"]) / safe))

    actual_files = {
        _portable_rel(p.relative_to(out_dir))
        for p in out_dir.rglob("*") if p.is_file()
    }
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files)
        extra = sorted(actual_files - expected_files)
        raise SystemExit(f"STOP: world-set file ledger mismatch; missing={missing}, extra={extra}")
    return root_manifest


def directory_digest(out_dir: Path) -> str:
    out_dir = Path(out_dir)
    h = hashlib.sha256()
    for p in sorted((p for p in out_dir.rglob("*") if p.is_file()),
                    key=lambda x: _portable_rel(x.relative_to(out_dir))):
        rel = _portable_rel(p.relative_to(out_dir))
        h.update(rel.encode("utf-8")); h.update(b"\0")
        h.update(hashlib.sha256(p.read_bytes()).digest()); h.update(b"\0")
    return h.hexdigest()
