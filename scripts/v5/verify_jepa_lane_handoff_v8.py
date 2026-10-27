"""Read-only successor V8 machine pointer guard. Not a source/issuer verifier."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

POINTER="results/target_discovery/unified_qualification_v1/JEPA_SUCCESSOR_POINTER_V8_20261027.json"
TERMINAL="TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
HEX40=re.compile(r"^[a-f0-9]{40}$")
EXPECTED_STATES={
 "task4":"PR459_X1_NEW_CANDIDATE_GREEN__INDEPENDENT_REVIEW_PENDING__X3_CROSS_OS_UNQUALIFIED",
 "real_g7":"UNQUALIFIED__PHYSICAL_MEASUREMENT_AND_DEPTH_PROVENANCE",
 "ps_task1":"PR458_NEW_13_HOSTILE_RED__CUMULATIVE_ACCEPTANCE_PENDING",
 "ps_task2":"PR458_NEW_13_HOSTILE_RED__CUMULATIVE_ACCEPTANCE_PENDING",
 "ps_task3":"OLD_DEPENDENCY_FIXTURE_ACCEPT_WITH_LIMITS__REVIEW_PENDING",
 "task5":"BRIDGE_INCREMENT_ACCEPTED_ONLY__FULL_A7_PENDING",
 "tasks6_8":"FIXTURE_ONLY_NONE_AND_ABSTENTION",
 "regulatory_e2g":"PR457_CURRENT_CI_GREEN__PUBLIC_REFERENCE_CONTEXT_ONLY__NOT_CAUSAL_BIOLOGY",
}


def require(pred, message):
    if not pred:
        raise ValueError(message)


def validate_pointer(doc, root):
    require(type(doc) is dict and doc.get("schema")=="JEPA_SUCCESSOR_HANDOFF_POINTER_V8_20261027","wrong V8 pointer schema")
    require(doc.get("authority")==TERMINAL and doc.get("no_scientific_authority") is True, "science/authority incorrectly promoted")
    require(doc.get("external_large_artifact_copy_to_git") is False, "raw external data custody policy changed")
    require(doc.get("active")==EXPECTED_STATES, "Task4, E3, PS acceptance, A7 or none gate altered")
    require(doc.get("frozen_unified_task3")=="117dd51dea827e734b299982da93991b934bdc8f", "frozen Task3 identity changed")
    audit=doc.get("master_audit")
    require(type(audit) is dict and audit.get("pr")==322, "master audit PR pointer invalid")
    require(audit.get("branch")=="science/jepa-robust-pipeline-post-jepa-anything-audit-20261013", "audit branch changed")
    require(type(audit.get("exact_head_at_pointer")) is str and HEX40.fullmatch(audit["exact_head_at_pointer"]), "audit exact head invalid")
    require(audit.get("ci_status_at_pointer") in ("QUEUED__NOT_YET_VERIFIED","EXACT_HEAD_CI_GREEN","EXACT_HEAD_V8_V8A_V8B_ALL_GREEN"),"unqualified audit CI state")
    for field in ("audit_doc","audit_machine","audit_no_repeat","asset_custody","validator","post_v8a_doc","post_v8a_machine","complete_takeover_index","post_v8b_doc","post_v8b_machine","v8b_supplement"):
        value=audit.get(field)
        require(type(value) is str and value.startswith(("docs/agent/","results/target_discovery/","scripts/v5/")),f"missing canonical audit file pointer {field}")
    handoff=doc.get("handoff")
    require(type(handoff) is dict and handoff.get("pr")==460 and handoff.get("older_versions_historical") is True,"handoff provenance invalid")
    require(handoff.get("branch")=="handoff/jepa-v8-clean-successor-from-audit-20261027","handoff branch changed")
    require(type(handoff.get("doc_intro_commit")) is str and HEX40.fullmatch(handoff["doc_intro_commit"]),"first V8 handoff commit invalid")
    handoff_path=handoff.get("doc")
    require(handoff_path=="docs/agent/JEPA_SUCCESSOR_HANDOFF_V8_20261027.md","handoff file changed")
    first=handoff.get("first_session")
    require(first=="docs/agent/JEPA_SUCCESSOR_FIRST_SESSION_V8B_20261027.md","first-session handoff missing")
    require((root/first).is_file(),"first-session handoff file missing")
    text=(root/handoff_path).read_text(encoding="utf-8") + "\n" + (root/first).read_text(encoding="utf-8")
    for item in ["TARGET_WINNER_NONE","#322","#451","Task4","X1","X3","G7","Tasks6–8","#456"]:
        require(item in text,"required unresolved gate/source not in successor handoff: "+item)
    order=doc.get("read_order")
    require(type(order) is list and len(order)==9 and len(set(order))==9 and order[0]==first and order[1]==handoff_path, "incorrect no-repeat read order")
    require(doc.get("next_owner",{}).get("independent_non_author"),"independent acceptance role missing")
    require(doc.get("next_owner",{}).get("chatgpt"),"independent new X1 review role missing")
    require(audit.get("post_v8a_machine")=="results/target_discovery/unified_qualification_v1/JEPA_POST_V8_SNAPSHOT_DELTA_V8A_20261027.json","new 13 PS REDs or X1 candidate index missing")
    require(audit.get("post_v8a_doc")=="docs/agent/JEPA_POST_V8_SNAPSHOT_DELTA_V8A_20261027.md","V8a human reviewer handoff missing")
    require("PR322:docs/agent/JEPA_POST_V8_SNAPSHOT_DELTA_V8A_20261027.md" in order,"read order omits latest new defects")
    require(audit.get("complete_takeover_index")=="results/target_discovery/unified_qualification_v1/JEPA_COMPLETE_TAKEOVER_FILE_INDEX_V8A_20261027.json","complete audit/script/result file index missing")
    require("PR322:results/target_discovery/unified_qualification_v1/JEPA_COMPLETE_TAKEOVER_FILE_INDEX_V8A_20261027.json" in order,"read order omits complete custody index")
    require(audit.get("post_v8b_doc")=="docs/agent/JEPA_POST_V8A_DELTA_V8B_20261027.md","V8b human drift delta missing")
    require(audit.get("post_v8b_machine")=="results/target_discovery/unified_qualification_v1/JEPA_POST_V8A_DELTA_V8B_20261027.json","V8b machine drift delta missing")
    require(audit.get("v8b_supplement")=="results/target_discovery/unified_qualification_v1/JEPA_TAKEOVER_SUPPLEMENT_V8B_20261027.json","V8b supplement missing")
    require(audit.get("post_v8b_ci_run_id")==40530745175 and audit.get("post_v8b_static_tests_passed")==11,"V8b exact-head CI evidence mismatch")
    require(audit.get("audit_v8_ci_run_id")==40530744438 and audit.get("audit_v8_hostile_tests_passed")==28,"V8 exact-head CI evidence mismatch")
    require(audit.get("post_v8a_ci_run_id")==40530744455 and audit.get("post_v8a_qualified_static_tests_passed")==51,"V8a exact-head CI evidence mismatch")
    require("PR322:docs/agent/JEPA_POST_V8A_DELTA_V8B_20261027.md" in order,"read order omits latest V8b drift delta")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument("--pointer",type=Path,default=None)
    args=p.parse_args()
    validate_pointer(json.loads((args.pointer or args.repo_root/POINTER).read_text()),args.repo_root)
    print("JEPA_V8_SUCCESSOR_POINTER_PASS__NO_SCIENTIFIC_AUTHORITY_ISSUED")


if __name__=="__main__":
    main()
