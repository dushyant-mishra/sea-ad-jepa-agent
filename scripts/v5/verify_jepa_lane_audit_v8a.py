"""Append-only V8a audit-delta verifier. Static provenance, NEVER issuer authority."""
from __future__ import annotations
import json
from pathlib import Path

from scripts.v5.verify_jepa_lane_audit_v8 import TERMINAL, validate_snapshot

BASE="results/target_discovery/unified_qualification_v1/JEPA_LANE_AUDIT_SNAPSHOT_V8_20261027.json"
DELTA="results/target_discovery/unified_qualification_v1/JEPA_POST_V8_SNAPSHOT_DELTA_V8A_20261027.json"
INDEX="results/target_discovery/unified_qualification_v1/JEPA_COMPLETE_TAKEOVER_FILE_INDEX_V8A_20261027.json"
EXPECTED={
    457:("cd86187ec03092bdc9ebb17e36046ac8853b4fd1","E2G_SEVEN_PUBLIC_SOURCES_PROVISIONAL_COVERAGE_ONLY__RESULT_RECEIPT_CI_RED"),
    458:("3b08081d7fb3fa99cf1459b13cbe47d5b0962547","PS_TASKS1_2_SECOND_WAVE_INDEPENDENT_RED_13_TESTS__CUMULATIVE_REVIEW_BLOCKED"),
    459:("57e707149b46ca011eee096f01dc08b64aeb8f9f","TASK4_X1_WRITE_AHEAD_INTENT_CANDIDATE_CI_GREEN__INDEPENDENT_REVIEW_PENDING__X3_UNQUALIFIED"),
}
RED={457:40517601114,458:40516953772}
GREEN={459:40518058012}
SOURCE_ROLES={
    457:"REGULATORY_ANNOTATION_NOT_CAUSALITY",
    458:"TESTS_ONLY_CANDIDATE_NOT_ACCEPTED",
    459:"MACHA_AUTHORED_TASK4_REPAIR_NOT_CUMULATIVELY_ACCEPTED",
}


def refuse(test: bool, msg: str) -> None:
    if not test:
        raise ValueError(msg)


def validate_delta(doc: object, base: object) -> None:
    validate_snapshot(base)
    refuse(type(doc) is dict and doc.get("schema")=="JEPA_AUDIT_V8A_POST_SNAPSHOT_DELTA_20261027","incorrect V8a delta schema")
    refuse(doc.get("authority")==TERMINAL and doc.get("original_v8_remains_immutable_historical_event") is True,"old audit overwritten / authorization altered")
    refuse(doc.get("supersedes_active_navigation_only")=="JEPA_LANE_AUDIT_SNAPSHOT_V8_20261027.json","V8a has invalid supersession")
    records=doc.get("records")
    refuse(type(records) is list and len(records)==3,"V8a missing or extra new PR")
    observed={}
    for r in records:
        refuse(type(r) is dict and type(r.get("pr")) is int and r["pr"] not in observed,"duplicate or invalid V8a PR")
        n=r["pr"]
        refuse(n in EXPECTED and (r.get("sha"),r.get("status"))==EXPECTED[n],"PR identity or verdict changed")
        refuse(r.get("url")==f"https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/{n}","mismatched PR URL")
        refuse(r.get("source_role")==SOURCE_ROLES[n],"source or reviewer role escalated")
        refuse(type(r.get("ci_green",[])) is list and type(r.get("ci_red",[])) is list,"missing CI evidence")
        observed[n]=r
    refuse(set(observed)==set(EXPECTED),"V8a new evidence missing")
    for n,rid in RED.items():
        refuse(rid in observed[n]["ci_red"],f"RED source for PR{n} deleted")
    for n,gid in GREEN.items():
        refuse(gid in observed[n]["ci_green"],f"candidate GREEN source for PR{n} deleted")
        refuse("INDEPENDENT_REVIEW_PENDING" in observed[n]["status"],"Task4 self-audit promoted")
    changes=doc.get("clear_new_work")
    refuse(type(changes) is dict and "13_HOSTILE_RED" in changes.get("ps_task1_2",""),"PS new RED hidden")
    refuse("INDEPENDENT_ADVERSARIAL_RECHECK_NEXT" in changes.get("task4",""),"X1 independence dropped")
    refuse("STILL_NOT_QUALIFIED"==changes.get("g7"),"unqualified G7 falsely passed")
    refuse("NOT_TF_BINDING_OR_CAUSAL" in changes.get("e2g",""),"E2G regulatory reference falsely promoted")
    refuse(doc.get("cannot_upgrade_from_ci") is True,"fixture CI granted authority")
    refuse(set(doc.get("preserved_old_red",[])) >= {448,455,452,449,442,450},"old RED lineage erased")
    refuse(doc.get("handoff_clean_successor_pr")==460,"clean handoff PR altered")
    scores=doc.get("new_red_ci_counts",{})
    refuse(scores.get("ps_tasks_1_2",{}).get("failed")==13,"PS 13 fresh RED count erased")
    refuse(scores.get("e2g_result_receipt",{}).get("test_collection_error") is True,"E2G result receipt still RED")
    refuse(doc.get("task4_author_green_counts",{}).get("windows_skipped")==7,"Windows skips hidden")



