from __future__ import annotations

import pytest

from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus, QualificationStage
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified import registry_v1 as r


def unit(unit_id="G8", *, stage=QualificationStage.KNOWN_TRUTH_QUALIFIED):
    return r.RegistryUnit(
        unit_id=unit_id,
        qualification_stage=stage,
        active_lineage_status=ActiveLineageStatus.ACTIVE,
        authority_scope=f"UNIT:{unit_id}",
        authority_restrictions=("NO_TRAINING_AUTHORITY",),
        manifest_sha="1"*64,
        access_policy_sha="2"*64,
        producer_code_sha="a"*40,
        executor_code_sha="b"*40,
        producer_policy_sha="3"*64,
        executor_policy_sha="4"*64,
        schema_sha="5"*64,
        metric_sha="6"*64,
        reference_producer_sha="7"*64,
        falsifier_sha="8"*64,
        population_authority="AUTHENTICATED_READER_SPLIT",
        claim_scope="POOLED_DONOR_LEVEL",
    )


def actor(role, actor_id):
    obj={"object_role":role,"actor_id":actor_id}
    return canonical_sha256(obj),obj


def evidence(requirement_class, **claims):
    obj={"object_role":"PREREQUISITE_EVIDENCE","requirement_class":requirement_class,**claims}
    return canonical_sha256(obj),obj


def unit_prereq(dep, target):
    return r.PrerequisiteRecord(
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
        evidence_receipt_sha="9"*64,
    )


def human_prereq(unit_obj, pid, klass, evidence_sha):
    return r.PrerequisiteRecord(
        prerequisite_id=pid,
        dependent_unit_id=unit_obj.unit_id,
        dependent_unit_sha=unit_obj.canonical_sha256(),
        prerequisite_unit_id=pid,
        prerequisite_unit_sha="c"*64,
        required_stage=QualificationStage.SEMANTICS_ONLY,
        required_lineage_status=ActiveLineageStatus.ACTIVE,
        manifest_sha=unit_obj.manifest_sha,
        access_policy_sha=unit_obj.access_policy_sha,
        gate="HUMAN_EXECUTABLE",
        content_required=False,
        content_validated=True,
        content_validation_receipt_sha=None,
        requirement_class=klass,
        external_state="SATISFIED",
        evidence_receipt_sha=evidence_sha,
    )


def test_boolean_dependency_verifier_cannot_make_digest_strings_authority():
    dep,target=unit(),unit("REF")
    p=unit_prereq(dep,target)
    reg=r.TDQualificationRegistry((dep,target),(p,),(),())
    result=r.derive_real_reference_ready("G8",reg,dependency_verifier=lambda _: True)
    assert not result.ready
    assert any("object" in b.lower() or "bytes" in b.lower() or "resolver" in b.lower() or "digest strings" in b.lower() for b in result.blockers)


def test_fabricated_promotion_receipt_cannot_establish_advanced_stage_provenance():
    u=unit(stage=QualificationStage.REAL_REFERENCE_READY)
    csha,cobj=actor("QUALIFICATION_CONTROLLER","controller")
    rsha,robj=actor("INDEPENDENT_REVIEWER","reviewer")
    psha,pobj=evidence(
        "PROCESS_ISOLATION",
        producer_process_isolated=True,
        harness_drives_finalization=True,
        reader_fit_values_out_of_process=True,
        protected_partitions_physically_absent=True,
    )
    ksha,kobj=evidence(
        "CROSS_PROCESS_LEDGER_CUSTODY",
        persistent_ledger=True,
        signing_key_out_of_process=True,
        key_custodian="HARNESS",
    )
    fake=r.PromotionReceipt(
        unit_id="G8",
        source_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
        destination_stage=QualificationStage.REAL_REFERENCE_READY,
        pre_registry_sha="d"*64,
        unit_identity_sha="e"*64,
        prerequisite_ids=(),
        prerequisite_shas=(),
        manifest_sha=u.manifest_sha,
        access_policy_sha=u.access_policy_sha,
        controller_identity=csha,
        reviewer_identity=rsha,
    )
    reg=r.TDQualificationRegistry(
        (u,),
        (
            human_prereq(u,"R1","PROCESS_ISOLATION",psha),
            human_prereq(u,"R4","CROSS_PROCESS_LEDGER_CUSTODY",ksha),
        ),
        (fake,),
        (),
    )
    objects={csha:cobj,rsha:robj,psha:pobj,ksha:kobj}
    with pytest.raises(r.RegistryError,match="promotion.*provenance|promotion.*history|receipt.*chain|pre_registry|unit identity"):
        r.promote_unit(
            reg,"G8",QualificationStage.HUMAN_EXECUTABLE,
            controller_identity=csha,
            reviewer_identity=rsha,
            authority_object_resolver=objects.get,
            dependency_verifier=lambda _: True,
        )
