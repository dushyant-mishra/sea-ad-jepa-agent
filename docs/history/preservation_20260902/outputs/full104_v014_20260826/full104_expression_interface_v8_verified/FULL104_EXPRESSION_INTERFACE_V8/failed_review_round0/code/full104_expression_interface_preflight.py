#!/usr/bin/env python3
"""Prospective freeze and bounded expression-interface proof for FULL104.

Freeze mode reads lineage metadata only. Execute mode is allowed only against a
hash-valid freeze and reads exactly two frozen reader-fit rows per operator.
"""
from __future__ import annotations
import argparse,csv,gzip,hashlib,heapq,json,subprocess,sys
from pathlib import Path
import h5py,numpy as np,pandas as pd
from scipy import sparse
from scipy.io import mmread
from full104_production_expression_firewall import assert_fit_only_nph_assets

SEED="FULL104_EXPRESSION_INTERFACE_V1_20260826";ROWS_PER_OPERATOR=2;ADDRESS_N=41238
ROOT=Path(__file__).resolve().parents[2];AUTH=Path(r"D:\Jepa project-stage81a3r-20260814\results\v4")
META=ROOT/"outputs/full104_v014_20260826/01_full104_metadata_adapter"
ENVELOPE=ROOT/"outputs/full104_v014_20260826/_staging_full104_expression_interface_v8_retry2"
PACKAGE=ENVELOPE/"FULL104_EXPRESSION_INTERFACE_V8"
OUT=PACKAGE/"interface_check"
PATCH_LOG=ROOT/"outputs/full104_v014_20260826/EXPRESSION_INTERFACE_EXECUTION_PATCH_LOG.md"

def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(8<<20),b""):h.update(b)
 return h.hexdigest()
def score(r):return hashlib.sha256("|".join([SEED,r["matrix_id"],r["row_locator"],r["canonical_cell_id"]]).encode()).hexdigest()
def decode(v):return np.asarray([x.decode() if isinstance(x,(bytes,np.bytes_)) else str(x) for x in v],object)
def hvec(g,k):
 n=g[k]
 if isinstance(n,h5py.Group) and "codes" in n:
  c=np.asarray(n["codes"]);a=decode(np.asarray(n["categories"]));return np.asarray([a[int(x)] if int(x)>=0 else "" for x in c],object)
 return decode(np.asarray(n))
def hvalue(g,k,i):
 n=g[k]
 if isinstance(n,h5py.Group) and "codes" in n:
  code=int(n["codes"][i]);v=n["categories"][code] if code>=0 else ""
 else:v=n[i]
 return v.decode() if isinstance(v,(bytes,np.bytes_)) else str(v)
def write_json(p,x):p.write_text(json.dumps(x,indent=2)+"\n",encoding="utf-8")

def authorities():
 return {
  "metadata_status":META/"FULL104_METADATA_SCOPE_STATUS.json","metadata_manifest":META/"FULL104_ADAPTER_SHA256_MANIFEST.csv",
  "reader_split":ROOT/"exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv",
  "assets":ROOT/"results/v4/stage81a2_canonical_asset_registry.csv","semantics":ROOT/"results/v4/stage81a2_matrix_semantics_contract.csv",
  "address_registry":ROOT/"results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv",
  "provenance":ROOT/"results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz",
  "operator_state":ROOT/"exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz",
  "collision":AUTH/"stage81a3r_expression_materialization_collision_ledger.csv.gz",
  "collision_supplement":AUTH/"stage81a3r_scalar_mapping_unregistered_collisions.csv",
  "hvs_hashes":ROOT/"results/v4/stage81a1d_living_human_download_hashes.csv","sea_hashes":ROOT/"results/v4/pre_stage81a2_dataset_manifest.csv",
  "nph_exactness":ROOT/"data/processed/v4/stage81a2r/nph52_physical_split/nph52_physical_split_exactness_manifest.csv",
  "nph_fit_manifest":PACKAGE/"NPH_READER_FIT_DERIVATIVE_MANIFEST.csv",
  "nph_fit_status":PACKAGE/"NPH_READER_FIT_FRESH_PROCESS_STATUS.json",
  "original_nph_denylist":PACKAGE/"ORIGINAL_NPH_MIXED_ASSET_DENYLIST.csv",
  "nph_disposition":ROOT/"data/processed/v4/stage81a3/stage81a3_nph_disposition_detail.csv.gz",
  "execution_patch_log":PATCH_LOG,
 }

