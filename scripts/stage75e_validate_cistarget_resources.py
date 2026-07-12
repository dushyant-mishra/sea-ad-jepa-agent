#!/usr/bin/env python3
"""Validate large cisTarget resources without loading their matrices into RAM."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def parse_sha1_manifest(path: Path) -> tuple[str, str]:
    line = path.read_text(encoding="utf-8").strip().splitlines()[0]
    parts = line.split()
    if len(parts) < 2:
        raise ValueError(f"Malformed SHA1 manifest: {path}")
    return parts[0].lower(), parts[-1].lstrip("*")


def stream_sha1(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_arrow_file(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {}
    try:
        import pyarrow as pa
        import pyarrow.ipc as ipc
        with pa.memory_map(str(path), "r") as source:
            reader = ipc.open_file(source)
            schema = reader.schema
            info.update({
                "arrow_open_pass": True,
                "record_batches": int(reader.num_record_batches),
                "n_schema_fields": int(len(schema)),
                "first_schema_fields": [str(field.name) for field in schema[:20]],
            })
            try:
                info["schema_metadata_keys"] = sorted(
                    k.decode("utf-8", errors="replace")
                    for k in (schema.metadata or {}).keys()
                )
            except Exception:
                info["schema_metadata_keys"] = []
            return info
    except Exception as ipc_exc:
        info["ipc_open_error"] = f"{type(ipc_exc).__name__}: {ipc_exc}"

    try:
        import pyarrow.feather as feather
        table = feather.read_table(path, columns=[])
        info.update({
            "arrow_open_pass": True,
            "fallback": "pyarrow.feather.read_table(columns=[])",
            "n_rows": int(table.num_rows),
            "n_schema_fields": int(table.num_columns),
        })
    except Exception as feather_exc:
        info.update({
            "arrow_open_pass": False,
            "feather_open_error": f"{type(feather_exc).__name__}: {feather_exc}",
        })
    return info


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--verify-sha1", action="store_true")
    args = parser.parse_args()

    project = args.project_dir.resolve()
    cfg = load_config(args.config.resolve())
    paths = cfg["paths"]
    outputs = cfg["outputs"]

    pairs = [
        ("cistarget_rankings", "cistarget_rankings_sha1"),
        ("cistarget_scores", "cistarget_scores_sha1"),
    ]

    rows: list[dict[str, Any]] = []
    details: dict[str, Any] = {
        "stage": cfg.get("stage"),
        "verify_sha1_requested": bool(args.verify_sha1),
        "resources": {},
        "safety": cfg.get("safety", {}),
    }
    failures: list[str] = []

    for resource_key, manifest_key in pairs:
        resource = project / paths[resource_key]["path"]
        manifest = project / paths[manifest_key]["path"]
        row: dict[str, Any] = {
            "resource": resource_key,
            "path": str(resource.relative_to(project)),
            "exists": resource.exists(),
            "size_bytes": resource.stat().st_size if resource.exists() else 0,
            "sha1_manifest_exists": manifest.exists(),
            "sha1_verified": None,
            "arrow_open_pass": False,
        }

        extra: dict[str, Any] = {}
        if not resource.exists() or resource.stat().st_size == 0:
            failures.append(f"{resource_key}: missing or empty")
        else:
            extra.update(inspect_arrow_file(resource))
            row["arrow_open_pass"] = bool(extra.get("arrow_open_pass", False))
            if not row["arrow_open_pass"]:
                failures.append(f"{resource_key}: Arrow/Feather open failed")

        if manifest.exists():
            expected, manifest_name = parse_sha1_manifest(manifest)
            extra["expected_sha1"] = expected
            extra["manifest_filename"] = manifest_name
            if args.verify_sha1 and resource.exists():
                observed = stream_sha1(resource)
                extra["observed_sha1"] = observed
                row["sha1_verified"] = observed == expected
                if not row["sha1_verified"]:
                    failures.append(f"{resource_key}: SHA1 mismatch")
        elif args.verify_sha1:
            failures.append(f"{resource_key}: SHA1 manifest missing")

        rows.append(row)
        details["resources"][resource_key] = {**row, **extra}

    motif = project / paths["motif_annotation"]["path"]
    motif_row = {
        "resource": "motif_annotation",
        "path": str(motif.relative_to(project)),
        "exists": motif.exists(),
        "size_bytes": motif.stat().st_size if motif.exists() else 0,
        "sha1_manifest_exists": False,
        "sha1_verified": None,
        "arrow_open_pass": None,
    }
    motif_detail: dict[str, Any] = {**motif_row}
    if motif.exists() and motif.stat().st_size > 0:
        with motif.open("r", encoding="utf-8", errors="replace") as handle:
            first_lines = [handle.readline().rstrip("\n") for _ in range(3)]
        motif_detail["first_lines"] = first_lines
        motif_detail["tabular_header_pass"] = bool(first_lines and "\t" in first_lines[0])
        if not motif_detail["tabular_header_pass"]:
            failures.append("motif_annotation: first line is not tab-delimited")
    else:
        failures.append("motif_annotation: missing or empty")
    rows.append(motif_row)
    details["resources"]["motif_annotation"] = motif_detail

    csv_path = project / outputs["cistarget_inventory_csv"]
    json_path = project / outputs["cistarget_inventory_json"]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    details["failures"] = failures
    details["resource_integrity_pass"] = not failures
    json_path.write_text(json.dumps(details, indent=2), encoding="utf-8")

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {json_path}")
    print(f"resource_integrity_pass={not failures}")
    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
