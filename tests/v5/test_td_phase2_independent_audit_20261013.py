from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import audit_td_phase2_independent_20261013 as A  # noqa: E402


def test_phase2_execution_and_custody_passes_exact_frozen_evidence():
    report = A.audit()
    assert report["status"] == "PASS_PHASE2_EXECUTION_AND_CUSTODY"
    assert report["receipt_sha256"] == "5382034332f24b0e37954b4f8e2cefe958f21ff644e6fd1ffec150d2478aa61b"
    assert report["qualification_status"] == "QUALIFIED"
    assert report["readiness_status"] == "READY_FOR_INDEPENDENT_QUALIFICATION_AUDIT__NO_REAL_EXECUTION_AUTHORITY"
    assert report["challenge_count"] == 9
    assert report["matched_count"] == 9
    assert report["real_execution_authorized"] is False
    assert report["scientific_scope"] == "TEST_QUALIFICATION_ONLY"


def test_phase2_expected_status_map_is_exact_and_preserves_not_estimable():
    report = A.audit()
    assert report["capability_statuses"] == {
        "REL_BROAD_MESO_POSITIVE": "PASS",
        "REL_FINE_RECURRENT_POSITIVE": "PASS",
        "REL_RARE_LOCAL_ISLAND_POSITIVE": "PASS",
        "REL_MULTI_ISLAND_POSITIVE": "PASS",
        "REL_DONOR_RESTRICTED_POSITIVE": "PASS",
        "REL_SOURCE_VISIBILITY_STRESS": "PASS",
        "REL_TECHNICAL_TWIN_NEGATIVE": "FAIL",
        "REL_NULL_NEGATIVE": "FAIL",
        "REL_UNDERPOWERED_POSITIVE": "NOT_ESTIMABLE",
    }


def test_phase2_audit_keeps_every_downstream_authority_closed():
    report = A.audit()
    assert all(value is False for value in report["authority"].values())
    assert report["real_td_authorized"] is False
    assert report["target_selection_authorized"] is False
    assert report["representation_selection_authorized"] is False
    assert report["td60_authorized"] is False
    assert report["stage4_authorized"] is False
    assert report["training_authorized"] is False
