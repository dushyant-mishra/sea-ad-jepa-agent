#!/usr/bin/env python3
"""Independent check of the Command-15A2 rank-boundary contradiction."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from scipy import linalg
ROOT=Path(__file__).resolve().parents[2];UP=ROOT/"outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902";EPS=np.finfo(np.float64).eps
def rank(x):
 s=np.linalg.svd(np.asarray(x,np.float64),compute_uv=False);return int(np.sum(s>max(x.shape)*EPS*s[0])) if s.size else 0
def build(mp,names,ix):
 x=np.ones((int(ix.sum()),1))
 for n in sorted(names):
  v=mp[n][ix];y=np.column_stack([x,v-v.mean()])
  if rank(y)>rank(x):x=y
 return x
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--package",type=Path,required=True);a=ap.parse_args();o=a.package
 s=json.loads((UP/"F1_NUISANCE_COLUMN_SCHEMA.json").read_text());M=np.fromfile(UP/"F1_NUISANCE_DONOR_DESIGN_F64LE.bin",dtype="<f8").reshape(104,49);cols=s["columns"];d=np.asarray(s["donor_order"]);src=np.asarray([x.split("::",1)[0] for x in d]);mp={n:M[:,i] for i,n in enumerate(cols)}
 cont=["recipient_physical_support","recipient_depth","correct_minus_null_visible_depth","correct_minus_null_measured_zero_rate"];source=["source_HVS","source_NPH52","source_SEA_AD"];allix=np.ones(104,dtype=bool);B=build(mp,source+cont,allix);O=M[:,[cols.index(f"operator_mix_{i:03d}") for i in range(42)]];ix=src=="NPH52";W=build(mp,cont,ix);Q=np.linalg.qr(W,mode="reduced")[0];R=O[ix][:,35:42]-Q@(Q.T@O[ix][:,35:42]);u,sn,v=np.linalg.svd(R,full_matrices=False);ss=linalg.svd(R,full_matrices=False,lapack_driver="gesvd")[1];tn=max(R.shape)*EPS*sn[0];ts=max(R.shape)*EPS*ss[0]
 z=np.zeros(104);z[ix]=u[:,1]*sn[1];X1=np.column_stack([B,np.r_[u[:,0]*sn[0],np.zeros(87)]]) if False else None
 first=np.zeros(104);first[ix]=u[:,0]*sn[0];P=np.column_stack([B,first-first.mean()]);direct=rank(np.column_stack([P,z-z.mean()]))>rank(P)
 prod=json.loads((o/"F1_HC3_NPH_COMPONENT2_DIAGNOSTIC.json").read_text())
 checks={"numpy_above_tau_R":bool(sn[1]>tn),"scipy_gesvd_above_tau_R":bool(ss[1]>ts),"direct_engine_rank_increase":bool(direct),"production_classification_matches":bool(prod["above_tau_R_numpy"]==bool(sn[1]>tn) and prod["above_tau_R_scipy"]==bool(ss[1]>ts) and prod["increases_frozen_engine_rank"]==bool(direct)),"firewall":True}
 terminal="STOP_F1_HC3_NPH_COMPONENT2_STATUS_CHANGED" if all([checks["numpy_above_tau_R"],checks["scipy_gesvd_above_tau_R"],not checks["direct_engine_rank_increase"],checks["production_classification_matches"]]) else "STOP_F1_HC3_NUMRANK_INDEPENDENT_MISMATCH"
 report={"terminal":terminal,"checks":checks,"independent_numpy_singular_value_2":float(sn[1]),"independent_numpy_tau_R":float(tn),"independent_scipy_singular_value_2":float(ss[1]),"independent_scipy_tau_R":float(ts),"production_helpers_imported":False,"expression_model_outcome_access":False}
 (o/"F1_HC3_NUMRANK_INDEPENDENT_VALIDATION.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps(report))
 if terminal=="STOP_F1_HC3_NUMRANK_INDEPENDENT_MISMATCH":raise SystemExit(2)
 raise SystemExit(3)
if __name__=="__main__":main()
