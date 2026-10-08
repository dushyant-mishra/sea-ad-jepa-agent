#!/usr/bin/env python3
"""Frozen production consumer exposing exactly two teacher-input arrays."""
from __future__ import annotations
import csv,hashlib
from pathlib import Path
from types import MappingProxyType
import numpy as np

def _sha(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(8<<20),b""):h.update(block)
    return h.hexdigest()

def load_teacher_inputs(package_root: str | Path):
    root=Path(package_root).resolve()
    manifest=root/"FULL104_EXPRESSION_INTERFACE_V8_SHA256_MANIFEST.csv"
    anchor=root.parent/"FULL104_EXPRESSION_INTERFACE_V8.PACKAGE_ROOT_SHA256.txt"
    if not manifest.is_file() or not anchor.is_file() or _sha(manifest)!=anchor.read_text(encoding="ascii").strip():
        raise RuntimeError("package root anchor mismatch")
    rows=list(csv.DictReader(manifest.open("r",encoding="utf-8-sig",newline="")))
    for row in rows:
        path=root/row["path"]
        if not path.is_file() or path.stat().st_size!=int(row["bytes"]) or _sha(path)!=row["sha256"]:
            raise RuntimeError("package artifact mismatch: "+row["path"])
    model_dir=root/"model_inputs"
    payload=model_dir/"FULL104_EXPRESSION_INTERFACE_PAYLOAD.npz"
    if {p.name for p in model_dir.iterdir() if p.is_file()}!={payload.name}:
        raise RuntimeError("model-input directory contains an undeclared file")
    with np.load(payload,allow_pickle=False) as data:
        if set(data.files)!={"normalized_values","observation_states"}:
            raise RuntimeError("teacher payload schema mismatch")
        values=np.asarray(data["normalized_values"])
        states=np.asarray(data["observation_states"])
    if values.dtype!=np.float32 or states.dtype!=np.uint8 or values.shape!=states.shape or values.ndim!=2 or values.shape[1]!=41238:
        raise RuntimeError("teacher payload geometry/dtype mismatch")
    if not np.isfinite(values).all() or not set(np.unique(states)).issubset({0,1,2}):
        raise RuntimeError("teacher payload numerical/state mismatch")
    result=MappingProxyType({"normalized_values":values,"observation_states":states})
    if set(result)!={"normalized_values","observation_states"}:
        raise AssertionError("consumer return schema changed")
    return result
