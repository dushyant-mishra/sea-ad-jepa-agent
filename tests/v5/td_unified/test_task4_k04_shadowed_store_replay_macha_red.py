"""Macha K04 RED against PR #545 head f68513ae (tests only; code UNCHANGED).

#545 closes K03 by requiring `type(custody_store) is PersistentCustodyStore` and by calling
`PersistentCustodyStore.replay(custody_store)` through the class. But the class `replay`
dispatches to `self.replay_optimized()`, which then calls `self._replay_semantic()`, both
through the INSTANCE. PersistentCustodyStore is an ordinary mutable class (no __slots__,
no __setattr__ guard), so an instance attribute shadows either method. A store of the exact
type then returns an exact-type `CustodyReplayResult(..., authoritative=True)` and earns
C1_PERSISTENT_REVOCATION = PERSISTENT_EXTERNAL.

The honest V1 store can never do this: `_replay_semantic` hard-codes authoritative=False
(task4_custody_store_v1.py:635). So the only route to PERSISTENT_EXTERNAL in V1 is forgery.
This is K02's lesson applied to C1: exact type is not provenance.

Latent today: C3 can no longer PASS (#545) and C5-C9 stay hard FAIL, so the barrier stays RED.
Repair-agnostic: the tests require only that a store with shadowed replay state does not earn
PERSISTENT_EXTERNAL. A guard test checks that an honest store still yields FAIL, not an error.

Synthetic fixtures only. No sealed exposure, training, GPU, real data or Stage 4.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.v5.td_unified.task4_authority_barrier_v1 import evaluate_task4_preauthority_barrier
from scripts.v5.td_unified.task4_custody_store_v1 import CustodyReplayResult, PersistentCustodyStore

HEAD = "f" * 64


def _forged_result():
    result = CustodyReplayResult(HEAD, 1, frozenset(), True)
    assert type(result) is CustodyReplayResult
    return result


def _c1(store):
    assert type(store) is PersistentCustodyStore
    status = evaluate_task4_preauthority_barrier(
        "G8", object(), custody_store=store, expected_head=HEAD, actor_context={}
    )
    assert status.overall == "RED"  # latent: C3 and C5-C9 still fail closed
    return status.checks["C1_PERSISTENT_REVOCATION"]


def _genuine_store(tmp_path: Path) -> PersistentCustodyStore:
    return PersistentCustodyStore(tmp_path / "custody", None, None)


def test_k04_guard_honest_store_never_earns_persistent_external(tmp_path):
    assert _c1(_genuine_store(tmp_path)) == "FAIL"


@pytest.mark.parametrize("shadowed", ["replay_optimized", "_replay_semantic"])
def test_k04_red_genuine_store_with_shadowed_replay_must_not_earn_persistent_external(tmp_path, shadowed):
    store = _genuine_store(tmp_path)
    setattr(store, shadowed, _forged_result)
    assert _c1(store) != "PERSISTENT_EXTERNAL", (
        f"K04: exact-type store with instance-shadowed {shadowed} earned C1 PERSISTENT_EXTERNAL")


def test_k04_red_uninitialised_exact_type_store_must_not_earn_persistent_external():
    store = object.__new__(PersistentCustodyStore)
    store.replay_optimized = _forged_result
    assert _c1(store) != "PERSISTENT_EXTERNAL", (
        "K04: object.__new__ store with no custody root earned C1 PERSISTENT_EXTERNAL")
