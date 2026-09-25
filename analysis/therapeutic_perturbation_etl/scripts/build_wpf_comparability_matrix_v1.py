#!/usr/bin/env python3
"""WP-F: source-bound, metadata-first study comparability. NOT a predictor.

This producer reads GSE335887's feature references and only identifier columns
from its previously unopened response tables. It reads *already development-
exposed* GSE301119 aggregate target engagement and three published bulk ETL
summaries. It does not read new numeric DE/FDR or protected FULL104 outcomes.
"""
from __future__ import annotations
import argparse,csv,gzip,hashlib,io,json,math,statistics
from collections import Counter,defaultdict
from itertools import combinations
from pathlib import Path

ROOT=Path("analysis/therapeutic_perturbation_etl")
BLOBS={
 "evidence/COMMITTED_OUTPUTS_SHA256_MANIFEST_V1.json":"97fe0f31038a702e70e1a2c4e70dbeb7a34e7683",
 "evidence/physical_inventory/STUDY_SOURCE_INVENTORY_RECEIPT_VNEXT.json":"4deebac29e0000b978ff1463115bf8727abd1af2",
 "evidence/gse301119_donor_aware_v1/gse301119_donor_aware_target_summary_v1.csv":"cec3c709f44b5575ef549a7d8a9e49066c4c8b06",
 "evidence/gse301119_donor_aware_v1/gse301119_donor_aware_receipt_v1.json":"838361a9c4cfe4aafd27761179bbbf49c0678448",
 "evidence/bulk_physical_v2/GSE254205_drug_response_summary_v2.json":"de2cea30a68145c14fcbb294857d325c286b0e3f",
 "evidence/bulk_physical_v2/BULK_DISEASE_CONTEXT_SUMMARY.json":"fa5bf6e7e98c35c7e22d9de9474ac7940048f4cf",
 "reference/GSE178317_sgrna_library_suppl_table5.csv":"e9f40526f64df31b56d95657657ab068094ac3a0",
 "evidence/gse293118/GSE293118_perturbation_identity.csv":"7cd6be560f211e0e053e98e8e834500232a185a8",
 "GSE311359_BIN1_IDENTITY_RESOLVED_20260924.md":"ca1398b6d155bb093416952fe3de7644cf1957b9",
 "GSE335887_METADATA_IDENTITY_CONTRACT_20260924.md":"70dc05762c35a429bea52acb67c6663dace9585e",
}
FEATURE_REF={
 "iTF":("reference/gse335887/GSE335887_itf_feature_reference.csv.gz",
       "fd2c3fa5b517c81bbd158516dacb00416f1883a654c795e126916620f77f225f"),
 "iMG":("reference/gse335887/GSE335887_img_feature_reference.csv.gz",
       "cbc733178cefa49f660e2728debb834eed4520a3691834ba212102b3a0f6c533")}
SCREENS={
 "Day8":("iTF_Microglia-Day-8-CROP-seq-CRISPRi.csv.gz",39,343707),
 "iTF_RNA":("iTF-Microglia-CROP-seq-CRISPRi.csv.gz",31,505527),
 "iMG_RNA":("iPSC-Microglia-CROP-seq-CRISPRi.csv.gz",31,417630),
 "iTF_ADT":("iTF-Microglia-CITE-seq-CRISPRi.csv.gz",31,None),
 "iMG_ADT":("iPSC-Microglia-CITE-seq-CRISPRi.csv.gz",31,None)}
