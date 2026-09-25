#!/usr/bin/env python3
"""Physically bind immutable HGNC 2026-Q3 metadata to the two 31-target screens.

Only the Gene and name metadata columns of the two verified CRISPRbrain tables
are read. NO aliases are silently resolved. NOT training/biological authority.
"""
import argparse,csv,hashlib,io,json,re,urllib.request
from pathlib import Path
from microglia_metadata_overlap_v1 import SCREENS,scan_identifiers,digest_members
ROOT=Path("analysis/therapeutic_perturbation_etl")
HGNC_URL="https://storage.googleapis.com/public-download-files/hgnc/archive/archive/quarterly/tsv/hgnc_complete_set_2026-07-07.tsv"
RELEASE="HGNC_COMPLETE_SET_QUARTERLY_2026-07-07"
ENSG=re.compile(r"^ENSG[0-9]{11}$")
SOURCES=("day12_iTF_CROP_RNA","day28_iPSC_CROP_RNA")
def source_rows(data):
    txt=data.decode("utf-8-sig")
    rd=csv.DictReader(io.StringIO(txt,newline=""),delimiter="\t")
    cols=set(rd.fieldnames or [])
    if not {"hgnc_id","symbol","status","ensembl_gene_id"}<=cols:
        raise ValueError("STOP: HGNC release schema mismatch")
    approved={};ambiguous=set();source_n=0
    for row in rd:
        source_n+=1
        if row["status"]!="Approved":continue
        sym=row["symbol"].strip();ensg=row["ensembl_gene_id"].strip()
        if not sym or not ensg or not ENSG.fullmatch(ensg):continue
        val={"ensembl":ensg,"hgnc_id":row["hgnc_id"]}
        if sym in approved and approved[sym]!=val:ambiguous.add(sym)
        else:approved[sym]=val
    for sym in ambiguous:approved.pop(sym,None)
    if not approved or source_n<1000:raise ValueError("STOP: suspiciously empty HGNC release")
    return approved,ambiguous,source_n
def map_features(a,b,approved,ambiguous):
    targets=a["targets"]&b["targets"];common=a["features"]&b["features"]
    assigned={};missing=[];ambig=[]
    for label in sorted(common):
        if label in ambiguous:ambig.append(label)
        elif label not in approved:missing.append(label)
        else:assigned[label]=approved[label]
    by_ensg={}
    for label,v in assigned.items():by_ensg.setdefault(v["ensembl"],[]).append(label)
    collisions={k:v for k,v in by_ensg.items() if len(v)>1}
    safe={s:v for s,v in assigned.items() if v["ensembl"] not in collisions}
    mapped_t={t:approved[t] for t in sorted(targets) if t in approved and t not in ambiguous}
    return {"common_literal_feature_count":len(common),"common_target_count":len(targets),
        "common_target_set_sha256":digest_members(targets),
        "exact_primary_targets_mapped":len(mapped_t),"target_names_not_mapped":sorted(targets-set(mapped_t)),
        "exact_primary_feature_labels_mapped_collision_free":len(safe),
        "labels_absent_from_primary_release":sorted(missing),
        "labels_ambiguous_primary":sorted(ambig),
        "ensembl_collisions":collisions,
        "target_primary_map":mapped_t,"collision_free_shared_feature_map":safe,
        "aliases_auto_mapped":False,"unresolved_features_treated_as_zero":False}
def build(repo,download):
    if len(download)>30000000:raise ValueError("STOP: unexpectedly large HGNC input")
    approved,ambig,n=source_rows(download)
    m=json.loads((repo/ROOT/"evidence/COMMITTED_OUTPUTS_SHA256_MANIFEST_V1.json").read_text())
    digest_map={x["path"]:x for x in m["files"]}; screens={}
    for key in SOURCES:
        filename,modality,expected,uncompressed,exposed=SCREENS[key]
        path=ROOT/"outputs/crisprbrain"/filename
        e=digest_map[path.as_posix()]
        compressed=(repo/path).read_bytes()
        if len(compressed)!=e["bytes"]:raise ValueError("STOP: wrong screen byte count")
        observed=scan_identifiers(compressed,e["sha256"],uncompressed)
        if len(observed["targets"])!=expected:raise ValueError("STOP: wrong screen target census")
        screens[key]=observed
    result=map_features(*(screens[s] for s in SOURCES),approved,ambig)
    if result["common_target_count"]!=31 or result["common_literal_feature_count"]!=13489:
        raise ValueError("STOP: pre-existing 31-target overlap changed")
    return {"schema":"HGNC_2026Q3_MICROGLIA_31TARGET_METADATA_CROSSWALK_V1",
        "HGNC_release":RELEASE,"HGNC_download_url":HGNC_URL,
        "HGNC_download_sha256":hashlib.sha256(download).hexdigest(),
        "HGNC_download_bytes":len(download),"HGNC_rows":n,
        "screens":{k:{"source_compressed_sha256":next(x for x in m["files"] if x["path"].endswith(SCREENS[k][0]))["sha256"],
                     "target_set_sha256":v["target_set_sha256"],"feature_set_sha256":v["feature_set_sha256"]} for k,v in screens.items()},
        "response_values_inspected":False,"mapping_scope":"PRIMARY_HGNC_EXACT_ONLY",
        "annotation_source_root_physically_measured":True,
        "full104_feature_alignment_authorized":False,"training_authorized":False,
        "crosswalk":result}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo",type=Path,required=True);ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise SystemExit("STOP: refuse overwrite")
    req=urllib.request.Request(HGNC_URL,headers={"User-Agent":"JEPA-METADATA-HGNC-Q3/1.0"})
    with urllib.request.urlopen(req,timeout=100) as u:blob=u.read(30000001)
    receipt=build(a.repo,blob)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(receipt,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:receipt["crosswalk"][k] for k in ("common_target_count","exact_primary_targets_mapped","common_literal_feature_count","exact_primary_feature_labels_mapped_collision_free")})+" HGNC_SHA "+receipt["HGNC_download_sha256"])
if __name__=="__main__":main()
