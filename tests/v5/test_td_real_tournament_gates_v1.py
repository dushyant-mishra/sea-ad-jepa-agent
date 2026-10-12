from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_real_tournament_contract_v1 as C  # noqa: E402
import td_real_tournament_gates_v1 as G  # noqa: E402


def _bindings(candidate):
    contract = C.load_real_tournament_contract(); gates = contract["candidates"][candidate]["required_gates"]
    return {g:{"qualified_gate_executor_sha256":("1"*63 + hex(i%16)[2:]),"estimand_sha256":("2"*63 + hex(i%16)[2:]),"decision_rule_sha256":("3"*63 + hex(i%16)[2:])} for i,g in enumerate(gates)}


def _outputs(candidate, bindings, status="PASS"):
    return {g:{**b,"status":status,"evidence_payload_sha256":"a"*64,"raw_sufficient_statistics":{"n_donors":3}} for g,b in bindings.items()}


def test_gate_bridge_requires_exact_candidate_gate_set_and_bound_identities():
    candidate = "C1_SHARED_EMERGENT"; bindings = _bindings(candidate); outputs = _outputs(candidate, bindings)
    receipt = G.evaluate_candidate(candidate, outputs, bindings)
    assert receipt.candidate_id == candidate
    assert set(receipt.gates) == set(C.load_real_tournament_contract()["candidates"][candidate]["required_gates"])
    assert receipt.status == "PASS"


def test_any_fail_fails_candidate_and_any_not_estimable_keeps_unresolved():
    candidate="C1_SHARED_EMERGENT"; bindings=_bindings(candidate); outputs=_outputs(candidate, bindings)
    first = next(iter(outputs)); outputs[first]["status"]="FAIL"
    assert G.evaluate_candidate(candidate, outputs, bindings).status == "FAIL"
    outputs=_outputs(candidate, bindings); outputs[first]["status"]="NOT_ESTIMABLE"
    assert G.evaluate_candidate(candidate, outputs, bindings).status == "NOT_ESTIMABLE"


def test_missing_gate_or_identity_drift_refuses():
    candidate="C1_SHARED_EMERGENT"; bindings=_bindings(candidate); outputs=_outputs(candidate, bindings)
    outputs.pop(next(iter(outputs)))
    with pytest.raises(G.GateBridgeError, match="exact required gate set"):
        G.evaluate_candidate(candidate, outputs, bindings)
    outputs=_outputs(candidate, bindings); first=next(iter(outputs)); outputs[first]["decision_rule_sha256"]="f"*64
    with pytest.raises(G.GateBridgeError, match="decision_rule_sha256"):
        G.evaluate_candidate(candidate, outputs, bindings)


def test_invalid_status_or_missing_raw_statistics_refuses():
    candidate="C1_SHARED_EMERGENT"; bindings=_bindings(candidate); outputs=_outputs(candidate, bindings)
    first=next(iter(outputs)); outputs[first]["status"]="MAYBE"
    with pytest.raises(G.GateBridgeError, match="PASS/FAIL/NOT_ESTIMABLE"):
        G.evaluate_candidate(candidate, outputs, bindings)
    outputs=_outputs(candidate, bindings); outputs[first].pop("raw_sufficient_statistics")
    with pytest.raises(G.GateBridgeError, match="raw_sufficient_statistics"):
        G.evaluate_candidate(candidate, outputs, bindings)


def test_receipt_carries_no_authority():
    candidate="C1_SHARED_EMERGENT"; bindings=_bindings(candidate)
    receipt=G.evaluate_candidate(candidate,_outputs(candidate,bindings),bindings)
    assert all(v is False for v in receipt.authority.values())
