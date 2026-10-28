"""Fail-closed *static* custody verifier for the Oct 28 JEPA successor source graph.

This is not a live GitHub check, a source issuer, a protected-data reader, or a
biological gate. It rejects ledger edits that erase the original hostile RED,
conflate candidate semantics, or promote fixtures into human training.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
LEDGER=Path("results/target_discovery/unified_qualification_v1/JEPA_LANE_TAKEOVER_MASTER_20261028.json")
AUDIT=Path("docs/agent/JEPA_LANE_TAKEOVER_MASTER_20261028.md")
AUTH="TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
ORIGINALS={
 "docs/agent/chat_exclusive_20261027/g7_local_input_admissibility_20261027_original.md":"4829c74e0a22de17a9c825e7fde4c720b2161e79",
 "docs/agent/chat_exclusive_20261027/g7_local_input_admissibility_v2_20261027_original.md":"540731aa1d1f56199336d7095180cf156b970645",
}
EXPECTED_PR_HEADS={
 314:"c6899a2910244a0352c0c57e7aea6e3026191da1",
 328:"25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec",
 344:"847fe734b15e52f204f18903a124e1cfd3bf111d",
 469:"7a6477244dfc817d929e210c38c1ea4b2d1a1927",
 471:"7957b7578168532eabad8b2b75126bb71e6f43b7",
 475:"b40d815290fd02ae89259e3b441eabcf7f69d5be",
 476:"26031df25b51087f2f3ec35a88eef2919d794c68",
 477:"c83088de090bc4f2fc6bbee353c46070bcca7be5",
 474:"e7635e7982e950a010d181ec6f6883a18ade0db6",
 478:"b7aa56e2915d2af7dd733f0f0253e684164ce70a",
 479:"ae762d7096a94ac663a0788f6f577ba404e37536",
 437:"fd3242ada6f77ba09ff2d8a1c7716eb9725ced11",
 480:"f39e605abc616cf59051a8bda9b0270cef5d6f09",
 465:"3b86b9467506539776e04a6470fa8f2f7363f129",
}
def must(ok,reason):
 if not ok:raise ValueError("JEPA_TAKEOVER_NO_PROMOTION_REFUSAL: "+reason)
def gitblob(raw:bytes):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def verify(d,doc:str,blob_map:dict[str,str]):
 must(d.get("schema")=="JEPA_LANE_TAKEOVER_MASTER_20261028_V1","schema")
 must(d.get("classification")=="APPEND_ONLY_CUSTODY_NAVIGATION__NO_NEW_SCIENCE_OR_ISSUER","document class")
 must(d.get("standing_authority")==AUTH,"authority")
 must(d.get("frozen_accepted_v8e_head")=="a271164554076d0acda3bd0cf0b1bf957c0fdfd3","historic frozen head")
 source=d.get("authoritative_source_pointers")
 must(type(source) is list and len(source)>=17,"complete source index")
 bynum={x.get("pr"):x for x in source if type(x) is dict}
 for pr,sha in EXPECTED_PR_HEADS.items():
  must(bynum.get(pr,{}).get("head")==sha,"historical source head "+str(pr))
 must(bynum.get(322,{}).get("previous_head_before_this_takeover")==
      "dfaba7967a77d482496d1b843f4a5d666b9ce570","audit starting head")
 must(bynum.get(460,{}).get("previous_head_before_this_takeover")==
      "6237438d0b1e708839d4b66547129d26664ae03e","handoff starting head")
 must(blob_map==ORIGINALS,"original local G7 report bytes changed")
 originals=d.get("central_source_artifacts",{}).get("original_local_g7_reports",[])
 must(type(originals) is list and len(originals)==2,"G7 report provenance missing")
 must({x.get("path"):x.get("git_blob") for x in originals}==ORIGINALS,
      "G7 original source blob declaration changed")
 must({x.get("role") for x in originals}=={
  "ORIGINAL_V1_SUPERSEDED_NOT_PASS",
  "CORRECTED_LOCAL_METADATA_SCOPE__G7_UNQUALIFIED"},"V1 mistake or V2 correction erased")
 must(d.get("central_source_artifacts",{}).get("source_binary_boundary")==
       "RAW_LARGE_ZIP_NPZ_CHECKPOINTS_HASH_ONLY_NOT_HOSTED_IN_GITHUB",
       "binary hosted/recoverable by hashes false claim")
 p=d.get("central_source_artifacts",{}).get("pasted_20261027_handoff",{})
 must(p.get("sha256")=="d08e24d481e77a89ebf07428601fe6c54759a9050adf58346d0fa6cb5281a549"
      and "NOT_VERBATIM_COPIED" in p.get("status",""),"unsaved raw handoff secretly promoted")
 decisions={x.get("id"):x for x in d.get("science_decisions",[]) if type(x) is dict}
 must(decisions.get("C2",{}).get("status")=="ACTIVE_NOT_A_JEPA_WINNER","C2 promoted")
 must(decisions.get("C3",{}).get("name")=="QUERY_MEASURED_STATE" and
      decisions["C3"].get("not")=="RARE_MICROGLIA" and
      decisions["C3"].get("status")=="DEVELOPMENTAL_NOT_PRODUCTION_QUALIFIED","C3 wrong taxonomy")
 must(decisions.get("SYNTH",{}).get("status")==
      "NOT_PRODUCTION_V3_1_1__NO_FULL_KNOWN_TRUTH_EXECUTION","fixture promoted")
 rv={x.get("pr"):x for x in d.get("reviewer_verdicts",[]) if type(x) is dict}
 must(set(rv)=={470,464,467,474,479,437},"review outcomes missing")
 must(rv[470].get("verdict")=="REPAIR_REQUIRED" and "11_PHYSICAL_DONOR_DEPTH_RED" in rv[470].get("repair_status",""),"G7 physical RED")
 must(rv[464].get("verdict")=="REJECT_INCREMENTAL" and "T2D_RED" in rv[464].get("repair_status",""),"T2-D issuer RED")
 must(rv[437].get("review_pr")==480 and rv[437].get("verdict")==
      "REPAIR_REQUIRED__R1_NUMERIC_ALIAS__R2_OBS_PARAMETER_SPOOF" and
      rv[437].get("repair_status")=="NO_SOURCE_REPAIR","Task3 independent RED")
 must(rv[479].get("verdict")=="AUTHOR_TESTS_PASS_124__6_WORKFLOWS_GREEN__INDEPENDENT_REVIEW_PENDING","V2 independent claim")
 must("REJECT_PHYSICAL_R2_PROMOTION" in rv[474].get("verdict",""),"R2 fixture science only")
 ci=d.get("ci_pins",{})
 must(ci.get("audit_before_freeze",{}).get("passed")==20 and
      ci.get("handoff_before_freeze",{}).get("passed")==2,"pre-freeze source state")
 must(ci.get("pr480",{}).get("review_expected_failed")==3 and
      ci["pr480"].get("review_control_passed")==1 and
      ci["pr480"].get("original_tests_passed")==33 and
      ci["pr480"].get("full_task3_failed")==3 and
      ci["pr480"].get("full_task3_passed")==391 and
      ci["pr480"].get("not_promoted") is True,"Task3 RED and nonauthority receipt")
 must(ci.get("pr479",{}).get("passed_tests")==124 and
      ci["pr479"].get("real_g7_cross_head_executed") is False,"G7 cross-head untested")
 must(ci.get("pr471",{}).get("historical_logical_files_sha_verified")==97,"97/97 historical custody only")
 gates=d.get("science_gates",{})
 must(gates.get("target_winner")=="NONE" and gates.get("representation_winner")=="NONE"
      and gates.get("real_training_authorized") is False and gates.get("stage4_authorized") is False,
      "winner or Stage4 authorization")
 must(gates.get("production_synthetic_task3")=="REPAIR_REQUIRED_AND_NO_CURRENT_REAL_CALIBRATION_ISSUER"
      and gates.get("production_synthetic_task4_candidate_neutral_biology")=="ABSENT_ON_REVIEWED_BRANCHES"
      and gates.get("G7_V2_cross_branch")=="NOT_TESTED","science gates promoted")
 for k,expected in [
    ("g7_physical_atom_identity","RED_R1"),
    ("g7_donor_specimen_independence","RED_R1D"),
    ("g7_q_excluded_normalization_issuer","RED_R2"),
    ("production_synthetic_t2_external_scan_issuer","RED")]:
  must(gates.get(k)==expected,"unresolved physical/source gate erased: "+k)
 must(type(d.get("next_actions")) is list and len(d["next_actions"])>=5,"successor task ownership")
 for word in ("PR #314","PR #480","PR #479","R1D","2⁵³","97/97","not copied verbatim","PS Task4","NOT TESTED"):
  must(word.casefold() in doc.casefold(),"no-repeat narrative missing: "+word)
 must(AUTH in doc,"narrative lacks hard stop")

def validate_root(root=ROOT):
 d=json.loads((root/LEDGER).read_text(encoding="utf-8"))
 doc=(root/AUDIT).read_text(encoding="utf-8")
 blobs={name:gitblob((root/name).read_bytes()) for name in ORIGINALS}
 verify(d,doc,blobs)
 return d

if __name__=="__main__":
 validate_root()
 print("JEPA_OCT28_MASTER_TAKEOVER_SOURCE_CUSTODY_OK__TASK3_3_RED__G7_EXTERNAL_RED__NO_REAL_TRAINING")
