"""Executable metadata-first F1 population firewall. Never opens expression values."""
from __future__ import annotations
import argparse,csv,gzip,hashlib,json,os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901"
INDEX=ROOT/"outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_ROW_LINEAGE.csv"
SPLIT=ROOT/"exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv"
ROLES=ROOT/"exports/master_donor_dataset_role_registry_20260825/MASTER_DONOR_DATASET_ROLE_TABLE.csv"
CELL=ROOT/"outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_CELL_DONOR_OPERATOR_AUTHORITY.json"
NULL=ROOT/"outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_PRIMARY_MAP.csv"
V8=ROOT/"outputs/full104_v014_20260826/full104_expression_interface_v8_verified/FULL104_EXPRESSION_INTERFACE_V8"
ALLOW=V8/"NPH_READER_FIT_DERIVATIVE_MANIFEST.csv"; DENY=V8/"ORIGINAL_NPH_MIXED_ASSET_DENYLIST.csv"
NAMESPACE=ROOT/"exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv"

def read(p):
 with p.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def b(v):return str(v).strip().lower() in ("true","1","yes")
def csha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

class Firewall:
 def __init__(self):
  self.read_count=0
  self.cells=json.loads(CELL.read_text())["selected_rows"]
  self.null=read(NULL); self.null_by={x["recipient_canonical_cell_id"]:x for x in self.null}
  self.targets={x["row_locator"] for x in self.cells}|{x["source_row_locator"] for x in self.null}
  self.split={x["donor_id"]:x["reader_partition"] for x in read(SPLIT)}
  self.roles=read(ROLES); self.lineage=self._lineage()
  self.allow={int(x["operator_index"]):x for x in read(ALLOW)}
  self.namespace_ids=[x["molecular_address_id"] for x in read(NAMESPACE)]
  self.deny={(os.path.normcase(os.path.abspath(x["canonical_original_path"])),x["original_sha256"].lower()) for x in read(DENY)}
  if set(self.allow)!=set(range(35,42)) or len(self.deny)!=7:raise ValueError("NPH authorities")
  for a in self.allow.values():
   p=(V8/a["derivative_relative_path"]).resolve()
   if not p.is_file() or p.stat().st_size!=int(a["derivative_size_bytes"]) or sha(p)!=a["derivative_sha256"].lower():raise ValueError("live NPH derivative hash")
 def _lineage(self):
  found={}
  for ix in read(INDEX):
   p=INDEX.parent/ix["path"]
   if sha(p)!=ix["sha256"]:raise ValueError("lineage shard hash")
   with gzip.open(p,"rt",encoding="utf-8",newline="") as f:
    for r in csv.DictReader(f):
     if r["row_locator"] in self.targets:
      if r["row_locator"] in found:raise ValueError("duplicate locator")
      found[r["row_locator"]]=r
  if set(found)!=self.targets:raise ValueError("missing lineage target")
  return found
 def _role_ok(self,r):
  hits=[x for x in self.roles if x["canonical_person_id"]==r["canonical_donor_id"] and x["matrix_id"]==r["matrix_id"]]
  return any(x["authority_status"]=="AUTHORITATIVE" and x["reader_partition"]=="reader_fit" and x["split_domain"]=="foundation" and x["split"]=="train" and b(x["foundation_eligible_asset"]) and not b(x["pathology_bearing_asset"]) and not b(x["pathology_used_for_foundation_split"]) for x in hits)
 def _row(self,locator,expected):
  r=self.lineage.get(locator)
  if r is None:raise ValueError("unknown locator")
  checks=(r["canonical_cell_id"]==expected["cell"],r["canonical_donor_id"]==expected["donor"],r["source"]==expected["source"],int(r["operator_index"])==int(expected["operator"]),r["reader_partition"]=="reader_fit",r["foundation_split"]=="foundation/train",r["eligibility_status"]=="LAWFUL_READER_FIT",self.split.get(r["donor_id"])=="reader_fit",self._role_ok(r))
  if not all(checks):raise ValueError("row firewall mismatch")
  return r
 def _asset(self,r,supplied=None):
  op=int(r["operator_index"])
  if r["source"]=="NPH52":
   a=self.allow.get(op)
   if a is None or a["matrix_id"]!=r["matrix_id"] or a["reader_partition"]!="reader_fit" or a["foundation_split"]!="foundation/train":raise ValueError("NPH allow mismatch")
   path=(V8/a["derivative_relative_path"]).resolve(); digest=a["derivative_sha256"].lower()
  else:
   hits=[x for x in self.roles if x["canonical_person_id"]==r["canonical_donor_id"] and x["matrix_id"]==r["matrix_id"] and x["reader_partition"]=="reader_fit" and x["split"]=="train"]
   if not hits:raise ValueError("asset registry miss")
   choices={(x["local_asset_path"],x["registered_asset_sha256"].lower()) for x in hits}
   if len(choices)!=1:raise ValueError("ambiguous asset authority")
   rel,digest=next(iter(choices));path=(ROOT/rel).resolve()
   if not path.is_file():raise ValueError("asset missing")
  if (os.path.normcase(str(path)),digest) in self.deny:raise ValueError("denied original NPH")
  if supplied is not None and (os.path.normcase(os.path.abspath(supplied[0])),supplied[1].lower())!=(os.path.normcase(str(path)),digest):raise ValueError("unknown/wrong asset")
  return str(path),digest
 def authorize_all(self,cells=None,nullrows=None,asset_override=None):
  cells=self.cells if cells is None else cells; nullrows=self.null if nullrows is None else nullrows
  nm={x["recipient_canonical_cell_id"]:x for x in nullrows}
  if len(cells)!=2781 or len(nm)!=2781:raise ValueError("population incomplete")
  desc=[]
  for x in cells:
   if b(x.get("pathology_bearing_asset",False)) or b(x.get("external",False)):raise ValueError("forbidden role")
   if x.get("reader_partition")!="reader_fit" or x.get("foundation_split")!="foundation/train":raise ValueError("supplied split mismatch")
   n=nm.get(x["canonical_cell_id"])
   if n is None or n["recipient_row_locator"]!=x["row_locator"]:raise ValueError("null map identity")
   rr=self._row(x["row_locator"],{"cell":x["canonical_cell_id"],"donor":x["canonical_donor_id"],"source":x["source"],"operator":x["operator_index"]})
   if x.get("row_lineage_sha256") and x["row_lineage_sha256"]!=csha(rr):raise ValueError("row lineage hash")
   sr=self._row(n["source_row_locator"],{"cell":n["source_canonical_cell_id"],"donor":n["source_canonical_donor_id"],"source":n["source_source"],"operator":n["operator_index"]})
   if rr["source"]!=sr["source"] or rr["operator_index"]!=sr["operator_index"] or rr["canonical_donor_id"]==sr["canonical_donor_id"] or rr["canonical_cell_id"]==sr["canonical_cell_id"]:raise ValueError("null causal mismatch")
   ra=self._asset(rr,asset_override.get(rr["row_locator"]) if asset_override else None);sa=self._asset(sr,asset_override.get(sr["row_locator"]) if asset_override else None)
   desc.append({"recipient":rr["row_locator"],"recipient_cell":rr["canonical_cell_id"],"source":rr["source"],"operator":int(rr["operator_index"]),"recipient_asset":ra,"null":sr["row_locator"],"null_cell":sr["canonical_cell_id"],"null_asset":sa,"recipient_lineage_sha256":csha(rr),"null_lineage_sha256":csha(sr)})
  return desc
 def callback(self,desc,response=None):
  # Called only after authorize_all has returned the complete population.
  self.read_count+=1
  request_sha=csha(desc)
  if response is None:return {"request_sha256":request_sha,"rows":len(desc),"namespace_columns":41238}
  if response.get("request_sha256")!=request_sha or response.get("ordered_recipient_locators")!=[x["recipient"] for x in desc] or response.get("ordered_null_locators")!=[x["null"] for x in desc] or response.get("shape")!=[len(desc)*2,41238] or response.get("dtype") not in ("float32","float64") or response.get("namespace_sha256")!="595fd8bc860b13ce9ec2a957b0f3d92f850effcb51ae6e2f06b8c5d25d7bd53f" or response.get("column_address_ids")!=self.namespace_ids or not response.get("reader_implementation_sha256"):raise ValueError("callback response binding")
  return True

