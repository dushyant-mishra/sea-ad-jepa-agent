"""Static source-custody check for independent Macha475 and subsequent ChatGPT repairs.

Does NOT recreate human data, execute a physical G7 gate, independently replay
the original GitHub hosted CI, or turn a SHA into issuer authority.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DELTA = "results/target_discovery/unified_qualification_v1/JEPA_POST_MACHA475_REPAIR476_477_REVIEW478_20261027.json"
MACHA = "results/target_discovery/unified_qualification_v1/JEPA_MACHA_REVIEW_AND_READINESS_DELTA_20261027.json"
AUTH = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
BLOBS = {
    "docs/agent/JEPA_MACHA_REVIEW_AND_READINESS_DELTA_20261027.md":"059c3eba4fb4b6ac2f1efd1d3519cb9bcb73e417",
    MACHA:"4ad3008a8c7b7e978cc50fde6bfad5c23038441e",
    "scripts/v5/review_probes/macha_20261027/g7_470_hostile_probe.py":"7f2e7f6f23379ea85903dc7409b98b57446eb91d",
    "scripts/v5/review_probes/macha_20261027/ps_canonical_differential_probe.py":"de0d18b78deb4cdd5b33df6a0ddd8e9afc60778e",
    "scripts/v5/review_probes/macha_20261027/q_excluded_g7_conformance_probe.py":"a864945d362882e5c18f13ce98c3074ab5c3e933",
    "scripts/v5/review_probes/macha_20261027/unified_task1_encoder_differential_probe.py":"5591cd25742b79973aa950876c4bccb3060a9106",
}

def require(ok, reason):
    if not ok:
        raise ValueError("POST_MACHA475_AUDIT_NONPROMOTION_REFUSAL: "+reason)

def git_blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()

def verify(data, original, source_blobs):
    require(data.get("schema")=="JEPA_POST_MACHA475_REPAIR476_477_REVIEW478_DELTA_V1","delta schema")
    require(data.get("record_kind")=="APPEND_ONLY_MIXED_INDEPENDENT_REVIEW_AUTHOR_REPAIR_NO_AUTHORITY","no frozen authority")
    require(data.get("authority")==AUTH,"real training forbidden")
    require(original.get("schema")=="JEPA_MACHA_REVIEW_AND_READINESS_DELTA_V1" and
            original.get("author_lane")=="MACHA" and original.get("append_only") is True and
            original.get("authority")==AUTH,"original Macha independent record")
    require(source_blobs==BLOBS,"Macha original six source blobs modified")
    prior={v.get("pr"):v for v in original.get("verdicts",[])}
    require(prior.get(470,{}).get("verdict")=="REPAIR_REQUIRED"
            and prior.get(467,{}).get("verdict")=="ACCEPT_INCREMENTAL_WITH_LIMITATIONS"
            and prior.get(464,{}).get("verdict")=="REJECT_INCREMENTAL","Macha review verdict drift")
    m=data.get("macha_review",{})
    require(m.get("pr")==475 and m.get("head")=="b40d815290fd02ae89259e3b441eabcf7f69d5be"
            and set(m.get("copied_to_audit",[]))==set(BLOBS),
            "Macha475 source custody")
    require(m.get("original_verdicts",{})=={"470":"REPAIR_REQUIRED","467":"ACCEPT_INCREMENTAL_WITH_LIMITATIONS","464":"REJECT_INCREMENTAL"},
            "historical verdict changed")
    repairs={v.get("pr"):v for v in data.get("chatgpt_repairs",[])}
    require(set(repairs)=={476,477},"new repair enumeration")
    a=repairs[476]
    require(a.get("head")=="26031df25b51087f2f3ec35a88eef2919d794c68" and
            a.get("targeted_ci_run")==40582085162 and a.get("targeted_passed")==60
            and a.get("targeted_deselected")==11 and
            a.get("original_review_remaining_failed")==1 and
            a.get("original_11_external_trust_red_preserved") is True and
            a.get("independently_accepted") is False and
            a.get("full_g7_authorized") is False,"R6 fixed fixture cannot erase physical G7 RED")
    b=repairs[477]
    require(b.get("head")=="c83088de090bc4f2fc6bbee353c46070bcca7be5" and
            b.get("targeted_ci_run")==40582199779 and
            b.get("targeted_4_platform_macha_hostile_pass_each")==23 and
            b.get("original_T2D_red_preserved") is True and
            b.get("independently_accepted") is False and
            b.get("ps_task12_cumulative_authorized") is False,"platform fix cannot erase T2-D RED")
    rev=data.get("independent_review",{})
    require(rev.get("pr")==478 and rev.get("source_pr")==474 and
            rev.get("source_head")=="e7635e7982e950a010d181ec6f6883a18ade0db6"
            and rev.get("head")=="b7aa56e2915d2af7dd733f0f0253e684164ce70a" and
            rev.get("verdict")=="ACCEPT_INCREMENTAL_FIXTURE_MATH_WITH_LIMITATIONS__REJECT_PHYSICAL_R2_PROMOTION"
            and rev.get("ci_run")==40583065261 and
            rev.get("total_hostile_and_original_passed")==106 and
            rev.get("independent_new_limitation_tests")==5 and
            rev.get("externally_authenticated") is False and
            rev.get("real_g7_authorized") is False,"depth producer issuer/control limitations")
    require(len(rev.get("counterexample_limits",[]))==3 and
            "SEPARATE_PRIVATE_PHYSICAL_LIBRARY_TOTAL" in rev.get("policy_decision",""),
            "hidden q/source coverage not qualified")
    bio=data.get("existing_biological_results_preserved",{})
    require(bio.get("corrected_human_td_pr")==314 and
            bio.get("candidate_C2")=="ACTIVE_NOT_WINNER" and
            bio.get("production_synthetic_task4_biology_generator")=="ABSENT_IN_REVIEWED_BRANCHES",
            "old biology or PS Task4 status altered")
    p=data.get("privacy_firewall",{})
    require(p.get("values_preserved_or_repeated") is False and
            p.get("used_for_scientific_decision") is False,"private row data repeated/promoted")

def validate_root(root=ROOT):
    m=json.loads((root/MACHA).read_text(encoding="utf-8"))
    d=json.loads((root/DELTA).read_text(encoding="utf-8"))
    found={}
    for path in BLOBS:
        raw=(root/path).read_bytes()
        found[path]=git_blob(raw)
    verify(d,m,found)

if __name__ == "__main__":
    validate_root()
    print("MACHA475_SOURCE_VERIFIED__R6_SNAPSHOT_60_PASS_R1D_RED__PS477_4_PLATFORMS_T2D_RED__DEPTH106_FIXTURE_ONLY")
