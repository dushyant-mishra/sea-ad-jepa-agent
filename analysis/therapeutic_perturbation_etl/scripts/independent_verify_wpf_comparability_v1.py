#!/usr/bin/env python3
"""Independent WP-F set algebra + scientific-authority negative checks.

Runs on the generated physical-source-bound matrix, not the producing code.
Adversarial mode mutates a genuine receipt and requires all mutations to STOP.
"""
import argparse,copy,hashlib,json
from itertools import combinations
from pathlib import Path

def root(labels):
    return hashlib.sha256(("\n".join(sorted(labels))+"\n").encode()).hexdigest()

def check(report):
    if report.get("schema")!="JEPA_ETL_WPF_COMPARABILITY_MATRIX_V1":
        raise ValueError("STOP: schema")
    if report.get("no_protected_numeric_response_values_inspected") is not True:
        raise ValueError("STOP: protected outcome exposure")
    if report.get("no_perturbation_predictor_fitted") is not True:
        raise ValueError("STOP: fitted model")
    if report.get("jepa_training_authorized") is not False or report.get("therapeutic_ranking_authorized") is not False:
        raise ValueError("STOP: training or therapeutic promotion")
    strata=report["strata"]
    if len(strata)!=13 or set(strata)!={
        "GSE178317_Day8_RNA","GSE335887_iTF_RNA","GSE335887_iMG_RNA",
        "GSE335887_iTF_ADT","GSE335887_iMG_ADT",
        "GSE301119_macrophage_CRISPRi","GSE301119_macrophage_CRISPRa",
        "GSE293118_HMC3_direct","GSE311359_iPSC_microglia_cis",
        "GSE175721_organoid_CRISPR","GSE254205_APOE4_GNE",
        "GSE241858_TREM2_R47H","GSE240609_APOE3ch"}:
        raise ValueError("STOP: missing/extra experimental strata")
    sets={}
    for k,row in strata.items():
        labels=row["authenticated_direct_target_labels"]
        n=row["authenticated_direct_targets"]
        if labels is None:
            if n is not None or row["target_set_sha256"] is not None:
                raise ValueError("STOP: claimed unknown target identity")
            sets[k]=None
        else:
            if len(labels)!=len(set(labels)) or len(labels)!=n or root(labels)!=row["target_set_sha256"]:
                raise ValueError("STOP: target identity root or population")
            if any(not isinstance(t,str) or not t for t in labels):
                raise ValueError("STOP: invalid label")
            sets[k]=set(labels)
        if not row["independent_unit_caveat"] or not row["outcome_exposure"]:
            raise ValueError("STOP: missing biological/exposure scope")
    if report["gse335887"]["authenticated_guide_targets"]!=30 or report["gse335887"]["published_targets"]!=31:
        raise ValueError("STOP: deposited vs published target count")
    if report["gse335887"]["unauthenticated_published_targets"]!=["ARID5B"]:
        raise ValueError("STOP: ARID5B identity falsely promoted")
    for k in ("GSE335887_iTF_RNA","GSE335887_iMG_RNA","GSE335887_iTF_ADT","GSE335887_iMG_ADT"):
        if len(sets[k])!=30 or "ARID5B" in sets[k]:
            raise ValueError("STOP: unauthenticated ARID5B in source guides")
        if strata[k]["study"]!="GSE335887":
            raise ValueError("STOP: wrong study scope")
    if any(strata[k]["outcome_exposure"]!="RESERVED_NUMERIC_DE"
           for k in ("GSE335887_iTF_RNA","GSE335887_iMG_RNA")):
        raise ValueError("STOP: reserved RNA outcome exposure")
    if any(strata[k]["outcome_exposure"]!="RESERVED_NUMERIC_PROTEIN"
           for k in ("GSE335887_iTF_ADT","GSE335887_iMG_ADT")):
        raise ValueError("STOP: reserved protein outcome exposure")
    if len(sets["GSE301119_macrophage_CRISPRi"])!=206 or len(sets["GSE301119_macrophage_CRISPRa"])!=206:
        raise ValueError("STOP: donor-aware modality target set")
    c=report["gse301119"]
    iset=sets["GSE301119_macrophage_CRISPRi"];aset=sets["GSE301119_macrophage_CRISPRa"]
    if len(iset&aset)!=204 or sorted(iset-aset)!=["RPL11","RPL7"] or sorted(aset-iset)!=["CDKN2A","TP53"]:
        raise ValueError("STOP: CRISPRi/a modality target mismatch")
    if c["cross_modality_feature_intersection_verified"] is not False or c["assayed_undetected_cannot_alone_prove_silencing"] is not True:
        raise ValueError("STOP: unsupported CRISPR modality or silencing claim")
    if c["no_population_inference_two_donors"] is not True:
        raise ValueError("STOP: donor population claim")
    for mode,med,count_und,zero,ngenes in (
       ("CRISPRi",-1.05180469086264,29,["ADGRG1","GPR87","TREML4"],36601),
       ("CRISPRa",1.97309634514678,1,["TREML4"],19162)):
        x=c["internal_validation"][mode]
        if x["n_independent_donors"]!=2 or not x["nonpopulation_inference"]:
            raise ValueError("STOP: nonpopulation donor scope")
        if abs(x["engagement_median"]-med)>1e-10 or x["genes_assayed"]!=ngenes or x["own_gene_status"]["ASSAYED_UNDETECTED"]!=count_und:
            raise ValueError("STOP: modality receipt changed")
        if x["assayed_undetected_with_zero_engagement"]!=zero:
            raise ValueError("STOP: undetected target is not automatically valid knockdown")
    if report["gse311359"]["physical_V2_id_keyed_rebuild_completed"] is not False or report["gse311359"]["feature_id_to_functional_cis_target_verified"] is not False:
        raise ValueError("STOP: BIN1 V2/cis validation falsely completed")
    if report["gse311359"]["distinct_depositor_cis_feature_ids"]!=["BIN1_enh_1","BIN1_enh_2","BIN1_enh_2_AS"]:
        raise ValueError("STOP: three BIN1 cis features collapsed")
    if report["gse175721"]["cell_guide_join_authenticated"] is not False:
        raise ValueError("STOP: author-blocked guide join falsely accepted")
    pairs=report["pairs"]
    if report["pair_count"]!=78 or len(pairs)!=78:
        raise ValueError("STOP: incomplete pairwise matrix")
    got=set()
    for p in pairs:
        a,b=p["a"],p["b"];key=frozenset((a,b))
        if a not in strata or b not in strata or a==b or key in got:
            raise ValueError("STOP: duplicate or invalid pair")
        got.add(key)
        expected=None if sets[a] is None or sets[b] is None else sorted(sets[a]&sets[b])
        count=None if expected is None else len(expected)
        if p["shared_direct_target_names"]!=expected or p["shared_direct_target_labels"]!=count:
            raise ValueError("STOP: pairwise target intersection mismatch")
        if p["automatically_pool"] is not False or p["independent_confirmation_authorized"] is not False:
            raise ValueError("STOP: illicit pooling or confirmation")
        if a.startswith("GSE335887") and b.startswith("GSE335887"):
            if strata[a]["readout"]!=strata[b]["readout"] and p["comparison_scope"]!="PAIRED_MULTIMODAL_ASSAY__NOT_INDEPENDENT_REPLICATION":
                raise ValueError("STOP: RNA/protein called independent")
            if strata[a]["readout"]==strata[b]["readout"] and "WITHIN_WTC11_" not in p["comparison_scope"]:
                raise ValueError("STOP: within-parental protocol+age called cross-donor")
        if {a,b}=={"GSE301119_macrophage_CRISPRi","GSE301119_macrophage_CRISPRa"} and p["comparison_scope"]!="OPPOSITE_CRISPR_MODES_INTERNAL_CONTROL__NOT_SAME_INTERVENTION":
            raise ValueError("STOP: opposite CRISPR interventions conflated")
    if len(got)!=len(list(combinations(strata,2))):
        raise ValueError("STOP: incomplete 78 unordered pairs")
    return {"strata":len(strata),"pairs_checked":len(got),
       "same_parental_WTC11_source_authenticated_targets":30,
       "shared_CRISPRi_CRISPRa_macrophage_target_names":204,
       "protected_numeric_outcomes_inspected":False,"jepa_training_authorized":False}

