"""Macha K03 RED against PR #543 head 7e4bffe8 (tests only; code UNCHANGED).

C1_PERSISTENT_REVOCATION reaches its required value PERSISTENT_EXTERNAL whenever
custody_store.replay() returns an object with authoritative=True and head == expected_head.
Neither the store nor the replay result is type-checked, and the caller supplies both the
store and expected_head. A two-line stand-in store therefore satisfies C1. The real
PersistentCustodyStore always replays authoritative=False (task4_custody_store_v1.py:635).

Erratum to Macha #541 finding A2: "C1 is always FAIL" holds only for the real store. The
barrier does not require the real store.

Combined with K02 (forged history custody), the caller-supplied inputs alone bring C1 and
C3 to their required values. Only the hard-coded C5-C9 FAIL keeps the barrier RED.
Latent today. Repair-agnostic: the tests require only that a self-asserted store does not
earn PERSISTENT_EXTERNAL.

Synthetic fixtures only. No sealed exposure, training, GPU, real data or Stage 4.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

from types import SimpleNamespace

from scripts.v5.td_unified.task4_authority_barrier_v1 import evaluate_task4_preauthority_barrier
from scripts.v5.td_unified.task4_custody_store_v1 import CustodyReplayResult

HEAD = "f" * 64


class _SelfAssertedStore:
    def __init__(self, result):
        self._result = result

    def replay(self):
        return self._result


def _c1(store):
    status = evaluate_task4_preauthority_barrier(
        "G8", object(), custody_store=store, expected_head=HEAD, actor_context={}
    )
    assert status.overall == "RED"  # latent: C5-C9 still fail closed
    return status.checks["C1_PERSISTENT_REVOCATION"]


def test_k03_red_duck_typed_store_must_not_earn_persistent_external():
    store = _SelfAssertedStore(SimpleNamespace(authoritative=True, head=HEAD))
    assert _c1(store) != "PERSISTENT_EXTERNAL", "K03: self-asserted store earned C1 PERSISTENT_EXTERNAL"


def test_k03_red_exact_replay_result_from_a_fake_store_must_not_earn_persistent_external():
    result = CustodyReplayResult(HEAD, 1, frozenset(), True)
    assert type(result) is CustodyReplayResult
    assert _c1(_SelfAssertedStore(result)) != "PERSISTENT_EXTERNAL", (
        "K03: exact-type replay result from a fake store earned C1 PERSISTENT_EXTERNAL")
