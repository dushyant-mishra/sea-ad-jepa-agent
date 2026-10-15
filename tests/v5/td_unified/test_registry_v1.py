from __future__ import annotations

import pytest

from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus, QualificationStage
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair, verified_prereq


def _r():
    from scripts.v5.td_unified import registry_v1 as r
    return r


def _unit(r, unit_id="G8", *, stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
          status=ActiveLineageStatus.ACTIVE, manifest="1"*64, access="2"*64,
          population_authority="AUTHENTICATED_READER_SPLIT", claim_scope="POOLED_DONOR_LEVEL"):
    return r.RegistryUnit(
        unit_id=unit_id, qualification_stage=stage, active_lineage_status=status,
        authority_scope=f"UNIT:{unit_id}", authority_restrictions=("NO_TRAINING_AUTHORITY",),
        manifest_sha=manifest, access_policy_sha=access, producer_code_sha="a"*40, executor_code_sha="b"*40,
        producer_actor_identity=r.canonical_sha256({"object_role":"SCIENTIFIC_PRODUCER","actor_id":f"producer:{unit_id}"}),
        executor_actor_identity=r.canonical_sha256({"object_role":"SCIENTIFIC_EXECUTOR","actor_id":f"executor:{unit_id}"}),
        producer_policy_sha="3"*64, executor_policy_sha="4"*64, schema_sha="5"*64,
        metric_sha="6"*64, reference_producer_sha="7"*64, falsifier_sha="8"*64,
        population_authority=population_authority, claim_scope=claim_scope)


def _actors(r, registry, unit=None, objects=None):
    controller={"object_role":"QUALIFICATION_CONTROLLER","actor_id":"C"}; reviewer={"object_role":"INDEPENDENT_REVIEWER","actor_id":"R"}
    c=r.canonical_sha256(controller); rv=r.canonical_sha256(reviewer)
    obj={} if objects is None else dict(objects); obj.update({c:controller,rv:reviewer})
    trusted=[controller,reviewer]
    if unit is not None:
        producer={"object_role":"SCIENTIFIC_PRODUCER","actor_id":f"producer:{unit.unit_id}"}; executor={"object_role":"SCIENTIFIC_EXECUTOR","actor_id":f"executor:{unit.unit_id}"}
        obj.update({unit.producer_actor_identity:producer,unit.executor_actor_identity:executor}); trusted.extend([producer,executor])
    for u in registry.units:
        for sha, role, actor in ((u.producer_actor_identity,"SCIENTIFIC_PRODUCER",f"producer:{u.unit_id}"),(u.executor_actor_identity,"SCIENTIFIC_EXECUTOR",f"executor:{u.unit_id}")):
            candidate={"object_role":role,"actor_id":actor}
            if canonical_sha256(candidate)==sha:
                obj[sha]=candidate; trusted.append(candidate)
    from tests.v5.td_unified.registry_v1_dependency_fixtures import bind_actor_registry
    registry,obj=bind_actor_registry(r,registry,obj,trusted_actor_objects=tuple(trusted))
    return registry,c,rv,obj.get


def _registry(r, units, prerequisites=()):
    return r.TDQualificationRegistry(tuple(units), tuple(prerequisites), (), ())


def _prereq(r, *, pid="P1", dependent="G8", target="REF", gate="REAL_REFERENCE_READY",
            required_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED, manifest="1"*64, access="2"*64,
            content_required=False, content_validated=True, requirement_class="UNIT", external_state="SATISFIED"):
    dep, ref = _unit(r, dependent, manifest=manifest, access=access), _unit(r, target, manifest=manifest, access=access)
    return r.PrerequisiteRecord(
        prerequisite_id=pid, dependent_unit_id=dependent, dependent_unit_sha=dep.canonical_sha256(),
        prerequisite_unit_id=target, prerequisite_unit_sha=ref.canonical_sha256(),
        required_stage=required_stage, required_lineage_status=ActiveLineageStatus.ACTIVE,
        manifest_sha=manifest, access_policy_sha=access, gate=gate,
        content_required=content_required, content_validated=content_validated,
        content_validation_receipt_sha=None, requirement_class=requirement_class,
        external_state=external_state, evidence_receipt_sha="9"*64)


def test_historical_promotion_receipt_remains_immutable_after_revocation():
    r=_r(); u,ref,deps=verified_pair(r); p=verified_prereq(r,u,ref); reg=_registry(r,[u,ref],[p])
    reg,c,rv,res=_actors(r,reg,objects=deps)
    custody=r.RegistryHistoryCustody(reg,attestation_key=b"task3-lawful-history-fixture")
    promoted=r.promote_unit(reg,"G8",QualificationStage.REAL_REFERENCE_READY,controller_identity=c,reviewer_identity=rv,authority_object_resolver=res,dependency_verifier=deps.get,history_custody=custody)
    old=promoted.promotions[0]
    revoked=r.revoke_or_supersede(promoted,"G8",ActiveLineageStatus.REVOKED_BY_DEFECT,reason_class="DEFECT",controller_identity=c,authority_object_resolver=res,dependency_verifier=deps.get,history_custody=custody)
    assert revoked.promotions[0]==old
    assert revoked.units_by_id()["G8"].active_lineage_status is ActiveLineageStatus.REVOKED_BY_DEFECT


