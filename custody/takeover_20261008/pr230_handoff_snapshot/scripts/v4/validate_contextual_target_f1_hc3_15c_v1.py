"""Independent 15C validator; deliberately does not import the production adapter."""
from __future__ import annotations

import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t

ROOT=Path(__file__).resolve().parents[2]
P15A4=ROOT/"outputs/contextual_teacher_target_v1_f1_hc3_replication_frontier_complete_20260902"
P15B=ROOT/"outputs/contextual_teacher_target_v1_f1_hc3_nuisance_design_freeze_20260902"
PPROV=ROOT/"outputs/contextual_teacher_target_v1_f1_hc3_15b_provenance_repair_20260902"
PROGRAMS=("broad_common","weak_distributed","local","local_core","local_halo","core_halo","sparse_marker_like","innovation_tail")
EXPECTED={"15a4":"a112bd4907f2c20b4346179264391ceb8d3e9ceee42f7a8bcb1bcd153e4cb09f","15b":"a9d10fa17f162f3552c15095f3ef3ed7111f71c7a83978682303a2138088e174","prov":"6b0abab515b847fda5724b3194efdd4ad1f58ec0a7e3ad20fa9941f24e6e513d","design":"5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3","schema":"d7d0be302b455f7be0982d3e7906778c4fac59aee9b9f5c43e6017090d25e778","decision":"5215faffe1e90b6567054fd7fb4d62d501787dbacd704e09ff28af9c65d45913","integration":"5dfd5858f1e8865f871b633a033e400f2d7fb5e2fb52bebbc613f7efed1bce2a"}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def manifest(directory,name,expected):
 p=directory/name
 if sha(p)!=expected:return False
 for row in csv.DictReader(p.open(encoding="utf-8-sig")):
  q=directory/row["relative_path"]
  if not q.is_file() or q.stat().st_size!=int(row["bytes"]) or sha(q)!=row["sha256"]:return False
 return True
def rank(x):
 s=np.linalg.svd(x,compute_uv=False);tol=max(x.shape)*np.finfo(float).eps*s[0];return int(np.sum(s>tol))
def interval(x):
 x=np.asarray(x,float);n=len(x);m=float(x.mean()) if n else None
 if n<2 or not np.isfinite(x).all() or np.var(x,ddof=1)==0:return {"estimable":False,"mean":m}
 se=float(x.std(ddof=1)/np.sqrt(n));z=m/se
 return {"estimable":True,"mean":m,"lower":m-student_t.ppf(.975,n-1)*se,"lower_one_sided":m-student_t.ppf(.95,n-1)*se,"p_positive":student_t.sf(z,n-1),"p_negative":student_t.cdf(z,n-1)}
def holm(p):
 p=np.asarray(p,float);order=np.argsort(p,kind="stable");out=np.empty(len(p));running=0.
 for j,i in enumerate(order):running=max(running,(len(p)-j)*p[i]);out[i]=min(1.,running)
 return out
def hc3(y,x):
 y=np.asarray(y,float);x=np.asarray(x,float);r=rank(x);df=len(y)-r
 inv=np.linalg.inv(x.T@x);beta=inv@x.T@y;res=y-x@beta;hat=np.sum((x@inv)*x,axis=1);den=1-hat
 if not np.isfinite(y).all() or r!=x.shape[1] or df<=0 or np.any(den<=np.sqrt(np.finfo(float).eps)):return {"estimable":False,"rank":r,"df":df,"lower":None}
 u=res/den;meat=np.zeros((x.shape[1],x.shape[1]))
 for i in range(len(y)):meat+=(u[i]**2)*np.outer(x[i],x[i])
 cov=inv@meat@inv;se=float(np.sqrt(max(0,cov[0,0])))
 if not np.isfinite(se) or se==0:return {"estimable":False,"rank":r,"df":df,"lower":None}
 return {"estimable":True,"rank":r,"df":df,"beta0":float(beta[0]),"lower":float(beta[0]-student_t.ppf(.975,df)*se),"p_positive":float(student_t.sf(beta[0]/se,df))}