def main():
 fw=Firewall();desc=fw.authorize_all();baseline_reads=fw.read_count
 attacks=[]
 def attack(name,mut):
  before=fw.read_count
  try:mut();rejected=False
  except ValueError:rejected=True
  attacks.append({"attack":name,"rejected_before_callback":rejected and fw.read_count==before,"expression_read_count":fw.read_count-before})
 cells=fw.cells;null=fw.null
 for field,value,name in (("reader_partition","reader_validation","reader_validation"),("reader_partition","reader_oracle","reader_oracle"),("foundation_split","DEV","DEV"),("foundation_split","SEALED","SEALED"),("source","external","external"),("canonical_cell_id","WRONG","wrong_cell"),("operator_index",99,"wrong_operator")):
  def m(field=field,value=value):
   cc=[dict(x) for x in cells];cc[0][field]=value;fw.authorize_all(cc,null)
  attack(name,m)
 for field,value,name in (("canonical_donor_id","NPH52::human_NPH_1025","relabeled_protected_donor"),("pathology_bearing_asset",True,"pathology"),("row_lineage_sha256","0"*64,"wrong_lineage_hash")):
  def m2(field=field,value=value):
   cc=[dict(x) for x in cells];cc[0][field]=value;fw.authorize_all(cc,null)
  attack(name,m2)
 def same_donor():
  nn=[dict(x) for x in null];nn[0]["source_canonical_donor_id"]=nn[0]["recipient_canonical_donor_id"];fw.authorize_all(cells,nn)
 attack("same_donor_null",same_donor)
 def wrong_map():
  nn=[dict(x) for x in null];nn[0]["source_row_locator"]=nn[1]["source_row_locator"];fw.authorize_all(cells,nn)
 attack("wrong_null_map",wrong_map)
 nph=next(x for x in cells if x["source"]=="NPH52");den=next(iter(fw.deny))
 attack("denied_original_nph",lambda:fw.authorize_all(cells,null,{nph["row_locator"]:den}))
 attack("unknown_nph_asset",lambda:fw.authorize_all(cells,null,{nph["row_locator"]:("X:/unknown.qs","0"*64)}))
 good=fw.callback(desc);response={"request_sha256":good["request_sha256"],"ordered_recipient_locators":[x["recipient"] for x in desc],"ordered_null_locators":[x["null"] for x in desc],"shape":[5562,41238],"dtype":"float32","namespace_sha256":"595fd8bc860b13ce9ec2a957b0f3d92f850effcb51ae6e2f06b8c5d25d7bd53f","column_address_ids":fw.namespace_ids,"reader_implementation_sha256":"metadata-only-fixture"};response_ok=fw.callback(desc,response)
 bad=dict(response);bad["ordered_recipient_locators"]=bad["ordered_recipient_locators"][::-1]
 try:fw.callback(desc,bad);bad_rejected=False
 except ValueError:bad_rejected=True
 badcol=dict(response);badcol["column_address_ids"]=list(response["column_address_ids"]);badcol["column_address_ids"][0],badcol["column_address_ids"][1]=badcol["column_address_ids"][1],badcol["column_address_ids"][0]
 try:fw.callback(desc,badcol);column_swap_rejected=False
 except ValueError:column_swap_rejected=True
 report={"schema":"f1-population-firewall-results-v3","status":"PASS" if all(x["rejected_before_callback"] for x in attacks) and response_ok and bad_rejected and column_swap_rejected else "STOP","recipients_authorized":len(desc),"null_sources_authorized":len(desc),"lineage_rows_independently_resolved":len(fw.lineage),"all_42_operator_shards_hash_verified":True,"nph_live_derivative_hashes_verified":7,"expression_values_opened":False,"baseline_expression_reads_before_authorization":baseline_reads,"sentinel_attacks":attacks,"callback_request_sha256":good["request_sha256"],"callback_response_binding_pass":bool(response_ok),"callback_wrong_order_rejected":bad_rejected,"callback_column_swap_rejected":column_swap_rejected,"future_reader_boundary":"The real F1 reader must be separately hash-pinned and construct column_address_ids from the frozen namespace; this metadata-only turn does not authorize a population executor.","nph_positive_allowlist_sha256":sha(ALLOW),"nph_original_denylist_sha256":sha(DENY),"master_roles_sha256":sha(ROLES),"reader_split_sha256":sha(SPLIT)}
 (OUT/"F1_POPULATION_FIREWALL_RESULTS.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps({"status":report["status"],"lineage":len(fw.lineage),"attacks":len(attacks)}))
 if report["status"]!="PASS":raise SystemExit(2)
if __name__=="__main__":main()
