"""Event90 two-branch source and new-agent handoff custody checks.

Read-only, no GitHub network, no data reading, no model import, no training.
This is a local snapshot consistency validator, NOT a private-source or
scientific acceptance verifier and NOT an exact cross-branch network check.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha1
import json
from pathlib import Path
import re
from typing import Mapping

MAP = ("results/target_discovery/unified_qualification_v1/"
       "JEPA_20261105_EVENT90_TWO_BRANCH_TAKEOVER_MAP.json")
HUMAN = ("docs/agent/"
         "JEPA_20261105_EVENT90_COMPLETE_SOURCE_SCRIPT_DATA_RESULT_AND_AGENT_TAKEOVER.md")
LEDGER = ("results/target_discovery/unified_qualification_v1/"
          "JEPA_CONTINUOUS_CHRONOLOGY_PROGRESS_V1.json")
INDEX = ("results/target_discovery/unified_qualification_v1/"
         "JEPA_20261104_MASTER_PRIMARY_SOURCE_NO_REPEAT_INDEX_V1.json")
HANDOFF = "docs/agent/JEPA_NEW_AGENT_LIVE_POINTER_20261029.md"
AUTHORITY = (
    "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__"
    "STAGE4_NOT_AUTHORIZED"
)
AUDIT_BRANCH = "science/jepa-robust-pipeline-post-jepa-anything-audit-20261013"
HANDOFF_BRANCH = "handoff/jepa-v8-clean-successor-from-audit-20261027"
HUMAN_SHA = "a33ed0cdd8af86e078dc115d3e7c820ebb2da94a"
EVENT90_INDEX_KEY = (
    "event90_complete_audit_handoff_source_script_data_result_continuity_20261105"
)
RED_SHA = {
    557: "bfa5345775570205def66eb19a98efc207d28d90",
    560: "3ab6c208206251728116debda1edb226cb5b647a",
    561: "be259ab4cdcf035d7bf05134f68b6fe8d09f8833",
    566: "60a16378c22b35ec5d52837c7c641cf6a59e0935",
    567: "c513693fa11b2c0ef72b68601ca83dcd5a0a5b2f",
}
REQUIRED_PUBLIC = (
    "docs/agent/JEPA_20261104_END_TO_END_SCIENTIFIC_NARRATIVE_AND_DECISION_LINEAGE_V1.md",
    "docs/agent/JEPA_20261104_V9_PREVIOUS_WORK_UNDERINDEXING_CORRECTION_V1.md",
    "docs/agent/JEPA_20261104_SOL_LANE_SUCCESSOR_DETAILED_OPERATIONAL_HANDOFF_EVENT68.md",
    "results/target_discovery/unified_qualification_v1/JEPA_20261104_SOL_LANE_SUCCESSOR_SOURCE_SCRIPT_DATA_RESULT_LOCATOR_EVENT68.json",
    "results/target_discovery/unified_qualification_v1/JEPA_20261104_COMPLETE_535_PR_AND_OPEN_ISSUE_METADATA_CENSUS_V1.json",
    "results/target_discovery/unified_qualification_v1/JEPA_20261104_LAST_14_DAYS_108_PR_RESULT_PRECEDENCE_AND_NO_REPEAT_V1.json",
)


def insist(value: object, reason: str) -> None:
    if not bool(value):
        raise ValueError("REFUSE_EVENT90_HANDOFF_CUSTODY__" + reason)


def _blob(raw: bytes) -> str:
    return sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _relative(value: object) -> str:
    insist(type(value) is str and value != "", "EMPTY_SOURCE_PATH")
    path = Path(value)
    insist(not path.is_absolute() and
           all(item not in (".", "..") for item in path.parts)
           and not value.startswith("./"), "UNSAFE_SOURCE_PATH")
    return value


def validate_manifest(map_data: object, human_bytes: bytes) -> dict:
    """Check source identity, exact gates, original reviewer tests and limits.

    Pure, easy to RED-test with mutated in-memory map. Source files not
    present on this checkout are treated as referenced historical/external
    paths, not interpreted as never implemented.
    """
    insist(type(map_data) is dict, "MAP_NOT_OBJECT")
    m = map_data
    insist(m.get("schema") ==
           "JEPA_EVENT90_COMPLETE_TWO_BRANCH_HISTORY_SOURCE_AND_OPERATIONAL_TAKEOVER_V1",
           "MAP_SCHEMA")
    insist(m.get("authority") == AUTHORITY, "AUTHORITY_CHANGED")
    insist(m.get("repository") == "dushyant-mishra/sea-ad-jepa-agent",
           "REPOSITORY_CHANGED")
    contract = m.get("branch_contract")
    insist(type(contract) is dict, "NO_BRANCH_CONTRACT")
    a, h = contract.get("canonical_audit"), contract.get("active_handoff")
    insist(type(a) is dict and a.get("pr") == 322
           and a.get("branch") == AUDIT_BRANCH, "AUDIT_BRANCH_CHANGED")
    insist(type(h) is dict and h.get("pr") == 460
           and h.get("branch") == HANDOFF_BRANCH, "HANDOFF_BRANCH_CHANGED")
    insist(a.get("chronology_path") == LEDGER
           and a.get("master_index_path") == INDEX
           and a.get("chronology_prior_events") == 89
           and a.get("expected_after_event90") == 90
           and a.get("index_prior_keys") == 54
           and a.get("expected_after_event90") is not None
           and a.get("expected_after_event90") == 90
           and a.get("expected_after_event90") - 1 ==
           a.get("chronology_prior_events")
           and a.get("index_prior_keys") + 1 == 55
           and a.get("expected_after_event90") == 90,
           "HISTORY_EVENT_DELTA_INVALID")
    insist(a.get("expected_after_event90") == 90 and
           a.get("index_prior_keys") == 54, "HISTORY_BASELINE")
    insist(h.get("live_first_read") == HANDOFF
           and h.get("update_after_audit_exact_head") is True,
           "LATEST_HANDOFF_POINTER_MISSING")
    human = contract.get("human_mirror")
    insist(type(human) is dict and human.get("path") == HUMAN
           and human.get("git_blob_sha1") == HUMAN_SHA
           and human.get("same_blob_on_both") is True
           and _blob(human_bytes) == HUMAN_SHA,
           "MIRRORED_HUMAN_BLOB_CHANGED")
    text = human_bytes.decode("utf-8")
    for clause in ("#322", "#460", "canonical_v5_runtime",
                   "V80 SEALED", "ATTEMPT_BEGIN",
                   "event", "NO TRAINING", "Event90"):
        insist(clause.lower() in text.lower(), "MISSING_CRITICAL_HUMAN_CLAUSE")
    insist(AUTHORITY in text, "HUMAN_AUTHORITY_MISSING")
    history = m.get("historical_scope")
    insist(type(history) is dict and
           history.get("source_locator_60", "").endswith(
               "JEPA_20261104_SOL_LANE_SUCCESSOR_SOURCE_SCRIPT_DATA_RESULT_LOCATOR_EVENT68.json"),
           "HISTORICAL_SOURCE_LOCATOR_MISSING")
    counts = history.get("locator_counts")
    insist(type(counts) is dict and counts == {
        "total": 60, "public_git_paths": 56,
        "found_at_recorded_ref": 55, "not_found_at_recorded_ref": 1,
        "owner_only_local_or_conversation": 4,
    }, "HISTORICAL_60_LOCATOR_COUNTS")
    for path in (history.get("historical_pr_census"),
                 history.get("recent_108_supersession")):
        _relative(path)
    finding = m.get("extra_finding")
    insist(type(finding) is dict
           and finding.get("legacy_id") == "canonical_v5_runtime"
           and finding.get("legacy_path") ==
           "src/sea_ad_jepa/v5/canonical_runtime.py"
           and finding.get("status", "").startswith("ERRATUM_OPEN")
           and finding.get("do_not_substitute_or_edit_old_record") is True,
           "BAD_OR_MISSING_SOURCE_ERRATUM")
    data = m.get("data_and_expiry")
    insist(type(data) is dict, "DATA_CUSTODY_MISSING")
    originals = data.get("v80_public_binaries_verified_on_both")
    insist(type(originals) is list and len(originals) == 2,
           "ORIGINAL_V80_PUBLIC_ARCHIVES_MISSING")
    sha = {x.get("role"): x.get("git_blob") for x in originals}
    insist(sha == {
        "ORIGINAL_FIT": "8b81742b66dfd7d2d40940933c7775a515e0610d",
        "ORIGINAL_RECEIPT": "4ec0e2eed6eba099645638232f3962482ae2dc26",
    }, "V80_FIT_RECEIPT_BLOBS_CHANGED")
    for x in originals:
        _relative(x["path"])
    ctrl = data.get("v80_controller_owner_only")
    insist(type(ctrl) is dict and ctrl.get("original_artifact_id") == 11866917064
           and ctrl.get("verified_private_vault") is False
           and ctrl.get("expires_at_utc") == "2026-11-13T03:01:58Z"
           and "NEVER_PUBLIC" in ctrl.get("status", ""),
           "PRIVATE_CONTROLLER_BOUNDARY_MISSING")
    dev = data.get("synthetic_dev2048_fit")
    insist(type(dev) is dict and dev.get("artifact_id") == 13364085153
           and dev.get("expires_at_utc") == "2026-12-04T21:02:06Z"
           and "NOT_HUMAN_RNA" in dev.get("scope", ""),
           "SYNTHETIC_FIT_EXPIRY_OR_SCOPE")
    read = m.get("historical_navigation")
    insist(type(read) is list and len(read) >= 10
           and len({x["role"] for x in read}) == len(read),
           "HISTORICAL_NAVIGATION_UNDERSPECIFIED")
    insist(all(x.get("pr") in (322, 460) and
               _relative(x.get("path"))
               for x in read), "BAD_HISTORICAL_NAV_SOURCE")
    prs = m.get("implementation_heads_20261105")
    insist(type(prs) is list and len(prs) >= 18
           and len({x["pr"] for x in prs}) == len(prs),
           "PR_COVERAGE_OR_DUPLICATE")
    heads = {p["pr"]: p["head"] for p in prs}
    insist(heads.get(570) == "0e2deffa0191ddfc8b11161a85224e6367d97c22"
           and heads.get(571) == "8656adcf7e96b1e9c52a598beb844f8f8f548644"
           and all(type(x) is str and re.fullmatch("[a-f0-9]{40}", x)
                   for x in heads.values()),
           "IMPLEMENTATION_HEAD_CHANGED")
    red = m.get("macha_original_red_immutable")
    insist(type(red) is list and
           {r["pr"]: r["blob"] for r in red} == RED_SHA,
           "ORIGINAL_MACHA_RED_DRIFT")
    ci = m.get("newest_ci")
    insist(type(ci) is dict and
           ci.get("v2_journal", {}).get("run") == 42062323739
           and ci["v2_journal"]["py311"] == 223
           and ci["v2_journal"]["py312"] == 223
           and ci.get("read_only_state", {}).get("run") == 42066951548
           and ci["read_only_state"]["py311"] == 28
           and ci["read_only_state"]["py312"] == 28
           and ci.get("independent_scoped_acceptance") == "PENDING",
           "AUTHOR_CI_MISLABELED_ACCEPTED")
    frontier = m.get("implementation_frontier")
    insist(type(frontier) is list and len(frontier) >= 7
           and any("RT1" in x and "permission" in x for x in frontier),
           "RESTART_AUTHORIZATION_NOT_PRESERVED")
    rules = m.get("permanent_two_branch_rule")
    insist(type(rules) is dict and rules.get("next_event_id") == 91
           and "append only" in rules.get("audit", "")
           and "Sol/Macha" in rules.get("independent_review", "")
           and len(rules.get("required_next_agent_packet", [])) >= 8,
           "FUTURE_HANDOFF_PROTOCOL_MISSING")
    return {
        "result": "EVENT90_HUMAN_MACHINE_SOURCE_LIMITS_VERIFIED",
        "source_paths_reachable_at_historical_refs": 55,
        "source_paths_known_bad": 1,
        "owner_only_unverified": 4,
        "training_authorized": False,
        "biological_qualification_proved": False,
        "authority": AUTHORITY,
    }


def validate_repository(root: Path, *, role: str) -> dict:
    insist(role in ("audit", "handoff"), "UNSUPPORTED_REPOSITORY_ROLE")
    root = Path(root)
    human = (root / HUMAN).read_bytes()
    m = json.loads((root / MAP).read_text(encoding="utf-8"))
    report = validate_manifest(m, human)
    if role == "audit":
        chronology = json.loads((root / LEDGER).read_text(encoding="utf-8"))
        entries = chronology.get("records")
        insist(type(entries) is list and len(entries) >= 90,
               "AUDIT_CHRONOLOGY_NOT_APPENDED")
        ids = [e.get("event_id") for e in entries]
        insist(len(set(ids)) == len(ids), "DUPLICATE_HISTORY_EVENT_ID")
        insist("20261105-EVENT90" in ids[-1] or
               any("EVENT90" in x for x in ids[89:]),
               "EVENT90_NOT_APPENDED")
        first89 = entries[:89]
        insist(all(type(x) is dict and "authority_after" in x
                   and x["authority_after"] == AUTHORITY
                   for x in first89[1:]),
               "HISTORICAL_AUTHORITY_CHANGED")
        index = json.loads((root / INDEX).read_text(encoding="utf-8"))
        insist(type(index) is dict and len(index) >= 55
               and index.get("root_authority") == AUTHORITY
               and EVENT90_INDEX_KEY in index,
               "INDEX_EVENT90_MISSING")
        ev90 = next(e for e in entries if "EVENT90" in e["event_id"])
        source_map = {
            s.get("path"): s.get("blob_sha1")
            for s in ev90.get("source_inputs", [])
        }
        insist(source_map.get(HUMAN) == HUMAN_SHA,
               "EVENT90_HUMAN_SOURCE_SHA_DRIFT")
        for item in REQUIRED_PUBLIC:
            insist((root / _relative(item)).is_file(),
                   "MISSING_HISTORICAL_ORIGINAL_SOURCE")
    else:
        text = (root / HANDOFF).read_text(encoding="utf-8")
        latest = re.match(r"# READ FIRST — EVENT([0-9]+)", text)
        insist(latest is not None and int(latest.group(1)) >= 90,
               "HANDOFF_NOT_PREPENDED_TO_LATEST")
        top = text.split("\n---\n", 1)[0]
        insist("#322" in top and "#460" in top and HUMAN in top
               and MAP in top and AUTHORITY in top,
               "HANDOFF_NEW_FIRST_READ_INCOMPLETE")
        insist(re.search(r"Audit head [a-f0-9]{40}", top) is not None,
               "HANDOFF_EXACT_AUDIT_HEAD_MISSING")
    return dict(report, role=role)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--role", choices=("audit", "handoff"), required=True)
    args = parser.parse_args()
    print(json.dumps(validate_repository(Path(args.root), role=args.role),
                     sort_keys=True))


if __name__ == "__main__":
    main()
