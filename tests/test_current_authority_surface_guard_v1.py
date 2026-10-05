import json
from pathlib import Path

from scripts.agent.verify_current_authority_surface_v1 import audit_authority_surface


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_pointer(
    root: Path,
    *,
    key: str = "handoff_path",
    current_task_status: str = "PREMISE_QUALIFICATION_PREFREEZE_IN_PROGRESS",
    current_task: str = "Freeze the premise qualification and real-RNA prefreeze contract before any deciding TRAIN-only result is opened.",
) -> None:
    _write(
        root / "docs/agent/JEPA_LATEST_HANDOFF_POINTER.json",
        json.dumps(
            {
                "date": "2026-10-05",
                "status": "V75_MEASUREMENT_ARCHITECTURE_QUALIFIED__TARGET_LINEAGE_RECONCILED__PREMISE_QUALIFICATION_PREFREEZE__TRAINING_OFF",
                key: "docs/agent/JEPA_NEW_CHAT_HANDOFF_20261005_TARGET_AUTHORITY_RESET.md",
                "current_task_status": current_task_status,
                "current_task": current_task,
                "authority_freshness_rule": "UPDATE_CANONICAL_SURFACE_WHEN_CURRENT_TASK_CLOSES_OR_NEXT_AUTHORIZED_TASK_CHANGES",
            }
        ),
    )


def _write_good_surface(root: Path) -> None:
    fixtures = {
        "START_HERE.md": "Date: 2026-10-05\nTraining: OFF\n500K: NOT AUTHORIZED\nNo qualified production target winner.\n160 is not biological dimension authority.\nTarget lineage reconstruction is COMPLETE.\nCurrent task: premise qualification prefreeze.\nAuthority freshness: update canonical surface when the current task closes or the next authorized task changes.\n",
        "README.md": "Current status — October 5, 2026\nTraining and multimodal training are OFF.\n500K is not authorized.\nNo qualified production target winner.\n160 is not biological dimensional authority.\nTarget lineage reconstruction is complete.\nCurrent task: premise qualification prefreeze.\nAuthority freshness: update canonical surface when the current task closes or the next authorized task changes.\n",
        "docs/agent/CURRENT_AUTHORITY_INDEX.md": "Date: 2026-10-05\nTRAINING = OFF\n500K NOT AUTHORIZED\nNo qualified production target winner.\n160 is not biological dimension authority.\nTarget lineage reconstruction is COMPLETE.\nCurrent task: premise qualification prefreeze.\nAuthority freshness: update canonical surface when the current task closes or the next authorized task changes.\n",
        "docs/agent/CURRENT_SUPERSESSION_MAP.md": "Date: 2026-10-05\nTRAINING = OFF\n500K NOT AUTHORIZED\nNo qualified production target winner.\n160 is not biological dimension authority.\nTarget lineage reconstruction is COMPLETE.\nCurrent task: premise qualification prefreeze.\nAuthority freshness: update canonical surface when the current task closes or the next authorized task changes.\n",
        "docs/agent/memory-os/ACTIVE_STATE.md": "Date: 2026-10-05\nTRAINING = OFF\n500K NOT AUTHORIZED\nNo qualified production target winner.\n160 is not biological dimension authority.\nTarget lineage reconstruction is COMPLETE.\nCurrent task: premise qualification prefreeze.\nAuthority freshness: update canonical surface when the current task closes or the next authorized task changes.\n",
        "docs/agent/ACTIVE_STATE.md": "Date: 2026-10-05\nStatus: SUPERSEDED_ALIAS_ROUTER\nCanonical: docs/agent/memory-os/ACTIVE_STATE.md\n",
        "docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json": json.dumps(
            {
                "status": "SUPERSEDED_ALIAS_ROUTER",
                "date": "2026-10-05",
                "canonical_current_state": "docs/agent/JEPA_HANDOFF_STATE_20261005_TARGET_AUTHORITY_RESET.json",
            }
        ),
        "docs/agent/memory-os/NEXT_ALLOWED_ACTION.json": json.dumps(
            {
                "status": "SUPERSEDED_ALIAS_ROUTER",
                "date": "2026-10-05",
                "canonical_current_state": "docs/agent/JEPA_LATEST_HANDOFF_POINTER.json",
                "next_action": "FOLLOW_POINTER_CURRENT_TASK",
            }
        ),
        "docs/agent/memory-os/START_EVERY_JEPA_CHAT.txt": "Date: 2026-10-05\nStatus: CURRENT_BOOTSTRAP_ROUTER\nREAD FIRST: START_HERE.md\n",
        "docs/agent/memory-os/JEPA_PROJECT_MEMORY_OS.md": "# JEPA PROJECT MEMORY OS\nDate: 2026-10-05\nStatus: CURRENT_BOOTSTRAP_FRAMEWORK\nCanonical startup: START_HERE.md\n",
    }
    for rel, text in fixtures.items():
        _write(root / rel, text)


