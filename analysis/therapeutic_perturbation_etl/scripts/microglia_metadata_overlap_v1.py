#!/usr/bin/env python3
"""Source-bound metadata-only audit. Never inspect numerical perturbation outcomes."""
import argparse,csv,gzip,hashlib,io,json,re
from itertools import combinations
from pathlib import Path
ROOT=Path("analysis/therapeutic_perturbation_etl")
SCREENS={
 "day8_iTF_CROP_RNA":("iTF_Microglia-Day-8-CROP-seq-CRISPRi.csv.gz","RNA",39,"41eb533dfd50852d0ebd8f2c27d42d5f6bb3b1f1264ab0c721106cfbaed9fc39",True),
 "day12_iTF_CROP_RNA":("iTF-Microglia-CROP-seq-CRISPRi.csv.gz","RNA",31,"6f65d728699863d207012227c72ac88cc2033cc1277ee6a74132bac8f3afbea8",False),
 "day28_iPSC_CROP_RNA":("iPSC-Microglia-CROP-seq-CRISPRi.csv.gz","RNA",31,"1efd4d840a46f0de32ce7839043df33e07db04d92f826855923e24f8fd36cdd2",False),
 "day12_iTF_CITE_PROTEIN":("iTF-Microglia-CITE-seq-CRISPRi.csv.gz","PROTEIN",31,"7b97a1098fb6144ba5c053620a18d6ab9d9fcb9fc50cf07124c6e3139c8014c8",False),
 "day28_iPSC_CITE_PROTEIN":("iPSC-Microglia-CITE-seq-CRISPRi.csv.gz","PROTEIN",31,"94cee8ca5ccb24057dcd98226f8fd58472151e6799d3aa7e46491d152f64f412",False)}
HEX=re.compile(r"^[0-9a-f]{64}$")
def digest_members(s): return hashlib.sha256(("\n".join(sorted(s))+"\n").encode()).hexdigest()
def scan_identifiers(raw,compressed_sha,uncompressed_sha):
    """Only the Gene/name columns are accessed; response data are not evaluated."""
    if not HEX.fullmatch(compressed_sha) or not HEX.fullmatch(uncompressed_sha): raise ValueError("invalid digest")
    if hashlib.sha256(raw).hexdigest()!=compressed_sha: raise ValueError("STOP: compressed source SHA mismatch")
    try: plain=gzip.decompress(raw)
    except (OSError,EOFError) as exc: raise ValueError("STOP: gzip damaged") from exc
    if hashlib.sha256(plain).hexdigest()!=uncompressed_sha: raise ValueError("STOP: uncompressed source SHA mismatch")
    reader=csv.reader(io.TextIOWrapper(io.BytesIO(plain),encoding="utf-8-sig",newline=""))
    try: header=next(reader)
    except StopIteration as exc: raise ValueError("STOP: empty file") from exc
    if header.count("Gene")!=1 or header.count("name")!=1: raise ValueError("STOP: missing or duplicate identifiers")
    gi,ti=header.index("Gene"),header.index("name")
    genes,targets=set(),set();n=0
    for row in reader:
        if len(row)!=len(header): raise ValueError("STOP: malformed row")
        gene,target=row[gi].strip(),row[ti].strip()
        if not gene or not target: raise ValueError("STOP: empty identifier")
        genes.add(gene);targets.add(target);n+=1
    if n==0: raise ValueError("STOP: no data rows")
    return {"rows":n,"targets":targets,"features":genes,"target_set_sha256":digest_members(targets),"feature_set_sha256":digest_members(genes)}
def compare_screen_metadata(screens):
    pairs=[]
    for (a,x),(b,y) in combinations(sorted(screens.items()),2):
        overlap=x["targets"]&y["targets"];same=x["modality"]==y["modality"]
        f=x["features"]&y["features"] if same else None
        pairs.append({"screen_a":a,"screen_b":b,"shared_target_count":len(overlap),
            "shared_target_names_METADATA_ONLY":sorted(overlap),"shared_target_set_sha256":digest_members(overlap),
            "same_outcome_modality":same,"shared_measured_feature_count":len(f) if same else None,
            "shared_feature_set_sha256":digest_members(f) if same else None,
            "donor_line_overlap":"NOT_CHECKED","biological_preparation_independence":"NOT_VERIFIED",
            "gene_id_authority":"LITERAL_LABELS_ONLY_NOT_FROZEN_ANNOTATION",
            "qualification":"METADATA_CANDIDATE_ONLY" if same and overlap and f else "DIFFERENT_MODALITY_OR_ZERO_OVERLAP"})
    return pairs
def build(repo):
    manifest=json.loads((repo/ROOT/"evidence/COMMITTED_OUTPUTS_SHA256_MANIFEST_V1.json").read_text())
    if manifest["schema"]!="PERTURBATION_COMMITTED_OUTPUTS_SHA256_MANIFEST_V1": raise ValueError("STOP: manifest schema")
    records={x["path"]:x for x in manifest["files"]}; screens={}
    for key,(filename,modality,n_expected,plain_sha,exposed) in SCREENS.items():
        relative=ROOT/"outputs/crisprbrain"/filename
        m=records.get(relative.as_posix())
        if m is None: raise ValueError("STOP: unmanifested source: "+filename)
        raw=(repo/relative).read_bytes()
        if len(raw)!=m["bytes"]: raise ValueError("STOP: compressed byte size: "+filename)
        s=scan_identifiers(raw,m["sha256"],plain_sha)
        if len(s["targets"])!=n_expected: raise ValueError("STOP: target census: "+filename)
        s.update({"modality":modality,"source":relative.as_posix(),"compressed_sha256":m["sha256"],
                  "uncompressed_sha256":plain_sha,"outcome_status":"EXPOSED_DEVELOPMENT" if exposed else "RESERVED_PROFILE_UNREAD_PER_LEDGER__REVERIFY"})
        screens[key]=s
    return {"schema":"CRISPRBRAIN_MICROGLIA_METADATA_OVERLAP_V1",
       "authority":"METADATA_ONLY_NOT_BIOLOGICAL_COMPARABILITY",
       "no_numeric_outcome_columns_inspected":True,"training_authority":False,
       "screens":{k:{a:b for a,b in s.items() if a not in ("targets","features")}|
                   {"target_count":len(s["targets"]),"feature_count":len(s["features"]),
                    "per_target_assay_label_present":{t:t in s["features"] for t in sorted(s["targets"])}} for k,s in screens.items()},
       "pairs":compare_screen_metadata(screens)}
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",required=True,type=Path);p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    if args.out.exists():raise SystemExit("STOP: refusing overwrite")
    report=build(args.repo);args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"screens":len(report["screens"]),"pairs":len(report["pairs"]),"scope":report["authority"]}))
if __name__=="__main__":main()
