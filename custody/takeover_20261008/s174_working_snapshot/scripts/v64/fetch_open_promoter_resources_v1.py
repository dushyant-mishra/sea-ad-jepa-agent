#!/usr/bin/env python3
"""Fetch explicitly approved open/public promoter-regulatory resources.

Defaults to dry-run. This utility is custody plumbing only:
- it does not authorize biological use;
- it does not infer a license from downloadability;
- it records exact bytes, size and SHA-256 when --download is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "results/v64/V64_OPEN_RESOURCE_FETCH_MANIFEST_V1.json"


def _urls(row: dict) -> list[str]:
    if "download_url" in row:
        return [row["download_url"]]
    return list(row.get("download_urls", []))


def _safe_name(resource_id: str, url: str, index: int) -> str:
    tail = url.rsplit("/", 1)[-1]
    tail = tail.replace("%2B", "+").replace("%3A", ":").replace("%2F", "_")
    if not tail or tail.endswith("/"):
        tail = f"resource_{index}"
    return f"{resource_id}__{index:02d}__{tail}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def plan(manifest: dict) -> list[dict]:
    out = []
    for row in manifest["resources"]:
        urls = _urls(row)
        if not urls:
            raise ValueError(f"resource {row.get('id')} has no exact download URL")
        for i, url in enumerate(urls, 1):
            if not isinstance(url, str) or not url.startswith("https://"):
                raise ValueError(f"resource {row.get('id')} has invalid URL {url!r}")
            out.append({
                "resource_id": row["id"],
                "url": url,
                "index": i,
                "declared_access": row.get("access"),
                "declared_license_or_terms": (
                    row.get("data_license_status")
                    or row.get("article_license")
                    or "UNSPECIFIED_IN_FETCH_MANIFEST"
                ),
            })
    return out


def fetch_one(item: dict, outdir: Path, timeout: float = 120.0) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    name = _safe_name(item["resource_id"], item["url"], item["index"])
    dst = outdir / name
    req = urllib.request.Request(item["url"], headers={"User-Agent": "sea-ad-jepa-v64-resource-fetch/1"})
    with urllib.request.urlopen(req, timeout=timeout) as src, dst.open("wb") as fh:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)
    return {
        **item,
        "path": str(dst),
        "bytes": dst.stat().st_size,
        "sha256": sha256_file(dst),
        "downloaded": True,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--outdir", type=Path, default=Path("open_resource_cache_v1"))
    ap.add_argument("--receipt", type=Path, default=Path("V64_OPEN_RESOURCE_FETCH_RECEIPT_V1.json"))
    ap.add_argument("--download", action="store_true", help="perform network downloads; default is dry-run")
    args = ap.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    items = plan(manifest)

    if not args.download:
        print(json.dumps({
            "schema": "V64_OPEN_RESOURCE_FETCH_DRY_RUN_V1",
            "manifest": str(args.manifest),
            "download": False,
            "items": items,
            "training_authorized": False,
        }, indent=2, sort_keys=True))
        return 0

    results = [fetch_one(item, args.outdir) for item in items]
    receipt = {
        "schema": "V64_OPEN_RESOURCE_FETCH_RECEIPT_V1",
        "manifest": str(args.manifest),
        "download": True,
        "items": results,
        "training_authorized": False,
        "biological_use_authorized": False,
    }
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
