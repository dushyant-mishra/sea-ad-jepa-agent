#!/usr/bin/env python3
"""Deterministic, blinded physical package writer for V79 V2_CORE worlds.

Engineering writes are barred from the frozen qualification seed. Qualification
realization reloads all scientific inputs from authenticated repository bytes and
requires controller authorization bound to the exact generator bundle, frozen
environment lock and locked Windows qualification environment.

The physical package has two separate surfaces:
- ``blinded_fit_inputs``: opaque world IDs, permitted model covariates, support and
  observations only. No truth, Q-label, seed root or operator/matrix identity.
- ``controller_truth``: planted truth and the Q-label<->opaque mapping, inaccessible
  to the fitting stage until scoring.

This module never benchmarks or fits a model.
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
FIT_ROOT_NAME = "blinded_fit_inputs"
TRUTH_ROOT_NAME = "controller_truth"
FIT_INDEX_NAME = "V79_V2_CORE_BLINDED_FIT_INDEX_V1.json"
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


def _record_array(outputs: dict[str, str], base_dir: Path, rel: str, value: Any) -> None:
    safe = _safe_rel(rel)
    outputs[_portable_rel(safe)] = _write_npy(base_dir / safe, value)


def _truth_for_hash(bundle: dict) -> dict:
    return {
        "detection": bundle["truth"]["detection"],
        "positive": bundle["truth"]["positive"],
        "new_donor_truth": bundle["new_donor_truth"],
        "support": bundle["support"],
        "operator_offsets": bundle.get("operator_offsets"),
    }


def _write_blinded_fit_bundle(*, out_dir: Path, design: dict[str, np.ndarray], bundle: dict,
                              bundle_sha: str) -> dict:
    opaque = G.opaque_world_id(str(bundle["world"]))
    fit_dir = Path(out_dir) / FIT_ROOT_NAME / opaque
    if fit_dir.exists():
        raise SystemExit(f"STOP: blinded fit output already exists: {fit_dir}")
    fit_dir.mkdir(parents=True, exist_ok=False)
    outputs: dict[str, str] = {}

    # Only covariates in frozen V2_CORE. Operator/matrix identity is deliberately absent.
    for key in ("src", "donor", "cls", "log_lib"):
        _record_array(outputs, fit_dir, f"design/{key}.npy", design[key])
    _record_array(outputs, fit_dir, "support.npy", bundle["support"])
    for rep in ("train", "same_donor", "new_donor"):
        obs = bundle["observations"][rep]
        _record_array(outputs, fit_dir, f"observations/{rep}/observed.npy", obs["observed"])
        _record_array(outputs, fit_dir, f"observations/{rep}/detected.npy", obs["detected"])

    manifest = {
        "schema": "V79_V2_CORE_BLINDED_WORLD_DATA_MANIFEST_V1",
        "opaque_world_id": opaque,
        "final_contract_sha256": G.FINAL_CONTRACT_SHA256,
        "pairing_amendment_sha256": G.PAIRING_AMENDMENT_SHA256,
        "generator_bundle_sha256": bundle_sha,
        "generated_outputs": dict(sorted(outputs.items())),
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "training_authorized": False,
    }
    manifest_sha = _write_json(fit_dir / "manifest.json", manifest)
    return {
        "opaque_world_id": opaque,
        "manifest_path": f"{FIT_ROOT_NAME}/{opaque}/manifest.json",
        "manifest_sha256": manifest_sha,
    }


def _write_controller_truth_bundle(*, out_dir: Path, design: dict[str, np.ndarray], bundle: dict,
                                   payload: dict, mode: str, bundle_sha: str,
                                   fit_manifest_sha: str) -> dict:
    name = str(bundle["world"])
    wi = int(bundle["world_index"])
    opaque = G.opaque_world_id(name)
    truth_dir = Path(out_dir) / TRUTH_ROOT_NAME / opaque
    if truth_dir.exists():
        raise SystemExit(f"STOP: controller truth output already exists: {truth_dir}")
    truth_dir.mkdir(parents=True, exist_ok=False)
    outputs: dict[str, str] = {}

    # Controller/scoring-only design details. Operator is hidden from the fitter.
    _record_array(outputs, truth_dir, "design/op.npy", design["op"])
    _record_array(outputs, truth_dir, "support.npy", bundle["support"])
    for part in ("detection", "positive"):
        for key, value in sorted(bundle["truth"][part].items()):
            _record_array(outputs, truth_dir, f"truth/{part}/{key}.npy", value)
    for part in ("detection", "positive"):
        for key in ("donor_raw_centered", "donor_effects", "factor_loading"):
            _record_array(outputs, truth_dir, f"truth/new_donor/{part}/{key}.npy",
                          bundle["new_donor_truth"][part][key])
    offsets = bundle.get("operator_offsets")
    if offsets is not None:
        for part in ("detection", "positive"):
            _record_array(outputs, truth_dir, f"truth/operator_offsets/{part}.npy", offsets[part])

    truth_obj = _truth_for_hash(bundle)
    manifest = {
        "schema": "V79_V2_CORE_CONTROLLER_TRUTH_MANIFEST_V1",
        "world_name": name,
        "world_index": wi,
        "opaque_world_id": opaque,
        "seed_parent_world_index": int(bundle["seed_parent_world_index"]),
        "seed_root": int(payload["seeds"]["root"]),
        "mode": mode,
        "design_sha256": bundle["design_sha256"],
        "scientific_truth_sha256": G.scientific_truth_sha(truth_obj),
        "blinded_fit_manifest_sha256": fit_manifest_sha,
        "final_contract_sha256": G.FINAL_CONTRACT_SHA256,
        "qualification_payload_sha256": G.QUALIFICATION_PAYLOAD_SHA256,
        "pairing_amendment_sha256": G.PAIRING_AMENDMENT_SHA256,
        "generator_bundle_sha256": bundle_sha,
        "generated_outputs": dict(sorted(outputs.items())),
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "training_authorized": False,
    }
    manifest_sha = _write_json(truth_dir / "manifest.json", manifest)
    return {
        "world_name": name,
        "world_index": wi,
        "opaque_world_id": opaque,
        "fit_manifest_path": f"{FIT_ROOT_NAME}/{opaque}/manifest.json",
        "fit_manifest_sha256": fit_manifest_sha,
        "truth_manifest_path": f"{TRUTH_ROOT_NAME}/{opaque}/manifest.json",
        "truth_manifest_sha256": manifest_sha,
        "scientific_truth_sha256": manifest["scientific_truth_sha256"],
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
    authority_worlds: list[dict] = []
    fit_index_worlds: list[dict] = []

    for world_def in payload["worlds"]["world_list"]:
        name = str(world_def["name"])
        bundle = A.assemble_world_in_memory(payload, cal, designs, world_def, amendment)
        fit_rec = _write_blinded_fit_bundle(out_dir=out_dir, design=designs[name], bundle=bundle,
                                            bundle_sha=bundle_sha)
        truth_rec = _write_controller_truth_bundle(
            out_dir=out_dir, design=designs[name], bundle=bundle, payload=payload, mode=mode,
            bundle_sha=bundle_sha, fit_manifest_sha=fit_rec["manifest_sha256"])
        authority_worlds.append(truth_rec)
        fit_index_worlds.append({
            "opaque_world_id": fit_rec["opaque_world_id"],
            "manifest_path": f"{fit_rec['opaque_world_id']}/manifest.json",
            "manifest_sha256": fit_rec["manifest_sha256"],
        })

    authority_worlds.sort(key=lambda r: r["world_index"])
    fit_index_worlds.sort(key=lambda r: r["opaque_world_id"])
    fit_index = {
        "schema": "V79_V2_CORE_BLINDED_FIT_INDEX_V1",
        "final_contract_sha256": G.FINAL_CONTRACT_SHA256,
        "pairing_amendment_sha256": G.PAIRING_AMENDMENT_SHA256,
        "generator_bundle_sha256": bundle_sha,
        "world_count": len(fit_index_worlds),
        "worlds": fit_index_worlds,
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "training_authorized": False,
    }
    fit_index_rel = f"{FIT_ROOT_NAME}/{FIT_INDEX_NAME}"
    fit_index_sha = _write_json(out_dir / fit_index_rel, fit_index)

    root_manifest: dict[str, Any] = {
        "schema": "V79_V2_CORE_WORLD_SET_MANIFEST_V1",
        "mode": mode,
        "seed_root": int(payload["seeds"]["root"]),
        "world_count": len(authority_worlds),
        "worlds": authority_worlds,
        "blinded_fit_root": FIT_ROOT_NAME,
        "blinded_fit_index_path": fit_index_rel,
        "blinded_fit_index_sha256": fit_index_sha,
        "controller_truth_root": TRUTH_ROOT_NAME,
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
    return _write_world_set(root=root, payload=payload, cal=cal, designs=designs, amendment=amendment,
                            out_dir=out_dir, mode="ENGINEERING_TEST_ONLY")


def load_frozen_qualification_inputs(root: Path) -> tuple[dict, dict, dict, dict[str, dict[str, np.ndarray]], dict]:
    """Reload every scientific input for the real qualification run from frozen, hash-bound repo bytes."""
    root = Path(root)
    contract, payload = G.load_launch_contract(root)
    if int(payload["seeds"]["root"]) != QUALIFICATION_SEED_ROOT:
        raise SystemExit("STOP: canonical qualification payload has unexpected seed root")
    amendment = G.load_pairing_amendment(root)
    cal_spec = contract["inputs"]["planting_calibration_masked"]
    cal_path = root / cal_spec["path"]
    if not cal_path.is_file() or _sha256_file(cal_path) != cal_spec["sha256"]:
        raise SystemExit("STOP: frozen planting calibration hash mismatch")
    cal = json.loads(cal_path.read_text(encoding="utf-8"))
    designs = G.build_world_designs(root, payload)
    return contract, payload, cal, designs, amendment


def validate_qualification_authorization(authorization: dict | None, *, root: Path,
                                         runtime_platform: str | None = None) -> dict:
    G.load_launch_contract(root)
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


def realize_qualification_worlds(*, root: Path, out_dir: Path, authorization: dict | None) -> dict:
    """Realize Q00-Q11 only from canonical frozen authorities; callers cannot inject scientific inputs."""
    contract, payload, cal, designs, amendment = load_frozen_qualification_inputs(root)
    if contract.get("qualification_worlds_generated") != 0 or contract.get("qualification_fits_run") != 0:
        raise SystemExit("STOP: canonical contract is not in the pre-generation/pre-fit state")
    auth = validate_qualification_authorization(authorization, root=root)
    return _write_world_set(root=root, payload=payload, cal=cal, designs=designs, amendment=amendment,
                            out_dir=out_dir, mode="QUALIFICATION_TRUTH_FREEZE", authorization=auth)


def _verify_output_ledger(base_dir: Path, outputs: dict, expected_files: set[str], root_dir: Path) -> None:
    if not isinstance(outputs, dict) or not outputs:
        raise SystemExit("STOP: generated-output ledger missing")
    for rel, digest in outputs.items():
        safe = _safe_rel(str(rel))
        fp = base_dir / safe
        if not fp.is_file() or _sha256_file(fp) != digest:
            raise SystemExit(f"STOP: package file hash mismatch: {fp}")
        expected_files.add(_portable_rel(fp.relative_to(root_dir)))


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

    fit_index_path = out_dir / _safe_rel(root_manifest["blinded_fit_index_path"])
    if not fit_index_path.is_file() or _sha256_file(fit_index_path) != root_manifest["blinded_fit_index_sha256"]:
        raise SystemExit("STOP: blinded fit index hash mismatch")
    expected_files.add(_portable_rel(fit_index_path.relative_to(out_dir)))
    fit_index = json.loads(fit_index_path.read_text(encoding="utf-8"))
    if fit_index.get("schema") != "V79_V2_CORE_BLINDED_FIT_INDEX_V1":
        raise SystemExit("STOP: wrong blinded fit index schema")
    if fit_index.get("world_count") != root_manifest.get("world_count"):
        raise SystemExit("STOP: blinded fit index world count mismatch")
    # Critical blinding invariant: no Q-labels or truth references in fit index bytes.
    raw_index = fit_index_path.read_text(encoding="utf-8")
    if any(f"Q{i:02d}" in raw_index for i in range(12)) or "truth" in raw_index.lower():
        raise SystemExit("STOP: blinded fit index leaks world identity or truth")

    root_worlds = root_manifest.get("worlds")
    if not isinstance(root_worlds, list) or len(root_worlds) != int(root_manifest.get("world_count", -1)):
        raise SystemExit("STOP: world-set count/list mismatch")
    root_by_opaque = {r["opaque_world_id"]: r for r in root_worlds}
    if len(root_by_opaque) != len(root_worlds):
        raise SystemExit("STOP: duplicate opaque world ID")

    for frec in fit_index.get("worlds", []):
        opaque = frec["opaque_world_id"]
        if opaque not in root_by_opaque:
            raise SystemExit("STOP: blinded fit index contains unknown opaque ID")
        fmp = out_dir / FIT_ROOT_NAME / _safe_rel(frec["manifest_path"])
        if not fmp.is_file() or _sha256_file(fmp) != frec["manifest_sha256"]:
            raise SystemExit("STOP: blinded fit manifest hash mismatch")
        expected_files.add(_portable_rel(fmp.relative_to(out_dir)))
        fm_raw = fmp.read_text(encoding="utf-8")
        fm = json.loads(fm_raw)
        if fm.get("schema") != "V79_V2_CORE_BLINDED_WORLD_DATA_MANIFEST_V1" or fm.get("opaque_world_id") != opaque:
            raise SystemExit("STOP: invalid blinded world-data manifest")
        if any(x in fm_raw for x in ("world_name", "world_index", "seed_root", "op.npy")) or "truth" in fm_raw.lower():
            raise SystemExit("STOP: blinded world-data manifest leaks forbidden identity/truth/operator information")
        if "design/op.npy" in fm.get("generated_outputs", {}):
            raise SystemExit("STOP: operator identity leaked into blinded fit inputs")
        _verify_output_ledger(fmp.parent, fm["generated_outputs"], expected_files, out_dir)
        root_rec = root_by_opaque[opaque]
        if root_rec["fit_manifest_sha256"] != frec["manifest_sha256"]:
            raise SystemExit("STOP: controller/blinded fit manifest binding mismatch")

    for rec in root_worlds:
        tmp = out_dir / _safe_rel(rec["truth_manifest_path"])
        if not tmp.is_file() or _sha256_file(tmp) != rec["truth_manifest_sha256"]:
            raise SystemExit("STOP: controller truth manifest hash mismatch")
        expected_files.add(_portable_rel(tmp.relative_to(out_dir)))
        tm = json.loads(tmp.read_text(encoding="utf-8"))
        if tm.get("schema") != "V79_V2_CORE_CONTROLLER_TRUTH_MANIFEST_V1":
            raise SystemExit("STOP: wrong controller truth manifest schema")
        if tm.get("world_name") != rec["world_name"] or int(tm.get("world_index", -1)) != int(rec["world_index"]):
            raise SystemExit("STOP: controller truth identity mismatch")
        if tm.get("opaque_world_id") != rec["opaque_world_id"] or tm.get("scientific_truth_sha256") != rec["scientific_truth_sha256"]:
            raise SystemExit("STOP: controller truth opaque/hash binding mismatch")
        if tm.get("blinded_fit_manifest_sha256") != rec["fit_manifest_sha256"]:
            raise SystemExit("STOP: truth-to-fit manifest binding mismatch")
        _verify_output_ledger(tmp.parent, tm["generated_outputs"], expected_files, out_dir)

    actual_files = {_portable_rel(p.relative_to(out_dir)) for p in out_dir.rglob("*") if p.is_file()}
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files); extra = sorted(actual_files - expected_files)
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
