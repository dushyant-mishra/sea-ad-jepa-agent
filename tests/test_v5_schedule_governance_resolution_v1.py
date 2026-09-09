import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "docs" / "agent" / "V5_SCHEDULE_GOVERNANCE_RESOLUTION_CANDIDATE_V1.json"


def load():
    return json.loads(P.read_text())


def test_no_obsolete_schedule_is_active_authority():
    x = load()
    assert x["status"].startswith("NO_ACTIVE_PRODUCTION_SCHEDULE_AUTHORITY")
    assert x["training_authorized"] is False
    assert x["execution_authorized"] is False
    for row in x["historical_quarantine"]:
        assert row["may_authorize_training"] is False


def test_old_horizon_and_base_proposal_are_both_quarantined():
    x = load()
    paths = {row["path"]: row for row in x["historical_quarantine"]}
    assert "docs/agent/TEACHER_STUDENT_V5_PRESENTATION_HORIZON_AUTHORITY_V1.json" in paths
    assert "docs/agent/TEACHER_STUDENT_V5_PROPOSAL_AUTHORITY_V3.json" in paths
    assert paths["docs/agent/TEACHER_STUDENT_V5_PROPOSAL_AUTHORITY_V3.json"]["quarantine_scope"] == "BASE_PROPOSAL_AND_BASE_SCHEDULE_ONLY"


def test_v3_is_candidate_not_promoted_authority():
    x = load()
    c = x["current_schedule_candidate"]
    assert c["role"] == "PROSPECTIVE_SUPERSESSION_CANDIDATE_ONLY"
    assert c["full_unique_cell_coverage"] is True
    assert c["independent_review_required_before_promotion"] is True
    assert c["training_authorized"] is False


def test_quarantine_reason_records_exact_incompatibility():
    x = load()
    old = next(r for r in x["historical_quarantine"] if r["schema"] == "TEACHER_STUDENT_V5_PRESENTATION_HORIZON_AUTHORITY_V1")
    assert "58037/864 > 64" in old["reason"]
    assert x["current_schedule_candidate"]["candidate_total_presentations"] == 5267086
