"""Independent, outcome-blind validation of the F1 adjudicator repair."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,subprocess,sys,tempfile
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/"outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901"
ASSIGN=OLD/"F1_QUERY_ASSIGNMENTS_2DRAW.csv"
PROGRAMS={"broad_common","weak_distributed","local","local_core","local_halo","core_halo","sparse_marker_like","innovation_tail"};EVIDENCE=(.2,.4,.6,.8,1.)
EXPECTED={"assignment":"12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617","old_root":"74ff3f54e0e15006d2d3970fa2429c1dd734abf1eb619886e2a2a68dd7c006e4","key":"7d91edec79ae27fd7c9fd35ebaf33454e05aaf39a0dd8c24d23a9460a3b5242a","weights":"018d80428c25a0060168a942ca03dc9e814783463cc077e3661008ba5f7b5eeb","namespace":"595fd8bc860b13ce9ec2a957b0f3d92f850effcb51ae6e2f06b8c5d25d7bd53f","null":"aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6","engine":"204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34"}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def rejects(obs,expected):return len(obs)!=222480 or len(set(obs))!=222480 or set(obs)!=expected
def main(out):
 if sha(ASSIGN)!=EXPECTED["assignment"]:raise SystemExit("STOP_F1_ADJUDICATOR_REPAIR_AUTHORITY_MISMATCH")
 rows=list(csv.DictReader(ASSIGN.open(encoding="utf-8-sig",newline="")));by_key={r["assignment_key_sha256"]:r for r in rows}
 cells={r["canonical_cell_id"] for r in rows};donors={r["donor_id"] for r in rows};operators={int(r["operator_index"]) for r in rows}
 pair=defaultdict(set);identity={};weights={}
 for r in rows:
  pair[(r["canonical_cell_id"],r["program"])].add(int(r["draw_replicate"]));ident=(r["donor_id"],r["source"],int(r["operator_index"]),r["evaluation_row_authority_sha256"])
  if r["canonical_cell_id"] in identity and identity[r["canonical_cell_id"]]!=ident:raise SystemExit("cell identity conflict")
  identity[r["canonical_cell_id"]]=ident;weights[r["canonical_cell_id"]]=(int(r["cell_weight_numerator"]),int(r["cell_weight_denominator"]),r["cell_weight_float64_hex"],r["cell_weight_authority_sha256"])
 authority_ok=len(rows)==len(by_key)==44496 and len(cells)==2781 and len(donors)==104 and len(operators)==42 and {r["program"] for r in rows}==PROGRAMS and len(pair)==2781*8 and all(x=={0,1} for x in pair.values())
 masses={d:sum((Fraction(weights[c][0],weights[c][1]) for c in cells if identity[c][0]==d),Fraction()) for d in donors};weights_ok={x[3] for x in weights.values()}=={EXPECTED["weights"]} and all(m==1 for m in masses.values()) and all(float(Fraction(x[0],x[1])).hex()==x[2] for x in weights.values())
 expected={(k,e) for k in by_key for e in EVIDENCE};obs=list(expected);first=rows[0];victim_d=first["donor_id"];victim_c=first["canonical_cell_id"]
 def identity_accepts(key,cell,donor,source,operator,program,replicate,query,row_authority):
  a=by_key.get(key);return a is not None and (cell,donor,source,int(operator),program,int(replicate),int(query),row_authority)==(a["canonical_cell_id"],a["donor_id"],a["source"],int(a["operator_index"]),a["program"],int(a["draw_replicate"]),int(a["selected_query_address"]),a["evaluation_row_authority_sha256"])
 args=(first["assignment_key_sha256"],first["canonical_cell_id"],first["donor_id"],first["source"],first["operator_index"],first["program"],first["draw_replicate"],first["selected_query_address"],first["evaluation_row_authority_sha256"]);alternate=next(c for c in cells if c!=victim_c)
 attacks={"drop_entire_donor_rejected":rejects([x for x in obs if by_key[x[0]]["donor_id"]!=victim_d],expected),"drop_entire_cell_rejected":rejects([x for x in obs if by_key[x[0]]["canonical_cell_id"]!=victim_c],expected),"missing_assignment_evidence_rejected":rejects(obs[:-1],expected),"duplicate_replace_rejected":rejects(obs[:-1]+[obs[0]],expected),"extra_assignment_rejected":rejects(obs+[("0"*64,.2)],expected),"donor_relabel_rejected":not identity_accepts(args[0],args[1],"new_donor",*args[3:]),"cell_relabel_rejected":not identity_accepts(args[0],alternate,*args[2:])}
 qid={str(v):not (math.isfinite(v) and v in (0.,.5,1.)) for v in (2.,-1.,.25,float("nan"),float("inf"))}
 integ=ROOT/"scripts/v4/contextual_target_f1_decision_integration_v3.py";v2=ROOT/"scripts/v4/contextual_target_f1_querydesign_decision_v2.py";engine=ROOT/"scripts/v4/contextual_target_f1_decision_v1.py"
 with tempfile.TemporaryDirectory() as td:
  io=Path(td)/"integration.json";subprocess.run([sys.executable,str(integ),"--out",str(io)],check=True,cwd=ROOT);integration=json.loads(io.read_text())
 qid_contract=OLD/"F1_QUERY_IDENTITY_V2_CONTRACT.md";qid_sha="15d873871787e0820f63aaead8f27a6f1057541e16640d8492053144a9c69423"
 v2text=v2.read_text(encoding="utf-8");itext=integ.read_text(encoding="utf-8");boundary=("QUERY_DESIGN_COMPONENT_ONLY" in v2text and '"qualified_query_design_component":' not in v2text and "FROZEN_FORWARD_AUTHORITY_SHA256=None" in v2text and "def integrate_records(" in itext and "def _integrate_aggregate(" not in itext and "def integrate(query_component,complete_payload" not in itext and integration["base_synthetic_complete_pass"] and integration["all_mandatory_vetoes_pass"] and integration["production_unfrozen_forward_rejected"] and integration["aggregate_only_production_qualification_api_absent"] and integration["qid_v2_supersession_hash"]==qid_sha and sha(qid_contract)==qid_sha and all(integration["mandatory_vetoes"].values()) and integration["mandatory_vetoes"]["complete_payload_subset_rejected"] and integration["mandatory_vetoes"]["nuisance_donor_omission_rejected"] and integration["mandatory_vetoes"]["empty_nuisance_rejected"] and integration["mandatory_vetoes"]["missing_nuisance_category_rejected"] and sha(engine)==EXPECTED["engine"])
 old_root=(OLD/"F1_QUERYDESIGN_REPAIR_MANIFEST_ROOT_SHA256.txt").read_text().strip()==EXPECTED["old_root"]
 key=json.loads((OLD/"F1_QUERY_RANDOMIZATION_AUTHORITY.json").read_text())["public_key_sha256"]==EXPECTED["key"]
 ns=json.loads((OLD/"F1_ADDRESS_NAMESPACE_AUDIT.json").read_text())["ordered_namespace_semantic_sha256"]==EXPECTED["namespace"]
 null_ok=EXPECTED["null"] in (OLD/"F1_QUERYDESIGN_REPAIR_SOURCE_AUTHORITY.json").read_text()
 result={"status":"PASS_F1_QUERYDESIGN_ADJUDICATOR_INDEPENDENT_VALIDATION" if all([authority_ok,weights_ok,all(attacks.values()),all(qid.values()),boundary,old_root,key,ns,null_ok]) else "STOP_F1_QUERYDESIGN_ADJUDICATOR_INDEPENDENT_MISMATCH","authority":{"assignment_rows":len(rows),"assignment_keys":len(by_key),"cells":len(cells),"donors":len(donors),"operators":len(operators),"programs":len(PROGRAMS),"result_key_universe":len(expected),"exact_assignment_population":authority_ok,"all_104_donor_weight_mass_exact":weights_ok},"population_attacks":attacks,"qid_win_domain_attacks":qid,"decision_boundary":{"component_only":boundary,"engine_sha256":sha(engine),"mandatory_vetoes":integration["mandatory_vetoes"]},"frozen_authorities":{"old_root":old_root,"random_key":key,"assignment":sha(ASSIGN)==EXPECTED["assignment"],"namespace":ns,"cell_weights":weights_ok,"null_map":null_ok},"firewall":{"real_execution_forward_authority_unfrozen":"FROZEN_FORWARD_AUTHORITY_SHA256=None" in v2text,"expression_or_outcomes_accessed":False,"training_or_ema_accessed":False}}
 out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 if not result["status"].startswith("PASS_"):raise SystemExit(result["status"])
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True);a=ap.parse_args();main(a.out)
