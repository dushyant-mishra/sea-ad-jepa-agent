import dataclasses
from pathlib import Path

import pytest

import scripts.v5.td_unified.registry_v1 as r
from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus as L
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q
from tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair, verified_prereq


def _actors(*, controller_id="C1", reviewer_id="R1"):
    controller = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": controller_id}
    reviewer = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": reviewer_id}
    objects = {r.canonical_sha256(controller): controller, r.canonical_sha256(reviewer): reviewer}
    return r.canonical_sha256(controller), r.canonical_sha256(reviewer), objects


def _setup(dep_stage=Q.KNOWN_TRUTH_QUALIFIED):
    dep, ref, deps = verified_pair(r, dep_stage=dep_stage)
    prereq = verified_prereq(r, dep, ref)
    registry = r.TDQualificationRegistry((dep, ref), (prereq,), (), ())
    controller, reviewer, objects = _actors()
    return dep, ref, deps, prereq, registry, controller, reviewer, objects


def _human_gate_evidence(registry, g8, ref, objects):
    isolation = {
        "object_role": "PREREQUISITE_EVIDENCE",
        "requirement_class": "PROCESS_ISOLATION",
        "producer_process_isolated": True,
        "harness_drives_finalization": True,
        "reader_fit_values_out_of_process": True,
        "protected_partitions_physically_absent": True,
    }
    custody = {
        "object_role": "PREREQUISITE_EVIDENCE",
        "requirement_class": "CROSS_PROCESS_LEDGER_CUSTODY",
        "persistent_ledger": True,
        "signing_key_out_of_process": True,
        "key_custodian": "HARNESS",
    }
    objects = dict(objects)
    objects[r.canonical_sha256(isolation)] = isolation
    objects[r.canonical_sha256(custody)] = custody

    def ext(pid, cls, evidence):
        return dataclasses.replace(
            verified_prereq(r, g8, ref, pid=pid, gate="HUMAN_EXECUTABLE", requirement_class=cls),
            evidence_receipt_sha=r.canonical_sha256(evidence),
        )

    return (
        ext("ISO", "PROCESS_ISOLATION", isolation),
        ext("CUS", "CROSS_PROCESS_LEDGER_CUSTODY", custody),
    ), objects


def test_t3_b1_unit_scope_and_no_training_authority_block_downstream_and_training_stages():
    dep, ref, deps, _, registry, controller, reviewer, objects = _setup()
    registry = r.promote_unit(
        registry, "G8", Q.REAL_REFERENCE_READY,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=objects.get,
        dependency_verifier=deps.get,
    )
    g8 = registry.units_by_id()["G8"]
    extra, objects = _human_gate_evidence(registry, g8, ref, objects)
    registry = r.TDQualificationRegistry(
        registry.units, registry.prerequisites + extra, registry.promotions, registry.revocations
    )
    registry = r.promote_unit(
        registry, "G8", Q.HUMAN_EXECUTABLE,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=objects.get,
        dependency_verifier=deps.get,
    )
    registry = r.promote_unit(
        registry, "G8", Q.HUMAN_EXECUTED,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=objects.get,
        dependency_verifier=deps.get,
    )
    for forbidden in (Q.DOWNSTREAM_CERTIFIED, Q.TRAINING_ELIGIBLE, Q.TRAINING_AUTHORIZED):
        with pytest.raises(r.RegistryError):
            r.promote_unit(
                registry, "G8", forbidden,
                controller_identity=controller,
                reviewer_identity=reviewer,
                authority_object_resolver=objects.get,
                dependency_verifier=deps.get,
            )


def test_t3_b2_stage_evidence_table_fails_closed_for_unimplemented_evidence_types():
    dep, ref, deps, _, registry, controller, _, objects = _setup(dep_stage=Q.SAME_CODE_PATH)
    with pytest.raises(r.RegistryError):
        r.promote_unit(
            registry, "G8", Q.KNOWN_TRUTH_QUALIFIED,
            controller_identity=controller,
            reviewer_identity=None,
            authority_object_resolver=objects.get,
            dependency_verifier=deps.get,
        )

    dep, ref, deps, _, registry, controller, reviewer, objects = _setup()
    registry = r.promote_unit(
        registry, "G8", Q.REAL_REFERENCE_READY,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=objects.get,
        dependency_verifier=deps.get,
    )
    g8 = registry.units_by_id()["G8"]
    extra, objects = _human_gate_evidence(registry, g8, ref, objects)
    registry = r.TDQualificationRegistry(
        registry.units, registry.prerequisites + extra, registry.promotions, registry.revocations
    )
    registry = r.promote_unit(
        registry, "G8", Q.HUMAN_EXECUTABLE,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=objects.get,
        dependency_verifier=deps.get,
    )
    with pytest.raises(r.RegistryError):
        r.promote_unit(
            registry, "G8", Q.HUMAN_EXECUTED,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=objects.get,
            dependency_verifier=deps.get,
        )


