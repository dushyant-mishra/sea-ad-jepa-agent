"""Auditable, fail-closed custody of Oct-28 JEPA successor source history.

Only checks archived claims and exact Git blobs, never physical issuer,
real human calibration or scientific target authorization. New hostile review
tests remain *.py.txt, never promoted to passing tests on this audit branch.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path("results/target_discovery/unified_qualification_v1/JEPA_CURRENT_SUCCESSOR_FREEZE_20261028.json")
AUTH = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
ORIGINAL = {
    "docs/agent/JEPA_MACHA_V2_G7_OBSERVATION_CONTRACT_DELTA_20261028.md": "fafa64b43b56c2207963d6920df0f46d5c6ebb93",
    "results/target_discovery/unified_qualification_v1/JEPA_MACHA_V2_G7_OBSERVATION_CONTRACT_DELTA_20261028.json": "66dabe48970cda74d5843379b08853c9e10cca05",
    "scripts/v5/review_probes/macha_20261028/observation_source_census_probe.py": "c0863c59eb6b9c69f5cca140294b41250b51552d",
    "scripts/v5/review_probes/macha_20261028/v2_g7_crosshead_probe.py": "7bbd941674f3362462765cf253ea2dbc746f5f7e",
    "docs/agent/review_probes/macha_20261028/pr481_test_observation_normalization_view_v2_macha_479_red.py.txt": "3dda6c2cc9be19d5daececfb07967e94067519f6",
    "docs/agent/review_probes/macha_20261028/pr482_test_td_real_g7_content_enforcement_v1_macha_476_red.py.txt": "fd98636f85967226af1605c376522865167c8706",
    "docs/agent/review_probes/macha_20261028/pr483_test_ps_t12_477_recheck_macha_red.py.txt": "f2d10a8c4ea3620c3f46f7d6b208c07279027d56",
    "docs/agent/review_probes/macha_20261028/pr486_test_calibration_v1_macha_480_repair.py.txt": "d0fff1483453eadc055866b67249c8e6cb21a9ef",
    "docs/agent/review_probes/macha_20261028/pr481_td-v2-normalization-view-macha479-review-red.yml.txt": "5a5e99af3fd0a06a4e41520dba6f594dd852dcbf",
    "docs/agent/review_probes/macha_20261028/pr482_td-g7-e3-macha476-review-red.yml.txt": "a13aa0b4f591ca75fee8bca745c09668bee0268b",
    "docs/agent/review_probes/macha_20261028/pr483_ps-t12-477-recheck-macha-red.yml.txt": "b44d9033aee62ae715ba0852f30d39fe5ef49855",
    "docs/agent/review_probes/macha_20261028/pr486_ps-task3-437-r1-r2-repair-macha.yml.txt": "e565171528bc277485ce6a87478f23b80cc5a610",
}

def reject(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("JEPA_OCT28_SUCCESSOR_FREEZE_NO_PROMOTION: "+why)

def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def validate(d: dict) -> None:
    reject(type(d) is dict and d.get("schema")=="JEPA_CHATGPT_LANE_SUCCESSOR_FREEZE_V1", "schema")
    reject(d.get("kind")=="APPEND_ONLY_SOURCE_RECONCILIATION__NOT_NEW_BIOLOGICAL_QUALIFICATION", "status")
    reject(d.get("scientific_standing")==AUTH, "unapproved authority")
    reject(d.get("frozen_prior_independent_V8e_head")=="a271164554076d0acda3bd0cf0b1bf957c0fdfd3", "frozen audit")
    reject(d.get("controlling_previous_audit_head")=="dfaba7967a77d482496d1b843f4a5d666b9ce570"
           and d.get("controlling_previous_handoff_head")=="6237438d0b1e708839d4b66547129d26664ae03e",
           "prior controlling heads")
    old={v.get("pr"):v for v in d.get("existing_historical_no_repeat",[]) if type(v) is dict and "pr" in v}
    reject(314 in old and old[314].get("status")=="CORRECTED_TD56_TD57B_TD59_PASS_TD57C_FAIL_ONE_SHOT_SPENT"
           and 328 in old and 469 in old and 471 in old and 475 in old, "completed biology rewritten")
    review=d.get("new_independent_review",{})
    reject(review.get("pr")==484 and review.get("head")=="5d84ed90417fbc1be1a13657a08491e2db6feef5"
           and review.get("base_audit_head")=="dfaba7967a77d482496d1b843f4a5d666b9ce570",
           "Macha original independent review")
    reject(dict(review.get("original_files",[]))=={k:v for k,v in ORIGINAL.items() if "docs/agent/review_probes/" not in k},
           "Macha484 original probes or report changed")
    ver={v.get("source_pr"):v for v in review.get("verdicts",[]) if type(v) is dict}
    reject(set(ver)=={479,476,477}, "review group")
    expected={
        479:(481,"REPAIR_REQUIRED",19,5),
        476:(482,"ACCEPT_INCREMENTAL_WITH_R1_R2_BLOCKERS",18,3),
        477:(483,"ACCEPT_INCREMENTAL_WITH_LIMITATIONS",8,2),
    }
    for source,(n,verdict,failed,passed) in expected.items():
        v=ver[source]
        reject(v.get("review_pr")==n and v.get("verdict")==verdict and
               v.get("new_red_failed",failed)==failed and
               v.get("new_characterization_passed",passed)==passed,
               "independent review verdict RED drift "+str(source))
    reject(ver[476].get("remaining_external_hostiles")==11,
           "R1/R1D/R2 revoked")
    original={v.get("pr"):v for v in d.get("original_red_tests_archived_outside_collection",[])
              if type(v) is dict}
    reject(set(original)=={481,482,483} and
           all(ORIGINAL.get(v["path"])==v.get("blob") and v["path"].endswith(".py.txt")
               for v in original.values()),"expected RED tests disappeared/relabelled")
    repair=d.get("task3_repair_candidate",{})
    reject(repair.get("pr")==486 and repair.get("head")=="f17080516f77e79fb6f6cb44903cbabdb2a85dd7"
           and repair.get("base_review_pr")==480 and
           repair.get("source_git_blob")=="a3406783892fe3fb016b1423ba1e3676412d235d"
           and repair.get("new_hostile_test_git_blob")=="d0fff1483453eadc055866b67249c8e6cb21a9ef"
           and repair.get("independently_accepted") is False, "unreviewed Task3 made eligible")
    require_limits={"OBSERVATION_PARAMETER_SEMANTICS_BOUND_FALSE",
                    "_AUTHENTICATED_CALIBRATION_REGISTRY_EMPTY",
                    "NO_REAL_POST_CORRECTION_TRAIN_ISSUER"}
    reject(require_limits.issubset(set(repair.get("limitations",[]))),"calibration issuer invented")
    runs={x.get("run"):x for x in repair.get("ci",[])}
    reject(set(runs)=={40741905858,40741906003,40741905819} and
           all(x.get("result")=="SUCCESS" for x in runs.values()), "Task3 hosted CI misrepresented")
    policy=d.get("new_observation_decision_proposed",{})
    reject(policy.get("status")=="MACHA_PROPOSED_NOT_DECIDING_LANE_ACCEPTED", "D1 decision backpromoted")
    reject(policy.get("D1",{}).get("name")=="VISIBLE_BASE_MAPPED_SUM_V1"
           and policy.get("D2",{}).get("default_recommendation") is False, "D1/D2 contract")
    head=policy.get("crosshead",{})
    reject(head.get("schema_compatibility")=="NO" and head.get("rename_adapter_accepted")==6 and
           head.get("rename_adapter_worlds")==200 and head.get("v3_reachable") is False and
           head.get("physical_provenance_authenticated") is False, "false G7 cross-head authority")
    blockers=policy.get("blocked",[])
    reject("G7 R1/R1D/R2" in blockers and "T2-D" in blockers and
           "PS Task4 candidate-neutral biology generator" in blockers, "original blockers erased")
    data=d.get("data_custody",{})
    reject(data.get("original_binaries_in_github") is False and
           data.get("human_raw_values_or_donor_identifiers_committed_by_this_freeze") is False,
           "data or human rights overclaim")

def validate_root(root: Path=ROOT) -> None:
    validate(json.loads((root/DATA).read_text(encoding="utf-8")))
    for path,digest in ORIGINAL.items():
        reject(blob_sha((root/path).read_bytes())==digest, "original Git blob drift: "+path)
    doc=(root/"docs/agent/JEPA_COMPLETE_LANE_TAKEOVER_FREEZE_20261028.md").read_text()
    for token in ("#479", "#476", "#477", "#486", "PR #314", "PS Task4", "D1", "D2", "TARGET_WINNER_NONE"):
        reject(token in doc, "takeover document lost "+token)

if __name__=="__main__":
    validate_root()
    print("JEPA_OCT28_LANE_FREEZE_SOURCE_BLOBS_12__MACHAREDS_AND_PS3_CANDIDATE__NO_AUTHORITY")
