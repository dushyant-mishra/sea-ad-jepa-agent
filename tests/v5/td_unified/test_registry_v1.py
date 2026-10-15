from __future__ import annotations

import importlib

import pytest

from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus, QualificationStage
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair, verified_prereq


def _r():
    try:
        return importlib.import_module("scripts.v5.td_unified.registry_v1")
    except ModuleNotFoundError as exc:
        pytest.fail(f"Unified Task 3 registry_v1 is not implemented yet: {exc}")


def _actors():
    cobj = {"object_role":"QUALIFICATION_CONTROLLER","actor_id":"C1"}
    robj = {"object_role":"INDEPENDENT_REVIEWER","actor_id":"R1"}
    csha, rsha = canonical_sha256(cobj), canonical_sha256(robj)
    return csha, rsha, {csha:cobj, rsha:robj}.get


def _unit(r, unit_id="G8", *, stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
          status=ActiveLineageStatus.ACTIVE, manifest="1"*64, access="2"*64,
          population_authority="AUTHENTICATED_READER_SPLIT", claim_scope="POOLED_DONOR_LEVEL"):
    return r.RegistryUnit(
        unit_id=unit_id, qualification_stage=stage, active_lineage_status=status,
        authority_scope=f"UNIT:{unit_id}", authority_restrictions=("NO_TRAINING_AUTHORITY",),
        manifest_sha=manifest, access_policy_sha=access, producer_code_sha="a"*40, executor_code_sha="b"*40,
        producer_policy_sha="3"*64, executor_policy_sha="4"*64, schema_sha="5"*64,
        metric_sha="6"*64, reference_producer_sha="7"*64, falsifier_sha="8"*64,
        population_authority=population_authority, claim_scope=claim_scope)


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
    r=_r(); u,ref,deps=verified_pair(r); p=verified_prereq(r,u,ref); reg=_registry(r,[u,ref],[p]); c,rv,res=_actors()
    promoted=r.promote_unit(reg,"G8",QualificationStage.REAL_REFERENCE_READY,controller_identity=c,reviewer_identity=rv,authority_object_resolver=res,dependency_verifier=deps.get)
    old=promoted.promotions[0]
    revoked=r.revoke_or_supersede(promoted,"G8",ActiveLineageStatus.REVOKED_BY_DEFECT,reason_class="DEFECT",controller_identity=c,authority_object_resolver=res)
    assert revoked.promotions[0]==old
    assert revoked.units_by_id()["G8"].active_lineage_status is ActiveLineageStatus.REVOKED_BY_DEFECT


def test_revoked_unit_cannot_satisfy_new_prerequisite():
    r=_r(); dep=_unit(r); ref=_unit(r,"REF",status=ActiveLineageStatus.REVOKED_BY_DEFECT)
    result=r.derive_real_reference_ready("G8",_registry(r,[dep,ref],[_prereq(r)]))
    assert not result.ready and any("revoked" in x.lower() for x in result.blockers)


def test_superseded_unit_cannot_promote():
    r=_r(); reg=_registry(r,[_unit(r,status=ActiveLineageStatus.SUPERSEDED)]); c,rv,res=_actors()
    with pytest.raises(r.RegistryError,match="ACTIVE|superseded"):
        r.promote_unit(reg,"G8",QualificationStage.REAL_REFERENCE_READY,controller_identity=c,reviewer_identity=rv,authority_object_resolver=res)


def test_code_or_policy_change_requires_new_identity_without_stage_inheritance():
    r=_r(); changed=r.reidentify_unit(_unit(r,stage=QualificationStage.REAL_REFERENCE_READY),producer_policy_sha="9"*64)
    assert changed.qualification_stage is QualificationStage.SEMANTICS_ONLY
    assert changed.active_lineage_status is ActiveLineageStatus.REQUIRES_REQUALIFICATION


def test_producer_cannot_self_qualify():
    r=_r(); reg=_registry(r,[_unit(r)]); _,rv,res=_actors()
    with pytest.raises(r.RegistryError,match="independent|self|controller"):
        r.promote_unit(reg,"G8",QualificationStage.REAL_REFERENCE_READY,controller_identity="a"*40,reviewer_identity=rv,authority_object_resolver=res)


def test_human_executable_requires_independent_reviewer():
    r=_r(); reg=_registry(r,[_unit(r,stage=QualificationStage.REAL_REFERENCE_READY)]); c,_,res=_actors()
    with pytest.raises(r.RegistryError,match="reviewer|independent"):
        r.promote_unit(reg,"G8",QualificationStage.HUMAN_EXECUTABLE,controller_identity=c,reviewer_identity=None,authority_object_resolver=res)


def test_ready_boolean_cannot_override_missing_prerequisite():
    r=_r(); result=r.derive_real_reference_ready("G8",_registry(r,[_unit(r)]),asserted_ready=True)
    assert not result.ready and result.blockers


def test_one_requalification_required_prerequisite_blocks_readiness():
    r=_r(); dep=_unit(r); ref=_unit(r,"REF",status=ActiveLineageStatus.REQUIRES_REQUALIFICATION)
    assert not r.derive_real_reference_ready("G8",_registry(r,[dep,ref],[_prereq(r)])).ready


