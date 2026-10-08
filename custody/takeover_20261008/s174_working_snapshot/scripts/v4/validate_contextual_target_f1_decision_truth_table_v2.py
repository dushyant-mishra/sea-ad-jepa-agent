"""Independent arithmetic/provenance validator for F1 decision truth-table reconciliation."""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t
ROOT=Path(__file__).resolve().parents[2];PROGRAMS=("broad_common","weak_distributed","local","local_core","local_halo","core_halo","sparse_marker_like","innovation_tail");EVIDENCE=np.asarray((.2,.4,.6,.8,1.));ALPHA=.05
EXPECTED={"zip":"47f490fb75d126600092bd77008f3f95e686f75d76c21dd755b8216ee82e9ed5","prior_manifest":"1f034fb002a97b6b6923835fbdca173e551e908195e6df456c718da71519741f","assignment":"12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617","key":"7d91edec79ae27fd7c9fd35ebaf33454e05aaf39a0dd8c24d23a9460a3b5242a","weight":"018d80428c25a0060168a942ca03dc9e814783463cc077e3661008ba5f7b5eeb","namespace":"595fd8bc860b13ce9ec2a957b0f3d92f850effcb51ae6e2f06b8c5d25d7bd53f","null":"aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6"}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def interval(x):
 x=np.asarray(x,np.float64);n=len(x);m=float(x.mean()) if n else None
 if n<2 or not np.isfinite(x).all() or float(np.var(x,ddof=1))==0:return {"estimable":False,"mean":m,"lower":None,"lower_one":None,"p_pos":None,"p_neg":None}
 se=float(x.std(ddof=1)/np.sqrt(n));return {"estimable":True,"mean":m,"lower":m-float(student_t.ppf(.975,n-1))*se,"lower_one":m-float(student_t.ppf(.95,n-1))*se,"p_pos":float(student_t.sf(m/se,n-1)),"p_neg":float(student_t.cdf(m/se,n-1))}
def holm(p):
 p=np.asarray(p,np.float64);order=np.argsort(p,kind="stable");out=np.empty(len(p));run=0.
 for rank,i in enumerate(order):run=max(run,(len(p)-rank)*p[i]);out[i]=min(1.,run)
 return out
def restore(x):
 if x=="NaN":return float("nan")
 if x=="Infinity":return float("inf")
 if x=="-Infinity":return float("-inf")
 if isinstance(x,dict):return {k:restore(v) for k,v in x.items()}
 if isinstance(x,list):return [restore(v) for v in x]
 return x
def rank(x):
 s=np.linalg.svd(x,compute_uv=False);tol=max(x.shape)*np.finfo(np.float64).eps*(s[0] if len(s) else 0.);return int(np.sum(s>tol))
def hc3(y,columns):
 y=np.asarray(y,np.float64);n=len(y);X=np.ones((n,1))
 for name in sorted(columns):
  v=np.asarray(columns[name],np.float64);candidate=np.column_stack([X,v-v.mean()])
  if rank(candidate)>rank(X):X=candidate
 r=rank(X);df=n-r
 if not np.isfinite(y).all() or r!=X.shape[1] or df<=0:return False
 inv=np.linalg.inv(X.T@X);b=inv@X.T@y;res=y-X@b;h=np.einsum("ij,jk,ik->i",X,inv,X);den=1-h
 if np.any(den<=np.sqrt(np.finfo(np.float64).eps)):return False
 u=res/den;cov=inv@(X.T@(X*(u*u)[:,None]))@inv;se=float(np.sqrt(max(0.,cov[0,0])))
 return bool(np.isfinite(se) and se>0 and b[0]-float(student_t.ppf(.975,df))*se>0)
def gates(p):
 overall=interval(p["overall_A"]);prog={k:interval(p["program_A"][k]) for k in PROGRAMS};direct={k:interval(p["program_delta"][k]) for k in PROGRAMS};qprog={k:interval(p["program_qid_margin"][k]) for k in PROGRAMS};dneg=holm([direct[k]["p_neg"] if direct[k]["estimable"] else 0 for k in PROGRAMS]);qneg=holm([qprog[k]["p_neg"] if qprog[k]["estimable"] else 0 for k in PROGRAMS]);x=EVIDENCE-EVIDENCE.mean();slopes=np.asarray(p["evidence_A"])@x/np.dot(x,x);slope=interval(slopes);qm=interval(p["qid_margin"]);qw=interval(p["qid_win_minus_half"]);d0=float(np.mean(p["draw0"]));d1=float(np.mean(p["draw1"]));source={s:interval([y for y,g in zip(p["nuisance_y"],p["source_group"]) if g==s]) for s in ("HVS","NPH52","SEA_AD")}
 return {"legal_provenance":bool(p["legal"]),"overall_A_60_one_sided_positive":bool(overall["estimable"] and overall["lower_one"]>0),"protected_program_family_estimable":all(prog[k]["estimable"] for k in PROGRAMS),"no_contextual_minus_direct_degradation":bool(all(direct[k]["estimable"] for k in PROGRAMS) and np.all(dneg>=ALPHA)),"evidence_trend_one_sided_positive":bool(slope["estimable"] and slope["lower_one"]>0),"qid_v2_margin_one_sided_positive":bool(qm["estimable"] and qm["lower_one"]>0),"qid_v2_win_one_sided_positive":bool(qw["estimable"] and qw["lower_one"]>0),"no_qid_v2_program_negative_margin":bool(all(qprog[k]["estimable"] for k in PROGRAMS) and np.all(qneg>=ALPHA)),"two_draw_sign_stable":bool(np.isfinite([d0,d1]).all() and not ((d0<0<d1) or (d1<0<d0))),"hc3_nuisance_positive":hc3(p["nuisance_y"],p["nuisance_columns"]),"cross_source_replication":all(v["estimable"] and v["lower"]>0 for v in source.values())}
