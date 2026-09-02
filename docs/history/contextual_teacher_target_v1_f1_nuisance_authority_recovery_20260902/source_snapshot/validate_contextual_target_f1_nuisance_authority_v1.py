#!/usr/bin/env python3
"""Independent, outcome-blind reproduction of the F1 nuisance authority."""
from __future__ import annotations
import csv, hashlib, json, multiprocessing as mp, os, struct
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"outputs/_staging_contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
ASSIGN=ROOT/"outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv"
NULL=ROOT/"outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_PRIMARY_MAP.csv"
STATES=ROOT/"exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
EXPR=ROOT/"outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4"
V8=ROOT/"outputs/full104_v014_20260826/full104_expression_interface_v8_verified/FULL104_EXPRESSION_INTERFACE_V8"
SEED="c5c5bc472850f17f0ca6249e3a2765e5924d411ef054691a5e7a5d9d29363a4f"
SOURCES=["HVS","NPH52","SEA_AD"]
GROWS={};GASSIGN={};GNULL={};GSTATES=None

def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(8<<20),b""):h.update(b)
 return h.hexdigest()
def root_hash(donors,cols,m):
 b=bytearray(b"F1_NUISANCE_DONOR_DESIGN_V1\0")
 for seq in (donors,cols):
  b.extend(struct.pack("<I",len(seq)))
  for s in seq:x=s.encode();b.extend(struct.pack("<I",len(x)));b.extend(x)
 b.extend(struct.pack("<QQ",*m.shape));b.extend(np.asarray(m,dtype="<f8",order="C").tobytes())
 return hashlib.sha256(b).hexdigest()
def independent_mask(locator,q,op):
 elig=np.flatnonzero(GSTATES[op]==1).astype(np.int32);elig=elig[elig!=q];prefix=f"{SEED}|{locator}|{q}|".encode()
 dig=np.empty(len(elig),dtype="V32")
 for i,j in enumerate(elig):dig[i]=hashlib.sha256(prefix+str(int(j)).encode()).digest()
 k=len(elig)*60//100;order=np.argpartition(dig,k-1);part=order[:k];threshold=dig[order[k-1]]
 if np.count_nonzero(dig==threshold)>1:
  selected=np.asarray([j for _,j in sorted((bytes(dig[i]),int(elig[i])) for i in range(len(elig)))[:k]],np.int32)
 else:selected=elig[part]
 if q in selected or np.any(GSTATES[op,selected]!=1):raise RuntimeError("mask semantics")
 return selected
def calc(cell):
 r=GROWS[cell];n=GROWS[GNULL[cell]];vals=[]
 for q,p,rep in GASSIGN[cell]:
  u=independent_mask(r["locator"],q,r["op"]);v=np.zeros(41238,bool);v[u]=1;ri=v[r["idx"]];ni=v[n["idx"]]
  dv=float(r["cnt"][ri].sum(dtype=np.int64)/r["lib"]-n["cnt"][ni].sum(dtype=np.int64)/n["lib"])
  dz=float((len(u)-np.count_nonzero(ri))/len(u)-(len(u)-np.count_nonzero(ni))/len(u))
  vals.append((q,p,rep,dv,dz,hashlib.sha256(np.sort(u).astype("<i4").tobytes()).hexdigest()))
 return cell,float(np.mean([x[3] for x in vals])),float(np.mean([x[4] for x in vals])),vals
def schema_accept(donors,cols,m,expected_donors,expected_cols):return donors==expected_donors and cols==expected_cols and m.dtype==np.float64 and m.shape==(104,49)

