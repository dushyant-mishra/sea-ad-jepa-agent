"""Guard the current successor-5 read-first review artifacts from stale claims."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / "results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_SUCCESSOR5_CANDIDATE_STATE_V1.json"
PACKET = ROOT / "docs/agent/UNIFIED_TASK4_SUCCESSOR5_REGENERATION_REVIEW_PACKET_V1_20261017.md"


def test_successor5_state_preserves_both_red_attacks_and_no_authority():
    state = json.loads(STATE.read_text(encoding="utf-8"))
    packet = PACKET.read_text(encoding="utf-8")
    assert state["schema"] == "UNIFIED_TASK4_SUCCESSOR5_CANDIDATE_STATE_V1"
    assert state["status"] == "CANDIDATE_ONLY__EXACT_HEAD_GREEN_AND_INDEPENDENT_REVIEW_REQUIRED"
    assert state["independent_acceptance"] == "ABSENT"
    assert state["original_red"]["pr"] == 417
    assert state["original_red"]["run_id"] == 39000234158
    assert state["independent_red"]["pr"] == 419
    assert state["independent_red"]["run_id"] == 39083015888
    assert state["followon_repair"]["pr"] == 420
    assert state["followon_repair"]["last_verified_code_test_sha"] == "441b24971668a6ea916205f79fd5f6abec4f0abc"
    for sha in state["rejected_predecessors"]:
        assert sha in packet
    assert state["scope"]["external_execution_attestation_wired"] is False
    assert state["scope"]["final_authority_fail_closed"] is True
    assert state["scope"]["authority_effect"] == "NONE"
    assert "process-local" in packet.lower()
    assert "PR #419" in packet
    assert state["global_authority"] in packet
