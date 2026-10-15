from __future__ import annotations

import dataclasses

import pytest

from scripts.v5.td_unified import registry_v1 as r
from scripts.v5.td_unified.authority_v1 import ActiveLineageStatus as L
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q
from tests.v5.td_unified.registry_v1_dependency_fixtures import (
    bind_actor_registry,
    verified_pair,
    verified_prereq,
)


KEY = b"task3-history-custody-test-key"


def _actors():
    controller = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": "C1"}
    reviewer = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": "R1"}
    objects = {
        r.canonical_sha256(controller): controller,
        r.canonical_sha256(reviewer): reviewer,
    }
    return r.canonical_sha256(controller), r.canonical_sha256(reviewer), objects


def _genesis_below_known_truth():
    dep, ref, dependencies = verified_pair(
        r, dep_stage=Q.SEMANTICS_ONLY, ref_stage=Q.SEMANTICS_ONLY
    )
    prerequisite = verified_prereq(
        r, dep, ref, required_stage=Q.SEMANTICS_ONLY
    )
    registry = r.TDQualificationRegistry((dep, ref), (prerequisite,), (), ())
    controller, reviewer, actors = _actors()
    registry, objects = bind_actor_registry(
        r,
        registry,
        {**dependencies, **actors},
        trusted_actor_objects=tuple(actors.values()),
    )
    return dep, ref, dependencies, registry, controller, reviewer, objects


def test_b5_history_custody_rejects_known_truth_or_advanced_or_prepopulated_genesis():
    dep, ref, dependencies = verified_pair(
        r, dep_stage=Q.KNOWN_TRUTH_QUALIFIED, ref_stage=Q.SAME_CODE_PATH
    )
    controller, reviewer, actors = _actors()
    registry = r.TDQualificationRegistry((dep, ref), (), (), ())
    registry, _ = bind_actor_registry(
        r,
        registry,
        {**dependencies, **actors},
        trusted_actor_objects=tuple(actors.values()),
    )
    with pytest.raises(r.RegistryError, match="genesis|history|KNOWN_TRUTH|sealed"):
        r.RegistryHistoryCustody(registry, attestation_key=KEY)


def test_b5_history_custody_records_lawful_prequalification_promotion_and_allows_prerequisite_only_change():
    _, ref, dependencies, registry, controller, reviewer, objects = _genesis_below_known_truth()
    custody = r.RegistryHistoryCustody(registry, attestation_key=KEY)
    promoted = r.promote_unit(
        registry,
        "G8",
        Q.SAME_CODE_PATH,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=objects.get,
        dependency_verifier=dependencies.get,
        history_custody=custody,
    )
    g8 = promoted.units_by_id()["G8"]
    extra = verified_prereq(
        r,
        g8,
        ref,
        pid="EXTRA",
        gate="REAL_REFERENCE_READY",
        required_stage=Q.SEMANTICS_ONLY,
        requirement_class="UNIT",
    )
    changed_prereqs = r.TDQualificationRegistry(
        promoted.units,
        promoted.prerequisites + (extra,),
        promoted.promotions,
        promoted.revocations,
        actor_registry_sha=promoted.actor_registry_sha,
    )
    custody.validate_current(changed_prereqs)


def test_b5_history_custody_rejects_unrecorded_fabricated_promotion():
    dep, ref, dependencies, genesis, controller, reviewer, objects = _genesis_below_known_truth()
    custody = r.RegistryHistoryCustody(genesis, attestation_key=KEY)
    promoted_unit = dataclasses.replace(dep, qualification_stage=Q.SAME_CODE_PATH)
    receipt = r.PromotionReceipt(
        unit_id="G8",
        source_stage=Q.SEMANTICS_ONLY,
        destination_stage=Q.SAME_CODE_PATH,
        pre_registry_sha=genesis.canonical_sha256(),
        unit_identity_sha=dep.canonical_sha256(),
        prerequisite_ids=tuple(p.prerequisite_id for p in genesis.prerequisites),
        prerequisite_shas=tuple(p.canonical_sha256() for p in genesis.prerequisites),
        manifest_sha=dep.manifest_sha,
        access_policy_sha=dep.access_policy_sha,
        controller_identity=controller,
        reviewer_identity=reviewer,
    )
    forged = r.TDQualificationRegistry(
        tuple(promoted_unit if u.unit_id == "G8" else u for u in genesis.units),
        genesis.prerequisites,
        (receipt,),
        (),
        actor_registry_sha=genesis.actor_registry_sha,
    )
    with pytest.raises(r.RegistryError, match="history|custody|head|event|anchor"):
        custody.validate_current(forged)


def test_b5_history_custody_rejects_deleted_recorded_revocation_below_known_truth():
    _, _, dependencies, genesis, controller, reviewer, objects = _genesis_below_known_truth()
    custody = r.RegistryHistoryCustody(genesis, attestation_key=KEY)
    promoted = r.promote_unit(
        genesis,
        "G8",
        Q.SAME_CODE_PATH,
        controller_identity=controller,
        reviewer_identity=reviewer,
        authority_object_resolver=objects.get,
        dependency_verifier=dependencies.get,
        history_custody=custody,
    )
    revoked = r.revoke_or_supersede(
        promoted,
        "G8",
        L.REVOKED_BY_DEFECT,
        reason_class="DEFECT",
        controller_identity=controller,
        authority_object_resolver=objects.get,
        dependency_verifier=dependencies.get,
        history_custody=custody,
    )
    forged_unit = dataclasses.replace(revoked.units_by_id()["G8"], active_lineage_status=L.ACTIVE)
    forged = r.TDQualificationRegistry(
        tuple(forged_unit if u.unit_id == "G8" else u for u in revoked.units),
        revoked.prerequisites,
        revoked.promotions,
        (),
        actor_registry_sha=revoked.actor_registry_sha,
    )
    with pytest.raises(r.RegistryError, match="history|custody|revocation|event|head"):
        custody.validate_current(forged)
