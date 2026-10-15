from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.v5.td_unified.authority_v1 import (
    ActiveLineageStatus,
    AuthorityError,
    AuthorityRecord,
    QualificationStage,
    validate_authority_record,
)

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = ROOT / "schemas" / "target_discovery" / "unified_v1" / "authority_record_v1.json"


def test_only_canonical_ordered_qualification_stages_are_accepted():
    expected = [
        "SEMANTICS_ONLY",
        "FIXTURE_SAME_INTERFACE",
        "SAME_CODE_PATH",
        "KNOWN_TRUTH_QUALIFIED",
        "REAL_REFERENCE_READY",
        "HUMAN_EXECUTABLE",
        "HUMAN_EXECUTED",
        "DOWNSTREAM_CERTIFIED",
        "TRAINING_ELIGIBLE",
        "TRAINING_AUTHORIZED",
    ]
    assert [x.value for x in QualificationStage] == expected
    with pytest.raises(ValueError):
        QualificationStage("GREEN")


def test_only_four_active_lineage_statuses_are_accepted():
    assert {x.value for x in ActiveLineageStatus} == {
        "ACTIVE",
        "SUPERSEDED",
        "REVOKED_BY_DEFECT",
        "REQUIRES_REQUALIFICATION",
    }
    with pytest.raises(ValueError):
        ActiveLineageStatus("PASS")


def test_authority_scope_is_required_and_unit_stage_cannot_imply_project_training():
    with pytest.raises(AuthorityError, match="scope"):
        validate_authority_record(
            AuthorityRecord(
                unit_id="G8_UNIT",
                qualification_stage=QualificationStage.SAME_CODE_PATH,
                active_lineage_status=ActiveLineageStatus.ACTIVE,
                authority_scope="",
            )
        )
    with pytest.raises(AuthorityError, match="training"):
        validate_authority_record(
            AuthorityRecord(
                unit_id="G8_UNIT",
                qualification_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
                active_lineage_status=ActiveLineageStatus.ACTIVE,
                authority_scope="PROJECT_TRAINING",
            )
        )


def test_bare_pass_green_or_mechanics_qualified_is_not_a_stage():
    for bad in ("PASS", "GREEN", "QUALIFIED", "MECHANICS_QUALIFIED"):
        with pytest.raises(ValueError):
            QualificationStage(bad)


def test_authority_schema_enum_sets_match_code_exactly():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False
    assert schema["properties"]["qualification_stage"]["enum"] == [x.value for x in QualificationStage]
    assert set(schema["properties"]["active_lineage_status"]["enum"]) == {x.value for x in ActiveLineageStatus}
    assert set(schema["required"]) == {"unit_id", "qualification_stage", "active_lineage_status", "authority_scope"}


def test_revoked_or_requalification_state_is_preserved_not_promoted_by_validation():
    for status in (ActiveLineageStatus.REVOKED_BY_DEFECT, ActiveLineageStatus.REQUIRES_REQUALIFICATION):
        record = AuthorityRecord(
            unit_id="G8_UNIT",
            qualification_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
            active_lineage_status=status,
            authority_scope="UNIT:G8",
        )
        assert validate_authority_record(record).active_lineage_status is status
