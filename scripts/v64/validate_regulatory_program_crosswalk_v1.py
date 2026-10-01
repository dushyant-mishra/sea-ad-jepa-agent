#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
NS=ROOT/"results/v64/V69_REGULATORY_PROGRAM_NAMESPACE_CONTRACT_V1.json"
CW=ROOT/"results/v64/V69_REGULATORY_PROGRAM_CROSSWALK_SCHEMA_V1.json"

def load(p): return json.loads(Path(p).read_text())

def membership_sha(program):
    lines=[
        f"PROGRAM_ID={program['program_id']}",
        f"PROGRAM_VERSION={program['program_version']}",
        "TF="+",".join(sorted(program.get("tf_ids",[]))),
        "GENE="+",".join(sorted(program.get("target_gene_ids",[]))),
        "REGION="+",".join(sorted(program.get("region_ids",[]))),
        f"REGION_BUILD={program.get('region_build','')}",
    ]
    return hashlib.sha256(("\n".join(lines)+"\n").encode()).hexdigest()

def validate_program(program, ns=None):
    ns=ns or load(NS); e=[]
    for k in ns["required_fields"]:
        if k not in program: e.append(f"MISSING_PROGRAM_FIELD:{k}")
    if e: return e
    if program["status"] not in ns["status_values"]: e.append("BAD_PROGRAM_STATUS")
    if program["definition_source"] not in ns["allowed_definition_sources"]: e.append("BAD_DEFINITION_SOURCE")
    if program.get("region_ids") and not program.get("region_build"): e.append("REGION_BUILD_REQUIRED")
    if program.get("membership_sha256") != membership_sha(program): e.append("MEMBERSHIP_SHA_MISMATCH")
    return e

def _check_support(block,label):
    e=[]
    if not isinstance(block,dict): return [f"{label}_BLOCK_REQUIRED"]
    n=int(block.get(f"n_program_{'genes' if label=='GENE' else 'regions' if label=='REGION' else 'tfs'}",-1))
    m=int(block.get(f"n_measured_{'genes' if label=='GENE' else 'regions' if label=='REGION' else 'tfs'}",-1))
    f=block.get("fraction_measured")
    if n<0 or m<0 or m>n: e.append(f"{label}_COUNT_INVALID")
    if n==0:
        if f not in (None,0,0.0): e.append(f"{label}_FRACTION_INVALID_FOR_ZERO_DENOM")
    else:
        if f is None or abs(float(f)-m/n)>1e-12: e.append(f"{label}_FRACTION_MISMATCH")
    return e

def validate_crosswalk(rec, schema=None):
    schema=schema or load(CW); e=[]
    for k in schema["required_record_fields"]:
        if k not in rec: e.append(f"MISSING_CROSSWALK_FIELD:{k}")
    if e:return e
    if rec["source_id"] not in schema["source_ids"]: e.append("BAD_SOURCE_ID")
    for label,key in [("GENE","gene_support"),("REGION","region_support"),("TF","tf_support")]:
        b=rec.get(key,{})
        if b.get("status") not in schema["support_semantics"][key]: e.append(f"BAD_{label}_SUPPORT_STATUS")
        e.extend(_check_support(b,label))
    if rec.get("structural_eligibility") not in schema["support_semantics"]["structural_eligibility"]:
        e.append("BAD_STRUCTURAL_ELIGIBILITY")
    miss=rec.get("missingness",{})
    for k in schema["missingness_fields"]:
        if k not in miss: e.append(f"MISSING_MISSINGNESS_FIELD:{k}")
    if rec.get("source_id","").startswith("FULL104_") and rec.get("pooled_full104_sources") is True:
        e.append("FULL104_SOURCE_POOLING_FORBIDDEN")
    if rec.get("biological_effect") not in (None,{},[]):
        e.append("STRUCTURAL_CROSSWALK_CANNOT_CARRY_BIOLOGICAL_EFFECT")
    if rec.get("region_support",{}).get("status") in ("MEASURED","PARTIAL"):
        if rec.get("region_build") and rec.get("program_region_build") and rec["region_build"]!=rec["program_region_build"]:
            if not rec.get("mapping_receipts",{}).get("region_build_mapping"):
                e.append("REGION_BUILD_MAPPING_RECEIPT_REQUIRED")
    return e

def validate_bundle(obj):
    programs=obj.get("programs",[])
    crosswalks=obj.get("crosswalks",[])
    e=[]
    pmap={}
    for i,p in enumerate(programs):
        for x in validate_program(p): e.append(f"PROGRAM_{i}:{x}")
        pmap[(p.get("program_id"),p.get("program_version"))]=p
    seen=set()
    for i,r in enumerate(crosswalks):
        for x in validate_crosswalk(r): e.append(f"CROSSWALK_{i}:{x}")
        key=(r.get("program_id"),r.get("program_version"),r.get("source_id"))
        if key in seen:e.append(f"DUPLICATE_CROSSWALK:{key}")
        seen.add(key)
        p=pmap.get((r.get("program_id"),r.get("program_version")))
        if p is None:e.append(f"CROSSWALK_{i}:UNKNOWN_PROGRAM")
        elif r.get("program_membership_sha256")!=p.get("membership_sha256"):
            e.append(f"CROSSWALK_{i}:PROGRAM_MEMBERSHIP_BINDING_MISMATCH")
    return e

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("bundle"); a=ap.parse_args()
    errors=validate_bundle(load(a.bundle))
    if errors:
        print("\n".join(errors)); raise SystemExit(1)
    print("PASS")
