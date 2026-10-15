from __future__ import annotations

import hashlib

import pytest

from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus, QualificationStage
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified import registry_v1 as r
from scripts.v5.td_unified import registry_v1_legacy as legacy
from tests.v5.td_unified.registry_v1_dependency_fixtures import (
    bind_actor_registry,
    direct_fixture_actor_objects,
    verified_pair,
    verified_prereq,
)


def actor(role, name):
    obj = {"object_role": role, "actor_id": name}
    return canonical_sha256(obj), obj


def unit(unit_id="G8", stage=QualificationStage.KNOWN_TRUTH_QUALIFIED):
    return r.RegistryUnit(
        unit_id=unit_id, qualification_stage=stage, active_lineage_status=ActiveLineageStatus.ACTIVE,
        authority_scope=f"UNIT:{unit_id}", authority_restrictions=("NO_TRAINING_AUTHORITY",),
        manifest_sha="1"*64, access_policy_sha="2"*64, producer_code_sha="a"*40, executor_code_sha="b"*40,
        producer_actor_identity=r.canonical_sha256({"object_role":"SCIENTIFIC_PRODUCER","actor_id":f"producer:{unit_id}"}),
        executor_actor_identity=r.canonical_sha256({"object_role":"SCIENTIFIC_EXECUTOR","actor_id":f"executor:{unit_id}"}),
        producer_policy_sha="3"*64, executor_policy_sha="4"*64, schema_sha="5"*64, metric_sha="6"*64,
        reference_producer_sha="7"*64, falsifier_sha="8"*64,
        population_authority="AUTHENTICATED_READER_SPLIT", claim_scope="POOLED_DONOR_LEVEL")


def evidence(role="PREREQUISITE_EVIDENCE", marker="ok"):
    obj = {"object_role": role, "requirement_class": "EXTERNAL_CONTROL", "marker": marker}
    return canonical_sha256(obj), obj


def prereq(dep, target, *, requirement_class="EXTERNAL_CONTROL", evidence_sha=None):
    esha = evidence_sha or evidence()[0]
    return r.PrerequisiteRecord(
        prerequisite_id="P1", dependent_unit_id=dep.unit_id, dependent_unit_sha=dep.canonical_sha256(),
        prerequisite_unit_id=target.unit_id, prerequisite_unit_sha=target.canonical_sha256(),
        required_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
        required_lineage_status=ActiveLineageStatus.ACTIVE,
        manifest_sha=dep.manifest_sha, access_policy_sha=dep.access_policy_sha,
        gate="REAL_REFERENCE_READY", content_required=False, content_validated=True,
        content_validation_receipt_sha=None, requirement_class=requirement_class,
        external_state="SATISFIED", evidence_receipt_sha=esha)


def registry(dep, target, p):
    return r.TDQualificationRegistry((dep, target), (p,), (), ())


def test_boolean_true_callback_is_not_evidence_authority():
    dep, target = unit(), unit("REF"); p = prereq(dep, target)
    reg = registry(dep, target, p)
    with pytest.raises(TypeError, match="prerequisite_evidence_verifier"):
        r.derive_real_reference_ready("G8", reg, prerequisite_evidence_verifier=lambda _: True)


def test_evidence_receipt_must_resolve_to_exact_role_tagged_object():
    dep, target, deps = verified_pair(r)
    good_sha, good = evidence(); bad_sha, bad = evidence("METRIC_DEFINITION", "spoof")
    p = verified_prereq(r, dep, target, requirement_class="EXTERNAL_CONTROL", evidence_receipt_sha=bad_sha); reg = registry(dep, target, p)
    result = r.derive_real_reference_ready("G8", reg, authority_object_resolver=lambda sha: bad if sha == bad_sha else None, dependency_verifier=deps.get)
    assert not result.ready
    assert any("role" in b.lower() for b in result.blockers)
    p2 = verified_prereq(r, dep, target, requirement_class="EXTERNAL_CONTROL", evidence_receipt_sha=good_sha); reg2 = registry(dep, target, p2)
    assert r.derive_real_reference_ready("G8", reg2, authority_object_resolver=lambda sha: good if sha == good_sha else None, dependency_verifier=deps.get).ready


