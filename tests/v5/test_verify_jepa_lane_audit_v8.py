"""Hostile tests for V8 audit continuity; do not touch protected data."""
from __future__ import annotations
from copy import deepcopy
import csv
import json
from pathlib import Path
import pytest
from scripts.v5.verify_jepa_lane_audit_v8 import (
    TERMINAL, SNAPSHOT, ASSETS, validate_snapshot, validate_assets, main
)
ROOT=Path(__file__).resolve().parents[2]


def sources():
    return json.loads((ROOT/SNAPSHOT).read_text())


def test_unmodified_frozen_audit_snapshot_verifies():
    validate_snapshot(sources())


def test_unmodified_external_artifact_sha_ledger_verifies():
    with (ROOT/ASSETS).open(newline="") as fh:
        validate_assets(list(csv.DictReader(fh)))


@pytest.mark.parametrize("patch", [
    lambda x: x.update(authority="TARGET_WINNER_C1"),
    lambda x: x["frozen_accepted_unified_tasks_0_3"].update(task3_sha="f"*40),
    lambda x: x["release_gates"].update(unified_task4="ACCEPTED"),
    lambda x: x["release_gates"].update(real_g7_e3="G7_QUALIFIED"),
    lambda x: x["release_gates"].update(ps_task4="AUTHORIZED"),
    lambda x: x["release_gates"].update(ps_task3="NO_RECHECK"),
    lambda x: x["records"].append(deepcopy(x["records"][0])),
    lambda x: next(y for y in x["records"] if y["pr"]==438).update(classification="BIOLOGY_PASS"),
    lambda x: next(y for y in x["records"] if y["pr"]==451).update(classification="REAL_TASK5_ACCEPTED"),
    lambda x: x["hostile_evidence"].pop("ps_task2_red_5"),
])
def test_authority_and_lineage_mutations_refused(patch):
    item=deepcopy(sources())
    patch(item)
    with pytest.raises(ValueError):
        validate_snapshot(item)


def test_forged_pr_link_or_invalid_sha_is_refused():
    base=sources()
    for field,value in [("url","https://example.invalid"),("sha","BAD")]:
        corrupted=deepcopy(base)
        corrupted["records"][0][field]=value
        with pytest.raises(ValueError):
            validate_snapshot(corrupted)


@pytest.mark.parametrize("field,value",[
    ("size_bytes","0"),("sha256","0"*63),
    ("github_or_external_custody","GITHUB_PUBLIC_RAW_UPLOADED"),
    ("filename","../payload.zip"),
])
def test_bad_attachment_custody_is_refused(field,value):
    with (ROOT/ASSETS).open(newline="") as fh:
        rows=list(csv.DictReader(fh))
    rows[0][field]=value
    with pytest.raises(ValueError):
        validate_assets(rows)


def test_audit_static_guard_does_not_authenticate_science():
    doc=sources()
    assert doc["authority"]==TERMINAL
    assert "NO_AUTHORITY" in doc["release_gates"]["unified_tasks6_8"] or "FIXTURES_ONLY" in doc["release_gates"]["unified_tasks6_8"]
