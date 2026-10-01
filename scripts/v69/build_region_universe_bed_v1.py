#!/usr/bin/env python3
"""V69: emit a route's region universe as a BED file for cisTarget database construction.

The region universe is the ONLY thing that differs between Route A and Route B, so
its identity is pinned by an ORDER-sensitive digest: the cisTarget database indexes
regions positionally, and a reordered BED would silently produce a database whose
rows mean something other than the caller believes.

Region names are written in the SCENIC+ convention `chr:start-end`, which is also
how the depositor spells the submitted peak IDs, so Route-A region names round-trip
to the matrix feature IDs exactly.

Fails closed on: unparseable region IDs, non-positive width, coordinates outside the
declared chromosome lengths, duplicate regions, and contigs absent from the FASTA
index (a region the motif scanner could never score).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def ordered_digest(items) -> str:
    h = hashlib.sha256()
    for i, s in enumerate(items):
        h.update(str(i).encode()); h.update(b"\x1f")
        h.update(str(s).encode()); h.update(b"\x1e")
    return h.hexdigest()


# PROSPECTIVE BOUND, declared before any region universe was emitted. Unplaced
# scaffolds are a negligible share of a 10x peak set; anything above this is a
# systematic contig-naming mismatch and must stop the run, not be absorbed.
MAX_DROPPED_REGION_FRACTION = 0.01


class FailClosed(Exception):
    def __init__(self, status, **detail):
        super().__init__(status)
        self.status = status
        self.detail = detail


def read_fasta_contigs(fasta_gz: Path) -> dict:
    """Contig name -> sequence length, read from a (bgzipped or plain) FASTA."""
    lengths = {}
    name = None
    n = 0
    opener = gzip.open if str(fasta_gz).endswith(".gz") else open
    with opener(fasta_gz, "rt") as fh:
        for line in fh:
            if line.startswith(">"):
                if name is not None:
                    lengths[name] = n
                name = line[1:].split()[0]
                n = 0
            else:
                n += len(line.strip())
    if name is not None:
        lengths[name] = n
    return lengths


def build(feature_table: Path, route_id: str, out_dir: Path,
          contig_lengths: dict, fasta_path: str, fasta_sha256: str,
          allow_contig_restriction: bool = False) -> dict:
    tbl = pd.read_csv(feature_table)
    ids = tbl["id"].astype(str)
    parsed = ids.str.extract(r"^(?P<chrom>[^:]+):(?P<start>\d+)-(?P<end>\d+)$")
    bad = parsed["chrom"].isna()
    if bad.any():
        raise FailClosed("FAIL__REGION_IDS_NOT_PARSEABLE",
                         n_unparseable=int(bad.sum()),
                         first_examples=ids[bad].head(5).tolist())
    df = pd.DataFrame({"chrom": parsed["chrom"],
                       "start": parsed["start"].astype(np.int64),
                       "end": parsed["end"].astype(np.int64)})
    df["name"] = df["chrom"] + ":" + df["start"].astype(str) + "-" + df["end"].astype(str)

    width = (df["end"] - df["start"]).to_numpy()
    if (width <= 0).any():
        raise FailClosed("FAIL__NON_POSITIVE_REGION_WIDTH",
                         n_bad=int((width <= 0).sum()))
    if df["name"].duplicated().any():
        raise FailClosed("FAIL__DUPLICATE_REGIONS",
                         n_duplicated=int(df["name"].duplicated().sum()))

    # Contigs the motif scanner could never score. GSE214979 spells unplaced
    # scaffolds in Ensembl style (GL000194.1) while the UCSC analysis set spells
    # them chrUn_GL000194v1, so they do not resolve. Dropping unplaced scaffolds
    # from a regulatory region universe is standard, but it is recorded here rather
    # than done silently, and it is BOUNDED: a drop larger than
    # MAX_DROPPED_REGION_FRACTION means a systematic naming mismatch rather than a
    # handful of scaffolds, and that must stop the run instead of being absorbed.
    missing_contigs = sorted(set(df["chrom"]) - set(contig_lengths))
    dropped = pd.DataFrame(columns=df.columns)
    if missing_contigs:
        if not allow_contig_restriction:
            raise FailClosed("FAIL__REGION_CONTIGS_ABSENT_FROM_FASTA",
                             missing_contigs=missing_contigs[:20],
                             n_missing_contigs=len(missing_contigs))
        keep = df["chrom"].isin(contig_lengths).to_numpy()
        frac = float((~keep).sum()) / len(df)
        if frac > MAX_DROPPED_REGION_FRACTION:
            raise FailClosed("FAIL__TOO_MANY_REGIONS_ON_CONTIGS_ABSENT_FROM_FASTA",
                             dropped_fraction=frac,
                             max_allowed=MAX_DROPPED_REGION_FRACTION,
                             n_dropped=int((~keep).sum()),
                             missing_contigs=missing_contigs[:20])
        dropped = df.loc[~keep].copy()
        df = df.loc[keep].reset_index(drop=True)
        width = (df["end"] - df["start"]).to_numpy()
    clen = df["chrom"].map(contig_lengths).to_numpy()
    over = df["end"].to_numpy() > clen
    if over.any():
        raise FailClosed("FAIL__REGION_END_BEYOND_CONTIG_LENGTH",
                         n_over=int(over.sum()),
                         first_examples=df.loc[over, "name"].head(5).tolist())

    out_dir.mkdir(parents=True, exist_ok=True)
    bed = out_dir / ("V69_%s_REGION_UNIVERSE.bed" % route_id)
    df[["chrom", "start", "end", "name"]].to_csv(
        bed, sep="\t", header=False, index=False)

    return {
        "schema": "V69_REGION_UNIVERSE_V1",
        "route_id": route_id,
        "built_utc": utcnow(),
        "source_feature_table": str(feature_table),
        "source_feature_table_sha256": sha256_file(feature_table),
        "n_regions": int(len(df)),
        "n_contigs": int(df["chrom"].nunique()),
        "contigs": sorted(set(df["chrom"].tolist())),
        "region_width": {"min": int(width.min()), "median": float(np.median(width)),
                         "mean": float(width.mean()), "max": int(width.max()),
                         "total_bp": int(width.sum())},
        "coordinate_convention": "BED half-open 0-based start, end exclusive, as spelled by the source feature IDs",
        "genome_build": "GRCh38",
        "reference_fasta": {"path": fasta_path, "sha256": fasta_sha256},
        "bed_path": str(bed),
        "bed_sha256": sha256_file(bed),
        "contig_restriction": {
            "applied": bool(len(dropped)),
            "allowed_by_caller": bool(allow_contig_restriction),
            "max_dropped_fraction_allowed": MAX_DROPPED_REGION_FRACTION,
            "n_regions_dropped": int(len(dropped)),
            "dropped_fraction": float(len(dropped) / (len(df) + len(dropped)))
            if (len(df) + len(dropped)) else 0.0,
            "contigs_absent_from_reference": missing_contigs,
            "reason": ("These regions lie on unplaced scaffolds that the reference "
                       "FASTA does not contain under the source's spelling "
                       "(GSE214979 uses Ensembl-style GL000194.1; the UCSC analysis "
                       "set uses chrUn_GL000194v1). A motif scanner could never score "
                       "them. They are DROPPED and COUNTED, never silently retained "
                       "with an unscoreable sequence."),
            "dropped_regions": dropped["name"].tolist()[:200],
            "semantics": "DROPPED regions are STRUCTURALLY_UNSCOREABLE, not biological absence.",
        },
        "ordered_region_digest": ordered_digest(df["name"].tolist()),
        "unordered_region_digest": ordered_digest(sorted(df["name"].tolist())),
        "why_ordered_digest": ("The cisTarget database indexes regions positionally. A "
                               "membership-only digest cannot detect a reordered BED, "
                               "which would yield a database whose rows mean something "
                               "other than the caller believes."),
        "status": "PASS__REGION_UNIVERSE_BUILT",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feature-table", required=True)
    ap.add_argument("--route-id", required=True)
    ap.add_argument("--fasta", required=True)
    ap.add_argument("--fasta-sha256", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--allow-contig-restriction", action="store_true",
                    help="Drop and COUNT regions on contigs absent from the reference "
                         "FASTA, up to MAX_DROPPED_REGION_FRACTION. Without this flag "
                         "any absent contig is a hard stop.")
    a = ap.parse_args(argv)
    try:
        contigs = read_fasta_contigs(Path(a.fasta))
        r = build(Path(a.feature_table), a.route_id, Path(a.out_dir),
                  contigs, a.fasta, a.fasta_sha256,
                  allow_contig_restriction=a.allow_contig_restriction)
    except FailClosed as e:
        r = {"schema": "V69_REGION_UNIVERSE_V1", "status": e.status, **e.detail}
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps(r, indent=2)[:3000])
    return 0 if str(r["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
