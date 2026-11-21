"""Static no-promotion V8d ledger validator. NOT an external trust-root verifier."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

MACHINE = "results/target_discovery/unified_qualification_v1/JEPA_POST_V8C_DELTA_V8D_20261027.json"
NARRATIVE = "docs/agent/JEPA_POST_V8C_DELTA_V8D_20261027.md"
AUTHORITY = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
PREVIOUS = ("V8", "V8a", "V8b", "V8c")
EXPECTED = {
    457: ("2fa7a4621c00e27e41c1c52afe122599d0114ae0", {40538117453:"success",40538117363:"success"}, "PUBLIC_CONTEXT_ONLY"),
    458: ("3b08081d7fb3fa99cf1459b13cbe47d5b0962547", {40516953772:"failure",40516953763:"failure"}, "13_HOSTILE_RED"),
    459: ("57e707149b46ca011eee096f01dc08b64aeb8f9f", {40518058012:"success"}, "SHORT_WRITE_RED"),
    460: ("368c34d5a919f09e118660c4ff311ba8f8188d51", {40533968217:"success",40533968150:"success"}, "V8D_UPDATE_REQUIRED"),
    461: ("495350d477a0b7ba65c13dcab5032d443f939cd5", {40519155593:"failure"}, "HOSTILE_INPUT"),
    462: ("67d2336155624a8657d2ef3320c9bfff175951ee", {40531130624:"failure"}, "TWO_RED"),
    463: ("84b05952112ca405436ee3ccf35cc1c0df53c14d", {40533382517:"success",40533382419:"success"}, "INDEPENDENT_INCREMENTAL_REVIEW_PENDING"),
    464: ("f6ee226c146c4c31d88ce5b845449ce21758cdeb", {40536232358:"success",40536232091:"failure",40536232086:"failure",40536232080:"failure",40536232098:"success"}, "T2D_UNAUTHENTICATED_SCAN_RED"),
}
PRIOR_PATHS = (
    "docs/agent/JEPA_POST_V8B_DELTA_V8C_20261027.md",
    "results/target_discovery/unified_qualification_v1/JEPA_POST_V8B_DELTA_V8C_20261027.json",
    "docs/agent/JEPA_POST_V8A_DELTA_V8B_20261027.md",
    "results/target_discovery/unified_qualification_v1/JEPA_COMPLETE_TAKEOVER_FILE_INDEX_V8A_20261027.json",
    "docs/agent/JEPA_NO_REPEAT_DELTA_V8_20261027.md",
)

def require(ok, why):
    if not ok:
        raise ValueError(why)

def validate(data, root):
    require(type(data) is dict and data.get("schema") == "JEPA_POST_V8C_DELTA_V8D_20261027", "bad V8d schema")
    require(data.get("authority") == AUTHORITY and data.get("append_only") is True, "V8d authority or history rewritten")
    require(data.get("prior_audit_head") == "1a6e59d338906fa9da1cbbc4b93c918349a4a3c5", "V8c SHA rewritten")
    require(data.get("prior_successor_head") == EXPECTED[460][0], "former successor SHA rewritten")
    require(data.get("snapshots_frozen") == list(PREVIOUS), "prior snapshots removed")
    require(data.get("stage4_authorized") is False and data.get("training_authorized") is False
            and data.get("source_authenticated_biology") is False, "unearned Stage4/source/real training promoted")
    for path in PRIOR_PATHS + (NARRATIVE,):
        require((root / path).is_file(), "prior audit or V8d narrative file absent: " + path)
    narrative = (root / NARRATIVE).read_text(encoding="utf-8")
    for token in ("T2-D", "#457", "#458", "#459", "#463", "#464", "149", "source-author-reported", AUTHORITY):
        require(token in narrative, "V8d narrative missing science/reviewer boundary: " + token)
    rows = data.get("live_ledger")
    require(type(rows) is list and len(rows) == len(EXPECTED), "head roster changed")
    require(all(type(row) is dict and type(row.get("pr")) is int for row in rows), "bad PR identity type")
    require({row["pr"] for row in rows} == set(EXPECTED), "duplicate or missing PR")
    for row in rows:
        sha, runs, marker = EXPECTED[row["pr"]]
        require(row.get("head") == sha and re.fullmatch(r"[0-9a-f]{40}",sha), "exact source head tampered")
        require(marker in row.get("status",""), "authorization state changed")
        ci = row.get("ci")
        require(type(ci) is list and len(ci) == len(runs), "CI roster altered")
        require({x.get("run"):x.get("conclusion") for x in ci} == runs, "CI identity/result altered")
        require(all(type(x.get("suite")) is str and x["suite"] for x in ci), "lost CI scope")
    a = {row["pr"]:row for row in rows}
    require("NOT independently re-verified" in a[457]["evidence"], "Stage75 source self-report promoted")
    require("No independent original-ATAC" in a[457]["caveats"], "genome-build qualification forged")
    require("T2D_UNAUTHENTICATED_SCAN_RED" in a[464]["status"], "T2-D must remain RED")
    rounds = data.get("audit_rounds")
    require(type(rounds) is list and len(rounds) >= 3, "independent audit rounds missing")
    require(all(type(x.get("finding")) is str for x in rounds), "audit findings absent")
    limitations = data.get("material_source_limitations")
    require(type(limitations) is list and len(limitations) >= 3, "source boundaries lost")
    require(any("T2-D" in v and "without" in v for v in limitations), "T2-D false acceptance")
    require(any("G7" in v and "no genuine" in v for v in limitations), "G7 source invented")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[2])
    args=p.parse_args()
    validate(json.loads((args.repo_root / MACHINE).read_text(encoding="utf-8")),args.repo_root)
    print("JEPA_V8D_STATIC_AUDIT_PASS__HOSTILE_RED_AND_SOURCE_UNCERTAINTY_PRESERVED__NO_AUTHORITY")

if __name__ == "__main__":
    main()
