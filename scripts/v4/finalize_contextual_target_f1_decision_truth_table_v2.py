"""Regenerate and hash the F1 decision truth-table external-review package."""
from __future__ import annotations
import argparse,csv,hashlib,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCES=[
 ("scripts/v4/contextual_target_f1_decision_v1.py","FROZEN_ARITHMETIC"),
 ("scripts/v4/contextual_target_f1_querydesign_decision_v2.py","FROZEN_POPULATION_COMPONENT"),
 ("scripts/v4/contextual_target_f1_decision_integration_v3.py","HISTORICAL_SUPERSEDED"),
 ("scripts/v4/contextual_target_f1_decision_v4.py","NEW_CURRENT_DECISION"),
 ("scripts/v4/contextual_target_f1_decision_integration_v4.py","NEW_CURRENT_INTEGRATION"),
 ("scripts/v4/test_contextual_target_f1_decision_truth_table_v2.py","NEW_ADVERSARIAL"),
 ("scripts/v4/validate_contextual_target_f1_decision_truth_table_v2.py","NEW_INDEPENDENT_VALIDATOR"),
 ("scripts/v4/finalize_contextual_target_f1_decision_truth_table_v2.py","NEW_FINALIZER"),
 ("outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_DECISION_LOGIC_PROPOSAL.md","FROZEN_AUTHORITY"),
 ("outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_CONTEXTUAL_STATISTICAL_ESTIMAND_CONTRACT.md","FROZEN_AUTHORITY"),
 ("outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_TWO_DRAW_QUERY_STATISTICAL_CONTRACT.md","FROZEN_AUTHORITY"),
 ("outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_IDENTITY_V2_CONTRACT.md","FROZEN_AUTHORITY"),
 ("outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv","FROZEN_AUTHORITY")]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def main(out):
 out.mkdir(parents=True,exist_ok=True);truth=out/"F1_FINAL_DECISION_TRUTH_TABLE_V2.json";external=out/"F1_EXTERNAL_NEGATIVE_PROGRAM_REPRODUCTION.json";adversarial=out/"F1_ISOLATED_DECISION_ADVERSARIAL.json";independent=out/"F1_DECISION_RECONCILIATION_INDEPENDENT_VALIDATION.json"
 subprocess.run([sys.executable,str(ROOT/"scripts/v4/test_contextual_target_f1_decision_truth_table_v2.py"),"--external",str(external),"--adversarial",str(adversarial)],cwd=ROOT,check=True)
 subprocess.run([sys.executable,str(ROOT/"scripts/v4/validate_contextual_target_f1_decision_truth_table_v2.py"),"--truth",str(truth),"--external",str(external),"--adversarial",str(adversarial),"--out",str(independent)],cwd=ROOT,check=True)
 snap=out/"source_snapshot";snap.mkdir(exist_ok=True);rows=[]
 for rel,role in SOURCES:
  p=ROOT/rel;rows.append({"path":rel,"sha256":sha(p),"role":role})
  if rel.startswith("scripts/"):shutil.copy2(p,snap/p.name)
 sm=out/"F1_DECISION_RECONCILIATION_SOURCE_MANIFEST.csv"
 with sm.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=("path","sha256","role"),lineterminator="\n");w.writeheader();w.writerows(rows)
 manifest=out/"F1_DECISION_RECONCILIATION_MANIFEST.csv";rootfile=out/"F1_DECISION_RECONCILIATION_MANIFEST_ROOT_SHA256.txt";files=sorted(p for p in out.rglob("*") if p.is_file() and p not in (manifest,rootfile))
 with manifest.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=("path","bytes","sha256"),lineterminator="\n");w.writeheader();w.writerows({"path":p.relative_to(out).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)} for p in files)
 rootfile.write_text(sha(manifest)+"\n",encoding="ascii");print(f"PASS_F1_DECISION_TRUTH_TABLE_RECONCILIATION_AWAITING_EXTERNAL_REVIEW {sha(manifest)}")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args();main(a.out)
