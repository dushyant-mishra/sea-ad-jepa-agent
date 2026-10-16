from __future__ import annotations

import hashlib
import hmac
from pathlib import Path

from scripts.v5.td_unified.task4_custody_store_v1 import PersistentCustodyStore, revocation_subject_identity


KEY = b"fixture-perf-key"
class S:
    signer_identity = "perf-harness"
    promotion_authority = "EXTERNAL_HARNESS_AUTHORITY"
    def sign(self, m): return hmac.new(KEY, m, hashlib.sha256).digest()
class V:
    trusted_signer_identities = frozenset({"perf-harness"})
    trusted_anchor_identities = frozenset({"perf-anchor"})
    def verify(self, m, s, i): return i == "perf-harness" and hmac.compare_digest(s, hmac.new(KEY, m, hashlib.sha256).digest())
class A:
    anchor_identity = "perf-anchor"
    promotion_authority = "EXTERNAL_HEAD_AUTHORITY"
    def publish(self, *, head, event_count): return head


def test_reference_and_optimized_replay_are_semantically_identical(tmp_path: Path):
    store = PersistentCustodyStore.open(tmp_path, verifier=V(), expected_head=None)
    signer, anchor = S(), A()
    for i in range(25):
        subject = revocation_subject_identity({"unit_id": f"u{i}", "manifest_sha": f"{i:064x}"})
        store.append_event({"kind": "REVOCATION", "subject_id": subject}, signer=signer, head_publisher=anchor)
    reference = store.replay_reference()
    optimized = store.replay_optimized()
    assert reference == optimized
    assert reference.event_count == 25


def test_projected_scale_constants_are_explicit():
    from scripts.v5.td_unified.task4_custody_store_v1 import HISTORICAL_SCALE_EVENTS, PROJECTED_SCALE_EVENTS
    assert HISTORICAL_SCALE_EVENTS == 10_000
    assert PROJECTED_SCALE_EVENTS == 100_000
