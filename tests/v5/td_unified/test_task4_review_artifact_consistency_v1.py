from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / "results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_CANDIDATE_STATE_V1.json"
PACKET = ROOT / "docs/agent/UNIFIED_TASK4_CANDIDATE_REVIEW_PACKET_20261016.md"
LEDGER = ROOT / "docs/agent/UNIFIED_TASK4_EXECUTION_LEDGER_20261016.md"

REJECTED = "b31371d62f3270c965d321e61c35898ca6be3721"
VERIFIED_SUCCESSOR = "ba3e521ff58ce8ad65f49d9fa0930871991a96de"


def test_task4_review_artifacts_preserve_rejected_predecessor_and_zero_authority():
    state = json.loads(STATE.read_text(encoding="utf-8"))
    packet = PACKET.read_text(encoding="utf-8")
    ledger = LEDGER.read_text(encoding="utf-8")

    assert state["authority_effect"] == "NONE"
    assert state["rejected_predecessor"]["candidate_sha"] == REJECTED
    assert state["rejected_predecessor"]["verdict"] == "REJECT_CALLER_SELF_MINTED_TRUST_ROOTS"
    assert state["last_verified_code_test_sha"] == VERIFIED_SUCCESSOR
    assert state["successor_authority_law"]["repository_replay_authoritative"] is False
    assert state["successor_authority_law"]["genuine_external_root_wired"] is False
    assert state["target_winner"] == "NONE"
    assert state["representation_winner"] == "NONE"
    assert state["real_training"] == "OFF"
    assert state["stage4_authorized"] is False

    for text in (packet, ledger):
        assert REJECTED in text
        assert VERIFIED_SUCCESSOR in text
        assert "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED" in text


def test_review_packet_does_not_rehabilitate_rejected_candidate():
    packet = PACKET.read_text(encoding="utf-8")
    assert "It is **rejected**" in packet
    assert "Do not rehabilitate `b31371d6...`" in packet
