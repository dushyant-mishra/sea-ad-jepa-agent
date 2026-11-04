"""Macha K02 RED against PR #543 head 7e4bffe8 (tests only; code UNCHANGED).

K01 (subclass overriding validate_current) is closed by #543's exact-type check and unbound call.
K02 is a separate route to the same false C3 report:

  C3_CURRENT_REGISTRY = PASS is derived from a history-custody object carried in the
  self-asserted actor_context mapping. RegistryHistoryCustody.validate_current compares the
  registry with the object's own stored state and never checks the object's provenance (lawful
  history-free genesis, HMAC chain). An object of the exact type whose stored state was forged
  therefore certifies fabricated history. This includes a unit at KNOWN_TRUTH_QUALIFIED with no
  anchored history, a genesis the lawful constructor refuses.

The barrier docstring calls the mapping-carried custody "already-verifiable"; these tests show
it is not. Latent: C1 and C5-C9 still FAIL, so overall stays RED and FINAL stays refused.

Repair-agnostic: the tests require only that forged custody does not earn PASS. Failing C3
closed for mapping-carried custody until an authenticated context supplies it is an acceptable
repair. So is any provenance binding that a caller holding only the in-process object cannot
forge.

Synthetic fixtures only. No sealed exposure, training, GPU, real data or Stage 4.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import copy
import dataclasses

import pytest

from scripts.v5.td_unified import registry_v1 as r
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q
from scripts.v5.td_unified.task4_authority_barrier_v1 import evaluate_task4_preauthority_barrier
from tests.v5.td_unified.registry_v1_dependency_fixtures import (
    bind_actor_registry,
    verified_pair,
    verified_prereq,
)

KEY = b"macha-k02-history-custody-key"


def _genesis():
    dep, ref, dependencies = verified_pair(r, dep_stage=Q.SEMANTICS_ONLY, ref_stage=Q.SEMANTICS_ONLY)
    prerequisite = verified_prereq(r, dep, ref, required_stage=Q.SEMANTICS_ONLY)
    controller = {"object_role": "QUALIFICATION_CONTROLLER", "actor_id": "C1"}
    reviewer = {"object_role": "INDEPENDENT_REVIEWER", "actor_id": "R1"}
    actors = {r.canonical_sha256(controller): controller, r.canonical_sha256(reviewer): reviewer}
    registry, _ = bind_actor_registry(
        r,
        r.TDQualificationRegistry((dep, ref), (prerequisite,), (), ()),
        {**dependencies, **actors},
        trusted_actor_objects=tuple(actors.values()),
    )
    return dep, registry, r.canonical_sha256(controller), r.canonical_sha256(reviewer)


def _fabricated_promotion(dep, genesis, controller, reviewer):
    receipt = r.PromotionReceipt(
        unit_id="G8",
        source_stage=Q.SEMANTICS_ONLY,
        destination_stage=Q.FIXTURE_SAME_INTERFACE,
        pre_registry_sha=genesis.canonical_sha256(),
        unit_identity_sha=dep.canonical_sha256(),
        prerequisite_ids=tuple(p.prerequisite_id for p in genesis.prerequisites),
        prerequisite_shas=tuple(p.canonical_sha256() for p in genesis.prerequisites),
        manifest_sha=dep.manifest_sha,
        access_policy_sha=dep.access_policy_sha,
        controller_identity=controller,
        reviewer_identity=reviewer,
    )
    promoted = dataclasses.replace(dep, qualification_stage=Q.FIXTURE_SAME_INTERFACE)
    return r.TDQualificationRegistry(
        tuple(promoted if u.unit_id == "G8" else u for u in genesis.units),
        genesis.prerequisites,
        (receipt,),
        (),
        actor_registry_sha=genesis.actor_registry_sha,
    )


def _store_state_from(custody, reg):
    custody._actor_registry_sha = reg.actor_registry_sha
    custody._unit_state = r._unit_payloads(reg)
    custody._promotions, custody._revocations = r._receipt_payloads(reg)
    return custody


def _forge_new(reg, genesis):
    f = object.__new__(r.RegistryHistoryCustody)
    f._key, f._events, f._head = b"attacker", [], "0" * 64
    return _store_state_from(f, reg)


def _forge_copy_of_lawful(reg, genesis):
    return _store_state_from(copy.copy(r.RegistryHistoryCustody(genesis, attestation_key=KEY)), reg)


class _Sub(r.RegistryHistoryCustody):
    def __init__(self):
        pass


def _forge_retyped_subclass(reg, genesis):
    inst = _Sub()
    inst.__class__ = r.RegistryHistoryCustody
    return _store_state_from(inst, reg)


class _Store:
    def replay(self):
        raise RuntimeError("no persistent store in this probe")


def _c3(reg, custody):
    status = evaluate_task4_preauthority_barrier(
        "G8", reg, custody_store=_Store(), expected_head="0" * 64, actor_context={"history_custody": custody}
    )
    assert status.overall == "RED"  # latent: C1 and C5-C9 still fail closed
    return status.checks["C3_CURRENT_REGISTRY"]


@pytest.mark.parametrize("forge", [_forge_new, _forge_copy_of_lawful, _forge_retyped_subclass])
def test_k02_red_forged_exact_type_custody_must_not_certify_fabricated_promotion(forge):
    dep, genesis, controller, reviewer = _genesis()
    fabricated = _fabricated_promotion(dep, genesis, controller, reviewer)
    forged = forge(fabricated, genesis)
    assert type(forged) is r.RegistryHistoryCustody
    assert _c3(fabricated, forged) != "PASS", "K02: exact-type custody with forged state certified fabricated history"


def test_k02_red_forged_custody_must_not_certify_known_truth_with_no_anchored_history():
    dep, genesis, _, _ = _genesis()
    advanced = dataclasses.replace(dep, qualification_stage=Q.KNOWN_TRUTH_QUALIFIED)
    fabricated = r.TDQualificationRegistry(
        tuple(advanced if u.unit_id == "G8" else u for u in genesis.units),
        genesis.prerequisites,
        (),
        (),
        actor_registry_sha=genesis.actor_registry_sha,
    )
    with pytest.raises(r.RegistryError):
        r.RegistryHistoryCustody(fabricated, attestation_key=KEY)  # the lawful constructor refuses this genesis
    assert _c3(fabricated, _forge_new(fabricated, genesis)) != "PASS", (
        "K02: forged custody certified KNOWN_TRUTH_QUALIFIED with no anchored history")


def test_guard_lawful_custody_still_refuses_fabricated_promotion():
    dep, genesis, controller, reviewer = _genesis()
    lawful = r.RegistryHistoryCustody(genesis, attestation_key=KEY)
    assert _c3(_fabricated_promotion(dep, genesis, controller, reviewer), lawful) != "PASS"
