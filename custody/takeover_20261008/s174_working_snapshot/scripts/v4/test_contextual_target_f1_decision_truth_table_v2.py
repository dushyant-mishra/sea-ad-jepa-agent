"""Outcome-blind deterministic reproduction and isolated tests for the F1 truth table."""
from __future__ import annotations
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;V1=HERE/"contextual_target_f1_decision_v1.py";V4=HERE/"contextual_target_f1_decision_v4.py";COMP=HERE/"contextual_target_f1_querydesign_decision_v2.py"
def load(p,name):s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
v1=load(V1,"v1");v4=load(V4,"v4");component=load(COMP,"component")
PROGRAMS=v4.PROGRAMS;EVIDENCE=v4.EVIDENCE
def json_safe(x):
 if isinstance(x,float) and not np.isfinite(x):return "NaN" if np.isnan(x) else ("Infinity" if x>0 else "-Infinity")
 if isinstance(x,dict):return {k:json_safe(v) for k,v in x.items()}
 if isinstance(x,list):return [json_safe(v) for v in x]
 return x
def canonical(x):return hashlib.sha256(json.dumps(json_safe(x),sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def base_payload():
 rng=np.random.default_rng(9022026);n=104;noise=rng.normal(0,.018,n);base=.34+.045*np.sin(np.arange(n)*.37)+noise;source=["HVS"]*35+["NPH52"]*34+["SEA_AD"]*35
 program={p:(base+.012*i+rng.normal(0,.006,n)).tolist() for i,p in enumerate(PROGRAMS)};direct={p:(.08+.012*np.sin(np.arange(n)*(.11+i*.007))+rng.normal(0,.004,n)).tolist() for i,p in enumerate(PROGRAMS)};qprog={p:(.16+.02*np.sin(np.arange(n)*(.13+i*.009))+rng.normal(0,.005,n)).tolist() for i,p in enumerate(PROGRAMS)}
 evidence=np.column_stack([base+.075*j+rng.normal(0,.003,n) for j in range(5)]);draw0=base+.012+np.linspace(-.004,.004,n);draw1=base-.012-np.linspace(-.004,.004,n)
 return {"overall_A":base.tolist(),"program_A":program,"program_delta":direct,"evidence_A":evidence.tolist(),"qid_margin":(.18+.03*np.sin(np.arange(n)*.17)+rng.normal(0,.004,n)).tolist(),"qid_win_minus_half":(.22+.025*np.cos(np.arange(n)*.19)+rng.normal(0,.004,n)).tolist(),"program_qid_margin":qprog,"draw0":draw0.tolist(),"draw1":draw1.tolist(),"nuisance_y":base.tolist(),"source_group":source,"nuisance_columns":{"source_HVS":([1.]*35+[0.]*69),"source_NPH52":([0.]*35+[1.]*34+[0.]*35),"operator_mix_00":np.sin(np.arange(n)*.23).tolist(),"recipient_depth":np.cos(np.arange(n)*.31).tolist(),"support_depth":np.sin(np.arange(n)*.41).tolist(),"visible_depth_delta":np.cos(np.arange(n)*.47).tolist(),"measured_zero_rate_delta":np.sin(np.arange(n)*.53).tolist()},"legal":True}
def to_v1(p):return {"overall_A":p["overall_A"],"program_A":p["program_A"],"program_delta":p["program_delta"],"evidence_A":p["evidence_A"],"query_margin":p["qid_margin"],"query_structure":p["qid_win_minus_half"],"nuisance_y":p["nuisance_y"],"source_group":p["source_group"],"nuisance_columns":p["nuisance_columns"],"legal":p["legal"]}
def external_reproduction():
 p=base_payload();p["program_A"]["local_core"]=(np.linspace(-.24,-.12,104)+.01*np.sin(np.arange(104))).tolist();old=v1.qualify(to_v1(p));current=v4.qualify_current(p)
 result={"status":"PASS_F1_EXTERNAL_FAILURE_REPRODUCED","payload":p,"payload_sha256":canonical(p),"old_v1_result":old,"old_v1_result_sha256":canonical(old),"required_reproduction":{"local_core_positive_holm_fails":old["program_positive_holm"]["local_core"]>=.05,"all_programs_reported_and_estimable":old["gates"]["all_programs_reported_and_estimable"],"old_v1_qualified_true":old["qualified"]},"current_truth_table_behavior":{"qualified":current["qualified"],"protected_program_family_estimable":current["gates"]["protected_program_family_estimable"],"local_core_positive_holm_report_only":current["reports"]["protected_program_positive_holm_report_only"]["local_core"],"explanation":"Finite negative local_core is estimable and changes a report-only positive Holm result. Frozen prose explicitly forbids turning that result into an all-program qualification hurdle."}}
 if not all(result["required_reproduction"].values()):raise RuntimeError("STOP_F1_EXTERNAL_FAILURE_NOT_REPRODUCED")
 return result
def attacks():
 base=base_payload();bd=v4.qualify_current(base)
 if not bd["qualified"]:raise RuntimeError(f"base does not pass: {bd['gates']}")
 specs=[]
 def add(name,intended,mutate,report_only=False,allowed_changed=None):
  p=copy.deepcopy(base);mutate(p);d=v4.qualify_current(p);changed=[k for k in bd["gates"] if bd["gates"][k]!=d["gates"][k]]
  expected=[intended] if allowed_changed is None else allowed_changed;isolated=(d["qualified"] if report_only else ((not d["qualified"]) and changed==expected))
  specs.append({"attack":name,"intended_gate":intended,"payload":json_safe(p),"payload_sha256":canonical(p),"base_gates":bd["gates"],"attacked_gates":d["gates"],"changed_gates":changed,"allowed_changed_gates":expected,"mathematical_coupling_declared":allowed_changed is not None,"attacked_qualified":d["qualified"],"report_only_family":report_only,"isolated_pass":bool(isolated)})
 add("A_protected_program_finite_negative_report_only","protected_program_positive_holm_report_only",lambda p:p["program_A"].__setitem__("local_core",(np.linspace(-.24,-.12,104)+.01*np.sin(np.arange(104))).tolist()),report_only=True)
 add("B_direct_degradation","no_contextual_minus_direct_degradation",lambda p:p["program_delta"].__setitem__("local_core",(-.3+.02*np.sin(np.arange(104))).tolist()))
 add("C_evidence_trend","evidence_trend_one_sided_positive",lambda p:p.__setitem__("evidence_A",np.column_stack([np.asarray(p["overall_A"])-.08*j for j in range(5)]).tolist()))
 add("D_qid_margin","qid_v2_margin_one_sided_positive",lambda p:p.__setitem__("qid_margin",(-.12+.02*np.sin(np.arange(104))).tolist()))
 add("E_qid_win","qid_v2_win_one_sided_positive",lambda p:p.__setitem__("qid_win_minus_half",(-.12+.02*np.cos(np.arange(104))).tolist()))
 def draw_attack(p):
  a=np.asarray(p["overall_A"]);p["draw0"]=(-.05+.005*np.sin(np.arange(104))).tolist();p["draw1"]=(2*a-np.asarray(p["draw0"])).tolist()
 add("F_draw_sign","two_draw_sign_stable",draw_attack)
 add("G_hc3_nuisance","hc3_nuisance_positive",lambda p:p.__setitem__("nuisance_columns",{f"rank_{i:03d}":np.eye(104)[:,i].tolist() for i in range(103)}))
 def source_attack(p):
  y=np.r_[.62+.02*np.sin(np.arange(35)),.62+.02*np.cos(np.arange(34)),-.04+.02*np.sin(np.arange(35))];p["overall_A"]=y.tolist();p["nuisance_y"]=y.tolist()
 add("H_cross_source","cross_source_replication",source_attack)
 add("I_nonfinite_qid_margin","qid_v2_margin_one_sided_positive",lambda p:p["qid_margin"].__setitem__(0,float("nan")))
 add("J_zero_variance_qid_win","qid_v2_win_one_sided_positive",lambda p:p.__setitem__("qid_win_minus_half",[.2]*104))
 def overall_attack(p):
  y=(-.12+.02*np.sin(np.arange(104))).tolist();p["overall_A"]=y;p["nuisance_y"]=list(y)
 add("K_overall_primary_failure_with_declared_shared_outcome_coupling","overall_A_60_one_sided_positive",overall_attack,allowed_changed=["overall_A_60_one_sided_positive","hc3_nuisance_positive","cross_source_replication"])
 add("L_qid_program_negative_holm","no_qid_v2_program_negative_margin",lambda p:p["program_qid_margin"].__setitem__("local_core",(-.25+.02*np.sin(np.arange(104))).tolist()))
 add("M_legal_provenance","legal_provenance",lambda p:p.__setitem__("legal",False))
 add("N_protected_program_unestimable","protected_program_family_estimable",lambda p:p["program_A"].__setitem__("local_core",[0.]*104))
 pop=component.frozen_population_adversarial();syn=component.synthetic();population_ok=all(pop.values()) and syn["donor_relabel_rejected"] and syn["cell_relabel_rejected"] and all(syn["qid_win_domain_attacks"].values())
 return {"status":"PASS_F1_ISOLATED_DECISION_ADVERSARIAL" if all(x["isolated_pass"] for x in specs) and population_ok else "STOP_F1_FINAL_DECISION_TRUTH_TABLE_UNRESOLVED","base_qualified":bd["qualified"],"base_payload":base,"base_payload_sha256":canonical(base),"base_gate_vector":bd["gates"],"attacks":specs,"population_attacks":pop,"record_identity_attacks":{"donor_relabel_rejected":syn["donor_relabel_rejected"],"cell_relabel_rejected":syn["cell_relabel_rejected"],"qid_win_domain_attacks":syn["qid_win_domain_attacks"]}}
def main(external,adversarial):
 e=external_reproduction();a=attacks();external.write_text(json.dumps(e,indent=2,allow_nan=False)+"\n",encoding="utf-8");adversarial.write_text(json.dumps(a,indent=2,allow_nan=False)+"\n",encoding="utf-8")
 if not a["status"].startswith("PASS_"):raise SystemExit(a["status"])
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--external",type=Path,required=True);p.add_argument("--adversarial",type=Path,required=True);a=p.parse_args();main(a.external,a.adversarial)
