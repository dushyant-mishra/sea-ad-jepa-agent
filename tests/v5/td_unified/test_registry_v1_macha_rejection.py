"""Preserved independent Macha rejection probes for Unified Task 3.

These tests intentionally encode the authority/custody defects found against
rejected head 851544e8.  They are the RED gate for successor repair; do not
weaken them to match implementation behavior.
"""
from __future__ import annotations

import dataclasses

import pytest

from scripts.v5.td_unified import registry_v1 as r
from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus as L
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q
from tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair, verified_prereq


def _actors(*, cid: str = "C1", rid: str = "R1"):
    controller = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": cid}
    reviewer = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": rid}
    objects = {
        r.canonical_sha256(controller): controller,
        r.canonical_sha256(reviewer): reviewer,
    }
    return r.canonical_sha256(controller), r.canonical_sha256(reviewer), objects


def _setup(*, dep_stage=Q.KNOWN_TRUTH_QUALIFIED):
    dep, ref, dependencies = verified_pair(r, dep_stage=dep_stage)
    prerequisite = verified_prereq(r, dep, ref)
    registry = r.TDQualificationRegistry((dep, ref), (prerequisite,), (), ())
    controller, reviewer, authority_objects = _actors()
    return dep, ref, dependencies, prerequisite, registry, controller, reviewer, authority_objects


def _human_execution_registry():
    dep, ref, dependencies, _, registry, controller, reviewer, authority_objects = _setup()
    ready_registry = r.promote_unit(
        registry,
        "G8",
        Q.REAL_REFERENCE_READY,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=authority_objects.get,
        dependency_verifier=dependencies.get,
    )
    g8 = ready_registry.units_by_id()["G8"]
    process_evidence = {
        "object_role": "PREREQUISITE_EVIDENCE",
        "requirement_class": "PROCESS_ISOLATION",
        "producer_process_isolated": True,
        "harness_drives_finalization": True,
        "reader_fit_values_out_of_process": True,
        "protected_partitions_physically_absent": True,
    }
    custody_evidence = {
        "object_role": "PREREQUISITE_EVIDENCE",
        "requirement_class": "CROSS_PROCESS_LEDGER_CUSTODY",
        "persistent_ledger": True,
        "signing_key_out_of_process": True,
        "key_custodian": "HARNESS",
    }
    resolver_objects = dict(authority_objects)
    resolver_objects[r.canonical_sha256(process_evidence)] = process_evidence
    resolver_objects[r.canonical_sha256(custody_evidence)] = custody_evidence
    original_snapshot = registry.to_payload()
    resolver_objects[r.canonical_sha256(original_snapshot)] = original_snapshot

    def external(pid: str, requirement_class: str, evidence: dict[str, object]):
        return dataclasses.replace(
            verified_prereq(
                r,
                g8,
                ref,
                pid=pid,
                gate="HUMAN_EXECUTABLE",
                requirement_class=requirement_class,
            ),
            evidence_receipt_sha=r.canonical_sha256(evidence),
        )

    with_human_prereqs = r.TDQualificationRegistry(
        ready_registry.units,
        ready_registry.prerequisites
        + (
            external("ISO", "PROCESS_ISOLATION", process_evidence),
            external("CUS", "CROSS_PROCESS_LEDGER_CUSTODY", custody_evidence),
        ),
        ready_registry.promotions,
        ready_registry.revocations,
    )
    return (
        ref,
        dependencies,
        with_human_prereqs,
        controller,
        reviewer,
        resolver_objects,
        process_evidence,
        custody_evidence,
    )


def test_h1_unit_scope_cannot_promote_beyond_human_executed():
    _, dependencies, registry, controller, reviewer, resolver_objects, _, _ = _human_execution_registry()
    registry = r.promote_unit(
        registry,
        "G8",
        Q.HUMAN_EXECUTABLE,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=resolver_objects.get,
        dependency_verifier=dependencies.get,
    )
    registry = r.promote_unit(
        registry,
        "G8",
        Q.HUMAN_EXECUTED,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=resolver_objects.get,
        dependency_verifier=dependencies.get,
    )
    with pytest.raises(r.RegistryError, match="UNIT|scope|NO_TRAINING_AUTHORITY|HUMAN_EXECUTED"):
        r.promote_unit(
            registry,
            "G8",
            Q.DOWNSTREAM_CERTIFIED,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=resolver_objects.get,
            dependency_verifier=dependencies.get,
        )


