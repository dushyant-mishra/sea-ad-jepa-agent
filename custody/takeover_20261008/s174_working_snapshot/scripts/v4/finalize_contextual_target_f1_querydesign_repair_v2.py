#!/usr/bin/env python3
"""Create the file manifest and external root anchor for the pre-result F1 repair."""
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901"
MAN=OUT/"F1_QUERYDESIGN_REPAIR_MANIFEST.csv";ANCHOR=OUT/"F1_QUERYDESIGN_REPAIR_MANIFEST_ROOT_SHA256.txt"
SCRIPTS=[ROOT/f"scripts/v4/{x}" for x in (
 "derive_contextual_target_f1_querydesign_repair_v2.py","validate_contextual_target_f1_querydesign_repair_v2.py",
 "contextual_target_f1_querydesign_decision_v2.py","contextual_target_f1_population_firewall_v2.py",
 "finalize_contextual_target_f1_querydesign_repair_v2.py")]
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def main():
 files=sorted([p for p in OUT.iterdir() if p.is_file() and p not in (MAN,ANCHOR)]+SCRIPTS,key=lambda p:str(p).lower())
 tmp=MAN.with_suffix(".csv.tmp")
 with tmp.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=("path","bytes","sha256","result_state"),lineterminator="\n");w.writeheader()
  for p in files:w.writerow({"path":str(p.relative_to(ROOT)).replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha(p),"result_state":"PRE_RESULT_FROZEN"})
 tmp.replace(MAN); root=sha(MAN); at=ANCHOR.with_suffix(".txt.tmp");at.write_text(root+"\n",encoding="ascii");at.replace(ANCHOR)
 print(json.dumps({"status":"PASS","manifest_rows":len(files),"manifest_sha256":root}))
if __name__=="__main__":main()
