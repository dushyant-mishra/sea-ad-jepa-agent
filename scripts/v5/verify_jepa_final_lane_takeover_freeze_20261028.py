"""Fail-closed static validation of the final Oct-28 JEPA lane takeover freeze.

This only verifies archived source/decision claims. It does not execute human
biology, authenticate a physical issuer, or grant target/training authority.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=Path("results/target_discovery/unified_qualification_v1/JEPA_FINAL_LANE_TAKEOVER_FREEZE_20261028.json")
DOC=Path("docs/agent/JEPA_FINAL_LANE_TAKEOVER_FREEZE_20261028.md")
AUTH="TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
PINNED={
"docs/agent/JEPA_COMPLETE_LANE_TAKEOVER_FREEZE_20261028.md":"46cee25071d6891bdb6b95e9ac3275f25ffcefa2",
"docs/agent/JEPA_LANE_TAKEOVER_MASTER_20261028.md":"89ad6477b801ce1f5bda3d0b1f7af383ed79235b",
"results/target_discovery/unified_qualification_v1/JEPA_CURRENT_SUCCESSOR_FREEZE_20261028.json":"49e47fc74aceca092a3f4f2cbf25e4bb94de10b2",
"results/target_discovery/unified_qualification_v1/JEPA_LANE_TAKEOVER_MASTER_20261028.json":"4d8e1284b6ebcf6a0f9e706bcbae76193a6c48ee",
"docs/agent/JEPA_MACHA_V2_G7_OBSERVATION_CONTRACT_DELTA_20261028.md":"fafa64b43b56c2207963d6920df0f46d5c6ebb93",
"results/target_discovery/unified_qualification_v1/JEPA_MACHA_V2_G7_OBSERVATION_CONTRACT_DELTA_20261028.json":"66dabe48970cda74d5843379b08853c9e10cca05",
"docs/agent/JEPA_PS_TASK3_MACHA437_INDEPENDENT_REVIEW_20261028.md":"3ea78eed8965cd46478bf980ab2d7105a2c689f6",
"results/production_synthetic/JEPA_TASK3_CHATGPT_INDEPENDENT_REVIEW_20261028.json":"f4da4386d948a47233f07f9c8d50fb31c0200d8e",
"docs/agent/chat_exclusive_20261028/PASTED_TEXT_V8A_SUCCESSOR_20261027_TEXT_EXTRACT.md":"58b4312666aae179ef0f9877c3447ab5a120ea28",
"docs/agent/chat_exclusive_20261028/PASTED_TEXT_SYNTH_DOWNSTREAM_20261027_TEXT_EXTRACT.md":"c99e2927845bad6acbea2191b6c8378d65913333",
"docs/agent/chat_exclusive_20261028/PASTED_SOURCES_CUSTODY_AND_SUPERSESSION.md":"e89b94d241cedbd8667a1adf77b02d9eec1110cb",
"results/target_discovery/chat_exclusive_takeover_20261028/DUPLICATE_PASTED_TEXT_SOURCE_CUSTODY_V1.json":"bc65e56035def6e198cdcb2cc65494f05c48d83a",
}
def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def req(ok,why):
    if not ok: raise ValueError("JEPA_FINAL_TAKEOVER_FREEZE_REFUSAL: "+why)
def validate(d):
    req(d.get("schema")=="JEPA_FINAL_LANE_TAKEOVER_FREEZE_20261028_V1","schema")
    req(d.get("classification")=="APPEND_ONLY_FINAL_NAVIGATION_AND_CUSTODY__NO_NEW_BIOLOGICAL_EXECUTION","classification")
    req(d.get("scientific_authority")==AUTH,"authority")
    req(d.get("frozen_independently_reviewed_v8e_head")=="a271164554076d0acda3bd0cf0b1bf957c0fdfd3","frozen V8e")
    reviews={x.get("source_pr"):x for x in d.get("current_independent_review_state",[]) if isinstance(x,dict)}
    req(reviews[479]["verdict"]=="REPAIR_REQUIRED" and reviews[479]["review_pr"]==481,"479 verdict")
    req(reviews[476]["verdict"]=="ACCEPT_INCREMENTAL_WITH_R1_R2_BLOCKERS" and reviews[476]["review_pr"]==482,"476 verdict")
    req(reviews[477]["verdict"]=="ACCEPT_INCREMENTAL_WITH_LIMITATIONS" and reviews[477]["review_pr"]==483,"477 verdict")
    req(reviews[437]["verdict"]=="REPAIR_REQUIRED__R1_NUMERIC_ALIAS__R2_OBS_PARAMETER_SPOOF","437 verdict")
    r486=reviews[486]
    req(r486.get("independent_chatgpt_acceptance") is False and
        "_AUTHENTICATED_CALIBRATION_REGISTRY_EMPTY".replace("_AUTHENTICATED","AUTHENTICATED") not in [],"486 unaccepted")
    req("AUTHENTICATED_CALIBRATION_REGISTRY_EMPTY" in r486.get("limitations",[]),"486 registry still empty")
    obs=d.get("observation_contract_decision_status",{})
    req(obs.get("status")=="MACHA_PROPOSED__DECIDING_LANE_NOT_YET_ACCEPTED","D1 undecided")
    req(obs.get("D1",{}).get("name")=="VISIBLE_BASE_MAPPED_SUM_V1" and obs.get("D1",{}).get("recommended_default") is True,"D1 proposal")
    req(obs.get("D2",{}).get("recommended_default") is False,"D2 default off")
    req(obs.get("g7_cross_head",{}).get("schema_compatible") is False and obs["g7_cross_head"].get("v3_reachable") is False,"G7 cross-head")
    blockers=set(d.get("production_synthetic_blockers",[]))
    for x in ("T2D_EXTERNAL_SCAN_ISSUER_RED","TASK3_REAL_TRAIN_OBSERVATION_CALIBRATION_ISSUER_UNQUALIFIED",
              "G7_R1_PHYSICAL_UNIT_R1D_DONOR_AND_R2_NORMALIZATION_PROVENANCE_RED",
              "PS_TASK4_CANDIDATE_NEUTRAL_BIOLOGICAL_GENERATOR_ABSENT_IN_REVIEWED_BRANCHES"):
        req(x in blockers,"blocker "+x)
    custody=d.get("source_and_data_custody",{})
    req(custody.get("original_large_binaries_in_github") is False and
        custody.get("raw_donor_or_per_cell_values_added_by_final_freeze") is False and
        custody.get("raw_binaries_recoverable_from_hash_alone") is False,"data custody")
    pasted=custody.get("duplicate_pasted_text_sources",{})
    req(pasted.get("status")=="TWO_DISTINCT_ORIGINAL_FILES_WITH_SAME_BASENAME__BYTE_PRESERVED__HISTORICAL_ONLY" and
        pasted.get("execute_as_instructions") is False and
        pasted.get("known_correction")=="SYNTH_DOWNSTREAM_C3_RARE_WORDING_SUPERSEDED__C3_IS_QUERY_MEASURED",
        "duplicate pasted source correction/custody")
    src={x.get("path"):x for x in pasted.get("sources",[]) if isinstance(x,dict)}
    req(src.get("docs/agent/chat_exclusive_20261028/PASTED_TEXT_V8A_SUCCESSOR_20261027_TEXT_EXTRACT.md",{}).get("git_blob")=="58b4312666aae179ef0f9877c3447ab5a120ea28" and
        src.get("docs/agent/chat_exclusive_20261028/PASTED_TEXT_SYNTH_DOWNSTREAM_20261027_TEXT_EXTRACT.md",{}).get("git_blob")=="c99e2927845bad6acbea2191b6c8378d65913333",
        "duplicate pasted source identities")
    req(len(d.get("do_not_repeat",[]))>=9,"no-repeat list")
    req(len(d.get("next_agent_order",[]))>=9,"successor order")
def validate_root(root=ROOT):
    d=json.loads((root/DATA).read_text())
    validate(d)
    for path,digest in PINNED.items():
        req(blob((root/path).read_bytes())==digest,"source drift "+path)
    doc=(root/DOC).read_text()
    for token in ("PR #314","R5","PR #479","PR #476","PR #477","PR #486","D1","D2","PS Task4","TARGET_WINNER_NONE"):
        req(token in doc,"missing doc token "+token)
if __name__=="__main__":
    validate_root()
    print("JEPA_FINAL_TAKEOVER_FREEZE_PASS__HISTORY_PRESERVED__OPEN_REDS_PRESERVED__NO_AUTHORITY")
