#!/usr/bin/env python3
"""Stage75F/F5a cisTarget region-name and overlap mapping audit.

The Stage75F batch BED files contain local peak IDs. The cisTarget SCREEN
rankings database uses its own region universe as Feather columns. This script
builds a reusable out-of-core region-index sidecar from bounded Feather column
reads, then maps each batch BED region to exact or overlapping cisTarget regions.
It does not run motif enrichment or claim validated regulation.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.feather as feather
import yaml


REGION_RE = re.compile(r"^(chr[^:]+):(\d+)-(\d+)$")


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config is not a mapping: {path}")
    return data


def parse_region(region: str) -> tuple[str | None, int | None, int | None]:
    match = REGION_RE.match(str(region))
    if not match:
        return None, None, None
    chrom, start, end = match.groups()
    return chrom, int(start), int(end)


def read_column_name(database: Path, index: int) -> str:
    table = feather.read_table(str(database), columns=[index], memory_map=False, use_threads=False)
    if table.num_columns != 1:
        raise RuntimeError(f"Expected one column for index {index}, got {table.num_columns}")
    return str(table.schema.field(0).name)


def index_exists(database: Path, index: int) -> bool:
    try:
        read_column_name(database, index)
        return True
    except Exception:
        return False


def find_num_columns(database: Path) -> int:
    lo = 0
    hi = 1
    while index_exists(database, hi - 1):
        lo = hi
        hi *= 2
    left = lo
    right = hi
    while left < right:
        mid = (left + right) // 2
        if index_exists(database, mid):
            left = mid + 1
        else:
            right = mid
    return left


def build_region_index(database: Path, output_csv_gz: Path, batch_size: int) -> dict[str, Any]:
    output_csv_gz.parent.mkdir(parents=True, exist_ok=True)
    n_columns = find_num_columns(database)
    print(f"cisTarget database columns={n_columns}", flush=True)
    n_parseable = 0
    n_written = 0
    with gzip.open(output_csv_gz, "wt", encoding="utf-8", newline="") as handle:
        handle.write("column_index,region_id,chrom,start,end\n")
        for start_idx in range(0, n_columns, batch_size):
            end_idx = min(start_idx + batch_size, n_columns)
            table = feather.read_table(
                str(database),
                columns=list(range(start_idx, end_idx)),
                memory_map=False,
                use_threads=False,
            )
            for offset, name in enumerate(table.schema.names):
                chrom, start, end = parse_region(name)
                if chrom is None:
                    continue
                n_parseable += 1
                handle.write(f"{start_idx + offset},{name},{chrom},{start},{end}\n")
                n_written += 1
            print(f"  indexed columns {end_idx}/{n_columns} parseable={n_parseable}", flush=True)
    return {"n_columns": n_columns, "n_parseable_regions": n_parseable, "index_csv_gz": str(output_csv_gz)}


def load_batch_regions(project: Path, manifest_csv: Path) -> pd.DataFrame:
    manifest = pd.read_csv(manifest_csv)
    rows: list[dict[str, Any]] = []
    for _, batch in manifest.iterrows():
        bed_path = project / str(batch["bed_path"])
        with bed_path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 4:
                    continue
                chrom, start_s, end_s, name = parts[:4]
                peak_id = name.split("|", 1)[1] if "|" in name else name
                rows.append({
                    "batch_id": int(batch["batch_id"]),
                    "tf": str(batch["tf"]),
                    "bed_path": str(batch["bed_path"]),
                    "query_region": peak_id,
                    "query_chrom": chrom,
                    "query_start": int(start_s),
                    "query_end": int(end_s),
                    "query_name": name,
                    "bed_line": line_no,
                })
    return pd.DataFrame(rows)


def overlap_bp(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    return max(0, min(a_end, b_end) - max(a_start, b_start))


def map_regions(index_csv_gz: Path, queries: pd.DataFrame, min_overlap_bp: int) -> pd.DataFrame:
    exact_query_ids = set(queries["query_region"].astype(str))
    best: dict[int, dict[str, Any]] = {
        int(i): {
            "exact_match": False,
            "mapped_db_region": "",
            "db_column_index": -1,
            "overlap_bp": 0,
            "overlap_fraction_query": 0.0,
            "overlap_fraction_db": 0.0,
        }
        for i in queries.index
    }
    by_chrom = {chrom: frame for chrom, frame in queries.groupby("query_chrom", sort=False)}

    for chunk in pd.read_csv(index_csv_gz, chunksize=250_000):
        for chrom, db_rows in chunk.groupby("chrom", sort=False):
            q = by_chrom.get(chrom)
            if q is None or q.empty:
                continue
            for db in db_rows.itertuples(index=False):
                db_start = int(db.start)
                db_end = int(db.end)
                db_len = max(1, db_end - db_start)
                candidates = q.loc[(q["query_start"] < db_end) & (q["query_end"] > db_start)]
                if candidates.empty:
                    continue
                for qidx, query in candidates.iterrows():
                    ov = overlap_bp(int(query.query_start), int(query.query_end), db_start, db_end)
                    if ov < min_overlap_bp:
                        continue
                    q_len = max(1, int(query.query_end) - int(query.query_start))
                    exact = str(query.query_region) == str(db.region_id)
                    current = best[int(qidx)]
                    better = exact or ov > int(current["overlap_bp"])
                    if better:
                        current.update({
                            "exact_match": bool(exact),
                            "mapped_db_region": str(db.region_id),
                            "db_column_index": int(db.column_index),
                            "overlap_bp": int(ov),
                            "overlap_fraction_query": float(ov / q_len),
                            "overlap_fraction_db": float(ov / db_len),
                        })
    mapped = queries.copy()
    best_df = pd.DataFrame.from_dict(best, orient="index")
    return pd.concat([mapped.reset_index(drop=True), best_df.reset_index(drop=True)], axis=1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--rebuild-index", action="store_true")
    args = parser.parse_args()

    project = args.project_dir.resolve()
    cfg = load_config(args.config.resolve())
    mapping_cfg = cfg["cistarget_region_mapping"]
    database_key = "cistarget_rankings" if mapping_cfg.get("database", "rankings") == "rankings" else "cistarget_scores"
    database = project / cfg["inputs"][database_key]
    index_csv_gz = project / mapping_cfg["index_csv_gz"]
    mapping_csv = project / mapping_cfg["mapping_csv"]
    summary_json = project / mapping_cfg["summary_json"]
    manifest_csv = project / cfg["outputs"]["batch_manifest_csv"]

    if args.rebuild_index or not index_csv_gz.exists():
        index_info = build_region_index(database, index_csv_gz, int(mapping_cfg.get("column_batch_size", 4096)))
    else:
        index_info = {"index_csv_gz": str(index_csv_gz), "reused_existing_index": True}

    queries = load_batch_regions(project, manifest_csv)
    mapped = map_regions(index_csv_gz, queries, int(mapping_cfg.get("min_overlap_bp", 1)))
    mapping_csv.parent.mkdir(parents=True, exist_ok=True)
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    mapped.to_csv(mapping_csv, index=False)

    summary = {
        "stage": "stage75f_cistarget_region_mapping_v1",
        "purpose": "region universe mapping audit before motif enrichment",
        "not_motif_enrichment": True,
        "not_validated_regulation": True,
        "database": str(database),
        "n_query_regions": int(len(mapped)),
        "n_exact_matches": int(mapped["exact_match"].sum()),
        "n_overlap_mapped": int((mapped["overlap_bp"] > 0).sum()),
        "n_unmapped": int((mapped["overlap_bp"] <= 0).sum()),
        "min_overlap_bp": int(mapping_cfg.get("min_overlap_bp", 1)),
        "index": index_info,
        "outputs": {
            "mapping_csv": str(mapping_csv.relative_to(project)),
            "summary_json": str(summary_json.relative_to(project)),
        },
        "safety": cfg.get("safety", {}),
    }
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote: {mapping_csv}")
    print(f"Wrote: {summary_json}")
    print(json.dumps(summary, indent=2))
    return 0 if summary["n_overlap_mapped"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
