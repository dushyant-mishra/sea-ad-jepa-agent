#!/usr/bin/env python3
"""Outcome-blind HC3 nuisance-design geometry diagnostic (Command 15A).

Reads only the frozen donor nuisance matrix/schema and operator observation-state
authority.  It does not select or freeze a repaired design.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, math
from itertools import product
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
UP = ROOT / "outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
STATES = ROOT / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
SPLIT = ROOT / "exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv"
ENGINE = ROOT / "scripts/v4/contextual_target_f1_decision_v1.py"
EPS = np.finfo(np.float64).eps
BOUNDARY = float(np.sqrt(EPS))
EXPECTED = {
 "F1_NUISANCE_DONOR_DESIGN_F64LE.bin":"1d8f837d18cedd8d1b8fd6138d1b25f886b8352c097a4723ca06421573334056",
 "F1_NUISANCE_COLUMN_SCHEMA.json":"9f90c764d0d97b5a10badc03dfcbafc364e0bf40e120a9aed6609e036b5924a7",
 "F1_NUISANCE_DONOR_DESIGN_AUTHORITY.json":"2a09bdbb4403870e3b240d6c12c06360d550062aaa16b3a9d565f60b2bd7f1bb",
 "F1_NUISANCE_HC3_COMPATIBILITY.json":"01adba7dcb1d6160dbfdd080317b310e87f51fa701ed97953a23769512d1eeda",
 "F1_NUISANCE_FORMULA_CONTRACT.md":"9c5c63fc850bb23856fcd450a60da9f175269b62aa8819133903f439c0480a89",
 "F1_NUISANCE_MANIFEST.csv":"fcebe4aecbd1a03b184005fe09c77a34a201910553c9048810498f0b7206fde9",
}
EXPECTED_OTHER = {ENGINE:"204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34",
 STATES:"852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537",
 SPLIT:"efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511"}
CONT = ["recipient_physical_support","recipient_depth","correct_minus_null_visible_depth","correct_minus_null_measured_zero_rate"]
SRC = ["source_HVS","source_NPH52","source_SEA_AD"]
OPS = [f"operator_mix_{i:03d}" for i in range(42)]

def sha(p: Path) -> str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(8<<20),b""): h.update(b)
 return h.hexdigest()

def dump(p: Path, x):
 p.write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")

def write_csv(p: Path, rows):
 rows=list(rows)
 with p.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ["empty"]); w.writeheader(); w.writerows(rows)

def rank(x):
 x=np.asarray(x,np.float64)
 if x.size==0:return 0
 s=np.linalg.svd(x,compute_uv=False); tol=max(x.shape)*EPS*(s[0] if len(s) else 0.)
 return int(np.sum(s>tol))

def select(columns, n, order=None, trace=False):
 X=np.ones((n,1),np.float64); kept=[]; tr=[]
 names=sorted(columns) if order is None else list(order)
 for name in names:
  rb=rank(X); hb=hat(X); v=np.asarray(columns[name],np.float64); C=np.column_stack([X,v-v.mean()]); ra=rank(C)
  if ra>rb: X=C; kept.append(name)
  if trace:
   ha=hat(X)
   tr.append({"candidate":name,"rank_before":rb,"rank_after":rank(X),"retained":ra>rb,
    "max_h_before":float(hb.max()),"max_h_after":float(ha.max()),
    "min_one_minus_h_before":float((1-hb).min()),"min_one_minus_h_after":float((1-ha).min()),
    "max_h_donor_index":int(np.argmax(ha)),"hc3_estimable_after":bool(np.all(1-ha>BOUNDARY))})
 return X,kept,tr

def hat(X):
 X=np.asarray(X,np.float64); return np.einsum("ij,jk,ik->i",X,np.linalg.inv(X.T@X),X)

def diagnostics(X, donors, sources, include_loo=True):
 s=np.linalg.svd(X,compute_uv=False); k=rank(X); h=hat(X); mean=k/len(X)
 loo=[k-rank(np.delete(X,i,axis=0)) for i in range(len(X))] if include_loo else []
 return {"n":len(X),"rank":k,"df":len(X)-k,"k_over_n":k/len(X),"n_over_k":len(X)/k,
  "mean_leverage":float(h.mean()),"rank_over_n_check_abs":float(abs(h.mean()-mean)),
  "max_leverage":float(h.max()),"max_leverage_over_mean":float(h.max()/mean),
  "max_leverage_donor":str(donors[int(np.argmax(h))]),"min_one_minus_h":float((1-h).min()),
  "above_2k_over_n":[str(donors[i]) for i in np.flatnonzero(h>2*mean)],
  "above_3k_over_n":[str(donors[i]) for i in np.flatnonzero(h>3*mean)],
  "hc3_boundary_donors":[str(donors[i]) for i in np.flatnonzero(1-h<=BOUNDARY)],
  "hc3_estimable":bool(np.all(1-h>BOUNDARY)),"condition_number":float(s[0]/s[k-1]),
  "singular_values":s.tolist(),"smallest_nonzero_singular_value":float(s[k-1]),
  "leave_one_donor_out_rank_loss":dict(zip(map(str,donors),map(int,loo))) if include_loo else {},
  "loo_rank_stable":bool(not loo or max(loo)==0),"worst_loo_rank_loss":int(max(loo) if loo else 0),
  "max_leverage_by_source":{q:float(h[sources==q].max()) for q in sorted(set(sources))}}

def orient(U,V):
 U=U.copy();V=V.copy()
 for j in range(V.shape[0]):
  a=np.abs(V[j]); m=np.flatnonzero(a==a.max())[0]
  if V[j,m]<0: V[j]*=-1; U[:,j]*=-1
 return U,V

def source_svds(M, cols, donors, sources):
 C=M[:,[cols.index(x) for x in CONT]]; O=M[:,[cols.index(x) for x in OPS]]
 out={}; loading=[]; scores=[]; embedded={}
 expected={"HVS":list(range(24)),"NPH52":list(range(35,42)),"SEA_AD":list(range(24,35))}
 for ss in ["HVS","NPH52","SEA_AD"]:
  ix=sources==ss; oi=np.flatnonzero(np.any(O[ix]!=0,axis=0)).tolist()
  if oi!=expected[ss]: raise RuntimeError("source operator set mismatch")
  W,_k,_=select({f"continuous_{j}":C[ix,j] for j in range(4)},int(ix.sum()))
  Q=np.linalg.svd(W,full_matrices=False)[0][:,:rank(W)]
  R=O[ix][:,oi]-Q@(Q.T@O[ix][:,oi])
  U,s,Vt=np.linalg.svd(R,full_matrices=False); U,Vt=orient(U,Vt); rr=rank(R)
  tied=[]; tol=max(R.shape)*EPS*s[0]
  a=0
  while a<rr:
   b=a+1
   while b<rr and abs(s[b]-s[a])<=tol:b+=1
   if b-a>1:tied.append(list(range(a+1,b+1)))
   a=b
  ev=s*s; cum=np.cumsum(ev)/ev.sum() if ev.sum() else np.zeros_like(ev)
  out[ss]={"donors":int(ix.sum()),"operators":oi,"operator_names":[OPS[j] for j in oi],"residual_rank":rr,
   "singular_values":s.tolist(),"squared_singular_values":ev.tolist(),"cumulative_frobenius_variance":cum.tolist(),
   "rank_tolerance":float(tol),"tied_component_subspaces":tied,"within_source_base_rank":rank(W)}
  Z=U[:,:rr]*s[:rr]; E=np.zeros((len(M),rr));E[ix]=Z;embedded[ss]=E
  ids=np.flatnonzero(ix)
  for j in range(rr):
   for z,op in enumerate(oi): loading.append({"source":ss,"component":j+1,"operator_index":op,"operator":OPS[op],"loading":float(Vt[j,z])})
   for z,i in enumerate(ids):scores.append({"source":ss,"component":j+1,"donor":str(donors[i]),"score":float(Z[z,j])})
 return out,loading,scores,embedded

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True);a=ap.parse_args();out=a.out;out.mkdir(parents=True,exist_ok=False)
 actual={}
 for n,h in EXPECTED.items(): actual[str((UP/n).relative_to(ROOT))]=sha(UP/n); assert actual[str((UP/n).relative_to(ROOT))]==h
 for p,h in EXPECTED_OTHER.items():actual[str(p.relative_to(ROOT))]=sha(p);assert actual[str(p.relative_to(ROOT))]==h
 schema=json.loads((UP/"F1_NUISANCE_COLUMN_SCHEMA.json").read_text()); auth=json.loads((UP/"F1_NUISANCE_DONOR_DESIGN_AUTHORITY.json").read_text())
 assert auth["semantic_root_sha256"]=="2f0c95b1d9c098f8593827f240f64a0b8e5512ead92fe50540f6e2dc231742ec"
 M=np.fromfile(UP/"F1_NUISANCE_DONOR_DESIGN_F64LE.bin",dtype="<f8").reshape(104,49); cols=schema["columns"]; donors=np.asarray(schema["donor_order"]); sources=np.asarray([x.split("::",1)[0] for x in donors])
 assert {q:int(np.sum(sources==q)) for q in set(sources)}=={"HVS":41,"NPH52":17,"SEA_AD":46}
 authority={"terminal_input_status":"PASS","primitive_nuisance_semantic_root":auth["semantic_root_sha256"],"input_sha256":actual,"rows":104,"raw_columns":49,"donor_counts":{"HVS":41,"NPH52":17,"SEA_AD":46},"firewall":{"expression_read":False,"model_or_checkpoint_read":False,"candidate_outcomes_read":False,"training_or_ema":False},"design_selection_authorized":False}
 dump(out/"F1_HC3_DIAGNOSTIC_AUTHORITY.json",authority)
 allmap={n:M[:,i] for i,n in enumerate(cols)}; X,kept,tr=select(allmap,104,trace=True)
 for z in tr:z["max_h_donor"]=str(donors[z.pop("max_h_donor_index")])
 first=next((z["candidate"] for z in tr if not z["hc3_estimable_after"]),None)
 expected_kept=["correct_minus_null_measured_zero_rate","correct_minus_null_visible_depth","operator_mix_000","operator_mix_001","operator_mix_002","operator_mix_005","operator_mix_013","operator_mix_019","operator_mix_023","operator_mix_024","operator_mix_029","operator_mix_030","operator_mix_031","operator_mix_032","operator_mix_035","operator_mix_036","recipient_depth"]
 h=hat(X); bad=[str(donors[i]) for i in np.flatnonzero(1-h<=BOUNDARY)]
 if rank(X)!=18 or kept!=expected_kept or bad!=["HVS::H20.06.354","NPH52::human_NPH_906"]:raise RuntimeError("STOP_F1_HC3_FAILURE_NOT_REPRODUCED")
 old={"rows":104,"raw_columns":49,"design_rank":18,"df":86,"retained_columns":kept,"unit_leverage_donors":bad,"hc3_denominator_boundary":BOUNDARY,"estimable":False,"first_nonestimable_candidate":first,"maximum_leverage":float(h.max())};dump(out/"F1_HC3_OLD_FAILURE_REPRODUCTION.json",old);write_csv(out/"F1_HC3_LEXICOGRAPHIC_TRACE.csv",tr)
 families={"A_intercept":[],"B_source":SRC,"C_four_continuous":CONT,"D_source_plus_continuous":SRC+CONT,"E_operator":OPS,"F_source_plus_operator":SRC+OPS,"G_continuous_plus_operator":CONT+OPS,"H_source_continuous_operator":SRC+CONT+OPS}
 fam={}
 for name,names in families.items():
  xx,kk,_=select({q:allmap[q] for q in names},104);fam[name]={"retained_columns":kk,"geometry":diagnostics(xx,donors,sources)}
 dump(out/"F1_HC3_FAMILY_GEOMETRY.json",fam)
 # Unit-leverage donor/operator trace.
 O=M[:,[cols.index(x) for x in OPS]]; unit=[]
 for dd in bad:
  i=list(donors).index(dd); ss=sources[i]; nz=np.flatnonzero(O[i]!=0); dist=np.linalg.norm(O[sources==ss]-O[i],axis=1); dist=sorted(float(x) for x in dist if x>0)
  deletion=[]
  for op in range(42):
   names=[x for x in SRC+CONT+OPS if x!=OPS[op]]; xx,_,_=select({q:allmap[q] for q in names},104);hh=hat(xx);deletion.append({"operator":OPS[op],"removes_unit_leverage":bool(1-hh[i]>BOUNDARY),"leverage_after_deletion":float(hh[i])})
  contributors=[x for x in kept if x.startswith("operator_mix_") and next(z["removes_unit_leverage"] for z in deletion if z["operator"]==x)]
  unit.append({"donor":dd,"source":ss,"nonzero_operator_mixtures":{OPS[j]:float(O[i,j]) for j in nz},"observed_operator_count":len(nz),
   "operator_donor_support_counts":{OPS[j]:int(np.sum(O[:,j]!=0)) for j in nz},"operator_unique_to_donor":{OPS[j]:bool(np.sum(O[:,j]!=0)==1) for j in nz},
   "nearest_within_source_operator_mixture_distances":dist[:10],"deleting_donor_lowers_raw_operator_rank":bool(rank(np.delete(O,i,axis=0))<rank(O)),
   "operator_column_deletion_trace":deletion,"retained_raw_columns_contributing_to_isolation":contributors,
   "isolation_direction":"single_raw_column" if len(contributors)==1 else "linear_combination_multiple_operator_columns"})
 dump(out/"F1_HC3_UNIT_LEVERAGE_DONOR_TRACE.json",unit)
 # Exact state-row equivalence and donor mixtures.
 z=np.load(STATES,allow_pickle=False);st=z["states"];oi=z["operator_index"];assert np.array_equal(oi,np.arange(42))
 rowsha=[hashlib.sha256(np.ascontiguousarray(st[i]).tobytes()).hexdigest() for i in range(42)]; groups={}
 for i,q in enumerate(rowsha):groups.setdefault(q,[]).append(i)
 classes=sorted(groups.values(),key=lambda x:x[0]); eqcols={f"state_equivalence_{j:03d}":O[:,g].sum(axis=1) for j,g in enumerate(classes)}
 xe,ke,_=select({**{q:allmap[q] for q in SRC+CONT},**eqcols},104)
 eq={"operator_row_sha256":dict(zip(map(str,range(42)),rowsha)),"equivalence_classes":classes,"class_count":len(classes),"retained_columns":ke,"geometry":diagnostics(xe,donors,sources),"diagnostic_only":True};dump(out/"F1_HC3_OPERATOR_STATE_EQUIVALENCE.json",eq)
 # Mandatory base and source-block residual SVD.
 B,bkeep,_=select({q:allmap[q] for q in SRC+CONT},104)
 if not diagnostics(B,donors,sources)["hc3_estimable"]:raise RuntimeError("STOP_F1_HC3_MANDATORY_BASE_NONESTIMABLE")
 spectra,loadings,scores,emb=source_svds(M,cols,donors,sources);spectra["mandatory_base"]={"retained_columns":bkeep,"geometry":diagnostics(B,donors,sources),"semantic_families_preserved":True}
 dump(out/"F1_HC3_SOURCE_SVD_SPECTRA.json",spectra);write_csv(out/"F1_HC3_SOURCE_SVD_LOADINGS.csv",loadings);write_csv(out/"F1_HC3_SOURCE_SVD_SCORES.csv",scores)
 frontier=[]
 ranks={q:spectra[q]["residual_rank"] for q in ["HVS","NPH52","SEA_AD"]}
 for rh,rn,rs in product(range(ranks["HVS"]+1),range(ranks["NPH52"]+1),range(ranks["SEA_AD"]+1)):
  xx=np.column_stack([B,emb["HVS"][:,:rh],emb["NPH52"][:,:rn],emb["SEA_AD"][:,:rs]]);d=diagnostics(xx,donors,sources)
  ev=[]
  for q,r in [("HVS",rh),("NPH52",rn),("SEA_AD",rs)]:ev.append(float(spectra[q]["cumulative_frobenius_variance"][r-1]) if r else 0.)
  frontier.append({"r_HVS":rh,"r_NPH52":rn,"r_SEAAD":rs,"rank":d["rank"],"df":d["df"],"k_over_n":d["k_over_n"],"n_over_k":d["n_over_k"],"HVS_variance_explained":ev[0],"NPH52_variance_explained":ev[1],"SEA_AD_variance_explained":ev[2],"equal_source_mean_variance_explained":float(np.mean(ev)),"minimum_source_variance_explained":float(np.min(ev)),"max_leverage":d["max_leverage"],"max_leverage_HVS":d["max_leverage_by_source"]["HVS"],"max_leverage_NPH52":d["max_leverage_by_source"]["NPH52"],"max_leverage_SEA_AD":d["max_leverage_by_source"]["SEA_AD"],"max_leverage_donor":d["max_leverage_donor"],"min_one_minus_h":d["min_one_minus_h"],"hc3_estimable":d["hc3_estimable"],"above_2k_over_n_count":len(d["above_2k_over_n"]),"above_3k_over_n_count":len(d["above_3k_over_n"]),"loo_rank_stable":d["loo_rank_stable"],"worst_loo_rank_loss":d["worst_loo_rank_loss"],"condition_number":d["condition_number"],"smallest_nonzero_singular_value":d["smallest_nonzero_singular_value"]})
 write_csv(out/"F1_HC3_SVD_PREFIX_FRONTIER.csv",frontier)
 # Global residual SVD comparator.
 Q=np.linalg.svd(B,full_matrices=False)[0][:,:rank(B)];R=O-Q@(Q.T@O);U,s,V=np.linalg.svd(R,full_matrices=False);U,V=orient(U,V);rr=rank(R);Z=U[:,:rr]*s[:rr];ev=s*s;cum=np.cumsum(ev)/ev.sum();glob=[]
 for r in range(rr+1):
  d=diagnostics(np.column_stack([B,Z[:,:r]]),donors,sources);glob.append({"r_global":r,"residual_variance_explained":float(cum[r-1]) if r else 0.,"rank":d["rank"],"df":d["df"],"k_over_n":d["k_over_n"],"n_over_k":d["n_over_k"],"max_leverage":d["max_leverage"],"max_leverage_HVS":d["max_leverage_by_source"]["HVS"],"max_leverage_NPH52":d["max_leverage_by_source"]["NPH52"],"max_leverage_SEA_AD":d["max_leverage_by_source"]["SEA_AD"],"max_leverage_donor":d["max_leverage_donor"],"min_one_minus_h":d["min_one_minus_h"],"hc3_estimable":d["hc3_estimable"],"above_2k_over_n_count":len(d["above_2k_over_n"]),"above_3k_over_n_count":len(d["above_3k_over_n"]),"loo_rank_stable":d["loo_rank_stable"],"worst_loo_rank_loss":d["worst_loo_rank_loss"],"condition_number":d["condition_number"],"smallest_nonzero_singular_value":d["smallest_nonzero_singular_value"]})
 write_csv(out/"F1_HC3_GLOBAL_SVD_FRONTIER.csv",glob)
 # Raw-order comparator: stop at first rank-increasing addition that crosses HC3 boundary.
 def raw_safe(order):
  xx=B.copy();names=[];trace=[]
  for q in order:
   v=allmap[q];cand=np.column_stack([xx,v-v.mean()])
   if rank(cand)==rank(xx):trace.append({"operator":q,"rank_increasing":False,"would_be_estimable":bool(np.all(1-hat(xx)>BOUNDARY))});continue
   ok=bool(np.all(1-hat(cand)>BOUNDARY));trace.append({"operator":q,"rank_increasing":True,"would_be_estimable":ok})
   if not ok:return names,q,trace,xx
   xx=cand;names.append(q)
  return names,None,trace,xx
 f,ff,ft,fx=raw_safe(OPS);r,rf,rt,rx=raw_safe(OPS[::-1]);same=rank(np.column_stack([fx,rx]))==rank(fx)==rank(rx)
 dump(out/"F1_HC3_RAW_ORDER_COMPARATOR.json",{"numeric_order":{"safe_columns":f,"first_nonestimable":ff,"trace":ft},"reverse_order":{"safe_columns":r,"first_nonestimable":rf,"trace":rt},"safe_subspaces_equal":same,"RAW_COLUMN_SAFE_SELECTION_IS_ORDER_DEPENDENT":not same,"diagnostic_only":True})
 # Synthetic arithmetic, including span/basis invariance.
 def hc3(y,xx):
  hh=hat(xx)
  if np.any(1-hh<=BOUNDARY):return {"estimable":False,"se":None}
  inv=np.linalg.inv(xx.T@xx);beta=inv@xx.T@y;res=y-xx@beta;u=res/(1-hh);cov=inv@(xx.T@(xx*(u*u)[:,None]))@inv;se=float(np.sqrt(max(0.,cov[0,0])));return {"estimable":bool(np.isfinite(se) and se>0),"se":se}
 y=np.sin(np.arange(104)*0.173)+np.cos(np.arange(104)*0.071);rng=np.random.default_rng(1501);A=np.linalg.qr(rng.normal(size=(B.shape[1],B.shape[1])))[0];Br=B@A
 reps={"mandatory_base":B,"old_failing_design":X,"svd_0_0_0":B,"svd_1_1_1":np.column_stack([B,emb["HVS"][:,:1],emb["NPH52"][:,:1],emb["SEA_AD"][:,:1]]),"svd_full":np.column_stack([B,emb["HVS"],emb["NPH52"],emb["SEA_AD"]])}
 def stable_projection_diag(x):
  u=np.linalg.svd(x,full_matrices=False)[0][:,:rank(x)];return np.sum(u*u,axis=1)
 synthetic_span=np.linalg.qr(rng.normal(size=(104,B.shape[1])),mode="reduced")[0];synthetic_reparameterized=synthetic_span@A
 stable_diff=float(np.max(np.abs(stable_projection_diag(synthetic_span)-stable_projection_diag(synthetic_reparameterized))))
 frozen_gram_diff=float(np.max(np.abs(hat(B)-hat(Br))))
 syn={q:hc3(y,x) for q,x in reps.items()};syn.update({"old_design_fails":not syn["old_failing_design"]["estimable"],"unit_leverage_direction_undefined":not hc3(y,np.column_stack([B,np.eye(104)[:,0]]))["estimable"],"basis_invariance_synthetic_full_rank_span_max_abs":stable_diff,"mandatory_base_frozen_gram_reparameterization_max_abs":frozen_gram_diff,"basis_invariance_pass":bool(stable_diff<=1e-12),"basis_invariance_note":"A well-conditioned synthetic raw-operator span verifies mathematical invariance. The ill-conditioned mandatory-base Gram-inverse discrepancy is reported separately; rotation does not change the underlying leverage geometry and is not a repair.","synthetic_outcomes_only":True});dump(out/"F1_HC3_SYNTHETIC_ARITHMETIC.json",syn)
 md="# F1 HC3 many-covariate diagnostics\n\nHC3 remains the frozen decision estimator. No HC0/HC1/HC2/HC4/HC5/CJN or many-covariate estimator is substituted. The reported n=104, k, n/k, mean/max leverage, max-to-mean leverage, exact HC3 boundary, and conventional 2k/n and 3k/n flags are descriptive and create no decision threshold. A future design freeze must consider both exact HC3 estimability and finite-sample degradation from high leverage/many covariates before h reaches one. Candidate-level quantities are in the frontier tables.\n"
 (out/"F1_HC3_MANY_COVARIATE_DIAGNOSTICS.md").write_text(md,encoding="utf-8")
 print(json.dumps({"status":"DIAGNOSTIC_DERIVATION_COMPLETE","frontier_rows":len(frontier),"global_rows":len(glob),"old_failure_reproduced":True,"out":str(out)}))

if __name__=="__main__":main()
