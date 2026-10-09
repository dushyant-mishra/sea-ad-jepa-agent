"""Single-gate F1 integration: validated records -> current v4 truth-table decision."""
from __future__ import annotations
import hashlib,importlib.util
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;COMPONENT=HERE/"contextual_target_f1_querydesign_decision_v2.py";DECISION=HERE/"contextual_target_f1_decision_v4.py"
DECISION_SHA="5215faffe1e90b6567054fd7fb4d62d501787dbacd704e09ff28af9c65d45913";TRUTH_TABLE_SHA="76d420a0aa71f9b062b7394453f1f33282f7c78a956fc950fceb7ead682dcf5e";FROZEN_NUISANCE_AUTHORITY_SHA256=None
EVIDENCE=(.2,.4,.6,.8,1.);NUISANCE_FIELDS=("source_indicators","operator_mixture_fractions","recipient_physical_support","recipient_depth","correct_minus_null_visible_depth","correct_minus_null_measured_zero_rate")
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def load(p,name,expected=None):
 if expected and sha(p)!=expected:raise ValueError("STOP_F1_FINAL_DECISION_TRUTH_TABLE_UNRESOLVED")
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def nuisance_columns(nuisance,donors):
 required={"donor_ids","nuisance_authority_sha256",*NUISANCE_FIELDS,"legal"}
 if set(nuisance)!=required or nuisance["donor_ids"]!=donors:raise ValueError("nuisance population binding mismatch")
 if type(nuisance["legal"]) is not bool:raise ValueError("legal provenance authority must be built-in bool")
 if FROZEN_NUISANCE_AUTHORITY_SHA256 is None or nuisance["nuisance_authority_sha256"]!=FROZEN_NUISANCE_AUTHORITY_SHA256:raise ValueError("STOP_F1_NUISANCE_AUTHORITY_NOT_FROZEN")
 cols={}
 for field in NUISANCE_FIELDS:
  value=nuisance[field]
  if isinstance(value,dict):
   if not value:raise ValueError("nuisance category empty")
   for name,a in sorted(value.items()):cols[f"{field}__{name}"]=a
  else:cols[field]=value
 if any(not isinstance(v,list) or len(v)!=104 for v in cols.values()):raise ValueError("nuisance population binding mismatch")
 return cols
def integrate_records(records,nuisance,forward_authority_sha256):
 component=load(COMPONENT,"f1_component_v2");agg=component.aggregate(records,forward_authority_sha256=forward_authority_sha256);donors=list(agg["donors"]);cols=nuisance_columns(nuisance,donors)
 payload={"overall_A":agg["overall"]["0.6"]["A"],"program_A":agg["program"]["0.6"],"program_delta":agg["program_direct"]["0.6"],"evidence_A":np.column_stack([agg["overall"][str(e)]["A"] for e in EVIDENCE]).tolist(),"qid_margin":agg["overall"]["0.6"]["qid_margin"],"qid_win_minus_half":agg["overall"]["0.6"]["qid_win_minus_half"],"program_qid_margin":agg["program_qid_margin"]["0.6"],"draw0":agg["overall"]["0.6"]["draw0"],"draw1":agg["overall"]["0.6"]["draw1"],"nuisance_y":agg["overall"]["0.6"]["A"],"source_group":agg["donor_source"],"nuisance_columns":cols,"legal":nuisance["legal"]}
 decision=load(DECISION,"f1_current_v4",DECISION_SHA).qualify_current(payload);decision["truth_table_sha256"]=TRUTH_TABLE_SHA;decision["population_authority"]=agg["population_authority"];return decision
