from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / "results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_CANDIDATE_STATE_V1.json"
PACKET = ROOT / "docs/agent/UNIFIED_TASK4_CANDIDATE_REVIEW_PACKET_20261016.md"
LEDGER = ROOT / "docs/agent/UNIFIED_TASK4_EXECUTION_LEDGER_20261016.md"

REJECTED_1 = "b31371d62f3270c965d321e61c35898ca6be3721"
REJECTED_2 = "c537db4e7b5b916cb3ddee1872fd4afa623a9b33"
VERIFIED_SUCCESSOR2 = "89fb48d581ba37bce9496854d039d900535d47c8"


def test_task4_review_artifacts_preserve_both_rejections_and_zero_authority():
    state = json.loads(STATE.read_text(encoding="utf-8"))
    packet = PACKET.read_text(encoding="utf-8")
    ledger = LEDGER.read_text(encoding="utf-8")

    assert state["authority_effect"] == "NONE"
    rejected = state["rejected_candidates"]
    assert [x["candidate_sha"] for x in rejected] == [REJECTED_1, REJECTED_2]
    assert rejected[0]["verdict"] == "REJECT_CALLER_SELF_MINTED_TRUST_ROOTS"
    assert rejected[1]["verdict"] == "REJECT_POST_SEAL_OBJECT_SUBSTITUTION"
    assert state["last_verified_code_test_sha"] == VERIFIED_SUCCESSOR2
    assert state["successor_authority_law"]["repository_replay_authoritative"] is False
    assert state["successor_authority_law"]["genuine_external_root_wired"] is False
    assert state["successor_authority_law"]["campaign_binds_exact_definition_sha"] is True
    assert state["successor_authority_law"]["campaign_binds_exact_realization_root"] is True
    assert state["target_winner"] == "NONE"
    assert state["representation_winner"] == "NONE"
    assert state["real_training"] == "OFF"
    assert state["stage4_authorized"] is False

    for text in (packet, ledger):
        for sha in (REJECTED_1, REJECTED_2, VERIFIED_SUCCESSOR2):
            assert sha in text
        assert "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED" in text


def test_review_packet_does_not_rehabilitate_either_rejected_candidate():
    packet = PACKET.read_text(encoding="utf-8")
    assert packet.count("is **rejected**") >= 2
    assert "Do not rehabilitate either rejected candidate" in packet