def independent_decision(p,x):
 schema=json.loads((P15B/"F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json").read_text());records=p["donor_records"]
 if set(records)!=set(schema["donor_order"]):raise ValueError("independent donor mismatch")
 vec=lambda key:np.asarray([records[d][key] for d in schema["donor_order"]],float);fam=lambda field,k:np.asarray([records[d][field][k] for d in schema["donor_order"]],float)
 overall=interval(vec("overall_A"));program={k:interval(fam("program_A",k)) for k in PROGRAMS};direct={k:interval(fam("program_delta",k)) for k in PROGRAMS};qprog={k:interval(fam("program_qid_margin",k)) for k in PROGRAMS}
 dneg=holm([direct[k].get("p_negative",0) if direct[k]["estimable"] else 0 for k in PROGRAMS]);qneg=holm([qprog[k].get("p_negative",0) if qprog[k]["estimable"] else 0 for k in PROGRAMS]);ev=np.asarray([records[d]["evidence_A"] for d in schema["donor_order"]],float);xx=np.asarray([.2,.4,.6,.8,1.]);xx-=xx.mean();slope=interval(ev@xx/(xx@xx));qm=interval(vec("qid_margin"));qw=interval(vec("qid_win_minus_half"));x2=np.ones((104,1),float)
 for i in range(1,16):
  candidate=np.column_stack([x2,x[:,i]-x[:,i].mean()])
  if rank(candidate)>rank(x2):x2=candidate
 rob=hc3(vec("overall_A"),x2);groups=np.array([d.split("::",1)[0] for d in schema["donor_order"]]);sources={g:interval(vec("overall_A")[groups==g]) for g in sorted(set(groups))};draw=[float(vec(k).mean()) for k in ("draw0","draw1")]
 gates={"legal_provenance":type(p["legal"]) is bool and p["legal"] is True,"overall_A_60_one_sided_positive":overall["estimable"] and overall["lower_one_sided"]>0,"protected_program_family_estimable":all(program[k]["estimable"] for k in PROGRAMS),"no_contextual_minus_direct_degradation":all(direct[k]["estimable"] for k in PROGRAMS) and np.all(dneg>=.05),"evidence_trend_one_sided_positive":slope["estimable"] and slope["lower_one_sided"]>0,"qid_v2_margin_one_sided_positive":qm["estimable"] and qm["lower_one_sided"]>0,"qid_v2_win_one_sided_positive":qw["estimable"] and qw["lower_one_sided"]>0,"no_qid_v2_program_negative_margin":all(qprog[k]["estimable"] for k in PROGRAMS) and np.all(qneg>=.05),"two_draw_sign_stable":np.isfinite(draw).all() and not(draw[0]<0<draw[1] or draw[1]<0<draw[0]),"hc3_nuisance_positive":rob["estimable"] and rob["lower"]>0,"cross_source_replication":all(v["estimable"] and v["lower"]>0 for v in sources.values())}
 return gates,rob,hashlib.sha256(x2.astype("<f8",copy=False).tobytes(order="C")).hexdigest()
