"""Non-promoting biological evidence -> synthetic challenge inventory guard.

This validates a research planning document, not the biological identity or measured
truth of the cited external data. No raw-data fetch, simulation or model fit.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

MACHINE = "results/target_discovery/biology_state_synthetic_crosswalk_v1/STATE_EVIDENCE_AND_SYNTHETIC_TEST_MAP_20261027.json"
DOCUMENT = "docs/agent/JEPA_BIOLOGICAL_STATE_TO_SYNTHETIC_CROSSWALK_20261027.md"
AUTH = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
PARENT_SHA = "a271164554076d0acda3bd0cf0b1bf957c0fdfd3"
HANDOFF_SHA = "b867a348d9244bcbc9d4ac696ebc0df6f325b6f8"
LINEAGES = {
 "integrated_design": (315,"af03ef67d52651463944a6de3a08e101ad00e0ea","DESIGN_ONLY"),
 "integrated_fixture": (328,"25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec","FIXTURE"),
 "synthetic_td": (337,"054a87a117aa0bbefafc5032fa354544e038162a","TEST_QUALIFIED_ONLY"),
 "real_tournament": (313,"206167a1eb86f1dec5f8285db56accbcd469bce9","OUTCOMES_UNREAD"),
 "post_td": (351,"2abcb9fe156eac340ff12adff9426ed38d929e3e","NO_TRAINING"),
 "fixture_bridge": (451,"bbdf9a90973303e41cee6d8bd9d05de38e9b828a","NO_A7_REAL_RECEIPT"),
 "e2g": (457,"5dd02b0954906618202459dd89f36a62f2f02de7","NONCAUSAL"),
}
QUESTIONS = {
 "SHARED_RNA_PROGRAM": ("C1_SHARED","NOT_ESTIMABLE_PENDING_REAL_TARGET_EVIDENCE"),
 "RELATIONAL_RNA_STATE": ("C2_RELATIONAL","NOT_ESTIMABLE_PENDING_REAL_RELATION_DECISION_LAW"),
 "RARE_MICROGLIAL_PROGRAM": ("RARE_SPECIALIST_NOT_C3","NOT_ESTIMABLE_PENDING_RARE_PROVENANCE_AND_CALIBRATION"),
 "ATAC_CONTEXT_PROGRAM": ("C5_SPECIALIST_AUXILIARY_ONLY","NOT_ESTIMABLE_PENDING_MEASURED_ATAC_STATE_AND_SOURCE_IDENTITY"),
 "INTERVENTION_RESPONSE_PROGRAM": ("PERTURBATION_SUPPORT_NOT_AUTOMATIC_TD_CANDIDATE","NOT_ESTIMABLE_PENDING_PERTURBATION_EFFECT_VALIDATION"),
 "NONADDITIVE_COMPOSITE_STATE": ("C6_THEN_C4_CONDITIONAL","DEFERRED_UNSUPPORTED"),
 "QUERY_MEASURED_RNA_STATE": ("C3_QUERY_MEASURED","NOT_ESTIMABLE_PENDING_CURRENT_Q_MEASURED_TARGET_SOURCE_AND_GATE"),
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
CITATION_SOURCES = {
 "docs/agent/JEPA_NEW_CHAT_HANDOFF_20260911_TARGET_DISCOVERY_V5_INTEGRATED_CURRENT.md",
 "docs/agent/JEPA_TERMINAL_TARGET_LINEAGE_RECONSTRUCTION_20261005_V3_FINAL.md",
 "docs/agent/JEPA_FULL_LANE_HISTORICAL_SYNTHETIC_TAKEOVER_V8_20261017.md",
 "docs/agent/JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.md",
 "docs/agent/JEPA_LANE_MASTER_AUDIT_INDEX_20261014.md",
 "results/reports/stage70_rare_microglia_auxiliary_head_robustness_lock_audit_report_v1.md",
 "docs/superpowers/specs/2026-10-13-unified-synthetic-integration-design.md",
 "docs/stage75f_out_of_core_execution_plan_v1.md",
 "docs/agent/JEPA_STAGE75_E2G_POSTHOC_TSS_GEOMETRY_READOUT_20261027.md",
 "docs/agent/JEPA_NEW_CHAT_HANDOFF_20260923_V23_FULL_CURRENT.md",
 "docs/stage77_tier_a_perturbation_mvp.md",
 "docs/superpowers/specs/2026-10-12-unified-synthetic-td-rehearsal-design-v2.md",
}
# Archival facts: source-controlled development results are distinct from real target authority.
COMPLETED_REAL_KEYS = {
 "TD_R5_QUERY_DEVELOPMENT": "HISTORICAL_DEVELOPMENTAL_RESULT__NOT_CURRENT_TARGET_WINNER",
 "TD56_59_RELATIONAL": "CORRECTED_REPLAY_PR314_COMPLETED__BROAD_MESO_VIABLE__C2_ACTIVE_NOT_WINNER",
 "V44_RNA_TEACHER_PROXIES": "ACTUAL_PROXIES_RUN__NO_Q_CONDITIONING__NO_FAIR_NEURAL_OR_BIOLOGY_WINNER",
 "STAGE70_REAL_RARE": "SOURCE_NATIVE_SAFE_NEGATIVE_PRIOR__NO_EXTERNAL_OR_TARGET_AUTHORITY",
 "M_STRICT_REAL_COUNTS": "REAL_SUPPORT_AND_TECHNICAL_AUDIT_QUALIFIED__NO_CANDIDATE_OUTCOMES",
 "MACHA_RNA_ATAC": "ASSAY_PROVENANCE_QUALIFIED__REGULATORY_STATE_BENCHMARK_NOT_DONE",
 "MACHA_GSE301119": "EXPERIMENTAL_TARGET_ENGAGEMENT_MEASURED__NOT_ADULT_MICROGLIA_OR_JEPA_STATE",
 "UNIFIED_FIXTURE_AND_POST_TD": "ALREADY_BUILT_REUSE_NO_DUPLICATE",
}
HISTORICAL_SOURCES = {
 "TD_R5_QUERY_DEVELOPMENT": ("docs/agent/TARGET_DISCOVERY_MASTER_HANDOFF_20261011.md","audit/target-discovery-takeover-20261011"),
 "TD56_59_RELATIONAL": ("docs/agent/TD_CORRECTED_REPLAY_OUTCOME_7819aabd_20261012/TD_CORRECTED_REPLAY_OUTCOME.md","c6899a2910244a0352c0c57e7aea6e3026191da1"),
 "V44_RNA_TEACHER_PROXIES": ("docs/agent/JEPA_V44_TINY_TOURNAMENT_NEW_CHAT_HANDOFF_20260926.md","research/v44-tiny-teacher-tournament-20260926"),
 "STAGE70_REAL_RARE": ("results/reports/stage70_rare_microglia_auxiliary_head_robustness_lock_audit_report_v1.md",PARENT_SHA),
 "M_STRICT_REAL_COUNTS": ("docs/agent/MACHA_TD_REAL_DATA_QUALIFICATION_HOSTILE_REVIEW_20261014.md","audit/td-real-data-qualification-macha-20261014"),
 "MACHA_RNA_ATAC": ("PR #164","0e36cede000c6c0eee66ab2b11ed43d41f7b9580"),
 "MACHA_GSE301119": ("PR #77","9a2a30e4c4c99be2a8f948aba680524c786d2737"),
 "UNIFIED_FIXTURE_AND_POST_TD": ("docs/agent/JEPA_FULL_LANE_HISTORICAL_SYNTHETIC_TAKEOVER_V8_20261017.md",PARENT_SHA),
}
REQUIRED_RULES = {"biological_truth","selection","masking","comparison","cross_modal","perturbation","measurements","eligibility"}
BANNED_AS_SCIENCE = {"PASS","QUALIFIED","SELECTED","AUTHORIZED","TRAINING_ON"}

def ensure(ok:bool,message:str):
    if not ok:
        raise ValueError(message)

def validate(d:dict,root:Path)->None:
    ensure(type(d) is dict and d.get("schema")=="JEPA_BIOLOGICAL_STATE_SYNTHETIC_CROSSWALK_V1","schema")
    ensure(d.get("kind")=="PROSPECTIVE_SCIENCE_PLANNING_FROM_HISTORICAL_SOURCES__NOT_A_REAL_EXPERIMENT","cannot masquerade as experiment")
    ensure(d.get("authority")==AUTH,"scientific promotion blocked")
    ensure(d.get("parent_audit")=={"pr":322,"head":PARENT_SHA},"audit SHA drift")
    ensure(d.get("active_handoff")=={"pr":460,"head":HANDOFF_SHA},"handoff SHA drift")
    lin=d.get("lineage")
    ensure(type(lin) is dict and set(lin)==set(LINEAGES),"synthetic integration provenance missing or extra")
    for name,(pr,sha,scope) in LINEAGES.items():
        row=lin[name]
        ensure(row.get("pr")==pr and row.get("head")==sha and scope in row.get("role",""),"changed lineage role "+name)
    rules=d.get("rules",{})
    ensure(type(rules) is dict and set(rules)==REQUIRED_RULES,"evidence rule lost")
    for key,value in rules.items():
        ensure(type(value) is str and len(value)>48,"empty rule "+key)
    items=d.get("state_questions")
    ensure(type(items) is list and len(items)==len(QUESTIONS),"missing candidate question")
    seen=set()
    for row in items:
        ensure(type(row) is dict,"row type")
        id=row.get("id")
        ensure(type(id) is str and id in QUESTIONS and id not in seen,"duplicate or preselected candidate")
        seen.add(id)
        family,promotion=QUESTIONS[id]
        ensure(row.get("family")==family and row.get("promotion")==promotion,"target invented/qualified "+id)
        for fld in ("question","evidence_tier","simulator_case","simulator_status","human_target_object_needed","first_forward_test"):
            ensure(type(row.get(fld)) is str and len(row[fld])>20, "required state science missing "+id+"/"+fld)
        ensure(row["simulator_case"].startswith(("PR328_","PR315_")),"new unqualified simulation "+id)
        ensure("PASS" not in row["promotion"] and "QUALIFIED" not in row["promotion"],"biology promoted "+id)
        srcs=row.get("real_evidence")
        ensure(type(srcs) is list and len(srcs)>=2,"no actual source reconciliation "+id)
        for source in srcs:
            ensure(type(source) is dict and source.get("source") in CITATION_SOURCES, "invented source file "+id)
            sha=source.get("sha")
            ensure(type(sha) is str and HEX40.fullmatch(sha) is not None,"unbound source "+id)
            expect="25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec" if source["source"].endswith("unified-synthetic-integration-design.md") else (
                "af03ef67d52651463944a6de3a08e101ad00e0ea" if source["source"].endswith("rehearsal-design-v2.md") else (
                "5dd02b0954906618202459dd89f36a62f2f02de7" if source["source"].endswith("GEOMETRY_READOUT_20261027.md") else PARENT_SHA))
            ensure(sha==expect,"source revision was silently changed "+id)
            ensure(type(source.get("interpretation")) is str and len(source["interpretation"])>48, "no claim limitation "+id)
        blockers=row.get("must_fail_or_abstain_on")
        ensure(type(blockers) is list and len(blockers)>=4 and all(type(x) is str and len(x)>19 for x in blockers),
               "falsifiers missing "+id)
    ensure(seen==set(QUESTIONS),"missing distinct test questions")
    evidence=d.get("completed_real_evidence")
    ensure(type(evidence) is list and len(evidence)==len(COMPLETED_REAL_KEYS),"completed real experiments missing")
    visited=set()
    for record in evidence:
        ensure(type(record) is dict,"historical source record type")
        key=record.get("key")
        ensure(type(key) is str and key in COMPLETED_REAL_KEYS and key not in visited,
               "duplicate or invented historical experiment")
        visited.add(key)
        ensure(record.get("classification")==COMPLETED_REAL_KEYS[key],"historical result promoted: "+key)
        ensure((record.get("source"),record.get("source_ref"))==HISTORICAL_SOURCES[key],"source lineage changed: "+key)
        for field in ("lane","measurement","result","new_experiment"):
            minimum = 2 if field=="new_experiment" else (8 if field=="lane" else 16)
            ensure(type(record.get(field)) is str and len(record[field])>=minimum,
                   "missing scope for "+key+"/"+field)
        ensure("TARGET_WINNER" not in record.get("classification","") or "NOT_CURRENT" in record["classification"],
               "real winner falsely selected")
    ensure(visited==set(COMPLETED_REAL_KEYS),"missing source class")
    ensure("C3_QUERY_MEASURED" in {x["family"] for x in items},"q-measured C3 absent")
    ensure("RARE_SPECIALIST_NOT_C3" in {x["family"] for x in items},"rare being mislabeled C3")
    for field in ("next_executable_science","deferrals"):
        arr=d.get(field)
        ensure(type(arr) is list and len(arr)>=4 and all(type(x) is str and len(x)>35 for x in arr),
               "no safe next-step or stopping boundary "+field)
    for marker in ("No real human candidate evaluation","No biological state or TF selected","No real training"):
        ensure(any(marker in x for x in d["deferrals"]),"lost refusal "+marker)
    doc=(root/DOCUMENT)
    ensure(doc.is_file(),"narrative crosswalk missing")
    txt=doc.read_text(encoding="utf-8")
    for term in ("PR #315","PR #328","PR #313","PRs #332/#351","PR #451","GSE301119",
                 "GSE311359","GSE178317","SCENIC+","NOT_ESTIMABLE","same-","G7",
                 "C3_QUERY_MEASURED","nearest-third","R5","V44","feature mapping defect",
                 "PR #314","CORRECTED_RELATIONAL_PROGRAM_CONSISTENT_WITH_HISTORICAL_SCALE_BRACKET",AUTH):
        ensure(term in txt,"source restriction absent in narrative "+term)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[2])
    a=ap.parse_args()
    validate(json.loads((a.repo_root/MACHINE).read_text(encoding="utf-8")),a.repo_root)
    print("BIOLOGY_SYNTHETIC_CROSSWALK_V1_PASS__SOURCE_LIMITED__NO_TARGET_PROMOTION")
if __name__=="__main__":
    main()
