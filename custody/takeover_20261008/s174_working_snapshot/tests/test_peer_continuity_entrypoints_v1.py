from __future__ import annotations

import hashlib
import json
import copy
from pathlib import Path

from scripts.agent.update_work_checkpoint import render_takeover_markdown, write_takeover
from scripts.agent.work_checkpoint import build_checkpoint


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json"
CLAUDE = ROOT / "CLAUDE.md"
ACTIVE_PLAN = ROOT / "docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_claude_entrypoint_points_to_machine_checkpoint_and_active_plan() -> None:
    text = CLAUDE.read_text(encoding="utf-8")
    assert "docs/agent/CURRENT_WORK_CHECKPOINT.json" in text
    assert "docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md" in text
    assert "Codex and Claude Code are equal implementation peers" in text
    assert "validate" in text.lower()
    assert "self-promote" in text.lower()


def test_active_plan_preserves_exact_scope_and_stop() -> None:
    text = ACTIVE_PLAN.read_text(encoding="utf-8")
    assert "PASS_TO_IMPLEMENT_CONTINUITY_AND_C2_ONLY" in text
    assert "Continuity -> preserved C2 -> exact defect localization -> regression test -> STOP" in text
    assert "Do not rehabilitate or retrain T1" in text
    assert "Real F1 remains forbidden" in text
    assert "F1-B successor" in text and "downstream" in text


def test_state_binds_authorities_firewall_and_exact_next_action() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    # active_agent is provenance only and rotates on every handoff, so it must be
    # asserted as peer membership. Pinning it to one agent would make a lawful
    # Codex->Claude takeover -- the system's primary use case -- fail the suite.
    assert state["peer_agents"] == ["CODEX", "CLAUDE_CODE"]
    assert state["active_agent"] in state["peer_agents"]
    assert state["provenance"]["last_agent"] in state["peer_agents"]
    assert state["agent_symmetry"]["equal_implementation_authority"] is True
    assert state["agent_symmetry"]["self_promotion_forbidden"] is True
    assert state["gates"]["current"] == "PASS_TO_IMPLEMENT_CONTINUITY_AND_C2_ONLY"
    assert state["firewall"] == {
        "real_f1_forbidden": True,
        "dev_expression_closed": True,
        "sealed_expression_closed": True,
        "pathology_closed": True,
        "production_training_forbidden": True,
    }
    # next_authorized_actions advances as work completes, so it is asserted as an
    # invariant rather than pinned to one moment's value. Pinning it made every
    # lawful advance of the plan fail the suite.
    actions = state["next_authorized_actions"]
    assert isinstance(actions, list) and actions
    assert all(isinstance(a, str) and a == a.upper() and a.strip() for a in actions)
    # Fail-closed: some action must return control for review.
    assert any(a.startswith("STOP_") for a in actions)
    assert "remote_only" in state["assets"] and "local" in state["assets"]


def test_state_authority_hashes_match_bytes() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    by_path = {item["path"]: item["sha256"] for item in state["authorities"]}
    required = [
        "AGENTS.md",
        "docs/superpowers/specs/2026-09-05-jepa-peer-agent-continuity-design.md",
        "docs/superpowers/plans/2026-09-05-jepa-continuity-c2-implementation-plan.md",
        "docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md",
    ]
    for relative in required:
        assert by_path[relative] == _sha(ROOT / relative)


def test_takeover_render_is_deterministic_and_agent_neutral() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    checkpoint = dict(state)
    checkpoint["schema"] = "JEPA_WORK_CHECKPOINT_V1"
    checkpoint["git"] = {
        "branch": "branch",
        "head_sha": "a" * 40,
        "origin_main_sha": "b" * 40,
    }
    checkpoint["checkpoint_semantic_sha256"] = "c" * 64
    first = render_takeover_markdown(checkpoint)
    second = render_takeover_markdown(checkpoint)
    assert first == second
    assert "CODEX" in first and "CLAUDE_CODE" in first
    # Render every current action and blocker, whatever they happen to be.
    for action in state["next_authorized_actions"]:
        assert action in first
    for blocker in state["unresolved_blockers"]:
        assert blocker in first
    assert "cannot promote" in first.lower()


def test_takeover_write_uses_lf_on_installed_python(tmp_path: Path) -> None:
    target = tmp_path / "TAKEOVER.md"
    write_takeover(target, "line one\nline two\n")
    assert target.read_bytes() == b"line one\nline two\n"


def test_codex_claude_codex_provenance_handoff_preserves_authority_and_action() -> None:
    codex_state = json.loads(STATE.read_text(encoding="utf-8"))
    claude_state = copy.deepcopy(codex_state)
    claude_state["provenance"]["last_agent"] = "CLAUDE_CODE"
    returned_state = copy.deepcopy(claude_state)
    returned_state["provenance"]["last_agent"] = "CODEX"
    checkpoints = [
        build_checkpoint(ROOT, ROOT, state)
        for state in (codex_state, claude_state, returned_state)
    ]
    assert checkpoints[0]["authorities"] == checkpoints[1]["authorities"] == checkpoints[2]["authorities"]
    assert checkpoints[0]["next_authorized_actions"] == checkpoints[1]["next_authorized_actions"] == checkpoints[2]["next_authorized_actions"]
