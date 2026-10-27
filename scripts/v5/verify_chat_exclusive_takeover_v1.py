"""Fail-closed *static* audit of 2026-10-27 chat-exclusive source custody.

This verifies claims in committed archive metadata; it cannot rehash binary
attachments that are not present on GitHub or attest to biological authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path("results/target_discovery/chat_exclusive_takeover_20261027/CHAT_LOCAL_SOURCE_SHA256_INVENTORY_V1.json")
CAL = Path("results/production_synthetic/JEPA_HISTORICAL_FOUNDATION_CALIBRATION_INTAKE_DELTA_20261027.json")
DOC = Path("docs/agent/JEPA_CHAT_EXCLUSIVE_LANE_TAKEOVER_V1_20261027.md")
V2 = Path("docs/agent/chat_exclusive_20261027/20261027_G7_LOCAL_HEADER_RESULT_V2_CORRECTED.json")
V1 = Path("docs/agent/chat_exclusive_20261027/20261027_G7_LOCAL_HEADER_RESULT_V1_SUPERSEDED.json")
AUTH = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
EXPECTED = {
    "FOUNDATION_CALIBRATION_BUNDLE_20260824.zip": ("07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444",410278055),
    "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001": ("b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e",303979881),
    "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002": ("5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875",303979880),
    "checkpoints.zip": ("ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c",71356460),
    "expression.zip": ("1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4",3599456),
    "t1_checkpoint_u0200.zip": ("0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c",233729581),
    "66e64913-959f-4a7c-bbfe-6ff906fb281d.npz": ("001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70",1531109),
    "Status and Repair Plan.txt": ("cb2befc374e4b594fb6d04bbb7c30a0ca702913ddc9d568fbfbf8ebca7bb7c56",5233),
    "WSL execution issue.txt": ("cd1c50bbec4c80b9b35f1824bba9112c7dbb357ede586b0a46e98532f57e474e",14576),
    "Pasted text.txt": ("d08e24d481e77a89ebf07428601fe6c54759a9050adf58346d0fa6cb5281a549",12541),
    "g7_local_input_probe_20261027.py": ("7950aff2d60da0a183458a2e4fdb61b79ade5d13457b410652ced83436ed701a",4391),
    "g7_local_input_probe_v2_20261027.py": ("0ab516508d416ac54493774fa862c639b670e6260edbc4586ebd5e36a075f9af",4539),
    "g7_local_input_admissibility_20261027.json": ("c89ad29b43f2f4823dc0e65d8c920cb15af861ac6f27fbe7971627caa0a32d85",2835),
    "g7_local_input_admissibility_v2_20261027.json": ("bec516bd425bb88cd4fcc394babe864e386afedde6b1552bbd1ffe24459c1670",2952),
}
BINARY = {
    "FOUNDATION_CALIBRATION_BUNDLE_20260824.zip",
    "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001",
    "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002",
    "checkpoints.zip", "expression.zip", "t1_checkpoint_u0200.zip",
    "66e64913-959f-4a7c-bbfe-6ff906fb281d.npz",
}

def ensure(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("CHAT_EXCLUSIVE_TAKEOVER_NO_PROMOTION_REFUSAL: "+reason)

def verify_record(inv: dict, cal: dict, v1: dict, v2: dict, doc: str) -> None:
    ensure(type(inv) is dict and inv.get("schema")=="JEPA_CHAT_ONLY_HISTORICAL_SOURCE_ASSET_LEDGER_V1","asset ledger schema")
    records=inv.get("files")
    ensure(type(records) is list and len(records)==20 and inv.get("total_local_files")==20,"all 20 source files")
    ensure(all(type(x) is dict and type(x.get("name")) is str and
               type(x.get("bytes")) is int and type(x.get("sha256")) is str and
               len(x["sha256"])==64 for x in records),"typed source digest/length")
    names=[x["name"] for x in records]
    ensure(len(set(names))==20,"duplicate source identity")
    by_name={x["name"]:x for x in records}
    for n,(sha,size) in EXPECTED.items():
        ensure(n in by_name and by_name[n]["sha256"]==sha and by_name[n]["bytes"]==size,
               "file identity rewritten: "+n)
    for n in BINARY:
        ensure("HASH_ONLY_IN_THIS_REPO" in by_name[n].get("custody",""),
               "human binary bytes falsely claimed copied: "+n)
    ensure(inv.get("current_authority")==AUTH,"asset ledger authorizes training")
    ensure(inv.get("archival_scope")=="CHAT_LOCAL_FILE_SHA256_INVENTORY_NOT_A_PERMANENT_BINARY_STORAGE_COPY",
           "raw file durability overclaim")
    ensure(v1.get("schema")=="JEPA_G7_LOCAL_ARCHIVE_ADMISSIBILITY_PROBE_20261027","V1 schema")
    ensure(v2.get("schema")=="JEPA_G7_LOCAL_ARCHIVE_ADMISSIBILITY_PROBE_V2_20261027","V2 schema")
    ensure(v1.get("assessment")==v2.get("assessment")=="INSUFFICIENT_TO_AUTHORIZE_AUTHENTIC_G7_E3",
           "V1/V2 G7 scope promoted")
    ensure(v1.get("expression_zip",{}).get("expression_read_before_freeze_is_selection_field") is True,
           "V1 historical wording erased")
    ensure(v2.get("expression_zip",{}).get("expression_read_before_freeze_column_present") is True
           and "expression_read_before_freeze_is_selection_field" not in v2.get("expression_zip",{}),
           "corrected V2 semantic caution erased")
    ensure(v2.get("authorization")==AUTH,"V2 G7 authorized")
    ensure(cal.get("schema")=="JEPA_HISTORICAL_FOUNDATION_CALIBRATION_INTAKE_DELTA_V1",
           "calibration audit schema")
    physical=cal.get("physical_verification",{})
    ensure(physical.get("logical_file_count")==physical.get("verified_member_sha256_count")==97,
           "historical 97/97 verification removed")
    ensure(physical.get("historical_manifest_sha256")==
           "da7c3daf507a66118131e88ae6685cf43eb14d4163539ade5e0705f6fb845cef",
           "manifest hash changed")
    ci=cal.get("ci",{})
    ensure(ci.get("synthetic_archive_hostile_run")==40571088557 and
           ci.get("synthetic_archive_hostile_cases_passed")==7 and
           ci.get("synthetic_archive_hostile_conclusion")=="SUCCESS",
           "PR471 hosted synthetic suite misreported")
    ensure(ci.get("real_source_reauthentication_by_ci") is False and
           ci.get("independent_scientific_acceptance") is False,
           "PR471 full source rights improperly claimed")
    ensure(cal.get("authority")==AUTH,"calibration promoted")
    for phrase in (
        "PR #314", "PR #328", "PR #369", "PR #437", "PR #469", "PR #470", "PR #471",
        "Macha", "C3=query-measured", "97/97", "R1/R2", "V3.1.1",
        "NO", "no-repeat", "NOT", "SOURCE",
    ):
        ensure(phrase.casefold() in doc.casefold(),"missing no-repeat navigation: "+phrase)
    ensure(AUTH in doc, "no hard training stop")

def validate_root(root: Path) -> None:
    verify_record(
        json.loads((root/DATA).read_text()),
        json.loads((root/CAL).read_text()),
        json.loads((root/V1).read_text()),
        json.loads((root/V2).read_text()),
        (root/DOC).read_text(),
    )
    required=[
        "docs/agent/chat_exclusive_20261027/20260811_WSL_EXECUTION_ISSUE_ARCHITECTURE_NOTES_ORIGINAL.txt",
        "docs/agent/chat_exclusive_20261027/20260912_STATUS_AND_REPAIR_PLAN_ORIGINAL.txt",
        "docs/agent/chat_exclusive_20261027/20261027_G7_LOCAL_HEADER_PROBE_V1_SUPERSEDED.py",
        "docs/agent/chat_exclusive_20261027/20261027_G7_LOCAL_HEADER_PROBE_V2_CORRECTED.py",
        "docs/agent/chat_exclusive_20261027/20261027_G7_LOCAL_V1_V2_SUPERSESSION_AUDIT.md",
    ]
    for p in required:
        ensure((root/p).is_file(),"missing preserved source: "+p)
    v1source=(root/required[2]).read_text()
    v2source=(root/required[3]).read_text()
    ensure("G7_LOCAL_METADATA_PROBE_PASS" in v1source
           and "G7_LOCAL_METADATA_INSPECTION_COMPLETE__G7_E3_UNQUALIFIED" in v2source,
           "original wrong-pass historical guard changed")
    ensure("expression_read_before_freeze_column_present" in v2source,
           "corrected local probe removed")

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo-root",type=Path,default=ROOT)
    a=parser.parse_args()
    validate_root(a.repo_root)
    print("JEPA_CHAT_EXCLUSIVE_SOURCES_20__HISTORICAL_97_SHA__G7_V2_NO_AUTHORITY__TAKEOVER_PASS")

if __name__=="__main__":
    main()
