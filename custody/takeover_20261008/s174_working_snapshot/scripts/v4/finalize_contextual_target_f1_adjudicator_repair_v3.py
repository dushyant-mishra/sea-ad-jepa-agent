"""Regenerate the outcome-blind adjudicator review package from current sources."""
from __future__ import annotations
import argparse,csv,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCES=[
 ("scripts/v4/contextual_target_f1_querydesign_decision_v2.py","CHANGED","query-design component"),
 ("scripts/v4/contextual_target_f1_decision_integration_v3.py","NEW","complete-engine adapter"),
 ("scripts/v4/validate_contextual_target_f1_adjudicator_repair_v3.py","NEW","independent validator"),
 ("scripts/v4/finalize_contextual_target_f1_adjudicator_repair_v3.py","NEW","package finalizer"),
 ("scripts/v4/contextual_target_f1_decision_v1.py","FROZEN_UNCHANGED","complete F1 engine"),
 ("scripts/v4/derive_contextual_target_f1_querydesign_repair_v2.py","UNCHANGED","assignment generator"),
 ("scripts/v4/contextual_target_f1_population_firewall_v2.py","UNCHANGED","population firewall"),
 ("scripts/v4/finalize_contextual_target_f1_querydesign_repair_v2.py","UNCHANGED","historical finalizer"),
 ("outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_DECISION_LOGIC_PROPOSAL.md","FROZEN_UNCHANGED","decision authority"),
 ("outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_CONTEXTUAL_STATISTICAL_ESTIMAND_CONTRACT.md","FROZEN_UNCHANGED","estimand authority"),
 ("outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_IDENTITY_V2_CONTRACT.md","FROZEN_UNCHANGED","QID-v2 authority"),
 ("outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv","FROZEN_UNCHANGED","assignment authority")]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def run(script,args,out):subprocess.run([sys.executable,str(ROOT/script),*args,str(out)],cwd=ROOT,check=True)
def main(out):
 out.mkdir(parents=True,exist_ok=True);snap=out/"source_snapshot";snap.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);q=td/"query.json";i=td/"integration.json"
  run("scripts/v4/contextual_target_f1_querydesign_decision_v2.py",["--synthetic-out"],q);run("scripts/v4/contextual_target_f1_decision_integration_v3.py",["--out"],i)
  qj=json.loads(q.read_text());ij=json.loads(i.read_text());combined={"status":"PASS_F1_ADJUDICATOR_SYNTHETIC_ADVERSARIAL","query_design":qj,"decision_integration":ij};(out/"F1_ADJUDICATOR_SYNTHETIC_ADVERSARIAL.json").write_text(json.dumps(combined,indent=2,allow_nan=False)+"\n",encoding="utf-8")
 run("scripts/v4/validate_contextual_target_f1_adjudicator_repair_v3.py",["--out"],out/"F1_ADJUDICATOR_INDEPENDENT_VALIDATION.json")
 source_rows=[]
 for rel,status,role in SOURCES:
  p=ROOT/rel;source_rows.append({"path":rel,"sha256":sha(p),"status":status,"role":role})
  if rel.startswith("scripts/"):shutil.copy2(p,snap/p.name)
 with (out/"F1_ADJUDICATOR_REPAIR_SOURCE_MANIFEST.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=("path","sha256","status","role"),lineterminator="\n");w.writeheader();w.writerows(source_rows)
 manifest=out/"F1_ADJUDICATOR_REPAIR_MANIFEST.csv";root_file=out/"F1_ADJUDICATOR_REPAIR_MANIFEST_ROOT_SHA256.txt"
 files=sorted(p for p in out.rglob("*") if p.is_file() and p not in (manifest,root_file))
 with manifest.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=("path","bytes","sha256"),lineterminator="\n");w.writeheader();w.writerows({"path":p.relative_to(out).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)} for p in files)
 root_file.write_text(sha(manifest)+"\n",encoding="ascii")
 print(json.dumps({"status":"PASS_F1_QUERYDESIGN_ADJUDICATOR_REPAIR_AWAITING_EXTERNAL_REVIEW","manifest_sha256":sha(manifest),"files":len(files)+2}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args();main(a.out)
