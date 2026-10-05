import json
from pathlib import Path

from scripts.agent.verify_current_authority_surface_v1 import audit_authority_surface


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_pointer(root: Path, *, key: str = "handoff_path") -> None:
    _write(
        root / "docs/agent/JEPA_LATEST_HANDOFF_POINTER.json",
        json.dumps(
            {
                "date": "2026-10-05",
                "status": "V75_MEASUREMENT_ARCHITECTURE_QUALIFIED__TARGET_AUTHORITY_RECONCILIATION_REQUIRED__TRAINING_OFF",
                key: "docs/agent/JEPA_NEW_CHAT_HANDOFF_20261005_TARGET_AUTHORITY_RESET.md",
            }
        ),
    )


def _write_good_surface(root: Path) -> None:
    fixtures = {
        "START_HERE.md": "Date: 2026-10-05\nTraining: OFF\n500K: NOT AUTHORIZED\nNo qualified production target winner.\n160 is not biological dimension authority.\n",
        "README.md": "Current status — October 5, 2026\nTraining and multimodal training are OFF.\n500K is not authorized.\nNo qualified production target winner.\n160 is not biological dimensional authority.\n",
        "docs/agent/CURRENT_AUTHORITY_INDEX.md": "Date: 2026-10-05\nTRAINING = OFF\n500K NOT AUTHORIZED\nNo qualified production target winner.\n160 is not biological dimension authority.\n",
        "docs/agent/CURRENT_SUPERSESSION_MAP.md": "Date: 2026-10-05\nTRAINING = OFF\n500K NOT AUTHORIZED\nNo qualified production target winner.\n160 is not biological dimension authority.\n",
        "docs/agent/memory-os/ACTIVE_STATE.md": "Date: 2026-10-05\nTRAINING = OFF\n500K NOT AUTHORIZED\nNo qualified production target winner.\n160 is not biological dimension authority.\n",
        "docs/agent/ACTIVE_STATE.md": "Date: 2026-10-05\nStatus: SUPERSEDED_ALIAS_ROUTER\nCanonical: docs/agent/memory-os/ACTIVE_STATE.md\n",
        "docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json": json.dumps(
            {
                "status": "SUPERSEDED_ALIAS_ROUTER",
                "date": "2026-10-05",
                "canonical_current_state": "docs/agent/JEPA_HANDOFF_STATE_20261005_TARGET_AUTHORITY_RESET.json",
            }
        ),
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
    _write_pointer(tmp_path)

    failures = audit_authority_surface(tmp_path)
    assert any("stale date" in failure for failure in failures)
    assert any("training contradiction" in failure for failure in failures)
    assert any("legacy current-looking alias" in failure for failure in failures)


def test_accepts_consistent_oct5_surface_with_live_pointer_schema(tmp_path: Path) -> None:
    _write_good_surface(tmp_path)
    _write_pointer(tmp_path, key="handoff_path")
    assert audit_authority_surface(tmp_path) == []


def test_legacy_handoff_key_remains_accepted(tmp_path: Path) -> None:
    _write_good_surface(tmp_path)
    _write_pointer(tmp_path, key="handoff")
    assert audit_authority_surface(tmp_path) == []
