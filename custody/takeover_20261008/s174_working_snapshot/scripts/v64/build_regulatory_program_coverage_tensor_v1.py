#!/usr/bin/env python3
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

EXPECTED_SOURCES=[
 "FULL104_HVS","FULL104_NPH52","FULL104_SEA_AD","NIH_CARD_STAGE4",
 "MORABITO_GSE174367","SEAAD_PUBLIC_MULTIOME","GSE272082",
 "PERTURBATION_ATLAS","SEAAD_SPATIAL"
]

def build_tensor(bundle):
    programs={(p["program_id"],p["program_version"]):p for p in bundle.get("programs",[])}
    by=defaultdict(dict)
    for r in bundle.get("crosswalks",[]):
        by[(r["program_id"],r["program_version"])][r["source_id"]]=r
    rows=[]
    for key,p in sorted(programs.items()):
        srcs=by.get(key,{})
        row={
          "program_id":p["program_id"],
          "program_version":p["program_version"],
          "program_membership_sha256":p["membership_sha256"],
          "definition_source":p["definition_source"],
          "sources":{},
          "full104_transport_ceiling":{
             "HVS":None,"NPH52":None,"SEA_AD":None,
             "all_three_source_families_minimum":None
          },
          "direct_multimodal_sources":[],
          "structurally_eligible_sources":[],
          "limitations":[]
        }
        full=[]
        for s in EXPECTED_SOURCES:
            r=srcs.get(s)
            if r is None:
                row["sources"][s]={"status":"NO_RECORD"}
                continue
            g=r["gene_support"]; rg=r["region_support"]; tf=r["tf_support"]
            row["sources"][s]={
              "status":"RECORDED",
              "structural_eligibility":r["structural_eligibility"],
              "gene_fraction":g["fraction_measured"],
              "region_fraction":rg["fraction_measured"],
              "tf_fraction":tf["fraction_measured"],
              "limitations":r.get("limitations",[])
            }
            if r["structural_eligibility"] in ("ELIGIBLE","PARTIALLY_ELIGIBLE"):
                row["structurally_eligible_sources"].append(s)
            if s in ("NIH_CARD_STAGE4","MORABITO_GSE174367","SEAAD_PUBLIC_MULTIOME","GSE272082") and r["structural_eligibility"]=="ELIGIBLE":
                row["direct_multimodal_sources"].append(s)
            if s.startswith("FULL104_"):
                v=g["fraction_measured"]
                name=s.replace("FULL104_","")
                row["full104_transport_ceiling"][name]=v
                if v is not None: full.append(v)
        row["full104_transport_ceiling"]["all_three_source_families_minimum"]=min(full) if len(full)==3 else None
        rows.append(row)
    return {
      "schema":"V70_REGULATORY_PROGRAM_COVERAGE_TENSOR_V1",
      "semantics":{
        "fractions":"structural feature-support fractions only; not biological validation",
        "full104_transport_ceiling":"gene-measurement ceiling only; actual RNA recoverability may be lower",
        "direct_multimodal_sources":"structurally eligible direct regulatory measurement sources; no biological result implied"
      },
      "rows":rows
    }

def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("bundle"); ap.add_argument("out"); a=ap.parse_args()
    x=json.loads(Path(a.bundle).read_text())
    Path(a.out).write_text(json.dumps(build_tensor(x),indent=2)+"\n")
    print(f"WROTE {a.out}")
if __name__=="__main__": main()