def validate_index(doc: object) -> None:
    refuse(type(doc) is dict and doc.get("schema")=="JEPA_COMPLETE_TAKEOVER_FILE_INDEX_V8A_20261027","wrong complete takeover index schema")
    refuse(doc.get("authority")==TERMINAL,"complete file index changed authority")
    refuse(doc.get("clean_successor_pr")==460,"clean successor pointer changed")
    refuse(doc.get("raw_binary_policy","").startswith("Large ZIP/NPZ/PT artifacts remain external"),"large private/raw artifact policy changed")
    cats=doc.get("categories")
    refuse(type(cats) is dict,"takeover categories missing")
    required={"historical_audit_docs","external_context_and_historical_imports","plans_and_specs","machine_results","executable_scripts","tests","workflows","clean_successor_files"}
    refuse(set(cats)==required,"complete file-index categories changed")
    counts=doc.get("counts")
    refuse(type(counts) is dict and set(counts)==required,"file-index counts missing")
    for key in required:
        refuse(type(cats[key]) is list and counts[key]==len(cats[key]) and counts[key]>0,"file-index count mismatch: "+key)
        refuse(len(cats[key])==len(set(cats[key])),"duplicate path in file-index category: "+key)
    docs=set(cats["historical_audit_docs"])
    results=set(cats["machine_results"])
    scripts=set(cats["executable_scripts"])
    tests=set(cats["tests"])
    for must in (
        "docs/agent/JEPA_LANE_AUDIT_SNAPSHOT_V8_20261027.md",
        "docs/agent/JEPA_POST_V8_SNAPSHOT_DELTA_V8A_20261027.md",
        "docs/agent/JEPA_NO_REPEAT_DELTA_V8_20261027.md",
        "docs/agent/JEPA_LOCAL_ATTACHMENT_CUSTODY_RECONCILIATION_V8_20261027.csv",
        "docs/agent/JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.md",
        "docs/agent/JEPA_GENE_IDENTITY_RECLASSIFICATION_AUDIT_20261013.md",
    ):
        refuse(must in docs,"critical historical audit missing from complete index: "+must)
    for must in (
        "results/target_discovery/unified_qualification_v1/JEPA_LANE_AUDIT_SNAPSHOT_V8_20261027.json",
        "results/target_discovery/unified_qualification_v1/JEPA_POST_V8_SNAPSHOT_DELTA_V8A_20261027.json",
    ):
        refuse(must in results,"critical machine evidence missing from complete index: "+must)
    refuse("scripts/v5/verify_jepa_lane_audit_v8.py" in scripts and "scripts/v5/verify_jepa_lane_audit_v8a.py" in scripts,"audit validators not indexed")
    refuse("tests/v5/test_verify_jepa_lane_audit_v8.py" in tests and "tests/v5/test_verify_jepa_lane_audit_v8a.py" in tests,"audit hostile tests not indexed")
    latest=doc.get("latest_post_v8_prs")
    refuse(type(latest) is list and {x.get("pr") for x in latest}=={457,458,459,460},"latest post-V8 PR map incomplete")
    by={x["pr"]:x for x in latest}
    refuse(by[458]["head"]=="3b08081d7fb3fa99cf1459b13cbe47d5b0962547","PS second-wave RED head changed")
    refuse(by[459]["head"]=="57e707149b46ca011eee096f01dc08b64aeb8f9f","Task4 X1 candidate head changed")
    refuse(by[460]["head"]=="68afef03780a25f7778802ebe3eb53cb0463fe1a","clean successor head changed")
    refuse(doc.get("reviewer_independence","").startswith("Implementation authors cannot cumulatively self-accept"),"independence rule removed")

def main() -> None:
    root=Path(__file__).resolve().parents[2]
    base=json.loads((root/BASE).read_text(encoding="utf-8"))
    delta=json.loads((root/DELTA).read_text(encoding="utf-8"))
    index=json.loads((root/INDEX).read_text(encoding="utf-8"))
    validate_delta(delta,base)
    validate_index(index)
    print("JEPA_V8A_DELTA_STATIC_PASS__RED_PRESERVED__NO_NEW_AUTHORITY")


if __name__=="__main__":
    main()