def main():
 global GROWS,GASSIGN,GNULL,GSTATES
 auth=json.loads((OUT/"F1_NUISANCE_DONOR_DESIGN_AUTHORITY.json").read_text());schema=json.loads((OUT/"F1_NUISANCE_COLUMN_SCHEMA.json").read_text())
 assignments=pd.read_csv(ASSIGN,dtype=str);null=pd.read_csv(NULL,dtype=str);GNULL=dict(zip(null.recipient_canonical_cell_id,null.source_canonical_cell_id))
 v8_selection=pd.read_csv(V8/"interface_check_v8r1/FULL104_EXPRESSION_INTERFACE_SELECTION.csv",dtype=str)
 target=set(assignments.canonical_cell_id)|set(GNULL.values())|set(v8_selection.canonical_cell_id)
 blocks=pd.read_csv(OUT/"F1_NUISANCE_EXPRESSION_BLOCKS_USED.csv",dtype=str);GROWS={}
 for br in blocks.itertuples(index=False):
  cp=ROOT/br.counts_path;mpath=ROOT/br.meta_path
  if sha(cp)!=br.counts_sha256 or sha(mpath)!=br.meta_sha256:raise RuntimeError("block hash")
  meta=pd.read_csv(mpath,dtype=str);z=np.load(cp,allow_pickle=False);data=z["data"];idx=z["indices"];ind=z["indptr"]
  for i,mr in enumerate(meta.itertuples(index=False)):
   cell=str(mr.canonical_cell_id)
   if cell not in target:continue
   aa,bb=int(ind[i]),int(ind[i+1]);cnt=np.asarray(data[aa:bb],np.int64);ii=np.asarray(idx[aa:bb],np.int32);lib=int(mr.source_library)
   x=np.log1p(cnt.astype(np.float64)*10000/lib).astype(np.float32);back=np.rint(np.expm1(x.astype(np.float64))*lib/10000).astype(np.int64)
   if not np.array_equal(cnt,back):raise RuntimeError("roundtrip")
   op=int(br.block_key[2:4]);GROWS[cell]={"idx":ii,"cnt":back,"lib":lib,"op":op}
 if set(GROWS)!=target:raise RuntimeError("row provenance")
 cellauth=json.loads((ROOT/"outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_CELL_DONOR_OPERATOR_AUTHORITY.json").read_text())["selected_rows"]
 loc={r["canonical_cell_id"]:r["row_locator"] for r in cellauth}
 for c in set(assignments.canonical_cell_id):GROWS[c]["locator"]=loc[c]
 for r in null.itertuples(index=False):GROWS[r.source_canonical_cell_id]["locator"]=r.source_row_locator
 with np.load(STATES,allow_pickle=False) as z:GSTATES=np.asarray(z["states"],np.uint8)
 GASSIGN=defaultdict(list)
 for r in assignments.itertuples(index=False):GASSIGN[r.canonical_cell_id].append((int(r.selected_query_address),r.program,int(r.draw_replicate)))
 cells=sorted(GASSIGN)
 workers=max(1,min(16,os.cpu_count() or 1))
 if os.name=="posix" and workers>1:
  with mp.get_context("fork").Pool(workers) as pool:results=pool.map(calc,cells,chunksize=8)
 else:results=[calc(c) for c in cells]
 by={x[0]:x for x in results}
 unique=assignments.drop_duplicates("canonical_cell_id");donors=sorted(assignments.donor_id.unique());weights={r.canonical_cell_id:int(r.cell_weight_numerator)/int(r.cell_weight_denominator) for r in unique.itertuples(index=False)}
 support=np.count_nonzero(GSTATES==1,axis=1);cols=[f"source_{s}" for s in SOURCES]+[f"operator_mix_{i:03d}" for i in range(42)]+["recipient_physical_support","recipient_depth","correct_minus_null_visible_depth","correct_minus_null_measured_zero_rate"]
 m=np.zeros((104,49),np.float64)
 for di,d in enumerate(donors):
  sub=unique[unique.donor_id.eq(d)];src=sub.source.unique().tolist();m[di,SOURCES.index(src[0])]=1
  for r in sub.itertuples(index=False):
   w=weights[r.canonical_cell_id];op=int(r.operator_index);m[di,3+op]+=w;m[di,45]+=w*support[op];m[di,46]+=w*GROWS[r.canonical_cell_id]["lib"];m[di,47]+=w*by[r.canonical_cell_id][1];m[di,48]+=w*by[r.canonical_cell_id][2]
 prod=np.fromfile(OUT/"F1_NUISANCE_DONOR_DESIGN_F64LE.bin",dtype="<f8").reshape(104,49)
 comp=pd.read_csv(OUT/"F1_NUISANCE_CELL_ASSIGNMENT_COMPONENTS.csv.gz",dtype={"canonical_cell_id":str})
 expected={(r.canonical_cell_id,int(r.query_address),r.program,int(r.draw_replicate)):(float(r.delta_visible_depth),float(r.delta_measured_zero_rate),r.recipient_u60_sorted_index_sha256) for r in comp.itertuples(index=False)}
 actual={}
 for c,_,_,vals in results:
  for q,p,rep,dv,dz,mh in vals:actual[(c,q,p,rep)]=(dv,dz,mh)
 pair_keys=set(expected)==set(actual);pair_max=max(max(abs(expected[k][i]-actual[k][i]) for i in (0,1)) for k in expected);mask_equal=all(expected[k][2]==actual[k][2] for k in expected)
 exact=np.array_equal(prod,m);root=root_hash(donors,cols,m)
 checks={"pair_keys":pair_keys,"pair_max_abs":pair_max,"mask_hashes_exact":mask_equal,"matrix_bytes_exact":exact,"independent_root":root,"expected_root":auth["semantic_root_sha256"],"schema_exact":schema_accept(donors,cols,m,schema["donor_order"],schema["columns"]),"matrix_max_abs":float(np.max(np.abs(prod-m)))}
 (OUT/"F1_NUISANCE_INDEPENDENT_DIAGNOSTIC.json").write_text(json.dumps(checks,indent=2,sort_keys=True)+"\n")
 if not (pair_keys and pair_max<=2e-16 and mask_equal and exact and root==auth["semantic_root_sha256"] and checks["schema_exact"]):raise RuntimeError("STOP_F1_NUISANCE_DESIGN_INDEPENDENT_MISMATCH "+repr(checks))

 # Independent 84-row inverse round-trip against the previously frozen values.
 vsel=v8_selection.assign(selection_row=v8_selection.selection_row.astype(int)).sort_values("selection_row")
 with np.load(V8/"model_inputs/FULL104_EXPRESSION_INTERFACE_PAYLOAD.npz",allow_pickle=False) as z:vx=np.asarray(z["normalized_values"])
 vfail=0
 for i,r in enumerate(vsel.itertuples(index=False)):
  rr=GROWS[str(r.canonical_cell_id)]
  raw=np.zeros(41238,np.int64);raw[rr["idx"]]=rr["cnt"];back=np.rint(np.expm1(vx[i].astype(np.float64))*rr["lib"]/10000).astype(np.int64);vfail+=int(np.count_nonzero(raw!=back))
 if vfail:raise RuntimeError("STOP_F1_NUISANCE_COUNT_ROUNDTRIP_FAILURE")

 # Adversarial domain checks; each either violates schema or changes the semantic root.
 attacks={}
 def changed(label,dd,cc,mm):attacks[label]=not schema_accept(dd,cc,mm,donors,cols) or root_hash(dd,cc,mm)!=root
 z=m.copy();z[:,46]=np.arange(104);changed("depth_replaced_by_nonzero_count",donors,cols,z)
 z=m.copy();z[:,46]=1.;changed("depth_replaced_by_normalized_sum",donors,cols,z)
 z=m.copy();z[:,3:45]=0
 for i,d in enumerate(donors):
  counts=Counter(unique.loc[unique.donor_id.eq(d),"operator_index"].astype(int));tot=sum(counts.values())
  for o,n in counts.items():z[i,3+o]=n/tot
 changed("raw_cell_frequency_operator_mix",donors,cols,z)
 changed("source_order_changed",donors,[cols[1],cols[0],*cols[2:]],m[:,[1,0,*range(2,49)]].copy())
 changed("reference_category_dropped",donors,cols[1:],m[:,1:].copy())
 attacks["float32_serialization"]=not schema_accept(donors,cols,m.astype(np.float32),donors,cols)
 changed("donor_reorder",donors[::-1],cols,m[::-1].copy())
 # Exact mask/source-library attacks on one unequal-library pair.
 first=next(c for c in cells if GROWS[c]["lib"]!=GROWS[GNULL[c]]["lib"]);q=GASSIGN[first][0][0];u=independent_mask(GROWS[first]["locator"],q,GROWS[first]["op"]);un=independent_mask(GROWS[GNULL[first]]["locator"],q,GROWS[first]["op"])
 attacks["null_mask_instead_of_recipient"]=not np.array_equal(np.sort(u),np.sort(un))
 n=GROWS[GNULL[first]];wrong=np.rint(np.expm1(np.log1p(n["cnt"]*10000/n["lib"]))*GROWS[first]["lib"]/10000).astype(np.int64);attacks["recipient_library_used_for_null"]=not np.array_equal(wrong,n["cnt"])
 if not all(attacks.values()):raise RuntimeError("adversarial fail "+repr(attacks))
 validation={"status":"PASS_F1_NUISANCE_INDEPENDENT_VALIDATION","production_builder_imported":False,"donors":104,"columns":49,"scalar_support_exact":True,"source_library_rows":len(GROWS),"pair_keyspace_exact":pair_keys,"pair_delta_max_abs":pair_max,"all_u60_hashes_exact":mask_equal,"matrix_byte_exact":exact,"semantic_root_sha256":root,"v8_intersecting_roundtrip_failures":vfail,"model_outcomes_read":False}
 (OUT/"F1_NUISANCE_INDEPENDENT_VALIDATION.json").write_text(json.dumps(validation,indent=2,sort_keys=True)+"\n")
 (OUT/"F1_NUISANCE_ADVERSARIAL.json").write_text(json.dumps({"status":"PASS","attacks":attacks},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"status":validation["status"],"root":root,"pair_max":pair_max,"attacks":len(attacks)}))
if __name__=="__main__":main()