def test_t3_b3_actor_registry_refuses_aliases_unknown_actors_and_self_qualification():
    dep, ref, deps, _, registry, _, _, _ = _setup()
    producer = "producer:G8"
    bad_controller_ids = [producer, producer + " ", " " + producer, producer.upper(), producer.replace(":", "\uff1a"), "minted-by-producer-1"]
    for controller_id in bad_controller_ids:
        controller, reviewer, objects = _actors(controller_id=controller_id, reviewer_id="R1")
        with pytest.raises(r.RegistryError):
            r.promote_unit(
                registry, "G8", Q.REAL_REFERENCE_READY,
                controller_identity=controller,
                reviewer_identity=reviewer,
                authority_object_resolver=objects.get,
                dependency_verifier=deps.get,
            )

    controller, reviewer, objects = _actors(controller_id="C1", reviewer_id="C1")
    with pytest.raises(r.RegistryError):
        r.promote_unit(
            registry, "G8", Q.REAL_REFERENCE_READY,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=objects.get,
            dependency_verifier=deps.get,
        )


def test_t3_b4_caller_cache_cannot_authenticate_or_survive_resolver_change():
    dep, ref, deps, _, registry, _, _, objects = _setup()
    cache = {}
    first = r.derive_real_reference_ready(
        "G8", registry,
        dependency_verifier=deps.get,
        authority_object_resolver=objects.get,
        verification_cache=cache,
    )
    assert first.ready

    second = r.derive_real_reference_ready(
        "G8", registry,
        dependency_verifier=lambda _: None,
        authority_object_resolver=objects.get,
        verification_cache=cache,
    )
    assert not second.ready

    poison = {}
    for unit in (dep, ref):
        for field in r._IDENTITY_64_FIELDS + r._IDENTITY_40_FIELDS:
            poison[("dependency-object-v1", unit.canonical_sha256(), field, getattr(unit, field))] = (True, None)
    poisoned = r.derive_real_reference_ready(
        "G8", registry,
        dependency_verifier=lambda _: None,
        authority_object_resolver=objects.get,
        verification_cache=poison,
    )
    assert not poisoned.ready


def test_t3_b5_revocation_erasure_and_fabricated_history_are_refused():
    dep, ref, deps, _, registry, controller, reviewer, objects = _setup()
    promoted = r.promote_unit(
        registry, "G8", Q.REAL_REFERENCE_READY,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=objects.get,
        dependency_verifier=deps.get,
    )
    revoked = r.revoke_or_supersede(
        promoted, "G8", L.REVOKED_BY_DEFECT,
        reason_class="DEFECT",
        controller_identity=controller,
        authority_object_resolver=objects.get,
        dependency_verifier=deps.get,
    )
    forged_unit = dataclasses.replace(revoked.units_by_id()["G8"], active_lineage_status=L.ACTIVE)
    forged = r.TDQualificationRegistry(
        tuple(forged_unit if u.unit_id == "G8" else u for u in revoked.units),
        revoked.prerequisites,
        revoked.promotions,
        (),
    )
    extra, objects2 = _human_gate_evidence(forged, forged_unit, ref, objects)
    forged = r.TDQualificationRegistry(forged.units, forged.prerequisites + extra, forged.promotions, ())
    with pytest.raises(r.RegistryError):
        r.promote_unit(
            forged, "G8", Q.HUMAN_EXECUTABLE,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=objects2.get,
            dependency_verifier=deps.get,
        )


def test_t3_b6_task3_ci_is_read_only_and_does_not_mutate_tests_or_production_code():
    workflows = list(Path(".github/workflows").glob("*task3*.yml"))
    assert workflows
    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        assert "contents: write" not in text
        assert "git push" not in text
        assert "git commit" not in text