def test_rejects_stale_and_conflicting_current_surface(tmp_path: Path) -> None:
    _write(tmp_path / "START_HERE.md", "Date: 2026-09-30\nStatus: OLD\n")
    _write(tmp_path / "README.md", "Training is authorized.\n")
    _write(tmp_path / "docs/agent/CURRENT_AUTHORITY_INDEX.md", "Date: 2026-09-11\nTraining remains OFF.\n")
    _write(tmp_path / "docs/agent/CURRENT_SUPERSESSION_MAP.md", "Date: 2026-09-11\n")
    _write(tmp_path / "docs/agent/memory-os/ACTIVE_STATE.md", "Date: 2026-09-09\n")
    _write(tmp_path / "docs/agent/ACTIVE_STATE.md", "Date: 2026-09-03\nJEPA v4 Current Scientific State\n")
    _write(tmp_path / "docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json", json.dumps({"active_agent": "CLAUDE_CODE"}))
    _write(tmp_path / "docs/agent/memory-os/NEXT_ALLOWED_ACTION.json", json.dumps({"last_updated": "2026-09-10", "next_action": "OLD_GATE"}))
    _write(tmp_path / "docs/agent/memory-os/START_EVERY_JEPA_CHAT.txt", "CURRENT FAIL-CLOSED RULE: 15C controls.\n")
    _write(tmp_path / "docs/agent/memory-os/JEPA_PROJECT_MEMORY_OS.md", "Date: 2026-08-23\nStatus: controlling project-governance layer\n")
    _write_pointer(tmp_path)

    failures = audit_authority_surface(tmp_path)
    assert any("stale date" in failure for failure in failures)
    assert any("training contradiction" in failure for failure in failures)
    assert any("legacy current-looking alias" in failure for failure in failures)
    assert any("memory-os bootstrap" in failure for failure in failures)


def test_accepts_consistent_oct5_surface_with_live_pointer_schema(tmp_path: Path) -> None:
    _write_good_surface(tmp_path)
    _write_pointer(tmp_path, key="handoff_path")
    assert audit_authority_surface(tmp_path) == []


def test_legacy_handoff_key_remains_accepted(tmp_path: Path) -> None:
    _write_good_surface(tmp_path)
    _write_pointer(tmp_path, key="handoff")
    assert audit_authority_surface(tmp_path) == []


def test_rejects_completed_target_lineage_still_advertised_as_current_task(tmp_path: Path) -> None:
    _write_good_surface(tmp_path)
    _write_pointer(
        tmp_path,
        current_task_status="TARGET_LINEAGE_RECONCILIATION_REQUIRED",
        current_task="Reconstruct the terminal target lineage before any new target experiment.",
    )
    failures = audit_authority_surface(tmp_path)
    assert any("authority freshness" in failure.lower() for failure in failures)
