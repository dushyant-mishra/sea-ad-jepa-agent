from __future__ import annotations

from dataclasses import replace

import pytest

from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus, QualificationStage
from scripts.v5.td_unified import registry_v1 as r


def unit(unit_id="G8", *, metric="6" * 64, stage=QualificationStage.KNOWN_TRUTH_QUALIFIED):
    return r.RegistryUnit(
        unit_id=unit_id,
        qualification_stage=stage,
        active_lineage_status=ActiveLineageStatus.ACTIVE,
        authority_scope=f"UNIT:{unit_id}",
        authority_restrictions=("NO_TRAINING_AUTHORITY",),
        manifest_sha="1" * 64,
        access_policy_sha="2" * 64,
        producer_code_sha="a" * 40,
        executor_code_sha="b" * 40,
        producer_policy_sha="3" * 64,
        executor_policy_sha="4" * 64,
        schema_sha="5" * 64,
        metric_sha=metric,
        reference_producer_sha="7" * 64,
        falsifier_sha="8" * 64,
        population_authority="AUTHENTICATED_READER_SPLIT",
        claim_scope="POOLED_DONOR_LEVEL",
    )


def prereq(dep, target, **kw):
    payload = dict(
        prerequisite_id="P1",
        dependent_unit_id=dep.unit_id,
        dependent_unit_sha=dep.canonical_sha256(),
        prerequisite_unit_id=target.unit_id,
        prerequisite_unit_sha=target.canonical_sha256(),
        required_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
        required_lineage_status=ActiveLineageStatus.ACTIVE,
        manifest_sha=dep.manifest_sha,
        access_policy_sha=dep.access_policy_sha,
        gate="REAL_REFERENCE_READY",
        content_required=False,
        content_validated=True,
        content_validation_receipt_sha=None,
        requirement_class="UNIT",
        external_state="SATISFIED",
        evidence_receipt_sha="9" * 64,
    )
    payload.update(kw)
    return r.PrerequisiteRecord(**payload)


def registry(dep, target, p):
    return r.TDQualificationRegistry(units=(dep, target), prerequisites=(p,), promotions=(), revocations=())


def test_participant_identity_must_be_exact_not_free_text():
    dep, target = unit(), unit("REF")
    reg = registry(dep, target, prereq(dep, target))
    with pytest.raises(r.RegistryError, match="identity|64-hex|exact"):
        r.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                       controller_identity="controller", reviewer_identity="reviewer")


def test_reviewer_cannot_alias_producer_executor_or_controller():
    dep, target = unit(), unit("REF")
    reg = registry(dep, target, prereq(dep, target))
    with pytest.raises(r.RegistryError, match="independent|reviewer"):
        r.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                       controller_identity="c" * 64, reviewer_identity=dep.producer_code_sha)


def test_prerequisite_binds_exact_target_registry_identity():
    dep, target = unit(), unit("REF")
    p = prereq(dep, target)
    substituted = unit("REF", metric="f" * 64)
    reg = r.TDQualificationRegistry(units=(dep, substituted), prerequisites=(p,), promotions=(), revocations=())
    result = r.derive_real_reference_ready("G8", reg)
    assert not result.ready
    assert any("identity" in b.lower() for b in result.blockers)


def test_prerequisite_binds_exact_dependent_registry_identity():
    dep, target = unit(), unit("REF")
    p = prereq(dep, target)
    changed_dep = unit(metric="e" * 64)
    reg = r.TDQualificationRegistry(units=(changed_dep, target), prerequisites=(p,), promotions=(), revocations=())
    result = r.derive_real_reference_ready("G8", reg)
    assert not result.ready
    assert any("dependent" in b.lower() and "identity" in b.lower() for b in result.blockers)


def test_content_validated_boolean_without_bound_validation_receipt_is_not_authority():
    dep, target = unit(), unit("REF")
    p = prereq(dep, target, content_required=True, content_validated=True, content_validation_receipt_sha=None)
    result = r.derive_real_reference_ready("G8", registry(dep, target, p))
    assert not result.ready
    assert any("content" in b.lower() and "receipt" in b.lower() for b in result.blockers)


def test_external_satisfied_status_requires_resolved_evidence_receipt():
    dep, target = unit(), unit("REF")
    p = prereq(dep, target, requirement_class="EXTERNAL_CONTROL", evidence_receipt_sha="d" * 64)
    reg = registry(dep, target, p)
    result = r.derive_real_reference_ready("G8", reg, prerequisite_evidence_verifier=lambda sha: False)
    assert not result.ready
    assert any("evidence" in b.lower() for b in result.blockers)


def test_external_evidence_positive_control_requires_exact_receipt_resolution():
    dep, target = unit(), unit("REF")
    p = prereq(dep, target, requirement_class="EXTERNAL_CONTROL", evidence_receipt_sha="d" * 64)
    reg = registry(dep, target, p)
    result = r.derive_real_reference_ready("G8", reg, prerequisite_evidence_verifier=lambda sha: sha == "d" * 64)
    assert result.ready
