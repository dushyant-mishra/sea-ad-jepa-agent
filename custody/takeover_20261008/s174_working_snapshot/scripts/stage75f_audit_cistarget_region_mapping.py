#!/usr/bin/env python3
"""Stage75F/F5a pycisTarget-compatible region mapping audit.

Build a reusable cisTarget region-name sidecar using bounded Feather reads, then
retain every query-to-database overlap satisfying the same rule as pycisTarget:

    overlap/query_length > fraction_overlap
    OR overlap/database_length > fraction_overlap

This stage does not run motif enrichment or claim validated regulation.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
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


def read_columns(database: Path, indices: list[int]):
    return feather.read_table(
        str(database),
        columns=indices,
        memory_map=False,
        use_threads=False,
    )


def index_exists(database: Path, index: int) -> bool:
    try:
        return read_columns(database, [index]).num_columns == 1
    except Exception:
        return False


def find_num_columns(database: Path) -> int:
    if not index_exists(database, 0):
        return 0
    lo, hi = 1, 2
    while index_exists(database, hi - 1):
        lo, hi = hi, hi * 2
    while lo < hi:
        mid = (lo + hi) // 2
        if index_exists(database, mid):
            lo = mid + 1
        else:
            hi = mid
    return lo


def file_identity(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path),
        "size_bytes": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def reusable_index(
    database: Path,
    index_csv: Path,
    index_manifest: Path,
) -> dict[str, Any] | None:
    if not index_csv.exists() or not index_manifest.exists():
        return None
    try:
        manifest = json.loads(index_manifest.read_text(encoding="utf-8"))
    except Exception:
        return None
    current = file_identity(database)
    source = manifest.get("source", {})
    if (
        manifest.get("complete") is True
        and source.get("size_bytes") == current["size_bytes"]
        and source.get("mtime_ns") == current["mtime_ns"]
    ):
        return manifest
    return None


def build_region_index(
    database: Path,
    index_csv: Path,
    index_manifest: Path,
    batch_size: int,
) -> dict[str, Any]:
    """Build an atomic, resumable-by-completion region coordinate sidecar."""
    index_csv.parent.mkdir(parents=True, exist_ok=True)
    index_manifest.parent.mkdir(parents=True, exist_ok=True)
    tmp_csv = index_csv.with_name(index_csv.name + ".tmp")
    tmp_manifest = index_manifest.with_name(index_manifest.name + ".tmp")
    tmp_csv.unlink(missing_ok=True)
    tmp_manifest.unlink(missing_ok=True)

    n_columns = find_num_columns(database)
    if n_columns <= 0:
        raise RuntimeError(f"No readable Feather columns: {database}")

    print(
        f"Building region index from {database.name}: "
        f"columns={n_columns} batch_size={batch_size}",
        flush=True,
    )
    n_regions = 0
    n_nonregions = 0
    name_hash = hashlib.sha256()

    try:
        with gzip.open(tmp_csv, "wt", encoding="utf-8", newline="") as handle:
            handle.write("column_index,region_id,chrom,start,end\n")
            for start_idx in range(0, n_columns, batch_size):
                end_idx = min(start_idx + batch_size, n_columns)
                indices = list(range(start_idx, end_idx))
                table = read_columns(database, indices)
                if table.num_columns != len(indices):
                    raise RuntimeError(
                        f"Read {table.num_columns} of {len(indices)} requested "
                        f"columns at {start_idx}:{end_idx}"
                    )

                for offset, name in enumerate(table.schema.names):
                    name = str(name)
                    name_hash.update(name.encode("utf-8"))
                    name_hash.update(b"\n")
                    chrom, start, end = parse_region(name)
                    if chrom is None:
                        n_nonregions += 1
                        continue
                    handle.write(
                        f"{start_idx + offset},{name},{chrom},{start},{end}\n"
                    )
                    n_regions += 1

                del table
                print(
                    f"  indexed {end_idx}/{n_columns}; regions={n_regions}",
                    flush=True,
                )

        manifest = {
            "stage": "stage75f_cistarget_region_index_v2",
            "source": file_identity(database),
            "n_columns": int(n_columns),
            "n_parseable_regions": int(n_regions),
            "n_nonregion_columns": int(n_nonregions),
            "column_name_sha256": name_hash.hexdigest(),
            "batch_size": int(batch_size),
            "index_csv_gz": str(index_csv),
            "complete": True,
        }
        tmp_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        tmp_csv.replace(index_csv)
        tmp_manifest.replace(index_manifest)
        return manifest
    except Exception:
        tmp_csv.unlink(missing_ok=True)
        tmp_manifest.unlink(missing_ok=True)
        raise


def verify_column_parity(
    source_database: Path,
    other_database: Path,
    n_columns: int,
    n_samples: int,
) -> dict[str, Any]:
    """Check that scores and rankings use the same numeric column index space."""
    other_count = find_num_columns(other_database)
    if other_count != n_columns:
        raise RuntimeError(
            f"Column count differs: {source_database.name}={n_columns}; "
            f"{other_database.name}={other_count}"
        )

    sample_count = max(2, min(int(n_samples), n_columns))
    indices = sorted(
        set(np.linspace(0, n_columns - 1, sample_count, dtype=np.int64).tolist())
    )
    source_names = list(read_columns(source_database, indices).schema.names)
    other_names = list(read_columns(other_database, indices).schema.names)
    mismatches = [
        {
            "column_index": int(i),
            "source_name": str(a),
            "other_name": str(b),
        }
        for i, a, b in zip(indices, source_names, other_names)
        if str(a) != str(b)
    ]
    if mismatches:
        raise RuntimeError(f"Column parity mismatch: {mismatches[:3]}")

    return {
        "pass": True,
        "n_columns": int(n_columns),
        "sampled_column_count": int(len(indices)),
        "sampled_indices": [int(i) for i in indices],
        "source_database": str(source_database),
        "other_database": str(other_database),
    }


def load_batch_regions(project: Path, manifest_csv: Path) -> pd.DataFrame:
    manifest = pd.read_csv(manifest_csv)
    required = {"batch_id", "tf", "bed_path"}
    missing = required - set(manifest.columns)
    if missing:
        raise ValueError(f"Missing manifest columns: {sorted(missing)}")

    rows: list[dict[str, Any]] = []
    query_row_id = 0
    for batch in manifest.itertuples(index=False):
        bed_path = project / str(batch.bed_path)
        with bed_path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 4:
                    raise ValueError(
                        f"{bed_path}:{line_no}: expected at least four BED columns"
                    )
                chrom, start_s, end_s, name = parts[:4]
                peak_id = name.split("|", 1)[1] if "|" in name else name
                rows.append(
                    {
                        "query_row_id": query_row_id,
                        "batch_id": int(batch.batch_id),
                        "tf": str(batch.tf),
                        "bed_path": str(batch.bed_path),
                        "query_region": peak_id,
                        "query_chrom": chrom,
                        "query_start": int(start_s),
                        "query_end": int(end_s),
                        "query_name": name,
                        "bed_line": int(line_no),
                    }
                )
                query_row_id += 1

    queries = pd.DataFrame(rows)
    if queries.empty:
        raise RuntimeError("No batch regions found")
    if (queries["query_end"] <= queries["query_start"]).any():
        raise ValueError("Invalid query interval detected")
    return queries


def map_regions(
    index_csv: Path,
    queries: pd.DataFrame,
    fraction_overlap: float,
    chunksize: int,
) -> pd.DataFrame:
    """Keep all overlaps that pass pycisTarget's strict > threshold rule."""
    if not 0 <= fraction_overlap < 1:
        raise ValueError("fraction_overlap must be in [0, 1)")

    by_chrom = {
        str(chrom): frame.copy()
        for chrom, frame in queries.groupby("query_chrom", sort=False)
    }
    parts: list[pd.DataFrame] = []

    for chunk_number, chunk in enumerate(
        pd.read_csv(index_csv, chunksize=chunksize),
        start=1,
    ):
        for chrom, db_rows in chunk.groupby("chrom", sort=False):
            q_rows = by_chrom.get(str(chrom))
            if q_rows is None or q_rows.empty:
                continue

            db_start = db_rows["start"].to_numpy(dtype=np.int64, copy=False)
            db_end = db_rows["end"].to_numpy(dtype=np.int64, copy=False)
            db_len = np.maximum(1, db_end - db_start)

            for query in q_rows.itertuples(index=False):
                q_start = int(query.query_start)
                q_end = int(query.query_end)
                q_len = max(1, q_end - q_start)

                overlap = np.minimum(db_end, q_end) - np.maximum(db_start, q_start)
                overlap = np.maximum(overlap, 0)
                frac_query = overlap / q_len
                frac_db = overlap / db_len
                keep = (frac_query > fraction_overlap) | (
                    frac_db > fraction_overlap
                )
                if not np.any(keep):
                    continue

                selected = db_rows.loc[
                    keep,
                    ["column_index", "region_id", "chrom", "start", "end"],
                ].copy()
                selected.rename(
                    columns={
                        "column_index": "db_column_index",
                        "region_id": "mapped_db_region",
                        "chrom": "db_chrom",
                        "start": "db_start",
                        "end": "db_end",
                    },
                    inplace=True,
                )
                selected["query_row_id"] = int(query.query_row_id)
                selected["batch_id"] = int(query.batch_id)
                selected["tf"] = str(query.tf)
                selected["bed_path"] = str(query.bed_path)
                selected["query_region"] = str(query.query_region)
                selected["query_chrom"] = str(query.query_chrom)
                selected["query_start"] = q_start
                selected["query_end"] = q_end
                selected["query_name"] = str(query.query_name)
                selected["bed_line"] = int(query.bed_line)
                selected["overlap_bp"] = overlap[keep].astype(np.int64)
                selected["overlap_fraction_query"] = frac_query[keep]
                selected["overlap_fraction_db"] = frac_db[keep]
                selected["exact_match"] = (
                    selected["mapped_db_region"].astype(str)
                    == str(query.query_region)
                )
                selected["fraction_overlap_threshold"] = float(
                    fraction_overlap
                )
                parts.append(selected)

        if chunk_number % 5 == 0:
            print(
                f"  scanned approximately {chunk_number * chunksize:,} "
                "database regions",
                flush=True,
            )

    columns = [
        "query_row_id",
        "batch_id",
        "tf",
        "bed_path",
        "query_region",
        "query_chrom",
        "query_start",
        "query_end",
        "query_name",
        "bed_line",
        "db_column_index",
        "mapped_db_region",
        "db_chrom",
        "db_start",
        "db_end",
        "overlap_bp",
        "overlap_fraction_query",
        "overlap_fraction_db",
        "exact_match",
        "fraction_overlap_threshold",
    ]
    if not parts:
        return pd.DataFrame(columns=columns)

    mappings = pd.concat(parts, ignore_index=True).loc[:, columns]
    mappings.sort_values(
        [
            "batch_id",
            "query_row_id",
            "exact_match",
            "overlap_bp",
            "mapped_db_region",
        ],
        ascending=[True, True, False, False, True],
        inplace=True,
    )
    mappings.drop_duplicates(
        ["query_row_id", "mapped_db_region"],
        keep="first",
        inplace=True,
    )
    return mappings.reset_index(drop=True)


