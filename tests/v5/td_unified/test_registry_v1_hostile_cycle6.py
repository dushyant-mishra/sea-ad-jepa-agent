from __future__ import annotations

from dataclasses import fields

import pytest

from scripts.v5.td_unified import registry_v1 as r
from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus, QualificationStage
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from tests.v5.td_unified.registry_v1_dependency_fixtures import bind_actor_registry, verified_pair, verified_prereq


def actor(role: str, actor_id: str):
    obj = {"object_role": role, "actor_id": actor_id}
    return canonical_sha256(obj), obj


def evidence():
    obj = {"object_role": "PREREQUISITE_EVIDENCE", "requirement_class": "EXTERNAL_CONTROL", "marker": "ok"}
    return canonical_sha256(obj), obj


def test_registry_unit_binds_exact_producer_and_executor_actor_identities():
    names = {f.name for f in fields(r.RegistryUnit)}
    assert "producer_actor_identity" in names
    assert "executor_actor_identity" in names


def test_producer_actor_cannot_self_issue_qualification_controller_receipt():
    dep, target, deps = verified_pair(r)
    esha, eobj = evidence()
    p = verified_prereq(r, dep, target, requirement_class="EXTERNAL_CONTROL", evidence_receipt_sha=esha)
    producer_sha, producer_obj = actor("SCIENTIFIC_PRODUCER", "same-actor")
    executor_sha, executor_obj = actor("SCIENTIFIC_EXECUTOR", "executor")
    controller_sha, controller_obj = actor("QUALIFICATION_CONTROLLER", "same-actor")
    reviewer_sha, reviewer_obj = actor("INDEPENDENT_REVIEWER", "reviewer")
    dep = r.RegistryUnit(**{
        **dep.__dict__,
        "producer_actor_identity": producer_sha,
        "executor_actor_identity": executor_sha,
    })
    p = r.PrerequisiteRecord(**{
        **p.__dict__,
        "dependent_unit_sha": dep.canonical_sha256(),
    })
    reg = r.TDQualificationRegistry((dep, target), (p,), (), ())
    objects = dict(deps)
    objects.update({
        esha: eobj,
        producer_sha: producer_obj,
        executor_sha: executor_obj,
        controller_sha: controller_obj,
        reviewer_sha: reviewer_obj,
    })
    reg, objects = bind_actor_registry(
        r, reg, objects,
        trusted_actor_objects=(controller_obj, reviewer_obj),
    )
    with pytest.raises(r.RegistryError, match="producer.*actor|self-qualif|independent.*controller"):
        r.promote_unit(
            reg,
            dep.unit_id,
            QualificationStage.REAL_REFERENCE_READY,
            controller_identity=controller_sha,
            reviewer_identity=reviewer_sha,
            authority_object_resolver=objects.get,
            dependency_verifier=objects.get,
        )


def test_executor_actor_cannot_issue_revocation_controller_receipt():
    dep, _, deps = verified_pair(r)
    producer_sha, producer_obj = actor("SCIENTIFIC_PRODUCER", "producer")
    executor_sha, executor_obj = actor("SCIENTIFIC_EXECUTOR", "same-actor")
    controller_sha, controller_obj = actor("QUALIFICATION_CONTROLLER", "same-actor")
    dep = r.RegistryUnit(**{
        **dep.__dict__,
        "producer_actor_identity": producer_sha,
        "executor_actor_identity": executor_sha,
    })
    deps.update({producer_sha: producer_obj, executor_sha: executor_obj})
    reg = r.TDQualificationRegistry((dep,), (), (), ())
    objects = dict(deps)
    objects[controller_sha] = controller_obj
    reg, objects = bind_actor_registry(r, reg, objects, trusted_actor_objects=(controller_obj,))
    with pytest.raises(r.RegistryError, match="executor.*actor|independent.*revocation"):
        r.revoke_or_supersede(
            reg,
            dep.unit_id,
            ActiveLineageStatus.REVOKED_BY_DEFECT,
            reason_class="DEFECT",
            controller_identity=controller_sha,
            authority_object_resolver=objects.get,
            dependency_verifier=objects.get,
        )


def test_reviewer_actor_cannot_alias_scientific_producer_actor():
    dep, target, deps = verified_pair(r)
    producer_sha, producer_obj = actor("SCIENTIFIC_PRODUCER", "same-actor")
    executor_sha, executor_obj = actor("SCIENTIFIC_EXECUTOR", "executor")
    controller_sha, controller_obj = actor("QUALIFICATION_CONTROLLER", "controller")
    reviewer_sha, reviewer_obj = actor("INDEPENDENT_REVIEWER", "same-actor")
    dep = r.RegistryUnit(**{
        **dep.__dict__,
        "producer_actor_identity": producer_sha,
        "executor_actor_identity": executor_sha,
    })
    deps.update({producer_sha: producer_obj, executor_sha: executor_obj})
    reg = r.TDQualificationRegistry((dep, target), (), (), ())
    resolver_objects = dict(deps)
    resolver_objects.update({controller_sha: controller_obj, reviewer_sha: reviewer_obj})
    reg, resolver_objects = bind_actor_registry(
        r, reg, resolver_objects,
        trusted_actor_objects=(controller_obj, reviewer_obj),
    )
    with pytest.raises(r.RegistryError, match="reviewer actor.*producer|reviewer actor.*executor"):
        r.promote_unit(
            reg,
            dep.unit_id,
            QualificationStage.REAL_REFERENCE_READY,
            controller_identity=controller_sha,
            reviewer_identity=reviewer_sha,
            authority_object_resolver=resolver_objects.get,
            dependency_verifier=resolver_objects.get,
        )


def test_actor_identity_change_resets_stage_and_requires_requalification():
    dep, _, _ = verified_pair(r)
    replacement_sha, _ = actor("SCIENTIFIC_PRODUCER", "replacement-producer")
    changed = r.reidentify_unit(dep, producer_actor_identity=replacement_sha)
    assert changed.qualification_stage is QualificationStage.SEMANTICS_ONLY
    assert changed.active_lineage_status is ActiveLineageStatus.REQUIRES_REQUALIFICATION
