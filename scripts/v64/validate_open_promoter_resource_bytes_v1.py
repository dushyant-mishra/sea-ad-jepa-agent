#!/usr/bin/env python3
"""Validate exact bytes fetched for V64 open promoter/regulatory resources.

Fail closed on HTML/challenge payloads, corrupt archives, malformed BED/GTF,
or file-type mismatches. This is custody validation only.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import zipfile


def _first_bytes(path: Path, n: int = 16) -> bytes:
    with path.open("rb") as fh:
        return fh.read(n)


def _looks_html(path: Path) -> bool:
    head = _first_bytes(path, 512).lstrip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html") or b"<title>client challenge</title>" in head


def validate_gzip_text(path: Path, *, expect_gtf: bool = False) -> dict:
    if _looks_html(path):
        raise ValueError(f"{path.name}: HTML payload, not gzip data")
    with gzip.open(path, "rt", encoding="utf-8", errors="strict") as fh:
        lines = 0
        feature_counts: dict[str, int] = {}
        for raw in fh:
            if raw.startswith("#"):
                continue
            line = raw.rstrip("\n")
            if not line:
                continue
            lines += 1
            if expect_gtf:
                parts = line.split("\t")
                if len(parts) != 9:
                    raise ValueError(f"{path.name}: malformed GTF line with {len(parts)} fields")
                feature_counts[parts[2]] = feature_counts.get(parts[2], 0) + 1
            if lines >= 5000 and not expect_gtf:
                break
        if lines == 0:
            raise ValueError(f"{path.name}: no data lines")
    out = {"kind": "gzip_text", "sampled_or_counted_lines": lines}
    if expect_gtf:
        out["feature_counts"] = feature_counts
        if feature_counts.get("gene", 0) < 1000 or feature_counts.get("transcript", 0) < 1000:
            raise ValueError(f"{path.name}: implausible GTF feature counts")
    return out


def validate_gzip_bed(path: Path) -> dict:
    if _looks_html(path):
        raise ValueError(f"{path.name}: HTML payload, not gzip BED")
    rows = 0
    columns_seen = set()
    with gzip.open(path, "rt", encoding="utf-8", errors="strict") as fh:
        for raw in fh:
            if not raw.strip() or raw.startswith("#"):
                continue
            parts = raw.rstrip("\n").split("\t")
            if len(parts) < 6:
                raise ValueError(f"{path.name}: BED row has <6 columns")
            start, end = int(parts[1]), int(parts[2])
            if start < 0 or end <= start:
                raise ValueError(f"{path.name}: invalid BED coordinates")
            columns_seen.add(len(parts))
            rows += 1
    if rows == 0:
        raise ValueError(f"{path.name}: no BED rows")
    return {"kind": "gzip_bed", "rows": rows, "column_counts_seen": sorted(columns_seen)}


def validate_bed(path: Path) -> dict:
    if _looks_html(path):
        raise ValueError(f"{path.name}: HTML payload, not BED")
    rows = 0
    with path.open("rt", encoding="utf-8", errors="strict") as fh:
        for raw in fh:
            if not raw.strip() or raw.startswith("#"):
                continue
            parts = raw.rstrip("\n").split("\t")
            if len(parts) < 3:
                raise ValueError(f"{path.name}: BED row has <3 columns")
            start, end = int(parts[1]), int(parts[2])
            if start < 0 or end <= start:
                raise ValueError(f"{path.name}: invalid BED coordinates")
            rows += 1
    if rows == 0:
        raise ValueError(f"{path.name}: no BED rows")
    return {"kind": "bed", "rows": rows}


def validate_xlsx(path: Path) -> dict:
    if _looks_html(path):
        raise ValueError(f"{path.name}: HTML/client-challenge payload, not XLSX")
    if not zipfile.is_zipfile(path):
        raise ValueError(f"{path.name}: not a ZIP/XLSX file")
    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise ValueError(f"{path.name}: corrupt ZIP member {bad}")
        names = set(zf.namelist())
        if "[Content_Types].xml" not in names or "xl/workbook.xml" not in names:
            raise ValueError(f"{path.name}: ZIP lacks XLSX workbook structure")
        sheets = sum(1 for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))
    return {"kind": "xlsx", "zip_members": len(names), "worksheet_xml_count": sheets}


def validate_item(path: Path, resource_id: str) -> dict:
    name = path.name
    if resource_id.startswith("GENCODE_"):
        return validate_gzip_text(path, expect_gtf=True)
    if resource_id == "FANTOM5_HG38_CAGE_PEAK_COORDINATES":
        return validate_gzip_bed(path)
    if resource_id.startswith("FANTOM5_"):
        return validate_gzip_text(path, expect_gtf=False)
    if resource_id.startswith("SCREEN_"):
        return validate_bed(path)
    if name.lower().endswith(".xlsx"):
        return validate_xlsx(path)
    raise ValueError(f"{name}: no validator for resource {resource_id}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch-receipt", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args(argv)

    receipt = json.loads(args.fetch_receipt.read_text(encoding="utf-8"))
    out_items = []
    failures = []
    for item in receipt["items"]:
        path = Path(item["path"])
        try:
            detail = validate_item(path, item["resource_id"])
            out_items.append({**item, "valid": True, "validation": detail})
        except Exception as exc:
            failures.append({
                "resource_id": item["resource_id"],
                "path": str(path),
                "url": item["url"],
                "valid": False,
                "error": str(exc),
            })

    out = {
        "schema": "V64_OPEN_RESOURCE_BYTE_VALIDATION_RECEIPT_V1",
        "fetch_receipt": str(args.fetch_receipt),
        "items_valid": len(out_items),
        "items_failed": len(failures),
        "validated_items": out_items,
        "failures": failures,
        "pass": len(failures) == 0,
        "training_authorized": False,
        "biological_use_authorized": False,
    }
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
