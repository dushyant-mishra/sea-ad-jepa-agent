#!/usr/bin/env python3
"""Authenticate and requalify a preserved foundation-state report.

The receipt is published by exclusive hard-link from an fsynced same-directory
temporary file, so an existing receipt is never overwritten and readers never see
a partially written target. This script cannot grant training or target-discovery
value-read authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src" / "sea_ad_jepa" / "v4" / "foundation_qualification_v4.py"


def _load_core():
    spec = importlib.util.spec_from_file_location("foundation_qualification_v4_cli_core", CORE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _atomic_exclusive_json(path: Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    data = (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as fh:
            tmp_path = Path(fh.name)
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        try:
            os.link(tmp_path, path)
        except FileExistsError:
            raise
        tmp_path.unlink()
        tmp_path = None
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def run(source_report: Path, out: Path) -> dict[str, Any]:
    source_report = Path(source_report)
    out = Path(out)
    raw = source_report.read_bytes()
    report = json.loads(raw.decode("utf-8"))
    core = _load_core()
    rec = core.requalify_historical_report(report)
    rec = dict(rec)
    rec["source_report_sha256"] = hashlib.sha256(raw).hexdigest()
    rec["source_report_bytes"] = len(raw)
    # Defense in depth: the CLI itself refuses any authority escalation even if
    # a future core implementation were changed incorrectly.
    for key in ("training_authorized", "target_discovery_value_read_authorized", "stage4_authorized"):
        if rec.get(key) is not False:
            raise RuntimeError(f"requalification attempted forbidden authority: {key}")
    _atomic_exclusive_json(out, rec)
    return rec


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Authenticate and requalify preserved foundation-state evidence")
    p.add_argument("--source-report", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    rec = run(a.source_report, a.out)
    print(json.dumps({"terminal": rec["terminal"], "source_report_sha256": rec["source_report_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
