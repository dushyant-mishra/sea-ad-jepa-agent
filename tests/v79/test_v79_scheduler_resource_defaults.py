"""Resource-safe scheduler defaults do not require Windows/WSL to test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import run_v79_scheduler as S  # noqa: E402


def test_scheduler_defaults_to_one_machine_wide_fit():
    assert S.DEFAULT_SLOTS == 1


def test_scheduler_keeps_a_nonzero_settle_window():
    assert S.DEFAULT_SETTLE_SECONDS >= 120