def test_revoked_unit_cannot_satisfy_new_prerequisite():
    r=_r(); dep=_unit(r); ref=_unit(r,"REF",status=ActiveLineageStatus.REVOKED_BY_DEFECT)
    result=r.derive_real_reference_ready("G8",_registry(r,[dep,ref],[_prereq(r)]))
    assert not result.ready and any("revoked" in x.lower() for x in result.blockers)


def test_superseded_unit_cannot_promote():
    r=_r(); u=_unit(r,status=ActiveLineageStatus.SUPERSEDED); reg=_registry(r,[u]); reg,c,rv,res=_actors(r,reg,u)
    with pytest.raises(r.RegistryError,match="ACTIVE"):
        r.promote_unit(reg,"G8",QualificationStage.REAL_REFERENCE_READY,controller_identity=c,reviewer_identity=rv,authority_object_resolver=res)


def test_reidentification_resets_stage_and_lineage():
    r=_r(); u=_unit(r,stage=QualificationStage.HUMAN_EXECUTABLE)
    changed=r.reidentify_unit(u,metric_sha="9"*64)
    assert changed.qualification_stage is QualificationStage.SEMANTICS_ONLY
    assert changed.active_lineage_status is ActiveLineageStatus.REQUIRES_REQUALIFICATION


def test_supersession_requires_successor_identity_and_scope():
    r=_r(); u=_unit(r); s=_unit(r,"G9"); reg=_registry(r,[u,s]); reg,c,_,res=_actors(r,reg)
    with pytest.raises(r.RegistryError,match="successor"):
        r.revoke_or_supersede(reg,"G8",ActiveLineageStatus.SUPERSEDED,reason_class="DESIGN",controller_identity=c,authority_object_resolver=res)


def test_human_executable_requires_independent_reviewer():
    r=_r(); u=_unit(r,stage=QualificationStage.REAL_REFERENCE_READY); reg=_registry(r,[u]); reg,c,_,res=_actors(r,reg,u)
    with pytest.raises(r.RegistryError,match="reviewer|independent"):
        r.promote_unit(reg,"G8",QualificationStage.HUMAN_EXECUTABLE,controller_identity=c,reviewer_identity=None,authority_object_resolver=res)


def test_duplicate_unit_ids_rejected():
    r=_r()
    with pytest.raises(r.RegistryError,match="duplicate"):
        r.TDQualificationRegistry((_unit(r),_unit(r)),(),(),())


def test_prerequisite_cycle_is_rejected():
    r=_r(); a=_unit(r,"G8"); b=_unit(r,"REF"); p1=_prereq(r,pid="P1",dependent="G8",target="REF"); p2=_prereq(r,pid="P2",dependent="REF",target="G8")
    reg=_registry(r,[a,b],[p1,p2])
    with pytest.raises(r.RegistryError,match="cycle"):
        r.derive_real_reference_ready("G8",reg,dependency_verifier=lambda _: True)


def test_missing_dependency_verifier_blocks_readiness():
    r=_r(); dep=_unit(r); ref=_unit(r,"REF"); result=r.derive_real_reference_ready("G8",_registry(r,[dep,ref],[_prereq(r)]))
    assert not result.ready and any("dependency" in x.lower() for x in result.blockers)


def test_boolean_dependency_verifier_is_not_authority():
    r=_r(); dep=_unit(r); ref=_unit(r,"REF"); result=r.derive_real_reference_ready("G8",_registry(r,[dep,ref],[_prereq(r)]),dependency_verifier=lambda _: True)
    assert not result.ready and any("dependency" in x.lower() for x in result.blockers)


def test_human_executable_blocked_without_external_process_isolation_prerequisite():
    r=_r(); u=_unit(r,stage=QualificationStage.REAL_REFERENCE_READY); reg=_registry(r,[u]); reg,c,rv,res=_actors(r,reg,u)
    with pytest.raises(r.RegistryError,match="process isolation|PROCESS_ISOLATION"):
        r.promote_unit(reg,"G8",QualificationStage.HUMAN_EXECUTABLE,controller_identity=c,reviewer_identity=rv,authority_object_resolver=res)


def test_fixture_unbound_population_cannot_be_real_reference_ready():
    r=_r(); dep=_unit(r,population_authority="FIXTURE_UNBOUND"); ref=_unit(r,"REF"); result=r.derive_real_reference_ready("G8",_registry(r,[dep,ref],[_prereq(r)]),dependency_verifier=lambda _: True)
    assert not result.ready and any("population" in x.lower() for x in result.blockers)


def test_per_fold_source_stratified_claim_scope_is_blocked():
    r=_r(); dep=_unit(r,claim_scope="PER_FOLD_SOURCE_STRATIFIED"); ref=_unit(r,"REF"); result=r.derive_real_reference_ready("G8",_registry(r,[dep,ref],[_prereq(r)]),dependency_verifier=lambda _: True)
    assert not result.ready and any("pooled" in x.lower() for x in result.blockers)


def test_registry_uses_exact_task1_stage_and_lineage_enums():
    r=_r(); u=_unit(r)
    assert isinstance(u.qualification_stage, QualificationStage)
    assert isinstance(u.active_lineage_status, ActiveLineageStatus)