def test_h2_known_truth_qualified_requires_closed_evidence_gate_and_reviewer():
    dep, ref, dependencies = verified_pair(r, dep_stage=Q.SAME_CODE_PATH)
    registry = r.TDQualificationRegistry((dep, ref), (), (), ())
    controller, _, authority_objects = _actors()
    with pytest.raises(r.RegistryError, match="KNOWN_TRUTH|evidence|reviewer|sealed|closed"):
        r.promote_unit(
            registry,
            "G8",
            Q.KNOWN_TRUTH_QUALIFIED,
            controller_identity=controller,
            reviewer_identity=None,
            authority_object_resolver=authority_objects.get,
            dependency_verifier=dependencies.get,
        )


@pytest.mark.parametrize(
    "controller_actor_id",
    [
        "producer:G8 ",
        " producer:G8",
        "PRODUCER:G8",
        "producer：G8",
        "minted-by-producer-1",
    ],
)
def test_b3_alias_or_self_minted_controller_is_refused(controller_actor_id: str):
    _, _, dependencies, _, registry, _, _, _ = _setup()
    controller, reviewer, authority_objects = _actors(cid=controller_actor_id)
    with pytest.raises(r.RegistryError, match="actor|registry|canonical|self|unknown|independ"):
        r.promote_unit(
            registry,
            "G8",
            Q.REAL_REFERENCE_READY,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=authority_objects.get,
            dependency_verifier=dependencies.get,
        )


def test_b3_reviewer_actor_equal_controller_is_refused():
    _, _, dependencies, _, registry, _, _, _ = _setup()
    controller, reviewer, authority_objects = _actors(cid="C1", rid="C1")
    with pytest.raises(r.RegistryError):
        r.promote_unit(
            registry,
            "G8",
            Q.REAL_REFERENCE_READY,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=authority_objects.get,
            dependency_verifier=dependencies.get,
        )


def test_b3_reviewer_actor_equal_producer_is_refused():
    _, _, dependencies, _, registry, _, _, _ = _setup()
    controller, reviewer, authority_objects = _actors(cid="C1", rid="producer:G8")
    with pytest.raises(r.RegistryError):
        r.promote_unit(
            registry,
            "G8",
            Q.REAL_REFERENCE_READY,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=authority_objects.get,
            dependency_verifier=dependencies.get,
        )


def test_h4_warmed_positive_cache_cannot_survive_resolver_change():
    _, _, dependencies, _, registry, _, _, authority_objects = _setup()
    cache: dict[object, object] = {}
    baseline = r.derive_real_reference_ready(
        "G8",
        registry,
        dependency_verifier=dependencies.get,
        authority_object_resolver=authority_objects.get,
        verification_cache=cache,
    )
    assert baseline.ready
    result = r.derive_real_reference_ready(
        "G8",
        registry,
        dependency_verifier=lambda _sha: None,
        authority_object_resolver=authority_objects.get,
        verification_cache=cache,
    )
    assert not result.ready, "cached positives must not authenticate a different/empty resolver"


def test_h3_caller_poisoned_cache_cannot_authenticate_missing_dependencies():
    dep, ref, _, _, registry, _, _, authority_objects = _setup()
    poison: dict[object, object] = {}
    for unit in (dep, ref):
        for field in r._IDENTITY_64_FIELDS + r._IDENTITY_40_FIELDS:
            poison[("dependency-object-v1", unit.canonical_sha256(), field, getattr(unit, field))] = (True, None)
    result = r.derive_real_reference_ready(
        "G8",
        registry,
        dependency_verifier=lambda _sha: None,
        authority_object_resolver=authority_objects.get,
        verification_cache=poison,
    )
    assert not result.ready, "caller cache entries are not authentication authority"


