"""S174: the real TRAIN cache the V77 lane calibrated against carries the historical HVS/SEA-AD
feature-axis defect. Every V77 script or result that touches it must be listed as affected, so the
defect cannot spread silently into new work, and the record must not overstate what was verified."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REC = ROOT / "results" / "v77" / "V77_SYNTHETIC_STATUS_AND_DEFECT_REGISTER_V2_ADDENDUM_4.json"
CACHE = "stage81a3r_corrected_real_train"
# Files that read the cache only to investigate S174, not to consume it. Each needs a reason.
INVESTIGATION = {
    "scripts/v77/probe_v77_s174_cache_axis.py":
        "the owner-authorized read-only TRAIN probe of 2026-10-07 that tests S174 against direct H5AD reads",
    "results/v77/V77_S174_CACHE_AXIS_PROBE_PREREGISTRATION_V1.json": "that probe's pre-registration",
    "results/v77/V77_S174_CACHE_AXIS_PROBE_RESULT_V1.json": "that probe's result",
    "scripts/v77/rebuild_s174_train_cache.py":
        "the owner-authorized S174 repair: reads the old cache only to rebuild it by identifier and to compare",
    "results/v77/S174_REBUILD_FREEZE_V1.json": "that repair's freeze record",
    "results/v77/S174_REBUILD_BUILD_RECEIPT_V1.json": "that repair's build receipt",
    "results/v77/S174_REBUILD_VERIFY_AND_COMPARISON_V1.json": "that repair's verification and old-against-new receipt",
}


def _s174():
    return next(e for e in json.loads(REC.read_text(encoding="utf-8"))["NEW_ENTRIES"] if e["id"] == "S174")


def _files_naming(pattern: str, folder: str) -> set[str]:
    out = []
    for p in sorted((ROOT / folder).glob("*")):
        if p.is_file() and p.suffix in (".py", ".json") and pattern in p.read_text(encoding="utf-8", errors="replace"):
            out.append(p.relative_to(ROOT).as_posix())
    return set(out)


def test_every_script_reading_the_cache_is_listed():
    assert _files_naming(CACHE, "scripts/v77") <= set(_s174()["affected_scripts"]) | set(INVESTIGATION)


def test_every_result_built_from_the_cache_is_listed():
    found = {f for f in _files_naming(CACHE, "results/v77") if "ADDENDUM_4" not in f}
    assert found <= set(_s174()["affected_results"]) | set(INVESTIGATION)


def test_the_probe_outcome_is_recorded_faithfully():
    res = ROOT / "results" / "v77" / "V77_S174_CACHE_AXIS_PROBE_RESULT_V1.json"
    add5 = ROOT / "results" / "v77" / "V77_SYNTHETIC_STATUS_AND_DEFECT_REGISTER_V2_ADDENDUM_5.json"
    r = json.loads(res.read_text(encoding="utf-8"))
    a = json.loads(add5.read_text(encoding="utf-8"))["S174_UPDATE"]
    assert a["verdict"] == r["verdict"]
    assert a["probe"]["result"]["sha256"] == hashlib.sha256(res.read_bytes()).hexdigest()
    pre = ROOT / a["probe"]["preregistration"]["path"]
    assert r["preregistration"]["sha256"] == hashlib.sha256(pre.read_bytes()).hexdigest()
    assert r["code"]["equals_preregistered"] is True
    if r["verdict"] == "S174_VALUE_VERIFIED":
        assert a["verification_status"] == "VALUE_VERIFIED"
        assert "REMAIN_SUSPENDED" in a["status"] and "REBUILD_NOT_AUTHORIZED" in a["status"]


def test_investigation_entries_carry_a_reason_and_are_not_consumers():
    assert all(INVESTIGATION.values())
    assert not set(INVESTIGATION) & (set(_s174()["affected_scripts"]) | set(_s174()["affected_results"]))


def test_the_record_does_not_overstate_verification_or_repair():
    e = _s174()
    assert e["verification_status"].startswith("INFERRED_FROM_CODE_AND_PROVENANCE__NOT_VALUE_VERIFIED")
    assert e["status"] == "RECORDED__AFFECTED_REAL_DATA_RESULTS_SUSPENDED__REPAIR_NOT_EXECUTED"
    assert "SUSPENDED" in e["s149_status"]
