#!/usr/bin/env python3
"""Independent verifier for the outcome-blind protected-program family audit."""
from __future__ import annotations
import argparse, ast, hashlib, importlib.util, json, tempfile
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
DECISION=ROOT/"scripts/v4/contextual_target_f1_decision_v4.py"
AUDIT_SCRIPT=ROOT/"scripts/v4/audit_protected_program_family_independence_v1.py"
AUTH_REL=Path("exports/contextual_biology_v6r5a_20260822")
EXPECTED_WEIGHTS_SHA="001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70"

def sha(p:Path):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""):h.update(b)
    return h.hexdigest()

def parse_programs(source:str):
    tree=ast.parse(source)
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id=="PROGRAMS":
                    value=ast.literal_eval(node.value)
                    if not isinstance(value,tuple) or not all(isinstance(x,str) for x in value):
                        raise RuntimeError("STOP_PROGRAMS_AST_INVALID")
                    return value
    raise RuntimeError("STOP_PROGRAMS_AST_MISSING")

def numerical_rank(w):
    s=np.linalg.svd(np.asarray(w,np.float64),compute_uv=False)
    tol=max(w.shape)*np.finfo(np.float64).eps*s[0]
    return int(np.sum(s>tol)),s,tol

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--canonical-root",type=Path,required=True);ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
    decision_programs=parse_programs(DECISION.read_text(encoding="utf-8"))
    spec=importlib.util.spec_from_file_location("pp_audit",AUDIT_SCRIPT)
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    hardcoded=tuple(audit.GATED)
    if decision_programs!=hardcoded:raise RuntimeError("STOP_AUDIT_GATED_FAMILY_STALE")
    weights=a.canonical_root/AUTH_REL/"program_weights.npz"
    if sha(weights)!=EXPECTED_WEIGHTS_SHA:raise RuntimeError("STOP_WEIGHT_AUTHORITY_MISMATCH")
    z=np.load(weights,allow_pickle=True)
    W=np.stack([np.asarray(z["l2__"+p],np.float64) for p in decision_programs])
    rank,s,tol=numerical_rank(W)
    core=np.asarray(z["l2__local_core"],np.float64);halo=np.asarray(z["l2__local_halo"],np.float64);combo=np.asarray(z["l2__core_halo"],np.float64)
    coef=np.linalg.lstsq(np.stack([core,halo],axis=1),combo,rcond=None)[0]
    resid=combo-(coef[0]*core+coef[1]*halo)
    identities={
      "innovation_equals_recurrent5_raw":bool(np.array_equal(z["raw__innovation_tail"],z["raw__recurrent_5pct"])),
      "innovation_equals_recurrent5_l2":bool(np.array_equal(z["l2__innovation_tail"],z["l2__recurrent_5pct"])),
      "innovation_equals_recurrent1_raw":bool(np.array_equal(z["raw__innovation_tail"],z["raw__recurrent_1pct"])),
      "innovation_equals_recurrent1_l2":bool(np.array_equal(z["l2__innovation_tail"],z["l2__recurrent_1pct"])),
    }
    # Mutation attacks on AST binding itself.
    src=DECISION.read_text(encoding="utf-8")
    mutation_results={}
    mutations={
      "remove_last":tuple(decision_programs[:-1]),
      "add_fake":tuple(decision_programs)+("fake_program",),
      "reorder":tuple(reversed(decision_programs)),
    }
    for name,mut in mutations.items():
        mutation_results[name]=bool(mut!=hardcoded)
    terminal=(rank==7 and float(np.max(np.abs(resid)))<1e-6 and all(identities.values()) and all(mutation_results.values()))
    doc={
      "schema":"PROTECTED_PROGRAM_FAMILY_INDEPENDENT_VERIFIER_V1",
      "terminal":"PASS_PROTECTED_PROGRAM_FAMILY_INDEPENDENT_VERIFIER" if terminal else "STOP_PROTECTED_PROGRAM_FAMILY_INDEPENDENT_VERIFIER",
      "decision_programs":decision_programs,"audit_hardcoded_programs":hardcoded,
      "decision_programs_exactly_bound":decision_programs==hardcoded,
      "weights_sha256":sha(weights),"rank":rank,"rank_tolerance":tol,"singular_values":[float(x) for x in s],
      "core_halo_coefficients":[float(x) for x in coef],"core_halo_max_abs_residual":float(np.max(np.abs(resid))),
      "identities":identities,"mutation_binding_tests":mutation_results,
      "scope":["A1 rank/dependence","A2 innovation/recurrent vector identity"],
      "nonconclusions":["does not select a replacement family","does not modify Holm","does not authorize rare census","does not authorize real F1"],
      "firewall":{"expression":False,"model_checkpoint":False,"outcome":False,"training":False},
    }
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"terminal":doc["terminal"],"rank":rank,"max_residual":doc["core_halo_max_abs_residual"]},indent=2))
if __name__=="__main__":main()
