#!/usr/bin/env python3
"""Independent read-only audit of Claude WP-F (PR #118), with five-target checks.

No GSE335887 numerical expression/FDR, HDF5, protected FULL104 outcomes,
or new-study response measurements are read. Day-8 and GSE301119 own-gene
engagements were explicitly exposed as DEVELOPMENT before this audit.
"""
import argparse,csv,gzip,hashlib,io,json
from pathlib import Path
from build_cross_study_comparability_matrix_v1 import PINNED_SOURCE_SHA256

ROOT=Path("analysis/therapeutic_perturbation_etl")
ORIGINAL_BLOBS={
  "day8_library":("reference/GSE178317_sgrna_library_suppl_table5.csv","e9f40526f64df31b56d95657657ab068094ac3a0"),
  "day8_development_engagement":("evidence/gse178317_recovery/gse178317_target_engagement_v2.csv","3dc8e48767e8f3e2b013c75ae145bfd802995d0b"),
  "gse301119_development_engagement":("evidence/gse301119_donor_aware_v1/gse301119_donor_aware_target_summary_v1.csv","cec3c709f44b5575ef549a7d8a9e49066c4c8b06"),
  "gse240609_241858_completed_receipt":("evidence/bulk_physical_v2/BULK_DISEASE_CONTEXT_SUMMARY.json","fa5bf6e7e98c35c7e22d9de9474ac7940048f4cf"),
}
FEATURE_REFS={
  "iTF":("reference/gse335887/GSE335887_itf_feature_reference.csv.gz","fd2c3fa5b517c81bbd158516dacb00416f1883a654c795e126916620f77f225f"),
  "iMG":("reference/gse335887/GSE335887_img_feature_reference.csv.gz","cbc733178cefa49f660e2728debb834eed4520a3691834ba212102b3a0f6c533"),
}
FIVE=("CSF1R","CSF2RA","CSF2RB","TGFBR1","TGFBR2")

