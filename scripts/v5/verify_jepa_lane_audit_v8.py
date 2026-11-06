"""V8 read-only JEPA audit/custody validator; no data fetch or authority issuance.

Tests static identity, anti-promotion and historical no-repeat bookkeeping.
It never authenticates external issuer/custody, protected data or biology.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

TERMINAL = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
SNAPSHOT = "results/target_discovery/unified_qualification_v1/JEPA_LANE_AUDIT_SNAPSHOT_V8_20261027.json"
ASSETS = "docs/agent/JEPA_LOCAL_ATTACHMENT_CUSTODY_RECONCILIATION_V8_20261027.csv"
POST_V8A = "results/target_discovery/unified_qualification_v1/JEPA_POST_V8_SNAPSHOT_DELTA_V8A_20261027.json"
SHA = re.compile(r"^[a-f0-9]{40}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
REQUIRED_PR_STATUS = {
    428:"UNIFIED_TASK4_CUMULATIVE_NOT_ACCEPTED",
    433:"G7_E3_REJECTED",
    437:"PS_TASK3_FIXTURE_ACCEPT_WITH_LIMITATIONS_OLD_DEPENDENCY",
    438:"FOUR_WORLD_SCIENCE_REJECTED_CLOSED",
    439:"TASK3_HOSTILE_RED_PRESERVED",
    440:"TASK5_FIXTURE_NOT_A7",
    441:"G7_HOSTILE_RED",
    442:"FOUR_WORLD_HOSTILE_RED",
    443:"TASK4_STALE_WRITER_RED",
    444:"POST_TD_BRIDGE_REJECTED_ORIGINAL",
    445:"TASK4_INCREMENT_REJECTED_AFTER_MACHAS_RECHECK",
    446:"G7_E3_REPAIR_REJECTED",
    447:"UNIFIED_TASKS6_8_FIXTURE_CANDIDATE_NO_AUTHORITY",
    448:"PS_TASK1_AUTHOR_DISCLOSED_RED",
    449:"G7_REPAIR_HOSTILE_RED",
    450:"POST_TD_BRIDGE_HOSTILE_RED",
    451:"TASK5_BRIDGE_INCREMENT_ACCEPT_LIMITS",
    452:"TASK4_X1_X2_X3_X5_X6_HOSTILE_RED",
    453:"PS_TASK1_REPAIR_GREEN_CUMULATIVE_REVIEW_OPEN",
    454:"TASK4_X1_RED_X3_OPEN",
    455:"PS_TASK2_INDEPENDENT_RED",
    456:"PS_TASK2_REPAIR_GREEN_CUMULATIVE_REVIEW_OPEN",
}
MANDATORY_OLD_PATHS = (
    "docs/agent/JEPA_LANE_AUDIT_SNAPSHOT_V7_20261017.md",
    "docs/agent/JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.md",
    "docs/agent/JEPA_GENE_IDENTITY_RECLASSIFICATION_AUDIT_20261013.md",
    "docs/agent/JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_20261013.csv",
    "docs/agent/JEPA_LANE_MASTER_AUDIT_INDEX_20261014.md",
    "results/target_discovery/unified_qualification_v1/JEPA_LANE_AUDIT_SNAPSHOT_V7_20261017.json",
)
DATA_POLICY = {
    "EXTERNAL_RAW_ONLY", "RECONSTRUCT_FROM_PARTS",
    "GIT_SNAPSHOT_ALREADY_EXISTS", "PROJECT_LOCAL_UNIMPORTED_EXACT_BYTES",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_snapshot(doc: object) -> None:
    require(type(doc) is dict and doc.get("schema") == "JEPA_AUDIT_LANE_V8_SNAPSHOT_20261027", "wrong V8 schema")
    require(doc.get("as_of_utc_date") == "2026-10-27", "unexpected evidence snapshot date")
    require(doc.get("authority") == TERMINAL, "global no-promotion invariant changed")
    frozen = doc.get("frozen_accepted_unified_tasks_0_3")
    require(type(frozen) is dict and frozen.get("task3_sha") == "117dd51dea827e734b299982da93991b934bdc8f", "Task3 frozen head changed")
    for key in ("audit_prior_head","handoff_prior_head"):
        require(type(doc.get(key)) is str and bool(SHA.fullmatch(doc[key])), "invalid prior branch identity")
    gates = doc.get("release_gates")
    require(type(gates) is dict and len(gates) == 8, "incomplete gate roster")
    for k,value in gates.items():
        require(type(k) is str and type(value) is str and value != "", "empty gate refusal status")
    # This is a *fixed historical snapshot*: an attacker cannot replace a
    # refusal with semantically reversed "NO_RECHECK" text or green-looking
    # values that happen to contain the expected substring.
    expected_gates = {
        "unified_task4":"X1_EXTERNAL_PUBLISHER_REFUSAL_RED__X3_WINDOWS_WSL_CROSS_LOCK_UNQUALIFIED__CUMULATIVE_INDEPENDENT_ACCEPTANCE_MISSING",
        "unified_task5":"TASK5_FIXTURE_ONLY__A7_SAME_CODE_PATH_NOT_QUALIFIED",
        "unified_tasks6_8":"NONPROMOTING_FIXTURES_ONLY__REAL_PRODUCER_AND_TARGET_RECEIPTS_MISSING",
        "real_g7_e3":"REJECTED__PHYSICAL_ATOM_AND_Q_EXCLUDED_DEPTH_AUTHENTICATION_MISSING",
        "ps_task1":"CHANGED_CANONICAL_DEPENDENCY__INDEPENDENT_CUMULATIVE_ACCEPTANCE_MISSING",
        "ps_task2":"CHANGED_CUSTODY_DEPENDENCY__INDEPENDENT_CUMULATIVE_ACCEPTANCE_MISSING",
        "ps_task3":"FIXTURE_MECHANICS_ACCEPTED_WITH_LIMITATIONS_OLD_DEPENDENCIES__RECHECK_NEEDED",
        "ps_task4":"DO_NOT_START_PENDING_TASKS1_3_INDEPENDENT_CHECKPOINT",
    }
    require(gates == expected_gates, "fixed historical acceptance or blockers changed")
    records = doc.get("records")
    require(type(records) is list and len(records) >= 30, "historical PR index incomplete")
    by_pr = {}
    for row in records:
        require(type(row) is dict and set(row) == {"pr","sha","classification","url"}, "inexact PR record")
        require(type(row["pr"]) is int and row["pr"] not in by_pr, "duplicate or invalid PR identity")
        require(type(row["sha"]) is str and bool(SHA.fullmatch(row["sha"])), "invalid PR exact head")
        require(type(row["classification"]) is str and row["classification"], "missing PR classification")
        require(row["url"] == f"https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/{row['pr']}", "PR link not exact")
        by_pr[row["pr"]] = row["classification"]
    for pr,status in REQUIRED_PR_STATUS.items():
        require(by_pr.get(pr) == status, f"missing or promoted historical PR #{pr}")
    hostile = doc.get("hostile_evidence")
    require(type(hostile) is dict and set(hostile.values()) <= set(by_pr), "missing hostile evidence PR")
    require(448 in hostile.values() and 455 in hostile.values(), "Task1/2 RED not retained")


def validate_post_v8a_delta(doc: object) -> None:
    """Require the post-snapshot independent RED and X1 green-but-unaccepted."""
    require(type(doc) is dict and doc.get("schema")=="JEPA_AUDIT_V8A_POST_SNAPSHOT_DELTA_20261027", "incorrect V8a schema")
    require(doc.get("authority")==TERMINAL and doc.get("cannot_upgrade_from_ci") is True, "V8a scientific authority promotion")
    require(doc.get("original_v8_remains_immutable_historical_event") is True, "V8 history rewrite permitted")
    rows=doc.get("records")
    require(type(rows) is list and len(rows)==3, "V8a PR roster incomplete")
    by={r.get("pr"):r for r in rows if type(r) is dict}
    require(set(by)=={457,458,459}, "missing or duplicate PR 457–459")
    expected={
        457:("cd86187ec03092bdc9ebb17e36046ac8853b4fd1","E2G_SEVEN_PUBLIC_SOURCES_PROVISIONAL_COVERAGE_ONLY__RESULT_RECEIPT_CI_RED"),
        458:("3b08081d7fb3fa99cf1459b13cbe47d5b0962547","PS_TASKS1_2_SECOND_WAVE_INDEPENDENT_RED_13_TESTS__CUMULATIVE_REVIEW_BLOCKED"),
        459:("57e707149b46ca011eee096f01dc08b64aeb8f9f","TASK4_X1_WRITE_AHEAD_INTENT_CANDIDATE_CI_GREEN__INDEPENDENT_REVIEW_PENDING__X3_UNQUALIFIED"),
    }
    for pr,(sha,status) in expected.items():
        row=by[pr]
        require(row.get("sha")==sha and row.get("status")==status, f"post-V8 source identity or review status mutated: #{pr}")
        require(row.get("url")==f"https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/{pr}","invalid post-V8 URL")
        require(type(row.get("ci_green")) is list and type(row.get("ci_red")) is list, "missing full red/green distinction")
    require(40516953772 in by[458]["ci_red"] and 40517601114 in by[457]["ci_red"], "new RED evidence lost")
    require(40518058012 in by[459]["ci_green"], "unreviewed X1 candidate CI evidence lost")
    require("INDEPENDENT" in doc.get("clear_new_work",{}).get("task4",""), "Task4 nonauthor review omitted")
    require(doc.get("new_red_ci_counts",{}).get("ps_tasks_1_2",{}).get("failed")==13, "PS Task1/2 failed tests hidden")
    require(doc.get("task4_author_green_counts",{}).get("windows_focus")==49, "Windows engineering result altered")
    require(doc.get("handoff_clean_successor_pr")==460, "conflict-free successor pointer missing")


def validate_assets(rows: list[dict]) -> None:
    require(len(rows) >= 12, "asset archive inventory incomplete")
    names = set()
    for row in rows:
        require(set(row) == {"filename","size_bytes","sha256","github_or_external_custody","description"}, "asset inventory schema changed")
        name = row["filename"]
        require(name not in names and name and "/" not in name and "\\" not in name, "duplicate or unsafe asset filename")
        names.add(name)
        require(row["size_bytes"].isascii() and row["size_bytes"].isdigit() and int(row["size_bytes"]) > 0, "bad asset byte size")
        require(bool(SHA256.fullmatch(row["sha256"])), "bad raw asset sha256")
        require(row["github_or_external_custody"] in DATA_POLICY, "raw asset upload or unsupported policy")
    require("Pasted markdown.md" in names, "new private scientific brief not indexed")
    require({"FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001",
             "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002",
             "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip"} <= names, "41K transport incomplete")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--snapshot", type=Path, default=None)
    p.add_argument("--assets", type=Path, default=None)
    args = p.parse_args()
    root = args.repo_root
    snap = args.snapshot or root / SNAPSHOT
    assets = args.assets or root / ASSETS
    validate_snapshot(json.loads(snap.read_text(encoding="utf-8")))
    post_v8a = root / POST_V8A
    if post_v8a.is_file():
        validate_post_v8a_delta(json.loads(post_v8a.read_text(encoding="utf-8")))

    with assets.open(encoding="utf-8", newline="") as fh:
        validate_assets(list(csv.DictReader(fh)))
    for path in MANDATORY_OLD_PATHS:
        require((root/path).is_file(), "historical audit missing: " + path)
    exact_imports = {
        "docs/agent/external_context/JEPA_PROBABILISTIC_ANTI_COLLAPSE_BRIEF_SOURCE_UNREVIEWED_20261026.md":"3423d3ba7feb023e25815f0355fcf355ade1a79ceec16dc2c8824700a0552a8d",
        "docs/agent/historical_imports/JEPA_PRIOR_TAKEOVER_TEXT_V4_20261017.md":"ba2e41dcf96247c12559ccf3bf872447e5b2b467f5b9dfcce14dac7fbfe95020",
    }
    for rel, recorded_sha in exact_imports.items():
        src = root / rel
        require(src.is_file(), "previously chat-only text missing: " + rel)
        require(hashlib.sha256(src.read_bytes()).hexdigest() == recorded_sha,
                "historical imported text bytes changed: " + rel)
    print("JEPA_V8_STATIC_AUDIT_PASS__HISTORICAL_SOURCES_PRESENT__NO_AUTHORITY_ISSUED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
