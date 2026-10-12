#!/usr/bin/env python3
"""Fit-side custody loader for physically separated V79 blinded benchmark inputs."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import v79_v2_core_fit_contract as FC
import v79_v2_core_fit_runner as R
import v79_v2_core_fit_surface as F

PREP_SCHEMA = "V79_V2_CORE_ENGINEERING_BENCHMARK_PREP_V1"
PREP_RECEIPT_NAME = "V79_V2_CORE_ENGINEERING_BENCHMARK_PREP_V1.json"
FIT_VIEW_NAME = "V79_V2_CORE_FIT_CONTRACT_VIEW_V1.json"
FIT_ROOT_NAME = "blinded_fit_inputs"
PREP_KEYS = {
    "schema", "executor_code_head", "source_contract_sha256", "fit_contract_view_path",
    "fit_contract_view_sha256", "execution_mode", "engineering_seed_root", "root_manifest_sha256",
    "blinded_index_sha256", "blinded_directory_digest", "selected_opaque_world_id",
    "selected_world_manifest_sha256", "fit_seed_ledger", "benchmark_fit_count", "benchmark_run",
    "qualification_fits_run", "scoring_run", "fit_truth_accessed", "training_authorized",
}
INDEX_KEYS = {"schema", "final_contract_sha256", "pairing_amendment_sha256", "generator_bundle_sha256",
              "world_count", "worlds", "benchmark_run", "qualification_fits_run", "training_authorized"}
WORLD_REC_KEYS = {"opaque_world_id", "manifest_path", "manifest_sha256"}


class FitCustodyRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise FitCustodyRefused(f"REFUSED V2_CORE fit custody: {msg}")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canonical(obj: Mapping) -> bytes:
    return (json.dumps(dict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _contains_controller_identity(obj) -> bool:
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            if str(k).lower() in {"world_name", "world_index", "q_label", "truth", "controller_truth", "operator", "matrix"}:
                return True
            if _contains_controller_identity(v):
                return True
    elif isinstance(obj, list):
        return any(_contains_controller_identity(x) for x in obj)
    elif isinstance(obj, str) and re.search(r"\bQ(?:0[0-9]|1[01])(?:_|\b)", obj):
        return True
    return False


def _blinded_digest(fit_root: Path) -> str:
    fit_root = Path(fit_root); h = hashlib.sha256()
    for p in sorted((p for p in fit_root.rglob("*") if p.is_file()), key=lambda x: x.relative_to(fit_root).as_posix()):
        rel = p.relative_to(fit_root).as_posix()
        h.update(rel.encode("utf-8")); h.update(b"\0"); h.update(hashlib.sha256(p.read_bytes()).digest()); h.update(b"\0")
    return h.hexdigest()


@dataclass(frozen=True)
class EngineeringCustody:
    custody_dir: Path
    receipt_sha256: str
    receipt: Mapping
    fit_contract: Mapping
    blinded_index: F.BlindedIndex
    selected_opaque_world_id: str
    selected_world_manifest_sha256: str
    seed_by_fit_id: Mapping[str, int]


def load_engineering_custody(custody_dir: Path, *, expected_prep_receipt_sha256: str) -> EngineeringCustody:
    custody_dir = Path(custody_dir)
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected_prep_receipt_sha256)):
        _refuse("64-hex prep receipt SHA-256 is required")
    if not custody_dir.is_dir():
        _refuse("custody directory missing")
    top = {p.name for p in custody_dir.iterdir()}; expected_top = {PREP_RECEIPT_NAME, FIT_VIEW_NAME, FIT_ROOT_NAME}
    if top != expected_top:
        _refuse(f"custody top-level set differs; extra={sorted(top-expected_top)}, missing={sorted(expected_top-top)}")
    receipt_path = custody_dir / PREP_RECEIPT_NAME; raw = receipt_path.read_bytes(); actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_prep_receipt_sha256:
        _refuse(f"prep receipt hash mismatch: {actual} != {expected_prep_receipt_sha256}")
    try:
        receipt = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        _refuse(f"invalid prep receipt JSON: {exc}")
    if _canonical(receipt) != raw:
        _refuse("prep receipt bytes are not canonical")
    if set(receipt) != PREP_KEYS:
        _refuse(f"prep receipt key set differs; extra={sorted(set(receipt)-PREP_KEYS)}, missing={sorted(PREP_KEYS-set(receipt))}")
    if _contains_controller_identity(receipt):
        _refuse("prep receipt leaks controller identity/truth")
    if receipt.get("schema") != PREP_SCHEMA or receipt.get("execution_mode") != "ENGINEERING_BENCHMARK":
        _refuse("wrong prep receipt schema/mode")
    if not re.fullmatch(r"[0-9a-f]{40}", str(receipt.get("executor_code_head", ""))):
        _refuse("invalid executor code head")
    for key, value in (("benchmark_run", False), ("qualification_fits_run", 0), ("scoring_run", False),
                       ("fit_truth_accessed", False), ("training_authorized", False)):
        if receipt.get(key) != value:
            _refuse(f"prep receipt boundary changed: {key}={receipt.get(key)!r}")
    if receipt.get("benchmark_fit_count") != 4 or receipt.get("source_contract_sha256") != FC.SOURCE_CONTRACT_SHA256:
        _refuse("prep receipt scope/source contract differs")

    fit_view_path = custody_dir / FIT_VIEW_NAME
    if receipt.get("fit_contract_view_path") != FIT_VIEW_NAME:
        _refuse("fit-contract path differs")
    fit_contract = FC.load_fit_contract_view(fit_view_path, expected_sha256=str(receipt.get("fit_contract_view_sha256", "")))

    fit_root = custody_dir / FIT_ROOT_NAME; index_path = fit_root / F.FIT_INDEX_NAME
    if not index_path.is_file() or _sha(index_path) != receipt.get("blinded_index_sha256"):
        _refuse("blinded index missing/hash mismatch")
    if _blinded_digest(fit_root) != receipt.get("blinded_directory_digest"):
        _refuse("blinded directory digest mismatch")
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as exc:
        _refuse(f"invalid blinded index JSON: {exc}")
    if set(index) != INDEX_KEYS or _contains_controller_identity(index):
        _refuse("blinded index key set or identity firewall differs")
    if index.get("schema") != "V79_V2_CORE_BLINDED_FIT_INDEX_V1" or index.get("final_contract_sha256") != FC.SOURCE_CONTRACT_SHA256:
        _refuse("blinded index schema/contract mismatch")
    if index.get("benchmark_run") is not False or index.get("qualification_fits_run") != 0 or index.get("training_authorized") is not False:
        _refuse("blinded index already records downstream execution")
    worlds = index.get("worlds")
    if not isinstance(worlds, list) or int(index.get("world_count", -1)) != len(worlds):
        _refuse("blinded index world count mismatch")
    ids = []
    for rec in worlds:
        if not isinstance(rec, Mapping) or set(rec) != WORLD_REC_KEYS:
            _refuse("blinded world record key set differs")
        oid = str(rec.get("opaque_world_id", ""))
        if not re.fullmatch(r"[0-9a-f]{12}", oid) or rec.get("manifest_path") != f"{oid}/manifest.json":
            _refuse("invalid opaque world record")
        if not re.fullmatch(r"[0-9a-f]{64}", str(rec.get("manifest_sha256", ""))):
            _refuse("invalid world manifest hash")
        ids.append(oid)
    if len(set(ids)) != len(ids):
        _refuse("duplicate opaque world ID")
    oid = str(receipt.get("selected_opaque_world_id", ""))
    if oid not in ids:
        _refuse("selected opaque world is absent from blinded index")
    selected = next(x for x in worlds if x["opaque_world_id"] == oid); msha = str(receipt.get("selected_world_manifest_sha256", ""))
    if selected.get("manifest_sha256") != msha:
        _refuse("selected world manifest binding mismatch")

    ledger = receipt.get("fit_seed_ledger")
    if not isinstance(ledger, list) or len(ledger) != 4:
        _refuse("engineering fit seed ledger must contain exactly four records")
    expected_ids = {R.fit_identity(oid, msha, part, g) for g in (0, 1) for part in ("detection", "positive")}
    seed_by_fit_id: dict[str, int] = {}
    for rec in ledger:
        if not isinstance(rec, Mapping) or set(rec) != {"fit_id", "primary_seed"}:
            _refuse("benchmark seed-ledger key set differs")
        fid = str(rec.get("fit_id", "")); seed = rec.get("primary_seed")
        if fid in seed_by_fit_id or fid not in expected_ids or not isinstance(seed, int) or not (0 <= seed <= 0xffffffff):
            _refuse("invalid/duplicate benchmark seed-ledger entry")
        seed_by_fit_id[fid] = int(seed)
    if set(seed_by_fit_id) != expected_ids:
        _refuse("benchmark seed ledger does not cover exact four fit IDs")

    blinded_index = F.BlindedIndex(fit_root=fit_root, execution_mode="ENGINEERING_BENCHMARK",
        root_manifest_sha256=str(receipt.get("root_manifest_sha256", "")), index_sha256=str(receipt.get("blinded_index_sha256", "")),
        index=index, opaque_world_ids=tuple(ids))
    return EngineeringCustody(custody_dir, actual, receipt, fit_contract, blinded_index, oid, msha, seed_by_fit_id)
