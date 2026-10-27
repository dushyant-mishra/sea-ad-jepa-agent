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
 "task4":"PR465_INDEPENDENT_ACCEPT_INCREMENTAL_SHORT_IO_ONLY__CUMULATIVE_TASK4_BLOCKED__X3_EXTERNAL_ISSUER_UNQUALIFIED",
 "unified_task1":"PR466_MACHA_REJECT_463__PR467_AUTHOR_GREEN_MACHA_REVIEW_PENDING",
 "real_g7":"UNQUALIFIED__PHYSICAL_MEASUREMENT_AND_DEPTH_PROVENANCE",
 "ps_task1":"PR458_13_OLD_RED__PR464_12_MECHANICS_GREEN_T2D_RED__CUMULATIVE_PENDING",
 "ps_task2":"PR458_13_OLD_RED__PR464_12_MECHANICS_GREEN_T2D_RED__CUMULATIVE_PENDING",
 "ps_task3":"OLD_DEPENDENCY_FIXTURE_ACCEPT_WITH_LIMITS__REVIEW_PENDING",
 "task5":"BRIDGE_INCREMENT_ACCEPTED_ONLY__FULL_A7_PENDING",
 "tasks6_8":"FIXTURE_ONLY_NONE_AND_ABSTENTION",
 "regulatory_e2g":"PR457_5DD_POSTHOC_TSS_GEOMETRY__NO_TF_CAUSALITY_OR_SOURCE_AUTHORITY",
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
    require(audit.get("ci_status_at_pointer") in ("QUEUED__NOT_YET_VERIFIED","EXACT_HEAD_CI_GREEN","EXACT_HEAD_V8_V8A_V8B_ALL_GREEN","EXACT_HEAD_V8_TO_V8C_ALL_GREEN","EXACT_HEAD_V8_TO_V8D_ALL_GREEN","EXACT_HEAD_V8_TO_V8E_ALL_GREEN"),"unqualified audit CI state")
    for field in ("audit_doc","audit_machine","audit_no_repeat","asset_custody","validator","post_v8a_doc","post_v8a_machine","complete_takeover_index","post_v8b_doc","post_v8b_machine","v8b_supplement","post_v8c_doc","post_v8c_machine","post_v8d_doc","post_v8d_machine","post_v8e_doc","post_v8e_machine"):
        value=audit.get(field)
        require(type(value) is str and value.startswith(("docs/agent/","results/target_discovery/","scripts/v5/")),f"missing canonical audit file pointer {field}")
    handoff=doc.get("handoff")
    require(type(handoff) is dict and handoff.get("pr")==460 and handoff.get("older_versions_historical") is True,"handoff provenance invalid")
    require(handoff.get("branch")=="handoff/jepa-v8-clean-successor-from-audit-20261027","handoff branch changed")
    require(type(handoff.get("doc_intro_commit")) is str and HEX40.fullmatch(handoff["doc_intro_commit"]),"first V8 handoff commit invalid")
    handoff_path=handoff.get("doc")
    require(handoff_path=="docs/agent/JEPA_SUCCESSOR_HANDOFF_V8_20261027.md","handoff file changed")
    first=handoff.get("first_session")
    require(first=="docs/agent/JEPA_SUCCESSOR_FIRST_SESSION_V8E_20261027.md","first-session handoff missing")
    require((root/first).is_file(),"first-session handoff file missing")
    text=(root/handoff_path).read_text(encoding="utf-8") + "\n" + (root/first).read_text(encoding="utf-8")
    for item in ["TARGET_WINNER_NONE","#322","#451","Task4","X1","X3","G7","Tasks6–8","#456"]:
        require(item in text,"required unresolved gate/source not in successor handoff: "+item)
    order=doc.get("read_order")
    require(type(order) is list and len(order)==15 and len(set(order))==15 and order[0]==first and order[1]==handoff["previous_first_session"] and order[2:4]==handoff["older_first_sessions"] and order[4]==handoff_path, "incorrect no-repeat read order")
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
    require("PR322:docs/agent/JEPA_POST_V8A_DELTA_V8B_20261027.md" in order,"read order omits V8b drift delta")
    require(handoff.get("previous_first_session")=="docs/agent/JEPA_SUCCESSOR_FIRST_SESSION_V8D_20261027.md" and handoff.get("older_first_sessions")==["docs/agent/JEPA_SUCCESSOR_FIRST_SESSION_V8C_20261027.md","docs/agent/JEPA_SUCCESSOR_FIRST_SESSION_V8B_20261027.md"],"V8b first session must remain in chronology")
    require((root/handoff["previous_first_session"]).is_file() and all((root/p).is_file() for p in handoff["older_first_sessions"]),"old first-session source missing")
    require(audit.get("post_v8c_doc")=="docs/agent/JEPA_POST_V8B_DELTA_V8C_20261027.md","V8c non-promoting review narrative missing")
    require(audit.get("post_v8c_machine")=="results/target_discovery/unified_qualification_v1/JEPA_POST_V8B_DELTA_V8C_20261027.json","V8c machine custody missing")
    require(audit.get("post_v8c_ci_run_id")==40532989787 and audit.get("post_v8c_static_tests_passed")==16,"V8c exact-head audit CI evidence mismatch")
    require(audit.get("exact_head_at_pointer")=="a271164554076d0acda3bd0cf0b1bf957c0fdfd3","audit head not pinned to qualified V8e")
    require(audit.get("post_v8e_doc")=="docs/agent/JEPA_POST_V8D_DELTA_V8E_20261027.md","V8e review narrative missing")
    require(audit.get("post_v8e_machine")=="results/target_discovery/unified_qualification_v1/JEPA_POST_V8D_DELTA_V8E_20261027.json","V8e machine delta missing")
    require(audit.get("post_v8e_ci_run_id")==40544360278 and audit.get("post_v8e_static_tests_passed")==22
            and audit.get("post_v8e_total_workflows_green")==15,"V8e CI evidence not qualified")
    require("PR322:docs/agent/JEPA_POST_V8D_DELTA_V8E_20261027.md" in order
            and "PR322:results/target_discovery/unified_qualification_v1/JEPA_POST_V8D_DELTA_V8E_20261027.json" in order,"latest review audit missing")
    require(audit.get("post_v8d_doc")=="docs/agent/JEPA_POST_V8C_DELTA_V8D_20261027.md","V8d source review missing")
    require(audit.get("post_v8d_machine")=="results/target_discovery/unified_qualification_v1/JEPA_POST_V8C_DELTA_V8D_20261027.json","V8d machine review missing")
    require(audit.get("post_v8d_ci_run_id")==40539643680 and audit.get("post_v8d_static_tests_passed")==20,"V8d exact CI receipt missing")
    require("PR322:docs/agent/JEPA_POST_V8C_DELTA_V8D_20261027.md" in order and "PR322:results/target_discovery/unified_qualification_v1/JEPA_POST_V8C_DELTA_V8D_20261027.json" in order,"V8d must lead latest audit navigation")
    require("PR322:docs/agent/JEPA_POST_V8B_DELTA_V8C_20261027.md" in order,"read order omits V8c new RED")
    issues=doc.get("current_review_heads",{})
    require(type(issues) is dict and set(issues)=={"461","462","463","464","465","466","467"},"new hostile reviewer roster lost")
    require(issues["461"].get("head")=="495350d477a0b7ba65c13dcab5032d443f939cd5" and issues["461"].get("ci_run")==40519155593,"Unified Task1 RED misbound")
    require(issues["462"].get("head")=="67d2336155624a8657d2ef3320c9bfff175951ee" and issues["462"].get("linux_run")==40530824776 and issues["462"].get("windows_run")==40531130624,"Task4 X1-S1/S2 RED misbound")
    require(issues["463"].get("head_at_pointer")=="84b05952112ca405436ee3ccf35cc1c0df53c14d" and issues["463"].get("focused_ci_run")==40533382517 and issues["463"].get("status")=="HISTORICAL_AUTHOR_CI_GREEN__MACHA_INDEPENDENT_REJECTED_AT_PR466","historical Unified Task1 rejection changed")
    require(issues["464"].get("head_at_pointer")=="f6ee226c146c4c31d88ce5b845449ce21758cdeb"
            and issues["464"].get("mechanics_run")==40536232358
            and issues["464"].get("controlling_red_run")==40536232091
            and "T2D_RED" in issues["464"].get("status",""),"PS Task1/2 T2-D hostile RED misrepresented")
    require(issues["465"].get("head_at_pointer")=="3b86b9467506539776e04a6470fa8f2f7363f129"
            and issues["465"].get("ci_run")==40538321346
            and issues["465"].get("review_comment_id")==6447851888
            and "CUMULATIVE_BLOCKED" in issues["465"].get("status",""),"Task4 scoped acceptance promoted")
    require(issues["466"].get("head_at_pointer")=="db69cd0a5777b4a23f0140de9f38980b3e5b95a9"
            and issues["466"].get("ci_run")==40541078808
            and "REJECT" in issues["466"].get("status",""),"Macha adversarial rejection suppressed")
    require(issues["467"].get("head_at_pointer")=="180b550e96b786ddfc53faa29bc81c1d3b503877"
            and issues["467"].get("ci_run")==40543388869
            and "PENDING" in issues["467"].get("status",""),"ChatGPT author repair self-accepted")
    e2g=doc.get("current_external_heads",{}).get("457",{})
    require(e2g.get("head_at_pointer")=="5dd02b0954906618202459dd89f36a62f2f02de7"
            and e2g.get("ci_runs")==[40541457559,40541457592]
            and "NONCAUSAL" in e2g.get("status",""),"E2G latest head or source trust misrepresented")
    require("T2D_RED" in doc["active"]["ps_task1"] and "T2D_RED" in doc["active"]["ps_task2"]
            and "NO_TF_CAUSALITY" in doc["active"]["regulatory_e2g"],"PS T2-D or public E2G promoted")
    require("CUMULATIVE_TASK4_BLOCKED" in doc["active"]["task4"]
            and "MACHA_REJECT_463" in doc["active"]["unified_task1"],"scoped Task4 or old encoder rejection was falsely promoted")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument("--pointer",type=Path,default=None)
    args=p.parse_args()
    validate_pointer(json.loads((args.pointer or args.repo_root/POINTER).read_text()),args.repo_root)
    print("JEPA_V8_SUCCESSOR_POINTER_PASS__NO_SCIENTIFIC_AUTHORITY_ISSUED")


if __name__=="__main__":
    main()
