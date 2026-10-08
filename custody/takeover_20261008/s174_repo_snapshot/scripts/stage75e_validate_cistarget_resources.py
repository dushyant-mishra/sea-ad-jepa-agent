#!/usr/bin/env python3
"""Validate cisTarget resources with a low-memory default path."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


LARGE_RESOURCE_BYTES = 1024**3


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config is not a mapping: {path}")
    return data


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


def inspect_file_header(path: Path, n_bytes: int = 16) -> dict[str, Any]:
    with path.open("rb") as handle:
        head = handle.read(n_bytes)
    return {
        "header_bytes_read": len(head),
        "header_hex": head.hex(),
        "nonempty_header_pass": len(head) > 0,
    }


def inspect_arrow_file(path: Path) -> dict[str, Any]:
    """Optional deeper check; not used by default for large cisTarget files."""
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
    parser.add_argument(
        "--inspect-arrow",
        action="store_true",
        help="Opt into pyarrow metadata/open checks. Disabled by default to avoid OOM on multi-GB cisTarget files.",
    )
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
        "inspect_arrow_requested": bool(args.inspect_arrow),
        "resources": {},
        "safety": cfg.get("safety", {}),
        "note": "Default validation avoids opening multi-GB Feather matrices to prevent container OOM; SHA1 was performed by the downloader or --verify-sha1.",
    }
    failures: list[str] = []

    for resource_key, manifest_key in pairs:
        resource = project / paths[resource_key]["path"]
        manifest = project / paths[manifest_key]["path"]
        size = resource.stat().st_size if resource.exists() else 0
        row: dict[str, Any] = {
            "resource": resource_key,
            "path": str(resource.relative_to(project)),
            "exists": resource.exists(),
            "size_bytes": size,
            "sha1_manifest_exists": manifest.exists(),
            "sha1_verified": None,
            "arrow_open_pass": None,
            "low_memory_integrity_pass": False,
        }

        extra: dict[str, Any] = {}
        if not resource.exists() or size == 0:
            failures.append(f"{resource_key}: missing or empty")
        else:
            extra.update(inspect_file_header(resource))
            row["low_memory_integrity_pass"] = bool(extra["nonempty_header_pass"])

        if manifest.exists():
            expected, manifest_name = parse_sha1_manifest(manifest)
            extra["expected_sha1"] = expected
            extra["manifest_filename"] = manifest_name
            extra["manifest_filename_match"] = manifest_name == resource.name
            if manifest_name != resource.name:
                failures.append(
                    f"{resource_key}: SHA1 manifest filename {manifest_name} does not match {resource.name}"
                )
            if args.verify_sha1 and resource.exists():
                observed = stream_sha1(resource)
                extra["observed_sha1"] = observed
                row["sha1_verified"] = observed == expected
                if not row["sha1_verified"]:
                    failures.append(f"{resource_key}: SHA1 mismatch")
        else:
            failures.append(f"{resource_key}: SHA1 manifest missing")

        if args.inspect_arrow and resource.exists() and size > 0:
            extra.update(inspect_arrow_file(resource))
            row["arrow_open_pass"] = bool(extra.get("arrow_open_pass", False))
            if not row["arrow_open_pass"]:
                failures.append(f"{resource_key}: Arrow/Feather open failed")
        elif size >= LARGE_RESOURCE_BYTES:
            extra["arrow_open_skipped_reason"] = "large_resource_default_low_memory_gate"

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
        "low_memory_integrity_pass": False,
    }
    motif_detail: dict[str, Any] = {**motif_row}
    if motif.exists() and motif.stat().st_size > 0:
        with motif.open("r", encoding="utf-8", errors="replace") as handle:
            first_lines = [handle.readline().rstrip("\n") for _ in range(3)]
        motif_detail["first_lines"] = first_lines
        motif_detail["tabular_header_pass"] = bool(first_lines and "\t" in first_lines[0])
        motif_row["low_memory_integrity_pass"] = bool(motif_detail["tabular_header_pass"])
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
