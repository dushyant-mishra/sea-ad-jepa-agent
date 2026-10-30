"""Static V8b delta/supplement guard. No remote authority verification."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

DELTA="results/target_discovery/unified_qualification_v1/JEPA_POST_V8A_DELTA_V8B_20261027.json"
SUP="results/target_discovery/unified_qualification_v1/JEPA_TAKEOVER_SUPPLEMENT_V8B_20261027.json"
TERMINAL="TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
HEX40=re.compile(r"^[a-f0-9]{40}$")
EXPECTED={
 "457":"17e7cc8818d27222fac5c0a3e91677640ea81153",
 "458":"3b08081d7fb3fa99cf1459b13cbe47d5b0962547",
 "459":"57e707149b46ca011eee096f01dc08b64aeb8f9f",
 "460":"a081f8d719372b14ab95120f4f7ba290a0940e4a",
}
CLASS={
 "457":"CURRENT_CI_GREEN__PUBLIC_REFERENCE_CONTEXT_ONLY__NO_CAUSAL_OR_TARGET_AUTHORITY",
 "458":"CURRENT_13_HOSTILE_RED__PS_TASK1_2_ACCEPTANCE_BLOCKED",
 "459":"AUTHOR_CANDIDATE_GREEN__INDEPENDENT_TASK4_REVIEW_PENDING__X3_OPEN",
 "460":"ACTIVE_CLEAN_SUCCESSOR__NAVIGATION_ONLY__NO_SCIENTIFIC_AUTHORITY",
}
def require(x,msg):
    if not x: raise ValueError(msg)

def validate(delta,sup,root):
    require(delta.get("schema")=="JEPA_POST_V8A_DELTA_V8B_20261027","wrong delta schema")
    require(delta.get("authority")==TERMINAL,"authority promoted")
    rows=delta.get("changes")
    require(type(rows) is list and len(rows)==4,"V8b active roster changed")
    got={str(x["pr"]):x["head"] for x in rows}
    require(got==EXPECTED,"V8b active heads changed")
    for row in rows:
        require(HEX40.fullmatch(row["head"]) is not None,"bad active SHA")
        require(type(row.get("ci")) is list and row["ci"],"CI identity missing")
    by={str(x["pr"]):x["classification"] for x in rows}
    require("NONAUTHORIZING" in by["457"],"E2G context promoted")
    require("13_HOSTILE_RED" in by["458"],"PS hostile RED lost")
    require("INDEPENDENT_CUMULATIVE_REVIEW_PENDING" in by["459"],"Task4 self-accepted")
    require("NO_SCIENTIFIC_AUTHORITY" in by["460"],"handoff branch promoted")
    require(sup.get("schema")=="JEPA_TAKEOVER_SUPPLEMENT_V8B_20261027","wrong supplement schema")
    require(sup.get("authority")==TERMINAL,"supplement authority promoted")
    require(sup.get("active_heads")==EXPECTED,"supplement active heads disagree")
    require(sup.get("exact_classification")==CLASS,"supplement classification altered")
    prior=sup.get("required_prior_files")
    require(type(prior) is list and len(prior)>=4,"prior audit sources lost")
    for rel in prior:
        require((root/rel).is_file(),"missing prior audit source "+rel)
    for rel in sup.get("v8b_files",[]):
        # workflow/test/script can be absent only while authoring this commit; once in CI all must exist.
        require((root/rel).is_file(),"missing V8b takeover file "+rel)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[2])
    args=p.parse_args()
    root=args.repo_root
    validate(json.loads((root/DELTA).read_text()),json.loads((root/SUP).read_text()),root)
    print("JEPA_V8B_DELTA_PASS__ACTIVE_HEAD_DRIFT_CAPTURED__NO_AUTHORITY_ISSUED")
if __name__=="__main__": main()
