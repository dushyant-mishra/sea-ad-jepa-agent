#!/usr/bin/env python3
"""Build an annotation-first GENCODE gene×TSS candidate universe.

Scientific semantics:
- GTF transcript features define candidate TSSs.
- Coordinates are preserved in both GTF 1-based and BED 0-based form.
- Transcripts sharing an exact TSS within one versioned gene collapse to one
  candidate TSS while transcript membership remains explicit.
- No activity/CAGE/ATAC evidence can remove candidates here.
- No promoter interval width is invented.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def parse_attrs(raw: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for field in raw.strip().strip(";").split(";"):
        field=field.strip()
        if not field:
            continue
        if " " not in field:
            raise ValueError(f"malformed GTF attribute field: {field!r}")
        key,val=field.split(" ",1)
        val=val.strip()
        if len(val)>=2 and val[0]=='"' and val[-1]=='"':
            val=val[1:-1]
        out[key].append(val)
    return dict(out)


def one(attrs: dict[str,list[str]], key: str, *, required: bool=True) -> str|None:
    vals=attrs.get(key,[])
    if not vals:
        if required:
            raise ValueError(f"missing required attribute {key}")
        return None
    if len(set(vals)) != 1:
        raise ValueError(f"attribute {key} has conflicting values: {vals!r}")
    return vals[0]


def base_id(versioned: str) -> str:
    return versioned.split(".",1)[0]


def iter_transcripts(path: Path):
    opener=gzip.open if path.suffix==".gz" else open
    with opener(path,"rt",encoding="utf-8") as fh:
        for line_no,raw in enumerate(fh,1):
            if not raw.strip() or raw.startswith("#"):
                continue
            parts=raw.rstrip("\n").split("\t")
            if len(parts)!=9:
                raise ValueError(f"line {line_no}: expected 9 GTF fields")
            chrom,source,feature,start,end,score,strand,frame,attr_raw=parts
            if feature!="transcript":
                continue
            if strand not in {"+","-"}:
                raise ValueError(f"line {line_no}: unsupported strand {strand!r}")
            start1,end1=int(start),int(end)
            if start1<1 or end1<start1:
                raise ValueError(f"line {line_no}: invalid coordinates")
            attrs=parse_attrs(attr_raw)
            gid=one(attrs,"gene_id")
            tid=one(attrs,"transcript_id")
            gname=one(attrs,"gene_name",required=False)
            gtype=one(attrs,"gene_type",required=False)
            ttype=one(attrs,"transcript_type",required=False)
            # GTF is 1-based inclusive. BED single-base TSS coordinate is 0-based.
            tss1=start1 if strand=="+" else end1
            tss0=tss1-1
            yield {
                "chrom":chrom,
                "strand":strand,
                "gtf_start_1based":start1,
                "gtf_end_1based":end1,
                "tss_1based":tss1,
                "tss_0based":tss0,
                "gene_id":gid,
                "gene_id_base":base_id(gid),
                "gene_name":gname or "",
                "gene_type":gtype or "",
                "transcript_id":tid,
                "transcript_id_base":base_id(tid),
                "transcript_type":ttype or "",
                "source":source,
            }


def stable_candidate_id(gene_id: str, chrom: str, strand: str, tss0: int) -> str:
    raw=f"GENCODE50|{gene_id}|{chrom}|{strand}|{tss0}".encode()
    return "GC50TSS_"+hashlib.sha256(raw).hexdigest()[:20]


def build(path: Path):
    groups: dict[tuple[str,str,str,int],dict] = {}
    tx_count=0
    gene_ids=set()
    gene_types=Counter()
    transcript_types=Counter()
    for row in iter_transcripts(path):
        tx_count+=1
        gene_ids.add(row["gene_id"])
        if row["gene_type"]:
            gene_types[row["gene_type"]]+=1
        if row["transcript_type"]:
            transcript_types[row["transcript_type"]]+=1
        key=(row["gene_id"],row["chrom"],row["strand"],row["tss_0based"])
        g=groups.get(key)
        if g is None:
            g={
                "candidate_promoter_id":stable_candidate_id(*key),
                "gene_id":row["gene_id"],
                "gene_id_base":row["gene_id_base"],
                "gene_name":row["gene_name"],
                "gene_type":row["gene_type"],
                "chrom":row["chrom"],
                "strand":row["strand"],
                "tss_0based":row["tss_0based"],
                "tss_1based":row["tss_1based"],
                "transcript_ids":[],
                "transcript_id_bases":[],
                "transcript_types":set(),
            }
            groups[key]=g
        else:
            if g["gene_name"] != row["gene_name"] or g["gene_type"] != row["gene_type"]:
                raise ValueError(f"conflicting gene metadata within candidate {key!r}")
        g["transcript_ids"].append(row["transcript_id"])
        g["transcript_id_bases"].append(row["transcript_id_base"])
        if row["transcript_type"]:
            g["transcript_types"].add(row["transcript_type"])
    rows=[]
    for key,g in groups.items():
        g["transcript_ids"]=sorted(set(g["transcript_ids"]))
        g["transcript_id_bases"]=sorted(set(g["transcript_id_bases"]))
        g["transcript_types"]=sorted(g["transcript_types"])
        g["n_transcripts_at_tss"]=len(g["transcript_ids"])
        rows.append(g)
    rows.sort(key=lambda r:(r["chrom"],r["tss_0based"],r["strand"],r["gene_id"]))
    census={
        "schema":"V64_GENCODE50_PROMOTER_CANDIDATE_CENSUS_V1",
        "input":str(path),
        "transcript_features":tx_count,
        "unique_versioned_genes_with_transcripts":len(gene_ids),
        "candidate_gene_tss":len(rows),
        "protein_coding_candidate_gene_tss":sum(r["gene_type"]=="protein_coding" for r in rows),
        "plus_candidates":sum(r["strand"]=="+" for r in rows),
        "minus_candidates":sum(r["strand"]=="-" for r in rows),
        "gene_type_candidate_counts":dict(Counter(r["gene_type"] for r in rows)),
        "annotation_only":True,
        "activity_gating_used":False,
        "promoter_interval_width_defined":False,
        "training_authorized":False,
    }
    return rows,census


FIELDS=[
 "candidate_promoter_id","gene_id","gene_id_base","gene_name","gene_type",
 "chrom","strand","tss_0based","tss_1based","n_transcripts_at_tss",
 "transcript_ids","transcript_id_bases","transcript_types"
]


def write_rows(rows, path: Path):
    opener=gzip.open if path.suffix==".gz" else open
    with opener(path,"wt",encoding="utf-8",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=FIELDS,delimiter="\t",extrasaction="ignore")
        w.writeheader()
        for r in rows:
            rr=dict(r)
            for k in ("transcript_ids","transcript_id_bases","transcript_types"):
                rr[k]=";".join(rr[k])
            w.writerow(rr)


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--gtf",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--census",type=Path,required=True)
    args=ap.parse_args(argv)
    rows,census=build(args.gtf)
    write_rows(rows,args.output)
    args.census.write_text(json.dumps(census,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(census,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