def write_batch_lists(
    project: Path,
    queries: pd.DataFrame,
    mappings: pd.DataFrame,
) -> pd.DataFrame:
    mapped_ids = set(
        mappings["query_row_id"].astype(int) if not mappings.empty else []
    )
    exact_ids = set(
        mappings.loc[mappings["exact_match"], "query_row_id"].astype(int)
        if not mappings.empty
        else []
    )
    rows: list[dict[str, Any]] = []

    for (batch_id, tf, bed_path), q_batch in queries.groupby(
        ["batch_id", "tf", "bed_path"],
        sort=True,
    ):
        m_batch = (
            mappings.loc[mappings["batch_id"].astype(int) == int(batch_id)].copy()
            if not mappings.empty
            else mappings.copy()
        )
        source_bed = project / str(bed_path)
        if source_bed.name.endswith(".regions.bed"):
            mapped_path = source_bed.with_name(
                source_bed.name.replace(
                    ".regions.bed", ".cistarget_regions.txt"
                )
            )
            unmapped_path = source_bed.with_name(
                source_bed.name.replace(
                    ".regions.bed", ".unmapped_regions.txt"
                )
            )
        else:
            mapped_path = source_bed.with_suffix(
                source_bed.suffix + ".cistarget_regions.txt"
            )
            unmapped_path = source_bed.with_suffix(
                source_bed.suffix + ".unmapped_regions.txt"
            )

        db_regions = sorted(set(m_batch["mapped_db_region"].astype(str)))
        mapped_path.write_text(
            "".join(f"{region}\n" for region in db_regions),
            encoding="utf-8",
        )
        unmapped = q_batch.loc[
            ~q_batch["query_row_id"].isin(mapped_ids), "query_region"
        ].astype(str)
        unmapped_path.write_text(
            "".join(f"{region}\n" for region in sorted(set(unmapped))),
            encoding="utf-8",
        )

        n_query = int(len(q_batch))
        n_mapped = int(q_batch["query_row_id"].isin(mapped_ids).sum())
        n_exact = int(q_batch["query_row_id"].isin(exact_ids).sum())
        rows.append(
            {
                "batch_id": int(batch_id),
                "tf": str(tf),
                "bed_path": str(bed_path),
                "n_query_regions": n_query,
                "n_mapped_query_regions": n_mapped,
                "n_unmapped_query_regions": n_query - n_mapped,
                "query_coverage_fraction": (
                    float(n_mapped / n_query) if n_query else 0.0
                ),
                "n_exact_query_regions": n_exact,
                "n_mapping_rows": int(len(m_batch)),
                "n_unique_db_regions": int(len(db_regions)),
                "mapped_db_regions_path": str(mapped_path.relative_to(project)),
                "unmapped_query_regions_path": str(
                    unmapped_path.relative_to(project)
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["batch_id", "tf"]
    ).reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--rebuild-index", action="store_true")
    args = parser.parse_args()

    project = args.project_dir.resolve()
    cfg = load_config(args.config.resolve())
    mapping_cfg = cfg["cistarget_region_mapping"]

    source_kind = str(mapping_cfg.get("database", "scores")).lower()
    if source_kind not in {"scores", "rankings"}:
        raise ValueError("database must be scores or rankings")
    source_key = (
        "cistarget_scores" if source_kind == "scores" else "cistarget_rankings"
    )
    other_key = (
        "cistarget_rankings" if source_kind == "scores" else "cistarget_scores"
    )
    source_database = project / cfg["inputs"][source_key]
    other_database = project / cfg["inputs"][other_key]

    index_csv = project / mapping_cfg["index_csv_gz"]
    index_manifest = project / mapping_cfg.get(
        "index_manifest_json",
        "data/processed/stage75f/"
        "hg38_screen_v10_clust_region_index_manifest_v2.json",
    )
    mapping_csv = project / mapping_cfg["mapping_csv"]
    coverage_csv = project / mapping_cfg.get(
        "coverage_csv",
        "results/tables/stage75f_cistarget_region_coverage_v1.csv",
    )
    summary_json = project / mapping_cfg["summary_json"]
    batch_manifest = project / cfg["outputs"]["batch_manifest_csv"]

    index_info = None if args.rebuild_index else reusable_index(
        source_database, index_csv, index_manifest
    )
    if index_info is None:
        index_info = build_region_index(
            source_database,
            index_csv,
            index_manifest,
            int(mapping_cfg.get("column_batch_size", 4096)),
        )
    else:
        index_info = dict(index_info)
        index_info["reused_existing_index"] = True
        print(f"Reusing completed index: {index_csv}", flush=True)

    parity = verify_column_parity(
        source_database,
        other_database,
        int(index_info["n_columns"]),
        int(mapping_cfg.get("schema_parity_sample_columns", 32)),
    )
    print(
        "Scores/rankings numeric column parity PASS; "
        f"sampled={parity['sampled_column_count']}",
        flush=True,
    )

    queries = load_batch_regions(project, batch_manifest)
    fraction_overlap = float(mapping_cfg.get("fraction_overlap", 0.4))
    mappings = map_regions(
        index_csv,
        queries,
        fraction_overlap,
        int(mapping_cfg.get("mapping_chunksize", 250_000)),
    )
    coverage = write_batch_lists(project, queries, mappings)

    mapping_csv.parent.mkdir(parents=True, exist_ok=True)
    coverage_csv.parent.mkdir(parents=True, exist_ok=True)
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    mappings.to_csv(mapping_csv, index=False)
    coverage.to_csv(coverage_csv, index=False)

    mapped_ids = set(
        mappings["query_row_id"].astype(int) if not mappings.empty else []
    )
    exact_ids = set(
        mappings.loc[mappings["exact_match"], "query_row_id"].astype(int)
        if not mappings.empty
        else []
    )
    primary_tfs = set(
        cfg.get("regulators", {}).get(
            "primary_passed_all_stage74_gates", []
        )
    )
    primary_coverage = coverage.loc[coverage["tf"].isin(primary_tfs)]
    primary_pass = bool(
        len(primary_coverage) > 0
        and (primary_coverage["n_mapped_query_regions"] > 0).all()
    )

    summary = {
        "stage": "stage75f_cistarget_region_mapping_v2",
        "purpose": (
            "pycisTarget-compatible region-universe mapping audit before "
            "motif enrichment"
        ),
        "not_motif_enrichment": True,
        "not_validated_regulation": True,
        "source_database_kind": source_kind,
        "source_database": str(source_database),
        "fraction_overlap_rule": (
            "overlap_fraction_query > threshold OR "
            "overlap_fraction_database > threshold"
        ),
        "fraction_overlap_threshold": fraction_overlap,
        "n_query_rows": int(len(queries)),
        "n_unique_query_regions": int(
            queries["query_region"].astype(str).nunique()
        ),
        "n_mapped_query_rows": int(
            queries["query_row_id"].isin(mapped_ids).sum()
        ),
        "n_unmapped_query_rows": int(
            (~queries["query_row_id"].isin(mapped_ids)).sum()
        ),
        "n_exact_query_rows": int(
            queries["query_row_id"].isin(exact_ids).sum()
        ),
        "n_mapping_rows": int(len(mappings)),
        "n_unique_mapped_db_regions": int(
            mappings["mapped_db_region"].astype(str).nunique()
            if not mappings.empty
            else 0
        ),
        "primary_batches_have_mapping": primary_pass,
        "index": index_info,
        "scores_rankings_column_parity": parity,
        "batch_coverage": coverage.to_dict(orient="records"),
        "outputs": {
            "mapping_csv": str(mapping_csv.relative_to(project)),
            "coverage_csv": str(coverage_csv.relative_to(project)),
            "summary_json": str(summary_json.relative_to(project)),
            "index_csv_gz": str(index_csv.relative_to(project)),
            "index_manifest_json": str(index_manifest.relative_to(project)),
        },
        "safety": cfg.get("safety", {}),
    }
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Wrote: {mapping_csv}", flush=True)
    print(f"Wrote: {coverage_csv}", flush=True)
    print(f"Wrote: {summary_json}", flush=True)
    print(json.dumps(summary, indent=2), flush=True)

    if not primary_pass:
        print(
            "FAIL: one or more primary-regulator batches have zero mappings",
            flush=True,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
