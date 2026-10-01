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
import bisect
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


def load_bed_index_robust(path: Path):
    """Return intervals, sorted starts, and prefix-max ends for correct point queries.

    A backward scan may stop only when the maximum end among all earlier intervals is
    <= the query point. Stopping at the first non-overlapping prior interval is wrong
    for nested BED intervals and undercounts FANTOM CAGE support.
    """
    from collections import defaultdict
    arr = defaultdict(list)
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 3:
                continue
            arr[p[0]].append((int(p[1]), int(p[2]), p[3:]))
    starts = {}
    prefix_max_end = {}
    for chrom, xs in arr.items():
        xs.sort(key=lambda x: (x[0], x[1]))
        starts[chrom] = [x[0] for x in xs]
        cur = -1
        pm = []
        for _start, end, _extras in xs:
            cur = max(cur, end)
            pm.append(cur)
        prefix_max_end[chrom] = pm
    return arr, starts, prefix_max_end


def point_hits_robust(index, starts, prefix_max_end, chrom: str, pos1: int):
    x = pos1 - 1
    xs = index.get(chrom, [])
    ss = starts.get(chrom, [])
    pm = prefix_max_end.get(chrom, [])
    j = bisect.bisect_right(ss, x) - 1
    out = []
    while j >= 0 and pm[j] > x:
        if xs[j][0] <= x < xs[j][1]:
            out.append(xs[j])
        j -= 1
    return out


def tss_id(g: dict) -> str:
    return f'GENCODE50:TSS:{g["gene_id"]}:{g["chrom"]}:{g["tss_1based"]}:{g["strand"]}'


def fantom_same_strand_hits(index, starts, prefix_max_end, chrom: str, pos1: int, strand: str):
    """FANTOM CAGE evidence is strand-aware and uses robust nested-interval queries.

    load_bed_index_robust stores BED columns 4+ in tuple element 2. For BED9,
    extras[2] is the BED strand (original column 6).
    """
    hits = point_hits_robust(index, starts, prefix_max_end, chrom, pos1)
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
    screen_idx, screen_starts, screen_pmax = load_bed_index_robust(args.screen_pls)
    if args.fantom_bed:
        fantom_idx, fantom_starts, fantom_pmax = load_bed_index_robust(args.fantom_bed)
    else:
        fantom_idx = fantom_starts = fantom_pmax = None

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
        "fantom_cage_overlap","fantom_cage_count","fantom_representative_tss_exact",
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
            sh = point_hits_robust(
                screen_idx, screen_starts, screen_pmax, g["chrom"], g["tss_1based"]
            )
            fhits = (
                fantom_same_strand_hits(
                    fantom_idx, fantom_starts, fantom_pmax,
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
                "fantom_representative_tss_exact": (
                    "" if fantom_idx is None else int(any(
                        len(h[2]) >= 4 and int(h[2][3]) == g["tss_1based"] - 1
                        for h in fhits
                    ))
                ),
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
                    "fantom_representative_tss_exact": row["fantom_representative_tss_exact"],
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
        "fantom_cage_overlap","fantom_cage_count","fantom_representative_tss_exact",
        "dong_transcripts_present_any","dong_same_chrom_transcripts",
        "dong_coordinate_match_transcripts",
    ]
    with gzip.open(args.tss_output, "wt", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=tss_fields, delimiter="\t")
        w.writeheader()
        for xid in sorted(tss):
            w.writerow({k: tss[xid][k] for k in tss_fields})

    screen_tss = sum(int(x["screen_pls_overlap"]) for x in tss.values())
    fantom_tss = sum(int(x["fantom_cage_overlap"]) for x in tss.values()) if fantom_idx is not None else None
    fantom_exact_tss = (
        sum(int(x["fantom_representative_tss_exact"]) for x in tss.values())
        if fantom_idx is not None else None
    )
    joint = {"screen_and_fantom": 0, "screen_only": 0, "fantom_only": 0, "neither": 0}
    if fantom_idx is not None:
        for x in tss.values():
            sc = bool(int(x["screen_pls_overlap"]))
            fc = bool(int(x["fantom_cage_overlap"]))
            joint[
                "screen_and_fantom" if sc and fc else
                "screen_only" if sc else
                "fantom_only" if fc else
                "neither"
            ] += 1

    receipt = {
        "schema": "V65_PROMOTER_DUAL_LEDGER_RECEIPT_V1",
        "candidate_authority": "GENCODE_V50_GRCH38_P14",
        "transcript_promoter_records": transcript_n,
        "exact_tss_loci": len(tss),
        "genes": len(genes),
        "exact_tss_evidence_coverage": {
            "screen_pls_overlap": screen_tss,
            "fantom_same_strand_overlap": fantom_tss,
            "fantom_exact_representative_tss": fantom_exact_tss,
            "screen_fantom_joint_states": joint if fantom_idx is not None else None,
        },
        "denominator_rule": "Evidence annotates GENCODE candidates and never removes them.",
        "fantom_coordinate_rule": "GENCODE TSS point must overlap a FANTOM hg38 peak on the SAME strand.",
        "interval_query_rule": "Point overlap uses sorted starts plus prefix-max interval ends; nested intervals cannot be hidden by a shorter later-starting interval.",
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
