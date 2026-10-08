#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path

import pandas as pd

SQLITE_REL = "metadata/foundation_metadata_rows.sqlite"
QUERY_MAP = {
    "FIT_SOURCE": """select source,count(*) cells,count(distinct donor_id) donors,count(distinct matrix_id) operators,count(distinct native_class) native_classes,count(distinct broad_class) broad_classes,count(distinct support_fingerprint) support_fingerprints from cells where partition='reader_fit' group by source order by source""",
    "PARTITION_SOURCE": """select partition,source,count(*) cells,count(distinct donor_id) donors,count(distinct matrix_id) operators,count(distinct native_class) native_classes,count(distinct broad_class) broad_classes from cells group by partition,source order by partition,source""",
    "FIT_DONOR": """select source,donor_id,count(*) cells,count(distinct matrix_id) operators,count(distinct native_class) native_classes,count(distinct broad_class) broad_classes from cells where partition='reader_fit' group by source,donor_id order by source,donor_id""",
    "FIT_OPERATOR_NATIVE_CLASS": """select source,operator_index,matrix_id,native_class,count(*) cells from cells where partition='reader_fit' group by source,operator_index,matrix_id,native_class order by operator_index,cells desc""",
    "DONOR_PARTITION_SOURCE": "select distinct donor_id,partition,source from cells order by donor_id",
    "FIT_BROAD_MISSING": """select source,sum(case when broad_class is null or trim(broad_class)='' then 1 else 0 end) missing_broad,count(*) cells from cells where partition='reader_fit' group by source order by source""",
    "FIT_SUPPORT_FINGERPRINT": """select source,support_fingerprint,count(*) cells,count(distinct donor_id) donors,count(distinct matrix_id) operators,count(distinct native_class) native_classes from cells where partition='reader_fit' group by source,support_fingerprint order by source,cells desc""",
    "SEA_AD_FIT_DONOR_REGION": """select donor_id,matrix_id,count(*) cells,count(distinct native_class) native_classes from cells where partition='reader_fit' and source='SEA_AD' group by donor_id,matrix_id order by donor_id,matrix_id""",
    "FIT_DONOR_NATIVE_CLASS": """select source,donor_id,native_class,count(*) cells from cells where partition='reader_fit' group by source,donor_id,native_class order by source,donor_id,native_class""",
    "FIT_NATIVE_CLASS_COVERAGE": """select source,native_class,count(*) cells,count(distinct donor_id) donors,count(distinct matrix_id) operators from cells where partition='reader_fit' group by source,native_class order by source,native_class""",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(32 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def expected_sqlite_sha(bundle_root: Path) -> str:
    manifest = pd.read_csv(bundle_root / "BUNDLE_SHA256_MANIFEST.csv")
    rows = manifest.loc[manifest.path == SQLITE_REL]
    if len(rows) != 1:
        raise SystemExit(f"manifest must contain exactly one {SQLITE_REL}")
    return str(rows.iloc[0].sha256).lower()


def write_manifest(out_dir: Path) -> None:
    rows = []
    for query_id in sorted(QUERY_MAP):
        path = out_dir / f"{query_id}.csv"
        if not path.is_file():
            continue
        frame = pd.read_csv(path)
        rows.append({
            "query_id": query_id,
            "path": path.name,
            "rows": int(len(frame)),
            "bytes": int(path.stat().st_size),
            "sha256": sha256(path),
        })
    pd.DataFrame(rows).to_csv(
        out_dir / "FULL104_DATASET_ETL_SQL_AGGREGATE_SHA256.csv",
        index=False,
        lineterminator="\n",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle-root", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--query-id", action="append", choices=(*QUERY_MAP, "ALL"), required=True)
    args = ap.parse_args()
    root = args.bundle_root.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    db = root / SQLITE_REL
    if not db.is_file():
        raise SystemExit(f"missing {db}")
    expected = expected_sqlite_sha(root)
    observed = sha256(db)
    if observed != expected:
        raise SystemExit(f"SQLite SHA mismatch {observed} != {expected}")

    requested = list(QUERY_MAP) if "ALL" in args.query_id else list(dict.fromkeys(args.query_id))
    con = sqlite3.connect(db)
    try:
        for query_id in requested:
            frame = pd.read_sql_query(QUERY_MAP[query_id], con)
            frame.to_csv(out / f"{query_id}.csv", index=False, lineterminator="\n")
            print(f"{query_id}: rows={len(frame)} sha256={sha256(out / (query_id + '.csv'))}")
    finally:
        con.close()
    write_manifest(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
