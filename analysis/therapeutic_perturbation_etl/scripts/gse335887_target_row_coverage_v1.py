#!/usr/bin/env python3
"""Source-hash-bound per-target PUBLISHED DE ROW coverage, no numeric effects.

Important: DE row presence != raw assay feature presence or detectability.
This module reads Gene/name columns only; never calculates expression, FDR, or
any new outcome from the two protected 31-target screens.
"""
import argparse,csv,gzip,hashlib,io,json
from pathlib import Path
from microglia_metadata_overlap_v1 import ROOT,SCREENS,digest_members
KEYS=("day12_iTF_CROP_RNA","day28_iPSC_CROP_RNA")
def scan_pair_rows(data,expected_compressed,expected_plain):
    if hashlib.sha256(data).hexdigest()!=expected_compressed:
        raise ValueError("STOP: compressed source SHA mismatch")
    plain=gzip.decompress(data)
    if hashlib.sha256(plain).hexdigest()!=expected_plain:
        raise ValueError("STOP: decompressed source SHA mismatch")
    rd=csv.reader(io.TextIOWrapper(io.BytesIO(plain),encoding="utf-8-sig",newline=""))
    head=next(rd)
    if head.count("Gene")!=1 or head.count("name")!=1:raise ValueError("STOP: identifier headers")
    gi,ti=head.index("Gene"),head.index("name")
    target_gene={};total=0
    for row in rd:
        if len(row)!=len(head):raise ValueError("STOP: malformed provider row")
        gene,target=row[gi].strip(),row[ti].strip()
        if not gene or not target:raise ValueError("STOP: empty target/gene identity")
        dest=target_gene.setdefault(target,set())
        if gene in dest:raise ValueError("STOP: duplicate published target×gene row")
        dest.add(gene);total+=1
    if not total:raise ValueError("STOP: empty source table")
    return target_gene,total
def derive(a,b, approved_primary=None):
    if set(a)!=set(b) or len(a)!=31:
        raise ValueError("STOP: 31 common target identities required")
    primary=set(approved_primary) if approved_primary is not None else None
    all_a=set().union(*a.values());all_b=set().union(*b.values())
    common=all_a&all_b
    if len(common)!=13489:raise ValueError("STOP: published union intersection changed")
    if primary is not None and (len(primary)!=13373 or not primary<=common):
        raise ValueError("STOP: wrong frozen primary gene universe")
    per=[]
    for target in sorted(a):
        shared=a[target]&b[target]
        per.append({
          "perturbed_target":target,
          "iTF_published_de_rows":len(a[target]),
          "iMG_published_de_rows":len(b[target]),
          "both_published_de_row_count":len(shared),
          "both_published_de_row_set_sha256":digest_members(shared),
          "both_primary_HGNC_published_de_rows":len(shared&primary) if primary is not None else None,
          "iTF_published_self_row":target in a[target],
          "iMG_published_self_row":target in b[target],
          "iTF_missing_from_published_de_rows_vs_whole_screen":len(all_a-a[target]),
          "iMG_missing_from_published_de_rows_vs_whole_screen":len(all_b-b[target]),
          "missing_row_interpretation":"UNRESOLVED_PROVIDER_FILTERING_VS_RAW_ASSAY__NEVER_ZERO_FILL"
        })
    return {"schema":"GSE335887_TARGET_SPECIFIC_PUBLISHED_DE_ROW_SUPPORT_V1",
       "source_role":"METADATA_ONLY_TWO_RESERVED_SCREENS_NUMERIC_RESPONSE_VALUES_UNREAD",
       "targets":31,"same_target_set_sha256":digest_members(a),
       "shared_screenwide_published_gene_label_count":len(common),
       "shared_screenwide_published_gene_label_sha256":digest_members(common),
       "shared_primary_HGNC_count":len(primary) if primary is not None else None,
       "per_target":per,
       "not_assay_measurement_authority":True,"raw_assay_gene_detection_NOT_VERIFIED":True,
       "no_effect_or_FDR_values_examined":True,"biological_replication_NOT_ESTABLISHED":True,
       "independent_confirmation_NOT_AUTHORIZED":True,"jepa_training_authorized":False}
def build(repo,frozen=None):
    m=json.loads((repo/ROOT/"evidence/COMMITTED_OUTPUTS_SHA256_MANIFEST_V1.json").read_text())
    if m["schema"]!="PERTURBATION_COMMITTED_OUTPUTS_SHA256_MANIFEST_V1":raise ValueError("STOP: manifest schema")
    lookup={x["path"]:x for x in m["files"]}
    scans={};sources={}
    for key in KEYS:
        filename,mode,nt,plain,exposed=SCREENS[key]
        path=ROOT/"outputs/crisprbrain"/filename
        ent=lookup.get(path.as_posix())
        if not ent:raise ValueError("STOP: unmanifested source")
        blob=(repo/path).read_bytes()
        if len(blob)!=ent["bytes"]:raise ValueError("STOP: compressed byte count")
        target_gene,n=scan_pair_rows(blob,ent["sha256"],plain)
        if len(target_gene)!=nt:raise ValueError("STOP: target census")
        scans[key]=target_gene;sources[key]={"source_path":path.as_posix(),
            "source_compressed_sha256":ent["sha256"],"source_uncompressed_sha256":plain,
            "source_published_DE_rows":n}
    approved=None
    if frozen is not None:
        j=json.loads(Path(frozen).read_text())
        if j.get("schema")!="GSE335887_PRIMARY_HGNC_FROZEN_ANNOTATION_V1" or j.get("frozen_annotation_contract_sha256")!="7afc212d475fbd329d6e343148aca85dca43df7856624eae82ded38c94570ebc":
            raise ValueError("STOP: frozen annotation root mismatch")
        if j.get("training_authorized") is not False or j.get("mapped_common_measured_feature_labels")!=13373:
            raise ValueError("STOP: wrong frozen crosswalk scope")
        approved={x["source_id"] for x in j["frozen_annotation_body"]["entries"]}
        target_set=set(scans[KEYS[0]])
        approved-=target_set
        # Restore all mapped feature labels that overlap the common screenwide feature set.
        common=set().union(*scans[KEYS[0]].values())&set().union(*scans[KEYS[1]].values())
        approved={x["source_id"] for x in j["frozen_annotation_body"]["entries"] if x["source_id"] in common}
        if len(approved)!=13373:raise ValueError("STOP: primary common measured set drift")
    result=derive(scans[KEYS[0]],scans[KEYS[1]],approved)
    result["sources"]=sources
    if sources[KEYS[0]]["source_published_DE_rows"]!=505527 or sources[KEYS[1]]["source_published_DE_rows"]!=417630:
        raise ValueError("STOP: published source row census changed")
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--frozen-annotation-json",type=Path)
    p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise SystemExit("STOP: output exists")
    result=build(a.repo,a.frozen_annotation_json)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    vals=[r["both_published_de_row_count"] for r in result["per_target"]]
    print(json.dumps({"targets":31,"screenwide_common_gene_labels":result["shared_screenwide_published_gene_label_count"],
      "per_target_both_row_min":min(vals),"per_target_both_row_max":max(vals),
      "per_target_both_row_median":sorted(vals)[15],"numeric_outcomes_inspected":False}))
if __name__=="__main__":main()
