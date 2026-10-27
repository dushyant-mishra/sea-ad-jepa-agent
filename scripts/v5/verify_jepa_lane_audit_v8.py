"""V8 read-only JEPA audit/custody validator; no data fetch or authority issuance.

Tests static identity, anti-promotion and historical no-repeat bookkeeping.
It never authenticates external issuer/custody, protected data or biology.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

TERMINAL = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
SNAPSHOT = "results/target_discovery/unified_qualification_v1/JEPA_LANE_AUDIT_SNAPSHOT_V8_20261027.json"
ASSETS = "docs/agent/JEPA_LOCAL_ATTACHMENT_CUSTODY_RECONCILIATION_V8_20261027.csv"
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
    with assets.open(encoding="utf-8", newline="") as fh:
        validate_assets(list(csv.DictReader(fh)))
    for path in MANDATORY_OLD_PATHS:
        require((root/path).is_file(), "historical audit missing: " + path)
    print("JEPA_V8_STATIC_AUDIT_PASS__HISTORICAL_SOURCES_PRESENT__NO_AUTHORITY_ISSUED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
