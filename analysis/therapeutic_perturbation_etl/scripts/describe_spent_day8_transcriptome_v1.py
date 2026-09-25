#!/usr/bin/env python3
"""Describe *already inspected* Day-8 DE. Never inspect reserved other screens."""
import argparse,csv,gzip,hashlib,io,json,math,statistics
from collections import defaultdict
from itertools import combinations
from pathlib import Path
SOURCE="analysis/therapeutic_perturbation_etl/outputs/crisprbrain/iTF_Microglia-Day-8-CROP-seq-CRISPRi.csv.gz"
COMPRESSED_SHA="201e8fb28a63dfb91ae5f37a77f9641a90c3cdf4c618943a55699c512227079f"
UNCOMPRESSED_SHA="41eb533dfd50852d0ebd8f2c27d42d5f6bb3b1f1264ab0c721106cfbaed9fc39"
def load(data,compressed_sha=COMPRESSED_SHA,uncompressed_sha=UNCOMPRESSED_SHA):
    if hashlib.sha256(data).hexdigest()!=compressed_sha:raise ValueError("STOP: compressed digest mismatch")
    try:plain=gzip.decompress(data)
    except (EOFError,OSError) as exc:raise ValueError("STOP: gzip invalid") from exc
    if hashlib.sha256(plain).hexdigest()!=uncompressed_sha:raise ValueError("STOP: uncompressed digest mismatch")
    rd=csv.DictReader(io.StringIO(plain.decode("utf-8-sig"),newline=""))
    if not {"Gene","name","Log2FC","FDR"}.issubset(set(rd.fieldnames or [])):raise ValueError("STOP: missing columns")
    if len(rd.fieldnames)!=len(set(rd.fieldnames)):raise ValueError("STOP: duplicate column")
    profiles=defaultdict(dict);rows=0;missing_fdr=0
    for item in rd:
        gene,target=(item.get(k) or "").strip() for k in ("Gene","name")
        if not gene or not target or gene in profiles[target]:raise ValueError("STOP: blank/duplicate identity")
        try:
            fc=float(item["Log2FC"])
            raw=(item["FDR"] or "").strip()
            fdr=float(raw) if raw else None
        except (TypeError,ValueError) as exc:raise ValueError("STOP: malformed FC/FDR") from exc
        if not math.isfinite(fc) or (fdr is not None and (not math.isfinite(fdr) or not (0<=fdr<=1))):
            raise ValueError("STOP: nonfinite FC/invalid FDR")
        if fdr is None:missing_fdr+=1
        profiles[target][gene]=(fc,fdr);rows+=1
    if not rows:raise ValueError("STOP: empty screen")
    return dict(profiles),{"source_compressed_sha256":compressed_sha,"source_uncompressed_sha256":uncompressed_sha,"rows":rows,"missing_fdr":missing_fdr}
def cos(vx,vy):
    xx=sum(x*x for x in vx);yy=sum(y*y for y in vy)
    return sum(x*y for x,y in zip(vx,vy))/math.sqrt(xx*yy) if xx>0 and yy>0 else None
def assess(profiles,src):
    if len(profiles)<2:raise ValueError("STOP: at least two targets required")
    universe=set().union(*(set(x) for x in profiles.values()))
    per_target=[]
    for target,rows in sorted(profiles.items()):
        subset=[(gene,*obs) for gene,obs in rows.items() if gene!=target]
        effects=[x[1] for x in subset]
        fdrknown=[x for x in subset if x[2] is not None]
        per_target.append({"target":target,"genes_measured_excluding_target":len(subset),
          "own_gene_row_present":target in rows,
          "off_target_median_abs_log2fc":statistics.median(map(abs,effects)) if effects else None,
          "off_target_genes_abs_fc_ge_0p5":sum(abs(x)>=.5 for x in effects),
          "off_target_genes_abs_fc_ge_1p0":sum(abs(x)>=1 for x in effects),
          "off_target_genes_with_fdr":len(fdrknown),
          "off_target_depositor_fdr_lt_0p05":sum(f<.05 for _,_,f in fdrknown),
          "off_target_depositor_fdr_lt_0p05_positive":sum(f<.05 and v>0 for _,v,f in fdrknown),
          "off_target_depositor_fdr_lt_0p05_negative":sum(f<.05 and v<0 for _,v,f in fdrknown)})
    pair_rows=[]
    for t1,t2 in combinations(sorted(profiles),2):
        a,b=profiles[t1],profiles[t2]
        genes=sorted((set(a)&set(b))-{t1,t2})
        ax=[a[g][0] for g in genes];by=[b[g][0] for g in genes]
        sig1={g for g in genes if a[g][1] is not None and a[g][1]<.05}
        sig2={g for g in genes if b[g][1] is not None and b[g][1]<.05}
        shared=len(sig1&sig2);union=len(sig1|sig2)
        pair_rows.append({"target_a":t1,"target_b":t2,"shared_assayed_off_target_genes":len(genes),
          "signed_cosine_all_common_off_target_genes":cos(ax,by),
          "fdr_hit_a":len(sig1),"fdr_hit_b":len(sig2),"fdr_hit_both":shared,
          "fdr_hit_jaccard":shared/union if union else None})
    usable=[p["signed_cosine_all_common_off_target_genes"] for p in pair_rows if p["signed_cosine_all_common_off_target_genes"] is not None]
    counts=[t["off_target_depositor_fdr_lt_0p05"] for t in per_target]
    return {"schema":"DAY8_EXPOSED_TRANSCRIPTOME_CHARACTERIZATION_V1",
      "source":SOURCE,"source_binding":src,
      "exposure":"DEVELOPMENT_INSPECTED_DAY8_ONLY","study_is_one_pooled_biological_preparation":True,
      "biological_uncertainty_estimable":False,"depositor_fdr_is_not_independent_biological_replication":True,
      "outcomes_other_than_day8_inspected":False,
      "prediction_metric_selected":False,"model_trained":False,"independent_confirmation":False,
      "gene_namespace":"PUBLISHED_LITERAL_LABELS_NOT_FROZEN_HGNC_CROSSWALK",
      "targets":len(profiles),"unique_measured_genes":len(universe),"target_pairs":len(pair_rows),
      "summary":{"median_off_target_depositor_fdr_hits_per_target":statistics.median(counts),
         "targets_with_zero_depositor_fdr_hits":sum(v==0 for v in counts),
         "median_signed_cosine_across_target_pairs":statistics.median(usable) if usable else None,
         "pairwise_similarity_estimated":len(usable)},
      "per_target":per_target,"pairwise_target_response":pair_rows}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo",type=Path,required=True);ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise SystemExit("STOP: refuse to overwrite")
    profiles,src=load((a.repo/SOURCE).read_bytes())
    if len(profiles)!=39 or src["rows"]!=343707:raise SystemExit("STOP: Day8 source population changed")
    result=assess(profiles,src)
    if result["unique_measured_genes"]!=10549:raise SystemExit("STOP: gene census changed")
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"targets":result["targets"],"genes":result["unique_measured_genes"],"pairs":result["target_pairs"],"summary":result["summary"]}))
if __name__=="__main__":main()
