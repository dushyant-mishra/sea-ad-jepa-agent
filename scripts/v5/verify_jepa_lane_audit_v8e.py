"""V8e append-only, no-promotion reviewer/CI/source-boundary guard."""
from __future__ import annotations
import json
import argparse
from pathlib import Path

MACHINE = "results/target_discovery/unified_qualification_v1/JEPA_POST_V8D_DELTA_V8E_20261027.json"
NARRATIVE = "docs/agent/JEPA_POST_V8D_DELTA_V8E_20261027.md"
AUTH = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
SHA = {465:"3b86b9467506539776e04a6470fa8f2f7363f129",
       466:"db69cd0a5777b4a23f0140de9f38980b3e5b95a9",
       467:"180b550e96b786ddfc53faa29bc81c1d3b503877",
       464:"f6ee226c146c4c31d88ce5b845449ce21758cdeb",
       457:"5dd02b0954906618202459dd89f36a62f2f02de7",
       459:"57e707149b46ca011eee096f01dc08b64aeb8f9f",
       460:"f750aa6989cabdcace7650e400a867556552d914"}
CI = {465:{"task4":40538321346,"task3":40538321445,"task2":40538321516,"integration":40538321569,"workflow_policy":40538321406},
      466:{"hostile_red":40541078808,"integration":40541078752},
      467:{"focused":40543388869,"integration":40543388748},
      464:{"mechanics":40536232358,"red":40536232091},
      457:{"receipt":40541457559,"intake":40541457592}}

def need(ok,message):
    if not ok: raise ValueError(message)

def validate(d,root):
    need(type(d) is dict and d.get("schema")=="JEPA_POST_V8D_DELTA_V8E_20261027","schema")
    need(d.get("authority")==AUTH and d.get("append_only") is True,"false authority or rewrite")
    need(d.get("prior_audit_head")=="a4c86fa83adf0cd718105807e9d254e09c989610","V8d historical audit changed")
    need(d.get("prior_successor_head")==SHA[460],"V8d successor changed")
    need(d.get("frozen_history")==["V8","V8a","V8b","V8c","V8d"],"history overwritten")
    for path in (NARRATIVE,MACHINE,"docs/agent/JEPA_POST_V8C_DELTA_V8D_20261027.md",
                 "docs/agent/JEPA_POST_V8B_DELTA_V8C_20261027.md",
                 "results/target_discovery/unified_qualification_v1/JEPA_COMPLETE_TAKEOVER_FILE_INDEX_V8A_20261027.json"):
        need((root/path).is_file(),"missing V8e or older source "+path)
    txt=(root/NARRATIVE).read_text(encoding="utf8")
    for term in ("REJECT_INCREMENTAL","ACCEPT_INCREMENTAL_WITH_LIMITATIONS","T2-D",
                 "posthoc","non-author","Windows","PRDX1",AUTH):
        need(term in txt,"V8e narrative boundary missing "+term)
    rows=d.get("evidence")
    need(type(rows) is list and len(rows)==len(SHA),"review evidence roster changed")
    need(all(type(row) is dict and type(row.get("pr")) is int for row in rows),"review PR type")
    by={row["pr"]:row for row in rows}
    need(len(by)==len(SHA) and set(by)==set(SHA),"duplicate/missing evidence")
    for pr,sha in SHA.items():
        need(by[pr].get("head")==sha,"source SHA incorrect "+str(pr))
    for pr,ci in CI.items():
        need(by[pr].get("ci")==ci,"CI run identity altered "+str(pr))
    need(by[465].get("result")=="CHATGPT_INDEPENDENT_ACCEPT_INCREMENTAL_WITH_LIMITATIONS__CUMULATIVE_TASK4_BLOCKED" and
         by[465].get("review_comment_id")==6447851888,"scope of Task4 verdict inflated")
    need(by[465].get("parent_review_sha")=="67d2336155624a8657d2ef3320c9bfff175951ee","X1 RED detached")
    need(len(by[465].get("limitations",[]))>=5,"Task4 technical limitations suppressed")
    need(by[466].get("result")=="MACHA_INDEPENDENT_REJECT_INCREMENTAL__V1_WINDOWS_NUMPY_INTC_UINTC__V2_METACLASS_STOPITERATION"
         and by[466].get("test_only") is True,"Macha independent RED suppressed")
    need(by[466].get("source_reviewed_sha")=="84b05952112ca405436ee3ccf35cc1c0df53c14d","rejected source retargeted")
    need("INDEPENDENT_REVIEW_PENDING" in by[467].get("result","") and
         by[467].get("parent_review_sha")==SHA[466],"ChatGPT encoder self-accepted")
    need("T2D" in by[464].get("result","") and "RED" in by[464]["result"],"T2-D falsely closed")
    need("NON_DECIDING_NONCAUSAL" in by[457].get("result","")
         and "not raw-source re-verification" in by[457].get("source_limit",""),"public E2G source promoted")
    g=d.get("governance",{})
    need(g.get("macha_reviews")==["467","464"] and g.get("chatgpt_reviews")==["465"],"reciprocal authorship scope changed")
    for x in ("task4_cumulative_accepted","unified_task1_cumulative_accepted",
              "production_synthetic_tasks1_2_cumulative_accepted","real_g7","stage4","real_training"):
        need(g.get(x) is False,"unearned cumulative/science acceptance "+x)
    need(d.get("source_evidence_type","").endswith("NOT_INDEPENDENT_BIOLOGICAL_AUTHENTICATION"),"source authentication inflated")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[2])
    root=parser.parse_args().repo_root
    validate(json.loads((root/MACHINE).read_text(encoding="utf8")),root)
    print("JEPA_V8E_PASS__INCREMENTAL_ACCEPT_ONLY__ENCODER_REJECT_PRESERVED__NO_SCIENCE_PROMOTION")
if __name__=="__main__":
    main()
