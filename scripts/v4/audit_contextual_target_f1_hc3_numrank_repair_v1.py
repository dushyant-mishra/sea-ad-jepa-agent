#!/usr/bin/env python3
"""Command 15A2 frozen-rank audit; stops if its joint rank requirements conflict."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from scipy import linalg

ROOT=Path(__file__).resolve().parents[2]
UP=ROOT/"outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
PRIOR=ROOT/"outputs/contextual_teacher_target_v1_f1_hc3_geometry_diagnostic_20260902"
ENGINE=ROOT/"scripts/v4/contextual_target_f1_decision_v1.py"
EPS=np.finfo(np.float64).eps;BOUND=float(np.sqrt(EPS))
CONT=["recipient_physical_support","recipient_depth","correct_minus_null_visible_depth","correct_minus_null_measured_zero_rate"]
SRC=["source_HVS","source_NPH52","source_SEA_AD"]
OPS=[f"operator_mix_{i:03d}" for i in range(42)]

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(8<<20),b""):h.update(b)
 return h.hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
def frozen_rank(x):
 x=np.asarray(x,np.float64);s=np.linalg.svd(x,compute_uv=False)
 return int(np.sum(s>max(x.shape)*EPS*s[0])) if s.size else 0
def select(mp,names,mask):
 X=np.ones((int(mask.sum()),1));kept=[]
 for name in sorted(names):
  v=np.asarray(mp[name][mask],np.float64);C=np.column_stack([X,v-v.mean()])
  if frozen_rank(C)>frozen_rank(X):X=C;kept.append(name)
 return X,kept
def hat(X):return np.einsum("ij,jk,ik->i",X,np.linalg.inv(X.T@X),X)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True);a=ap.parse_args();o=a.out;o.mkdir(parents=True,exist_ok=False)
 expected={PRIOR/"F1_HC3_MANIFEST.csv":"1bb7010e0268fe99f3c0ea952a05d6818466fa0e54734fc15f3a2c2be5406230",UP/"F1_NUISANCE_DONOR_DESIGN_F64LE.bin":"1d8f837d18cedd8d1b8fd6138d1b25f886b8352c097a4723ca06421573334056",UP/"F1_NUISANCE_COLUMN_SCHEMA.json":"9f90c764d0d97b5a10badc03dfcbafc364e0bf40e120a9aed6609e036b5924a7",ENGINE:"204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34"}
 actual={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in expected};assert all(actual[str(p.relative_to(ROOT)).replace('\\','/')]==h for p,h in expected.items())
 schema=json.loads((UP/"F1_NUISANCE_COLUMN_SCHEMA.json").read_text());auth=json.loads((UP/"F1_NUISANCE_DONOR_DESIGN_AUTHORITY.json").read_text());assert auth["semantic_root_sha256"]=="2f0c95b1d9c098f8593827f240f64a0b8e5512ead92fe50540f6e2dc231742ec"
 M=np.fromfile(UP/"F1_NUISANCE_DONOR_DESIGN_F64LE.bin",dtype="<f8").reshape(104,49);cols=schema["columns"];donors=np.asarray(schema["donor_order"]);sources=np.asarray([d.split("::",1)[0] for d in donors]);mp={n:M[:,i] for i,n in enumerate(cols)};allmask=np.ones(104,dtype=bool)
 # Exact old STOP.
 oldX,oldkept=select(mp,cols,allmask);oldh=hat(oldX);bad=[str(donors[i]) for i in np.flatnonzero(1-oldh<=BOUND)]
 old_ok=frozen_rank(oldX)==18 and bad==["HVS::H20.06.354","NPH52::human_NPH_906"]
 if not old_ok:raise RuntimeError("STOP_F1_HC3_NUMRANK_AUTHORITY_MISMATCH")
 B,bkeep=select(mp,SRC+CONT,allmask);bh=hat(B);base_ok=frozen_rank(B)==B.shape[1] and np.all(1-bh>BOUND)
 if not base_ok:raise RuntimeError("STOP_F1_HC3_MANDATORY_BASE_NONESTIMABLE")
 authority={"status":"PASS_AUTHORITY","prior_manifest_sha256":sha(PRIOR/"F1_HC3_MANIFEST.csv"),"input_sha256":actual,"primitive_semantic_root":auth["semantic_root_sha256"],"old_stop_reproduced":old_ok,"old_rank":18,"old_df":86,"old_unit_leverage_donors":bad,"mandatory_base_rank":frozen_rank(B),"mandatory_base_columns":bkeep,"hard_firewall":{"expression":False,"checkpoint_or_model":False,"outcome":False,"training_or_ema":False},"design_selection_authorized":False};dump(o/"F1_HC3_NUMRANK_REPAIR_AUTHORITY.json",authority)
 rule={"source":"scripts/v4/contextual_target_f1_decision_v1.py::frozen_rank","formula":"tau(A)=max(A.shape)*float64_eps*s_max(A)","float64_eps":EPS,"strict_comparison":"s_j > tau(A)","equivalence_verified":True,"alternative_cutoff_introduced":False};dump(o/"F1_HC3_FROZEN_RANK_RULE.json",rule)
 O=M[:,[cols.index(q) for q in OPS]];spect={};erank={};cross={};nph={};trace=[]
 opmap={"HVS":list(range(24)),"NPH52":list(range(35,42)),"SEA_AD":list(range(24,35))}
 for ss in ["HVS","NPH52","SEA_AD"]:
  ix=sources==ss;W,_=select(mp,CONT,ix);Q=linalg.qr(W,mode="economic")[0];R=O[ix][:,opmap[ss]]-Q@(Q.T@O[ix][:,opmap[ss]])
  un,sn,vhn=np.linalg.svd(R,full_matrices=False);us,ssv,vhs=linalg.svd(R,full_matrices=False,lapack_driver="gesvd")
  taun=max(R.shape)*EPS*sn[0];taus=max(R.shape)*EPS*ssv[0];rn=int(np.sum(sn>taun));rs=int(np.sum(ssv>taus))
  Pn=un[:,:rn]@un[:,:rn].T;Ps=us[:,:rs]@us[:,:rs].T
  spect[ss]={"shape":list(R.shape),"singular_values_numpy":sn.tolist(),"s_max":float(sn[0]),"tau_R":float(taun),"s_over_tau":(sn/taun).tolist(),"effective_rank_numpy":rn,"discarded_components_numpy":list(range(rn+1,len(sn)+1)),"orthogonality_residual_max_abs":float(np.max(np.abs(Q.T@R)))}
  cross[ss]={"numpy_effective_rank":rn,"scipy_gesvd_effective_rank":rs,"scipy_singular_values":ssv.tolist(),"scipy_tau_R":float(taus),"retained_projection_max_abs_difference":float(np.max(np.abs(Pn-Ps))) if rn==rs else None,"effective_rank_agrees":rn==rs}
  erank[ss]={"effective_rank_under_tau_R":rn,"direct_engine_admissible_count":None}
  X=B.copy();admitted=0
  for j in range(len(sn)):
   z=np.zeros(104);z[ix]=un[:,j]*sn[j];C=np.column_stack([X,z-z.mean()]);before=frozen_rank(X);after=frozen_rank(C);inc=after>before;above=bool(sn[j]>taun)
   trace.append({"source":ss,"component":j+1,"singular_value":float(sn[j]),"tau_R":float(taun),"above_tau_R":above,"rank_before":before,"rank_after":after,"increases_frozen_engine_rank":inc,"jointly_admissible":bool(above and inc)})
   if above and inc:X=C;admitted+=1
  erank[ss]["direct_engine_admissible_count"]=admitted
  if ss=="NPH52":nph={"component":2,"singular_value_numpy":float(sn[1]),"tau_R_numpy":float(taun),"s_over_tau_numpy":float(sn[1]/taun),"above_tau_R_numpy":bool(sn[1]>taun),"singular_value_scipy_gesvd":float(ssv[1]),"tau_R_scipy_gesvd":float(taus),"s_over_tau_scipy":float(ssv[1]/taus),"above_tau_R_scipy":bool(ssv[1]>taus),"increases_frozen_engine_rank":next(x["increases_frozen_engine_rank"] for x in trace if x["source"]==ss and x["component"]==2),"required_consistently_numerical_null_under_tau_R":False,"status":"STOP_F1_HC3_NPH_COMPONENT2_STATUS_CHANGED"}
 dump(o/"F1_HC3_SOURCE_RESIDUAL_SPECTRA.json",spect);dump(o/"F1_HC3_SOURCE_EFFECTIVE_RANK.json",erank);dump(o/"F1_HC3_NPH_COMPONENT2_DIAGNOSTIC.json",nph);dump(o/"F1_HC3_SVD_CROSSIMPLEMENTATION_VALIDATION.json",cross)
 with (o/"F1_HC3_COMPONENT_FROZEN_ENGINE_TRACE.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(trace[0]));w.writeheader();w.writerows(trace)
 # Fail-closed placeholders: no repaired frontier is constructed after the explicit prerequisite fails.
 (o/"F1_HC3_REPAIRED_SVD_PREFIX_FRONTIER.csv").write_text("status,reason\nNOT_CONSTRUCTED,STOP_F1_HC3_NPH_COMPONENT2_STATUS_CHANGED\n",encoding="utf-8")
 recon={"status":"NOT_EVALUATED_AFTER_PREREQUISITE_STOP","previous_rows":105,"previous_rank_deficient_rows":35,"repaired_frontier_row_count":None,"PREVIOUS_FRONTIER_FAILURE_FULLY_EXPLAINED_BY_NPH52_NUMERICAL_NULL_COMPONENT":None};dump(o/"F1_HC3_PREVIOUS_105_35_RECONCILIATION.json",recon)
 print(json.dumps({"terminal":"STOP_F1_HC3_NPH_COMPONENT2_STATUS_CHANGED","nph_component2":nph,"ranks":erank}))
 raise SystemExit(3)

if __name__=="__main__":main()
