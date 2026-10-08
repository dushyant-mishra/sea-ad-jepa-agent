#!/usr/bin/env python3
"""Fail-closed NPH source firewall for FULL104 production consumers."""
from __future__ import annotations
import hashlib
from pathlib import Path
import pandas as pd

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(8<<20),b""):h.update(block)
    return h.hexdigest()

def canonical(path: Path) -> str:
    return str(Path(path).resolve()).replace("\\","/").casefold()

def assert_fit_only_nph_assets(asset_paths, asset_hashes, denylist_csv: Path, package_root: Path) -> None:
    asset_paths=list(asset_paths);asset_hashes=list(asset_hashes)
    if len(asset_paths)!=7 or len(asset_hashes)!=7 or len(asset_paths)!=len(asset_hashes):
        raise RuntimeError("exactly seven paired NPH derivative paths/hashes are required")
    if len({canonical(Path(p)) for p in asset_paths})!=7 or len({str(h).lower() for h in asset_hashes})!=7:
        raise RuntimeError("NPH derivative paths/hashes must be unique")
    deny=pd.read_csv(denylist_csv,dtype=str)
    required={"canonical_original_path","original_sha256"}
    if set(deny.columns)!=required or len(deny)!=7:
        raise RuntimeError("invalid original-NPH denylist")
    denied_paths=set(deny.canonical_original_path.map(lambda x:canonical(Path(x))))
    denied_hashes=set(deny.original_sha256.str.lower())
    package_key=canonical(package_root)+"/"
    for raw,digest in zip(asset_paths,asset_hashes):
        path=Path(raw).resolve();key=canonical(path)
        if key in denied_paths or str(digest).lower() in denied_hashes:
            raise RuntimeError("original mixed NPH asset denied")
        if not key.startswith(package_key):
            raise RuntimeError("NPH derivative is outside the verified package")
        if not path.is_file() or sha256(path)!=str(digest).lower():
            raise RuntimeError("NPH derivative authentication failed")

def run_negative_firewall_selftests(denylist_csv: Path, package_root: Path) -> None:
    deny=pd.read_csv(denylist_csv,dtype=str)
    denied=Path(deny.iloc[0].canonical_original_path)
    failed_closed=False
    try:assert_fit_only_nph_assets([denied],[],denylist_csv,package_root)
    except RuntimeError:failed_closed=True
    if not failed_closed:raise AssertionError("mismatched parallel inputs bypassed firewall")
    failed_closed=False
    try:assert_fit_only_nph_assets([denied]*7,deny.original_sha256.tolist(),denylist_csv,package_root)
    except RuntimeError:failed_closed=True
    if not failed_closed:raise AssertionError("denied original NPH asset bypassed firewall")
