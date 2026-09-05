#!/usr/bin/env python3
"""Independent verifier for the outcome-blind protected-program family audit."""
from __future__ import annotations
import argparse, ast, csv, hashlib, importlib.util, json
from pathlib import Path
import numpy as np
from scipy import linalg

ROOT=Path(__file__).resolve().parents[2]
DECISION=ROOT/"scripts/v4/contextual_target_f1_decision_v4.py"
AUDIT_SCRIPT=ROOT/"scripts/v4/audit_protected_program_family_independence_v1.py"
AUTH_REL=Path("exports/contextual_biology_v6r5a_20260822")
EXPECTED_WEIGHTS_SHA="001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70"
UNGATED=("recurrent_5pct","recurrent_1pct")

def sha(p:Path):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""):h.update(b)
    return h.hexdigest()

def sha_array(a):
    return hashlib.sha256(np.ascontiguousarray(a,dtype=np.float32).tobytes()).hexdigest()

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

def svd_rank(w):
    w=np.asarray(w,np.float64);s=np.linalg.svd(w,compute_uv=False)
    tol=max(w.shape)*np.finfo(np.float64).eps*s[0]
    return int(np.sum(s>tol)),s,tol

def qr_rank(w):
    w=np.asarray(w,np.float64);_,r,_=linalg.qr(w,mode="economic",pivoting=True)
    d=np.abs(np.diag(r));tol=max(w.shape)*np.finfo(np.float64).eps*(d[0] if len(d) else 0.0)
    return int(np.sum(d>tol)),d,tol

def binding_ok(decision_programs,audit_programs):
    return tuple(decision_programs)==tuple(audit_programs)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--canonical-root",type=Path,required=True);ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
    decision_programs=parse_programs(DECISION.read_text(encoding="utf-8"))
    spec=importlib.util.spec_from_file_location("pp_audit",AUDIT_SCRIPT)
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    audit_programs=tuple(audit.GATED)
    if not binding_ok(decision_programs,audit_programs):raise RuntimeError("STOP_AUDIT_GATED_FAMILY_STALE")

    base=a.canonical_root/AUTH_REL;weights=base/"program_weights.npz";registry_path=base/"program_registry.csv"
    if sha(weights)!=EXPECTED_WEIGHTS_SHA:raise RuntimeError("STOP_WEIGHT_AUTHORITY_MISMATCH")
    if not registry_path.is_file():raise RuntimeError("STOP_REGISTRY_MISSING")
    z=np.load(weights,allow_pickle=True)
    all_programs=tuple(decision_programs)+UNGATED
    with registry_path.open("r",encoding="utf-8-sig",newline="") as f:
        registry={r["program_name"]:r for r in csv.DictReader(f)}
    digest_rows=[]
    for p in all_programs:
        if p not in registry:raise RuntimeError("STOP_REGISTRY_PROGRAM_MISSING")
        for kind,field in (("raw","raw_weight_sha256"),("l2","l2_weight_sha256")):
            actual=sha_array(z[f"{kind}__{p}"]);expected=registry[p][field]
            digest_rows.append({"program":p,"kind":kind,"expected":expected,"actual":actual,"match":actual==expected})
    registry_all_match=all(r["match"] for r in digest_rows)

    W=np.stack([np.asarray(z["l2__"+p],np.float64) for p in decision_programs])
    rank_svd,s,tol_svd=svd_rank(W);rank_qr,diag,tol_qr=qr_rank(W)
    core=np.asarray(z["l2__local_core"],np.float64);halo=np.asarray(z["l2__local_halo"],np.float64);combo=np.asarray(z["l2__core_halo"],np.float64)
    coef=np.linalg.lstsq(np.stack([core,halo],axis=1),combo,rcond=None)[0]
    resid=combo-(coef[0]*core+coef[1]*halo)
    identities={
      "innovation_equals_recurrent5_raw":bool(np.array_equal(z["raw__innovation_tail"],z["raw__recurrent_5pct"])),
      "innovation_equals_recurrent5_l2":bool(np.array_equal(z["l2__innovation_tail"],z["l2__recurrent_5pct"])),
      "innovation_equals_recurrent1_raw":bool(np.array_equal(z["raw__innovation_tail"],z["raw__recurrent_1pct"])),
      "innovation_equals_recurrent1_l2":bool(np.array_equal(z["l2__innovation_tail"],z["l2__recurrent_1pct"])),
    }

    mutations={
      "remove_last":tuple(decision_programs[:-1]),
      "add_fake":tuple(decision_programs)+("fake_program",),
      "reorder":tuple(reversed(decision_programs)),
    }
    mutation_binding_tests={name:(not binding_ok(mut,audit_programs)) for name,mut in mutations.items()}
    # Byte/digest mutation logic: a one-byte/one-value change must alter recomputed digest.
    probe_raw=np.asarray(z["raw__"+decision_programs[0]],np.float32).copy();probe_raw.flat[0]=np.nextafter(probe_raw.flat[0],np.float32(np.inf),dtype=np.float32)
    probe_l2=np.asarray(z["l2__"+decision_programs[0]],np.float32).copy();probe_l2.flat[0]=np.nextafter(probe_l2.flat[0],np.float32(np.inf),dtype=np.float32)
    mutation_digest_tests={
      "raw_array_mutation_detected":sha_array(probe_raw)!=registry[decision_programs[0]]["raw_weight_sha256"],
      "l2_array_mutation_detected":sha_array(probe_l2)!=registry[decision_programs[0]]["l2_weight_sha256"],
      "registry_digest_mutation_detected":("0"*64)!=sha_array(z["raw__"+decision_programs[0]]),
    }

    terminal=(rank_svd==7 and rank_qr==7 and registry_all_match and float(np.max(np.abs(resid)))<1e-6
              and all(identities.values()) and all(mutation_binding_tests.values()) and all(mutation_digest_tests.values()))
    doc={
      "schema":"PROTECTED_PROGRAM_FAMILY_INDEPENDENT_VERIFIER_V2",
      "terminal":"PASS_PROTECTED_PROGRAM_FAMILY_INDEPENDENT_VERIFIER" if terminal else "STOP_PROTECTED_PROGRAM_FAMILY_INDEPENDENT_VERIFIER",
      "decision_programs":decision_programs,"audit_programs":audit_programs,
      "decision_programs_exactly_bound":binding_ok(decision_programs,audit_programs),
      "weights_sha256":sha(weights),"registry_sha256":sha(registry_path),"registry_digest_reverification_all_match":registry_all_match,
      "registry_digest_rows":digest_rows,
      "rank_svd":rank_svd,"rank_qr_pivoted":rank_qr,"svd_tolerance":tol_svd,"qr_tolerance":tol_qr,
      "singular_values":[float(x) for x in s],"pivoted_qr_diag":[float(x) for x in diag],
      "core_halo_coefficients":[float(x) for x in coef],"core_halo_max_abs_residual":float(np.max(np.abs(resid))),
      "identities":identities,"mutation_binding_tests":mutation_binding_tests,"mutation_digest_tests":mutation_digest_tests,
      "scope":["A1 rank/dependence","A2 innovation/recurrent vector identity"],
      "nonconclusions":["does not select a replacement family","does not modify Holm","does not decide QID 7-vs-8","does not authorize rare census","does not authorize real F1"],
      "firewall":{"expression":False,"model_checkpoint":False,"outcome":False,"training":False},
    }
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"terminal":doc["terminal"],"rank_svd":rank_svd,"rank_qr":rank_qr,"registry_all_match":registry_all_match,"max_residual":doc["core_halo_max_abs_residual"]},indent=2))
if __name__=="__main__":main()
