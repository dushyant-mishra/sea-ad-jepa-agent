from __future__ import annotations

from pathlib import Path

from scripts.v5.td_unified.premerger_custody_completeness_v1 import (
    GLOBAL_AUTHORITY,
    validate_completeness,
)

ROOT = Path(__file__).resolve().parents[3]
RESULT_DIR = ROOT / "results" / "target_discovery" / "unified_qualification_v1"
COMPLETENESS = RESULT_DIR / "PREMERGER_MERGED_CUSTODY_COMPLETENESS_V1.json"
UNRESOLVED = RESULT_DIR / "PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json"


def test_premerger_merged_custody_completeness_validator_passes():
    report = validate_completeness(COMPLETENESS, UNRESOLVED)
    assert report["status"] == "PASS_PREMERGER_MERGED_CUSTODY_COMPLETENESS_V1"
    assert report["group_count"] == 5
    assert report["required_unresolved_count"] == 9
    assert report["global_authority"] == GLOBAL_AUTHORITY