def test_stale_manifest_or_access_identity_blocks_readiness():
    r=_r(); dep=_unit(r); ref=_unit(r,"REF",manifest="f"*64)
    result=r.derive_real_reference_ready("G8",_registry(r,[dep,ref],[_prereq(r)]))
    assert not result.ready and any("manifest" in x.lower() for x in result.blockers)


def test_cycle_in_prerequisite_graph_fails_closed():
    r=_r(); a,b=_unit(r,"A"),_unit(r,"B")
    with pytest.raises(r.RegistryError,match="cycle"):
        r.derive_real_reference_ready("A",_registry(r,[a,b],[_prereq(r,pid="AB",dependent="A",target="B"),_prereq(r,pid="BA",dependent="B",target="A")]))


def test_unsatisfied_prerequisites_remain_visible():
    r=_r(); dep=_unit(r); ref=_unit(r,"REF",stage=QualificationStage.SEMANTICS_ONLY)
    result=r.derive_real_reference_ready("G8",_registry(r,[dep,ref],[_prereq(r)]))
    assert not result.ready and "P1" in result.unsatisfied_prerequisite_ids


def test_fixture_unbound_cannot_satisfy_real_reference_ready():
    r=_r(); result=r.derive_real_reference_ready("G8",_registry(r,[_unit(r,population_authority="FIXTURE_UNBOUND")]))
    assert not result.ready and any("AUTHENTICATED_READER_SPLIT" in x for x in result.blockers)


def test_human_executable_blocked_without_external_process_isolation_prerequisite():
    r=_r(); reg=_registry(r,[_unit(r,stage=QualificationStage.REAL_REFERENCE_READY)]); c,rv,res=_actors()
    with pytest.raises(r.RegistryError,match="process isolation|PROCESS_ISOLATION"):
        r.promote_unit(reg,"G8",QualificationStage.HUMAN_EXECUTABLE,controller_identity=c,reviewer_identity=rv,authority_object_resolver=res)


def test_vacuous_metric_identity_cannot_satisfy_content_qualified_prerequisite():
    r=_r(); dep,ref=_unit(r),_unit(r,"REF")
    p=_prereq(r,requirement_class="METRIC_CONTENT",content_required=True,content_validated=False)
    result=r.derive_real_reference_ready("G8",_registry(r,[dep,ref],[p]))
    assert not result.ready and any("content" in x.lower() for x in result.blockers)


def test_cross_process_receipt_dependency_requires_persistence_and_key_custody():
    r=_r(); u=_unit(r,stage=QualificationStage.REAL_REFERENCE_READY)
    reg=_registry(r,[u],[_prereq(r,pid="R4",target="R4",gate="HUMAN_EXECUTABLE",requirement_class="CROSS_PROCESS_LEDGER_CUSTODY",external_state="UNRESOLVED")])
    c,rv,res=_actors()
    with pytest.raises(r.RegistryError,match="custody|persistence|R4"):
        r.promote_unit(reg,"G8",QualificationStage.HUMAN_EXECUTABLE,controller_identity=c,reviewer_identity=rv,authority_object_resolver=res)


def test_pooled_crossfit_scope_cannot_promote_per_fold_source_stratified_claim():
    r=_r(); result=r.derive_real_reference_ready("G8",_registry(r,[_unit(r,claim_scope="PER_FOLD_SOURCE_STRATIFIED")]))
    assert not result.ready and any("pooled" in x.lower() or "source" in x.lower() for x in result.blockers)


def test_recursive_verification_cache_invalidates_on_dependency_identity_change():
    r=_r(); calls=[]; dep,ref,deps=verified_pair(r); p=verified_prereq(r,dep,ref); reg=_registry(r,[dep,ref],[p]); cache={}
    def verify(sha): calls.append(sha); return deps.get(sha)
    assert r.derive_real_reference_ready("G8",reg,dependency_verifier=verify,verification_cache=cache).ready
    changed=r.replace_unit(reg,r.reidentify_unit(ref,metric_sha="9"*64))
    assert not r.derive_real_reference_ready("G8",changed,dependency_verifier=verify,verification_cache=cache).ready
    assert calls


def test_cached_ready_result_cannot_survive_manifest_or_access_change():
    r=_r(); dep,ref,deps=verified_pair(r); p=verified_prereq(r,dep,ref); reg=_registry(r,[dep,ref],[p]); cache={}
    assert r.derive_real_reference_ready("G8",reg,dependency_verifier=deps.get,verification_cache=cache).ready
    assert not r.derive_real_reference_ready("G8",r.replace_unit(reg,_unit(r,"G8",manifest="e"*64)),dependency_verifier=deps.get,verification_cache=cache).ready


def test_registry_uses_exact_task1_stage_and_lineage_enums():
    r=_r(); payload=_unit(r).to_payload()
    assert payload["qualification_stage"]==QualificationStage.KNOWN_TRUTH_QUALIFIED.value
    assert payload["active_lineage_status"]==ActiveLineageStatus.ACTIVE.value
