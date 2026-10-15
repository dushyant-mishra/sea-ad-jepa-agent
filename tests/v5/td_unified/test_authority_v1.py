from __future__ import annotations

import pytest

from scripts.v5.td_unified.authority_v1 import (
    ActiveLineageStatus,
    AuthorityError,
    AuthorityRecord,
    QualificationStage,
    validate_authority_record,
)


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
