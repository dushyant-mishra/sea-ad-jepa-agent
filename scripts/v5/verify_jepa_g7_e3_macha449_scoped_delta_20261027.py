"""Fail-closed static custody of the appended G7 E3 scoped evidence delta.

This verifies an archived GitHub source/CI *claim inventory*, not physical
measurement identity, q-excluded depth, real G7 authority or science results.
It makes no GitHub calls and cannot independently authenticate issuers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RELATIVE = Path("results/target_discovery/unified_qualification_v1/JEPA_G7_E3_MACHA449_SCOPED_DELTA_20261027.json")
STANDING = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
SOURCE_REVIEW = "062bfe369348ac4d9ed89c0aa162abf0d9806397"
SOURCE_REPAIR = "2e173fa4889531ba686aa439707cf86effd6cc95"
EXACT_BLOBS = {
    "macha_recheck_git_blob": "02b7923e42df901c5f14bb757c44e5fb3cfa1373",
    "macha_original_hostile_git_blob": "efaf84b0fb6fe22ad199e677e546ad27fee42c08",
    "original_base_git_blob": "d28ca093f8b50c422f01e2182c93816222890121",
    "real_g7_v3_executor_git_blob": "b9a232011f370d89038edadfd053a9333230acbe",
}
SCOPED = {
    "R3": "Reject non-injective V3 source::donor keys",
    "R4": "Carry both explicit false physical identity",
    "R5": "Bound canonical JSON nesting",
}
REDS = {
    "R1": "BLOCKED_EXTERNAL_PHYSICAL_ATOM_IDENTITY",
    "R2": "BLOCKED_EXTERNAL_Q_EXCLUDED_LIBRARY_PROVENANCE",
}

def check(flag: bool, reason: str) -> None:
    if not flag:
        raise ValueError("G7_E3_AUDIT_NONPROMOTION_REFUSAL: " + reason)

def validate(data: dict) -> None:
    check(type(data) is dict and data.get("schema") ==
          "JEPA_G7_E3_MACHA449_SCOPED_DELTA_V1", "schema")
    check(data.get("document_kind") ==
          "APPEND_ONLY_HISTORICAL_AUDIT_DELTA__CANDIDATE_NOT_ACCEPTANCE", "status")
    check(data.get("authority") == STANDING, "unauthorized promotion")
    a=data.get("parent_qualified_audit", {})
    check(a == {"pr": 322,
                "previous_head": "a271164554076d0acda3bd0cf0b1bf957c0fdfd3",
                "previously_qualified_head_unchanged": True}, "audit previous SHA")
    check(data.get("handoff") == {"pr": 460,
          "previous_head": "b867a348d9244bcbc9d4ac696ebc0df6f325b6f8"}, "handoff previous SHA")
    review=data.get("source_review", {})
    check(review.get("pr") == 449 and review.get("head") == SOURCE_REVIEW
          and review.get("reviewer") == "MACHA"
          and review.get("verdict") == "HOSTILE_RED_13_CASES", "historical Macha red")
    repair=data.get("repair_candidate", {})
    check(repair.get("pr") == 470 and repair.get("head") == SOURCE_REPAIR
          and repair.get("base_pr") == 449
          and repair.get("status") == "AUTHOR_CANDIDATE__INDEPENDENT_REVIEW_OUTSTANDING",
          "patch not independently accepted")
    check(data.get("unchanged_tests") == EXACT_BLOBS, "hostile test or consumer drift")
    changes=data.get("changes")
    check(type(changes) is list and len(changes) == 3, "scoped fixes")
    for row in changes:
        name=row.get("finding") if type(row) is dict else None
        check(name in SCOPED and SCOPED[name] in row.get("action", "") and
              row.get("classification") == "SCOPED_IMPLEMENTATION_ATTEMPT" and
              row.get("independent_acceptance") is False, "scope or acceptance forged")
    check({r["finding"] for r in changes} == set(SCOPED), "fix enumeration")
    residual=data.get("known_unresolved")
    check(type(residual) is list and len(residual) == 2, "all physical blockers")
    check({r.get("finding"):r.get("classification") for r in residual
           if type(r) is dict} == REDS, "original ten red cannot disappear")
    for row in residual:
        check(row.get("must_remain_red") is True and len(row.get("reason", "")) > 70,
              "R1/R2 fail closed")
    ci=data.get("ci", {})
    check(ci.get("scoped_run_id") == 40566765654 and
          ci.get("scoped_conclusion") == "SUCCESS" and
          ci.get("scoped_passed") == 45 and
          ci.get("scoped_deselected") == 10, "scoped receipt changed")
    check(ci.get("full_run_id") == 40566765636 and
          ci.get("full_conclusion") == "FAILURE" and
          ci.get("full_passed") == 45 and ci.get("full_failed") == 10,
          "controlling original red changed")
    check(ci.get("scoped_red_recheck_failures") == 10 and
          ci.get("scoped_red_recheck") ==
          "R1_R2_10_HOSTILE_RED_RETAINED__NO_PHYSICAL_OR_DEPTH_AUTHORITY",
          "unresolved hidden by scoped green")
    check(ci.get("original_R1_R2_authority") == "BLOCKED" and
          ci.get("independent_acceptance") is False and
          ci.get("no_promoting_inference") is True,
          "reported green as full biological authority")
    synthetic=data.get("synthetic_execution", {})
    check(synthetic.get("design_pr") == 344 and synthetic.get("pivot_pr") == 379 and
          synthetic.get("source_fixture_pr") == 328 and
          synthetic.get("interop_pr") == 469 and
          synthetic.get("status") == "NOT_FULL_KNOWN_TRUTH_QUALIFIED",
          "fixture promoted to production")
    science=data.get("target_science", {})
    check(science.get("historical_replay_pr") == 314 and
          science.get("target_winner") == "NONE" and
          science.get("real_training_authorized") is False and
          "MEASURED_TARGET_CONSTRUCTOR" in science.get("teacher_guard", ""),
          "biological claim promoted")
    actions=data.get("review_actions")
    check(type(actions) is list and len(actions) >= 3 and
          all(type(x) is str and len(x) > 60 for x in actions),
          "reviewer obligations missing")

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args=parser.parse_args()
    p=args.repo_root/RELATIVE
    validate(json.loads(p.read_text(encoding="utf-8")))
    print("JEPA_G7_E3_SCOPED_AUDIT_DELTA_PASS__R1_R2_RED__NO_SCIENCE_PROMOTION")

if __name__ == "__main__":
    main()