def write_original_nph_denylist():
 exact=pd.read_csv(ROOT/"data/processed/v4/stage81a2r/nph52_physical_split/nph52_physical_split_exactness_manifest.csv",dtype=str)
 train=exact[exact.partition.eq("TRAIN")].copy()
 if len(train)!=7 or not train.exact_lossless_subset_pass.str.lower().eq("true").all():raise RuntimeError("original NPH exactness authority mismatch")
 rows=[];prefix="/mnt/d/Jepa project/"
 for r in train.itertuples(index=False):
  raw=str(r.derivative_path).replace("\\","/")
  if not raw.startswith(prefix):raise RuntimeError("original NPH path outside canonical prefix")
  path=(ROOT/raw[len(prefix):]).resolve()
  rows.append({"canonical_original_path":str(path),"original_sha256":str(r.derivative_sha256).lower()})
 pd.DataFrame(rows).sort_values("canonical_original_path").to_csv(PACKAGE/"ORIGINAL_NPH_MIXED_ASSET_DENYLIST.csv",index=False,lineterminator="\n")

def validate_metadata_manifest():
 rows=pd.read_csv(META/"FULL104_ADAPTER_SHA256_MANIFEST.csv")
 for r in rows.itertuples(index=False):
  p=(ROOT/str(r.path)) if str(r.path).startswith("scripts/") else META/str(r.path)
  if not p.is_file() or p.stat().st_size!=int(r.bytes) or sha(p)!=str(r.sha256):raise RuntimeError("metadata manifest mismatch "+str(r.path))
 status=json.loads((META/"FULL104_METADATA_SCOPE_STATUS.json").read_text())
 if status["status"]!="PASS_FULL104_PRODUCTION_SCOPE_RECONCILED" or status["phase2_started"]:raise RuntimeError("metadata scope gate unavailable")

def select_lineage_rows():
 selected=[]
 index=pd.read_csv(META/"FULL104_ROW_LINEAGE.csv").sort_values("operator_index")
 if len(index)!=42 or set(index.operator_index)!=set(range(42)):raise RuntimeError("operator shard index mismatch")
 for item in index.itertuples(index=False):
  best=[]
  with gzip.open(META/str(item.path),"rt",encoding="utf-8",newline="") as f:
   for row in csv.DictReader(f):
    if row["reader_partition"]!="reader_fit" or row["foundation_split"]!="foundation/train":raise RuntimeError("firewall row mismatch")
    key=score(row);heapq.heappush(best,(-int(key,16),row,key))
    if len(best)>ROWS_PER_OPERATOR:heapq.heappop(best)
  chosen=sorted([(k,r) for _,r,k in best],key=lambda x:(x[0],x[1]["row_locator"]))
  if len(chosen)!=ROWS_PER_OPERATOR:raise RuntimeError("selection quota failure")
  selected.extend([dict(r,selection_hash=k) for k,r in chosen])
 sel=pd.DataFrame(selected).sort_values(["operator_index","selection_hash"]).reset_index(drop=True);sel.insert(0,"selection_row",np.arange(len(sel)))
 if len(sel)!=84 or sel.operator_index.astype(int).nunique()!=42:raise RuntimeError("selection geometry mismatch")
 return sel

