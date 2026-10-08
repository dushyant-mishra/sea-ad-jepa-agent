#!/usr/bin/env python3
"""Outcome-blind compatibility audit against the already-frozen HC3 engine."""
import hashlib, json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"outputs/_staging_contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
ENGINE=ROOT/"scripts/v4/contextual_target_f1_decision_v1.py"

def rank(x):
 s=np.linalg.svd(np.asarray(x,np.float64),compute_uv=False);tol=max(x.shape)*np.finfo(np.float64).eps*(s[0] if len(s) else 0.);return int(np.sum(s>tol))
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(8<<20),b""):h.update(b)
 return h.hexdigest()

s=json.loads((OUT/"F1_NUISANCE_COLUMN_SCHEMA.json").read_text())
m=np.fromfile(OUT/"F1_NUISANCE_DONOR_DESIGN_F64LE.bin",dtype="<f8").reshape(104,49)
X=np.ones((104,1),np.float64);kept=[]
for name in sorted(s["columns"]):
 v=m[:,s["columns"].index(name)];candidate=np.column_stack([X,v-v.mean()])
 if rank(candidate)>rank(X):X=candidate;kept.append(name)
xtxi=np.linalg.inv(X.T@X);h=np.einsum("ij,jk,ik->i",X,xtxi,X);threshold=float(np.sqrt(np.finfo(np.float64).eps))
bad=np.flatnonzero(1-h<=threshold)
doc={"status":"STOP_F1_NUISANCE_HC3_DESIGN_NONESTIMABLE" if len(bad) else "PASS","outcome_blind":True,"frozen_engine_path":"scripts/v4/contextual_target_f1_decision_v1.py","frozen_engine_sha256":sha(ENGINE),"design_rank":rank(X),"columns_including_intercept":X.shape[1],"df":104-rank(X),"retained_columns":kept,"hc3_denominator_threshold":threshold,"maximum_leverage":float(h.max()),"unit_leverage_donors":[{"donor_id":s["donor_order"][int(i)],"leverage":float(h[i]),"one_minus_leverage":float(1-h[i])} for i in bad],"consequence":"frozen hc3_intercept returns estimable=false before using any outcome whenever any 1-h <= sqrt(float64_eps)","nuisance_semantic_root_sha256":json.loads((OUT/"F1_NUISANCE_DONOR_DESIGN_AUTHORITY.json").read_text())["semantic_root_sha256"],"scientific_rule_changed":False,"model_outcomes_read":False}
(OUT/"F1_NUISANCE_HC3_COMPATIBILITY.json").write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n")
print(json.dumps(doc))
