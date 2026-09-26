#!/usr/bin/env python3
"""V42 read-only exact-byte custody check for chat-exclusive original files (ten text plus one V33 ZIP).

Seven original binary uploads are MANIFEST_ONLY, not in this Git checkout.
This script must not treat their inventory hashes as proof the bytes are here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/agent/chat-local-source-preservation-20260926/JEPA_CHAT_LOCAL_18_FILE_CUSTODY_MANIFEST_V42.json"
EXPECTED_UPLOADED = 11
EXPECTED_MISSING = 7


def main() -> None:
    data = json.loads(MANIFEST.read_bytes())
    assert data["schema"] == "JEPA_CHAT_LOCAL_18_FILE_CUSTODY_MANIFEST_V42"
    assert data["training_authorized"] is False
    assert data["protected_outcomes_opened"] is False
    entries = data["entries"]
    assert len(entries) == data["files_count"] == EXPECTED_UPLOADED + EXPECTED_MISSING
    assert len({x["name"] for x in entries}) == len(entries)
    exact = 0
    absent = 0
    for rec in entries:
        assert rec["scientific_authority"] == "NONE_FROM_PRESENCE_ALONE"
        assert len(rec["sha256"]) == 64 and rec["bytes"] > 0
        path = rec["git_path"]
        if path is None:
            assert rec["git_blob_sha"] is None
            assert rec["custody_status"] == "MANIFEST_ONLY_BYTES_STILL_IN_CHAT"
            absent += 1
            continue
        assert path.startswith("docs/agent/chat-local-source-preservation-20260926/")
        assert path.endswith(rec["name"])
        assert rec["custody_status"] == "UPLOADED_EXACT_BYTES"
        original = (ROOT / path).read_bytes()
        assert len(original) == rec["bytes"], f"byte count mismatch {path}"
        assert hashlib.sha256(original).hexdigest() == rec["sha256"], f"SHA256 mismatch {path}"
        git_blob = hashlib.sha1(f"blob {len(original)}".encode() + bytes([0]) + original).hexdigest()
        assert git_blob == rec["git_blob_sha"], f"Git blob SHA mismatch {path}"
        exact += 1
    assert exact == data["original_files_uploaded_exact"] == EXPECTED_UPLOADED
    assert sum(x["git_path"] is not None and x["name"].endswith(".zip") for x in entries) == data["original_binary_files_uploaded_exact"] == 1
    assert sum(x["git_path"] is not None and not x["name"].endswith(".zip") for x in entries) == data["original_text_files_uploaded_exact"] == 10
    assert absent == data["binary_files_manifest_only"] == EXPECTED_MISSING
    # No silent binary placeholder is present in the committed preservation folder.
    folder = MANIFEST.parent
    present = {
        p.name for p in folder.iterdir()
        if p.is_file() and p.name != MANIFEST.name
    }
    approved = {x["name"] for x in entries if x["git_path"] is not None}
    assert present == approved, f"untracked binary or missing original: {present ^ approved}"
    # Cross-check the LIVE-branch handoff against the authoritative original-byte
    # manifest. An earlier V42 snapshot passed custody but retained a stale
    # eight-binary blocker and omitted the already-executed PR #169 repair.
    machine_path = ROOT / "docs/agent/JEPA_V42_MACHINE_STATE_20260926.json"
    machine = json.loads(machine_path.read_bytes())
    assert machine["authorization"]["training"] is False
    assert machine["authorization"]["protected_full104_outcomes_opened"] is False
    assert machine["asset_custody"]["binary_not_transferred"] == absent == 7
    assert machine["asset_custody"]["originals_in_github_verified"] == exact == 11
    assert machine["asset_custody"]["uploaded_exact_text"] == 10
    assert machine["asset_custody"]["uploaded_exact_historical_binary_zip"] == 1
    blockers = set(machine["open_blockers"])
    assert "missing_eight_original_binaries_remote_custody" not in blockers
    assert "missing_seven_original_binaries_remote_custody" in blockers
    pr169 = machine["prs"]["masking_pr169_successor"]
    assert pr169["number"] == 169
    assert pr169["head"] == "e14c4003daf1248502ee83161fda8eb52376bb84"
    assert pr169["run"] == 36249786388
    assert pr169["hosted_primary_test_passed"] == 924
    assert pr169["hosted_skipped"] == 0
    assert pr169["scientific_execution_authorized"] is False
    assert pr169["n1_opened"] is False
    handoff = (ROOT / "docs/agent/JEPA_NEW_CHAT_HANDOFF_20260926_V42_EXCLUSIVE_CHAT_ASSETS_AND_EXECUTION.md").read_text()
    assert "PR #169 (Lane C masking freeze versioned repair)" in handoff
    assert "seven" in handoff.lower() and "18" in handoff
    assert "TRAINING=OFF" in handoff
    print("V42_HANDOFF_PR169_924_PASS_AND_SEVEN_MISSING_STATE_CONSISTENT")
    print("V42_EXACT_11_OF_11_ORIGINAL_SHA256_AND_GIT_BLOB_MATCH")
    print("V42_7_BINARY_FILES_MANIFEST_ONLY_NOT_FALSELY_REPORTED_AS_GITHUB_UPLOADS")
    print("V42_TRAINING_AUTHORIZED_FALSE")
if __name__ == "__main__":
    main()
