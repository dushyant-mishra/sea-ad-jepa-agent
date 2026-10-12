#!/usr/bin/env python3
"""Hash-first controller truth loader for V79 V2_CORE qualification scoring.

This module is controller-only. It maps opaque fit identities back to frozen Q-world
truth only after qualification fitting is complete. Every committed truth array is
verified against its immutable per-world manifest before it can be read.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np

from v79_v2_core_fit_contract import SOURCE_CONTRACT_SHA256

TRUTH_SCHEMA="V79_V2_CORE_CONTROLLER_TRUTH_MANIFEST_V1"
MODE="QUALIFICATION_TRUTH_FREEZE"
OPAQUE_RE=re.compile(r"^[0-9a-f]{12}$")


class TruthRefused(RuntimeError): pass

def _refuse(msg:str): raise TruthRefused(f"REFUSED V2_CORE controller truth: {msg}")
def _sha(path:Path)->str: return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _safe(base:Path,rel:str)->Path:
    p=Path(rel)
    if p.is_absolute() or not p.parts or ".." in p.parts: _refuse(f"unsafe truth path {rel!r}")
    q=base/p
    if not q.is_file(): _refuse(f"missing truth file {rel}")
    try: q.resolve(strict=True).relative_to(base.resolve(strict=True))
    except Exception: _refuse(f"truth path escapes root: {rel}")
    return q


def _json(path:Path)->dict:
    try: x=json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: _refuse(f"invalid JSON {path}: {exc}")
    if not isinstance(x,dict): _refuse("truth manifest must be object")
    return x


@dataclass(frozen=True)
class TruthWorld:
    directory: Path
    opaque_world_id: str
    world_index: int
    world_name: str
    manifest: Mapping

    def load(self, rel: str) -> np.ndarray:
        outputs=self.manifest["generated_outputs"]
        if rel not in outputs: _refuse(f"unmanifested truth request {rel}")
        p=_safe(self.directory,rel)
        actual=_sha(p); expected=str(outputs[rel])
        if actual!=expected: _refuse(f"truth hash mismatch {rel}: {actual} != {expected}")
        try:
            with p.open("rb") as f: a=np.load(f,allow_pickle=False)
        except Exception as exc: _refuse(f"unreadable truth array {rel}: {exc}")
        if np.asarray(a).dtype.hasobject: _refuse(f"object dtype forbidden in truth array {rel}")
        return np.asarray(a)


def load_truth_world(directory:Path)->TruthWorld:
    directory=Path(directory)
    if not directory.is_dir(): _refuse(f"truth world directory missing: {directory}")
    oid=directory.name
    if not OPAQUE_RE.fullmatch(oid): _refuse(f"nonopaque truth directory {oid!r}")
    mpath=_safe(directory,"manifest.json"); m=_json(mpath)
    required={"benchmark_run","blinded_fit_manifest_sha256","design_sha256","final_contract_sha256","generated_outputs",
              "generator_bundle_sha256","mode","opaque_world_id","pairing_amendment_sha256","qualification_fits_run",
              "qualification_payload_sha256","schema","scientific_truth_sha256","seed_parent_world_index","seed_root",
              "training_authorized","world_index","world_name"}
    if set(m)!=required: _refuse(f"truth manifest key set differs for {oid}")
    if m.get("schema")!=TRUTH_SCHEMA or m.get("mode")!=MODE or m.get("opaque_world_id")!=oid:
        _refuse(f"truth manifest identity/schema differs for {oid}")
    if m.get("final_contract_sha256")!=SOURCE_CONTRACT_SHA256:
        _refuse(f"truth manifest contract differs for {oid}")
    if m.get("benchmark_run") is not False or m.get("qualification_fits_run")!=0 or m.get("training_authorized") is not False:
        _refuse(f"truth manifest downstream state differs for {oid}")
    wi=m.get("world_index"); wn=m.get("world_name")
    if not isinstance(wi,int) or wi<0 or not isinstance(wn,str) or not re.fullmatch(r"Q(?:0[0-9]|1[01])_[A-Z0-9_]+",wn):
        _refuse(f"invalid controller world identity for {oid}")
    outputs=m.get("generated_outputs")
    if not isinstance(outputs,dict) or not outputs: _refuse(f"empty truth outputs for {oid}")
    for rel,expected in outputs.items():
        if not isinstance(rel,str) or not re.fullmatch(r"[0-9a-f]{64}",str(expected)): _refuse("invalid truth output record")
        if rel=="design/op.npy" or rel=="support.npy" or rel.startswith("truth/"):
            p=_safe(directory,rel)
            if _sha(p)!=expected: _refuse(f"truth hash mismatch {oid}/{rel}")
        else: _refuse(f"unexpected truth output path {rel}")
    physical={p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file() and p.name!="manifest.json"}
    if physical!=set(outputs):
        _refuse(f"truth physical file set differs for {oid}; extra={sorted(physical-set(outputs))}, missing={sorted(set(outputs)-physical)}")
    return TruthWorld(directory,oid,int(wi),wn,m)


def load_truth_set(truth_root:Path, contract:Mapping)->dict[str,TruthWorld]:
    truth_root=Path(truth_root)
    if not truth_root.is_dir(): _refuse("controller truth root missing")
    worlds=[load_truth_world(p) for p in sorted(truth_root.iterdir()) if p.is_dir()]
    if len(worlds)!=12: _refuse(f"controller truth contains {len(worlds)} worlds, expected 12")
    if len({w.opaque_world_id for w in worlds})!=12 or len({w.world_index for w in worlds})!=12 or len({w.world_name for w in worlds})!=12:
        _refuse("controller truth world identities are not one-to-one")
    expected_names=[]
    for rec in contract.get("worlds",{}).get("world_list",[]):
        if isinstance(rec,Mapping): expected_names.append(str(rec.get("name")))
        else: expected_names.append(str(rec))
    if set(expected_names)!={w.world_name for w in worlds} or len(expected_names)!=12:
        _refuse("controller truth world names differ from frozen contract")
    if {w.world_index for w in worlds}!=set(range(12)): _refuse("controller truth world indices differ")
    return {w.world_name:w for w in worlds}
