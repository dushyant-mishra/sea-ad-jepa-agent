#!/usr/bin/env python3
"""Independent network recheck of the seven-source public E2G interval survey.

Public browser files only. No requester-pays bucket, controlled dataset, model
training, real microglial validation or Stage75 TF->gene edge authority.
"""
from __future__ import annotations
import csv
import gzip
import io
import json
import math
from collections import defaultdict
from pathlib import Path
from survey_e2g_public_7tracks_v1 import (
    PANEL, MAX_TOTAL, public_sources, bounded_public_download
)

REGISTRY=Path("results/regulatory/e2g_public_7track_provisional_result_receipt_v1_20261027.json")
MATCH=Path("results/regulatory/e2g_public_geometry_panel_matched_control_counts_v1_20261027.csv")
MACRO=("inflammatory_macrophage_ENCSR593WXK",
       "inflammatory_macrophage_ENCSR643ZGR",
       "inflammatory_macrophage_ENCSR226JLK")
SC=("Macrophage","Immune_monocyte_1")
EXPECTED={"panel":{"exact":1,"p50":126,"p80":111,"distal_p50":30,"sc_overlap_p50":91,"sc_distal_p50":21},
          "matched_control":{"exact":2,"p50":110,"p80":89,"distal_p50":33,"sc_overlap_p50":55,"sc_distal_p50":9}}


def load_genes():
    with MATCH.open(newline="",encoding="utf-8") as stream:
        r=list(csv.DictReader(stream))
    if len(r)!=54 or len({x["gene"] for x in r})!=54:
        raise ValueError("Changed panel/control roster")
    p={x["gene"] for x in r if x["role"]=="PANEL"}
    c={x["gene"] for x in r if x["role"]=="MATCHED_NONPANEL_CONTROL"}
    if len(p)!=27 or len(c)!=27 or (p&c):
        raise ValueError("Unexpected group membership")
    return p,c


def parse(raw,compressed,family,genes):
    reader=gzip.GzipFile(fileobj=io.BytesIO(raw)) if compressed else io.BytesIO(raw)
    output=defaultdict(set); n=0
    for line in reader:
        if not line.strip():continue
        x=line.decode("utf-8").rstrip("\r\n").split("\t")
        if len(x)!=10:raise ValueError("BEDPE schema changed")
        if x[0]!=x[3] or not x[0].startswith("chr"):
            raise ValueError("Bad chromosome")
        chrom=x[0]
        start,end,tss=int(x[1]),int(x[2]),int(x[4])
        score=float(x[7])
        if start<0 or end<=start or tss<0 or not math.isfinite(score) or not 0<=score<=1:
            raise ValueError("Bad BEDPE intervals or score")
        n+=1
        label=x[6].split("|",1)[0]
        if family=="scE2G":
            for suffix in ("_intergenic","_promoter","_genic"):
                if label.endswith(suffix):
                    label=label[:-len(suffix)]
                    break
        if label in genes:
            output[label].add((chrom,start,end,tss))
    return output,n


def similarity(a,b):
    if a[0]!=b[0] or a[3]!=b[3]:return 0.
    inter=max(0,min(a[2],b[2])-max(a[1],b[1]))
    if not inter:return 0.
    return min(inter/(a[2]-a[1]),inter/(b[2]-b[1]))


def threeway(anchor,b,c,threshold):
    for x in b:
        if similarity(anchor,x)<threshold:continue
        for y in c:
            if similarity(anchor,y)>=threshold and similarity(x,y)>=threshold:
                return True
    return False


