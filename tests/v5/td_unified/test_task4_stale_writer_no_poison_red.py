"""Independent Task4 C1(b) RED: stale process handles cannot poison durable custody.

This probes process-local mechanical consistency only; no external trust root
is granted and genuine R4/C1(b) authority remains blocked even after repair.
"""
from __future__ import annotations
import hashlib
import hmac
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest

from scripts.v5.td_unified.task4_actor_attestation_v1 import ActorActionAttestation
from scripts.v5.td_unified.task4_custody_store_v1 import (
    PersistentCustodyStore, Task4CustodyError,
)

ACTOR="a"*64
SIGN_KEY=b"independent-task4-fixture-sign"
ACTOR_KEY=b"independent-task4-fixture-actor"

class Signer:
    signer_identity=ACTOR
    promotion_authority="EXTERNAL_HARNESS_AUTHORITY"
    def sign(self,message):return hmac.new(SIGN_KEY,message,hashlib.sha256).digest()

class Verifier:
    trusted_signer_identities=frozenset({ACTOR})
    trusted_anchor_identities=frozenset({"anchor-fixture"})
    def verify(self,message,signature,signer_identity):
        return signer_identity==ACTOR and hmac.compare_digest(
            signature,hmac.new(SIGN_KEY,message,hashlib.sha256).digest())

class ActorVerifier:
    trusted_signer_identities=frozenset({"fixture-ca"})
    def verify(self,message,signature,signer_identity):
        return signer_identity=="fixture-ca" and hmac.compare_digest(
            signature,hmac.new(ACTOR_KEY,message,hashlib.sha256).digest())

class Publisher:
    anchor_identity="anchor-fixture"
    promotion_authority="EXTERNAL_HEAD_AUTHORITY"
    def publish(self,*,head,event_count):return head

def _open(path):
    return PersistentCustodyStore.open(
        path,verifier=Verifier(),expected_head=None,
        actor_registry={ACTOR:{"role":"QUALIFICATION_CONTROLLER"}},
        frozen_actor_policy={"CUSTODY_APPEND":{"QUALIFICATION_CONTROLLER"}},
        actor_attestation_verifier=ActorVerifier()
    )

def _attest(store,payload):
    subject,seq=store.next_append_subject(payload)
    unsigned=ActorActionAttestation(ACTOR,"QUALIFICATION_CONTROLLER","CUSTODY_APPEND",
                                    subject,seq,b"","fixture-ca")
    sig=hmac.new(ACTOR_KEY,unsigned.message(),hashlib.sha256).digest()
    return ActorActionAttestation(ACTOR,"QUALIFICATION_CONTROLLER","CUSTODY_APPEND",
                                  subject,seq,sig,"fixture-ca")

def _append(store,payload):
    return store.append_event(payload,signer=Signer(),
                              signer_attestation=_attest(store,payload),head_publisher=Publisher())

def test_stale_writer_must_fail_before_bytes_and_leave_chain_replayable(tmp_path:Path):
    fresh=_open(tmp_path)
    stale=_open(tmp_path)  # same genesis observed before any event
    head=_append(fresh,{"kind":"STATE","id":"first"})
    with pytest.raises(Task4CustodyError):
        _append(stale,{"kind":"STATE","id":"stale"})
    # Old code raises *after* writing a duplicate seq=1, irreversibly
    # poisoning the on-disk ledger. Refusal alone is not sufficient.
    reopened=_open(tmp_path)
    assert reopened.replay().head==head
    assert reopened.replay().event_count==1
    assert reopened.replay().authoritative is False

def test_two_racing_issued_writers_cannot_corrupt_custody(tmp_path:Path):
    left,right=_open(tmp_path),_open(tmp_path)
    payloads=[{"kind":"STATE","id":"left"},{"kind":"STATE","id":"right"}]
    def attempt(pair):
        store,payload=pair
        try:
            return ("ok",_append(store,payload))
        except Task4CustodyError:
            return ("refused",None)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(attempt,[(left,payloads[0]),(right,payloads[1])]))
    assert sorted(x[0] for x in outcomes)==["ok","refused"]
    reloaded=_open(tmp_path)
    assert reloaded.replay().event_count==1
    assert reloaded.replay().authoritative is False

def _subprocess_stale_writer(root, label, gate, out):
    store = _open(Path(root))
    gate.wait(timeout=12)
    try:
        out.put(("ok", _append(store, {"kind":"STATE","id":label})))
    except Task4CustodyError:
        out.put(("refused", None))
    except Exception as exc:
        out.put(("unexpected", type(exc).__name__))

def test_separate_os_processes_are_serialized_before_append(tmp_path: Path):
    import multiprocessing
    import os
    if os.name != "posix" or "fork" not in multiprocessing.get_all_start_methods():
        pytest.skip("requires POSIX fork; Windows mechanisms tested separately")
    ctx = multiprocessing.get_context("fork")
    barrier = ctx.Barrier(2)
    results = ctx.Queue()
    workers = [ctx.Process(target=_subprocess_stale_writer,
                args=(str(tmp_path), label, barrier, results))
               for label in ("first", "second")]
    try:
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=15)
        assert all(not worker.is_alive() and worker.exitcode == 0 for worker in workers)
        outcomes = [results.get(timeout=3) for _ in workers]
        assert sorted(x[0] for x in outcomes) == ["ok", "refused"]
        fresh = _open(tmp_path).replay()
        assert fresh.event_count == 1
        assert fresh.authoritative is False
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=3)
