#!/usr/bin/env python3
"""Build the V65 annotation-first dual promoter ledger.

GENCODE defines existence. Evidence layers annotate only.

Outputs:
1) transcript/promoter-isoform ledger: one row per GENCODE transcript record;
2) exact-TSS ledger: one row per unique gene_id × chromosome × strand × exact TSS;
3) transcript->TSS membership: deterministic one-to-one mapping for every transcript row.

SCREEN/FANTOM are coordinate evidence. Dong Data 7 is transcript/promoter-isoform
evidence and joins chromosome-aware. No evidence source may delete a GENCODE row.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "scripts/v64/build_promoter_candidate_ledger_v1.py"


def _load_v1():
    spec = importlib.util.spec_from_file_location("promoter_v1", V1)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load V1 promoter helpers")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tss_id(g: dict) -> str:
    return f'GENCODE50:TSS:{g["gene_id"]}:{g["chrom"]}:{g["tss_1based"]}:{g["strand"]}'


def fantom_same_strand_hits(v1, index, starts, chrom: str, pos1: int, strand: str):
    """FANTOM CAGE evidence is strand-aware.

    load_bed_index stores BED columns 4+ in tuple element 2. For BED9,
    extras[2] is the BED strand (original column 6).
    """
    hits = v1.point_hits(index, starts, chrom, pos1)
    out = []
    for h in hits:
        extras = h[2]
        if len(extras) < 3:
            raise ValueError("FANTOM BED row lacks strand column")
        if extras[2] == strand:
            out.append(h)
    return out


def build(args) -> dict:
    v1 = _load_v1()
    screen_idx, screen_starts = v1.load_bed_index(args.screen_pls)
    if args.fantom_bed:
        fantom_idx, fantom_starts = v1.load_bed_index(args.fantom_bed)
    else:
        fantom_idx = fantom_starts = None

    if args.dong_data7:
        dong_by_key, dong_any_tid, dong_multiplicity = v1.load_dong_data7(args.dong_data7)
    else:
        dong_by_key, dong_any_tid, dong_multiplicity = {}, set(), {}

    for p in (args.transcript_output, args.tss_output, args.membership_output, args.receipt):
        p.parent.mkdir(parents=True, exist_ok=True)

    transcript_fields = [
        "candidate_promoter_id","exact_tss_id","transcript_id","gene_id","gene_name",
        "transcript_type","chrom","tss_1based","strand",
        "screen_pls_overlap","screen_pls_count",
        "dong_transcript_id_present_any","dong_same_chrom_present","dong_gene_match",
        "dong_coordinate_match","dong_internal_promoter","dong_fivemost",
        "fantom_cage_overlap","fantom_cage_count",
    ]
    membership_fields = [
        "candidate_promoter_id","transcript_id","gene_id","exact_tss_id",
        "chrom","tss_1based","strand"
    ]

    tss = {}
    transcript_n = 0
    genes = set()

    with gzip.open(args.transcript_output, "wt", newline="", encoding="utf-8") as tfh, \
         gzip.open(args.membership_output, "wt", newline="", encoding="utf-8") as mfh:
        tw = csv.DictWriter(tfh, fieldnames=transcript_fields, delimiter="\t")
        mw = csv.DictWriter(mfh, fieldnames=membership_fields, delimiter="\t")
        tw.writeheader(); mw.writeheader()

        for g in v1.load_gencode(args.gencode_gtf):
            transcript_n += 1
            genes.add(g["gene_id"])
            xid = tss_id(g)
            sh = v1.point_hits(screen_idx, screen_starts, g["chrom"], g["tss_1based"])
            fhits = (
                fantom_same_strand_hits(
                    v1, fantom_idx, fantom_starts,
                    g["chrom"], g["tss_1based"], g["strand"]
                )
                if fantom_idx is not None else []
            )
            dong_any = int(g["transcript_id"] in dong_any_tid)
            d = dong_by_key.get((g["transcript_id"], g["chrom"]))
            row = {
                **g,
                "exact_tss_id": xid,
                "screen_pls_overlap": int(bool(sh)),
                "screen_pls_count": len(sh),
                "dong_transcript_id_present_any": dong_any,
                "dong_same_chrom_present": int(d is not None),
                "dong_gene_match": int(bool(d and d["dong_gene_id"] == g["gene_id"])),
                "dong_coordinate_match": int(bool(
                    d and d["dong_gene_id"] == g["gene_id"]
                    and d["dong_tss_1based"] == g["tss_1based"]
                    and d["dong_strand"] == g["strand"]
                )),
                "dong_internal_promoter": "" if d is None else int(d["dong_internal_promoter"]),
                "dong_fivemost": "" if d is None else int(d["dong_fivemost"]),
                "fantom_cage_overlap": "" if fantom_idx is None else int(bool(fhits)),
                "fantom_cage_count": "" if fantom_idx is None else len(fhits),
            }
            tw.writerow({k: row[k] for k in transcript_fields})
            mw.writerow({k: row[k] for k in membership_fields})

            if xid not in tss:
                tss[xid] = {
                    "exact_tss_id": xid,
                    "gene_id": g["gene_id"],
                    "gene_name": g["gene_name"],
                    "chrom": g["chrom"],
                    "tss_1based": g["tss_1based"],
                    "strand": g["strand"],
                    "transcript_count": 0,
                    "screen_pls_overlap": int(bool(sh)),
                    "screen_pls_count": len(sh),
                    "fantom_cage_overlap": "" if fantom_idx is None else int(bool(fhits)),
                    "fantom_cage_count": "" if fantom_idx is None else len(fhits),
                    "dong_transcripts_present_any": 0,
                    "dong_same_chrom_transcripts": 0,
                    "dong_coordinate_match_transcripts": 0,
                }
            x = tss[xid]
            x["transcript_count"] += 1
            x["dong_transcripts_present_any"] += dong_any
            x["dong_same_chrom_transcripts"] += int(d is not None)
            x["dong_coordinate_match_transcripts"] += row["dong_coordinate_match"]

    tss_fields = [
        "exact_tss_id","gene_id","gene_name","chrom","tss_1based","strand",
        "transcript_count","screen_pls_overlap","screen_pls_count",
        "fantom_cage_overlap","fantom_cage_count",
        "dong_transcripts_present_any","dong_same_chrom_transcripts",
        "dong_coordinate_match_transcripts",
    ]
    with gzip.open(args.tss_output, "wt", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=tss_fields, delimiter="\t")
        w.writeheader()
        for xid in sorted(tss):
            w.writerow({k: tss[xid][k] for k in tss_fields})

    receipt = {
        "schema": "V65_PROMOTER_DUAL_LEDGER_RECEIPT_V1",
        "candidate_authority": "GENCODE_V50_GRCH38_P14",
        "transcript_promoter_records": transcript_n,
        "exact_tss_loci": len(tss),
        "genes": len(genes),
        "denominator_rule": "Evidence annotates GENCODE candidates and never removes them.",
        "fantom_coordinate_rule": "GENCODE TSS point must overlap a FANTOM hg38 peak on the SAME strand.",
        "keys": {
            "transcript": "gene_id + transcript_id + chromosome + strand + exact TSS + release",
            "exact_tss": "gene_id + chromosome + strand + exact TSS",
            "dong_join": "transcript_id + chromosome",
        },
        "dong_duplicate_transcript_ids": sum(1 for v in dong_multiplicity.values() if v > 1),
        "inputs": {
            "gencode_gtf": {"path": str(args.gencode_gtf), "sha256": sha256_file(args.gencode_gtf)},
            "screen_pls": {"path": str(args.screen_pls), "sha256": sha256_file(args.screen_pls)},
            "dong_data7": None if not args.dong_data7 else {
                "path": str(args.dong_data7), "sha256": sha256_file(args.dong_data7)},
            "fantom_bed": None if not args.fantom_bed else {
                "path": str(args.fantom_bed), "sha256": sha256_file(args.fantom_bed)},
        },
        "outputs": {
            "transcript_ledger": {"path": str(args.transcript_output), "sha256": sha256_file(args.transcript_output)},
            "exact_tss_ledger": {"path": str(args.tss_output), "sha256": sha256_file(args.tss_output)},
            "membership": {"path": str(args.membership_output), "sha256": sha256_file(args.membership_output)},
        },
        "governance": {
            "training": "OFF",
            "promoter_selection_executed": False,
            "biological_correspondence_opened": False,
        },
    }
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gencode-gtf", type=Path, required=True)
    ap.add_argument("--screen-pls", type=Path, required=True)
    ap.add_argument("--dong-data7", type=Path)
    ap.add_argument("--fantom-bed", type=Path)
    ap.add_argument("--transcript-output", type=Path, required=True)
    ap.add_argument("--tss-output", type=Path, required=True)
    ap.add_argument("--membership-output", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args(argv)
    print(json.dumps(build(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