def assess(genes,tracks):
    U,A,B=[tracks[i] for i in MACRO]
    out={"exact":0,"p50":0,"p80":0,"distal_p50":0,
         "sc_overlap_p50":0,"sc_distal_p50":0}
    for gene in genes:
        for iv in U.get(gene,set()):
            if iv in A.get(gene,set()) and iv in B.get(gene,set()):
                out["exact"]+=1
            if threeway(iv,A.get(gene,set()),B.get(gene,set()),.8):
                out["p80"]+=1
            if threeway(iv,A.get(gene,set()),B.get(gene,set()),.5):
                out["p50"]+=1
                distal=abs((iv[1]+iv[2])/2-iv[3])>=20_000
                out["distal_p50"]+=int(distal)
                match=any(similarity(iv,sciv)>=.5 for s in SC for sciv in tracks[s].get(gene,set()))
                out["sc_overlap_p50"]+=int(match)
                out["sc_distal_p50"]+=int(distal and match)
    return out


def main():
    panel,controls=load_genes()
    selected=panel|controls
    original=json.loads(REGISTRY.read_text())
    hashes={x["source_id"]:x for x in original["source_results"]}
    urls=public_sources()
    if set(urls)!=set(PANEL) or set(hashes)!=set(PANEL):
        raise ValueError("Source registry drift")
    rawleft=MAX_TOTAL
    data={}
    sourcechecks=[]
    for ident in PANEL:
        record=hashes[ident]
        import urllib.parse
        u=urls[ident]["e2gPredictionsUrl"]
        if urllib.parse.urlsplit(u).path.rsplit("/",1)[-1]!= {
            "inflammatory_macrophage_ENCSR593WXK":"encode_e2g_predictions_inflammatory_macrophage_ENCSR593WXK_thresholded_predictions.bedpe.gz",
            "inflammatory_macrophage_ENCSR643ZGR":"encode_e2g_predictions_inflammatory_macrophage_ENCSR643ZGR_thresholded_predictions.bedpe.gz",
            "inflammatory_macrophage_ENCSR226JLK":"encode_e2g_predictions_inflammatory_macrophage_ENCSR226JLK_thresholded_predictions.bedpe.gz",
            "Macrophage":"Macrophage_encode_e2g_predictions_threshold0.173.bedpe",
            "Immune_monocyte_1":"Immune_monocyte_1_encode_e2g_predictions_threshold0.173.bedpe",
            "brain_ENCSR344FLH":"encode_e2g_predictions_brain_ENCSR344FLH_thresholded_predictions.bedpe.gz",
            "Stitziel_hCA_Myeloid":"encode_e2g_predictions_threshold0.177.bedpe",
        }[ident]:raise ValueError("Source URL basename changed")
        blob,sha=bounded_public_download(u,rawleft)
        if sha!=record["source_sha256"]:raise ValueError("Source hash changed")
        rawleft-=len(blob)
        parsed,n=parse(blob,u.endswith(".gz"),urls[ident]["modelType"],selected)
        if n!=record["total_thresholded_track_rows"]:
            raise ValueError("Source predicted rows changed")
        data[ident]=parsed
        sourcechecks.append({"id":ident,"sha256":sha,"rows":n})
    result={"schema":"JEPA_INDEPENDENT_E2G_GEOMETRIC_RECHECK_V1",
            "status":"PUBLIC_SOURCE_HASHES_VERIFIED__REFERENCE_ONLY",
            "panel":assess(panel,data),"matched_control":assess(controls,data),
            "source_checks":sourcechecks,
            "controls":"Frozen 27 nonpanel genes selected before cross-context results",
            "methods":"exact or baseline anchored reciprocal >=0.5/0.8 with 3-way clique, same symbol+TSS",
            "TF_to_gene_validation":None,"experimental_microglia_validation":False,
            "biological_effect_inference":False,"training_authorized":False}
    for group,expect in EXPECTED.items():
        for k,v in expect.items():
            if result[group][k]!=v:
                raise ValueError(f"Independent recheck failed: {group}.{k} got {result[group][k]} expected {v}")
    out=Path("e2g_independent_recheck_receipt.json")
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"PASS_INDEPENDENT_SOURCE_RECHECK",
         "panel":result["panel"],"matched_control":result["matched_control"],
         "no_regulatory_authority":True},indent=2))


if __name__=="__main__":
    main()
