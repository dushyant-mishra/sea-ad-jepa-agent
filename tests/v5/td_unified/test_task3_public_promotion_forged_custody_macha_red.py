"""Macha reachability RED for #546 against frozen Task 3 117dd51d (tests only; code UNCHANGED).

#546 R1/R2 call the private helper `_require_history_custody`. This file asks what #546
leaves open: does the custody defect reach an authority stage through the PUBLIC
`promote_unit`, with every other frozen preflight (legacy, actor policy, registered
prerequisite actors, frozen Task 2 manifest + reader-split raw resolver) satisfied?

World: the frozen recheck3 N2 world (`_world`/`_bind`/`_rrr`, Task 2-valid manifest and raw
reader split). Both units are DECLARED KNOWN_TRUTH_QUALIFIED at construction, with no
anchored sealed-challenge history. Frozen Task 3 closes this with custody: no custody is
refused (frozen N2 test) and honest custody refuses the genesis (guard below). Supply a
forged custody instead:
  - SUBCLASS overriding validate_current/_record_transition (R1 at the public entrypoint);
  - EXACT TYPE `object.__new__(RegistryHistoryCustody)` whose anchored state is copied from
    the attacker's own registry. No subclass, so an exact-type check alone (#543 K01 style)
    would not close it; only authenticated history can.

R2 (#546) overwrites only `_head`; nothing consumes head_attestation, so R2 alone changes no
decision. It shows the HMAC chain is never verified, which is the root of the exact-type route.

Synthetic fixtures only. No sealed exposure, training, GPU, real data or Stage 4.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import pytest

from scripts.v5.td_unified import registry_v1 as r
from scripts.v5.td_unified.authority_v1 import QualificationStage as Q
from tests.v5.td_unified import registry_v1_dependency_fixtures as fx
from tests.v5.td_unified.test_registry_v1_macha_recheck3 import _bind, _rrr, _world


class _SubclassCustody(r.RegistryHistoryCustody):
    def __init__(self):
        pass

    def validate_current(self, registry):
        return None

    def _record_transition(self, before, after, *, kind):
        return None


def _exact_type_forged_custody(registry):
    custody = object.__new__(r.RegistryHistoryCustody)
    custody._key = b"attacker-chosen-key"
    custody._actor_registry_sha = registry.actor_registry_sha
    custody._unit_state = r._unit_payloads(registry)
    custody._promotions, custody._revocations = r._receipt_payloads(registry)
    custody._events = []
    custody._head = "0" * 64
    assert type(custody) is r.RegistryHistoryCustody
    return custody


def _declared_known_truth_world(monkeypatch):
    (g8, ref), store = _world(monkeypatch, [("G8", Q.KNOWN_TRUTH_QUALIFIED), ("REF", Q.KNOWN_TRUTH_QUALIFIED)])
    return _bind((g8, ref), (fx.verified_prereq(r, g8, ref),), store)


def test_guard_honest_custody_refuses_declared_known_truth_genesis(monkeypatch):
    registry = _declared_known_truth_world(monkeypatch)[0]
    with pytest.raises(r.RegistryError, match="KNOWN_TRUTH|genesis"):
        r.RegistryHistoryCustody(registry, attestation_key=b"harness-key")


@pytest.mark.parametrize(
    "factory",
    [lambda reg: _SubclassCustody(), _exact_type_forged_custody],
    ids=["subclass", "exact_type_object_new"],
)
def test_red_public_promotion_with_forged_custody_must_not_reach_real_reference_ready(monkeypatch, factory):
    registry, controller, reviewer, objects = _declared_known_truth_world(monkeypatch)
    with pytest.raises(r.RegistryError, match="custody|history"):
        promoted = _rrr(registry, controller, reviewer, objects, custody=factory(registry))
        stage = promoted.units_by_id()["G8"].qualification_stage.value
        pytest.fail(f"forged custody reached {stage} via public promote_unit (N2 side door reopened)")
