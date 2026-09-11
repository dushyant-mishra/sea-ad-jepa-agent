#!/usr/bin/env python3
"""Schema/validation for V21 S0-S4 measurements; never executes biology."""
from __future__ import annotations
import hashlib,json,math
from typing import Any,Mapping,Sequence

STOP="STOP_T0_V21_MEASUREMENT_ARTIFACT_INVALID"
KIND="t0_v21_estimator_measurement_artifact_v1"
CANDIDATES=("S0","S1","S2","S3","S4")
RIDGE_METRICS=("beta_direction","cell_score_geometry","donor_summaries")
REQ_ROOTS=("expression_root_digest","donor_role_ledger_digest","molecular_address_digest","common_core_digest","code_sha","contract_sha")

def _fail(m): raise RuntimeError(f"{STOP}: {m}")
def _hex(n,v):
 s=str(v)
 if len(s)!=64 or any(c not in '0123456789abcdef' for c in s): _fail(f"{n} must be lowercase SHA-256")
 return s
def _plain(v):
 if isinstance(v,Mapping): return {str(k):_plain(v[k]) for k in sorted(v,key=str)}
 if isinstance(v,(list,tuple)): return [_plain(x) for x in v]
 if isinstance(v,(str,int,bool)) or v is None:return v
 if isinstance(v,float):
  if not math.isfinite(v):_fail("nonfinite value")
  return v
 _fail(f"unsupported type {type(v).__name__}")
def digest(v,domain): return hashlib.sha256(domain.encode()+b'\0'+json.dumps(_plain(v),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def seal_measurement_artifact(*,source_roots:Mapping[str,str],candidate_table:Mapping[str,Mapping[str,Any]],thinning_draws:Sequence[Mapping[str,Any]],biology_preservation:Mapping[str,Any],ridge_stability:Mapping[str,Mapping[str,Any]])->dict[str,Any]:
 missing=[k for k in REQ_ROOTS if k not in source_roots]
 if missing:_fail(f"source roots missing {missing}")
 for k in REQ_ROOTS:_hex(k,source_roots[k])
 if tuple(sorted(candidate_table))!=CANDIDATES:_fail("candidate table must contain exactly S0-S4")
 if not thinning_draws:_fail("thinning realization provenance is required")
 for d in thinning_draws:
  for k in ("retention","draw_index","draw_digest"):
   if k not in d:_fail(f"thinning draw missing {k}")
  r=float(d["retention"])
  if not (0<r<=1):_fail("thinning retention must be in (0,1]")
  _hex("draw_digest",d["draw_digest"])
 for c in CANDIDATES:
  row=candidate_table[c]
  for k in ("definition_digest","worst_standardized_displacement","selection_eligible"):
   if k not in row:_fail(f"{c} missing {k}")
  _hex(f"{c}.definition_digest",row["definition_digest"])
  if not math.isfinite(float(row["worst_standardized_displacement"])):_fail(f"{c} displacement nonfinite")
  if c not in biology_preservation:_fail(f"{c} missing held-out biology preservation envelope")
  if c not in ridge_stability:_fail(f"{c} missing ridge stability")
  metrics=ridge_stability[c]
  if set(metrics)!=set(RIDGE_METRICS):_fail(f"{c} ridge stability must cover exactly {RIDGE_METRICS}")
  for m in RIDGE_METRICS:
   vals=metrics[m]
   if not isinstance(vals,Mapping) or "lodo_envelope" not in vals or "induced_displacement" not in vals:_fail(f"{c}/{m} incomplete")
   if not all(math.isfinite(float(vals[x])) for x in ("lodo_envelope","induced_displacement")):_fail(f"{c}/{m} nonfinite")
 body={"kind":KIND,"source_roots":_plain(source_roots),"candidate_table":_plain(candidate_table),"thinning_draws":_plain(thinning_draws),"biology_preservation":_plain(biology_preservation),"ridge_stability":_plain(ridge_stability)}
 body["artifact_digest"]=digest(body,"T0_V21_MEASUREMENT_ARTIFACT_V1")
 return body

def validate_measurement_artifact(artifact:Mapping[str,Any],*,expected_source_roots:Mapping[str,str])->dict[str,Any]:
 if artifact.get("kind")!=KIND:_fail("validated measurement artifact required")
 rec=artifact.get("artifact_digest",""); body={k:artifact[k] for k in artifact if k!="artifact_digest"}
 if rec!=digest(body,"T0_V21_MEASUREMENT_ARTIFACT_V1"):_fail("artifact digest does not recompute")
 if dict(artifact.get("source_roots",{}))!=dict(expected_source_roots):_fail("source roots do not match external expected authority")
 rebuilt=seal_measurement_artifact(source_roots=artifact["source_roots"],candidate_table=artifact["candidate_table"],thinning_draws=artifact["thinning_draws"],biology_preservation=artifact["biology_preservation"],ridge_stability=artifact["ridge_stability"])
 if rebuilt["artifact_digest"]!=rec:_fail("artifact structure invalid")
 return {"verified":True,"artifact_digest":rec}