def freeze():
 if OUT.exists():raise FileExistsError(OUT)
 OUT.mkdir(parents=True);write_original_nph_denylist();validate_metadata_manifest();auth=authorities()
 if any(not p.is_file() for p in auth.values()):raise FileNotFoundError([str(p) for p in auth.values() if not p.is_file()])
 sel=select_lineage_rows()
 sel_path=OUT/"FULL104_EXPRESSION_INTERFACE_SELECTION.csv";sel.to_csv(sel_path,index=False,lineterminator="\n")

 assets=pd.read_csv(auth["assets"],dtype=str).set_index("dataset_id");hvs=pd.read_csv(auth["hvs_hashes"],dtype=str);sea=pd.read_csv(auth["sea_hashes"],dtype=str);nph=pd.read_csv(auth["nph_fit_manifest"],dtype=str)
 pins=[]
 for matrix_id in sorted(sel.matrix_id.unique()):
  source=str(sel.loc[sel.matrix_id.eq(matrix_id),"source"].iloc[0])
  if source in {"HVS","SEA_AD"}:
   a=assets.loc[matrix_id];rel=Path(str(a.matrix_path_or_object)).as_posix();p=ROOT/rel
   reg=hvs[hvs.source_path.eq(rel)] if source=="HVS" else sea[sea.source_path.eq(rel)]
   if len(reg)!=1:raise RuntimeError("missing unique registered asset identity "+matrix_id)
   registered_sha=str(reg.iloc[0]["sha256" if source=="HVS" else "source_hash"]);registered_bytes=int(reg.iloc[0].size_bytes)
   if not p.is_file() or p.stat().st_size!=registered_bytes:raise RuntimeError("source asset size mismatch "+matrix_id)
   pins.append({"source":source,"matrix_id":matrix_id,"asset_root":"project","expression_path":rel,"registered_bytes":registered_bytes,"registered_sha256":registered_sha,"pin_mode":"authenticated_registry_identity_plus_live_size","registry":auth["hvs_hashes" if source=="HVS" else "sea_hashes"].relative_to(ROOT).as_posix()})
  else:
   reg=nph[nph.matrix_id.eq(matrix_id)]
   if len(reg)!=1 or str(reg.iloc[0].reader_partition)!="reader_fit" or str(reg.iloc[0].foundation_split)!="foundation/train":raise RuntimeError("NPH fit-only identity mismatch")
   rel=Path(str(reg.iloc[0].derivative_relative_path)).as_posix();p=PACKAGE/rel
   if not p.is_file() or p.stat().st_size!=int(reg.iloc[0].derivative_size_bytes):raise RuntimeError("NPH fit-only derivative size mismatch")
   pins.append({"source":source,"matrix_id":matrix_id,"asset_root":"package","expression_path":rel,"registered_bytes":int(reg.iloc[0].derivative_size_bytes),"registered_sha256":str(reg.iloc[0].derivative_sha256),"pin_mode":"fresh_verified_reader_fit_only_derivative_sha256","registry":auth["nph_fit_manifest"].relative_to(ROOT).as_posix()})
 pins_path=OUT/"FULL104_EXPRESSION_ASSET_PINS.csv";pd.DataFrame(pins).to_csv(pins_path,index=False,lineterminator="\n")
 code=[ROOT/"scripts/v4/full104_expression_interface_preflight.py",ROOT/"scripts/v4/full104_expression_interface_nph_v8.R",ROOT/"scripts/v4/full104_expression_interface_consumer.py",ROOT/"scripts/v4/full104_production_expression_firewall.py",ROOT/"scripts/v4/build_nph_reader_fit_quarantine.R",ROOT/"scripts/v4/verify_nph_reader_fit_quarantine.R"]
 contract={"schema":"full104-expression-interface-freeze-v8","status":"FROZEN_BEFORE_EXPRESSION","selection":{"algorithm":"two minimum SHA256 rows per operator, recomputed from pinned lineage at execution","seed":SEED,"rows_per_operator":2,"rows":84,"operators":42,"path":sel_path.name,"sha256":sha(sel_path)},"asset_pins":{"path":pins_path.name,"sha256":sha(pins_path),"HVS_SEA_mode":"registered SHA256 verified against live bytes before H5 open","NPH_mode":"fresh-process-verified physical reader_fit-only derivative; original path/hash denied"},"payload":{"addresses":41238,"teacher_inputs":["normalized_values","observation_states"],"identity_sidecar_fields":["selection_row","matrix_id","source_row","canonical_cell_id","donor_id","retrieval_backend"],"identity_sidecar_is_teacher_input":False,"normalization":"log1p(raw_count*10000/full_source_library) exactly once","measured_zero":"state=MEASURED_SCALAR and numeric value=0 remains evidence","non_scalar_numeric_value":"must equal 0"},"prohibited":["original mixed NPH expression","D selection","parameter selection","reader_validation expression","reader_oracle expression","DEV expression","SEALED expression","pathology","biological endpoint use"],"authorities":{k:{"path":str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),"sha256":sha(p)} for k,p in auth.items()},"code":{str(p.relative_to(ROOT)):{"sha256":sha(p)} for p in code},"expression_read":False,"phase2_started":False}
 write_json(OUT/"FULL104_EXPRESSION_INTERFACE_FREEZE.json",contract)
 manifest=[]
 for p in [sel_path,pins_path,OUT/"FULL104_EXPRESSION_INTERFACE_FREEZE.json",*code]:
  manifest.append({"path":str(p.relative_to(ROOT)),"bytes":p.stat().st_size,"sha256":sha(p)})
 manifest_path=OUT/"FULL104_EXPRESSION_INTERFACE_FREEZE_MANIFEST.csv";pd.DataFrame(manifest).to_csv(manifest_path,index=False,lineterminator="\n")
 (OUT/"FULL104_EXPRESSION_INTERFACE_FREEZE_MANIFEST_SHA256.txt").write_text(sha(manifest_path)+"\n",encoding="ascii")
 print(json.dumps({"status":contract["status"],"rows":84,"operators":42,"selection_sha256":sha(sel_path)},indent=2))

