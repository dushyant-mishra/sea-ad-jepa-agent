#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def read_intervals(path: Path):
    with open(path, newline="") as fh:
        rows=list(csv.DictReader(fh))
    out=[]
    for i,r in enumerate(rows):
        out.append({
            "index":i,
            "chrom":r["chrom"],
            "start":int(r["start"]),
            "end":int(r["end"]),
            "id":r.get("id") or r.get("window_id") or r.get("peak_id") or f"ROW{i}",
        })
    return out


def all_overlaps(query, target):
    by_chrom=defaultdict(list)
    for t in target:
        by_chrom[t["chrom"]].append(t)
    rows=[]
    for q in query:
        hits=[]
        for t in by_chrom.get(q["chrom"], []):
            overlap=max(0, min(q["end"],t["end"]) - max(q["start"],t["start"]))
            if overlap > 0:
                hits.append((t,overlap))
        for t,overlap in hits:
            rows.append({
                "query_id":q["id"],
                "target_id":t["id"],
                "overlap_bp":overlap,
                "query_fraction":overlap/max(q["end"]-q["start"],1),
                "target_fraction":overlap/max(t["end"]-t["start"],1),
            })
    return rows


def write_crosswalk(query_path: Path, target_path: Path, out_path: Path):
    q=read_intervals(query_path)
    t=read_intervals(target_path)
    rows=all_overlaps(q,t)
    out_path.parent.mkdir(parents=True,exist_ok=True)
    with open(out_path,"w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=[
            "query_id","target_id","overlap_bp","query_fraction","target_fraction"])
        w.writeheader(); w.writerows(rows)
    per_query=defaultdict(int)
    for r in rows: per_query[r["query_id"]]+=1
    return {
        "schema":"V72_ALL_OVERLAPS_CROSSWALK_RECEIPT_V1",
        "query_rows":len(q),
        "target_rows":len(t),
        "overlap_pairs":len(rows),
        "queries_with_multiple_targets":sum(v>1 for v in per_query.values()),
        "max_targets_per_query":max(per_query.values(),default=0),
        "first_hit_only_forbidden":True,
        "status":"PASS__ALL_OVERLAPS_ENUMERATED",
    }


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--query",required=True)
    ap.add_argument("--target",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args(argv)
    print(json.dumps(write_crosswalk(Path(a.query),Path(a.target),Path(a.out)),indent=2))


if __name__=="__main__":
    main()
