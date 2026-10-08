"""Fail-atomic publication for the synthetic-only F1 15C integration package."""
from __future__ import annotations
import argparse,csv,hashlib,json,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TOP=("F1_15C_INTEGRATION_AUTHORITY.json","F1_15C_NUISANCE_SEMANTIC_PREFLIGHT.json","F1_15C_NUISANCE_INTEGRATION_CONTRACT.md","F1_15C_SELECTED_DESIGN_REVERIFICATION.json","F1_15C_SYNTHETIC_BASELINE.json","F1_15C_NUISANCE_ADVERSARIAL.json","F1_15C_FULL_DECISION_REGRESSION.json","F1_15C_INDEPENDENT_VALIDATION.json","F1_15C_SOURCE_MANIFEST.csv","F1_15C_MULTIAGENT.md","F1_15C_MANIFEST.csv","F1_15C_EXTERNAL_REVIEW_HANDOFF.md")
SOURCES=("scripts/v4/contextual_target_f1_hc3_15c_adapter_v1.py","scripts/v4/run_contextual_target_f1_hc3_15c_v1.py","scripts/v4/validate_contextual_target_f1_hc3_15c_v1.py","scripts/v4/finalize_contextual_target_f1_hc3_15c_v1.py","tests/v4/test_contextual_target_f1_hc3_15c_integration_v1.py")
UNCHANGED=("scripts/v4/contextual_target_f1_decision_v4.py","scripts/v4/contextual_target_f1_decision_integration_v4.py","scripts/v4/contextual_target_f1_decision_v1.py","scripts/v4/contextual_target_f1_querydesign_decision_v2.py")
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def status(path,key,expected):return json.loads(path.read_text())[key]==expected
def run(staging,final):
 if final.exists():raise SystemExit("final directory already exists")
 required={"F1_15C_INTEGRATION_AUTHORITY.json":("status","PASS_F1_15C_AUTHORITY_VERIFIED"),"F1_15C_SELECTED_DESIGN_REVERIFICATION.json":("status","PASS_F1_15C_SELECTED_DESIGN_REVERIFIED"),"F1_15C_SYNTHETIC_BASELINE.json":("status","PASS_F1_15C_SYNTHETIC_ALL_PASS"),"F1_15C_NUISANCE_ADVERSARIAL.json":("status","PASS_F1_15C_NUISANCE_ADVERSARIAL"),"F1_15C_FULL_DECISION_REGRESSION.json":("status","PASS_F1_15C_FULL_DECISION_REGRESSION"),"F1_15C_INDEPENDENT_VALIDATION.json":("status","PASS_F1_15C_INDEPENDENT_VALIDATION")}
 if not all(status(staging/name,*rule) for name,rule in required.items()):raise SystemExit("STOP_F1_15C_INDEPENDENT_MISMATCH")
 snap=staging/"source_snapshot";snap.mkdir(exist_ok=True)
 source_rows=[]
 for rel in SOURCES:
  src=ROOT/rel;dst=snap/src.name;shutil.copy2(src,dst);source_rows.append({"role":"new_15c_snapshot","project_path":rel,"snapshot_path":f"source_snapshot/{dst.name}","bytes":dst.stat().st_size,"sha256":sha(dst)})
 for rel in UNCHANGED:
  src=ROOT/rel;source_rows.append({"role":"unchanged_reviewed_authority","project_path":rel,"snapshot_path":"NOT_COPIED_HASH_BOUND","bytes":src.stat().st_size,"sha256":sha(src)})
 with (staging/"F1_15C_SOURCE_MANIFEST.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=source_rows[0]);w.writeheader();w.writerows(source_rows)
 handoff="# F1 15C External Review Handoff\n\nTerminal: `PASS_F1_HC3_15C_DECISION_INTEGRATION_AWAITING_EXTERNAL_REVIEW`\n\nThe frozen current-104 nuisance design `(5,0,4)` is additively bound to the unchanged F1 decision engine. Synthetic baseline, actual authority-mutation attacks, all prior 14 decision cases, legal/population identity tests, and an independent HC3 implementation pass. The adapter is donor-keyed and rejects positional arrays. The exact frozen input design SHA is distinguished from the effective matrix produced by the pre-existing per-column centering rule.\n\nNo expression, model/checkpoint tensor, real outcome, training, optimizer, or EMA was accessed. Real reader/forward authority remains unset and real execution fails closed. External review is mandatory before any next freeze.\n"
 (staging/"F1_15C_EXTERNAL_REVIEW_HANDOFF.md").write_text(handoff,encoding="utf-8")
 manifest_paths=[p for p in staging.rglob("*") if p.is_file() and p.name!="F1_15C_MANIFEST.csv"]
 rows=[]
 for p in sorted(manifest_paths,key=lambda q:q.relative_to(staging).as_posix()):rows.append({"relative_path":p.relative_to(staging).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)})
 with (staging/"F1_15C_MANIFEST.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 actual={p.name for p in staging.iterdir() if p.is_file()}
 if actual!=set(TOP) or {p.name for p in snap.iterdir()}!={Path(p).name for p in SOURCES}:raise SystemExit("publication inventory mismatch")
 final.parent.mkdir(parents=True,exist_ok=True);staging.rename(final)
 anchor=ROOT/"docs/agent/provenance-anchors/F1_HC3_15C_DECISION_INTEGRATION_ROOT_20260902.json";anchor.parent.mkdir(parents=True,exist_ok=True)
 anchor.write_text(json.dumps({"schema":"f1-15c-external-root-v1","package":final.resolve().relative_to(ROOT).as_posix(),"manifest_sha256":sha(final/"F1_15C_MANIFEST.csv"),"handoff_sha256":sha(final/"F1_15C_EXTERNAL_REVIEW_HANDOFF.md"),"terminal":"PASS_F1_HC3_15C_DECISION_INTEGRATION_AWAITING_EXTERNAL_REVIEW"},indent=2)+"\n")
 print(json.dumps({"status":"PASS_F1_HC3_15C_DECISION_INTEGRATION_AWAITING_EXTERNAL_REVIEW","manifest_sha256":sha(final/"F1_15C_MANIFEST.csv"),"anchor_sha256":sha(anchor)}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--staging",type=Path,required=True);p.add_argument("--final",type=Path,required=True);a=p.parse_args();run(a.staging,a.final)
