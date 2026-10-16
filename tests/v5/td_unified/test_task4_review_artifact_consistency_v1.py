from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / "results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_CANDIDATE_STATE_V1.json"
PACKET = ROOT / "docs/agent/UNIFIED_TASK4_CANDIDATE_REVIEW_PACKET_20261016.md"
LEDGER = ROOT / "docs/agent/UNIFIED_TASK4_EXECUTION_LEDGER_20261016.md"

REJECTED_1 = "b31371d62f3270c965d321e61c35898ca6be3721"
REJECTED_2 = "c537db4e7b5b916cb3ddee1872fd4afa623a9b33"
REJECTED_3 = "b5ed724cbc6a39d4f2cd68103c5367c2cfafcff3"
VERIFIED_SUCCESSOR3 = "4d4947af63ba067f2f1f06cb5f80ec1fd5bc67e7"


def test_task4_review_artifacts_preserve_three_rejections_and_zero_authority():
    state = json.loads(STATE.read_text(encoding="utf-8"))
    packet = PACKET.read_text(encoding="utf-8")
    ledger = LEDGER.read_text(encoding="utf-8")

    assert state["authority_effect"] == "NONE"
    rejected = state["rejected_candidates"]
    assert [x["candidate_sha"] for x in rejected] == [REJECTED_1, REJECTED_2, REJECTED_3]
    assert rejected[0]["verdict"] == "REJECT_CALLER_SELF_MINTED_TRUST_ROOTS"
    assert rejected[1]["verdict"] == "REJECT_POST_SEAL_OBJECT_SUBSTITUTION"
    assert rejected[2]["verdict"] == "REJECT_CALLER_FABRICABLE_ADVANCED_CAMPAIGN_STATE"
    assert state["last_verified_code_test_sha"] == VERIFIED_SUCCESSOR3
    law = state["successor_authority_law"]
    assert law["repository_replay_authoritative"] is False
    assert law["genuine_external_root_wired"] is False
    assert law["campaign_binds_exact_definition_sha"] is True
    assert law["campaign_binds_exact_realization_root"] is True
    assert law["in_process_lifecycle_provenance_required"] is True
    assert law["direct_advanced_campaign_construction_allowed"] is False
    assert law["lifecycle_provenance_scope"] == "PROCESS_LOCAL_MECHANICS_ONLY"
    assert state["target_winner"] == "NONE"
    assert state["representation_winner"] == "NONE"
    assert state["real_training"] == "OFF"
    assert state["stage4_authorized"] is False

    for text in (packet, ledger):
        for sha in (REJECTED_1, REJECTED_2, REJECTED_3, VERIFIED_SUCCESSOR3):
            assert sha in text
        assert "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED" in text


def test_review_packet_does_not_rehabilitate_any_rejected_candidate():
    packet = PACKET.read_text(encoding="utf-8")
    assert packet.count("is **rejected**") >= 3
    assert "Do not rehabilitate any rejected candidate" in packet
