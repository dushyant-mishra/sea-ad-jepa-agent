"""Independent strict-type and frozen-regression validation for the F1 legal boolean repair."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
EXPECTED={"zip":"3b841042102583526d75260273d6f309def52be5514156cf054d4b226ecfdc91","manifest":"9ee0e2f196f20677f6ea723092a8c142e6fe641322935b358093c1631757ca61","truth":"76d420a0aa71f9b062b7394453f1f33282f7c78a956fc950fceb7ead682dcf5e","assignment":"12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617","v2":"ac8157105b66ccd1617efb3740768a91711b429e5288afc34fb9a54adedcc462","old_decision":"cd51a219a1075462e94a6e5ad77d7f647800b619b81431c83972aca4aca47b65","old_integration":"6e7303155cdbd540263b4699439b293748e927c7afc64b0722ae05fda8daecc0","reg_external":"8cae651af09f0485816b32c012b5bcffd38dae7b56fbed5f6cfec5453304bcdd","reg_adversarial":"3f6db0f92fa593a38f12c8719eea109099b2607cf871054b705111ee28dda72e"}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def main(domain,reproduction,out):
 prior=ROOT/"outputs/contextual_teacher_target_v1_f1_decision_truth_table_repair_20260902";assign=ROOT/"outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv";decision=ROOT/"scripts/v4/contextual_target_f1_decision_v4.py";integration=ROOT/"scripts/v4/contextual_target_f1_decision_integration_v4.py";v2=ROOT/"scripts/v4/contextual_target_f1_querydesign_decision_v2.py"
 authority=sha(ROOT/"outputs/CONTEXTUAL_TEACHER_TARGET_V1_F1_DECISION_TRUTH_TABLE_REVIEW_20260902.zip")==EXPECTED["zip"] and sha(prior/"F1_DECISION_RECONCILIATION_MANIFEST.csv")==EXPECTED["manifest"] and sha(prior/"F1_FINAL_DECISION_TRUTH_TABLE_V2.json")==EXPECTED["truth"] and sha(assign)==EXPECTED["assignment"] and sha(v2)==EXPECTED["v2"]
 rep=json.loads(reproduction.read_text());reproduced=rep["pre_edit_decision_v4_sha256"]==EXPECTED["old_decision"] and [x["legal_gate"] for x in rep["results"]]==[False,True,True,True,True,True,True]
 dom=json.loads(domain.read_text());cases={x["case"]:x for x in dom["cases"]};expected_names={"bool_true","bool_false","str_True","str_False","str_true","str_false","str_1","str_0","int_0","int_1","empty_list","list_1","empty_dict","dict_x1","none","numpy_bool_true","numpy_bool_false"};domain_ok=dom["status"]=="PASS_F1_LEGAL_BOOLEAN_DOMAIN_ADVERSARIAL" and set(cases)==expected_names and all(x["expected_behavior"] for x in cases.values()) and cases["bool_true"]["qualified"] and not cases["bool_true"]["decision_rejected"] and not cases["bool_false"]["qualified"] and not cases["bool_false"]["decision_rejected"] and all(cases[n]["decision_rejected"] and cases[n]["integration_type_rejected"] for n in expected_names-{"bool_true","bool_false"})
 ds=decision.read_text();ins=integration.read_text();static_ok='type(payload["legal"]) is not bool' in ds and 'payload["legal"] is True' in ds and 'bool(payload["legal"])' not in ds and 'type(nuisance["legal"]) is not bool' in ins and '"legal":nuisance["legal"]' in ins and 'bool(nuisance["legal"])' not in ins
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);ext=td/"ext.json";adv=td/"adv.json";pop=td/"pop.json"
  subprocess.run([sys.executable,str(ROOT/"scripts/v4/test_contextual_target_f1_decision_truth_table_v2.py"),"--external",str(ext),"--adversarial",str(adv)],cwd=ROOT,check=True)
  subprocess.run([sys.executable,str(v2),"--synthetic-out",str(pop)],cwd=ROOT,check=True)
  pj=json.loads(pop.read_text());regression=sha(ext)==EXPECTED["reg_external"] and sha(adv)==EXPECTED["reg_adversarial"] and len(json.loads(adv.read_text())["attacks"])==14 and json.loads(adv.read_text())["status"]=="PASS_F1_ISOLATED_DECISION_ADVERSARIAL" and all(pj["frozen_population"].values()) and pj["donor_relabel_rejected"] and pj["cell_relabel_rejected"] and all(pj["qid_win_domain_attacks"].values())
 truth_unchanged=sha(prior/"F1_FINAL_DECISION_TRUTH_TABLE_V2.json")==EXPECTED["truth"];blocked="FROZEN_FORWARD_AUTHORITY_SHA256=None" in v2.read_text() and "FROZEN_NUISANCE_AUTHORITY_SHA256=None" in ins;ok=all((authority,reproduced,domain_ok,static_ok,regression,truth_unchanged,blocked))
 result={"status":"PASS_F1_LEGAL_BOOLEAN_INDEPENDENT_VALIDATION" if ok else "STOP_F1_LEGAL_BOOLEAN_INDEPENDENT_MISMATCH","authority_verified":authority,"external_failure_reproduced":reproduced,"strict_domain_independently_verified":domain_ok,"source_type_boundary_verified":static_ok,"frozen_14_decision_and_population_regressions_exact":regression,"truth_table_sha256_unchanged":truth_unchanged,"truth_table_sha256":sha(prior/"F1_FINAL_DECISION_TRUTH_TABLE_V2.json"),"current_source_sha256":{"decision_v4":sha(decision),"integration_v4":sha(integration)},"forward_and_nuisance_authorities_unfrozen":blocked,"expression_or_candidate_outcomes_accessed":False,"training_or_ema_accessed":False}
 out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 if not ok:raise SystemExit(result["status"])
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--domain",type=Path,required=True);p.add_argument("--reproduction",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();main(a.domain,a.reproduction,a.out)
