from __future__ import annotations

import platform
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "v79"
sys.path.insert(0, str(HERE))
import v79_v2_core_resource_monitor as RM  # noqa: E402


pytestmark = pytest.mark.skipif(platform.system().lower() != "windows", reason="real Win32 resource monitor check")


def test_real_windows_rss_bytes_returns_positive_process_working_set():
    rss = RM._rss_bytes()
    assert isinstance(rss, int)
    assert rss > 0


def test_real_windows_resource_monitor_enters_polls_and_exits():
    with RM.ResourceMonitor(poll_seconds=0.01) as monitor:
        payload = bytearray(1024 * 1024)
        payload[0] = 1
        time.sleep(0.03)
    assert monitor.peak_rss > 0
    assert monitor.wall_seconds > 0
    assert monitor.process_cpu_seconds >= 0