def main(truth,external,adversarial,out):
 t=json.loads(truth.read_text());e=json.loads(external.read_text());a=json.loads(adversarial.read_text());families=t["families"];ids=[x["id"] for x in families]
 truth_ok=len(families)==12 and len(set(ids))==12 and t["current_claim_scope"]=="FINITE_FROZEN_2781_DESIGN_SAMPLED_W2_EXPECTATION" and t["program_estimand"]=="DESIGN_SAMPLED_W2_PROGRAM_ESTIMAND" and next(x for x in families if x["id"]=="protected_program_A_60")["role"]=="estimability_gate_and_positive_holm_report_only" and next(x for x in families if x["id"]=="overall_contextual_A_60")["tail_convention"]=="one_sided_positive"
 base_ind=gates(a["base_payload"]);base_match=base_ind==a["base_gate_vector"] and all(base_ind.values());attack_checks={}
 for x in a["attacks"]:
  g=gates(restore(x["payload"]));changed=[k for k in base_ind if base_ind[k]!=g[k]];attack_checks[x["attack"]]=g==x["attacked_gates"] and changed==x["changed_gates"] and x["isolated_pass"]
 ep=e["payload"];local=interval(ep["program_A"]["local_core"]);all_prog=all(interval(ep["program_A"][p])["estimable"] for p in PROGRAMS);external_ok=local["estimable"] and local["p_pos"]>.05 and all_prog and e["old_v1_result"]["qualified"] and e["required_reproduction"]["local_core_positive_holm_fails"]
 assign=ROOT/"outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv";rows=list(csv.DictReader(assign.open(encoding="utf-8-sig",newline="")));keys={r["assignment_key_sha256"] for r in rows};cells={r["canonical_cell_id"] for r in rows};donors={r["donor_id"] for r in rows};ops={r["operator_index"] for r in rows};pair=defaultdict(set)
 for r in rows:pair[(r["canonical_cell_id"],r["program"])].add(int(r["draw_replicate"]))
 population_ok=sha(assign)==EXPECTED["assignment"] and len(rows)==len(keys)==44496 and len(cells)==2781 and len(donors)==104 and len(ops)==42 and len(pair)==2781*8 and all(v=={0,1} for v in pair.values()) and len({(k,e) for k in keys for e in EVIDENCE})==222480
 prior=ROOT/"outputs/contextual_teacher_target_v1_f1_querydesign_adjudicator_repair_20260902";auth_ok=sha(ROOT/"outputs/CONTEXTUAL_TEACHER_TARGET_V1_F1_ADJUDICATOR_REPAIR_REVIEW_20260902.zip")==EXPECTED["zip"] and sha(prior/"F1_ADJUDICATOR_REPAIR_MANIFEST.csv")==EXPECTED["prior_manifest"] and EXPECTED["key"] in (ROOT/"outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_RANDOMIZATION_AUTHORITY.json").read_text() and EXPECTED["weight"] in assign.read_text(encoding="utf-8-sig") and EXPECTED["namespace"] in (prior/"F1_ADJUDICATOR_REPAIR_AUTHORITY.json").read_text() and EXPECTED["null"] in (prior/"F1_ADJUDICATOR_REPAIR_AUTHORITY.json").read_text()
 integration=(ROOT/"scripts/v4/contextual_target_f1_decision_integration_v4.py").read_text();decision=(ROOT/"scripts/v4/contextual_target_f1_decision_v4.py").read_text();single_gate="v1.qualify" not in integration and "qualify_current(payload)" in integration and integration.count("qualify_current(")==1 and "PANEL_CONDITIONED_QUERY_SAMPLE" not in decision
 blocked="FROZEN_FORWARD_AUTHORITY_SHA256=None" in (ROOT/"scripts/v4/contextual_target_f1_querydesign_decision_v2.py").read_text() and "FROZEN_NUISANCE_AUTHORITY_SHA256=None" in integration
 ok=all([truth_ok,base_match,all(attack_checks.values()),external_ok,population_ok,auth_ok,single_gate,blocked])
 result={"status":"PASS_F1_DECISION_RECONCILIATION_INDEPENDENT_VALIDATION" if ok else "STOP_F1_DECISION_RECONCILIATION_INDEPENDENT_MISMATCH","truth_table":{"families":len(families),"unique_single_gate_semantics":truth_ok,"claim_scope_current":t["current_claim_scope"]},"independent_arithmetic":{"base_exact_match":base_match,"isolated_attack_exact_matches":attack_checks,"external_negative_program_reproduced":external_ok},"population":{"assignments":len(rows),"record_universe":len(keys)*5,"cells":len(cells),"donors":len(donors),"operators":len(ops),"exact":population_ok},"authorities_unchanged":auth_ok,"no_stale_wholesale_v1_qualify":single_gate,"real_forward_and_nuisance_unfrozen":blocked,"expression_or_candidate_outcomes_accessed":False,"training_or_ema_accessed":False}
 out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 if not ok:raise SystemExit(result["status"])
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--truth",type=Path,required=True);p.add_argument("--external",type=Path,required=True);p.add_argument("--adversarial",type=Path,required=True);p.add_argument("--out",type=Path,required=True);x=p.parse_args();main(x.truth,x.external,x.adversarial,x.out)
