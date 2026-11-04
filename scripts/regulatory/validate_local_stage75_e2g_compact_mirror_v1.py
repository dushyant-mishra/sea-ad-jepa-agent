#!/usr/bin/env python3
"""Fail-closed repository-side cross-check of local Stage75/E2G compact mirrors.

Does NOT re-download original uploaded 319-row source evidence. The uploaded
ZIP SHA and its manifest are audited locally and recorded separately. This CI
check only validates derived result coherence against tracked frozen summary.
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SUMMARY=ROOT/"results/tables/stage75_integrated_tf_target_summary_v1.csv"
RECUR=ROOT/"results/regulatory/stage75_e2g_149_peak_7context_recurrence_v1_20261027.csv"
SOURCES=ROOT/"results/regulatory/stage75_e2g_7context_coordinate_summary_v1_20261027.csv"
MACRO=("inflammatory_macrophage_ENCSR593WXK","inflammatory_macrophage_ENCSR643ZGR","inflammatory_macrophage_ENCSR226JLK")
SC=("Macrophage","Immune_monocyte_1")
ALL=(*MACRO,*SC,"brain_ENCSR344FLH","Stitziel_hCA_Myeloid")
COUNTS=(40,34,43,36,51,3,59)

def read(path):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def run():
    frozen=read(SUMMARY)
    recur=read(RECUR)
    sources=read(SOURCES)
    if len(frozen)!=96 or len(recur)!=149 or len(sources)!=7:
        raise ValueError("Frozen source or compact mirror row count drift")
    frozen_pairs={(r["tf"],r["target_gene"]) for r in frozen}
    observed_pairs={(r["tf"],r["target_gene"]) for r in recur}
    if len(frozen_pairs)!=96 or frozen_pairs!=observed_pairs:
        raise ValueError("Observed peak hypotheses outside frozen TF-gene pairs")
    if len({r["stage75_peak_id"] for r in recur})!=56:
        raise ValueError("Physical Stage75 peak diversity drift")
    if set(r["source_id"] for r in sources)!=set(ALL):
        raise ValueError("Seven source identities drifted")
    if any(r["motif_class"] not in ("direct","extended_only") for r in recur):
        raise ValueError("Motif classification drift")
    bypair=defaultdict(list)
    for row in recur:
        bypair[(row["tf"],row["target_gene"])].append(row)
        chrom,_,interval=row["stage75_peak_id"].partition(":")
        pos=interval.split("-")
        if not chrom.startswith("chr") or len(pos)!=2 or int(pos[0])>=int(pos[1]):
            raise ValueError("Malformed source peak coordinate")
        if row["HLA_DPA1_DPB1_source_address_caution"]!=str(int(row["target_gene"] in ("HLA-DPA1","HLA-DPB1"))):
            raise ValueError("Historic HLA address caveat silently lost")
    for row in frozen:
        entries=bypair[(row["tf"],row["target_gene"])]
        if len(entries)!=int(row["n_unique_query_peaks"]):
            raise ValueError("Per-pair unique peak scaffold mismatch")
        is_direct=any(x["motif_class"]=="direct" for x in entries)
        if ("direct" if is_direct else "extended_only")!=row["motif_support_class"]:
            raise ValueError("Frozen motif summary altered")
    summary={s["source_id"]:s for s in sources}
    for sid,expected in zip(ALL,COUNTS):
        n=sum(int(r[sid]) for r in recur)
        if n!=expected or n!=int(summary[sid]["tf_gene_peak_hypotheses_r50"]):
            raise ValueError("Cross-source overlap count drift")
        pairs={(r["tf"],r["target_gene"]) for r in recur if int(r[sid])}
        if len(pairs)!=int(summary[sid]["tf_gene_pairs_with_r50"]):
            raise ValueError("Distinct TF-gene overlap count drift")
    cohort=[r for r in recur if all(int(r[s]) for s in MACRO) and any(int(r[s]) for s in SC)]
    if (len(cohort)!=26 or len({r["stage75_peak_id"] for r in cohort})!=12
        or len({(r["tf"],r["target_gene"]) for r in cohort})!=23
        or len({r["target_gene"] for r in cohort})!=9):
        raise ValueError("Cross-model recurrence unit mismatch")
    if any(float(r["stage75_abs_distance_to_tss"])>=20000 for r in cohort):
        raise ValueError("Previously absent distal recurring region appeared")
    if sum(r["motif_class"]=="direct" for r in cohort)!=8:
        raise ValueError("Direct motif support overclaim/drift")
    print("PASS: compact Stage75/E2G mirror, 96 frozen pairs, 149 hypothesis units, 26 recurrence, 12 peaks, no distal survivors")
    print("LIMIT: original uploaded fine-grained file and genome-build attestations NOT in repository")

if __name__=="__main__":run()