def git_blob(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()
def digest(data):return hashlib.sha256(data).hexdigest()
def members_root(s):return digest(("\n".join(sorted(s))+"\n").encode())
def frozen_text(repo,path):
    key=path
    raw=(repo/ROOT/path).read_bytes()
    if git_blob(raw)!=BLOBS[key]:raise ValueError("STOP: frozen committed source blob: "+path)
    return raw
def parse_csv(data):return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"),newline="")))
def read_public_guide_refs(repo):
    out={};physical={}
    for group,(rel,sha) in FEATURE_REF.items():
        raw=(repo/ROOT/rel).read_bytes()
        if len(raw)!=4381 or digest(raw)!=sha:raise ValueError("STOP: authentic feature reference mismatch "+group)
        text=gzip.decompress(raw)
        out[group]=parse_csv(text)
        physical[group]={"compressed_sha256":sha,"decompressed_sha256":digest(text),
            "rows":len(out[group])}
    if out["iTF"]!=out["iMG"]:raise ValueError("STOP: iTF/iMG feature reference differs")
    rows=out["iTF"]
    required={"id","name","read","pattern","sequence","feature_type","target_gene_id","target_gene_name"}
    if not rows or not required<=rows[0].keys():raise ValueError("STOP: feature-reference schema")
    if len(rows)!=245 or len({x["id"] for x in rows})!=245:raise ValueError("STOP: duplicate/missing IDs")
    guides=[x for x in rows if x["feature_type"]=="CRISPR Guide Capture"]
    antibodies=[x for x in rows if x["feature_type"]=="Antibody Capture"]
    if len(guides)!=65 or len(antibodies)!=180:raise ValueError("STOP: guide/antibody census")
    if len({x["sequence"] for x in guides})!=65:raise ValueError("STOP: duplicate protospacers")
    if len({x["id"] for x in antibodies})!=180 or len({x["sequence"] for x in antibodies})!=180:
        raise ValueError("STOP: duplicate antibody ID/barcode")
    # Public NTC identity is encoded by the authentic guide feature ID.
    # NTC's target_gene_id field is a label and is not guaranteed blank.
    nt=[x for x in guides if x["id"].startswith("non-targeting_")]
    if len(nt)!=5 or len({x["id"] for x in nt})!=5:
        raise ValueError("STOP: wrong source-authenticated NTC feature IDs")
    if {x["id"] for x in nt}!={"non-targeting_h3_532","non-targeting_h6_711",
                              "non-targeting_h3_594","non-targeting_h5_749",
                              "non-targeting_h5_546"}:
        raise ValueError("STOP: NTC guide library identity changed")
    pert=[x for x in guides if x not in nt]
    if len(pert)!=60 or any(not x["target_gene_id"] or not x["target_gene_name"] for x in pert):
        raise ValueError("STOP: source protein/guide classification or target identity")
    t=Counter(x["target_gene_name"] for x in pert)
    if len(t)!=30 or set(t.values())!={2} or "ARID5B" in t:
        raise ValueError("STOP: source guide target/protospacer census "+str(dict(t)))
    return {"targets":set(t),"target_per_guide":dict(t),"guide_id_set_sha256":members_root(x["id"] for x in guides),
      "targets_sha256":members_root(t),"antibodies":180,"guides":65,
      "source_ref":physical,"raw_protein_panel_authority":"180_CATALOG_IDS_NOT_PROCESSED_ASSAY_ID_CROSSWALK"}
def screen_metadata(repo,manifest):
    m={x["path"]:x for x in manifest["files"]};out={}
    for name,(file,expect_targets,expect_rows) in SCREENS.items():
        path=ROOT/"outputs/crisprbrain"/file
        if path.as_posix() not in m:raise ValueError("STOP: missing source manifest "+name)
        rec=m[path.as_posix()];raw=(repo/path).read_bytes()
        if len(raw)!=rec["bytes"] or digest(raw)!=rec["sha256"]:
            raise ValueError("STOP: changed compressed CRISPRbrain table "+name)
        data=gzip.decompress(raw)
        reader=csv.reader(io.StringIO(data.decode("utf-8-sig"),newline=""))
        head=next(reader)
        if head.count("name")!=1 or head.count("Gene")!=1:raise ValueError("STOP: identifier schema")
        gi,ti=head.index("Gene"),head.index("name")
        per=defaultdict(set);n=0
        for row in reader:
            if len(row)!=len(head):raise ValueError("STOP: damaged public table")
            gene,target=row[gi].strip(),row[ti].strip()
            if not gene or not target:raise ValueError("STOP: blank identity")
            if gene in per[target]:raise ValueError("STOP: duplicated target feature")
            per[target].add(gene);n+=1
        if len(per)!=expect_targets or (expect_rows is not None and n!=expect_rows):
            raise ValueError("STOP: source screen population changed "+name)
        out[name]={"targets":set(per),"features":set().union(*per.values()),
            "per_target":per,"source_sha256":rec["sha256"],"rows":n,
            "status":"ALREADY_INSPECTED_DEVELOPMENT" if name=="Day8" else
                     "RESERVED_NUMERIC_RESPONSE_NOT_OPENED",
            "assay":"PROCESSED_PROTEIN" if name.endswith("ADT") else "PUBLISHED_RNA_DE"}
    return out
def parse_c_targets(raw,receipt):
    r=parse_csv(raw)
    if len(r)!=412 or not r or set(x["modality"] for x in r)!={"CRISPRa","CRISPRi"}:
        raise ValueError("STOP: donor summary census")
    sets={}
    details={}
    for mode in ("CRISPRi","CRISPRa"):
        rows=[x for x in r if x["modality"]==mode]
        targets={x["target_gene"] for x in rows}
        if len(rows)!=206 or len(targets)!=206:raise ValueError("STOP: wrong target census "+mode)
        exp=receipt["modalities"][mode]
        if exp["targets"]!=206 or exp["genes_assayed"] not in (19162,36601):
            raise ValueError("STOP: physical receipt changed")
        expected_gene=36601 if mode=="CRISPRi" else 19162
        if exp["genes_assayed"]!=expected_gene:raise ValueError("STOP: modality feature census changed")
        statuses=Counter(x["own_gene_status"] for x in rows)
        expected=(176,29,1) if mode=="CRISPRi" else (204,1,1)
        if tuple(statuses[k] for k in ("ASSAYED_DETECTED","ASSAYED_UNDETECTED","STRUCTURALLY_UNMEASURED"))!=expected:
            raise ValueError("STOP: own-gene observation category drift")
        nn=sum(x["cross_donor_mean_estimable"]=="TRUE" for x in rows)
        if nn!=(204 if mode=="CRISPRi" else 198):raise ValueError("STOP: donor support drift")
        zero_undetected=sorted(x["target_gene"] for x in rows if
            x["own_gene_status"]=="ASSAYED_UNDETECTED" and x["engagement_log2fc"] not in ("","NA")
            and float(x["engagement_log2fc"])==0)
        if zero_undetected!=(["ADGRG1","GPR87","TREML4"] if mode=="CRISPRi" else ["TREML4"]):
            raise ValueError("STOP: nondetection/zero-engagement diagnostic changed")
        nonmissing=[float(x["engagement_log2fc"]) for x in rows if x["engagement_log2fc"] not in ("","NA")]
        med=statistics.median(nonmissing)
        if abs(med-(-1.05180469086264 if mode=="CRISPRi" else 1.97309634514678))>1e-10:
            raise ValueError("STOP: directional control median changed")
        sets[mode]=targets;details[mode]={"targets":206,"genes_assayed":expected_gene,
            "cross_donor_estimable":nn,"engagement_median":med,
            "own_gene_status":dict(statuses),"assayed_undetected_with_zero_engagement":zero_undetected,
            "n_independent_donors":2,"nonpopulation_inference":True}
    if len(sets["CRISPRi"]&sets["CRISPRa"])!=204:
        raise ValueError("STOP: modalities do not share expected target set")
    return sets,details,r
def build(repo):
    frozen={k:git_blob((repo/ROOT/k).read_bytes()) for k in BLOBS}
    for k,h in BLOBS.items():
        if frozen[k]!=h:raise ValueError("STOP: input source sha mismatch: "+k)
    inventory=json.loads(frozen_text(repo,"evidence/physical_inventory/STUDY_SOURCE_INVENTORY_RECEIPT_VNEXT.json"))
    if inventory["authenticity_summary"]["verified"]!=16 or inventory["authenticity_summary"]["digest_mismatch"]!=0:
        raise ValueError("STOP: physical source inventory drift")
    # WP-A's old per-study ETL labels are historical and MUST NOT be used as current WP-C/D/E status.
    if inventory["per_study"]["GSE311359"]["etl_status"]!="STOP_AUTHOR_SOURCE_MISSING_FOR_BIN1":
        raise ValueError("STOP: historical inventory changed, explicit authority revision needed")
    cs=json.loads(frozen_text(repo,"evidence/gse301119_donor_aware_v1/gse301119_donor_aware_receipt_v1.json"))
    cs_sets,cs_details,cs_rows=parse_c_targets(
        frozen_text(repo,"evidence/gse301119_donor_aware_v1/gse301119_donor_aware_target_summary_v1.csv"),cs)
    b=read_public_guide_refs(repo)
    manifest=json.loads(frozen_text(repo,"evidence/COMMITTED_OUTPUTS_SHA256_MANIFEST_V1.json"))
    if manifest["schema"]!="PERTURBATION_COMMITTED_OUTPUTS_SHA256_MANIFEST_V1":
        raise ValueError("STOP: output manifest changed")
    screens=screen_metadata(repo,manifest)
    for k in ("iTF_RNA","iMG_RNA","iTF_ADT","iMG_ADT"):
        if screens[k]["targets"]-b["targets"]!={"ARID5B"}:
            raise ValueError("STOP: source guide vs published target mismatch "+k)
    if screens["Day8"]["targets"]&b["targets"]:
        raise ValueError("STOP: Day8 claims an authenticated overlap")
    if len(screens["iTF_RNA"]["features"]&screens["iMG_RNA"]["features"])!=13489:
        raise ValueError("STOP: published transcriptome common-row census")
    if len(screens["iTF_ADT"]["features"]&screens["iMG_ADT"]["features"])!=167:
        raise ValueError("STOP: protein published common-row census")
    day8=parse_csv(frozen_text(repo,"reference/GSE178317_sgrna_library_suppl_table5.csv"))
    day8_set={x["target_gene"] for x in day8 if x["target_gene"]!="NTC"}
    if len(day8_set)!=39 or day8_set!=screens["Day8"]["targets"]:
        raise ValueError("STOP: Day8 direct target source mismatch")
    hmc=parse_csv(frozen_text(repo,"evidence/gse293118/GSE293118_perturbation_identity.csv"))
    hmc6={x["target_id"] for x in hmc if x["target_class"]=="gene"}
    if len(hmc6)!=6 or hmc6&b["targets"]:
        raise ValueError("STOP: HMC3 direct gene target mapping changed")
    bulk=json.loads(frozen_text(repo,"evidence/bulk_physical_v2/BULK_DISEASE_CONTEXT_SUMMARY.json"))
    drug=json.loads(frozen_text(repo,"evidence/bulk_physical_v2/GSE254205_drug_response_summary_v2.json"))
    if bulk["GSE240609"]["replicates_per_design_cell"]!=1 or bulk["GSE240609"]["uncertainty_estimable"] is not False or bulk["GSE241858"]["baseline"]["clones_per_genotype"]!=2:
        raise ValueError("STOP: bulk design census drift")
    if (drug["genes_assayed"],drug["genes_assayed_but_undetected"],drug["samples"])!=(58395,22278,9):
        raise ValueError("STOP: drug measured/undetected assay status drift")
    wpe=frozen_text(repo,"GSE311359_BIN1_IDENTITY_RESOLVED_20260924.md").decode()
    if not all(s in wpe for s in ("BIN1_enh_1","BIN1_enh_2","BIN1_enh_2_AS","381","379","36,982")):
        raise ValueError("STOP: source-verified BIN1 identity document changed")
    # These axes describe what is scientifically admissible, not who/what 'wins'.
    strata=[
      ("GSE178317_Day8_RNA","GSE178317","microglia_pooled_day8","direct_CRISPRi","RNA_DE",day8_set,"one pooled preparation; four capture wells", "DEVELOPMENT"),
      ("GSE335887_iTF_RNA","GSE335887","WTC11_TF_day12","direct_CRISPRi","RNA_DE",b["targets"],"one parent line; two iTF GEX preparations in merged DE", "RESERVED_NUMERIC_DE"),
      ("GSE335887_iMG_RNA","GSE335887","WTC11_cytokine_day28","direct_CRISPRi","RNA_DE",b["targets"],"same WTC11 parent; independent prep count not authenticated", "RESERVED_NUMERIC_DE"),
      ("GSE335887_iTF_ADT","GSE335887","WTC11_TF_day12","direct_CRISPRi","PROTEIN_ADT",b["targets"],"paired subset of iTF RNA library, not independent", "RESERVED_NUMERIC_PROTEIN"),
      ("GSE335887_iMG_ADT","GSE335887","WTC11_cytokine_day28","direct_CRISPRi","PROTEIN_ADT",b["targets"],"paired with iMG RNA library, not independent", "RESERVED_NUMERIC_PROTEIN"),
      ("GSE301119_macrophage_CRISPRi","GSE301119","primary_macrophage_two_donors","direct_CRISPRi","RNA_DE",cs_sets["CRISPRi"],"two donors; guide cells are not donors", "DEVELOPMENT"),
      ("GSE301119_macrophage_CRISPRa","GSE301119","primary_macrophage_two_donors","direct_CRISPRa","RNA_DE",cs_sets["CRISPRa"],"two donors; opposite intervention", "DEVELOPMENT"),
      ("GSE293118_HMC3_direct","GSE293118","HMC3_immortalized","direct_CRISPRi","RNA_DE",hmc6,"six directly measurable targets; one-guide cases", "DEVELOPMENT"),
      ("GSE311359_iPSC_microglia_cis","GSE311359","iPSC_microglia_seven_samples","cis_regulatory_CRISPRi","RNA_DE",None,"381 distinct capture IDs; BIN1 three separate cis elements; V2 rebuild required", "DEVELOPMENT"),
      ("GSE175721_organoid_CRISPR","GSE175721","organoid_microglia","guide_unassigned","RNA",None,"authentic cell→guide join absent", "RESERVED_GUIDE_BLOCKED"),
      ("GSE254205_APOE4_GNE","GSE254205","APOE4_iMG_amyloid_one_model","drug_plus_amyloid","BULK_RNA",None,"three replicates/condition; drug not CRISPR", "DEVELOPMENT_BULK"),
      ("GSE241858_TREM2_R47H","GSE241858","iPSC_microglia_clones","genotype_by_cytokine","BULK_RNA",None,"two independent clones/genotype", "DEVELOPMENT"),
      ("GSE240609_APOE3ch","GSE240609","CD11b_post_neuron_coculture","genotype_by_coculture","BULK_RNA",None,"one sample/design cell; no population SE", "DEVELOPMENT")
    ]
    strata_out={k:{"study":study,"biological_system":system,"intervention":intervention,"readout":readout,
                   "authenticated_direct_targets":None if targets is None else len(targets),
                   "authenticated_direct_target_labels":None if targets is None else sorted(targets),
                   "target_set_sha256":None if targets is None else members_root(targets),
                   "independent_unit_caveat":unit,"outcome_exposure":exposure}
                for k,study,system,intervention,readout,targets,unit,exposure in strata}
    pairs=[]
    for a,c in combinations(strata,2):
        ak,studyA,sysA,interA,readA,targA,unitA,expA=a
        bk,studyB,sysB,interB,readB,targB,unitB,expB=c
        overlap=len(targA&targB) if targA is not None and targB is not None else None
        if studyA==studyB=="GSE335887":
            if readA==readB=="RNA_DE":
                scope="WITHIN_WTC11_PROTOCOL_PLUS_AGE__NOT_INDEPENDENT_DONORS"
            elif readA==readB=="PROTEIN_ADT":
                scope="WITHIN_WTC11_PROTEIN_PROTOCOL_PLUS_AGE__PROCESSED_ANTIBODY_IDS_UNVERIFIED"
            else:scope="PAIRED_MULTIMODAL_ASSAY__NOT_INDEPENDENT_REPLICATION"
        elif studyA==studyB=="GSE301119":
            scope="OPPOSITE_CRISPR_MODES_INTERNAL_CONTROL__NOT_SAME_INTERVENTION"
        elif targA is None or targB is None:
            scope="NOT_DIRECT_TARGET_EQUIVALENT__INTERVENTION_OR_JOIN_DIFFERENT"
        elif overlap==0:
            scope="NO_SHARED_AUTHENTICATED_DIRECT_TARGET"
        else:
            scope="TARGET_LABEL_OVERLAP_ONLY__CROSS_STUDY_BIOLOGY_AND_UNIT_UNVERIFIED"
        pairs.append({"a":ak,"b":bk,"shared_direct_target_labels":overlap,
                      "shared_direct_target_names":None if targA is None or targB is None else sorted(targA&targB),
                      "comparison_scope":scope,"automatically_pool":False,
                      "independent_confirmation_authorized":False})
    pair_idx={(p["a"],p["b"]):p for p in pairs}
    def pair(a,b):
        return pair_idx.get((a,b)) or pair_idx[(b,a)]
    if (pair("GSE335887_iTF_RNA","GSE335887_iMG_RNA")["shared_direct_target_labels"]!=30 or
        pair("GSE178317_Day8_RNA","GSE335887_iTF_RNA")["shared_direct_target_labels"]!=0 or
        pair("GSE301119_macrophage_CRISPRi","GSE301119_macrophage_CRISPRa")["shared_direct_target_labels"]!=204 or
        pair("GSE335887_iTF_RNA","GSE301119_macrophage_CRISPRi")["shared_direct_target_labels"]!=1):
        raise ValueError("STOP: scientifically material pairwise target overlap changed")
    return {"schema":"JEPA_ETL_WPF_COMPARABILITY_MATRIX_V1",
        "source_parent_commit":"3ad4871baf23031c48835da7ef6b18ffe19c836e",
        "input_git_blob_sha1":BLOBS,"feature_reference_source":b["source_ref"],
        "exposure_scope":"IDENTIFIER_COLUMNS_ONLY_IN_RESERVED_CRISPRBRAIN_SCREENS",
        "no_protected_numeric_response_values_inspected":True,"no_perturbation_predictor_fitted":True,
        "source_inventory_status":"16_PRIMARY_ASSETS_PHYSICALLY_VERIFIED__STUDY_ETL_LABELS_SUPERSEDED_AFTER_WPA",
        "gse335887":{"published_targets":31,"authenticated_guide_targets":30,
          "unauthenticated_published_targets":["ARID5B"],"guides":65,
          "antibody_panel":180,"processed_protein_shared_label_count":167,
          "published_RNA_screenwide_shared_row_label_count":13489,
          "published_RNA_row_masks_are_not_raw_assay_detection_masks":True,
          "shared_parent_line":"WTC11","protocol_and_age_confound":True,
          "run_level_10x_chemistry_verified":False,"independent_iMG_preparation_count_verified":False},
        "gse301119":{"internal_validation":cs_details,
          "shared_CRISPRi_CRISPRa_target_names":204,
          "CRISPRi_only_target_names":sorted(cs_sets["CRISPRi"]-cs_sets["CRISPRa"]),
          "CRISPRa_only_target_names":sorted(cs_sets["CRISPRa"]-cs_sets["CRISPRi"]),
          "cross_modality_feature_intersection_verified":False,
          "assayed_undetected_cannot_alone_prove_silencing":True,
          "no_population_inference_two_donors":True},
        "gse311359":{"feature_ids_distinct":381,"duplicate_display_name":"BIN1",
          "distinct_depositor_cis_feature_ids":["BIN1_enh_1","BIN1_enh_2","BIN1_enh_2_AS"],
          "feature_id_to_functional_cis_target_verified":False,
          "physical_V2_id_keyed_rebuild_completed":False,
          "other_82_name_collision_absence":"CLAUDE_SOURCE_EXHAUSTIVE_REPORT__V2_PARITY_NOT_YET_PROVED"},
        "gse175721":{"cell_guide_join_authenticated":False,"status":"STOP_AUTHOR_GUIDE_ASSIGNMENT"},
        "bulk":{"GSE254205":drug,"GSE241858":bulk["GSE241858"],
                "GSE240609":bulk["GSE240609"]},
        "strata":strata_out,"pair_count":len(pairs),"pairs":pairs,
        "jepa_training_authorized":False,"therapeutic_ranking_authorized":False}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists():raise SystemExit("STOP: refuse overwrite")
    report=build(args.repo)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n")
    print(json.dumps({"strata":len(report["strata"]),"pairs":report["pair_count"],
      "gse335887_authenticated_targets":report["gse335887"]["authenticated_guide_targets"],
      "gse301119_shared_targets":report["gse301119"]["shared_CRISPRi_CRISPRa_target_names"],
      "numeric_reserved_outcomes_inspected":False}))
if __name__=="__main__":main()
