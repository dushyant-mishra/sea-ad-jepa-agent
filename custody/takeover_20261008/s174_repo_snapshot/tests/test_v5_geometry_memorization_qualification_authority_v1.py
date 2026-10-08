from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.geometry_memorization_qualification_authority_v1 import (
    GeometryMemorizationQualificationAuthorityV1,
)


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_GEOMETRY_MEMORIZATION_QUALIFICATION_AUTHORITY_V1",
        geometry_artifact_sha256=h("geometry-artifact"),
        protected_registry_authority_sha256=h("protected-registry"),
        execution_source_sha256=h("execution-source"),
        result_artifact_sha256=h("result"),
        qualification_protocol_id="CURRENT_GEOMETRY_MEMORIZATION_CAPACITY_PREDICATE_V1",
        execution_status="EXECUTED_PASS",
        training_authorized=False,
    )
    values.update(updates)
    return GeometryMemorizationQualificationAuthorityV1(**values)


def test_valid_geometry_memorization_evidence_is_deterministic() -> None:
    a = authority(); a.validate()
    assert a.canonical_digest() == authority().canonical_digest()
    assert a.passed is True


def test_geometry_memorization_roles_are_distinct_sha_roots() -> None:
    same = h("same")
    with pytest.raises(ValueError, match="distinct"):
        authority(geometry_artifact_sha256=same, result_artifact_sha256=same).validate()
    with pytest.raises(ValueError, match="execution_source_sha256"):
        authority(execution_source_sha256="test.py").validate()


def test_protocol_and_execution_status_are_fail_closed() -> None:
    with pytest.raises(ValueError, match="qualification_protocol_id"):
        authority(qualification_protocol_id="HISTORICAL_STAGE_A_IS_ENOUGH").validate()
    for bad in ("NOT_RUN", "SKIPPED", "PASS", "PENDING"):
        with pytest.raises(ValueError, match="execution_status"):
            authority(execution_status=bad).validate()
    assert authority(execution_status="EXECUTED_FAIL").passed is False


def test_geometry_memorization_qualification_cannot_authorize_training() -> None:
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()
