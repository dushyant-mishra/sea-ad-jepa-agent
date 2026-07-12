#!/usr/bin/env python3
"""Stage75E/E4 mechanics-only pycisTarget/SCENIC+ resource smoke test.

This script does not run biological inference. It checks that the validated
container can import the SCENIC+ ecosystem, see the bounded smoke inputs, read
motif-to-TF annotations, and open cisTarget Arrow schemas without memory mapping
multi-GB files.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


REGION_RE = re.compile(r"^chr[^:]+:\d+-\d+$")


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config is not a mapping: {path}")
    return data


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def read_list(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def inspect_bed(path: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6:
                failures.append(f"line {line_no}: expected >=6 BED columns")
                continue
            chrom, start_s, end_s, name, score, strand = parts[:6]
            try:
                start = int(start_s)
                end = int(end_s)
            except ValueError:
                failures.append(f"line {line_no}: non-integer coordinates")
                continue
            if start < 0 or end <= start:
                failures.append(f"line {line_no}: invalid interval")
            peak_id = name.split("|", 1)[1] if "|" in name else name
            if not REGION_RE.match(peak_id):
                failures.append(f"line {line_no}: name does not contain chr:start-end peak id")
            rows.append({"chrom": chrom, "start": start, "end": end, "name": name, "peak_id": peak_id})
    return {
        "n_regions": len(rows),
        "n_unique_region_ids": len({r["peak_id"] for r in rows}),
        "first_regions": rows[:5],
        "bed_failures": failures,
        "bed_pass": len(rows) > 0 and not failures,
    }


def inspect_arrow_schema(path: Path, max_fields: int) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        info["open_pass"] = False
        info["error"] = "missing"
        return info
    info["size_bytes"] = path.stat().st_size
    try:
        import pyarrow as pa
        import pyarrow.ipc as ipc
        with pa.OSFile(str(path), "rb") as source:
            reader = ipc.open_file(source)
            schema = reader.schema
            info.update({
                "open_pass": True,
                "record_batches": int(reader.num_record_batches),
                "n_schema_fields": int(len(schema)),
                "first_schema_fields": [str(field.name) for field in list(schema)[:max_fields]],
            })
    except Exception as exc:
        info.update({"open_pass": False, "error": f"{type(exc).__name__}: {exc}"})
    return info


def inspect_motif_tf_overlap(path: Path, tfs: list[str]) -> dict[str, Any]:
    tf_set = set(tfs)
    found: set[str] = set()
    n_rows = 0
    chunks = 0
    try:
        for chunk in pd.read_csv(
            path,
            sep="\t",
            usecols=["gene_name"],
            chunksize=250_000,
            low_memory=False,
        ):
            chunks += 1
            n_rows += int(len(chunk))
            found.update(set(chunk["gene_name"].dropna().astype(str)) & tf_set)
    except Exception as exc:
        return {
            "motif_table_pass": False,
            "error": f"{type(exc).__name__}: {exc}",
            "tf_overlap": [],
            "missing_tfs": tfs,
        }
    return {
        "motif_table_pass": bool(found),
        "n_rows_scanned": n_rows,
        "chunks_scanned": chunks,
        "tf_overlap": [tf for tf in tfs if tf in found],
        "missing_tfs": [tf for tf in tfs if tf not in found],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--max-schema-fields", type=int, default=12)
    args = parser.parse_args()

    project = args.project_dir.resolve()
    cfg = load_config(args.config.resolve())
    paths = cfg["paths"]
    outputs = cfg.get("outputs", {})

    report_path = project / outputs.get(
        "pycistarget_smoke_json",
        "results/reports/stage75e_pycistarget_smoke_v1.json",
    )
    table_path = project / outputs.get(
        "pycistarget_smoke_csv",
        "results/tables/stage75e_pycistarget_smoke_v1.csv",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.parent.mkdir(parents=True, exist_ok=True)

    modules = ["scenicplus", "pycistarget", "pycisTopic", "ctxcore", "pyarrow", "pandas"]
    module_status = {name: module_available(name) for name in modules}

    bed_path = project / outputs["smoke_regions_bed"]
    tf_path = project / outputs["smoke_tf_list"]
    gene_path = project / outputs["smoke_gene_list"]
    motif_path = project / paths["motif_annotation"]["path"]

    tfs = read_list(tf_path)
    genes = read_list(gene_path)
    bed_info = inspect_bed(bed_path)
    motif_info = inspect_motif_tf_overlap(motif_path, tfs)
    rankings_info = inspect_arrow_schema(project / paths["cistarget_rankings"]["path"], args.max_schema_fields)
    scores_info = inspect_arrow_schema(project / paths["cistarget_scores"]["path"], args.max_schema_fields)

    checks = [
        {"check": "scenicplus_import", "pass": module_status["scenicplus"]},
        {"check": "pycistarget_import", "pass": module_status["pycistarget"]},
        {"check": "pycisTopic_import", "pass": module_status["pycisTopic"]},
        {"check": "ctxcore_import", "pass": module_status["ctxcore"]},
        {"check": "bounded_bed_valid", "pass": bed_info["bed_pass"]},
        {"check": "tf_list_nonempty", "pass": len(tfs) > 0},
        {"check": "gene_list_nonempty", "pass": len(genes) > 0},
        {"check": "motif_table_tf_overlap", "pass": motif_info["motif_table_pass"]},
        {"check": "rankings_arrow_schema_open", "pass": rankings_info["open_pass"]},
        {"check": "scores_arrow_schema_open", "pass": scores_info["open_pass"]},
    ]
    smoke_pass = all(bool(row["pass"]) for row in checks)

    report = {
        "stage": "stage75e_pycistarget_mechanics_smoke_v1",
        "purpose": "mechanics-only resource and API smoke test; not motif enrichment inference",
        "not_for_candidate_selection": True,
        "not_motif_supported_yet": True,
        "not_validated_regulation": True,
        "project_dir": str(project),
        "module_status": module_status,
        "n_tfs": len(tfs),
        "tfs": tfs,
        "n_genes": len(genes),
        "bed": bed_info,
        "motif_annotation": motif_info,
        "cistarget_rankings": rankings_info,
        "cistarget_scores": scores_info,
        "checks": checks,
        "smoke_pass": smoke_pass,
        "safety": cfg.get("safety", {}),
    }
    pd.DataFrame(checks).to_csv(table_path, index=False)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote: {table_path}")
    print(f"Wrote: {report_path}")
    print(f"smoke_pass={smoke_pass}")
    if not smoke_pass:
        for row in checks:
            if not row["pass"]:
                print(f"FAIL: {row['check']}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())