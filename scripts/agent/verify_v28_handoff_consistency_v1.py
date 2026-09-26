#!/usr/bin/env python3
"""Fail-closed consistency audit of the published V28 handoff ONLY.

This is a documentary metadata guard, not live GitHub verification, source-input
rehashing, V5 authority issuance, or proof of any biological result. Explicitly
refuses accidental promotion of S9/gradient counters/synthetic geometry, a
missing source or a falsely green training-authorization claim.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

EXPECTED_CALIBRATION = "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444"
EXPECTED_BAD_NPZ = "001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70"
DOCS = "docs/agent/"
POINTER = DOCS + "JEPA_LATEST_HANDOFF_POINTER.json"
STATE = DOCS + "JEPA_V28_VERIFIED_HANDOFF_STATE_20260926.json"
ASSETS = DOCS + "JEPA_V28_LOCAL_ASSETS_SHA256_20260926.json"
REQUIRED = ("handoff_path", "state_path", "evidence_index_path",
            "takeover_path", "local_sha_manifest_path")

def require(condition, code):
    if not condition:
        raise ValueError("STOP_V28_HANDOFF_" + code)

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def verify(root: Path):
    root = Path(root)
    pointer, state, manifest = [read_json(root / item) for item in (POINTER, STATE, ASSETS)]
    require(pointer.get("schema") == "JEPA_LATEST_HANDOFF_POINTER_V28_DOCS_ONLY",
            "WRONG_POINTER_SCHEMA")
    require(state.get("schema") == "JEPA_V28_VERIFIED_HANDOFF_STATE_V1",
            "WRONG_STATE_SCHEMA")
    require(pointer.get("main_V25_controls_until_reviewed_merge") is True and
            state.get("main_governance", "").startswith("V25_START_HERE"),
            "FALSE_MAIN_PROMOTION")
    require(state.get("main_controlling_head") == pointer.get("source_main_at_branch_creation"),
            "MAIN_ROOT_MISMATCH")
    require(all(isinstance(pointer.get(k), str) and
                pointer[k].startswith(DOCS) and (root / pointer[k]).is_file()
                for k in REQUIRED), "MISSING_REFERENCED_FILE")
    require(pointer["state_path"] == STATE and pointer["local_sha_manifest_path"] == ASSETS,
            "POINTER_ROLE_CROSSING")
    require(state["navigation"]["handoff"] == pointer["handoff_path"] and
            state["navigation"]["index"] == pointer["evidence_index_path"] and
            state["navigation"]["assets"] == pointer["local_sha_manifest_path"] and
            state["navigation"]["next_steps"] == pointer["takeover_path"],
            "STATE_POINTER_ROLE_MISMATCH")
    auth = state["evidence"]["authority"]
    require(auth["upstream_slots"] == 32 and auth["receipt_slots"] == 33 and
            auth["own_schema_validated_candidates"] == 6 and auth["full_closure_roots"] == 0 and
            auth["full_package_frozen"] is False and
            auth["training_contract_issued"] is False, "FALSE_AUTHORITY_CLOSURE")
    env = state["evidence"]["environment"]
    require(env["S9"].startswith("RETRACTED_FALSE_ALARM") and
            "Library/bin" in env["canonical_invocation"] and
            env["reexecution_due_to_S9"] == "NOT_REQUIRED", "S9_RETRACTION_LOST")
    mech = state["evidence"]["synthetic_mechanics"]
    require(mech["real_reader_fit_expression_consumed"] is False and
            mech["success_counter_40of40_claim"].startswith("RETRACTED_VACUOUS") and
            mech["execution_device"] == "CPU", "VACUOUS_GRADIENT_OR_GPU_PROMOTION")
    fit = state["evidence"]["fit_metadata"]
    require(fit["physical_source_zip_sha256"] == EXPECTED_CALIBRATION and
            fit["original_local_archive_members"] == 9 and
            fit["pr146_individual_original_files"] == 10 and
            fit["fit_donors"] == 104 and fit["fit_cells"] == 4553407 and
            fit["eligible_cells"] == 4553348 and fit["donor_operator_groups"] == 1400,
            "HISTORICAL_POPULATION_OR_ZIP_SPILLOVER")
    require(state["evidence"]["pass1_bridge"]["raw_level4_blocks_opened"] == 0 and
            state["evidence"]["raw_level4"]["all104_verdict"].startswith("NOT_EXECUTED"),
            "RAW_COUNT_FALSE_GREEN")
    require(state["protected"]["training"] == "OFF" and
            state["protected"]["D_shared_G5"] == "SEALED" and
            state["protected"]["N1_terminal_outcomes"] == "UNOPENED" and
            state["protected"]["reader_oracle_23"] == "SEALED",
            "PROTECTED_ACCESS_INFLATION")
    require(manifest.get("schema") == "JEPA_V28_LOCAL_ASSET_VERIFICATION_V1" and
            manifest.get("count") == 14 and len(manifest.get("assets", [])) == 14,
            "LOCAL_ASSET_CENSUS")
    entries = manifest["assets"]
    names = [x["filename"] for x in entries]
    require(len(names) == len(set(names)), "DUPLICATE_LOCAL_ASSET")
    require(all(isinstance(x.get("bytes"), int) and x["bytes"] > 0 and
                isinstance(x.get("sha256"), str) and len(x["sha256"]) == 64 and
                all(c in "0123456789abcdef" for c in x["sha256"])
                and x.get("role") for x in entries), "INVALID_LOCAL_ASSET")
    byname = {x["filename"]: x for x in entries}
    require(byname["FOUNDATION_CALIBRATION_BUNDLE_20260824.zip"]["sha256"] == EXPECTED_CALIBRATION,
            "CALIBRATION_ROOT_REPLACED")
    bad = byname["66e64913-959f-4a7c-bbfe-6ff906fb281d.npz"]
    require(bad["sha256"] == EXPECTED_BAD_NPZ and "DO_NOT_USE" in bad["role"],
            "MISMATCHED_NPZ_PROMOTED")
    for k in ("handoff_path", "evidence_index_path", "takeover_path"):
        content = (root / pointer[k]).read_text(encoding="utf-8")
        require("training" in content.lower() and "PR149" in content,
                "INCOMPLETE_" + k.upper())
    return {"status": "PASS_V28_HANDOFF_CONSISTENCY_ONLY",
            "asset_count": len(entries), "root_slots": auth["receipt_slots"],
            "closed_root_count": 0, "main_promoted": False,
            "training_authorized": False}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path,
                   default=Path(__file__).resolve().parents[2])
    args = p.parse_args()
    print(json.dumps(verify(args.repo_root), sort_keys=True))
