#!/usr/bin/env python3
"""Controller-side preparation of physically isolated V79 qualification fit custody.

No fitting occurs here. The controller may read the frozen realized root manifest to
reproduce scientific-identity keyed seeds, but only opaque fit-id -> seed records,
blinded_fit_inputs, a sanitized fit-contract view and a sanitized execution
authorization are copied into the fit custody directory.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import v79_v2_core_fit_contract as FC
import v79_v2_core_fit_surface as F
import v79_v2_core_launch as L
import v79_v2_core_qualification_custody as C
import v79_v2_core_seed_ledger as S

FIT_VIEW_NAME = "V79_V2_CORE_FIT_CONTRACT_VIEW_V1.json"
AUTH_NAME = "V79_V2_CORE_QUALIFICATION_EXECUTION_AUTHORIZATION_V1.json"
RECEIPT_NAME = "V79_V2_CORE_QUALIFICATION_CUSTODY_V1.json"
RECEIPT_SCHEMA = "V79_V2_CORE_QUALIFICATION_CUSTODY_V1"


class QualificationPrepRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise QualificationPrepRefused(f"REFUSED V2_CORE qualification prep: {msg}")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canon(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _write_once(path: Path, raw: bytes) -> str:
    if path.exists(): _refuse(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def _git_head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _require_clean(root: Path) -> None:
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip():
        _refuse("repository working tree is not clean")


def build_fit_contract_view(contract: dict) -> dict:
    streams = contract["seeds"]["gene_streams"]
    resource_keys = ("environment", "concurrency", "settle_seconds_between_worlds", "xla_host_devices",
                     "checkpoint", "compact_outputs", "engineering_benchmark")
    view = {
        "schema": FC.SCHEMA,
        "source_contract_sha256": FC.SOURCE_CONTRACT_SHA256,
        "model": copy.deepcopy(contract["model"]),
        "parameterization": copy.deepcopy(contract["parameterization"]),
        "priors": copy.deepcopy(contract["priors"]),
        "inference": copy.deepcopy(contract["inference"]),
        "resources": {**{k: copy.deepcopy(contract["resources"][k]) for k in resource_keys},
                      "estimate": {"n_fits": contract["resources"]["estimate"]["n_fits"]},
                      "qualification_world_count": len(contract["worlds"]["world_list"])},
        "seeds": {"engineering_benchmark_root": contract["seeds"]["engineering_benchmark_root"],
                  "gene_streams": {k: streams[k] for k in ("fit_det_primary", "fit_det_escalation",
                                                             "fit_pos_primary", "fit_pos_escalation")}},
        "result_schemas": {"fit_record": contract["result_schemas"]["fit_record"]},
    }
    FC.validate_fit_contract_view(view); return view


def _compact_donor_draw_count(contract: dict) -> int:
    text=str(contract["resources"]["compact_outputs"])
    m=re.search(r"float32\s+npz\s+of\s+(\d+)\s+thinned\s+donor-effect\s+draws",text)
    if not m: _refuse("cannot parse frozen compact donor-draw count")
    return int(m.group(1))


def _digest(base: Path) -> str:
    h=hashlib.sha256(); base=Path(base)
    for p in sorted((p for p in base.rglob("*") if p.is_file()), key=lambda x:x.relative_to(base).as_posix()):
        rel=p.relative_to(base).as_posix(); h.update(rel.encode()); h.update(b"\0"); h.update(hashlib.sha256(p.read_bytes()).digest()); h.update(b"\0")
    return h.hexdigest()


def prepare(root: Path, package_dir: Path, authorization_path: Path, custody_dir: Path) -> dict:
    root=Path(root); package_dir=Path(package_dir); authorization_path=Path(authorization_path); custody_dir=Path(custody_dir)
    _require_clean(root)
    if custody_dir.exists(): _refuse("custody destination already exists")
    contract_path=root/"results/v79/v2_core_qualification"/L.FINAL_CONTRACT_NAME
    contract=L.require_launch_authority(contract_path, root=root)
    if _sha(contract_path)!=FC.SOURCE_CONTRACT_SHA256: _refuse("contract bytes differ")
    index=F.load_blinded_index(package_dir, expected_mode="QUALIFICATION_TRUTH_FREEZE",
        expected_root_manifest_sha=F.QUALIFICATION_ROOT_MANIFEST_SHA256,
        expected_index_sha=F.QUALIFICATION_INDEX_SHA256)
    root_manifest=json.loads((package_dir/F.ROOT_MANIFEST_NAME).read_text(encoding="utf-8"))
    ledger=S.build_seed_ledger(contract, root_manifest, index.index)
    try: auth=json.loads(authorization_path.read_text(encoding="utf-8"))
    except Exception as exc: _refuse(f"unreadable authorization: {exc}")
    sanitized=C.sanitize_execution_authorization(auth, expected_seed_ledger=ledger)
    fit_view=build_fit_contract_view(contract)

    custody_dir.mkdir(parents=True, exist_ok=False)
    src=package_dir/F.FIT_ROOT_NAME; dst=custody_dir/F.FIT_ROOT_NAME
    shutil.copytree(src,dst,copy_function=shutil.copyfile)
    if _digest(src)!=_digest(dst): _refuse("blinded custody copy digest mismatch")
    fit_view_sha=_write_once(custody_dir/FIT_VIEW_NAME, FC.canonical_bytes(fit_view))
    auth_sha=_write_once(custody_dir/AUTH_NAME, _canon(sanitized))
    receipt={"schema":RECEIPT_SCHEMA,"executor_code_head":_git_head(root),
             "source_contract_sha256":FC.SOURCE_CONTRACT_SHA256,
             "root_manifest_sha256":F.QUALIFICATION_ROOT_MANIFEST_SHA256,
             "blinded_index_sha256":F.QUALIFICATION_INDEX_SHA256,
             "blinded_directory_digest":_digest(dst),
             "fit_contract_view_path":FIT_VIEW_NAME,"fit_contract_view_sha256":fit_view_sha,
             "authorization_path":AUTH_NAME,"authorization_sha256":auth_sha,
             "fit_count":C.EXPECTED_FITS,"ppc_draws":int(contract["ppc"]["draws"]),
             "donor_draws_stored":_compact_donor_draw_count(contract),
             "qualification_fits_run":0,"scoring_run":False,
             "truth_accessed":False,"training_authorized":False}
    receipt_sha=_write_once(custody_dir/RECEIPT_NAME,_canon(receipt))
    receipt["custody_receipt_sha256"]=receipt_sha
    if (custody_dir/F.ROOT_MANIFEST_NAME).exists() or (custody_dir/"controller_truth").exists():
        _refuse("controller root/truth leaked into qualification custody")
    return receipt


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("root"); p.add_argument("package_dir"); p.add_argument("authorization_path"); p.add_argument("custody_dir")
    a=p.parse_args(argv); print(json.dumps(prepare(Path(a.root),Path(a.package_dir),Path(a.authorization_path),Path(a.custody_dir)),indent=2))

if __name__=="__main__": main()
