#!/usr/bin/env python3
"""Authenticate the exact GSE73721 processed expression artifact for V64 P3.

This script DOES NOT define an expression threshold and DOES NOT execute P3.
It only establishes byte/schema/sample authority for the exact GEO supplementary
file already identified prospectively:

    GSE73721_Human_and_mouse_table.csv.gz

Required GEO myeloid sample identities:
    GSM1901339  45yo ctx myeloid
    GSM1901340  51yo ctx myeloid
    GSM1901341  63 yo ctx myeloid

Fail closed: do not substitute a mirror/reprocessed export or infer columns from
position if the exact sample identities cannot be established from the artifact.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import sys

EXPECTED_BASENAME = "GSE73721_Human_and_mouse_table.csv.gz"
GEO = "GSE73721"
MYELOID_GSM = ["GSM1901339", "GSM1901340", "GSM1901341"]
MYELOID_TITLES = ["45yo ctx myeloid", "51yo ctx myeloid", "63 yo ctx myeloid"]


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip()).lower()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if os.path.basename(a.file) != EXPECTED_BASENAME:
        raise SystemExit(
            f"STOP_WRONG_FILE_NAME got={os.path.basename(a.file)!r} "
            f"expected={EXPECTED_BASENAME!r}"
        )
    if os.path.exists(a.out):
        raise SystemExit("STOP_OUTPUT_EXISTS")

    digest = sha256(a.file)
    n_bytes = os.path.getsize(a.file)

    # gzip integrity + CSV parsing. Preserve the raw first rows in the receipt;
    # do not guess schema from a third-party reprocessed copy.
    try:
        with gzip.open(a.file, "rt", newline="", encoding="utf-8-sig") as fh:
            reader = csv.reader(fh)
            rows = []
            for _, row in zip(range(12), reader):
                rows.append(row)
    except Exception as e:
        raise SystemExit(f"STOP_GZIP_OR_CSV_INVALID {type(e).__name__}: {e}")

    if not rows:
        raise SystemExit("STOP_EMPTY_PROCESSED_FILE")

    width = max(len(r) for r in rows)
    flat = [str(x) for r in rows for x in r]
    flat_norm = [norm(x) for x in flat]

    gsm_hits = {
        gsm: [x for x in flat if gsm.lower() in str(x).lower()]
        for gsm in MYELOID_GSM
    }
    title_hits = {
        title: [x for x in flat if norm(title) in norm(x)]
        for title in MYELOID_TITLES
    }

    # Also expose every early cell containing "myeloid" or "microgl" so a
    # schema that labels condition rather than GSM can be adjudicated explicitly.
    myeloid_like = sorted({
        x for x in flat
        if "myeloid" in norm(x) or "microgl" in norm(x) or "macroph" in norm(x)
    })

    exact_gsms_visible = all(bool(gsm_hits[g]) for g in MYELOID_GSM)
    exact_titles_visible = all(bool(title_hits[t]) for t in MYELOID_TITLES)

    # Candidate gene-key labels only; do not select one silently.
    gene_key_candidates = sorted({
        x for x in flat
        if norm(x) in {
            "gene_symbol", "gene symbol", "gene", "symbol",
            "ensembl", "ensembl_gene_id", "entrez", "entrez id",
            "gene_id", "gene id"
        }
    })

    receipt = {
        "schema": "V64_P3_GSE73721_EXACT_FILE_AUTHENTICATION_V1",
        "date": "2026-09-29",
        "status": "BYTE_AUTHENTICATED_SCHEMA_RECORDED__P3_THRESHOLD_NOT_FROZEN",
        "source": {
            "geo": GEO,
            "expected_file": EXPECTED_BASENAME,
            "path": os.path.abspath(a.file),
            "bytes": n_bytes,
            "sha256": digest
        },
        "gzip_csv": {
            "valid": True,
            "first_rows": rows,
            "max_width_first_rows": width
        },
        "required_myeloid_identity": {
            "GSMs": MYELOID_GSM,
            "titles": MYELOID_TITLES,
            "gsm_hits_in_first_rows": gsm_hits,
            "title_hits_in_first_rows": title_hits,
            "myeloid_like_cells_first_rows": myeloid_like,
            "all_three_GSMs_visible_in_first_rows": exact_gsms_visible,
            "all_three_titles_visible_in_first_rows": exact_titles_visible
        },
        "gene_key_candidates_first_rows": gene_key_candidates,
        "governance": {
            "expression_threshold_defined": False,
            "P3_executed": False,
            "substitute_file_allowed": False,
            "project_RNA_used": False,
            "NIH_CARD_used": False,
            "Morabito_used": False
        },
        "next_gate": (
            "After this receipt is reviewed, prospectively freeze the exact gene-key "
            "join and microglial expression/detection rule BEFORE computing P3 "
            "candidate attrition. If the exact myeloid sample identities are not "
            "recoverable from this artifact, STOP and adjudicate schema; do not infer "
            "sample columns by position."
        )
    }

    with open(a.out, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print(json.dumps({
        "file": EXPECTED_BASENAME,
        "bytes": n_bytes,
        "sha256": digest,
        "all_three_GSMs_visible_first_rows": exact_gsms_visible,
        "all_three_titles_visible_first_rows": exact_titles_visible,
        "myeloid_like_cells_first_rows": myeloid_like,
        "gene_key_candidates_first_rows": gene_key_candidates
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
