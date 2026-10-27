#!/usr/bin/env python3
"""Fail-closed independent stdlib receipt validator. No biology/training authority."""
from __future__ import annotations
import argparse
import csv
import hashlib
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

FILES = {
 "stage75_e2g_r50_266_source_element_matches_v1_20261027.csv": "5e9ccc4143842dbe4f13ec117380e677a303dcededab3e85d82f723d858f9864",
 "stage75_e2g_149_peak_7context_recurrence_v1_20261027.csv": "155acae4accc4e1a9175f20177b02935a524370e22b75d43622ba2dec60fd1ee",
 "stage75_e2g_85_scaffold_peak_recurrence_controls_v1_20261027.csv": "544279fc7418b95b8b3f7b9dd5216f91412b499397296a1129e98e0ca6e5be8d",
 "e2g_stage75_tss_106_unique_source_peak_comparisons_v1_20261027.csv": "be290586d64002240234b32308129b4d0a57008f60f0915760d51e81de73a79f",
 "e2g_stage75_9_within_gene_geometry_matched_peaks_v1_20261027.csv": "874961f5326bebce451baebfb9e37b94fec2397703871732f3482f62df20d245",
}
MAC = ("inflammatory_macrophage_ENCSR593WXK", "inflammatory_macrophage_ENCSR643ZGR", "inflammatory_macrophage_ENCSR226JLK")
SC = ("Macrophage", "Immune_monocyte_1")
SOURCES = (*MAC, *SC, "brain_ENCSR344FLH", "Stitziel_hCA_Myeloid")
RX = re.compile(r"^(chr(?:[1-9]|1[0-9]|2[0-2]|X|Y|M|MT)):(\d+)-(\d+)$")

def require(test, description):
    if not test:
        raise ValueError(description)

def load(root):
    frames={}
    for name,digest in FILES.items():
        path=root/name
        raw=path.read_bytes()
        require(hashlib.sha256(raw).hexdigest()==digest, "SOURCE_SHA256_DRIFT: "+name)
        with path.open(newline="",encoding="utf-8") as handle:
            frames[name]=list(csv.DictReader(handle))
    return frames

def peak_mid(name):
    m=RX.fullmatch(name)
    require(m is not None, "bad peak format")
    a,b=map(int,m.groups()[1:])
    require(a<b and a>=0, "bad peak coordinates")
    return (a+b)//2

