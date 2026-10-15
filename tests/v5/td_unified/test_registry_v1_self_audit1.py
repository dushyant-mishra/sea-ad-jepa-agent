from __future__ import annotations

import pytest

from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus, QualificationStage
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified import registry_v1 as r
from tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair, verified_prereq


def unit(unit_id="G8", *, metric="6" * 64, stage=QualificationStage.KNOWN_TRUTH_QUALIFIED):
    return r.RegistryUnit(
        unit_id=unit_id, qualification_stage=stage, active_lineage_status=ActiveLineageStatus.ACTIVE,
        authority_scope=f"UNIT:{unit_id}", authority_restrictions=("NO_TRAINING_AUTHORITY",),
        manifest_sha="1"*64, access_policy_sha="2"*64, producer_code_sha="a"*40, executor_code_sha="b"*40,
        producer_actor_identity=r.canonical_sha256({"object_role":"SCIENTIFIC_PRODUCER","actor_id":f"producer:{unit_id}"}),
        executor_actor_identity=r.canonical_sha256({"object_role":"SCIENTIFIC_EXECUTOR","actor_id":f"executor:{unit_id}"}),
        producer_policy_sha="3"*64, executor_policy_sha="4"*64, schema_sha="5"*64, metric_sha=metric,
        reference_producer_sha="7"*64, falsifier_sha="8"*64,
        population_authority="AUTHENTICATED_READER_SPLIT", claim_scope="POOLED_DONOR_LEVEL")


def prereq(dep, target, **kw):
    payload=dict(
        prerequisite_id="P1", dependent_unit_id=dep.unit_id, dependent_unit_sha=dep.canonical_sha256(),
        prerequisite_unit_id=target.unit_id, prerequisite_unit_sha=target.canonical_sha256(),
        required_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
        required_lineage_status=ActiveLineageStatus.ACTIVE,
        manifest_sha=dep.manifest_sha, access_policy_sha=dep.access_policy_sha, gate="REAL_REFERENCE_READY",
        content_required=False, content_validated=True, content_validation_receipt_sha=None,
        requirement_class="UNIT", external_state="SATISFIED", evidence_receipt_sha="9"*64)
    payload.update(kw); return r.PrerequisiteRecord(**payload)


def registry(dep,target,p): return r.TDQualificationRegistry((dep,target),(p,),(),())

def actor(role,name):
    obj={"object_role":role,"actor_id":name}; return canonical_sha256(obj),obj

def evidence(marker="ok"):
    obj={"object_role":"PREREQUISITE_EVIDENCE","requirement_class":"EXTERNAL_CONTROL","marker":marker}; return canonical_sha256(obj),obj


def test_participant_identity_must_be_exact_not_free_text():
    dep,target=unit(),unit("REF"); reg=registry(dep,target,prereq(dep,target))
    with pytest.raises(r.RegistryError,match="identity|64-hex|exact|resolver"):
        r.promote_unit(reg,"G8",QualificationStage.REAL_REFERENCE_READY,controller_identity="controller",reviewer_identity="reviewer")


def test_reviewer_cannot_alias_producer_executor_or_controller():
    dep,target=unit(),unit("REF"); reg=registry(dep,target,prereq(dep,target)); c,cobj=actor("QUALIFICATION_CONTROLLER","C")
    with pytest.raises(r.RegistryError,match="independent|reviewer"):
        r.promote_unit(reg,"G8",QualificationStage.REAL_REFERENCE_READY,controller_identity=c,reviewer_identity=dep.producer_code_sha,authority_object_resolver={c:cobj}.get)


def test_prerequisite_binds_exact_target_registry_identity():
    dep,target=unit(),unit("REF"); p=prereq(dep,target); substituted=unit("REF",metric="f"*64)
    result=r.derive_real_reference_ready("G8",r.TDQualificationRegistry((dep,substituted),(p,),(),()))
    assert not result.ready and any("identity" in b.lower() for b in result.blockers)


def test_prerequisite_binds_exact_dependent_registry_identity():
    dep,target=unit(),unit("REF"); p=prereq(dep,target); changed=unit(metric="e"*64)
    result=r.derive_real_reference_ready("G8",r.TDQualificationRegistry((changed,target),(p,),(),()))
    assert not result.ready and any("dependent" in b.lower() and "identity" in b.lower() for b in result.blockers)


def test_content_validated_boolean_without_bound_validation_receipt_is_not_authority():
    dep,target=unit(),unit("REF"); p=prereq(dep,target,content_required=True,content_validated=True,content_validation_receipt_sha=None)
    result=r.derive_real_reference_ready("G8",registry(dep,target,p))
    assert not result.ready and any("content" in b.lower() and "receipt" in b.lower() for b in result.blockers)


def test_external_satisfied_status_requires_resolved_evidence_receipt():
    dep,target=unit(),unit("REF"); esha,eobj=evidence(); p=prereq(dep,target,requirement_class="EXTERNAL_CONTROL",evidence_receipt_sha=esha)
    result=r.derive_real_reference_ready("G8",registry(dep,target,p),authority_object_resolver=lambda _:None)
    assert not result.ready and any("resolver" in b.lower() or "object" in b.lower() for b in result.blockers)


def test_external_evidence_positive_control_requires_exact_receipt_resolution():
    dep,target,deps=verified_pair(r); esha,eobj=evidence(); p=verified_prereq(r,dep,target,requirement_class="EXTERNAL_CONTROL",evidence_receipt_sha=esha)
    result=r.derive_real_reference_ready("G8",registry(dep,target,p),authority_object_resolver=lambda sha:eobj if sha==esha else None,dependency_verifier=deps.get)
    assert result.ready
