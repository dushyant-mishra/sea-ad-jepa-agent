#!/usr/bin/env python3
"""Convert paired synthetic ATAC counts into deterministic 10x-style fragment shards.

Each nonzero cell-region entry becomes one BED-like fragment row:
  chrom  start  end  barcode  multiplicity
The fifth column carries the synthetic count, avoiding count-times row explosion while
retaining fragment multiplicity. Output gzip headers are normalized (mtime=0, no filename)
so identical logical inputs produce identical bytes.

This producer reads only model-facing paired-multiome output. It never opens hidden truth.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path

import numpy as np


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def deterministic_gzip_text(path: Path):
    raw = open(path, "wb")
    gz = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    text = io.TextIOWrapper(gz, encoding="utf-8", newline="\n")
    return raw, gz, text


def build(root: Path) -> dict:
    multi = root / "observable_raw" / "PAIRED_MULTIOME_like_sharded"
    out = root / "observable_raw" / "PAIRED_MULTIOME_fragments"
    out.mkdir(parents=True, exist_ok=True)
    mm = json.loads((multi / "PAIRED_MULTIOME_SHARDED_MANIFEST.json").read_text())
    shards = []
    total_rows = 0
    total_multiplicity = 0

    for s in mm["shards"]:
        p = multi / s["file"]
        if sha256_file(p) != s["sha256"]:
            raise RuntimeError("paired-multiome shard digest mismatch: " + s["file"])
        z = np.load(p, allow_pickle=False)
        counts = z["atac_counts"]
        chrom = z["atac_region_chrom"]
        start = z["atac_region_start"]
        end = z["atac_region_end"]
        ids = z["global_cell_index"]
        cell_ids = z["cell_id"]
        if counts.shape != (len(start), len(ids)):
            raise RuntimeError("ATAC shape does not match region/cell axes")

        fp = out / f"FRAGMENTS_{int(ids[0]):09d}_{int(ids[-1])+1:09d}.tsv.gz"
        raw, gz, text = deterministic_gzip_text(fp)
        rows = 0
        multiplicity = 0
        try:
            # Cell-major then region-major ordering is frozen and shard-order independent.
            for j in range(len(ids)):
                nz = np.flatnonzero(counts[:, j] > 0)
                barcode = str(cell_ids[j])
                for r in nz:
                    c = int(counts[r, j])
                    text.write(f"{chrom[r]}\t{int(start[r])}\t{int(end[r])}\t{barcode}\t{c}\n")
                    rows += 1
                    multiplicity += c
        finally:
            text.flush()
            text.close()
            # TextIOWrapper closes gz and raw; explicit guards make intent clear.
            if not gz.closed:
                gz.close()
            if not raw.closed:
                raw.close()
        shards.append(dict(
            start=int(ids[0]), stop=int(ids[-1]) + 1,
            file=fp.name, sha256=sha256_file(fp),
            rows=rows, multiplicity=multiplicity,
            source_multiome_file=s["file"], source_multiome_sha256=s["sha256"],
        ))
        total_rows += rows
        total_multiplicity += multiplicity

    manifest = dict(
        schema="V73_SYNTHETIC_FRAGMENT_MANIFEST_V1",
        format="10x-style five-column fragments: chrom,start,end,barcode,multiplicity",
        deterministic_gzip=dict(mtime=0, filename_header="empty"),
        ordering="global-cell-major then region-major within each shard",
        hidden_truth_read=False,
        source_manifest="PAIRED_MULTIOME_SHARDED_MANIFEST.json",
        n_cells=mm["n_cells"],
        total_rows=total_rows,
        total_multiplicity=total_multiplicity,
        shards=shards,
    )
    mp = out / "SYNTHETIC_FRAGMENT_MANIFEST.json"
    mp.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    a = ap.parse_args()
    m = build(Path(a.root))
    print(json.dumps(dict(status="PASS", rows=m["total_rows"], multiplicity=m["total_multiplicity"], shards=len(m["shards"])), indent=2))


if __name__ == "__main__":
    main()