def check(root):
    f=load(root)
    rows=f["stage75_e2g_r50_266_source_element_matches_v1_20261027.csv"]
    recurrence=f["stage75_e2g_149_peak_7context_recurrence_v1_20261027.csv"]
    scaffold=f["stage75_e2g_85_scaffold_peak_recurrence_controls_v1_20261027.csv"]
    tss=f["e2g_stage75_tss_106_unique_source_peak_comparisons_v1_20261027.csv"]
    pairs=f["e2g_stage75_9_within_gene_geometry_matched_peaks_v1_20261027.csv"]
    require((len(rows),len(recurrence),len(scaffold),len(tss),len(pairs))==(266,149,85,106,9), "row count drift")
    seen={}
    for r in rows:
        k=(r["target_gene"],r["stage75_peak_id"],r["source_id"],int(r["external_reported_gene_tss"]))
        stage=float(r["stage75_nearest_gene_distance_bp"])
        external=abs(peak_mid(r["stage75_peak_id"])-k[3])
        val=(stage,external,abs(stage-external))
        if k in seen:
            require(seen[k]==val, "same peak/source TSS discrepancy changed across TF")
        seen[k]=val
    require(len(seen)==106, "source peak/TSS units drift")
    recorded={}
    for r in tss:
        k=(r["target_gene"],r["stage75_peak_id"],r["source_id"],int(r["external_reported_gene_tss"]))
        require(k not in recorded and k in seen, "TSS mirror identity drift")
        x=(float(r["stage75_nearest_gene_distance_bp"]),int(r["external_midpoint_distance_bp"]),
           float(r["stage75_external_midpoint_distance_disagreement_bp"]))
        require(all(abs(a-b)<1e-7 for a,b in zip(x,seen[k])), "midpoint distance arithmetic drift")
        recorded[k]=x
    require(set(recorded)==set(seen), "source peak/TSS mirror incomplete")
    hist=Counter("<=500" if v[2]<=500 else "501-2000" if v[2]<=2000 else ">2000" for v in seen.values())
    require(hist==Counter({"<=500":90, "501-2000":13, ">2000":3}), "TSS discrepancy strata changed")
    large=[k for k,v in seen.items() if v[2]>2000]
    require({k[:2] for k in large}=={("PRDX1","chr1:45543742-45544241")} and len(large)==3, "PRDX1 source discrepancy drift")
    require({seen[k][2] for k in large}=={20794}, "PRDX1 20,794bp discrepancy drift")

    compatible={(gene,peak,src) for (gene,peak,src,_),v in seen.items() if v[2]<=2000}
    raw_counts=Counter()
    stricter_counts=Counter()
    before=after=0
    locus_labels=defaultdict(list)
    for r in recurrence:
        gene,peak=r["target_gene"],r["stage75_peak_id"]
        source_flags=tuple(int(r[s]) for s in SOURCES)
        locus_labels[(gene,peak)].append(source_flags)
        prior=[int(r[s]) for s in MAC]
        strict=[int(r[s]) and int((gene,peak,s) in compatible) for s in MAC]
        sc_prior=[int(r[s]) for s in SC]
        sc_strict=[int(r[s]) and int((gene,peak,s) in compatible) for s in SC]
        before+=int(all(prior) and any(sc_prior))
        after+=int(all(strict) and any(sc_strict))
        for sid in SOURCES:
            orig=int(r[sid])
            raw_counts[sid]+=orig
            stricter_counts[sid]+=int(orig and (gene,peak,sid) in compatible)
    require(len(locus_labels)==56, "number of physical gene/peak units changed")
    require(sum(len(v)>1 for v in locus_labels.values())==37, "multilabel TF reuse changed")
    require(all(len(set(values))==1 for values in locus_labels.values()), "TF labels altered E2G overlap for same physical peak")
    require(tuple(raw_counts[s] for s in SOURCES)==(40,34,43,36,51,3,59), "old source r50 counts changed")
    require(tuple(stricter_counts[s] for s in SOURCES)==(40,31,40,36,51,3,56), "TSS sensitivity r50 counts changed")
    require(before==after==26, "strict cross-source recurrence changed")

    originals={r["peak_id"]:r for r in scaffold}
    require(len(originals)==85, "duplicate scaffold peaks")
    require(sum(r["stage75_motif_hit_present"]=="True" for r in scaffold)==56, "motif-hit exposure changed")
    used_motif=set();used_other=set()
    for r in pairs:
        g,a,b=r["target_gene"],r["motif_peak_id"],r["other_peak_id"]
        require(a in originals and b in originals and a!=b, "matched peaks not in scaffold")
        left,right=originals[a],originals[b]
        require(left["target_gene"]==right["target_gene"]==g, "not same target gene")
        require(left["stage75_motif_hit_present"]=="True" and right["stage75_motif_hit_present"]=="False", "motif-control class drift")
        require(a not in used_motif and b not in used_other, "matched peak reused")
        used_motif.add(a);used_other.add(b)
        wr=abs(math.log2(float(left["peak_width"])/float(right["peak_width"])))
        dr=abs(math.log2((float(left["distance_bp"])+1000)/(float(right["distance_bp"])+1000)))
        require(wr<=1+1e-10 and dr<=1+1e-10, "geometry caliper breach")
        require(abs(wr-float(r["abs_log2_width_ratio"]))<1e-8 and abs(dr-float(r["abs_log2_distance_plus1k_ratio"]))<1e-8, "geometry pair calculation drift")
        require(int(r["motif_cross_context_r50"])==int(left["macro3_sc"]) and int(r["other_cross_context_r50"])==int(right["macro3_sc"]), "pair recurrence outcome drift")
    require(len({r["target_gene"] for r in pairs})==7, "within-gene matched coverage changed")
    require(sum(int(r["motif_cross_context_r50"]) for r in pairs)==4 and sum(int(r["other_cross_context_r50"]) for r in pairs)==2, "matched outcome sums changed")
    print("PASS_POSTHOC_SOURCE_BOUND__106_TSS_UNITS__9_GEOMETRY_MATCHES__37_REUSED_LOCI__26_REFERENCE_RECURRENCE")
    print("NO_TF_OR_CAUSAL_VALIDATION__NO_TARGET_SELECTION__NO_TRAINING__NO_STAGE4")
    return True

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--root",type=Path,default=Path("results/regulatory"))
    args=cli.parse_args()
    check(args.root)