def mapping_for(matrix_id,source,prov,coll,supp):
 source_key="HVS_COMMON" if source=="HVS" else "SEA_AD_COMMON"
 m=prov[prov.source_dataset_id.eq(source_key)][["source_feature_index","molecular_address_index"]].copy();blocked=set(coll.loc[coll.matrix_id.astype(str).eq(matrix_id),"source_feature_index"].astype(int))
 for s in supp.loc[supp.matrix_id.astype(str).eq(matrix_id),"source_feature_indices"].astype(str):blocked.update(map(int,s.split("|")))
 m=m[~m.source_feature_index.astype(int).isin(blocked)]
 if m.source_feature_index.duplicated().any() or m.molecular_address_index.duplicated().any():raise RuntimeError("noninjective mapping "+matrix_id)
 return dict(zip(m.source_feature_index.astype(int),m.molecular_address_index.astype(int)))

def execute():
 freeze_path=OUT/"FULL104_EXPRESSION_INTERFACE_FREEZE.json";contract=json.loads(freeze_path.read_text());auth=authorities()
 manifest_path=OUT/"FULL104_EXPRESSION_INTERFACE_FREEZE_MANIFEST.csv";anchor=(OUT/"FULL104_EXPRESSION_INTERFACE_FREEZE_MANIFEST_SHA256.txt").read_text().strip()
 if sha(manifest_path)!=anchor:raise RuntimeError("external freeze manifest anchor mismatch")
 for r in pd.read_csv(manifest_path).itertuples(index=False):
  p=ROOT/str(r.path)
  if not p.is_file() or p.stat().st_size!=int(r.bytes) or sha(p)!=str(r.sha256):raise RuntimeError("freeze manifest mismatch "+str(r.path))
 validate_metadata_manifest()
 if contract["status"]!="FROZEN_BEFORE_EXPRESSION" or contract["expression_read"] or contract["phase2_started"]:raise RuntimeError("invalid freeze state")
 for k,v in contract["authorities"].items():
  p=auth[k]
  if sha(p)!=v["sha256"]:raise RuntimeError("authority hash drift "+k)
 for raw,v in contract["code"].items():
  if sha(ROOT/raw)!=v["sha256"]:raise RuntimeError("preflight code drift "+raw)
 sel_path=OUT/contract["selection"]["path"]
 if sha(sel_path)!=contract["selection"]["sha256"]:raise RuntimeError("selection drift")
 sel=pd.read_csv(sel_path,dtype=str)
 if len(sel)!=84 or set(sel.reader_partition)!={"reader_fit"} or set(sel.foundation_split)!={"foundation/train"} or set(sel.eligibility_status)!={"LAWFUL_READER_FIT"}:raise RuntimeError("selection firewall/geometry mismatch")
 counts=sel.operator_index.astype(int).value_counts().to_dict()
 if counts!={i:2 for i in range(42)}:raise RuntimeError("selection operator quota mismatch")
 reader=pd.read_csv(auth["reader_split"],dtype=str);fit=set(reader.loc[reader.reader_partition.eq("reader_fit"),"donor_id"])
 if set(sel.donor_id)-fit:raise RuntimeError("selection contains non-fit donor")
 expected=select_lineage_rows().astype(str);observed=sel.astype(str)
 if expected.columns.tolist()!=observed.columns.tolist() or not expected.equals(observed):raise RuntimeError("selection is not deterministic lineage minimum")
 sel["operator_index"]=sel.operator_index.astype(int);sel["source_row"]=sel.source_row.astype(int);sel["selection_row"]=sel.selection_row.astype(int)
 pins=pd.read_csv(OUT/contract["asset_pins"]["path"],dtype=str)
 if sha(OUT/contract["asset_pins"]["path"])!=contract["asset_pins"]["sha256"]:raise RuntimeError("asset pins drift")
 if len(pins)!=42 or set(pins.matrix_id)!=set(sel.matrix_id) or sel.groupby("operator_index").matrix_id.nunique().to_dict()!={i:1 for i in range(42)}:raise RuntimeError("all-42 operator asset reachability mismatch")
 def asset_path(row):return (ROOT/str(row.expression_path)) if str(row.asset_root)=="project" else (PACKAGE/str(row.expression_path))
 if set(pins.source)!={"HVS","SEA_AD","NPH52"} or any(not asset_path(p).is_file() for p in pins.itertuples(index=False)):raise RuntimeError("source asset path reachability mismatch")
 nph_pins=pins[pins.source.eq("NPH52")]
 assert_fit_only_nph_assets([asset_path(p) for p in nph_pins.itertuples(index=False)],nph_pins.registered_sha256.tolist(),auth["original_nph_denylist"],PACKAGE)
 rscript=Path(r"C:\Program Files\R\R-4.1.2\bin\Rscript.exe")
 bool_test=OUT/"BOOLEAN_AUTHORITY_SELFTEST.csv"
 subprocess.run([str(rscript),str(ROOT/"scripts/v4/full104_expression_interface_nph_v8.R"),"--selftest",str(bool_test)],check=True)
 bt=pd.read_csv(bool_test,dtype=str)
 if bt.input.tolist()!=["True","TRUE"," true ","False","FALSE"," false "] or bt.parsed.str.lower().tolist()!=["true","true","true","false","false","false"] or set(bt.invalid_rejected.str.lower())!={"true"}:raise RuntimeError("Boolean authority self-test mismatch")
 nph_validation=OUT/"_nph_authority_validation"
 subprocess.run([str(rscript),str(ROOT/"scripts/v4/full104_expression_interface_nph_v8.R"),str(ROOT),str(PACKAGE),str(sel_path),str(auth["provenance"]),str(AUTH),str(nph_validation),"validate"],check=True)
 validation=pd.read_csv(nph_validation/"NPH_FIT_ONLY_AUTHORITY_VALIDATION.csv",dtype=str)
 selected_nph=set(sel.loc[sel.source.eq("NPH52"),"matrix_id"])
 if set(validation.matrix_id)!=selected_nph or len(validation)!=len(selected_nph) or set(validation.reader_partition)!={"reader_fit"} or set(validation.original_path_and_hash_denied.str.lower())!={"true"}:raise RuntimeError("NPH fit-only authority/path validation mismatch")
 for p in pins.itertuples(index=False):
  path=asset_path(p)
  if path.stat().st_size!=int(p.registered_bytes):raise RuntimeError("asset size drift "+p.matrix_id)
  if sha(path)!=p.registered_sha256:raise RuntimeError("live expression asset hash drift "+p.matrix_id)
 assets=pd.read_csv(auth["assets"],dtype=str).set_index("dataset_id")
 identity_rows=[]
 for matrix_id,g in sel[~sel.source.eq("NPH52")].groupby("matrix_id",sort=True):
  source=str(g.source.iloc[0]);a=assets.loc[matrix_id]
  with h5py.File(ROOT/str(a.matrix_path_or_object),"r") as h:
   donor_key="donor_id" if source=="HVS" else "Donor ID"
   for r in g.itertuples(index=False):
    sr=int(r.source_row);cell=hvalue(h["obs"],"exp_component_name",sr);donor=hvalue(h["obs"],donor_key,sr)
    if cell!=str(r.canonical_cell_id) or donor!=str(r.donor_id):raise RuntimeError("metadata-only H5 row locator identity mismatch")
    identity_rows.append({"selection_row":int(r.selection_row),"matrix_id":matrix_id,"source_row":sr,"canonical_cell_id":cell,"donor_id":donor,"expression_matrix_accessed":False})
 pd.DataFrame(identity_rows).to_csv(OUT/"H5_ROW_IDENTITY_VALIDATION.csv",index=False,lineterminator="\n")
 states_np=np.load(auth["operator_state"],allow_pickle=False);states_by_op=states_np["states"].astype(np.uint8)
 if states_by_op.shape!=(42,41238) or states_np["molecular_address_index"].tolist()!=list(range(41238)):raise RuntimeError("state/address geometry mismatch")
 if states_np["state_names"].astype(str).tolist()!=["STRUCTURALLY_UNMEASURED","MEASURED_SCALAR","MEASURED_COLLISION_UNRESOLVED"]:raise RuntimeError("state name/code ordering mismatch")
 registry=pd.read_csv(auth["address_registry"],low_memory=False)
 if len(registry)!=41238 or registry.molecular_address_index.astype(int).tolist()!=list(range(41238)):raise RuntimeError("address registry ordering mismatch")
 sem=pd.read_csv(auth["semantics"],dtype=str).set_index("dataset_id")
 prov=pd.read_csv(auth["provenance"],low_memory=False);coll=pd.read_csv(auth["collision"],low_memory=False);supp=pd.read_csv(auth["collision_supplement"])
 disposition=pd.read_csv(auth["nph_disposition"],dtype=str);disposition["source_row"]=disposition.groupby("source_object",sort=False).cumcount()
 for r in sel[sel.source.eq("NPH52")].itertuples(index=False):
  obj=str(r.matrix_id).removeprefix("NPH52::matrix::");hit=disposition[(disposition.source_object.eq(obj))&(disposition.source_row.eq(int(r.source_row)))]
  if len(hit)!=1 or str(hit.iloc[0].source_cell_id)!=str(r.canonical_cell_id) or str(hit.iloc[0].donor_id)!=str(r.donor_id) or str(hit.iloc[0].foundation_eligibility).lower()!="true":raise RuntimeError("NPH source_row identity mismatch")

 def materialize(rep):
  raw=np.zeros((len(sel),ADDRESS_N),np.int32);libs=np.zeros(len(sel),np.float64);identity=[]
  for matrix_id,g in sel[~sel.source.eq("NPH52")].groupby("matrix_id",sort=True):
   source=str(g.source.iloc[0]);a=assets.loc[matrix_id];c=sem.loc[matrix_id]
   if str(c.matrix_semantics)!="raw_integer_counts" or str(c.normalization_already_applied).lower()!="false" or str(c.log_transform_already_applied).lower()!="false":raise RuntimeError("matrix semantics mismatch")
   m=mapping_for(matrix_id,source,prov,coll,supp)
   op=int(g.operator_index.iloc[0]);targets=np.fromiter(m.values(),dtype=np.int64)
   if len(targets) and not np.all(states_by_op[op,targets]==1):raise RuntimeError("retained H5 mapping target is not MEASURED_SCALAR")
   with h5py.File(ROOT/str(a.matrix_path_or_object),"r") as h:
    donor_key="donor_id" if source=="HVS" else "Donor ID";node=h[str(c.matrix_slot)]
    for r in g.itertuples(index=False):
     sr=int(r.source_row);dest=int(r.selection_row)
     if hvalue(h["obs"],"exp_component_name",sr)!=str(r.canonical_cell_id) or hvalue(h["obs"],donor_key,sr)!=str(r.donor_id):raise RuntimeError("H5 row identity mismatch")
     a0,b0=int(node["indptr"][sr]),int(node["indptr"][sr+1]);idx=np.asarray(node["indices"][a0:b0],np.int64);x=np.asarray(node["data"][a0:b0])
     if np.any(x<0) or not np.allclose(x,np.rint(x)):raise RuntimeError("H5 payload not raw integer counts")
     libs[dest]=float(x.sum())
     for j,v in zip(idx,x):
      target=m.get(int(j))
      if target is not None and v:raw[dest,target]=int(round(float(v)))
     identity.append((dest,matrix_id,sr,str(r.canonical_cell_id),str(r.donor_id),"h5ad_obs_and_raw_X"))
  nph_out=OUT/f"_nph_replay_{rep}";nph_out.mkdir(exist_ok=False)
  subprocess.run([str(rscript),str(ROOT/"scripts/v4/full104_expression_interface_nph_v8.R"),str(ROOT),str(PACKAGE),str(sel_path),str(auth["provenance"]),str(AUTH),str(nph_out)],check=True)
  for op in sorted(sel.loc[sel.source.eq("NPH52"),"operator_index"].unique()):
   g=sel[sel.operator_index.eq(op)].sort_values("selection_row");mat=mmread(nph_out/f"op{op:02d}.mtx").tocsr();meta=pd.read_csv(nph_out/f"op{op:02d}.meta.csv")
   obj=str(g.matrix_id.iloc[0]).removeprefix("NPH52::matrix::");source_key="NPH52::"+obj
   m=prov[prov.source_dataset_id.eq(source_key)][["source_feature_index","molecular_address_index"]].copy();blocked=set(coll.loc[coll.matrix_id.astype(str).eq(str(g.matrix_id.iloc[0])),"source_feature_index"].astype(int))
   for s in supp.loc[supp.matrix_id.astype(str).eq(str(g.matrix_id.iloc[0])),"source_feature_indices"].astype(str):blocked.update(map(int,s.split("|")))
   targets=m.loc[~m.source_feature_index.astype(int).isin(blocked),"molecular_address_index"].astype(int).to_numpy()
   if len(targets) and not np.all(states_by_op[int(op),targets]==1):raise RuntimeError("retained NPH mapping target is not MEASURED_SCALAR")
   if meta.selection_row.astype(int).tolist()!=g.selection_row.tolist() or meta.canonical_cell_id.astype(str).tolist()!=g.canonical_cell_id.astype(str).tolist():raise RuntimeError("NPH output identity/order mismatch")
   for local,r in enumerate(g.itertuples(index=False)):
    dest=int(r.selection_row);raw[dest]=mat.getrow(local).toarray()[0].astype(np.int32);libs[dest]=float(meta.iloc[local].source_library);identity.append((dest,r.matrix_id,int(r.source_row),r.canonical_cell_id,r.donor_id,"nph_fresh_verified_reader_fit_only_derivative"))
  states=states_by_op[sel.sort_values("selection_row").operator_index.to_numpy()]
  if np.any(raw[states!=1]!=0):raise RuntimeError("numeric payload outside MEASURED_SCALAR")
  values=np.log1p(raw.astype(np.float64)*(10000/np.maximum(libs,1))[:,None]).astype(np.float32)
  return raw,values,states,libs,sorted(identity)
 first=materialize("A");second=materialize("B")
 for name,a,b in zip(["raw","values","states","libraries","identity"],first,second):
  same=np.array_equal(a,b) if name!="identity" else a==b
  if not same:raise RuntimeError("deterministic replay mismatch "+name)
 raw,values,states,libs,identity=first
 if not np.isfinite(values).all() or np.any(values[states!=1]!=0):raise RuntimeError("normalized payload semantic violation")
 measured_zero=int(np.count_nonzero((states==1)&(raw==0)));struct=int(np.count_nonzero(states==0));collision=int(np.count_nonzero(states==2))
 if measured_zero<=0 or struct<=0 or collision<=0:raise RuntimeError("three-state/zero coverage missing")
 model_dir=PACKAGE/"model_inputs";audit_dir=PACKAGE/"audit_identity";model_dir.mkdir(exist_ok=False);audit_dir.mkdir(exist_ok=False)
 payload=model_dir/"FULL104_EXPRESSION_INTERFACE_PAYLOAD.npz";np.savez_compressed(payload,normalized_values=values,observation_states=states)
 side=pd.DataFrame(identity,columns=["selection_row","matrix_id","source_row","canonical_cell_id","donor_id","retrieval_backend"]).sort_values("selection_row");side.to_csv(audit_dir/"FULL104_EXPRESSION_INTERFACE_IDENTITY.csv",index=False,lineterminator="\n")
 report={"schema":"full104-expression-interface-preflight-v8","status":"PASS_FULL104_EXPRESSION_INTERFACE_AWAITING_INDEPENDENT_REVIEWS","cells":len(sel),"operators":42,"addresses":41238,"deterministic_replay_exact":True,"row_identity_exact":True,"address_order_exact":True,"normalization":"log1p(raw_count*10000/full_source_library) exactly once","raw_nonnegative_integer":True,"numeric_only_measured_scalar":True,"measured_zero_retained":True,"measured_zero_slots":measured_zero,"structurally_unmeasured_slots":struct,"collision_unresolved_slots":collision,"teacher_payload_fields":["normalized_values","observation_states"],"unrestricted_covariates_in_teacher_payload":False,"source_asset_pins_sha256":sha(OUT/contract["asset_pins"]["path"]),"selection_sha256":sha(sel_path),"payload_sha256":sha(payload),"expression_read":True,"reader_fit_only":True,"original_mixed_nph_opened_in_v8_process":False,"protected_expression_opened_in_v8_process":False,"quarantine_splitter_transient_protected_deserialization":True,"quarantine_splitter_protected_expression_used_for_derived_quantity":False,"parameter_selected":False,"phase2_started":False}
 write_json(OUT/"FULL104_EXPRESSION_INTERFACE_PREFLIGHT.json",report);print(json.dumps(report,indent=2))

def main():
 ap=argparse.ArgumentParser();ap.add_argument("mode",choices=["freeze","execute"]);a=ap.parse_args();freeze() if a.mode=="freeze" else execute()
if __name__=="__main__":main()
