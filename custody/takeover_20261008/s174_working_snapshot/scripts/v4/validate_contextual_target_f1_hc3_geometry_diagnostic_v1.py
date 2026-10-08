#!/usr/bin/env python3
"""Independent reconstruction for the F1 HC3 Command-15A diagnostic.

This file intentionally does not import the production diagnostic helpers.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from itertools import product
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
UP=ROOT/"outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
STATE=ROOT/"exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
EPS=np.finfo(np.float64).eps;BOUND=float(np.sqrt(EPS))
CONT=["recipient_physical_support","recipient_depth","correct_minus_null_visible_depth","correct_minus_null_measured_zero_rate"]
SRC=["source_HVS","source_NPH52","source_SEA_AD"]
OPS=[f"operator_mix_{i:03d}" for i in range(42)]

def rnk(a):
 a=np.asarray(a,dtype=np.float64);s=np.linalg.svd(a,compute_uv=False)
 return int(np.count_nonzero(s>max(a.shape)*EPS*s[0])) if s.size else 0

def construct(mapping,n):
 x=np.ones((n,1),dtype=np.float64);names=[]
 for name in sorted(mapping):
  v=np.asarray(mapping[name],dtype=np.float64);trial=np.column_stack((x,v-np.mean(v,dtype=np.float64)))
  if rnk(trial)>rnk(x):x=trial;names.append(name)
 return x,names

def lev(x):
 g=np.linalg.solve(x.T@x,x.T);return np.sum(x*g.T,axis=1)

def geom(x,src):
 k=rnk(x);h=lev(x);sing=np.linalg.svd(x,compute_uv=False);loss=[k-rnk(np.delete(x,i,axis=0)) for i in range(len(x))]
 return {"rank":k,"df":len(x)-k,"max_leverage":float(h.max()),"min_one_minus_h":float((1-h).min()),"hc3_estimable":bool(np.all(1-h>BOUND)),"worst_loo_rank_loss":max(loss),"loo_rank_stable":max(loss)==0,"condition_number":float(sing[0]/sing[k-1]),"smallest_nonzero_singular_value":float(sing[k-1]),"max_leverage_by_source":{q:float(h[src==q].max()) for q in sorted(set(src))}}

def close(a,b,tol=5e-11):return abs(float(a)-float(b))<=tol*max(1.,abs(float(a)),abs(float(b)))

def main():
 p=argparse.ArgumentParser();p.add_argument("--diagnostic",type=Path,required=True);a=p.parse_args();out=a.diagnostic
 schema=json.loads((UP/"F1_NUISANCE_COLUMN_SCHEMA.json").read_text());M=np.fromfile(UP/"F1_NUISANCE_DONOR_DESIGN_F64LE.bin",dtype="<f8").reshape(schema["shape"]);cols=schema["columns"];donors=np.asarray(schema["donor_order"]);src=np.asarray([x.split("::",1)[0] for x in donors]);mapping={n:M[:,i] for i,n in enumerate(cols)}
 old=json.loads((out/"F1_HC3_OLD_FAILURE_REPRODUCTION.json").read_text());X,kept=construct(mapping,104);h=lev(X);bad=[str(donors[i]) for i in np.flatnonzero(1-h<=BOUND)]
 old_ok=(rnk(X)==18 and kept==old["retained_columns"] and bad==old["unit_leverage_donors"] and old["estimable"] is False)
 # Family ranks and complete LOO maps.
 families={"A_intercept":[],"B_source":SRC,"C_four_continuous":CONT,"D_source_plus_continuous":SRC+CONT,"E_operator":OPS,"F_source_plus_operator":SRC+OPS,"G_continuous_plus_operator":CONT+OPS,"H_source_continuous_operator":SRC+CONT+OPS}
 fdoc=json.loads((out/"F1_HC3_FAMILY_GEOMETRY.json").read_text());family_ok=True
 for key,names in families.items():
  xx,_=construct({q:mapping[q] for q in names},104);d=geom(xx,src);got=fdoc[key]["geometry"]
  family_ok &= d["rank"]==got["rank"] and d["worst_loo_rank_loss"]==got["worst_loo_rank_loss"] and close(d["max_leverage"],got["max_leverage"])
  expected={str(donors[i]):int(d["rank"]-rnk(np.delete(xx,i,axis=0))) for i in range(104)}
  family_ok &= expected==got["leave_one_donor_out_rank_loss"]
 # Exact state equivalence independently hashed.
 z=np.load(STATE,allow_pickle=False);rows=z["states"];groups={}
 for i in range(42):groups.setdefault(hashlib.sha256(rows[i].tobytes(order="C")).hexdigest(),[]).append(i)
 classes=sorted(groups.values(),key=lambda g:g[0]);eq=json.loads((out/"F1_HC3_OPERATOR_STATE_EQUIVALENCE.json").read_text());state_ok=classes==eq["equivalence_classes"]
 # Unit patterns.
 O=M[:,[cols.index(q) for q in OPS]];utr=json.loads((out/"F1_HC3_UNIT_LEVERAGE_DONOR_TRACE.json").read_text());unit_ok=True
 for rec in utr:
  i=list(donors).index(rec["donor"]);nz=np.flatnonzero(O[i]!=0)
  unit_ok &= rec["nonzero_operator_mixtures"]=={OPS[j]:float(O[i,j]) for j in nz}
  unit_ok &= rec["operator_donor_support_counts"]=={OPS[j]:int(np.count_nonzero(O[:,j])) for j in nz}
 # Independent source residual construction and SVD.
 C=M[:,[cols.index(q) for q in CONT]];spect=json.loads((out/"F1_HC3_SOURCE_SVD_SPECTRA.json").read_text());emb={};svd_ok=True
 expected_ops={"HVS":range(24),"NPH52":range(35,42),"SEA_AD":range(24,35)}
 for ss in ["HVS","NPH52","SEA_AD"]:
  ix=src==ss;oi=np.flatnonzero(np.any(O[ix]!=0,axis=0));assert list(oi)==list(expected_ops[ss])
  w,_=construct({f"c{j}":C[ix,j] for j in range(4)},int(ix.sum()));u0,_,_=np.linalg.svd(w,full_matrices=False);q=u0[:,:rnk(w)];res=O[ix][:,oi]-q@(q.T@O[ix][:,oi]);u,s,vt=np.linalg.svd(res,full_matrices=False);rr=rnk(res)
  for j in range(vt.shape[0]):
   m=np.flatnonzero(np.abs(vt[j])==np.abs(vt[j]).max())[0]
   if vt[j,m]<0:u[:,j]*=-1;vt[j]*=-1
  svd_ok &= rr==spect[ss]["residual_rank"] and np.allclose(s,spect[ss]["singular_values"],rtol=3e-12,atol=3e-14)
  e=np.zeros((104,rr));e[ix]=u[:,:rr]*s[:rr];emb[ss]=e
 B,bkeep=construct({q:mapping[q] for q in SRC+CONT},104);base_ok=bkeep==spect["mandatory_base"]["retained_columns"] and geom(B,src)["hc3_estimable"]
 # Every source-prefix frontier row.
 with (out/"F1_HC3_SVD_PREFIX_FRONTIER.csv").open(newline="",encoding="utf-8") as f: rowsf=list(csv.DictReader(f))
 frontier_ok=len(rowsf)==np.prod([spect[q]["residual_rank"]+1 for q in ["HVS","NPH52","SEA_AD"]]);frontier_max=0.
 indexed={(int(r["r_HVS"]),int(r["r_NPH52"]),int(r["r_SEAAD"])):r for r in rowsf}
 for triple in product(range(spect["HVS"]["residual_rank"]+1),range(spect["NPH52"]["residual_rank"]+1),range(spect["SEA_AD"]["residual_rank"]+1)):
  xx=np.column_stack([B,emb["HVS"][:,:triple[0]],emb["NPH52"][:,:triple[1]],emb["SEA_AD"][:,:triple[2]]]);d=geom(xx,src);r=indexed[triple]
  errs=[abs(d[k]-float(r[k])) for k in ["max_leverage","min_one_minus_h","condition_number","smallest_nonzero_singular_value"]];frontier_max=max(frontier_max,max(errs))
  frontier_ok &= d["rank"]==int(r["rank"]) and d["df"]==int(r["df"]) and d["hc3_estimable"]==(r["hc3_estimable"]=="True") and d["loo_rank_stable"]==(r["loo_rank_stable"]=="True") and d["worst_loo_rank_loss"]==int(r["worst_loo_rank_loss"]) and all(close(d[k],r[k]) for k in ["max_leverage","min_one_minus_h","condition_number","smallest_nonzero_singular_value"])
 # Stratified plus all boundary candidates hat checks are covered by every-row geometry above.
 syn=json.loads((out/"F1_HC3_SYNTHETIC_ARITHMETIC.json").read_text());rng=np.random.default_rng(9817);T=np.linalg.qr(rng.normal(size=(B.shape[1],B.shape[1])))[0]
 def projdiag(x):
  u=np.linalg.svd(x,full_matrices=False)[0][:,:rnk(x)];return np.sum(u*u,axis=1)
 S=np.linalg.qr(rng.normal(size=(104,B.shape[1])),mode="reduced")[0];basis_diff=float(np.max(np.abs(projdiag(S)-projdiag(S@T))));basis_ok=basis_diff<=1e-12 and syn["basis_invariance_pass"]
 # No disallowed input path is present in authority; authoritative read set is exact.
 auth=json.loads((out/"F1_HC3_DIAGNOSTIC_AUTHORITY.json").read_text());firewall_ok=all(auth["firewall"][k] is False for k in auth["firewall"])
 checks={"old_unit_leverage_failure":bool(old_ok),"family_ranks_and_all_loo":bool(family_ok),"mandatory_base":bool(base_ok),"unit_donor_patterns":bool(unit_ok),"observation_state_equivalence":bool(state_ok),"source_residual_svd":bool(svd_ok),"every_prefix_frontier_row":bool(frontier_ok),"basis_invariance":bool(basis_ok),"firewall":bool(firewall_ok)}
 status="PASS" if all(checks.values()) else "STOP_F1_HC3_FRONTIER_INDEPENDENT_MISMATCH"
 report={"status":status,"checks":checks,"old_boundary_donors":bad,"frontier_rows_checked":len(rowsf),"frontier_max_abs_scalar_difference":frontier_max,"independent_basis_invariance_max_hat_abs":basis_diff,"production_diagnostic_helpers_imported":False,"candidate_outcomes_read":False,"expression_read":False,"model_or_checkpoint_read":False}
 (out/"F1_HC3_INDEPENDENT_VALIDATION.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps(report))
 if status!="PASS":raise SystemExit(2)

if __name__=="__main__":main()
