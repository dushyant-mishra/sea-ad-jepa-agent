#!/usr/bin/env python3
"""Bind verified HGNC July 2026 exact-symbol metadata to existing FrozenAnnotation.

No expression outcomes, detected-gene masks, gene-alias guesses, biological
replication, FULL104 alignment or JEPA training authority are produced.
"""
import argparse,hashlib,json,re,sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"src"))
from sea_ad_jepa.perturbation.cross_study_feature_contract_v1 import (
    FeatureMapEntry, freeze_annotation,
)

PARENT_SHA="e73e9259177884b5994fc81ed733c1b3d4df34c84290bc9dddc86e960d5d6419"
EXPECTED_SOURCE_SHAS={
 "day12_iTF_CROP_RNA":{
   "source_compressed_sha256":"58c48fa4400d469a0e616940070bb426a71df77ff12e6de2bbf8efb119ff884e",
   "source_uncompressed_sha256":"6f65d728699863d207012227c72ac88cc2033cc1277ee6a74132bac8f3afbea8"},
 "day28_iPSC_CROP_RNA":{
   "source_compressed_sha256":"818ae3c383811c94ab56ea588d34fbaaeaa1c808673125f68d62644e6ca19606",
   "source_uncompressed_sha256":"1efd4d840a46f0de32ce7839043df33e07db04d92f826855923e24f8fd36cdd2"},
}
HGNC_ID=re.compile(r"^HGNC:[1-9]\d*$")
ENSG=re.compile(r"^ENSG\d{11}$")
def freeze_verified_report(report, *, require_real_census=True):
    if report.get("schema")!="HGNC_2026Q3_MICROGLIA_31TARGET_METADATA_CROSSWALK_V1":
        raise ValueError("STOP: wrong crosswalk schema")
    if report.get("HGNC_download_sha256")!=PARENT_SHA or report.get("HGNC_download_bytes")!=16913890:
        raise ValueError("STOP: frozen HGNC source bytes/digest mismatch")
    if report.get("response_values_inspected") is not False or report.get("training_authorized") is not False:
        raise ValueError("STOP: crosswalk is not metadata-only")
    for screen,expected in EXPECTED_SOURCE_SHAS.items():
        observed=report.get("screens",{}).get(screen,{})
        for namespace,sha in expected.items():
            if observed.get(namespace)!=sha:
                raise ValueError("STOP: wrong CRISPRbrain "+namespace+" for "+screen)
    data=report["crosswalk"]
    feature_map=data["collision_free_shared_feature_map"]
    target_map=data["target_primary_map"]
    missing=data["labels_absent_from_primary_release"]
    ambiguous=data["labels_ambiguous_primary"]
    collisions=data["ensembl_collisions"]
    if collisions or ambiguous:raise ValueError("STOP: ambiguous or colliding mappings require review")
    if len(feature_map)!=data["exact_primary_feature_labels_mapped_collision_free"]:
        raise ValueError("STOP: feature map census changed")
    if len(target_map)!=data["exact_primary_targets_mapped"]:
        raise ValueError("STOP: target map census changed")
    if len(feature_map)+len(missing)!=data["common_literal_feature_count"]:
        raise ValueError("STOP: unknown features unaccounted for")
    if set(feature_map)&set(missing):raise ValueError("STOP: mapped and excluded overlap")
    if len(set(missing))!=len(missing):raise ValueError("STOP: duplicate exclusions")
    if require_real_census and (data["common_target_count"]!=31
         or len(target_map)!=31 or data["common_literal_feature_count"]!=13489
         or len(feature_map)!=13373 or len(missing)!=116):
        raise ValueError("STOP: prior physical census mismatch")
    combined=dict(feature_map)
    for sym,item in target_map.items():
        if sym in combined and combined[sym]!=item:
            raise ValueError("STOP: same HGNC symbol maps differently as feature and target")
        combined[sym]=item
    e={}
    for sym,item in combined.items():
        if not sym or sym!=sym.strip() or not isinstance(item,dict):
            raise ValueError("STOP: malformed label")
        ens=item.get("ensembl");hgnc=item.get("hgnc_id")
        if not isinstance(ens,str) or not ENSG.fullmatch(ens) or not isinstance(hgnc,str) or not HGNC_ID.fullmatch(hgnc):
            raise ValueError("STOP: malformed HGNC/Ensembl pair")
        if ens in e and e[ens]!=sym:
            raise ValueError("STOP: duplicate canonical Ensembl across labels")
        e[ens]=sym
    annotations=tuple(
        FeatureMapEntry(namespace="HGNC_SYMBOL",source_id=sym,
            canonical_ensembl=item["ensembl"],annotation_evidence_id=item["hgnc_id"],
            mapping_status="PRIMARY_ID")
        for sym,item in combined.items()
    )
    freeze=freeze_annotation(release="HGNC_COMPLETE_SET_2026-07-07",
        annotation_file_sha256=PARENT_SHA,entries=annotations)
    return {"schema":"GSE335887_PRIMARY_HGNC_FROZEN_ANNOTATION_V1",
        "metadata_parent_sha256":hashlib.sha256(json.dumps(report,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest(),
        "HGNC_source_sha256":PARENT_SHA,
        "CRISPRbrain_screen_source_sha256":EXPECTED_SOURCE_SHAS,
        "annotated_symbol_count":len(freeze.entries),
        "mapped_common_measured_feature_labels":len(feature_map),
        "mapped_common_intervention_target_labels":len(target_map),
        "unresolved_shared_feature_labels":missing,
        "unresolved_shared_feature_count":len(missing),
        "source_type":"EXACT_APPROVED_PRIMARY_SYMBOL_ONLY",
        "biological_sample_overlap":"SAME_WTC11_PARENTAL_LINE",
        "assay_detection_masks_verified":False,
        "full104_alignment_authorized":False,
        "perturbation_prediction_authorized":False,
        "training_authorized":False,
        "frozen_annotation_body":freeze.body(),
        "frozen_annotation_contract_sha256":freeze.contract_sha256}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--crosswalk-json",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists():raise SystemExit("STOP: refuse overwrite")
    v=json.loads(args.crosswalk_json.read_text())
    result=freeze_verified_report(v)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"frozen_annotation_contract_sha256":result["frozen_annotation_contract_sha256"],
      "entries":result["annotated_symbol_count"],
      "shared_features":result["mapped_common_measured_feature_labels"],
      "unresolved":result["unresolved_shared_feature_count"]}))
if __name__=="__main__":main()