def adversarial(report):
    # Each alteration is made on a true source-bound output; the independent
    # checker must STOP even after the JSON is reserialized without error.
    changes=[
      ("false_ARID5B_guide_authority",lambda x:x["gse335887"].update(authenticated_guide_targets=31)),
      ("erase_ARID5B_exclusion",lambda x:x["gse335887"].update(unauthenticated_published_targets=[])),
      ("source_set_forged",lambda x:x["strata"]["GSE335887_iTF_RNA"]["authenticated_direct_target_labels"].append("ARID5B")),
      ("source_root_rehashed_but_wrong",lambda x:x["strata"]["GSE335887_iTF_RNA"].update(target_set_sha256="0"*64)),
      ("paired_library_claims_independent",lambda x:x["pairs"].__setitem__(0,{**x["pairs"][0],"independent_confirmation_authorized":True})),
      ("underreported_pair_count",lambda x:x["pairs"].pop()),
      ("fake_shared_target",lambda x:x["pairs"].__setitem__(0,{**x["pairs"][0],"shared_direct_target_labels":77})),
      ("opposite_mode_pooled",lambda x:[p.update(comparison_scope="SAME_INTERVENTION") for p in x["pairs"] if {p["a"],p["b"]}=={"GSE301119_macrophage_CRISPRi","GSE301119_macrophage_CRISPRa"}]),
      ("BIN1_false_functional_cis",lambda x:x["gse311359"].update(feature_id_to_functional_cis_target_verified=True)),
      ("BIN1_false_V2",lambda x:x["gse311359"].update(physical_V2_id_keyed_rebuild_completed=True)),
      ("GSE175721_false_join",lambda x:x["gse175721"].update(cell_guide_join_authenticated=True)),
      ("numeric_exposure_flag_forged",lambda x:x.update(no_protected_numeric_response_values_inspected=False)),
      ("WTC11_profile_unblinded",lambda x:x["strata"]["GSE335887_iMG_RNA"].update(outcome_exposure="INSPECTED")),
      ("macrophage_faux_population",lambda x:x["gse301119"].update(no_population_inference_two_donors=False)),
      ("CRISPRi_undetected_zero_dropped",lambda x:x["gse301119"]["internal_validation"]["CRISPRi"].update(assayed_undetected_with_zero_engagement=[])),
      ("false_cross_modality_gene_space",lambda x:x["gse301119"].update(cross_modality_feature_intersection_verified=True)),
      ("wrong_microglial_donor_count",lambda x:x["strata"]["GSE335887_iMG_RNA"].update(independent_unit_caveat="")),
    ]
    for label,edit in changes:
        copied=copy.deepcopy(report);edit(copied)
        try:check(copied)
        except ValueError:continue
        raise AssertionError("RED-TEAM MISS: "+label)
    return len(changes)

def main():
    p=argparse.ArgumentParser();p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--adversarial",action="store_true")
    args=p.parse_args();x=json.loads(args.receipt.read_text())
    good=check(x)
    if args.adversarial:good["redteam_falsifications_stopped"]=adversarial(x)
    print(json.dumps(good,sort_keys=True))
if __name__=="__main__":main()