def test_controller_and_reviewer_are_resolved_objects_before_real_authority_gate():
    dep, target, deps = verified_pair(r); esha, eobj = evidence(); p = verified_prereq(r, dep, target, requirement_class="EXTERNAL_CONTROL", evidence_receipt_sha=esha)
    reg = registry(dep, target, p)
    csha, cobj = actor("QUALIFICATION_CONTROLLER", "C1")
    rsha, robj = actor("INDEPENDENT_REVIEWER", "R1")
    reg, objects = bind_actor_registry(
        r, reg, deps, trusted_actor_objects=(cobj, robj)
    )
    objects[esha] = eobj
    with pytest.raises(r.RegistryError, match="resolver|controller.*object|authority object|actor registry"):
        r.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                       controller_identity=csha, reviewer_identity=rsha)
    mechanics = legacy.promote_unit(
        reg, "G8", QualificationStage.REAL_REFERENCE_READY,
        controller_identity=csha, reviewer_identity=rsha,
        authority_object_resolver=objects.get, dependency_verifier=deps.get,
    )
    assert mechanics.units_by_id()["G8"].qualification_stage is QualificationStage.REAL_REFERENCE_READY
    with pytest.raises(r.RegistryError, match="Task 2|manifest|population|reader-split"):
        r.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                       controller_identity=csha, reviewer_identity=rsha,
                       authority_object_resolver=objects.get, dependency_verifier=deps.get)


def test_wrong_role_controller_object_is_refused_even_with_matching_digest():
    dep, target = unit(), unit("REF"); esha, eobj = evidence(); p = prereq(dep, target, evidence_sha=esha)
    reg = registry(dep, target, p)
    csha, cobj = actor("INDEPENDENT_REVIEWER", "NOT_CONTROLLER")
    rsha, robj = actor("INDEPENDENT_REVIEWER", "R1")
    objects = {csha:cobj, rsha:robj, esha:eobj}
    objects.update(direct_fixture_actor_objects(dep))
    objects.update(direct_fixture_actor_objects(target))
    reg, objects = bind_actor_registry(
        r, reg, objects, trusted_actor_objects=(cobj, robj)
    )
    with pytest.raises(r.RegistryError, match="controller.*role|role.*controller"):
        r.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                       controller_identity=csha, reviewer_identity=rsha,
                       authority_object_resolver=objects.get, dependency_verifier=objects.get)


def test_mechanics_promotion_receipt_explicitly_binds_prerequisite_record_identities_without_claiming_real_rrr_authority():
    dep, target, deps = verified_pair(r); esha, eobj = evidence(); p = verified_prereq(r, dep, target, requirement_class="EXTERNAL_CONTROL", evidence_receipt_sha=esha)
    reg = registry(dep, target, p)
    csha, cobj = actor("QUALIFICATION_CONTROLLER", "C1"); rsha, robj = actor("INDEPENDENT_REVIEWER", "R1")
    reg, objects = bind_actor_registry(
        r, reg, deps, trusted_actor_objects=(cobj, robj)
    )
    objects[esha] = eobj
    promoted = legacy.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                                   controller_identity=csha, reviewer_identity=rsha,
                                   authority_object_resolver=objects.get,
                                   dependency_verifier=deps.get)
    receipt = promoted.promotions[0]
    assert receipt.prerequisite_shas == (p.canonical_sha256(),)
    with pytest.raises(r.RegistryError, match="Task 2|manifest|population|reader-split"):
        r.promote_unit(reg, "G8", QualificationStage.REAL_REFERENCE_READY,
                       controller_identity=csha, reviewer_identity=rsha,
                       authority_object_resolver=objects.get,
                       dependency_verifier=deps.get)


def test_supersession_binds_existing_exact_successor_and_pre_registry_identity():
    old, successor = unit(), unit("G8_V2")
    reg = r.TDQualificationRegistry((old, successor), (), (), ())
    csha, cobj = actor("QUALIFICATION_CONTROLLER", "C1")
    objects = {csha:cobj}
    objects.update(direct_fixture_actor_objects(old))
    objects.update(direct_fixture_actor_objects(successor))
    reg, objects = bind_actor_registry(
        r, reg, objects, trusted_actor_objects=(cobj,)
    )
    changed = r.revoke_or_supersede(reg, "G8", ActiveLineageStatus.SUPERSEDED,
        reason_class="POLICY_CHANGE", controller_identity=csha,
        successor_unit_id="G8_V2", successor_unit_sha=successor.canonical_sha256(),
        requalification_scope="FULL_UNIT", authority_object_resolver=objects.get, dependency_verifier=objects.get)
    receipt = changed.revocations[0]
    assert receipt.pre_registry_sha == reg.canonical_sha256()
    assert receipt.successor_unit_sha == successor.canonical_sha256()
    with pytest.raises(r.RegistryError, match="successor.*identity"):
        r.revoke_or_supersede(reg, "G8", ActiveLineageStatus.SUPERSEDED,
            reason_class="POLICY_CHANGE", controller_identity=csha,
            successor_unit_id="G8_V2", successor_unit_sha="f"*64,
            requalification_scope="FULL_UNIT", authority_object_resolver=objects.get, dependency_verifier=objects.get)