def sha(data):return hashlib.sha256(data).hexdigest()
def blob(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()
def rows(data):
    out=list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"),newline="")))
    if not out or not out[0]:raise ValueError("STOP: empty/malformed CSV")
    return out
def read(repo,role):
    path,expected=ORIGINAL_BLOBS[role]
    data=(repo/ROOT/path).read_bytes()
    if blob(data)!=expected:raise ValueError("STOP: original "+role+" byte authority changed")
    return data
def guides(repo):
    decompressed=[]
    for role,(p,expected) in FEATURE_REFS.items():
        raw=(repo/ROOT/p).read_bytes()
        if len(raw)!=4381 or sha(raw)!=expected:raise ValueError("STOP: GSE335887 reference "+role+" SHA/size")
        decompressed.append(gzip.decompress(raw))
    if decompressed[0]!=decompressed[1]:raise ValueError("STOP: library not row-identical")
    table=rows(decompressed[0])
    allg=[r for r in table if r["feature_type"]=="CRISPR Guide Capture"]
    nt=[r for r in allg if r["id"].startswith("non-targeting_")]
    on=[r for r in allg if r not in nt]
    if len(table)!=245 or len(allg)!=65 or len(nt)!=5 or len(on)!=60:
        raise ValueError("STOP: GSE335887 feature/guide/NTC census")
    if len({r["id"] for r in table})!=245 or len({r["sequence"] for r in allg})!=65:
        raise ValueError("STOP: duplicate feature ID/protospacer")
    group={}
    for x in on:
        if not x["target_gene_name"] or not x["target_gene_id"]:
            raise ValueError("STOP: authentic target identity chain incomplete")
        group.setdefault(x["target_gene_name"],set()).add(x["sequence"])
    if len(group)!=30 or any(len(v)!=2 for v in group.values()) or "ARID5B" in group:
        raise ValueError("STOP: ARID5B/30-target library mismatch")
    antibodies=[r for r in table if r["feature_type"]=="Antibody Capture"]
    if len(antibodies)!=180 or len({r["id"] for r in antibodies})!=180 or len({r["sequence"] for r in antibodies})!=180:
        raise ValueError("STOP: unique antibody IDs/barcodes")
    return set(group),{"authentic_guide_targets":30,"guide_features":65,
          "distinct_protospacers":65,"non_targeting_guides":5,
          "antibody_catalog_ids":180,"ARID5B_guide_identity":"NOT_DEPOSITED",
          "iTF_iMG_library_byte_equal_after_gzip":True}
def audit(repo,wp_receipt,wp_csv):
    if wp_receipt["schema"]!="CROSS_STUDY_COMPARABILITY_MATRIX_V1":
        raise ValueError("STOP: wrong WP-F receipt")
    if wp_receipt.get("source_digests_match_previously_authenticated_origins") is not True:
        raise ValueError("STOP: input digests never compared to previously sealed authority")
    if wp_receipt["source_digests"]!=PINNED_SOURCE_SHA256:
        raise ValueError("STOP: input digests not pinned")
    if wp_receipt.get("jepa_prediction_used") is not False or wp_receipt.get("training_authorized") is not False or wp_receipt.get("therapeutic_ranking") is not False:
        raise ValueError("STOP: non-authorized result promotion")
    if sha(wp_csv)!=wp_receipt["matrix_csv_sha256"]:
        raise ValueError("STOP: changed WP-F matrix bytes")
    matrix=rows(wp_csv)
    if len(matrix)!=9 or len({x["study"] for x in matrix})!=9:
        raise ValueError("STOP: incomplete/duplicated study census")
    design={x["study"]:x for x in matrix}
    if design["GSE240609"]["response_outcome_exposure"]!="DERIVED_DEVELOPMENT_V2_NOT_RESERVED_CONFIRMATION":
        raise ValueError("STOP: completed WP-D GSE240609 still called a held-out study")
    if design["GSE335887"]["response_outcome_exposure"]!="UNOPENED_RESERVED":
        raise ValueError("STOP: reserved GSE335887 profile now declared exposed")
    bulk=json.loads(read(repo,"gse240609_241858_completed_receipt"))
    if bulk["GSE240609"]["uncertainty_estimable"] is not False or bulk["GSE240609"]["replicates_per_design_cell"]!=1:
        raise ValueError("STOP: GSE240609 invalid biological precision")
    guide_set,guide_receipt=guides(repo)
    day_lib=rows(read(repo,"day8_library"))
    day8_set={x["target_gene"] for x in day_lib if x["target_gene"]!="NTC"}
    if len(day8_set)!=39 or guide_set&day8_set:
        raise ValueError("STOP: Day8–GSE335887 false direct-target overlap")
    drows=rows(read(repo,"day8_development_engagement"))
    day={x["target_gene"]:x for x in drows}
    if set(day)!=day8_set:raise ValueError("STOP: Day8 source vs engagement mismatch")
    macro=rows(read(repo,"gse301119_development_engagement"))
    mr={m:{x["target_gene"]:x for x in macro if x["modality"]==m} for m in ("CRISPRi","CRISPRa")}
    if any(len(x)!=206 for x in mr.values()):raise ValueError("STOP: per-modality target count")
    i,a=set(mr["CRISPRi"]),set(mr["CRISPRa"])
    if len(i&a)!=204 or len(i|a)!=208 or i-a!={"RPL11","RPL7"} or a-i!={"CDKN2A","TP53"}:
        raise ValueError("STOP: paired CRISPRi/a universe")
    if guide_set&(i|a)!={"SPI1"}:raise ValueError("STOP: WTC11→macrophage direct target")
    five=set(day8_set)&i&a
    if five!=set(FIVE):raise ValueError("STOP: five independent direct-target overlaps")
    if wp_receipt["shared_direct_targets"].get("GSE178317|GSE301119")!=list(FIVE):
        raise ValueError("STOP: original WP-F five-target receipt")
    if wp_receipt["shared_direct_targets"].get("GSE335887|GSE301119")!=["SPI1"]:
        raise ValueError("STOP: original WP-F SPI1 receipt")
    if wp_receipt["authenticated_direct_target_counts"]!={"GSE335887":30,"GSE178317":39,"GSE301119":208}:
        raise ValueError("STOP: original direct-target scope changed")
    effects=[]
    for target in FIVE:
        d=day[target];ri=mr["CRISPRi"][target];ra=mr["CRISPRa"][target]
        if d["biological_uncertainty_estimable"]!="False":raise ValueError("STOP: Day8 technical wells promoted")
        if ri["cross_donor_mean_estimable"]!="TRUE" or ra["cross_donor_mean_estimable"]!="TRUE":
            raise ValueError("STOP: donor support absent for "+target)
        if any(v["own_gene_status"]!="ASSAYED_DETECTED" for v in (ri,ra)):
            raise ValueError("STOP: own target not measured "+target)
        vd,vi,va=(float(d["engagement_log2fc"]),float(ri["engagement_log2fc"]),float(ra["engagement_log2fc"]))
        if not vd<0 or not vi<0 or not va>0:raise ValueError("STOP: cross-lab sign mismatch "+target)
        if not all(float(ri[k])<0 and float(ra[k])>0 for k in ("engagement_D1","engagement_D2")):
            raise ValueError("STOP: hidden within-donor reversal "+target)
        effects.append({"target":target,"Day8_CRISPRi_log2fc":vd,
               "GSE301119_CRISPRi_log2fc":vi,"GSE301119_CRISPRa_log2fc":va,
               "two_macrophage_donors_each_support_expected_sign":True})
    return {"schema":"CLAUDE_WPF_INDEPENDENT_SOURCE_PINNED_REVIEW_V1",
      "input_source_git_blob_sha1":{k:v for k,(_,v) in ORIGINAL_BLOBS.items()},
      "feature_reference_sha256":{k:v for k,(_,v) in FEATURE_REFS.items()},
      "verified_source_guide_reference":guide_receipt,
      "Day8_GSE301119_shared_direct_targets":list(FIVE),
      "Day8_GSE335887_shared_authenticated_targets":[],
      "GSE335887_macrophage_shared_authenticated_targets":["SPI1"],
      "GSE301119_modality_target_intersection":204,
      "GSE301119_modality_target_union":208,
      "five_target_development_engagement_direction_check":effects,
      "gse240609_exposure":"WP_D_INSPECTED_DEVELOPMENT",
      "Day8_biological_replicate_uncertainty_estimable":False,
      "GSE301119_population_inference_authorized":False,
      "GSE335887_numeric_outcome_unopened":True,
      "GSE175721_author_guide_assignment_still_missing":True,
      "GSE311359_BIN1_physical_V2_pending":True,
      "downstream_cross_experiment_prediction_validated":False,
      "jepa_training_authorized":False}
def attack(receipt,matrix,repo):
    import copy
    mutants=[
      ("forged_source_digest",lambda r,b:r["source_digests"].update(gse178317_lib="0"*64)),
      ("false_digest_verification",lambda r,b:r.update(source_digests_match_previously_authenticated_origins=False)),
      ("fake_matrix_crc",lambda r,b:r.update(matrix_csv_sha256="0"*64)),
      ("ARID5B_false_count",lambda r,b:r["authenticated_direct_target_counts"].update(GSE335887=31)),
      ("five_target_corruption",lambda r,b:r["shared_direct_targets"]["GSE178317|GSE301119"].append("ARID5B")),
      ("false_training",lambda r,b:r.update(training_authorized=True)),
      ("WP_D_false_holdout",lambda r,b:b.replace(b"DERIVED_DEVELOPMENT_V2_NOT_RESERVED_CONFIRMATION",b"UNOPENED_RESERVED")),
    ]
    count=0
    for name,mut in mutants:
        r=copy.deepcopy(receipt)
        if name=="WP_D_false_holdout":
            altered=mut(r,matrix)
            # Function result is new bytes; mutations to input r are not needed.
            altered=matrix.replace(b"DERIVED_DEVELOPMENT_V2_NOT_RESERVED_CONFIRMATION",b"UNOPENED_RESERVED")
        else:mut(r,matrix);altered=matrix
        try:audit(repo,r,altered)
        except ValueError:count+=1;continue
        raise AssertionError("RED-TEAM FAILED TO DETECT "+name)
    return count
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--wp-receipt",type=Path,required=True)
    p.add_argument("--wp-matrix",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--adversarial",action="store_true")
    args=p.parse_args()
    if args.out.exists():raise SystemExit("STOP: refusing overwrite")
    parent=json.loads(args.wp_receipt.read_text());data=args.wp_matrix.read_bytes()
    report=audit(args.repo,parent,data)
    if args.adversarial:report["adversarial_forged_receipts_stopped"]=attack(parent,data,args.repo)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"verified_direct_shared_targets":len(FIVE),"adversarial_forged_receipts_stopped":report.get("adversarial_forged_receipts_stopped",0),"protected_numeric_outcomes_inspected":False}))
if __name__=="__main__":main()
