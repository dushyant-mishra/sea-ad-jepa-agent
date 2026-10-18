"""Prevent a successor-5 GREEN from being mistaken for Task 4 acceptance."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / "results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_SUCCESSOR6_CANDIDATE_STATE_V1.json"
PACKET = ROOT / "docs/agent/UNIFIED_TASK4_SUCCESSOR6_FINITE_EXAM_REVIEW_PACKET_V1_20261017.md"


def test_successor6_preserves_rejected_successor5_and_both_independent_reds():
    state = json.loads(STATE.read_text(encoding="utf-8"))
    packet = PACKET.read_text(encoding="utf-8")
    assert state["schema"] == "UNIFIED_TASK4_SUCCESSOR6_CANDIDATE_STATE_V1"
    assert state["rejected_current_predecessor"] == "36e3b46f1ca44465864a11872b459b5d108d6a67"
    assert state["public_duplicate_remint_red"]["pr"] == 422
    assert state["public_duplicate_remint_red"]["run_id"] == 39084356745
    assert state["concurrent_spend_red"]["pr"] == 424
    assert state["concurrent_spend_red"]["run_id"] == 39084723524
    assert state["independent_review_verdict"] == "ABSENT"
    assert state["mechanics_scope"] == "PROCESS_LOCAL_DEVELOPMENT_ONLY"
    assert state["cross_process_uniqueness_authorized"] is False
    assert state["external_authority_wired"] is False
    for sha in state["rejected_predecessors"]:
        assert sha in packet
    assert "PR #422" in packet and "PR #424" in packet
    assert state["global_authority"] in packet