def test_h6_deleted_revocation_history_cannot_be_rebuilt_into_active_lineage():
    ref, dependencies, registry, controller, reviewer, resolver_objects, _, _ = _human_execution_registry()
    # Recreate the exact RRR registry used by Macha before adding HUMAN_EXECUTABLE prerequisites.
    rrr_registry = r.TDQualificationRegistry(
        registry.units,
        tuple(p for p in registry.prerequisites if p.gate == "REAL_REFERENCE_READY"),
        registry.promotions,
        registry.revocations,
    )
    revoked = r.revoke_or_supersede(
        rrr_registry,
        "G8",
        L.REVOKED_BY_DEFECT,
        reason_class="DEFECT",
        controller_identity=controller,
        authority_object_resolver=resolver_objects.get,
        dependency_verifier=dependencies.get,
    )
    forged_unit = dataclasses.replace(revoked.units_by_id()["G8"], active_lineage_status=L.ACTIVE)
    forged_back = r.TDQualificationRegistry(
        tuple(forged_unit if u.unit_id == "G8" else u for u in revoked.units),
        registry.prerequisites,
        revoked.promotions,
        (),
    )
    with pytest.raises(r.RegistryError, match="history|revocation|replay|anchor|genesis"):
        r.promote_unit(
            forged_back,
            "G8",
            Q.HUMAN_EXECUTABLE,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=resolver_objects.get,
            dependency_verifier=dependencies.get,
        )


def test_h5_fabricated_rrr_history_cannot_enable_human_executable():
    dep, ref, dependencies = verified_pair(r, dep_stage=Q.REAL_REFERENCE_READY)
    controller, reviewer, authority_objects = _actors()
    predecessor = dataclasses.replace(dep, qualification_stage=Q.KNOWN_TRUTH_QUALIFIED)
    fake_snapshot = {
        "schema": "TD_QUALIFICATION_REGISTRY_V1",
        "units": [predecessor.to_payload(), ref.to_payload()],
        "prerequisites": [],
        "promotions": [],
        "revocations": [],
    }
    fake_receipt = r.PromotionReceipt(
        "G8",
        Q.KNOWN_TRUTH_QUALIFIED,
        Q.REAL_REFERENCE_READY,
        r.canonical_sha256(fake_snapshot),
        predecessor.canonical_sha256(),
        (),
        (),
        dep.manifest_sha,
        dep.access_policy_sha,
        controller,
        reviewer,
    )
    process_evidence = {
        "object_role": "PREREQUISITE_EVIDENCE",
        "requirement_class": "PROCESS_ISOLATION",
        "producer_process_isolated": True,
        "harness_drives_finalization": True,
        "reader_fit_values_out_of_process": True,
        "protected_partitions_physically_absent": True,
    }
    custody_evidence = {
        "object_role": "PREREQUISITE_EVIDENCE",
        "requirement_class": "CROSS_PROCESS_LEDGER_CUSTODY",
        "persistent_ledger": True,
        "signing_key_out_of_process": True,
        "key_custodian": "HARNESS",
    }
    resolver_objects = dict(authority_objects)
    resolver_objects[r.canonical_sha256(fake_snapshot)] = fake_snapshot
    resolver_objects[r.canonical_sha256(process_evidence)] = process_evidence
    resolver_objects[r.canonical_sha256(custody_evidence)] = custody_evidence

    def external(pid: str, requirement_class: str, evidence: dict[str, object]):
        return dataclasses.replace(
            verified_prereq(
                r,
                dep,
                ref,
                pid=pid,
                gate="HUMAN_EXECUTABLE",
                requirement_class=requirement_class,
            ),
            evidence_receipt_sha=r.canonical_sha256(evidence),
        )

    forged_registry = r.TDQualificationRegistry(
        (dep, ref),
        (
            external("ISO", "PROCESS_ISOLATION", process_evidence),
            external("CUS", "CROSS_PROCESS_LEDGER_CUSTODY", custody_evidence),
        ),
        (fake_receipt,),
        (),
    )
    with pytest.raises(r.RegistryError, match="history|replay|lawful|genesis|anchor"):
        r.promote_unit(
            forged_registry,
            "G8",
            Q.HUMAN_EXECUTABLE,
            controller_identity=controller,
            reviewer_identity=reviewer,
            authority_object_resolver=resolver_objects.get,
            dependency_verifier=dependencies.get,
        )
