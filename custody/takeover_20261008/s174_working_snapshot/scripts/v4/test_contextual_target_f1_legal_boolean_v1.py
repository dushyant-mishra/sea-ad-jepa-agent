"""Strict built-in-boolean domain tests; no project data or outcomes."""
from __future__ import annotations
import argparse,copy,importlib.util,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
def load(p,n):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
decision=load(HERE/"contextual_target_f1_decision_v4.py","decision_v4");integration=load(HERE/"contextual_target_f1_decision_integration_v4.py","integration_v4");fixtures=load(HERE/"test_contextual_target_f1_decision_truth_table_v2.py","fixtures")
CASES=[("bool_true",True),("bool_false",False),("str_True","True"),("str_False","False"),("str_true","true"),("str_false","false"),("str_1","1"),("str_0","0"),("int_0",0),("int_1",1),("empty_list",[]),("list_1",[1]),("empty_dict",{}),("dict_x1",{"x":1}),("none",None),("numpy_bool_true",np.bool_(True)),("numpy_bool_false",np.bool_(False))]
def nuisance(value):return {"donor_ids":[f"d{i}" for i in range(104)],"nuisance_authority_sha256":"unfrozen-test","source_indicators":{"HVS":[0.]*104},"operator_mixture_fractions":{"op0":[0.]*104},"recipient_physical_support":[0.]*104,"recipient_depth":[0.]*104,"correct_minus_null_visible_depth":[0.]*104,"correct_minus_null_measured_zero_rate":[0.]*104,"legal":value}
def main(out):
 base=fixtures.base_payload();rows=[]
 for name,value in CASES:
  p=copy.deepcopy(base);p["legal"]=value;decision_rejected=False;decision_qualified=False;legal_gate=False;decision_error=None
  try:r=decision.qualify_current(p);decision_qualified=r["qualified"];legal_gate=r["gates"]["legal_provenance"]
  except ValueError as e:decision_rejected=True;decision_error=str(e)
  integration_type_rejected=False;integration_reached_unfrozen_authority=False
  try:integration.nuisance_columns(nuisance(value),nuisance(value)["donor_ids"])
  except ValueError as e:
   integration_type_rejected="built-in bool" in str(e);integration_reached_unfrozen_authority="NOT_FROZEN" in str(e)
  expected=(name=="bool_true" and decision_qualified and legal_gate and integration_reached_unfrozen_authority) or (name=="bool_false" and not decision_rejected and not decision_qualified and not legal_gate and integration_reached_unfrozen_authority) or (name not in ("bool_true","bool_false") and decision_rejected and integration_type_rejected)
  rows.append({"case":name,"python_type":f"{type(value).__module__}.{type(value).__name__}","decision_rejected":decision_rejected,"decision_error":decision_error,"legal_gate":bool(legal_gate),"qualified":bool(decision_qualified),"integration_type_rejected":integration_type_rejected,"integration_builtin_bool_reached_unfrozen_authority_gate":integration_reached_unfrozen_authority,"expected_behavior":bool(expected)})
 result={"status":"PASS_F1_LEGAL_BOOLEAN_DOMAIN_ADVERSARIAL" if all(x["expected_behavior"] for x in rows) else "STOP_F1_LEGAL_BOOLEAN_DOMAIN_FAIL_OPEN","controlling_mechanism":"Both Python entry boundaries require type(value) is bool. JSON booleans deserialize to built-in bool; NumPy scalars and truthy containers are rejected.","cases":rows}
 out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
 if not result["status"].startswith("PASS_"):raise SystemExit(result["status"])
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args();main(a.out)
