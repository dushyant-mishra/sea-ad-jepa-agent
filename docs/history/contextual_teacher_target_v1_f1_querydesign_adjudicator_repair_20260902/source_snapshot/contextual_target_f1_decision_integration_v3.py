"""Production integration from validated F1 records; aggregate-only execution is synthetic-only."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ENGINE=HERE/"contextual_target_f1_decision_v1.py";COMPONENT=HERE/"contextual_target_f1_querydesign_decision_v2.py"
ENGINE_SHA="204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34";ASSIGN_SHA="12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617";QID_V2_SHA="15d873871787e0820f63aaead8f27a6f1057541e16640d8492053144a9c69423"
FROZEN_NUISANCE_AUTHORITY_SHA256=None
EVIDENCE=(.2,.4,.6,.8,1.);PROGRAMS=("broad_common","weak_distributed","local","local_core","local_halo","core_halo","sparse_marker_like","innovation_tail")
NUISANCE_FIELDS=("source_indicators","operator_mixture_fractions","recipient_physical_support","recipient_depth","correct_minus_null_visible_depth","correct_minus_null_measured_zero_rate")
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def load(p,name,expected=None):
 if expected and sha(p)!=expected:raise ValueError("STOP_F1_QUERYDESIGN_DECISION_INTEGRATION_UNRESOLVED")
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def validate_population(agg,synthetic=False):
 p=agg.get("population_authority",{});d=agg.get("donors",[])
 expected={"assignment_sha256":ASSIGN_SHA,"assignment_count":44496,"result_count":222480,"cell_count":2781,"donor_count":104,"operator_count":42,"test_fixture":False}
 if len(d)!=104 or len(set(d))!=104 or (p.get("test_fixture") is not True if synthetic else p!=expected):raise ValueError("STOP_F1_QUERYDESIGN_POPULATION_INCOMPLETE integration population")
def nuisance_columns(nuisance,donors,synthetic=False):
 required={"donor_ids","nuisance_authority_sha256",*NUISANCE_FIELDS,"legal"}
 if set(nuisance)!=required or nuisance["donor_ids"]!=donors:raise ValueError("nuisance population binding mismatch")
 if not synthetic and (FROZEN_NUISANCE_AUTHORITY_SHA256 is None or nuisance["nuisance_authority_sha256"]!=FROZEN_NUISANCE_AUTHORITY_SHA256):raise ValueError("STOP_F1_NUISANCE_AUTHORITY_NOT_FROZEN")
 n=len(donors);cols={}
 for field in NUISANCE_FIELDS:
  value=nuisance[field]
  if isinstance(value,dict):
   if not value:raise ValueError("nuisance category empty")
   for name,a in sorted(value.items()):cols[f"{field}__{name}"]=a
  else:cols[field]=value
 if any(not isinstance(v,list) or len(v)!=n for v in cols.values()):raise ValueError("nuisance population binding mismatch")
 return cols
def build_payload(agg,nuisance,synthetic=False):
 validate_population(agg,synthetic);donors=list(agg["donors"]);cols=nuisance_columns(nuisance,donors,synthetic);source=list(agg.get("donor_source",[]))
 if len(source)!=104:return (_ for _ in ()).throw(ValueError("source population binding mismatch"))
 # QID-v2 contract (hash above) prospectively replaced the old Spearman diagnostic with margin + win-minus-half.
 return {"overall_A":agg["overall"]["0.6"]["A"],"program_A":agg["program"]["0.6"],"program_delta":agg["program_direct"]["0.6"],"evidence_A":np.column_stack([agg["overall"][str(e)]["A"] for e in EVIDENCE]).tolist(),"query_margin":agg["overall"]["0.6"]["qid_margin"],"query_structure":agg["overall"]["0.6"]["qid_win_minus_half"],"nuisance_y":agg["overall"]["0.6"]["A"],"source_group":source,"nuisance_columns":cols,"legal":bool(nuisance["legal"])}
def integrate_records(records,nuisance,forward_authority_sha256):
 """The sole production qualification entry; raw records are always revalidated."""
 c=load(COMPONENT,"f1_component_v2");agg=c.aggregate(records,forward_authority_sha256=forward_authority_sha256);payload=build_payload(agg,nuisance,False);component=c.adjudicate(agg);complete=load(ENGINE,"frozen_f1_v1",ENGINE_SHA).qualify(payload);cp=component.get("query_design_component_pass")
 if component.get("component_scope")!="QUERY_DESIGN_COMPONENT_ONLY" or type(cp) is not bool:raise ValueError("component boundary mismatch")
 return {"decision_scope":"COMPLETE_F1_HASH_BOUND_INTEGRATION","query_design_component_pass":cp,"complete_engine_qualified":complete["qualified"],"qualified":bool(cp and complete["qualified"]),"complete_engine_sha256":ENGINE_SHA,"query_identity_v2_contract_sha256":QID_V2_SHA,"complete_engine":complete}
def fixture():
 rng=np.random.default_rng(1701);n=104;donors=[f"d{i:03d}" for i in range(n)];base=np.linspace(.22,.42,n)+rng.normal(0,.015,n);agg={"donors":donors,"donor_source":["HVS"]*35+["NPH52"]*34+["SEA_AD"]*35,"population_authority":{"test_fixture":True,"donor_count":104},"overall":{},"program":{},"program_direct":{},"program_qid_margin":{}}
 for j,e in enumerate(EVIDENCE):
  agg["overall"][str(e)]={"A":(base+.08*j).tolist(),"direct":np.linspace(.02,.08,n).tolist(),"qid_margin":(base*.4).tolist(),"qid_win_minus_half":(base*.3).tolist(),"draw0":(base+.001).tolist(),"draw1":(base-.001).tolist()};agg["program"][str(e)]={p:(base+.01*i+.08*j).tolist() for i,p in enumerate(PROGRAMS)};agg["program_direct"][str(e)]={p:(np.linspace(.02,.08,n)+.002*i).tolist() for i,p in enumerate(PROGRAMS)};agg["program_qid_margin"][str(e)]={p:(base*.4+.001*i).tolist() for i,p in enumerate(PROGRAMS)}
 nuisance={"donor_ids":donors,"nuisance_authority_sha256":"synthetic","source_indicators":{"HVS":[1.]*35+[0.]*69,"NPH52":[0.]*35+[1.]*34+[0.]*35},"operator_mixture_fractions":{"op0":np.tile([0.,1.],52).tolist()},"recipient_physical_support":np.linspace(.2,.8,n).tolist(),"recipient_depth":np.linspace(1,2,n).tolist(),"correct_minus_null_visible_depth":np.linspace(-.2,.2,n).tolist(),"correct_minus_null_measured_zero_rate":np.linspace(-.1,.1,n).tolist(),"legal":True};return agg,nuisance
def test_decision(agg,nuisance):
 c=load(COMPONENT,"f1_component_v2");component=c.adjudicate(agg);complete=load(ENGINE,"frozen_f1_v1",ENGINE_SHA).qualify(build_payload(agg,nuisance,True));return bool(component["query_design_component_pass"] and complete["qualified"])
def adversarial():
 agg,nu=fixture();attacks={}
 def run(name,mutator):
  a=json.loads(json.dumps(agg));n=json.loads(json.dumps(nu))
  try:mutator(a,n);attacks[name]=not test_decision(a,n)
  except (ValueError,KeyError,TypeError):attacks[name]=True
 run("protected_program_primary_failure_veto",lambda a,n:a["program"]["0.6"].__setitem__("local_core",[0.]*104));run("significant_direct_degradation_veto",lambda a,n:a["program_direct"]["0.6"].__setitem__("local_core",(-np.linspace(.2,.4,104)).tolist()));run("evidence_trend_failure_veto",lambda a,n:[a["overall"][str(e)].__setitem__("A",[0.]*104) for e in EVIDENCE]);run("source_confined_veto",lambda a,n:a["overall"]["0.6"].__setitem__("A",[.6]*35+[0.]*69));run("hc3_nuisance_veto",lambda a,n:a["overall"]["0.6"].__setitem__("A",np.linspace(-1,1,104).tolist()));run("cross_source_replication_veto",lambda a,n:a["overall"]["0.6"].__setitem__("A",[.6]*35+[-.2]*34+[.6]*35));run("nonfinite_endpoint_veto",lambda a,n:a["program_direct"]["0.6"]["local"].__setitem__(0,float("nan")));run("missing_program_veto",lambda a,n:a["program"]["0.6"].pop("local"));run("nuisance_nonestimable_veto",lambda a,n:n.__setitem__("operator_mixture_fractions",{f"x{i:03d}":np.eye(104)[:,i].tolist() for i in range(103)}));run("zero_variance_endpoint_veto",lambda a,n:a["overall"]["0.6"].__setitem__("A",[0.]*104));run("complete_payload_subset_rejected",lambda a,n:(a.__setitem__("donors",a["donors"][:-1]),n.__setitem__("donor_ids",n["donor_ids"][:-1])));run("nuisance_donor_omission_rejected",lambda a,n:n.__setitem__("donor_ids",n["donor_ids"][:-1]));run("empty_nuisance_rejected",lambda a,n:n.__setitem__("operator_mixture_fractions",{}));run("missing_nuisance_category_rejected",lambda a,n:n.pop("recipient_depth"))
 try:integrate_records([],nu,"caller-chosen");blocked=False
 except ValueError as e:blocked="STOP_FORWARD_AUTHORITY_NOT_FROZEN" in str(e)
 return {"base_synthetic_complete_pass":test_decision(agg,nu),"mandatory_vetoes":attacks,"all_mandatory_vetoes_pass":all(attacks.values()),"production_unfrozen_forward_rejected":blocked,"aggregate_only_production_qualification_api_absent":True,"qid_v2_supersession_hash":QID_V2_SHA}
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--out",type=Path,required=True);x=a.parse_args();x.out.write_text(json.dumps(adversarial(),indent=2,allow_nan=False)+"\n",encoding="utf-8")
