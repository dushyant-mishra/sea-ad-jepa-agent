"""S174: the real TRAIN cache the V77 lane calibrated against carries the historical HVS/SEA-AD
feature-axis defect. Every V77 script or result that touches it must be listed as affected, so the
defect cannot spread silently into new work, and the record must not overstate what was verified."""
from __future__ import annotations

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


def test_investigation_entries_carry_a_reason_and_are_not_consumers():
    assert all(INVESTIGATION.values())
    assert not set(INVESTIGATION) & (set(_s174()["affected_scripts"]) | set(_s174()["affected_results"]))


def test_the_record_does_not_overstate_verification_or_repair():
    e = _s174()
    assert e["verification_status"].startswith("INFERRED_FROM_CODE_AND_PROVENANCE__NOT_VALUE_VERIFIED")
    assert e["status"] == "RECORDED__AFFECTED_REAL_DATA_RESULTS_SUSPENDED__REPAIR_NOT_EXECUTED"
    assert "SUSPENDED" in e["s149_status"]
