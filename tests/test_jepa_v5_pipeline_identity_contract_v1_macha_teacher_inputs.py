"""Macha pre-pilot RED: the contract said the teacher receives all 2,048
address values, while the PR548 adapter and forward probe give BOTH
encoders the q-excluded base and refuse q in either packed input.

Static/contract-only: no model, forward, optimizer, backward or EMA.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.v5 import jepa_v5_pipeline_identity_contract_v1 as pic

ROOT = Path(__file__).resolve().parents[1]
Q = [1672, 1673, 1674, 1675]
BASE = [a for a in range(2048) if a not in Q]


@pytest.fixture(scope="module")
def coordinates():
    return pic.load_contract(ROOT / pic.CONTRACT_PATH)["components"]["molecular_coordinates"]


def test_vocabulary_is_not_the_values_an_encoder_receives(coordinates):
    assert coordinates["vocabulary_address_ids"] == list(range(2048))
    assert coordinates["teacher_address_ids"] == BASE
    assert coordinates["student_address_ids"] == BASE
    assert coordinates["encoder_input_mode"] == "SHARED_BASE_MASKED_BLOCK_JEPA"
    assert coordinates["teacher_only_query_mode"] == "L04_OWNER_DECISION_PENDING__NOT_IMPLEMENTED"


def test_contract_agrees_with_the_pr548_probe_that_neither_encoder_gets_q(coordinates):
    probe = (ROOT / "scripts/v5/jepa_synth2048_v5_readiness.py").read_text(encoding="utf-8")
    assert '"teacher acquired excluded q address"' in probe
    assert '"student acquired excluded q address"' in probe
    assert not set(Q) & set(coordinates["teacher_address_ids"])
    assert not set(Q) & set(coordinates["student_address_ids"])


def test_request_claiming_the_teacher_receives_query_values_is_refused():
    contract = pic.load_contract(ROOT / pic.CONTRACT_PATH)
    request = pic.expected_run_request(contract)
    request["teacher_address_ids"] = list(range(2048))
    with pytest.raises(pic.PipelineIdentityRefusal, match="MOLECULAR_ORDER_CHANGED__teacher_address_ids"):
        pic.verify_run_request(contract, request)