def run(package,out):
 checks={"15a4_manifest":manifest(P15A4,"F1_HC3_15A4_MANIFEST.csv",EXPECTED["15a4"]),"15b_manifest":manifest(P15B,"F1_HC3_15B_MANIFEST.csv",EXPECTED["15b"]),"provenance_manifest":manifest(PPROV,"F1_HC3_15B_PROVENANCE_REPAIR_MANIFEST.csv",EXPECTED["prov"]),"truth_table":sha(ROOT/"outputs/contextual_teacher_target_v1_f1_decision_truth_table_repair_20260902/F1_FINAL_DECISION_TRUTH_TABLE_V2.json")=="76d420a0aa71f9b062b7394453f1f33282f7c78a956fc950fceb7ead682dcf5e","namespace_audit":sha(ROOT/"outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_ADDRESS_NAMESPACE_AUDIT.json")=="14b423d5ebca3cdda9a71d0d8b1974e7fe00aaaf84711355312cca01f5085384"}
 schema_path=P15B/"F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json";design_path=P15B/"F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin";schema=json.loads(schema_path.read_text());x=np.fromfile(design_path,dtype="<f8").reshape(104,16);q=np.linalg.qr(x,mode="reduced")[0];loo=[i for i in range(104) if rank(np.delete(x,i,axis=0))!=16]
 baseline=json.loads((package/"F1_15C_SYNTHETIC_BASELINE.json").read_text());gates,rob,effective_sha=independent_decision(baseline["payload"],x)
 adversarial=json.loads((package/"F1_15C_NUISANCE_ADVERSARIAL.json").read_text());regression=json.loads((package/"F1_15C_FULL_DECISION_REGRESSION.json").read_text());attack={a["attack"]:a for a in adversarial["attacks"]}
 a_gates,a_hc3,_=independent_decision(attack["A_nuisance_veto"]["payload"],x)
 zero=json.loads(json.dumps(baseline["payload"]));[r.__setitem__("overall_A",0.) for r in zero["donor_records"].values()];z_gates,z_hc3,_=independent_decision(zero,x)
 design_attacks=all(attack[k]["actual_candidate_design_sha256"]!=EXPECTED["design"] or attack[k]["actual_candidate_schema_sha256"]!=EXPECTED["schema"] for k in ("C_one_bit_design_mutation","D_wrong_triple","H_forbidden_NPH_C1","I_forbidden_HVS_C6","J_old_raw_rank18_design"))
 legal=attack["N_legal_type_domain"]["cases"];legal_independent=all(row["qualified"]==(row["case"]=="True") for row in legal)
 adversarial_independent={"nuisance_veto_exact":not a_gates["hc3_nuisance_positive"] and all(v for k,v in a_gates.items() if k!="hc3_nuisance_positive"),"zero_hc3_unestimable":not z_hc3["estimable"] and not z_gates["hc3_nuisance_positive"],"candidate_authority_mutations_distinct":design_attacks,"donor_keyed_api":set(baseline["payload"])=={"donor_records","legal"} and set(baseline["payload"]["donor_records"])==set(schema["donor_order"]),"legal_domain":legal_independent,"all_reported_attacks_pass":all(a["pass"] for a in adversarial["attacks"])}
 regression_independent=len(regression["legacy_14_cases"])==14 and all(a["isolated_pass"] for a in regression["legacy_14_cases"]) and regression["assignment_rows"]==44496 and regression["assignment_evidence_records"]==222480 and regression["single_hc3_gate"]
 source_text="\n".join((ROOT/p).read_text() for p in ("scripts/v4/contextual_target_f1_hc3_15c_adapter_v1.py","scripts/v4/run_contextual_target_f1_hc3_15c_v1.py"));forbidden_tokens=(".h5ad",".qs\"","torch.load","load_state_dict","backward(","optimizer.step","update_ema(")
 firewall_pass=not any(token in source_text.lower() for token in forbidden_tokens)
 result={"status":"PASS_F1_15C_INDEPENDENT_VALIDATION","authority_checks":checks,"design":{"sha256":sha(design_path),"schema_sha256":sha(schema_path),"triple":schema["selected_triple"],"donor_order_exact":len(schema["donor_order"])==len(set(schema["donor_order"]))==104,"rank":rank(x),"df":104-rank(x),"max_leverage":float(np.max(np.sum(q*q,axis=1))),"loo_critical_indices":loo,"effective_centered_sha256":effective_sha,"effective_sha_matches_production":effective_sha==baseline["decision"]["nuisance_effective_centered_design_sha256"]},"independent_hc3":rob,"gate_vector_exact":gates==baseline["decision"]["gates"],"synthetic_qualified":all(gates.values()),"independent_adversarial":adversarial_independent,"independent_regression":regression_independent,"reviewed_sources_unchanged":sha(ROOT/"scripts/v4/contextual_target_f1_decision_v4.py")==EXPECTED["decision"] and sha(ROOT/"scripts/v4/contextual_target_f1_decision_integration_v4.py")==EXPECTED["integration"],"real_reader_forward_authority_unset":"REAL_READER_FORWARD_AUTHORITY_SHA256 = None" in source_text,"forbidden_access_audit_pass":firewall_pass,"forbidden_access_audit_method":"static import/path/API audit of all production runner and adapter source; no expression/model/checkpoint APIs or suffixes permitted","terminal_status":"PASS_F1_HC3_15C_DECISION_INTEGRATION_AWAITING_EXTERNAL_REVIEW"}
 ok=all(checks.values()) and result["design"]["sha256"]==EXPECTED["design"] and result["design"]["schema_sha256"]==EXPECTED["schema"] and result["design"]["triple"]==[5,0,4] and result["design"]["rank"]==16 and not loo and result["design"]["effective_sha_matches_production"] and result["gate_vector_exact"] and result["synthetic_qualified"] and all(adversarial_independent.values()) and regression_independent and result["reviewed_sources_unchanged"] and result["real_reader_forward_authority_unset"] and firewall_pass
 if not ok:result["status"]="STOP_F1_15C_INDEPENDENT_MISMATCH"
 out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 if not ok:raise SystemExit(result["status"])
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--package",type=Path,required=True);a.add_argument("--out",type=Path,required=True);x=a.parse_args();run(x.package,x.out)
